"""Reporting-only recovery against the existing completed episode checkpoint."""
import unittest,tempfile,json,pickle,hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import pandas as pd
import src.simulation.multiepisode_pricing as m
CP=m.FINAL/'episode_0001/checkpoint_0016_1944f2bd'
def signature(d):
 return (m.weights_hash(d.online),m.weights_hash(d.target),hashlib.sha256(pickle.dumps([v.numpy() for v in d.online.optimizer.variables])).hexdigest(),hashlib.sha256(pickle.dumps(list(d.replay.items))).hexdigest(),json.dumps(d.replay.rng.bit_generator.state,sort_keys=True),json.dumps(d.rng.bit_generator.state,sort_keys=True),d.training_steps,d.epsilon)
class RecoveryTests(unittest.TestCase):
 def test_optional_metric(self):
  self.assertEqual(m.reserve_reposition_count(SimpleNamespace()),0)
  self.assertEqual(m.reserve_reposition_count(SimpleNamespace(reserve_reposition_rejections=7)),7)
 def test_completed_checkpoint_no_replay(self):
  meta=json.loads((CP/'manifest.json').read_text())
  for f,h in meta['files'].items():self.assertEqual(m.sha(CP/f),h)
  d=m.PricingDQN.load(CP/'dqn');before=signature(d)
  self.assertEqual((len(d.replay),d.training_steps,d.epsilon),(7662,120,.99772))
  state=pickle.loads((CP/'simulator.pkl').read_bytes());self.assertEqual(state['slot_index'],16);self.assertEqual(len(state['reports']),16)
  for key in ['request_rng','customer_rng','python_rng','numpy_rng']:self.assertIn(key,state)
  calls=[]
  class EpisodeTwoReached(Exception):pass
  def reset(spec,learner):
   calls.append(spec['episode'])
   if spec['episode']==2:
    self.assertEqual(signature(learner),before);raise EpisodeTwoReached()
   return SimpleNamespace(request_rng=np.random.default_rng(),customer=SimpleNamespace(rng=np.random.default_rng()),routing=SimpleNamespace())
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);ns=root/'models';ep=ns/'episode_0001';ep.mkdir(parents=True)
   (ep/CP.name).symlink_to(CP,target_is_directory=True)
   (ep/'CURRENT.json').write_text(json.dumps(dict(directory=CP.name,manifest_sha256=m.sha(CP/'manifest.json'))))
   with patch.object(m,'FINAL',ns),patch.object(m,'RUN_OUT',root/'report'),patch.object(m,'reset',reset),patch.object(m,'slot',side_effect=AssertionError('Completed episode replayed')),patch.object(m,'checkpoint',return_value=str(CP)):
    with self.assertRaises(EpisodeTwoReached):m.run_final(resume=True)
   rows=pd.read_csv(ns/'episode_metrics.csv');self.assertEqual(rows.episode.tolist(),[1]);self.assertEqual(rows.replay_insertions.tolist(),[7662]);self.assertEqual(rows.optimizer_updates.tolist(),[120]);self.assertAlmostEqual(rows.revenue.iloc[0],sum(r['reward'] for r in state['reports']))
   self.assertEqual(json.loads((ns/'protocol_cursor.json').read_text())['episode_index'],1)
   self.assertEqual(calls,[1,2])
if __name__=='__main__':unittest.main()
