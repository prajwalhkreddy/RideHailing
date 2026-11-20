"""Bounded inference-only checks; saved real-run probabilities, no training."""
import json, unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
import pandas as pd
from src.simulation.utc_od_state import UTCSnapshot, UTCStateBuilder, UTCLedger
from src.pricing.od_contract import od_states, pairs_from_support
from src.rl.od_pricing_dqn import ODPricingDQN
from src.simulation.utc_od_inputs import state_sources
P=Path('results_v2/federated_learning/2026-11-17_online_routing_rng_retry_002')

def fixture():
 manifest=json.loads(Path('results_v2/federated_learning/2026-11-17_online_routing_retry_001/information_contract.json').read_text())
 pairs=pairs_from_support(json.loads(Path(manifest['artifacts']['od_support']['path']).read_text()))
 first=pairs[0]; second=next(p for p in pairs if p[0]!=first[0])
 learned=np.load(P/'primary_probabilities.npz')['values'][0]
 control=np.load(P/'control_probabilities.npz')['values'][0]
 t=pd.Timestamp('2026-03-12T04:30Z'); ledger=UTCLedger();ledger.completed[t-pd.Timedelta(minutes=30)]=(t,np.zeros(142,int),0.)
 masks={g:(learned[g]>0)|(control[g]>0) for g in range(142)}
 def builder(values):
  snap=lambda v:UTCSnapshot(t,t,v,t)
  return UTCStateBuilder(snap({g:float(g+1) for g in range(142)}),ledger,[],snap(dict(enumerate(values))),snap({g:(g%5)*.25 for g in range(142)}),masks)
 operational=NS(state_for=lambda _:pd.DataFrame({'Grid_ID':range(142),'F_hat':np.arange(142)*.01}))
 def states(values):return od_states(NS(timestamp=t,operational=operational,current_states=builder(values)),(first,second))
 return t,learned,control,masks,builder,states,(first,second)

class CouplingTests(unittest.TestCase):
 def test_two_origins_and_exact_features(self):
  t,p,_,m,b,states,pairs=fixture()
  for (o,d),s in states(p).items():
   self.assertEqual(s.shape,(13,));np.testing.assert_array_equal(s[3:12],p[o]);self.assertAlmostEqual(s[0],o+1);self.assertAlmostEqual(s[1],o*.3,places=5);self.assertEqual(s[2],0);self.assertEqual(s[12],(d%5)*.25);self.assertEqual(s[3:12][~m[o]].sum(),0)
 def test_actual_dqn_dependence_without_weight_changes(self):
  _,p,c,_,_,states,_=fixture();net=ODPricingDQN(seed=42,master_math=True,utc_mode=True);before=[w.copy() for w in net.online.get_weights()]
  a=np.stack(list(states(p).values()));b=np.stack(list(states(c).values()))
  np.testing.assert_array_equal(a[:,[0,1,2,12]],b[:,[0,1,2,12]])
  self.assertGreater(float(np.max(np.abs(net.online(a).numpy()-net.online(b).numpy()))),1e-7)
  for x,y in zip(before,net.online.get_weights()):np.testing.assert_array_equal(x,y)
  self.assertEqual(net.training_steps,0);self.assertEqual(int(net.online.optimizer.iterations),0)
 def test_future_stale_and_invalid_mask_rejected(self):
  t,p,_,m,b,_,pairs=fixture();o,d=pairs[0]
  for stamp in [t-pd.Timedelta(minutes=30),t+pd.Timedelta(minutes=30)]:
   x=b(p);x.routing=UTCSnapshot(stamp,stamp,dict(enumerate(p)),stamp)
   with self.assertRaises(ValueError):x.build(o,d,t)
  bad=p.copy();bad[o,0]=-1
  with self.assertRaises(ValueError):b(bad).build(o,d,t)
 def test_live_feedback_branch_no_utility_replacement(self):
  t,p,_,m,b,_,pairs=fixture();calls=[]
  def predict(vectors,masks,when):calls.append(when);return dict(enumerate(p))
  e=NS(timestamp=t,utc_inputs={'popularity':{g:0 for g in range(142)},'popularity_available_at':t},routing=None,operational=None,passengers={},ledger=b(p).ledger,driver_hierarchy=NS(mode='FRESH_UNTRAINED_GLOBAL',mean_probabilities=predict))
  with patch('src.simulation.utc_od_inputs.forecast',return_value=b(p).forecast),patch('src.simulation.utc_od_inputs.RoutingState.from_producer',side_effect=lambda r,op,t,g:NS(values=np.zeros(169),mask=m[g])),patch('src.routing.research_feedback.decision',side_effect=AssertionError('Utility replacement')):
   out=state_sources(e)
  self.assertEqual(calls,[t])
  for o,d in pairs:np.testing.assert_array_equal(out.build(o,d,t)[3:12],p[o])
 def test_saved_real_run_versions_and_private_actions(self):
  v=json.loads((P/'validation.json').read_text());self.assertEqual(v['federation_rounds'],4);self.assertEqual(v['local_updates'],19342);self.assertTrue(v['independent_repeat_exact']);self.assertTrue(v['checkpoint_resume_exact']);self.assertTrue(v['control_outcome_differences_zero']);self.assertTrue(all(x>0 for x in v['control_probability_mean_abs_difference']))

if __name__=='__main__':unittest.main()
