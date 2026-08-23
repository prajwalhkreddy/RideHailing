"""Synthetic NB11 action masking, score selection, and EV reposition tests."""

from __future__ import annotations

import unittest

import pandas as pd

from src.charging.energy import EnergyParameters
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import (
    RoutingAction, RoutingParameters, build_grid_routing_features,
    build_routing_state, execute_reposition, select_action, valid_action_mask,
)
from src.simulation.statistics import OperationalStatistics


class RoutingBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75, 60, 7.5, 0.15, 30, .9, 75, .5, .05, .5, .7, .2)
        self.routing = RoutingParameters(15, 3, 30)
        self.stats = OperationalStatistics([0, 1, 2], .3).update_slot(0)
        supply = pd.DataFrame({"grid_id": [0, 1, 2], "supply_total": [1, 2, 3], "supply_idle": [1, 2, 3], "supply_busy": [0, 0, 0], "supply_charging": [0, 0, 0]})
        self.features = build_grid_routing_features({0: 1., 1: 2., 2: 3.}, supply, self.stats)
        self.neighbours = pd.DataFrame({"GridID": [1, 1], "NeighbourGridID": [0, 2], "Direction": ["north", "east"]})
        self.vehicle = VehicleState(7, 1, VehicleStatus.IDLE, None, 0, "idle", 30.)

    def test_state_contains_current_neighbour_vehicle_context_and_masks_boundaries(self) -> None:
        state = build_routing_state(self.vehicle, self.features, self.neighbours)
        self.assertEqual(state.current_features.grid_id, 1)
        self.assertEqual(state.action_features[RoutingAction.NORTH].grid_id, 0)
        self.assertIsNone(state.action_features[RoutingAction.SOUTH])
        self.assertEqual(valid_action_mask(state), {RoutingAction.STAY: True, RoutingAction.NORTH: True, RoutingAction.EAST: True, RoutingAction.SOUTH: False, RoutingAction.WEST: False})

    def test_external_argmax_ignores_invalid_actions_and_uses_fixed_tie_order(self) -> None:
        state = build_routing_state(self.vehicle, self.features, self.neighbours)
        scores = {RoutingAction.STAY: 1., RoutingAction.NORTH: 2., RoutingAction.EAST: 2., RoutingAction.SOUTH: 99., RoutingAction.WEST: 98.}
        self.assertEqual(select_action(state, scores), RoutingAction.NORTH)

    def test_duration_feasibility_and_energy_transition(self) -> None:
        self.assertEqual(self.routing.duration_minutes(), 12.)
        state = build_routing_state(self.vehicle, self.features, self.neighbours)
        transition = execute_reposition(self.vehicle, state, RoutingAction.EAST, self.routing, self.energy)
        self.assertEqual((transition.origin_grid, transition.destination_grid, transition.distance_km, transition.duration_minutes), (1, 2, 3., 12.))
        self.assertAlmostEqual(self.vehicle.energy_level, 29.55)
        self.assertEqual(self.vehicle.trip_status, VehicleStatus.IDLE)
        with self.assertRaisesRegex(ValueError, "feasibility"):
            RoutingParameters(15, 3, 10).validate()

    def test_low_energy_vehicle_cannot_reposition_and_crossing_trigger_enters_charging(self) -> None:
        low = VehicleState(8, 1, VehicleStatus.IDLE, None, 0, "idle", 15.)
        state = build_routing_state(low, self.features, self.neighbours)
        with self.assertRaisesRegex(ValueError, "requiring charging"):
            execute_reposition(low, state, RoutingAction.NORTH, self.routing, self.energy)
        crossing = VehicleState(9, 1, VehicleStatus.IDLE, None, 0, "idle", 15.1)
        transition = execute_reposition(crossing, build_routing_state(crossing, self.features, self.neighbours), RoutingAction.NORTH, self.routing, self.energy)
        self.assertEqual((transition.status_after, crossing.trip_status, crossing.current_grid), (VehicleStatus.CHARGING, VehicleStatus.CHARGING, 0))

    def test_stay_is_zero_distance_zero_energy(self) -> None:
        state = build_routing_state(self.vehicle, self.features, self.neighbours)
        transition = execute_reposition(self.vehicle, state, RoutingAction.STAY, self.routing, self.energy)
        self.assertEqual((transition.distance_km, transition.duration_minutes, self.vehicle.energy_level), (0., 0., 30.))


if __name__ == "__main__":
    unittest.main()
