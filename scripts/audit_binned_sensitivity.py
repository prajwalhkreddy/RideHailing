"""Bounded provisional estimator evidence; no fitting or runtime activation."""
import sys,json,hashlib,subprocess,io,unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pricing.binned_sensitivity import binned_elasticity,VERSION,historical_pool
OUT=ROOT/'results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/final_validation'
POP=ROOT/'data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet'
OLD=ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/methodology_contract.json'
GROUP=ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json'
COUNTS=ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_manifest.csv'

def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def stats(values):
 a=np.asarray(values,float);a=a[np.isfinite(a)]
 if not len(a):return {'N':0}
 q=np.quantile(a,[.005,.05,.5,.95,.995])
 return dict(N=len(a),mean=float(a.mean()),SD=float(a.std()),minimum=float(a.min()),maximum=float(a.max()),**dict(zip(['P005','P05','median','P95','P995'],map(float,q))))

def clean_json(x):
 if isinstance(x,dict):return {k:clean_json(v) for k,v in x.items()}
 if isinstance(x,list):return [clean_json(v) for v in x]
 if isinstance(x,float) and not np.isfinite(x):return str(x)
 return x

def main():
 if OUT.exists():raise FileExistsError(OUT)
 OUT.mkdir(parents=True)
 old=json.loads(OLD.read_text());group=json.loads(GROUP.read_text());p,l=old['P_base'],old['L_base']
 columns=['pickup_timestamp','fare','distance_km','weather_code','hour','epsilon','is_runtime_candidate']
 f=pd.read_parquet(POP,columns=columns)
 if not ((f.pickup_timestamp>='2026-01-01')&(f.pickup_timestamp<'2026-03-16')).all():raise ValueError('Calibration boundary violation')
 if not ((f.distance_km>=1.5)&(f.distance_km<75)).all():raise ValueError('Scope mismatch')
 f['T_group']=np.select([f.hour<4,f.hour<6,f.hour<16],['T1','T2','T3'],default='T4')
 counts=pd.read_csv(COUNTS).set_index('support_id').N.to_dict()
 mapping={(r['raw_weather_code'],r['T_group']):r.get('time_specific_weather_group','') for r in group['mapping']}
 assignment={}
 for code,T in f[['weather_code','T_group']].drop_duplicates().itertuples(index=False,name=None):
  candidates=[mapping.get((code,T),'')]+(['RAW_'+str(int(code))] if T=='T1' else [])+[T+'_POOLED','GLOBAL']
  assignment[(code,T)]=next(s for s in candidates if s and counts.get(s,0)>=5000)
 f['historical_condition']=[assignment[k] for k in zip(f.weather_code,f.T_group)]
 pools={sid:historical_pool(f,sid,mapping) for sid in old['conditions']}
 pieces=[]
 for sid,g in pools.items():
  piece=binned_elasticity(g,p_base=p,l_base=l);piece.insert(0,'historical_condition',sid);pieces.append(piece)
 bins=pd.concat(pieces,ignore_index=True)
 global_bins=binned_elasticity(f,p_base=p,l_base=l)
 bins.to_csv(OUT/'conditional_distance_bins.csv',index=False);global_bins.to_csv(OUT/'global_distance_bins.csv',index=False)
 support=f.groupby(['weather_code','T_group','historical_condition']).size().rename('N').reset_index()
 support['population_percentage']=100*support.N/len(f);support.to_csv(OUT/'conditional_population_support.csv',index=False)
 summary=[]
 for sid,g in pools.items():
  if int(g.is_runtime_candidate.sum())!=int(counts[sid]):raise ValueError('Historical pool support mismatch: '+sid)
  b=bins[bins.historical_condition==sid];positive=b[b.epsilon>0]
  summary.append(dict(condition=sid,source_N=len(g),overlapping_pool_percentage=100*len(g)/len(f),assigned_request_N=int((f.historical_condition==sid).sum()),occupied_bins=len(b),positive_bins=len(positive),negative_bins=int((b.epsilon<0).sum()),zero_bins=int((b.epsilon==0).sum()),undefined_bins=int(b.epsilon.isna().sum()),near_zero_price_bins_diagnostic=int((b.relative_price_deviation.abs()<.05).sum()),old_runtime_candidate_N=int(g.is_runtime_candidate.sum()),**{'bin_'+k:v for k,v in stats(b.epsilon).items()},weighted_positive_bin_mean=float(np.average(positive.epsilon,weights=positive.n_requests)) if len(positive) else None))
 pd.DataFrame(summary).to_csv(OUT/'conditional_estimator_summary.csv',index=False)
 comparison=[dict(estimator='EXISTING_TRIP_LEVEL_5PCT_POSITIVE',source_N=len(f),**stats(f.loc[f.is_runtime_candidate,'epsilon'])),dict(estimator='NEW_SIGNED_BIN_LEVEL_EXACT_DENOMINATOR',source_N=len(f),**stats(global_bins.epsilon)),dict(estimator='NEW_POSITIVE_BIN_DIAGNOSTIC_NOT_SELECTED',source_N=len(f),**stats(global_bins.loc[global_bins.epsilon>0,'epsilon']))]
 pd.DataFrame(comparison).to_csv(OUT/'estimator_comparison.csv',index=False)
 # Descriptive empirical integration, not a selected sampling distribution.
 acceptance=[]
 for name,eps in [('existing_trip_positive',f.loc[f.is_runtime_candidate,'epsilon'].to_numpy()),('positive_bins_equal_weight_diagnostic',global_bins.loc[global_bins.epsilon>0,'epsilon'].to_numpy())]:
  eps=eps[np.isfinite(eps)&(eps>0)]
  for distance in [1.5,l,10.]:
   ceiling=p+(p/eps)*((distance-l)/l)
   for price in [6.6,p,94.7]:acceptance.append(dict(estimator=name,distance_km=distance,price_USD=price,acceptance_fraction=float(np.mean(price<=ceiling)),N=len(eps),status='DESCRIPTIVE_NOT_A_RUNTIME_MODEL'))
 pd.DataFrame(acceptance).to_csv(OUT/'fixed_offer_acceptance_diagnostic.csv',index=False)
 (OUT/'historical_fit_reference.json').write_text(json.dumps(clean_json(dict(source=str(OLD),conditions=old['conditions'],reuse_status='CANDIDATE_FAMILIES_ONLY_PARAMETERS_NOT_TRANSFERABLE_TO_BIN_ESTIMATES')),indent=2))
 # Bounded permitted-date coverage, no protected observations.
 source=ROOT/'data/processed/spatial_3km_jan_mar_2026/trips_jan_mar_2026.parquet'
 z=pd.read_parquet(source,columns=['tpep_pickup_datetime','tpep_dropoff_datetime','trip_distance','fare_amount','PUGridID','DOGridID'],filters=[('tpep_pickup_datetime','>=',pd.Timestamp('2026-03-01')),('tpep_pickup_datetime','<',pd.Timestamp('2026-03-17'))])
 duration=(z.tpep_dropoff_datetime-z.tpep_pickup_datetime).dt.total_seconds()
 eligible=np.isfinite(z[['trip_distance','fare_amount']]).all(axis=1)&np.isfinite(duration)&(duration>0)&(z.trip_distance>=0)&(z.fare_amount>=0)
 grid=z[['PUGridID','DOGridID']];valid=np.isfinite(grid).all(axis=1)&(grid>=0).all(axis=1)&(grid<142).all(axis=1)&(grid==np.floor(grid)).all(axis=1)
 known=json.loads((ROOT/'results_v2/pricing_dqn/2026-11-17_feasible_od_validation/od_feasibility.json').read_text())
 codes=set(o*142+d for o,d,n in known['pair_counts']);supported=(z.PUGridID*142+z.DOGridID).isin(codes)
 z['eligible']=eligible;z['invalid_spatial']=eligible&~valid;z['unseen_valid']=eligible&valid&~supported;z['date']=z.tpep_pickup_datetime.dt.strftime('%Y-%m-%d')
 coverage=z.groupby('date').agg(source_N=('eligible','size'),eligible_N=('eligible','sum'),invalid_spatial_N=('invalid_spatial','sum'),unseen_valid_N=('unseen_valid','sum')).reset_index()
 coverage['unseen_percentage_of_eligible']=100*coverage.unseen_valid_N/coverage.eligible_N
 coverage.to_csv(OUT/'od_coverage_by_date.csv',index=False)
 unseen=z.loc[z.unseen_valid].groupby(['PUGridID','DOGridID']).size().rename('affected_requests').reset_index();unseen.to_csv(OUT/'unseen_valid_od_pairs.csv',index=False)
 coverage_summary=dict(start='2026-03-01',end_exclusive='2026-03-17',source_N=len(z),eligible_N=int(eligible.sum()),geographically_invalid_N=int((eligible&~valid).sum()),unseen_valid_pairs=len(unseen),unseen_valid_requests=int(z.unseen_valid.sum()),unseen_percentage=float(100*z.unseen_valid.sum()/eligible.sum()))
 contract=dict(version=VERSION,runtime_approved=False,status='BLOCKED_PENDING_CONDITIONING_DECISION',P_base=p,L_base_km=l,reference_status='PROVISIONAL_UNCHANGED',bin_width_km=.5,bin_origin_km=0,bin_convention='LEFT_CLOSED_RIGHT_OPEN_LOWER_LIMIT',denominator='exact zero undefined; near-zero values retained for diagnostic only',distribution_weighting='NOT_FROZEN_EQUAL_BIN_AND_REQUEST_WEIGHTED_DIAGNOSTICS',source_N=len(f),calibration_start='2026-01-01',calibration_end_exclusive='2026-03-16',blockers=['CNN Temperature/WindSpeed conditioning not defined for sensitivity','Binned support/sign/near-zero and sparse-bin fit eligibility need reconciliation before runtime promotion'],historical_runtime_unchanged=True)
 (OUT/'calibration_contract.json').write_text(json.dumps(contract,indent=2))
 log=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_binned_sensitivity','tests.test_dispatch_reward','tests.test_slot_pricing_v3','tests.test_od_pricing','tests.test_historical_request_replay'])
 tests=unittest.TextTestRunner(stream=log,verbosity=1).run(suite);(OUT/'test_results.txt').write_text(log.getvalue())
 report=dict(contract=contract,od_coverage=coverage_summary,comparison=comparison,conditional_population_fraction_sum=float(support.population_percentage.sum()),conditional_groups=len(summary),observed_weather_time_combinations=len(support),tests=dict(run=tests.testsRun,failures=len(tests.failures),errors=len(tests.errors)),git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),git_dirty_state=subprocess.check_output(['git','status','--porcelain'],text=True),seed=42,source_hashes={str(x.relative_to(ROOT)):digest(x) for x in [POP,OLD,GROUP,ROOT/'src/pricing/binned_sensitivity.py',Path(__file__).resolve(),ROOT/'tests/test_binned_sensitivity.py',ROOT/'data/processed/cnn_jan_mar_2026_3km_30min/feature_specification.json']})
 (OUT/'validation.json').write_text(json.dumps(clean_json(report),indent=2));print(json.dumps(dict(coverage=coverage_summary,comparison=comparison,tests=report['tests'])))
 return 0 if tests.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
