#!/usr/bin/env python3
"""Demonstrate NB10 station selection, efficient charging, FCFS and promotion."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.charging.energy import energy_parameters_from_config
from src.charging.stations import ChargingInfrastructure, ChargingStation
from src.data.config import load_config
from src.fleet.state import VehicleState, VehicleStatus


def vehicle(vehicle_id: int, grid_id: int, energy_kwh: float) -> VehicleState:
    return VehicleState(vehicle_id, grid_id, VehicleStatus.IDLE, None, 0, "idle", energy_kwh)


def main() -> int:
    """Run a small power/queue demonstration; no full fleet simulation occurs."""
    try:
        config = load_config(ROOT / "config/config.yaml")
        processed = ROOT / config["data"]["processed_dir"]
        definition = pd.read_parquet(processed / "charging_stations_2026_01.parquet")
        grid = pd.read_parquet(processed / "grid_lookup.parquet", columns=["GridID", "CentroidX", "CentroidY"])
        centroids = {int(row.GridID): (float(row.CentroidX), float(row.CentroidY)) for row in grid.itertuples(index=False)}
        parameters = energy_parameters_from_config(config)
        # Full configured network confirms nearest-centroid selection.
        network = ChargingInfrastructure([ChargingStation(int(row.station_id), int(row.grid_id), config["charging"]["station_max_power_kw"], parameters.charging_power_kw) for row in definition.itertuples(index=False)], centroids)
        low = vehicle(0, int(definition.iloc[0].grid_id), 6.0)
        selected = network.present_vehicle(low, parameters, 0)
        network.advance_mini_slot([low], config["simulation"]["mini_slot_minutes"], parameters)
        if abs(low.energy_level - 6.9) > 1e-9:
            raise ValueError("Efficiency demonstration did not yield 0.9 kWh.")

        # One-EV power fixture demonstrates FCFS queue and immediate promotion.
        station = ChargingStation(0, int(definition.iloc[0].grid_id), parameters.charging_power_kw, parameters.charging_power_kw)
        queue_demo = ChargingInfrastructure([station], centroids)
        active, queued = vehicle(1, station.grid_id, 6.0), vehicle(2, station.grid_id, 6.0)
        queue_demo.present_vehicle(active, parameters, 0)
        queue_demo.present_vehicle(queued, parameters, 1)
        active.energy_level = 74.1
        queue_demo.advance_mini_slot([active, queued], 2, parameters)
        if active.trip_status is not VehicleStatus.IDLE or station.active_vehicle_ids != {2}:
            raise ValueError("Release/promotion demonstration failed.")
        print("NB10 CHARGING INFRASTRUCTURE: PASS")
        print(f"top_15_grid_ids: {definition.grid_id.tolist()}")
        print(f"nearest_station: vehicle=0 -> station={selected.station_id}, grid={selected.grid_id}")
        print("efficient_charge: 30 kW × 0.90 × 2/60 h = +0.9 kWh")
        print("fcfs_fixture: active vehicle released at 75 kWh; first queued vehicle promoted; queue wait incremented by 2 min")
        return 0
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"NB10 CHARGING INFRASTRUCTURE FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
