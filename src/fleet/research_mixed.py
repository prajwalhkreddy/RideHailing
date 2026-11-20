"""Deterministic research EV composition; existing vehicles default to EV."""
import numpy as np
VERSION='MIXED_EV_FLEET_V1'
def configure(fleet,share,seed):
    if share not in (.1,.2,.3):raise ValueError('Supported EV shares: 0.1, 0.2, 0.3')
    ordered=sorted(fleet.vehicles,key=lambda v:v.vehicle_id)
    count=len(ordered)*share
    if not float(count).is_integer():raise ValueError('Fleet size incompatible with exact EV share')
    ids=set(np.random.default_rng(seed).choice(len(ordered),int(count),replace=False).tolist())
    for i,v in enumerate(ordered):
        if v.trip_status.value!='IDLE':raise ValueError('Configure composition only before execution')
        v.is_ev=i in ids
        if not v.is_ev:v.energy_level=0.
    return dict(version=VERSION,share=share,ev_count=len(ids),fleet_size=len(ordered),seed=seed)

def decision(engine,vehicle):
    from src.routing.operational_interface import LocalDecision,u1,u2
    p=engine.profiles.loc[vehicle.vehicle_id];r=engine.routing;g=vehicle.current_grid
    if getattr(vehicle,'is_ev',True):
        return r.decide(engine.operational,engine.timestamp,grid=g,energy_kwh=vehicle.energy_level,minimum_energy_kwh=engine.energy.battery_capacity_kwh*engine.energy.charging_trigger_soc,p_min=p.price_preference,w_max_minutes=p.wait_preference,h_max_minutes=p.charging_wait_preference_minutes,energy_per_km=engine.energy.consumption_rate_kwh_per_km)
    state=r.state(engine.operational,engine.timestamp);options=[]
    for a,(target,d) in sorted(r.candidates(g).items()):
        v=state.loc[target];score=u1(p.price_preference,v.mu,v.sigma,sigma_floor=r.config.sigma_floor)+u2(v.F_hat,p.wait_preference)-r.config.cost(d)
        options.append(LocalDecision(a,target,target,'REPOSITION',score,d))
    return min(options,key=lambda d:(-d.score,d.action_index))
