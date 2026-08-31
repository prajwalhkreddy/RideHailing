"""Standard disjoint-arm LinUCB for the approved pricing factors."""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from src.pricing.state import PRICING_CONTEXT_DIMENSION, validate_pricing_context


PRICING_FACTORS = (0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15)


@dataclass(frozen=True)
class PricingDecision:
    arm_index: int
    pricing_factor: float
    scores: np.ndarray
    context: np.ndarray
    cold_start: bool


class DisjointLinUCB:
    """One independent ridge-regression state per fixed pricing arm."""

    def __init__(self, alpha: float, context_dimension: int = PRICING_CONTEXT_DIMENSION, random_seed: int = 42) -> None:
        if not isinstance(context_dimension, int) or context_dimension != PRICING_CONTEXT_DIMENSION:
            raise ValueError(f"Pricing context dimension must be {PRICING_CONTEXT_DIMENSION}.")
        if not isinstance(alpha, (int, float)) or not np.isfinite(alpha) or alpha < 0:
            raise ValueError("LinUCB alpha must be finite and non-negative.")
        self.alpha = float(alpha)
        self.context_dimension = context_dimension
        self.arms = PRICING_FACTORS
        self.A = [np.eye(context_dimension, dtype=np.float64) for _ in self.arms]
        self.b = [np.zeros(context_dimension, dtype=np.float64) for _ in self.arms]
        self.selection_counts = np.zeros(len(self.arms), dtype=np.int64)
        self.update_counts = np.zeros(len(self.arms), dtype=np.int64)
        self.pending_cold_start = np.zeros(len(self.arms), dtype=np.int64)
        self.tie_rng = np.random.default_rng(random_seed)

    def scores(self, context) -> np.ndarray:
        x = validate_pricing_context(context)
        scores = np.empty(len(self.arms), dtype=np.float64)
        for index, (matrix, vector) in enumerate(zip(self.A, self.b)):
            theta = np.linalg.solve(matrix, vector)
            solved_context = np.linalg.solve(matrix, x)
            uncertainty = max(0.0, float(x @ solved_context))
            scores[index] = float(theta @ x + self.alpha * np.sqrt(uncertainty))
        if not np.isfinite(scores).all():
            raise ValueError("LinUCB produced non-finite arm scores.")
        return scores

    def select(self, context) -> PricingDecision:
        x = validate_pricing_context(context)
        scores = self.scores(x)
        unobserved = np.flatnonzero(self.update_counts == 0)
        eligible = np.flatnonzero((self.update_counts == 0) & (self.pending_cold_start == 0))
        cold_start = bool(len(unobserved))
        if cold_start:
            if len(eligible):
                arm_index = int(eligible[0])
            else:
                minimum_pending = self.pending_cold_start[unobserved].min()
                arm_index = int(unobserved[self.pending_cold_start[unobserved] == minimum_pending][0])
            self.pending_cold_start[arm_index] += 1
        else:
            maximum = float(scores.max())
            tied = np.flatnonzero(np.isclose(scores, maximum, rtol=1e-7, atol=1e-8))
            arm_index = int(self.tie_rng.choice(tied))
        self.selection_counts[arm_index] += 1
        return PricingDecision(arm_index, self.arms[arm_index], scores.copy(), x.copy(), cold_start)

    def discard_pending_observation(self, arm_index: int) -> None:
        """Release a cold-start assignment when no request produced a reward observation."""
        if isinstance(arm_index, bool) or not isinstance(arm_index, int) or not 0 <= arm_index < len(self.arms):
            raise ValueError("Selected pricing arm index is invalid.")
        if self.pending_cold_start[arm_index] > 0:
            self.pending_cold_start[arm_index] -= 1

    def update(self, context, arm_index: int, reward: float) -> None:
        x = validate_pricing_context(context)
        if isinstance(arm_index, bool) or not isinstance(arm_index, int) or not 0 <= arm_index < len(self.arms):
            raise ValueError("Selected pricing arm index is invalid.")
        payoff = float(reward)
        if not np.isfinite(payoff) or payoff < 0:
            raise ValueError("Accepted-revenue payoff must be finite and non-negative.")
        if self.pending_cold_start[arm_index] > 0:
            self.pending_cold_start[arm_index] -= 1
        self.A[arm_index] += np.outer(x, x)
        self.b[arm_index] += payoff * x
        self.update_counts[arm_index] += 1

    def export_state(self) -> dict[str, Any]:
        return {
            "arms": list(self.arms),
            "context_dimension": self.context_dimension,
            "alpha": self.alpha,
            "A": [matrix.copy() for matrix in self.A],
            "b": [vector.copy() for vector in self.b],
            "selection_counts": self.selection_counts.copy(),
            "update_counts": self.update_counts.copy(),
            "pending_cold_start": self.pending_cold_start.copy(),
            "tie_rng_state": deepcopy(self.tie_rng.bit_generator.state),
        }

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "DisjointLinUCB":
        if not isinstance(state, Mapping) or state.get("arms") != list(PRICING_FACTORS):
            raise ValueError("LinUCB state has incompatible pricing arms.")
        learner = cls(float(state["alpha"]), int(state["context_dimension"]))
        matrices, vectors = state.get("A"), state.get("b")
        if not isinstance(matrices, list) or not isinstance(vectors, list) or len(matrices) != len(PRICING_FACTORS) or len(vectors) != len(PRICING_FACTORS):
            raise ValueError("LinUCB state has an incompatible arm-state count.")
        for index in range(len(PRICING_FACTORS)):
            matrix, vector = np.asarray(matrices[index], dtype=np.float64), np.asarray(vectors[index], dtype=np.float64)
            if matrix.shape != (PRICING_CONTEXT_DIMENSION, PRICING_CONTEXT_DIMENSION) or vector.shape != (PRICING_CONTEXT_DIMENSION,) or not np.isfinite(matrix).all() or not np.isfinite(vector).all():
                raise ValueError("LinUCB state contains invalid matrices or vectors.")
            learner.A[index] = matrix.copy()
            learner.b[index] = vector.copy()
        for name in ("selection_counts", "update_counts"):
            counts = np.asarray(state.get(name))
            if counts.shape != (len(PRICING_FACTORS),) or not np.issubdtype(counts.dtype, np.integer) or (counts < 0).any():
                raise ValueError("LinUCB state contains invalid counts.")
            setattr(learner, name, counts.astype(np.int64, copy=True))
        pending = np.asarray(state.get("pending_cold_start"))
        if pending.shape != (len(PRICING_FACTORS),) or not np.issubdtype(pending.dtype, np.integer) or (pending < 0).any():
            raise ValueError("LinUCB state contains invalid pending cold-start counts.")
        learner.pending_cold_start = pending.astype(np.int64, copy=True)
        learner.tie_rng.bit_generator.state = state["tie_rng_state"]
        return learner
