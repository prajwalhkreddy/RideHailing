#!/usr/bin/env python3
"""Persist one deterministic common NB12/NB13 seed state and metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.routing.baseline import ACTION_ORDER
from src.routing.learning import POLICY_ARCHITECTURE_VERSION, STATE_DIMENSION, LocalRoutingLearner, RoutingLearningParameters


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    seed = 42
    parameters = RoutingLearningParameters()
    learner = LocalRoutingLearner(-1, parameters, seed=seed)
    artifact = ROOT / "models/routing/nb12_nb13_common_initialization_seed42.npz"
    metadata_path = artifact.with_name(artifact.stem + "_metadata.json")
    np.savez(artifact, **{f"weight_{index}": weight for index, weight in enumerate(learner.policy_model.get_weights())})
    metadata = {
        "seed": seed, "architecture_version": POLICY_ARCHITECTURE_VERSION,
        "input_dimension": STATE_DIMENSION, "hidden_sizes": list(parameters.hidden_units),
        "action_order": [action.value for action in ACTION_ORDER],
        "initialization_procedure": "one TensorFlow/Keras seed-42 model copied exactly to every local and global policy",
        "model_parameter_sha256": sha256(artifact),
        "optimizer": "Adam", "learning_rate": parameters.learning_rate,
        "local_observation_capacity": parameters.local_observation_capacity,
        "batch_size": parameters.batch_size, "local_epochs": parameters.local_epochs,
        "fedavg_rule": "sample-count-weighted mean of new-observation participating clients",
        "participation_rule": "vehicle has at least one new valid NB11 observation in the completed slot",
        "aggregation_cadence": "end of every 30-minute main slot",
        "first_slot_probability_rule": "uniform over valid actions; invalid actions zero",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(artifact), "metadata": str(metadata_path), "metadata_sha256": sha256(metadata_path), **metadata}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
