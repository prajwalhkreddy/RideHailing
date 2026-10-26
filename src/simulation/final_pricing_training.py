"""Resumable execution layer for the frozen non-private pricing experiment."""
from pathlib import Path
import os,json,pickle,hashlib,random,signal,uuid,fcntl
from dataclasses import asdict
import numpy as np,pandas as pd,tensorflow as tf
from src.simulation.final_production import ProductionExperiment
from src.rl.pricing_dqn import PricingDQN,DQNConfig
from src.simulation.temporal_protocol import assert_training_update_allowed
ROOT=Path(__file__).resolve().parents[2]
ROUTING=ROOT/'models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras'
MODEL=ROOT/'models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42'
OUT=ROOT/'results/analysis/2026-10-25_final_nonprivate_pricing_training'
FIELDS=('fleet','charging','operational','ledger','passengers','missions','timestamp','clock','slot_index','request_id','reports','unsupported_demand','reserve_assignment_rejections','reserve_rejected_request_ids','charging_events')

def atomic_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,indent=2,default=str)+'\n');tmp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def weights_hash(model):return hashlib.sha256(b''.join(x.tobytes() for x in model.get_weights())).hexdigest()
def identity():
    selected=json.loads((ROOT/'results/analysis/2026-10-25_final_simulator_routing_training/routing_model_selection.json').read_text())
    digest=sha(ROUTING)
    if selected['checkpoint']!=str(ROUTING.relative_to(ROOT)) or selected['checkpoint_sha256']!=digest:raise ValueError('Selected routing identity mismatch.')
    return dict(path=str(ROUTING),sha256=digest,status='SIMULATOR_DERIVED_ROUTING_BASELINE',ROUTING_EFFECTIVENESS_CONCERN='YES',inference_only=True)
def lock_writer(namespace):
    namespace=Path(namespace);namespace.mkdir(parents=True,exist_ok=True)
    f=(namespace/'writer.lock').open('a')
    try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:f.close();raise RuntimeError('An active pricing writer already holds the lock.')
    return f

def checkpoint(x,namespace,route_identity):
    namespace=Path(namespace);name=f'checkpoint_{x.slot_index:04d}_{uuid.uuid4().hex[:8]}'
    tmp=namespace/('.'+name);tmp.mkdir()
    x.dqn.save(tmp/'dqn')
    state={k:getattr(x,k) for k in FIELDS}
    state.update(request_rng=x.request_rng.bit_generator.state,customer_rng=x.customer.rng.bit_generator.state,python_rng=random.getstate(),numpy_rng=np.random.get_state(),reserve_reposition_rejections=getattr(x.routing,'reserve_reposition_rejections',0))
    (tmp/'simulator.pkl').write_bytes(pickle.dumps(state,protocol=5))
    meta=dict(version=1,slots=x.slot_index,timestamp=str(x.timestamp),routing=route_identity,reachability='EV_POST_MOVEMENT_STATION_REACHABILITY',config=asdict(x.dqn.config),optimizer_steps=x.dqn.training_steps,replay_size=len(x.dqn.replay),epsilon=x.dqn.epsilon,initialization='FRESH_SEED_42',files={str(p.relative_to(tmp)):sha(p) for p in tmp.rglob('*') if p.is_file()})
    atomic_json(tmp/'manifest.json',meta)
    # All payload files are durable before the atomic commit pointer advances.
    for p in tmp.rglob('*'):
        if p.is_file():
            with p.open('rb') as f:os.fsync(f.fileno())
    tmp.rename(namespace/name)
    atomic_json(namespace/'CURRENT.json',dict(directory=name,manifest_sha256=sha(namespace/name/'manifest.json')))
    with (namespace/'CURRENT.json').open('rb') as f:os.fsync(f.fileno())
    return str(namespace/name)

def restore(x,namespace,route_identity):
    namespace=Path(namespace);pointer=json.loads((namespace/'CURRENT.json').read_text());p=namespace/pointer['directory']
    if p.parent!=namespace or sha(p/'manifest.json')!=pointer['manifest_sha256']:raise ValueError('Invalid checkpoint commit.')
    m=json.loads((p/'manifest.json').read_text())
    if m['routing']!=route_identity or m['config']!=asdict(DQNConfig()) or m['reachability']!='EV_POST_MOVEMENT_STATION_REACHABILITY':raise ValueError('Incompatible resume contract.')
    for file,digest in m['files'].items():
        if sha(p/file)!=digest:raise ValueError('Checkpoint payload hash mismatch.')
    state=pickle.loads((p/'simulator.pkl').read_bytes())
    for k in FIELDS:setattr(x,k,state[k])
    x.dqn=PricingDQN.load(p/'dqn')
    x.request_rng.bit_generator.state=state['request_rng'];x.customer.rng.bit_generator.state=state['customer_rng'];random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng'])
    x.routing.reserve_reposition_rejections=state['reserve_reposition_rejections']
    if x.slot_index!=m['slots'] or x.timestamp!=pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*x.slot_index) or x.clock!=x.timestamp:raise ValueError('Checkpoint slot clock mismatch.')
    if (len(x.dqn.replay),x.dqn.training_steps,x.dqn.epsilon)!=(m['replay_size'],m['optimizer_steps'],m['epsilon']):raise ValueError('Checkpoint optimizer/replay mismatch.')
    if x.slot_index<720:x.current_states=x._state_sources()
    return str(p)

def metrics(x,status,cp):
    reports=x.reports;loss=[r['training']['loss'] for r in reports[-8:] if r['training']]
    return dict(status=status,pid=os.getpid(),timestamp=str(x.timestamp),slots_completed=x.slot_index,target_slots=720,requests=sum(r['requests'] for r in reports),accepted=sum(r['accepted'] for r in reports),rejected=sum(r['rejected'] for r in reports),assignments=sum(r['assigned'] for r in reports),unmatched=sum(r['unmatched'] for r in reports),revenue=sum(r['reward'] for r in reports),replay_transitions=sum(r['transitions'] for r in reports),replay_size=len(x.dqn.replay),optimizer_updates=x.dqn.training_steps,epsilon=x.dqn.epsilon,mean_recent_loss=float(np.mean(loss)) if loss else None,fleet_count=len(x.fleet.vehicles),charging_events=len(x.charging_events),reserve_assignment_rejections=x.reserve_assignment_rejections,reserve_rejected_requests=len(x.reserve_rejected_request_ids),reserve_reposition_rejections=getattr(x.routing,'reserve_reposition_rejections',0),checkpoint_path=cp,pricing_action_counts=np.sum([r['pricing_action_counts'] for r in reports],axis=0).tolist() if reports else [0]*7)

def run(*,namespace=MODEL,output=OUT,resume=False,stop_after_slot=720,cadence=8,lock_fd=None):
    namespace=Path(namespace);output=Path(output)
    if not 1<=stop_after_slot<=720 or not 1<=cadence<=8:raise ValueError('Require target 1..720 and checkpoint cadence 1..8.')
    lock=os.fdopen(lock_fd,'a') if lock_fd is not None else lock_writer(namespace)
    output.mkdir(parents=True,exist_ok=True)
    atomic_json(namespace/'process.json',dict(pid=os.getpid(),namespace=str(namespace)))
    stop=[]
    def stopping(sig,frame):stop.append(sig)
    old={s:signal.signal(s,stopping) for s in (signal.SIGINT,signal.SIGTERM)}
    cp=None
    try:
        if resume!=(namespace/'CURRENT.json').exists():raise ValueError('Fresh requires unused namespace; resume requires committed checkpoint.')
        rid=identity();tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
        print(json.dumps(dict(status='STARTING',pid=os.getpid(),routing=rid,resume=resume)),flush=True)
        x=ProductionExperiment(start='2026-03-01',seed=42,routing_checkpoint=ROUTING,frozen_routing=True)
        routing_hash=weights_hash(x.policy)
        if resume:cp=restore(x,namespace,rid)
        else:
            assert not len(x.dqn.replay) and x.dqn.training_steps==0 and x.dqn.epsilon==1.
            for a,b in zip(x.dqn.online.get_weights(),x.dqn.target.get_weights()):np.testing.assert_array_equal(a,b)
            cp=checkpoint(x,namespace,rid)
            atomic_json(namespace/'initialization.json',dict(seed=42,source='FRESH_SEED_42',online_sha256=weights_hash(x.dqn.online),target_sha256=weights_hash(x.dqn.target),replay_size=0,optimizer_steps=0,epsilon=1.,timestamp=str(x.timestamp),checkpoint=cp))
        atomic_json(output/'routing_checkpoint_identity.json',rid)
        initial=metrics(x,'RUNNING',cp);initial['routing_weights_sha256']=routing_hash
        atomic_json(output/'training_status.json',initial);print(json.dumps(initial),flush=True)
        while x.slot_index<stop_after_slot and not stop:
            assert pd.Timestamp('2026-03-01')<=x.timestamp<pd.Timestamp('2026-03-16')
            assert_training_update_allowed(x.timestamp)
            r=x.run_slot(train_dqn=True,terminal=x.slot_index==719)
            assert r['federated_updates']==0 and r['fleet_size']==5000
            assert all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in x.fleet.vehicles)
            assert weights_hash(x.policy)==routing_hash
            if x.slot_index%cadence==0 or x.slot_index%48==0 or x.slot_index==stop_after_slot or stop:
                cp=checkpoint(x,namespace,rid)
                status='COMPLETE' if x.slot_index==720 else 'PAUSED' if stop or x.slot_index==stop_after_slot else 'RUNNING'
                m=metrics(x,status,cp);atomic_json(output/'training_status.json',m)
                pd.DataFrame(x.reports).to_csv(output/'slot_metrics.csv',index=False)
                print(json.dumps(m),flush=True)
        if stop and (not x.reports or x.slot_index%cadence==0):
            atomic_json(output/'training_status.json',metrics(x,'PAUSED',cp))
        return x,cp
    except BaseException as e:
        atomic_json(output/'failure.json',dict(error=repr(e),last_committed_checkpoint=cp,pid=os.getpid()))
        print(json.dumps(dict(status='FAILED',error=repr(e),checkpoint=cp)),flush=True)
        raise
    finally:
        for s,h in old.items():signal.signal(s,h)
        lock.close()
