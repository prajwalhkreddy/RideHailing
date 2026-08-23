"""Legacy NB4 CNN-dataset generation without model or TensorFlow dependencies."""

from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd


# NB4 contract: current Demand remains excluded because USE_CURRENT_DEMAND=False.
CNN_CHANNELS = [
    "HistoricalDemand",
    "Temperature",
    "WindSpeed",
    "WeatherCode",
    "DayOfWeek",
    "Hour",
    "Period",
]
TRAIN_RATIO = 0.80
ARTIFACT_NAMES = {
    "x_train": "X_train.npy",
    "y_train": "y_train.npy",
    "x_test": "X_test.npy",
    "y_test": "y_test.npy",
    "time_train": "time_train.npy",
    "time_test": "time_test.npy",
    "metadata": "metadata.pkl",
}


def validate_tensor_inputs(
    demand_master: pd.DataFrame, grid: pd.DataFrame, grid_mask: np.ndarray, grid_metadata: dict[str, Any]
) -> None:
    """Validate the frozen NB3/grid artifacts required by legacy NB4.

    NB4 maps each valid GridID to its precomputed Row/Column image position.
    This validation intentionally rejects a mismatch instead of rebuilding or
    changing the authoritative NB1–NB3 spatial representation.
    """
    required_demand = {"TimeSlot", "TimeIndex", "GridID", "Demand", "Row", "Column", *CNN_CHANNELS}
    if missing := required_demand - set(demand_master.columns):
        raise ValueError(f"Demand master lacks NB4-required columns: {sorted(missing)}")
    required_grid = {"GridID", "Row", "Column"}
    if missing := required_grid - set(grid.columns):
        raise ValueError(f"Grid lookup lacks NB4-required columns: {sorted(missing)}")
    rows, columns = int(grid_metadata["grid_rows"]), int(grid_metadata["grid_columns"])
    if grid_mask.shape != (rows, columns):
        raise ValueError("Grid mask dimensions do not match canonical grid metadata.")
    if len(grid) != int(grid_metadata["valid_cells"]) or int(grid_mask.sum()) != len(grid):
        raise ValueError("Grid lookup, mask, and metadata disagree on valid-cell count.")
    if demand_master["GridID"].nunique() != len(grid):
        raise ValueError("Demand master GridIDs do not match the canonical grid count.")
    if demand_master[["TimeIndex", "GridID"]].duplicated().any():
        raise ValueError("Demand master must contain one row per TimeIndex and GridID.")
    expected_per_time = demand_master.groupby("TimeIndex", observed=True)["GridID"].nunique()
    if not (expected_per_time == len(grid)).all():
        raise ValueError("Every NB4 time snapshot must contain every valid GridID exactly once.")


def build_cnn_tensors(
    demand_master: pd.DataFrame, grid: pd.DataFrame, grid_mask: np.ndarray, grid_metadata: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create legacy NB4 feature and one-step-ahead target tensors.

    For each ordered 30-minute snapshot ``t``, X stores seven spatial maps at
    ``t`` in the fixed NB4 channel order. y stores raw pickup Demand at ``t+1``.
    Arrays are initialized with zeros, so all canonical invalid/padded mask
    positions remain zero in both X and y exactly as in NB4.
    """
    validate_tensor_inputs(demand_master, grid, grid_mask, grid_metadata)
    rows, columns = int(grid_metadata["grid_rows"]), int(grid_metadata["grid_columns"])
    ordered_grid = grid[["GridID", "Row", "Column"]].sort_values("GridID").reset_index(drop=True)
    ordered = demand_master.sort_values(["TimeIndex", "GridID"]).reset_index(drop=True)
    time_index = ordered["TimeIndex"].drop_duplicates().to_numpy()
    expected_indices = np.arange(len(time_index), dtype=time_index.dtype)
    if not np.array_equal(time_index, expected_indices):
        raise ValueError("NB4 requires sequential TimeIndex values beginning at zero.")
    snapshots = len(time_index)
    cells = len(ordered_grid)
    if len(ordered) != snapshots * cells:
        raise ValueError("Demand master row count is incompatible with complete NB4 snapshots.")
    source_positions = ordered[["Row", "Column"]].to_numpy().reshape(snapshots, cells, 2)
    canonical_positions = ordered_grid[["Row", "Column"]].to_numpy()
    if not np.array_equal(source_positions, np.broadcast_to(canonical_positions, source_positions.shape)):
        raise ValueError("Demand-master Row/Column positions do not match canonical GridID positions.")

    feature_values = ordered[CNN_CHANNELS].to_numpy(dtype=np.float32).reshape(snapshots, cells, len(CNN_CHANNELS))
    demand_values = ordered["Demand"].to_numpy(dtype=np.float32).reshape(snapshots, cells)
    row_positions, column_positions = canonical_positions.T
    x = np.zeros((snapshots - 1, len(CNN_CHANNELS), rows, columns), dtype=np.float32)
    y = np.zeros((snapshots - 1, 1, rows, columns), dtype=np.float32)
    for channel in range(len(CNN_CHANNELS)):
        x[:, channel, row_positions, column_positions] = feature_values[:-1, :, channel]
    y[:, 0, row_positions, column_positions] = demand_values[1:]
    time_slots = ordered["TimeSlot"].drop_duplicates().to_numpy()[:-1]
    return x, y, time_slots


def chronological_split(
    x: np.ndarray, y: np.ndarray, time_slots: np.ndarray, train_ratio: float = TRAIN_RATIO
) -> dict[str, np.ndarray]:
    """Apply NB4's unshuffled chronological 80/20 split."""
    if not (len(x) == len(y) == len(time_slots)):
        raise ValueError("X, y, and sample TimeSlot arrays must have equal lengths.")
    split_index = int(len(x) * train_ratio)
    return {
        "x_train": x[:split_index], "y_train": y[:split_index],
        "x_test": x[split_index:], "y_test": y[split_index:],
        "time_train": time_slots[:split_index], "time_test": time_slots[split_index:],
    }


def artifact_paths(dataset_dir: str | Path) -> dict[str, Path]:
    """Return the exact NB4/NB5-compatible artifact filenames."""
    root = Path(dataset_dir)
    return {name: root / filename for name, filename in ARTIFACT_NAMES.items()}


def save_cnn_dataset(dataset_dir: str | Path, arrays: dict[str, np.ndarray], grid_metadata: dict[str, Any]) -> dict[str, Path]:
    """Persist NB4's split arrays and legacy ``metadata.pkl`` contract."""
    paths = artifact_paths(dataset_dir)
    Path(dataset_dir).mkdir(parents=True, exist_ok=True)
    for key in ("x_train", "y_train", "x_test", "y_test", "time_train", "time_test"):
        np.save(paths[key], arrays[key])
    metadata = {
        "rows": int(grid_metadata["grid_rows"]),
        "cols": int(grid_metadata["grid_columns"]),
        "channels": CNN_CHANNELS,
        "train_samples": len(arrays["x_train"]),
        "test_samples": len(arrays["x_test"]),
        "train_ratio": TRAIN_RATIO,
        "input_shape": arrays["x_train"].shape,
        "target_shape": arrays["y_train"].shape,
    }
    with paths["metadata"].open("wb") as handle:
        pickle.dump(metadata, handle)
    return paths


def load_cnn_dataset(dataset_dir: str | Path) -> dict[str, Any]:
    """Reload all persisted NB4 artifacts for validation or downstream NB5 use."""
    paths = artifact_paths(dataset_dir)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing CNN dataset artifacts: " + ", ".join(missing))
    with paths["metadata"].open("rb") as handle:
        metadata = pickle.load(handle)
    return {**{key: np.load(paths[key]) for key in paths if key != "metadata"}, "metadata": metadata, "paths": paths}


def validate_cnn_dataset(dataset_dir: str | Path, grid_metadata: dict[str, Any]) -> dict[str, Any]:
    """Validate persisted NB4 split arrays, shapes, dtypes, and metadata."""
    dataset = load_cnn_dataset(dataset_dir)
    metadata = dataset["metadata"]
    rows, columns = int(grid_metadata["grid_rows"]), int(grid_metadata["grid_columns"])
    if metadata.get("rows") != rows or metadata.get("cols") != columns or metadata.get("channels") != CNN_CHANNELS:
        raise ValueError("CNN dataset metadata is incompatible with the canonical NB4 contract.")
    for split in ("train", "test"):
        x, y, times = dataset[f"x_{split}"], dataset[f"y_{split}"], dataset[f"time_{split}"]
        if x.dtype != np.float32 or y.dtype != np.float32:
            raise ValueError("NB4 feature and target arrays must be float32.")
        if x.shape != (len(times), len(CNN_CHANNELS), rows, columns):
            raise ValueError(f"X_{split} shape is incompatible with NB4 metadata.")
        if y.shape != (len(times), 1, rows, columns):
            raise ValueError(f"y_{split} shape is incompatible with NB4 metadata.")
    if len(dataset["time_train"]) != metadata["train_samples"] or len(dataset["time_test"]) != metadata["test_samples"]:
        raise ValueError("CNN dataset metadata sample counts do not match persisted arrays.")
    if len(dataset["time_train"]) and len(dataset["time_test"]) and dataset["time_train"][-1] >= dataset["time_test"][0]:
        raise ValueError("CNN train/test times are not strictly chronological.")
    return {"samples": len(dataset["x_train"]) + len(dataset["x_test"]), "x_train_shape": dataset["x_train"].shape, "x_test_shape": dataset["x_test"].shape, "y_train_shape": dataset["y_train"].shape, "y_test_shape": dataset["y_test"].shape}
