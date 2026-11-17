"""Bounded completion using persisted bin evidence; no model training."""
import json,sys,hashlib,warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pricing.slot_v3 import FittedSensitivity
from src.pricing.binned_sampler import VERSION
BASE=ROOT/'results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review'
OUT=BASE/'provisional_sampling';OUT.mkdir(exist_ok=True)
f=pd.read_csv(BASE/'final_validation/conditional_distance_bins.csv')
old=FittedSensitivity();conditions={};fits=[]
for sid,g in f.groupby('historical_condition'):
 a=g.loc[g.status=='POSITIVE_ELASTICITY','epsilon'].to_numpy();lo,hi=float(a.min()),float(a.max())
 conditions[sid]=dict(values=a.tolist(),lower=lo,upper=hi,positive_bins=len(a),nonpositive_or_undefined_bins=len(g)-len(a),source_requests=int(g.n_requests.sum()))
 # One bounded fit/family/pool; diagnostics are in-sample, never held-out claims.
 for name,dist in [('lognormal',stats.lognorm),('generalized_gamma',stats.gengamma),('normal_truncated_to_empirical_support',stats.norm),('exponential',stats.expon)]:
  try:
   with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    params=dist.fit(a,floc=0) if name in {'lognormal','generalized_gamma','exponential'} else dist.fit(a)
   lower,upper=dist.cdf([lo,hi],*params);mass=upper-lower
   if not np.isfinite(mass) or mass<=0:raise ValueError('No finite support mass')
   cdf=lambda x:np.clip((dist.cdf(x,*params)-lower)/mass,0,1)
   ks=stats.kstest(a,cdf).statistic
   loglik=float(np.sum(dist.logpdf(a,*params)-np.log(mass)))
   fits.append(dict(condition=sid,family=name,N=len(a),mean=a.mean(),SD=a.std(),minimum=lo,maximum=hi,parameters=json.dumps(list(params)),support_lower=lo,support_upper=hi,KS=ks,log_likelihood=loglik,status='IN_SAMPLE_DIAGNOSTIC'))
  except Exception as e:fits.append(dict(condition=sid,family=name,N=len(a),status=str(e)))
pd.DataFrame(fits).to_csv(OUT/'bounded_family_comparison.csv',index=False)
c=dict(version=VERSION,status='PROVISIONAL_OPT_IN',final_master_compliance=False,P_base=old.contract['P_base'],L_base=old.contract['L_base'],distance_unit='km',grouping=old.grouping,historical_support_counts={k:int(v) for k,v in old.counts.items()},conditions=conditions,
 observation_unit='One bin elasticity per occupied bin; equal empirical bin probability, duplicates retained',
 support_rule='Positive finite bin estimates; inclusive empirical minimum/maximum per pool. No magnitude transform or extra near-zero floor.',
 exclusions='Negative/zero/nonfinite estimates retained in diagnostic CSV; excluded only from positive sampler, no trip deletion.',
 reference_status='Existing references retained provisionally; master reference selection not resolved',
 open_decisions=['Continuous Temperature/WindSpeed conditioning','Final reference construction','Final distribution selection and bin-estimate weighting approval'],
 fallback='Existing historical >=5000 trip-candidate support rule and ordering; not evidence of 5000 independent bin estimates',
 calibration_period='2026-01-01 <= pickup_timestamp < 2026-03-16',seed=42)
(OUT/'sampling_contract.json').write_text(json.dumps(c,indent=2,allow_nan=False)+'\n')
# Inspect only eligible-period weather and calibration timestamps; no protected evaluation rows.
wpath=ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet'
w=pd.read_parquet(wpath,columns=['TimeSlot','Temperature','WindSpeed','WeatherCode'],filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-03-16'))])
conflicts=w.groupby('TimeSlot')[['Temperature','WindSpeed','WeatherCode']].nunique(dropna=False).max().to_dict()
w=w.drop_duplicates('TimeSlot').set_index('TimeSlot')
pop=pd.read_parquet(ROOT/'data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet',columns=['pickup_timestamp','weather_code'])
x=w.reindex(pop.pickup_timestamp.dt.floor('30min'))
coverage=dict(period=c['calibration_period'],slots=len(w),expected_slots=3552,source=str(wpath.relative_to(ROOT)),within_slot_unique_max={k:int(v) for k,v in conflicts.items()},population_N=len(pop),finite_temperature_N=int(np.isfinite(x.Temperature).sum()),finite_windspeed_N=int(np.isfinite(x.WindSpeed).sum()),weather_code_mismatch_N=int((x.WeatherCode.to_numpy()!=pop.weather_code.to_numpy()).sum()),temperature_min=float(w.Temperature.min()),temperature_max=float(w.Temperature.max()),windspeed_min=float(w.WindSpeed.min()),windspeed_max=float(w.WindSpeed.max()),units='Meteostat metric defaults: Temperature Celsius; WindSpeed km/h; see installed Meteostat source evidence',coverage_caveat='Processed coverage includes existing forward/backward filling; not original observation completeness',decision='OPEN_METHODOLOGICAL_DECISION',potential_approaches='Conditional regression or validated stratification could be evaluated separately; neither selected or implemented.')
(OUT/'continuous_weather_availability.json').write_text(json.dumps(coverage,indent=2)+'\n')
print(json.dumps(dict(pools=len(conditions),family_rows=len(fits),weather=coverage)))
