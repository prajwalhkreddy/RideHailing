"""Final proposed request-level 8D pricing-context contracts."""

from __future__ import annotations

from datetime import datetime
import unittest

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel
from src.pricing.request_context import (
    REQUEST_PRICING_CONTEXT_FEATURE_ORDER, WEATHER_SEVERITY,
    build_request_pricing_context, destination_popularity,
    relevant_od_routing_probability, weather_severity,
)
from src.pricing.scaler import (
    DEFAULT_BASE_PRICE_REF_P99, DEFAULT_DISTANCE_REF_P99_KM,
    PricingContextScaler, fit_base_price_reference_p99,
)


class RequestPricingContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = pd.DataFrame({
            "GridID": list(range(9)),
            "Row": [0, 0, 0, 1, 1, 1, 2, 2, 2],
            "Column": [0, 1, 2, 0, 1, 2, 0, 1, 2],
        })
        self.probabilities = np.array([.10, .20, .30, .15, .25])
        self.timestamp = datetime(2026, 1, 1, 0, 0)
        self.popularity = pd.DataFrame({
            "TimeSlot": [self.timestamp] * 9,
            "GridID": list(range(9)),
            "popularity_value": [0, .25, .5, .75, 1, 0, .25, .5, .75],
        })
        groups = pd.DataFrame({
            "WeatherCode": list(WEATHER_SEVERITY),
            "Period": [0] * len(WEATHER_SEVERITY),
            "P_base": [20.] * len(WEATHER_SEVERITY),
            "D_base": [4.] * len(WEATHER_SEVERITY),
            "epsilon_mean": [1.] * len(WEATHER_SEVERITY),
            "epsilon_std_population": [.2] * len(WEATHER_SEVERITY),
        })
        self.model = HistoricalCustomerSensitivityModel(groups, np.random.default_rng(7))

    def request(self, origin: int = 4, destination: int = 4, distance: float = 5., fare: float = 10.) -> RequestState:
        return RequestState(1, 0, origin, destination, base_fare=fare, trip_distance_km=distance)

    def test_all_cardinal_diagonal_far_and_same_grid_routing_rules(self) -> None:
        expected = {
            4: .10, 1: .20, 5: .30, 7: .15, 3: .25,
            2: .50, 0: .45, 8: .45, 6: .40,
        }
        for destination, value in expected.items():
            with self.subTest(destination=destination):
                result = relevant_od_routing_probability(4, destination, self.probabilities, self.grid)
                self.assertAlmostEqual(result, value)
                self.assertTrue(0 <= result <= 1)
        far_grid = pd.concat([
            self.grid,
            pd.DataFrame({"GridID": [20, 21], "Row": [-4, 8], "Column": [1, 9]}),
        ], ignore_index=True)
        self.assertEqual(relevant_od_routing_probability(4, 20, self.probabilities, far_grid), .20)
        self.assertAlmostEqual(relevant_od_routing_probability(4, 21, self.probabilities, far_grid), .45)

    def test_destination_popularity_uses_current_slot_and_destination_only(self) -> None:
        self.assertEqual(destination_popularity(self.popularity, self.timestamp, 4), 1.)
        first = self._build(self.request(origin=3, destination=4))
        changed_origin = self._build(self.request(origin=5, destination=4))
        changed_destination = self._build(self.request(origin=3, destination=3))
        self.assertEqual(first[3], changed_origin[3])
        self.assertNotEqual(first[3], changed_destination[3])
        previous = self.popularity.copy()
        previous["TimeSlot"] = pd.Timestamp(self.timestamp) - pd.Timedelta(minutes=30)
        with self.assertRaises(KeyError):
            destination_popularity(previous, self.timestamp, 4)

    def test_distance_and_base_price_scaling_are_exact_and_clipped(self) -> None:
        scaler = PricingContextScaler(
            45., 9., distance_ref_p99_km=DEFAULT_DISTANCE_REF_P99_KM,
            base_price_ref_p99=DEFAULT_BASE_PRICE_REF_P99,
        )
        self.assertAlmostEqual(
            scaler.scale_distance(5.), np.log1p(5.) / np.log1p(DEFAULT_DISTANCE_REF_P99_KM),
        )
        self.assertEqual(scaler.scale_distance(DEFAULT_DISTANCE_REF_P99_KM), 1.)
        self.assertEqual(scaler.scale_distance(DEFAULT_DISTANCE_REF_P99_KM + 1), 1.)
        self.assertAlmostEqual(
            scaler.scale_base_price(20.), np.log1p(20.) / np.log1p(DEFAULT_BASE_PRICE_REF_P99),
        )

    def test_base_price_is_wt_lookup_and_empirical_fare_cannot_change_it(self) -> None:
        first = self._build(self.request(fare=1.))
        second = self._build(self.request(fare=10_000.))
        self.assertEqual(first[5], second[5])
        self.assertAlmostEqual(first[5], np.log1p(20.) / np.log1p(DEFAULT_BASE_PRICE_REF_P99))

    def test_request_weighted_base_reference_and_held_out_exclusion(self) -> None:
        groups = pd.DataFrame({"WeatherCode": [1., 2.], "Period": [0, 0], "P_base": [10., 100.]})
        weather = np.array([1.] * 99 + [2., 2.])
        periods = np.zeros(101)
        times = np.array(["2026-01-01"] * 100 + ["2026-01-26"], dtype="datetime64[ns]")
        fitted = fit_base_price_reference_p99(
            weather, periods, times, groups, "2026-01-01", "2026-01-25T18:30:00",
        )
        expected = float(np.percentile(np.array([10.] * 99 + [100.]), 99))
        self.assertEqual(fitted, expected)
        # Changing only the held-out observation's group cannot change the fit.
        held_out_weather = np.concatenate([weather[:100], [1.]])
        self.assertEqual(fit_base_price_reference_p99(
            held_out_weather, periods, times, groups, "2026-01-01", "2026-01-25T18:30:00",
        ), fitted)

    def test_time_endpoints_midpoint_and_complete_frozen_order(self) -> None:
        self.assertEqual(REQUEST_PRICING_CONTEXT_FEATURE_ORDER, (
            "scaled_predicted_demand", "scaled_corrected_supply", "relevant_od_routing_probability",
            "destination_popularity", "scaled_trip_distance_km", "scaled_P_base",
            "scaled_time", "weather_severity",
        ))
        self.assertEqual(self._build(self.request())[6], 0.)
        for period in (23, 47):
            timestamp = datetime(2026, 1, 1, period // 2, 30 * (period % 2))
            popularity = self.popularity.copy(); popularity["TimeSlot"] = timestamp
            groups = pd.DataFrame({
                "WeatherCode": [1.], "Period": [period], "P_base": [20.], "D_base": [4.],
                "epsilon_mean": [1.], "epsilon_std_population": [.2],
            })
            model = HistoricalCustomerSensitivityModel(groups, np.random.default_rng(1))
            context = build_request_pricing_context(
                request=self.request(), predicted_demand=10., corrected_supply=2.,
                routing_probabilities=self.probabilities, simulation_timestamp=timestamp,
                weather_code=1., grid_lookup=self.grid, popularity_table=popularity,
                historical_customer_model=model,
            )
            self.assertEqual(context[6], period / 47.)

    def test_every_observed_weather_code_and_unknown_failure(self) -> None:
        expected = {
            1: 0, 2: 0, 3: 0, 5: .25, 7: .25, 14: .25,
            8: .5, 15: .5, 21: .5, 9: .75, 12: .75, 13: 1, 16: 1,
        }
        self.assertEqual(dict(WEATHER_SEVERITY), expected)
        for code, severity in expected.items():
            self.assertEqual(weather_severity(code), severity)
        with self.assertRaisesRegex(ValueError, "Unknown WeatherCode"):
            weather_severity(999)

    def test_builder_is_deterministic_finite_bounded_and_does_not_mutate_inputs(self) -> None:
        request = self.request(destination=2)
        grid_before, popularity_before = self.grid.copy(deep=True), self.popularity.copy(deep=True)
        rng_before = repr(self.model.rng.bit_generator.state)
        first = self._build(request)
        second = self._build(request)
        self.assertEqual(first.shape, (8,))
        self.assertEqual(first.dtype, np.float64)
        self.assertTrue(np.isfinite(first).all())
        self.assertTrue(((first >= 0) & (first <= 1)).all())
        np.testing.assert_array_equal(first, second)
        pd.testing.assert_frame_equal(self.grid, grid_before)
        pd.testing.assert_frame_equal(self.popularity, popularity_before)
        self.assertEqual(repr(self.model.rng.bit_generator.state), rng_before)
        self.assertIsNone(request.pricing_factor)
        self.assertIsNone(request.customer_accepted)
        self.assertIsNone(request.assigned_vehicle_id)

    def _build(self, request: RequestState) -> np.ndarray:
        return build_request_pricing_context(
            request=request, predicted_demand=10., corrected_supply=2.,
            routing_probabilities=self.probabilities, simulation_timestamp=self.timestamp,
            weather_code=1., grid_lookup=self.grid, popularity_table=self.popularity,
            historical_customer_model=self.model,
        )


if __name__ == "__main__":
    unittest.main()
