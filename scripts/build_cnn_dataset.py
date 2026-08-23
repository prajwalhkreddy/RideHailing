#!/usr/bin/env python3
"""Build the legacy NB4 CNN arrays only; no TensorFlow or model training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.data.config import load_config
from src.demand.tensors import (
    build_cnn_tensors, chronological_split, save_cnn_dataset,
    validate_cnn_dataset, validate_tensor_inputs,
)


def parse_args() -> argparse.Namespace:
    """Parse independent NB4 tensor build/validation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate persisted NB4 arrays without rebuilding.")
    parser.add_argument("--force", action="store_true", help="Explicitly rebuild the NB4 tensor artifacts.")
    return parser.parse_args()


def load_inputs(processed_dir: Path, demand_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, dict]:
    """Load frozen NB1–NB3 artifacts without rebuilding any upstream stage."""
    grid_path = processed_dir / "grid_lookup.parquet"
    mask_path = processed_dir / "grid_mask.npy"
    metadata_path = processed_dir / "grid_metadata.json"
    missing = [str(path) for path in (demand_path, grid_path, mask_path, metadata_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("NB4 requires frozen NB1–NB3 artifacts: " + ", ".join(missing))
    demand = pd.read_parquet(demand_path)
    grid = pd.read_parquet(grid_path)
    mask = np.load(mask_path)
    with metadata_path.open("r", encoding="utf-8") as handle:
        grid_metadata = json.load(handle)
    validate_tensor_inputs(demand, grid, mask, grid_metadata)
    return demand, grid, mask, grid_metadata


def main() -> int:
    """Execute or validate the standalone legacy NB4 tensor-generation stage."""
    args = parse_args()
    config = load_config(ROOT / "config/config.yaml")
    processed_dir = ROOT / config["data"]["processed_dir"]
    demand_path = ROOT / config["data"]["demand_master_path"]
    dataset_dir = ROOT / config["data"]["cnn_dataset_dir"]
    try:
        if args.validate:
            _, _, _, grid_metadata = load_inputs(processed_dir, demand_path)
            report = validate_cnn_dataset(dataset_dir, grid_metadata)
        elif dataset_dir.is_dir() and not args.force:
            _, _, _, grid_metadata = load_inputs(processed_dir, demand_path)
            report = validate_cnn_dataset(dataset_dir, grid_metadata)
        else:
            demand, grid, mask, grid_metadata = load_inputs(processed_dir, demand_path)
            x, y, time_slots = build_cnn_tensors(demand, grid, mask, grid_metadata)
            arrays = chronological_split(x, y, time_slots)
            save_cnn_dataset(dataset_dir, arrays, grid_metadata)
            report = validate_cnn_dataset(dataset_dir, grid_metadata)
        print("NB4 CNN DATASET: PASS")
        for key, value in report.items():
            print(f"{key}: {value}")
        return 0
    except (FileNotFoundError, ValueError, KeyError) as error:
        print(f"NB4 CNN DATASET FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
