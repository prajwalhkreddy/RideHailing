import unittest,json
from pathlib import Path
from unittest.mock import patch
import numpy as np,pandas as pd
from src.routing.online_provenance import OnlineHierarchy
from src.routing.learning import LocalPolicyObservation
from tests.test_online_routing_provenance import synthetic_update
class MultiFederationTests(unittest.TestCase):
 def test_equal_clients_and_future_rejection(self):
  c=json.loads(Path('results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration/routing_initialization.json').read_text())
  h=OnlineHierarchy(c,updates_enabled=True);start=pd.Timestamp(c['experiment_start']);end=start+pd.Timedelta(minutes=30)
  before=h._global.get_weights()
  for d in (0,1):h.record(d,LocalPolicyObservation(np.ones(169,np.float32),0,np.ones(9,bool),slot_id=0),event_time=end)
  with self.assertRaises(ValueError):h.record(3,LocalPolicyObservation(np.ones(169,np.float32),0,np.ones(9,bool),slot_id=0),event_time=end+pd.Timedelta(seconds=1))
  with patch('src.routing.learning.LocalRoutingLearner.train_for_slot',synthetic_update):h.finish_slot(start,end)
  for old,new in zip(before,h._global.get_weights()):np.testing.assert_allclose(new,old+1.5,rtol=0,atol=2e-7)
  self.assertEqual(h.global_version,1);self.assertEqual(h.available_at,end)
  restored=OnlineHierarchy.restore(h.snapshot())
  for a,b in zip(restored._global.get_weights(),h._global.get_weights()):np.testing.assert_array_equal(a,b)
if __name__=='__main__':unittest.main()
