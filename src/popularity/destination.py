"""Approved leakage-safe destination/drop-off popularity methodology."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Collection, Iterable

import numpy as np
import pandas as pd


SLOT_MINUTES = 30
WINDOW_SLOTS = 6
METHODOLOGY_VERSION = "destination_dropoff_trailing_6slot_global_quintiles_v1"
POPULARITY_LEVELS = ("Very Low", "Low", "Medium", "High", "Very High")
POPULARITY_ENCODING = {
    "Very Low": 0.00, "Low": 0.25, "Medium": 0.50,
    "High": 0.75, "Very High": 1.00,
}
POPULARITY_COLUMNS = [
    "TimeSlot", "GridID", "dropoff_count", "dropoff_ma_3h",
    "popularity_level", "popularity_value",
]


@dataclass(frozen=True)
class PopularityThresholds:
    q20: float
    q40: float
    q60: float
    q80: float
    reference_start: str
    reference_end_exclusive: str
    window_slots: int = WINDOW_SLOTS
    slot_minutes: int = SLOT_MINUTES
    methodology_version: str = METHODOLOGY_VERSION

    def __post_init__(self) -> None:
        values = (self.q20, self.q40, self.q60, self.q80)
        if not all(math.isfinite(value) for value in values) or tuple(sorted(values)) != values:
            raise ValueError("Popularity quintile thresholds must be finite and nondecreasing.")
        if self.window_slots != WINDOW_SLOTS or self.slot_minutes != SLOT_MINUTES:
            raise ValueError("Popularity thresholds require six 30-minute slots.")

    @property
    def duplicates_present(self) -> bool:
        return len({self.q20, self.q40, self.q60, self.q80}) < 4

    def to_metadata(self) -> dict:
        return {**asdict(self), "encoding": dict(POPULARITY_ENCODING), "duplicates_present": self.duplicates_present}

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(self.to_metadata(), handle, indent=2, sort_keys=True)


def aggregate_dropoffs(
    trips: pd.DataFrame,
    valid_grid_ids: Collection[int],
    time_slots: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Count empirical drop-offs by their drop-off slot and destination grid."""
    required = {"tpep_dropoff_datetime", "DOGridID"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack destination-popularity columns: {sorted(missing)}")
    grids = tuple(sorted(set(int(grid) for grid in valid_grid_ids)))
    slots = pd.DatetimeIndex(time_slots).sort_values().unique()
    if not grids or not len(slots):
        raise ValueError("Popularity aggregation requires grids and time slots.")
    if len(slots) > 1 and not (pd.Series(slots).diff().dropna() == pd.Timedelta(minutes=SLOT_MINUTES)).all():
        raise ValueError("Popularity time slots must be consecutive 30-minute boundaries.")
    work = trips[["tpep_dropoff_datetime", "DOGridID"]].copy()
    work["tpep_dropoff_datetime"] = pd.to_datetime(work["tpep_dropoff_datetime"], errors="raise")
    if work["tpep_dropoff_datetime"].dt.tz is not None:
        raise ValueError("Popularity requires timezone-naive timestamps consistent with frozen taxi data.")
    work["TimeSlot"] = work["tpep_dropoff_datetime"].dt.floor(f"{SLOT_MINUTES}min")
    work = work.loc[work["TimeSlot"].isin(slots) & work["DOGridID"].isin(grids)]
    counts = work.groupby(["TimeSlot", "DOGridID"], observed=True).size().rename("dropoff_count").reset_index().rename(columns={"DOGridID": "GridID"})
    complete = pd.MultiIndex.from_product([slots, grids], names=["TimeSlot", "GridID"]).to_frame(index=False)
    result = complete.merge(counts, on=["TimeSlot", "GridID"], how="left")
    result["GridID"] = result["GridID"].astype(np.int32)
    result["dropoff_count"] = result["dropoff_count"].fillna(0).astype(np.int32)
    return result.sort_values(["TimeSlot", "GridID"]).reset_index(drop=True)


def trailing_dropoff_average(counts: pd.DataFrame, window_slots: int = WINDOW_SLOTS) -> pd.DataFrame:
    """Add a strictly lagged SMA over up to six available prior slots."""
    if window_slots != WINDOW_SLOTS:
        raise ValueError("Approved destination popularity requires a six-slot window.")
    required = {"TimeSlot", "GridID", "dropoff_count"}
    if missing := required - set(counts.columns):
        raise ValueError(f"Drop-off counts lack columns: {sorted(missing)}")
    result = counts.sort_values(["GridID", "TimeSlot"]).reset_index(drop=True).copy()
    if (result["dropoff_count"] < 0).any() or result.duplicated(["TimeSlot", "GridID"]).any():
        raise ValueError("Drop-off counts must be non-negative and unique per grid-slot.")
    result["dropoff_ma_3h"] = result.groupby("GridID", sort=False)["dropoff_count"].transform(
        lambda values: values.shift(1).rolling(WINDOW_SLOTS, min_periods=1).mean()
    )
    return result.sort_values(["TimeSlot", "GridID"]).reset_index(drop=True)


def fit_popularity_thresholds(
    moving_averages: Iterable[float], *, reference_start, reference_end_exclusive,
) -> PopularityThresholds:
    """Fit fixed global quintiles from valid reference-period moving averages."""
    values = np.asarray(list(moving_averages), dtype=np.float64)
    values = values[np.isfinite(values)]
    if not len(values) or (values < 0).any():
        raise ValueError("Threshold fitting requires finite non-negative reference moving averages.")
    q20, q40, q60, q80 = np.quantile(values, [.2, .4, .6, .8])
    return PopularityThresholds(
        float(q20), float(q40), float(q60), float(q80),
        pd.Timestamp(reference_start).isoformat(), pd.Timestamp(reference_end_exclusive).isoformat(),
    )


def popularity_level(value: float, thresholds: PopularityThresholds) -> str:
    """Apply the approved inclusive-upper-bound classification exactly."""
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError("Popularity moving average must be finite and non-negative.")
    if number <= thresholds.q20:
        return "Very Low"
    if number <= thresholds.q40:
        return "Low"
    if number <= thresholds.q60:
        return "Medium"
    if number <= thresholds.q80:
        return "High"
    return "Very High"


def apply_popularity_levels(frame: pd.DataFrame, thresholds: PopularityThresholds) -> pd.DataFrame:
    """Apply fixed thresholds, retaining missing warm-up rows as unavailable."""
    if "dropoff_ma_3h" not in frame:
        raise ValueError("Popularity application requires dropoff_ma_3h.")
    result = frame.copy()
    valid = result["dropoff_ma_3h"].notna()
    result["popularity_level"] = pd.Series(pd.NA, index=result.index, dtype="string")
    result.loc[valid, "popularity_level"] = result.loc[valid, "dropoff_ma_3h"].map(lambda value: popularity_level(value, thresholds))
    result["popularity_value"] = result["popularity_level"].map(POPULARITY_ENCODING).astype(float)
    encoded = set(result.loc[valid, "popularity_value"].unique())
    if not encoded.issubset(set(POPULARITY_ENCODING.values())):
        raise ValueError("Popularity encoder emitted a non-approved value.")
    return result[POPULARITY_COLUMNS]


def build_destination_popularity(
    trips: pd.DataFrame,
    valid_grid_ids: Collection[int],
    time_slots: pd.DatetimeIndex,
    *,
    reference_start,
    reference_end_exclusive,
) -> tuple[pd.DataFrame, PopularityThresholds]:
    """Aggregate, lag, fit on the reference interval, and apply fixed thresholds."""
    moving = trailing_dropoff_average(aggregate_dropoffs(trips, valid_grid_ids, time_slots))
    start, end = pd.Timestamp(reference_start), pd.Timestamp(reference_end_exclusive)
    reference = moving.loc[(moving["TimeSlot"] >= start) & (moving["TimeSlot"] < end), "dropoff_ma_3h"]
    thresholds = fit_popularity_thresholds(reference, reference_start=start, reference_end_exclusive=end)
    return apply_popularity_levels(moving, thresholds), thresholds
