"""Opt-in final pricing protocol; old single-pass runner remains unchanged."""
from pathlib import Path
import json,pickle,hashlib,random,os,signal
import numpy as np,pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.simulation.final_pricing_training import checkpoint as _checkpoint,FIELDS,weights_hash,atomic_json,sha,lock_writer
from src.rl.pricing_dqn import PricingDQN,DQNConfig
from src.simulation.pricing_safety_monitor import EPISODES as MONITOR_EPISODES,learner_fingerprint,observe
ROOT=Path(__file__).resolve().parents[2]
ROUTING=ROOT/'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'
DIGEST='db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a'
OUT=ROOT/'results/analysis/2026-10-31_final_pricing_training_protocol'
FINAL=ROOT/'models/pricing_dqn/final_nonprivate_multiepisode_seed42'
RUN_OUT=ROOT/'results/analysis/2026-10-31_final_nonprivate_pricing_training'
def checkpoint(x,namespace,identity):
    Path(namespace).mkdir(parents=True,exist_ok=True)
    return _checkpoint(x,namespace,identity)

def plan():
 starts=np.random.default_rng(42).integers(0,705,500)
 seeds=np.random.SeedSequence(42).spawn(500)
 return [dict(episode=i+1,start=str(pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*int(k))),start_slot=int(k),environment_seed=int(seeds[i].generate_state(1)[0])) for i,k in enumerate(starts)]
def guard(start,slots=16,development=False):
 t=pd.Timestamp(start)
 if development:
  if t!=pd.Timestamp('2026-03-16') or slots!=4:raise ValueError('Fixed development fixture only.')
 elif slots!=16 or not pd.Timestamp('2026-03-01')<=t or t+pd.Timedelta(minutes=30*slots)>pd.Timestamp('2026-03-16'):raise ValueError('Training window must remain within March1–15.')
def reset(spec,learner):
 guard(spec['start']);assert sha(ROUTING)==DIGEST
 x=ProductionExperiment(start=spec['start'],seed=spec['environment_seed'],routing_checkpoint=ROUTING,frozen_routing=True);x.dqn=learner
 return x
def updates_for_slot(learner,timestamp):
 t=pd.Timestamp(timestamp)
 if not pd.Timestamp('2026-03-01')<=t<pd.Timestamp('2026-03-16'):raise ValueError('No nontraining-date updates.')
 return [r for _ in range(8) if (r:=learner.train_step()) is not None]
def slot(x,terminal=False,development=False):
 start=x.timestamp;before=x.dqn.training_steps;rep=x.run_slot(terminal=terminal,train_dqn=False,explore_pricing=not development)
 updates=[] if development else updates_for_slot(x.dqn,start)
 expected=0 if development or len(x.dqn.replay)<1000 else 8
 assert x.dqn.training_steps-before==expected and rep['federated_updates']==0
 assert rep['fleet_size']==5000 and all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in x.fleet.vehicles)
 rep.update(optimizer_updates=len(updates),epsilon=x.dqn.epsilon,mean_loss=float(np.mean([u['loss'] for u in updates])) if updates else None)
 return rep
RID=dict(path=str(ROUTING),sha256=DIGEST,inference_only=True)
def restore_episode(x,namespace):
 namespace=Path(namespace);ptr=json.loads((namespace/'CURRENT.json').read_text());p=namespace/ptr['directory'];meta=json.loads((p/'manifest.json').read_text());assert sha(p/'manifest.json')==ptr['manifest_sha256'] and meta['routing']==RID
 for f,h in meta['files'].items():assert sha(p/f)==h
 state=pickle.loads((p/'simulator.pkl').read_bytes())
 for k in FIELDS:setattr(x,k,state[k])
 x.dqn=PricingDQN.load(p/'dqn');x.request_rng.bit_generator.state=state['request_rng'];x.customer.rng.bit_generator.state=state['customer_rng'];random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng']);x.routing.reserve_reposition_rejections=state['reserve_reposition_rejections'];x.od=None
 if x.slot_index<16:x.current_states=x._state_sources()
 assert x.clock==x.timestamp and x.dqn.training_steps==meta['optimizer_steps']
 return x

def reserve_reposition_count(routing):
 # OperationalRouting.decide creates this counter only on the first rejected
 # reposition candidate. Absence therefore means zero observed rejections.
 return getattr(routing,'reserve_reposition_rejections',0)

def summarize(x,episode):
 r=x.reports;replay=list(x.dqn.replay.items);states=np.stack([z[0] for z in replay[-512:]]) if replay else None;q=x.dqn.online(states,training=False).numpy() if states is not None else np.zeros((1,7));requests=sum(z['requests'] for z in r);accepted=sum(z['accepted'] for z in r);assigned=sum(z['assigned'] for z in r)
 return dict(episode=episode,revenue=sum(z['reward'] for z in r),assignments=assigned,requests=requests,acceptance_rate=accepted/requests if requests else 0,fulfillment_rate=assigned/accepted if accepted else 0,action_counts=np.sum([z['pricing_action_counts'] for z in r],axis=0).tolist(),mean_abs_Q=float(np.abs(q).mean()),median_abs_Q=float(np.median(np.abs(q))),mean_Q_spread=float(np.ptp(q,axis=1).mean()),epsilon=x.dqn.epsilon,replay_size=len(x.dqn.replay),optimizer_updates=x.dqn.training_steps,mean_loss=float(np.mean([z['mean_loss'] for z in r if z.get('mean_loss') is not None])) if any(z.get('mean_loss') is not None for z in r) else None)
def run_fixture():
 ns=ROOT/'models/pricing_dqn/final_multiepisode_protocol_fixture_seed42';ns.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'protocol_fixture_results.json').exists():return
 learner=PricingDQN();records=[];checks=[]
 specs=[plan()[1]] if (OUT/'fixture_attempt1_failure.json').exists() else plan()[:2]
 for spec in specs:
  x=reset(spec,learner);z=reset(spec,learner)
  signature=lambda a:hashlib.sha256(pickle.dumps([(v.vehicle_id,v.current_grid,v.trip_status,v.energy_level) for v in a.fleet.vehicles])).hexdigest()
  assert signature(x)==signature(z);assert x.customer.rng.bit_generator.state==z.customer.rng.bit_generator.state;del z
  before=len(learner.replay);steps=learner.training_steps;route=weights_hash(x.policy)
  for j in range(16):
   rep=slot(x,terminal=j==15)
   if j==7:
    cp=checkpoint(x,ns/f'episode_{spec["episode"]}',RID);online=weights_hash(x.dqn.online);target=weights_hash(x.dqn.target);state=x.customer.rng.bit_generator.state
    x=restore_episode(x,ns/f'episode_{spec["episode"]}');assert online==weights_hash(x.dqn.online) and target==weights_hash(x.dqn.target) and state==x.customer.rng.bit_generator.state
   print('FIXTURE',spec['episode'],j+1,rep['transitions'],x.dqn.training_steps,flush=True)
  learner=x.dqn;assert weights_hash(x.policy)==route and sha(ROUTING)==DIGEST
  records.append(summarize(x,spec['episode']));checks.append(dict(episode=spec['episode'],start=spec['start'],slots=16,replay_start=before,replay_end=len(learner.replay),updates=learner.training_steps-steps,transitions=sum(z['transitions'] for z in x.reports),charging_events=len(x.charging_events),reset_reproducible=True,mid_episode_reload=True,fleet_energy_valid=True,routing_immutable=True,passenger_model=type(x.customer).__name__))
  pd.DataFrame(x.reports).to_csv(OUT/f'fixture_episode_{spec["episode"]}_slots.csv',index=False)
 probe=reset(plan()[2],learner);assert probe.dqn is learner and len(probe.dqn.replay)==len(learner.replay) and probe.dqn.training_steps==learner.training_steps
 atomic_json(OUT/'protocol_fixture_results.json',dict(status='PASS',reset_preserves_learner_and_replay=True,interrupted_attempts=1 if (OUT/'fixture_attempt1_failure.json').exists() else 0,episodes=checks,summaries=records,final_replay=len(learner.replay),final_optimizer_updates=learner.training_steps,epsilon=learner.epsilon,routing_sha256=sha(ROUTING),long_training_launched=False))

def run_final(resume=False):
 """Explicit future launch only; fixed budget, no automatic extension."""
 lock=lock_writer(FINAL)
 RUN_OUT.mkdir(parents=True,exist_ok=True)
 stop=[]
 old={sig:signal.signal(sig,lambda signum,frame:stop.append(signum)) for sig in (signal.SIGINT,signal.SIGTERM)}
 specs=json.loads((OUT/'episode_protocol.json').read_text())['starts']
 assert len(specs)==500
 for spec in specs:guard(spec['start'])
 assert sha(ROUTING)==DIGEST
 assert json.loads((OUT/'final_launch_config.json').read_text())['FINAL_PRICING_DQN_PROTOCOL_FROZEN']=='YES'
 statepath=FINAL/'protocol_cursor.json';records=[];start=0;learner=None if resume else PricingDQN()
 if resume and not statepath.exists():
  # Early partial runs have no completed-episode cursor; load their saved learner.
  first=FINAL/'episode_0001';pointer=json.loads((first/'CURRENT.json').read_text())
  learner=PricingDQN.load(first/pointer['directory']/'dqn')
 if not resume:
  assert not statepath.exists() and not list(FINAL.glob('episode_*'))
  assert len(learner.replay)==0 and learner.training_steps==0 and learner.epsilon==1.0
  assert weights_hash(learner.online)==weights_hash(learner.target)
 atomic_json(FINAL/'process.json',dict(pid=os.getpid(),namespace=str(FINAL),resume=resume,log=str(RUN_OUT/'training.log'),routing=RID))
 def status(name,x=None,episode=0,cp=None):
  payload=dict(status=name,pid=os.getpid(),episode=episode,slots_completed=0 if x is None else x.slot_index,replay_size=len(learner.replay),optimizer_updates=learner.training_steps,epsilon=learner.epsilon,routing_sha256=DIGEST,namespace=str(FINAL),checkpoint=cp,resume=resume)
  atomic_json(RUN_OUT/'status.json',payload)
  print(json.dumps(payload),flush=True)
 try:
  if resume and statepath.exists():
   cur=json.loads(statepath.read_text());start=cur['episode_index'];learner=PricingDQN.load(Path(cur['dqn_checkpoint']));records=cur['records']
  elif statepath.exists():raise ValueError('Use explicit resume for existing final run.')
  for i in range(start,500):
   x=reset(specs[i],learner);ns=FINAL/f'episode_{i+1:04d}'
   if (ns/'CURRENT.json').exists():
    if not resume:raise ValueError('Existing partial episode requires resume.')
    x=restore_episode(x,ns)
   learner=x.dqn
   status('EPISODE_INITIALIZED',x,i+1)
   while x.slot_index<16:
    slot(x,terminal=x.slot_index==15)
    status('SLOT_COMPLETED',x,i+1)
    if x.slot_index%8==0 or stop:
     cp=checkpoint(x,ns,RID);status('CHECKPOINTED',x,i+1,cp)
    if stop:
     status('STOPPED_SAFE',x,i+1,cp);return
   learner=x.dqn;records.append(summarize(x,i+1));records[-1].update(source_start=specs[i]['start'],slots_completed=x.slot_index,accepted=sum(r['accepted'] for r in x.reports),rejected=sum(r['rejected'] for r in x.reports),unmatched=sum(r['unmatched'] for r in x.reports),replay_insertions=sum(r['transitions'] for r in x.reports),fleet_count=len(x.fleet.vehicles),charging_events=len(x.charging_events),reserve_assignment_rejections=x.reserve_assignment_rejections,reserve_rejected_requests=len(x.reserve_rejected_request_ids),reserve_reposition_rejections=reserve_reposition_count(x.routing),price_ineligible_candidate_count=sum(r['price_ineligible_candidate_count'] for r in x.reports));records[-1]['rolling25_revenue']=float(np.mean([r['revenue'] for r in records[-25:]]));records[-1]['rolling25_assignments']=float(np.mean([r['assignments'] for r in records[-25:]]));cp=checkpoint(x,ns,RID);pd.DataFrame(records).to_csv(FINAL/'episode_metrics.csv',index=False)
   if (i+1)%25==0 or i+1 in MONITOR_EPISODES:
    guard('2026-03-16',4,True);dev=ProductionExperiment(start='2026-03-16',seed=424242,routing_checkpoint=ROUTING,frozen_routing=True);dev.dqn=learner;before=learner_fingerprint(learner)
    for j in range(4):
     slot(dev,terminal=j==3,development=True)
     if stop:
      status('STOPPED_SAFE',x,i+1,cp);return
    assert before==learner_fingerprint(learner);development=summarize(dev,i+1);atomic_json(FINAL/f'development_episode_{i+1:04d}.json',development)
    if i+1 in MONITOR_EPISODES:
     monitoring=observe(learner,i+1,records[-1]['mean_loss'],development)
     assert before==learner_fingerprint(learner)
     atomic_json(RUN_OUT/f'monitoring_episode_{i+1:04d}.json',monitoring)
   atomic_json(statepath,dict(episode_index=i+1,dqn_checkpoint=str(Path(cp)/'dqn'),records=records))
  atomic_json(FINAL/'convergence_review.json',dict(status='REVIEW_REQUIRED',candidate_episode=500,CONVERGENCE_ESTABLISHED='INCONCLUSIVE',automatic_extension=False))
  status('COMPLETED',x,500,cp)
 except Exception as exc:
  atomic_json(RUN_OUT/'failure.json',dict(error=repr(exc),pid=os.getpid()));raise
 finally:
  for sig,handler in old.items():signal.signal(sig,handler)
  lock.close()
