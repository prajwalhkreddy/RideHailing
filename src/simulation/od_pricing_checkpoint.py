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

SCHEMA = 'FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_3'
from src.pricing.binned_sampler import BinnedSensitivity
from src.pricing.weighted_binned_sampler import restore_sensitivity
from src.simulation.historical_request_replay import PROTOCOL
SOURCES = ['src/simulation/historical_request_replay.py', 'src/pricing/od_contract.py', 'src/pricing/dispatch_reward.py',
           'src/rl/od_pricing_dqn.py', 'src/simulation/od_pricing_runtime.py',
           'src/simulation/od_pricing_checkpoint.py', 'src/pricing/binned_sampler.py', 'src/pricing/weighted_binned_sampler.py']


def identities(runtime):
    hashes = artifacts(runtime)
    hashes.update({str((ROOT/p).resolve()): digest(ROOT/p) for p in SOURCES})
    if isinstance(runtime.provider, BinnedSensitivity):
        hashes[runtime.provider.calibration_path] = runtime.provider.calibration_hash
    return hashes


def boundary(r):
    e = r.engine
    if r.checkpoint_phase != 'OD_POST_SLOT_COMMIT' or not 1 <= r.slots <= 16:
        raise ValueError('Unsafe OD checkpoint boundary')
    allowed(e.timestamp)
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
    if len(r.slot_audit) != len(r.pairs)*r.slots or len(r.learner.replay) != min(100000, len(r.slot_audit)) or len(r.learner.identities) != len(r.learner.replay):
        raise ValueError('Incomplete OD replay commit')
    expected = [(s['slot'], s['origin_grid'], s['destination_grid']) for s in r.slot_audit][-100000:]
    if list(r.learner.identities) != expected:
        raise ValueError('OD replay identities mismatch')
    for row, transition in zip(r.slot_audit[-100000:], r.learner.replay):
        if row['learning_reward'] != transition[2] or not np.isclose(row['assignment_revenue'], transition[2]):
            raise ValueError('OD replay reward mismatch')
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
    if isinstance(runtime.provider, BinnedSensitivity):
        payload['runtime']['provider'] = runtime.provider.snapshot()
    write_json(temp/'runtime.json', encode(payload))
    runtime.learner.save(temp/'learner'); e.dqn.save(temp/'inactive_engine_learner')
    manifest = dict(schema=SCHEMA, demand_protocol=PROTOCOL, version=VERSION, reward_contract=REWARD_VERSION,
                    software=software(), support_hash=runtime.od_support['support_sha256'],
                    artifact_hashes=identities(runtime), slot=runtime.slots,
                    timestamp=str(e.timestamp), state_dimension=13, action_dimension=7,
                    config=encode(runtime.provider.contract), checkpoint_status='COMPLETE')
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


def load_od_checkpoint(path):
    p = Path(path); m = json.loads((p/'manifest.json').read_text())
    required = dict(schema=SCHEMA, demand_protocol=PROTOCOL, version=VERSION, reward_contract=REWARD_VERSION,
                    software=software(), state_dimension=13, action_dimension=7,
                    config=encode(load_contract()), checkpoint_status='COMPLETE')
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
        r = object.__new__(ODPricingRuntime); r.__dict__.update(payload['runtime'])
        if isinstance(r.provider, dict):
            r.provider = restore_sensitivity(r.provider)
        sensitivity = dict(version=r.provider.calibration['version'], sha256=r.provider.calibration_hash) if isinstance(r.provider,BinnedSensitivity) else dict(version='HISTORICAL_V3')
        if m.get('sensitivity') != sensitivity: raise ValueError('Incompatible sensitivity version')
        e = object.__new__(ProductionExperiment); e.__dict__.update(payload['engine']); r.engine = e
        import geopandas as gpd
        e.grid = gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet')
        e.neighbours = pd.read_parquet(e.base/'neighbour_map.parquet')
        if identities(r) != m['artifact_hashes']: raise ValueError('Incomplete OD provenance')
        e.policy = load_final_policy(r.routing_checkpoint_path)
        e.dqn = PricingDQN.load(p/'inactive_engine_learner')
        r.learner = ODPricingDQN.load(p/'learner'); e.current_states.ledger = e.ledger
        boundary(r)
        if r.slots != m['slot'] or str(e.timestamp) != m['timestamp'] or r.od_support['support_sha256'] != m['support_hash']:
            raise ValueError('OD manifest/runtime mismatch')
    except Exception:
        restore_rng(saved)
        raise
    restore_rng(payload['rng'])
    return r
