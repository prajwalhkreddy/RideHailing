#!/usr/bin/env python3
"""Build the legacy-compatible NB3 demand master table; no CNN/tensor work."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.data.config import load_config
from src.data.weather import load_processed_weather
from src.demand.aggregation import (
    add_historical_demand, add_temporal_features, aggregate_pickup_demand,
    build_time_slots, complete_space_time_grid, merge_hourly_weather,
)
from src.demand.contracts import demand_metadata_path, validate_demand_master, validate_grid_input_contract


def parse_args() -> argparse.Namespace:
    """Parse NB3's independent build/validation flags."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate an existing demand master without rebuilding.")
    parser.add_argument("--force", action="store_true", help="Explicitly rebuild NB3 outputs.")
    return parser.parse_args()


def load_first_milestone_inputs(processed_dir: Path, month: str) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, dict]:
    """Load and validate canonical trip/grid inputs supplied by milestone one."""
    trips_path = processed_dir / "cleaned_trips.parquet"
    grid_path = processed_dir / "grid_lookup.parquet"
    mask_path = processed_dir / "grid_mask.npy"
    metadata_path = processed_dir / "grid_metadata.json"
    missing = [str(path) for path in (trips_path, grid_path, mask_path, metadata_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("NB3 requires first-milestone artifacts: " + ", ".join(missing))
    trips = pd.read_parquet(trips_path, columns=["tpep_pickup_datetime", "PUGridID"])
    grid = pd.read_parquet(grid_path)
    mask = np.load(mask_path)
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    validate_grid_input_contract(grid, mask, metadata, month)
    return trips, grid, mask, metadata


def validate_existing(output_path: Path, processed_dir: Path, month: str) -> dict[str, int]:
    """Reload and validate an existing NB3 table against canonical grid artifacts."""
    if not output_path.is_file():
        raise FileNotFoundError(f"NB3 demand master is missing: {output_path}. Run without --validate after supplying weather.")
    _, grid, _, _ = load_first_milestone_inputs(processed_dir, month)
    master = pd.read_parquet(output_path)
    validate_demand_master(master, grid, month)
    return {"time_slots": master["TimeSlot"].nunique(), "valid_grid_ids": master["GridID"].nunique(), "rows": len(master)}


def main() -> int:
    """Execute NB3 or validate a prior complete NB3 output."""
    args = parse_args()
    config = load_config(ROOT / "config/config.yaml")
    data = config["data"]
    month = data["month"]
    interval = config["time"]["interval_minutes"]
    processed_dir = ROOT / data["processed_dir"]
    output_path = ROOT / data["demand_master_path"]
    try:
        if args.validate:
            report = validate_existing(output_path, processed_dir, month)
            print("NB3 DEMAND MASTER VALIDATION: PASS")
            for key, value in report.items():
                print(f"{key}: {value}")
            return 0
        if output_path.is_file() and not args.force:
            report = validate_existing(output_path, processed_dir, month)
            print("EXISTING NB3 DEMAND MASTER VALID: PASS")
            for key, value in report.items():
                print(f"{key}: {value}")
            return 0

        trips, grid, _mask, grid_metadata = load_first_milestone_inputs(processed_dir, month)
        weather = load_processed_weather(ROOT / data["weather_path"], month)
        time_slots = build_time_slots(month, interval)
        demand, january_trip_count = aggregate_pickup_demand(trips, month, interval)
        master = complete_space_time_grid(demand, grid, time_slots)
        master = merge_hourly_weather(master, weather)
        master = add_temporal_features(master)
        master = add_historical_demand(master)
        validate_demand_master(master, grid, month)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        master.to_parquet(output_path, index=False)
        provenance = {
            "build_timestamp_utc": datetime.now(UTC).isoformat(),
            "data_month": month,
            "time_interval_minutes": interval,
            "source_trips": str((processed_dir / "cleaned_trips.parquet").relative_to(ROOT)),
            "source_grid": str((processed_dir / "grid_lookup.parquet").relative_to(ROOT)),
            "source_weather": data["weather_path"],
            "weather_records": len(weather),
            "trips_within_month": january_trip_count,
            "time_slots": len(time_slots),
            "valid_grid_ids": len(grid),
            "rows": len(master),
            "legacy_traceability": {
                "notebook": "NB3_DemandAggregation.ipynb",
                "demand": "Pickup count by (TimeSlot, PUGridID); DOGridID is not used.",
                "historical_demand": "Strictly earlier expanding mean by GridID, DayOfWeek, Period.",
                "timezone": "Unresolved legacy timezone-naive taxi/weather alignment; no conversion applied.",
                "normalization": "None in NB3.",
            },
            "grid_metadata": {key: grid_metadata[key] for key in ("metric_crs", "grid_size_meters", "grid_rows", "grid_columns", "valid_cells")},
        }
        with demand_metadata_path(output_path).open("w", encoding="utf-8") as handle:
            json.dump(provenance, handle, indent=2, sort_keys=True)
        print("NB3 DEMAND MASTER: PASS")
        print(f"time_slots: {len(time_slots)}")
        print(f"valid_grid_ids: {len(grid)}")
        print(f"rows: {len(master)}")
        print(f"weather_records: {len(weather)}")
        print(f"trips_within_month: {january_trip_count}")
        print(f"output: {output_path.relative_to(ROOT)}")
        return 0
    except (FileNotFoundError, ValueError, KeyError) as error:
        print(f"NB3 BUILD FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
