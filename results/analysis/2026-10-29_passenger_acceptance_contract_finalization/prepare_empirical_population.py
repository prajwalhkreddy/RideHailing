from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
from src.pricing.empirical_sensitivity import EmpiricalCustomerSensitivityModel
R=Path.cwd();O=R/'results/analysis/2026-10-29_passenger_acceptance_contract_finalization';O.mkdir(exist_ok=True)
meta=json.loads((R/'data/processed/customer_price_sensitivity_2026_01_metadata.json').read_text());start=pd.Timestamp(meta['training_start_inclusive']);end=pd.Timestamp(meta['training_cutoff_exclusive'])
x=pd.read_parquet(R/meta['source_trip_artifact'],columns=['tpep_pickup_datetime','fare_amount','trip_distance'],filters=[('tpep_pickup_datetime','>=',start),('tpep_pickup_datetime','<',end)])
w=pd.read_parquet(R/meta['weather_time_lookup_artifact'],columns=['TimeSlot','WeatherCode','Period'],filters=[('TimeSlot','>=',start),('TimeSlot','<',end)]).drop_duplicates()
x['TimeSlot']=x.tpep_pickup_datetime.dt.floor('30min');x=x.merge(w,on='TimeSlot',how='left',validate='many_to_one');v=np.isfinite(x[['fare_amount','trip_distance','WeatherCode','Period']]).all(axis=1)&(x.fare_amount>0)&x.trip_distance.gt(0)&x.trip_distance.le(100)&x.Period.between(0,47)&(x.Period%1==0);x=x[v].copy();assert len(x)==2812236
bases=pd.read_parquet(R/meta['output_artifact'])[['WeatherCode','Period','P_base','D_base']];x=x.merge(bases,on=['WeatherCode','Period'],validate='many_to_one')
x['epsilon_abs']=abs(((x.trip_distance-x.D_base)/x.D_base)/((x.fare_amount-x.P_base)/x.P_base))
p=R/'data/processed/passenger_empirical_absolute_epsilon_2026_01.parquet';x.to_parquet(p,index=False)
p.with_suffix('.json').write_text(json.dumps(dict(training_start_inclusive=str(start),training_cutoff_exclusive=str(end),source_N=len(x),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),epsilon='abs(Delta_D/Delta_P)',method='EMPIRICAL_WITH_REPLACEMENT',fallback='exact -> period -> weather -> global; broader bases recomputed within each broader population',source_metadata=meta),indent=2)+'\n')
m=EmpiricalCustomerSensitivityModel(x,np.random.default_rng(42))
exact=[(k,a) for k,a in m.pools.items() if k[0]=='exact'];hist=np.concatenate([a for k,a in exact]);old=json.loads((R/'results/analysis/2026-10-29_passenger_epsilon_support_analysis/epsilon_distribution.json').read_text());assert len(hist)==old['N'] and hist.min()==old['min_positive'];assert np.isclose(hist.mean(),old['mean'])
# Sampling strata weighted by historical row counts, independent diagnostic RNG.
counts=np.random.default_rng(42).multinomial(1000000,np.array([len(a) for k,a in exact])/len(hist));samples=[]
for (k,pool),n in zip(exact,counts):
 sample=np.array([m.sample_epsilon(k[1],k[2]) for _ in range(n)])
 assert np.isin(sample,pool).all();samples.append(sample)
sample=np.concatenate(samples)
def stats(a):return dict(N=len(a),mean=float(a.mean()),median=float(np.median(a)),SD_population=float(a.std()),min=float(a.min()),max=float(a.max()),**{f'P{q}':float(np.quantile(a,q/100)) for q in [.1,.5,1,5,25,75,95,99]})
def save(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
save('distribution_fidelity.json',dict(historical=stats(hist),sampled=stats(sample),seed=42,weighting='Exact contexts weighted by their historical sampling-pool counts; multinomial diagnostic context allocation; one million runtime sampler draws.',support_membership='PASS all draws in resolved pool',below_support=0,interpretation='Finite bootstrap mean/SD may vary substantially because rare empirical extremes are retained; no lower-SD pass criterion.'))
save('empirical_sampler_validation.json',dict(source_N=len(x),exact_N=len(hist),exact_contexts=len(exact),support=[float(hist.min()),float(hist.max())],excluded_by_context=[dict(level=k[0],weather=k[1],period=k[2],**v) for k,v in m.exclusions.items()],old_analysis_reproduced=True,zero_floor=False,duplicate_frequency_preserved=True))
print(json.dumps(dict(N=len(hist),support=[hist.min(),hist.max()],historical=stats(hist),sampled=stats(sample))))
