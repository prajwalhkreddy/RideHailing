"""Focused deterministic NB13 policy-network FedAvg contracts."""

from __future__ import annotations

import unittest

import numpy as np

from src.routing.baseline import ACTION_ORDER, GridRoutingFeatures, RoutingAction, RoutingState
from src.routing.federated import aggregate_policy_updates
from src.routing.learning import (
    POLICY_ARCHITECTURE_VERSION, STATE_DIMENSION, LocalRoutingLearner,
    RoutingLearningParameters,
)


def _payload(vehicle_id: int, sample_count: int, values: tuple[float, ...] = (1., 3.)) -> dict:
    shapes = ((87, 64), (64,), (64, 32), (32,), (32, 5), (5,))
    return {
        "vehicle_id": vehicle_id,
        "weights": [np.full(shape, values[index % len(values)], dtype=np.float32) for index, shape in enumerate(shapes)],
        "sample_count": sample_count,
        "state_dimension": STATE_DIMENSION,
        "action_order": [action.value for action in ACTION_ORDER],
        "architecture_version": POLICY_ARCHITECTURE_VERSION,
    }


def _features(grid_id: int, demand: float) -> GridRoutingFeatures:
    return GridRoutingFeatures(grid_id, demand, 1, 1, 0, 0, 10., 2., 10., 2., 6., 2., 6., 2., True, 0.)


def _state() -> RoutingState:
    current = _features(1, 10.)
    return RoutingState(0, 1, 40., current, {
        RoutingAction.STAY: current,
        RoutingAction.NORTH: _features(0, 11.),
        RoutingAction.EAST: _features(2, 12.),
        RoutingAction.SOUTH: None,
        RoutingAction.WEST: None,
    })


class RoutingFederatedTests(unittest.TestCase):
    def test_one_equal_unequal_and_three_client_fedavg(self) -> None:
        one = aggregate_policy_updates([_payload(1, 2, (4., 6.))], round_index=1)
        self.assertTrue(np.array_equal(one.weights[0], _payload(1, 2, (4., 6.))["weights"][0]))

        equal = aggregate_policy_updates([_payload(1, 2, (2., 4.)), _payload(2, 2, (6., 8.))], round_index=2)
        self.assertTrue(np.allclose(equal.weights[0], 4.))
        self.assertTrue(np.allclose(equal.weights[1], 6.))

        unequal = aggregate_policy_updates([_payload(1, 1, (2., 4.)), _payload(2, 3, (6., 8.))], round_index=3)
        self.assertTrue(np.allclose(unequal.weights[0], .25 * 2. + .75 * 6.))
        self.assertTrue(np.allclose(unequal.weights[1], .25 * 4. + .75 * 8.))

        three = aggregate_policy_updates([_payload(1, 1, (1., 2.)), _payload(2, 2, (4., 5.)), _payload(3, 3, (7., 8.))], round_index=4)
        self.assertTrue(np.allclose(three.weights[0], (1. * 1. + 2. * 4. + 3. * 7.) / 6.))
        self.assertEqual(three.metadata.total_sample_count, 6)

    def test_zero_sample_clients_are_skipped_and_all_zero_is_no_update(self) -> None:
        result = aggregate_policy_updates([_payload(1, 0, (100., 100.)), _payload(2, 2, (5., 7.))], round_index=5)
        self.assertTrue(np.allclose(result.weights[0], 5.))
        self.assertEqual((result.metadata.participating_updates, result.metadata.skipped_zero_sample_vehicle_ids), (1, (1,)))
        no_update = aggregate_policy_updates([_payload(1, 0), _payload(2, 0)], round_index=6)
        self.assertFalse(no_update.updated)
        self.assertIsNone(no_update.weights)
        self.assertEqual(no_update.metadata.total_sample_count, 0)

    def test_metadata_compatibility_failures_are_rejected(self) -> None:
        cases = []
        wrong_dimension = _payload(2, 1); wrong_dimension["state_dimension"] = 86; cases.append((wrong_dimension, "state dimension"))
        wrong_order = _payload(2, 1); wrong_order["action_order"] = list(reversed(wrong_order["action_order"])); cases.append((wrong_order, "action order"))
        wrong_version = _payload(2, 1); wrong_version["architecture_version"] = "other"; cases.append((wrong_version, "architecture version"))
        negative = _payload(2, 1); negative["sample_count"] = -1; cases.append((negative, "sample_count"))
        for payload, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                aggregate_policy_updates([_payload(1, 1), payload], round_index=1)

    def test_tensor_count_shape_and_finiteness_are_validated(self) -> None:
        missing = _payload(2, 1); missing["weights"] = missing["weights"][:-1]
        shape = _payload(2, 1); shape["weights"][0] = np.ones((3, 2), dtype=np.float32)
        nan = _payload(2, 1); nan["weights"][0][0, 0] = np.nan
        inf = _payload(2, 1); inf["weights"][1][0] = np.inf
        for payload, message in ((missing, "number"), (shape, "shapes"), (nan, "finite"), (inf, "finite")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                aggregate_policy_updates([_payload(1, 1), payload], round_index=1)

    def test_aggregation_is_copying_and_does_not_mutate_clients(self) -> None:
        first, second = _payload(1, 1), _payload(2, 3, (5., 7.))
        originals = [[tensor.copy() for tensor in item["weights"]] for item in (first, second)]
        result = aggregate_policy_updates([first, second], round_index=2)
        for item, before in zip((first, second), originals):
            for actual, expected in zip(item["weights"], before):
                self.assertTrue(np.array_equal(actual, expected))
        for global_tensor in result.weights:
            self.assertFalse(any(np.shares_memory(global_tensor, local) for item in (first, second) for local in item["weights"]))

    def test_raw_local_data_is_rejected_and_not_required(self) -> None:
        result = aggregate_policy_updates([_payload(1, 1)], round_index=1)
        self.assertTrue(result.updated)
        private = _payload(1, 1); private["states"] = [np.zeros(87)]
        with self.assertRaisesRegex(ValueError, "raw local data"):
            aggregate_policy_updates([private], round_index=1)

    def test_nb12_local_divergence_unequal_fedavg_and_global_reload(self) -> None:
        parameters = RoutingLearningParameters(learning_rate=.01, local_observation_capacity=8, batch_size=3, local_epochs=3)
        state = _state()
        learner_a = LocalRoutingLearner(1, parameters, seed=4)
        learner_b = LocalRoutingLearner(2, parameters, seed=5)
        learner_b.reset_from_global_weights(learner_a.policy_model.get_weights())
        self.assertTrue(np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state)))
        learner_a.record_observation(state, RoutingAction.EAST)
        for _ in range(3):
            learner_b.record_observation(state, RoutingAction.STAY)
        learner_a.train_for_slot(1); learner_b.train_for_slot(1)
        self.assertFalse(np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state)))
        update_a, update_b = learner_a.export_local_update(), learner_b.export_local_update()
        original_a = [weight.copy() for weight in update_a["weights"]]
        original_b = [weight.copy() for weight in update_b["weights"]]
        result = aggregate_policy_updates([update_a, update_b], round_index=1)
        self.assertEqual((update_a["sample_count"], update_b["sample_count"]), (1, 3))
        for global_weight, weight_a, weight_b in zip(result.weights, original_a, original_b):
            self.assertTrue(np.allclose(global_weight, .25 * weight_a + .75 * weight_b, rtol=1e-6, atol=1e-7))
        fresh_a = LocalRoutingLearner(3, parameters, seed=6)
        fresh_b = LocalRoutingLearner(4, parameters, seed=7)
        fresh_a.reset_from_global_weights(result.weights); fresh_b.reset_from_global_weights(result.weights)
        probabilities = fresh_a.policy_probabilities(state)
        self.assertTrue(np.allclose(probabilities, fresh_b.policy_probabilities(state)))
        self.assertTrue(np.isfinite(probabilities).all())
        self.assertTrue(np.array_equal(probabilities[3:], np.zeros(2, dtype=np.float32)))
        self.assertAlmostEqual(float(probabilities.sum()), 1.)
        self.assertTrue({"states", "actions", "rewards", "observations"}.isdisjoint(update_a))


if __name__ == "__main__":
    unittest.main()
