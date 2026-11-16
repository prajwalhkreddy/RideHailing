import unittest
import numpy as np
from src.simulation.pricing_version import (V3, LEGACY, CURRENT_ROUTING,
    HISTORICAL_ROUTING, validate_probabilities)
from src.pricing.slot_v3 import validate_state
from src.pricing.state import build_pricing_context

class PricingVersionTests(unittest.TestCase):
    def test_current_diagonals_unchanged(self):
        p=np.array([.1,.1,.2,.1,.1,.1,.1,.1,.1])
        q=validate_probabilities(p,pricing_version=V3,routing_action_version=CURRENT_ROUTING)
        np.testing.assert_array_equal(p,q)
        s=validate_state([1,1,0,0,*q,.1,.25])
        np.testing.assert_allclose(s[4:13],p,rtol=1e-7)
        self.assertEqual(s.shape,(15,))
    def test_stay_action(self):
        from src.rl.slot_pricing_v3 import SlotDQN
        p=validate_probabilities([1,0,0,0,0,0,0,0,0],pricing_version=V3,routing_action_version=CURRENT_ROUTING)
        s=validate_state([1,1,0,0,*p,.1,.25])
        self.assertIn(SlotDQN(42).select_action(s),range(7))
    def test_legacy_still_accepts_historical_fixture(self):
        p=validate_probabilities([1,0,0,0,0],pricing_version=LEGACY,routing_action_version=HISTORICAL_ROUTING)
        self.assertEqual(build_pricing_context(10,1,p,.5).shape,(8,))
    def test_mismatches(self):
        for version,route,n in [(V3,CURRENT_ROUTING,5),(LEGACY,HISTORICAL_ROUTING,9),(V3,HISTORICAL_ROUTING,9),(LEGACY,CURRENT_ROUTING,5)]:
            with self.subTest(version=version,route=route,n=n):
                with self.assertRaises(ValueError):validate_probabilities([1]+[0]*(n-1),pricing_version=version,routing_action_version=route)
    def test_legacy_execution_explicitly_unavailable(self):
        from src.simulation.main_slot import run_main_slot
        from src.simulation.multi_slot import run_multi_slot_simulation
        for runner in [run_main_slot,run_multi_slot_simulation]:
            with self.assertRaisesRegex(ValueError,'LEGACY_INTERFACE_NOT_EXECUTABLE'):
                runner(pricing_version=LEGACY)
