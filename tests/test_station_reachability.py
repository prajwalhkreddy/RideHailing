import unittest,math
from types import SimpleNamespace
from tests.test_operational_routing import router,fixture
from src.dispatch.dispatch import find_eligible_vehicle
from src.charging.energy import EnergyParameters
from src.fleet.state import VehicleState,VehicleStatus
from src.fleet.fleet import Fleet
from src.routing.operational_interface import u3
import yaml
from pathlib import Path
class ReserveTests(unittest.TestCase):
 def setUp(self):
  self.r=router();self.energy=EnergyParameters(**yaml.safe_load(Path('config/config.yaml').read_text())['energy'])
 def eligible(self,remaining,reserve=3.):
  v=VehicleState(299,74,VehicleStatus.IDLE,None,0,'idle',20.+remaining)
  f=Fleet([v],frozenset(range(142)),2)
  q=SimpleNamespace(origin_grid=74,destination_grid=104,trip_distance_km=20./.15)
  return find_eligible_vehicle(q,f,{},self.energy,lambda g:reserve)
 def test_passenger_ample(self):self.assertIsNotNone(self.eligible(5))
 def test_passenger_equality(self):self.assertIsNotNone(self.eligible(3))
 def test_passenger_below(self):self.assertIsNone(self.eligible(2.999))
 def test_vehicle299(self):self.assertIsNone(self.eligible(1.7248694329320955,self.r.minimum_station_energy(104,.15)))
 def test_station_zero(self):
  for g in self.r.stations.grid_id:self.assertEqual(self.r.minimum_station_energy(int(g),.15),0)
 def test_multihop_diagonal(self):self.assertAlmostEqual(self.r.minimum_station_energy(104,.15),5*3000*math.sqrt(2)/1000*.15)
 def test_reposition_adequate(self):self.assertTrue(self.r.preserves_station_reachability(20,.45,104,.15))
 def test_reposition_rejection_and_stay(self):
  e=fixture();reserve=self.r.minimum_station_energy(104,.15)
  # Isolated trigger value tests the non-charging argmax at the reserve boundary.
  d=self.r.decide(e,e.timestamp,grid=104,energy_kwh=reserve,minimum_energy_kwh=0,p_min=10,w_max_minutes=1,h_max_minutes=10,energy_per_km=.15)
  self.assertGreater(self.r.reserve_reposition_rejections,0)
  self.assertTrue(self.r.preserves_station_reachability(reserve,d.distance_m/1000*.15,d.next_grid,.15))
  self.assertTrue(self.r.preserves_station_reachability(reserve,0,104,.15))
 def test_trigger_equality(self):
  e=fixture();d=self.r.decide(e,e.timestamp,grid=104,energy_kwh=15,minimum_energy_kwh=15,p_min=10,w_max_minutes=1,h_max_minutes=10,energy_per_km=.15);self.assertEqual(d.branch,'CHARGING')
 def test_u3(self):self.assertAlmostEqual(u3(10,10,wait_floor_minutes=1e-6),.6321205588285577)
 def test_impossible(self):
  e=fixture()
  with self.assertRaisesRegex(ValueError,'No energy-feasible'):self.r.decide(e,e.timestamp,grid=104,energy_kwh=1.724869,minimum_energy_kwh=15,p_min=10,w_max_minutes=1,h_max_minutes=10,energy_per_km=.15)
 def test_timed_no_teleport_nonnegative(self):
  e=fixture();d=self.r.decide(e,e.timestamp,grid=104,energy_kwh=15,minimum_energy_kwh=15,p_min=10,w_max_minutes=1,h_max_minutes=10,energy_per_km=.15)
  v=VehicleState(299,104,VehicleStatus.IDLE,None,0,'idle',15)
  duration=self.r.start_next_hop(v,d,speed_kmph=15,energy_per_km=.15)
  self.assertEqual(v.current_grid,104);self.assertGreater(duration,0);self.assertGreaterEqual(v.energy_level,0)
 def test_legacy_checkpoint_rejected(self):
  from src.simulation.routing_experience_generation import RoutingExperienceExperiment
  x=RoutingExperienceExperiment.__new__(RoutingExperienceExperiment)
  with self.assertRaisesRegex(ValueError,'Superseded pre-reachability'):
   x.restore(Path('data/processed/routing_experiences_mar01_mar15_2026/generation_checkpoint.pkl'))
if __name__=='__main__':unittest.main()

