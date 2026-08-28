"""Standalone contextual pricing and customer-acceptance components."""

from src.pricing.customer import AcceptanceDecision, customer_acceptance_probability, draw_customer_acceptance, offered_fare
from src.pricing.linucb import PRICING_FACTORS, DisjointLinUCB, PricingDecision
from src.pricing.reward import ContextRevenueAccumulator, accepted_fare_revenue, slot_accepted_revenue
from src.pricing.state import PRICING_CONTEXT_DIMENSION, PRICING_CONTEXT_FEATURE_ORDER, build_pricing_context

__all__ = [
    "AcceptanceDecision", "customer_acceptance_probability", "draw_customer_acceptance", "offered_fare",
    "PRICING_FACTORS", "DisjointLinUCB", "PricingDecision", "ContextRevenueAccumulator",
    "accepted_fare_revenue", "slot_accepted_revenue", "PRICING_CONTEXT_DIMENSION",
    "PRICING_CONTEXT_FEATURE_ORDER", "build_pricing_context",
]
