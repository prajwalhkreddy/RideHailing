"""Leakage-safe provenance checks for the persisted pricing scaler."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.fleet.fleet import initialize_fleet
from src.pricing.scaler import PricingContextScaler, fit_supply_reference_p99
from src.pricing.supply import build_raw_pricing_supply


ROOT = Path(__file__).resolve().parents[1]


class PricingScalerReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (ROOT / "config/pricing_context_scaler.json").open(encoding="utf-8") as handle:
            cls.metadata = json.load(handle)

    def test_demand_reference_is_chronological_training_only_and_artifacts_match(self) -> None:
        reference = self.metadata["demand_reference"]
        self.assertFalse(reference["test_predictions_used_for_fit"])
        self.assertLess(reference["period_start"], reference["period_end_inclusive"])
        self.assertEqual(reference["nonnegative_p99"], self.metadata["demand_ref_p99"])
        for relative, key in (
            ("models/demand/cnn_model.keras", "cnn_model_sha256"),
            ("models/demand/normalization.pkl", "normalization_sha256"),
            ("data/processed/cnn/X_train.npy", "x_train_sha256"),
        ):
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), reference[key])

    def test_frozen_cnn_inference_does_not_change_weights(self) -> None:
        from src.demand.inference import load_predictor, predict_demand

        model, normalization = load_predictor(
            ROOT / "models/demand/cnn_model.keras", ROOT / "models/demand/normalization.pkl",
        )
        before = [weight.numpy().copy() for weight in model.weights]
        features = np.load(ROOT / "data/processed/cnn/X_train.npy", mmap_mode="r")[:1]
        self.assertTrue(np.isfinite(predict_demand(np.asarray(features), model, normalization)).all())
        for old, current in zip(before, model.weights):
            np.testing.assert_array_equal(old, current.numpy())

    def test_supply_reference_reproduces_production_initialization_only(self) -> None:
        reference = self.metadata["supply_reference"]
        grids = pd.read_parquet(ROOT / reference["grid_lookup"])["GridID"].astype(int).tolist()
        vehicles = initialize_fleet(
            reference["fleet_size"], grids, reference["random_seed"], initial_energy_level=60.,
            initialization_method=reference["initialization_method"],
        )
        supply = build_raw_pricing_supply(
            vehicles, grids, datetime.fromisoformat(reference["calibration_observation_time"]),
        )["total_supply"].to_numpy(dtype=np.float64)
        times = np.repeat(np.datetime64(reference["calibration_observation_time"]), len(supply))
        fitted = fit_supply_reference_p99(
            supply, times, reference["training_start_inclusive"], reference["training_end_exclusive"],
        )
        self.assertEqual(fitted, self.metadata["supply_ref_p99"])
        self.assertEqual(len(supply), reference["valid_grid_count"])
        self.assertEqual(reference["supply_semantics"], "idle_plus_incoming")
        self.assertEqual((reference["idle_count"], reference["incoming_count"]), (5000, 0))

    def test_supply_reference_is_p99_training_only_and_held_out_cannot_change_it(self) -> None:
        cutoff = "2026-01-25T18:30:00"
        training = np.array([0., 1., 2., 9., 10.])
        times = np.array(["2026-01-01"] * len(training), dtype="datetime64[ns]")
        baseline = fit_supply_reference_p99(training, times, "2026-01-01", cutoff)
        combined = np.concatenate([[1.e12], training, [1.e12, 1.e12]])
        combined_times = np.concatenate([
            np.array(["2025-12-31"], dtype="datetime64[ns]"), times,
            np.array(["2026-01-26", "2026-01-31"], dtype="datetime64[ns]"),
        ])
        self.assertEqual(fit_supply_reference_p99(combined, combined_times, "2026-01-01", cutoff), baseline)
        self.assertEqual(baseline, float(np.percentile(training, 99)))
        self.assertFalse(self.metadata["supply_reference"]["held_out_observations_used"])

    def test_metadata_round_trip_is_deterministic(self) -> None:
        scaler = PricingContextScaler.load(ROOT / "config/pricing_context_scaler.json")
        self.assertEqual((scaler.demand_ref_p99, scaler.supply_ref_p99), (45.085255432128896, 9.))
        self.assertEqual(self.metadata["methodology_version"], "pricing_context_scaling_v1_1_corrected_supply")
        self.assertEqual(self.metadata["legacy_supply_ref_p99"], 9.)

    def test_fare_reference_is_positive_training_only_and_serialized(self) -> None:
        with (ROOT / "config/pricing_reward.json").open(encoding="utf-8") as handle:
            reward = json.load(handle)
        reference = reward["fare_reference"]
        self.assertEqual(reward["fare_ref_p99"], 73.)
        self.assertGreater(reward["fare_ref_p99"], 0.)
        self.assertTrue(np.isfinite(reward["fare_ref_p99"]))
        self.assertFalse(reference["held_out_fares_used"])
        self.assertEqual(reference["period_end_exclusive"], "2026-01-25T18:30:00")
        self.assertEqual(hashlib.sha256((ROOT / reference["source"]).read_bytes()).hexdigest(), reference["source_sha256"])
        fares = pd.read_parquet(ROOT / reference["source"], columns=[reference["timestamp_column"], reference["fare_column"]])
        training = fares.loc[
            (fares[reference["timestamp_column"]] >= pd.Timestamp(reference["period_start_inclusive"]))
            & (fares[reference["timestamp_column"]] < pd.Timestamp(reference["period_end_exclusive"]))
            & np.isfinite(fares[reference["fare_column"]])
            & (fares[reference["fare_column"]] > 0),
            reference["fare_column"],
        ].to_numpy(dtype=np.float64)
        held_out = fares.loc[
            fares[reference["timestamp_column"]] >= pd.Timestamp(reference["period_end_exclusive"]),
            reference["fare_column"],
        ].to_numpy(dtype=np.float64).copy()
        baseline = float(np.percentile(training, 99))
        held_out[:] = 1.e12
        self.assertEqual(baseline, reward["fare_ref_p99"])
        self.assertEqual(float(np.percentile(training, 99)), baseline)


if __name__ == "__main__":
    unittest.main()
