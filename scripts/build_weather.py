#!/usr/bin/env python3
"""Build the legacy-compatible January 2026 Meteostat weather artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.config import load_config
from src.data.weather import (
    build_weather_metadata, fetch_hourly_weather, load_processed_weather,
    prepare_weather, save_weather, validate_weather, weather_metadata_path,
)


def parse_args() -> argparse.Namespace:
    """Parse weather-stage build and validation modes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", help="Validate existing weather only.")
    parser.add_argument("--force", action="store_true", help="Refetch and rebuild the weather artifact.")
    return parser.parse_args()


def validate_existing(output: Path, month: str) -> dict[str, object]:
    """Reload and validate the existing weather artifact and provenance sidecar."""
    weather = load_processed_weather(output, month)
    metadata_file = weather_metadata_path(output)
    if not metadata_file.is_file():
        raise FileNotFoundError(f"Weather provenance metadata is missing: {metadata_file}")
    with metadata_file.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    if metadata.get("meteostat_version") != "1.7.6":
        raise ValueError("Weather metadata does not record legacy Meteostat version 1.7.6.")
    return {"rows": len(weather), "first": str(weather["Datetime"].min()), "last": str(weather["Datetime"].max())}


def main() -> int:
    """Fetch, prepare, validate, and persist the legacy weather contract."""
    args = parse_args()
    config = load_config(ROOT / "config/config.yaml")
    weather_config = config["weather"]
    month = config["data"]["month"]
    output = ROOT / weather_config["output"]
    try:
        if args.validate:
            report = validate_existing(output, month)
            print("WEATHER VALIDATION: PASS")
            for key, value in report.items():
                print(f"{key}: {value}")
            return 0
        if output.is_file() and not args.force:
            report = validate_existing(output, month)
            print("EXISTING WEATHER ARTIFACT VALID: PASS")
            for key, value in report.items():
                print(f"{key}: {value}")
            return 0

        raw_weather = fetch_hourly_weather(
            weather_config["latitude"], weather_config["longitude"], weather_config["altitude_m"],
            weather_config["start"], weather_config["end"],
        )
        weather, fill_counts = prepare_weather(raw_weather)
        validate_weather(weather, month)
        metadata = build_weather_metadata(weather=weather, raw_row_count=len(raw_weather), fill_counts=fill_counts, config=weather_config)
        artifact, metadata_file = save_weather(weather, output, metadata)
        print("WEATHER BUILD: PASS")
        print(f"raw_rows: {len(raw_weather)}")
        print(f"processed_rows: {len(weather)}")
        print(f"missing_before_fill: {fill_counts['before_fill']}")
        print(f"missing_after_fill: {fill_counts['after_fill']}")
        print(f"artifact: {artifact.relative_to(ROOT)}")
        print(f"metadata: {metadata_file.relative_to(ROOT)}")
        return 0
    except (FileNotFoundError, RuntimeError, ValueError, KeyError) as error:
        print(f"WEATHER BUILD FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
