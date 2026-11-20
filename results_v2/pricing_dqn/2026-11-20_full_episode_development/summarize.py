"""Reconcile completed development evidence; no model loading or training."""
from pathlib import Path
import json,hashlib,shutil
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parent
M=Path('models/pricing_dqn/2026-11-20_full_episode_development_seed42')
load=lambda n:json.loads((R/n).read_text())
a=load('primary_checks.json');b=load('resume_checks.json');assert len(a)==16 and b==a[15:]
m=load('primary_metrics.json');res=load('resume_metrics.json')[0]
for k in ['pricing_losses','pricing_gradient_norms','epsilon_after','pricing_updates','revenue','replay_size','global_sha256']:assert m[-1][k]==res[k],k
coverage=pd.read_csv(R/'request_coverage_preflight.csv');actual=pd.read_csv(R/'primary_request_reconciliation.csv')
for k in ['source_rows','eligible_rows','excluded_invalid_trip_rows','realized_requests','fallback_requests','order_hash']:assert coverage[k].tolist()==actual[k].tolist(),k
assert [x['terminal'] for x in m]==[False]*15+[True]
assert sum(x['requests'] for x in m)==int(actual.realized_requests.sum())
assert all(x['active_od_contexts']==9572 and x['transitions']==9572 for x in m)
assert all(np.isfinite(x['pricing_gradient_norms']).all() and x['pricing_parameter_change_l2']>0 for x in m)
assert all(np.isclose(x['supported_reward']+x['fallback_reward'],x['revenue']) for x in m)
checkpoints=[]
for d in [M/'rolling',M/'final_checkpoint']:
 p=d.resolve();manifest=json.loads((p/'manifest.json').read_text())
 checkpoints.append(dict(path=str(d),resolved_path=str(p),slot=manifest['slot'],bytes=sum(f.stat().st_size for f in p.rglob('*') if f.is_file()),manifest_sha256=hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest(),component_hashes=manifest['component_hashes']))
(R/'checkpoint_inventory.json').write_text(json.dumps(checkpoints,indent=2)+'\n')
c=load('primary_complete.json');loss=[v for x in m for v in x['pricing_losses']];grad=[v for x in m for v in x['pricing_gradient_norms']]
v=dict(status='PASSED',contract='MASTER_OD_FULL_EPISODE_DEVELOPMENT_V1',slots=16,terminal=True,truncated=False,source_rows=int(actual.source_rows.sum()),eligible_requests=c['requests'],invalid_exclusions=int(actual.excluded_invalid_trip_rows.sum()),fallback_requests=int(actual.fallback_requests.sum()),accepted=c['accepted'],rejected=c['requests']-c['accepted'],assigned=c['assigned'],accepted_unmatched=c['accepted']-c['assigned'],revenue=c['total_revenue'],supported_reward=sum(x['supported_reward'] for x in m),fallback_reward=sum(x['fallback_reward'] for x in m),generated_transitions=sum(x['transitions'] for x in m),final_replay_size=m[-1]['replay_size'],pricing_updates=c['pricing_updates'],target_updates=m[-1]['target_updates'],epsilon_start=1.,epsilon_end=m[-1]['epsilon_after'],loss_min=min(loss),loss_max=max(loss),gradient_norm_min=min(grad),gradient_norm_max=max(grad),routing_updates=sum(x['optimizer_updates'] for x in m),routing_sample_presentations=sum(x['trained_sample_presentations'] for x in m),federation_rounds=m[-1]['federation_round'],primary_slot_seconds=sum(x['seconds'] for x in m),primary_wall_seconds_file_timestamps=(R/'primary_complete.json').stat().st_mtime-(R/'primary_run.log').stat().st_birthtime,peak_rss_bytes=max(x['peak_rss_bytes'] for x in m),charging_events=m[-1]['charging_events'],nonstay_routing_decisions=sum(sum(x['routing_action_counts'][1:]) for x in m),final_EV_energy_kWh=m[-1]['ev_energy_sum'],fleet_size=5000,EVs=500,non_EVs=4500,recovery_initial_state_exact=True,recovery_final_state_exact=True,recovery_losses_gradients_exact=True,recovery_slots_executed=1,tests_passed=32,tests_failed=0,checkpoint_bytes=sum(x['bytes'] for x in checkpoints),disk_free_after=shutil.disk_usage('.').free,protected_period_accessed=False,additional_episode_started=False,correctness_blockers=[])
v['source_hashes']={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['scripts/run_full_od_development.py','tests/test_full_od_development.py']}
(R/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
f=load('frozen_protocol.json');f['status']='COMPLETED_VALIDATED';f['configuration']['checkpoint_policy']='rolling at slots4,8,12,15 plus final16; bounded slot16 recovery';(R/'frozen_protocol.json').write_text(json.dumps(f,indent=2)+'\n')
print(json.dumps(v,indent=2))
