"""Focused final driver-contention adapter, outside-option, and dispatch tests."""

from __future__ import annotations

from datetime import datetime, timedelta
import unittest

import pandas as pd

from src.charging.energy import EnergyParameters
from src.dispatch.contention import (
    DriverContentionInputs, evaluate_request_contention, grid_centroids,
    normalized_trip_energy_burden, pickup_distance_reference, pickup_wait_preference,
)
from src.dispatch.dispatch import (
    DISPATCH_MODEL_CONTENTION, dispatch_requests, eligible_local_vehicles,
)
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.routing.baseline import CandidateUtilityInput, GridRoutingFeatures, RoutingAction


class DriverContentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75., 60., 7.5, .15, 30., .9, 75., .5, .05, .5, .7, .2)
        self.lookup = pd.DataFrame({
            "GridID": [0, 1, 2, 3], "CentroidX": [0., 3000., 6000., 3000.],
            "CentroidY": [0., 0., 0., 3000.],
        })
        self.neighbours = {0: (1,), 1: (0, 2, 3), 2: (1,), 3: (1,)}
        self.directional = pd.DataFrame({
            "GridID": [0, 1, 1, 1, 2, 3], "NeighbourGridID": [1, 0, 2, 3, 1, 1],
            "Direction": ["east", "west", "east", "north", "west", "south"],
        })
        self.features = {
            grid: GridRoutingFeatures(grid, 10., 2, 2, 0, 0, 10., 10., 10., 10., .5, .5, .5, .5, True, 0.)
            for grid in range(4)
        }
        self.low = {action: CandidateUtilityInput(0., 1., 1.) for action in RoutingAction}
        self.high = {action: CandidateUtilityInput(20., 0., 0.) for action in RoutingAction}

    @staticmethod
    def vehicle(vehicle_id: int, grid: int, *, energy: float = 75., status: VehicleStatus = VehicleStatus.IDLE, action: str = "idle") -> VehicleState:
        if status is VehicleStatus.BUSY:
            return VehicleState(vehicle_id, grid, status, 1, 5., "transporting", energy)
        return VehicleState(vehicle_id, grid, status, None, 0., action, energy)

    @staticmethod
    def request(request_id: int, origin: int = 0, destination: int = 2, request_time: int = 0, fare: float = 20., km: float = 10.) -> RequestState:
        pickup = datetime(2026, 1, 1, 0, request_time * 2)
        miles = km / 1.609344
        return RequestState(
            request_id, request_time, origin, destination, base_fare=10., pricing_factor=fare / 10., offered_fare=fare,
            acceptance_probability=1., customer_accepted=True, customer_model="eq31",
            source_trip_id=request_id, empirical_pickup_datetime=pickup,
            empirical_dropoff_datetime=pickup + timedelta(minutes=10), trip_duration_minutes=10.,
            trip_distance_miles=miles, trip_distance_km=km,
        )

    def context(self, preferences: dict[int, dict[RoutingAction, CandidateUtilityInput]]) -> DriverContentionInputs:
        return DriverContentionInputs.from_grid_geometry(
            routing_features=self.features, directional_neighbour_map=self.directional,
            utility_inputs_by_vehicle=preferences, energy_parameters=self.energy,
            grid_lookup=self.lookup, neighbour_lookup=self.neighbours,
        )

    def test_geometry_only_pickup_adapter_and_clipping(self) -> None:
        centroids, unit = grid_centroids(self.lookup)
        reference = pickup_distance_reference(centroids, self.neighbours)
        self.assertEqual((unit, reference), ("EPSG:2263 feet", 3000.))
        self.assertEqual(pickup_wait_preference(0., reference), 1.)
        self.assertEqual(pickup_wait_preference(reference, reference), 0.)
        self.assertEqual(pickup_wait_preference(reference / 2, reference), .5)
        self.assertEqual(pickup_wait_preference(reference * 2, reference), 0.)

    def test_energy_burden_uses_full_capacity_and_clips(self) -> None:
        self.assertEqual(normalized_trip_energy_burden(0., 75.), 0.)
        self.assertEqual(normalized_trip_energy_burden(37.5, 75.), .5)
        self.assertEqual(normalized_trip_energy_burden(75., 75.), 1.)
        self.assertEqual(normalized_trip_energy_burden(100., 75.), 1.)

    def test_outside_option_and_contention_inequality_are_pure(self) -> None:
        vehicle = self.vehicle(7, 0)
        request = self.request(1)
        before = vehicle.__dict__.copy()
        low = evaluate_request_contention(
            vehicle=vehicle, request=request, routing_features=self.features,
            directional_neighbour_map=self.directional, alternative_inputs=self.low,
            energy=self.energy, centroids=grid_centroids(self.lookup)[0], pickup_reference=3000.,
        )
        high = evaluate_request_contention(
            vehicle=vehicle, request=request, routing_features=self.features,
            directional_neighbour_map=self.directional, alternative_inputs=self.high,
            energy=self.energy, centroids=grid_centroids(self.lookup)[0], pickup_reference=3000.,
        )
        self.assertTrue(low.contends)
        self.assertFalse(high.contends)
        self.assertEqual(vehicle.__dict__, before)
        equality = low.__class__(**{**low.__dict__, "best_alternative_utility": low.request_utility, "contends": low.request_utility >= low.request_utility})
        self.assertTrue(equality.contends)

    def test_geographic_and_state_eligibility(self) -> None:
        request = self.request(1)
        fleet = Fleet([
            self.vehicle(0, 0), self.vehicle(1, 1), self.vehicle(2, 2), self.vehicle(3, 3),
            self.vehicle(4, 0, status=VehicleStatus.BUSY),
            self.vehicle(5, 0, status=VehicleStatus.CHARGING, action="charging_queue"),
            self.vehicle(6, 0, energy=1.),
        ], frozenset(range(4)), 2)
        eligible = eligible_local_vehicles(request, fleet, self.neighbours, self.energy)
        self.assertEqual([vehicle.vehicle_id for vehicle in eligible], [0, 1])

    def test_noncontending_same_grid_does_not_block_neighbour(self) -> None:
        fleet = Fleet([self.vehicle(10, 0), self.vehicle(2, 1)], frozenset(range(4)), 2)
        request = self.request(1)
        dispatch_requests(
            [request], fleet, self.neighbours, 2, 15, self.energy,
            dispatch_model=DISPATCH_MODEL_CONTENTION,
            contention_inputs=self.context({10: self.high, 2: self.low}),
        )
        self.assertEqual((request.status, request.assigned_vehicle_id), (RequestStatus.ASSIGNED, 2))
        self.assertEqual((request.eligible_vehicle_count, request.contender_count), (2, 1))
        self.assertEqual(request.selected_vehicle_origin_grid, 1)
        self.assertEqual(request.selected_pickup_distance, 3000.)

    def test_distance_then_utility_then_id_ranking(self) -> None:
        # Same-grid distance wins even with lower utility.
        fleet = Fleet([self.vehicle(8, 0), self.vehicle(1, 1)], frozenset(range(4)), 2)
        request = self.request(1)
        dispatch_requests([request], fleet, self.neighbours, 2, 15, self.energy,
                          dispatch_model=DISPATCH_MODEL_CONTENTION,
                          contention_inputs=self.context({8: self.low, 1: self.low}))
        self.assertEqual(request.assigned_vehicle_id, 8)

        # Equal pickup distance and utility resolves to lowest ID deterministically.
        fleet = Fleet([self.vehicle(9, 1), self.vehicle(3, 1)], frozenset(range(4)), 2)
        tied = self.request(2)
        dispatch_requests([tied], fleet, self.neighbours, 2, 15, self.energy,
                          dispatch_model=DISPATCH_MODEL_CONTENTION,
                          contention_inputs=self.context({9: self.low, 3: self.low}))
        self.assertEqual(tied.assigned_vehicle_id, 3)

        # At equal pickup distance, request utility precedes vehicle ID.
        fleet = Fleet([self.vehicle(1, 1, energy=30.), self.vehicle(7, 1, energy=75.)], frozenset(range(4)), 2)
        utility_ranked = self.request(3)
        dispatch_requests([utility_ranked], fleet, self.neighbours, 2, 15, self.energy,
                          dispatch_model=DISPATCH_MODEL_CONTENTION,
                          contention_inputs=self.context({1: self.low, 7: self.low}))
        self.assertEqual(utility_ranked.assigned_vehicle_id, 7)

    def test_fcfs_mutates_availability_and_no_queue(self) -> None:
        fleet = Fleet([self.vehicle(4, 0)], frozenset(range(4)), 2)
        later, earlier = self.request(2, request_time=1), self.request(1, request_time=0)
        dispatch_requests([later, earlier], fleet, self.neighbours, 2, 15, self.energy,
                          dispatch_model=DISPATCH_MODEL_CONTENTION,
                          contention_inputs=self.context({4: self.low}))
        self.assertEqual(earlier.status, RequestStatus.ASSIGNED)
        self.assertEqual(later.status, RequestStatus.UNSERVED)

    def test_default_legacy_bypasses_contention(self) -> None:
        fleet = Fleet([self.vehicle(9, 0), self.vehicle(1, 1)], frozenset(range(4)), 2)
        request = self.request(1)
        dispatch_requests([request], fleet, self.neighbours, 2, 15, self.energy)
        self.assertEqual(request.assigned_vehicle_id, 9)
        self.assertIsNone(request.eligible_vehicle_count)


if __name__ == "__main__":
    unittest.main()
