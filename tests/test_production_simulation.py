"""Focused contracts for the authoritative production assembler."""

from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.dispatch.generation import build_empirical_od_distribution, generate_requests
from src.routing.production import sha256_file
from src.simulation.production import EXPECTED_GRID_COUNT, EXPECTED_HASHES, PRODUCTION_END_EXCLUSIVE, PRODUCTION_SLOT_COUNT, PRODUCTION_START, ProductionExperiment


ROOT = Path(__file__).resolve().parents[1]


class ProductionSimulationTests(unittest.TestCase):
    def test_frozen_artifacts_and_first_eight_predictions_exist(self) -> None:
        experiment = ProductionExperiment.__new__(ProductionExperiment)
        experiment.root = ROOT
        paths = experiment._paths()
        for name, expected in EXPECTED_HASHES.items():
            self.assertTrue(paths[name].is_file())
            self.assertEqual(sha256_file(paths[name]), expected)
        grid = pd.read_parquet(paths["grid"], columns=["GridID"])
        self.assertEqual((len(grid), grid.GridID.nunique()), (EXPECTED_GRID_COUNT, EXPECTED_GRID_COUNT))
        times = pd.DatetimeIndex(np.load(paths["cnn_times"]))
        targets = times + pd.Timedelta(minutes=30)
        required = pd.date_range(PRODUCTION_START, periods=9, freq="30min")
        self.assertTrue(required.isin(targets).all())
        self.assertEqual((len(targets), targets[0], targets[-1]), (PRODUCTION_SLOT_COUNT, pd.Timestamp("2026-01-25 19:00"), pd.Timestamp("2026-01-31 23:30")))
        self.assertTrue(targets.is_unique and targets.is_monotonic_increasing)
        self.assertNotIn(pd.Timestamp("2026-01-25 18:30"), targets)
        self.assertNotIn(pd.Timestamp(PRODUCTION_END_EXCLUSIVE), targets)

    def test_persistent_request_rng_advances_and_is_reproducible(self) -> None:
        trips = pd.DataFrame({
            "PUGridID": [0, 0], "DOGridID": [0, 1],
            "tpep_pickup_datetime": pd.to_datetime(["2026-01-01 00:01", "2026-01-01 00:11"]),
            "tpep_dropoff_datetime": pd.to_datetime(["2026-01-01 00:06", "2026-01-01 00:21"]),
            "trip_distance": [1., 2.], "fare_amount": [10., 20.],
        })
        distribution = build_empirical_od_distribution(trips, [0, 1])

        def trajectory(seed: int):
            rng = np.random.default_rng(seed)
            first = generate_requests({0: 8, 1: 0}, distribution, [0, 1], 15, None, rng=rng)
            state_after_first = repr(rng.bit_generator.state)
            second = generate_requests({0: 8, 1: 0}, distribution, [0, 1], 15, None, 8, rng=rng)
            return ([item.source_trip_id for item in first], [item.source_trip_id for item in second], state_after_first, repr(rng.bit_generator.state))

        first = trajectory(42)
        self.assertEqual(first, trajectory(42))
        self.assertNotEqual(first[:2], trajectory(43)[:2])
        self.assertNotEqual(first[2], first[3])
        self.assertNotEqual(first[0], first[1])

    def test_request_rng_rejects_simultaneous_seed_reset(self) -> None:
        trips = pd.DataFrame({
            "PUGridID": [0], "DOGridID": [0],
            "tpep_pickup_datetime": pd.to_datetime(["2026-01-01 00:01"]),
            "tpep_dropoff_datetime": pd.to_datetime(["2026-01-01 00:06"]),
            "trip_distance": [1.], "fare_amount": [10.],
        })
        distribution = build_empirical_od_distribution(trips, [0])
        with self.assertRaisesRegex(ValueError, "either random_seed or a persistent rng"):
            generate_requests({0: 1}, distribution, [0], 15, 42, rng=np.random.default_rng(42))

    def test_popularity_artifact_is_unique_current_slot_destination_state(self) -> None:
        popularity = pd.read_parquet(ROOT / "data/processed/destination_popularity_2026_01.parquet")
        self.assertFalse(popularity.duplicated(["TimeSlot", "GridID"]).any())
        rows = popularity.loc[pd.to_datetime(popularity.TimeSlot) == pd.Timestamp(PRODUCTION_START)]
        self.assertEqual((len(rows), rows.GridID.nunique()), (EXPECTED_GRID_COUNT, EXPECTED_GRID_COUNT))
        self.assertTrue(set(rows.popularity_value).issubset({0., .25, .5, .75, 1.}))

    def test_prediction_indices_map_input_to_next_slot_target(self) -> None:
        inputs = pd.DatetimeIndex(np.load(ROOT / "data/processed/cnn/time_test.npy"))
        targets = inputs + pd.Timedelta(minutes=30)
        self.assertEqual((inputs[0], targets[0]), (pd.Timestamp("2026-01-25 18:30"), pd.Timestamp("2026-01-25 19:00")))
        self.assertEqual((inputs[297], targets[297]), (pd.Timestamp("2026-01-31 23:00"), pd.Timestamp("2026-01-31 23:30")))
        self.assertEqual(targets.get_loc(pd.Timestamp("2026-01-25 19:00")), 0)
        self.assertEqual(targets.get_loc(pd.Timestamp("2026-01-31 23:30")), 297)


if __name__ == "__main__":
    unittest.main()
