"""Read-only model diagnosis and four-slot March16 inference comparisons."""
from pathlib import Path
import sys,json,hashlib,math
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.rl.pricing_dqn import PricingDQN,PricingAction,validate_state
from src.simulation.final_production import ProductionExperiment
import src.simulation.final_production as runner
OUT=Path(__file__).resolve().parent
NS=ROOT/'models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42'
CP=NS/'checkpoint_0720_a79095b4'
def save(name,x):
 p=OUT/name;tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2,default=str)+'\n');tmp.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def variables(model):return hashlib.sha256(b''.join(v.numpy().tobytes() for v in model.variables)).hexdigest()
def agent_hash(d):return (variables(d.online),variables(d.target),hashlib.sha256(b''.join(v.numpy().tobytes() for v in d.online.optimizer.variables)).hexdigest(),d.training_steps,len(d.replay),json.dumps(d.rng.bit_generator.state),json.dumps(d.replay.rng.bit_generator.state))
def diagnose():
 m=json.loads((CP/'manifest.json').read_text());ptr=json.loads((NS/'CURRENT.json').read_text())
 assert ptr['directory']==CP.name and ptr['manifest_sha256']==sha(CP/'manifest.json')
 for path,digest in m['files'].items():assert sha(CP/path)==digest
 reports=pd.read_csv(ROOT/'results/analysis/2026-10-25_final_nonprivate_pricing_training/slot_metrics.csv')
 assert len(reports)==720 and reports.transitions.sum()==288181
 assert pd.to_datetime(reports.timestamp).equals(pd.Series(pd.date_range('2026-03-01',periods=720,freq='30min'),name='timestamp'))
 trained=reports.training.notna();assert trained.sum()==718 and not trained.iloc[:2].any() and trained.iloc[2:].all()
 d=PricingDQN.load(CP/'dqn');b=PricingDQN.load(CP/'dqn')
 assert (m['slots'],d.training_steps,len(d.replay))==(720,718,100000) and np.isclose(d.epsilon,.986358)
 assert agent_hash(d)==agent_hash(b)
 assert all(np.isfinite(v.numpy()).all() for mod in [d.online,d.target] for v in mod.variables)
 assert all(np.isfinite(v.numpy()).all() for v in d.online.optimizer.variables)
 rows=list(d.replay.items);idx=np.linspace(0,len(rows)-1,10000,dtype=int);states=np.stack([rows[i][0] for i in idx]);q=d.online(states,training=False).numpy()
 np.testing.assert_array_equal(q,b.online(states,training=False).numpy());assert np.isfinite(q).all()
 cut=288181-100000;first=int(np.searchsorted(reports.transitions.cumsum().to_numpy(),cut,side='right'))
 cadence=dict(checkpoint=str(CP.relative_to(ROOT)),slots=720,completion=m['timestamp'],optimizer_updates=718,epsilon=d.epsilon,replay_transitions=288181,replay_capacity=100000,replay_size=len(d.replay),first_three_slots=reports[['timestamp','transitions','replay_size']].head(3).to_dict('records'),rule='Exactly one train_step per completed main slot; returns without update when replay_size <1000. First two slots have 473 and921 transitions; slot3 crosses1000. Slots3..720 each update once.',online_target_optimizer_finite=True,optimizer_iterations=int(d.online.optimizer.iterations.numpy()),deterministic_reload=True,checkpoint_payload_hashes_valid=True,source_hashes=m['files'])
 save('training_cadence.json',cadence)
 thresholds={str(e):dict(continuous_updates=50000*(1-e)/.95,first_integer_update=math.ceil(round(50000*(1-e)/.95,10))) for e in [.9,.5,.1,.05]}
 schedule=dict(formula='epsilon(u)=1-0.95*min(u/50000,1)',epsilon_718=d.epsilon,thresholds=thresholds,decay_fraction_completed=718/50000,epsilon_reduction=.95*718/50000,passes_at_718_updates_each=50000/718,passes_if_replay_carried_and_only_initial_two_warmup_slots=(50000+2)/720,whole_passes_in_either_case=70,classification='TRAINING_SCHEDULE_MISMATCH',PROJECT_CONFIG_DECISION_REQUIRED=True,decision='Agree whether to change optimizer cadence, express epsilon decay relative to the available training horizon, or explicitly permit multiple chronological training episodes. No option selected or executed.',interpretation='Only 1.436% of the planned decay occurs; training remains nearly random. This alone does not establish that greedy Q predictions are useless.')
 save('epsilon_schedule_diagnosis.json',schedule)
 counts=np.bincount(q.argmax(1),minlength=7);sortedq=np.sort(q,axis=1);gap=sortedq[:,-1]-sortedq[:,-2];tolerance=.01*np.maximum(1,np.maximum(abs(sortedq[:,-1]),abs(sortedq[:,-2])))
 diag=dict(sample_N=len(states),sampling='10000 evenly spaced stored current states in final chronological 100000-transition replay; preserves frequency, no deduplication; not a uniform sample of all training history',replay_start_slot=int(first),replay_start_timestamp=reports.timestamp.iloc[first],finite_Q=True,raw_Q_min=float(q.min()),raw_Q_mean=float(q.mean()),raw_Q_max=float(q.max()),absolute_Q_min=float(abs(q).min()),absolute_Q_mean=float(abs(q).mean()),absolute_Q_max=float(abs(q).max()),mean_action_Q_spread=float(np.ptp(q,axis=1).mean()),mean_top1_top2_gap=float(gap.mean()),greedy_action_counts=counts.tolist(),greedy_action_percentages=(100*counts/len(states)).tolist(),never_selected_count=int((counts==0).sum()),largest_greedy_share=float(counts.max()/len(states)),near_tie_fraction=float((gap<=tolerance).mean()),near_tie_definition='top1-top2 <= 0.01*max(1,abs(top1),abs(top2)); descriptive threshold only',checkpoint_reload_predictions_exact=True)
 save('q_value_diagnostics.json',diag);print(json.dumps(dict(phase='checkpoint_and_Q_PASS',q_summary=diag)),flush=True)
 return m

def inference(m):
 original=runner.artifact_snapshots
 def guarded(t):
  if not pd.Timestamp('2026-03-16')<=pd.Timestamp(t)<pd.Timestamp('2026-03-17'):raise ValueError('Diagnostic prohibits non-March16 source access')
  return original(t)
 runner.artifact_snapshots=guarded
 shared_od=None;request_signatures=[]
 for mode,name in [('greedy','march16_greedy_diagnostic.json'),('fixed100','march16_fixed100_comparator.json')]:
  if (OUT/name).exists():
   raise RuntimeError('Completed diagnostic exists; do not overwrite or repeat it.')
  x=ProductionExperiment(start='2026-03-16',seed=42,dqn_checkpoint=CP/'dqn',routing_checkpoint=Path(m['routing']['path']),frozen_routing=True)
  x.od=shared_od;before=agent_hash(x.dqn);routing_before=variables(x.policy);selected=x.dqn.select_action
  def select(state,*,explore=True):
   validate_state(state)
   a=selected(state,explore=False) if mode=='greedy' else PricingAction(3,1.,0.,False)
   return PricingAction(a.action_index,a.pricing_factor,0.,False)
  x.dqn.select_action=select
  def forbidden(*args,**kwargs):raise AssertionError('Diagnostic cannot insert replay or update optimizer')
  x.dqn.store=forbidden;x.dqn.train_step=forbidden
  dispatched_factors=[];request_factors=[];observed_q=[];slot_signatures=[]
  for i in range(4):
   assert x.timestamp==pd.Timestamp('2026-03-16')+pd.Timedelta(minutes=30*i)
   requests=x.requests_for_slot()
   signature=hashlib.sha256(repr([(r.request_id,r.origin_grid,r.destination_grid,r.request_time,r.trip_distance_miles,r.trip_duration_minutes) for r in requests]).encode()).hexdigest();slot_signatures.append(signature)
   if mode=='fixed100':assert signature==request_signatures[i]
   # Existing runner computes action only once per OD/slot. Inspect those causal states compactly.
   keys=sorted({(r.origin_grid,r.destination_grid) for r in requests})
   if keys:
    values=x.dqn.online(np.stack([x.current_states.build(*k,x.timestamp) for k in keys]),training=False).numpy();assert np.isfinite(values).all();observed_q.append(values)
   result=x.run_slot(requests,terminal=i==3,train_dqn=False)
   from src.dispatch.request import RequestStatus
   dispatched_factors.extend(r.pricing_factor for r in requests if r.status is RequestStatus.ASSIGNED);request_factors.extend(r.pricing_factor for r in requests)
   assert agent_hash(x.dqn)==before and variables(x.policy)==routing_before
   assert result['fleet_size']==5000 and result['transitions']==0 and result['federated_updates']==0 and result['training'] is None
   assert len({v.vehicle_id for v in x.fleet.vehicles})==5000 and all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in x.fleet.vehicles)
   print(json.dumps(dict(mode=mode,slot=i+1,requests=result['requests'],assigned=result['assigned'],revenue=result['reward'])),flush=True)
  q=np.concatenate(observed_q);counts=np.sum([r['pricing_action_counts'] for r in x.reports],axis=0)
  summary=dict(status='PASS',date='2026-03-16',start='00:00',end='02:00',slots=4,period_rationale='Bounded existing short-run interface; full48-slot pair not inexpensive at observed runtime. Results are early-night diagnostic only.',initialization='fresh identical seed42 fleet/operational state per mode; final trained DQN loaded; not continuation of training fleet',mode=mode,requests=sum(r['requests'] for r in x.reports),accepted=sum(r['accepted'] for r in x.reports),rejected=sum(r['rejected'] for r in x.reports),assignments=sum(r['assigned'] for r in x.reports),unmatched=sum(r['unmatched'] for r in x.reports),revenue=sum(r['reward'] for r in x.reports),pricing_action_counts=counts.tolist(),pricing_action_count_unit='one selected action per observed OD/main-slot, not per request',mean_dispatched_factor=float(np.mean(dispatched_factors)) if dispatched_factors else None,mean_requested_factor=float(np.mean(request_factors)),fleet_conservation=True,fleet_count=5000,charging_events=len(x.charging_events),reserve_assignment_rejections=x.reserve_assignment_rejections,reserve_rejected_requests=len(x.reserve_rejected_request_ids),reserve_reposition_rejections=getattr(x.routing,'reserve_reposition_rejections',0),optimizer_updates_before=718,optimizer_updates_after=x.dqn.training_steps,model_optimizer_rng_unchanged=agent_hash(x.dqn)==before,replay_size_before=100000,replay_size_after=len(x.dqn.replay),inference_epsilon=0.,persisted_training_epsilon=x.dqn.epsilon,checkpoint_unchanged=True,routing_weights_unchanged=True,request_signatures=slot_signatures,mean_observed_Q_spread=float(np.ptp(q,axis=1).mean()),observed_greedy_counts=np.bincount(q.argmax(1),minlength=7).tolist(),protected_evaluation_accessed=False)
  save(name,summary)
  if mode=='greedy':shared_od=x.od;request_signatures=slot_signatures
  del x
 for path,digest in m['files'].items():assert sha(CP/path)==digest
 print('DIAGNOSIS COMPLETE; checkpoint unchanged',flush=True)
if __name__=='__main__':inference(diagnose())
