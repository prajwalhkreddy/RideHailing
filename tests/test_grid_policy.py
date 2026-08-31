"""Tests for the approved vehicle-to-grid policy aggregation baseline."""

from __future__ import annotations

import unittest

import numpy as np

from src.routing.baseline import ACTION_ORDER, RoutingAction
from src.simulation.grid_policy import aggregate_grid_policy_probabilities


class GridPolicyAggregationTests(unittest.TestCase):
    def test_one_vehicle_is_identical_copy_in_fixed_action_order(self) -> None:
        source = np.array([.1, .2, .3, .15, .25])
        result = aggregate_grid_policy_probabilities([7], {7: [source]})[7]
        np.testing.assert_allclose(result.probabilities, source)
        self.assertEqual(tuple(action.value for action in ACTION_ORDER), ("STAY", "NORTH", "EAST", "SOUTH", "WEST"))
        self.assertEqual((result.source, result.vehicle_vector_count), ("current_vehicle_mean", 1))
        self.assertFalse(np.shares_memory(source, result.probabilities))

    def test_two_and_several_vehicles_use_exact_unweighted_arithmetic_mean(self) -> None:
        two = [np.array([1., 0., 0., 0., 0.]), np.array([0., 0., 1., 0., 0.])]
        result = aggregate_grid_policy_probabilities([0], {0: two})[0]
        np.testing.assert_allclose(result.probabilities, [.5, 0., .5, 0., 0.])
        several = two + [np.array([0., 0., 0., 1., 0.])]
        result = aggregate_grid_policy_probabilities([0], {0: several})[0]
        np.testing.assert_allclose(result.probabilities, [1 / 3, 0., 1 / 3, 1 / 3, 0.])
        self.assertEqual(result.vehicle_vector_count, 3)

    def test_masked_zeros_are_preserved_per_vehicle_then_averaged(self) -> None:
        vectors = [np.array([.4, 0., .6, 0., 0.]), np.array([.2, .3, 0., .5, 0.])]
        result = aggregate_grid_policy_probabilities([0], {0: vectors})[0].probabilities
        np.testing.assert_allclose(result, [.3, .15, .3, .25, 0.])
        self.assertAlmostEqual(float(result.sum()), 1.0)
        self.assertEqual(result[ACTION_ORDER.index(RoutingAction.WEST)], 0.0)

    def test_invalid_shape_nonfinite_negative_and_sum_are_rejected(self) -> None:
        invalid = ([1., 0.], [np.nan, 0., 0., 0., 1.], [1., 0., 0., 0., -.1], [.1] * 5)
        for vector in invalid:
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                aggregate_grid_policy_probabilities([0], {0: [vector]})

    def test_zero_vehicle_carries_previous_before_initialization(self) -> None:
        previous = np.array([.2] * 5)
        initial = np.array([1., 0., 0., 0., 0.])
        result = aggregate_grid_policy_probabilities([0], {}, previous_grid_probabilities={0: previous}, initial_grid_policy_probabilities={0: initial})[0]
        np.testing.assert_allclose(result.probabilities, previous)
        self.assertEqual((result.source, result.vehicle_vector_count), ("carry_forward", 0))
        self.assertFalse(np.shares_memory(previous, result.probabilities))

    def test_zero_vehicle_uses_initialization_or_requires_explicit_fallback(self) -> None:
        initial = np.array([0., 1., 0., 0., 0.])
        result = aggregate_grid_policy_probabilities([0], {}, initial_grid_policy_probabilities={0: initial})[0]
        np.testing.assert_allclose(result.probabilities, initial)
        self.assertEqual(result.source, "initialization")
        with self.assertRaisesRegex(ValueError, "zero eligible"):
            aggregate_grid_policy_probabilities([0], {})

    def test_averages_probabilities_not_argmax_or_supply_weighted_votes(self) -> None:
        vectors = [np.array([.49, .51, 0., 0., 0.]), np.array([.49, 0., .51, 0., 0.])]
        result = aggregate_grid_policy_probabilities([0], {0: vectors})[0].probabilities
        np.testing.assert_allclose(result, [.49, .255, .255, 0., 0.])
        self.assertEqual(int(np.argmax(result)), ACTION_ORDER.index(RoutingAction.STAY))


if __name__ == "__main__":
    unittest.main()
