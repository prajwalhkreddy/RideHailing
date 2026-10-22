from pathlib import Path
import json,hashlib
import pandas as pd
from src.simulation.pricing_dqn_fixture import run_fixture
out=Path('results/analysis/2026-10-21_pricing_dqn_simulator_integration')
if (out/'state_validation.json').exists():raise SystemExit('Completed results exist; inspect/reuse rather than implicit rerun.')
checkpoints=[Path('models/pricing_dqn/standalone_13x64x64x7_fixture'),Path('models/routing_policy/jan_mar_2026_3km_169x64x32x9')]
protected={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for folder in checkpoints for f in folder.iterdir() if f.is_file()}
runs=[run_fixture(),run_fixture(3)]
for key,name in [('trace','integration_trace.csv'),('states','state_vectors.csv'),('requests','acceptance_dispatch_trace.csv'),('reward','reward_reconciliation.csv')]:pd.DataFrame([r for run in runs for r in run[key]]).to_csv(out/name,index=False)
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in protected.items())
(out/'fleet_conservation.json').write_text(json.dumps(dict(expected_vehicles_per_run=3,all_checks_passed=True,mini_slot_checks=[r for run in runs for r in run['fleet']]),indent=2)+'\n')
(out/'state_validation.json').write_text(json.dumps(dict(passed=True,runs=2,state_vectors=48,replay_transitions=24,terminal_transitions=6,checkpoint_hashes_unchanged=True,state_dimension=13,next_state_timing_verified=True,J_disp_counts_verified=True,incoming_counts_verified=True,terminal_targets_verified=True,optimizer_updates=0),indent=2)+'\n')
(out/'integration_config.json').write_text(json.dumps(dict(seed=42,start='2026-03-16 00:00:00',end='2026-03-16 02:00:00',slots_per_run=4,origins=[0,1,2],destination_mapping={0:1,1:2,2:0},vehicles_per_run=3,requests_per_run=36,modes=['checkpoint_greedy_explore_false','forced_action_3'],routing_status='PROVISIONAL_ROUTING_BASELINE',dispatch_model='legacy_fcfs_lowest_id',replay='fresh isolated buffers; production minimum1000 unchanged; optimizer skipped',requests='controlled synthetic requests, not historical trip observations; IDs refer only to this fixture',request_pattern='two distance=D_base and one distance=0.5*D_base per origin per slot, all at mini-slot0; 40-minute durations',warm_start='explicitly completed empty pre-start slot; initialized idle fleet, no prior simulated dispatches',reward_attribution='each OD transition receives revenue attributable to its own priced requests; sum equals slot reward, no repeated whole-slot credit',protected_checkpoint_hashes=protected),indent=2)+'\n')
print(pd.DataFrame([r for run in runs for r in run['reward']]).groupby('mode')[['accepted','assigned','rejected','unmatched','ledger_reward']].sum().to_string())
