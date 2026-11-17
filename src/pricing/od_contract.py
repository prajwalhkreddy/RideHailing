"""Observed January OD support and causal master §5.1 state construction."""
import hashlib
import json
import numpy as np
import pandas as pd
from src.pricing.dqn_contract import grid
from src.pricing.slot_v3 import ROOT
from src.dispatch.generation import build_empirical_od_distribution

VERSION = 'FEASIBLE_OD_PRICING_V1'
STATE_DIMENSION = 13


def validate_state(value):
    x = np.asarray(value, dtype=float)
    if x.shape != (13,) or not np.isfinite(x).all() or (x < 0).any() or (x > np.finfo(np.float32).max).any():
        raise ValueError('Finite nonnegative OD 13D state required')
    if not np.isclose(x[3:12].sum(), 1) or x[12] not in (0, .25, .5, .75, 1):
        raise ValueError('Invalid OD routing probabilities or popularity')
    return x.astype(np.float32)


def support_from_trips(trips):
    dates = pd.to_datetime(trips.tpep_pickup_datetime)
    if dates.isna().any() or not ((dates >= '2026-01-01') & (dates < '2026-02-01')).all():
        raise ValueError('OD evidence must contain January 2026 only')
    od = build_empirical_od_distribution(trips, range(142))
    counts = od.empirical_trips.groupby(['PUGridID', 'DOGridID']).size()
    records = [[int(o), int(d), int(n)] for (o, d), n in counts.sort_index().items()]
    metadata = dict(rule='POSITIVE_OBSERVED_JANUARY_SUPPORT', start='2026-01-01', end_exclusive='2026-02-01',
                    source_rows=len(trips), eligible_rows=od.total_trips, pair_counts=records,
                    stricter_threshold='RESEARCH_DECISION_REQUIRED')
    metadata['support_sha256'] = hashlib.sha256(json.dumps(records, separators=(',', ':')).encode()).hexdigest()
    return metadata


def load_support():
    path = ROOT/'data/processed/spatial_3km_jan_mar_2026/trips_jan_mar_2026.parquet'
    columns = ['PUGridID', 'DOGridID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime', 'trip_distance', 'fare_amount']
    trips = pd.read_parquet(path, columns=columns, filters=[('tpep_pickup_datetime', '>=', pd.Timestamp('2026-01-01')), ('tpep_pickup_datetime', '<', pd.Timestamp('2026-02-01'))])
    result = support_from_trips(trips)
    result['source'] = str(path)
    return result


def pairs_from_support(metadata):
    records = metadata['pair_counts']
    if metadata['start'] != '2026-01-01' or metadata['end_exclusive'] != '2026-02-01':
        raise ValueError('Invalid OD evidence window')
    digest = hashlib.sha256(json.dumps(records, separators=(',', ':')).encode()).hexdigest()
    if digest != metadata['support_sha256']:
        raise ValueError('OD support hash mismatch')
    pairs = tuple((grid(o), grid(d)) for o, d, n in records)
    if not pairs or pairs != tuple(sorted(set(pairs))) or any(type(n) is not int or n <= 0 for _, _, n in records):
        raise ValueError('Invalid observed OD support')
    return pairs


def od_states(engine, pairs):
    """Count-valued features at t; EWMA dispatch/min × 30 min = dispatch/slot."""
    operational = engine.operational.state_for(engine.timestamp).set_index('Grid_ID')
    result = {}
    origins = {}
    for origin, destination in pairs:
        # Existing builder verifies causal snapshots, masks and commitments.
        if origin not in origins:
            origins[origin] = engine.current_states.build(origin, destination, engine.timestamp)
        state = origins[origin].copy()
        state[12] = engine.current_states.popularity.get(destination, engine.timestamp)
        state[1] = float(operational.loc[origin, 'F_hat']) * 30.0
        result[(origin, destination)] = validate_state(state)
    return result
