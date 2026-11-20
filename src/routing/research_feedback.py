"""Platform-visible probabilities only; utility and memories remain driver-side."""
import copy
import numpy as np
from src.fleet.state import VehicleStatus
from src.fleet.research_mixed import decision

def probabilities(engine,vectors,masks):
    h=engine.driver_hierarchy
    if h.mode!='UTILITY':return h.mean_probabilities(vectors,masks,engine.timestamp)
    shadow=copy.copy(engine);shadow.routing=copy.copy(engine.routing)
    counts={g:np.zeros(9) for g in masks}
    for v in sorted(engine.fleet.vehicles,key=lambda v:v.vehicle_id):
        if v.trip_status is VehicleStatus.IDLE and v.vehicle_id not in engine.charging.vehicle_station:
            d=decision(shadow,v);counts[v.current_grid][shadow.routing.label(d,v.current_grid)]+=1
    for g,p in counts.items():
        if p.sum()==0:p[0]=1
        p/=p.sum()
        if np.any(p[~masks[g]]) or not np.isfinite(p).all():raise ValueError('Invalid routing response')
    return counts
