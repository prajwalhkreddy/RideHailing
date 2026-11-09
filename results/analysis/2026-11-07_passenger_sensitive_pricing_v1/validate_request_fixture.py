"""Two capped training-date slots, fresh learner; zero optimization/inference provenance reuse."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from src.pricing.passenger_sensitive_v1 import PositiveEpsilonProvider
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
from src.simulation.passenger_sensitive_v1 import PassengerSensitiveExperiment
R=Path(__file__).parent
if (R/'fixture_validation.json').exists():raise SystemExit('Completed fixture exists; reuse it.')
support=json.loads((R/'restricted_calibration_support.json').read_text())
decision=json.loads((R/'epsilon_min_decision.json').read_text())
floor=decision['candidates']['P0.5']
provider=PositiveEpsilonProvider(np.load(R/'positive_epsilon_calibration.npy',mmap_mode='r'),floor,rng=np.random.default_rng(42),provenance=support,frozen=False)
learner=PassengerSensitiveDQN()
namespace=Path('models/pricing_dqn/passenger_sensitive_v1_seed42')
if not namespace.exists():learner.save(namespace)
else:
 m=json.loads((namespace/'checkpoint.json').read_text());assert m['schema']=='passenger_sensitive_request_v1' and m['training_steps']==0
 # Do not load any prior weights into the diagnostic learner.
weights=[a.copy() for a in learner.online.get_weights()]
route=Path('models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras')
x=PassengerSensitiveExperiment(provider=provider,learner=learner,start='2026-03-12 15:30',seed=42,routing_checkpoint=route,validation_only=True)
for slot in range(2):
 requests=x.requests_for_slot()
 requests=sorted(requests,key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds,r.request_id))[:200]
 report=x.run_slot(requests=requests,terminal=slot==1,train_dqn=False)
 print(json.dumps(report),flush=True)
f=pd.DataFrame(x.request_audit);links=pd.DataFrame(x.linker.audit)
assert len(f)==400 and x.linker.pending is None
assert len(links)==int(f.transition_created.sum())==int(f.selected_action_index.notna().sum())
assert f.loc[f.pricing_outcome=='NO_FEASIBLE_PRICING_ACTION','selected_action_index'].isna().all()
assert not f.loc[f.pricing_outcome=='NO_FEASIBLE_PRICING_ACTION','transition_created'].any()
active=f[f.selected_action_index.notna()]
assert (active.P_offer_USD<=active.P_c_USD).all() and active.passenger_status.eq('ACCEPTED').all()
assert learner.training_steps==0
for a,b in zip(weights,learner.online.get_weights()):np.testing.assert_array_equal(a,b)
assert np.isclose(f.reward.sum(),sum(r['reward'] for r in x.reports),rtol=1e-12)
for i in range(len(links)-1):assert links.iloc[i].next_actionable_request_id==links.iloc[i+1].Request_ID
assert int(links.done.sum())==1
assert len(learner.replay)==len(links)
f.to_csv(R/'request_level_mask_validation.csv',index=False);links.to_csv(R/'request_level_transition_validation.csv',index=False)
pd.DataFrame(x.reports).to_csv(R/'slot_validation.csv',index=False)
summary=dict(status='PASS',fixture='First200 chronological generated requests in each of two March12 slots; diagnostic capped demand, not performance evaluation',epsilon_floor=floor,epsilon_floor_status='P0.5_DIAGNOSTIC_ONLY_NOT_FROZEN',requests_seen=len(f),offers_generated=len(active),no_feasible_pricing_action=int(f.selected_action_index.isna().sum()),offered_passenger_accepted=len(active),offered_passenger_rejected=0,assigned=int(f.assignment_status.sum()),accepted_unmatched=int(len(active)-f.assignment_status.sum()),transitions_added=len(links),optimizer_updates=0,reward=float(f.reward.sum()),weights_unchanged=True,fleet_size=len(x.fleet.vehicles),old_checkpoint_loaded=False,protected_final_period_untouched=True,fresh_checkpoint_untrained=True)
(R/'fixture_validation.json').write_text(json.dumps(summary,indent=2)+'\n')
(namespace/'training_gate.json').write_text(json.dumps({'epsilon_min_status':'RESEARCH_DECISION_REQUIRED','long_training_allowed':False,'fresh_untrained':True,'historical_checkpoint_loaded':False},indent=2)+'\n')
print(json.dumps(summary))
