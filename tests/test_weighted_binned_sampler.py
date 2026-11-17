import copy,inspect,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from src.pricing.weighted_binned_sampler import WeightedBinnedSensitivity,load_sensitivity,restore_sensitivity,VERSION
from src.pricing.binned_sampler import BinnedSensitivity
from src.pricing.slot_v3 import FittedSensitivity,pmax
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from src.pricing.od_contract import support_from_trips
from tests.test_od_pricing import runtime,evidence
from tests.test_historical_request_replay import frame
CONTRACT=Path('results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration/sampling_contract.json')
UNIFORM=Path('results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/provisional_sampling/sampling_contract.json')

class WeightedTests(unittest.TestCase):
 def test_conditional_counts_and_moments(self):
  s=WeightedBinnedSensitivity(CONTRACT);bins=pd.read_csv('results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/final_validation/conditional_distance_bins.csv')
  for sid,p in s.calibration['conditions'].items():
   b=bins[bins.historical_condition==sid];pos=b[b.status=='POSITIVE_ELASTICITY'];n=np.array(p['request_counts']);w=np.array(p['probabilities']);a=np.array(p['values'])
   np.testing.assert_array_equal(n,pos.n_requests);np.testing.assert_allclose(w,n/n.sum(),rtol=0,atol=1e-15)
   self.assertEqual(p['source_requests'],int(b.n_requests.sum()));self.assertEqual(p['represented_requests']+p['excluded_bin_requests'],p['source_requests']);self.assertAlmostEqual(w.sum(),1)
   if sid=='GLOBAL':
    self.assertEqual(n.sum(),6967155);m=w@a;self.assertAlmostEqual(m,1.7152994769891905,places=12);self.assertAlmostEqual(np.sqrt(w@((a-m)**2)),.41601488931379027,places=12)
 def test_deterministic_weighted_draw_and_no_distance_input(self):
  a=WeightedBinnedSensitivity(CONTRACT,42);rng=np.random.default_rng(42)
  self.assertEqual(list(inspect.signature(a.draw).parameters),['code','t'])
  for code,t in [(1,'2026-03-01'),(15,'2026-03-01'),(999,'2026-03-01'),(8,'2026-03-01 08:00')]*20:
   sid,_,_=a.select(code,t);p=a.calibration['conditions'][sid];x=a.draw(code,t)
   self.assertEqual(x['epsilon'],float(rng.choice(p['values'],p=p['probabilities'])));self.assertGreaterEqual(x['epsilon'],p['lower']);self.assertLessEqual(x['epsilon'],p['upper'])
  self.assertEqual(a.select(999,'2026-03-01')[0],'T1_POOLED')
 def test_invalid_weights_rejected(self):
  c=json.loads(CONTRACT.read_text())
  for mode in ['negative','nonfinite','zero','mismatch','shape','count','period']:
   d=copy.deepcopy(c);p=d['conditions']['GLOBAL']
   if mode=='negative':p['probabilities'][0]=-1
   if mode=='nonfinite':p['probabilities'][0]=float('nan')
   if mode=='zero':p['request_counts']=[0]*len(p['values'])
   if mode=='mismatch':p['probabilities'][0]+=.01
   if mode=='shape':p['request_counts'].pop()
   if mode=='count':p['source_requests']+=1
   if mode=='period':d['calibration_period']='March17-31'
   with tempfile.TemporaryDirectory() as tmp:
    f=Path(tmp)/'c.json';f.write_text(json.dumps(d))
    with self.assertRaises(ValueError):WeightedBinnedSensitivity(f)
 def test_uniform_compatibility(self):
  s=load_sensitivity(UNIFORM,42);self.assertIs(type(s),BinnedSensitivity);rng=np.random.default_rng(42)
  for _ in range(20):
   sid,_,_=s.select(1,'2026-03-01');self.assertEqual(s.draw(1,'2026-03-01')['epsilon'],float(rng.choice(s.calibration['conditions'][sid]['values'])))
  with self.assertRaises(ValueError):WeightedBinnedSensitivity(UNIFORM)
  with self.assertRaises(ValueError):BinnedSensitivity(CONTRACT)
 def test_acceptance_and_snapshot(self):
  s=load_sensitivity(CONTRACT,42);c=s.contract;p,l=c['P_base'],c['L_base'];self.assertEqual(pmax(l,2,c),p);self.assertAlmostEqual(pmax(2*l,2,c),1.5*p)
  snap=s.snapshot();other=restore_sensitivity(snap);self.assertEqual(s.draw(1,'2026-03-01'),other.draw(1,'2026-03-01'))
  snap['binned_sampler_version']=BinnedSensitivity.VERSION
  with self.assertRaises(ValueError):restore_sensitivity(snap)
 def test_replay_checkpoint_reward_and_fleet(self):
  r=runtime();self.assertIs(type(r.provider),FittedSensitivity)
  r=runtime(lambda **kw: ODPricingRuntime(sensitivity_contract=CONTRACT,od_support=support_from_trips(evidence()),**kw))
  with patch('src.simulation.historical_request_replay.read_slot',side_effect=frame):
   r.run_slot(policy=lambda od,s:0,weather_code=1)
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'snapshot';save_od_checkpoint(r,p);other=load_od_checkpoint(p)
    for obj in [r,other]:obj.run_slot(policy=lambda od,s:0,weather_code=1)
    self.assertEqual(r.audit,other.audit);self.assertEqual(r.slot_audit,other.slot_audit);self.assertEqual(r.demand_state,other.demand_state)
    self.assertTrue(all(x['sensitivity_version']==VERSION for x in r.audit))
    self.assertAlmostEqual(r.environment_reward,sum(x['reward_contribution'] for x in r.audit[-4:]));self.assertAlmostEqual(sum(x['reward_contribution'] for x in r.audit),sum(x[2] for x in r.learner.replay))
    for name in ['fleet','operational','missions','passengers','ledger']:self.assertEqual(encode(getattr(r.engine,name)),encode(getattr(other.engine,name)))
    m=json.loads((p/'manifest.json').read_text());m['sensitivity']['version']=BinnedSensitivity.VERSION;(p/'manifest.json').write_text(json.dumps(m))
    with self.assertRaises(ValueError):load_od_checkpoint(p)
