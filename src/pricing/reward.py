"""Accepted-trip offered-revenue payoff for standalone pricing."""

from __future__ import annotations

import math
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_REWARD_METADATA_PATH = Path(__file__).resolve().parents[2] / "config/pricing_reward.json"
with DEFAULT_REWARD_METADATA_PATH.open(encoding="utf-8") as _handle:
    _REWARD_METADATA = json.load(_handle)
FARE_REF_P99 = float(_REWARD_METADATA["fare_ref_p99"])


@dataclass(frozen=True)
class OpportunityReward:
    raw_revenue_per_opportunity: float
    normalized_reward: float
    clipped: bool


def revenue_opportunity_reward(
    accepted_revenue: float,
    generated_requests: int,
    fare_ref_p99: float = FARE_REF_P99,
) -> OpportunityReward:
    """Normalize accepted revenue per generated pricing opportunity."""
    revenue, reference = float(accepted_revenue), float(fare_ref_p99)
    if not math.isfinite(revenue) or revenue < 0:
        raise ValueError("accepted_revenue must be finite and non-negative.")
    if isinstance(generated_requests, bool) or not isinstance(generated_requests, int) or generated_requests <= 0:
        raise ValueError("generated_requests must be a positive integer learning observation.")
    if not math.isfinite(reference) or reference <= 0:
        raise ValueError("fare_ref_p99 must be finite and positive.")
    raw = revenue / generated_requests
    unbounded = raw / reference
    normalized = min(1.0, max(0.0, unbounded))
    return OpportunityReward(raw, normalized, not math.isclose(normalized, unbounded))


def accepted_fare_revenue(offered_fare: float, accepted: bool) -> float:
    fare = float(offered_fare)
    if not math.isfinite(fare) or fare < 0:
        raise ValueError("offered_fare must be finite and non-negative.")
    if not isinstance(accepted, bool):
        raise ValueError("accepted must be boolean.")
    return fare if accepted else 0.0


class ContextRevenueAccumulator:
    """Accumulate accepted offered fares for one context/action during a slot."""

    def __init__(self) -> None:
        self.accepted_revenue = 0.0
        self.request_count = 0
        self.accepted_count = 0

    def add(self, offered_fare: float, accepted: bool) -> float:
        contribution = accepted_fare_revenue(offered_fare, accepted)
        self.accepted_revenue += contribution
        self.request_count += 1
        self.accepted_count += int(accepted)
        return contribution


def slot_accepted_revenue(context_revenues: Iterable[float]) -> float:
    values = [float(value) for value in context_revenues]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Context revenues must be finite and non-negative.")
    return float(sum(values))
