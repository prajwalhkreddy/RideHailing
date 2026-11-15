import unittest,types,copy
import numpy as np
from review import clone,instrument,sha
from src.pricing.passenger_sensitive_v1 import guard_date
class CounterfactualTests(unittest.TestCase):
 def test_clone_rng_isolation(self):
  e=types.SimpleNamespace(pricing=types.ModuleType('pricing'),policy=object(),dqn=types.SimpleNamespace(learner=object()),provider=types.SimpleNamespace(rng=np.random.default_rng(42),values=np.array([1.,2.])),fleet=types.SimpleNamespace(vehicles=[{'soc':5}]))
  a=clone(e);b=clone(e);self.assertEqual(sha(a.provider.rng.bit_generator.state),sha(b.provider.rng.bit_generator.state));self.assertEqual(a.provider.rng.random(),b.provider.rng.random());a.fleet.vehicles[0]['soc']=0;self.assertEqual(e.fleet.vehicles[0]['soc'],5);self.assertEqual(b.fleet.vehicles[0]['soc'],5)
 def test_instrumentation_compiles(self):
  a,b=instrument();self.assertTrue(callable(a));self.assertTrue(callable(b))
 def test_protected_guard(self):
  with self.assertRaises(ValueError):guard_date('2026-03-17')
  with self.assertRaises(ValueError):guard_date('2026-03-31')
if __name__=='__main__':unittest.main()
