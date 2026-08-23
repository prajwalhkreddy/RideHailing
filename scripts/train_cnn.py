#!/usr/bin/env python3
"""Train or validate only the legacy NB5 demand-prediction CNN stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import pickle
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from src.data.config import load_config
from src.demand.inference import load_predictor, predict_demand
from src.demand.model import (
    BATCH_SIZE, EPOCHS, LEARNING_RATE, VALIDATION_SPLIT, build_model,
    channels_first_to_last, compute_normalization, evaluate_predictions,
    model_artifact_paths, normalize_features, save_training_artifacts,
    set_deterministic_seeds, train_model,
)
from src.demand.tensors import CNN_CHANNELS, load_cnn_dataset, validate_cnn_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Explicitly train and overwrite NB5 artifacts.")
    parser.add_argument("--validate", action="store_true", help="Validate saved NB5 artifacts without training.")
    return parser.parse_args()


def load_frozen_inputs(config: dict) -> tuple[dict, dict]:
    """Load NB4 arrays and only the metadata required to validate them."""
    processed = ROOT / config["data"]["processed_dir"]
    with (processed / "grid_metadata.json").open(encoding="utf-8") as handle:
        grid_metadata = json.load(handle)
    dataset_dir = ROOT / config["data"]["cnn_dataset_dir"]
    validate_cnn_dataset(dataset_dir, grid_metadata)
    return load_cnn_dataset(dataset_dir), grid_metadata


def save_plots(history: dict[str, list[float]], y_test: np.ndarray, predictions: np.ndarray, output_dir: Path) -> None:
    """Persist the four visualizations produced by reference NB5."""
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(history["loss"], label="Training Loss", linewidth=2)
    plt.plot(history["val_loss"], label="Validation Loss", linewidth=2)
    plt.xlabel("Epoch"); plt.ylabel("Loss (MSE)"); plt.title("CNN Training History"); plt.legend(); plt.grid(True)
    plt.tight_layout(); plt.savefig(output_dir / "cnn_training_history.png", dpi=150); plt.close()

    actual, predicted = y_test[0, :, :, 0], predictions[0, :, :, 0]
    difference = predicted - actual
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    vmax = max(actual.max(), predicted.max())
    im1 = axes[0].imshow(actual, cmap="viridis", vmin=0, vmax=vmax); axes[0].set_title("Actual Demand")
    im2 = axes[1].imshow(predicted, cmap="viridis", vmin=0, vmax=vmax); axes[1].set_title("Predicted Demand")
    im3 = axes[2].imshow(difference, cmap="coolwarm"); axes[2].set_title("Prediction Error")
    for axis in axes: axis.set_xticks([]); axis.set_yticks([])
    fig.colorbar(im1, ax=axes[0]); fig.colorbar(im2, ax=axes[1]); fig.colorbar(im3, ax=axes[2])
    fig.tight_layout(); fig.savefig(output_dir / "cnn_demand_maps.png", dpi=150); plt.close(fig)

    y_true, y_est = y_test.reshape(-1), predictions.reshape(-1)
    maximum = max(y_true.max(), y_est.max())
    plt.figure(figsize=(6, 6)); plt.scatter(y_true, y_est, alpha=0.15)
    plt.plot([0, maximum], [0, maximum], "r--", linewidth=2, label="Perfect Prediction")
    plt.xlabel("Actual Demand"); plt.ylabel("Predicted Demand"); plt.title("Actual vs Predicted Demand")
    plt.legend(); plt.grid(True); plt.tight_layout(); plt.savefig(output_dir / "cnn_actual_vs_predicted.png", dpi=150); plt.close()

    plt.figure(figsize=(8, 5)); plt.hist(y_est - y_true, bins=60, edgecolor="black")
    plt.axvline(0, color="red", linestyle="--", linewidth=2)
    plt.title("Prediction Error Distribution"); plt.xlabel("Prediction Error"); plt.ylabel("Frequency"); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(output_dir / "cnn_prediction_error_histogram.png", dpi=150); plt.close()


def validate_saved_artifacts(config: dict) -> dict[str, object]:
    """Validate frozen model, saved normalization, predictions, and inference path."""
    dataset, _ = load_frozen_inputs(config)
    paths = model_artifact_paths(ROOT / "models/demand")
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing NB5 artifacts: " + ", ".join(missing))
    model, normalization = load_predictor(paths["model"], paths["normalization"])
    prediction = np.load(paths["predictions"])
    expected = (len(dataset["x_test"]), dataset["metadata"]["rows"], dataset["metadata"]["cols"], 1)
    if prediction.shape != expected:
        raise ValueError("Saved prediction tensor shape is incompatible with NB4 test data.")
    reloaded = predict_demand(dataset["x_test"][:1], model, normalization)
    if reloaded.shape != (1, *expected[1:]) or not np.isfinite(reloaded).all():
        raise ValueError("Frozen model inference contract failed.")
    with paths["history"].open("rb") as handle:
        history = pickle.load(handle)
    if not {"loss", "mae", "val_loss", "val_mae"}.issubset(history):
        raise ValueError("Saved training history lacks NB5 metrics.")
    metrics = pd.read_csv(paths["metrics"])
    if metrics["Metric"].tolist() != ["RMSE", "MAE", "MAPE (%)", "R² Score"]:
        raise ValueError("Saved metrics do not match the NB5 contract.")
    return {"prediction_shape": prediction.shape, "parameter_count": model.count_params(), "epochs_trained": len(history["loss"])}


def train(config: dict) -> dict[str, object]:
    """Execute one NB5 training run from frozen NB4 arrays."""
    dataset, _ = load_frozen_inputs(config)
    metadata = dataset["metadata"]
    set_deterministic_seeds(config["random_seed"])
    normalization = compute_normalization(dataset["x_train"], metadata["channels"])
    x_train = channels_first_to_last(normalize_features(dataset["x_train"], normalization))
    x_test = channels_first_to_last(normalize_features(dataset["x_test"], normalization))
    y_train = channels_first_to_last(dataset["y_train"], target=True)
    y_test = channels_first_to_last(dataset["y_test"], target=True)
    model = build_model(metadata["rows"], metadata["cols"], len(metadata["channels"]))
    started = time.perf_counter()
    history = train_model(model, x_train, y_train).history
    duration_seconds = time.perf_counter() - started
    predictions = model.predict(x_test, verbose=1)
    metrics = evaluate_predictions(y_test, predictions)
    paths = save_training_artifacts(ROOT / "models/demand", model, normalization, history, predictions, metrics)
    save_plots(history, y_test, predictions, ROOT / "outputs/figures")
    provenance = {
        "tensorflow_version": tf.__version__, "keras_version": tf.keras.__version__, "random_seed": config["random_seed"],
        "source_dataset": str(ROOT / config["data"]["cnn_dataset_dir"]), "channels": CNN_CHANNELS,
        "normalization_fit": "X_train only", "target_normalization": "none", "padding_policy": "unmasked legacy baseline",
        "training": {"learning_rate": LEARNING_RATE, "batch_size": BATCH_SIZE, "epochs_requested": EPOCHS, "validation_split": VALIDATION_SPLIT, "shuffle": True, "early_stopping": {"monitor": "val_loss", "patience": 5, "restore_best_weights": True}},
        "duration_seconds": duration_seconds,
    }
    with (ROOT / "models/demand/cnn_provenance.json").open("w", encoding="utf-8") as handle:
        json.dump(provenance, handle, indent=2)
    return {"paths": paths, "history": history, "metrics": metrics, "duration_seconds": duration_seconds, "parameter_count": model.count_params(), "prediction_shape": predictions.shape}


def main() -> int:
    args = parse_args()
    config = load_config(ROOT / "config/config.yaml")
    try:
        if args.validate:
            report = validate_saved_artifacts(config)
            print("NB5 CNN ARTIFACTS: PASS")
            for key, value in report.items(): print(f"{key}: {value}")
        else:
            paths = model_artifact_paths(ROOT / "models/demand")
            if paths["model"].is_file() and not args.force:
                report = validate_saved_artifacts(config)
                print("NB5 CNN ARTIFACTS: PASS (existing; use --force to retrain)")
                for key, value in report.items(): print(f"{key}: {value}")
            else:
                report = train(config)
                print("NB5 CNN TRAINING: PASS")
                print(f"parameter_count: {report['parameter_count']}")
                print(f"prediction_shape: {report['prediction_shape']}")
                print(f"duration_seconds: {report['duration_seconds']:.2f}")
                print(report["metrics"].to_string(index=False))
        return 0
    except (FileNotFoundError, ValueError, KeyError, OSError) as error:
        print(f"NB5 CNN FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
