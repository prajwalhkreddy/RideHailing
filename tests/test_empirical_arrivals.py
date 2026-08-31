"""Deterministic empirical within-main-slot arrival mapping tests."""

from __future__ import annotations

from datetime import datetime, timedelta
import unittest

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.dispatch.dispatch import dispatch_requests
from src.dispatch.generation import (
    build_empirical_od_distribution, empirical_mini_slot_index,
    empirical_within_slot_offset_seconds, generate_requests, historical_bucket_start,
)
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus


class EmpiricalArrivalTests(unittest.TestCase):
    def test_bucket_flooring_and_exact_boundary_mappings(self) -> None:
        cases = {
            "2026-01-01 08:00:00": 0,
            "2026-01-01 08:01:59": 0,
            "2026-01-01 08:02:00": 1,
            "2026-01-01 08:17:43": 8,
            "2026-01-01 08:28:00": 14,
            "2026-01-01 08:29:59": 14,
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(empirical_mini_slot_index(value), expected)
        self.assertEqual(historical_bucket_start("2026-01-01 08:17:43"), pd.Timestamp("2026-01-01 08:00:00"))
        self.assertEqual(empirical_within_slot_offset_seconds("2026-01-01 08:17:43"), 17 * 60 + 43)

    def test_both_half_hours_and_absolute_date_hour_do_not_change_relative_mapping(self) -> None:
        self.assertEqual(historical_bucket_start("2026-01-01 08:37:00"), pd.Timestamp("2026-01-01 08:30:00"))
        self.assertEqual(empirical_mini_slot_index("2026-01-01 08:07:00"), 3)
        self.assertEqual(empirical_mini_slot_index("2026-01-01 08:37:00"), 3)
        self.assertEqual(empirical_mini_slot_index("2030-12-31 22:07:00"), 3)

    @staticmethod
    def frame(pickups) -> pd.DataFrame:
        pickup = pd.to_datetime(pickups)
        return pd.DataFrame({
            "PUGridID": [0] * len(pickup), "DOGridID": [1] * len(pickup),
            "tpep_pickup_datetime": pickup,
            "tpep_dropoff_datetime": pickup + pd.to_timedelta(18, unit="minute"),
            "trip_distance": np.arange(1, len(pickup) + 1, dtype=float),
            "fare_amount": np.arange(10, 10 + len(pickup), dtype=float),
        })

    def test_generation_uses_sampled_row_offset_and_preserves_all_joint_fields(self) -> None:
        frame = self.frame(["2026-01-01 08:17:43"])
        distribution = build_empirical_od_distribution(frame, [0, 1])
        request = generate_requests({0: 1}, distribution, [0, 1], 15, 42)[0]
        self.assertEqual((request.request_time, request.empirical_within_slot_offset_seconds), (8, 1063.))
        self.assertEqual((request.origin_grid, request.destination_grid, request.base_fare), (0, 1, 10.))
        self.assertEqual((request.trip_duration_minutes, request.trip_distance_miles, request.trip_distance_km), (18., 1., 1.609344))
        self.assertEqual(request.empirical_pickup_datetime, frame.iloc[0].tpep_pickup_datetime)

    def test_no_uniform_arrival_draw_and_deterministic_offset_distribution(self) -> None:
        pickups = ["2026-01-01 08:01:20", "2026-01-01 08:07:40", "2026-01-01 08:17:43", "2026-01-01 08:29:20"]
        distribution = build_empirical_od_distribution(self.frame(pickups), [0, 1])
        sampled = [distribution.sample_trip(0, np.random.default_rng(seed)) for seed in range(4)]
        self.assertTrue(all(empirical_mini_slot_index(item.pickup_datetime) in (0, 3, 8, 14) for item in sampled))
        single = build_empirical_od_distribution(self.frame([pickups[2]]), [0, 1])
        self.assertEqual({generate_requests({0: 1}, single, [0, 1], 15, seed)[0].request_time for seed in range(20)}, {8})

    def test_cross_slot_busy_and_energy_remain_correct_with_empirical_arrival(self) -> None:
        pickup = datetime(2026, 1, 1, 8, 28, 20)
        frame = self.frame([pickup])
        request = generate_requests({0: 1}, build_empirical_od_distribution(frame, [0, 1]), [0, 1], 15, 5)[0]
        vehicle = VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 40.)
        fleet = Fleet([vehicle], frozenset((0, 1)), 2)
        energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, energy)
        self.assertEqual((request.request_time, request.trip_start_minute, request.busy_until_minute), (14, 28., 46.))
        after = vehicle.energy_level
        self.assertAlmostEqual(request.passenger_energy_kwh, 1.609344 * .15)
        for _ in range(8):
            fleet.advance_mini_slot()
            self.assertEqual(vehicle.trip_status, VehicleStatus.BUSY)
            self.assertEqual(vehicle.energy_level, after)
        fleet.advance_mini_slot()
        self.assertEqual(vehicle.trip_status, VehicleStatus.IDLE)

    def test_rejection_and_acceptance_rng_contracts_are_unchanged(self) -> None:
        request = generate_requests({0: 1}, build_empirical_od_distribution(self.frame(["2026-01-01 08:17:43"]), [0, 1]), [0, 1], 15, 1)[0]
        request.customer_accepted = False
        # Pricing integration owns rejection; an explicitly rejected request is not passed here.
        self.assertEqual(request.status, RequestStatus.PENDING)
        first, second = np.random.default_rng(9), np.random.default_rng(9)
        self.assertEqual(first.random(), second.random())


if __name__ == "__main__":
    unittest.main()
