"""Quick spatial migration regression suite, excluding training-bearing tests."""
import sys, unittest, inspect, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import os
os.chdir(ROOT)
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
modules=['test_active_3km_foundation','test_metric_grid','test_grid','test_spatial_mapping','test_artifacts','test_config','test_grid_policy','test_destination_popularity','test_energy','test_fleet_state','test_routing_baseline','test_routing_learning','test_routing_federated','test_routing_production']
suite=unittest.TestSuite();skipped=[]
def flatten(s):
 for t in s:
  if isinstance(t,unittest.TestSuite):yield from flatten(t)
  else:yield t
for name in modules:
 for test in flatten(unittest.defaultTestLoader.loadTestsFromName(name)):
  method=getattr(test,test._testMethodName)
  if 'train_for_slot' in inspect.getsource(method):skipped.append(test.id())
  else:suite.addTest(test)
r=unittest.TextTestRunner(verbosity=2).run(suite)
Path('results/analysis/2026-10-19_true_3km_grid_activation/test_results.json').write_text(json.dumps({'run':r.testsRun,'failures':[(t.id(),s) for t,s in r.failures],'errors':[(t.id(),s) for t,s in r.errors],'training_tests_not_run':skipped},indent=2))
sys.exit(not r.wasSuccessful())
