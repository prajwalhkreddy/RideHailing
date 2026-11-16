import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np
from src.simulation.v3_episode1_protocol import TIMESTAMPS,assert_slot,update_after_slot
from src.rl.slot_pricing_v3 import SlotDQN
from src.pricing.slot_v3 import load_contract
class Episode1ProtocolTests(unittest.TestCase):
 def test_exact_timestamps(self):
  self.assertEqual(len(TIMESTAMPS),16);self.assertEqual(TIMESTAMPS[0],datetime(2026,3,1));self.assertEqual(TIMESTAMPS[-1],datetime(2026,3,1,7,30))
  self.assertTrue(all((b-a).total_seconds()==1800 for a,b in zip(TIMESTAMPS,TIMESTAMPS[1:])))
 def test_protected_dates(self):
  for day in range(16,32):
   with self.assertRaises(ValueError):assert_slot(datetime(2026,3,day),0)
  with self.assertRaises(ValueError):assert_slot(datetime(2026,3,1,8),16)
 def runtime(self,n):
  learner=SimpleNamespace(replay=[None]*n,training_steps=0)
  def step():learner.training_steps+=1;return .1
  learner.train_step=Mock(side_effect=step)
  return SimpleNamespace(checkpoint_phase='POST_SLOT_COMMIT',engine=SimpleNamespace(timestamp=datetime(2026,3,1,4)),slots=8,learner=learner)
 def test_below_warmup(self):
  r=self.runtime(999);self.assertEqual(update_after_slot(r),[]);r.learner.train_step.assert_not_called()
 def test_eight_updates(self):
  for n in [1000,1136,2272]:
   r=self.runtime(n);self.assertEqual(len(update_after_slot(r)),8);self.assertEqual(r.learner.training_steps,8)
 def test_mid_slot_rejected(self):
  r=self.runtime(1136);r.checkpoint_phase='IN_SLOT'
  with self.assertRaises(ValueError):update_after_slot(r)
 def test_exploration_optimizer_only(self):
  d=SlotDQN(42);s=np.zeros(15);s[4]=1
  for _ in range(3):d.select_action(s)
  self.assertEqual(d.epsilon,1.);self.assertEqual(d.decisions,3)
  for _ in range(1000):d.store(s,0,0.,s,False)
  d.train_step();self.assertEqual(d.training_steps,1);self.assertEqual(d.epsilon,1-.95/50000)
  d.select_action(s);self.assertEqual(d.epsilon,1-.95/50000)
 def test_frozen_protocol(self):
  p=load_contract()['training_protocol'];self.assertEqual(p['exploration_decay_unit'],'optimizer_update');self.assertEqual(p['optimizer_updates_per_warm_slot'],8);self.assertEqual(p['seed'],42);self.assertEqual(p['sensitivity_seed'],43)
if __name__=='__main__':unittest.main()
