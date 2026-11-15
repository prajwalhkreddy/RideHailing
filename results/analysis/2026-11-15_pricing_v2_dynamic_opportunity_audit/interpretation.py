def value_classification(state_difference, net, immediate, tolerance=1e-8):
    recovery = net - immediate
    if net > tolerance:
        return "NET_POSITIVE_DYNAMIC_VALUE"
    if recovery > tolerance:
        return "FULL_REVENUE_RECOVERY" if abs(net) <= tolerance else "PARTIAL_REVENUE_RECOVERY"
    return "STATE_DIFFERENCE_NO_RECOVERY" if state_difference else "NO_STATE_EFFECT"

def reconvergence_classification(horizons):
    """Ordered (horizon, state_difference) pairs; equality is observed, not interpolated."""
    by = dict(horizons)
    label = ("PERSISTS_MULTIPLE_SLOTS" if by.get("ONE_FULL_SLOT_AFTER_BOUNDARY", False)
             else "PERSISTS_ACROSS_ROUTING_BOUNDARY" if by.get("NEXT_SLOT_BOUNDARY", False)
             else "SHORT_LIVED_DIVERGENCE" if any(by.values()) else "NO_STATE_DIVERGENCE")
    seen = False
    first_equal = None
    for horizon, changed in horizons:
        if seen and not changed:
            first_equal = horizon
            break
        seen = seen or changed
    return label, first_equal
