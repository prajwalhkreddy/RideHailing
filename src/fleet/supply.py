"""Canonical GridID-level fleet supply aggregation and reconciliation."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from src.fleet.state import VehicleState, VehicleStatus


SUPPLY_COLUMNS = ["grid_id", "supply_total", "supply_idle", "supply_busy", "supply_charging"]


def aggregate_grid_supply(fleet: Iterable[VehicleState], valid_grid_ids: Iterable[int]) -> pd.DataFrame:
    """Aggregate every canonical grid, retaining zero-supply cells."""
    grid_ids = sorted(set(valid_grid_ids))
    vehicle_rows = [(vehicle.current_grid, vehicle.trip_status.value) for vehicle in fleet]
    counts = pd.DataFrame(vehicle_rows, columns=["grid_id", "trip_status"])
    supply = pd.DataFrame({"grid_id": grid_ids})
    if not counts.empty:
        totals = counts.groupby("grid_id", observed=True).size().rename("supply_total")
        supply = supply.join(totals, on="grid_id")
        for status, column in ((VehicleStatus.IDLE, "supply_idle"), (VehicleStatus.BUSY, "supply_busy"), (VehicleStatus.CHARGING, "supply_charging")):
            status_counts = counts[counts["trip_status"] == status.value].groupby("grid_id", observed=True).size().rename(column)
            supply = supply.join(status_counts, on="grid_id")
    for column in SUPPLY_COLUMNS[1:]:
        if column not in supply:
            supply[column] = 0
        supply[column] = supply[column].fillna(0).astype("int64")
    validate_grid_supply(supply, len(vehicle_rows), grid_ids)
    return supply[SUPPLY_COLUMNS]


def validate_grid_supply(supply: pd.DataFrame, fleet_size: int, valid_grid_ids: Iterable[int]) -> None:
    """Enforce per-grid and fleet-wide supply invariants."""
    grids = sorted(set(valid_grid_ids))
    if supply.columns.tolist() != SUPPLY_COLUMNS:
        raise ValueError("Grid supply schema is incompatible with the fleet contract.")
    if supply["grid_id"].tolist() != grids:
        raise ValueError("Grid supply must contain every canonical GridID exactly once in order.")
    statuses = supply[["supply_idle", "supply_busy", "supply_charging"]].sum(axis=1)
    if not statuses.equals(supply["supply_total"]):
        raise ValueError("Grid supply status totals do not reconcile per grid.")
    if int(supply["supply_total"].sum()) != fleet_size:
        raise ValueError("Grid supply total does not reconcile with fleet size.")

