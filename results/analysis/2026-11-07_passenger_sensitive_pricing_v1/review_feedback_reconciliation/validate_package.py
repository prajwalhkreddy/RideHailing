from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
from src.pricing.passenger_sensitive_v1 import PositiveEpsilonProvider
R=Path(__file__).parent;V=R.parent
for path,before in json.loads((V/'positive_first_historical_integrity_before.json').read_text()).items():
 p=Path(path);assert p.stat().st_size==before['size'] and p.stat().st_mtime_ns==before['mtime_ns']
 if 'sha256' in before:assert hashlib.sha256(p.read_bytes()).hexdigest()==before['sha256']
s=json.loads((V/'restricted_calibration_support.json').read_text())
p=PositiveEpsilonProvider([s['positive_support_lower'],s['positive_support_upper']],s['positive_support_lower'],rng=np.random.default_rng(42),provenance=s,frozen=True);p.require_training_ready()
a=pd.read_csv(R/'feasible_arm_before_after.csv');t=pd.read_csv(R/'sensitivity_truncation_comparison.csv');raw=pd.read_csv(R/'raw_vs_effective_preference_summary.csv')
for row in t.itertuples():
 z=a[a.candidate==row.candidate];assert z.before_N.sum()==z.after_N.sum()==row.retained_N
 assert z.loc[z.feasible_arms==0,'after_N'].iloc[0]==0
 assert np.isclose(z.after_pct.sum(),100)
 assert row.zero_count==row.invalid_count==0
 assert raw[(raw.candidate==row.candidate)&(raw.category=='effective_min_protection_applied')].N.iloc[0]==z.loc[z.feasible_arms==0,'before_N'].iloc[0]
f=pd.read_csv(R/'pricing_factor_dataset_justification.csv');assert int(f[f.metric.str.startswith('bin_')].N.sum())==8692819
assert pd.read_csv(R/'pricing_factor_distance_band_coverage.csv').N.sum()==8692819
assert pd.read_csv(R/'pricing_factor_time_group_coverage.csv').N.sum()==8692819
paths=[V/'README.md',V/'METHODOLOGY.md',R/'README.md',Path('README.md'),Path('results/analysis/2026-11-01_current_state_review/README.md'),Path('results/analysis/2026-11-04_academic_review_validation/README.md')]
for p in paths:
 text=p.read_text();assert 'V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION' in text and 'PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED' in text
 assert str(s['positive_support_upper']) in text
 assert 'SUPERSEDED_BY_EFFECTIVE_THRESHOLD_REFORMULATION' in text
 assert 'truncated' in text.lower() and 'long training' in text.lower()
for p in ['src/pricing/passenger_sensitive_v1.py','src/simulation/passenger_sensitive_v1.py','src/dispatch/request.py']:
 compile(Path(p).read_text(),p,'exec')
q=R/'review_feedback_validation.json';j=json.loads(q.read_text());j['package_checks']={'status':'PASS','historical_integrity':'All Record029 directory file size/mtime unchanged; small artifacts SHA256 unchanged','arm_counts_reconcile':True,'fare_bins_and_groups_reconcile':True,'frozen_provider_ready':True,'current_documentation_consistent':True,'long_training_started':False};q.write_text(json.dumps(j,indent=2)+'\n')
print('PACKAGE_VALIDATION_PASS')
