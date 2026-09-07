#!/usr/bin/env python3
"""Build the frozen pre-cutoff NB9 fare-prior artifact."""
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import pandas as pd
from src.pricing.historical_sensitivity import TRAINING_END_EXCLUSIVE
from src.routing.production import build_fare_bootstrap, sha256_file

def main() -> int:
    source = ROOT / "data/processed/cleaned_trips.parquet"
    grid_source = ROOT / "data/processed/grid_lookup.parquet"
    output = ROOT / "data/processed/nb9_fare_bootstrap_2026_01_25_1830.parquet"
    metadata_path = output.with_name(output.stem + "_metadata.json")
    trips = pd.read_parquet(source, columns=["tpep_pickup_datetime", "fare_amount", "PUGridID"])
    grids = pd.read_parquet(grid_source, columns=["GridID"]).GridID.astype(int)
    artifact, summary = build_fare_bootstrap(trips, grids)
    artifact.to_parquet(output, index=False)
    metadata = {"training_cutoff_exclusive": TRAINING_END_EXCLUSIVE.isoformat(), "source_file": str(source.relative_to(ROOT)), "validity": "finite fare_amount > 0; finite canonical PUGridID; pickup before cutoff", "grouping": "PUGridID", "standard_deviation_ddof": 0, **summary, "parquet_sha256": sha256_file(output), "purpose": "historical initialization only; not a held-out outcome or NB9 current-slot observation"}
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(output), "metadata": str(metadata_path), "metadata_sha256": sha256_file(metadata_path), **metadata}, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
