"""Bounded analysis only. Reads restricted cache/saved CSVs; never imports simulator."""
from pathlib import Path
import json,hashlib,re,sys,time
import numpy as np,pandas as pd
R=Path(__file__).parent
F=R.parent/'2026-11-09_academic_review_followup_pricing'
AUD=R.parent/'2026-11-13_pricing_recalibration_context_audit'
P=22.354198442390455; OLD=21.34586956773507
for n in ['array_a','epsilon_population','zero_denominator','distribution_fits','distance_cutoffs','fare_bounds','reference_values','pricing_contract','decision_support','intermediate']:(R/n).mkdir(exist_ok=True)
def js(n,x):
 p=R/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,default=lambda z:z.item() if isinstance(z,np.generic) else str(z))+'\n');t.replace(p)
def save(n,x):pd.DataFrame(x).to_csv(R/n,index=False)
def checkpoint(stage,**kw):js('progress.json',dict(stage=stage,updated=time.strftime('%Y-%m-%dT%H:%M:%S'),**kw));print(stage,flush=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
Q=np.array([.01,.05,.1,.25,.5,.75,.9,.95,.99]);QN=['P1','P5','P10','P25','median','P75','P90','P95','P99']
def stats(x,w=None):
 x=np.asarray(x);w=np.ones(len(x)) if w is None else np.asarray(w,dtype=float);good=np.isfinite(x);tot=w.sum();z=x[good];v=w[good];N=v.sum()
 d=dict(N_units=len(x),total_mass=tot,finite_units=int(good.sum()),finite_mass=N,undefined_units=int((~good).sum()),undefined_mass=float(w[~good].sum()),negative_units=int((z<0).sum()),negative_mass=float(v[z<0].sum()),zero_units=int((z==0).sum()),zero_mass=float(v[z==0].sum()),positive_units=int((z>0).sum()),positive_mass=float(v[z>0].sum()),effective_N_Kish=float(N*N/np.dot(v,v)))
 if not N:return d
 order=np.argsort(z);zz=z[order];vv=v[order];cum=np.cumsum(vv)/N;quant=zz[np.minimum(np.searchsorted(cum,Q),len(zz)-1)]
 mean=np.dot(z,v)/N;sd=np.sqrt(np.dot((z-mean)**2,v)/N)
 d.update(mean=mean,weighted_mean=mean,population_SD=sd,min=float(zz[0]),max=float(zz[-1]),**dict(zip(QN,quant)))
 return d

def data_phase():
 if (R/'intermediate/data_complete.json').exists():print('REUSE data phase');return
 # Existing audit fingerprint is the authority for saved array source, no raw preparation.
 source=F/'fare_distance/fare_by_distance_0p5km.csv'
 audit=AUD.joinpath('README.md').read_text();m=re.search(r'`'+re.escape(str(source.relative_to(Path.cwd())))+r'`: `([0-9a-f]{64})`',audit)
 assert m and sha(source)==m.group(1),'Saved array source changed since audit'
 b=pd.read_csv(source);a=b[(b.lower_distance_km>=1)&(b.upper_distance_km<=75)].copy().reset_index(drop=True)
 assert len(a)==148 and a.N.sum()==7946921
 assert np.isclose(np.average(a.mean_fare,weights=a.N),P,atol=1e-13,rtol=0)
 evidence=[Path('README.md'),Path('src/pricing/passenger_sensitive_v1.py'),Path('src/simulation/passenger_sensitive_v1.py'),Path('src/rl/passenger_sensitive_dqn.py'),AUD/'README.md',source,Path('data/processed/price_distance_sensitivity_record029/authoritative_epsilon_methodology.json')]
 js('input_fingerprints.json',{str(p):sha(p) for p in evidence})
 f=pd.read_parquet(F/'jan01_mar15_analysis_cache.parquet');assert len(f)==8692819
 assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
 fare=f.fare.to_numpy();dist=f.trip_distance.to_numpy()*1.609344;ids=np.floor(dist/.5).astype(int);domain=(dist>=1)&(dist<75)
 assert np.isfinite(fare).all() and np.isfinite(dist).all() and (fare>0).all()
 counts=np.bincount(ids);sums=np.bincount(ids,weights=dist)
 assert np.array_equal(counts[2:150],a.N)
 a['centre_km']=(a.lower_distance_km+a.upper_distance_km)/2;a['actual_mean_distance_km']=sums[2:150]/counts[2:150]
 save('array_a/array_a_verified.csv',a)
 near=[]
 for scope,mask in [('ARRAY_RANGE',domain),('ALL_SAFE',np.ones(len(f),bool))]:
  for tau in [.25,.5,1,2]:
   mask2=mask&(abs(fare-P)<=tau)
   near.append(dict(scope=scope,half_window_USD=tau,N=int(mask2.sum()),mean_distance_km=float(dist[mask2].mean()),mean_fare=float(fare[mask2].mean()),definition='Diagnostic price-conditioned mean; tau not newly approved'))
 save('reference_values/price_conditioned_candidates.csv',near)
 lc=next(x['mean_distance_km'] for x in near if x['scope']=='ARRAY_RANGE' and x['half_window_USD']==1)
 candidates={'A_LOWER_EDGE':4.5,'B_INTERPOLATED':4.616983790655043,'C_PRICE_NEAR_PM1':lc}
 js('reference_values/candidates.json',dict(P_base_exact=P,P_base_document=22.3542,P_base_historical=OLD,L_candidates=candidates,C_definition='Mean distance among 1<=km<75 safe-period rows with abs(fare-P_candidate)<=1USD; diagnostic inherited window, NOT selected.',taxi_meter_threshold='NOT_ESTABLISHED'))
 records=[];summary=[];zeros=[];extremes=[];reps={'LOWER_EDGE':'lower_distance_km','CENTRE':'centre_km','ACTUAL_MEAN':'actual_mean_distance_km'}
 for cname,L in candidates.items():
  for rep,col in reps.items():
   rp=(a.mean_fare.to_numpy()-P)/P;rl=(a[col].to_numpy()-L)/L;e=np.divide(rl,rp,out=np.full(len(a),np.nan),where=rp!=0)
   for i in range(len(a)):records.append(dict(candidate=cname,L_base=L,representation=rep,lower_edge=a.lower_distance_km[i],N=a.N[i],L=a[col][i],P=a.mean_fare[i],r_P=rp[i],r_L=rl[i],new_e=e[i]))
   for pop,w in [('BIN_UNWEIGHTED',None),('BIN_COUNT_WEIGHTED',a.N.to_numpy())]:
    summary.append(dict(population=pop,candidate=cname,L_base=L,representation=rep,scope='ARRAY_RANGE',near_price_001_mass=float(np.sum((abs(a.mean_fare-P)<=.01)*(1 if w is None else w))),**stats(e,w)))
    ww=np.ones(len(e)) if w is None else w
    for case,mk in [('0/nonzero',(rl==0)&(rp!=0)),('nonzero/0',(rl!=0)&(rp==0)),('0/0',(rl==0)&(rp==0))]:zeros.append(dict(population=pop,candidate=cname,representation=rep,case=case,units=int(mk.sum()),mass=float(ww[mk].sum())))
  rp=(fare-P)/P;rl=(dist-L)/L;e=np.divide(rl,rp,out=np.full(len(f),np.nan),where=rp!=0)
  for scope,mask in [('ARRAY_RANGE',domain),('ALL_SAFE',np.ones(len(f),bool))]:
   s=stats(e[mask]);summary.append(dict(population='TRIP_LEVEL_NEW_E',candidate=cname,L_base=L,representation='ACTUAL_TRIP',scope=scope,near_price_001_mass=int((mask&(abs(fare-P)<=.01)).sum()),**s))
   for case,mk in [('0/nonzero',(rl==0)&(rp!=0)),('nonzero/0',(rl!=0)&(rp==0)),('0/0',(rl==0)&(rp==0))]:zeros.append(dict(population='TRIP_LEVEL_NEW_E',candidate=cname,representation='ACTUAL_TRIP_'+scope,case=case,units=int((mask&mk).sum()),mass=int((mask&mk).sum())))
  np.save(R/f'intermediate/new_e_{cname}.npy',e[domain])
  for kind,score in [('largest_positive',e),('most_negative',-e),('largest_absolute',abs(e)),('smallest_price_gap',-abs(rp))]:
   eligible=np.flatnonzero(domain&np.isfinite(e));ix=eligible[np.argpartition(score[eligible],-8)[-8:]];ix=ix[np.argsort(score[ix])[::-1]]
   for j in ix:extremes.append(dict(candidate=cname,selection=kind,source_row_index=int(f.source_row_index.iloc[j]),timestamp=str(f.pickup_timestamp.iloc[j]),fare=fare[j],distance_km=dist[j],r_P=rp[j],r_L=rl[j],new_e=e[j],same_reference_reciprocal=rp[j]/rl[j] if rl[j]!=0 else np.nan,Record029_epsilon=f.epsilon.iloc[j],Record029_status=f.epsilon_status.iloc[j]))
  checkpoint('CANDIDATE_SUMMARY_COMPLETE',candidate=cname)
 save('array_a/array_distance_representation_comparison.csv',records);save('epsilon_population/population_statistics.csv',summary);save('zero_denominator/zero_cases.csv',zeros);save('zero_denominator/extreme_new_e_examples.csv',extremes)
 # Safe-period validity is defined anew: no historical VALID/T0 filtering.
 np.save(R/'intermediate/fare_array_range.npy',fare[domain]);np.save(R/'intermediate/distance_array_range.npy',dist[domain])
 mass=[]
 for lo,hi in [(1,5),(5,10),(10,20),(20,40),(40,60),(60,75)]:
  mask=a.lower_distance_km.ge(lo)&a.upper_distance_km.le(hi)
  mass.append(dict(lower_km=lo,upper_km=hi,bin_N=int(mask.sum()),trip_N=int(a.loc[mask,'N'].sum()),unweighted_bin_pct=100*mask.mean(),count_weighted_pct=100*a.loc[mask,'N'].sum()/a.N.sum()))
 save('epsilon_population/distance_probability_mass.csv',mass)
 # Resolution diagnostics with exact and rounded bases; cumulative bands include exact-zero cases.
 denom=[];precision=[];reciprocal=[]
 for pname,p in [('EXACT',P),('DOCUMENT_ROUNDED',22.3542),('HISTORICAL',OLD)]:
  rp=(fare-p)/p;gap=abs(fare-p)
  for scope,mask in [('ARRAY_RANGE',domain),('ALL_SAFE',np.ones(len(f),bool))]:
   for usd in [0,.01,.05,.10,.25,.50,1.]:denom.append(dict(P_definition=pname,P_base=p,scope=scope,absolute_fare_gap_le_USD=usd,relative_gap_le=usd/p,N=int((mask&(gap<=usd)).sum()),percentage=100*np.mean(gap[mask]<=usd),minimum_observed_gap=float(gap[mask].min())))
  for cname,L in candidates.items():
   rl=(dist[domain]-L)/L;rp1=rp[domain];e=np.divide(rl,rp1,out=np.full(len(rl),np.nan),where=rp1!=0)
   precision.append(dict(P_definition=pname,P_base=p,candidate=cname,L_base=L,population='TRIP_LEVEL_NEW_E',**stats(e)))
   good=np.isfinite(rl)&np.isfinite(rp1)&(rl!=0)&(rp1!=0)
   error=abs((rl[good]/rp1[good])*(rp1[good]/rl[good])-1)
   reciprocal.append(dict(P_definition=pname,candidate=cname,N=int(good.sum()),max_abs_product_error=float(error.max()),mean_abs_product_error=float(error.mean()),mismatch_gt_1e_12=int((error>1e-12).sum())))
 save('zero_denominator/price_gap_bands.csv',denom);save('reference_values/P_base_sensitivity.csv',precision);save('epsilon_population/reciprocal_validation.csv',reciprocal)
 js('zero_denominator/fare_precision.json',dict(N=len(f),near_cent_grid_fraction=float(np.mean(abs(fare*100-np.round(fare*100))<1e-7)),minimum_distance_from_exact_P=float(abs(fare-P).min()),nonfinite_fare_N=int((~np.isfinite(fare)).sum()),comment='Precision is observed, not an automatic exclusion rule; inclusive dollar bands are diagnostics.'))
 # Distance filters: retain old allowed physical range only as sensitivity reference.
 scenarios={}
 for lo in [1,1.5,2]:scenarios[f'LOWER_{lo}_UPPER_75']=(dist>=lo)&(dist<75)
 scenarios['LOWER_1_EXISTING_100_MILES']=(dist>=1)&(dist<=160.9344)
 for threshold in [50,100]:
  sparse=a.loc[a.N>=threshold,'lower_distance_km'].to_numpy();valid_ids=(sparse/.5).astype(int)
  scenarios[f'MIN_{threshold}_INDIVIDUAL']=domain&np.isin(ids,valid_ids)
  good=a.N.to_numpy()>=threshold;stop=int(np.flatnonzero(~good)[0]) if (~good).any() else len(a);endpoint=1+.5*stop
  scenarios[f'MIN_{threshold}_CONTIGUOUS']=(dist>=1)&(dist<endpoint)
 cuts=[];bounds=[];clips=[];boundsets=[]
 quantiles=[.001,.005,.01,.025,.05,.95,.975,.99,.995,.999,1]
 labels=['P0.1','P0.5','P1','P2.5','P5','P95','P97.5','P99','P99.5','P99.9','maximum']
 scenarios_bound={'ALL_SAFE':np.ones(len(f),bool),**scenarios}
 for label,mask in scenarios_bound.items():
  pp=fare[mask];qs=np.quantile(pp,quantiles);n=len(pp)
  bounds.append(dict(scenario=label,N=n,**dict(zip(labels,qs))))
  for q in [.001,.005,.01,.025,.05]:
   low,high=np.quantile(pp,[q,1-q]);v=dict(scenario=label,q_lower=q,q_upper=1-q,lower=low,upper=high,pct_clipped_low=100*np.mean(pp<low),pct_clipped_high=100*np.mean(pp>high),pct_unaffected=100*np.mean((pp>=low)&(pp<=high)))
   clips.append(v);boundsets.append(v)
  if label=='ALL_SAFE':continue
  p=float(pp.mean());lnear=float(dist[mask&(abs(fare-p)<=1)].mean());selected=b[b.lower_distance_km.isin(np.unique(ids[mask])*.5)]
  for ref,L in [('FIXED_4P5',4.5),('SCENARIO_PRICE_NEAR_PM1',lnear)]:
   rp=(pp-p)/p;rr=(dist[mask]-L)/L;e=np.divide(rr,rp,out=np.full(n,np.nan),where=rp!=0)
   cuts.append(dict(scenario=label,L_definition=ref,L_base=L,P_base=p,retained_trips=n,excluded_trips=len(f)-n,retained_pct=100*n/len(f),demand_mass_lost_pct=100*(1-n/len(f)),bins_retained=len(selected),largest_usable_endpoint_km=float(selected.upper_distance_km.max()),bin_mean_fare_min=selected.mean_fare.min(),bin_mean_fare_max=selected.mean_fare.max(),**stats(e)))
 save('distance_cutoffs/filter_scenarios.csv',cuts);save('fare_bounds/trip_fare_quantiles.csv',bounds);save('fare_bounds/quantile_clipping_effects.csv',clips)
 # Arithmetic candidate offers and empirical coverage.
 actions=np.array([.85,.9,.95,1,1.05,1.1,1.15]);offers=[];coverage=[];collapse=[]
 for pn,p in [('HISTORICAL',OLD),('NEW_EXACT',P),('DOCUMENT_ROUNDED',22.3542)]:
  for fac in actions:offers.append(dict(P_definition=pn,P_base=p,factor=fac,offer=p*fac,provisional_platform_min=.85*p,base_fare_floor_candidate=p,provisional_platform_max=1.15*p))
  for lo,hi in [(0,1),(1,5),(5,10),(10,20),(20,40),(40,60),(60,75),(75,160.9344001)]:
   m=(dist>=lo)&(dist<hi);z=fare[m]
   coverage.append(dict(P_definition=pn,lower_km=lo,upper_km=hi,N=len(z),fare_median=np.median(z),below_offer_pct=100*np.mean(z<actions[0]*p),within_offer_pct=100*np.mean((z>=actions[0]*p)&(z<=actions[-1]*p)),above_offer_pct=100*np.mean(z>actions[-1]*p)))
  for br in boundsets:
   vals=np.clip(actions*p,br['lower'],br['upper']);uniq=len(np.unique(vals));pairs=sum(vals[i]==vals[j] for i in range(7) for j in range(i+1,7))
   collapse.append(dict(P_definition=pn,bound_scenario=br['scenario'],q_lower=br['q_lower'],lower=br['lower'],upper=br['upper'],unique_prices=uniq,collapsed_arm_count=7-uniq,collapsed_pairs=pairs,pair_collapse_pct=100*pairs/21,clipped_offer_values=json.dumps(vals.tolist()),interpretation='Global offers/bounds: same arithmetic for every request; no stochastic request frequency implied'))
 save('pricing_contract/candidate_action_prices.csv',offers);save('pricing_contract/action_coverage_by_distance.csv',coverage);save('pricing_contract/clipping_action_collapse.csv',collapse)
 # No runtime generated: saved March16 fixture provides bounded generator comparison only.
 dev=pd.read_csv(R.parent/'2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/professor_review/episode25_march16_request_level_acceptance.csv',usecols=['L_gg_prime_km','request_timestamp'])
 assert pd.to_datetime(dev.request_timestamp).ge('2026-03-16').all() and pd.to_datetime(dev.request_timestamp).lt('2026-03-17').all()
 dd=dev.L_gg_prime_km.to_numpy();dids=np.floor(dd/.5).astype(int);dh=np.bincount(dids,minlength=150)[2:150];ng=dh.sum();p=a.N.to_numpy()/a.N.sum();q=dh/ng
 tv=.5*abs(p-q).sum();from scipy.spatial.distance import jensenshannon
 js('decision_support/generator_comparison.json',dict(scope='Saved Episode25 March16 four-slot development illustration only; not calibration or general generator certification',N=len(dd),in_array_range_N=int(ng),below_1_N=int((dd<1).sum()),ge75_N=int((dd>=75).sum()),conditional_halfkm_total_variation=float(tv),conditional_KS_binned=float(abs(np.cumsum(p)-np.cumsum(q)).max()),conditional_JS_distance=float(jensenshannon(p,q)),no_new_simulation=True))
 save('decision_support/generator_distance_comparison.csv',[dict(lower_km=float(a.lower_distance_km[i]),array_N=int(a.N[i]),array_probability=float(p[i]),development_N=int(dh[i]),development_conditional_probability=float(q[i])) for i in range(148)])
 js('intermediate/data_complete.json',dict(candidates=candidates,N_all=len(f),N_array=int(domain.sum()),historical_status_not_used=True,cache_min=str(f.pickup_timestamp.min()),cache_max=str(f.pickup_timestamp.max()),source_csv_sha256=sha(source)))
 checkpoint('DATA_AND_DESCRIPTIVES_COMPLETE')

if __name__=='__main__':data_phase()
