"""Bounded, development-only academic-review reconciliation; no model fitting."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent; V=R.parent
P=21.34586956773507;L=4.856998243316242;MIN=.85*P;MAX=1.15*P
source='data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet'
def dump(n,x):(R/n).write_text(json.dumps(x,indent=2,default=lambda v:v.item())+'\n')
def stats(x):
 qs=[0,.001,.005,.01,.025,.05,.1,.25,.5,.75,.9,.95,.99,.995,1]
 return dict(N=len(x),mean=float(np.mean(x)),SD=float(np.std(x)),**dict(zip(['min','P0.1','P0.5','P1','P2.5','P5','P10','P25','median','P75','P90','P95','P99','P99.5','max'],map(float,np.quantile(x,qs)))))
f=pd.read_parquet(source,columns=['pickup_timestamp','epsilon','epsilon_status','fare','trip_distance','hour'],filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-16'))])
assert f.pickup_timestamp.max()<pd.Timestamp('2026-03-16')
valid=f.epsilon_status.eq('VALID')&np.isfinite(f.epsilon)
signed=f.loc[valid,'epsilon'].to_numpy(); eligible=valid&f.epsilon.ne(0)
pos=f.loc[eligible,'epsilon'].abs().to_numpy();d=f.loc[eligible,'trip_distance'].to_numpy()*1.609344
rows=[dict(distribution='SIGNED_HISTORICAL_SENSITIVITY',**stats(signed),negative_pct=100*np.mean(signed<0),positive_pct=100*np.mean(signed>0),zero_pct=100*np.mean(signed==0)),dict(distribution='POSITIVE_V1_BEHAVIOURAL_PROXY_BEFORE_SUPPORT',**stats(pos))]
summary=dict(source=source,N_cleaned_date_restricted=len(f),N_valid=len(signed),unresolved_status_N=int((~f.epsilon_status.eq('VALID')).sum()),unresolved_status_pct=100*float((~f.epsilon_status.eq('VALID')).mean()),valid_nonfinite_N=int((f.epsilon_status.eq('VALID')&~np.isfinite(f.epsilon)).sum()),latest_timestamp=str(f.pickup_timestamp.max()))
old=json.loads((V/'restricted_calibration_support.json').read_text())
comparisons=[];armrows=[];rawrows=[];tails=[]
for name,qlo,qhi in [('T0',.005,.995),('T1',.005,.99),('T2',.01,.995),('T3',.01,.99)]:
 lo,hi=np.quantile(pos,[qlo,qhi]);m=(pos>=lo)&(pos<=hi);e=pos[m];dist=d[m]
 if name=='T0':
  assert lo==old['positive_support_lower'] and hi==old['positive_support_upper'] and len(e)==old['N_positive_supported']
  assert np.array_equal(e,np.load(V/'positive_epsilon_calibration.npy',mmap_mode='r'))
  rows.append(dict(distribution='POSITIVE_V1_SUPPORTED_T0',**stats(e)))
  summary.update(support_lower=float(lo),support_upper=float(hi),retained_N=len(e),retained_pct=100*float(m.mean()))
  for side,mask in [('lower',pos<lo),('upper',pos>hi)]:
   z=pos[mask];raw=P+(P/z)*((d[mask]-L)/L)
   tails.append(dict(tail=side,N=len(z),percentage=100*float(mask.mean()),epsilon_min=float(z.min()),epsilon_max=float(z.max()),raw_preference_min=float(raw.min()),raw_preference_max=float(raw.max()),raw_preference_median=float(np.median(raw))))
 raw=P+(P/e)*((dist-L)/L);effective=np.maximum(MIN,raw)
 assert np.isfinite(raw).all() and (effective>=MIN).all() and (effective>=raw).all()
 before=sum((P*a<=raw).astype(np.int8) for a in [.85,.9,.95,1,1.05,1.1,1.15]);after=sum((P*a<=effective).astype(np.int8) for a in [.85,.9,.95,1,1.05,1.1,1.15]);assert (after>=1).all()
 comparisons.append(dict(candidate=name,lower=float(lo),upper=float(hi),retained_N=len(e),retained_pct=100*float(m.mean()),lower_excluded_N=int((pos<lo).sum()),upper_excluded_N=int((pos>hi).sum()),epsilon_mean=float(e.mean()),epsilon_SD=float(e.std()),epsilon_median=float(np.median(e)),zero_count=int((e==0).sum()),invalid_count=int((~np.isfinite(raw)).sum()),**{'P_raw_'+k:v for k,v in stats(raw).items()},**{'P_accept_'+k:v for k,v in stats(effective).items()},mean_feasible_arms=float(after.mean()),no_offer_pct=100*float((after==0).mean())))
 for n in range(8):armrows.append(dict(candidate=name,feasible_arms=n,before_N=int((before==n).sum()),before_pct=100*float((before==n).mean()),after_N=int((after==n).sum()),after_pct=100*float((after==n).mean())))
 tol=1e-10
 for label,mask in [('raw_lt_0',raw<0),('raw_le_0',raw<=0),('raw_positive_below_min',(raw>0)&(raw<MIN)),('raw_equal_min_tolerance',np.isclose(raw,MIN,rtol=0,atol=tol)),('raw_within_platform_bounds',(raw>=MIN)&(raw<=MAX)),('raw_above_max',raw>MAX),('effective_min_protection_applied',raw<MIN)]:
  rawrows.append(dict(candidate=name,category=label,N=int(mask.sum()),percentage=100*float(mask.mean()),equality_tolerance=tol))
pd.DataFrame(rows).to_csv(R/'sensitivity_distribution_summary.csv',index=False)
pd.DataFrame(comparisons).to_csv(R/'sensitivity_truncation_comparison.csv',index=False)
pd.DataFrame(armrows).to_csv(R/'feasible_arm_before_after.csv',index=False)
pd.DataFrame(rawrows).to_csv(R/'raw_vs_effective_preference_summary.csv',index=False)
pd.DataFrame(tails).to_csv(R/'excluded_tail_summary.csv',index=False)
# Fare evidence uses ALL cleaned development-date rows, not epsilon validity/support selection.
fare=f.fare.to_numpy();rat= fare/P;assert np.isfinite(rat).all() and (rat>0).all()
factor=[dict(metric='N',value=len(rat))]+[dict(metric='P'+str(q*100),value=float(np.quantile(rat,q))) for q in [.01,.05,.1,.25,.5,.75,.9,.95,.99]]
edges=[-np.inf,.85,.9,.95,1,1.05,1.1,1.15,np.inf]
for i in range(8):
 # Internal bins left-closed/right-open; last interior includes 1.15.
 m=(rat>=edges[i])&(rat<edges[i+1])
 if i==6:m=(rat>=1.10)&(rat<=1.15)
 if i==7:m=rat>1.15
 factor.append(dict(metric=f'bin_{edges[i]}_{edges[i+1]}',value=100*float(m.mean()),N=int(m.sum())))
factor.append(dict(metric='within_0.85_1.15',value=100*float(((rat>=.85)&(rat<=1.15)).mean()),N=int(((rat>=.85)&(rat<=1.15)).sum())))
pd.DataFrame(factor).to_csv(R/'pricing_factor_dataset_justification.csv',index=False)
bands=[];km=f.trip_distance.to_numpy()*1.609344
for lo,hi in zip([0,1,2,3,3.17,4,5,7.5,10,15],[1,2,3,3.17,4,5,7.5,10,15,np.inf]):
 m=(km>=lo)&(km<hi);z=rat[m]
 bands.append(dict(distance_band_km=f'[{lo},{hi})',N=len(z),median=float(np.median(z)),P10=float(np.quantile(z,.1)),P90=float(np.quantile(z,.9)),within_platform_range_pct=100*float(((z>=.85)&(z<=1.15)).mean())))
pd.DataFrame(bands).to_csv(R/'pricing_factor_distance_band_coverage.csv',index=False)
times=[]
for group,lo,hi in [('T1',0,3),('T2',4,5),('T3',6,15),('T4',16,23)]:
 z=rat[f.hour.between(lo,hi).to_numpy()];times.append(dict(time_group=group,N=len(z),median=float(np.median(z)),P10=float(np.quantile(z,.1)),P90=float(np.quantile(z,.9)),within_platform_range_pct=100*float(((z>=.85)&(z<=1.15)).mean())))
pd.DataFrame(times).to_csv(R/'pricing_factor_time_group_coverage.csv',index=False)
# Full observations represented on symlog/log axes; no tail trimming for graphs.
fig,ax=plt.subplots(figsize=(9,5));mx=max(abs(signed.min()),abs(signed.max()));bins=np.unique(np.r_[-np.geomspace(.001,mx,120)[::-1],0,np.geomspace(.001,mx,120)])
ax.hist(signed,bins=bins,weights=np.full(len(signed),100/len(signed)));ax.set_xscale('symlog',linthresh=.1);ax.set(xlabel='Signed historical sensitivity (symlog axis)',ylabel='Observations per bin (%)',title='Jan1–Mar15 VALID signed sensitivity');fig.tight_layout();fig.savefig(R/'signed_epsilon_distribution.png',dpi=160);plt.close(fig)
for log,name in [(False,'positive_epsilon_distribution.png'),(True,'positive_epsilon_distribution_logx.png')]:
 fig,ax=plt.subplots(figsize=(9,5));bins=np.geomspace(pos.min(),pos.max(),120) if log else np.linspace(0,pos.max(),150)
 ax.hist(pos,bins=bins,weights=np.full(len(pos),100/len(pos)),color='#31827c')
 if log:ax.set_xscale('log')
 else:ax.set_yscale('log')
 ax.axvline(summary['support_lower'],color='#a83b30',linestyle='--',label='T0 support bounds');ax.axvline(summary['support_upper'],color='#a83b30',linestyle='--');ax.legend();ax.set(xlabel='Absolute historical sensitivity'+(' (log axis)' if log else ''),ylabel='Observations per bin (%)'+('' if log else ', log scale'),title='Jan1–Mar15 positive proxy: full distribution');fig.tight_layout();fig.savefig(R/name,dpi=160);plt.close(fig)
summary['signed']=rows[0];summary['positive_before_support']=rows[1];summary['T0_supported']=rows[2];summary['tails']=tails
summary.update(selected_truncation='T0',epsilon_min=float(old['positive_support_lower']),additional_floor=False,sampling='TRUNCATED_EMPIRICAL_RESAMPLING',factor_coverage_pct=100*float(((rat>=.85)&(rat<=1.15)).mean()),factor_justification='MODERATE',equation_number_source_verified=False,RHS_resolved_by_project_decision=True)
dump('analysis_summary.json',summary)
print(json.dumps(summary))
