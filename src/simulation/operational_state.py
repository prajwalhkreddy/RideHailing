"""Causal, explicit-configuration operational state for the active true-3-km grid.

Price EWMAs retain the provisional statistics.py semantics, not a claimed
manuscript recurrence. Call complete_slot only after all outcomes are complete.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from src.dispatch.request import RequestStatus


@dataclass(frozen=True)
class SmoothingParameters:
    alpha: float
    beta: float
    delta: float
    kappa: float
    sigma_floor: float

    @classmethod
    def from_config(cls, config):
        """Fail closed while the project's explicit decisions remain null."""
        section = config['operational_state']
        return cls(**{name: section.get(name)
                      for name in ('alpha', 'beta', 'delta', 'kappa', 'sigma_floor')})

    def __post_init__(self):
        for name in ('alpha', 'beta', 'delta', 'kappa'):
            x = getattr(self, name)
            if x is None or not np.isfinite(x) or not 0 < x <= 1:
                raise ValueError(f'CONFIG_DECISION_REQUIRED: {name} must be in (0,1].')
        if self.sigma_floor is None or not np.isfinite(self.sigma_floor) or self.sigma_floor <= 0:
            raise ValueError('CONFIG_DECISION_REQUIRED: positive sigma_floor required.')


def charging_grid_observations(infrastructure):
    """Queue-length-weighted elapsed waits across ALL stations in each grid.

    Empty observed station queues contribute zero queued EVs; an entirely empty
    station grid reports zero. Nonstation grids have no observation.
    """
    values = {}
    for station in infrastructure.stations.values():
        values.setdefault(station.grid_id, []).extend(e.wait_minutes for e in station.queue)
    return {g: float(np.mean(v)) if v else 0.0 for g, v in values.items()}


class OperationalGridState:
    """Publish immutable-by-copy state at a decision boundary, 142 rows/slot.

    Priors must have Grid_ID, mu, sigma, F_hat, H_hat; prior_as_of must precede
    first decision. No default F/H prior or smoothing coefficients are invented.
    """
    def __init__(self, grid_lookup, priors, *, first_timestamp, prior_as_of, parameters):
        ids = grid_lookup['GridID'].tolist()
        if len(ids) != 142 or set(ids) != set(range(142)):
            raise ValueError('Expected active true-3-km 142-grid domain.')
        # Geometry checks prevent a legacy subset from masquerading as active.
        if grid_lookup.crs is None or grid_lookup.crs.to_epsg() != 32118:
            raise ValueError('Expected EPSG:32118 metric grid.')
        bounds = grid_lookup.geometry.bounds
        if not np.allclose(bounds.maxx-bounds.minx, 3000) or not np.allclose(bounds.maxy-bounds.miny, 3000):
            raise ValueError('Expected 3000-metre cells.')
        self.timestamp = pd.Timestamp(first_timestamp)
        if pd.Timestamp(prior_as_of) >= self.timestamp:
            raise ValueError('Prior cutoff must precede first decision.')
        if self.timestamp != self.timestamp.floor('30min'):
            raise ValueError('Decision timestamps must align to 30 minutes.')
        self.parameters = parameters
        if len(priors) != 142 or priors.Grid_ID.duplicated().any() or set(priors.Grid_ID) != set(ids):
            raise ValueError('Exactly one prior per active grid is required.')
        self._state = priors.set_index('Grid_ID')[['mu','sigma','F_hat','H_hat']].sort_index().astype(float)
        if not np.isfinite(self._state.to_numpy()).all() or (self._state < 0).any().any():
            raise ValueError('Finite nonnegative explicit priors required.')
        self._observations = self._empty_observations()

    def _empty_observations(self):
        return pd.DataFrame({'successful_dispatch_count': 0,
            'observed_mean_dispatch_price': None, 'observed_dispatch_price_std': None,
            'observed_charging_wait': None}, index=self._state.index)

    def state_for(self, timestamp):
        if pd.Timestamp(timestamp) != self.timestamp:
            raise ValueError('Only the current decision boundary may be consumed.')
        result = self._state.join(self._observations).reset_index()
        result.insert(0, 'timestamp', self.timestamp)
        result['sigma_for_denominator'] = result.sigma.clip(lower=self.parameters.sigma_floor)
        return result

    def complete_slot(self, *, slot_start, completed_at, requests=(), charging_waits=None):
        start, end = pd.Timestamp(slot_start), pd.Timestamp(completed_at)
        if start != self.timestamp or end != start + pd.Timedelta(minutes=30):
            raise ValueError('Complete exactly the current 30-minute slot before publishing next state.')
        prices = {}
        for r in requests:
            if r.origin_grid not in self._state.index:
                raise ValueError('Unknown origin grid.')
            if r.status is RequestStatus.ASSIGNED:
                if r.assigned_vehicle_id is None or r.offered_fare is None or not np.isfinite(r.offered_fare) or r.offered_fare < 0:
                    raise ValueError('Assigned dispatch requires vehicle and finite nonnegative price.')
                prices.setdefault(r.origin_grid, []).append(float(r.offered_fare))
        waits = dict(charging_waits or {})
        if any(g not in self._state.index or not np.isfinite(w) or w < 0 for g,w in waits.items()):
            raise ValueError('Invalid charging observation.')
        obs = self._empty_observations()
        nxt = self._state.copy()
        p = self.parameters
        for g in nxt.index:
            fares = prices.get(g, [])
            obs.at[g,'successful_dispatch_count'] = len(fares)
            nxt.at[g,'F_hat'] = p.delta * len(fares)/30 + (1-p.delta)*nxt.at[g,'F_hat']
            if fares:
                mean, std = float(np.mean(fares)), float(np.std(fares, ddof=0))
                obs.at[g,'observed_mean_dispatch_price'] = mean
                obs.at[g,'observed_dispatch_price_std'] = std
                nxt.at[g,'mu'] = p.alpha*mean + (1-p.alpha)*nxt.at[g,'mu']
                nxt.at[g,'sigma'] = p.beta*std + (1-p.beta)*nxt.at[g,'sigma']
            if g in waits:
                obs.at[g,'observed_charging_wait'] = waits[g]
                nxt.at[g,'H_hat'] = p.kappa*waits[g] + (1-p.kappa)*nxt.at[g,'H_hat']
        self._state, self._observations, self.timestamp = nxt, obs, end
        return self.state_for(end)
