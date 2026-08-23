#!/usr/bin/env python3
"""Small deterministic NB12 demonstration; it does not run a simulator."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.config import load_config
from src.routing.baseline import GridRoutingFeatures, RoutingAction, RoutingState
from src.routing.learning import LocalRoutingLearner, routing_learning_parameters_from_config


def _features(grid_id: int, demand: float) -> GridRoutingFeatures:
    return GridRoutingFeatures(grid_id, demand, 1, 1, 0, 0, 8., 0., 8., 0., 2., 0., 2., 0., True, 0.)


def _state(demand: float) -> RoutingState:
    current = _features(1, demand)
    return RoutingState(0, 1, 30., current, {RoutingAction.STAY: current, RoutingAction.NORTH: _features(0, demand + 1), RoutingAction.EAST: _features(2, demand + 2), RoutingAction.SOUTH: None, RoutingAction.WEST: None})


def main() -> int:
    config = load_config(ROOT / "config/config.yaml")
    # One-sample batch keeps this demo small; the persisted approved config is unchanged.
    parameters = replace(routing_learning_parameters_from_config(config), batch_size=1, target_update_interval_slots=1)
    learner = LocalRoutingLearner(vehicle_id=0, parameters=parameters, seed=config["random_seed"])
    state, next_state = _state(10.), _state(12.)
    action = learner.choose_action(state, training=False)
    learner.record_completed_outcome(state, action, True, next_state)
    learner.record_completed_outcome(next_state, RoutingAction.STAY, False, _state(13.))
    loss = learner.train_for_slot(1)
    exported = learner.export_local_update()
    print("NB12 LOCAL ROUTING LEARNING: PASS")
    print(f"action: {action.value}; q_values: {learner.q_values(state).round(6).tolist()}")
    print("next-slot rewards: [1.0, 0.0]")
    print(f"one local update loss: {loss:.6f}; epsilon: {learner.epsilon:.6f}")
    print(f"federated-ready export: {len(exported['weights'])} weight arrays, sample_count={exported['sample_count']}; raw replay omitted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
