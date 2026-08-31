"""Project-baseline aggregation of vehicle policy probabilities for pricing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Sequence

import numpy as np

from src.routing.baseline import ACTION_ORDER


@dataclass(frozen=True)
class GridPolicyProbabilities:
    grid_id: int
    probabilities: np.ndarray
    source: str
    vehicle_vector_count: int


def _validated_probability_vector(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64)
    if vector.shape != (len(ACTION_ORDER),):
        raise ValueError(f"{name} must follow the five-action order STAY/NORTH/EAST/SOUTH/WEST.")
    if not np.isfinite(vector).all() or (vector < 0).any():
        raise ValueError(f"{name} must be finite and non-negative.")
    total = float(vector.sum())
    if not np.isclose(total, 1.0, rtol=1e-7, atol=1e-8):
        raise ValueError(f"{name} must sum approximately to one.")
    return (vector / total).copy()


def aggregate_grid_policy_probabilities(
    required_grid_ids: Collection[int],
    vehicle_probabilities_by_grid: Mapping[int, Sequence[Sequence[float] | np.ndarray]],
    *,
    previous_grid_probabilities: Mapping[int, Sequence[float] | np.ndarray] | None = None,
    initial_grid_policy_probabilities: Mapping[int, Sequence[float] | np.ndarray] | None = None,
) -> dict[int, GridPolicyProbabilities]:
    """Mean masked vehicle probabilities, or use the approved zero-vehicle fallback."""
    grid_ids = tuple(sorted(set(required_grid_ids)))
    if not grid_ids:
        raise ValueError("At least one pricing grid is required.")
    unexpected = set(vehicle_probabilities_by_grid) - set(grid_ids)
    if unexpected:
        raise ValueError(f"Vehicle probabilities reference unexpected grids: {sorted(unexpected)}")
    previous = previous_grid_probabilities or {}
    initial = initial_grid_policy_probabilities or {}
    results: dict[int, GridPolicyProbabilities] = {}
    for grid_id in grid_ids:
        vectors = [
            _validated_probability_vector(values, f"Vehicle probability vector for grid {grid_id}")
            for values in vehicle_probabilities_by_grid.get(grid_id, ())
        ]
        if vectors:
            mean = np.mean(np.stack(vectors), axis=0, dtype=np.float64)
            probabilities = _validated_probability_vector(mean, f"Mean probability vector for grid {grid_id}")
            source = "current_vehicle_mean"
        elif grid_id in previous:
            probabilities = _validated_probability_vector(previous[grid_id], f"Previous probability vector for grid {grid_id}")
            source = "carry_forward"
        elif grid_id in initial:
            probabilities = _validated_probability_vector(initial[grid_id], f"Initial probability vector for grid {grid_id}")
            source = "initialization"
        else:
            raise ValueError(
                f"Grid {grid_id} has zero eligible vehicle policy states and no previous or initial probability vector."
            )
        results[grid_id] = GridPolicyProbabilities(grid_id, probabilities, source, len(vectors))
    return results
