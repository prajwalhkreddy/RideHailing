from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('results/analysis/2026-11-04_academic_review_validation')
def dump(name,x):(R/name).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def save(name):plt.tight_layout();plt.savefig(R/name,dpi=160);plt.close()
f=pd.read_csv(R/'request_level_pricing_full.csv',float_precision='round_trip');N=len(f)
base=f.P_base_USD.to_numpy();eps=f.epsilon_used.to_numpy();km=f.trip_distance_km.to_numpy();lb=f.runtime_L_base_km.to_numpy();native=f.trip_distance_miles_RAW.to_numpy();nativebase=lb/1.609344
pmax=base+((km-lb)/lb)*base/eps
pmaxnative=base+(native-nativebase)/nativebase*base/eps
np.testing.assert_allclose(pmax,f.P_max_USD,rtol=1e-12,atol=1e-10)
np.testing.assert_allclose(f.P_offer_USD,base*f.pricing_factor,rtol=1e-14)
calc=np.where(f.P_offer_USD<=pmax,'ACCEPT','REJECT');mismatches=int((calc!=f.recorded_passenger_decision).sum());assert mismatches==0
f['recomputed_passenger_decision']=calc
f.to_csv(R/'request_level_pricing_full.csv',index=False)
# Stratified reproducible diagnostic sample, not a population-weighted estimator.
cat=np.where(np.isclose(f.P_max_USD,base,rtol=0,atol=1e-9),'APPROX_EQUAL',np.where(f.P_max_USD<base,'BELOW','ABOVE'))
strata=f.assign(base_category=cat).groupby(['unmatched_reason','pricing_factor','base_category'],sort=True)
chosen=set()
for _,g in strata:
 chosen.update(g.index[np.linspace(0,len(g)-1,min(3,len(g)),dtype=int)].tolist())
remaining=np.array(sorted(set(f.index)-chosen));need=min(300,N)-len(chosen)
if need>0:chosen.update(remaining[np.linspace(0,len(remaining)-1,need,dtype=int)].tolist())
sample=f.loc[sorted(chosen)];assert 100<=len(sample)<=500
sample.to_csv(R/'request_level_pricing_review_sample.csv',index=False)
accepted=f.recorded_passenger_decision.eq('ACCEPT')
gap=f.P_offer_USD-f.P_max_USD
categories=[]
for k in ['BELOW','APPROX_EQUAL','ABOVE']:
 g=f[cat==k];categories.append(dict(category=k,N=len(g),percentage=100*len(g)/N,acceptance_percentage=100*g.recorded_passenger_decision.eq('ACCEPT').mean() if len(g) else None,mean_trip_distance_km=g.trip_distance_km.mean() if len(g) else None,median_trip_distance_km=g.trip_distance_km.median() if len(g) else None,pricing_factor_counts={str(a):int(b) for a,b in g.pricing_factor.value_counts().sort_index().items()}))
summary=dict(N=N,accepted=int(accepted.sum()),rejected=int((~accepted).sum()),acceptance_percentage=100*accepted.mean(),rejection_percentage=100*(~accepted).mean(),PASSENGER_DECISION_MISMATCH_COUNT=mismatches,exact_equality_count=int((f.P_offer_USD==f.P_max_USD).sum()),missing_numeric_count=int(f.select_dtypes('number').isna().sum().sum()),nonfinite_numeric_count=int((~np.isfinite(f.select_dtypes('number').to_numpy())).sum()),approximate_reporting_tolerance_USD=1e-9,comparison_rule='P_offer <= P_max, equality accepted; no tolerance in actual decision',price_gap_USD=dict(zip(['min','P5','median','P95','max'],map(float,np.quantile(gap,[0,.05,.5,.95,1]))),mean=float(gap.mean())),offer_vs_pmax={'below':int((gap< -1e-9).sum()),'approximately_equal':int((abs(gap)<=1e-9).sum()),'above':int((gap>1e-9).sum())},pmax_vs_runtime_pbase=categories,runtime_P_base_USD=list(map(float,f.P_base_USD.unique())),runtime_L_base_km=list(map(float,f.runtime_L_base_km.unique())),negative_Pmax_count=int((f.P_max_USD<0).sum()),pmax_km_vs_recorded_max_abs_difference_USD=float(np.max(abs(pmax-f.P_max_USD))),pmax_km_vs_recorded_mean_abs_difference_USD=float(np.mean(abs(pmax-f.P_max_USD))),pmax_native_vs_km_max_abs_difference_USD=float(np.max(abs(pmax-pmaxnative))),pmax_allclose_mismatch_count=int((~np.isclose(pmax,f.P_max_USD,rtol=1e-12,atol=1e-10)).sum()),request_sample_N=len(sample),sample_method='Sorted outcome × pricing factor × Pmax/base stratum coverage then deterministic evenly spaced rows; no synthetic rows',eligibility_definition='At each actual request decision time: origin or direct-neighbour IDLE drivers; charging-trigger, trip-energy and post-trip station-reserve feasible; price eligible iff offered fare >= persisted price_preference. Rejected passengers receive observational eligibility counts without dispatch.',outcomes_exhaustive=True)
dump('request_validation_summary.json',summary)
out=[]
for k in ['PASSENGER_REJECTED','PASSENGER_ACCEPTED_ASSIGNED','PASSENGER_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER','PASSENGER_ACCEPTED_OTHER_UNMATCHED']:
 n=int((f.unmatched_reason==k).sum());out.append(dict(outcome=k,N=n,percentage_total=100*n/N,percentage_accepted=None if k=='PASSENGER_REJECTED' else 100*n/accepted.sum()))
assert sum(v['N'] for v in out)==N
pd.DataFrame(out).to_csv(R/'passenger_driver_conflicts.csv',index=False)
p=pd.read_parquet('data/processed/driver_preferences_seed42.parquet');pref=p.price_preference.to_numpy();rows=[]
for b in f.P_base_USD.unique():
 ratio=pref/b;near=np.isclose(pref,.85*b,rtol=0,atol=1e-9)
 stats=dict(zip(['min','P1','P5','median','P95','P99','max'],np.quantile(pref,[0,.01,.05,.5,.95,.99,1])));ratio_stats=dict(zip(['min','P1','P5','median','P95','P99','max'],np.quantile(ratio,[0,.01,.05,.5,.95,.99,1])))
 rows.append(dict(runtime_P_base_USD=b,context_request_N=int((f.P_base_USD==b).sum()),profile_N=len(p),**{k+'_P_min_USD':v for k,v in stats.items()},mean_P_min_USD=pref.mean(),**{k+'_P_min_over_runtime_P_base':v for k,v in ratio_stats.items()},mean_P_min_over_runtime_P_base=ratio.mean(),below_085_N=int(((pref<.85*b)&~near).sum()),approximately_085_N=int(near.sum()),between_085_and_100_N=int(((pref>.85*b)&~near&(pref<b)).sum()),at_or_above_100_N=int((pref>=b).sum()),gate='P_offer_USD >= price_preference_USD',normalization_scope='All 5000 persisted drivers against the actual selected-slot runtime context; not global historical base'))
assert all(r['below_085_N']+r['approximately_085_N']+r['between_085_and_100_N']+r['at_or_above_100_N']==5000 for r in rows)
pd.DataFrame(rows).to_csv(R/'driver_preference_summary.csv',index=False)
fig,ax=plt.subplots(figsize=(8,6))
for mask,label,col in [(accepted,'Accepted','#0072B2'),(~accepted,'Rejected','#D55E00')]:ax.scatter(f.loc[mask,'P_max_USD'],f.loc[mask,'P_offer_USD'],s=12,alpha=.45,label=label,color=col)
lo=min(f.P_max_USD.min(),f.P_offer_USD.min());hi=max(f.P_max_USD.max(),f.P_offer_USD.max());ax.plot([lo,hi],[lo,hi],'k--',label='Equality');ax.set_xscale('symlog',linthresh=50);ax.set_yscale('symlog',linthresh=50);ax.set(xlabel='Passenger P_max (USD; symlog)',ylabel='Offered fare (USD; symlog)',title='Episode 25, slot 9: all requests; no clipping');ax.legend();save('offered_price_vs_pmax.png')
fig,ax=plt.subplots(figsize=(8,6))
for mask,label,col in [(accepted,'Accepted','#0072B2'),(~accepted,'Rejected','#D55E00')]:ax.scatter(f.loc[mask,'P_base_USD'],f.loc[mask,'P_max_USD'],s=12,alpha=.4,label=label,color=col)
ax.plot([base.min()*.9,base.max()*1.1],[base.min()*.9,base.max()*1.1],'k--',label='Equality');ax.set_yscale('symlog',linthresh=50);ax.set(xlabel='Contextual runtime P_base (USD)',ylabel='Passenger P_max (USD; symlog)',title='Episode 25, slot 9: contextual base versus passenger threshold');ax.legend();save('pbase_vs_pmax.png')
print(json.dumps(summary,indent=2))
