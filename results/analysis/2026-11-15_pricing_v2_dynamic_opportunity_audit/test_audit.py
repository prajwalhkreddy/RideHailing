import unittest,types
import numpy as np
from audit import methods,prior
class InfrastructureTests(unittest.TestCase):
 def test_boundary_instrumentation(self):
  a,b=methods();self.assertTrue(callable(a));self.assertTrue(callable(b));self.assertIn('route_idle',b.__code__.co_names);self.assertIn('complete_slot',b.__code__.co_names)
 def test_clone_rng_and_isolation(self):
  e=types.SimpleNamespace(pricing=types.ModuleType('pricing'),policy=object(),dqn=types.SimpleNamespace(learner=object()),provider=types.SimpleNamespace(rng=np.random.default_rng(42)),fleet=types.SimpleNamespace(vehicles=[{'soc':5}]))
  a=prior.clone(e);b=prior.clone(e);self.assertEqual(a.provider.rng.random(),b.provider.rng.random());a.fleet.vehicles[0]['soc']=0;self.assertEqual(b.fleet.vehicles[0]['soc'],5)
 def test_eligibility_expansion_and_driver_change(self):
  from audit import eligible,pick
  from src.charging.energy import EnergyParameters
  from src.fleet.state import VehicleStatus
  import yaml
  from pathlib import Path
  energy=EnergyParameters(**yaml.safe_load(Path('config/config.yaml').read_text())['energy'])
  v=lambda i:types.SimpleNamespace(vehicle_id=i,current_grid=0,trip_status=VehicleStatus.IDLE,energy_level=60.)
  env=types.SimpleNamespace(lookup={0:()},fleet=types.SimpleNamespace(vehicles=[v(1),v(2)]),energy=energy,station_reserve=lambda g:0.,profiles=types.SimpleNamespace(price_preference={1:25.,2:20.}))
  request=types.SimpleNamespace(origin_grid=0,destination_grid=1,trip_distance_km=3.,offered_fare=None)
  self.assertEqual(eligible(env,request,22.),{2});self.assertEqual(eligible(env,request,26.),{1,2})
  self.assertEqual(pick(env,request,22.),2);self.assertEqual(pick(env,request,26.),1)
  self.assertIsNone(request.offered_fare)
 def test_protected_guard(self):
  from src.pricing.passenger_sensitive_v1 import guard_date
  with self.assertRaises(ValueError):guard_date('2026-03-17')
if __name__=='__main__':unittest.main()
