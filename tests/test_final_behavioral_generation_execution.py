import unittest,tempfile,fcntl,pickle
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from src.simulation import routing_experience_generation as g
from tests.test_routing_generation_execution import Fake

class FinalBehavioralExecutionTests(unittest.TestCase):
 def test_second_writer_preserves_pid(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'data/processed/routing_experiences_mar01_mar15_2026_final_behavioral';p.mkdir(parents=True);(p/'generation.pid').write_text('12345\n')
   with (p/'generation.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaisesRegex(RuntimeError,'Another generation'):g.generate(d,final_behavioral=True)
   self.assertEqual((p/'generation.pid').read_text(),'12345\n')
 def test_no_implicit_resume(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'data/processed/routing_experiences_mar01_mar15_2026_final_behavioral';p.mkdir(parents=True);(p/'generation_checkpoint.pkl').write_bytes(b'old')
   with self.assertRaisesRegex(ValueError,'explicit resume'):g.generate(d,final_behavioral=True)
   self.assertEqual((p/'generation_checkpoint.pkl').read_bytes(),b'old')
 def test_validation_cap(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'two clean slots'):g.generate(d,final_behavioral=True,validation_only=True,stop_after_slot=3)
 def test_checkpoint_contract_rejects_old(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'cp';p.write_bytes(pickle.dumps(dict(reachability_contract='EV_POST_MOVEMENT_STATION_REACHABILITY')))
   x=SimpleNamespace(behavioral_contract_identity={'sampler':'new'})
   with self.assertRaisesRegex(ValueError,'contract mismatch'):g.RoutingExperienceExperiment.restore(x,p)
 def test_safe_term_checkpoint(self):
  import signal
  x=Fake();run=x.run_slot
  def stop_after_one(**kw):
   r=run(**kw);signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None);return r
  x.run_slot=stop_after_one
  with tempfile.TemporaryDirectory() as d,patch.object(g,'RoutingExperienceExperiment',return_value=x):
   g.generate(d,stop_after_slot=8);self.assertEqual(x.saved,[0,1]);self.assertEqual(x.slot_index,1)
