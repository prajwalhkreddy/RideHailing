"""Standalone proposed historical customer-sensitivity model contracts."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.pricing.customer_sensitivity import (
    HistoricalCustomerSensitivityModel, dispatch_price, maximum_price,
    sample_positive_truncated_normal,
)


class HistoricalCustomerSensitivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.groups = pd.DataFrame({
            "WeatherCode": [1., 2.], "Period": [3, 4],
            "P_base": [20., 30.], "D_base": [4., 6.],
            "epsilon_mean": [1., 2.], "epsilon_std_population": [.5, 0.],
        })

    def model(self, seed: int = 42) -> HistoricalCustomerSensitivityModel:
        return HistoricalCustomerSensitivityModel(self.groups, np.random.default_rng(seed))

    @staticmethod
    def fallback_groups() -> pd.DataFrame:
        return pd.DataFrame({
            "fallback_level": ["period", "weather", "global"],
            "WeatherCode": [np.nan, 1., np.nan], "Period": [4, pd.NA, pd.NA],
            "P_base": [40., 50., 60.], "D_base": [8., 10., 12.],
            "epsilon_mean": [3., 4., 5.], "epsilon_std_population": [0., 0., 0.],
            "sample_count": [10, 20, 30],
        })

    def test_group_lookup_returns_exact_artifact_parameters_and_missing_fails(self) -> None:
        parameters = self.model().parameters_for(1., 3)
        self.assertEqual(
            (parameters.p_base, parameters.d_base, parameters.epsilon_mean,
             parameters.epsilon_std_population),
            (20., 4., 1., .5),
        )
        with self.assertRaisesRegex(KeyError, "No historical sensitivity group"):
            self.model().parameters_for(9., 3)

    def test_seeded_sequences_are_reproducible_distinct_and_advance_per_request(self) -> None:
        first, second, third = self.model(7), self.model(7), self.model(8)
        sequence_a = [first.sample_epsilon(1., 3) for _ in range(12)]
        sequence_b = [second.sample_epsilon(1., 3) for _ in range(12)]
        sequence_c = [third.sample_epsilon(1., 3) for _ in range(12)]
        self.assertEqual(sequence_a, sequence_b)
        self.assertNotEqual(sequence_a, sequence_c)
        self.assertGreater(len(set(sequence_a)), 1)
        self.assertTrue(all(np.isfinite(value) and value > 0 for value in sequence_a))

    def test_zero_sigma_is_deterministic_and_invalid_parameters_fail(self) -> None:
        model = self.model()
        self.assertEqual([model.sample_epsilon(2., 4) for _ in range(3)], [2., 2., 2.])
        for column, value in (
            ("epsilon_mean", np.nan), ("epsilon_std_population", np.inf),
            ("epsilon_std_population", -1.),
        ):
            invalid = self.groups.copy(); invalid.loc[0, column] = value
            with self.subTest(column=column, value=value), self.assertRaises(ValueError):
                HistoricalCustomerSensitivityModel(invalid, np.random.default_rng(1))
        with self.assertRaisesRegex(ValueError, "requires epsilon_mean"):
            sample_positive_truncated_normal(0., 0., np.random.default_rng(1))

    def test_truncated_normal_statistical_sanity(self) -> None:
        rng = np.random.default_rng(123)
        draws = np.array([sample_positive_truncated_normal(1., .5, rng) for _ in range(5_000)])
        self.assertTrue(np.isfinite(draws).all())
        self.assertTrue((draws > 0).all())
        self.assertGreater(draws.mean(), 1.)
        self.assertLess(draws.mean(), 1.2)
        self.assertGreater(np.quantile(draws, .05), 0.)
        self.assertLess(np.quantile(draws, .95), 2.)

    def test_dispatch_and_maximum_price_formulas_and_validation(self) -> None:
        self.assertEqual(dispatch_price(20., 1.1), 22.)
        self.assertEqual(maximum_price(20., 4., 4., 2.), 20.)
        self.assertEqual(maximum_price(20., 4., 6., 2.), 25.)
        self.assertEqual(maximum_price(20., 4., 2., 2.), 15.)
        self.assertLess(maximum_price(20., 4., 6., 4.), maximum_price(20., 4., 6., 2.))
        self.assertGreater(maximum_price(20., 4., 2., 4.), maximum_price(20., 4., 2., 2.))
        for arguments in ((0., 1.), (20., 0.), (np.inf, 1.)):
            with self.subTest(dispatch=arguments), self.assertRaises(ValueError):
                dispatch_price(*arguments)
        for arguments in ((0., 4., 2., 1.), (20., 0., 2., 1.), (20., 4., -1., 1.), (20., 4., 2., 0.)):
            with self.subTest(maximum=arguments), self.assertRaises(ValueError):
                maximum_price(*arguments)

    def test_structured_acceptance_includes_equality_acceptance(self) -> None:
        deterministic = pd.DataFrame({
            "WeatherCode": [1.], "Period": [3], "P_base": [20.], "D_base": [4.],
            "epsilon_mean": [2.], "epsilon_std_population": [0.],
        })
        model = HistoricalCustomerSensitivityModel(deterministic, np.random.default_rng(1))
        equal = model.evaluate(1., 3, 4., 1.)
        below = model.evaluate(1., 3, 6., 1.)
        above = model.evaluate(1., 3, 2., 1.)
        self.assertTrue(equal.accepted)
        self.assertEqual(equal.p_dispatch, equal.p_max)
        self.assertTrue(below.accepted)
        self.assertFalse(above.accepted)
        self.assertEqual(
            (equal.weather_code, equal.period, equal.p_base, equal.d_base,
             equal.actual_distance, equal.alpha, equal.epsilon_customer),
            (1., 3, 20., 4., 4., 1., 2.),
        )

    def test_hierarchical_lookup_order_levels_and_consistent_parameter_records(self) -> None:
        model = HistoricalCustomerSensitivityModel(
            self.groups, np.random.default_rng(1), self.fallback_groups(), "hierarchical",
        )
        cases = [((1., 3), "exact", 20., 4., 1.), ((9., 4), "period", 40., 8., 3.),
                 ((1., 8), "weather", 50., 10., 4.), ((9., 8), "global", 60., 12., 5.)]
        for arguments, level, p_base, d_base, mean in cases:
            with self.subTest(level=level):
                resolved = model.resolve_parameters(*arguments)
                self.assertEqual(resolved.fallback_level_used, level)
                self.assertEqual(
                    (resolved.parameters.p_base, resolved.parameters.d_base, resolved.parameters.epsilon_mean),
                    (p_base, d_base, mean),
                )
        with self.assertRaises(KeyError):
            self.model().resolve_parameters(9., 4)

    def test_fallback_evaluation_reuses_one_record_and_is_seed_reproducible(self) -> None:
        first = HistoricalCustomerSensitivityModel(self.groups, np.random.default_rng(7), self.fallback_groups(), "hierarchical")
        second = HistoricalCustomerSensitivityModel(self.groups, np.random.default_rng(7), self.fallback_groups(), "hierarchical")
        a, b = first.evaluate(9., 4, 8., 1.), second.evaluate(9., 4, 8., 1.)
        self.assertEqual((a.p_base, a.d_base, a.epsilon_customer, a.sensitivity_lookup_level), (40., 8., 3., "period"))
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
