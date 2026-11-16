import unittest,tempfile,json
from pathlib import Path
import numpy as np
from src.pricing.slot_v3 import *
from src.rl.slot_pricing_v3 import SlotDQN
from src.rl.pricing_dqn import bellman_targets
class V3Tests(unittest.TestCase):
 def test_actions(self):
  c=load_contract();a=np.array(c['actions']);self.assertEqual(len(a),7);np.testing.assert_allclose(a[[0,-1]]*c['P_base'],[6.6,94.7]);np.testing.assert_allclose(np.diff(a),np.diff(a)[0])
 def test_mapping(self):
  p=FittedSensitivity();self.assertEqual(p.select(13,'2026-03-12')[0],'RAW_13');self.assertEqual(p.select(15,'2026-03-12')[0],'RAW_15');self.assertEqual(p.select(17,'2026-03-12')[0],'T1_POOLED');self.assertEqual(p.select(21,'2026-03-12')[0],'T1_POOLED');self.assertEqual(p.select(1,'2026-03-12')[0],'T1_G1')
  for hour,T in [(4,'T2'),(6,'T3'),(16,'T4')]:self.assertEqual(p.select(1,f'2026-03-12 {hour:02d}:00')[0],T+'_POOLED')
 def test_determinism_support(self):
  a=FittedSensitivity(19);b=FittedSensitivity(19)
  for code in [1,13,15,17,21]:
   x=a.draw(code,'2026-03-12');self.assertEqual(x,b.draw(code,'2026-03-12'));self.assertGreater(x['epsilon'],0)
 def test_pmax(self):
  c=load_contract();self.assertEqual(pmax(c['L_base'],1,c),c['P_base']);self.assertLess(pmax(0,.1,c),0)
  for e in [0,-1,float('nan')]:
   with self.assertRaises(ValueError):pmax(1,e,c)
 def test_protected(self):
  for t in ['2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):allowed(t)
 def test_state(self):
  s=np.array([1,2,3,4,*([1/9]*9),.1,.25]);self.assertEqual(validate_state(s).shape,(15,));
  with self.assertRaises(ValueError):validate_state(np.ones(13))
 def test_target(self):
  np.testing.assert_allclose(bellman_targets([10,10],np.array([False,True]),np.ones((2,7))*20,.99),[29.8,10])
 def test_checkpoint(self):
  d=SlotDQN();s=np.array([1,2,3,4,*([1/9]*9),.1,.25]);d.store(s,0,6.6,s,True)
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'new';d.save(p);e=SlotDQN.load(p);self.assertEqual(len(e.replay),1);np.testing.assert_array_equal(d.online(s[None]).numpy(),e.online(s[None]).numpy());m=json.loads((p/'checkpoint.json').read_text());m['version']='v2';(p/'checkpoint.json').write_text(json.dumps(m))
   with self.assertRaises(ValueError):SlotDQN.load(p)
 def test_no_passenger_action_signature(self):
  import inspect
  self.assertEqual(list(inspect.signature(SlotDQN.select_action).parameters),['self','state','explore'])
 def test_bounded_evidence(self):
  import pandas as pd
  o=CONTRACT.parent;f=pd.read_csv(o/'bounded_request_validation.csv');s=pd.read_csv(o/'bounded_slot_validation.csv');self.assertTrue((f.accepted==(f.P_offer<=f.P_max)).all());self.assertTrue((f.loc[~f.accepted,'reward_contribution']==0).all());self.assertTrue((f.loc[f.dispatch_outcome=='ACCEPTED_BUT_UNMATCHED','reward_contribution']>0).all());self.assertTrue((s.generated==s.accepted+s.rejected).all());self.assertTrue(s.groupby('slot').size().eq(142).all());self.assertTrue((pd.to_datetime(s.next_state_timestamp)-pd.to_datetime(s.slot)).eq(pd.Timedelta(minutes=30)).all())
if __name__=='__main__':unittest.main()
