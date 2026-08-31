#!/usr/bin/env python3
"""Build or validate leakage-safe January destination popularity."""

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
from src.demand.aggregation import build_time_slots
from src.popularity.destination import (
    POPULARITY_COLUMNS, POPULARITY_ENCODING, PopularityThresholds,
    build_destination_popularity,
)


def _validate(frame: pd.DataFrame) -> None:
    if frame.columns.tolist() != POPULARITY_COLUMNS:
        raise ValueError("Destination-popularity artifact schema is incompatible.")
    if frame.duplicated(["TimeSlot", "GridID"]).any() or (frame["dropoff_count"] < 0).any():
        raise ValueError("Destination-popularity rows must be unique and non-negative.")
    available = frame["dropoff_ma_3h"].notna()
    if set(frame.loc[available, "popularity_value"].unique()) - set(POPULARITY_ENCODING.values()):
        raise ValueError("Destination-popularity artifact contains invalid encodings.")
    if frame.loc[available, ["popularity_level", "popularity_value"]].isna().any().any():
        raise ValueError("Available moving averages require labels and encodings.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Explicitly rebuild the derived artifact.")
    parser.add_argument("--validate", action="store_true", help="Validate existing derived artifacts only.")
    args = parser.parse_args()
    try:
        config = load_config(ROOT / "config/config.yaml")
        processed = ROOT / config["data"]["processed_dir"]
        artifact = processed / "destination_popularity_2026_01.parquet"
        metadata = processed / "destination_popularity_2026_01_metadata.json"
        if args.validate or (artifact.is_file() and metadata.is_file() and not args.force):
            frame = pd.read_parquet(artifact)
            with metadata.open(encoding="utf-8") as handle:
                saved = json.load(handle)
            PopularityThresholds(**{key: saved[key] for key in (
                "q20", "q40", "q60", "q80", "reference_start", "reference_end_exclusive",
                "window_slots", "slot_minutes", "methodology_version",
            )})
        else:
            trips = pd.read_parquet(processed / "cleaned_trips.parquet", columns=["tpep_dropoff_datetime", "DOGridID"])
            grids = pd.read_parquet(processed / "grid_lookup.parquet", columns=["GridID"])["GridID"].astype(int).tolist()
            slots = build_time_slots(config["data"]["month"], config["time"]["interval_minutes"])
            test_times = np.load(processed / "cnn/time_test.npy")
            reference_end = pd.Timestamp(test_times[0])
            frame, thresholds = build_destination_popularity(
                trips, grids, slots, reference_start=slots[0], reference_end_exclusive=reference_end,
            )
            _validate(frame)
            frame.to_parquet(artifact, index=False)
            thresholds.save(metadata)
        _validate(frame)
        print("DESTINATION POPULARITY: PASS")
        print(f"rows={len(frame)} grids={frame.GridID.nunique()} slots={frame.TimeSlot.nunique()}")
        print(f"warmup_unavailable={int(frame.dropoff_ma_3h.isna().sum())}")
        print(f"artifact={artifact.relative_to(ROOT)}")
        print(f"metadata={metadata.relative_to(ROOT)}")
        return 0
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"DESTINATION POPULARITY FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
