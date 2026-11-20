"""Research-only generator initialization; historical capture remains unchanged."""
import json,os,subprocess,sys,unittest
import numpy as np,tensorflow as tf
from scripts.validate_online_routing_experiment import initialize_experiment_rng,rng_domains
from src.simulation.v3_checkpoint import rng_bundle,restore_rng
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters
class ExperimentRNGTests(unittest.TestCase):
 def test_capture_pure_and_restore(self):
  initialize_experiment_rng(42);before=rng_domains();saved=rng_bundle()
  self.assertEqual(before,rng_domains())
  tf.random.get_global_generator().uniform([5]);self.assertNotEqual(before,rng_domains())
  restore_rng(saved);self.assertEqual(before,rng_domains())
 def test_model_identity_preserved(self):
  a=build_routing_policy_model(RoutingLearningParameters(),seed=42).get_weights()
  initialize_experiment_rng(42)
  b=build_routing_policy_model(RoutingLearningParameters(),seed=42).get_weights()
  for x,y in zip(a,b):np.testing.assert_array_equal(x,y)
 def test_owned_numpy_stream_unchanged(self):
  stream=np.random.default_rng(43);before=json.dumps(stream.bit_generator.state)
  initialize_experiment_rng(42)
  self.assertEqual(before,json.dumps(stream.bit_generator.state))
 def test_independent_process_initialization_and_slot_boundary(self):
  code="""
import json,numpy as np,pandas as pd
from pathlib import Path
from scripts.validate_online_routing_experiment import initialize_experiment_rng,rng_domains,hash_value
from src.routing.online_provenance import OnlineHierarchy
from src.routing.learning import LocalPolicyObservation
from src.fleet.research_mixed import configure
from tests.test_research_hierarchy import fleet
initialize_experiment_rng(42)
a={'initialized':rng_domains()}
c=json.loads(Path('results_v2/federated_learning/2026-11-17_online_routing_retry_001/routing_initialization.json').read_text())
h=OnlineHierarchy(c);a['model']=rng_domains();a['weights']=hash_value(h._global.get_weights())
f=fleet(10);configure(f,.1,42);a['fleet']=rng_domains()
t=pd.Timestamp(c['experiment_start']);o=LocalPolicyObservation(np.ones(169,dtype=np.float32),0,np.ones(9,dtype=bool),slot_id=0)
h.record(0,o,event_time=t);a['before_slot']=rng_domains();h.finish_slot(t,t+pd.Timedelta(minutes=30));a['after_slot']=rng_domains()
print(json.dumps(a,sort_keys=True))
"""
  env=dict(os.environ,TF_CPP_MIN_LOG_LEVEL='3')
  a=subprocess.check_output([sys.executable,'-B','-c',code],env=env,text=True)
  b=subprocess.check_output([sys.executable,'-B','-c',code],env=env,text=True)
  self.assertEqual(json.loads(a),json.loads(b))
