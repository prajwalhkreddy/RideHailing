"""Final pricing contracts and causal 13D state; no Q-network or training."""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from src.pricing.customer import offered_fare
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel,maximum_price
from src.pricing.linucb import PRICING_FACTORS

FEATURES=('J_hat','J_disp_previous','I_incoming','p_STAY','p_N','p_NE','p_E','p_SE','p_S','p_SW','p_W','p_NW','destination_popularity')
ROOT=Path(__file__).resolve().parents[2]

def timestamp(value, aligned=False):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tz is not None or (aligned and t!=t.floor('30min')):
        raise ValueError('Finite timezone-naive NYC project timestamp required; slots align to 30 minutes.')
    return t

def grid(value):
    if isinstance(value,bool) or not isinstance(value,(int,np.integer)) or not 0<=value<142:
        raise ValueError('Expected active integer Grid_ID 0..141.')
    return int(value)

def finite(value):
    x=float(value)
    if not np.isfinite(x) or x<0:raise ValueError('Finite nonnegative value required.')
    return x

def threshold_acceptance(p_base,d_base,distance_miles,E,pricing_factor):
    fare=offered_fare(p_base,pricing_factor)
    limit=maximum_price(p_base,d_base,distance_miles,E)
    return fare<=limit,fare,limit

def behavioural_model(rng,decision_timestamp):
    """Preserve verified legacy E sampler; never ingest Record-029 epsilon."""
    if timestamp(decision_timestamp)<pd.Timestamp('2026-01-25 18:30'):
        raise ValueError('Behavioural prior not available before training cutoff.')
    paths=[]
    for stem in ('customer_price_sensitivity_2026_01','customer_price_sensitivity_fallback_2026_01'):
        p=ROOT/'data/processed'/f'{stem}.parquet'
        meta=json.loads((ROOT/'data/processed'/f'{stem}_metadata.json').read_text())
        if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['output_sha256']:raise ValueError('Behavioural source fingerprint mismatch.')
        paths.append(p)
    return HistoricalCustomerSensitivityModel.from_parquet(paths[0],rng,paths[1],'hierarchical')

@dataclass(frozen=True)
class DispatchOutcome:
    request_id:int
    origin:int
    assigned_at:object
    accepted:bool
    assigned:bool
    fare_usd:float

class DispatchLedger:
    def __init__(self):self.completed={}
    def complete_slot(self,slot_start,completed_at,outcomes):
        start=timestamp(slot_start,True);end=timestamp(completed_at,True)
        if end!=start+pd.Timedelta(minutes=30) or start in self.completed:raise ValueError('Complete a unique 30-minute slot.')
        counts=np.zeros(142,dtype=int);reward=0.;ids=set()
        for event in outcomes:
            if event.request_id in ids:raise ValueError('Duplicate request outcome.')
            ids.add(event.request_id);g=grid(event.origin)
            when=timestamp(event.assigned_at)
            if not start<=when<end:raise ValueError('Outcome outside completed slot.')
            if event.assigned:
                if not event.accepted:raise ValueError('Assigned outcome cannot be passenger rejected.')
                counts[g]+=1;reward+=finite(event.fare_usd)
        self.completed[start]=(end,counts,reward)
        return reward
    def previous(self,decision_timestamp):
        t=timestamp(decision_timestamp,True)
        try:end,counts,_=self.completed[t-pd.Timedelta(minutes=30)]
        except KeyError:raise ValueError('Previous completed slot is required; no silent zero history.')
        if end!=t:raise ValueError('Wrong lag.')
        return counts.copy()

@dataclass(frozen=True)
class PassengerCommitment:
    vehicle_id:int
    destination:int
    committed_at:object
    dropoff_at:object


def incoming(commitments,decision_timestamp):
    t=timestamp(decision_timestamp,True);end=t+pd.Timedelta(minutes=30);counts=np.zeros(142,dtype=int);seen=set()
    for c in commitments:
        if c.vehicle_id in seen:raise ValueError('Duplicate active passenger vehicle.')
        seen.add(c.vehicle_id);g=grid(c.destination)
        committed=timestamp(c.committed_at);arrival=timestamp(c.dropoff_at)
        if committed>=t or arrival<committed:raise ValueError('Commitment must be known before decision; arrival must follow assignment.')
        if t<arrival<=end:counts[g]+=1
    return counts

@dataclass(frozen=True)
class Snapshot:
    target_timestamp:object
    available_at:object
    values:dict
    observed_through:object

    def get(self,g,t):
        if timestamp(self.target_timestamp,True)!=t or timestamp(self.available_at)>t or timestamp(self.observed_through)>t:
            raise ValueError('Snapshot is misaligned or uses future information.')
        if g not in self.values:raise ValueError('Required grid value missing.')
        return self.values[g]

class PricingStateBuilder:
    def __init__(self,forecast,ledger,commitments,routing,popularity,action_masks):
        if not all(isinstance(s,Snapshot) for s in (forecast,routing,popularity)) or not isinstance(ledger,DispatchLedger) or commitments is None or action_masks is None:
            raise ValueError('All pricing-state sources, including explicit passenger commitments, are required.')
        self.forecast=forecast;self.ledger=ledger;self.commitments=tuple(commitments)
        self.routing=routing;self.popularity=popularity;self.action_masks=action_masks
    def build(self,origin,destination,decision_timestamp):
        g=grid(origin);d=grid(destination);t=timestamp(decision_timestamp,True)
        probs=np.asarray(self.routing.get(g,t),dtype=float)
        if g not in self.action_masks:raise ValueError('Missing action mask.')
        mask=np.asarray(self.action_masks[g],dtype=bool)
        if probs.shape!=(9,) or mask.shape!=(9,) or not mask[0] or not np.isfinite(probs).all() or (probs<0).any():raise ValueError('Invalid nine-action probabilities/mask.')
        if np.any(probs[~mask]!=0) or not np.isclose(probs.sum(),1,rtol=1e-7,atol=1e-8):raise ValueError('Unnormalized or unmasked routing probabilities.')
        popularity=finite(self.popularity.get(d,t))
        if popularity not in (0.,.25,.5,.75,1.):raise ValueError('Expected existing ordinal popularity encoding.')
        values=np.array([finite(self.forecast.get(g,t)),self.ledger.previous(t)[g],incoming(self.commitments,t)[g],*probs,popularity],dtype=float)
        if values.shape!=(13,) or not np.isfinite(values).all():raise ValueError('Invalid 13D state.')
        return values


def artifact_snapshots(decision_timestamp):
    """Read exact saved epoch-200 forecast and existing causal popularity only."""
    t=timestamp(decision_timestamp,True);base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
    meta=json.loads((base/'destination_popularity_thresholds.json').read_text())
    if t<pd.Timestamp(meta['runtime_available_from']):raise ValueError('Popularity fit unavailable before cutoff.')
    from src.simulation.temporal_protocol import protocol
    temporal=protocol()
    forecast_path=ROOT/temporal['rl_forecast_path'] if pd.Timestamp(temporal['rl_train_start'])<=t<=pd.Timestamp(temporal['rl_train_end']) else ROOT/'results/analysis/2026-10-19_operational_grid_state/dqn_ready_forecasts.parquet'
    forecast=pd.read_parquet(forecast_path,filters=[('forecast_timestamp','==',t)])
    popularity=pd.read_parquet(base/'destination_popularity.parquet',filters=[('TimeSlot','==',t)])
    for frame,key in [(forecast,'Grid_ID'),(popularity,'GridID')]:
        if len(frame)!=142 or frame[key].duplicated().any() or set(frame[key])!=set(range(142)):raise ValueError('Required complete artifact timestamp unavailable.')
    return (Snapshot(t,t,dict(zip(forecast.Grid_ID,forecast.predicted_demand)),t-pd.Timedelta(minutes=30)),
            Snapshot(t,t,dict(zip(popularity.GridID,popularity.popularity_value)),t))


def completed_request_outcomes(requests,slot_start):
    """Snapshot current dispatch lifecycle outcomes at assignment time.

    request_time is a two-minute mini-slot index, not an absolute timestamp.
    """
    from src.dispatch.request import RequestStatus
    start=timestamp(slot_start,True);result=[]
    for r in requests:
        if not isinstance(r.request_time,(int,np.integer)) or not 0<=r.request_time<15:raise ValueError('Invalid two-minute request mini-slot.')
        assigned=r.status is RequestStatus.ASSIGNED
        if assigned and (r.assigned_vehicle_id is None or r.customer_accepted is not True):raise ValueError('Assignment requires accepted request and vehicle.')
        result.append(DispatchOutcome(r.request_id,r.origin_grid,start+pd.Timedelta(minutes=2*r.request_time),r.customer_accepted is True,assigned,r.offered_fare if assigned else 0.))
    return result


def mean_routing_response(probability_vectors,mask):
    """Mean already-masked policy probabilities; no fallback for empty population."""
    x=np.asarray(probability_vectors,dtype=float);mask=np.asarray(mask,dtype=bool)
    if x.ndim!=2 or x.shape[0]==0 or x.shape[1]!=9 or mask.shape!=(9,) or not mask[0]:raise ValueError('Explicit nonempty nine-action routing population required.')
    if not np.isfinite(x).all() or (x<0).any() or np.any(x[:,~mask]!=0) or not np.allclose(x.sum(1),1,rtol=1e-7,atol=1e-8):raise ValueError('Invalid policy probability vectors.')
    return x.mean(0)


def passenger_commitment(request,assignment_slot_start):
    """Adapt an active assigned passenger request, never a generic BUSY vehicle.

    Caller supplies only still-active passenger trips at the decision boundary.
    """
    from src.dispatch.request import RequestStatus
    if request.status is not RequestStatus.ASSIGNED or request.assigned_vehicle_id is None or request.customer_accepted is not True:
        raise ValueError('Active accepted assigned passenger request required.')
    if not isinstance(request.request_time,(int,np.integer)) or not 0<=request.request_time<15:raise ValueError('Invalid mini-slot.')
    duration=finite(request.trip_duration_minutes)
    if duration<=0:raise ValueError('Known positive passenger duration required.')
    start=timestamp(assignment_slot_start,True)+pd.Timedelta(minutes=2*request.request_time)
    return PassengerCommitment(request.assigned_vehicle_id,grid(request.destination_grid),start,start+pd.Timedelta(minutes=duration))
