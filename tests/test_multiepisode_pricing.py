import unittest,tempfile
from pathlib import Path
import numpy as np
from src.simulation.multiepisode_pricing import plan,guard,updates_for_slot
from src.rl.pricing_dqn import PricingDQN
class ProtocolTests(unittest.TestCase):
 def test_windows(self):
  a=plan();self.assertEqual(a,plan());self.assertEqual(len(a),500)
  for s in a:guard(s['start'])
  for d in ['2026-03-16','2026-03-17','2026-03-15 17:00']:
   with self.assertRaises(ValueError):guard(d)
 def test_cadence_resume_replay(self):
  a=PricingDQN();s=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
  self.assertEqual(updates_for_slot(a,'2026-03-01'),[])
  for i in range(1000):a.store(s,i%7,float(i%3),s,i%2==0)
  self.assertEqual(len(updates_for_slot(a,'2026-03-01')),8);self.assertEqual(a.training_steps,8)
  with tempfile.TemporaryDirectory() as d:
   a.save(d);b=PricingDQN.load(d);self.assertEqual(len(b.replay),1000);self.assertEqual(updates_for_slot(a,'2026-03-02'),updates_for_slot(b,'2026-03-02'))
   for x,y in zip(a.online.get_weights(),b.online.get_weights()):np.testing.assert_array_equal(x,y)
  with self.assertRaises(ValueError):updates_for_slot(a,'2026-03-16')
  before=(a.training_steps,len(a.replay),a.rng.bit_generator.state);a.select_action(s,explore=False);self.assertEqual(before,(a.training_steps,len(a.replay),a.rng.bit_generator.state))
 def test_checkpoint_creates_episode_namespace(self):
  from unittest.mock import patch
  from src.simulation.multiepisode_pricing import checkpoint
  with tempfile.TemporaryDirectory() as d:
   target=Path(d)/'new_episode'
   def fake(x,ns,rid):
    self.assertTrue(Path(ns).is_dir());return 'saved'
   with patch('src.simulation.multiepisode_pricing._checkpoint',side_effect=fake):self.assertEqual(checkpoint(object(),target,{}),'saved')
if __name__=='__main__':unittest.main()
