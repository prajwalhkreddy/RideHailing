"""Persistence and validation for the single authoritative spatial grid."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import pickle
import platform
from pathlib import Path
import sys
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from src.spatial.grid import validate_grid
from src.spatial.mapping import build_zone_to_grids, validate_neighbor_map


ARTIFACT_NAMES = {
    "grid": "grid_lookup.parquet",
    "mask": "grid_mask.npy",
    "zone_mapping": "zone_grid_mapping.parquet",
    "zone_lookup": "zone_to_grids.pkl",
    "neighbors": "neighbour_map.parquet",
    "metadata": "grid_metadata.json",
}


def artifact_paths(processed_dir: str | Path) -> dict[str, Path]:
    """Return all first-milestone artifact paths under ``data/processed``."""
    root = Path(processed_dir)
    return {name: root / filename for name, filename in ARTIFACT_NAMES.items()}


def save_grid_artifacts(
    processed_dir: str | Path,
    grid: gpd.GeoDataFrame,
    grid_mask: np.ndarray,
    zone_grid_mapping: pd.DataFrame,
    neighbor_map: pd.DataFrame,
    metadata: dict[str, Any],
) -> dict[str, Path]:
    """Persist authoritative grid artifacts for independent downstream reloads."""
    validate_grid(grid)
    paths = artifact_paths(processed_dir)
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    grid.to_parquet(paths["grid"], index=False)
    np.save(paths["mask"], grid_mask)
    zone_grid_mapping[["LocationID", "GridID"]].to_parquet(paths["zone_mapping"], index=False)
    neighbor_map.to_parquet(paths["neighbors"], index=False)
    with paths["zone_lookup"].open("wb") as handle:
        pickle.dump(build_zone_to_grids(zone_grid_mapping), handle)
    metadata = {
        **metadata,
        "build_timestamp_utc": datetime.now(UTC).isoformat(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }
    with paths["metadata"].open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
    return paths


def load_grid_artifacts(processed_dir: str | Path) -> dict[str, Any]:
    """Load the single persisted grid representation and related artifacts."""
    paths = artifact_paths(processed_dir)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing spatial artifacts: " + ", ".join(missing))
    with paths["zone_lookup"].open("rb") as handle:
        zone_to_grids = pickle.load(handle)
    with paths["metadata"].open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    return {
        "grid": gpd.read_parquet(paths["grid"]),
        "grid_mask": np.load(paths["mask"]),
        "zone_grid_mapping": pd.read_parquet(paths["zone_mapping"]),
        "zone_to_grids": zone_to_grids,
        "neighbor_map": pd.read_parquet(paths["neighbors"]),
        "metadata": metadata,
        "paths": paths,
    }


def validate_grid_artifacts(processed_dir: str | Path) -> dict[str, int]:
    """Reload and validate persisted schemas, dimensions, mappings, and links."""
    artifacts = load_grid_artifacts(processed_dir)
    grid = artifacts["grid"]
    validate_grid(grid)
    mask = artifacts["grid_mask"]
    expected_shape = (int(grid["Row"].max()) + 1, int(grid["Column"].max()) + 1)
    if mask.shape != expected_shape or int(mask.sum()) != len(grid):
        raise ValueError(f"Grid mask is incompatible: shape {mask.shape}, expected {expected_shape}.")
    mapping = artifacts["zone_grid_mapping"]
    valid_ids = set(grid["GridID"].astype(int))
    if mapping.empty or not set(mapping["GridID"].astype(int)).issubset(valid_ids):
        raise ValueError("Zone-grid mapping is empty or contains invalid GridIDs.")
    expected_lookup = build_zone_to_grids(mapping)
    if artifacts["zone_to_grids"] != expected_lookup:
        raise ValueError("zone_to_grids.pkl disagrees with zone_grid_mapping.parquet.")
    validate_neighbor_map(artifacts["neighbor_map"], valid_ids)
    return {
        "valid_cells": len(grid),
        "grid_rows": expected_shape[0],
        "grid_columns": expected_shape[1],
        "zone_grid_mappings": len(mapping),
        "neighbor_links": len(artifacts["neighbor_map"]),
    }
