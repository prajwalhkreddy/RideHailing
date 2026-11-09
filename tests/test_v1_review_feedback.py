import unittest,json
from pathlib import Path
import numpy as np
from src.pricing.passenger_sensitive_v1 import *
from src.rl.passenger_sensitive_dqn import masked_targets
R=Path('results/analysis/2026-11-07_passenger_sensitive_pricing_v1')
class ReviewTests(unittest.TestCase):
 def test_threshold_cases(self):
  for raw in [-100,0,P_PLATFORM_MIN-1,P_PLATFORM_MIN,P_BASE_USD,P_PLATFORM_MAX,1000]:
   a=effective_threshold(raw)
   self.assertGreaterEqual(a,raw);self.assertGreaterEqual(a,P_PLATFORM_MIN)
   self.assertEqual(a,raw if raw>=P_PLATFORM_MIN else P_PLATFORM_MIN)
   self.assertTrue(feasible_mask(a)[0])
 def test_invalid_threshold(self):
  for x in [np.nan,np.inf,-np.inf]:
   with self.assertRaises(ValueError):effective_threshold(x)
 def test_arms_exact(self):
  self.assertEqual(ACTIONS,(.85,.90,.95,1,1.05,1.10,1.15))
  self.assertEqual(P_PLATFORM_MIN,.85*P_BASE_USD);self.assertEqual(P_PLATFORM_MAX,1.15*P_BASE_USD)
  np.testing.assert_array_equal(CANDIDATE_PRICES,np.array(ACTIONS)*P_BASE_USD)
 def test_effective_target(self):
  m=feasible_mask(effective_threshold(-10))[None,:]
  self.assertEqual(m.sum(),1)
  y=masked_targets([2],[False],[[3,1e6,1e6,1e6,1e6,1e6,1e6]],m,[30])
  self.assertAlmostEqual(float(y[0]),2+.99*3,places=5)
 def test_positive_sequence_not_signed_first(self):
  import pandas as pd
  t=pd.to_datetime(['2026-01-01']*5+['2026-03-16','2026-03-17'])
  e=np.array([-10,-1,0,np.nan,2,10000,20000])
  z=np.abs(e[(t<pd.Timestamp('2026-03-16'))&np.isfinite(e)&(e!=0)])
  np.testing.assert_array_equal(z,[10,1,2]);self.assertGreater(np.quantile(z,.005),0)
 def test_truncated_sampling_duplicate_mass(self):
  prov={'calibration_start':'2026-01-01','calibration_last_timestamp':'2026-03-15','sampling_family':'TRUNCATED_EMPIRICAL_RESAMPLING','positive_support_lower':1.,'positive_support_upper':2.}
  def p():return PositiveEpsilonProvider([1,2,2,2],1,rng=np.random.default_rng(42),provenance=prov)
  a,b=p(),p();x=np.array([a.sample().value for _ in range(2000)]);y=np.array([b.sample().value for _ in range(2000)])
  np.testing.assert_array_equal(x,y);self.assertTrue(((x>=1)&(x<=2)).all());self.assertTrue(.70<(x==2).mean()<.80)
  for values,floor in [([.9,2],1),([1,3],1),([1,2],1.1)]:
   with self.assertRaises(ValueError):PositiveEpsilonProvider(values,floor,rng=np.random.default_rng(1),provenance=prov)
 def test_saved_corrected_support(self):
  s=json.loads((R/'restricted_calibration_support.json').read_text())
  self.assertEqual(s['support_name'],'V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT')
  self.assertLess(s['calibration_last_timestamp'],'2026-03-16')
  self.assertEqual(s['N_positive_supported'],8598805)
 def test_saved_new_fixture(self):
  import pandas as pd,ast
  q=R/'review_feedback_reconciliation';f=pd.read_csv(q/'request_level_review_feedback_validation.csv');t=pd.read_csv(q/'request_level_transition_validation.csv')
  self.assertEqual(len(f),400);self.assertEqual(len(t),400)
  self.assertTrue((f.feasible_action_count>=1).all());self.assertTrue((f.P_offer_USD<=f.P_accept_c).all())
  np.testing.assert_allclose(f.P_accept_c,np.maximum(P_PLATFORM_MIN,f.P_raw_c))
  self.assertTrue(f.selected_action_index.notna().all());self.assertTrue(f.transition_created.all())
  np.testing.assert_allclose(f.reward,np.where(f.assignment_status,f.P_offer_USD,0))
  lookup=f.set_index('Request_ID')
  for row in t.itertuples():
   if not row.done:
    nxt=lookup.loc[int(row.next_actionable_request_id)]
    np.testing.assert_array_equal(ast.literal_eval(row.next_action_mask),feasible_mask(nxt.P_accept_c))
 def test_dispatch_audit_formula(self):
  from src.dispatch.request import RequestState,RequestStatus
  r=RequestState(1,0,0,1,trip_distance_km=1,base_fare=P_BASE_USD,offered_fare=P_PLATFORM_MIN,pricing_factor=.85,customer_model='passenger_sensitive_v1',customer_accepted=True,v1_epsilon_c=.1,v1_epsilon_min=.01,v1_raw_pc_usd=maximum_price(1,.1),v1_pc_usd=effective_threshold(maximum_price(1,.1)))
  from datetime import datetime,timedelta
  r.source_trip_id=1;r.empirical_pickup_datetime=datetime(2026,3,12);r.empirical_dropoff_datetime=datetime(2026,3,12)+timedelta(minutes=5);r.trip_duration_minutes=5;r.trip_distance_miles=1/1.609344
  r.validate(range(142),15)
  r.v1_pc_usd+=1
  with self.assertRaises(ValueError):r.validate(range(142),15)
