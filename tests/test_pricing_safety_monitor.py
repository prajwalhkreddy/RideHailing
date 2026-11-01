import unittest
import numpy as np
from src.rl.pricing_dqn import PricingDQN
from src.simulation.pricing_safety_monitor import observe,learner_fingerprint,EPISODES
class MonitorTests(unittest.TestCase):
 def test_pure_monitor(self):
  d=PricingDQN();s=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
  for i in range(10):d.store(s,i%7,10.,s,bool(i%2))
  before=learner_fingerprint(d);v=observe(d,10,0.,dict(revenue=100.,assignments=10,action_counts=[1]*7))
  self.assertEqual(before,learner_fingerprint(d));self.assertEqual(v['terminal_N'],5);self.assertEqual(v['optimizer_updates'],0);self.assertEqual(EPISODES,{10,25,50,100})
  self.assertEqual(set(v['flags']),{'TERMINAL_CALIBRATION_CONCERN','Q_SCALE_CONCERN','BOOTSTRAP_DOMINANCE_CONCERN'})
if __name__=='__main__':unittest.main()
