from pathlib import Path
import sys,json
import pandas as pd,numpy as np
R=Path(__file__).parent;sys.path.insert(0,str(R));from analyze import P,OLD,save,js,checkpoint
if not (R/'intermediate/supplement_complete.json').exists():
 f=pd.read_parquet(R.parent/'2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet',columns=['pickup_timestamp','fare','trip_distance']);assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
 fare=f.fare.to_numpy();distance=f.trip_distance.to_numpy()*1.609344;rp=(fare-P)/P
 candidates=json.loads((R/'reference_values/candidates.json').read_text())['L_candidates'];precision=[]
 for c,L in candidates.items():
  e=((distance-L)/L)/rp;np.save(R/f'intermediate/new_e_ALL_SAFE_{c}.npy',e)
  for label,p in [('DOCUMENT_ROUNDED',22.3542),('HISTORICAL',OLD)]:
   alt=((distance-L)/L)/((fare-p)/p);diff=abs(alt-e)
   precision.append(dict(candidate=c,comparison=label,scope='ALL_SAFE',N=len(e),mean_abs_e_difference=float(diff.mean()),max_abs_e_difference=float(diff.max()),median_abs_e_difference=float(np.median(diff)),sign_changes=int((np.sign(e)!=np.sign(alt)).sum())))
 save('reference_values/epsilon_precision_effects.csv',precision)
 # Isolate distance-filter effect from simultaneously re-estimating a price denominator.
 from analyze import stats
 b=pd.read_csv(R/'array_a/array_a_verified.csv');ids=np.floor(distance/.5).astype(int);domain=(distance>=1)&(distance<75)
 masks={f'LOWER_{lo}_UPPER_75':(distance>=lo)&(distance<75) for lo in [1,1.5,2]};masks['LOWER_1_EXISTING_100_MILES']=(distance>=1)&(distance<=160.9344)
 for n in [50,100]:
  allowed=(b.loc[b.N>=n,'lower_distance_km']/.5).astype(int);masks[f'MIN_{n}_INDIVIDUAL']=domain&np.isin(ids,allowed)
  stop=np.flatnonzero(b.N.to_numpy()<n)[0];masks[f'MIN_{n}_CONTIGUOUS']=(distance>=1)&(distance<1+.5*stop)
 rows=[]
 base=((distance-4.5)/4.5)/rp
 for label,m in masks.items():rows.append(dict(scenario=label,P_base_fixed=P,L_base_fixed=4.5,observed_max_km=float(distance[m].max()),physical_upper_bound_km=160.9344 if '100_MILES' in label else 75.,**stats(base[m])))
 save('distance_cutoffs/fixed_reference_comparison.csv',rows)
 js('intermediate/supplement_complete.json',dict(full_safe_fit_inputs_created=True,protected_rows_selected=0));checkpoint('SUPPLEMENT_COMPLETE')
