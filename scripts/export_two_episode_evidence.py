"""Read-only checkpoint-ledger extraction. No simulator/model imports or execution."""
from pathlib import Path
import json, mmap, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'results_v2/publication'; T=O/'tables'; F=O/'figures'
P=R/'results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration'
M=R/'models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42'
provenance={}; figures=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def record(p):provenance[str(p.relative_to(R))]=sha(p)
def decode(v):
 if not isinstance(v,dict):return v
 t=v['type']
 if t=='dict':return {k:decode(x) for k,x in v['items']}
 if t in ('list','tuple'):return [decode(x) for x in v['items']]
 if t=='float':return float.fromhex(v['hex'])
 raise ValueError(t)
def ledger(path):
 # Locate only recorded request audit; skip private memories and model state.
 with path.open('rb') as f:
  with mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
   pos=0;found=[]
   while True:
    pos=m.find(b'["audit",',pos)
    if pos<0:break
    if b'"request_id"' in m[pos:pos+180]:found.append(pos)
    pos+=1
   assert len(found)==1,found
   pos=found[0]+len(b'["audit", ')
   for size in [32,64,128,256]:
    try:v,end=json.JSONDecoder().raw_decode(m[pos:pos+size*1024**2].decode());break
    except json.JSONDecodeError:continue
   else:raise ValueError('Audit exceeds bounded extraction limit')
 record(path)
 manifest=json.loads((path.parent/'manifest.json').read_text());assert provenance[str(path.relative_to(R))]==manifest['component_hashes']['runtime.json']
 record(path.parent/'manifest.json')
 return pd.DataFrame(decode(v))
frames=[]
for ep,role in [(1,'milestone'),(2,'latest')]:
 d=ledger((M/role).resolve()/'runtime.json');d['episode_id']=ep;frames.append(d)
d=pd.concat(frames,ignore_index=True)
print('Recorded ledger rows',len(d),'columns',','.join(d.columns),flush=True)
assert len(d)==68845 and d.request_id.is_unique
x=pd.DataFrame({'experiment_id':P.name,'episode_id':d.episode_id,'slot_start_utc':pd.to_datetime(d.slot,utc=True)})
x['slot_start_ny']=x.slot_start_utc.dt.tz_convert('America/New_York')
x['slot_index']=x.groupby('episode_id').slot_start_utc.rank(method='dense').astype(int)
mapfields={'request_id':'request_id','request_arrival_utc':'source_pickup','origin_grid':'origin_grid','destination_grid':'destination_grid','trip_distance_km':'L','weather_code':'weather_code','time_group':'T_group','sensitivity_group':'sensitivity_condition','sampled_elasticity':'epsilon','p_base_usd':'P_base','l_base_km':'L_base','selected_pricing_factor':'factor','offered_price_usd':'P_offer','maximum_acceptable_price_usd':'P_max','accepted':'accepted','fallback_od':'is_fallback','successful_dispatch_reward_usd':'reward_contribution'}
for out,src in mapfields.items():x[out]=d[src] if src in d else np.nan
x['request_arrival_utc']=pd.to_datetime(x.request_arrival_utc,utc=True)
x['rejected']=~x.accepted;x['assigned']=d.dispatch_outcome.eq('ACCEPTED_AND_ASSIGNED');x['accepted_unmatched']=x.accepted&~x.assigned
x['rejection_reason']=np.where(x.rejected,'offered_price_exceeds_raw_ceiling',None)
x['source_trip_distance_km']=x.trip_distance_km;x['source_trip_distance_miles_reconstructed']=x.trip_distance_km/1.609344
x['dispatch_outcome']=d.dispatch_outcome;x['source_trip_id']=d.source_trip_id
x['value_provenance']='recorded checkpoint audit; derived flags and converted timestamps'
expected=x.p_base_usd+(x.p_base_usd/x.sampled_elasticity)*((x.trip_distance_km-x.l_base_km)/x.l_base_km)
err=abs(expected-x.maximum_acceptable_price_usd)
assert err.max()<1e-10 and (x.accepted==(x.offered_price_usd<=x.maximum_acceptable_price_usd)).all()
assert np.allclose(x.offered_price_usd,x.selected_pricing_factor*x.p_base_usd,rtol=0,atol=1e-12)
assert np.allclose(x.successful_dispatch_reward_usd,np.where(x.assigned,x.offered_price_usd,0),rtol=0,atol=1e-12)
assert x.accepted.sum()==18218 and x.assigned.sum()==14834 and x.accepted_unmatched.sum()==3384
assert x.request_arrival_utc.min()>=pd.Timestamp('2026-03-01T05:00Z') and x.request_arrival_utc.max()<pd.Timestamp('2026-03-01T21:00Z')
x.to_csv(T/'two_episode_passenger_acceptance_details.csv',index=False,na_rep='NA')
slots=json.loads((P/'slot_metrics.json').read_text());record(P/'slot_metrics.json'); rows=[]
for ep in (1,2):
 p=P/f'episode{ep}_request_reconciliation.json';record(p); rec=json.loads(p.read_text())['demand']
 for a in [s for s in slots if s['episode']==ep]:
  r=rec[a['slot']-1];g=x[(x.episode_id==ep)&(x.slot_index==a['slot'])];n=len(g)
  assert n==a['requests']==r['eligible_rows'] and g.accepted.sum()==a['accepted'] and g.assigned.sum()==a['assigned']
  assert hashlib.sha256(json.dumps(g.request_id.tolist()).encode()).hexdigest()==r['order_hash']
  assert np.isclose(g.successful_dispatch_reward_usd.sum(),a['revenue'],atol=1e-8)
  rows.append(dict(episode_id=ep,slot_index=a['slot'],slot_start_utc=g.slot_start_utc.iloc[0],slot_start_ny=g.slot_start_ny.iloc[0],total_source_requests=r['source_rows'],excluded_requests=r['excluded_invalid_trip_rows'],eligible_requests=n,accepted=a['accepted'],rejected=n-a['accepted'],acceptance_rate=a['accepted']/n,assigned=a['assigned'],accepted_unmatched=a['accepted']-a['assigned'],dispatch_success_rate=a['assigned']/a['accepted'],supported_od_requests=n-int(g.fallback_od.sum()),fallback_od_requests=int(g.fallback_od.sum()),supported_reward_usd=a['reward'],fallback_revenue_usd=a['fallback_revenue'],total_revenue_usd=a['revenue'],revenue_per_eligible_request_usd=a['revenue']/n,mean_offered_price_usd=g.offered_price_usd.mean(),mean_sampled_elasticity=g.sampled_elasticity.mean(),mean_maximum_acceptable_price_usd=g.maximum_acceptable_price_usd.mean(),epsilon_exploration=a['epsilon_before'],pricing_optimizer_updates=len(a['losses']),federation_round=a['federation_round']))
s=pd.DataFrame(rows);s.to_csv(T/'two_episode_slot_acceptance_summary.csv',index=False)
record(P/'validation.json');record(P/'frozen_configuration.json');record(P/'information_contract.json');record(P/'routing_initialization.json')
for p in ['src/simulation/od_pricing_runtime.py','src/simulation/historical_request_replay.py','src/pricing/slot_v3.py']:record(R/p)
def summary(keys,name):
 a=x.groupby(keys,observed=True,dropna=False).agg(N=('request_id','size'),accepted=('accepted','sum'),rejected=('rejected','sum'),assigned=('assigned','sum'),accepted_unmatched=('accepted_unmatched','sum'),revenue_usd=('successful_dispatch_reward_usd','sum')).reset_index();a['acceptance_rate']=a.accepted/a.N;a['assignment_rate_per_request']=a.assigned/a.N;a.to_csv(T/name,index=False);return a
x['distance_band_km']=pd.cut(x.trip_distance_km,[0,2,5,10,20,np.inf],right=False)
x['fare_band_usd']=pd.cut(x.offered_price_usd,[0,10,25,50,75,100,np.inf],right=False)
x['elasticity_band']=pd.cut(x.sampled_elasticity,[0,1.5,2,2.5,3,np.inf],right=False)
analyses={}
for keys,name in [(['distance_band_km'],'distance'),(['selected_pricing_factor'],'factor'),(['fare_band_usd'],'fare'),(['elasticity_band'],'elasticity'),(['weather_code','time_group','sensitivity_group'],'weather_time'),(['fallback_od'],'od_support')]:analyses[name]=summary(keys,'two_episode_acceptance_by_'+name+'.csv')
x['rejection_margin_usd']=x.offered_price_usd-x.maximum_acceptable_price_usd
x[['maximum_acceptable_price_usd','offered_price_usd','sampled_elasticity','rejection_margin_usd']].describe(percentiles=[.01,.05,.5,.95,.99]).to_csv(T/'two_episode_price_distribution_statistics.csv')
def save(name,fig,caption):
 fig.suptitle(caption,fontsize=11);fig.tight_layout(rect=(0,.04,1,.93));fig.text(.01,.005,'Source: two_episode_passenger_acceptance_details.csv / slot summary; March 1 training',fontsize=6)
 for ext in ('png','svg'):fig.savefig(F/(name+'.'+ext),dpi=150)
 plt.close(fig);figures.append({'figure':name,'source':'results_v2/publication/tables/two_episode_passenger_acceptance_details.csv','caption':caption})
f,ax=plt.subplots(figsize=(10,4));ax.stackplot(range(1,33),s.assigned,s.accepted_unmatched,s.rejected,labels=['Assigned','Accepted unmatched','Price rejected']);ax.set(xlabel='Consecutive half-hour slot (05:00–21:00 UTC)',ylabel='Requests');ax.legend();save('two_episode_acceptance_by_slot',f,'Two-episode training: passenger acceptance and dispatch outcomes')
f,axes=plt.subplots(2,2,figsize=(11,7))
for ax,name in zip(axes.flat,['distance','factor','fare','elasticity']):
 a=analyses[name];ax.bar(range(len(a)),a.acceptance_rate*100);ax.set(xticks=range(len(a)),xticklabels=[f'{v:.3f}' if isinstance(v,float) else str(v) for v in a.iloc[:,0]],ylabel='Accepted (%)',xlabel=name+' band / factor');ax.tick_params(axis='x',rotation=25);ax.set_ylim(0,max(a.acceptance_rate*100)*1.18)
 for i,r in a.iterrows():ax.text(i,r.acceptance_rate*100+1,str(int(r.N)),ha='center',fontsize=7)
save('two_episode_acceptance_strata',f,'Observed training acceptance; labels show request denominators (not causal effects)')
f,axes=plt.subplots(1,3,figsize=(12,4))
for ax,col,label in zip(axes,['offered_price_usd','maximum_acceptable_price_usd','rejection_margin_usd'],['Offered fare (USD)','Raw acceptance ceiling (USD)','Offer − ceiling (USD)']):ax.hist(x[col],bins=60);ax.set(xlabel=label,ylabel='Requests')
save('two_episode_price_distributions',f,'Recorded fares, raw ceilings and rejection margins; all eligible requests')
f,ax=plt.subplots(figsize=(10,4));a=analyses['weather_time'];labels=a.weather_code.astype(str)+' / '+a.time_group+' / '+a.sensitivity_group;ax.bar(labels,a.acceptance_rate*100);ax.set(ylabel='Accepted (%)',xlabel='Weather code / time / sensitivity group');ax.tick_params(axis='x',rotation=25);save('two_episode_weather_time_acceptance',f,'Recorded weather/time groups; denominators in companion CSV')
# Missing saved CNN error-distribution figure; reuse permitted saved forecast export only.
p=R/'results_v2/cnn_demand/2026-11-18_softplus_causal_research_training/forecasts.parquet';record(p);c=pd.read_parquet(p);assert c.target_start.max()<pd.Timestamp('2026-03-17T04:00Z')
f,axes=plt.subplots(1,2,figsize=(10,4))
for ax,(split,g) in zip(axes,c.groupby('split')):
 ax.hist(g.predicted_demand-g.observed_demand,bins=80,log=True);ax.set(title=split,xlabel='Predicted − actual requests / grid / slot',ylabel='Cells (log count)')
f.suptitle('Saved Softplus CNN error distributions; validation and March16 development');f.tight_layout()
for ext in ('svg','png'):f.savefig(F/('cnn_error_distribution.'+ext),dpi=150)
plt.close(f);figures.append(dict(figure='cnn_error_distribution',source=str(p.relative_to(R)),caption='Saved Softplus prediction errors; no new inference'))
pd.DataFrame(figures).to_csv(T/'passenger_evidence_figure_manifest.csv',index=False)
validation=dict(status='PASS',passenger_rows=len(x),slots=len(s),accepted=int(x.accepted.sum()),rejected=int(x.rejected.sum()),assigned=int(x.assigned.sum()),accepted_unmatched=int(x.accepted_unmatched.sum()),revenue=float(x.successful_dispatch_reward_usd.sum()),formula_max_abs_error=float(err.max()),request_order_hashes_matched=32,source_population=int(s.total_source_requests.sum()),excluded=int(s.excluded_requests.sum()),fallback_requests=int(x.fallback_od.sum()),sampling='Recorded exact hex-float checkpoint values; no RNG reconstruction',protected_period_access=False,simulation_rerun=False,training=False,source_sha256=provenance,figure_manifest='tables/passenger_evidence_figure_manifest.csv')
(O/'passenger_evidence_validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps({k:v for k,v in validation.items() if k!='source_sha256'},indent=2))
