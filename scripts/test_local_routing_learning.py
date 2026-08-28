#!/usr/bin/env python3
"""Small deterministic corrected-NB12 supervised policy demonstration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.charging.energy import energy_parameters_from_config
from src.data.config import load_config
from src.routing.baseline import CandidateUtilityInput, GridRoutingFeatures, RoutingAction, RoutingState, select_action
from src.routing.learning import ACTION_ORDER, LocalRoutingLearner, encode_routing_state, routing_learning_parameters_from_config


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


def main() -> int:
    config = load_config(ROOT / "config/config.yaml")
    parameters = replace(routing_learning_parameters_from_config(config), learning_rate=.01, batch_size=1, local_epochs=10)
    state = _state()
    decision = select_action(state, {
        RoutingAction.STAY: CandidateUtilityInput(8., 8., .20),
        RoutingAction.NORTH: CandidateUtilityInput(10., 6., .10),
        RoutingAction.EAST: CandidateUtilityInput(12., 4., .05),
    }, energy_parameters_from_config(config))

    east = ACTION_ORDER.index(RoutingAction.EAST)
    learner_a = LocalRoutingLearner(0, parameters, seed=config["random_seed"])
    learner_b = LocalRoutingLearner(1, parameters, seed=config["random_seed"] + 1)
    common_weights = learner_a.policy_model.get_weights()
    learner_b.reset_from_global_weights(common_weights)
    logits = learner_a.policy_logits(state)
    before = learner_a.policy_probabilities(state)

    audit = np.array([value if value is not None else np.nan for value in decision.utility_vector.values()], dtype=np.float32)
    learner_a.record_observation(state, decision.chosen_action, utility_vector=audit, slot_id=1)
    learner_b.record_observation(state, RoutingAction.STAY, slot_id=1)
    loss_a, loss_b = learner_a.train_for_slot(1), learner_b.train_for_slot(1)
    after = learner_a.policy_probabilities(state)
    export = learner_a.export_local_update()

    assert decision.chosen_action is RoutingAction.EAST
    assert np.array_equal(before[3:], np.zeros(2, dtype=np.float32))
    assert np.isclose(before.sum(), 1.)
    assert after[east] > before[east]
    assert not np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state))
    assert {"observations", "states", "actions", "utility_vector"}.isdisjoint(export)

    print("NB12 LOCAL SUPERVISED ROUTING POLICY: PASS")
    print(f"encoded state: shape={encode_routing_state(state).shape}, dtype={encode_routing_state(state).dtype}")
    print(f"initial logits: {logits.round(6).tolist()}")
    print(f"initial masked probabilities: {before.round(6).tolist()} (sum={before.sum():.6f})")
    print(f"NB11 selected label: {decision.chosen_action.value}; P(EAST): {before[east]:.6f} -> {after[east]:.6f}; loss={loss_a:.6f}")
    print(f"different local labels diverged: {not np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state))}; learner_b_loss={loss_b:.6f}")
    print(f"export: {len(export['weights'])} weight arrays, sample_count={export['sample_count']}, raw observations absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
