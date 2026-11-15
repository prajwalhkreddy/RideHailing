import unittest,json,importlib.util,tempfile,copy
from pathlib import Path
import numpy as np,pandas as pd
from src.pricing.passenger_sensitive_v2_conditioned import ConditionedV2SensitivityProvider,DEFAULT_GROUPING,VERSION
from src.pricing.passenger_sensitive_v2 import sha256,resolve_pricing
P=Path('results/analysis/2026-11-14_pricing_v2_time_specific_weather')
spec=importlib.util.spec_from_file_location('time_grouping',P/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AnalysisTests(unittest.TestCase):
 def test_time(self):self.assertEqual([m.time_group(h) for h in [0,3,4,5,6,15,16,23]],['T1','T1','T2','T2','T3','T3','T4','T4'])
 def test_bad_hour(self):
  for h in [-1,24,1.5]:
   with self.assertRaises(ValueError):m.time_group(h)
 def test_distance(self):np.testing.assert_allclose(m.pdist([[0,0],[3,4]]),[5])
 def test_partition(self):
  x=np.array([[0,0],[.1,0],[10,10],[10.1,10]]);a=m.labels(x,2);np.testing.assert_array_equal(a,m.labels(x,2));self.assertEqual(a[0],a[1]);self.assertNotEqual(a[0],a[2])
 def test_selection_not_silhouette_only(self):
  r=dict(K=2,silhouette=.9,minimum_cluster_codes=1,stability_median=1,stability_p10=1);self.assertIsNone(m.choose([r]));r.update(minimum_cluster_codes=2);self.assertEqual(m.choose([r])['K'],2)
 def test_simpler_near_tie(self):
  r=dict(K=2,silhouette=.5,minimum_cluster_codes=2,stability_median=.9,stability_p10=.8);s=dict(r,K=3,silhouette=.51);self.assertEqual(m.choose([s,r])['K'],2)
 def test_support_and_population(self):
  s=pd.read_csv(P/'weather_code_time_statistics.csv');self.assertEqual(s.N.sum(),5779213);self.assertTrue((s.N_ge100==s.N.ge(100)).all())
 def test_complete_mapping(self):
  f=pd.read_csv(P/'weather_time_group_mapping.csv');self.assertEqual(len(f),56);self.assertFalse(f.duplicated(['raw_weather_code','T_group']).any());self.assertTrue(f.loc[f.N.lt(100),'time_specific_weather_group'].isna().all())
 def test_support_moments(self):
  s=pd.read_csv(P/'conditional_support_manifest.csv');t=s[s.level.eq(2)];g=s[s.support_id.eq('GLOBAL')].iloc[0];mean=np.average(t['mean'],weights=t.N);sd=np.sqrt(np.average(t.SD**2+(t['mean']-mean)**2,weights=t.N));self.assertEqual(t.N.sum(),5779213);self.assertAlmostEqual(mean,g['mean'],12);self.assertAlmostEqual(sd,g.SD,12)
class RuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=ConditionedV2SensitivityProvider(rng=np.random.default_rng(42),expected_grouping_hash=sha256(DEFAULT_GROUPING))
 def setUp(self):self.p.rng=np.random.default_rng(42);self.p.fallback_counts={str(i):0 for i in range(4)}
 def test_no_context_fails(self):
  with self.assertRaises(ValueError):self.p.sample()
 def test_all_cells_select_explicit_support(self):
  for code,t in self.p.mapping:
   meta=self.p.select_support(code,self.p.grouping['T_group_definitions'][t][0]);self.assertIn(meta['support_id'],self.p.supports);self.assertIn(meta['fallback_level'],range(4))
 def test_time_specific_lookup(self):self.assertNotEqual(self.p.select_support(1,0)['support_id'],self.p.select_support(1,6)['support_id'])
 def test_determinism_membership_logging(self):
  saved=self.p.state_dict();a=[self.p.sample_request(1,'2026-03-16 00:00')[1] for _ in range(10)];self.p.load_state_dict(saved);b=[self.p.sample_request(1,'2026-03-16 00:00')[1] for _ in range(10)];self.assertEqual(a,b);self.assertEqual(sum(self.p.fallback_counts.values()),10)
  for meta in a:self.assertTrue(np.any(self.p.supports[meta['support_id']]==meta['sampled_epsilon']))
 def test_guard(self):
  for date in ['2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):self.p.sample_request(1,date)
 def test_unknown_explicit_fallback(self):self.assertIn(self.p.select_support(999,0)['fallback_level'],[2,3])
 def test_no_silent_version(self):
  with self.assertRaises(ValueError):resolve_pricing('v2',self.p)
  self.assertIs(resolve_pricing(VERSION,self.p),self.p.pricing)
 def test_state_mismatch(self):
  for key in ['mapping_hash','conditional_support_manifest_hash','fallback_policy_version','sensitivity_version']:
   state=self.p.state_dict();state[key]='wrong'
   with self.assertRaises(ValueError):self.p.load_state_dict(state)
 def test_checkpoint_round_trip(self):
  from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
  d=PassengerSensitiveDQN();d.sensitivity_provider=self.p
  with tempfile.TemporaryDirectory() as tmp:
   d.save(tmp);state=self.p.state_dict();loaded=PassengerSensitiveDQN.load(tmp,sensitivity_provider=self.p);self.assertEqual(loaded._loaded_sensitivity_version,VERSION);self.assertEqual(self.p.state_dict(),state)
   meta=Path(tmp)/'checkpoint.json';x=json.loads(meta.read_text());x['sensitivity_state']['mapping_hash']='wrong';meta.write_text(json.dumps(x))
   with self.assertRaises(ValueError):PassengerSensitiveDQN.load(tmp,sensitivity_provider=self.p)
 def test_fallback_levels(self):
  self.assertEqual(self.p.select_support(13,0)['fallback_level'],1)
  self.assertEqual(self.p.select_support(17,0)['fallback_level'],2)
  original=self.p.supports
  try:
   self.p.supports=dict(original);self.p.supports['T1_POOLED']=np.array([1.]);self.assertEqual(self.p.select_support(999,0)['fallback_level'],3)
  finally:self.p.supports=original
 def test_conditional_request_price_contract(self):
  from src.dispatch.request import RequestState
  from datetime import datetime,timedelta
  c=self.p.pricing;t=datetime(2026,1,1);km=3.;e=2.;raw=c.maximum_price(km,e);pc=c.effective_threshold(raw)
  r=RequestState(1,0,0,1,base_fare=c.P_BASE_USD,pricing_factor=.85,offered_fare=.85*c.P_BASE_USD,customer_accepted=True,customer_model='passenger_sensitive_weather_time_conditioned_v2',source_trip_id=0,empirical_pickup_datetime=t,empirical_dropoff_datetime=t+timedelta(minutes=1),trip_duration_minutes=1.,trip_distance_km=km,trip_distance_miles=km/1.609344,v1_epsilon_c=e,v1_epsilon_min=0.,v1_raw_pc_usd=raw,v1_pc_usd=pc,v2_reference_p_base=c.P_BASE_USD,v2_reference_l_base_km=c.L_BASE_KM)
  r.validate(range(142),15);r.v1_raw_pc_usd+=1
  with self.assertRaises(ValueError):r.validate(range(142),15)
 def test_all_actions_use_single_draw(self):
  draw,meta=self.p.sample_request(1,'2026-03-16');before=self.p.state_dict();pc=self.p.pricing.effective_threshold(self.p.pricing.maximum_price(3,draw.value));self.p.pricing.feasible_mask(pc);self.assertEqual(self.p.state_dict(),before)
 def test_two_request_runtime_context(self):
  import sys,importlib.util,copy
  folder=Path('results/training/pricing_v2_staged_training_001/weather_conditioned')
  spec=importlib.util.spec_from_file_location('conditioned_prepare_test',folder/'prepare_development.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
  f,manifest=d.load_fixture();env=d.environment(self.p,d.EvaluationPolicy('HIGHEST_FEASIBLE'));requests=copy.deepcopy(f['slots'][0][:2]);env.run_slot(requests,terminal=True,train_dqn=False,explore_pricing=False)
  self.assertEqual(len(env.request_audit),2);self.assertEqual(sum(self.p.fallback_counts.values()),2)
  for row in env.request_audit:
   self.assertEqual(row['sampled_epsilon'],row['epsilon_c']);self.assertEqual(row['T_group'],'T1');self.assertLessEqual(row['P_offer_USD'],row['P_accept_c'])
 def test_harness_gate_before_environment(self):
  import sys,importlib.util
  from unittest.mock import patch
  folder=Path('results/training/pricing_v2_staged_training_001/weather_conditioned');old=sys.modules.pop('prepare_development',None);sys.path.insert(0,str(folder.resolve()))
  try:
   spec=importlib.util.spec_from_file_location('conditioned_harness_test',folder/'training_harness.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
   with patch.object(Path,'read_text',return_value=json.dumps({'verdict':'BLOCKED'})),patch.object(h,'provider') as provider:
    with self.assertRaisesRegex(ValueError,'Conditional launch gate'):h.run()
    provider.assert_not_called()
  finally:
   sys.path.pop(0);sys.modules.pop('prepare_development',None)
   if old is not None:sys.modules['prepare_development']=old
if __name__=='__main__':unittest.main()
