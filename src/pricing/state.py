"""Validated eight-feature context for standalone contextual pricing."""

from __future__ import annotations

import numpy as np

from src.pricing.scaler import DEFAULT_PRICING_CONTEXT_SCALER, PricingContextScaler


ROUTING_PROBABILITY_ORDER = ("STAY", "NORTH", "EAST", "SOUTH", "WEST")
PRICING_CONTEXT_FEATURE_ORDER = (
    "scaled_predicted_demand", "scaled_current_supply", "P(STAY)", "P(NORTH)",
    "P(EAST)", "P(SOUTH)", "P(WEST)", "popularity",
)
PRICING_CONTEXT_DIMENSION = len(PRICING_CONTEXT_FEATURE_ORDER)


def build_pricing_context(
    predicted_demand: float,
    current_supply: float,
    routing_probabilities,
    popularity: float,
    scaler: PricingContextScaler = DEFAULT_PRICING_CONTEXT_SCALER,
) -> np.ndarray:
    """Return the bounded float64 context in the approved feature order."""
    demand, supply, popularity_value = float(predicted_demand), float(current_supply), float(popularity)
    probabilities = np.asarray(routing_probabilities, dtype=np.float64)
    if not np.isfinite([demand, supply, popularity_value]).all():
        raise ValueError("Demand, supply, and popularity must be finite.")
    if supply < 0:
        raise ValueError("Current supply must be non-negative.")
    if probabilities.shape != (5,) or not np.isfinite(probabilities).all() or (probabilities < 0).any():
        raise ValueError("Routing probabilities must be five finite non-negative values.")
    if not np.isclose(probabilities.sum(), 1.0, rtol=1e-7, atol=1e-8):
        raise ValueError("Routing probabilities must sum to one.")
    if not 0. <= popularity_value <= 1.:
        raise ValueError("Popularity must be within [0,1].")
    context = np.concatenate((
        [scaler.scale_demand(demand), scaler.scale_supply(supply)], probabilities, [popularity_value],
    )).astype(np.float64, copy=False)
    if context.shape != (PRICING_CONTEXT_DIMENSION,):
        raise ValueError("Pricing context must have exactly eight features.")
    return context


def validate_pricing_context(context) -> np.ndarray:
    """Validate either approved bounded 8D context without normalizing it."""
    values = np.asarray(context, dtype=np.float64)
    if values.shape != (PRICING_CONTEXT_DIMENSION,) or not np.isfinite(values).all():
        raise ValueError("Pricing context must be a finite eight-element vector.")
    if (values < 0).any() or (values > 1).any():
        raise ValueError("Pricing context features must be within [0,1].")
    return values.copy()
