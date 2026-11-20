"""Non-learned research routing: existing private utility, no model weights."""
import copy
import json
import numpy as np
from pathlib import Path
from src.fleet.state import VehicleStatus
VERSION = 'NONLEARNED_PRIVATE_UTILITY_ROUTING_V1'

def validate(path):
    c=json.loads(Path(path).read_text())
    if c != {'version':VERSION,'learned':False,'probabilities':'idle-fleet deterministic-action frequencies; empty-grid STAY','utility':'existing operational_interface.decide'}:
        raise ValueError('Incompatible non-learned routing contract')
    return c

def probabilities(engine, masks):
    # A shallow interface copy keeps diagnostic reserve counters out of live state.
    routing=copy.copy(engine.routing)
    counts={g:np.zeros(9,dtype=float) for g in masks}
    for v in sorted(engine.fleet.vehicles,key=lambda v:v.vehicle_id):
        if v.trip_status is not VehicleStatus.IDLE or v.vehicle_id in engine.charging.vehicle_station:continue
        p=engine.profiles.loc[v.vehicle_id];g=v.current_grid
        d=routing.decide(engine.operational,engine.timestamp,grid=g,energy_kwh=v.energy_level,
            minimum_energy_kwh=engine.energy.battery_capacity_kwh*engine.energy.charging_trigger_soc,
            p_min=p.price_preference,w_max_minutes=p.wait_preference,h_max_minutes=p.charging_wait_preference_minutes,
            energy_per_km=engine.energy.consumption_rate_kwh_per_km)
        counts[g][routing.label(d,g)]+=1
    for g,a in counts.items():
        if not a.sum():a[0]=1
        a/=a.sum()
        if not np.isfinite(a).all() or (a<0).any() or np.any(a[~masks[g]]) or not np.isclose(a.sum(),1):
            raise ValueError('Invalid utility routing probabilities')
    return counts
