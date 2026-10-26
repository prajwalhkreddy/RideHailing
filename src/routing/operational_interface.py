"""Roadmap utilities and causal state interface; no production activation.

The final state has 169 features. Production coefficients remain explicit.
"""
from dataclasses import dataclass
import heapq
import math
import numpy as np
import pandas as pd
from src.routing.baseline import ACTION_ORDER, movement_distance_m


def nonnegative(x, name):
    if x is None or not math.isfinite(x) or x < 0:
        raise ValueError(f'{name} must be finite and nonnegative.')
    return float(x)


def safeguard(x, name):
    if x is None or not math.isfinite(x) or x <= 0:
        raise ValueError(f'CONFIG_DECISION_REQUIRED: positive {name} required.')
    return float(x)


def u1(p_min, mu, sigma, *, sigma_floor):
    floor = safeguard(sigma_floor, 'sigma_floor')
    z = (nonnegative(p_min,'P_min')-nonnegative(mu,'mu')) / max(nonnegative(sigma,'sigma'),floor)
    return .5 * math.erfc(z/math.sqrt(2))


def u2(f_per_minute, w_minutes):
    exponent = nonnegative(f_per_minute,'F_hat') * nonnegative(w_minutes,'W_max_minutes')
    # Largest representable value below one preserves the open upper bound.
    return min(-math.expm1(-exponent), float(np.nextafter(1.,0.)))


def u3(h_max_minutes, h_hat_minutes, *, wait_floor_minutes):
    floor = safeguard(wait_floor_minutes,'H_hat_floor_minutes')
    return -math.expm1(-nonnegative(h_max_minutes,'H_max_minutes') / max(nonnegative(h_hat_minutes,'H_hat_minutes'),floor))


@dataclass(frozen=True)
class UtilityConfig:
    sigma_floor: float
    wait_floor_minutes: float
    cost_per_km: float

    def __post_init__(self):
        safeguard(self.sigma_floor,'sigma_floor');safeguard(self.wait_floor_minutes,'H_hat_floor_minutes')
        nonnegative(self.cost_per_km,'explicit normalized utility cost_per_km')

    def cost(self, distance_m):
        return nonnegative(distance_m,'distance_m')/1000*self.cost_per_km


@dataclass(frozen=True)
class LocalDecision:
    action_index: int
    next_grid: int
    final_grid: int
    branch: str
    score: float
    distance_m: float
    station_id: int | None = None


class OperationalRouting:
    def __init__(self, neighbours, stations, config):
        self.config=config
        self.edges={g:{} for g in range(142)}
        for r in neighbours.itertuples():
            g,h,a=int(r.GridID),int(r.NeighbourGridID),int(r.ActionIndex)
            if g not in self.edges or h not in self.edges or not 1<=a<=8 or a in self.edges[g]:
                raise ValueError('Invalid active-grid edge/action.')
            if not math.isclose(r.DistanceMeters,movement_distance_m(ACTION_ORDER[a])):
                raise ValueError('Incorrect action distance.')
            self.edges[g][a]=(h,float(r.DistanceMeters))
        if stations.station_id.duplicated().any() or not set(stations.grid_id).issubset(self.edges):
            raise ValueError('Invalid station mapping.')
        self.stations=stations[['station_id','grid_id']].copy()

    def candidates(self,g):
        if g not in self.edges:raise ValueError('Unknown active grid.')
        return {0:(g,0.),**self.edges[g]}

    def state(self, producer, timestamp):
        frame=producer.state_for(timestamp)
        if len(frame)!=142 or frame.Grid_ID.duplicated().any() or set(frame.Grid_ID)!=set(self.edges):
            raise ValueError('Operational state requires all active grids.')
        if not np.isfinite(frame[['mu','sigma','F_hat','H_hat']]).all().all():
            raise ValueError('Nonfinite operational state.')
        return frame.set_index('Grid_ID')

    def paths(self,g):
        self.candidates(g)
        best={g:(0.,0)};q=[(0.,0,g)]
        while q:
            d,first,node=heapq.heappop(q)
            if best[node]!=(d,first):continue
            for a,(target,length) in sorted(self.edges[node].items()):
                candidate=(d+length,a if node==g else first)
                if target not in best or candidate<best[target]:
                    best[target]=candidate;heapq.heappush(q,(*candidate,target))
        return best

    def minimum_station_energy(self, grid, energy_per_km):
        """Minimum modeled station-route energy, kWh; zero at a station."""
        consumption=nonnegative(energy_per_km,'energy_per_km')
        if not hasattr(self,'_station_distance_cache'):self._station_distance_cache={}
        if grid not in self._station_distance_cache:
            paths=self.paths(grid)
            distances=[paths[int(g)][0] for g in self.stations.grid_id if int(g) in paths]
            if not distances:raise ValueError('No reachable charging station in topology.')
            self._station_distance_cache[grid]=min(distances)
        return self._station_distance_cache[grid]/1000*consumption

    def preserves_station_reachability(self, energy, movement_energy, destination, energy_per_km):
        return nonnegative(energy,'energy')-nonnegative(movement_energy,'movement_energy') >= self.minimum_station_energy(destination,energy_per_km)

    def decide(self, producer, timestamp, *, grid, energy_kwh, minimum_energy_kwh,
               p_min, w_max_minutes, h_max_minutes, energy_per_km, idle=True):
        if not idle:raise ValueError('Only idle vehicles may route.')
        energy=nonnegative(energy_kwh,'energy');minimum=nonnegative(minimum_energy_kwh,'minimum_energy')
        consumption=nonnegative(energy_per_km,'energy_per_km')
        state=self.state(producer,timestamp);options=[]
        if energy>minimum:
            for a,(target,d) in sorted(self.candidates(grid).items()):
                if d/1000*consumption>energy:continue
                if not self.preserves_station_reachability(energy,d/1000*consumption,target,consumption):
                    self.reserve_reposition_rejections=getattr(self,'reserve_reposition_rejections',0)+1
                    continue
                r=state.loc[target]
                score=u1(p_min,r.mu,r.sigma,sigma_floor=self.config.sigma_floor)+u2(r.F_hat,w_max_minutes)-self.config.cost(d)
                options.append(LocalDecision(a,target,target,'REPOSITION',score,d))
        else:
            paths=self.paths(grid)
            for station in self.stations.sort_values('station_id').itertuples():
                if station.grid_id not in paths:continue
                d,a=paths[station.grid_id]
                if d/1000*consumption>energy:continue
                score=u3(h_max_minutes,state.loc[station.grid_id].H_hat,wait_floor_minutes=self.config.wait_floor_minutes)-self.config.cost(d)
                next_grid,step=self.candidates(grid)[a]
                options.append(LocalDecision(a,next_grid,int(station.grid_id),'CHARGING',score,step,int(station.station_id)))
        if not options:raise ValueError('No energy-feasible destination; no teleport fallback.')
        return min(options,key=lambda r:(-r.score,r.action_index,r.station_id if r.station_id is not None else -1))

    def encode(self,producer,timestamp,grid,*,expected_dimension=None):
        state=self.state(producer,timestamp);candidates=self.candidates(grid);values=[]
        for a in range(9):
            values.extend(state.loc[candidates[a][0],['mu','sigma','F_hat']].tolist() if a in candidates else [0.,0.,0.])
        values.extend(state.loc[list(range(142)),'H_hat'].tolist())
        vector=np.asarray(values,dtype=np.float32)
        if not np.isfinite(vector).all():raise ValueError('Nonfinite encoded state.')
        if expected_dimension is not None and expected_dimension!=len(vector):
            raise ValueError('Expected final 169-feature state; legacy 155 input is incompatible.')
        return vector,np.array([a in candidates for a in range(9)],dtype=bool)

    def label(self,decision,grid):
        candidates=self.candidates(grid)
        if decision.action_index not in candidates or candidates[decision.action_index][0]!=decision.next_grid:
            raise ValueError('Decision label does not match masked next hop.')
        return decision.action_index

    def start_next_hop(self, vehicle, decision, *, speed_kmph, energy_per_km):
        """Start only the selected edge; arrival remains the fleet's timed job.

        STAY at a station does not reserve a charger: existing station admission
        must handle capacity/queueing after arrival.
        """
        from src.fleet.state import VehicleStatus
        if vehicle.trip_status is not VehicleStatus.IDLE:
            raise ValueError('Only idle vehicles may start navigation.')
        self.label(decision, vehicle.current_grid)
        distance = self.candidates(vehicle.current_grid)[decision.action_index][1]
        speed = safeguard(speed_kmph, 'speed_kmph')
        consumed = distance/1000 * nonnegative(energy_per_km, 'energy_per_km')
        if consumed > vehicle.energy_level:
            raise ValueError('Insufficient energy for next hop.')
        if decision.action_index:
            vehicle.abandon_idle_wait()
            vehicle.energy_level -= consumed
            vehicle.trip_status = VehicleStatus.BUSY
            vehicle.destination = decision.next_grid
            vehicle.remaining_travel_time = distance/1000/speed*60
        return distance/1000/speed*60
