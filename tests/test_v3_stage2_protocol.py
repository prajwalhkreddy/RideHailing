import unittest
from datetime import datetime,timedelta
from types import SimpleNamespace
from src.simulation.v3_stage2_protocol import timestamps,begin_episode,update_after_slot
class Stage2Tests(unittest.TestCase):
 def test_chronology(self):
  ts=[t for e in range(2,11) for t in timestamps(e)]
  self.assertEqual(len(ts),144);self.assertEqual(ts[0],datetime(2026,3,1,8));self.assertEqual(ts[-1],datetime(2026,3,4,7,30))
  self.assertTrue(all(b-a==timedelta(minutes=30) for a,b in zip(ts,ts[1:])))
  with self.assertRaises(ValueError):timestamps(11)
 def test_boundary_only_metadata(self):
  r=SimpleNamespace(episode=1,slots=16,checkpoint_phase='POST_SLOT_COMMIT',engine=SimpleNamespace(timestamp=datetime(2026,3,1,8),clock=datetime(2026,3,1,8),slot_index=16),learner=object(),states=object(),audit=[1],slot_audit=[2],provider=object(),dropoff=object())
  before=dict(vars(r));begin_episode(r,2)
  self.assertEqual(r.slots,0);self.assertEqual(r.episode,2)
  for k,v in before.items():
   if k not in ('episode','slots','checkpoint_phase'):self.assertIs(getattr(r,k),v)
 def test_updates(self):
  learner=SimpleNamespace(replay=[None]*2272,training_steps=72)
  def step():learner.training_steps+=1;return 1.
  learner.train_step=step
  r=SimpleNamespace(episode=2,slots=1,checkpoint_phase='POST_SLOT_COMMIT',engine=SimpleNamespace(timestamp=datetime(2026,3,1,8,30)),learner=learner)
  self.assertEqual(len(update_after_slot(r)),8);self.assertEqual(learner.training_steps,80)
  learner.replay=[];self.assertEqual(update_after_slot(r),[])
 def test_bad_boundary(self):
  r=SimpleNamespace(episode=1,slots=15,checkpoint_phase='POST_SLOT_COMMIT')
  with self.assertRaises(ValueError):begin_episode(r,2)
if __name__=='__main__':unittest.main()
