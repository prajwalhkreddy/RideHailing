"""Explicit reference fallback without learned-support expansion."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from tests.test_od_pricing import runtime, requests
from tests.test_historical_request_replay import frame
from src.pricing.unseen_od import VERSION, validate
from src.simulation.historical_request_replay import replay_requests
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode

POLICY={'version':VERSION,'factor':1.0}
class FallbackTests(unittest.TestCase):
 def test_preserve_and_reject_invalid(self):
  f=frame();a,m=replay_requests(f,'2026-03-12',[(1,1)],fallback_contract=POLICY)
  self.assertEqual(len(a),4);self.assertEqual(m['fallback_requests'],4)
  self.assertEqual([(r.origin_grid,r.destination_grid) for r in a],[(0,1)]*4)
  f.loc[0,'PUGridID']=142
  with self.assertRaises(ValueError):replay_requests(f,'2026-03-12',[(1,1)],fallback_contract=POLICY)
  with self.assertRaises(ValueError):validate(dict(version=VERSION,factor=.9))
 def test_revenue_replay_and_resume(self):
  r=runtime();r.fallback_contract=POLICY.copy();pairs=r.pairs;support=r.od_support.copy()
  req=requests(r.engine.timestamp)
  for x in req:x.destination_grid=3
  rows=r.run_slot(req,policy=lambda d,s:0,weather_code=1)
  self.assertTrue(all(x['is_fallback'] and x['factor']==1. for x in rows))
  self.assertTrue(all(x['accepted']==(x['P_offer']<=x['P_max']) for x in rows))
  self.assertGreater(r.system_revenue,0)
  self.assertEqual(r.environment_reward,0)
  self.assertTrue(all(x[2]==0 for x in r.learner.replay))
  self.assertEqual(len(r.learner.replay),len(pairs))
  self.assertEqual(r.pairs,pairs);self.assertEqual(r.od_support,support)
  self.assertEqual(r.system_revenue,sum(x['P_offer'] for x in rows if x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED'))
  self.assertTrue(all(x['reward_contribution']==0 for x in rows if x['dispatch_outcome']!='ACCEPTED_AND_ASSIGNED'))
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'saved';save_od_checkpoint(r,p)
   with self.assertRaises(ValueError):load_od_checkpoint(p)
   other=load_od_checkpoint(p,fallback_contract=POLICY)
   for obj in (r,other):obj.run_slot([],policy=lambda d,s:0,weather_code=1)
   self.assertEqual(encode(r.audit),encode(other.audit));self.assertEqual(encode(r.fallback_audit),encode(other.fallback_audit))
   self.assertEqual(encode(r.engine.fleet),encode(other.engine.fleet))
