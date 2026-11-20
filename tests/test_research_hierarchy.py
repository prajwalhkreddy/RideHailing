import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np,pandas as pd
from src.routing.research_hierarchy import DriverHierarchy,VERSION
from src.routing.learning import LocalPolicyObservation
from src.fleet.research_mixed import configure
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from tests.test_utc_od_runtime import inputs
from tests.test_od_pricing import evidence
from src.pricing.od_contract import support_from_trips
ROUTE='results_v2/simulation/2026-11-17_prospective_utility_acceptance/routing_contract.json'
def fleet(n):return Fleet([VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(n)],frozenset(range(142)),2)
def runtime(seed=42,mode="UTILITY"):
 return ODPricingRuntime(start='2026-03-12',routing_checkpoint=ROUTE,research_routing=True,driver_hierarchy=DriverHierarchy(seed=seed,mode=mode),ev_share=.2,seed=seed,fleet=fleet(10),driver_profiles=pd.DataFrame(dict(vehicle_id=range(10),price_preference=[0.]*10,wait_preference=[10.]*10,charging_wait_preference_minutes=[10.]*10)),utc_inputs=inputs('2026-03-12'),od_support=support_from_trips(evidence()))
class HierarchyTests(unittest.TestCase):
 def test_fresh_global_runtime_feedback(self):
  a=runtime(mode='FRESH_UNTRAINED_GLOBAL')
  self.assertIsNone(a.engine.policy)
  a.run_slot([],policy=lambda d,s:0)
  self.assertEqual(a.engine.driver_hierarchy.round,1)
  self.assertFalse(a.engine.driver_hierarchy._locals)
  self.assertTrue(all(np.isfinite(x).all() for x in a.states.values()))
 def test_mixed_percentages(self):
  for share,n in [(.1,500),(.2,1000),(.3,1500)]:
   a=fleet(5000);b=fleet(5000);configure(a,share,42);configure(b,share,42)
   self.assertEqual(sum(v.is_ev for v in a.vehicles),n);self.assertEqual([vars(v) for v in a.vehicles],[vars(v) for v in b.vehicles])
 def test_federation_private_release_and_resume(self):
  a=DriverHierarchy(mode='FRESH_UNTRAINED_GLOBAL',updates_enabled=True)
  mask=np.ones(9,dtype=bool);state=np.ones(169,dtype=np.float32)
  for d in [0,1]:a.record(d,LocalPolicyObservation(state,d,mask,slot_id=0))
  start=pd.Timestamp('2026-03-12',tz='UTC');end=start+pd.Timedelta(minutes=30)
  before=[v.copy() for v in a._global.get_weights()];release=a.finish_slot(start,end)
  self.assertEqual(set(release),{'version','round','participants','privacy','available_at'})
  self.assertTrue(any(not np.array_equal(x,y) for x,y in zip(before,a._global.get_weights())))
  with self.assertRaises(ValueError):a.mean_probabilities([state],{0:mask},start)
  with self.assertRaises(ValueError):a.finish_slot(start,end)
  b=DriverHierarchy.restore(a.snapshot())
  for x in [a,b]:
   for d in [0,1]:x.record(d,LocalPolicyObservation(state,d,mask,slot_id=1))
   x.finish_slot(end,end+pd.Timedelta(minutes=30))
  self.assertEqual(encode(a.snapshot()),encode(b.snapshot()))
  p=a.mean_probabilities([state],{0:mask},end+pd.Timedelta(minutes=30))[0];self.assertAlmostEqual(p.sum(),1,places=6)
  with self.assertRaises(ValueError):DriverHierarchy(mode='HISTORICAL_CHECKPOINT')
 def test_mixed_runtime_resume(self):
  a=runtime();non=next(v for v in a.engine.fleet.vehicles if not v.is_ev)
  from src.charging.energy import deduct_passenger_trip_energy,requires_charging
  self.assertEqual(deduct_passenger_trip_energy(non,10,a.engine.energy),0);self.assertFalse(requires_charging(non,a.engine.energy))
  station=next(iter(a.engine.charging.stations.values()))
  original_grid=non.current_grid;non.current_grid=station.grid_id
  with self.assertRaisesRegex(ValueError,'threshold'):a.engine.charging.admit_arrived(non,station.station_id,a.engine.energy,0)
  non.current_grid=original_grid
  from src.dispatch.dispatch import find_eligible_vehicle
  from types import SimpleNamespace
  request=SimpleNamespace(origin_grid=non.current_grid,destination_grid=1,trip_distance_km=10.)
  selected=find_eligible_vehicle(request,Fleet([non],frozenset(range(142)),2),{},a.engine.energy,lambda g:1000.)
  self.assertIs(selected,non)
  a.run_slot([],policy=lambda d,s:0)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'snapshot';save_od_checkpoint(a,path)
   with self.assertRaises(ValueError):load_od_checkpoint(path,master_math=True,utc_mode=True)
   b=load_od_checkpoint(path,master_math=True,utc_mode=True,hierarchy_contract=a.engine.driver_hierarchy.contract(),ev_composition=a.engine.ev_composition)
   for x in [a,b]:x.run_slot([],policy=lambda d,s:0)
   self.assertEqual(encode(a.engine.fleet),encode(b.engine.fleet));self.assertEqual(encode(a.engine.charging),encode(b.engine.charging));self.assertEqual(encode(a.engine.driver_hierarchy.snapshot()),encode(b.engine.driver_hierarchy.snapshot()))
   for pair in a.states:np.testing.assert_array_equal(a.states[pair],b.states[pair])
   self.assertTrue(all(v.energy_level==0 for v in a.engine.fleet.vehicles if not v.is_ev))
 def test_prospective_learning_not_authorized_by_baseline_manifest(self):
  manifest=json.loads(Path('results_v2/simulation/2026-11-17_prospective_utility_acceptance/information_contract.json').read_text())
  with self.assertRaisesRegex(ValueError,'online-learning provenance'):
   ODPricingRuntime(start='2026-03-12',routing_checkpoint=ROUTE,information_contract=manifest,driver_hierarchy=DriverHierarchy(mode='FRESH_UNTRAINED_GLOBAL'))
 def test_gym_checker(self):
  from src.simulation.od_gymnasium import ODPricingEnv
  from gymnasium.utils.env_checker import check_env
  def factory(seed=None):
   r=runtime(42 if seed is None else seed);original=r.run_slot
   r.run_slot=lambda **kw:original([],**kw)
   return r
  pairs=runtime().pairs
  env=ODPricingEnv(factory,pairs,horizon=2);check_env(env,skip_render_check=True)
  env.reset(seed=42);action=np.zeros(len(pairs),dtype=np.int64)
  env.step(action);_,_,terminated,truncated,info=env.step(action)
  self.assertFalse(terminated);self.assertTrue(truncated);self.assertNotIn('driver_preferences',info)
