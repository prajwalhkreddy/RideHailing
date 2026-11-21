"""Bounded publication-export checks; no simulator or model execution."""
import unittest,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'results_v2/publication';T=O/'tables'
class EvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.x=pd.read_csv(T/'two_episode_passenger_acceptance_details.csv',float_precision='round_trip');cls.s=pd.read_csv(T/'two_episode_slot_acceptance_summary.csv');cls.v=json.loads((O/'passenger_evidence_validation.json').read_text())
 def test_unique_population(self):
  self.assertEqual(len(self.x),68845);self.assertTrue(self.x.request_id.is_unique);self.assertEqual(self.x.groupby('episode_id').size().tolist(),[30359,38486])
 def test_slots_and_counts(self):
  self.assertEqual(len(self.s),32);self.assertEqual(self.s.groupby('episode_id').size().tolist(),[16,16]);self.assertEqual(self.s.eligible_requests.sum(),68845);self.assertEqual(self.s.total_source_requests.sum(),70106);self.assertEqual(self.s.excluded_requests.sum(),1261)
 def test_exclusive_outcomes(self):
  x=self.x;self.assertTrue((x.accepted!=x.rejected).all());self.assertTrue((x.assigned|x.accepted_unmatched).equals(x.accepted));self.assertFalse((x.assigned&x.accepted_unmatched).any());self.assertEqual(x.accepted.sum(),18218);self.assertEqual(x.assigned.sum(),14834)
 def test_formula_and_units(self):
  x=self.x;np.testing.assert_allclose(x.p_base_usd,22.354198442390455,rtol=0,atol=1e-13);np.testing.assert_allclose(x.l_base_km,4.616983790655043,rtol=0,atol=1e-14)
  p=x.p_base_usd+x.p_base_usd/x.sampled_elasticity*((x.trip_distance_km-x.l_base_km)/x.l_base_km)
  np.testing.assert_allclose(p,x.maximum_acceptable_price_usd,rtol=0,atol=1e-10);np.testing.assert_allclose(x.source_trip_distance_miles_reconstructed*1.609344,x.trip_distance_km,rtol=0,atol=1e-12);self.assertTrue((x.accepted==(x.offered_price_usd<=p)).all())
 def test_reward_and_fallback(self):
  x=self.x;np.testing.assert_allclose(x.successful_dispatch_reward_usd,np.where(x.assigned,x.offered_price_usd,0),rtol=0,atol=1e-10);self.assertAlmostEqual(x.successful_dispatch_reward_usd.sum(),326987.19694548374,places=7);self.assertEqual(x.fallback_od.sum(),36);self.assertEqual(x[x.fallback_od].assigned.sum(),35)
  np.testing.assert_allclose(self.s.supported_reward_usd+self.s.fallback_revenue_usd,self.s.total_revenue_usd,rtol=0,atol=1e-8)
 def test_slot_reconciliation(self):
  for a in self.s.itertuples():
   x=self.x[(self.x.episode_id==a.episode_id)&(self.x.slot_index==a.slot_index)];self.assertEqual(len(x),a.eligible_requests);self.assertEqual(x.accepted.sum(),a.accepted);self.assertEqual(x.assigned.sum(),a.assigned);self.assertAlmostEqual(x.offered_price_usd.mean(),a.mean_offered_price_usd,places=10)
 def test_chronology(self):
  t=pd.to_datetime(self.x.request_arrival_utc,utc=True);s=pd.to_datetime(self.x.slot_start_utc,utc=True);self.assertTrue(((t>=s)&(t<s+pd.Timedelta(minutes=30))).all());self.assertEqual(set(t.dt.date.astype(str)),{'2026-03-01'});self.assertFalse(self.v['protected_period_access'])
 def test_request_order_and_provenance(self):
  for ep in (1,2):
   p=R/f'results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration/episode{ep}_request_reconciliation.json'
   for i,a in enumerate(json.loads(p.read_text())['demand'],1):
    x=self.x[(self.x.episode_id==ep)&(self.x.slot_index==i)];self.assertEqual(hashlib.sha256(json.dumps(x.request_id.tolist()).encode()).hexdigest(),a['order_hash'])
  self.assertGreaterEqual(len(self.v['source_sha256']),10)
  for p,h in self.v['source_sha256'].items():self.assertTrue((R/p).exists());self.assertEqual(len(h),64)
 def test_group_denominators_and_figures(self):
  for name in ['distance','factor','fare','elasticity','weather_time','od_support']:
   a=pd.read_csv(T/f'two_episode_acceptance_by_{name}.csv');self.assertEqual(a.N.sum(),68845);self.assertEqual(a.accepted.sum(),18218);self.assertEqual(a.assigned.sum(),14834)
  for r in pd.read_csv(T/'passenger_evidence_figure_manifest.csv').itertuples():
   self.assertTrue((R/r.source).exists())
   for ext in ('svg','png'):self.assertGreater((O/'figures'/f'{r.figure}.{ext}').stat().st_size,1000)
 def test_inventory_paths_and_no_missing_fields(self):
  for p in pd.read_csv(T/'master_results_inventory.csv').existing_artifact_path:self.assertTrue((R/p.split('#')[0]).exists(),p)
  self.assertFalse(self.x.drop(columns=['rejection_reason']).isna().any().any());self.assertFalse(self.s.isna().any().any())
if __name__=='__main__':unittest.main()
