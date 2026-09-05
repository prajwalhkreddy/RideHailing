"""Correct raw pricing supply: current IDLE plus known incoming dropoffs."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import unittest

import pandas as pd

from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.supply import PRICING_SUPPLY_COLUMNS, build_raw_pricing_supply


class PricingSupplyTests(unittest.TestCase):
    grids = (0, 1, 2, 3)
    start = datetime(2026, 1, 1, 8, 0)

    @staticmethod
    def vehicle(
        vehicle_id: int, grid: int, status: VehicleStatus,
        destination: int | None = None, remaining: float = 0., action: str | None = None,
    ) -> VehicleState:
        return VehicleState(
            vehicle_id, grid, status, destination, remaining,
            action or status.value.lower(), 50.,
        )

    def test_idle_incoming_destination_exclusions_zero_grids_and_no_double_counting(self) -> None:
        vehicles = [
            self.vehicle(0, 0, VehicleStatus.IDLE),
            self.vehicle(1, 0, VehicleStatus.BUSY, 1, 10., "transporting"),
            self.vehicle(2, 0, VehicleStatus.BUSY, 1, 20., "transporting"),
            self.vehicle(3, 1, VehicleStatus.BUSY, 2, 31., "transporting"),
            self.vehicle(4, 2, VehicleStatus.CHARGING, action="charging"),
            self.vehicle(5, 3, VehicleStatus.CHARGING, action="charging_queue"),
        ]
        result = build_raw_pricing_supply(vehicles, self.grids, self.start).set_index("grid_id")
        self.assertEqual(result.loc[0].tolist(), [1, 0, 1])
        self.assertEqual(result.loc[1].tolist(), [0, 2, 2])
        self.assertEqual(result.loc[2].tolist(), [0, 0, 0])
        self.assertEqual(result.loc[3].tolist(), [0, 0, 0])
        self.assertEqual(int(result.incoming_supply.sum()), 2)
        self.assertTrue((result.total_supply == result.idle_supply + result.incoming_supply).all())

    def test_completion_window_matches_existing_end_of_mini_slot_semantics(self) -> None:
        vehicles = [
            # Exactly at start is already IDLE at its completed destination.
            self.vehicle(0, 1, VehicleStatus.IDLE),
            self.vehicle(1, 0, VehicleStatus.BUSY, 1, .000001, "transporting"),
            self.vehicle(2, 0, VehicleStatus.BUSY, 1, 29.999999, "transporting"),
            self.vehicle(3, 0, VehicleStatus.BUSY, 1, 30., "transporting"),
            self.vehicle(4, 0, VehicleStatus.BUSY, 1, 30.000001, "transporting"),
        ]
        row = build_raw_pricing_supply(vehicles, self.grids, self.start).set_index("grid_id").loc[1]
        self.assertEqual((row.idle_supply, row.incoming_supply, row.total_supply), (1, 3, 4))

    def test_multiple_destinations_are_counted_once_at_dropoff_not_current_grid(self) -> None:
        vehicles = [
            self.vehicle(0, 0, VehicleStatus.BUSY, 2, 2., "transporting"),
            self.vehicle(1, 1, VehicleStatus.BUSY, 2, 30., "transporting"),
            self.vehicle(2, 2, VehicleStatus.BUSY, 3, 15., "transporting"),
        ]
        result = build_raw_pricing_supply(vehicles, self.grids, self.start).set_index("grid_id")
        self.assertEqual(result.incoming_supply.to_dict(), {0: 0, 1: 0, 2: 2, 3: 1})
        self.assertEqual(int(result.total_supply.sum()), 3)

    def test_result_is_deterministic_complete_integer_and_does_not_mutate_state(self) -> None:
        vehicles = [
            self.vehicle(0, 0, VehicleStatus.IDLE),
            self.vehicle(1, 3, VehicleStatus.BUSY, 1, 12., "transporting"),
        ]
        before = deepcopy(vehicles)
        first = build_raw_pricing_supply(vehicles, self.grids, self.start)
        second = build_raw_pricing_supply(vehicles, self.grids, self.start)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first.columns.tolist(), PRICING_SUPPLY_COLUMNS)
        self.assertEqual(first.grid_id.tolist(), list(self.grids))
        self.assertTrue(all(str(dtype) == "int64" for dtype in first[PRICING_SUPPLY_COLUMNS[1:]].dtypes))
        self.assertEqual(vehicles, before)


if __name__ == "__main__":
    unittest.main()
