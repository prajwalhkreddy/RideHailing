import unittest
import numpy as np,pandas as pd
from src.pricing.dqn_contract import *

def fixture():
 t=pd.Timestamp('2026-03-16');start=t-pd.Timedelta(minutes=30)
 ledger=DispatchLedger();events=[DispatchOutcome(1,0,start,True,True,20),DispatchOutcome(2,0,start,True,False,90),DispatchOutcome(3,0,start,False,False,80),DispatchOutcome(4,0,start,True,True,30)]
 ledger.complete_slot(start,t,events)
 snap=lambda values:Snapshot(t,t,values,start)
 b=PricingStateBuilder(snap({0:12}),ledger,[PassengerCommitment(1,0,start,t+pd.Timedelta(minutes=10))],snap({0:[.2,.1,.1,.1,.1,.1,.1,.1,.1]}),snap({0:.25,1:.75}),{0:[True]*9})
 return t,b,events
class PricingContractTests(unittest.TestCase):
 def test_exact_state_and_destination(self):
  t,b,_=fixture();expected=[12,2,1,.2,.1,.1,.1,.1,.1,.1,.1,.1,.75]
  np.testing.assert_allclose(b.build(0,1,t),expected)
  x=b.build(0,0,t);np.testing.assert_equal(x[:-1],expected[:-1]);self.assertEqual(x[-1],.25)
 def test_reward(self):
  t,b,e=fixture();self.assertEqual(b.ledger.completed[t-pd.Timedelta(minutes=30)][2],50)
 def test_acceptance(self):
  self.assertTrue(threshold_acceptance(20,4,4,2,.95)[0]);self.assertTrue(threshold_acceptance(20,4,4,2,1)[0]);self.assertFalse(threshold_acceptance(20,4,4,2,1.05)[0])
  self.assertEqual(threshold_acceptance(20,4,6,2,1)[2],25)
  self.assertEqual(threshold_acceptance(20,4,2,2,1)[2],15)
  for E in [0,-1,float('nan')]:
   with self.assertRaises(ValueError):threshold_acceptance(20,4,4,E,1)
 def test_actions(self):
  self.assertEqual(PRICING_FACTORS,(.85,.9,.95,1.,1.05,1.1,1.15));self.assertEqual(offered_fare(20,1.1),22)
  with self.assertRaises(ValueError):offered_fare(20,2.)
 def test_lag_missing(self):
  t,b,_=fixture()
  with self.assertRaises(ValueError):b.ledger.previous(t+pd.Timedelta(minutes=30))
 def test_timing(self):
  t,b,_=fixture();b.forecast=Snapshot(t,t+pd.Timedelta(seconds=1),{0:12},t)
  with self.assertRaises(ValueError):b.build(0,1,t)
  t,b,_=fixture();b.popularity=Snapshot(t,t,{1:.75},t+pd.Timedelta(minutes=30))
  with self.assertRaises(ValueError):b.build(0,1,t)
 def test_arrivals(self):
  t,b,_=fixture();prior=t-pd.Timedelta(minutes=1)
  c=[PassengerCommitment(1,0,prior,t),PassengerCommitment(2,0,prior,t+pd.Timedelta(minutes=30)),PassengerCommitment(3,0,prior,t+pd.Timedelta(minutes=31))]
  self.assertEqual(incoming(c,t)[0],1)
  with self.assertRaises(ValueError):incoming([PassengerCommitment(4,0,t,t+pd.Timedelta(minutes=2))],t)
 def test_invalid_states(self):
  for vector in [[1]*5,[.2]*9,[float('nan')]*9]:
   t,b,_=fixture();b.routing=Snapshot(t,t,{0:vector},t)
   with self.assertRaises(ValueError):b.build(0,1,t)
  t,b,_=fixture();b.action_masks[0][1]=False
  with self.assertRaises(ValueError):b.build(0,1,t)
  for g in [-1,142,1.2]:
   with self.assertRaises(ValueError):b.build(g,1,t)
 def test_missing_and_time(self):
  t,b,_=fixture()
  with self.assertRaises(ValueError):b.build(0,2,t)
  with self.assertRaises(ValueError):b.build(0,1,t+pd.Timedelta(minutes=1))
 def test_verified_behavioral_source(self):
  model=behavioural_model(np.random.default_rng(42),'2026-03-16')
  p=model.parameters_for(1.,16);self.assertGreater(p.p_base,0);self.assertGreater(p.d_base,0)
  self.assertGreater(model.sample_epsilon(1.,16),0)
 def test_artifacts(self):
  a,b=artifact_snapshots('2026-03-16');self.assertEqual(len(a.values),142);self.assertEqual(len(b.values),142)
 def test_runtime_adapters(self):
  from src.dispatch.request import RequestState,RequestStatus
  r=RequestState(1,14,0,1,status=RequestStatus.ASSIGNED,assigned_vehicle_id=7,offered_fare=25,customer_accepted=True,trip_duration_minutes=10)
  events=completed_request_outcomes([r],'2026-03-15 23:30')
  self.assertEqual(events[0].fare_usd,25)
  c=passenger_commitment(r,'2026-03-15 23:30')
  self.assertEqual(incoming([c],'2026-03-16')[1],1)
  mask=[True]+[False]*8
  np.testing.assert_equal(mean_routing_response([[1]+[0]*8,[1]+[0]*8],mask),[1]+[0]*8)
  with self.assertRaises(ValueError):mean_routing_response([],mask)
if __name__=='__main__':unittest.main()
