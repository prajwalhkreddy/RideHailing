"""Offline bounded decision evidence; never writes runtime contracts."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pricing.binned_sensitivity import binned_elasticity,historical_pool
from src.pricing.slot_v3 import FittedSensitivity,pmax
BASE=ROOT/'results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review'
OUT=ROOT/'results_v2/passenger_sensitivity/2026-11-17_methodology_decision'
POP=ROOT/'data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet'

def weights(counts):
 a=np.asarray(counts,float)
 if not len(a) or not np.isfinite(a).all() or (a<0).any() or a.sum()<=0:raise ValueError('Invalid weights')
 return a/a.sum()

def summary(a,w):
 a=np.asarray(a,float);w=weights(w)
 if not np.isfinite(a).all() or (a<=0).any():raise ValueError('Positive finite empirical support required')
 order=np.argsort(a,kind='stable');x=a[order];cdf=np.cumsum(w[order]);cdf[-1]=1
 q=x[np.searchsorted(cdf,[.005,.05,.25,.5,.75,.95,.995])]
 m=float(w@a)
 return dict(mean=m,SD=float(np.sqrt(w@((a-m)**2))),minimum=float(x[0]),maximum=float(x[-1]),**dict(zip(['P005','P05','P25','median','P75','P95','P995'],map(float,q))))

def acceptance(a,w,d,p,pbase,lbase):
 a=np.asarray(a,float)
 if not np.isfinite(a).all() or (a<=0).any():raise ValueError('Invalid epsilon')
 ceiling=pbase+(pbase/a)*((d-lbase)/lbase)
 if not np.isfinite(ceiling).all():raise ValueError('Nonfinite ceiling')
 weights(w)  # validate before computing the ratio of accepted to total mass
 mass=np.asarray(w,float)
 return float(mass[p<=ceiling].sum()/mass.sum())

def boundary(f):
 if not ((f.pickup_timestamp>=pd.Timestamp('2026-01-01'))&(f.pickup_timestamp<pd.Timestamp('2026-03-16'))).all():raise ValueError('Protected/out-of-scope timestamp')

def main():
 OUT.mkdir(exist_ok=True)
 old=FittedSensitivity();p,l=old.contract['P_base'],old.contract['L_base']
 bins=pd.read_csv(BASE/'final_validation/conditional_distance_bins.csv')
 bins.to_csv(OUT/'bin_request_counts.csv',index=False)
 comparison=[];acc=[]
 for sid,g in bins.groupby('historical_condition'):
  pos=g[g.epsilon>0]
  for name,w in [('uniform_bins',np.ones(len(pos))),('request_count_weighted_bins',pos.n_requests.to_numpy())]:
   comparison.append(dict(condition=sid,weighting=name,positive_bins=len(pos),source_requests=int(g.n_requests.sum()),represented_positive_requests=int(pos.n_requests.sum()),excluded_bin_requests=int(g.n_requests.sum()-pos.n_requests.sum()),effective_bin_N=float(1/(weights(w)**2).sum()),**summary(pos.epsilon,w)))
   for d in [1.5,3.,l,10.,30.]:
    for factor in old.contract['actions']:
     acc.append(dict(condition=sid,method=name,distance_km=d,factor=factor,price_USD=factor*p,acceptance=acceptance(pos.epsilon,w,d,factor*p,p,l)))
  # Fixed inverse-CDF midpoint integration of the existing historical fitted distribution.
  draws=old.distribution(sid).ppf((np.arange(4096)+.5)/4096)
  for d in [1.5,3.,l,10.,30.]:
   for factor in old.contract['actions']:
    acc.append(dict(condition=sid,method='historical_fitted_4096_midpoint',distance_km=d,factor=factor,price_USD=factor*p,acceptance=acceptance(draws,np.ones(len(draws)),d,factor*p,p,l)))
 pd.DataFrame(comparison).to_csv(OUT/'weighting_comparison.csv',index=False)
 # One eligible-population read is necessary for weather-slot evidence and temporal reaggregation.
 f=pd.read_parquet(POP,columns=['pickup_timestamp','distance_km','fare','weather_code','hour','epsilon','is_runtime_candidate']);boundary(f)
 f['T_group']=np.select([f.hour<4,f.hour<6,f.hour<16],['T1','T2','T3'],default='T4')
 f['weather_slot']=f.pickup_timestamp.dt.floor('h')
 mapping={(r['raw_weather_code'],r['T_group']):r.get('time_specific_weather_group','') for r in old.grouping['mapping']}
 assignments={}
 for code,T in f[['weather_code','T_group']].drop_duplicates().itertuples(index=False,name=None):
  opts=[mapping.get((code,T),'')]+(['RAW_'+str(int(code))] if T=='T1' else [])+[T+'_POOLED','GLOBAL']
  assignments[code,T]=next(s for s in opts if s and old.counts.get(s,0)>=5000)
 f['assigned_condition']=[assignments[x] for x in zip(f.weather_code,f.T_group)]
 assigned=f.groupby('assigned_condition').size().rename('N').reset_index();assigned['fraction']=assigned.N/len(f);assert np.isclose(assigned.fraction.sum(),1)
 assigned.to_csv(OUT/'assigned_population_proportions.csv',index=False)
 # Historical trip-level acceptance via sorted arrays, exact empirical counts, no resampling.
 for sid in old.contract['conditions']:
  pool=historical_pool(f,sid,mapping);a=np.sort(pool.loc[pool.is_runtime_candidate,'epsilon'].to_numpy())
  for d in [1.5,3.,l,10.,30.]:
   for factor in old.contract['actions']:
    # vectorized empirical integration: bounded number of conditions, no simulation
    value=acceptance(a,np.ones(len(a)),d,factor*p,p,l)
    acc.append(dict(condition=sid,method='historical_positive_trip',distance_km=d,factor=factor,price_USD=factor*p,acceptance=value))
 pd.DataFrame(acc).to_csv(OUT/'acceptance_impact.csv',index=False)
 # Reference nearest observed fare is only conditional on retaining the previous selected base target.
 fares=np.sort(f.fare.unique());near=float(fares[np.argmin(abs(fares-p))])
 global_bins=bins[bins.historical_condition=='GLOBAL'].copy()
 alt=((global_bins.bin_lower_km-l)/l)/((global_bins.mean_fare-near)/near)
 ref=dict(existing_P_base=p,existing_L_base_km=l,existing_derivation='Pbase weighted mean on prior [1,75)km scope; Lbase interpolated mean-fare crossing',master_derivation='Observed fare nearest selected base fare; mean of selected representative distances near selected base distance',equivalent=False,full_faithful_alternative_computable=False,missing_choices=['Selected base fare/distance targets','Representative distance selection/nearness rule'],conditional_nearest_observed_fare=near,conditional_nearest_fare_support=int((f.fare==near).sum()),conditional_P_delta=near-p,conditional_L_unchanged=l,conditional_max_abs_bin_epsilon_change=float(abs(alt-global_bins.epsilon).max()),conditional_mean_bin_epsilon_change=float((alt-global_bins.epsilon).mean()),warning='One-component diagnostic, not a fully master-selected reference pair; no references replaced')
 (OUT/'reference_comparison.json').write_text(json.dumps(ref,indent=2)+'\n')
 w=pd.read_parquet(ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet',columns=['TimeSlot','Temperature','WindSpeed','WeatherCode'],filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-03-16'))])
 w['weather_slot']=w.TimeSlot.dt.floor('h');w=w.groupby('weather_slot')[['Temperature','WindSpeed','WeatherCode']].first()
 # Weather-hour x distance-bin means; each weather hour is one diagnostic observation.
 sb=binned_elasticity(f,p_base=p,l_base=l,group_columns=['weather_slot','assigned_condition'])
 sp=sb[sb.epsilon>0]
 hourly=sp.groupby(['weather_slot','assigned_condition']).agg(median_positive_bin_epsilon=('epsilon','median'),positive_bins=('epsilon','size')).reset_index().merge(w,on='weather_slot',how='left')
 detail=f.groupby(['weather_slot','assigned_condition']).agg(requests=('fare','size'),mean_distance_km=('distance_km','mean')).reset_index()
 hourly=hourly.merge(detail,on=['weather_slot','assigned_condition']);assert not hourly[['Temperature','WindSpeed']].isna().any().any()
 hourly.to_csv(OUT/'hourly_weather_evidence.csv',index=False)
 gs=[]
 for sid,g in hourly.groupby('assigned_condition'):
  gs.append(dict(condition=sid,hours=len(g),distinct_dates=g.weather_slot.dt.date.nunique(),train_hours=int((g.weather_slot<'2026-03-01').sum()),validation_hours=int((g.weather_slot>='2026-03-01').sum()),requests=int(g.requests.sum()),temperature_min=g.Temperature.min(),temperature_max=g.Temperature.max(),temperature_SD=g.Temperature.std(ddof=0),wind_min=g.WindSpeed.min(),wind_max=g.WindSpeed.max(),wind_SD=g.WindSpeed.std(ddof=0),temperature_outcome_spearman=g.Temperature.corr(g.median_positive_bin_epsilon,method='spearman'),wind_outcome_spearman=g.WindSpeed.corr(g.median_positive_bin_epsilon,method='spearman'),median_positive_bins=g.positive_bins.median()))
 pd.DataFrame(gs).to_csv(OUT/'conditional_weather_support.csv',index=False)
 # Continuous OLS association probe only; not a sensitivity sampling model.
 tr=hourly.weather_slot<'2026-03-01';te=~tr
 group=pd.get_dummies(hourly.assigned_condition,dtype=float)
 supported=group.columns[(group.loc[tr].sum()>0)]
 usable=hourly.assigned_condition.isin(supported);te=te&usable
 G=group[supported].to_numpy(dtype=float);y=hourly.median_positive_bin_epsilon.to_numpy(dtype=float)
 regression=[]
 for control in [False,True]:
  X=G
  if control:X=np.column_stack([X,hourly.mean_distance_km])
  for continuous in [False,True]:
   design=np.column_stack([X,hourly[['Temperature','WindSpeed']]]) if continuous else X
   design=np.asarray(design,dtype=float)
   coef=np.linalg.lstsq(design[tr],y[tr],rcond=None)[0];pred=design@coef;err=pred[te]-y[te]
   regression.append(dict(distance_composition_control=control,continuous_weather=continuous,train_hours=int(tr.sum()),validation_hours=int(te.sum()),MAE=float(abs(err).mean()),RMSE=float(np.sqrt((err**2).mean())),temperature_coefficient=float(coef[-2]) if continuous else None,wind_coefficient=float(coef[-1]) if continuous else None,negative_predictions=int((pred[te]<0).sum())))
 pd.DataFrame(regression).to_csv(OUT/'temporal_weather_association.csv',index=False)
 # Temporal bin stability: no new family tuning. Existing fits use all dates, thus not held-out.
 temporal=[]
 for sid in old.contract['conditions']:
  pool=historical_pool(f,sid,mapping)
  b1=binned_elasticity(pool[pool.pickup_timestamp<'2026-03-01'],p_base=p,l_base=l)
  b2=binned_elasticity(pool[pool.pickup_timestamp>='2026-03-01'],p_base=p,l_base=l)
  a=b1.loc[b1.epsilon>0,'epsilon'].to_numpy();b=b2.loc[b2.epsilon>0,'epsilon'].to_numpy()
  temporal.append(dict(condition=sid,train_positive_bins=len(a),validation_positive_bins=len(b),train_requests=int(b1.n_requests.sum()),validation_requests=int(b2.n_requests.sum()),KS_train_validation=stats.ks_2samp(a,b).statistic if len(a) and len(b) else None,validation_outside_train_support_pct=float(100*((b<a.min())|(b>a.max())).mean()) if len(a) and len(b) else None,train_mean=float(a.mean()) if len(a) else None,validation_mean=float(b.mean()) if len(b) else None,status='TEMPORAL_STABILITY_NOT_HELDOUT_FAMILY_SELECTION'))
 pd.DataFrame(temporal).to_csv(OUT/'temporal_distribution_stability.csv',index=False)
 fits=pd.read_csv(BASE/'provisional_sampling/bounded_family_comparison.csv')
 fits['KS_rank_within_pool']=fits.groupby('condition').KS.rank(method='min');fits['evaluation_limitation']='Equal-bin ordinary fit then truncation; full-period in-sample, no held-out family validation'
 fits.to_csv(OUT/'distribution_fit_summary.csv',index=False)
 weather=dict(N=len(f),hours=int(hourly.weather_slot.nunique()),units=dict(Temperature='Celsius',WindSpeed='km/h'),processed_finite_coverage='100%; prior fill retained',observed_not_forecast=True,decision_time_availability_verified=False,temporal_split='Train Jan1-Feb28; validation Mar1-Mar15',outcome='Median positive hourly bin elasticity; descriptive noisy aggregation, not individual latent sensitivity',group_temperature_explained_variance=float(1-hourly.groupby('assigned_condition').Temperature.transform(lambda x:x-x.mean()).var(ddof=0)/hourly.Temperature.var(ddof=0)),group_wind_explained_variance=float(1-hourly.groupby('assigned_condition').WindSpeed.transform(lambda x:x-x.mean()).var(ddof=0)/hourly.WindSpeed.var(ddof=0)),temperature_wind_correlation=float(hourly.Temperature.corr(hourly.WindSpeed)),independence_caveat='1776 hours at most, serially correlated weather; trips/grids are not independent weather replicates; no p-values')
 hourly['T_group']=np.select([hourly.weather_slot.dt.hour<4,hourly.weather_slot.dt.hour<6,hourly.weather_slot.dt.hour<16],['T1','T2','T3'],default='T4')
 for group_name in ['WeatherCode','T_group']:
  for feature in ['Temperature','WindSpeed']:
   weather[group_name+'_'+feature+'_explained_variance']=float(1-hourly.groupby(group_name)[feature].transform(lambda x:x-x.mean()).var(ddof=0)/hourly[feature].var(ddof=0))
 weather['no_eligible_outcome_hours']=[str(t) for t in pd.date_range('2026-01-01','2026-03-15 23:00',freq='h').difference(hourly.weather_slot)]
 weather['validation_hours_excluded_unseen_condition']=int((~tr & ~usable).sum())
 (OUT/'weather_evidence.json').write_text(json.dumps(weather,indent=2)+'\n')
 config=dict(seed='No stochastic draws; deterministic midpoint quadrature for historical fits',population=str(POP.relative_to(ROOT)),N=len(f),period='Jan1-Mar15 inclusive',bin_width_km=.5,P_base=p,L_base_km=l,weights='Uniform or normalized positive-bin request counts, comparison only',quantiles='Inverse discrete CDF (first cumulative weight >= probability)',production_modified=False,protected_period_read=False,new_conditional_model_implemented=False)
 (OUT/'configuration.json').write_text(json.dumps(config,indent=2)+'\n')
 print(json.dumps(dict(reference=ref,weather=weather,association=regression),indent=2))
if __name__=='__main__':main()
