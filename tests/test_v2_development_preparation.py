"""No-learning development preparation contracts."""
import importlib.util,unittest,copy
from pathlib import Path
import numpy as np
p=Path('results/training/pricing_v2_staged_training_001/prepare_development.py')
s=importlib.util.spec_from_file_location('v2_development',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class DevelopmentTests(unittest.TestCase):
 def state(self):return np.array([0,0,0]+[1/9]*9+[0],dtype=np.float32)
 def test_baseline_actions(self):
  mask=np.array([True,True,True,False,False,False,False])
  for policy,expected in [('HIGHEST_FEASIBLE',2),('LOWEST_FEASIBLE',0),('NEUTRAL_1_00_WITH_EXISTING_FALLBACK',2)]:
   d=m.EvaluationPolicy(policy);self.assertEqual(d.select_action(self.state(),mask).action_index,expected);self.assertEqual(d.training_steps,0)
 def test_no_learning(self):
  d=m.EvaluationPolicy('HIGHEST_FEASIBLE')
  with self.assertRaises(RuntimeError):d.train_step()
  with self.assertRaises(RuntimeError):d.complete_slot(None)
  with self.assertRaises(ValueError):d.select_action(self.state(),np.ones(7,bool),explore=True)
 def test_empty_mask(self):
  with self.assertRaises(ValueError):m.EvaluationPolicy('HIGHEST_FEASIBLE').select_action(self.state(),np.zeros(7,bool))
 def test_fixture_slot_count(self):
  with self.assertRaises(ValueError):m.validate_requests([])
 def test_clone_isolation(self):
  initial=[{'vehicle_id':1,'energy_level':60}];clone=copy.deepcopy(initial);clone[0]['energy_level']=0
  self.assertEqual(initial[0]['energy_level'],60);self.assertNotEqual(m.digest(initial),m.digest(clone))

 def test_zero_distance_matches_runtime_contract(self):
  from src.dispatch.request import RequestState
  import pandas as pd
  t=pd.Timestamp('2026-01-01')
  req=RequestState(0,0,0,0,base_fare=1.,source_trip_id=0,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=1)).to_pydatetime(),trip_duration_minutes=1.,trip_distance_miles=0.,trip_distance_km=0.)
  slots=[[req]]+[[] for _ in range(47)]
  self.assertEqual(m.validate_requests(slots),1)
  req.trip_distance_km=-1
  with self.assertRaises(ValueError):m.validate_requests(slots)
