"""Execution-only comparison: same sequential updates and random samples."""
import tempfile,unittest
import numpy as np
from src.rl.pricing_dqn import PricingDQN
class CompiledExecutionTests(unittest.TestCase):
 def test_eight_sequential_updates(self):
  a=PricingDQN();s=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
  for i in range(1000):a.store(s,i%7,float(i%3),s,bool(i%2))
  with tempfile.TemporaryDirectory() as d:
   a.save(d);b=PricingDQN.load(d);b.enable_compiled_updates()
   for _ in range(8):
    a.train_step();b.compiled_train_step()
    self.assertEqual(a.replay.rng.bit_generator.state,b.replay.rng.bit_generator.state)
    self.assertEqual(a.training_steps,b.training_steps);self.assertEqual(a.epsilon,b.epsilon)
    for x,y in zip(a.online.get_weights()+a.target.get_weights(),b.online.get_weights()+b.target.get_weights()):np.testing.assert_allclose(x,y,rtol=1e-5,atol=1e-5)
   self.assertEqual(int(b.online.optimizer.iterations),8)
   for _ in range(30):self.assertEqual(a.select_action(s),b.select_action(s))
if __name__=='__main__':unittest.main()
