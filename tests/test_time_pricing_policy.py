import unittest
from src.pricing.time_policy import TimePricingPolicy
from src.simulation.pricing_dispatch import run_pricing_dispatch_slot

class TimePricingTests(unittest.TestCase):
    def test_identity(self):
        for hour in range(24):
            for mode in ['BASELINE', 'EXPERIMENT_A']:
                self.assertEqual(TimePricingPolicy(mode).apply(1.15, hour), 1.15)

    def test_boundaries(self):
        for hour, expected in [(0,.95),(7,.95),(8,1.1),(19,1.1),(20,.95),(23,.95)]:
            self.assertEqual(TimePricingPolicy('TIME_OF_DAY',1.1,.95).apply(1.,hour),expected)

    def test_invalid_config(self):
        for value in [0,-1,float('nan'),float('inf'),True]:
            with self.assertRaises(ValueError):
                TimePricingPolicy('TIME_OF_DAY',value)
        with self.assertRaises(ValueError):
            TimePricingPolicy.from_config({'unknown': 1})
        with self.assertRaises(ValueError):
            TimePricingPolicy('BASELINE',1.1)

    def test_control_guard_before_state_mutation(self):
        policy=TimePricingPolicy.from_config({'mode':'EXPERIMENT_A'})
        with self.assertRaisesRegex(RuntimeError,'signed Record-029'):
            run_pricing_dispatch_slot([],{},None,None,{},2,15,None,time_pricing_policy=policy)
        TimePricingPolicy().require_runtime_support()
