#!/usr/bin/env python3
"""Build or validate Phase-1 historical customer sensitivity artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.data.config import load_config
from src.pricing.historical_sensitivity import (
    DISTANCE_MAX_MILES, DISTANCE_RESOLUTION_MILES, GROUP_KEYS, METHODOLOGY_VERSION,
    TRAINING_END_EXCLUSIVE, TRAINING_START,
    build_weather_time_lookup, preprocess_historical_sensitivity, validate_group_output,
)


ARTIFACT_NAME = "customer_price_sensitivity_2026_01.parquet"
METADATA_NAME = "customer_price_sensitivity_2026_01_metadata.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _describe(values: pd.Series) -> dict[str, float | int]:
    series = values.astype(float)
    return {
        "count": int(series.count()), "min": float(series.min()),
        "median": float(series.median()), "mean": float(series.mean()),
        "p95": float(series.quantile(.95)), "max": float(series.max()),
    }


def _print_report(groups: pd.DataFrame, counts: dict[str, int]) -> None:
    print("CUSTOMER PRICE SENSITIVITY PHASE 1: PASS")
    for key, value in counts.items():
        print(f"{key}={value}")
    print(f"weather_code_count={groups.WeatherCode.nunique()}")
    print(f"weather_codes={groups.WeatherCode.sort_values().unique().tolist()}")
    print(f"period_min={int(groups.Period.min())} period_max={int(groups.Period.max())}")
    for name, values in (
        ("sample_count_valid", groups.sample_count_valid),
        ("P_base", groups.P_base), ("D_base", groups.D_base),
    ):
        print(f"{name}_distribution={json.dumps(_describe(values), sort_keys=True)}")


def _print_epsilon_report(observations: pd.DataFrame, groups: pd.DataFrame) -> None:
    epsilon = observations["epsilon"]
    summary = {
        "count": int(len(epsilon)), "mean": float(epsilon.mean()),
        "median": float(epsilon.median()), "std_sample": float(epsilon.std(ddof=1)),
        "p01": float(epsilon.quantile(.01)), "p05": float(epsilon.quantile(.05)),
        "p25": float(epsilon.quantile(.25)), "p75": float(epsilon.quantile(.75)),
        "p95": float(epsilon.quantile(.95)), "p99": float(epsilon.quantile(.99)),
        "max": float(epsilon.max()),
    }
    print(f"epsilon_distribution={json.dumps(summary, sort_keys=True)}")
    for threshold in (10, 100, 1_000, 10_000):
        print(f"epsilon_gt_{threshold}={int((epsilon > threshold).sum())}")
    columns = ["WeatherCode", "Period", "sample_count_valid", "excluded_zero_delta_d_count", "P_base", "D_base", "epsilon_mean", "epsilon_std_population"]
    print("highest_epsilon_mean:")
    print(groups.nlargest(10, "epsilon_mean")[columns].to_string(index=False))
    print("highest_epsilon_std_population:")
    print(groups.nlargest(10, "epsilon_std_population")[columns].to_string(index=False))
    print("smallest_valid_sample_count:")
    print(groups.sort_values(GROUP_KEYS + ["sample_count_valid"])[columns].sort_values("sample_count_valid", kind="stable").head(10).to_string(index=False))


def _metadata(
    *, source_trips: Path, source_weather: Path, source_demand: Path,
    output: Path, counts: dict[str, int], groups: pd.DataFrame,
) -> dict:
    return {
        "methodology_version": METHODOLOGY_VERSION,
        "source_trip_artifact": str(source_trips.relative_to(ROOT)),
        "source_trip_sha256": _sha256(source_trips),
        "source_weather_artifact": str(source_weather.relative_to(ROOT)),
        "source_weather_sha256": _sha256(source_weather),
        "weather_time_lookup_artifact": str(source_demand.relative_to(ROOT)),
        "weather_time_lookup_sha256": _sha256(source_demand),
        "training_start_inclusive": TRAINING_START.isoformat(),
        "training_cutoff_exclusive": TRAINING_END_EXCLUSIVE.isoformat(),
        "cutoff_policy": "pickup timestamp >= training start and < training cutoff",
        "price_field": "fare_amount", "price_validity": "finite and > 0",
        "distance_field": "trip_distance", "distance_unit": "miles",
        "distance_min_exclusive": 0,
        "distance_max_inclusive": DISTANCE_MAX_MILES,
        "distance_validity": "finite and > 0 and <= 100 miles",
        "distance_resolution": DISTANCE_RESOLUTION_MILES,
        "distance_resolution_unit": "miles",
        "grouping_keys": GROUP_KEYS,
        "base_price_rule": "arithmetic mean fare_amount within WeatherCode x Period",
        "base_distance_rule": "arithmetic mean trip_distance within WeatherCode x Period",
        "epsilon_formula": "abs(((P-P_base)/P_base)/((D-D_base)/D_base))",
        "epsilon_denominator_eligibility": "abs(trip_distance - D_base) >= 0.01 miles",
        "outlier_policy": "none; epsilon is not clipped, winsorized, capped, or truncated",
        "standard_deviations": {"epsilon_std_population": "ddof=0", "epsilon_std_sample": "ddof=1"},
        "filter_counts_note": "invalid-reason counts are independent condition counts and may overlap",
        **counts,
        "weather_code_values": [float(value) for value in sorted(groups.WeatherCode.unique())],
        "period_min": int(groups.Period.min()), "period_max": int(groups.Period.max()),
        "output_artifact": str(output.relative_to(ROOT)),
        "output_sha256": _sha256(output),
        "software": {
            "python": sys.version.split()[0], "pandas": pd.__version__,
            "numpy": np.__version__, "pyarrow": importlib.metadata.version("pyarrow"),
        },
        "phase_2_status": "not implemented: no sampling, distribution fit, P_max, acceptance, dispatch, reward, or LinUCB integration",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Explicitly rebuild existing derived artifacts.")
    parser.add_argument("--validate", action="store_true", help="Validate existing derived artifacts only.")
    args = parser.parse_args()
    config = load_config(ROOT / "config/config.yaml")
    processed = ROOT / config["data"]["processed_dir"]
    trips_path = processed / "cleaned_trips.parquet"
    weather_path = ROOT / config["data"]["weather_path"]
    demand_path = ROOT / config["data"]["demand_master_path"]
    artifact = processed / ARTIFACT_NAME
    metadata_path = processed / METADATA_NAME
    required = (trips_path, weather_path, demand_path)
    if missing := [str(path) for path in required if not path.is_file()]:
        raise FileNotFoundError(f"Missing Phase-1 input artifacts: {missing}")

    if args.validate or (artifact.is_file() and metadata_path.is_file() and not args.force):
        groups = pd.read_parquet(artifact)
        validate_group_output(groups)
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)
        if metadata.get("output_sha256") != _sha256(artifact):
            raise ValueError("Historical sensitivity artifact hash does not match metadata.")
        _print_report(groups, {key: int(metadata[key]) for key in (
            "input_row_count", "training_period_row_count", "valid_input_row_count",
            "valid_epsilon_row_count", "excluded_zero_delta_d_count",
            "excluded_distance_above_100_count", "excluded_below_distance_resolution_count",
            "observed_group_count",
        )})
        print(f"artifact={artifact.relative_to(ROOT)}")
        print(f"metadata={metadata_path.relative_to(ROOT)}")
        return 0

    trips = pd.read_parquet(trips_path, columns=[
        "tpep_pickup_datetime", "fare_amount", "trip_distance", "PUGridID", "DOGridID",
    ])
    demand = pd.read_parquet(demand_path, columns=["TimeSlot", "WeatherCode", "Period"])
    lookup = build_weather_time_lookup(demand)
    result = preprocess_historical_sensitivity(trips, lookup)
    validate_group_output(result.groups)
    result.groups.to_parquet(artifact, index=False)
    metadata = _metadata(
        source_trips=trips_path, source_weather=weather_path, source_demand=demand_path,
        output=artifact, counts=dict(result.counts), groups=result.groups,
    )
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    _print_report(result.groups, dict(result.counts))
    _print_epsilon_report(result.observations, result.groups)
    print(f"artifact={artifact.relative_to(ROOT)}")
    print(f"metadata={metadata_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
