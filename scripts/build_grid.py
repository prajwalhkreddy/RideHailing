#!/usr/bin/env python3
"""Build and validate the NB1/NB2-compatible January 2026 spatial stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.data.config import load_config
from src.data.taxi import inspect_taxi_schema, load_taxi_data, prepare_legacy_trips
from src.spatial.artifacts import artifact_paths, save_grid_artifacts, validate_grid_artifacts
from src.spatial.grid import build_grid, load_taxi_zones
from src.spatial.mapping import assign_grid_ids_by_zone_legacy, build_neighbor_map, build_zone_to_grids


def parse_args() -> argparse.Namespace:
    """Parse independent stage-script flags."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate existing artifacts without rebuilding.")
    parser.add_argument("--force", action="store_true", help="Rebuild this stage's artifacts explicitly.")
    return parser.parse_args()


def print_report(title: str, report: dict[str, object]) -> None:
    """Print a concise, deterministic execution report."""
    print(f"\n{title}")
    print("=" * len(title))
    for key, value in report.items():
        print(f"{key}: {value}")


def main() -> int:
    """Execute one complete persisted data/spatial checkpoint."""
    args = parse_args()
    config = load_config(ROOT / "config/config.yaml")
    data = config["data"]
    grid_config = config["grid"]
    processed_dir = ROOT / data["processed_dir"]
    paths = artifact_paths(processed_dir)

    if args.validate:
        report = validate_grid_artifacts(processed_dir)
        print_report("GRID ARTIFACT VALIDATION: PASS", report)
        return 0
    if not args.force and all(path.is_file() for path in paths.values()):
        report = validate_grid_artifacts(processed_dir)
        print_report("EXISTING GRID ARTIFACTS VALID: PASS", report)
        return 0

    taxi_path = ROOT / data["yellow_taxi_path"]
    zones_path = ROOT / data["taxi_zones_path"]
    schema = inspect_taxi_schema(taxi_path)
    zones = load_taxi_zones(str(zones_path), grid_config["metric_crs"])
    result = build_grid(zones, grid_config["size_meters"])
    zone_to_grids = build_zone_to_grids(result.zone_grid_mapping)
    grid = result.grid
    grid_mask = np.zeros((int(grid["Row"].max()) + 1, int(grid["Column"].max()) + 1), dtype=np.uint8)
    grid_mask[grid["Row"].to_numpy(), grid["Column"].to_numpy()] = 1
    neighbors = build_neighbor_map(grid)

    trips = load_taxi_data(taxi_path)
    prepared, filtering = prepare_legacy_trips(trips, set(zone_to_grids))
    month_number = int(data["month"].split("-")[1])
    rng = np.random.default_rng(config["random_seed"] + month_number)
    prepared = assign_grid_ids_by_zone_legacy(prepared, "PULocationID", "PUGridID", zone_to_grids, rng)
    prepared = assign_grid_ids_by_zone_legacy(prepared, "DOLocationID", "DOGridID", zone_to_grids, rng)
    valid_ids = set(grid["GridID"].astype(int))
    pickup_unmapped = int((~prepared["PUGridID"].isin(valid_ids)).sum())
    dropoff_unmapped = int((~prepared["DOGridID"].isin(valid_ids)).sum())
    if pickup_unmapped or dropoff_unmapped:
        raise ValueError("Legacy zone assignment produced invalid GridIDs.")

    processed_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = processed_dir / "cleaned_trips.parquet"
    prepared.to_parquet(cleaned_path, index=False)
    metadata = {
        "data_month": data["month"],
        "source_dataset": str(taxi_path.relative_to(ROOT)),
        "taxi_zone_source": str(zones_path.relative_to(ROOT)),
        "source_records": schema["records"],
        "source_columns": schema["columns"],
        "filtering_statistics": filtering,
        "grid_size_meters": grid_config["size_meters"],
        "geometry": grid_config["geometry"],
        "metric_crs": grid_config["metric_crs"],
        "random_seed": config["random_seed"],
        "generated_cells": result.generated_cell_count,
        "valid_cells": len(grid),
        "grid_rows": int(grid["Row"].max()) + 1,
        "grid_columns": int(grid["Column"].max()) + 1,
        "zone_grid_mappings": len(result.zone_grid_mapping),
        "neighbor_links": len(neighbors),
        "mapping_statistics": {
            "pickup_mapped": len(prepared) - pickup_unmapped,
            "pickup_unmapped": pickup_unmapped,
            "dropoff_mapped": len(prepared) - dropoff_unmapped,
            "dropoff_unmapped": dropoff_unmapped,
        },
        "time_interval_minutes": config["time"]["interval_minutes"],
        "legacy_traceability": {
            "grid": "NB1_Spatial_Info_Build.ipynb",
            "trip_assignment": "NB2_GridToTripAssignment",
            "assignment_method": "seeded_zone_to_grid_sampling",
            "coordinate_limitation": "The January 2026 source has no longitude/latitude columns; NB2's LocationID-based seeded sampling is preserved explicitly.",
            "neighbor_convention": "New persisted artifact: side-adjacent square cells only; NB1/NB2 did not define neighbors.",
        },
    }
    spatial_paths = save_grid_artifacts(processed_dir, grid, grid_mask, result.zone_grid_mapping, neighbors, metadata)
    validation = validate_grid_artifacts(processed_dir)
    report = {
        "input_records": schema["records"],
        **filtering,
        "pickup_mapped": len(prepared) - pickup_unmapped,
        "pickup_unmapped": pickup_unmapped,
        "dropoff_mapped": len(prepared) - dropoff_unmapped,
        "dropoff_unmapped": dropoff_unmapped,
        "coordinate_columns_present": False,
        "assignment_method": "NB2 seeded LocationID -> GridID sampling",
        "cleaned_trips": cleaned_path.relative_to(ROOT),
        "grid_lookup": spatial_paths["grid"].relative_to(ROOT),
        **validation,
    }
    print_report("FIRST DATA/SPATIAL MILESTONE: PASS", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
