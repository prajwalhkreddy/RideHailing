"""Focused independent checks for the approved positive-first calibration correction."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
R=Path(__file__).parent
s=json.loads((R/'restricted_calibration_support.json').read_text())
f=pd.read_parquet(s['source'],columns=['pickup_timestamp','epsilon','epsilon_status','trip_distance'],filters=[('pickup_timestamp','>=',pd.Timestamp('2026-01-01')),('pickup_timestamp','<',pd.Timestamp('2026-03-16'))])
v=f.epsilon_status.eq('VALID')&np.isfinite(f.epsilon)&f.epsilon.ne(0)
a=np.abs(f.loc[v,'epsilon'].to_numpy());lo,hi=np.quantile(a,[.005,.995],method='linear')
assert lo==s['positive_support_lower'] and hi==s['positive_support_upper']
m=v&f.epsilon.abs().between(lo,hi,inclusive='both')
raw=np.load(R/'positive_epsilon_calibration.npy',mmap_mode='r');d=np.load(R/'calibration_distance_km.npy',mmap_mode='r')
assert np.array_equal(raw,f.loc[m,'epsilon'].abs().to_numpy())
assert np.array_equal(d,f.loc[m,'trip_distance'].to_numpy()*1.609344)
assert len(raw)==s['N_positive_supported'] and (raw>=lo).all() and (raw<=hi).all()
comparison=pd.read_csv(R/'epsilon_floor_comparison.csv',float_precision='round_trip')
summary=pd.read_csv(R/'epsilon_positive_distribution.csv',float_precision='round_trip').iloc[0]
assert int(summary.N)==len(raw) and summary['min_positive']==raw.min() and summary['max']==raw.max()
assert s['N_positive_before_support']==len(a)
assert s['excluded_below_support']+s['excluded_above_support']+len(raw)==len(a)
arms=pd.read_csv(R/'feasible_arm_distribution.csv');groups=pd.read_csv(R/'epsilon_four_group_diagnostics.csv')
for name,q in [('NO_FLOOR',None),('P0.5',.005),('P1',.01),('P2.5',.025),('P5',.05)]:
 row=comparison[comparison.candidate.eq(name)].iloc[0]
 floor=0 if q is None else float(np.quantile(raw,q))
 assert floor==row.epsilon_min
 e=np.maximum(raw,floor);pc=21.34586956773507*(1+(d/4.856998243316242-1)/e)
 # Algebraically independent form; tolerate roundoff only near price equalities.
 original=21.34586956773507+(21.34586956773507/e)*((d-4.856998243316242)/4.856998243316242)
 assert np.allclose(pc,original,rtol=1e-12,atol=1e-10)
 count=sum((21.34586956773507*x<=original).astype(np.int8) for x in [.85,.9,.95,1,1.05,1.1,1.15])
 assert int((original<0).sum())==row.negative_Pc_count
 assert int((original<=0).sum())==row.nonpositive_Pc_count
 assert np.isclose((count==0).mean()*100,row.no_feasible_action_percentage,rtol=0,atol=1e-12)
 assert np.isfinite(original).all()
 for n in range(8):assert int(arms[(arms.candidate==name)&(arms.feasible_action_count==n)].N.iloc[0])==int((count==n).sum())
 assert groups[groups.candidate==name].N.sum()==len(raw)
for path,old in json.loads((R/'positive_first_historical_integrity_before.json').read_text()).items():
 p=Path(path);assert p.stat().st_size==old['size'] and p.stat().st_mtime_ns==old['mtime_ns']
 if 'sha256' in old:assert hashlib.sha256(p.read_bytes()).hexdigest()==old['sha256']
for path in ['README.md','results/analysis/2026-11-01_current_state_review/README.md','results/analysis/2026-11-04_academic_review_validation/README.md',str(R/'README.md')]:
 t=Path(path).read_text();assert 'positive' in t and 'superseded' in t and str(hi) in t
result=dict(status='PASS',positive_first_quantiles_verified=True,inclusive_support_and_source_order_verified=True,source_distance_pairing_verified=True,additional_floor_quantiles_verified=True,Pc_and_feasible_counts_verified=True,group_population_totals_verified=True,historical_Record029_unchanged=True,calibration_latest_timestamp=str(f.pickup_timestamp.max()),March16_excluded=True,March17_31_excluded=True,simulation_rerun=False,long_training_started=False,N=len(raw),support=[float(lo),float(hi)],prior_fixture='Preserved historical mechanics evidence; superseded calibration')
(R/'positive_first_calibration_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
