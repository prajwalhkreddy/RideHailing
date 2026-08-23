"""Focused deterministic tests for NB10 Part 1 EV battery energy operations."""

from __future__ import annotations

import unittest

from src.charging.energy import (
    EnergyParameters, apply_distance_energy, charge_vehicle,
    charging_energy_gain_kwh, energy_consumed_kwh, enter_charging,
    initial_energy, requires_charging, sample_initial_socs, initialize_ev_fleet, validate_vehicle_energy,
)
from src.fleet.state import VehicleState, VehicleStatus
from src.fleet.supply import aggregate_grid_supply, validate_grid_supply


class EnergyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = EnergyParameters(75.0, 60.0, 7.5, 0.15, 30.0, 0.90, 75.0, 0.50, 0.05, 0.50, 0.70, 0.20)
        self.grids = [10, 20]

    @staticmethod
    def vehicle(energy: float, status: VehicleStatus = VehicleStatus.IDLE) -> VehicleState:
        return VehicleState(0, 10, status, None, 0, "charging" if status is VehicleStatus.CHARGING else "idle", energy)

    def test_literature_backed_parameters_and_initial_energy(self) -> None:
        self.parameters.validate()
        self.assertEqual(initial_energy(self.parameters), 60.0)
        self.assertEqual((self.parameters.battery_capacity_kwh, self.parameters.minimum_energy_kwh, self.parameters.consumption_rate_kwh_per_km, self.parameters.charging_power_kw, self.parameters.charging_efficiency), (75.0, 7.5, 0.15, 30.0, 0.90))

    def test_distance_consumption_zero_and_negative_distance(self) -> None:
        self.assertEqual(energy_consumed_kwh(100, self.parameters), 15.0)
        self.assertEqual(energy_consumed_kwh(0, self.parameters), 0.0)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            energy_consumed_kwh(-1, self.parameters)

    def test_distance_energy_rejects_negative_energy_and_moves_low_energy_idle_vehicle_to_charging(self) -> None:
        impossible = self.vehicle(1.0)
        with self.assertRaisesRegex(ValueError, "negative"):
            apply_distance_energy(impossible, 10, self.parameters)
        low = self.vehicle(8.0)
        self.assertEqual(apply_distance_energy(low, 4, self.parameters), 0.6)
        self.assertAlmostEqual(low.energy_level, 7.4)
        self.assertEqual(low.trip_status, VehicleStatus.CHARGING)

    def test_supervisor_soc_initialization_and_twenty_percent_trigger_boundary(self) -> None:
        first, second = sample_initial_socs(20, self.parameters, 42), sample_initial_socs(20, self.parameters, 42)
        self.assertTrue((first == second).all())
        self.assertTrue(((first >= 0.50) & (first <= 0.70)).all())
        self.assertGreater(len(set(first.tolist())), 1)
        fleet = initialize_ev_fleet(20, [10, 20], 42, self.parameters)
        self.assertTrue(all(vehicle.energy_level == soc * 75 for vehicle, soc in zip(fleet, first)))
        at_trigger, below_trigger, above_trigger = self.vehicle(15.0), self.vehicle(14.99), self.vehicle(15.01)
        self.assertTrue(requires_charging(at_trigger, self.parameters))
        self.assertTrue(requires_charging(below_trigger, self.parameters))
        self.assertFalse(requires_charging(above_trigger, self.parameters))
        enter_charging(at_trigger, self.parameters)
        self.assertEqual((at_trigger.trip_status, at_trigger.current_action), (VehicleStatus.CHARGING, "charging"))

    def test_charging_gain_arbitrary_duration_cap_and_full_release(self) -> None:
        vehicle = self.vehicle(6.5, VehicleStatus.CHARGING)
        self.assertEqual(charging_energy_gain_kwh(2, self.parameters), 0.9)
        self.assertAlmostEqual(charge_vehicle(vehicle, 2, self.parameters), 0.9)
        self.assertAlmostEqual(vehicle.energy_level, 7.4)
        self.assertEqual(vehicle.trip_status, VehicleStatus.CHARGING)
        self.assertEqual(charging_energy_gain_kwh(30, self.parameters), 13.5)
        vehicle.energy_level = 74.5
        self.assertEqual(charge_vehicle(vehicle, 2, self.parameters), 0.5)
        self.assertEqual((vehicle.energy_level, vehicle.trip_status), (75.0, VehicleStatus.IDLE))

    def test_configurable_release_threshold(self) -> None:
        parameters = EnergyParameters(75, 60, 7.5, 0.15, 30, 0.90, 10, 0.50, 0.05, 0.50, 0.70, 0.20)
        vehicle = self.vehicle(9, VehicleStatus.CHARGING)
        charge_vehicle(vehicle, 2, parameters)
        self.assertEqual((vehicle.energy_level, vehicle.trip_status), (9.9, VehicleStatus.CHARGING))
        charge_vehicle(vehicle, 1 / 4, parameters)
        self.assertAlmostEqual(vehicle.energy_level, 10.0125)
        self.assertEqual(vehicle.trip_status, VehicleStatus.IDLE)

    def test_vehicle_energy_bounds_and_fleet_supply_reconcile(self) -> None:
        too_high = self.vehicle(76)
        with self.assertRaisesRegex(ValueError, "within"):
            validate_vehicle_energy(too_high, self.parameters)
        vehicles = [self.vehicle(6.0), VehicleState(1, 20, VehicleStatus.IDLE, None, 0, "idle", 60.0)]
        enter_charging(vehicles[0], self.parameters)
        supply = aggregate_grid_supply(vehicles, self.grids)
        validate_grid_supply(supply, 2, self.grids)
        self.assertEqual(supply[["supply_idle", "supply_busy", "supply_charging"]].sum().tolist(), [1, 0, 1])


if __name__ == "__main__":
    unittest.main()
