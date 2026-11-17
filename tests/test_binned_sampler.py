"""Bounded opt-in sampling/runtime verification; no training."""
import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
from src.pricing.binned_sampler import BinnedSensitivity,VERSION
from src.pricing.slot_v3 import pmax,FittedSensitivity
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from tests.test_od_pricing import runtime,requests,evidence
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.pricing.od_contract import support_from_trips
CONTRACT=Path('results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/provisional_sampling/sampling_contract.json')
class SamplerTests(unittest.TestCase):
 def test_determinism_support_and_groups(self):
  a=BinnedSensitivity(CONTRACT,42);b=BinnedSensitivity(CONTRACT,42)
  for code,t in [(1,'2026-03-01'),(15,'2026-03-01'),(999,'2026-03-01'),(8,'2026-03-01 08:00')]*25:
   x=a.draw(code,t);self.assertEqual(x,b.draw(code,t));pool=a.calibration['conditions'][x['sensitivity_condition']]
   self.assertIn(x['epsilon'],pool['values']);self.assertGreater(x['epsilon'],0)
  self.assertEqual(a.select(999,'2026-03-01')[0],'T1_POOLED')
  self.assertEqual(a.select(15,'2026-03-01')[0],'RAW_15')
  for code in [float('nan'),float('inf'),1.5]:
   with self.assertRaises(ValueError):a.draw(code,'2026-03-01')
  with self.assertRaises(ValueError):a.draw(1,'2026-03-17')
 def test_invalid_contract_and_snapshot(self):
  c=json.loads(CONTRACT.read_text())
  for edit in ['bounds','zero','reference','version']:
   d=copy.deepcopy(c)
   if edit=='bounds':d['conditions']['GLOBAL']['lower']=0
   if edit=='zero':d['conditions']['GLOBAL']['values'][0]=0
   if edit=='reference':d['P_base']=10
   if edit=='version':d['version']='OLD'
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'c.json';p.write_text(json.dumps(d))
    with self.assertRaises(ValueError):BinnedSensitivity(p)
  a=BinnedSensitivity(CONTRACT);a.draw(1,'2026-03-01');b=BinnedSensitivity.restore(a.snapshot())
  self.assertEqual(a.draw(1,'2026-03-01'),b.draw(1,'2026-03-01'))
 def test_acceptance_formula(self):
  c=BinnedSensitivity(CONTRACT).contract;p,l=c['P_base'],c['L_base']
  self.assertEqual(pmax(l,2,c),p)
  self.assertAlmostEqual(pmax(2*l,2,c),1.5*p)
  self.assertTrue(1.5*p<=pmax(2*l,2,c))
  self.assertFalse(1.6*p<=pmax(2*l,2,c))
  for e in [0,-1,float('nan')]:
   with self.assertRaises(ValueError):pmax(l,e,c)
 def test_checkpoint_resume_reward_and_version(self):
  r=runtime();self.assertIs(type(r.provider),FittedSensitivity)
  r=runtime(lambda **kw: ODPricingRuntime(sensitivity_contract=CONTRACT,od_support=support_from_trips(evidence()),**kw))
  r.run_slot(requests(r.engine.timestamp),policy=lambda od,s:0,weather_code=1)
  self.assertAlmostEqual(r.environment_reward,sum(x['reward_contribution'] for x in r.audit))
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'snapshot';save_od_checkpoint(r,p);b=load_od_checkpoint(p)
   args=dict(policy=lambda od,s:0,weather_code=1)
   r.run_slot([],**args);b.run_slot([],**args)
   self.assertEqual(r.audit,b.audit);self.assertEqual(r.slot_audit,b.slot_audit)
   for name in ['fleet','operational','missions','passengers','ledger']:
    self.assertEqual(encode(getattr(r.engine,name)),encode(getattr(b.engine,name)))
   self.assertEqual(r.provider.draw(1,r.engine.timestamp),b.provider.draw(1,b.engine.timestamp))
   manifest=json.loads((p/'manifest.json').read_text());manifest['sensitivity']['version']='HISTORICAL_V3';(p/'manifest.json').write_text(json.dumps(manifest))
   with self.assertRaises(ValueError):load_od_checkpoint(p)
 def test_opt_in_historical_replay(self):
  from unittest.mock import patch
  from tests.test_historical_request_replay import frame
  r=runtime(lambda **kw: ODPricingRuntime(sensitivity_contract=CONTRACT,od_support=support_from_trips(evidence()),**kw))
  with patch('src.simulation.historical_request_replay.read_slot',side_effect=frame):
   rows=r.run_slot(policy=lambda od,s:0,weather_code=1)
  self.assertEqual(len(rows),4);self.assertEqual(r.demand_state['requests_consumed'],4)
  self.assertTrue(all(x['sensitivity_version']==VERSION for x in rows))
  self.assertAlmostEqual(sum(x['reward_contribution'] for x in rows),sum(x[2] for x in r.learner.replay))
