import unittest
from datetime import datetime,timedelta
from types import SimpleNamespace
from scripts.handoff_v3_ep25 import validate_gate,KEYS,RESUME
from src.simulation.v3_stage3_protocol import timestamps,begin_episode,update_after_slot
class HandoffTests(unittest.TestCase):
 def records(self):
  s=dict(status='COMPLETED',pid=33413,episode=10,stage_slots_completed=144,stage_target_slots=144,latest_completed_episode=10,failure=None,timestamp='2026-03-04 08:00:00',latest_safe_checkpoint=str(RESUME))
  g={k:'PASS' for k in KEYS};g.update(MARCH17_31='UNTOUCHED',CONTINUE_TO_EPISODES_11_25='RECOMMENDED')
  m=dict(checkpoint_schema_version='V3_FULL_RUNTIME_1',checkpoint_status='COMPLETE',episode=10,slot=16,terminal=True,absolute_timestamp='2026-03-04 08:00:00',optimizer_updates=1224,replay_size=22720,exploration_epsilon=1-.95*1224/50000)
  return s,g,m,dict(checkpoint_status='COMPLETE')
 def test_gate_passes(self):validate_gate(*self.records())
 def test_gate_fail_closed(self):
  for mutate in [lambda s,g,m,c:s.update(status='RUNNING'),lambda s,g,m,c:s.update(failure='error'),lambda s,g,m,c:s.pop('failure'),lambda s,g,m,c:g.pop('CHECKPOINT_VALID'),lambda s,g,m,c:g.update(CONTINUE_TO_EPISODES_11_25='NOT_RECOMMENDED'),lambda s,g,m,c:m.update(slot=15),lambda s,g,m,c:c.update(checkpoint_status='WRITING'),lambda s,g,m,c:s.update(latest_safe_checkpoint=str(RESUME.parent/'episode_010_slot_015'))]:
   args=self.records();mutate(*args)
   with self.assertRaises(ValueError):validate_gate(*args)
 def test_exact_chronology(self):
  t=[t for e in range(11,26) for t in timestamps(e)]
  self.assertEqual(len(t),240);self.assertEqual(t[0],datetime(2026,3,4,8));self.assertEqual(t[-1],datetime(2026,3,9,7,30));self.assertTrue(all(b-a==timedelta(minutes=30) for a,b in zip(t,t[1:])))
  for e in [10,26]:
   with self.assertRaises(ValueError):timestamps(e)
 def test_no_runtime_reset(self):
  e=SimpleNamespace(timestamp=datetime(2026,3,4,8),clock=datetime(2026,3,4,8),slot_index=160)
  r=SimpleNamespace(episode=10,slots=16,checkpoint_phase='POST_SLOT_COMMIT',engine=e,learner=object(),provider=object(),dropoff=object(),audit=[1],slot_audit=[2],states=object())
  before=dict(vars(r));begin_episode(r,11)
  for k,v in before.items():
   if k not in ['episode','slots','checkpoint_phase']:self.assertIs(getattr(r,k),v)
  self.assertEqual(e.slot_index,160)
 def test_exact_update_cadence(self):
  l=SimpleNamespace(replay=[None]*22720,training_steps=1224)
  def step():l.training_steps+=1;return .1
  l.train_step=step
  r=SimpleNamespace(episode=11,slots=1,checkpoint_phase='POST_SLOT_COMMIT',learner=l,engine=SimpleNamespace(timestamp=datetime(2026,3,4,8,30)))
  self.assertEqual(len(update_after_slot(r)),8);self.assertEqual(l.training_steps,1232)
if __name__=='__main__':unittest.main()
