"""Reporting-only checks; no simulator/model imports."""
import unittest,json,hashlib
from pathlib import Path
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];V=R/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3';O=V/'review_ep01_ep10'
class ReportingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=pd.read_csv(O/'episode_summary.csv');cls.a=pd.read_csv(O/'action_summary.csv');cls.summary=json.loads((O/'review_summary.json').read_text())
 def test_exact_scope(self):self.assertEqual(self.e.episode.tolist(),list(range(1,11)));self.assertEqual(self.e.end_timestamp.iloc[-1],'2026-03-04 07:30:00')
 def test_totals(self):
  for k in ['requests','accepted','rejected','assignments','accepted_unmatched']:self.assertEqual(int(self.e[k].sum()),self.summary['totals'][k])
  self.assertEqual(self.e.requests.sum(),293819);self.assertEqual(self.e[self.e.episode>1].requests.sum(),269726)
 def test_funnel(self):
  self.assertTrue((self.e.requests==self.e.accepted+self.e.rejected).all());self.assertTrue((self.e.accepted==self.e.assignments+self.e.accepted_unmatched).all())
 def test_actions(self):
  c=json.loads((V/'methodology_contract.json').read_text());np.testing.assert_allclose(self.a.factor,c['actions'],rtol=0,atol=1e-15)
  self.assertEqual(self.a.contexts_selected.sum(),22720);self.assertEqual(self.a.requests_exposed.sum(),self.e.requests.sum());self.assertEqual(self.a.accepted.sum(),self.e.accepted.sum())
 def test_reward(self):self.assertAlmostEqual(self.a.accepted_revenue.sum(),self.e.accepted_revenue.sum(),places=7)
 def test_optimizer_replay(self):
  self.assertEqual(self.e.optimizer_updates_episode.tolist(),[72]+[128]*9);self.assertEqual(self.e.replay_size_end.tolist(),[2272*i for i in range(1,11)]);np.testing.assert_allclose(self.e.epsilon_end,1-.95*self.e.optimizer_updates_end/50000,rtol=0,atol=2e-16)
 def test_chart_hashes(self):
  charts=json.loads((O/'chart_manifest.json').read_text());self.assertGreaterEqual(len(charts),17)
  for c in charts:
   self.assertEqual(c['episode_range'],'1–10')
   for ext in ['png','pdf']:self.assertEqual(hashlib.sha256((R/c[ext+'_file']).read_bytes()).hexdigest(),c['SHA256_'+ext])
 def test_documentation_consistency(self):
  d=json.loads((O/'documentation_consistency_check.json').read_text());self.assertEqual(d['status'],'PASS')
  blocks=[]
  for p in d['paths']:blocks.append((R/p).read_text().split('<!-- V3_REVIEW_CURRENT_BEGIN -->')[1].split('<!-- V3_REVIEW_CURRENT_END -->')[0])
  self.assertEqual(len(set(blocks)),1)
 def test_unavailable_not_fabricated(self):
  for k in ['mean_abs_Q','max_abs_Q','mean_abs_TD']:self.assertTrue((self.e[k]=='NOT_AVAILABLE_FROM_PERSISTED_V3_ARTIFACTS').all())
 def test_source_scope(self):
  sources=json.loads((O/'source_manifest.json').read_text())
  for p in sources:
   self.assertNotIn('stage_ep11_ep25',p);self.assertNotIn('test_predictions',p);self.assertNotIn('results/training/pricing_v2',p);self.assertNotIn('passenger_sensitive_pricing_v1',p)
  self.assertTrue(json.loads((O/'numerical_reconciliation.json').read_text())['no_simulator_instantiated'])
 def test_request_audit(self):
  d=pd.read_parquet(O/'tables/request_level_audit.parquet');self.assertEqual(len(d),293819);self.assertTrue(d.episode.between(1,10).all());self.assertTrue((d.accepted==(d.P_offer<=d.P_max)).all());self.assertTrue(d.request_id.is_unique)
 def test_sensitivity_totals(self):
  d=pd.read_csv(O/'sensitivity_runtime_summary.csv');self.assertEqual(d.requests.sum(),self.e.requests.sum());self.assertEqual(d.accepted.sum(),self.e.accepted.sum())
if __name__=='__main__':unittest.main()
