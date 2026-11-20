"""Explicit research forecast bundle and UTC engine initialization boundaries."""
import numpy as np
import pandas as pd
from src.demand.causal_timing import timing, CHANNELS
from src.demand.persistence_weather import contract, fingerprint, VERSION
from src.simulation.utc_od_state import instant, UTCSnapshot, UTCStateBuilder
from src.routing.final_state import RoutingState
from src.routing.learning import masked_softmax
from src.fleet.state import VehicleStatus

BASELINE = 'JANUARY_HISTORICAL_AVERAGE_DEMAND_V1'

def forecast(inputs,t):
    t=instant(t,True);m=inputs['weather_contract']
    baseline=inputs.get('forecast_protocol')==BASELINE
    expected={'version':BASELINE if baseline else VERSION,'weather_contract_sha256':fingerprint(m)}
    if baseline:
        provenance=inputs['baseline_provenance']
        if provenance.get('method')!='January grid/local-half-hour arithmetic mean' or provenance.get('training_start')!='2026-01-01' or provenance.get('training_end_exclusive')!='2026-02-01':raise ValueError('Invalid historical baseline provenance')
        if instant(provenance['available_at'])>t-pd.Timedelta(minutes=30):raise ValueError('Future baseline information')
        from pathlib import Path
        import hashlib
        if hashlib.sha256(Path(provenance['artifact_path']).read_bytes()).hexdigest()!=provenance['artifact_sha256']:raise ValueError('Changed baseline artifact')
    if m!=contract(120) or inputs['checkpoint_metadata']!=expected:
        raise ValueError('Incompatible/oracle forecast provenance')
    if inputs['channels']!=list(CHANNELS) or inputs['grid_ids']!=list(range(142)):
        raise ValueError('Invalid CNN feature/grid contract')
    f=inputs['forecasts'][str(t)]
    if len(f)!=142 or set(f.Grid_ID)!=set(range(142)):raise ValueError('Invalid forecast grid')
    for name in ['issued_at','target_start','target_end','feature_cutoff','observation_time','assumed_available_at']:
        if any(pd.Timestamp(value).tz is None for value in f[name]):raise ValueError('Naive forecast timestamp')
    for k,v in timing(t).items():
        if not (pd.to_datetime(f[k],utc=True)==v.tz_convert('UTC')).all():raise ValueError('Forecast timing mismatch')
    obs=pd.to_datetime(f.observation_time,utc=True);available=pd.to_datetime(f.assumed_available_at,utc=True)
    if not (available==obs+pd.Timedelta(minutes=120)).all() or not (available<=t-pd.Timedelta(minutes=30)).all():raise ValueError('Weather availability violation')
    if baseline:
        table=pd.read_csv(provenance['artifact_path'])
        local=t.tz_convert('America/New_York');period=local.hour*2+local.minute//30
        expected_values=table.loc[table.period==period].set_index('Grid_ID').reindex(f.Grid_ID).predicted_demand.to_numpy(float)
        if not np.allclose(f.predicted_demand.to_numpy(float),expected_values,rtol=0,atol=1e-12):raise ValueError('Baseline predictions disagree with artifact')
    a=f.predicted_demand.to_numpy(float)
    if not np.isfinite(a).all() or (a<0).any():raise ValueError('Invalid demand')
    return UTCSnapshot(t,t-pd.Timedelta(minutes=30),dict(zip(f.Grid_ID,a)),t-pd.Timedelta(minutes=30))

def state_sources(e):
    t=e.timestamp;f=forecast(e.utc_inputs,t);vectors=[];masks={}
    for g in range(142):
        s=RoutingState.from_producer(e.routing,e.operational,t,g);vectors.append(s.values);masks[g]=s.mask
    hierarchy=getattr(e,"driver_hierarchy",None)
    if hierarchy is not None:
        from src.routing.research_feedback import probabilities
        probs=probabilities(e,vectors,masks)
    elif getattr(e,"research_routing",False):
        from src.simulation.research_utility_routing import probabilities
        probs=probabilities(e,masks)
    else:
        logits=e.policy(np.stack(vectors),training=False).numpy()
        probs={g:masked_softmax(logits[g],masks[g]) for g in range(142)}
    for vid,c in e.passengers.items():
        v=e.fleet.vehicle(vid)
        if v.trip_status is not VehicleStatus.BUSY or v.destination!=c.destination or c.dropoff_at<=t or not np.isclose(v.remaining_travel_time,(c.dropoff_at-t).total_seconds()/60,atol=1e-8):raise ValueError('Passenger event mismatch')
    pop=e.utc_inputs['popularity']
    if instant(e.utc_inputs['popularity_available_at'])>t:raise ValueError('Future popularity')
    return UTCStateBuilder(f,e.ledger,list(e.passengers.values()),UTCSnapshot(t,t,probs,t),UTCSnapshot(t,e.utc_inputs['popularity_available_at'],pop,e.utc_inputs['popularity_available_at']),masks)
