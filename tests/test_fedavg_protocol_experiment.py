"""Focused contract checks for the authorized B/C/D experiment."""
import unittest
import numpy as np
from scripts.experiment_fedavg_protocols import batch_positions,flat
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters,POLICY_ARCHITECTURE_VERSION
from src.routing.baseline import ACTION_ORDER
from src.routing.federated import aggregate_policy_updates
class ProtocolTests(unittest.TestCase):
 def test_deterministic_offsets_and_no_duplicates(self):
  p=np.arange(576);starts=[]
  for r in range(1,6):
   b=batch_positions(p,12,r,1);c=batch_positions(p,12,r,5);d=batch_positions(p,12,r,5)
   self.assertEqual(len(b),1);self.assertEqual(len(c),5);np.testing.assert_array_equal(b[0],c[0]);np.testing.assert_array_equal(np.concatenate(c),np.concatenate(d));self.assertEqual(len(np.unique(np.concatenate(c))),160);starts.append(int(b[0][0]))
  self.assertEqual(len(set(starts)),5)
 def test_small_clients_use_available_rows(self):
  for n in [0,1,17,31,32,33,129]:
   for cap in [1,5]:
    batches=batch_positions(np.arange(n),3,1,cap)
    self.assertEqual(len(batches),min(cap,int(np.ceil(n/32))))
    self.assertEqual(sum(map(len,batches)),min(n,cap*32))
 def test_streaming_matches_existing_sample_weighting(self):
  base=build_routing_policy_model(RoutingLearningParameters(),seed=42).get_weights();updates=[]
  for client,count in enumerate([0,19,211]):
   updates.append(dict(vehicle_id=client,sample_count=count,weights=[w+client*.001 for w in base],state_dimension=169,action_order=[a.value for a in ACTION_ORDER],architecture_version=POLICY_ARCHITECTURE_VERSION))
  result=aggregate_policy_updates(updates,round_index=0)
  for k,w in enumerate(result.weights):
   expected=(sum(u['weights'][k].astype(float)*u['sample_count'] for u in updates)/230).astype(np.float32);np.testing.assert_array_equal(w,expected)
  self.assertEqual(result.metadata.skipped_zero_sample_vehicle_ids,(0,))
 def test_seed_initialization_identical(self):
  a=build_routing_policy_model(RoutingLearningParameters(),seed=42);b=build_routing_policy_model(RoutingLearningParameters(),seed=42);np.testing.assert_array_equal(flat(a.get_weights()),flat(b.get_weights()))
if __name__=='__main__':unittest.main()
