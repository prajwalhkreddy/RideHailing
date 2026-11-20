"""Observed pickups as request-arrival proxies, independent of CNN forecasts."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.pricing.slot_v3 import ROOT, allowed
from src.pricing.slot_v3_request import V3Request

PROTOCOL = 'HISTORICAL_REQUEST_REPLAY_V1'
SOURCE = ROOT/'data/processed/spatial_3km_jan_mar_2026/trips_jan_mar_2026.parquet'
COLUMNS = ['tpep_pickup_datetime','tpep_dropoff_datetime','PUGridID','DOGridID',
           'trip_distance','fare_amount','source_file_month','source_prepared_row']


def initial_state(start, *, utc_mode=False):
    return dict(protocol=PROTOCOL, source=str(SOURCE), next_slot=str(_time(start,utc_mode)),
                slots_completed=0, requests_consumed=0, ordering='pickup_timestamp,source_file_month,source_prepared_row',
                last_slot=None, last_count=0, request_cursor=0, last_order_hash=None,
                rng=None, last_mode=None)


def _time(value, utc_mode=False):
    if not utc_mode:return allowed(value)
    from src.simulation.utc_od_state import instant
    t=instant(value,True)
    allowed(t.tz_convert("America/New_York").tz_localize(None))
    return t

def read_slot(slot, *, utc_mode=False):
    t=_time(slot,utc_mode)
    end=t+pd.Timedelta(minutes=30)
    if utc_mode:
        t=t.tz_convert("America/New_York").tz_localize(None)
        end=end.tz_convert("America/New_York").tz_localize(None)
    return pd.read_parquet(SOURCE, columns=COLUMNS,
        filters=[('tpep_pickup_datetime','>=',t),('tpep_pickup_datetime','<',end)])


def replay_requests(frame, slot, pairs, *, utc_mode=False, fallback_contract=None):
    from src.pricing.unseen_od import validate
    fallback_contract=validate(fallback_contract)
    """Conserve eligible rows; unsupported OD aborts, never silently removes rows."""
    t=_time(slot,utc_mode);end=t+pd.Timedelta(minutes=30)
    if not set(COLUMNS).issubset(frame.columns): raise ValueError('Missing historical replay fields')
    f=frame[COLUMNS].copy()
    if utc_mode:
        from src.simulation.master_od_contract import utc
        for name in ['tpep_pickup_datetime','tpep_dropoff_datetime']:
            values=pd.to_datetime(f[name])
            f[name]=values.dt.tz_localize('America/New_York',ambiguous='raise',nonexistent='raise').dt.tz_convert('UTC') if values.dt.tz is None else values.dt.tz_convert('UTC')
    pickup=pd.to_datetime(f.tpep_pickup_datetime);dropoff=pd.to_datetime(f.tpep_dropoff_datetime)
    if pickup.isna().any() or not ((pickup>=t)&(pickup<end)).all(): raise ValueError('Historical slot mismatch')
    duration=(dropoff-pickup).dt.total_seconds()/60
    numeric=f[['trip_distance','fare_amount','PUGridID','DOGridID','source_file_month','source_prepared_row']].to_numpy(dtype=float)
    # Same duration/distance/fare eligibility as the existing empirical generator;
    # spatial and identity violations fail rather than being repaired.
    eligible=np.isfinite(numeric[:,:2]).all(axis=1)&np.isfinite(duration)&(duration>0)&(f.trip_distance>=0)&(f.fare_amount>=0)
    f=f.loc[eligible].copy();f['duration_minutes']=duration.loc[eligible]
    for name,low,high in [('PUGridID',0,141),('DOGridID',0,141),('source_file_month',1,3),('source_prepared_row',0,10**12-1)]:
        a=f[name].to_numpy(float)
        if not np.isfinite(a).all() or (a!=np.floor(a)).any() or (a<low).any() or (a>high).any(): raise ValueError('Invalid historical '+name)
    if f[['source_file_month','source_prepared_row']].duplicated().any(): raise ValueError('Duplicate source identity')
    f=f.sort_values(['tpep_pickup_datetime','source_file_month','source_prepared_row'],kind='stable')
    unsupported=sorted(set(zip(f.PUGridID.astype(int),f.DOGridID.astype(int)))-set(pairs))
    if unsupported and fallback_contract is None: raise ValueError(f'UNSUPPORTED_HISTORICAL_OD: {len(unsupported)} pairs; first={unsupported[:5]}; research decision required')
    requests=[];identities=[]
    for row in f.itertuples(index=False):
        pickup=pd.Timestamp(row.tpep_pickup_datetime);offset=(pickup-t).total_seconds()
        identity=int(row.source_file_month)*10**12+int(row.source_prepared_row)
        request=V3Request(request_id=identity,request_time=int(offset//120),origin_grid=int(row.PUGridID),destination_grid=int(row.DOGridID),
            base_fare=float(row.fare_amount),source_trip_id=identity,empirical_pickup_datetime=pickup.to_pydatetime(),
            empirical_dropoff_datetime=pd.Timestamp(row.tpep_dropoff_datetime).to_pydatetime(),
            trip_duration_minutes=float(row.duration_minutes),trip_distance_miles=float(row.trip_distance),
            trip_distance_km=float(row.trip_distance)*1.609344,empirical_within_slot_offset_seconds=offset)
        request.source_file_month=int(row.source_file_month);request.source_prepared_row=int(row.source_prepared_row)
        request.observed_fare=float(row.fare_amount);request.validate(range(142),15)
        requests.append(request);identities.append(identity)
    report=dict(source_rows=len(frame),eligible_rows=len(f),excluded_invalid_trip_rows=int((~eligible).sum()),
                realized_requests=len(requests),unsupported_pairs=len(unsupported),
                fallback_requests=sum((r.origin_grid,r.destination_grid) not in set(pairs) for r in requests),
                order_hash=hashlib.sha256(json.dumps(identities).encode()).hexdigest())
    return requests,report


def realize(state, slot, pairs, *, utc_mode=False, fallback_contract=None):
    if state['protocol']!=PROTOCOL or state['next_slot']!=str(_time(slot,utc_mode)) or state['source']!=str(SOURCE): raise ValueError('Replay protocol/cursor mismatch')
    return replay_requests(read_slot(slot,utc_mode=utc_mode),slot,pairs,utc_mode=utc_mode,fallback_contract=fallback_contract)


def commit(state, slot, count, report, mode, *, utc_mode=False):
    if state['next_slot']!=str(_time(slot,utc_mode)): raise ValueError('Replay commit cursor mismatch')
    state.update(next_slot=str(pd.Timestamp(slot)+pd.Timedelta(minutes=30)),last_slot=str(slot),
        last_count=count,request_cursor=count,last_order_hash=report.get('order_hash'),last_mode=mode)
    state['slots_completed']+=1;state['requests_consumed']+=count
