import unittest,json
from pathlib import Path
import numpy as np,pandas as pd
from src.pricing.dqn_contract import *
from src.rl.pricing_dqn import action_index
from tests.test_pricing_dqn_contract import fixture

class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.root=Path('results/analysis/2026-10-21_pricing_dqn_simulator_integration')
  cls.trace=pd.read_csv(cls.root/'integration_trace.csv');cls.requests=pd.read_csv(cls.root/'acceptance_dispatch_trace.csv');cls.reward=pd.read_csv(cls.root/'reward_reconciliation.csv')
 def test_states_and_lags(self):
  states=pd.read_csv(self.root/'state_vectors.csv')
  self.assertEqual(len(states),48);self.assertTrue(np.isfinite(states[list(FEATURES)]).all().all())
  self.assertTrue(np.allclose(states[list(FEATURES)[3:12]].sum(axis=1),1))
  for _,rows in self.trace.groupby(['mode','origin_grid']):
   rows=rows.sort_values('timestamp');np.testing.assert_equal(rows.J_disp_prev.to_numpy()[1:],rows.successful_dispatch_count.to_numpy()[:-1])
 def test_forced_outcomes(self):
  f=self.requests.query("mode == 'forced_3'")
  self.assertTrue((f.accepted & f.assigned).any());self.assertTrue((f.accepted & ~f.assigned).any());self.assertTrue((~f.accepted).any())
  self.assertFalse((~f.accepted & f.assigned).any())
  np.testing.assert_array_equal(f.accepted.to_numpy(),(f.P_disp<=f.threshold).to_numpy())
  self.assertTrue((f.P_disp==f.threshold).any())
 def test_fares_rewards(self):
  self.assertTrue(np.allclose(self.trace.P_disp,self.trace.P_base*self.trace.pricing_factor))
  self.assertTrue((self.reward.difference==0).all())
  self.assertAlmostEqual(self.requests.reward.sum(),self.reward.ledger_reward.sum())
  self.assertAlmostEqual(self.trace.reward.sum(),self.reward.ledger_reward.sum())
  self.assertTrue((self.requests.loc[~self.requests.assigned,'reward']==0).all())
 def test_vehicle_assignment_conservation(self):
  assigned=self.requests[self.requests.assigned]
  self.assertFalse(assigned.duplicated(['mode','timestamp','assigned_vehicle']).any())
  f=json.loads((self.root/'fleet_conservation.json').read_text());self.assertTrue(f['all_checks_passed'])
  for r in f['mini_slot_checks']:self.assertEqual(r['idle']+r['busy'],3)
  self.assertGreater(self.trace.incoming.sum(),0)
 def test_replay_terminal_and_protection(self):
  v=json.loads((self.root/'state_validation.json').read_text());self.assertEqual(v['replay_transitions'],24);self.assertEqual(v['terminal_transitions'],6)
  self.assertTrue(v['terminal_targets_verified']);self.assertTrue(v['checkpoint_hashes_unchanged']);self.assertEqual(v['optimizer_updates'],0)
  for _,r in self.trace.groupby('mode'):np.testing.assert_equal(r.replay_size,np.arange(1,13));self.assertEqual(r.done.sum(),3)
 def test_fail_closed_missing_sources(self):
  t,b,_=fixture()
  for k in range(6):
   args=[b.forecast,b.ledger,b.commitments,b.routing,b.popularity,b.action_masks];args[k]=None
   with self.assertRaises(ValueError):PricingStateBuilder(*args)
  for k in ('forecast','routing','popularity'):
   t,b,_=fixture();setattr(b,k,Snapshot(t,t,{},t))
   with self.assertRaises(ValueError):b.build(0,1,t)
  with self.assertRaises(ValueError):threshold_acceptance(float('nan'),3,3,2,1)
  with self.assertRaises(ValueError):action_index(7)
if __name__=='__main__':unittest.main()
