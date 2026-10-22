import unittest,tempfile,json
from pathlib import Path
import numpy as np
from src.rl.pricing_dqn import *

def state():return np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
def agent():return PricingDQN(DQNConfig(batch_size=2,minimum_replay_size=2,replay_capacity=10))
class DQNTests(unittest.TestCase):
 def test_network(self):
  a=agent();self.assertEqual(a.online.input_shape,(None,13));self.assertEqual(a.online.output_shape,(None,7))
  self.assertEqual(a.online.layers[-1].activation.__name__,'linear')
  for x,y in zip(a.online.get_weights(),a.target.get_weights()):np.testing.assert_array_equal(x,y)
 def test_mapping_and_ties(self):
  a=agent();self.assertEqual(ACTIONS,(.85,.90,.95,1.,1.05,1.10,1.15))
  a.online.set_weights([np.zeros_like(w) for w in a.online.get_weights()]);self.assertEqual(a.select_action(state(),explore=False).action_index,0)
  w=a.online.get_weights();w[-1][4]=10;a.online.set_weights(w)
  self.assertEqual(a.select_action(state(),explore=False).pricing_factor,1.05)
  b=agent();draws=[b.select_action(state()).action_index for _ in range(70)];self.assertEqual(set(draws),set(range(7)))
  c=agent();self.assertEqual(draws,[c.select_action(state()).action_index for _ in range(70)])
 def test_schedule(self):
  a=agent()
  for step,expected in [(0,1),(25000,.525),(50000,.05),(60000,.05)]:
   a.training_steps=step;self.assertAlmostEqual(a.epsilon,expected)
 def test_replay_validation(self):
  b=ReplayBuffer(3,42)
  for action in [-1,7,1.5,True]:
   with self.assertRaises(ValueError):b.add(state(),action,1,state(),False)
  with self.assertRaises(ValueError):b.add(state(),0,float('nan'),state(),False)
  with self.assertRaises(ValueError):b.add(state(),0,1,state(),1)
  for bad in [np.zeros(12),np.zeros(13),np.full(13,np.nan)]:
   with self.assertRaises(ValueError):b.add(bad,0,1,state(),False)
  for i in range(5):b.add(state(),i,1,state(),False)
  self.assertEqual(len(b),3)
 def test_replay_determinism_and_copy(self):
  a=ReplayBuffer(10,42);b=ReplayBuffer(10,42)
  for i in range(7):a.add(state(),i,i,state(),False);b.add(state(),i,i,state(),False)
  for x,y in zip(a.sample(4),b.sample(4)):np.testing.assert_array_equal(x,y)
  s=state();a.add(s,0,1,s,False);s[0]=100;self.assertEqual(a.items[-1][0][0],1)
 def test_bellman(self):
  q=np.tile(np.arange(7),(2,1));np.testing.assert_allclose(bellman_targets([10,10],[False,True],q,.99),[15.94,10])
 def test_soft_update(self):
  a=agent();a.online.set_weights([np.full_like(w,4) for w in a.online.get_weights()]);a.target.set_weights([np.full_like(w,2) for w in a.target.get_weights()]);soft_update(a.online,a.target,.005)
  for w in a.target.get_weights():np.testing.assert_allclose(w,2.01)
 def test_optimizer_target_and_warmup(self):
  a=agent();self.assertIsNone(a.train_step());a.store(state(),0,10,state(),True);a.store(state(),1,20,state(),False)
  oldtarget=[w.copy() for w in a.target.get_weights()];oldonline=[w.copy() for w in a.online.get_weights()]
  result=a.train_step();self.assertTrue(np.isfinite(result['loss']));self.assertEqual(a.training_steps,1)
  self.assertTrue(any(not np.array_equal(x,y) for x,y in zip(oldonline,a.online.get_weights())))
  for old,new,target in zip(oldtarget,a.online.get_weights(),a.target.get_weights()):np.testing.assert_allclose(target,.995*old+.005*new,atol=1e-7)
 def test_target_not_online_bellman(self):
  a=agent();a.target.set_weights([np.zeros_like(w) for w in a.target.get_weights()]);w=a.target.get_weights();w[-1]=np.arange(7,dtype=np.float32);a.target.set_weights(w)
  for _ in range(2):a.store(state(),0,10,state(),False)
  self.assertAlmostEqual(a.train_step()['mean_target'],15.94,places=5)
 def test_checkpoint_exact_resume(self):
  a=agent()
  for i in range(7):a.store(state(),i,i,state(),i%2==0)
  a.train_step()
  with tempfile.TemporaryDirectory() as d:
   a.save(d);b=PricingDQN.load(d)
   for x,y in zip(a.online.optimizer.variables,b.online.optimizer.variables):np.testing.assert_array_equal(x.numpy(),y.numpy())
   self.assertEqual(a.select_action(state()),b.select_action(state()))
   da,db=a.train_step(),b.train_step();self.assertEqual(da,db)
   for x,y in zip(a.online.get_weights(),b.online.get_weights()):np.testing.assert_array_equal(x,y)
   for x,y in zip(a.target.get_weights(),b.target.get_weights()):np.testing.assert_array_equal(x,y)
   p=Path(d)/'checkpoint.json';m=json.loads(p.read_text());m['actions'][0]=.8;p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):PricingDQN.load(d)
 def test_reward_interface(self):
  from src.pricing.dqn_contract import DispatchLedger,DispatchOutcome
  import pandas as pd
  start=pd.Timestamp('2026-03-16');l=DispatchLedger()
  events=[DispatchOutcome(i,0,start,True,True,fare) for i,fare in enumerate([20,25,30])]
  events.extend([DispatchOutcome(3,0,start,True,False,100),DispatchOutcome(4,0,start,False,False,100)])
  reward=l.complete_slot(start,start+pd.Timedelta(minutes=30),events);self.assertEqual(reward,75)
  a=agent();a.store(state(),3,reward,state(),True);self.assertEqual(a.replay.items[0][2],75)
if __name__=='__main__':unittest.main()
