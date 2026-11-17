"""Build a versioned weighted contract exclusively from saved calibration bins."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pricing.weighted_binned_sampler import VERSION,WeightedBinnedSensitivity
from scripts.sensitivity_decision_analysis import summary
BASE=ROOT/'results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review'
OUT=ROOT/'results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration'

def main():
 OUT.mkdir(exist_ok=True)
 contract=json.loads((BASE/'provisional_sampling/sampling_contract.json').read_text())
 bins=pd.read_csv(BASE/'final_validation/conditional_distance_bins.csv')
 contract.update(version=VERSION,weighting='HISTORICAL_REQUEST_COUNT',source_N=6967155,decision='PROJECT_METHODOLOGY_DECISION',observation_unit='Bin elasticity with probability proportional to eligible historical request count; represents observed trip-distance mixture, not identified individual heterogeneity',open_decisions=['Final reference construction','Continuous-weather feature alignment and decision-time availability','Empirical tail/support adequacy'],seed=42)
 rows=[]
 for sid,g in bins.groupby('historical_condition'):
  pos=g[g.status=='POSITIVE_ELASTICITY'];n=pos.n_requests.to_numpy(dtype=np.int64);a=pos.epsilon.to_numpy(float)
  assert int(g.n_requests.sum())==contract['conditions'][sid]['source_requests']
  pool=contract['conditions'][sid]
  pool.update(values=a.tolist(),bin_lower_km=pos.bin_lower_km.tolist(),request_counts=n.tolist(),probabilities=(n/n.sum()).tolist(),represented_requests=int(n.sum()),excluded_bin_requests=int(g.n_requests.sum()-n.sum()))
  rows.append(dict(condition=sid,source_requests=pool['source_requests'],represented_requests=pool['represented_requests'],excluded_bin_requests=pool['excluded_bin_requests'],positive_bins=len(a),weight_sum=float(sum(pool['probabilities'])),**summary(a,n)))
 g=next(x for x in rows if x['condition']=='GLOBAL')
 assert g['source_requests']==6967155 and g['represented_requests']==6967155
 expected=pd.read_csv(ROOT/'results_v2/passenger_sensitivity/2026-11-17_methodology_decision/weighting_comparison.csv')
 for r in rows:
  ref=expected[(expected.condition==r['condition'])&(expected.weighting=='request_count_weighted_bins')].iloc[0]
  assert np.isclose(r['mean'],ref['mean'],rtol=0,atol=1e-12) and np.isclose(r['SD'],ref.SD,rtol=0,atol=1e-12)
 contract['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'final_validation/conditional_distance_bins.csv',BASE/'provisional_sampling/sampling_contract.json',ROOT/'results_v2/passenger_sensitivity/2026-11-17_methodology_decision/weighting_comparison.csv']}
 contract['support_limitation']='January-February versus March1-15 support exceedance remains diagnostic; no bounds widened using held-out bins. This contract reuses the explicitly authorized Jan1-Mar15 calibration population, not a train-only evaluation model.'
 (OUT/'sampling_contract.json').write_text(json.dumps(contract,indent=2,allow_nan=False)+'\n')
 for row in rows:row['variance']=row['SD']**2
 pd.DataFrame(rows).to_csv(OUT/'distribution_statistics.csv',index=False)
 temporal=pd.read_csv(ROOT/'results_v2/passenger_sensitivity/2026-11-17_methodology_decision/temporal_distribution_stability.csv')
 temporal['boundary_adjustment']='NONE';temporal['interpretation']='Unweighted percentage of positive validation bin estimates, not percentage of passengers; no clipping or fitted tail extrapolation'
 temporal.to_csv(OUT/'support_exceedance_review.csv',index=False)
 WeightedBinnedSensitivity(OUT/'sampling_contract.json')
 print(json.dumps(g))
if __name__=='__main__':main()
