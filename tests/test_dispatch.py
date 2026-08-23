"""Synthetic tests for approved empirical-OD request generation and FCFS dispatch."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.dispatch.dispatch import build_neighbour_lookup, dispatch_requests, find_eligible_vehicle, request_summary
from src.dispatch.generation import build_empirical_od_distribution, generate_requests, validate_od_distribution
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.fleet.supply import aggregate_grid_supply, validate_grid_supply


class DispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grids = [0, 1, 2, 3]
        self.trips = pd.DataFrame({"PUGridID": [0, 0, 0, 1, 2], "DOGridID": [0, 1, 1, 2, 3]})
        self.od = build_empirical_od_distribution(self.trips, self.grids)
        map_frame = pd.DataFrame({"GridID": [0, 1, 1, 2], "NeighbourGridID": [1, 0, 2, 1]})
        self.neighbours = build_neighbour_lookup(map_frame, self.grids)

    @staticmethod
    def vehicle(vehicle_id: int, grid: int, status: VehicleStatus = VehicleStatus.IDLE) -> VehicleState:
        if status is VehicleStatus.BUSY:
            return VehicleState(vehicle_id, grid, status, 1, 2, "transporting", 1.0)
        return VehicleState(vehicle_id, grid, status, None, 0, "charging" if status is VehicleStatus.CHARGING else "idle", 1.0)

    def fleet(self, vehicles: list[VehicleState]) -> Fleet:
        return Fleet(vehicles, frozenset(self.grids), mini_slot_minutes=2)

    def pending(self, request_id: int, origin: int = 0, destination: int = 1, mini_slot: int = 0) -> RequestState:
        return RequestState(request_id, mini_slot, origin, destination)

    def test_empirical_od_counts_probabilities_and_seeded_sampling(self) -> None:
        self.assertEqual(self.od.total_trips, 5)
        self.assertEqual(self.od.od_pair_count, 4)
        self.assertEqual(self.od.origin_counts, {0: 3, 1: 1, 2: 1})
        np.testing.assert_array_equal(self.od.destinations[0], np.array([0, 1]))
        np.testing.assert_allclose(self.od.probabilities[0], np.array([1 / 3, 2 / 3]))
        validate_od_distribution(self.od, self.grids)
        first = [self.od.sample_destination(0, np.random.default_rng(42)) for _ in range(1)]
        rng_one, rng_two = np.random.default_rng(5), np.random.default_rng(5)
        self.assertEqual([self.od.sample_destination(0, rng_one) for _ in range(10)], [self.od.sample_destination(0, rng_two) for _ in range(10)])
        self.assertEqual(len(first), 1)

    def test_generation_count_zero_ids_grids_slots_and_determinism(self) -> None:
        demand = {0: 4, 1: 2}
        first = generate_requests(demand, self.od, self.grids, 15, 42)
        second = generate_requests(demand, self.od, self.grids, 15, 42)
        self.assertEqual(len(first), 6)
        self.assertEqual([(r.request_id, r.request_time, r.origin_grid, r.destination_grid) for r in first], [(r.request_id, r.request_time, r.origin_grid, r.destination_grid) for r in second])
        self.assertEqual(sorted(r.request_id for r in first), list(range(6)))
        self.assertTrue(all(r.origin_grid in self.grids and r.destination_grid in self.grids and 0 <= r.request_time < 15 for r in first))
        self.assertEqual(generate_requests({0: 0}, self.od, self.grids, 15, 42), [])

    def test_same_grid_is_preferred_even_when_neighbour_has_lower_id(self) -> None:
        fleet = self.fleet([self.vehicle(10, 0), self.vehicle(0, 1)])
        self.assertEqual(find_eligible_vehicle(self.pending(0), fleet, self.neighbours).vehicle_id, 10)

    def test_neighbour_used_only_when_same_grid_empty_and_no_beyond_direct_search(self) -> None:
        fleet = self.fleet([self.vehicle(5, 1), self.vehicle(0, 2)])
        self.assertEqual(find_eligible_vehicle(self.pending(0), fleet, self.neighbours).vehicle_id, 5)
        no_direct = self.fleet([self.vehicle(0, 2)])
        self.assertIsNone(find_eligible_vehicle(self.pending(0), no_direct, self.neighbours))

    def test_lowest_id_wins_within_neighbour_pool(self) -> None:
        fleet = self.fleet([self.vehicle(9, 1), self.vehicle(2, 1)])
        self.assertEqual(find_eligible_vehicle(self.pending(0), fleet, self.neighbours).vehicle_id, 2)

    def test_busy_and_charging_are_never_assigned(self) -> None:
        fleet = self.fleet([self.vehicle(0, 0, VehicleStatus.BUSY), self.vehicle(1, 1, VehicleStatus.CHARGING)])
        request = self.pending(0)
        summary = dispatch_requests([request], fleet, self.neighbours, 2, 15)
        self.assertEqual(summary, {"requests_total": 1, "requests_served": 0, "requests_unserved": 1})
        self.assertEqual(request.status, RequestStatus.UNSERVED)

    def test_fcfs_contention_assignment_wait_and_one_vehicle_constraint(self) -> None:
        fleet = self.fleet([self.vehicle(3, 0)])
        later, earlier = self.pending(2), self.pending(1)
        summary = dispatch_requests([later, earlier], fleet, self.neighbours, 2, 15)
        self.assertEqual(summary, {"requests_total": 2, "requests_served": 1, "requests_unserved": 1})
        self.assertEqual(earlier.status, RequestStatus.ASSIGNED)
        self.assertEqual(earlier.assigned_vehicle_id, 3)
        self.assertEqual(earlier.wait_time, 0)
        self.assertEqual(later.status, RequestStatus.UNSERVED)
        self.assertEqual(fleet.vehicle(3).trip_status, VehicleStatus.BUSY)

    def test_two_minute_placeholder_completes_through_fleet_logic_and_supply_reconciles(self) -> None:
        fleet = self.fleet([self.vehicle(0, 0), self.vehicle(1, 3)])
        request = self.pending(0, origin=0, destination=1)
        dispatch_requests([request], fleet, self.neighbours, 2, 15)
        fleet.advance_mini_slot()
        vehicle = fleet.vehicle(0)
        self.assertEqual((vehicle.trip_status, vehicle.current_grid, vehicle.destination, vehicle.remaining_travel_time), (VehicleStatus.IDLE, 1, None, 0))
        supply = aggregate_grid_supply(fleet.vehicles, self.grids)
        validate_grid_supply(supply, 2, self.grids)
        self.assertEqual(request_summary([request]), {"requests_total": 1, "requests_served": 1, "requests_unserved": 0})


if __name__ == "__main__":
    unittest.main()
