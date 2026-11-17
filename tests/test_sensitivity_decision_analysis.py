import unittest
import numpy as np
import pandas as pd
from scripts.sensitivity_decision_analysis import weights,summary,acceptance,boundary,BASE,OUT

class DecisionEvidenceTests(unittest.TestCase):
 def test_weights_and_request_interpretation(self):
  np.testing.assert_allclose(weights([1,3]),[.25,.75])
  self.assertAlmostEqual(summary([1,3],[1,3])['mean'],2.5)
  self.assertEqual(summary([1,3],[1,3])['median'],3)
  for w in [[0,0],[-1,2],[np.inf,2]]:
   with self.assertRaises(ValueError):weights(w)
 def test_support_and_determinism(self):
  a=summary([1,2,3],[3,2,1]);self.assertEqual(a,summary([1,2,3],[3,2,1]));self.assertEqual(a['minimum'],1);self.assertEqual(a['maximum'],3)
  with self.assertRaises(ValueError):summary([0,1],[1,1])
 def test_acceptance_exact_boundary(self):
  self.assertEqual(acceptance([1,2],[1,1],4,30,20,2),1)
  self.assertEqual(acceptance([1,2],[1,1],4,31,20,2),.5)
  self.assertEqual(acceptance([1,2],[1,1],2,20,20,2),1)
  self.assertEqual(acceptance([1,2],[1,1],2,21,20,2),0)
 def test_period_rejection(self):
  boundary(pd.DataFrame({'pickup_timestamp':pd.to_datetime(['2026-01-01 00:00','2026-03-15 23:59'])}))
  for t in ['2026-03-16','2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):boundary(pd.DataFrame({'pickup_timestamp':pd.to_datetime([t])}))
 def test_saved_count_and_groups(self):
  b=pd.read_csv(OUT/'bin_request_counts.csv');self.assertEqual(int(b.loc[b.historical_condition=='GLOBAL','n_requests'].sum()),6967155)
  reference=pd.read_csv(BASE/'final_validation/conditional_distance_bins.csv');pd.testing.assert_frame_equal(b,reference)
  s=pd.read_csv(OUT/'assigned_population_proportions.csv');self.assertEqual(int(s.N.sum()),6967155);self.assertAlmostEqual(s.fraction.sum(),1)
  a=pd.read_csv(OUT/'acceptance_impact.csv');self.assertTrue(a.acceptance.between(0,1).all());self.assertEqual(a.condition.nunique(),8)
  t=pd.read_csv(OUT/'temporal_weather_association.csv');self.assertTrue((t.train_hours>0).all());self.assertTrue((t.validation_hours>0).all())
