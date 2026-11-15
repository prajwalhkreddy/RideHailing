import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
from src.pricing.passenger_sensitive_v2 import V2EmpiricalSensitivityProvider,V2PriceContract,resolve_pricing
from src.pricing.passenger_sensitive_v1 import PositiveEpsilonProvider,guard_date,maximum_price,P_BASE_USD,L_BASE_KM

class V2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=V2EmpiricalSensitivityProvider(rng=np.random.default_rng(42))
 def setUp(self):self.p.rng=np.random.default_rng(42)
 def test_population(self):self.assertEqual(len(self.p.values),5779213);self.assertTrue((self.p.values>0).all())
 def test_fixed_seed(self):
  a=self.p.sample_many(100);self.p.rng=np.random.default_rng(42);np.testing.assert_array_equal(a,self.p.sample_many(100))
 def test_different_seed(self):
  a=self.p.sample_many(100);self.p.rng=np.random.default_rng(43);self.assertFalse(np.array_equal(a,self.p.sample_many(100)))
 def test_exact_membership(self):self.assertTrue(np.isin(self.p.sample_many(1000),self.p.values).all())
 def test_replacement(self):
  old=self.p.values
  try:self.p.values=np.array([1.,2.]);a=self.p.sample_many(100);self.assertEqual(len(a),100);self.assertEqual(len(np.unique(a)),2)
  finally:self.p.values=old
 def test_no_floor(self):
  d=self.p.sample();self.assertEqual(d.value,d.raw);self.assertEqual(d.minimum,0.)
 def test_rng_continuation(self):
  self.p.sample_many(20);s=self.p.state_dict();a=self.p.sample_many(100);self.p.load_state_dict(s);np.testing.assert_array_equal(a,self.p.sample_many(100))
 def test_incompatible_state(self):
  for field in ['passenger_sensitivity_version','contract_sha256','empirical_support_sha256']:
   s=self.p.state_dict();s[field]='wrong'
   with self.assertRaises(ValueError):self.p.load_state_dict(s)
 def test_version_gate(self):
  self.assertIs(resolve_pricing('v2',self.p),self.p.pricing)
  with self.assertRaises(ValueError):resolve_pricing('v1',self.p)
 def test_legacy_default(self):
  p=PositiveEpsilonProvider([1,2],.1,rng=np.random.default_rng(42),provenance={'calibration_start':'2026-01-01','calibration_last_timestamp':'2026-03-15'})
  self.assertEqual(resolve_pricing('v1',p).P_BASE_USD,P_BASE_USD)
  self.assertEqual(maximum_price(L_BASE_KM,2),P_BASE_USD)
 def test_units_and_inverse(self):
  c=self.p.pricing;e=2.;distance=c.L_BASE_KM*1.5;price=c.maximum_price(distance,e)
  self.assertAlmostEqual(price,c.P_BASE_USD*1.25)
  self.assertAlmostEqual(((distance-c.L_BASE_KM)/c.L_BASE_KM)/((price-c.P_BASE_USD)/c.P_BASE_USD),e)
 def test_zero_no_fallback(self):
  with self.assertRaises(ValueError):self.p.pricing.maximum_price(5,0)
 def test_finite_and_mask(self):
  for e in self.p.sample_many(100):
   pc=self.p.pricing.effective_threshold(self.p.pricing.maximum_price(3,e));m=self.p.pricing.feasible_mask(pc);self.assertTrue(m[0]);self.assertEqual(m.shape,(7,));self.assertTrue(np.isfinite(pc))
 def test_protected_date(self):
  with self.assertRaises(ValueError):guard_date('2026-03-17')
 def test_training_blocked(self):
  with self.assertRaises(ValueError):self.p.require_training_ready()
 def test_hash_failure(self):
  with tempfile.TemporaryDirectory() as t:
   c=copy.deepcopy(self.p.contract);c['source_hashes']={'x':'incorrect'};Path(t,'x').write_text('changed');Path(t,'c.json').write_text(json.dumps(c))
   with self.assertRaisesRegex(ValueError,'source hash mismatch'):V2EmpiricalSensitivityProvider(rng=np.random.default_rng(42),root=t,contract_path='c.json')
 def test_versioned_checkpoint(self):
  from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
  learner=PassengerSensitiveDQN();learner.sensitivity_provider=self.p
  with tempfile.TemporaryDirectory() as tmp:
   learner.save(tmp);expected=self.p.sample_many(50)
   with self.assertRaises(ValueError):PassengerSensitiveDQN.load(tmp)
   restored=PassengerSensitiveDQN.load(tmp,sensitivity_provider=self.p)
   np.testing.assert_array_equal(expected,self.p.sample_many(50))
   self.assertEqual(restored._loaded_sensitivity_version,'v2')
 def test_legacy_checkpoint_not_v2(self):
  from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'checkpoint.json').write_text(json.dumps({'schema':'passenger_sensitive_request_v1','discount_semantics':'PER_REQUEST_TRANSITION'}))
   with self.assertRaises(ValueError):PassengerSensitiveDQN.load(tmp,sensitivity_provider=self.p)
 def test_contract_hash_failure(self):
  with self.assertRaisesRegex(ValueError,'contract hash mismatch'):
   V2EmpiricalSensitivityProvider(rng=np.random.default_rng(42),expected_contract_sha256='wrong')
 def test_validated_training_gate_without_training(self):
  self.p.training_authorized=True
  try:self.p.require_training_ready()
  finally:self.p.training_authorized=False
 def test_request_v2_price_contract(self):
  from src.dispatch.request import RequestState
  from datetime import datetime,timedelta
  c=self.p.pricing;t=datetime(2026,1,1);km=3.;e=2.;raw=c.maximum_price(km,e);pc=c.effective_threshold(raw)
  r=RequestState(1,0,0,1,base_fare=c.P_BASE_USD,pricing_factor=.85,offered_fare=.85*c.P_BASE_USD,customer_accepted=True,customer_model='passenger_sensitive_v2',source_trip_id=0,empirical_pickup_datetime=t,empirical_dropoff_datetime=t+timedelta(minutes=1),trip_duration_minutes=1.,trip_distance_km=km,trip_distance_miles=km/1.609344,v1_epsilon_c=e,v1_epsilon_min=0.,v1_raw_pc_usd=raw,v1_pc_usd=pc,v2_reference_p_base=c.P_BASE_USD,v2_reference_l_base_km=c.L_BASE_KM)
  r.validate(range(142),15);r.offered_fare+=1
  with self.assertRaises(ValueError):r.validate(range(142),15)
if __name__=='__main__':unittest.main()
