"""Reloadable NB5 demand-CNN inference interface for future consumers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf

from src.demand.model import load_normalization, normalize_features
from src.demand.tensors import CNN_CHANNELS


def load_predictor(model_path: str | Path, normalization_path: str | Path) -> tuple[tf.keras.Model, dict[str, Any]]:
    """Load the frozen CNN and its training-only normalization parameters."""
    model = tf.keras.models.load_model(model_path)
    normalization = load_normalization(normalization_path)
    return model, normalization


def predict_demand(features: np.ndarray, model: tf.keras.Model, normalization: dict[str, Any]) -> np.ndarray:
    """Predict raw-demand maps from seven-channel NB4-style spatial inputs.

    ``features`` may be a single ``(7, rows, cols)`` map or a batch in legacy
    channels-first ``(samples, 7, rows, cols)`` storage order.  The returned
    maps use TensorFlow's ``(samples, rows, cols, 1)`` order, matching NB5.
    Padded cells are not masked because the reference baseline evaluates the
    complete padded grid.
    """
    values = np.asarray(features)
    if values.ndim == 3:
        values = values[None, ...]
    if values.ndim != 4 or values.shape[1] != len(CNN_CHANNELS):
        raise ValueError("Inference requires (samples, 7, rows, columns) NB4 features.")
    expected = tuple(model.input_shape[1:])
    if tuple(values.shape[2:]) != expected[:2] or expected[2] != len(CNN_CHANNELS):
        raise ValueError("Feature grid dimensions or channel order are incompatible with the frozen model.")
    normalized = normalize_features(values, normalization)
    prediction = model.predict(np.transpose(normalized, (0, 2, 3, 1)), verbose=0)
    if prediction.shape != (len(values), expected[0], expected[1], 1):
        raise ValueError("Frozen model returned an unexpected demand-prediction shape.")
    return prediction
