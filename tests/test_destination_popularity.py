"""Approved destination/drop-off popularity methodology tests."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from src.popularity.destination import (
    POPULARITY_ENCODING, PopularityThresholds, aggregate_dropoffs,
    apply_popularity_levels, fit_popularity_thresholds, popularity_level,
    trailing_dropoff_average,
)


class DestinationPopularityTests(unittest.TestCase):
    slots = pd.date_range("2026-01-01 08:00", periods=7, freq="30min")

    def test_dropoff_timestamp_and_destination_control_complete_aggregation(self) -> None:
        trips = pd.DataFrame({
            "tpep_pickup_datetime": pd.to_datetime(["2026-01-01 08:20", "2026-01-01 08:35", "2026-01-01 08:36"]),
            "tpep_dropoff_datetime": pd.to_datetime(["2026-01-01 08:43", "2026-01-01 08:44", "2026-01-01 08:50"]),
            "PUGridID": [7, 8, 7], "DOGridID": [7, 7, 8],
        })
        result = aggregate_dropoffs(trips, [7, 8], self.slots)
        row = result.set_index(["TimeSlot", "GridID"])
        self.assertEqual(row.at[(pd.Timestamp("2026-01-01 08:30"), 7), "dropoff_count"], 2)
        self.assertEqual(row.at[(pd.Timestamp("2026-01-01 08:30"), 8), "dropoff_count"], 1)
        self.assertEqual(row.at[(pd.Timestamp("2026-01-01 08:00"), 7), "dropoff_count"], 0)

    def test_trailing_six_slots_excludes_current_and_warms_up(self) -> None:
        counts = pd.DataFrame({"TimeSlot": self.slots, "GridID": 7, "dropoff_count": [2, 4, 6, 8, 10, 12, 14]})
        result = trailing_dropoff_average(counts).set_index("TimeSlot")
        self.assertTrue(np.isnan(result.at[self.slots[0], "dropoff_ma_3h"]))
        self.assertEqual(result.at[self.slots[1], "dropoff_ma_3h"], 2)
        self.assertEqual(result.at[self.slots[6], "dropoff_ma_3h"], 7)

    def test_current_and_future_changes_cannot_leak_backward(self) -> None:
        base = pd.DataFrame({"TimeSlot": self.slots, "GridID": 7, "dropoff_count": [2, 4, 6, 8, 10, 12, 14]})
        current = base.copy(); current.loc[6, "dropoff_count"] = 999
        future = base.copy(); future.loc[5, "dropoff_count"] = 999
        original = trailing_dropoff_average(base)
        self.assertEqual(trailing_dropoff_average(current).loc[6, "dropoff_ma_3h"], original.loc[6, "dropoff_ma_3h"])
        self.assertEqual(trailing_dropoff_average(future).loc[4, "dropoff_ma_3h"], original.loc[4, "dropoff_ma_3h"])
        self.assertNotEqual(trailing_dropoff_average(future).loc[6, "dropoff_ma_3h"], original.loc[6, "dropoff_ma_3h"])

    def test_global_quintile_fit_boundaries_and_encoding(self) -> None:
        thresholds = fit_popularity_thresholds(range(1, 11), reference_start=self.slots[0], reference_end_exclusive=self.slots[-1])
        np.testing.assert_allclose([thresholds.q20, thresholds.q40, thresholds.q60, thresholds.q80], [2.8, 4.6, 6.4, 8.2])
        values = [thresholds.q20, thresholds.q40, thresholds.q60, thresholds.q80, thresholds.q80 + 1]
        self.assertEqual([popularity_level(value, thresholds) for value in values], list(POPULARITY_ENCODING))
        frame = pd.DataFrame({"TimeSlot": self.slots[:5], "GridID": 7, "dropoff_count": 0, "dropoff_ma_3h": values})
        encoded = apply_popularity_levels(frame, thresholds)
        self.assertEqual(encoded.popularity_value.tolist(), [0, .25, .5, .75, 1])

    def test_duplicate_thresholds_follow_exact_inequalities(self) -> None:
        thresholds = PopularityThresholds(0, 0, 0, 1, "2026-01-01", "2026-01-02")
        self.assertTrue(thresholds.duplicates_present)
        self.assertEqual(popularity_level(0, thresholds), "Very Low")
        self.assertEqual(popularity_level(.5, thresholds), "High")
        self.assertEqual(popularity_level(2, thresholds), "Very High")

    def test_threshold_metadata_serialization_is_deterministic(self) -> None:
        thresholds = PopularityThresholds(1, 2, 3, 4, "2026-01-01", "2026-01-02")
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.json", Path(directory) / "b.json"
            thresholds.save(first); thresholds.save(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertIn('"Very High": 1.0', first.read_text())


if __name__ == "__main__":
    unittest.main()
