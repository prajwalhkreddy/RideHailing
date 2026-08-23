"""Focused synthetic tests for the frozen legacy NB5 CNN contract."""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

import numpy as np

from src.demand.inference import load_predictor, predict_demand
from src.demand.model import (
    build_model, channels_first_to_last, compute_normalization,
    evaluate_predictions, load_normalization, normalize_features,
    save_normalization,
)
from src.demand.tensors import CNN_CHANNELS


class CNNModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.x_train = np.arange(4 * 7 * 2 * 3, dtype=np.float32).reshape(4, 7, 2, 3)
        self.x_test = np.full((2, 7, 2, 3), 1000, dtype=np.float32)

    def test_channels_first_to_channels_last(self) -> None:
        converted = channels_first_to_last(self.x_train)
        self.assertEqual(converted.shape, (4, 2, 3, 7))
        self.assertEqual(converted[2, 1, 2, 5], self.x_train[2, 5, 1, 2])
        targets = np.ones((4, 1, 2, 3), dtype=np.float32)
        self.assertEqual(channels_first_to_last(targets, target=True).shape, (4, 2, 3, 1))

    def test_normalization_is_fitted_on_train_only_and_does_not_touch_y(self) -> None:
        normalization = compute_normalization(self.x_train)
        self.assertEqual(normalization["channels"], CNN_CHANNELS)
        expected_mean = self.x_train[:, 0].mean()
        self.assertAlmostEqual(float(normalization["means"][0]), float(expected_mean), places=5)
        normalized_test = normalize_features(self.x_test, normalization)
        self.assertNotAlmostEqual(float(normalized_test[:, 0].mean()), 0.0, places=3)
        zero_channel = self.x_train.copy()
        zero_channel[:, 6] = 0
        self.assertEqual(float(compute_normalization(zero_channel)["stds"][6]), 1.0)

    def test_normalization_persistence(self) -> None:
        normalization = compute_normalization(self.x_train)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "normalization.pkl"
            save_normalization(path, normalization)
            loaded = load_normalization(path)
        np.testing.assert_array_equal(loaded["means"], normalization["means"])
        np.testing.assert_array_equal(loaded["stds"], normalization["stds"])
        self.assertEqual(loaded["channels"], CNN_CHANNELS)

    def test_model_shape_reload_and_inference_contract(self) -> None:
        model = build_model(2, 3)
        self.assertEqual(model.input_shape, (None, 2, 3, 7))
        self.assertEqual(model.output_shape, (None, 2, 3, 1))
        self.assertEqual(model.count_params(), 39041)
        normalization = compute_normalization(self.x_train)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "cnn_model.keras"
            normalization_path = root / "normalization.pkl"
            model.save(model_path)
            save_normalization(normalization_path, normalization)
            loaded_model, loaded_normalization = load_predictor(model_path, normalization_path)
            prediction = predict_demand(self.x_test[:1], loaded_model, loaded_normalization)
        self.assertEqual(prediction.shape, (1, 2, 3, 1))
        with self.assertRaises(ValueError):
            predict_demand(np.zeros((1, 6, 2, 3), dtype=np.float32), model, normalization)

    def test_positive_demand_mape_filtering(self) -> None:
        actual = np.array([[[[0.0], [2.0]]]], dtype=np.float32)
        estimated = np.array([[[[100.0], [1.0]]]], dtype=np.float32)
        metrics = evaluate_predictions(actual, estimated).set_index("Metric")["Value"]
        self.assertAlmostEqual(float(metrics["MAPE (%)"]), 50.0, places=5)
        self.assertAlmostEqual(float(metrics["MAE"]), 50.5, places=5)


if __name__ == "__main__":
    unittest.main()
