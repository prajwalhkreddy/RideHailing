"""Explicit pricing/routing boundaries; never project routing probabilities."""
import numpy as np

V3 = "SOURCE_ALIGNED_SLOT_PRICING_V3"
LEGACY = "LEGACY_LINUCB_8D"
CURRENT_ROUTING = "CURRENT_ROUTING_9"
HISTORICAL_ROUTING = "HISTORICAL_ROUTING_5"
ORDERS = {V3: ("STAY", "N", "NE", "E", "SE", "S", "SW", "W", "NW"),
          LEGACY: ("STAY", "N", "E", "S", "W")}


def validate_probabilities(values, *, pricing_version, routing_action_version):
    if pricing_version not in ORDERS:
        raise ValueError("Unknown pricing_version")
    expected = CURRENT_ROUTING if pricing_version == V3 else HISTORICAL_ROUTING
    if routing_action_version != expected:
        raise ValueError("Pricing/routing version mismatch")
    a = np.asarray(values, dtype=float)
    if a.shape != (len(ORDERS[pricing_version]),):
        raise ValueError("Pricing/routing probability dimension mismatch")
    if not np.isfinite(a).all() or (a < 0).any() or not np.isclose(a.sum(), 1.):
        raise ValueError("Invalid routing probabilities")
    return a.copy()  # Validation only: no redistribution or normalization.


def validate_v3_runtime(runtime):
    from src.simulation.slot_pricing_v3 import SlotPricingV3
    from src.pricing.slot_v3 import validate_state
    if not isinstance(runtime, SlotPricingV3):
        raise ValueError("V3 requires its explicit persistent SlotPricingV3 runtime")
    for state in runtime.states.values():
        validate_state(state)
        validate_probabilities(state[4:13], pricing_version=V3,
                               routing_action_version=CURRENT_ROUTING)
    if runtime.engine.operational.timestamp != runtime.engine.timestamp:
        raise ValueError("Operational producer/runtime timestamp mismatch")


def require_v3_execution(pricing_version, runtime):
    if pricing_version == LEGACY:
        raise ValueError("LEGACY_INTERFACE_NOT_EXECUTABLE_WITH_CURRENT_ROUTING: "
                         "historical five-action pricing requires a historical policy source")
    if pricing_version != V3:
        raise ValueError("Unknown pricing_version")
    validate_v3_runtime(runtime)
