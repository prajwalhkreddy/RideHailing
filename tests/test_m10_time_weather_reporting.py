"""Focused reporting checks against frozen artifacts; no simulations."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

import numpy as np
import pandas as pd
from scripts.plot_m10_time_weather import DEFAULT, STATS, clock_label, prepare_series


class TimeWeatherReportingTests(unittest.TestCase):
    def test_sparse_conditions_are_gaps_without_pooling(self):
        table = pd.DataFrame([
            [0, 1, 2, .2, .15, .1, .3],
            [2, 1, 1, .7, .7, .7, .7],
            [0, 2, 3, .9, .8, .4, 1.1],
            [1, 2, 0, np.nan, np.nan, np.nan, np.nan],
        ], columns=['time_bucket', 'WeatherCode', 'sample_count'] + STATS)
        mean = prepare_series(table, [1, 2, 21], 3, 1)
        band = prepare_series(table, [1, 2, 21], 3, 2)
        self.assertEqual(mean.loc[(0, 1), 'mean_epsilon'], .2)
        self.assertEqual(mean.loc[(0, 2), 'mean_epsilon'], .9)
        self.assertEqual(mean.loc[(2, 1), 'mean_epsilon'], .7)
        self.assertTrue(band.loc[(2, 1), STATS].isna().all())
        self.assertTrue(mean.loc[(1, 1), STATS].isna().all())
        self.assertTrue(mean.loc[(1, 2), STATS].isna().all())
        self.assertTrue(mean.xs(21, level='WeatherCode')[STATS].isna().all().all())

    def test_every_frozen_statistic_matches_display_grid(self):
        for variant, periods in [('hourly', 24), ('30min', 48)]:
            table = pd.read_csv(DEFAULT / f'sensitivity_conditions_{variant}.csv', float_precision='round_trip')
            codes = sorted(table.WeatherCode.unique())
            for minimum in [1, 2]:
                grid = prepare_series(table, codes, periods, minimum)
                for row in table.itertuples():
                    actual = grid.loc[(row.time_bucket, row.WeatherCode), STATS].to_numpy(dtype=float)
                    expected = np.array([getattr(row, col) for col in STATS]) if row.sample_count >= minimum else np.full(4, np.nan)
                    np.testing.assert_array_equal(actual, expected)
                self.assertEqual(len(grid), periods * len(codes))

    def test_original_artifacts_byte_identical_and_manifest_valid(self):
        manifest_path = DEFAULT / 'artifact_manifest.json'
        original = json.loads(subprocess.check_output(['git', 'show', f'HEAD:{manifest_path}']))
        current = json.loads(manifest_path.read_text())
        for name, checksum in original.items():
            if name != 'README.md':
                self.assertEqual(hashlib.sha256((DEFAULT / name).read_bytes()).hexdigest(), checksum, name)
        for name, checksum in current.items():
            self.assertEqual(hashlib.sha256((DEFAULT / name).read_bytes()).hexdigest(), checksum, name)
        old_verification = subprocess.check_output(['git', 'show', f'HEAD:{DEFAULT}/verification.json'])
        self.assertEqual((DEFAULT / 'verification.json').read_bytes(), old_verification)

    def test_support_limits_and_clock_labels(self):
        manifest = json.loads((DEFAULT / 'elasticity_time_weather_chart_manifest.json').read_text())
        self.assertEqual(manifest['support']['hourly']['observations'], 487710)
        self.assertEqual(manifest['support']['hourly']['missing_combinations'], 195)
        self.assertEqual(manifest['support']['hourly']['observations_by_weather']['21'], 0)
        self.assertEqual(len(manifest['support']['30min']['singleton_distribution_omissions']), 2)
        summary = pd.read_csv(DEFAULT / 'overall_sensitivity_summary.csv', float_precision='round_trip')
        for chart in manifest['charts']:
            if chart['view_only_upper_limit'] is not None:
                expected = summary.loc[summary.variant.eq(chart['variant']) & summary['transform'].eq('raw'), 'p99'].iloc[0]
                self.assertEqual(chart['view_only_upper_limit'], expected)
        self.assertEqual(clock_label(0, 30), '00:00')
        self.assertEqual(clock_label(1, 30), '00:30')
        self.assertEqual(clock_label(47, 30), '23:30')
        self.assertEqual(clock_label(23, 60), '23:00')


if __name__ == '__main__':
    unittest.main()
