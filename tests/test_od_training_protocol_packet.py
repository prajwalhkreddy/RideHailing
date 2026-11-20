"""Bounded proposal validation; no ML or simulation imports."""
import unittest,json,csv,math
from datetime import datetime,timedelta
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.build_od_training_protocol_packet import epsilon,old_epsilon
P=Path(__file__).resolve().parents[1]/'results_v2/pricing_dqn/2026-11-20_training_protocol_decision'
class ProtocolTests(unittest.TestCase):
 def setUp(self): self.c=json.loads((P/'proposed_configuration.json').read_text())
 def test_old_schedule_thresholds(self):
  for t,n in [(0.5,26316),(.2,42106),(.1,47369)]:
   self.assertLessEqual(old_epsilon(n),t); self.assertGreater(old_epsilon(n-1),t)
  self.assertAlmostEqual(old_epsilon(128),.997568)
 def test_proposed_schedule(self):
  for n,t in [(0,1),(9,1),(10,.995),(1000,.5),(1600,.2),(1800,.1),(4480,.1)]:self.assertAlmostEqual(epsilon(n),t)
  self.assertGreater(self.c['pricing']['minimum_replay_size'], self.c['pricing']['batch_size'])
 def test_exact_coverage(self):
  rows=list(csv.DictReader((P/'episode_plan.csv').read_text().splitlines()));self.assertEqual(len(rows),35)
  for i,r in enumerate(rows):
   a=datetime.fromisoformat(r['start_utc']);b=datetime.fromisoformat(r['end_exclusive_utc']);self.assertEqual(b-a,timedelta(hours=8));self.assertEqual(int(r['slots']),16)
   if i:self.assertEqual(rows[i-1]['end_exclusive_utc'],r['start_utc'])
  self.assertEqual(rows[-1]['end_exclusive_local'],'2026-03-12T17:00:00-04:00')
 def test_dst(self):
  from zoneinfo import ZoneInfo
  a=datetime.fromisoformat(self.c['training']['start']);xs=[(a+timedelta(minutes=30*i)).astimezone(ZoneInfo('America/New_York')) for i in range(560)]
  self.assertEqual(sum(x.date().isoformat()=='2026-03-08' for x in xs),46)
  self.assertFalse(any(x.date().isoformat()=='2026-03-08' and x.hour==2 for x in xs))
 def test_eval_isolation(self):
  e=self.c['evaluation'];self.assertEqual(e['epsilon'],0);self.assertFalse(e['pricing_updates']);self.assertFalse(e['routing_updates']);self.assertFalse(e['protected_access'])
  for r in csv.DictReader((P/'evaluation_windows.csv').read_text().splitlines()):
   self.assertGreaterEqual(r['start_local'][:10],'2026-03-13');self.assertLessEqual(r['end_exclusive_local'][:10],'2026-03-17')
   self.assertLess(r['start_local'][:10],'2026-03-17')
 def test_replay(self):
  r=json.loads((P/'replay_analysis.json').read_text());self.assertEqual(16*9572,153152);self.assertEqual(10*9572+4280,100000);self.assertLessEqual(r['zero_reward_retained'],r['retained']);self.assertEqual(self.c['pricing']['minimum_replay_size'],1000)
 def test_checkpoint(self):
  s=self.c['storage'];self.assertEqual(s['max_retained_resumable'],3);self.assertEqual(len(s['roles']),3);self.assertTrue(s['atomic']);self.assertLessEqual((3+1)*s['max_checkpoint_GiB'],s['max_run_GiB'])
 def test_not_launchable(self):
  self.assertFalse(self.c['launch_authorized']);self.assertEqual(self.c['status'],'PROPOSED_REQUIRES_APPROVAL');self.assertFalse(self.c['forecast']['cnn_enabled']);self.assertEqual(self.c['routing']['aggregation'],'EQUAL_PARTICIPATING_CLIENT_V1')
if __name__=='__main__':unittest.main()
