"""Offline historical price-distance sensitivity preprocessing.

This module implements Phase 1 only.  It does not sample customers, construct
``P_max``, make acceptance decisions, or alter online pricing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd


METHODOLOGY_VERSION = "customer_price_distance_sensitivity_wt_v1_1"
TRAINING_START = pd.Timestamp("2026-01-01 00:00:00")
TRAINING_END_EXCLUSIVE = pd.Timestamp("2026-01-25 18:30:00")
DISTANCE_MAX_MILES = 100.0
DISTANCE_RESOLUTION_MILES = 0.01
GROUP_KEYS = ["WeatherCode", "Period"]
DIAGNOSTIC_COLUMNS = [
    "tpep_pickup_datetime", "PUGridID", "DOGridID", "WeatherCode", "Period",
    "fare_amount", "trip_distance", "P_base", "D_base", "DeltaP", "DeltaD", "epsilon",
]
GROUP_COLUMNS = [
    "WeatherCode", "Period", "sample_count_raw", "sample_count_valid",
    "excluded_zero_delta_d_count", "excluded_below_distance_resolution_count",
    "P_base", "D_base", "epsilon_mean",
    "epsilon_median", "epsilon_std_population", "epsilon_std_sample",
    "epsilon_min", "epsilon_p01", "epsilon_p05", "epsilon_p25",
    "epsilon_p75", "epsilon_p95", "epsilon_p99", "epsilon_max",
]
FALLBACK_METHODOLOGY_VERSION = "customer_price_distance_sensitivity_hierarchical_fallback_v1"
FALLBACK_COLUMNS = [
    "fallback_level", "WeatherCode", "Period", "sample_count",
    "P_base", "D_base", "epsilon_mean", "epsilon_std_population",
]


@dataclass(frozen=True)
class HistoricalSensitivityResult:
    """Deterministic Phase-1 group output, diagnostics, and filter counts."""

    groups: pd.DataFrame
    observations: pd.DataFrame
    counts: Mapping[str, int]
    valid_inputs: pd.DataFrame | None = None


def build_sensitivity_fallbacks(
    trips: pd.DataFrame,
    weather_time_lookup: pd.DataFrame,
    *,
    training_start: pd.Timestamp = TRAINING_START,
    training_end_exclusive: pd.Timestamp = TRAINING_END_EXCLUSIVE,
) -> pd.DataFrame:
    """Recompute internally consistent Period/Weather/Global parameters."""
    exact = preprocess_historical_sensitivity(
        trips, weather_time_lookup, training_start=training_start,
        training_end_exclusive=training_end_exclusive,
    )
    if exact.valid_inputs is None:
        raise ValueError("Fallback construction requires valid Phase-1.1 training inputs.")
    valid = exact.valid_inputs.copy(deep=True)

    def aggregate(level: str, keys: list[str]) -> pd.DataFrame:
        work = valid.copy(deep=True)
        if keys:
            bases = work.groupby(keys, observed=True).agg(
                P_base=("fare_amount", "mean"), D_base=("trip_distance", "mean"),
            )
            work = work.join(bases, on=keys)
        else:
            bases = pd.DataFrame({
                "P_base": [work["fare_amount"].mean()],
                "D_base": [work["trip_distance"].mean()],
            })
            work["P_base"], work["D_base"] = bases.at[0, "P_base"], bases.at[0, "D_base"]
        difference = (work["trip_distance"] - work["D_base"]).abs()
        tolerance = np.finfo(np.float64).eps * 8 * np.maximum.reduce([
            np.ones(len(work)), work["trip_distance"].abs().to_numpy(), work["D_base"].abs().to_numpy(),
        ])
        eligible = work.loc[difference + tolerance >= DISTANCE_RESOLUTION_MILES].copy()
        eligible["DeltaP"] = (eligible["fare_amount"] - eligible["P_base"]) / eligible["P_base"]
        eligible["DeltaD"] = (eligible["trip_distance"] - eligible["D_base"]) / eligible["D_base"]
        eligible["epsilon"] = (eligible["DeltaP"] / eligible["DeltaD"]).abs()
        if keys:
            epsilon = eligible.groupby(keys, observed=True)["epsilon"].agg(
                sample_count="size", epsilon_mean="mean",
                epsilon_std_population=lambda values: values.std(ddof=0),
            )
            result = bases.join(epsilon).reset_index()
        else:
            result = bases.assign(
                sample_count=len(eligible), epsilon_mean=eligible["epsilon"].mean(),
                epsilon_std_population=eligible["epsilon"].std(ddof=0),
            )
        result.insert(0, "fallback_level", level)
        if "WeatherCode" not in result:
            result["WeatherCode"] = np.nan
        if "Period" not in result:
            result["Period"] = pd.NA
        return result[FALLBACK_COLUMNS]

    result = pd.concat([
        aggregate("period", ["Period"]), aggregate("weather", ["WeatherCode"]),
        aggregate("global", []),
    ], ignore_index=True)
    result["Period"] = result["Period"].astype("Int64")
    numeric = result[["sample_count", "P_base", "D_base", "epsilon_mean", "epsilon_std_population"]]
    if not np.isfinite(numeric.to_numpy(dtype=np.float64)).all():
        raise ValueError("Fallback sensitivity parameters must be finite.")
    if (result[["sample_count", "P_base", "D_base"]] <= 0).any().any() or (result[["epsilon_mean", "epsilon_std_population"]] < 0).any().any():
        raise ValueError("Fallback bases/counts must be positive and epsilon statistics non-negative.")
    result["sample_count"] = result["sample_count"].astype("int64")
    return result.reset_index(drop=True)


def build_weather_time_lookup(demand_master: pd.DataFrame) -> pd.DataFrame:
    """Return the existing NB3 weather/30-minute-period mapping by TimeSlot."""
    required = {"TimeSlot", "WeatherCode", "Period"}
    if missing := required - set(demand_master.columns):
        raise ValueError(f"Demand master lacks weather/time columns: {sorted(missing)}")
    lookup = demand_master[["TimeSlot", "WeatherCode", "Period"]].copy()
    lookup["TimeSlot"] = pd.to_datetime(lookup["TimeSlot"], errors="coerce")
    if lookup["TimeSlot"].isna().any():
        raise ValueError("Demand-master TimeSlot values must be valid timestamps.")
    conflicts = lookup.groupby("TimeSlot", observed=True)[["WeatherCode", "Period"]].nunique(dropna=False)
    if (conflicts > 1).any().any():
        raise ValueError("WeatherCode and Period must be unique for each TimeSlot.")
    lookup = lookup.drop_duplicates("TimeSlot").sort_values("TimeSlot").reset_index(drop=True)
    expected_period = lookup["TimeSlot"].dt.hour * 2 + lookup["TimeSlot"].dt.minute // 30
    numeric_period = pd.to_numeric(lookup["Period"], errors="coerce")
    if numeric_period.isna().any() or not np.array_equal(numeric_period.to_numpy(), expected_period.to_numpy()):
        raise ValueError("Period does not follow the existing 48-period NB3 convention.")
    lookup["Period"] = numeric_period.astype(np.int8)
    return lookup


def _group_quantile(values: pd.core.groupby.SeriesGroupBy, quantile: float) -> pd.Series:
    return values.quantile(quantile)


def preprocess_historical_sensitivity(
    trips: pd.DataFrame,
    weather_time_lookup: pd.DataFrame,
    *,
    training_start: pd.Timestamp = TRAINING_START,
    training_end_exclusive: pd.Timestamp = TRAINING_END_EXCLUSIVE,
) -> HistoricalSensitivityResult:
    """Calculate raw professor-approved ``abs(DeltaP / DeltaD)`` by W,T.

    Invalid-reason counts are condition counts and can overlap.  Group
    ``sample_count_raw`` is the reference-period count with valid W,T context;
    ``sample_count_valid`` is the final finite epsilon count after the explicit
    raw-distance-resolution exclusion.
    """
    required = {"tpep_pickup_datetime", "fare_amount", "trip_distance"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack sensitivity columns: {sorted(missing)}")
    start, end = pd.Timestamp(training_start), pd.Timestamp(training_end_exclusive)
    if start.tz is not None or end.tz is not None or not start < end:
        raise ValueError("Training boundaries must be ordered timezone-naive timestamps.")

    source = trips.copy(deep=True)
    pickup = pd.to_datetime(source["tpep_pickup_datetime"], errors="coerce")
    invalid_timestamp = pickup.isna()
    in_period = pickup.notna() & (pickup >= start) & (pickup < end)
    training = source.loc[in_period].copy()
    training["tpep_pickup_datetime"] = pickup.loc[in_period]
    training["TimeSlot"] = training["tpep_pickup_datetime"].dt.floor("30min")

    lookup = build_weather_time_lookup(weather_time_lookup)
    training = training.merge(lookup, on="TimeSlot", how="left", validate="many_to_one")
    fare = pd.to_numeric(training["fare_amount"], errors="coerce")
    distance = pd.to_numeric(training["trip_distance"], errors="coerce")
    weather = pd.to_numeric(training["WeatherCode"], errors="coerce")
    period = pd.to_numeric(training["Period"], errors="coerce")
    invalid_fare = ~np.isfinite(fare) | (fare <= 0)
    invalid_distance = ~np.isfinite(distance) | (distance <= 0)
    distance_above_maximum = np.isfinite(distance) & (distance > DISTANCE_MAX_MILES)
    invalid_weather = ~np.isfinite(weather)
    invalid_period = ~np.isfinite(period) | (period < 0) | (period > 47) | (period % 1 != 0)
    valid_context = ~invalid_weather & ~invalid_period
    valid_input = valid_context & ~invalid_fare & ~invalid_distance & ~distance_above_maximum

    training["fare_amount"] = fare
    training["trip_distance"] = distance
    training["WeatherCode"] = weather
    training["Period"] = period
    raw_counts = (
        training.loc[valid_context].groupby(GROUP_KEYS, observed=True).size().rename("sample_count_raw")
    )
    valid = training.loc[valid_input].copy()
    if valid.empty:
        raise ValueError("No valid historical sensitivity observations remain.")
    bases = valid.groupby(GROUP_KEYS, observed=True).agg(
        P_base=("fare_amount", "mean"), D_base=("trip_distance", "mean"),
    )
    if (~np.isfinite(bases.to_numpy())).any() or (bases <= 0).any().any():
        raise ValueError("Every W,T group requires finite positive base values.")
    valid = valid.join(bases, on=GROUP_KEYS)
    raw_distance_difference = (valid["trip_distance"] - valid["D_base"]).abs()
    comparison_tolerance = np.finfo(np.float64).eps * 8 * np.maximum.reduce([
        np.ones(len(valid)), valid["trip_distance"].abs().to_numpy(), valid["D_base"].abs().to_numpy(),
    ])
    below_resolution = raw_distance_difference + comparison_tolerance < DISTANCE_RESOLUTION_MILES
    numerical_zero = raw_distance_difference <= comparison_tolerance
    zero_counts = valid.loc[numerical_zero].groupby(GROUP_KEYS, observed=True).size().rename(
        "excluded_zero_delta_d_count"
    )
    resolution_counts = valid.loc[below_resolution].groupby(GROUP_KEYS, observed=True).size().rename(
        "excluded_below_distance_resolution_count"
    )
    observations = valid.loc[~below_resolution].copy()
    observations["DeltaP"] = (observations["fare_amount"] - observations["P_base"]) / observations["P_base"]
    observations["DeltaD"] = (observations["trip_distance"] - observations["D_base"]) / observations["D_base"]
    observations["epsilon"] = (observations["DeltaP"] / observations["DeltaD"]).abs()
    if observations.empty or not np.isfinite(observations["epsilon"]).all():
        raise ValueError("Sensitivity calculation produced no finite observations.")
    if (observations["epsilon"] < 0).any():
        raise ValueError("Historical sensitivity magnitudes must be non-negative.")

    grouped = observations.groupby(GROUP_KEYS, observed=True)["epsilon"]
    groups = pd.DataFrame({
        "sample_count_valid": grouped.size(),
        "epsilon_mean": grouped.mean(),
        "epsilon_median": grouped.median(),
        "epsilon_std_population": grouped.std(ddof=0),
        "epsilon_std_sample": grouped.std(ddof=1),
        "epsilon_min": grouped.min(),
        "epsilon_p01": _group_quantile(grouped, .01),
        "epsilon_p05": _group_quantile(grouped, .05),
        "epsilon_p25": _group_quantile(grouped, .25),
        "epsilon_p75": _group_quantile(grouped, .75),
        "epsilon_p95": _group_quantile(grouped, .95),
        "epsilon_p99": _group_quantile(grouped, .99),
        "epsilon_max": grouped.max(),
    }).join(bases).join(raw_counts).join(zero_counts).join(resolution_counts)
    groups["excluded_zero_delta_d_count"] = groups["excluded_zero_delta_d_count"].fillna(0).astype("int64")
    groups["excluded_below_distance_resolution_count"] = groups[
        "excluded_below_distance_resolution_count"
    ].fillna(0).astype("int64")
    groups[["sample_count_raw", "sample_count_valid"]] = groups[["sample_count_raw", "sample_count_valid"]].astype("int64")
    groups = groups.reset_index()[GROUP_COLUMNS].sort_values(GROUP_KEYS).reset_index(drop=True)

    diagnostic = observations.reindex(columns=DIAGNOSTIC_COLUMNS).sort_values(
        ["tpep_pickup_datetime", "WeatherCode", "Period"], kind="stable"
    ).reset_index(drop=True)
    counts = {
        "input_row_count": int(len(source)),
        "excluded_invalid_timestamp_count": int(invalid_timestamp.sum()),
        "excluded_outside_training_period_count": int((pickup.notna() & ~in_period).sum()),
        "training_period_row_count": int(in_period.sum()),
        "excluded_invalid_fare_count": int(invalid_fare.sum()),
        "excluded_invalid_distance_count": int(invalid_distance.sum()),
        "excluded_distance_above_100_count": int(distance_above_maximum.sum()),
        "excluded_missing_weather_count": int(invalid_weather.sum()),
        "excluded_invalid_period_count": int(invalid_period.sum()),
        "valid_input_row_count": int(valid_input.sum()),
        "excluded_zero_delta_d_count": int(numerical_zero.sum()),
        "excluded_below_distance_resolution_count": int(below_resolution.sum()),
        "valid_epsilon_row_count": int(len(observations)),
        "observed_group_count": int(len(groups)),
    }
    return HistoricalSensitivityResult(
        groups, diagnostic, counts,
        valid[["WeatherCode", "Period", "fare_amount", "trip_distance"]].reset_index(drop=True),
    )


def validate_group_output(groups: pd.DataFrame) -> None:
    """Validate a persisted Phase-1 group artifact without changing it."""
    if groups.columns.tolist() != GROUP_COLUMNS or groups.empty:
        raise ValueError("Historical sensitivity group artifact has an invalid schema.")
    if groups.duplicated(GROUP_KEYS).any():
        raise ValueError("Historical sensitivity groups must be unique by W,T.")
    if not groups["Period"].between(0, 47).all():
        raise ValueError("Historical sensitivity Period must be in 0..47.")
    finite_columns = [column for column in GROUP_COLUMNS if column != "epsilon_std_sample"]
    if not np.isfinite(groups[finite_columns].to_numpy(dtype=np.float64)).all():
        raise ValueError("Historical sensitivity output contains non-finite required values.")
    if (groups[["P_base", "D_base"]] <= 0).any().any() or (groups.filter(like="epsilon_") < 0).any().any():
        raise ValueError("Base values must be positive and sensitivity statistics non-negative.")
    singleton = groups["sample_count_valid"] == 1
    if groups.loc[~singleton, "epsilon_std_sample"].isna().any() or groups.loc[singleton, "epsilon_std_sample"].notna().any():
        raise ValueError("Sample SD must use ddof=1 and remain unavailable for singleton groups.")
