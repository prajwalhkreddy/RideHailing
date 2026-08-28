"""Focused deterministic NB11 utility, masking, and EV reposition tests."""

from __future__ import annotations
import unittest
import pandas as pd

from src.charging.energy import EnergyParameters
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import (
    CandidateUtilityInput, DegradationParameters, GridRoutingFeatures, RoutingAction,
    RoutingParameters, battery_degradation_cost, build_routing_state,
    candidate_utility, charging_time_to_full_minutes, charging_time_utility,
    execute_reposition, price_utility, select_action, valid_action_mask, wait_utility,
)


def _feature(grid_id: int, mean_fare: float = 10., std_fare: float = 2., mean_wait: float = 6., std_wait: float = 2.) -> GridRoutingFeatures:
    return GridRoutingFeatures(grid_id, 1., 1, 1, 0, 0, mean_fare, std_fare, mean_fare, std_fare, mean_wait, std_wait, mean_wait, std_wait, True, 0.)


class RoutingBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75, 60, 7.5, 0.15, 30, .9, 75, .5, .05, .5, .7, .2)
        self.routing = RoutingParameters(15, 3, 30)
        self.features = {0: _feature(0), 1: _feature(1), 2: _feature(2)}
        self.neighbours = pd.DataFrame({"GridID": [1, 1], "NeighbourGridID": [0, 2], "Direction": ["north", "east"]})
        self.vehicle = VehicleState(7, 1, VehicleStatus.IDLE, None, 0, "idle", 30.)

    def _state(self):
        return build_routing_state(self.vehicle, self.features, self.neighbours)

    def test_price_utility_piecewise_and_zero_sigma(self) -> None:
        self.assertEqual(price_utility(7., 10., 2.), 0.)
        self.assertEqual(price_utility(10., 10., 2.), .5)
        self.assertEqual(price_utility(13., 10., 2.), 1.)
        self.assertEqual(price_utility(9., 10., 0.), 0.)
        self.assertEqual(price_utility(10., 10., 0.), 1.)

    def test_wait_utility_decreases_and_handles_zero_sigma(self) -> None:
        self.assertEqual(wait_utility(4., 6., 2.), 1.)
        self.assertEqual(wait_utility(6., 6., 2.), .5)
        self.assertEqual(wait_utility(8., 6., 2.), 0.)
        self.assertEqual(wait_utility(6., 6., 0.), 1.)
        self.assertEqual(wait_utility(7., 6., 0.), 0.)

    def test_charging_time_utility_uses_nb10_effective_power(self) -> None:
        threshold = self.energy.battery_capacity_kwh * self.energy.charging_trigger_soc
        self.assertEqual(charging_time_utility(threshold, self.energy), 0.)
        self.assertGreater(charging_time_utility(60., self.energy), charging_time_utility(30., self.energy))
        self.assertEqual(charging_time_utility(75., self.energy), 1.)
        self.assertAlmostEqual(charging_time_to_full_minutes(60., self.energy), 15. / (30. * .9) * 60.)

    def test_degradation_paper_interface_is_explicit_raw_cost(self) -> None:
        parameters = DegradationParameters(2., 1000., 8.314, 298., .1, 30., 5., 2., 3, 10000., 75., 4., 1., 12000., 1000., .1)
        result = battery_degradation_cost(parameters)
        self.assertAlmostEqual(result.temperature_power_k, 301.)
        self.assertAlmostEqual(result.total_cost, result.temperature_cost + result.dod_cost)
        self.assertGreater(result.total_cost, 1.)
        with self.assertRaises(TypeError):
            DegradationParameters()  # type: ignore[call-arg]

    def test_equal_weight_candidate_utility_requires_normalized_penalty(self) -> None:
        components = candidate_utility(_feature(1), CandidateUtilityInput(10., 6., .1), 75., self.energy)
        self.assertEqual((components.price, components.wait, components.charging), (.5, .5, .9))
        self.assertAlmostEqual(components.total, (.5 + .5 + .9) / 3.)
        with self.assertRaisesRegex(ValueError, "normalized"):
            candidate_utility(_feature(1), CandidateUtilityInput(10., 6., 5.), 75., self.energy)

    def test_state_mask_maximum_utility_and_fixed_tie(self) -> None:
        state = self._state()
        inputs = {
            RoutingAction.STAY: CandidateUtilityInput(8., 8., .2),
            RoutingAction.NORTH: CandidateUtilityInput(12., 4., .1),
            RoutingAction.EAST: CandidateUtilityInput(12., 4., .1),
            RoutingAction.SOUTH: CandidateUtilityInput(100., 0., 0.),
        }
        decision = select_action(state, inputs, self.energy)
        self.assertEqual(decision.chosen_action, RoutingAction.NORTH)
        self.assertIsNone(decision.utility_vector[RoutingAction.SOUTH])
        self.assertEqual(decision.valid_action_mask, valid_action_mask(state))
        self.assertNotAlmostEqual(sum(value for value in decision.utility_vector.values() if value is not None), 1.)
        self.assertEqual({action for action, value in decision.components.items() if value is not None}, {RoutingAction.STAY, RoutingAction.NORTH, RoutingAction.EAST})

    def test_explicit_inputs_required_for_every_valid_candidate(self) -> None:
        with self.assertRaisesRegex(ValueError, "required"):
            select_action(self._state(), {RoutingAction.STAY: CandidateUtilityInput(10., 6., 0.)}, self.energy)

    def test_duration_feasibility_and_energy_transition(self) -> None:
        self.assertEqual(self.routing.duration_minutes(), 12.)
        transition = execute_reposition(self.vehicle, self._state(), RoutingAction.EAST, self.routing, self.energy)
        self.assertEqual((transition.origin_grid, transition.destination_grid, transition.distance_km, transition.duration_minutes), (1, 2, 3., 12.))
        self.assertAlmostEqual(self.vehicle.energy_level, 29.55)
        self.assertEqual(self.vehicle.trip_status, VehicleStatus.IDLE)
        with self.assertRaisesRegex(ValueError, "feasibility"):
            RoutingParameters(15, 3, 10).validate()

    def test_eligibility_energy_feasibility_and_post_move_charging(self) -> None:
        for status in (VehicleStatus.BUSY, VehicleStatus.CHARGING):
            vehicle = VehicleState(8, 1, status, 0 if status is VehicleStatus.BUSY else None, 2 if status is VehicleStatus.BUSY else 0, status.value.lower(), 30.)
            with self.assertRaisesRegex(ValueError, "Only idle"):
                execute_reposition(vehicle, build_routing_state(vehicle, self.features, self.neighbours), RoutingAction.NORTH, self.routing, self.energy)
        low = VehicleState(9, 1, VehicleStatus.IDLE, None, 0, "idle", 15.)
        with self.assertRaisesRegex(ValueError, "requiring charging"):
            execute_reposition(low, build_routing_state(low, self.features, self.neighbours), RoutingAction.NORTH, self.routing, self.energy)
        crossing = VehicleState(10, 1, VehicleStatus.IDLE, None, 0, "idle", 15.1)
        transition = execute_reposition(crossing, build_routing_state(crossing, self.features, self.neighbours), RoutingAction.NORTH, self.routing, self.energy)
        self.assertEqual((transition.status_after, crossing.trip_status), (VehicleStatus.CHARGING, VehicleStatus.CHARGING))

    def test_stay_is_zero_distance_zero_energy(self) -> None:
        transition = execute_reposition(self.vehicle, self._state(), RoutingAction.STAY, self.routing, self.energy)
        self.assertEqual((transition.distance_km, transition.duration_minutes, self.vehicle.energy_level), (0., 0., 30.))


if __name__ == "__main__":
    unittest.main()
