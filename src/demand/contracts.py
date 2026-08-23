"""Contracts and validation for the legacy-compatible NB3 demand master table."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEMAND_MASTER_COLUMNS = [
    "TimeSlot", "GridID", "Demand", "Row", "Column", "Temperature",
    "WindSpeed", "WeatherCode", "DayOfWeek", "Hour", "Minute", "Period",
    "TimeIndex", "HistoricalDemand",
]
GRID_LOOKUP_COLUMNS = {"GridID", "Row", "Column", "geometry"}
GRID_METADATA_FIELDS = {
    "data_month", "grid_rows", "grid_columns", "valid_cells", "metric_crs", "grid_size_meters",
}


def validate_grid_input_contract(
    grid: pd.DataFrame, mask: np.ndarray, metadata: dict[str, Any], month: str
) -> None:
    """Validate that first-milestone artifacts describe one coherent NB3 grid."""
    missing_columns = GRID_LOOKUP_COLUMNS - set(grid.columns)
    if missing_columns:
        raise ValueError(f"grid_lookup.parquet lacks required columns: {sorted(missing_columns)}")
    missing_metadata = GRID_METADATA_FIELDS - set(metadata)
    if missing_metadata:
        raise ValueError(f"grid_metadata.json lacks required fields: {sorted(missing_metadata)}")
    if metadata["data_month"] != month:
        raise ValueError(f"Grid metadata month {metadata['data_month']!r} does not match configured month {month!r}.")
    expected_shape = (int(metadata["grid_rows"]), int(metadata["grid_columns"]))
    if tuple(mask.shape) != expected_shape:
        raise ValueError(f"Grid mask shape {mask.shape} does not match metadata dimensions {expected_shape}.")
    if len(grid) != int(metadata["valid_cells"]) or int(mask.sum()) != len(grid):
        raise ValueError("Grid lookup, mask, and metadata disagree on valid cell count.")
    if grid["GridID"].duplicated().any() or grid[["Row", "Column"]].duplicated().any():
        raise ValueError("Grid lookup contains duplicate GridIDs or Row/Column positions.")
    if grid["Row"].min() < 0 or grid["Column"].min() < 0:
        raise ValueError("Grid lookup contains negative Row or Column values.")
    if grid["Row"].max() >= expected_shape[0] or grid["Column"].max() >= expected_shape[1]:
        raise ValueError("Grid lookup positions exceed metadata dimensions.")


def validate_demand_master(
    demand_master: pd.DataFrame, grid: pd.DataFrame, month: str
) -> None:
    """Validate the fixed 14-column NB3 output contract and its key invariants."""
    if list(demand_master.columns) != DEMAND_MASTER_COLUMNS:
        raise ValueError("Demand master columns must match the fixed legacy NB3 column order.")
    if demand_master.empty or demand_master.isna().any().any():
        raise ValueError("Demand master must be non-empty and contain no missing values.")
    start = pd.Timestamp(f"{month}-01 00:00:00")
    end = start + pd.offsets.MonthBegin(1)
    time_slots = demand_master["TimeSlot"].drop_duplicates().sort_values()
    expected_slots = pd.date_range(start, end, freq="30min", inclusive="left")
    if not pd.DatetimeIndex(time_slots).equals(expected_slots):
        raise ValueError(f"Demand master must contain the complete 30-minute calendar for {month}.")
    valid_ids = set(grid["GridID"].astype(int))
    if set(demand_master["GridID"].astype(int)) != valid_ids:
        raise ValueError("Demand master GridIDs do not match the canonical grid lookup.")
    expected_rows = len(expected_slots) * len(grid)
    if len(demand_master) != expected_rows or demand_master[["TimeSlot", "GridID"]].duplicated().any():
        raise ValueError("Demand master must contain one row per valid GridID and TimeSlot.")
    if (demand_master["Demand"] < 0).any() or (demand_master["HistoricalDemand"] < 0).any():
        raise ValueError("Demand and HistoricalDemand must be non-negative.")


def demand_metadata_path(output_path: str | Path) -> Path:
    """Return the separate provenance sidecar without changing the 14-column table."""
    path = Path(output_path)
    return path.with_name(f"{path.stem}_metadata.json")
