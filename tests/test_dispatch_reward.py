"""Bounded reward fixtures; no experiment training or historical output writes."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.pricing.dispatch_reward import reconcile_dispatch_rewards, REWARD_VERSION
from src.simulation.dispatch_reward_runtime import DispatchRewardRuntime
from src.simulation.slot_pricing_v3 import SlotPricingV3
from src.rl.dispatch_reward_dqn import DispatchRewardDQN
from src.rl.slot_pricing_v3 import SlotDQN
from src.simulation.v3_checkpoint import save_v3_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.dispatch.request import RequestState


def row(outcome, identity=0, fare=10.):
    return dict(slot='2026-03-12', request_id=identity, destination_context=1,
                accepted=outcome != 'PASSENGER_REJECTED', dispatch_outcome=outcome, P_offer=fare)


class RewardArithmeticTests(unittest.TestCase):
    def test_rejected(self):
        self.assertEqual(reconcile_dispatch_rewards([row('PASSENGER_REJECTED')], [1]), ([0.], {1: 0.}))

    def test_unmatched(self):
        self.assertEqual(reconcile_dispatch_rewards([row('ACCEPTED_BUT_UNMATCHED')], [1])[1], {1: 0.})

    def test_assigned(self):
        self.assertEqual(reconcile_dispatch_rewards([row('ACCEPTED_AND_ASSIGNED')], [1])[1], {1: 10.})

    def test_multiple_and_empty_context(self):
        rows = [row('ACCEPTED_AND_ASSIGNED', 0), row('ACCEPTED_AND_ASSIGNED', 1, 20.)]
        self.assertEqual(reconcile_dispatch_rewards(rows, [1, 2])[1], {1: 30., 2: 0.})

    def test_duplicate_rejected(self):
        r = row('ACCEPTED_AND_ASSIGNED')
        with self.assertRaises(ValueError):
            reconcile_dispatch_rewards([r, r], [1])

    def test_invalid_audit_rejected(self):
        r = row('ACCEPTED_AND_ASSIGNED'); r['accepted'] = False
        with self.assertRaises(ValueError):
            reconcile_dispatch_rewards([r], [1])


class RewardIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtimes = []
        for runtime_type in (SlotPricingV3, DispatchRewardRuntime):
            fleet = Fleet([VehicleState(i, 0, VehicleStatus.IDLE, None, 0, 'idle', 60.) for i in range(2)], frozenset(range(142)), 2)
            profiles = pd.DataFrame(dict(vehicle_id=range(2), price_preference=[0.]*2,
                wait_preference=[10.]*2, charging_wait_preference_minutes=[10.]*2))
            runtime = runtime_type(start='2026-03-12', seed=42, fleet=fleet, driver_profiles=profiles,
                routing_checkpoint='models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras')
            t = runtime.engine.timestamp
            requests = [RequestState(i, 0, 0, 1, base_fare=20., source_trip_id=i,
                empirical_pickup_datetime=t.to_pydatetime(),
                empirical_dropoff_datetime=(t+pd.Timedelta(minutes=150)).to_pydatetime(),
                trip_duration_minutes=150., trip_distance_miles=d/1.609344, trip_distance_km=d)
                for i, d in enumerate([30., 30., 30., .01])]
            runtime.run_slot(requests, policy=lambda d, s: 0, weather_code=1)
            cls.runtimes.append(runtime)
        cls.old, cls.new = cls.runtimes

    def test_all_outcomes_exercised(self):
        self.assertEqual({r['dispatch_outcome'] for r in self.new.audit},
            {'PASSENGER_REJECTED', 'ACCEPTED_BUT_UNMATCHED', 'ACCEPTED_AND_ASSIGNED'})

    def test_replay_matches_assignment_and_request_rewards(self):
        for slot, transition in zip(self.new.slot_audit, self.new.learner.replay):
            self.assertAlmostEqual(transition[2], slot['assignment_revenue'])
            self.assertEqual(transition[2], slot['learning_reward'])
        self.assertAlmostEqual(sum(r['reward_contribution'] for r in self.new.audit), sum(x[2] for x in self.new.learner.replay))
        self.assertTrue(all(r['reward_contribution'] == 0 for r in self.new.audit if r['dispatch_outcome'] != 'ACCEPTED_AND_ASSIGNED'))

    def test_historical_reward_unchanged(self):
        self.assertAlmostEqual(sum(x[2] for x in self.old.learner.replay), sum(r['P_offer'] for r in self.old.audit if r['accepted']))
        self.assertGreater(sum(x[2] for x in self.old.learner.replay), sum(x[2] for x in self.new.learner.replay))

    def test_dispatch_rng_and_states_identical(self):
        fields = ['request_id', 'P_offer', 'epsilon', 'P_max', 'accepted', 'dispatch_outcome']
        self.assertEqual([[r[k] for k in fields] for r in self.old.audit], [[r[k] for k in fields] for r in self.new.audit])
        for name in ['fleet', 'passengers', 'missions', 'request_rng', 'operational', 'ledger']:
            self.assertEqual(encode(getattr(self.old.engine, name)), encode(getattr(self.new.engine, name)))
        self.assertEqual(encode(self.old.provider.rng), encode(self.new.provider.rng))
        for a, b in zip(self.old.learner.replay, self.new.learner.replay):
            np.testing.assert_array_equal(a[0], b[0]); np.testing.assert_array_equal(a[3], b[3])
            self.assertEqual((a[1], a[4]), (b[1], b[4]))
        self.assertEqual(self.new.learner.training_steps, 0)

    def test_checkpoint_version_roundtrip_and_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            new_path, old_path = Path(tmp)/'new', Path(tmp)/'old'
            self.new.learner.save(new_path); self.old.learner.save(old_path)
            loaded = DispatchRewardDQN.load(new_path)
            self.assertEqual([t[2] for t in loaded.replay], [t[2] for t in self.new.learner.replay])
            self.assertEqual(json.loads((new_path/'checkpoint.json').read_text())['reward_contract'], REWARD_VERSION)
            with self.assertRaises(ValueError): DispatchRewardDQN.load(old_path)
            with self.assertRaises(ValueError): SlotDQN.load(new_path)
            self.assertEqual(len(SlotDQN.load(old_path).replay), 142)

    def test_historical_full_runtime_save_rejected_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'checkpoint'
            with self.assertRaises(ValueError): save_v3_checkpoint(self.new, path)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
