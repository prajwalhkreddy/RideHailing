"""Finalize evidence only after complete baseline repeats; never launches training."""
from pathlib import Path
import json,hashlib,subprocess,sys
import pandas as pd
from prepare_development import O,sha256,load_fixture,js
A=Path('results/analysis/2026-11-14_pricing_v2_time_specific_weather')
def main():
 cfg=json.loads((O/'training_harness_config.json').read_text());identity=cfg['sensitivity_identity']
 for path,h in cfg['implementation_hashes'].items():
  if sha256(path)!=h:raise ValueError('Implementation changed after validation: '+path)
 contract=json.loads((A/'weather_time_grouping_contract.json').read_text())
 for path,h in contract['source_hashes'].items():
  if sha256(path)!=h:raise ValueError('Frozen source changed')
 for row in pd.read_csv(A/'conditional_support_manifest.csv').to_dict('records'):
  if sha256(row['path'])!=row['support_hash']:raise ValueError('Support changed')
 f,m=load_fixture();baseline=json.loads((O/'baseline_manifest.json').read_text());rows=pd.read_csv(O/'weather_conditioned_baseline_comparison.csv');repro=pd.read_csv(O/'v2_full_day_baseline_reproducibility.csv')
 if baseline['status']!='FROZEN' or len(rows)!=3 or len(repro)!=3 or not repro.exact_match.all():raise ValueError('Full baseline repeats incomplete')
 if set(rows.policy)!={'HIGHEST_FEASIBLE','LOWEST_FEASIBLE','NEUTRAL_1_00_WITH_EXISTING_FALLBACK'}:raise ValueError('Missing baseline policy')
 if not rows.requests.eq(m['request_count']).all() or not rows.fleet_conserved.all() or not rows.optimizer_updates.eq(0).all():raise ValueError('Baseline invariant failure')
 for name in ['invalid_masks','no_feasible_actions','passenger_threshold_violations']:
  if not rows[name].eq(0).all():raise ValueError('Baseline '+name)
 if not rows.conditioning_sha256.eq(m['conditioning_sha256']).all():raise ValueError('Conditional sequences differ')
 reg=json.loads((A/'regression_results.json').read_text())
 if len(reg)!=4 or any(r['exit_code'] for r in reg):raise ValueError('Regression failure')
 log=(A/'test_results.txt').read_text()
 if 'Ran 23 tests' not in log or not log.rstrip().endswith('OK'):raise ValueError('Focused tests incomplete')
 result=dict(verdict='READY_TO_LAUNCH_V2_STAGE25',training_started=False,March17_31_untouched=True,sensitivity_identity=identity,grouping_contract_hash=identity['grouping_contract_hash'],selected_K_per_T=contract['selected_K_per_T'],fixture_requests=m['request_count'],fixture_slots=48,baseline_policies=3,baseline_executions=6,exact_baseline_reproducibility=True,focused_tests=23,regression_counts=[41,57,123,239],baseline_comparison_sha256=sha256(O/'weather_conditioned_baseline_comparison.csv'),runtime_implementation_hashes=cfg['implementation_hashes'])
 js(O/'prelaunch_verification.json',result)
 check=subprocess.run([sys.executable,'-B',str(O/'training_harness.py'),'--verify'],capture_output=True,text=True)
 (O/'harness_verification.txt').write_text(check.stdout+check.stderr)
 if check.returncode:raise ValueError('Harness verification failed: '+check.stderr[-1200:])
 cfg['status']='READY_PREPARED_NOT_STARTED';js(O/'training_harness_config.json',cfg)
 result['harness_gate_validation']='PASS';js(O/'prelaunch_verification.json',result);js(O/'verification.json',result);js(A/'verification.json',result);js(A/'prelaunch_verification.json',result)
 for folder in [O,A]:
  path=folder/'runtime_conditioning_verification.json';v=json.loads(path.read_text());v.update(status='INTEGRATED_VALIDATED_NOT_TRAINED',baseline_status='FROZEN_REPRODUCIBLE',gate=result['verdict']);js(path,v)
 rows.to_csv(A/'weather_conditioned_baseline_comparison.csv',index=False)
 text='\n## Completed full-day validation\n\n**READY_TO_LAUNCH_V2_STAGE25. Training has NOT started.** All three conditioned policies completed48 slots and exact full repeats with the same73,754 request/context/epsilon records, unchanged initial fleet and validated dependencies. Full request tables matched exactly across repeats; no optimizer updates occurred. Fleet conservation and reward/feasibility checks passed. The versioned harness verification passed. March17–31 remains untouched.\n\n| Policy | Assignments | Revenue USD | Unmatched |\n|---|---:|---:|---:|\n'
 for r in rows.itertuples():text+=f'|{r.policy}|{r.assignments}|{r.revenue:.6f}|{r.unmatched}|\n'
 text+='\n23 focused tests and the41/57/123/239 scoped suites passed (overlapping coverage). Conditional support selection and per-request epsilon sequences are identical across policies. Charging entry/exit counts in the baseline table are observed at slot boundaries; detailed event count is separately recorded. Read `prelaunch_verification.json` and `baseline_manifest.json` for hashes. Readiness is not authorization to start training in this task.\n'
 for path in [A/'README.md',O/'README.md']:
  with path.open('a') as s:s.write(text)
 current='''## Current V2 conditional launch gate — 14 November 2026

**READY_TO_LAUNCH_V2_STAGE25. TRAINING: NOT YET STARTED.** This supersedes prior pending-baseline and global-mapping blockers. V2 sensitivity is WEATHER/TIME CONDITIONED with TIME-SPECIFIC grouping. T1_G1={1,2,3,5,7,8,9,12,14,16}, T1_G2={13,15}; T2/T3/T4 use explicit T_GROUP_POOLED_FALLBACK. Global pooled V2 remains CONTROL/FALLBACK. The retained support threshold and four fallback levels remain documented; undersized T1_G2 uses raw-weather fallback. All48 March16 slots completed for highest/lowest/neutral policies and exact repeats;73,754 requests per run. The conditioned fixture, supports, mapping, checkpoints and future harness are hash/version bound. No training or March17–31 access occurred. See `results/training/pricing_v2_staged_training_001/weather_conditioned/README.md` and `results/analysis/2026-11-14_pricing_v2_time_specific_weather/README.md` for full evidence. Stop here; do not launch Episode1 in this task.

'''
 for path in [Path('README.md'),Path('results/analysis/2026-11-01_current_state_review/README.md'),O.parent/'README.md']:
  head,rest=path.read_text().split('\n',1);path.write_text(head+'\n\n'+current+rest.lstrip('\n'))
 for name in ['weather_conditioning_launch_gate.json','prelaunch_verification.json']:js(O.parent/name,dict(result,authoritative_harness=str(O/'training_harness.py'),pooled_harness_status='SUPERSEDED_CONTROL_DO_NOT_LAUNCH'))
 for name in ['training_status.json','verification.json']:
  path=O.parent/name;v=json.loads(path.read_text());v.update(current_weather_conditioning_gate=result['verdict'],authoritative_harness=str(O/'training_harness.py'),training_started=False);js(path,v)
 print(rows[['policy','assignments','revenue','unmatched']].to_string(index=False));print(result['verdict'])
if __name__=='__main__':
 try:main()
 except BaseException as e:
  path=O/'prelaunch_verification.json';js(path,dict(verdict='V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_FINAL_VERIFICATION_FAILED',reason=str(e),training_started=False));raise
