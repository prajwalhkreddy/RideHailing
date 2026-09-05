"""Raw pricing supply from available idle and known incoming vehicles."""

from __future__ import annotations

from datetime import datetime, timedelta
import math
from typing import Iterable

import pandas as pd

from src.fleet.fleet import validate_fleet
from src.fleet.state import VehicleState, VehicleStatus


PRICING_SUPPLY_COLUMNS = ["grid_id", "idle_supply", "incoming_supply", "total_supply"]


def build_raw_pricing_supply(
    vehicles: Iterable[VehicleState],
    valid_grid_ids: Iterable[int],
    slot_start: datetime,
    main_slot_minutes: float = 30.0,
) -> pd.DataFrame:
    """Count IDLE vehicles now plus BUSY vehicles completing in ``(start, end]``.

    A BUSY vehicle is assigned to its already-known passenger destination. The
    function is read-only and returns unscaled integer counts for every grid.
    """
    items = list(vehicles)
    grids = sorted(set(valid_grid_ids))
    if not grids:
        raise ValueError("Pricing supply requires at least one valid GridID.")
    if not isinstance(slot_start, datetime):
        raise ValueError("slot_start must be a datetime.")
    duration = float(main_slot_minutes)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("main_slot_minutes must be finite and positive.")
    validate_fleet(items, grids)

    slot_end = slot_start + timedelta(minutes=duration)
    idle = {grid_id: 0 for grid_id in grids}
    incoming = {grid_id: 0 for grid_id in grids}
    for vehicle in items:
        if vehicle.trip_status is VehicleStatus.IDLE:
            idle[vehicle.current_grid] += 1
        elif vehicle.trip_status is VehicleStatus.BUSY:
            expected_completion = slot_start + timedelta(minutes=vehicle.remaining_travel_time)
            if slot_start < expected_completion <= slot_end:
                # BUSY-state validation guarantees a canonical destination.
                incoming[vehicle.destination] += 1  # type: ignore[index]

    result = pd.DataFrame({
        "grid_id": grids,
        "idle_supply": [idle[grid_id] for grid_id in grids],
        "incoming_supply": [incoming[grid_id] for grid_id in grids],
    })
    result["total_supply"] = result["idle_supply"] + result["incoming_supply"]
    result[PRICING_SUPPLY_COLUMNS[1:]] = result[PRICING_SUPPLY_COLUMNS[1:]].astype("int64")
    return result[PRICING_SUPPLY_COLUMNS]
