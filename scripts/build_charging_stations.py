#!/usr/bin/env python3
"""Build or validate the auditable January-activity NB10 station definition."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.charging.stations import build_station_definition, save_station_definition, validate_station_definition
from src.data.config import load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Explicitly rebuild the NB10 station artifact.")
    parser.add_argument("--validate", action="store_true", help="Validate the persisted station artifact only.")
    args = parser.parse_args()
    try:
        config = load_config(ROOT / "config/config.yaml")
        processed = ROOT / config["data"]["processed_dir"]
        output = processed / "charging_stations_2026_01.parquet"
        grid = pd.read_parquet(processed / "grid_lookup.parquet", columns=["GridID"])
        valid = grid["GridID"].astype(int).tolist()
        if args.validate or (output.is_file() and not args.force):
            definition = pd.read_parquet(output)
        else:
            trips = pd.read_parquet(processed / "cleaned_trips.parquet", columns=["PUGridID", "DOGridID"])
            definition = build_station_definition(trips, valid, config["charging"]["number_of_charging_stations"])
            save_station_definition(output, definition)
        validate_station_definition(definition, valid, config["charging"]["number_of_charging_stations"])
        print("NB10 STATION DEFINITION: PASS")
        print(definition.to_string(index=False))
        return 0
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"NB10 STATION DEFINITION FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
