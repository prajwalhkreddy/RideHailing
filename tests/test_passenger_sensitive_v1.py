import json,tempfile,unittest
from pathlib import Path
import numpy as np
from src.pricing.passenger_sensitive_v1 import *
from src.rl.passenger_sensitive_dqn import *

def state():
 s=np.zeros(13);s[3]=1.;return s

def provider(seed=42,floor=.1):
 return PositiveEpsilonProvider([.01,.5,2,2],floor,rng=np.random.default_rng(seed),provenance={'calibration_start':'2026-01-01','calibration_last_timestamp':'2026-03-15 23:59'})

class V1Tests(unittest.TestCase):
 def test_equation(self):
  self.assertEqual(maximum_price(L_BASE_KM,2),P_BASE_USD)
  self.assertLess(maximum_price(1,2),P_BASE_USD);self.assertGreater(maximum_price(10,2),P_BASE_USD)
  self.assertLess(maximum_price(0,.01),0)
 def test_invalid_epsilon(self):
  for e in [0,-1,np.nan,np.inf]:
   with self.assertRaises(ValueError):maximum_price(3,e)
 def test_provider(self):
  a,b=provider(),provider();aa=[a.sample() for _ in range(100)];bb=[b.sample() for _ in range(100)]
  self.assertEqual(aa,bb);self.assertTrue(all(x.value>=.1 for x in aa));self.assertTrue(any(x.raw<.1 for x in aa))
  with self.assertRaises(ValueError):provider(floor=None)
  with self.assertRaises(ValueError):a.require_training_ready()
 def test_mask_boundary(self):
  self.assertTrue(feasible_mask(CANDIDATE_PRICES[0])[0]);self.assertFalse(feasible_mask(np.nextafter(CANDIDATE_PRICES[0],-np.inf)).any())
  np.testing.assert_array_equal(CANDIDATE_PRICES,np.array(ACTIONS)*P_BASE_USD)
 def test_fresh_and_masked_actions(self):
  l=PassengerSensitiveDQN();m=np.array([False,True,False,True,False,False,False])
  for _ in range(100):self.assertIn(l.select_action(state(),m).action_index,[1,3])
  self.assertIn(l.select_action(state(),m,explore=False).action_index,[1,3])
  self.assertIsNone(l.select_action(state(),np.zeros(7,bool)))
  self.assertEqual(l.training_steps,0);self.assertEqual(len(l.replay),0);self.assertEqual(l.epsilon,1.)
  for a,b in zip(l.online.get_weights(),l.target.get_weights()):np.testing.assert_array_equal(a,b)
 def test_masked_target(self):
  m=np.array([[True,False,False,False,False,False,False]])
  y=masked_targets([2],[False],[[3,10000,9,9,9,9,9]],m,[30]);self.assertAlmostEqual(float(y[0]),2+.99*3,places=5)
 def test_request_discount_independent_of_elapsed_time(self):
  m=np.ones((4,7),bool);q=np.ones((4,7))*10
  y=masked_targets([0]*4,np.zeros(4,bool),q,m,[0,1/60,30,60]);np.testing.assert_array_equal(y,np.full(4,9.9,np.float32))
 def test_terminal(self):
  self.assertEqual(masked_targets([4],[True],np.ones((1,7))*100,np.zeros((1,7),bool),[30])[0],4)
 def test_empty_nonterminal_raises(self):
  with self.assertRaises(ValueError):masked_targets([4],[False],np.ones((1,7)),np.zeros((1,7),bool),[0])
 def test_replay_schema(self):
  r=RequestReplay();r.add(state(),2,5,state(),False,np.ones(7,bool),0);self.assertEqual(len(r.sample(1)),7)
  with self.assertRaises(ValueError):r.add(state(),None,0,state(),True,np.zeros(7,bool),0)
 def test_next_actionable(self):
  l=PassengerSensitiveDQN();link=ActionableRequestLinker(l);m=np.ones(7,bool)
  link.observe(1,state(),0,5,'2026-03-01 00:00',m)
  link.observe(2,state(),None,0,'2026-03-01 00:01',np.zeros(7,bool));self.assertEqual(len(l.replay),0)
  link.observe(3,state(),1,0,'2026-03-01 00:31',m);self.assertEqual(len(l.replay),1)
  self.assertEqual(link.audit[0]['next_actionable_request_id'],3);self.assertEqual(link.audit[0]['delta_t_minutes'],31)
  link.finish_episode('2026-03-01 01:00');self.assertEqual(len(l.replay),2);self.assertTrue(link.audit[-1]['done'])
 def test_same_timestamp(self):
  l=PassengerSensitiveDQN();k=ActionableRequestLinker(l);m=np.ones(7,bool)
  for i in range(2):k.observe(i,state(),0,0,'2026-03-01',m)
  self.assertEqual(k.audit[0]['gamma_eff'],.99)
 def test_chronology(self):
  k=ActionableRequestLinker(PassengerSensitiveDQN());k.observe(0,state(),None,0,'2026-03-02',np.zeros(7,bool))
  with self.assertRaises(ValueError):k.observe(1,state(),None,0,'2026-03-01',np.zeros(7,bool))
 def test_cadence(self):
  l=PassengerSensitiveDQN();self.assertEqual(l.complete_slot('2026-03-01'),[])
  for _ in range(1000):l.store(state(),0,0,state(),True,np.zeros(7,bool),0)
  self.assertEqual(len(l.complete_slot('2026-03-01')),8);self.assertEqual(l.training_steps,8)
  for _ in range(1000):l.store(state(),0,0,state(),True,np.zeros(7,bool),0)
  self.assertEqual(len(l.complete_slot('2026-03-01 00:30')),8);self.assertEqual(l.training_steps,16)
 def test_protected_dates(self):
  for t in ['2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):guard_date(t)
  with self.assertRaises(ValueError):guard_date('2026-03-16',calibration=True)
 def test_checkpoint_roundtrip(self):
  a=PassengerSensitiveDQN();a.store(state(),1,3,state(),False,np.ones(7,bool),4)
  with tempfile.TemporaryDirectory() as tmp:
   a.save(tmp);b=PassengerSensitiveDQN.load(tmp)
   self.assertEqual(len(b.replay),1);self.assertEqual(b.replay.items[0][-1],4)
   for x,y in zip(a.online.get_weights(),b.online.get_weights()):np.testing.assert_array_equal(x,y)
 def test_old_checkpoint_rejected_without_load(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'checkpoint.json').write_text(json.dumps({'version':1}))
   with self.assertRaises(ValueError):PassengerSensitiveDQN.load(tmp)
 def test_time_aware_checkpoint_rejected_before_loading_models(self):
  with tempfile.TemporaryDirectory() as tmp:
   Path(tmp,'checkpoint.json').write_text(json.dumps({'schema':'passenger_sensitive_request_v1'}))
   with self.assertRaises(ValueError):PassengerSensitiveDQN.load(tmp)
 def test_wrong_state_dimension(self):
  with self.assertRaises(ValueError):PassengerSensitiveDQN().select_action(np.zeros(14),np.ones(7,bool))

class V1AdditionalTests(unittest.TestCase):
 def test_greedy_masks_highest_q(self):
  l=PassengerSensitiveDQN();weights=l.online.get_weights()
  for w in weights:w.fill(0)
  weights[-1][:]=[10000,2,3,4,5,6,7];l.online.set_weights(weights)
  mask=np.array([False,True,True,False,False,False,False])
  self.assertEqual(l.select_action(state(),mask,explore=False).action_index,2)
 def test_no_action_preserves_rng(self):
  l=PassengerSensitiveDQN();before=json.dumps(l.rng.bit_generator.state)
  l.select_action(state(),np.zeros(7,bool));self.assertEqual(before,json.dumps(l.rng.bit_generator.state))
 def test_invalid_delta(self):
  with self.assertRaises(ValueError):masked_targets([0],[False],np.zeros((1,7)),np.ones((1,7),bool),[-1])
 def test_pending_across_empty_period(self):
  l=PassengerSensitiveDQN();k=ActionableRequestLinker(l)
  k.observe(1,state(),1,0,'2026-03-01 00:00',np.ones(7,bool))
  k.observe(2,state(),None,0,'2026-03-01 01:00',np.zeros(7,bool))
  self.assertEqual(len(l.replay),0);k.observe(3,state(),0,5,'2026-03-01 01:30',np.ones(7,bool))
  self.assertEqual(k.audit[0]['delta_t_minutes'],90);self.assertEqual(k.audit[0]['reward'],0)
 def test_empty_episode(self):
  l=PassengerSensitiveDQN();k=ActionableRequestLinker(l)
  k.observe(1,state(),None,0,'2026-03-01',np.zeros(7,bool));k.finish_episode('2026-03-01 00:30');self.assertEqual(len(l.replay),0)
 def test_provider_rejects_signed_values(self):
  with self.assertRaises(ValueError):PositiveEpsilonProvider([-1,1],.1,rng=np.random.default_rng(42),provenance={'calibration_start':'2026-01-01','calibration_last_timestamp':'2026-03-15'})
 def test_training_gate_requires_frozen_decision(self):
  p=provider();p.frozen=True
  with self.assertRaises(ValueError):p.require_training_ready()
 def test_no_offer_request_validation(self):
  from src.dispatch.request import RequestState,RequestStatus
  r=RequestState(1,0,0,1,status=RequestStatus.UNSERVED,v1_pricing_outcome='NO_FEASIBLE_PRICING_ACTION')
  r.validate(range(142),15);r.customer_accepted=False
  with self.assertRaises(ValueError):r.validate(range(142),15)

class V1SavedIntegrationTests(unittest.TestCase):
 def test_actual_bounded_slot_outputs(self):
  import pandas as pd
  r=Path('results/analysis/2026-11-07_passenger_sensitive_pricing_v1')
  f=pd.read_csv(r/'request_level_mask_validation.csv');t=pd.read_csv(r/'request_level_transition_validation.csv');slots=pd.read_csv(r/'slot_validation.csv')
  self.assertEqual(len(f),400);no=f.selected_action_index.isna()
  self.assertEqual(int(no.sum()),277);self.assertTrue(f.loc[no,'P_offer_USD'].isna().all());self.assertTrue(f.loc[no,'passenger_status'].eq('NOT_OFFERED').all())
  self.assertTrue((f.loc[no,'reward']==0).all());self.assertFalse(f.loc[no,'transition_created'].any())
  self.assertEqual(len(t),123);self.assertEqual(int(slots.offered_passenger_rejected.sum()),0)
  np.testing.assert_allclose(f.loc[f.assignment_status,'reward'],f.loc[f.assignment_status,'P_offer_USD'])
  # Historical fixture is intentionally unchanged, not the current target contract.
  np.testing.assert_allclose(t.gamma_eff,.99**(t.delta_t_minutes/30))
  self.assertEqual(int(slots.optimizer_updates.sum()),0);self.assertTrue((slots.fleet_size==5000).all())
 def test_next_mask_and_request_times(self):
  import pandas as pd,ast
  r=Path('results/analysis/2026-11-07_passenger_sensitive_pricing_v1');f=pd.read_csv(r/'request_level_mask_validation.csv').set_index('Request_ID');t=pd.read_csv(r/'request_level_transition_validation.csv')
  columns=['mask_'+x for x in ['085','090','095','100','105','110','115']]
  for row in t.itertuples():
   if row.done:continue
   current=f.loc[row.Request_ID];nxt=f.loc[int(row.next_actionable_request_id)]
   self.assertAlmostEqual(row.delta_t_minutes,(pd.Timestamp(nxt.timestamp)-pd.Timestamp(current.timestamp)).total_seconds()/60)
   np.testing.assert_array_equal(ast.literal_eval(row.next_action_mask),nxt[columns].to_numpy(bool))
 def test_unresolved_floor_training_gate(self):
  m=json.loads(Path('models/pricing_dqn/passenger_sensitive_v1_seed42/training_gate.json').read_text())
  self.assertFalse(m['long_training_allowed']);self.assertTrue(m['fresh_untrained'])
