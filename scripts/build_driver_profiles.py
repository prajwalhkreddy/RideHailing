#!/usr/bin/env python3
"""Build the frozen seed-42 production driver-preference artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.pricing.historical_sensitivity import TRAINING_END_EXCLUSIVE
from src.routing.production import PROFILE_GENERATION_VERSION, generate_driver_profiles, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = ROOT / f"data/processed/driver_preferences_seed{args.seed}.parquet"
    metadata_path = output.with_name(output.stem + "_metadata.json")
    if (output.exists() or metadata_path.exists()) and not args.force:
        raise FileExistsError("Driver-profile artifacts already exist; pass --force to rebuild explicitly.")
    trips_path = ROOT / "data/processed/cleaned_trips.parquet"
    trips = pd.read_parquet(trips_path, columns=["tpep_pickup_datetime", "fare_amount"])
    profiles, calibration = generate_driver_profiles(trips, range(5000), seed=args.seed)
    profiles.to_parquet(output, index=False)
    metadata = {
        "seed": args.seed,
        "profile_generation_version": PROFILE_GENERATION_VERSION,
        "training_cutoff_exclusive": TRAINING_END_EXCLUSIVE.isoformat(),
        "fare_source": str(trips_path.relative_to(ROOT)),
        **calibration,
        "fare_validity": "finite fare_amount > 0 and pickup timestamp before cutoff",
        "wait_preference_source": "Synthetic project assumption",
        "wait_distribution": "Uniform(0,30 minutes)",
        "sampling_distribution": "uniform",
        "persistence": "fixed per driver for complete simulation",
        "profile_row_count": len(profiles),
        "parquet_sha256": sha256_file(output),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(output), "metadata": str(metadata_path), **metadata}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
