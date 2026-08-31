"""Focused contracts for deterministic read-only validation reporting."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from scripts.generate_validation_figures import EXPECTED_FACTORS, EXPECTED_TOTALS, generate_reporting
from src.pricing.linucb import PRICING_FACTORS
from src.reporting.customer_response import customer_acceptance_summary, customer_response_table
from src.reporting.dispatch import dispatch_metric_summary, dispatch_summary_table
from src.reporting.pricing import pricing_decision_table, pricing_factor_summary
from src.simulation.validation_24h import run_small_fleet_validation


class ValidationReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = run_small_fleet_validation(48, seed=42)
        cls.pricing = pricing_decision_table(cls.report)
        cls.customer = customer_response_table(cls.report)
        cls.dispatch = dispatch_summary_table(cls.report)

    def test_pricing_rows_factors_probabilities_rewards_and_counts(self) -> None:
        self.assertEqual(len(self.pricing), 192)
        counts = self.pricing.selected_pricing_factor.value_counts().to_dict()
        self.assertEqual(counts, EXPECTED_FACTORS)
        self.assertTrue(set(self.pricing.selected_pricing_factor).issubset(PRICING_FACTORS))
        probabilities = self.pricing[["p_stay", "p_north", "p_east", "p_south", "p_west"]].to_numpy()
        np.testing.assert_allclose(probabilities.sum(axis=1), 1.)
        self.assertTrue(((self.pricing.normalized_reward >= 0) & (self.pricing.normalized_reward <= 1)).all())
        self.assertTrue((self.pricing.generated_requests == self.pricing.accepted_requests + self.pricing.rejected_requests).all())

    def test_dispatch_funnel_and_aggregate_rates_are_exact(self) -> None:
        totals = {name: int(self.dispatch[name].sum()) for name in EXPECTED_TOTALS}
        self.assertEqual(totals, EXPECTED_TOTALS)
        self.assertTrue((self.dispatch.accepted == self.dispatch.served + self.dispatch.accepted_unserved).all())
        metrics = dispatch_metric_summary(self.dispatch).set_index("metric").value
        self.assertAlmostEqual(metrics.acceptance_rate, 1146 / 1536)
        self.assertAlmostEqual(metrics.dispatch_success_rate, 1059 / 1146)
        self.assertAlmostEqual(metrics.service_rate, 1059 / 1536)

    def test_factor_summaries_use_aggregate_count_ratios(self) -> None:
        pricing = pricing_factor_summary(self.pricing)
        customer = customer_acceptance_summary(self.customer)
        self.assertEqual(int(pricing.decisions.sum()), 192)
        for row in customer.itertuples(index=False):
            self.assertAlmostEqual(row.acceptance_rate, row.accepted / row.generated)

    def test_same_seed_produces_identical_summary_tables(self) -> None:
        first = run_small_fleet_validation(2, seed=9)
        second = run_small_fleet_validation(2, seed=9)
        pd.testing.assert_frame_equal(pricing_decision_table(first), pricing_decision_table(second))
        pd.testing.assert_frame_equal(customer_response_table(first), customer_response_table(second))
        pd.testing.assert_frame_equal(dispatch_summary_table(first), dispatch_summary_table(second))

    def test_generation_is_deterministic_nonmutating_and_produces_expected_files(self) -> None:
        signature = self.report.trajectory_signature
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = generate_reporting(first_dir, self.report, plots=True)
            second = generate_reporting(second_dir, self.report, plots=False)
            self.assertEqual(self.report.trajectory_signature, signature)
            first_root, second_root = Path(first_dir), Path(second_dir)
            pngs = [path for path in first if path.suffix == ".png"]
            self.assertEqual(len(pngs), 11)
            self.assertTrue(all(path.is_file() and path.stat().st_size > 0 for path in pngs))
            expected = {
                "summary.json", "figure_manifest.json", "pricing_decisions.csv",
                "customer_response.csv", "dispatch_summary.csv",
            }
            validation = first_root / "results/validation/validation_50v_4g_48slots_seed42"
            self.assertTrue(expected.issubset({path.name for path in validation.iterdir()}))
            for relative in (
                "results/validation/validation_50v_4g_48slots_seed42/summary.json",
                "results/validation/validation_50v_4g_48slots_seed42/pricing_decisions.csv",
                "results/validation/validation_50v_4g_48slots_seed42/customer_response.csv",
                "results/validation/validation_50v_4g_48slots_seed42/dispatch_summary.csv",
            ):
                self.assertEqual((first_root / relative).read_bytes(), (second_root / relative).read_bytes())
            summary = json.loads((validation / "summary.json").read_text())
            self.assertEqual(summary["generated"], 1536)


if __name__ == "__main__":
    unittest.main()
