"""Ordinary ride-hailing customer acceptance and offered-fare mechanics."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from src.pricing.linucb import PRICING_FACTORS


@dataclass(frozen=True)
class AcceptanceDecision:
    accepted: bool
    probability: float


def _validated_factor(pricing_factor: float) -> float:
    factor = float(pricing_factor)
    if not math.isfinite(factor) or factor not in PRICING_FACTORS:
        raise ValueError("pricing_factor must be one of the seven approved arms.")
    return factor


def offered_fare(base_fare: float, pricing_factor: float) -> float:
    """Apply the selected project pricing factor to a provided base fare."""
    base, factor = float(base_fare), _validated_factor(pricing_factor)
    if not math.isfinite(base) or base < 0:
        raise ValueError("base_fare must be finite and non-negative.")
    return float(base * factor)


def customer_acceptance_probability(pricing_factor: float, supply: float, potential_demand: float) -> float:
    """Ordinary ride-hailing Eq. (31), mapping project factor to paper lambda^1."""
    factor = _validated_factor(pricing_factor)
    supply_value, demand_value = float(supply), float(potential_demand)
    if not math.isfinite(supply_value) or supply_value < 0:
        raise ValueError("supply must be finite and non-negative.")
    if not math.isfinite(demand_value) or demand_value <= 0:
        raise ValueError("potential_demand must be finite and strictly positive.")
    exponent = 0.67 * factor * supply_value / demand_value - 1.67
    if exponent >= 0:
        exp_negative = math.exp(-exponent)
        probability = exp_negative / (1.0 + exp_negative)
    else:
        probability = 1.0 / (1.0 + math.exp(exponent))
    if not math.isfinite(probability):
        raise ValueError("Customer acceptance probability must be finite.")
    return float(min(1.0, max(0.0, probability)))


def draw_customer_acceptance(pricing_factor: float, supply: float, potential_demand: float, rng: np.random.Generator) -> AcceptanceDecision:
    """Draw before dispatch using only the explicitly supplied RNG."""
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be an explicit numpy.random.Generator.")
    probability = customer_acceptance_probability(pricing_factor, supply, potential_demand)
    return AcceptanceDecision(bool(rng.random() < probability), probability)
