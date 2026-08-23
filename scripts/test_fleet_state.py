#!/usr/bin/env python3
"""Run the fleet/grid-supply milestone acceptance checks; no dispatch occurs."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data.config import load_config
from src.charging.energy import energy_parameters_from_config, initialize_ev_fleet
from src.fleet.fleet import Fleet, initialize_fleet, mini_slots_per_main_slot, validate_fleet
from src.fleet.supply import aggregate_grid_supply, validate_grid_supply
from src.fleet.state import VehicleStatus


def load_valid_grid_ids(config: dict) -> list[int]:
    """Load, but never rebuild, the authoritative canonical grid lookup."""
    path = ROOT / config["data"]["processed_dir"] / "grid_lookup.parquet"
    if not path.is_file():
        raise FileNotFoundError(f"Canonical grid artifact is missing: {path}")
    grid_ids = pd.read_parquet(path, columns=["GridID"])["GridID"].astype(int).tolist()
    if len(grid_ids) != len(set(grid_ids)):
        raise ValueError("Canonical grid lookup contains duplicate GridIDs.")
    return sorted(grid_ids)


def main() -> int:
    """Exercise only state/supply contracts using a representative 6-minute trip."""
    try:
        config = load_config(ROOT / "config/config.yaml")
        simulation = config["simulation"]
        valid_grid_ids = load_valid_grid_ids(config)
        slots = mini_slots_per_main_slot(simulation["main_slot_minutes"], simulation["mini_slot_minutes"])
        fleet = initialize_ev_fleet(simulation["fleet_size"], valid_grid_ids, config["random_seed"], energy_parameters_from_config(config), simulation["initialization_method"])
        validate_fleet(fleet, valid_grid_ids, simulation["fleet_size"])
        initial_supply = aggregate_grid_supply(fleet, valid_grid_ids)
        validate_grid_supply(initial_supply, simulation["fleet_size"], valid_grid_ids)

        stateful_fleet = Fleet(fleet, frozenset(valid_grid_ids), simulation["mini_slot_minutes"])
        vehicle = stateful_fleet.vehicle(0)
        destination = next(grid for grid in valid_grid_ids if grid != vehicle.current_grid)
        stateful_fleet.assign_busy(vehicle.vehicle_id, destination, travel_duration_minutes=6)
        for _ in range(3):
            stateful_fleet.advance_mini_slot()
        completed = stateful_fleet.vehicle(vehicle.vehicle_id)
        if not (completed.trip_status is VehicleStatus.IDLE and completed.current_grid == destination and completed.destination is None and completed.remaining_travel_time == 0):
            raise ValueError("Representative BUSY -> IDLE transition did not complete correctly.")
        final_supply = aggregate_grid_supply(stateful_fleet.vehicles, valid_grid_ids)
        validate_grid_supply(final_supply, simulation["fleet_size"], valid_grid_ids)
        counts = final_supply[["supply_idle", "supply_busy", "supply_charging"]].sum()
        print("FLEET STATE: PASS")
        print(f"fleet_size: {len(fleet)}")
        print(f"valid_grids: {len(valid_grid_ids)}")
        print(f"initial_statuses: idle={int(initial_supply.supply_idle.sum())}, busy={int(initial_supply.supply_busy.sum())}, charging={int(initial_supply.supply_charging.sum())}")
        print(f"mini_slots_per_main_slot: {slots}")
        print("representative_transition: IDLE -> BUSY (6 min) -> IDLE at destination")
        print(f"final_statuses: idle={int(counts.supply_idle)}, busy={int(counts.supply_busy)}, charging={int(counts.supply_charging)}")
        return 0
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"FLEET STATE FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
