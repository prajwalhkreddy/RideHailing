"""Focused Phase-1 historical customer sensitivity contracts."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.pricing.historical_sensitivity import (
    DISTANCE_MAX_MILES, DISTANCE_RESOLUTION_MILES, TRAINING_END_EXCLUSIVE,
    build_sensitivity_fallbacks, build_weather_time_lookup, preprocess_historical_sensitivity,
)


class HistoricalSensitivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lookup = pd.DataFrame({
            "TimeSlot": pd.to_datetime([
                "2026-01-01 00:00", "2026-01-01 00:30", "2026-01-25 18:30",
            ]),
            "WeatherCode": [1., 2., 1.],
            "Period": [0, 1, 37],
        })
        self.trips = pd.DataFrame({
            "tpep_pickup_datetime": pd.to_datetime([
                "2026-01-01 00:01", "2026-01-01 00:02", "2026-01-01 00:03",
                "2026-01-01 00:31", "2026-01-01 00:32",
                "2026-01-25 18:30",
            ]),
            "fare_amount": [10., 30., 20., 8., 12., 1000.],
            "trip_distance": [1., 2., 3., 1., 3., 1000.],
            "PUGridID": [10, 20, 30, 10, 20, 10],
            "DOGridID": [20, 30, 10, 20, 30, 20],
        })

    def test_exact_bases_changes_epsilon_and_population_sample_sd(self) -> None:
        result = preprocess_historical_sensitivity(self.trips, self.lookup)
        group = result.groups.set_index(["WeatherCode", "Period"]).loc[(1., 0)]
        self.assertEqual(group.P_base, 20.)
        self.assertEqual(group.D_base, 2.)
        observations = result.observations.loc[result.observations.WeatherCode == 1.].set_index("fare_amount")
        self.assertAlmostEqual(observations.at[10., "DeltaP"], (10. - 20.) / 20.)
        self.assertAlmostEqual(observations.at[10., "DeltaD"], (1. - 2.) / 2.)
        self.assertAlmostEqual(observations.at[10., "epsilon"], abs((-.5) / (-.5)))
        expected = np.asarray([1., 0.])
        self.assertAlmostEqual(group.epsilon_mean, expected.mean())
        self.assertAlmostEqual(group.epsilon_std_population, expected.std(ddof=0))
        self.assertAlmostEqual(group.epsilon_std_sample, expected.std(ddof=1))
        self.assertTrue((result.observations.epsilon >= 0).all())

    def test_absolute_value_is_applied_before_group_statistics(self) -> None:
        trips = self.trips.iloc[:3].copy()
        trips["trip_distance"] = [1., 2., 4.]
        result = preprocess_historical_sensitivity(trips, self.lookup)
        signed = result.observations.DeltaP / result.observations.DeltaD
        self.assertTrue((signed < 0).any())
        self.assertAlmostEqual(result.groups.iloc[0].epsilon_mean, signed.abs().mean())
        self.assertNotAlmostEqual(result.groups.iloc[0].epsilon_mean, abs(signed.mean()))

    def test_zero_delta_d_is_excluded_counted_and_never_infinite(self) -> None:
        result = preprocess_historical_sensitivity(self.trips, self.lookup)
        first = result.groups.set_index(["WeatherCode", "Period"]).loc[(1., 0)]
        second = result.groups.set_index(["WeatherCode", "Period"]).loc[(2., 1)]
        self.assertEqual(first.excluded_zero_delta_d_count, 1)
        self.assertEqual(second.excluded_zero_delta_d_count, 0)
        self.assertEqual(result.counts["excluded_zero_delta_d_count"], 1)
        self.assertEqual(result.counts["excluded_below_distance_resolution_count"], 1)
        self.assertTrue(np.isfinite(result.observations.epsilon).all())

    def test_distance_above_100_is_excluded_before_bases_but_100_is_valid(self) -> None:
        trips = self.trips.iloc[:4].copy()
        trips["fare_amount"] = [10., 20., 30., 10_000.]
        trips["trip_distance"] = [1., 3., DISTANCE_MAX_MILES, 101.]
        trips["tpep_pickup_datetime"] = pd.to_datetime([
            "2026-01-01 00:01", "2026-01-01 00:02",
            "2026-01-01 00:03", "2026-01-01 00:04",
        ])
        result = preprocess_historical_sensitivity(trips, self.lookup)
        group = result.groups.iloc[0]
        self.assertEqual(result.counts["excluded_distance_above_100_count"], 1)
        self.assertEqual(result.counts["valid_input_row_count"], 3)
        self.assertEqual(group.P_base, 20.)
        self.assertEqual(group.D_base, (1. + 3. + 100.) / 3.)
        self.assertIn(100., result.observations.trip_distance.to_numpy())
        self.assertNotIn(101., result.observations.trip_distance.to_numpy())

    def test_raw_distance_resolution_is_applied_after_group_bases(self) -> None:
        trips = self.trips.iloc[:4].copy()
        trips["tpep_pickup_datetime"] = pd.to_datetime([
            "2026-01-01 00:01", "2026-01-01 00:02",
            "2026-01-01 00:03", "2026-01-01 00:04",
        ])
        trips["fare_amount"] = [10., 20., 30., 40.]
        trips["trip_distance"] = [1.995, 2.005, 2.03, 1.97]
        result = preprocess_historical_sensitivity(trips, self.lookup)
        group = result.groups.iloc[0]
        self.assertAlmostEqual(group.P_base, 25.)
        self.assertAlmostEqual(group.D_base, 2.)
        self.assertEqual(group.excluded_below_distance_resolution_count, 2)
        self.assertEqual(result.counts["excluded_below_distance_resolution_count"], 2)
        self.assertEqual(set(result.observations.trip_distance), {1.97, 2.03})
        expected = (result.observations.DeltaP / result.observations.DeltaD).abs()
        np.testing.assert_allclose(result.observations.epsilon, expected)

    def test_raw_distance_deviation_exactly_resolution_is_eligible(self) -> None:
        trips = self.trips.iloc[:2].copy()
        trips["fare_amount"] = [10., 30.]
        trips["trip_distance"] = [2. - DISTANCE_RESOLUTION_MILES, 2. + DISTANCE_RESOLUTION_MILES]
        result = preprocess_historical_sensitivity(trips, self.lookup)
        self.assertAlmostEqual(result.groups.iloc[0].D_base, 2.)
        self.assertEqual(result.counts["excluded_below_distance_resolution_count"], 0)
        self.assertEqual(len(result.observations), 2)

    def test_cutoff_is_end_exclusive_and_cannot_change_bases(self) -> None:
        result = preprocess_historical_sensitivity(self.trips, self.lookup)
        group = result.groups.set_index(["WeatherCode", "Period"]).loc[(1., 0)]
        self.assertEqual((group.P_base, group.D_base), (20., 2.))
        self.assertEqual(result.counts["excluded_outside_training_period_count"], 1)
        self.assertFalse((result.observations.tpep_pickup_datetime >= TRAINING_END_EXCLUSIVE).any())

    def test_grids_are_pooled_while_weather_time_groups_remain_separate(self) -> None:
        result = preprocess_historical_sensitivity(self.trips, self.lookup)
        groups = result.groups.set_index(["WeatherCode", "Period"])
        self.assertEqual(set(groups.index), {(1., 0), (2., 1)})
        self.assertEqual(groups.loc[(1., 0), "sample_count_raw"], 3)
        self.assertEqual(groups.loc[(2., 1), "P_base"], 10.)
        self.assertEqual(groups.loc[(2., 1), "D_base"], 2.)

    def test_period_mapping_matches_existing_half_hour_convention(self) -> None:
        full = pd.DataFrame({
            "TimeSlot": pd.date_range("2026-01-01", periods=48, freq="30min"),
            "WeatherCode": 1., "Period": np.arange(48),
        })
        mapped = build_weather_time_lookup(full)
        self.assertEqual(mapped.Period.tolist(), list(range(48)))
        invalid = full.copy(); invalid.loc[1, "Period"] = 2
        with self.assertRaisesRegex(ValueError, "48-period"):
            build_weather_time_lookup(invalid)

    def test_input_is_not_mutated_and_result_is_deterministic(self) -> None:
        original_trips, original_lookup = self.trips.copy(deep=True), self.lookup.copy(deep=True)
        first = preprocess_historical_sensitivity(self.trips, self.lookup)
        second = preprocess_historical_sensitivity(self.trips, self.lookup)
        pd.testing.assert_frame_equal(self.trips, original_trips)
        pd.testing.assert_frame_equal(self.lookup, original_lookup)
        pd.testing.assert_frame_equal(first.groups, second.groups)
        pd.testing.assert_frame_equal(first.observations, second.observations)
        self.assertEqual(first.counts, second.counts)

    def test_invalid_rows_are_recorded_by_reason(self) -> None:
        invalid = pd.DataFrame({
            "tpep_pickup_datetime": ["bad", "2026-01-01 00:04", "2026-01-01 00:05"],
            "fare_amount": [10., 0., 10.], "trip_distance": [1., 1., np.inf],
        })
        combined = pd.concat([self.trips.iloc[:3], invalid], ignore_index=True)
        result = preprocess_historical_sensitivity(combined, self.lookup)
        self.assertEqual(result.counts["excluded_invalid_timestamp_count"], 1)
        self.assertEqual(result.counts["excluded_invalid_fare_count"], 1)
        self.assertEqual(result.counts["excluded_invalid_distance_count"], 1)

    def test_fallback_levels_recompute_own_training_bases_and_are_deterministic(self) -> None:
        lookup = pd.DataFrame({
            "TimeSlot": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:30", "2026-01-02 00:00", "2026-01-25 18:30"]),
            "WeatherCode": [1., 1., 2., 9.], "Period": [0, 1, 0, 37],
        })
        rows = []
        for timestamp, fares, distances in (
            ("2026-01-01 00:00", [10., 20., 30.], [1., 2., 4.]),
            ("2026-01-01 00:30", [20., 30., 40.], [2., 4., 8.]),
            ("2026-01-02 00:00", [40., 50., 60.], [3., 6., 9.]),
        ):
            for offset, (fare, distance) in enumerate(zip(fares, distances), 1):
                rows.append((pd.Timestamp(timestamp) + pd.Timedelta(minutes=offset), fare, distance))
        rows.extend([
            (pd.Timestamp("2026-01-02 00:04"), 10000., 101.),
            (pd.Timestamp("2026-01-25 18:30"), 10000., 50.),
        ])
        trips = pd.DataFrame(rows, columns=["tpep_pickup_datetime", "fare_amount", "trip_distance"])
        first = build_sensitivity_fallbacks(trips, lookup)
        second = build_sensitivity_fallbacks(trips, lookup)
        pd.testing.assert_frame_equal(first, second)
        period = first[(first.fallback_level == "period") & (first.Period == 0)].iloc[0]
        weather = first[(first.fallback_level == "weather") & (first.WeatherCode == 1.)].iloc[0]
        global_row = first[first.fallback_level == "global"].iloc[0]
        self.assertEqual((period.P_base, period.D_base), (35., 25. / 6.))
        self.assertEqual((weather.P_base, weather.D_base), (25., 3.5))
        self.assertEqual((global_row.P_base, global_row.D_base), (100. / 3., 13. / 3.))
        self.assertLess(global_row.P_base, 1000.)
        self.assertTrue(np.isfinite(first[["epsilon_mean", "epsilon_std_population"]]).all().all())
        self.assertTrue((first.sample_count <= 9).all())

    def test_fallback_excludes_sub_resolution_deviations_from_epsilon_only(self) -> None:
        lookup = pd.DataFrame({
            "TimeSlot": [pd.Timestamp("2026-01-01")], "WeatherCode": [1.], "Period": [0],
        })
        trips = pd.DataFrame({
            "tpep_pickup_datetime": pd.to_datetime([
                "2026-01-01 00:01", "2026-01-01 00:02", "2026-01-01 00:03", "2026-01-01 00:04",
            ]),
            "fare_amount": [10., 20., 30., 40.],
            "trip_distance": [1., 1.995, 2.005, 3.],
        })
        result = build_sensitivity_fallbacks(trips, lookup)
        self.assertTrue((result.P_base == 25.).all())
        self.assertTrue((result.D_base == 2.).all())
        self.assertTrue((result.sample_count == 2).all())
        eligible = trips.iloc[[0, 3]]
        expected = abs(((eligible.fare_amount - 25.) / 25.) / ((eligible.trip_distance - 2.) / 2.))
        self.assertTrue(np.allclose(result.epsilon_mean, expected.mean()))


if __name__ == "__main__":
    unittest.main()
