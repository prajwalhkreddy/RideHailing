"""Legacy NB5 CNN training, evaluation, and artifact helpers.

This module reproduces the reference notebook's baseline: channel-wise input
normalization from the training split, a same-padded three-layer CNN, Keras's
shuffled ``validation_split``, and unmasked full-grid evaluation.
"""

from __future__ import annotations

import os
from pathlib import Path
import pickle
import random
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Conv2D, Input
from tensorflow.keras.optimizers import Adam

from src.demand.tensors import CNN_CHANNELS


FILTERS = (32, 64, 32)
KERNEL_SIZE = (3, 3)
LEARNING_RATE = 0.001
BATCH_SIZE = 32
EPOCHS = 50
VALIDATION_SPLIT = 0.20
NORMALIZATION_FILENAME = "normalization.pkl"
MODEL_FILENAME = "cnn_model.keras"
METRICS_FILENAME = "cnn_metrics.csv"
PREDICTIONS_FILENAME = "cnn_predictions.npy"
HISTORY_FILENAME = "cnn_history.pkl"


def set_deterministic_seeds(seed: int) -> None:
    """Make the best available deterministic TensorFlow setup for NB5."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["TF_DETERMINISTIC_OPS"] = "1"
    random.seed(seed)
    np.random.seed(seed)
    tf.keras.utils.set_random_seed(seed)
    try:
        tf.config.experimental.enable_op_determinism()
    except (AttributeError, RuntimeError):
        # Some TensorFlow builds either enable this eagerly or lack the API.
        pass


def validate_channels_first_features(features: np.ndarray, channels: list[str] | tuple[str, ...] = CNN_CHANNELS) -> None:
    """Validate legacy channels-first feature tensors without altering them."""
    if features.ndim != 4:
        raise ValueError("Feature tensor must have shape (samples, channels, rows, columns).")
    if features.shape[1] != len(channels):
        raise ValueError(f"Feature tensor must contain exactly {len(channels)} NB4 channels.")
    if not np.issubdtype(features.dtype, np.number):
        raise ValueError("Feature tensor must be numeric.")
    if not np.isfinite(features).all():
        raise ValueError("Feature tensor contains non-finite values.")


def validate_channels_first_targets(targets: np.ndarray, rows: int, cols: int) -> None:
    """Validate raw-demand channels-first target tensors."""
    if targets.ndim != 4 or targets.shape[1:] != (1, rows, cols):
        raise ValueError("Target tensor must have shape (samples, 1, rows, columns).")
    if not np.issubdtype(targets.dtype, np.number) or not np.isfinite(targets).all():
        raise ValueError("Target tensor must be finite and numeric.")


def compute_normalization(features: np.ndarray, channels: list[str] | tuple[str, ...] = CNN_CHANNELS) -> dict[str, Any]:
    """Fit NB5 per-channel training statistics only on a channels-first X array."""
    validate_channels_first_features(features, channels)
    means = features.mean(axis=(0, 2, 3), dtype=np.float64).astype(np.float32)
    stds = features.std(axis=(0, 2, 3), dtype=np.float64).astype(np.float32)
    stds[stds == 0] = 1.0
    return {"means": means, "stds": stds, "channels": list(channels)}


def validate_normalization(normalization: dict[str, Any], channels: list[str] | tuple[str, ...] = CNN_CHANNELS) -> None:
    """Check the legacy normalization artifact before applying it."""
    if normalization.get("channels") != list(channels):
        raise ValueError("Normalization channel order is incompatible with the NB4 dataset.")
    means = np.asarray(normalization.get("means"))
    stds = np.asarray(normalization.get("stds"))
    if means.shape != (len(channels),) or stds.shape != (len(channels),):
        raise ValueError("Normalization means/stds must have one value per channel.")
    if not np.isfinite(means).all() or not np.isfinite(stds).all() or (stds <= 0).any():
        raise ValueError("Normalization means/stds must be finite, with strictly positive stds.")


def normalize_features(features: np.ndarray, normalization: dict[str, Any]) -> np.ndarray:
    """Apply saved training statistics channel-wise, leaving the source array untouched."""
    validate_channels_first_features(features)
    validate_normalization(normalization)
    means = np.asarray(normalization["means"], dtype=np.float32)[None, :, None, None]
    stds = np.asarray(normalization["stds"], dtype=np.float32)[None, :, None, None]
    return ((features.astype(np.float32, copy=True) - means) / stds).astype(np.float32, copy=False)


def channels_first_to_last(values: np.ndarray, *, target: bool = False) -> np.ndarray:
    """Transpose NB4 storage order to TensorFlow's channels-last order."""
    if values.ndim != 4:
        raise ValueError("Tensor must be four-dimensional for channels-first conversion.")
    expected = 1 if target else len(CNN_CHANNELS)
    if values.shape[1] != expected:
        raise ValueError(f"Channels-first tensor must have {expected} channel(s).")
    return np.transpose(values, (0, 2, 3, 1))


def build_model(rows: int, cols: int, channels: int = len(CNN_CHANNELS)) -> Model:
    """Build the exact same-padded CNN architecture defined by legacy NB5."""
    if rows <= 0 or cols <= 0 or channels != len(CNN_CHANNELS):
        raise ValueError("NB5 requires positive grid dimensions and exactly seven input channels.")
    inputs = Input(shape=(rows, cols, channels), name="InputLayer")
    x = Conv2D(FILTERS[0], KERNEL_SIZE, padding="same", activation="relu", name="Conv1")(inputs)
    x = Conv2D(FILTERS[1], KERNEL_SIZE, padding="same", activation="relu", name="Conv2")(x)
    x = Conv2D(FILTERS[2], KERNEL_SIZE, padding="same", activation="relu", name="Conv3")(x)
    outputs = Conv2D(1, (1, 1), padding="same", activation="linear", name="OutputLayer")(x)
    model = Model(inputs=inputs, outputs=outputs, name="DemandPredictionCNN")
    model.compile(optimizer=Adam(learning_rate=LEARNING_RATE), loss="mse", metrics=["mae"])
    return model


def train_model(model: Model, x_train: np.ndarray, y_train: np.ndarray, *, verbose: int = 1) -> Any:
    """Train with NB5's EarlyStopping and Keras validation-split behaviour."""
    early_stop = EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=verbose)
    return model.fit(
        x_train,
        y_train,
        validation_split=VALIDATION_SPLIT,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop],
        shuffle=True,
        verbose=verbose,
    )


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> pd.DataFrame:
    """Compute the exact NB5 full-grid metrics, including positive-demand MAPE."""
    if y_true.shape != y_pred.shape:
        raise ValueError("Predictions and targets must have identical shapes.")
    actual, estimated = y_true.reshape(-1), y_pred.reshape(-1)
    if not np.isfinite(actual).all() or not np.isfinite(estimated).all():
        raise ValueError("Predictions and targets must be finite for evaluation.")
    positive = actual > 0
    mape = np.mean(np.abs((actual[positive] - estimated[positive]) / actual[positive])) * 100 if positive.any() else np.nan
    return pd.DataFrame({"Metric": ["RMSE", "MAE", "MAPE (%)", "R² Score"], "Value": [
        float(np.sqrt(mean_squared_error(actual, estimated))),
        float(mean_absolute_error(actual, estimated)),
        float(mape),
        float(r2_score(actual, estimated)),
    ]})


def save_normalization(path: str | Path, normalization: dict[str, Any]) -> None:
    """Persist NB5-compatible normalization.pkl."""
    validate_normalization(normalization)
    with Path(path).open("wb") as handle:
        pickle.dump(normalization, handle)


def load_normalization(path: str | Path) -> dict[str, Any]:
    """Load and validate a NB5-compatible normalization artifact."""
    with Path(path).open("rb") as handle:
        normalization = pickle.load(handle)
    validate_normalization(normalization)
    return normalization


def model_artifact_paths(model_dir: str | Path) -> dict[str, Path]:
    """Return the exact legacy NB5 persisted artifact paths."""
    root = Path(model_dir)
    return {
        "normalization": root / NORMALIZATION_FILENAME,
        "model": root / MODEL_FILENAME,
        "metrics": root / METRICS_FILENAME,
        "predictions": root / PREDICTIONS_FILENAME,
        "history": root / HISTORY_FILENAME,
    }


def save_training_artifacts(model_dir: str | Path, model: Model, normalization: dict[str, Any], history: dict[str, list[float]], predictions: np.ndarray, metrics: pd.DataFrame) -> dict[str, Path]:
    """Save all legacy NB5 model artifacts without modifying NB4 arrays."""
    paths = model_artifact_paths(model_dir)
    Path(model_dir).mkdir(parents=True, exist_ok=True)
    save_normalization(paths["normalization"], normalization)
    metrics.to_csv(paths["metrics"], index=False)
    np.save(paths["predictions"], predictions)
    model.save(paths["model"])
    with paths["history"].open("wb") as handle:
        pickle.dump(history, handle)
    return paths
