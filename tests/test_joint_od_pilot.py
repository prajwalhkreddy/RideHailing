"""Bounded checks of the inherited OD training settings, without simulation."""
import unittest
import numpy as np
from src.rl.od_pricing_dqn import ODPricingDQN
class JointPilotTests(unittest.TestCase):
 def test_documented_warmup_update_epsilon_and_target(self):
  a=ODPricingDQN(42,master_math=True,utc_mode=True)
  s=np.zeros(13,np.float32);s[3]=1
  before=[x.copy() for x in a.online.get_weights()]
  for i in range(999):a.store(s,0,4,s,False,identity=('2026-03-12T04:00Z',i//142,i%142))
  self.assertIsNone(a.train_step());self.assertEqual(a.training_steps,0);self.assertEqual(a.epsilon,1)
  a.store(s,0,4,s,False,identity=('2026-03-12T04:00Z',7,5))
  old=a.target.get_weights();loss=a.train_step()
  self.assertTrue(np.isfinite(loss));self.assertEqual(a.training_steps,1)
  self.assertAlmostEqual(a.epsilon,1-.95/50000)
  self.assertTrue(any(not np.array_equal(x,y) for x,y in zip(before,a.online.get_weights())))
  for t,o,n in zip(a.target.get_weights(),old,a.online.get_weights()):np.testing.assert_allclose(t,(1-.005)*o+.005*n,atol=1e-7)
