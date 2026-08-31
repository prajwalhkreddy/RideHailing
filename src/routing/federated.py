"""NB13 synchronous sample-weighted aggregation of NB12 policy networks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from src.routing.baseline import ACTION_ORDER
from src.routing.learning import POLICY_ARCHITECTURE_VERSION, STATE_DIMENSION


_REQUIRED_UPDATE_KEYS = {
    "vehicle_id", "weights", "sample_count", "state_dimension",
    "action_order", "architecture_version",
}
_FORBIDDEN_LOCAL_DATA_KEYS = {
    "observations", "states", "actions", "action_masks", "utility_vectors",
    "trajectories", "requests", "rewards", "replay",
}
_EXPECTED_WEIGHT_SHAPES = ((87, 64), (64,), (64, 32), (32,), (32, 5), (5,))


@dataclass(frozen=True)
class FederatedRoundMetadata:
    round_index: int
    submitted_updates: int
    participating_updates: int
    total_sample_count: int
    skipped_zero_sample_vehicle_ids: tuple[int, ...]
    client_sample_counts: tuple[tuple[int, int], ...]
    architecture_version: str | None
    state_dimension: int | None
    action_order: tuple[str, ...]


@dataclass(frozen=True)
class FederatedRoundResult:
    """One global-policy update; ``weights=None`` means no update occurred."""

    updated: bool
    weights: tuple[np.ndarray, ...] | None
    metadata: FederatedRoundMetadata


@dataclass(frozen=True)
class _ValidatedUpdate:
    vehicle_id: int
    weights: tuple[np.ndarray, ...]
    sample_count: int


def _validate_update(payload: Mapping[str, Any], reference_shapes: tuple[tuple[int, ...], ...] | None) -> _ValidatedUpdate:
    if not isinstance(payload, Mapping):
        raise ValueError("Each local update must be a mapping exported by corrected NB12.")
    missing = _REQUIRED_UPDATE_KEYS.difference(payload)
    if missing:
        raise ValueError(f"Local update is missing required fields: {sorted(missing)}.")
    private_fields = _FORBIDDEN_LOCAL_DATA_KEYS.intersection(payload)
    if private_fields:
        raise ValueError(f"Local update must not contain raw local data: {sorted(private_fields)}.")
    sample_count = payload["sample_count"]
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 0:
        raise ValueError("sample_count must be a non-negative integer.")
    if payload["state_dimension"] != STATE_DIMENSION:
        raise ValueError(f"Incompatible state dimension; expected {STATE_DIMENSION}.")
    expected_actions = [action.value for action in ACTION_ORDER]
    if payload["action_order"] != expected_actions:
        raise ValueError(f"Incompatible action order; expected {expected_actions}.")
    if payload["architecture_version"] != POLICY_ARCHITECTURE_VERSION:
        raise ValueError(f"Incompatible architecture version; expected {POLICY_ARCHITECTURE_VERSION}.")
    raw_weights = payload["weights"]
    if not isinstance(raw_weights, Sequence) or isinstance(raw_weights, (str, bytes)) or not raw_weights:
        raise ValueError("Local update weights must be a non-empty tensor sequence.")
    weights: list[np.ndarray] = []
    for tensor in raw_weights:
        array = np.asarray(tensor)
        if not np.issubdtype(array.dtype, np.floating) or not np.isfinite(array).all():
            raise ValueError("Local policy weights must be finite floating-point tensors.")
        weights.append(array.copy())
    if len(weights) != len(_EXPECTED_WEIGHT_SHAPES):
        raise ValueError(f"Local policy update has the wrong number of weight tensors; expected {len(_EXPECTED_WEIGHT_SHAPES)}.")
    shapes = tuple(array.shape for array in weights)
    if shapes != _EXPECTED_WEIGHT_SHAPES:
        raise ValueError(f"Local policy tensor shapes do not match the corrected NB12 architecture: {_EXPECTED_WEIGHT_SHAPES}.")
    if reference_shapes is not None:
        if len(shapes) != len(reference_shapes):
            raise ValueError("Local policy updates have different numbers of weight tensors.")
        if shapes != reference_shapes:
            raise ValueError("Corresponding local policy weight tensor shapes must match.")
    vehicle_id = payload["vehicle_id"]
    if isinstance(vehicle_id, bool) or not isinstance(vehicle_id, int):
        raise ValueError("vehicle_id must be an integer.")
    return _ValidatedUpdate(vehicle_id, tuple(weights), sample_count)


def aggregate_policy_updates(updates: Sequence[Mapping[str, Any]], *, round_index: int) -> FederatedRoundResult:
    """Validate supplied clients and perform sample-count-weighted FedAvg.

    Every submitted update is compatibility-validated, including zero-sample
    clients. Zero-sample updates are then excluded from the weighted average.
    """
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError("round_index must be a non-negative integer.")
    if not isinstance(updates, Sequence) or isinstance(updates, (str, bytes)):
        raise ValueError("updates must be an explicit sequence of local payloads.")

    validated: list[_ValidatedUpdate] = []
    reference_shapes: tuple[tuple[int, ...], ...] | None = None
    for payload in updates:
        item = _validate_update(payload, reference_shapes)
        if reference_shapes is None:
            reference_shapes = tuple(weight.shape for weight in item.weights)
        validated.append(item)

    positive = [item for item in validated if item.sample_count > 0]
    skipped = tuple(item.vehicle_id for item in validated if item.sample_count == 0)
    total_samples = sum(item.sample_count for item in positive)
    metadata = FederatedRoundMetadata(
        round_index=round_index,
        submitted_updates=len(validated),
        participating_updates=len(positive),
        total_sample_count=total_samples,
        skipped_zero_sample_vehicle_ids=skipped,
        client_sample_counts=tuple((item.vehicle_id, item.sample_count) for item in validated),
        architecture_version=POLICY_ARCHITECTURE_VERSION if validated else None,
        state_dimension=STATE_DIMENSION if validated else None,
        action_order=tuple(action.value for action in ACTION_ORDER) if validated else (),
    )
    if not positive:
        return FederatedRoundResult(False, None, metadata)

    reference_dtypes = tuple(weight.dtype for weight in positive[0].weights)
    aggregated: list[np.ndarray] = []
    for tensor_index in range(len(positive[0].weights)):
        accumulator = np.zeros(positive[0].weights[tensor_index].shape, dtype=np.float64)
        for item in positive:
            accumulator += item.weights[tensor_index].astype(np.float64, copy=False) * item.sample_count
        tensor = (accumulator / total_samples).astype(reference_dtypes[tensor_index], copy=False)
        if not np.isfinite(tensor).all():
            raise ValueError("Federated averaging produced non-finite global weights.")
        aggregated.append(tensor.copy())
    return FederatedRoundResult(True, tuple(aggregated), metadata)
