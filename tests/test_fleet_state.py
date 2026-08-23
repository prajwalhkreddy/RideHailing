"""Synthetic unit tests for vehicle state and complete-grid fleet supply."""

from __future__ import annotations

import unittest

from src.fleet.fleet import Fleet, initialize_fleet, mini_slots_per_main_slot, validate_fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.fleet.supply import aggregate_grid_supply, validate_grid_supply


class FleetStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grids = [10, 20, 30, 40]

    def test_requested_size_unique_ids_valid_grids_deterministic_and_idle(self) -> None:
        first = initialize_fleet(8, self.grids, random_seed=42)
        second = initialize_fleet(8, self.grids, random_seed=42)
        self.assertEqual(len(first), 8)
        self.assertEqual([v.vehicle_id for v in first], list(range(8)))
        self.assertTrue(all(v.current_grid in self.grids for v in first))
        self.assertEqual([v.current_grid for v in first], [v.current_grid for v in second])
        self.assertTrue(all(v.trip_status is VehicleStatus.IDLE for v in first))
        self.assertTrue(all(v.destination is None and v.remaining_travel_time == 0 and v.current_action == "idle" for v in first))

    def test_invalid_state_status_and_grid_are_rejected(self) -> None:
        invalid_status = VehicleState(0, 10, "IDLE", None, 0, "idle", 1.0)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "trip_status"):
            invalid_status.validate(self.grids)
        invalid_grid = VehicleState(0, 99, VehicleStatus.IDLE, None, 0, "idle", 1.0)
        with self.assertRaisesRegex(ValueError, "current_grid"):
            invalid_grid.validate(self.grids)

    def test_idle_to_busy_assignment_validates_destination_duration_and_transition(self) -> None:
        fleet = Fleet(initialize_fleet(2, self.grids, 7), frozenset(self.grids), mini_slot_minutes=2)
        vehicle = fleet.vehicle(0)
        with self.assertRaisesRegex(ValueError, "destination"):
            fleet.assign_busy(0, 99, 2)
        with self.assertRaisesRegex(ValueError, "travel_duration"):
            fleet.assign_busy(0, 20, 0)
        fleet.assign_busy(0, 20, 6)
        self.assertEqual((vehicle.trip_status, vehicle.destination, vehicle.remaining_travel_time, vehicle.current_action), (VehicleStatus.BUSY, 20, 6, "transporting"))
        with self.assertRaisesRegex(ValueError, "Only IDLE"):
            fleet.assign_busy(0, 30, 2)

    def test_mini_slot_decrements_without_negative_and_completes_at_destination(self) -> None:
        fleet = Fleet(initialize_fleet(1, self.grids, 8), frozenset(self.grids), mini_slot_minutes=2)
        fleet.assign_busy(0, 40, 6)
        fleet.advance_mini_slot()
        self.assertEqual(fleet.vehicle(0).remaining_travel_time, 4)
        fleet.advance_mini_slot(); self.assertEqual(fleet.vehicle(0).remaining_travel_time, 2)
        fleet.advance_mini_slot()
        vehicle = fleet.vehicle(0)
        self.assertEqual(vehicle.trip_status, VehicleStatus.IDLE)
        self.assertEqual(vehicle.current_grid, 40)
        self.assertIsNone(vehicle.destination)
        self.assertEqual(vehicle.remaining_travel_time, 0)
        fleet.advance_mini_slot()
        self.assertEqual(vehicle.remaining_travel_time, 0)

    def test_charging_is_representable(self) -> None:
        vehicle = VehicleState(3, 10, VehicleStatus.CHARGING, None, 0, "charging", 0.5)
        vehicle.validate(self.grids)

    def test_supply_includes_zero_grids_and_reconciles_statuses(self) -> None:
        vehicles = [
            VehicleState(0, 10, VehicleStatus.IDLE, None, 0, "idle", 1.0),
            VehicleState(1, 10, VehicleStatus.CHARGING, None, 0, "charging", 0.5),
            VehicleState(2, 20, VehicleStatus.BUSY, 30, 2, "transporting", 0.7),
        ]
        validate_fleet(vehicles, self.grids, expected_size=3)
        supply = aggregate_grid_supply(vehicles, self.grids)
        self.assertEqual(supply["grid_id"].tolist(), self.grids)
        self.assertEqual(int(supply.loc[supply.grid_id == 40, "supply_total"].iloc[0]), 0)
        self.assertEqual(supply[["supply_idle", "supply_busy", "supply_charging"]].sum().tolist(), [1, 1, 1])
        validate_grid_supply(supply, 3, self.grids)

    def test_supply_invalid_grid_and_invalid_reconciliation_are_rejected(self) -> None:
        invalid = [VehicleState(0, 99, VehicleStatus.IDLE, None, 0, "idle", 1.0)]
        with self.assertRaisesRegex(ValueError, "current_grid"):
            validate_fleet(invalid, self.grids)
        supply = aggregate_grid_supply(initialize_fleet(2, self.grids, 1), self.grids)
        supply.loc[0, "supply_total"] += 1
        with self.assertRaisesRegex(ValueError, "status totals"):
            validate_grid_supply(supply, 2, self.grids)

    def test_main_and_mini_slot_relationship(self) -> None:
        self.assertEqual(mini_slots_per_main_slot(30, 2), 15)
        with self.assertRaisesRegex(ValueError, "whole multiple"):
            mini_slots_per_main_slot(30, 7)


if __name__ == "__main__":
    unittest.main()
