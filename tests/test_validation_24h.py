"""Focused tests for generic N-slot and 24-hour validation health checks."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.pricing.linucb import PRICING_FACTORS
from src.popularity.destination import POPULARITY_ENCODING
from src.simulation.validation_24h import run_small_fleet_validation


ROOT = Path(__file__).resolve().parents[1]


class Validation24hTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_small_fleet_validation(8, seed=42)

    def test_generic_n_slot_driver_timestamps_state_and_accounting(self) -> None:
        slots = self.report.result.slots
        self.assertEqual(len(slots), 8)
        self.assertEqual([slot.timestamp for slot in slots], [self.report.result.start_time + timedelta(minutes=30 * i) for i in range(8)])
        self.assertEqual(self.report.result.end_time, self.report.result.start_time + timedelta(hours=4))
        self.assertEqual([slot.pricing_updates_before for slot in slots], list(range(0, 32, 4)))
        self.assertEqual([slot.pricing_updates_after for slot in slots], list(range(4, 36, 4)))
        self.assertTrue(all(slot.generated == slot.accepted + slot.rejected for slot in slots))
        self.assertTrue(all(slot.accepted == slot.served + slot.accepted_but_unserved for slot in slots))
        self.assertTrue(all(sum(slot.fleet_counts.values()) == 50 for slot in slots))

    def test_energy_bounds_charging_integrity_and_no_nonfinite_values(self) -> None:
        self.assertTrue(self.report.passed)
        self.assertAlmostEqual(self.report.energy_accounting_error_kwh, 0., places=8)
        self.assertEqual((self.report.nan_count, self.report.energy_bound_failures, self.report.probability_failures), (0, 0, 0))
        self.assertTrue(all(slot.charging_capacity_valid and slot.queue_membership_valid for slot in self.report.result.slots))
        self.assertTrue(all(0 <= slot.minimum_energy_kwh <= slot.maximum_energy_kwh <= 75 for slot in self.report.result.slots))
        self.assertEqual(self.report.scaling_clip_counts["contexts"], 8 * 4)
        self.assertTrue(all(item["finite"] for item in self.report.linucb_conditioning.values()))

    def test_pricing_routing_policy_learning_and_federation_stability(self) -> None:
        slots = self.report.result.slots
        self.assertTrue(all(factor in PRICING_FACTORS for slot in slots for factor in slot.pricing_factors.values()))
        self.assertTrue(all(slot.routing_decisions_valid for slot in slots))
        self.assertTrue(all(np.isclose(policy.probabilities.sum(), 1.) for slot in slots for policy in slot.grid_policy.values()))
        self.assertEqual([slot.federation_requested for slot in slots], [False, False, False, True, False, False, False, True])
        self.assertTrue(all(slot.learners_trained >= 0 and slot.local_observations >= 0 for slot in slots))
        self.assertTrue(set(self.report.grid_policy_source_counts) <= {"current_vehicle_mean", "carry_forward", "initialization"})
        self.assertTrue(all(set(slot.pricing_popularity.values()).issubset(set(POPULARITY_ENCODING.values())) for slot in slots))
        self.assertFalse(self.report.popularity_table[["popularity_level", "popularity_value"]].isna().any().any())
        self.assertEqual(self.report.cold_start_assignments, PRICING_FACTORS)
        self.assertEqual(self.report.normal_selection_begins_at, 9)
        self.assertTrue(all(value is not None and 0 <= value <= 1 for value in self.report.cold_start_rewards))
        self.assertEqual(self.report.reward_clip_count, 0)
        self.assertTrue(all(item["update_count"] >= 1 for item in self.report.linucb_conditioning.values()))

    def test_short_replay_is_deterministic_without_future_outcome_input(self) -> None:
        first = run_small_fleet_validation(2, seed=9)
        second = run_small_fleet_validation(2, seed=9)
        self.assertEqual(first.trajectory_signature, second.trajectory_signature)
        self.assertEqual(first.summary_table[["generated", "accepted", "served"]].to_dict("records"), second.summary_table[["generated", "accepted", "served"]].to_dict("records"))

    def test_generated_24h_summary_has_48_finite_consecutive_rows(self) -> None:
        path = ROOT / "results/tables/validation_24h_summary.csv"
        factors = ROOT / "results/tables/validation_24h_pricing_factors.csv"
        self.assertTrue(path.is_file() and factors.is_file())
        frame = pd.read_csv(path, parse_dates=["timestamp"])
        self.assertEqual(len(frame), 48)
        self.assertEqual(frame.slot_index.tolist(), list(range(48)))
        self.assertTrue((frame.timestamp.diff().dropna() == pd.Timedelta(minutes=30)).all())
        self.assertFalse(frame.select_dtypes(include=[np.number]).isna().any().any())
        self.assertTrue((frame[["generated", "accepted", "rejected", "served", "idle", "busy", "charging"]] >= 0).all().all())


if __name__ == "__main__":
    unittest.main()
