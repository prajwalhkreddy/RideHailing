"""Synthetic tests for NB10 station placement and power-limited FCFS state."""

from __future__ import annotations

import unittest

import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import (
    ChargingInfrastructure, ChargingStation, build_station_definition,
    stations_from_definition, validate_station_definition,
)
from src.dispatch.dispatch import find_eligible_vehicle
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.simulation.statistics import OperationalStatistics


class ChargingStationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grids = list(range(20))
        self.parameters = EnergyParameters(75, 60, 7.5, 0.15, 30, 0.90, 75, 0.50, 0.05, 0.50, 0.70, 0.20)
        self.centroids = {grid: (float(grid), 0.0) for grid in self.grids}

    def vehicle(self, vehicle_id: int, grid: int, energy: float = 6.0, status: VehicleStatus = VehicleStatus.IDLE) -> VehicleState:
        return VehicleState(vehicle_id, grid, status, None, 0, "idle", energy)

    def test_popularity_ranking_exact_count_tie_break_and_reproducibility(self) -> None:
        trips = pd.DataFrame({"PUGridID": [2, 2, 1, 3, 3], "DOGridID": [1, 1, 2, 2, 3]})
        first = build_station_definition(trips, self.grids, 15)
        second = build_station_definition(trips, self.grids, 15)
        self.assertEqual(len(first), 15)
        self.assertTrue(first.equals(second))
        validate_station_definition(first, self.grids, 15)
        row_two = first[first.grid_id == 2].iloc[0]
        self.assertEqual((int(row_two.pickup_count), int(row_two.dropoff_count), int(row_two.popularity)), (2, 2, 4))
        equal_zero_grids = first[first.popularity == 0].grid_id.tolist()
        self.assertEqual(equal_zero_grids, sorted(equal_zero_grids))

    def test_nearest_station_and_station_id_tie_break(self) -> None:
        infrastructure = ChargingInfrastructure([ChargingStation(1, 4, 3000, 30), ChargingStation(0, 6, 3000, 30)], self.centroids)
        self.assertEqual(infrastructure.nearest_station(self.vehicle(0, 5)).station_id, 0)

    def test_power_cap_reservation_and_fcfs_queue_tie_break(self) -> None:
        station = ChargingStation(0, 0, 30, 30)
        infrastructure = ChargingInfrastructure([station], self.centroids)
        active, first_draw, second_draw = self.vehicle(0, 0), self.vehicle(1, 0), self.vehicle(9, 0)
        infrastructure.present_vehicle(active, self.parameters, 0)
        infrastructure.present_vehicle(first_draw, self.parameters, 1)
        infrastructure.present_vehicle(second_draw, self.parameters, 1)
        self.assertEqual(station.active_reserved_power_kw, 30)
        self.assertFalse(station.charging_available)
        self.assertEqual([entry.vehicle_id for entry in station.queue], [9, 1])
        with self.assertRaisesRegex(ValueError, "already active or queued"):
            infrastructure.present_vehicle(first_draw, self.parameters, 2)

    def test_seeded_random_priority_is_reproducible_and_preserves_earlier_arrivals(self) -> None:
        def queue_ids(seed: int) -> list[int]:
            station = ChargingStation(0, 0, 30, 30)
            infrastructure = ChargingInfrastructure([station], self.centroids, random_seed=seed)
            infrastructure.present_vehicle(self.vehicle(0, 0), self.parameters, 0)
            infrastructure.present_vehicle(self.vehicle(1, 0), self.parameters, 2)
            infrastructure.present_vehicle(self.vehicle(9, 0), self.parameters, 1)
            infrastructure.present_vehicle(self.vehicle(2, 0), self.parameters, 1)
            return [entry.vehicle_id for entry in station.queue]
        self.assertEqual(queue_ids(42), queue_ids(42))
        self.assertEqual(queue_ids(42)[0], 9)

    def test_queue_wait_release_power_and_promote(self) -> None:
        station = ChargingStation(0, 0, 30, 30)
        infrastructure = ChargingInfrastructure([station], self.centroids)
        active, queued = self.vehicle(0, 0, 6.0), self.vehicle(1, 0, 6.0)
        infrastructure.present_vehicle(active, self.parameters, 0)
        infrastructure.present_vehicle(queued, self.parameters, 1)
        active.energy_level = 74.1  # Synthetic near-release active charging state.
        infrastructure.advance_mini_slot([active, queued], 2, self.parameters)
        self.assertEqual((active.energy_level, active.trip_status), (75.0, VehicleStatus.IDLE))
        self.assertEqual(station.active_vehicle_ids, {1})
        self.assertEqual(station.queue, [])
        self.assertTrue(station.charging_available is False)
        self.assertEqual(queued.current_action, "charging")

    def test_efficiency_queue_wait_and_charging_observations_reach_nb9(self) -> None:
        station = ChargingStation(0, 0, 30, 30)
        infrastructure = ChargingInfrastructure([station], self.centroids)
        active, queued = self.vehicle(0, 0), self.vehicle(1, 0)
        infrastructure.present_vehicle(active, self.parameters, 0)
        infrastructure.present_vehicle(queued, self.parameters, 1)
        infrastructure.advance_mini_slot([active, queued], 2, self.parameters)
        self.assertAlmostEqual(active.energy_level, 6.9)
        self.assertEqual(station.charging_wait, 2.0)
        observations = infrastructure.charging_observations()
        records = OperationalStatistics([0, 1], 0.3).update_slot(0, charging_observations=observations)
        by_grid = {record.grid_id: record for record in records}
        self.assertEqual((by_grid[0].charging_available, by_grid[0].charging_wait), (False, 2.0))
        self.assertEqual((by_grid[1].charging_available, by_grid[1].charging_wait), (None, None))

    def test_low_energy_idle_is_ineligible_for_dispatch_and_busy_trip_finishes_first(self) -> None:
        low = self.vehicle(0, 0)
        fleet = Fleet([low], frozenset(self.grids), 2)
        request = RequestState(0, 0, 0, 1)
        self.assertIsNone(find_eligible_vehicle(request, fleet, {0: []}, self.parameters))
        busy = VehicleState(1, 0, VehicleStatus.BUSY, 1, 2, "transporting", 6.0)
        with self.assertRaisesRegex(ValueError, "complete"):
            from src.charging.energy import enter_charging
            enter_charging(busy, self.parameters)
        Fleet([busy], frozenset(self.grids), 2).advance_mini_slot()
        self.assertEqual(busy.trip_status, VehicleStatus.IDLE)

    def test_implied_hundred_active_power_slots_without_hard_coded_charger_count(self) -> None:
        station = ChargingStation(0, 0, 3000, 30)
        infrastructure = ChargingInfrastructure([station], self.centroids)
        vehicles = [self.vehicle(index, 0) for index in range(101)]
        for vehicle in vehicles:
            infrastructure.present_vehicle(vehicle, self.parameters, 0)
        self.assertEqual(len(station.active_vehicle_ids), 100)
        self.assertEqual(len(station.queue), 1)
        self.assertEqual(station.active_reserved_power_kw, 3000)


if __name__ == "__main__":
    unittest.main()
