"""Reaggregate raw empirical fields within Jan-Feb; no March intermediates."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd,numpy as np
from src.pricing.binned_sensitivity import binned_elasticity,historical_pool
from src.pricing.prospective_binned_sampler import VERSION,ProspectiveBinnedSensitivity
from scripts.sensitivity_decision_analysis import summary
from src.pricing.slot_v3 import load_contract
OUT=Path('results_v2/simulation/2026-11-17_prospective_acceptance_v1')
SOURCE=Path('data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet')
GROUP=Path('results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json')
def main():
 f=pd.read_parquet(SOURCE,columns=['pickup_timestamp','distance_km','fare','weather_code','hour'],filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-01'))])
 if not ((f.pickup_timestamp>='2026-01-01')&(f.pickup_timestamp<'2026-03-01')).all():raise ValueError('Future calibration row')
 assert ((f.distance_km>=1.5)&(f.distance_km<75)).all()
 f['T_group']=np.select([f.hour<4,f.hour<6,f.hour<16],['T1','T2','T3'],default='T4')
 grouping=json.loads(GROUP.read_text());mapping={(r['raw_weather_code'],r['T_group']):r.get('time_specific_weather_group','') for r in grouping['mapping']}
 old=load_contract();conditions={};counts={};pieces=[];stats=[]
 for sid in old['conditions']:
  pool=historical_pool(f,sid,mapping);b=binned_elasticity(pool,p_base=old['P_base'],l_base=old['L_base']);b['condition']=sid;pieces.append(b)
  pos=b[b.status=='POSITIVE_ELASTICITY'];counts[sid]=int(pos.n_requests.sum())
  if pos.empty:continue
  a=pos.epsilon.to_numpy();n=pos.n_requests.to_numpy();p=dict(values=a.tolist(),request_counts=n.tolist(),probabilities=(n/n.sum()).tolist(),lower=float(a.min()),upper=float(a.max()),source_requests=len(pool),represented_requests=int(n.sum()),excluded_bin_requests=int(len(pool)-n.sum()))
  assert b.n_requests.sum()==len(pool)
  conditions[sid]=p;stats.append(dict(condition=sid,source_requests=len(pool),represented_requests=int(n.sum()),**summary(a,n)))
 pd.concat(pieces).to_csv(OUT/'conditional_distance_bins.csv',index=False);pd.DataFrame(stats).to_csv(OUT/'distribution_statistics.csv',index=False)
 last=pd.Timestamp(f.pickup_timestamp.max()).tz_localize('America/New_York')
 pop=dict(source=str(SOURCE),columns=['pickup_timestamp','distance_km','fare','weather_code','hour'],filters='2026-01-01 <= pickup_timestamp < 2026-03-01',N=len(f),latest_observation=str(last),selected_rows_sha256=hashlib.sha256(pd.util.hash_pandas_object(f,index=False).values.tobytes()).hexdigest(),excluded_derived_fields=['epsilon','is_runtime_candidate'],scope='Fixed 1.5 <= distance_km < 75; no March-fitted support or candidate flag consumed')
 pp=OUT/'population_manifest.json';pp.write_text(json.dumps(pop,indent=2)+'\n')
 provenance=dict(path=str(pp.resolve()),sha256=hashlib.sha256(pp.read_bytes()).hexdigest(),source_start='2026-01-01T00:00:00-05:00',source_end_exclusive='2026-03-01T00:00:00-05:00',latest_observation=str(last),fitting_cutoff='2026-03-01T00:00:00-05:00',methodology_version=VERSION)
 c=dict(version=VERSION,calibration_period='2026-01-01 <= pickup_timestamp < 2026-03-01',source_N=len(f),P_base=old['P_base'],L_base=old['L_base'],grouping=grouping,conditions=conditions,support_counts=counts,population_provenance=provenance,reference_status='Preserved project assumptions; not re-estimated',grouping_status='Fixed development-tuned definitions; not independently selected on Jan-Feb',fallback='Existing ordering and >=5000 support; counts now positive-bin represented Jan-Feb requests',weighting='HISTORICAL_REQUEST_COUNT',support='Inclusive min/max positive finite bin estimates only',bin_width_km=.5)
 path=OUT/'sampling_contract.json';path.write_text(json.dumps(c,indent=2,allow_nan=False)+'\n');ProspectiveBinnedSensitivity(path)
 print(json.dumps(dict(N=len(f),latest=str(last),global_statistics=next(x for x in stats if x['condition']=='GLOBAL'))))
if __name__=='__main__':main()
