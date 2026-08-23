"""Contract tests for NB3 output and first-milestone metadata compatibility."""

import unittest

import numpy as np
import pandas as pd

from src.demand.contracts import DEMAND_MASTER_COLUMNS, validate_demand_master, validate_grid_input_contract


class DemandArtifactTests(unittest.TestCase):
    def test_grid_metadata_dimension_mismatch_fails(self) -> None:
        grid = pd.DataFrame({"GridID": [0], "Row": [0], "Column": [0], "geometry": [None]})
        metadata = {"data_month": "2026-01", "grid_rows": 1, "grid_columns": 2, "valid_cells": 1, "metric_crs": "EPSG:2263", "grid_size_meters": 3000}
        with self.assertRaisesRegex(ValueError, "mask shape"):
            validate_grid_input_contract(grid, np.ones((1, 1), dtype=np.uint8), metadata, "2026-01")

    def test_grid_metadata_month_mismatch_fails(self) -> None:
        grid = pd.DataFrame({"GridID": [0], "Row": [0], "Column": [0], "geometry": [None]})
        metadata = {"data_month": "2026-02", "grid_rows": 1, "grid_columns": 1, "valid_cells": 1, "metric_crs": "EPSG:2263", "grid_size_meters": 3000}
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_grid_input_contract(grid, np.ones((1, 1), dtype=np.uint8), metadata, "2026-01")

    def test_output_column_order_is_fixed(self) -> None:
        grid = pd.DataFrame({"GridID": [0]})
        times = pd.date_range("2026-01-01", "2026-02-01", freq="30min", inclusive="left")
        master = pd.DataFrame({"TimeSlot": times, "GridID": 0, "Demand": 0, "Row": 0, "Column": 0, "Temperature": 1.0, "WindSpeed": 2.0, "WeatherCode": 3, "DayOfWeek": times.dayofweek, "Hour": times.hour, "Minute": times.minute, "Period": times.hour * 2 + times.minute // 30, "TimeIndex": range(len(times)), "HistoricalDemand": 0.0})
        validate_demand_master(master[DEMAND_MASTER_COLUMNS], grid, "2026-01")
        with self.assertRaisesRegex(ValueError, "column order"):
            validate_demand_master(master[list(reversed(DEMAND_MASTER_COLUMNS))], grid, "2026-01")
