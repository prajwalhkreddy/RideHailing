import unittest,pickle
import numpy as np
import pandas as pd
from src.pricing.empirical_sensitivity import absolute_epsilon,EmpiricalCustomerSensitivityModel
from src.pricing.customer_sensitivity import maximum_price

class EmpiricalPassengerTests(unittest.TestCase):
 def model(self,seed=42):
  x=pd.DataFrame(dict(WeatherCode=[1,1,1,1,8,8,8,8],Period=[0,0,0,0,1,1,1,1],fare_amount=[10,20,10,20,20,40,20,40],trip_distance=[1,3,1,3,2,8,2,8]))
  return EmpiricalCustomerSensitivityModel(x,np.random.default_rng(seed))
 def test_formula_sign_zero_nonfinite(self):
  e,v,c=absolute_epsilon([10,20,30,40,np.inf],[2,3,3,4,3],20,3)
  self.assertAlmostEqual(e[0],2/3);self.assertFalse(v[1]);self.assertFalse(v[2]);self.assertFalse(v[4]);self.assertEqual(c['exact_zero_delta_P'],1);self.assertEqual(c['nonpositive'],2)
 def test_negative_ratio_absolute(self):
  e,v,c=absolute_epsilon([10],[4],20,3);self.assertAlmostEqual(e[0],2/3);self.assertTrue(v[0])
 def test_near_zero_retained_exactly(self):
  e,v,c=absolute_epsilon([10],[3.0000000001],20,3);self.assertTrue(v[0]);self.assertLess(e[0],.001)
 def test_seed_membership_replacement(self):
  a=self.model();b=self.model();x=[a.sample_epsilon(1,0) for _ in range(100)];y=[b.sample_epsilon(1,0) for _ in range(100)];self.assertEqual(x,y);pool=a.pool_for(a.resolve_parameters(1,0));self.assertTrue(np.isin(x,pool).all());self.assertGreater(len(x),len(pool));self.assertGreaterEqual(min(x),min(pool))
 def test_context_fallback(self):
  m=self.model()
  for w,t,level in [(1,0,'exact'),(99,0,'period'),(1,47,'weather'),(99,47,'global')]:self.assertEqual(m.resolve_parameters(w,t).fallback_level_used,level)
  self.assertNotEqual(m.parameters[('exact',1.,0)].d_base,m.parameters[('exact',8.,1)].d_base)
 def test_empty_exact_pool_falls_back(self):
  x=pd.DataFrame(dict(WeatherCode=[1,8,8],Period=[0,0,0],fare_amount=[10,20,30],trip_distance=[1,4,8]));m=EmpiricalCustomerSensitivityModel(x,np.random.default_rng(42));self.assertEqual(m.resolve_parameters(1,0).fallback_level_used,'period')
 def test_signed_distance_and_acceptance_equality(self):
  self.assertEqual(maximum_price(20,4,6,2),25);self.assertEqual(maximum_price(20,4,4,2),20);self.assertEqual(maximum_price(20,4,2,2),15)
  m=self.model();r=m.resolve_parameters(1,0);d=m.evaluate_resolved(r,r.parameters.d_base,1.);self.assertEqual(d.p_dispatch,d.p_max);self.assertTrue(d.accepted)
 def test_pmax_fail_closed(self):
  for e in [0,-1,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):maximum_price(20,4,6,e)
  with self.assertRaises(ValueError):maximum_price(1e308,1,1e308,1e-300)
 def test_checkpoint_next_draw(self):
  m=self.model();m.sample_epsilon(1,0);restored=pickle.loads(pickle.dumps(m));self.assertEqual([m.sample_epsilon(8,1) for _ in range(100)],[restored.sample_epsilon(8,1) for _ in range(100)])
 def test_duplicate_frequency_preserved(self):
  m=self.model();self.assertEqual(len(m.pools[('exact',1.,0)]),4)
