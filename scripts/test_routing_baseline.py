#!/usr/bin/env python3
"""Run a small deterministic NB11 score/mask/repositioning demonstration."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.charging.energy import energy_parameters_from_config
from src.data.config import load_config
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import RoutingAction, RoutingParameters, build_grid_routing_features, build_routing_state, execute_reposition, select_action, valid_action_mask
from src.simulation.statistics import OperationalStatistics


def main() -> int:
    config = load_config(ROOT / "config/config.yaml")
    energy = energy_parameters_from_config(config)
    routing = RoutingParameters(**config["routing"])
    stats = OperationalStatistics([0, 1, 2], config["statistics"]["ewma_alpha"]).update_slot(0)
    supply = pd.DataFrame({"grid_id": [0, 1, 2], "supply_total": [1, 2, 1], "supply_idle": [1, 2, 1], "supply_busy": [0, 0, 0], "supply_charging": [0, 0, 0]})
    features = build_grid_routing_features({0: 5., 1: 10., 2: 20.}, supply, stats)
    neighbours = pd.DataFrame({"GridID": [1, 1], "NeighbourGridID": [0, 2], "Direction": ["north", "east"]})
    vehicle = VehicleState(0, 1, VehicleStatus.IDLE, None, 0, "idle", 30.)
    state = build_routing_state(vehicle, features, neighbours)
    action = select_action(state, {RoutingAction.STAY: .1, RoutingAction.NORTH: .3, RoutingAction.EAST: .9, RoutingAction.SOUTH: 99., RoutingAction.WEST: 98.})
    transition = execute_reposition(vehicle, state, action, routing, energy)
    print("NB11 ROUTING BASELINE: PASS")
    print(f"mask: {valid_action_mask(state)}")
    print(f"selected_action: {action.value}; destination_grid: {transition.destination_grid}")
    print(f"movement: {transition.distance_km:.1f} km at 15 km/h = {transition.duration_minutes:.1f} min")
    print(f"energy: {transition.energy_before_kwh:.2f} -> {transition.energy_after_kwh:.2f} kWh (consumed 0.45 kWh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
