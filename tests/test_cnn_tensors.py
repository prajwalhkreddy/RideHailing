"""Synthetic tests for the frozen legacy NB4 tensor-generation contract."""

import tempfile
import unittest

import numpy as np
import pandas as pd

from src.demand.tensors import (
    CNN_CHANNELS, build_cnn_tensors, chronological_split, load_cnn_dataset,
    save_cnn_dataset, validate_tensor_inputs,
)


def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, dict]:
    grid = pd.DataFrame({"GridID": [0, 1], "Row": [0, 1], "Column": [0, 2]})
    rows = []
    for time_index in range(3):
        for grid_id, row, column in grid.itertuples(index=False):
            rows.append({"TimeSlot": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=30 * time_index), "TimeIndex": time_index, "GridID": grid_id, "Row": row, "Column": column, "Demand": 10 * time_index + grid_id, "HistoricalDemand": 100 * time_index + grid_id, "Temperature": 200 * time_index + grid_id, "WindSpeed": 300 * time_index + grid_id, "WeatherCode": 400 * time_index + grid_id, "DayOfWeek": 3, "Hour": time_index // 2, "Period": time_index})
    mask = np.zeros((2, 3), dtype=np.uint8)
    mask[0, 0] = 1
    mask[1, 2] = 1
    metadata = {"grid_rows": 2, "grid_columns": 3, "valid_cells": 2}
    return pd.DataFrame(rows), grid, mask, metadata


class CnnTensorTests(unittest.TestCase):
    def test_exact_feature_order_and_grid_placement(self) -> None:
        demand, grid, mask, metadata = synthetic_inputs()
        x, y, _ = build_cnn_tensors(demand, grid, mask, metadata)
        self.assertEqual(CNN_CHANNELS, ["HistoricalDemand", "Temperature", "WindSpeed", "WeatherCode", "DayOfWeek", "Hour", "Period"])
        self.assertEqual(x.shape, (2, 7, 2, 3))
        self.assertEqual(x[0, :, 0, 0].tolist(), [0, 0, 0, 0, 3, 0, 0])
        self.assertEqual(x[1, :, 1, 2].tolist(), [101, 201, 301, 401, 3, 0, 1])
        self.assertTrue(np.all(x[:, :, 0, 1] == 0))
        self.assertTrue(np.all(y[:, :, 0, 1] == 0))

    def test_target_is_next_time_demand(self) -> None:
        demand, grid, mask, metadata = synthetic_inputs()
        _x, y, times = build_cnn_tensors(demand, grid, mask, metadata)
        self.assertEqual(times.tolist(), [np.datetime64("2026-01-01T00:00:00.000000"), np.datetime64("2026-01-01T00:30:00.000000")])
        self.assertEqual(y[:, 0, 0, 0].tolist(), [10.0, 20.0])
        self.assertEqual(y[:, 0, 1, 2].tolist(), [11.0, 21.0])

    def test_chronological_split_does_not_shuffle(self) -> None:
        x = np.zeros((5, 7, 2, 3), dtype=np.float32)
        y = np.zeros((5, 1, 2, 3), dtype=np.float32)
        times = np.array(pd.date_range("2026-01-01", periods=5, freq="30min"))
        split = chronological_split(x, y, times)
        self.assertEqual(split["x_train"].shape[0], 4)
        self.assertEqual(split["x_test"].shape[0], 1)
        self.assertEqual(split["time_train"][-1], times[3])
        self.assertEqual(split["time_test"][0], times[4])

    def test_persistence_and_reload(self) -> None:
        demand, grid, mask, metadata = synthetic_inputs()
        x, y, times = build_cnn_tensors(demand, grid, mask, metadata)
        arrays = chronological_split(x, y, times)
        with tempfile.TemporaryDirectory() as directory:
            save_cnn_dataset(directory, arrays, metadata)
            loaded = load_cnn_dataset(directory)
        self.assertTrue(np.array_equal(loaded["x_train"], arrays["x_train"]))
        self.assertEqual(loaded["metadata"]["channels"], CNN_CHANNELS)

    def test_invalid_input_contract_fails(self) -> None:
        demand, grid, mask, metadata = synthetic_inputs()
        with self.assertRaisesRegex(ValueError, "lacks NB4-required columns"):
            validate_tensor_inputs(demand.drop(columns="Period"), grid, mask, metadata)
