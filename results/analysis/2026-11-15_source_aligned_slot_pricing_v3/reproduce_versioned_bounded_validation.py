import json,hashlib
import numpy as np,pandas as pd
from src.simulation.slot_pricing_v3 import SlotPricingV3
from src.simulation.multi_slot import run_multi_slot_simulation
from src.simulation.main_slot import run_main_slot
from src.simulation.pricing_version import V3
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
from src.dispatch.request import RequestState
from src.routing.final_state import RoutingState,encode_routing_state
from pathlib import Path
p=Path('results/analysis/2026-11-15_source_aligned_slot_pricing_v3')
x=SlotPricingV3(start='2026-03-12',routing_checkpoint='models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras',fleet=Fleet([VehicleState(i,i,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(3)],frozenset(range(142)),2),driver_profiles=pd.DataFrame(dict(vehicle_id=range(3),price_preference=[0.]*3,wait_preference=[10.]*3,charging_wait_preference_minutes=[10.]*3)))
producer=x.engine.operational;rows=[]
for j in range(3):
 t=x.engine.timestamp;before=producer.state_for(t);previous=before.set_index('Grid_ID')
 for g in range(142):
  s=RoutingState.from_producer(x.engine.routing,producer,t,g);assert encode_routing_state(s).shape==(169,)
  assert np.isclose(x.states[g][4:13].sum(),1.)
 r=RequestState(j,0,0,1,base_fare=20.,source_trip_id=j,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=40)).to_pydatetime(),trip_duration_minutes=40.,trip_distance_miles=30/1.609344,trip_distance_km=30.)
 # Same explicit runtime traverses the multi-slot/main-slot dispatch each call.
 run_multi_slot_simulation(pricing_version=V3,runtime=x,slot_requests=[[r]],policy=lambda d,s:0,weather_code=1)
 assert x.engine.operational is producer
 after=producer.state_for(x.engine.timestamp).set_index('Grid_ID');delta=producer.parameters.delta
 for g in range(142):
  n=after.loc[g,'successful_dispatch_count']
  assert np.isclose(after.loc[g,'F_hat'],delta*n/30+(1-delta)*previous.loc[g,'F_hat'])
  if n==0:assert after.loc[g,'mu']==previous.loc[g,'mu'] and after.loc[g,'sigma']==previous.loc[g,'sigma']
 for g in [0,1,2]:
  a=after.loc[g];rows.append(dict(slot=j,grid=g,timestamp=str(x.engine.timestamp),mu=a.mu,sigma=a.sigma,F_hat=a.F_hat,H_hat=a.H_hat,state_hash=hashlib.sha256(after[['mu','sigma','F_hat','H_hat']].to_numpy().tobytes()).hexdigest()))
 try:producer.state_for(t)
 except ValueError:pass
 else:raise AssertionError('stale boundary allowed')
assert x.learner.training_steps==0 and len(x.learner.replay)==426
pd.DataFrame(rows).to_csv(p/'versioned_operational_state_slot_trace.csv',index=False)
(p/'versioned_bounded_validation.json').write_text(json.dumps(dict(slots=3,requests=3,transitions=426,optimizer_updates=0,same_producer=True,current_routing_states_valid=True,no_future_access=True,status='PASS'),indent=2)+'\n')
print('3 slots PASS; same producer; 426 transitions; zero optimizer updates')
