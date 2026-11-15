"""Focused reporting integrity checks; no runtime or model imports."""
import unittest,json,hashlib,ast
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
from pypdf import PdfReader
O=Path(__file__).resolve().parent;R=O.parents[2];T=R/'results/training/pricing_v2_staged_training_001/weather_conditioned'
class ReportingIntegrity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.man=json.loads((O/'source_manifest.json').read_text());cls.ix=pd.read_csv(O/'visual_index.csv').fillna('');cls.cov=pd.read_csv(O/'requested_visual_coverage.csv').fillna('')
 def test_source_hashes_unchanged(self):
  for p,m in self.man['sources'].items():
   h=hashlib.sha256()
   with (R/p).open('rb') as f:
    for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
   self.assertEqual(h.hexdigest(),m['sha256'],p)
 def test_visual_images_and_ids(self):
  self.assertTrue(self.ix.visual_id.is_unique)
  for p in self.ix.final_output_path:
   if p:
    with Image.open(O/p) as im:self.assertGreater(im.width,800);im.verify()
 def test_requested_core_ids_present(self):
  ids={f'{a}{i}' for a,n in {'A':5,'B':5,'C':6,'D':9,'E':5,'F':1,'G':9,'H':3,'I':3,'J':4,'K':5,'L':1}.items() for i in range(1,n+1)}
  self.assertTrue(ids.issubset(set(self.ix.visual_id)))
 def test_coverage_reports_real_gaps(self):
  self.assertEqual(int(self.cov.status.eq('MISSING').sum()),3)
  self.assertTrue(set(self.cov.status).issubset({'MISSING','PRESENT_CURRENT','PRESENT_HISTORICAL','NOT_APPLICABLE_CURRENT_RUNTIME'}))
  self.assertIn('Missing:',(O/'README.md').read_text())
 def test_population_flow(self):
  p=pd.read_csv(O/'tables/population_flow.csv').iloc[0]
  self.assertEqual(p.source_population_N,p.denominator_unresolved_N+p.negative_epsilon_N+p.final_nonnegative_candidate_N)
  self.assertEqual(p.final_nonnegative_candidate_N,5779213)
  self.assertEqual(pd.read_csv(O/'tables/calibration_bins.csv').N.sum(),6967155)
 def test_exact_development_comparison(self):
  d=pd.read_csv(O/'tables/development_comparison.csv');self.assertTrue(d.requests.eq(73754).all());self.assertEqual(d.iloc[0].assignments,59632);self.assertEqual(d.iloc[1].assignments,59768)
  self.assertAlmostEqual(d.iloc[0].revenue-d.iloc[1].revenue,-23974.8778294639,places=6)
 def test_fixture_dates_and_feasibility(self):
  d=pd.read_parquet(T/'HIGHEST_FEASIBLE_requests.parquet');self.assertTrue(pd.to_datetime(d.timestamp).dt.strftime('%Y-%m-%d').eq('2026-03-16').all())
  a=np.array([.85,.9,.95,1,1.05,1.1,1.15]);expected=d.P_base_USD.to_numpy()[:,None]*a<=d.P_accept_c.to_numpy()[:,None]+1e-12
  actual=d[['mask_'+x for x in ['085','090','095','100','105','110','115']]].to_numpy(bool)
  np.testing.assert_array_equal(expected,actual);np.testing.assert_array_equal(actual.sum(1),d.feasible_action_count)
 def test_action_counts_and_agreement(self):
  d=pd.read_csv(T/'development_actions_ep25.csv');c=d[d.feasible_action_count>1];g=c.feasible_action_count-1-c.selected_action_index
  self.assertEqual(len(c),27719);self.assertEqual(int((g>0).sum()),15800);self.assertEqual(int((g==1).sum()),11325)
  s=pd.read_csv(T/'postrun_analysis/policy_stability.csv');self.assertAlmostEqual(s[(s.from_episode==20)&(s.to_episode==25)].iloc[0].choice_agreement_pct,41.0801255456546)
 def test_dynamic_evidence(self):
  q=pd.read_csv(O/'tables/dynamic_cases.csv');self.assertEqual(len(q),20);self.assertEqual(int((q.net_revenue_difference>1e-8).sum()),0)
  self.assertEqual(int(q.q_ranking_incorrect.sum()),19);self.assertEqual(int(q.q_discounted_ranking_incorrect.sum()),20)
 def test_no_production_execution_imports(self):
  for name in ['build_review.py','complete_review.py','audit_guidance.py']:
   tr=ast.parse((O/name).read_text())
   for n in ast.walk(tr):
    if isinstance(n,ast.ImportFrom):self.assertFalse((n.module or '').startswith(('src.','tensorflow','torch','sklearn','scipy.cluster')))
    if isinstance(n,ast.Import):
     for a in n.names:self.assertFalse(a.name.startswith(('src.','tensorflow','torch','sklearn','scipy.cluster')))
 def test_no_protected_observation_source(self):
  for p in self.man['sources']:
   if p.endswith(('.parquet','.npy','.npz')):
    self.assertTrue(any(x in p for x in ['recalibration_decision_analysis/intermediate','time_specific_weather_2026_11_14/GLOBAL.npy','weather_conditioned/HIGHEST_FEASIBLE_requests.parquet']),p)
 def test_summary_one_page(self):self.assertEqual(len(PdfReader(O/'review_summary.pdf').pages),1)
if __name__=='__main__':unittest.main(verbosity=2)
