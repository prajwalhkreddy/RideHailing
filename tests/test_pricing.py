"""Deterministic standalone pricing, acceptance, and reward contracts."""

from __future__ import annotations

import math
import unittest

import numpy as np

from src.pricing.customer import customer_acceptance_probability, draw_customer_acceptance, offered_fare
from src.pricing.linucb import PRICING_FACTORS, DisjointLinUCB
from src.pricing.reward import (
    FARE_REF_P99, MAX_PRICING_FACTOR, REQUEST_REWARD_REF,
    ContextRevenueAccumulator, accepted_fare_revenue, request_learning_reward,
    revenue_opportunity_reward, slot_accepted_revenue,
)
from src.pricing.scaler import DEFAULT_BASE_PRICE_REF_P99
from src.pricing.scaler import PricingContextScaler
from src.pricing.state import PRICING_CONTEXT_DIMENSION, PRICING_CONTEXT_FEATURE_ORDER, build_pricing_context


class PricingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.probabilities = [0.20, 0.40, 0.25, 0.05, 0.10]
        self.context = build_pricing_context(20., 10., self.probabilities, .8)

    def test_context_exact_order_dimension_dtype_and_full_routing_vector(self) -> None:
        self.assertEqual(PRICING_CONTEXT_DIMENSION, 8)
        self.assertEqual(PRICING_CONTEXT_FEATURE_ORDER, ("scaled_predicted_demand", "scaled_current_supply", "P(STAY)", "P(NORTH)", "P(EAST)", "P(SOUTH)", "P(WEST)", "popularity"))
        self.assertEqual(self.context.dtype, np.float64)
        self.assertTrue(np.allclose(self.context, np.array([
            np.log1p(20.) / np.log1p(45.085255432128896), 1., .20, .40, .25, .05, .10, .8,
        ])))
        self.assertTrue(((0. <= self.context) & (self.context <= 1.)).all())

    def test_context_validation_rejects_invalid_inputs(self) -> None:
        invalid = (
            (1., -1., self.probabilities, 1.),
            (1., 1., [1., 0., 0., 0.], 1.),
            (1., 1., [.2, .2, .2, .2, .3], 1.),
            (1., 1., [.2, .2, .2, -.1, .5], 1.),
            (float("nan"), 1., self.probabilities, 1.),
            (1., 1., self.probabilities, float("inf")),
            (1., 1., self.probabilities, 1.1),
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                build_pricing_context(*arguments)

    def test_scaler_exact_demand_supply_edges_and_intermediate_values(self) -> None:
        scaler = PricingContextScaler(99., 9.)
        self.assertEqual([scaler.scale_demand(value) for value in (-3.5, 0., 99., 100.)], [0., 0., 1., 1.])
        self.assertAlmostEqual(scaler.scale_demand(9.), np.log1p(9.) / np.log1p(99.))
        self.assertEqual([scaler.scale_supply(value) for value in (0., 9., 10.)], [0., 1., 1.])
        self.assertAlmostEqual(scaler.scale_supply(3.), np.log1p(3.) / np.log1p(9.))
        for invalid in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(kind="demand", invalid=invalid), self.assertRaises(ValueError):
                scaler.scale_demand(invalid)
        for invalid in (-1., float("nan"), float("inf"), -float("inf")):
            with self.subTest(kind="supply", invalid=invalid), self.assertRaises(ValueError):
                scaler.scale_supply(invalid)

    def test_request_reward_reference_and_unclipped_linear_scaling(self) -> None:
        self.assertEqual(MAX_PRICING_FACTOR, 1.15)
        self.assertEqual(REQUEST_REWARD_REF, DEFAULT_BASE_PRICE_REF_P99 * 1.15)
        self.assertEqual(request_learning_reward(0., "training_reference"), 0.)
        self.assertEqual(request_learning_reward(REQUEST_REWARD_REF, "training_reference"), 1.)
        self.assertEqual(request_learning_reward(REQUEST_REWARD_REF * 2., "training_reference"), 2.)
        self.assertEqual(request_learning_reward(17., "none"), 17.)
        self.assertAlmostEqual(
            request_learning_reward(20., "training_reference") / request_learning_reward(10., "training_reference"), 2.,
        )

    def test_scaler_fit_is_persisted_and_independent_of_held_out_values(self) -> None:
        metadata = {
            "demand_ref_p99": 45.085255432128896,
            "supply_ref_p99": 9.,
            "demand_reference": {"source": "training", "test_predictions_used_for_fit": False},
            "supply_reference": {"source": "initialization"},
        }
        first = PricingContextScaler.from_metadata(metadata)
        held_out_a = np.array([-100., 0., 5.])
        held_out_b = np.array([1.e9, 1.e10])
        self.assertNotEqual(np.percentile(np.maximum(held_out_a, 0), 99), np.percentile(held_out_b, 99))
        self.assertEqual(first.demand_ref_p99, PricingContextScaler.from_metadata(metadata).demand_ref_p99)
        self.assertEqual(first.supply_ref_p99, 9.)

    def test_exact_arms_initial_state_no_aliasing_and_fixed_tie(self) -> None:
        learner = DisjointLinUCB(alpha=1.)
        self.assertEqual(learner.arms, (0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15))
        for matrix, vector in zip(learner.A, learner.b):
            self.assertTrue(np.array_equal(matrix, np.eye(8)))
            self.assertTrue(np.array_equal(vector, np.zeros(8)))
            self.assertEqual((matrix.shape, vector.shape), ((8, 8), (8,)))
        self.assertFalse(np.shares_memory(learner.A[0], learner.A[1]))
        decision = learner.select(self.context)
        self.assertEqual((decision.arm_index, decision.pricing_factor), (0, .85))
        self.assertTrue(np.isfinite(decision.scores).all())

    def test_maximum_score_selected_and_only_approved_arm_returned(self) -> None:
        learner = DisjointLinUCB(alpha=0.)
        learner.update_counts[:] = 1
        learner.b[4] = self.context.copy()
        decision = learner.select(self.context)
        self.assertEqual((decision.arm_index, decision.pricing_factor), (4, PRICING_FACTORS[4]))
        self.assertIn(decision.pricing_factor, PRICING_FACTORS)

    def test_update_changes_only_selected_arm_by_exact_outer_product(self) -> None:
        learner = DisjointLinUCB(alpha=1.)
        before_a = [value.copy() for value in learner.A]
        before_b = [value.copy() for value in learner.b]
        learner.update(self.context, 3, 25.)
        self.assertTrue(np.allclose(learner.A[3], before_a[3] + np.outer(self.context, self.context)))
        self.assertTrue(np.allclose(learner.b[3], before_b[3] + 25. * self.context))
        for index in set(range(7)) - {3}:
            self.assertTrue(np.array_equal(learner.A[index], before_a[index]))
            self.assertTrue(np.array_equal(learner.b[index], before_b[index]))
        before = learner.b[2].copy(); learner.update(self.context, 2, 0.)
        self.assertTrue(np.array_equal(learner.b[2], before))

    def test_copy_safe_state_export_and_import(self) -> None:
        learner = DisjointLinUCB(alpha=1.)
        learner.select(self.context); learner.update(self.context, 0, 10.)
        exported = learner.export_state()
        restored = DisjointLinUCB.from_state(exported)
        self.assertTrue(np.array_equal(restored.A[0], learner.A[0]))
        self.assertTrue(np.array_equal(restored.b[0], learner.b[0]))
        exported["A"][0][0, 0] = 999.
        self.assertNotEqual(restored.A[0][0, 0], 999.)
        self.assertTrue(np.array_equal(restored.pending_cold_start, learner.pending_cold_start))

    def test_global_pending_aware_cold_start_and_seeded_post_cold_ties(self) -> None:
        learner = DisjointLinUCB(alpha=1., random_seed=17)
        first = [learner.select(self.context) for _ in range(4)]
        self.assertEqual([item.pricing_factor for item in first], list(PRICING_FACTORS[:4]))
        self.assertEqual(learner.pending_cold_start.tolist(), [1, 1, 1, 1, 0, 0, 0])
        for item in first:
            learner.update(item.context, item.arm_index, .5)
        second = [learner.select(self.context) for _ in range(3)]
        self.assertEqual([item.pricing_factor for item in second], list(PRICING_FACTORS[4:]))
        for item in second:
            learner.update(item.context, item.arm_index, .5)
        self.assertTrue((learner.update_counts >= 1).all())
        tied_a = DisjointLinUCB(alpha=1., random_seed=7)
        tied_b = DisjointLinUCB(alpha=1., random_seed=7)
        for tied in (tied_a, tied_b):
            tied.update_counts[:] = 1
        selections_a = [tied_a.select(self.context).arm_index for _ in range(12)]
        selections_b = [tied_b.select(self.context).arm_index for _ in range(12)]
        self.assertEqual(selections_a, selections_b)
        self.assertTrue(set(selections_a) <= set(range(7)))
        self.assertTrue(any(index != 0 for index in selections_a))

    def test_revenue_per_opportunity_normalization_preserves_rejections(self) -> None:
        example_a = revenue_opportunity_reward(90., 10, 20.)
        example_b = revenue_opportunity_reward(75., 10, 20.)
        self.assertEqual((example_a.raw_revenue_per_opportunity, example_a.normalized_reward), (9., .45))
        self.assertEqual((example_b.raw_revenue_per_opportunity, example_b.normalized_reward), (7.5, .375))
        self.assertGreater(example_a.normalized_reward, example_b.normalized_reward)
        self.assertEqual(FARE_REF_P99, 73.)
        self.assertEqual(revenue_opportunity_reward(1000., 1, 20.).normalized_reward, 1.)
        with self.assertRaises(ValueError):
            revenue_opportunity_reward(0., 0, 20.)

    def test_eq31_exact_monotonic_bounded_and_zero_demand_guard(self) -> None:
        factor, supply, demand = 1.0, 10., 20.
        expected = 1. / (1. + math.exp(.67 * factor * supply / demand - 1.67))
        self.assertAlmostEqual(customer_acceptance_probability(factor, supply, demand), expected)
        low = customer_acceptance_probability(.85, supply, demand)
        high = customer_acceptance_probability(1.15, supply, demand)
        self.assertGreater(low, high)
        self.assertTrue(0 <= low <= 1 and np.isfinite(low))
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            customer_acceptance_probability(1., supply, 0.)

    def test_acceptance_draw_is_seeded_boolean_and_auditable(self) -> None:
        first, second = np.random.default_rng(42), np.random.default_rng(42)
        draws_a = [draw_customer_acceptance(1., 10., 20., first) for _ in range(5)]
        draws_b = [draw_customer_acceptance(1., 10., 20., second) for _ in range(5)]
        self.assertEqual(draws_a, draws_b)
        self.assertTrue(all(isinstance(item.accepted, bool) and 0 <= item.probability <= 1 for item in draws_a))

    def test_offered_fare_formula_and_validation(self) -> None:
        self.assertAlmostEqual(offered_fare(100., 1.10), 110.)
        self.assertEqual(offered_fare(0., .85), 0.)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            offered_fare(-1., 1.)

    def test_reward_is_accumulated_accepted_offered_revenue_without_average(self) -> None:
        self.assertEqual(accepted_fare_revenue(20., True), 20.)
        self.assertEqual(accepted_fare_revenue(20., False), 0.)
        context = ContextRevenueAccumulator()
        context.add(210., True); context.add(330., True); context.add(250., False)
        self.assertEqual((context.accepted_revenue, context.request_count, context.accepted_count), (540., 3, 2))
        self.assertEqual(slot_accepted_revenue([540., 60.]), 600.)

    def test_context_specific_slot_feedback_has_no_dispatch_dependency(self) -> None:
        learner = DisjointLinUCB(alpha=1.)
        decision = learner.select(self.context)
        factor = decision.pricing_factor
        revenue = ContextRevenueAccumulator()
        for base, accepted in ((100., True), (200., False), (50., True)):
            revenue.add(offered_fare(base, factor), accepted)
        before_nonselected = [matrix.copy() for matrix in learner.A]
        reward = revenue_opportunity_reward(revenue.accepted_revenue, revenue.request_count)
        learner.update(decision.context, decision.arm_index, reward.normalized_reward)
        self.assertEqual(revenue.accepted_revenue, 150. * factor)
        self.assertEqual(learner.update_counts[decision.arm_index], 1)
        for index in set(range(7)) - {decision.arm_index}:
            self.assertTrue(np.array_equal(learner.A[index], before_nonselected[index]))


if __name__ == "__main__":
    unittest.main()
