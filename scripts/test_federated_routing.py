#!/usr/bin/env python3
"""Tiny deterministic NB13 sample-weighted policy FedAvg demonstration."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.data.config import load_config
from src.routing.baseline import GridRoutingFeatures, RoutingAction, RoutingState
from src.routing.federated import aggregate_policy_updates
from src.routing.learning import LocalRoutingLearner, routing_learning_parameters_from_config


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
    parameters = replace(routing_learning_parameters_from_config(config), learning_rate=.01, batch_size=3, local_epochs=3)
    state = _state()
    learner_a = LocalRoutingLearner(1, parameters, seed=config["random_seed"])
    learner_b = LocalRoutingLearner(2, parameters, seed=config["random_seed"] + 1)
    learner_b.reset_from_global_weights(learner_a.policy_model.get_weights())
    initially_identical = np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state))

    learner_a.record_observation(state, RoutingAction.EAST)
    for _ in range(3):
        learner_b.record_observation(state, RoutingAction.STAY)
    learner_a.train_for_slot(1)
    learner_b.train_for_slot(1)
    locally_diverged = not np.allclose(learner_a.policy_probabilities(state), learner_b.policy_probabilities(state))
    update_a, update_b = learner_a.export_local_update(), learner_b.export_local_update()
    result = aggregate_policy_updates([update_a, update_b], round_index=1)
    weighted_check = all(
        np.allclose(global_weight, .25 * weight_a + .75 * weight_b, rtol=1e-6, atol=1e-7)
        for global_weight, weight_a, weight_b in zip(result.weights, update_a["weights"], update_b["weights"])
    )

    fresh = LocalRoutingLearner(3, parameters, seed=config["random_seed"] + 2)
    fresh.reset_from_global_weights(result.weights)
    probabilities = fresh.policy_probabilities(state)
    raw_absent = all({"observations", "states", "actions", "action_masks", "utility_vectors"}.isdisjoint(update) for update in (update_a, update_b))

    assert initially_identical and locally_diverged and weighted_check and raw_absent
    assert np.array_equal(probabilities[3:], np.zeros(2, dtype=np.float32)) and np.isclose(probabilities.sum(), 1.)
    print("NB13 FEDERATED ROUTING POLICY: PASS")
    print(f"initial local models identical: {initially_identical}")
    print(f"local models diverged after EAST/STAY training: {locally_diverged}")
    print(f"sample counts: A={update_a['sample_count']}, B={update_b['sample_count']}; FedAvg weights: A=0.25, B=0.75")
    print(f"weighted-average tensor check passed: {weighted_check}")
    print(f"global model load passed: {probabilities.shape == (5,)}; masked policy sum={probabilities.sum():.6f}")
    print(f"raw local observations exported: {not raw_absent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
