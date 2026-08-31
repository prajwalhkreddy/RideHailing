"""Empirical duration, canonical distance, and passenger-energy integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import unittest

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingInfrastructure, ChargingStation
from src.dispatch.dispatch import dispatch_requests, find_eligible_vehicle
from src.dispatch.generation import MILES_TO_KM, build_empirical_od_distribution, generate_requests
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.fleet.supply import aggregate_grid_supply
from src.routing.baseline import GridRoutingFeatures, RoutingAction, RoutingParameters, RoutingState, execute_reposition


class PassengerTripIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        self.pickup = datetime(2026, 1, 1, 0, 0)

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame({
            "PUGridID": [0, 0], "DOGridID": [1, 0],
            "tpep_pickup_datetime": [self.pickup, self.pickup + timedelta(minutes=1)],
            "tpep_dropoff_datetime": [self.pickup + timedelta(minutes=18), self.pickup + timedelta(minutes=8)],
            "trip_distance": [5., 1.], "fare_amount": [25., 9.],
        })

    def empirical_request(self, *, request_time=14, miles=5., duration=18.) -> RequestState:
        return RequestState(
            0, request_time, 0, 1, base_fare=25., source_trip_id=7,
            empirical_pickup_datetime=self.pickup,
            empirical_dropoff_datetime=self.pickup + timedelta(minutes=duration),
            trip_duration_minutes=duration, trip_distance_miles=miles,
            trip_distance_km=miles * MILES_TO_KM,
        )

    def fleet(self, energy=40.) -> Fleet:
        return Fleet([VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", energy)], frozenset((0, 1)), 2)

    def test_same_sampled_row_propagates_od_timestamps_duration_distance_and_fare(self) -> None:
        distribution = build_empirical_od_distribution(self.frame(), [0, 1])
        requests = generate_requests({0: 4}, distribution, [0, 1], 15, 4)
        source = self.frame()
        for request in requests:
            row = source.iloc[request.source_trip_id]
            self.assertEqual((request.origin_grid, request.destination_grid), (row.PUGridID, row.DOGridID))
            self.assertEqual((request.empirical_pickup_datetime, request.empirical_dropoff_datetime), (row.tpep_pickup_datetime, row.tpep_dropoff_datetime))
            self.assertEqual(request.trip_duration_minutes, (row.tpep_dropoff_datetime - row.tpep_pickup_datetime).total_seconds() / 60.)
            self.assertEqual((request.trip_distance_miles, request.trip_distance_km, request.base_fare), (row.trip_distance, row.trip_distance * MILES_TO_KM, row.fare_amount))

    def test_miles_to_km_and_energy_are_exact_approved_units(self) -> None:
        self.assertEqual(1. * MILES_TO_KM, 1.609344)
        self.assertEqual(5. * MILES_TO_KM, 8.04672)
        request, fleet = self.empirical_request(request_time=0), self.fleet()
        dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, self.energy)
        self.assertAlmostEqual(request.passenger_energy_kwh, 1.207008)
        self.assertAlmostEqual(request.passenger_energy_before_kwh - request.passenger_energy_after_kwh, 1.207008)

    def test_invalid_duration_distance_and_fare_rows_are_excluded_not_clipped(self) -> None:
        frame = self.frame()
        invalid = pd.DataFrame({
            "PUGridID": [0, 0, 0], "DOGridID": [1, 1, 1],
            "tpep_pickup_datetime": [self.pickup] * 3,
            "tpep_dropoff_datetime": [self.pickup, self.pickup + timedelta(minutes=1), self.pickup + timedelta(minutes=1)],
            "trip_distance": [1., -1., np.inf], "fare_amount": [10., 10., -1.],
        })
        distribution = build_empirical_od_distribution(pd.concat([frame, invalid], ignore_index=True), [0, 1])
        self.assertEqual((distribution.source_trip_count, distribution.total_trips, distribution.excluded_invalid_trip_count), (5, 2, 3))
        for invalid_distance in (-1., np.nan, np.inf):
            request = self.empirical_request(miles=invalid_distance)
            with self.assertRaises(ValueError):
                request.validate([0, 1], 15)

    def test_empirical_duration_overrides_two_minute_fallback_and_completes_at_0046(self) -> None:
        request, fleet = self.empirical_request(), self.fleet()
        dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, self.energy)
        self.assertEqual((request.trip_start_minute, request.busy_until_minute), (28., 46.))
        self.assertEqual(fleet.vehicle(0).remaining_travel_time, 18.)
        fleet.advance_mini_slot()  # 00:30
        self.assertEqual((fleet.vehicle(0).trip_status, fleet.vehicle(0).remaining_travel_time), (VehicleStatus.BUSY, 16.))
        for _ in range(7):  # through 00:44
            fleet.advance_mini_slot()
        self.assertEqual(fleet.vehicle(0).trip_status, VehicleStatus.BUSY)
        fleet.advance_mini_slot()  # 00:46
        self.assertEqual((fleet.vehicle(0).trip_status, fleet.vehicle(0).current_grid), (VehicleStatus.IDLE, 1))

    def test_energy_deducted_once_busy_excluded_then_completion_can_charge(self) -> None:
        request, fleet = self.empirical_request(), self.fleet(16.)
        before = fleet.vehicle(0).energy_level
        dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, self.energy)
        after_assignment = fleet.vehicle(0).energy_level
        self.assertAlmostEqual(before - after_assignment, 1.207008)
        for _ in range(8):
            fleet.advance_mini_slot()
            self.assertEqual(fleet.vehicle(0).energy_level, after_assignment)
        self.assertEqual(aggregate_grid_supply(fleet.vehicles, [0, 1]).supply_idle.sum(), 0)
        feature = GridRoutingFeatures(0, 1., 1, 0, 1, 0, 1., 0., 1., 0., 0., 0., 0., 0., True, 0.)
        state = RoutingState(0, 0, after_assignment, feature, {action: feature if action is RoutingAction.STAY else None for action in RoutingAction})
        with self.assertRaisesRegex(ValueError, "Only idle"):
            execute_reposition(fleet.vehicle(0), state, RoutingAction.STAY, RoutingParameters(15., 3., 30.), self.energy)
        fleet.advance_mini_slot()
        infrastructure = ChargingInfrastructure([ChargingStation(0, 1, 30, 30)], {0: (0., 0.), 1: (1., 0.)})
        infrastructure.present_vehicle(fleet.vehicle(0), self.energy, 0)
        self.assertEqual(fleet.vehicle(0).trip_status, VehicleStatus.CHARGING)

    def test_trip_specific_energy_feasibility_uses_existing_energy_domain(self) -> None:
        request = self.empirical_request(request_time=0, miles=100.)
        fleet = self.fleet(16.)
        self.assertIsNone(find_eligible_vehicle(request, fleet, {0: (1,)}, self.energy))
        dispatch_requests([request], fleet, {0: (1,)}, 2, 15, self.energy)
        self.assertEqual(request.status, RequestStatus.UNSERVED)
        self.assertEqual(fleet.vehicle(0).energy_level, 16.)


if __name__ == "__main__":
    unittest.main()
