#!/usr/bin/env python3
"""Build or validate hierarchical W,T sensitivity fallback parameters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pricing.historical_sensitivity import (
    DISTANCE_MAX_MILES, DISTANCE_RESOLUTION_MILES, FALLBACK_COLUMNS,
    FALLBACK_METHODOLOGY_VERSION, TRAINING_END_EXCLUSIVE, TRAINING_START,
    build_sensitivity_fallbacks,
)

ARTIFACT = ROOT / "data/processed/customer_price_sensitivity_fallback_2026_01.parquet"
METADATA = ROOT / "data/processed/customer_price_sensitivity_fallback_2026_01_metadata.json"
TRIPS = ROOT / "data/processed/cleaned_trips.parquet"
DEMAND = ROOT / "data/processed/demand_master_2026_01.parquet"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(frame: pd.DataFrame) -> None:
    if frame.columns.tolist() != FALLBACK_COLUMNS or frame.empty:
        raise ValueError("Fallback sensitivity artifact schema is invalid.")
    if frame.duplicated(["fallback_level", "WeatherCode", "Period"]).any():
        raise ValueError("Fallback sensitivity keys must be unique.")
    if set(frame.fallback_level) != {"period", "weather", "global"}:
        raise ValueError("Fallback artifact must contain all hierarchy levels.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate or (ARTIFACT.exists() and METADATA.exists() and not args.force):
        frame = pd.read_parquet(ARTIFACT); validate(frame)
        metadata = json.loads(METADATA.read_text(encoding="utf-8"))
        if metadata["output_sha256"] != sha256(ARTIFACT):
            raise ValueError("Fallback artifact hash does not match metadata.")
    else:
        trips = pd.read_parquet(TRIPS, columns=["tpep_pickup_datetime", "fare_amount", "trip_distance"])
        demand = pd.read_parquet(DEMAND, columns=["TimeSlot", "WeatherCode", "Period"])
        frame = build_sensitivity_fallbacks(trips, demand); validate(frame)
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(ARTIFACT, index=False)
        metadata = {
            "methodology_version": FALLBACK_METHODOLOGY_VERSION,
            "source_trip_artifact": str(TRIPS.relative_to(ROOT)),
            "source_trip_sha256": sha256(TRIPS),
            "weather_time_lookup_artifact": str(DEMAND.relative_to(ROOT)),
            "weather_time_lookup_sha256": sha256(DEMAND),
            "training_start_inclusive": TRAINING_START.isoformat(),
            "training_cutoff_exclusive": TRAINING_END_EXCLUSIVE.isoformat(),
            "validity": f"finite fare_amount > 0; finite 0 < trip_distance <= {DISTANCE_MAX_MILES} miles; valid WeatherCode and Period",
            "distance_denominator_resolution_miles": DISTANCE_RESOLUTION_MILES,
            "base_formulas": "P_base=mean(fare_amount); D_base=mean(trip_distance), independently per fallback group",
            "epsilon_formula": "abs(((P-P_base)/P_base)/((D-D_base)/D_base))",
            "grouping": {"period": "Period across WeatherCodes", "weather": "WeatherCode across Periods", "global": "all valid training rows"},
            "period_group_count": int((frame.fallback_level == "period").sum()),
            "weather_group_count": int((frame.fallback_level == "weather").sum()),
            "global_group_count": int((frame.fallback_level == "global").sum()),
            "output_artifact": str(ARTIFACT.relative_to(ROOT)),
            "output_sha256": sha256(ARTIFACT),
        }
        METADATA.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(frame.groupby("fallback_level", sort=False).size().to_dict())
    print(f"artifact={ARTIFACT.relative_to(ROOT)} sha256={sha256(ARTIFACT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
