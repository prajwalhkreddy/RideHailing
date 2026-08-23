"""Unit tests for legacy NB3 pickup-demand and historical-demand semantics."""

import unittest

import pandas as pd

from src.demand.aggregation import (
    add_historical_demand, add_temporal_features, aggregate_pickup_demand,
    build_time_slots, complete_space_time_grid,
)


class DemandAggregationTests(unittest.TestCase):
    def test_flooring_and_january_boundary_filter(self) -> None:
        trips = pd.DataFrame({"tpep_pickup_datetime": ["2025-12-31 23:59", "2026-01-01 00:01", "2026-01-31 23:59", "2026-02-01 00:00"], "PUGridID": [0, 0, 1, 1]})
        demand, retained = aggregate_pickup_demand(trips, "2026-01", 30)
        self.assertEqual(retained, 2)
        self.assertEqual(demand[["TimeSlot", "GridID", "Demand"]].values.tolist(), [[pd.Timestamp("2026-01-01 00:00"), 0, 1], [pd.Timestamp("2026-01-31 23:30"), 1, 1]])

    def test_complete_space_time_grid_zero_fills_valid_cells(self) -> None:
        grid = pd.DataFrame({"GridID": [0, 1], "Row": [0, 0], "Column": [0, 1]})
        demand = pd.DataFrame({"TimeSlot": [pd.Timestamp("2026-01-01 00:00")], "GridID": [0], "Demand": [3]})
        result = complete_space_time_grid(demand, grid, pd.DatetimeIndex([pd.Timestamp("2026-01-01 00:00"), pd.Timestamp("2026-01-01 00:30")]))
        self.assertEqual(len(result), 4)
        self.assertEqual(result["Demand"].tolist(), [3, 0, 0, 0])
        self.assertEqual(result[["Row", "Column"]].values.tolist(), [[0, 0], [0, 1], [0, 0], [0, 1]])

    def test_temporal_fields_match_legacy_definitions(self) -> None:
        master = pd.DataFrame({"TimeSlot": [pd.Timestamp("2026-01-01 00:30")], "GridID": [0], "Demand": [1], "Row": [0], "Column": [0], "Temperature": [1.0], "WindSpeed": [2.0], "WeatherCode": [3]})
        result = add_temporal_features(master)
        self.assertEqual(result.loc[0, ["DayOfWeek", "Hour", "Minute", "Period", "TimeIndex"]].tolist(), [3, 0, 30, 1, 0])

    def test_historical_demand_excludes_current_and_future_values(self) -> None:
        master = pd.DataFrame({
            "TimeSlot": pd.to_datetime(["2026-01-05 00:00", "2026-01-12 00:00", "2026-01-19 00:00"]),
            "GridID": [0, 0, 0], "Demand": [2, 4, 100], "Row": [0, 0, 0], "Column": [0, 0, 0],
            "Temperature": [1.0, 1.0, 1.0], "WindSpeed": [2.0, 2.0, 2.0], "WeatherCode": [3, 3, 3],
            "DayOfWeek": [0, 0, 0], "Hour": [0, 0, 0], "Minute": [0, 0, 0], "Period": [0, 0, 0], "TimeIndex": [0, 48, 96],
        })
        result = add_historical_demand(master)
        self.assertEqual(result["HistoricalDemand"].tolist(), [0.0, 2.0, 3.0])

    def test_january_calendar_has_1488_slots(self) -> None:
        self.assertEqual(len(build_time_slots("2026-01", 30)), 1488)

    def test_missing_pickup_grid_column_fails_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "required NB3 columns"):
            aggregate_pickup_demand(pd.DataFrame({"tpep_pickup_datetime": ["2026-01-01"]}), "2026-01", 30)
