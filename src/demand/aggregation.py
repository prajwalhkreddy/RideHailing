"""Legacy-compatible NB3 tabular demand preparation; no tensors or CNN logic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.weather import WEATHER_COLUMNS
from src.demand.contracts import DEMAND_MASTER_COLUMNS


def month_bounds(month: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return timezone-naive legacy month boundaries for a ``YYYY-MM`` month."""
    try:
        start = pd.Timestamp(f"{month}-01 00:00:00")
    except ValueError as error:
        raise ValueError(f"Month must be formatted YYYY-MM, got {month!r}.") from error
    return start, start + pd.offsets.MonthBegin(1)


def build_time_slots(month: str, interval_minutes: int) -> pd.DatetimeIndex:
    """Create the complete NB3 calendar rather than inferring sparse coverage.

    The legacy notebook's January 2026 execution yielded all 1,488 half-hour
    slots. This function makes that observed calendar contract explicit while
    preserving the legacy 30-minute resolution.
    """
    if interval_minutes != 30:
        raise ValueError("NB3 requires the legacy 30-minute aggregation interval.")
    start, end = month_bounds(month)
    return pd.date_range(start, end, freq="30min", inclusive="left")


def aggregate_pickup_demand(trips: pd.DataFrame, month: str, interval_minutes: int) -> tuple[pd.DataFrame, int]:
    """Filter January pickups and count trips by ``(TimeSlot, PUGridID)``.

    NB3 intentionally ignores ``DOGridID``: its target is unweighted pickup
    count, not dropoff activity, fare, passenger count, or distance.
    """
    required = {"tpep_pickup_datetime", "PUGridID"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Cleaned trips lack required NB3 columns: {sorted(missing)}")
    work = trips[["tpep_pickup_datetime", "PUGridID"]].copy()
    work["tpep_pickup_datetime"] = pd.to_datetime(work["tpep_pickup_datetime"], errors="raise")
    if work["tpep_pickup_datetime"].dt.tz is not None:
        raise ValueError("Taxi pickup timestamps are timezone-aware; NB3 requires legacy naive timestamps.")
    work["TimeSlot"] = work["tpep_pickup_datetime"].dt.floor(f"{interval_minutes}min")
    start, end = month_bounds(month)
    work = work.loc[(work["TimeSlot"] >= start) & (work["TimeSlot"] < end)].copy()
    demand = (
        work.groupby(["TimeSlot", "PUGridID"], observed=True)
        .size()
        .reset_index(name="Demand")
        .rename(columns={"PUGridID": "GridID"})
    )
    demand["GridID"] = demand["GridID"].astype(np.int32)
    demand["Demand"] = demand["Demand"].astype(np.int16)
    return demand, len(work)


def complete_space_time_grid(
    demand: pd.DataFrame, grid: pd.DataFrame, time_slots: pd.DatetimeIndex
) -> pd.DataFrame:
    """Materialize every valid grid-time pair and zero-fill missing pickups."""
    required = {"GridID", "Row", "Column"}
    if missing := required - set(grid.columns):
        raise ValueError(f"Grid lookup lacks columns required for demand completion: {sorted(missing)}")
    grid_ids = grid["GridID"].sort_values().unique()
    space_time = pd.MultiIndex.from_product([time_slots, grid_ids], names=["TimeSlot", "GridID"]).to_frame(index=False)
    master = space_time.merge(demand, on=["TimeSlot", "GridID"], how="left")
    master["Demand"] = master["Demand"].fillna(0).astype(np.int16)
    master = master.merge(grid[["GridID", "Row", "Column"]], on="GridID", how="left")
    if master[["Row", "Column"]].isna().any().any():
        raise ValueError("A demand GridID could not be attached to canonical Row/Column coordinates.")
    return master.sort_values(["TimeSlot", "GridID"]).reset_index(drop=True)


def merge_hourly_weather(master: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Join each legacy hourly weather record to both corresponding demand slots."""
    weather_table = weather[WEATHER_COLUMNS].copy()
    weather_table["WeatherHour"] = weather_table["Datetime"].dt.floor("h")
    result = master.copy()
    result["WeatherHour"] = result["TimeSlot"].dt.floor("h")
    result = result.merge(weather_table[["WeatherHour", "Temperature", "WindSpeed", "WeatherCode"]], on="WeatherHour", how="left")
    result = result.drop(columns=["WeatherHour"])
    if result[["Temperature", "WindSpeed", "WeatherCode"]].isna().any().any():
        raise ValueError("Hourly weather join left missing values in the NB3 demand table.")
    return result


def add_temporal_features(master: pd.DataFrame) -> pd.DataFrame:
    """Add the exact legacy weekday/hour/minute/period/time-index fields."""
    result = master.copy()
    result["DayOfWeek"] = result["TimeSlot"].dt.dayofweek.astype(np.int8)
    result["Hour"] = result["TimeSlot"].dt.hour.astype(np.int8)
    result["Minute"] = result["TimeSlot"].dt.minute.astype(np.int8)
    result["Period"] = (result["Hour"] * 2 + (result["Minute"] // 30)).astype(np.int8)
    unique_slots = result["TimeSlot"].drop_duplicates().sort_values().reset_index(drop=True)
    time_lookup = pd.DataFrame({"TimeSlot": unique_slots, "TimeIndex": np.arange(len(unique_slots), dtype=np.int16)})
    return result.merge(time_lookup, on="TimeSlot", how="left")


def add_historical_demand(master: pd.DataFrame) -> pd.DataFrame:
    """Add strictly backward-looking legacy HistoricalDemand.

    Within each GridID/weekday/period group, the current count is subtracted
    from its cumulative sum before division. The first observation has no
    prior history and therefore receives the notebook's explicit value zero.
    """
    groups = ["GridID", "DayOfWeek", "Period"]
    result = master.sort_values(groups + ["TimeIndex"]).reset_index(drop=True).copy()
    prior_sum = result.groupby(groups)["Demand"].cumsum() - result["Demand"]
    prior_count = result.groupby(groups).cumcount()
    result["HistoricalDemand"] = (prior_sum / prior_count.replace(0, np.nan)).fillna(0).astype(np.float32)
    return result.sort_values(["TimeIndex", "GridID"]).reset_index(drop=True)[DEMAND_MASTER_COLUMNS]
