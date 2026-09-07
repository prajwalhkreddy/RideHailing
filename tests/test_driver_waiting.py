"""Focused driver/vehicle idle-wait semantics and NB9 attribution tests."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from src.charging.energy import EnergyParameters, charge_vehicle, enter_charging
from src.dispatch.dispatch import DriverWaitObservation, dispatch_requests
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import (
    GridRoutingFeatures, RoutingAction, RoutingParameters, build_routing_state,
    execute_reposition,
)


class DriverWaitingTests(unittest.TestCase):
    grids = frozenset((0, 1))
    neighbours = {0: (1,), 1: (0,)}
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)

    @staticmethod
    def idle(vehicle_id=0, grid=0, energy=40.) -> VehicleState:
        return VehicleState(vehicle_id, grid, VehicleStatus.IDLE, None, 0, "idle", energy)

    def fleet(self, *vehicles) -> Fleet:
        return Fleet(list(vehicles), self.grids, 2)

    def dispatch(self, fleet, *, origin=0, destination=1, request_id=0, request_time=0, slot_start_time=None):
        observations: list[DriverWaitObservation] = []
        request = RequestState(request_id, request_time, origin, destination)
        dispatch_requests([request], fleet, self.neighbours, 2, 15, driver_wait_observations=observations, slot_start_time=slot_start_time)
        return observations

    def test_initialization_increment_and_three_slots_before_dispatch(self) -> None:
        fleet = self.fleet(self.idle())
        vehicle = fleet.vehicle(0)
        self.assertEqual((vehicle.idle_wait_minutes, vehicle.idle_wait_grid), (0, 0))
        fleet.advance_mini_slot(); self.assertEqual(vehicle.idle_wait_minutes, 2)
        fleet.advance_mini_slot(); fleet.advance_mini_slot()
        observations = self.dispatch(fleet)
        self.assertEqual(observations, [DriverWaitObservation(0, 0, 6.)])
        self.assertEqual((vehicle.trip_status, vehicle.idle_wait_minutes, vehicle.idle_wait_grid), (VehicleStatus.BUSY, 0, None))

    def test_nonidle_states_do_not_increment_and_completions_start_zero(self) -> None:
        busy = VehicleState(0, 0, VehicleStatus.BUSY, 1, 2, "transporting", 40.)
        charging = VehicleState(1, 0, VehicleStatus.CHARGING, None, 0, "charging", 74.5)
        fleet = self.fleet(busy, charging)
        fleet.advance_mini_slot()
        self.assertEqual((busy.trip_status, busy.current_grid, busy.idle_wait_minutes, busy.idle_wait_grid), (VehicleStatus.IDLE, 1, 0, 1))
        self.assertEqual((charging.idle_wait_minutes, charging.idle_wait_grid), (0, None))
        charge_vehicle(charging, 2, self.energy)
        self.assertEqual((charging.trip_status, charging.idle_wait_minutes, charging.idle_wait_grid), (VehicleStatus.IDLE, 0, 0))

    def test_neighbor_dispatch_attributes_wait_to_vehicle_grid(self) -> None:
        fleet = self.fleet(self.idle(grid=1))
        for _ in range(3): fleet.advance_mini_slot()
        observations = self.dispatch(fleet, origin=0)
        self.assertEqual(observations, [DriverWaitObservation(0, 1, 6.)])

    def test_cross_main_slot_boundary_preserves_active_wait(self) -> None:
        fleet = self.fleet(self.idle())
        for _ in range(16): fleet.advance_mini_slot()
        self.assertEqual(self.dispatch(fleet)[0].wait_minutes, 32)

    def test_stay_preserves_and_move_waits_for_arrival_before_restart(self) -> None:
        vehicle = self.idle()
        fleet = self.fleet(vehicle)
        for _ in range(3): fleet.advance_mini_slot()
        feature0 = GridRoutingFeatures(0, 1, 1, 1, 0, 0, 10, 1, 10, 1, 6, 1, 6, 1, True, 0)
        feature1 = GridRoutingFeatures(1, 1, 1, 1, 0, 0, 10, 1, 10, 1, 6, 1, 6, 1, True, 0)
        import pandas as pd
        neighbours = pd.DataFrame([(0, 1, "east")], columns=["GridID", "NeighbourGridID", "Direction"])
        state = build_routing_state(vehicle, {0: feature0, 1: feature1}, neighbours)
        execute_reposition(vehicle, state, RoutingAction.STAY, RoutingParameters(15, 3, 30), self.energy)
        self.assertEqual((vehicle.idle_wait_minutes, vehicle.idle_wait_grid), (6, 0))
        execute_reposition(vehicle, state, RoutingAction.EAST, RoutingParameters(15, 3, 30), self.energy)
        self.assertEqual((vehicle.current_grid, vehicle.trip_status, vehicle.remaining_travel_time, vehicle.idle_wait_grid), (0, VehicleStatus.BUSY, 12, None))
        for _ in range(5): fleet.advance_mini_slot()
        self.assertEqual((vehicle.current_grid, vehicle.trip_status, vehicle.remaining_travel_time, vehicle.idle_wait_grid), (0, VehicleStatus.BUSY, 2, None))
        fleet.advance_mini_slot()
        self.assertEqual((vehicle.current_grid, vehicle.trip_status, vehicle.idle_wait_minutes, vehicle.idle_wait_grid), (1, VehicleStatus.IDLE, 0, 1))
        for _ in range(3): fleet.advance_mini_slot()
        self.assertEqual(self.dispatch(fleet, origin=0)[0], DriverWaitObservation(0, 1, 6.))

    def test_completed_wait_records_assignment_clock_once(self) -> None:
        fleet = self.fleet(self.idle())
        for _ in range(3):
            fleet.advance_mini_slot()
        start = datetime(2026, 1, 1, 10, 0)
        observation = self.dispatch(fleet, request_time=3, slot_start_time=start)[0]
        self.assertEqual((observation.idle_start_time, observation.dispatch_time), (start, start + timedelta(minutes=6)))
        self.assertEqual(observation.wait_minutes, 6)
        self.assertEqual(self.dispatch(fleet, request_id=1), [])

    def test_entering_charging_abandons_idle_wait(self) -> None:
        vehicle = self.idle(energy=6.)
        fleet = self.fleet(vehicle)
        fleet.advance_mini_slot()
        enter_charging(vehicle, self.energy)
        self.assertEqual((vehicle.trip_status, vehicle.idle_wait_minutes, vehicle.idle_wait_grid), (VehicleStatus.CHARGING, 0, None))


if __name__ == "__main__":
    unittest.main()
