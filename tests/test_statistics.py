"""Focused synthetic NB9 fare/wait aggregation and EWMA tests."""

from __future__ import annotations

import unittest

from src.dispatch.request import RequestState, RequestStatus
from src.dispatch.dispatch import DriverWaitObservation
from src.simulation.statistics import FareObservation, OperationalStatistics, routing_feature_frame


def assigned(request_id: int, grid_id: int, wait: int) -> RequestState:
    return RequestState(request_id, 0, grid_id, grid_id, RequestStatus.ASSIGNED, request_id, wait)


def waits(grid_id: int, *values: float) -> list[DriverWaitObservation]:
    return [DriverWaitObservation(index, grid_id, value) for index, value in enumerate(values)]


class OperationalStatisticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = OperationalStatistics([10, 20, 30], 0.30)

    def by_grid(self, records):
        return {record.grid_id: record for record in records}

    def test_fare_and_wait_means_population_stds_and_separate_counts(self) -> None:
        records = self.by_grid(self.engine.update_slot(
            0,
            [FareObservation(10, 100), FareObservation(10, 120), FareObservation(10, 140)],
            driver_wait_observations=waits(10, 2, 6, 8, 4, 10),
        ))
        row = records[10]
        self.assertEqual((row.fare_count, row.wait_count), (3, 5))
        self.assertAlmostEqual(row.mean_fare, 120.0)
        self.assertAlmostEqual(row.std_fare, (800 / 3) ** 0.5)
        self.assertAlmostEqual(row.mean_wait, 6.0)
        self.assertAlmostEqual(row.std_wait, (40 / 5) ** 0.5)
        self.assertAlmostEqual(row.ewma_std_fare, row.std_fare)
        self.assertAlmostEqual(row.ewma_std_wait, row.std_wait)

    def test_only_successful_fares_and_assigned_waits_are_included(self) -> None:
        unserved = RequestState(1, 0, 10, 10, RequestStatus.UNSERVED)
        row = self.by_grid(self.engine.update_slot(0, [FareObservation(10, 10), FareObservation(10, 999, successful=False)], [assigned(0, 10, 3), unserved], driver_wait_observations=waits(10, 3)))[10]
        self.assertEqual((row.fare_count, row.mean_fare, row.wait_count, row.mean_wait), (1, 10.0, 1, 3.0))

    def test_first_observation_and_exact_incremental_ewma_formula(self) -> None:
        first = self.by_grid(self.engine.update_slot(0, [FareObservation(10, 100)], driver_wait_observations=waits(10, 2)))[10]
        second = self.by_grid(self.engine.update_slot(1, [FareObservation(10, 200)], driver_wait_observations=waits(10, 12)))[10]
        self.assertEqual((first.ewma_fare, first.ewma_wait), (100.0, 2.0))
        self.assertAlmostEqual(second.ewma_fare, 0.3 * 200 + 0.7 * 100)
        self.assertAlmostEqual(second.ewma_wait, 0.3 * 12 + 0.7 * 2)

    def test_configured_alpha_changes_result_and_invalid_alpha_rejected(self) -> None:
        fast = OperationalStatistics([10], 1.0)
        fast.update_slot(0, [FareObservation(10, 100)])
        row = fast.update_slot(1, [FareObservation(10, 200)])[0]
        self.assertEqual(row.ewma_fare, 200.0)
        with self.assertRaisesRegex(ValueError, "ewma_alpha"):
            OperationalStatistics([10], 0)
        with self.assertRaisesRegex(ValueError, "ewma_alpha"):
            OperationalStatistics([10], 1.1)

    def test_no_observation_carries_existing_ewma_and_never_observed_remains_missing(self) -> None:
        self.engine.update_slot(0, [FareObservation(10, 100)], driver_wait_observations=waits(10, 3))
        rows = self.by_grid(self.engine.update_slot(1))
        self.assertEqual((rows[10].fare_count, rows[10].mean_fare, rows[10].ewma_fare), (0, None, 100.0))
        self.assertEqual((rows[20].ewma_fare, rows[20].ewma_wait), (None, None))

    def test_multiple_grids_are_independent_and_deterministic(self) -> None:
        one = OperationalStatistics([10, 20], 0.3).update_slot(0, [FareObservation(10, 100), FareObservation(20, 200)])
        two = OperationalStatistics([10, 20], 0.3).update_slot(0, [FareObservation(10, 100), FareObservation(20, 200)])
        self.assertEqual(one, two)
        rows = self.by_grid(one)
        self.assertEqual((rows[10].ewma_fare, rows[20].ewma_fare), (100.0, 200.0))

    def test_charging_missing_and_routing_feature_export(self) -> None:
        records = self.engine.update_slot(0, [FareObservation(10, 100)], [assigned(0, 10, 0)])
        self.assertTrue(all(row.charging_available is None and row.charging_wait is None for row in records))
        features = routing_feature_frame(records)
        self.assertEqual(features.columns.tolist(), ["grid_id", "slot_id", "mean_fare", "std_fare", "ewma_fare", "ewma_std_fare", "mean_wait", "std_wait", "ewma_wait", "ewma_std_wait", "charging_available", "charging_wait"])
        self.assertEqual(len(features), 3)

    def test_invalid_grid_and_negative_observations_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid GridID"):
            self.engine.update_slot(0, [FareObservation(99, 1)])
        with self.assertRaisesRegex(ValueError, "non-negative"):
            self.engine.update_slot(0, [FareObservation(10, -1)])


if __name__ == "__main__":
    unittest.main()
