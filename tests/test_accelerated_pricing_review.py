import unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from src.simulation import accelerated_pricing_review as r
from src.rl.pricing_dqn import PricingDQN
class ReviewTests(unittest.TestCase):
 def test_fresh_and_128_updates(self):
  a=PricingDQN();b=PricingDQN();self.assertEqual(r.fingerprint(a),r.fingerprint(b));self.assertEqual(a.epsilon,1);self.assertEqual(len(a.replay),0)
  self.assertEqual(r.base.weights_hash(a.online),r.base.weights_hash(a.target))
  s=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
  self.assertEqual(r.update_slot(a,'2026-03-01'),[])
  for i in range(1000):a.store(s,i%7,i%3,s,bool(i%2))
  calls=[];original=a.replay.sample
  def sample(n):calls.append(n);return original(n)
  a.replay.sample=sample
  self.assertEqual(len(r.update_slot(a,'2026-03-01')),128);self.assertEqual(calls,[64]*128)
  self.assertEqual(a.training_steps,128);self.assertEqual(int(a.online.optimizer.iterations),128)
  for k in [0,49999,50000,50001]:
   a.training_steps=k;self.assertAlmostEqual(a.epsilon,1-.95*min(k/50000,1))
  for t in ['2026-03-16','2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):r.update_slot(a,t)
 def test_development_no_mutation(self):
  d=PricingDQN();before=r.fingerprint(d);s=np.array([1,0,0,1,0,0,0,0,0,0,0,0,.5],np.float32)
  x=SimpleNamespace(timestamp='2026-03-16',current_states=SimpleNamespace(build=lambda *args:s))
  calls=[]
  def slot(x,terminal,development):
   self.assertTrue(development);d.select_action(s,explore=False);calls.append(terminal)
  with patch.object(r.base,'ProductionExperiment',return_value=x),patch.object(r,'checked_slot',side_effect=slot),patch.object(r,'metrics',return_value={'revenue':0}):
   r.evaluate(d,0,[]);self.assertEqual(calls,[False,False,False,True]);self.assertEqual(r.fingerprint(d),before)
 def test_duplicate_writer_does_not_replace_pid(self):
  with tempfile.TemporaryDirectory() as tmp:
   ns=Path(tmp);p=ns/'process.json';p.write_text('preserved')
   lock=r.base.lock_writer(ns)
   try:
    with patch.object(r,'MODEL',ns):
     with self.assertRaises(RuntimeError):r.run()
    self.assertEqual(p.read_text(),'preserved')
   finally:lock.close()
 def test_development_protected_guard_before_reads(self):
  for date in ['2026-03-17','2026-03-31']:
   x=SimpleNamespace(timestamp=date)
   with self.assertRaises(ValueError):r.checked_slot(x,False,True)
if __name__=='__main__':unittest.main()
