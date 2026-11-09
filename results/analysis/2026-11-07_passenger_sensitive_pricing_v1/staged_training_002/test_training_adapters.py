import importlib.util,unittest
import numpy as np
p='results/analysis/2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/run_staged.py'
spec=importlib.util.spec_from_file_location('stage',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_monitor_preserves_actions(self):
  a=m.PassengerSensitiveDQN();b=m.PassengerSensitiveDQN();m.attach_monitor(b);s=np.zeros(13);s[3]=1;mask=np.array([True,True,False,False,False,False,False])
  for _ in range(20):self.assertEqual(a.select_action(s,mask),b.select_action(s,mask))
  self.assertEqual(m.fingerprint(a),m.fingerprint(b))
 def test_development_no_mutation(self):
  d=m.PassengerSensitiveDQN();before=m.fingerprint(d);v=m.EvaluationView(d);m.attach_monitor(v);s=np.zeros(13);s[3]=1;mask=np.ones(7,bool)
  v.select_action(s,mask,explore=False);v.store(s,0,1,s,True,np.zeros(7,bool),0)
  self.assertEqual(before,m.fingerprint(d))
 def test_mc(self):np.testing.assert_allclose(m.mc_returns([1,2,3],[1,.5,.99],[False,False,True]),[4.5,3.5,3])
class DiscountTests(unittest.TestCase):
 def test_stage4_not_authorized(self):
  with self.assertRaises(ValueError):m.main(4)
 def test_new_namespace(self):
  self.assertEqual(m.M.name,'staged_training_002')
 def test_request_mc(self):
  np.testing.assert_allclose(m.mc_returns([1,2,3],[.99]*3,[False,False,True]),[1+.99*2+.99**2*3,2+.99*3,3])
 def test_fresh_stage1_never_loads_checkpoint(self):
  import ast
  tree=ast.parse(m.Path(p).read_text())
  main=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
  branch=next(x for x in main.body if isinstance(x,ast.If) and ast.unparse(x.test)=='stage_number == 1')
  calls=[ast.unparse(x.func) for stmt in branch.body for x in ast.walk(stmt) if isinstance(x,ast.Call)]
  self.assertIn('PassengerSensitiveDQN',calls)
  self.assertNotIn('PassengerSensitiveDQN.load',calls)
unittest.main()
