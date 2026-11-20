"""Atomic, versioned OD runtime snapshots using the existing explicit value codec."""
import json
import os
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
from src.simulation.v3_checkpoint import (ENGINE_EXTERNAL, digest, software, artifacts,
    rng_bundle, restore_rng, write_json)
from src.simulation.v3_checkpoint_codec import encode, decode
from src.pricing.od_contract import VERSION, pairs_from_support, od_states, validate_state
from src.pricing.dispatch_reward import REWARD_VERSION
from src.pricing.slot_v3 import ROOT, allowed, load_contract
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.final_production import ProductionExperiment
from src.rl.od_pricing_dqn import ODPricingDQN
from src.rl.pricing_dqn import PricingDQN
from src.routing.learning import load_final_policy
from src.fleet.fleet import validate_fleet

SCHEMA = 'FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_5'
from src.simulation.master_operational_state import MasterOperationalGridState
from src.simulation.operational_state import OperationalGridState
import copy
from src.pricing.binned_sampler import BinnedSensitivity
from src.pricing.weighted_binned_sampler import restore_sensitivity
from src.simulation.historical_request_replay import PROTOCOL
SOURCES = ['src/simulation/multi_episode_od.py','src/routing/online_provenance.py','src/routing/research_hierarchy.py','src/routing/research_feedback.py','src/fleet/research_mixed.py','src/charging/energy.py','src/dispatch/dispatch.py','src/simulation/research_utility_routing.py','src/simulation/information_cutoff.py','src/pricing/prospective_binned_sampler.py','src/pricing/unseen_od.py','src/simulation/utc_od_state.py','src/simulation/utc_od_inputs.py','src/simulation/utc_od_codec.py','src/simulation/master_operational_state.py', 'src/simulation/master_od_contract.py', 'src/simulation/historical_request_replay.py', 'src/pricing/od_contract.py', 'src/pricing/dispatch_reward.py',
           'src/rl/od_pricing_dqn.py', 'src/simulation/od_pricing_runtime.py',
           'src/simulation/od_pricing_checkpoint.py', 'src/pricing/binned_sampler.py', 'src/pricing/weighted_binned_sampler.py']


def identities(runtime):
    hashes = artifacts(runtime)
    hashes.update({str((ROOT/p).resolve()): digest(ROOT/p) for p in SOURCES})
    if isinstance(runtime.provider, BinnedSensitivity):
        hashes[runtime.provider.calibration_path] = runtime.provider.calibration_hash
    return hashes


def boundary(r):
    from src.pricing.unseen_od import validate
    validate(r.fallback_contract)
    from src.pricing.prospective_binned_sampler import VERSION as PROSPECTIVE
    if getattr(r.provider,'VERSION',None)==PROSPECTIVE and r.information_contract is None:raise ValueError('Prospective checkpoint lacks cutoff contract')
    if r.information_contract is not None:
        from src.simulation.information_cutoff import validate_manifest
        validate_manifest(r.information_contract)
    e = r.engine
    h=getattr(e,'driver_hierarchy',None)
    if h is not None and (h.round!=r.slots+getattr(r,'episode_offset',0) or h.available_at!=e.timestamp):raise ValueError('Federation checkpoint boundary mismatch')
    composition=getattr(e,'ev_composition',None)
    if composition is not None and (sum(getattr(v,'is_ev',True) for v in e.fleet.vehicles)!=composition['ev_count'] or len(e.fleet.vehicles)!=composition['fleet_size']):raise ValueError('EV composition checkpoint mismatch')
    if r.checkpoint_phase != 'OD_POST_SLOT_COMMIT' or not 1 <= r.slots <= 16:
        raise ValueError('Unsafe OD checkpoint boundary')
    from src.simulation.historical_request_replay import _time
    _time(e.timestamp,r.utc_mode)
    if r.utc_mode:
        from src.simulation.utc_od_state import instant
        for value in [e.clock,e.operational.timestamp,*e.ledger.completed]:instant(value,True)
        for c in e.passengers.values():
            instant(c.committed_at);instant(c.dropoff_at)
    if r.demand_state.get('protocol')!=PROTOCOL or r.demand_state.get('next_slot')!=str(e.timestamp) or r.demand_state.get('slots_completed')!=r.slots:
        raise ValueError('Demand protocol/cursor mismatch')
    if r.demand_state['requests_consumed']!=len(r.audit) or len(r.demand_audit)!=r.slots:
        raise ValueError('Demand request reconciliation mismatch')
    if e.clock != e.timestamp or e.operational.timestamp != e.timestamp or e.slot_index != r.slots:
        raise ValueError('OD clock mismatch')
    if r.reward_version != REWARD_VERSION or r.provider.contract != load_contract():
        raise ValueError('OD reward/pricing contract mismatch')
    if r.pairs != pairs_from_support(r.od_support) or tuple(r.states) != r.pairs:
        raise ValueError('OD support/state mismatch')
    history=getattr(r,'prior_slot_audit',[])+r.slot_audit
    if len(r.slot_audit) != len(r.pairs)*r.slots or len(r.learner.replay) != min(100000, len(history)) or len(r.learner.identities) != len(r.learner.replay):
        raise ValueError('Incomplete OD replay commit')
    expected = [(s['slot'], s['origin_grid'], s['destination_grid']) for s in history][-100000:]
    if list(r.learner.identities) != expected:
        raise ValueError('OD replay identities mismatch')
    for row, transition in zip(history[-100000:], r.learner.replay):
        if row['learning_reward'] != transition[2] or not np.isclose(row['assignment_revenue'], transition[2]):
            raise ValueError('OD replay reward mismatch')
    if len(r.fallback_audit)!=r.slots:raise ValueError('Incomplete fallback accounting')
    for row in r.audit:
        fallback=row['od_context'] not in r.pairs
        if row['is_fallback']!=fallback or (fallback and r.fallback_contract is None):raise ValueError('Fallback/support identity mismatch')
        if fallback and (row['factor']!=r.fallback_contract['factor'] or row['P_offer']!=row['P_base']*row['factor']):raise ValueError('Fallback price mismatch')
    for summary in r.fallback_audit:
        rr=[row for row in r.audit if row['slot']==summary['slot']]
        supported=sum(row['reward_contribution'] for row in rr if not row['is_fallback'])
        fallback=sum(row['reward_contribution'] for row in rr if row['is_fallback'])
        if not np.allclose([supported,fallback,supported+fallback],[summary['supported_reward'],summary['fallback_revenue'],summary['total_system_revenue']],rtol=1e-12,atol=1e-9):raise ValueError('Fallback revenue mismatch')
    expected_states = od_states(e, r.pairs)
    for pair, state in r.states.items():
        validate_state(state)
        if not np.array_equal(state, expected_states[pair]): raise ValueError('OD state reconstruction mismatch')
    validate_fleet(e.fleet.vehicles, range(142), e.fleet_size)
    if not np.isfinite(e.operational.state_for(e.timestamp)[['mu','sigma','F_hat','H_hat']]).all().all():
        raise ValueError('Invalid operational state')


def save_od_checkpoint(runtime, path):
    boundary(runtime)
    p = Path(path)
    if p.exists(): raise FileExistsError(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.'+p.name+'.writing-', dir=p.parent))
    e = runtime.engine
    payload = dict(runtime={k:v for k,v in vars(runtime).items() if k not in {'engine','learner'}},
                   engine={k:v for k,v in vars(e).items() if k not in ENGINE_EXTERNAL}, rng=rng_bundle())
    hierarchy=getattr(e,'driver_hierarchy',None)
    payload['engine']['driver_hierarchy']=None if hierarchy is None else hierarchy.snapshot()
    if isinstance(runtime.provider, BinnedSensitivity):
        payload['runtime']['provider'] = runtime.provider.snapshot()
    # Serialize the new state explicitly without changing the historical codec.
    if runtime.master_math:
        state=copy.copy(e.operational);state.__class__=OperationalGridState
        payload['engine']['operational']=state
    from src.simulation.utc_od_codec import adapt
    write_json(temp/'runtime.json', encode(adapt(payload) if runtime.utc_mode else payload))
    runtime.learner.save(temp/'learner'); e.dqn.save(temp/'inactive_engine_learner')
    manifest = dict(schema=SCHEMA, demand_protocol=PROTOCOL, version=VERSION, reward_contract=REWARD_VERSION,
                    software=software(), support_hash=runtime.od_support['support_sha256'],
                    artifact_hashes=identities(runtime), slot=runtime.slots,
                    timestamp=str(e.timestamp), state_dimension=13, action_dimension=7,
                    config=encode(runtime.provider.contract), checkpoint_status='COMPLETE')
    manifest['orchestration_contract'] = 'CHRONOLOGICAL_OD_V1' if getattr(runtime,'multi_episode',False) else 'SINGLE_EPISODE_V1'
    manifest['forecast_input_protocol'] = getattr(e,'utc_inputs',{}).get('forecast_protocol','EXISTING_PERSISTENCE_OR_LEGACY')
    manifest['hierarchy']=None if hierarchy is None else hierarchy.contract()
    manifest['ev_composition']=getattr(e,'ev_composition',None)
    manifest['information_contract'] = runtime.information_contract
    manifest['unseen_od_policy'] = runtime.fallback_contract
    manifest['mathematics'] = runtime.learner.loss_contract
    manifest['temporal_protocol'] = 'OD_AWARE_UTC_ELAPSED_V1' if runtime.utc_mode else 'LEGACY_NAIVE_CLOCK_BLOCKED_FOR_CAUSAL_OPERATION'
    manifest['forecast_provenance'] = 'ASSUMED_120_MINUTE_RESEARCH_ONLY' if runtime.utc_mode else 'LEGACY_ARTIFACT_UNVERIFIED'
    manifest['sensitivity'] = dict(version=runtime.provider.calibration['version'], sha256=runtime.provider.calibration_hash) if isinstance(runtime.provider,BinnedSensitivity) else dict(version='HISTORICAL_V3')
    manifest['component_hashes'] = {str(f.relative_to(temp)):digest(f) for f in temp.rglob('*') if f.is_file()}
    write_json(temp/'manifest.json', manifest)
    for f in temp.rglob('*'):
        if f.is_file():
            with f.open('rb') as stream: os.fsync(stream.fileno())
    fd = os.open(temp, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    os.rename(temp, p)
    fd = os.open(p.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return manifest


def load_od_checkpoint(path, *, master_math=False, utc_mode=False, fallback_contract=None, information_contract=None, hierarchy_contract=None, ev_composition=None, multi_episode=False):
    from src.pricing.unseen_od import validate
    fallback_contract=validate(fallback_contract)
    if information_contract is not None:
        from src.simulation.information_cutoff import validate_manifest
        validate_manifest(information_contract)
    p = Path(path); m = json.loads((p/'manifest.json').read_text())
    required = dict(hierarchy=hierarchy_contract,ev_composition=ev_composition,information_contract=information_contract, unseen_od_policy=fallback_contract, mathematics='MASTER_HALF_SQUARED_BELLMAN_V1' if master_math else 'HISTORICAL_OD_HUBER_V1', temporal_protocol='OD_AWARE_UTC_ELAPSED_V1' if utc_mode else 'LEGACY_NAIVE_CLOCK_BLOCKED_FOR_CAUSAL_OPERATION', forecast_provenance='ASSUMED_120_MINUTE_RESEARCH_ONLY' if utc_mode else 'LEGACY_ARTIFACT_UNVERIFIED', schema=SCHEMA, demand_protocol=PROTOCOL, version=VERSION, reward_contract=REWARD_VERSION,
                    software=software(), state_dimension=13, action_dimension=7,
                    config=encode(load_contract()), checkpoint_status='COMPLETE')
    if m.get('orchestration_contract','SINGLE_EPISODE_V1') != ('CHRONOLOGICAL_OD_V1' if multi_episode else 'SINGLE_EPISODE_V1'):raise ValueError('Incompatible orchestration checkpoint')
    if any(m.get(k) != v for k,v in required.items()): raise ValueError('Incompatible OD runtime checkpoint')
    actual = {str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f != p/'manifest.json'}
    if actual != set(m['component_hashes']): raise ValueError('Missing/unlisted OD components')
    for rel, h in m['component_hashes'].items():
        f = (p/rel).resolve()
        if not f.is_relative_to(p.resolve()) or digest(f) != h: raise ValueError('Corrupt OD component')
    for f,h in m['artifact_hashes'].items():
        if digest(f) != h: raise ValueError('Changed OD artifact: '+f)
    saved = rng_bundle()
    try:
        payload = decode(json.loads((p/'runtime.json').read_text()))
        if utc_mode:
            from src.simulation.utc_od_codec import adapt
            payload=adapt(payload,restore=True)
        r = object.__new__(ODPricingRuntime); r.__dict__.update(payload['runtime'])
        if isinstance(r.provider, dict):
            r.provider = restore_sensitivity(r.provider)
        sensitivity = dict(version=r.provider.calibration['version'], sha256=r.provider.calibration_hash) if isinstance(r.provider,BinnedSensitivity) else dict(version='HISTORICAL_V3')
        if m.get('sensitivity') != sensitivity: raise ValueError('Incompatible sensitivity version')
        if r.information_contract != information_contract:raise ValueError('Information-cutoff checkpoint mismatch')
        if r.fallback_contract != fallback_contract: raise ValueError('Incompatible unseen-OD policy')
        if r.utc_mode != utc_mode or r.master_math != master_math: raise ValueError('Incompatible EWMA contract')
        e = object.__new__(ProductionExperiment); e.__dict__.update(payload['engine']); r.engine = e
        if e.driver_hierarchy is not None:
            from src.routing.research_hierarchy import DriverHierarchy
            if 'online_provenance' in e.driver_hierarchy:
                from src.routing.online_provenance import OnlineHierarchy
                e.driver_hierarchy=OnlineHierarchy.restore(e.driver_hierarchy)
            else:e.driver_hierarchy=DriverHierarchy.restore(e.driver_hierarchy)
            actual=e.driver_hierarchy.contract()
            if actual!=hierarchy_contract:raise ValueError('Hierarchy configuration mismatch')
        if getattr(e,'ev_composition',None)!=ev_composition:raise ValueError('Fleet composition mismatch')
        if m.get('forecast_input_protocol') != getattr(e,'utc_inputs',{}).get('forecast_protocol','EXISTING_PERSISTENCE_OR_LEGACY'):raise ValueError('Forecast protocol mismatch')
        if master_math: e.operational.__class__=MasterOperationalGridState
        import geopandas as gpd
        e.grid = gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet')
        e.neighbours = pd.read_parquet(e.base/'neighbour_map.parquet')
        if identities(r) != m['artifact_hashes']: raise ValueError('Incomplete OD provenance')
        if getattr(e,"research_routing",False):
            from src.simulation.research_utility_routing import validate
            if hasattr(e.driver_hierarchy,'provenance'):
                if json.loads(Path(r.routing_checkpoint_path).read_text())!=e.driver_hierarchy.provenance:raise ValueError('Online checkpoint lineage mismatch')
            else:validate(r.routing_checkpoint_path)
            e.policy=None
        else:e.policy = load_final_policy(r.routing_checkpoint_path)
        e.dqn = PricingDQN.load(p/'inactive_engine_learner')
        r.learner = ODPricingDQN.load(p/'learner',master_math=master_math,utc_mode=utc_mode,exploration_contract='MASTER_UPDATE_STAIRCASE_V1' if multi_episode else 'HISTORICAL_LINEAR_V1'); e.current_states.ledger = e.ledger
        boundary(r)
        if r.slots != m['slot'] or str(e.timestamp) != m['timestamp'] or r.od_support['support_sha256'] != m['support_hash']:
            raise ValueError('OD manifest/runtime mismatch')
    except Exception:
        restore_rng(saved)
        raise
    restore_rng(payload['rng'])
    return r
