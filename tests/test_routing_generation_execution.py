import unittest,tempfile,pickle
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,pandas as pd
from src.simulation import routing_experience_generation as g
class Fake:
 def __init__(self):
  self.slot_index=0;self.timestamp=pd.Timestamp('2026-03-01');self.experience_id=0;self.pending=[];self.reports=[];self.charging_events=[];self.fleet=SimpleNamespace(vehicles=list(range(5000)));self.dqn=SimpleNamespace(replay=[],training_steps=0);self.saved=[]
  self.reserve_assignment_rejections=0;self.reserve_rejected_request_ids=set();self.routing=SimpleNamespace(reserve_reposition_rejections=0)
 def checkpoint(self,p):self.saved.append(self.slot_index);p.write_bytes(pickle.dumps({'slot':self.slot_index}))
 def run_slot(self,**kw):
  i=self.slot_index;t=self.timestamp
  self.pending=[dict(experience_id=i,driver_id=0,timestamp=t,current_grid=0,state_169=[0.]*169,action_mask_9=[True]*9,label_action_0_to_8=0,decision_type='REPOSITION',event_offset_minutes=0.)]
  self.slot_index+=1;self.timestamp+=pd.Timedelta(minutes=30);self.experience_id+=1
  r=dict(timestamp=str(t),requests=1,accepted=1,rejected=0,assigned=1,unmatched=0,charging_decisions=0,fleet_size=5000);self.reports.append(r);return r
class Tests(unittest.TestCase):
 def test_interval_and_final(self):
  x=Fake()
  with tempfile.TemporaryDirectory() as d,patch.object(g,'RoutingExperienceExperiment',return_value=x):
   g.generate(d,stop_after_slot=17);self.assertEqual(x.saved,[0,8,16,17]);self.assertEqual(len(list((Path(d)/'data/processed/routing_experiences_mar01_mar15_2026_reachability').glob('slot_*.parquet'))),17)
 def test_day_boundary(self):
  x=Fake();x.timestamp=pd.Timestamp('2026-03-01 23:30')
  with tempfile.TemporaryDirectory() as d,patch.object(g,'RoutingExperienceExperiment',return_value=x):
   g.generate(d,stop_after_slot=3);self.assertEqual(x.saved,[0,1,3])
 def test_resume_required(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(FileNotFoundError):g.generate(d,resume=True)
 def test_single_writer_lock(self):
  import fcntl
  with tempfile.TemporaryDirectory() as d:
   data=Path(d)/'data/processed/routing_experiences_mar01_mar15_2026_reachability';data.mkdir(parents=True)
   with (data/'generation.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaisesRegex(RuntimeError,'Another generation'):g.generate(d)
 def test_different_uncommitted_partition_fails_closed(self):
  import json
  x=Fake()
  with tempfile.TemporaryDirectory() as d,patch.object(g,'RoutingExperienceExperiment',return_value=x):
   data=Path(d)/'data/processed/routing_experiences_mar01_mar15_2026_reachability';data.mkdir(parents=True)
   g.pq.write_table(g.pa.Table.from_pylist([],schema=g.SCHEMA),data/'slot_0000.parquet')
   with self.assertRaisesRegex(ValueError,'differs on replay'):g.generate(d,stop_after_slot=1)
   status=json.loads((Path(d)/'results/analysis/2026-10-25_routing_generation_reachability/generation_status.json').read_text())
   self.assertEqual(status['completed_slots'],0);self.assertEqual(x.saved,[0])
if __name__=='__main__':unittest.main()
