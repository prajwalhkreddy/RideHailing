"""Focused corrected-NB12 supervised local policy contracts."""

from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from src.charging.energy import EnergyParameters
from src.routing.baseline import (
    ACTION_ORDER, CandidateUtilityInput, GridRoutingFeatures, RoutingAction,
    RoutingState, select_action,
)
from src.routing.learning import (
    POLICY_ARCHITECTURE_VERSION, STATE_DIMENSION, STATE_FEATURE_ORDER,
    LocalObservationBuffer, LocalPolicyObservation, LocalRoutingLearner,
    RoutingLearningParameters, action_mask_array, build_routing_policy_model,
    encode_routing_state, masked_softmax,
)


def _features(grid_id: int, value: float) -> GridRoutingFeatures:
    return GridRoutingFeatures(grid_id, value, 2, 1, 1, 0, 10., 2., value + .3, .4, 6., 2., value + .7, .8, True, .9)


def _state(*, east: bool = True, demand: float = 10.0) -> RoutingState:
    current = _features(10, demand)
    return RoutingState(8, 10, 40., current, {
        RoutingAction.STAY: current,
        RoutingAction.NORTH: _features(9, 20.),
        RoutingAction.EAST: _features(11, 30.) if east else None,
        RoutingAction.SOUTH: None,
        RoutingAction.WEST: None,
    })


class RoutingLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = RoutingLearningParameters(learning_rate=.01, local_observation_capacity=8, batch_size=8, local_epochs=10)
        self.state = _state()

    def test_fixed_deterministic_float32_state_contract(self) -> None:
        first = encode_routing_state(_state(east=False))
        second = encode_routing_state(_state(east=False))
        self.assertEqual((STATE_DIMENSION, first.shape, first.dtype), (87, (87,), np.dtype("float32")))
        self.assertTrue(np.array_equal(first, second))
        self.assertTrue(np.isfinite(first).all())
        self.assertEqual(STATE_FEATURE_ORDER[:5], ("vehicle.current_grid", "vehicle.energy_level", "STAY.valid", "STAY.grid_id", "STAY.predicted_demand"))
        self.assertEqual(STATE_FEATURE_ORDER[-17], "WEST.valid")
        east_start = 2 + 2 * 17
        self.assertTrue(np.array_equal(first[east_start:east_start + 17], np.zeros(17, dtype=np.float32)))
        missing = replace(self.state, current_features=replace(self.state.current_features, charging_available=None))
        missing.action_features[RoutingAction.STAY] = missing.current_features
        self.assertEqual(encode_routing_state(missing)[2 + 15], -1.)

    def test_common_model_is_87_64_32_5_logits_only(self) -> None:
        first = build_routing_policy_model(self.parameters, seed=4)
        second = build_routing_policy_model(self.parameters, seed=5)
        self.assertEqual((first.input_shape, first.output_shape), ((None, 87), (None, 5)))
        self.assertEqual([layer.units for layer in first.layers[1:]], [64, 32, 5])
        self.assertEqual(first.layers[-1].name, "action_logits")
        self.assertEqual([weight.shape for weight in first.get_weights()], [weight.shape for weight in second.get_weights()])
        learner = LocalRoutingLearner(1, self.parameters, seed=1)
        self.assertFalse(hasattr(learner, "target_model"))
        self.assertFalse(hasattr(learner, "online_model"))

    def test_masked_policy_normalizes_valid_actions_only(self) -> None:
        probabilities = masked_softmax(np.array([0., 1., 2., 999., 998.]), np.array([True, True, True, False, False]))
        self.assertEqual(probabilities.shape, (5,))
        self.assertTrue(np.isfinite(probabilities).all())
        self.assertTrue((probabilities >= 0).all())
        self.assertEqual((probabilities[3], probabilities[4]), (0., 0.))
        self.assertAlmostEqual(float(probabilities.sum()), 1.)
        only_east = masked_softmax(np.arange(5.), np.array([False, False, True, False, False]))
        self.assertTrue(np.array_equal(only_east, np.array([0., 0., 1., 0., 0.], dtype=np.float32)))

    def test_nb11_selected_action_is_supervised_label_not_utility_target(self) -> None:
        energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        inputs = {
            RoutingAction.STAY: CandidateUtilityInput(8., 8., .2),
            RoutingAction.NORTH: CandidateUtilityInput(10., 6., .1),
            RoutingAction.EAST: CandidateUtilityInput(12., 4., .05),
        }
        decision = select_action(self.state, inputs, energy)
        self.assertEqual(decision.chosen_action, RoutingAction.EAST)
        learner = LocalRoutingLearner(8, self.parameters, seed=7)
        audit = np.array([value if value is not None else np.nan for value in decision.utility_vector.values()], dtype=np.float32)
        learner.record_observation(self.state, decision.chosen_action, action_mask=action_mask_array(self.state), utility_vector=audit, slot_id=3)
        item = learner.observations._items[0]
        self.assertEqual(item.chosen_action_index, ACTION_ORDER.index(RoutingAction.EAST))
        self.assertEqual(item.state.shape, (87,))
        self.assertFalse(hasattr(item, "reward"))
        self.assertFalse(hasattr(item, "next_state"))

    def test_supervised_training_increases_chosen_probability_and_zero_data_skips(self) -> None:
        learner = LocalRoutingLearner(8, self.parameters, seed=12)
        before_weights = [weight.copy() for weight in learner.policy_model.get_weights()]
        self.assertIsNone(learner.train_for_slot(0))
        self.assertTrue(all(np.array_equal(a, b) for a, b in zip(before_weights, learner.policy_model.get_weights())))
        before = float(learner.policy_probabilities(self.state)[ACTION_ORDER.index(RoutingAction.EAST)])
        learner.record_observation(self.state, RoutingAction.EAST)
        loss = learner.train_for_slot(1)
        after = float(learner.policy_probabilities(self.state)[ACTION_ORDER.index(RoutingAction.EAST)])
        self.assertIsInstance(loss, float)
        self.assertGreater(after, before)
        self.assertGreater(learner.gradient_updates, 0)
        with self.assertRaisesRegex(ValueError, "at most once"):
            learner.train_for_slot(1)

    def test_local_buffers_are_bounded_and_vehicle_isolated(self) -> None:
        parameters = replace(self.parameters, local_observation_capacity=2, batch_size=2)
        first, second = LocalRoutingLearner(1, parameters, seed=1), LocalRoutingLearner(2, parameters, seed=2)
        for action in (RoutingAction.STAY, RoutingAction.NORTH, RoutingAction.EAST):
            first.record_observation(self.state, action)
        self.assertEqual((len(first.observations), len(second.observations)), (2, 0))
        with self.assertRaisesRegex(ValueError, "valid"):
            second.record_observation(self.state, RoutingAction.SOUTH)

    def test_common_initialization_then_different_labels_diverge(self) -> None:
        first = LocalRoutingLearner(1, self.parameters, seed=3)
        second = LocalRoutingLearner(2, self.parameters, seed=9)
        common = first.policy_model.get_weights()
        second.reset_from_global_weights(common)
        self.assertTrue(np.allclose(first.policy_probabilities(self.state), second.policy_probabilities(self.state)))
        first.record_observation(self.state, RoutingAction.EAST)
        second.record_observation(self.state, RoutingAction.STAY)
        first.train_for_slot(1)
        second.train_for_slot(1)
        self.assertFalse(np.allclose(first.policy_probabilities(self.state), second.policy_probabilities(self.state)))
        self.assertEqual([w.shape for w in first.policy_model.get_weights()], [w.shape for w in second.policy_model.get_weights()])

    def test_federated_ready_export_excludes_raw_observations(self) -> None:
        learner = LocalRoutingLearner(8, self.parameters, seed=5)
        learner.record_observation(self.state, RoutingAction.EAST)
        learner.train_for_slot(2)
        exported = learner.export_local_update()
        self.assertEqual((exported["vehicle_id"], exported["sample_count"], exported["state_dimension"]), (8, 1, 87))
        self.assertEqual(exported["action_order"], [action.value for action in ACTION_ORDER])
        self.assertEqual(exported["architecture_version"], POLICY_ARCHITECTURE_VERSION)
        self.assertEqual([w.shape for w in exported["weights"]], [w.shape for w in learner.policy_model.get_weights()])
        self.assertTrue({"observations", "states", "actions", "utility_vector"}.isdisjoint(exported))

    def test_invalid_state_observation_and_parameter_contracts(self) -> None:
        with self.assertRaisesRegex(ValueError, "batch_size"):
            RoutingLearningParameters(local_observation_capacity=1, batch_size=2).validate()
        invalid = LocalPolicyObservation(np.zeros(2, dtype=np.float32), 0, np.ones(5, dtype=bool))
        with self.assertRaisesRegex(ValueError, "87-feature"):
            LocalObservationBuffer(1).add(invalid)
        with self.assertRaisesRegex(ValueError, "finite"):
            encode_routing_state(replace(self.state, energy_level=float("nan")))


if __name__ == "__main__":
    unittest.main()
