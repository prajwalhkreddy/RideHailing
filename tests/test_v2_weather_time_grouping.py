"""Bounded grouping tests; no training, support mutation or protected data reads."""
import importlib.util,json,unittest
from pathlib import Path
import numpy as np
import pandas as pd
P=Path('results/analysis/2026-11-14_pricing_v2_weather_time_conditioning')
spec=importlib.util.spec_from_file_location('v2_grouping',P/'analyze.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def features(n=100,mean=1.,sd=2.,groups=('T1','T2','T3','T4')):return {t:dict(N=n,mean=mean,SD=sd) for t in groups}
class GroupingTests(unittest.TestCase):
 def test_time_boundaries(self):
  self.assertEqual([m.tg(h) for h in [0,3,4,5,6,15,16,23]],['T1','T1','T2','T2','T3','T3','T4','T4'])
 def test_time_invalid(self):
  for h in [-1,24]:
   with self.assertRaises(ValueError):m.tg(h)
 def test_shared_only(self):
  a=features();b=features(mean=3,groups=('T1','T3','T4'));shared,raw,d=m.pair(a,b)
  self.assertEqual(shared,['T1','T3','T4']);self.assertAlmostEqual(raw,np.sqrt(12));self.assertAlmostEqual(d,np.sqrt(2))
 def test_normalization_overlap_invariant(self):
  a=features();b=features(mean=3)
  self.assertAlmostEqual(m.pair(a,b)[2],m.pair(a,b,omit='T1')[2])
 def test_support_inclusive(self):
  self.assertEqual(len(m.pair(features(100),features(100))[0]),4)
  self.assertEqual(m.pair(features(99),features())[0],[])
 def test_no_shared_features_not_zero(self):self.assertEqual(m.pair(features(groups=('T1',)),features(groups=('T2',))),([],None,None))
 def test_low_support_excluded(self):
  c,d=m.matrix({1:features(),2:features(mean=2),13:features(groups=('T1','T4'))});self.assertEqual(c,[1,2]);self.assertEqual(d.shape,(2,2))
 def test_incompatible_overlap_removal_deterministic(self):
  a={1:features(groups=('T1','T2','T3')),2:features(groups=('T2','T3','T4')),3:features()}
  c,d=m.matrix(a);cc,dd=m.matrix(dict(reversed(list(a.items()))));self.assertEqual(c,cc);np.testing.assert_array_equal(d,dd);self.assertEqual(c,[1,3])
 def test_clustering_deterministic(self):
  d=np.array([[0.,.1,3,3],[.1,0,3,3],[3,3,0,.2],[3,3,.2,0]])
  np.testing.assert_array_equal(m.partition(d,2),m.partition(d,2));a=m.partition(d,2);self.assertEqual(a[0],a[1]);self.assertNotEqual(a[0],a[2]);self.assertEqual(a[2],a[3])
 def test_endpoints(self):
  d=np.array([[0.,1],[1,0]]);np.testing.assert_array_equal(m.partition(d,1),[0,0]);np.testing.assert_array_equal(m.partition(d,2),[0,1])
 def test_artifact_population_reconciliation(self):
  s=pd.read_csv(P/'weather_code_time_statistics.csv');self.assertEqual(int(s.N.sum()),5779213);self.assertTrue(s.SD.ge(0).all());self.assertTrue(s.distinct_dates.le(74).all())
 def test_pooled_moments(self):
  s=pd.read_csv(P/'weather_code_time_statistics.csv');v=json.loads((P/'analysis_verification.json').read_text());mean=np.average(s['mean'],weights=s.N);var=np.average(s.SD**2+(s['mean']-mean)**2,weights=s.N);self.assertAlmostEqual(mean,v['mean'],places=12);self.assertAlmostEqual(np.sqrt(var),v['SD'],places=12)
 def test_hourly_reuse(self):
  s=pd.read_csv(P/'reused_weather_hour_diagnostics.csv');self.assertEqual(int(s.N.sum()),5779213);self.assertEqual(len(s),211);self.assertTrue(s.SD.lt(4).all())
 def test_mapping_covers_codes_without_fabricating_freeze(self):
  s=pd.read_csv(P/'weather_code_group_mapping.csv');self.assertEqual(set(s.raw_weather_code),{1,2,3,5,7,8,9,12,13,14,15,16,17,21});self.assertTrue(s.weather_group.isna().all());self.assertTrue(s.mapping_status.eq('NOT_APPROVED_FOR_RUNTIME').all())
 def test_no_single_scalar_approval(self):
  c=json.loads((P/'weather_grouping_contract.json').read_text());self.assertEqual(c['mapping'],{});self.assertIsNone(c['number_of_groups']);self.assertEqual(c['best_diagnostic_K'],3)
 def test_candidate_selection_reproducible(self):
  s=pd.read_csv(P/'weather_cluster_candidates.csv');best=s.dropna(subset=['silhouette']).sort_values(['silhouette','K'],ascending=[False,True]).iloc[0];self.assertEqual(int(best.K),3)
 def test_fallback_preserves_existing_stronger_rule(self):
  c=json.loads((P/'weather_grouping_contract.json').read_text());self.assertEqual(c['fallback_policy']['levels'],['weather_group_time_group','weather_group','time_group','global']);self.assertEqual(c['fallback_policy']['minimum_support_N'],5000)
 def test_date_boundary_and_no_launch(self):
  v=json.loads((P/'verification.json').read_text());self.assertFalse(v['training_started']);self.assertFalse(v['runtime_modified']);self.assertFalse(v['weather_mapping_frozen']);self.assertTrue(v['March17_31_untouched'])
if __name__=='__main__':unittest.main()
