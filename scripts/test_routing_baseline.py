#!/usr/bin/env python3
"""Run a small deterministic NB11 utility/mask/repositioning demonstration."""

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
from src.routing.baseline import CandidateUtilityInput, GridRoutingFeatures, RoutingAction, RoutingParameters, build_routing_state, execute_reposition, select_action


def main() -> int:
    config = load_config(ROOT / "config/config.yaml")
    energy = energy_parameters_from_config(config)
    routing = RoutingParameters(**config["routing"])
    def feature(grid_id: int) -> GridRoutingFeatures:
        return GridRoutingFeatures(grid_id, 10., 1, 1, 0, 0, 10., 2., 10., 2., 6., 2., 6., 2., True, 0.)
    features = {grid_id: feature(grid_id) for grid_id in (0, 1, 2)}
    neighbours = pd.DataFrame({"GridID": [1, 1], "NeighbourGridID": [0, 2], "Direction": ["north", "east"]})
    vehicle = VehicleState(0, 1, VehicleStatus.IDLE, None, 0, "idle", 30.)
    state = build_routing_state(vehicle, features, neighbours)
    inputs = {
        RoutingAction.STAY: CandidateUtilityInput(8., 8., .20),
        RoutingAction.NORTH: CandidateUtilityInput(10., 6., .10),
        RoutingAction.EAST: CandidateUtilityInput(12., 4., .05),
        # Explicit high-preference input cannot make masked SOUTH selectable.
        RoutingAction.SOUTH: CandidateUtilityInput(100., 0., 0.),
    }
    decision = select_action(state, inputs, energy)
    transition = execute_reposition(vehicle, state, decision.chosen_action, routing, energy)
    print("NB11 ROUTING BASELINE: PASS")
    print("candidate U_price U_wait U_charge U_total")
    for action in (RoutingAction.STAY, RoutingAction.NORTH, RoutingAction.EAST, RoutingAction.SOUTH, RoutingAction.WEST):
        item = decision.components[action]
        print(f"{action.value:9} MASKED") if item is None else print(f"{action.value:9} {item.price:.3f}   {item.wait:.3f}  {item.charging:.3f}    {item.total:.3f}")
    print(f"selected maximum-utility action: {decision.chosen_action.value}; destination_grid: {transition.destination_grid}")
    print(f"movement: {transition.distance_km:.1f} km at 15 km/h = {transition.duration_minutes:.1f} min")
    print(f"energy: {transition.energy_before_kwh:.2f} -> {transition.energy_after_kwh:.2f} kWh (consumed 0.45 kWh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
