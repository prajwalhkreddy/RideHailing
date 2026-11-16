"""Stage-3 V3_FULL_RUNTIME_1 adapter with cumulative engine/audit counters.
Episode-1 reader and its hashed source remain unchanged.
"""
from pathlib import Path
import hashlib,json,os,platform,random,tempfile,time
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import tensorflow as tf
from src.simulation.v3_checkpoint_codec import encode,decode
from src.pricing.slot_v3 import ROOT,CONTRACT,VERSION,load_contract,allowed,validate_state
from src.simulation.slot_pricing_v3 import SlotPricingV3
from src.simulation.final_production import ProductionExperiment
from src.rl.slot_pricing_v3 import SlotDQN
from src.rl.pricing_dqn import PricingDQN
from src.routing.learning import load_final_policy
from src.fleet.fleet import validate_fleet

SCHEMA='V3_FULL_RUNTIME_1'
ENGINE_EXTERNAL={'grid','neighbours','policy','dqn'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def software():
    return dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,tensorflow=tf.__version__)


def artifacts(runtime):
    from src.simulation.temporal_protocol import CONFIG,protocol
    base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
    paths=[CONTRACT,CONFIG,ROOT/'config/config.yaml',ROOT/'data/processed/grid_metadata.json',
           ROOT/'data/processed/grid_lookup.parquet',base/'neighbour_map.parquet',base/'charging_stations.parquet',
           base/'destination_popularity.parquet',base/'destination_popularity_thresholds.json',
           ROOT/protocol()['rl_forecast_path'],ROOT/'results/analysis/2026-10-19_operational_grid_state/dqn_ready_forecasts.parquet',
           Path(runtime.routing_checkpoint_path),
           ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json',
           ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_manifest.csv',
           ROOT/'results/analysis/2026-11-15_v3_remaining_decisions/dropoff_probability_contract.json',
           base/'demand_master_jan_mar_2026.parquet',base/'trips_jan_mar_2026.parquet']
    paths += [ROOT/p for p in load_contract()['source_hashes']]
    paths += [ROOT/p for p in ['src/simulation/v3_checkpoint.py','src/simulation/v3_checkpoint_codec.py',
        'src/simulation/v3_episode1_protocol.py','scripts/train_v3_episode1.py',
        'src/simulation/slot_pricing_v3.py','src/rl/slot_pricing_v3.py','src/pricing/slot_v3.py',
        'src/simulation/final_production.py','src/simulation/operational_state.py',
        'src/routing/final_state.py','src/routing/operational_interface.py']]
    paths += [ROOT/'src/simulation/v3_stage2_checkpoint.py',ROOT/'src/simulation/v3_stage2_protocol.py',ROOT/'scripts/train_v3_stage2.py',ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/training/stage_ep02_ep10/stage2_protocol.json']
    paths += [ROOT/'src/simulation/v3_stage3_checkpoint.py',ROOT/'src/simulation/v3_stage3_protocol.py',ROOT/'scripts/train_v3_stage3.py',ROOT/'scripts/handoff_v3_ep25.py',ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/training/stage_ep11_ep25/stage3_protocol.json']
    return {str(p.resolve()):digest(p) for p in dict.fromkeys(paths)}


def boundary(r):
    e=r.engine
    if getattr(r,'checkpoint_phase',None)!='POST_SLOT_COMMIT' or not 1<=r.slots<=16:
        raise ValueError('UNSAFE_CHECKPOINT_BOUNDARY')
    allowed(e.timestamp)
    if not 11<=r.episode<=25:raise ValueError('Stage3 episode outside approved bounds')
    total=(r.episode-1)*16+r.slots
    if e.timestamp!=pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*total):raise ValueError('Stage3 chronology')
    if e.timestamp!=e.clock or e.operational.timestamp!=e.timestamp or e.slot_index!=total:
        raise ValueError('UNSAFE_CHECKPOINT_BOUNDARY: clocks')
    if len(r.slot_audit)!=142*total or len(r.learner.replay)!=142*total:
        raise ValueError('Incomplete slot transition commit')
    validate_fleet(e.fleet.vehicles,range(142),e.fleet_size)
    for s in r.states.values():validate_state(s)
    frame=e.operational.state_for(e.timestamp)
    if not np.isfinite(frame[['mu','sigma','F_hat','H_hat']]).all().all():raise ValueError('Invalid operational state')


def rng_bundle():
    g=tf.random.get_global_generator()
    return dict(python=random.getstate(),numpy=np.random.get_state(),tensorflow=g.state.numpy(),tensorflow_algorithm=int(g.algorithm))


def restore_rng(b):
    random.setstate(b['python']);np.random.set_state(b['numpy'])
    tf.random.set_global_generator(tf.random.Generator.from_state(b['tensorflow'],b['tensorflow_algorithm']))


def write_json(p,value):
    with p.open('w') as f:json.dump(value,f,allow_nan=False);f.flush();os.fsync(f.fileno())


def save_v3_checkpoint(runtime,checkpoint_dir):
    boundary(runtime);start=time.perf_counter();p=Path(checkpoint_dir)
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix='.'+p.name+'.writing-',dir=p.parent))
    write_json(temp/'status.json',{'checkpoint_status':'WRITING'})
    c=load_contract();e=runtime.engine
    # Every mutable owner is explicit; duplicate ledger references are relinked on load.
    payload={'runtime':{k:v for k,v in vars(runtime).items() if k not in {'engine','learner'}},
             'engine':{k:v for k,v in vars(e).items() if k not in ENGINE_EXTERNAL},'rng':rng_bundle()}
    write_json(temp/'runtime.json',encode(payload))
    runtime.learner.save(temp/'learner')
    # Inert legacy constructor member is preserved, never used for V3 pricing.
    e.dqn.save(temp/'inactive_engine_learner')
    manifest=dict(checkpoint_schema_version=SCHEMA,methodology_version=VERSION,versions=c['versions'],
                  routing_action_version='CURRENT_ROUTING_9',operational_state_version='OperationalGridState_1',
                  replay_schema='V3_15D_DESTINATION_SLOT_DEQUE_1',checkpoint_phase='POST_SLOT_COMMIT',
                  checkpoint_status='COMPLETE',episode=runtime.episode,slot=runtime.slots,
                  absolute_timestamp=str(e.timestamp),terminal=runtime.slots==16,
                  optimizer_updates=runtime.learner.training_steps,
                  exploration_epsilon=runtime.learner.epsilon,
                  exploration_position=runtime.learner.training_steps,exploration_basis='optimizer_update',
                  replay_size=len(runtime.learner.replay),replay_capacity=runtime.learner.replay.maxlen,
                  seed=runtime.seed,created_at=datetime.now(timezone.utc).isoformat(),
                  FARE_SUPPORT='P0.5–P99.5',FARE_RANGE=[6.60,94.70],ACTION_FACTORS=c['actions'],
                  output_dimension=7,software=software(),artifact_hashes=artifacts(runtime))
    write_json(temp/'status.json',{'checkpoint_status':'COMPLETE'})
    files={str(f.relative_to(temp)):digest(f) for f in temp.rglob('*') if f.is_file()}
    manifest['component_hashes']=files
    write_json(temp/'manifest.json',manifest)
    for f in temp.rglob('*'):
        if f.is_file():
            with f.open('rb') as stream:os.fsync(stream.fileno())
    fd=os.open(temp,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    os.rename(temp,p)
    fd=os.open(p.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return {'seconds':time.perf_counter()-start,'bytes':sum(f.stat().st_size for f in p.rglob('*') if f.is_file()),'manifest':manifest}


def load_v3_checkpoint(checkpoint_dir):
    p=Path(checkpoint_dir);m=json.loads((p/'manifest.json').read_text());c=load_contract()
    required={'checkpoint_schema_version':SCHEMA,'methodology_version':VERSION,'versions':c['versions'],
              'ACTION_FACTORS':c['actions'],'FARE_RANGE':[6.6,94.7],'output_dimension':7,
              'routing_action_version':'CURRENT_ROUTING_9','operational_state_version':'OperationalGridState_1',
              'replay_schema':'V3_15D_DESTINATION_SLOT_DEQUE_1','checkpoint_phase':'POST_SLOT_COMMIT',
              'checkpoint_status':'COMPLETE','software':software(),'replay_capacity':100000}
    if any(m.get(k)!=v for k,v in required.items()):raise ValueError('Incompatible V3 checkpoint manifest')
    allowed(m['absolute_timestamp'])
    required_files={'runtime.json','status.json','learner/online.keras','learner/target.keras','learner/replay.npz','learner/checkpoint.json'}
    if not required_files.issubset(m['component_hashes']):raise ValueError('Missing checkpoint component')
    actual={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.name!='manifest.json'}
    if actual!=set(m['component_hashes']):raise ValueError('Missing or unlisted checkpoint component')
    for rel,h in m['component_hashes'].items():
        f=(p/rel).resolve()
        if not f.is_relative_to(p.resolve()) or not f.is_file() or digest(f)!=h:raise ValueError('Corrupt component: '+rel)
    if json.loads((p/'status.json').read_text()).get('checkpoint_status')!='COMPLETE':raise ValueError('Incomplete checkpoint')
    for path,h in m['artifact_hashes'].items():
        if digest(path)!=h:raise ValueError('Immutable artifact mismatch: '+path)
    # No runtime instance is mutated; publish only after complete validation.
    saved_globals=rng_bundle()
    try:
        d=decode(json.loads((p/'runtime.json').read_text()))
        r=object.__new__(SlotPricingV3);r.__dict__.update(d['runtime'])
        e=object.__new__(ProductionExperiment);e.__dict__.update(d['engine']);r.engine=e
        import geopandas as gpd
        e.grid=gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet')
        e.neighbours=pd.read_parquet(e.base/'neighbour_map.parquet')
        if str(Path(r.routing_checkpoint_path).resolve()) not in m['artifact_hashes']:raise ValueError('Missing routing identity')
        if artifacts(r)!=m['artifact_hashes']:raise ValueError('Incomplete immutable artifact manifest')
        e.policy=load_final_policy(r.routing_checkpoint_path)
        e.dqn=PricingDQN.load(p/'inactive_engine_learner')
        r.learner=SlotDQN.load(p/'learner')
        e.current_states.ledger=e.ledger
        boundary(r)
        if r.slots!=m['slot'] or str(e.timestamp)!=m['absolute_timestamp'] or len(r.learner.replay)!=m['replay_size'] or r.learner.training_steps!=m['optimizer_updates'] or r.learner.training_steps!=m['exploration_position']:
            raise ValueError('Manifest/state mismatch')
        if r.episode!=m['episode'] or (r.slots==16)!=m['terminal'] or r.learner.epsilon!=m['exploration_epsilon']:raise ValueError('Temporal/exploration metadata mismatch')
        if m.get('exploration_basis')!='optimizer_update':raise ValueError('Exploration basis mismatch')
        if r.provider.contract!=c:raise ValueError('Distribution contract mismatch')
        for net in (r.learner.online,r.learner.target):
            if any(not np.isfinite(w).all() for w in net.get_weights()):raise ValueError('Nonfinite model')
        if any(not np.isfinite(v.numpy()).all() for v in r.learner.online.optimizer.variables):raise ValueError('Nonfinite optimizer')
    except Exception:
        restore_rng(saved_globals)
        raise
    restore_rng(d['rng']);return r
