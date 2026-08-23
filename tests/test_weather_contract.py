"""Tests for the fixed legacy Meteostat weather input contract."""

import unittest

import json
from pathlib import Path
import tempfile

import pandas as pd

from src.data.weather import (
    WEATHER_COLUMNS, build_weather_metadata, prepare_processed_weather,
    prepare_weather, save_weather, validate_processed_weather_contract,
)
from src.demand.aggregation import merge_hourly_weather


class WeatherContractTests(unittest.TestCase):
    def test_missing_weather_columns_fail_loudly(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            prepare_processed_weather(pd.DataFrame({"Datetime": ["2026-01-01"]}))

    def test_legacy_forward_then_backward_fill(self) -> None:
        weather = pd.DataFrame({"Datetime": ["2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 02:00"], "Temperature": [None, 2.0, None], "WindSpeed": [1.0, None, 3.0], "WeatherCode": [None, 4.0, None]})
        result = prepare_processed_weather(weather)
        self.assertEqual(result["Temperature"].tolist(), [2.0, 2.0, 2.0])
        self.assertEqual(result["WindSpeed"].tolist(), [1.0, 1.0, 3.0])
        self.assertEqual(result["WeatherCode"].tolist(), [4.0, 4.0, 4.0])

    def test_hourly_weather_join_applies_to_both_half_hours(self) -> None:
        master = pd.DataFrame({"TimeSlot": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 00:30"]), "GridID": [0, 0], "Demand": [1, 2], "Row": [0, 0], "Column": [0, 0]})
        weather = prepare_processed_weather(pd.DataFrame({"Datetime": ["2026-01-01 00:00"], "Temperature": [1.0], "WindSpeed": [2.0], "WeatherCode": [3]}))
        result = merge_hourly_weather(master, weather)
        self.assertEqual(result[["Temperature", "WindSpeed", "WeatherCode"]].values.tolist(), [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]])

    def test_wrong_month_calendar_fails(self) -> None:
        weather = pd.DataFrame({"Datetime": pd.date_range("2026-02-01", periods=744, freq="h"), "Temperature": [1.0] * 744, "WindSpeed": [2.0] * 744, "WeatherCode": [3] * 744})
        with self.assertRaisesRegex(ValueError, "must cover every hour"):
            validate_processed_weather_contract(weather, "2026-01")

    def test_timezone_aware_weather_fails_without_a_research_decision(self) -> None:
        weather = pd.DataFrame({"Datetime": [pd.Timestamp("2026-01-01 00:00", tz="UTC")], "Temperature": [1.0], "WindSpeed": [2.0], "WeatherCode": [3]})
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            prepare_processed_weather(weather)

    def test_legacy_provider_response_is_renamed_and_prepared(self) -> None:
        raw = pd.DataFrame({"temp": [None, 2.0], "wspd": [1.0, None], "coco": [None, 4.0]}, index=pd.DatetimeIndex(["2026-01-01 00:00", "2026-01-01 01:00"], name="time"))
        prepared, counts = prepare_weather(raw)
        self.assertEqual(prepared.columns.tolist(), WEATHER_COLUMNS)
        self.assertEqual(prepared["Temperature"].tolist(), [2.0, 2.0])
        self.assertEqual(counts["before_fill"], {"Temperature": 1, "WindSpeed": 1, "WeatherCode": 1})
        self.assertEqual(counts["after_fill"], {"Temperature": 0, "WindSpeed": 0, "WeatherCode": 0})

    def test_save_weather_round_trips_the_legacy_four_column_contract(self) -> None:
        weather = prepare_processed_weather(pd.DataFrame({"Datetime": pd.date_range("2026-01-01", periods=2, freq="h"), "Temperature": [1.0, 2.0], "WindSpeed": [3.0, 4.0], "WeatherCode": [1, 2]}))
        config = {"provider": "meteostat", "latitude": 40.7128, "longitude": -74.006, "altitude_m": 10, "start": "2026-01-01 00:00:00", "end": "2026-01-31 23:59:59"}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nyc_weather_processed_2026_01.parquet"
            metadata = build_weather_metadata(weather=weather, raw_row_count=2, fill_counts={"before_fill": {"Temperature": 0, "WindSpeed": 0, "WeatherCode": 0}, "after_fill": {"Temperature": 0, "WindSpeed": 0, "WeatherCode": 0}}, config=config)
            artifact, metadata_file = save_weather(weather, output, metadata)
            reloaded = pd.read_parquet(artifact)
            saved_metadata = json.loads(metadata_file.read_text())
        self.assertEqual(reloaded.columns.tolist(), WEATHER_COLUMNS)
        self.assertEqual(reloaded.values.tolist(), weather.values.tolist())
        self.assertIn("output_sha256", saved_metadata)
