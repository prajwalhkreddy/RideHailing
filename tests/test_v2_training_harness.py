"""Mock-only scheduling and value tests: no optimizer execution."""
import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
P=Path('results/training/pricing_v2_staged_training_001')
sys.path.insert(0,str(P.resolve()))
import training_harness as h
class HarnessTests(unittest.TestCase):
 def test_schedule(self):
  episodes=[];checkpoints=[];evaluations=[];statuses=[]
  h.schedule(episodes.append,checkpoints.append,evaluations.append,lambda *a:statuses.append(a))
  self.assertEqual(episodes,list(range(1,26)));self.assertEqual(checkpoints,[1,5,10,15,20,25]);self.assertEqual(evaluations,checkpoints);self.assertEqual(statuses[-1][0],'COMPLETED')
 def test_hard_stop(self):
  visited=[];statuses=[]
  def step(e):
   visited.append(e)
   if e==3:raise ValueError('synthetic invariant')
  with self.assertRaisesRegex(ValueError,'synthetic invariant'):h.schedule(step,lambda e:None,lambda e:None,lambda *a:statuses.append(a))
  self.assertEqual(visited,[1,2,3]);self.assertEqual(statuses[-1][0],'FAILED_HARD_INVARIANT');self.assertIn('synthetic invariant',statuses[-1][2]['traceback'])
 def test_dates(self):
  h.validate_episode({'start':'2026-03-15 16:00'})
  for t in ['2026-03-15 16:30','2026-03-16','2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):h.validate_episode({'start':t})
 def test_mc_per_request(self):
  np.testing.assert_allclose(h.mc_returns([1,2,3]),[1+.99*2+.99**2*3,2+.99*3,3])
  with self.assertRaises(ValueError):h.mc_returns([float('nan')])
 def test_no_episode26(self):self.assertEqual(h.CHECKPOINTS[-1],25)
 def test_evaluation_fingerprint_guard(self):
  from unittest.mock import patch
  with patch.object(h,'fingerprint',side_effect=['same','same']):self.assertEqual(h.guarded_evaluation(object(),lambda:42),42)
  with patch.object(h,'fingerprint',side_effect=['before','after']):
   with self.assertRaisesRegex(ValueError,'mutated'):h.guarded_evaluation(object(),lambda:42)
 def test_continuation_identity(self):
  m=dict(methodology_version='V2',sensitivity_version='v2',episode=5,next_episode=6,update=640,config_sha256='c',fixture_manifest_sha256='f',support_sha256='s')
  h.validate_continuation(m,'c','f','s')
  for key in ['sensitivity_version','support_sha256','config_sha256','fixture_manifest_sha256']:
   bad=dict(m);bad[key]='wrong'
   with self.assertRaises(ValueError):h.validate_continuation(bad,'c','f','s')
  with self.assertRaisesRegex(ValueError,'Missing'):h.validate_continuation({},'c','f','s')

 def test_weather_conditioning_blocks_before_fixture_or_training(self):
  from unittest.mock import patch
  import json
  with patch.object(Path,'read_text',return_value=json.dumps({'verdict':'V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_NOT_READY'})), patch.object(h,'load_fixture') as fixture, patch.object(h,'provider') as provider:
   with self.assertRaisesRegex(ValueError,'V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_NOT_READY'):h.run()
   fixture.assert_not_called();provider.assert_not_called()
