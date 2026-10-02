"""Focused input-population contracts; no simulation dependencies."""
import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from src.elasticity_v2.population import COLUMNS, clean_trips, join_weather, weather_coverage


class PopulationTests(unittest.TestCase):
    def test_boundaries_and_basic_rules(self):
        raw = pd.DataFrame({'tpep_pickup_datetime': ['2025-12-31 23:59:59', '2026-01-01', '2026-03-31 23:59:59', '2026-04-01', None, '2026-02-01', '2026-02-01', '2026-02-01', '2026-02-01'],
                            'fare_amount': [1, 1, 2, 1, 1, np.inf, 0, 1, 1],
                            'trip_distance': [1, 101, 2, 1, 1, 1, 1, np.nan, -1]})
        # Mixed timestamp formats are parsed individually to construct test input.
        raw['tpep_pickup_datetime'] = pd.to_datetime(raw.tpep_pickup_datetime, format='mixed')
        clean, report = clean_trips(raw)
        self.assertEqual(len(clean), 2)
        self.assertEqual(clean.trip_distance.tolist(), [101, 2])
        self.assertEqual(report['outside_window_valid_timestamp'], 2)
        self.assertEqual(set(report['failures_all_source_rows'].values()), {1})

    def test_month_calendars_and_duplicates(self):
        for month, n in [('2026-01', 744), ('2026-02', 672), ('2026-03', 744)]:
            weather = pd.DataFrame({'Datetime': pd.date_range(month+'-01', periods=n, freq='h'), 'WeatherCode': 1})
            self.assertEqual(weather_coverage(weather, month)['actual_hours'], n)
            for bad in [weather.iloc[:-1], pd.concat([weather, weather.iloc[:1]]), weather.assign(WeatherCode=np.nan)]:
                with self.assertRaises(ValueError):
                    weather_coverage(bad, month)

    def test_join_determinism_and_schema_without_od(self):
        raw = pd.DataFrame({'tpep_pickup_datetime': pd.to_datetime(['2026-02-01 00:59:59', '2026-02-01 01:00:00', '2026-02-01 02:00:00']), 'fare_amount': [1, 2, 3], 'trip_distance': [2, 3, 4]})
        clean, _ = clean_trips(raw)
        weather = pd.DataFrame({'Datetime': pd.date_range('2026-02-01', periods=2, freq='h'), 'WeatherCode': [7, 9]})
        a = join_weather(clean, weather)
        pd.testing.assert_frame_equal(a, join_weather(clean, weather.iloc[::-1]))
        self.assertEqual(a.columns.tolist(), COLUMNS)
        self.assertEqual(a.WeatherCode.iloc[:2].tolist(), [7, 9])
        self.assertTrue(pd.isna(a.WeatherCode.iloc[2]))
        with self.assertRaises(ValueError):
            join_weather(clean, pd.concat([weather, weather.iloc[:1]]))

    def test_saved_population(self):
        root = Path('data/processed/elasticity_v2')
        if not (root / 'population_manifest.json').exists():
            self.skipTest('Population not yet generated')
        manifest = json.loads((root / 'population_manifest.json').read_text())
        source = pq.ParquetFile(root / 'elasticity_input_2026_01_03.parquet')
        self.assertEqual(source.schema_arrow.names, COLUMNS)
        self.assertEqual(source.metadata.num_rows, manifest['join']['matched_rows'])
        self.assertEqual(manifest['join']['unmatched_rows'], 0)
        self.assertEqual(sum(w['actual_hours'] for w in manifest['weather'].values()), 2160)
        weather = pd.concat([pd.read_parquet(v['file']) for v in manifest['weather'].values()])
        lookup = weather.set_index('Datetime').WeatherCode
        for batch in source.iter_batches(batch_size=250000):
            t = batch.to_pandas()
            self.assertTrue(t.pickup_timestamp.ge('2026-01-01').all())
            self.assertTrue(t.pickup_timestamp.lt('2026-04-01').all())
            self.assertTrue(t.hour.eq(t.pickup_timestamp.dt.hour).all())
            self.assertTrue(np.isfinite(t[['fare', 'trip_distance']]).all().all())
            self.assertTrue(t[['fare', 'trip_distance']].gt(0).all().all())
            self.assertTrue(t.WeatherCode.notna().all())
            expected = t.pickup_timestamp.dt.floor('h').map(lookup)
            np.testing.assert_array_equal(t.WeatherCode.to_numpy(), expected.to_numpy())


if __name__ == '__main__':
    unittest.main()
