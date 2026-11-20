"""Approved chronological research orchestration; historical single episodes unchanged."""
from contextlib import contextmanager
from pathlib import Path
import copy,json,os,shutil
import numpy as np
import pandas as pd
VERSION='CHRONOLOGICAL_OD_V1'
START=pd.Timestamp('2026-03-01T05:00Z')
END=START+pd.Timedelta(hours=35*8)
def episode_bounds(index):
    if type(index) is not int or not 0<=index<35:raise ValueError('Episode outside approved budget')
    a=START+pd.Timedelta(hours=index*8)
    return a,a+pd.Timedelta(hours=8)
def validate_start(start,h,evaluation=False):
    from src.routing.online_provenance import MULTI_VERSION,utc
    t=utc(start)
    if h.provenance['version']!=MULTI_VERSION:raise ValueError('Multi-episode routing version required')
    if evaluation:
        if h.updates_enabled or not pd.Timestamp('2026-03-13T04:00Z')<=t<pd.Timestamp('2026-03-17T04:00Z') or t<h.experience_cutoff:raise ValueError('Invalid frozen evaluation boundary')
    elif not START<=t<END or t!=START+pd.Timedelta(minutes=30*h.round) or h.round%16:raise ValueError('Invalid chronological episode boundary')

def fleet_identity(r):
    return tuple((v.vehicle_id,v.is_ev) for v in r.engine.fleet.vehicles)
def advance_episode(r,factory):
    """Factory creates a physical reset at next UTC boundary using retained hierarchy."""
    from src.simulation.v3_checkpoint import rng_bundle,restore_rng
    from src.pricing.od_contract import od_states
    if not r.multi_episode or r.slots!=16 or r.evaluation_mode:raise ValueError('Only complete training episodes can advance')
    index=getattr(r,'episode_offset',0)//16+1
    start,_=episode_bounds(index)
    if r.engine.timestamp!=start:raise ValueError('Nonchronological reset')
    h=r.engine.driver_hierarchy
    if h.round!=index*16:raise ValueError('Federation round mismatch')
    identities=fleet_identity(r)
    if not set(h._memory).issubset({x[0] for x in identities}):raise ValueError('Unknown private-memory driver')
    saved=rng_bundle()
    try:new=factory(start,h)
    finally:restore_rng(saved) # constructors seed networks; never reset the training random stream
    if fleet_identity(new)!=identities or not new.engine.profiles.equals(r.engine.profiles):raise ValueError('Reset changed driver identities/preferences')
    new.learner=r.learner;new.provider=r.provider
    new.prior_slot_audit=(getattr(r,'prior_slot_audit',[])+r.slot_audit)[-100000:]
    new.episode_offset=index*16;new.episode=index;new.engine.routing_slot_offset=index*16
    new.states=od_states(new.engine,new.pairs)
    if new.engine.passengers or new.engine.missions or new.engine.charging.vehicle_station:raise ValueError('Physical reset incomplete')
    new.reset_evidence=dict(previous_timestamp=str(r.engine.timestamp),episode=index+1,identities_unchanged=True,learner_identity_preserved=new.learner is r.learner,hierarchy_identity_preserved=new.engine.driver_hierarchy is h,provider_rng_preserved=new.provider is r.provider,censored_passengers=len(r.engine.passengers),censored_charging=len(r.engine.charging.vehicle_station),censored_missions=len(r.engine.missions))
    return new

def replay_diagnostics(r):
    ids=list(r.learner.identities);rewards=np.array([x[2] for x in r.learner.replay])
    ages=np.array([(r.engine.timestamp-pd.Timestamp(x[0])).total_seconds()/1800 for x in ids])
    generated=(getattr(r,'episode_offset',0)+r.slots)*len(r.pairs)
    return dict(generated=generated,retained=len(ids),evicted=generated-len(ids),distinct_od=len({tuple(x[1:]) for x in ids}),zero_reward_fraction=float(np.mean(rewards==0)),positive_reward_fraction=float(np.mean(rewards>0)),age_slots_quantiles=np.quantile(ages,[0,.5,.9,1]).tolist(),episode_zero_request_contexts=sum(x['generated']==0 for x in r.slot_audit))

@contextmanager
def isolated_evaluation(training,start,factory,seed=42):
    """Independent physical/learner state; caller must use yielded greedy step only."""
    from src.simulation.v3_checkpoint import rng_bundle,restore_rng
    from src.routing.research_hierarchy import DriverHierarchy
    from src.pricing.od_contract import od_states
    class Frozen(DriverHierarchy):
        def record(self,*args,**kwargs):pass
        def finish_slot(self,start,end):
            if end-start!=pd.Timedelta(minutes=30) or start<self.experience_cutoff:raise ValueError('Evaluation clock mismatch')
            self.available_at=end;self.last_end=end
            return dict(participants=0)
    saved=rng_bundle()
    try:
        h=training.engine.driver_hierarchy
        frozen=Frozen(mode='FRESH_UNTRAINED_GLOBAL',seed=seed,updates_enabled=False,parameters=h.parameters,aggregation=h.aggregation)
        frozen._global.set_weights(h._global.get_weights());frozen.provenance=copy.deepcopy(h.provenance)
        frozen.experience_cutoff=h.experience_cutoff;frozen.available_at=h.available_at;frozen.global_version=h.global_version
        e=factory(start,frozen,evaluation_mode=True)
        e.learner.online.set_weights(training.learner.online.get_weights());e.learner.target.set_weights(training.learner.target.get_weights())
        def forbidden_update():raise ValueError('Frozen evaluation forbids optimizer updates')
        e.learner.train_step=forbidden_update
        e.states=od_states(e.engine,e.pairs)
        def step(**kwargs):
            if e.slots>=16:raise ValueError('Evaluation window finished')
            return e.run_slot(policy=lambda pair,state:e.learner.select_action(state,explore=False),**kwargs)
        yield e,step
    finally:restore_rng(saved)

def retain_checkpoint(r,root,role='latest',writer=None):
    """At most three designated generations plus one atomic writer staging directory."""
    from src.simulation.od_pricing_checkpoint import save_od_checkpoint
    if role not in {'latest','best','milestone'}:raise ValueError('Unknown checkpoint role')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if any(x.name.startswith('.') and '.writing-' in x.name for x in root.iterdir()):raise RuntimeError('Interrupted staging generation needs explicit inspection')
    size=sum(x.stat().st_size for x in root.rglob('*') if x.is_file() and not x.is_symlink())
    free=shutil.disk_usage(root).free
    if size>80*1024**3 or free<70*1024**3:raise RuntimeError('Checkpoint growth/free-space guard')
    pointer=root/role;old=pointer.resolve() if pointer.is_symlink() else None
    name=f'{role}_episode{getattr(r,"episode_offset",0)//16+1:02d}_slot{r.slots:02d}'
    target=root/name
    (writer or save_od_checkpoint)(r,target)
    n=sum(x.stat().st_size for x in target.rglob('*') if x.is_file())
    if n>20*1024**3:raise RuntimeError('Checkpoint exceeds projected generation size; old pointer preserved')
    tmp=root/('.'+role+'.new');tmp.symlink_to(target.name);os.replace(tmp,pointer)
    fd=os.open(root,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    if old is not None and old!=target:
        if old.parent!=root.resolve() or not old.name.startswith(role+'_episode'):raise ValueError('Unsafe retirement path')
        shutil.rmtree(old)
    return target
