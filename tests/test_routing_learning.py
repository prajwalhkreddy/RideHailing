"""Focused NB12 local routing-learning contracts with synthetic NB11 states."""

from __future__ import annotations

from dataclasses import replace
import unittest

import numpy as np

from src.routing.baseline import ACTION_ORDER, GridRoutingFeatures, RoutingAction, RoutingState
from src.routing.learning import (
    STATE_DIMENSION,
    STATE_FEATURE_ORDER,
    LocalReplayBuffer,
    LocalRoutingExperience,
    LocalRoutingLearner,
    RoutingLearningParameters,
    action_mask_array,
    encode_routing_state,
)


def _features(grid_id: int, value: float) -> GridRoutingFeatures:
    return GridRoutingFeatures(grid_id, value, 2, 1, 1, 0, value + .1, .2, value + .3, .4, value + .5, .6, value + .7, .8, True, .9)


def _state(*, east: bool = True, demand: float = 10.0) -> RoutingState:
    current = _features(10, demand)
    return RoutingState(
        vehicle_id=8,
        current_grid=10,
        energy_level=40.0,
        current_features=current,
        action_features={
            RoutingAction.STAY: current,
            RoutingAction.NORTH: _features(9, 20.0),
            RoutingAction.EAST: _features(11, 30.0) if east else None,
            RoutingAction.SOUTH: None,
            RoutingAction.WEST: None,
        },
    )


class RoutingLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = RoutingLearningParameters(replay_capacity=8, batch_size=1, target_update_interval_slots=1)
        self.state = _state()
        self.next_state = _state(demand=12.0)

    def test_fixed_vector_order_mask_and_invalid_candidate_encoding(self) -> None:
        vector = encode_routing_state(_state(east=False))
        self.assertEqual(STATE_DIMENSION, 87)
        self.assertEqual(vector.dtype, np.float32)
        self.assertEqual(vector.shape, (87,))
        self.assertTrue(np.isfinite(vector).all())
        self.assertEqual(STATE_FEATURE_ORDER[:2], ("vehicle.current_grid", "vehicle.energy_level"))
        self.assertEqual(STATE_FEATURE_ORDER[2:5], ("STAY.valid", "STAY.grid_id", "STAY.predicted_demand"))
        east_start = 2 + 2 * 17
        self.assertTrue(np.array_equal(vector[east_start:east_start + 17], np.zeros(17, dtype=np.float32)))
        self.assertTrue(np.array_equal(action_mask_array(_state(east=False)), np.array([True, True, False, False, False])))

    def test_q_contract_masks_invalid_actions_and_seeded_exploration_is_deterministic(self) -> None:
        first = LocalRoutingLearner(8, self.parameters, seed=19)
        second = LocalRoutingLearner(8, self.parameters, seed=19)
        self.assertEqual(first.q_values(self.state).shape, (5,))
        # Give invalid SOUTH/WEST huge values: NB11 masking still prevents them.
        first.q_values = lambda _: np.asarray([0., 1., 2., 999., 998.], dtype=np.float32)  # type: ignore[method-assign]
        self.assertEqual(first.choose_action(self.state, training=False), RoutingAction.EAST)
        first.epsilon = second.epsilon = 1.0
        first_actions = [first.choose_action(self.state, training=True) for _ in range(10)]
        second_actions = [second.choose_action(self.state, training=True) for _ in range(10)]
        self.assertEqual(first_actions, second_actions)
        self.assertTrue(all(action in (RoutingAction.STAY, RoutingAction.NORTH, RoutingAction.EAST) for action in first_actions))

    def test_next_slot_binary_reward_replay_capacity_and_no_unfinished_experience(self) -> None:
        learner = LocalRoutingLearner(8, self.parameters, seed=3)
        self.assertFalse(learner.record_completed_outcome(self.state, RoutingAction.STAY, None, self.next_state))
        self.assertEqual(len(learner.replay), 0)
        self.assertTrue(learner.record_completed_outcome(self.state, RoutingAction.STAY, True, self.next_state))
        self.assertTrue(learner.record_completed_outcome(self.state, RoutingAction.NORTH, False, self.next_state))
        self.assertEqual([item.reward for item in learner.replay._items], [1.0, 0.0])
        with self.assertRaisesRegex(ValueError, "masked"):
            learner.record_completed_outcome(self.state, RoutingAction.SOUTH, True, self.next_state)
        buffer = LocalReplayBuffer(1)
        item = next(iter(learner.replay._items))
        buffer.add(item)
        buffer.add(item)
        self.assertEqual(len(buffer), 1)

    def test_once_per_slot_training_target_sync_and_federated_safe_export(self) -> None:
        learner = LocalRoutingLearner(8, self.parameters, seed=7)
        self.assertIsNone(learner.train_for_slot(0))
        self.assertTrue(learner.record_completed_outcome(self.state, RoutingAction.EAST, True, self.next_state))
        loss = learner.train_for_slot(1)
        self.assertIsInstance(loss, float)
        self.assertEqual((learner.gradient_updates, learner.local_sample_count), (1, 1))
        self.assertLess(learner.epsilon, self.parameters.epsilon_start)
        for online, target in zip(learner.online_model.get_weights(), learner.target_model.get_weights()):
            self.assertTrue(np.array_equal(online, target))
        with self.assertRaisesRegex(ValueError, "at most once"):
            learner.train_for_slot(1)
        exported = learner.export_local_update()
        self.assertEqual((exported["vehicle_id"], exported["sample_count"], exported["state_dimension"]), (8, 1, 87))
        self.assertEqual(exported["action_order"], [action.value for action in ACTION_ORDER])
        self.assertNotIn("replay", exported)
        receiver = LocalRoutingLearner(9, self.parameters, seed=11)
        receiver.reset_from_global_weights(exported["weights"])
        for expected, actual in zip(exported["weights"], receiver.online_model.get_weights()):
            self.assertTrue(np.array_equal(expected, actual))

    def test_invalid_contracts_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "batch_size"):
            RoutingLearningParameters(replay_capacity=1, batch_size=2).validate()
        invalid = LocalRoutingExperience(np.zeros(2, dtype=np.float32), 0, 1.0, np.zeros(STATE_DIMENSION, dtype=np.float32), np.ones(5, dtype=bool))
        with self.assertRaisesRegex(ValueError, "vector dimension"):
            LocalReplayBuffer(1).add(invalid)
        bad_state = replace(self.state, energy_level=float("nan"))
        with self.assertRaisesRegex(ValueError, "finite"):
            encode_routing_state(bad_state)


if __name__ == "__main__":
    unittest.main()
