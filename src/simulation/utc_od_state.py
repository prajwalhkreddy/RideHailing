"""UTC-only OD state adapters; legacy pricing contracts are unchanged."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from src.pricing.dqn_contract import DispatchLedger, Snapshot, PricingStateBuilder, grid, finite
from src.pricing.od_contract import validate_state

PROTOCOL='OD_AWARE_UTC_ELAPSED_V1'

def instant(value, aligned=False):
    t=pd.Timestamp(value)
    if pd.isna(t) or t.tz is None or str(t.tz)!='UTC' or (aligned and t!=t.floor('30min')):
        raise ValueError('Explicit aware UTC instant required')
    return t

class UTCLedger(DispatchLedger):
    def complete_slot(self,slot_start,completed_at,outcomes):
        start,end=instant(slot_start,True),instant(completed_at,True)
        if end!=start+pd.Timedelta(minutes=30) or start in self.completed:raise ValueError('Invalid completed slot')
        counts=np.zeros(142,int);reward=0.;seen=set()
        for x in outcomes:
            if x.request_id in seen or not start<=instant(x.assigned_at)<end:raise ValueError('Duplicate/out-of-slot outcome')
            seen.add(x.request_id)
            if x.assigned:
                if not x.accepted:raise ValueError('Rejected assignment')
                counts[grid(x.origin)]+=1;reward+=finite(x.fare_usd)
        self.completed[start]=(end,counts,reward);return reward
    def previous(self,t):
        t=instant(t,True)
        end,counts,_=self.completed[t-pd.Timedelta(minutes=30)]
        if end!=t:raise ValueError('Invalid ledger lag')
        return counts.copy()

class UTCSnapshot(Snapshot):
    def get(self,g,t):
        t=instant(t,True)
        if instant(self.target_timestamp,True)!=t or instant(self.available_at)>t or instant(self.observed_through)>t:raise ValueError('Future/misaligned snapshot')
        return self.values[g]

class UTCStateBuilder(PricingStateBuilder):
    def build(self,origin,destination,decision_timestamp):
        t=instant(decision_timestamp,True);g=grid(origin);d=grid(destination)
        probs=np.asarray(self.routing.get(g,t),float);mask=np.asarray(self.action_masks[g],bool)
        if probs.shape!=(9,) or mask.shape!=(9,) or not mask[0] or not np.isfinite(probs).all() or (probs<0).any() or np.any(probs[~mask]!=0) or not np.isclose(probs.sum(),1):raise ValueError('Invalid routing probabilities')
        incoming=0;seen=set()
        for c in self.commitments:
            a,b=instant(c.committed_at),instant(c.dropoff_at)
            if c.vehicle_id in seen or a>=t or b<a:raise ValueError('Invalid commitment')
            seen.add(c.vehicle_id)
            incoming+=int(c.destination==g and t<b<=t+pd.Timedelta(minutes=30))
        return validate_state([finite(self.forecast.get(g,t)),self.ledger.previous(t)[g],incoming,*probs,finite(self.popularity.get(d,t))])
