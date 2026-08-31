"""Leakage-safe provenance checks for the persisted pricing scaler."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.fleet.fleet import initialize_fleet
from src.fleet.supply import aggregate_grid_supply
from src.pricing.scaler import PricingContextScaler


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
        supply = aggregate_grid_supply(vehicles, grids)["supply_total"].to_numpy(dtype=np.float64)
        self.assertEqual(float(np.percentile(supply, 99)), self.metadata["supply_ref_p99"])
        self.assertEqual(len(supply), reference["valid_grid_count"])

    def test_metadata_round_trip_is_deterministic(self) -> None:
        scaler = PricingContextScaler.load(ROOT / "config/pricing_context_scaler.json")
        self.assertEqual((scaler.demand_ref_p99, scaler.supply_ref_p99), (45.085255432128896, 9.))
        self.assertEqual(self.metadata["methodology_version"], "pricing_context_scaling_v1")

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
