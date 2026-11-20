"""Opt-in §6 state; no changes to historical OperationalGridState."""
import numpy as np
import pandas as pd
from src.dispatch.request import RequestStatus
from src.simulation.operational_state import OperationalGridState
from src.simulation.master_od_contract import EWMA, ewma

class MasterOperationalGridState(OperationalGridState):
    contract_version = EWMA

    def complete_slot(self, *, slot_start, completed_at, requests=(), charging_waits=None):
        start,end=pd.Timestamp(slot_start),pd.Timestamp(completed_at)
        if start != self.timestamp or end != start+pd.Timedelta(minutes=30):
            raise ValueError('Complete exactly one elapsed slot')
        prices={}
        for r in requests:
            if r.origin_grid not in self._state.index:
                raise ValueError('Unknown origin')
            if r.status is RequestStatus.ASSIGNED:
                if r.assigned_vehicle_id is None or r.offered_fare is None or not np.isfinite(r.offered_fare) or r.offered_fare < 0:
                    raise ValueError('Invalid successful dispatch')
                prices.setdefault(r.origin_grid,[]).append(r.offered_fare)
        waits=dict(charging_waits or {})
        if any(g not in self._state.index or not np.isfinite(v) or v<0 for g,v in waits.items()):
            raise ValueError('Invalid wait observation')
        obs=self._empty_observations();obs['observed_dispatch_price_mad_previous_mean']=np.nan
        nxt=self._state.copy()
        for g in nxt.index:
            fares=prices.get(g,[]);old=self._state.loc[g].to_numpy()
            nxt.loc[g]=ewma(old,fares,waits.get(g),self.parameters)
            obs.at[g,'successful_dispatch_count']=len(fares)
            if fares:
                obs.at[g,'observed_mean_dispatch_price']=float(np.mean(fares))
                obs.at[g,'observed_dispatch_price_mad_previous_mean']=float(np.abs(np.asarray(fares)-old[0]).mean())
            if g in waits:obs.at[g,'observed_charging_wait']=waits[g]
        self._state,self._observations,self.timestamp=nxt,obs,end
        return self.state_for(end)
