#!/usr/bin/env python3
"""Run a tiny deterministic one-slot pricing/acceptance/dispatch demo."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import DisjointLinUCB
from src.simulation.pricing_dispatch import PricingContextInput, run_pricing_dispatch_slot


def main() -> int:
    contexts = {
        0: PricingContextInput(3.0, (0.20, 0.40, 0.20, 0.10, 0.10), 0.80),
        1: PricingContextInput(2.0, (0.40, 0.20, 0.10, 0.20, 0.10), 0.60),
    }
    requests = [
        RequestState(0, 0, 0, 1, base_fare=10.0),
        RequestState(1, 1, 1, 0, base_fare=20.0),
        RequestState(2, 8, 0, 1, base_fare=12.0),
        RequestState(3, 14, 1, 0, base_fare=16.0),
    ]
    fleet = Fleet(
        [VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 1.0)],
        frozenset((0, 1)),
        mini_slot_minutes=2,
    )
    learner = DisjointLinUCB(alpha=1.0)
    result = run_pricing_dispatch_slot(
        requests, contexts, learner, fleet, {0: (1,), 1: (0,)},
        default_trip_duration_minutes=2,
        mini_slots_per_main_slot=15,
        acceptance_rng=np.random.default_rng(4),
    )

    print("START OF SLOT")
    for context_id, context_result in result.pricing_by_context.items():
        print(f"Context {context_id}: vector={context_result.decision.context.tolist()} factor={context_result.decision.pricing_factor:.2f}")
    print("DURING SLOT")
    for audit in result.request_audit:
        outcome = "accepted" if audit.customer_accepted else "rejected"
        service = "served" if audit.served else ("unserved" if audit.customer_accepted else "not-dispatched")
        print(f"request {audit.request_id}: base={audit.base_fare:.2f} factor={audit.pricing_factor:.2f} offered={audit.offered_fare:.2f} P_accept={audit.acceptance_probability:.4f} {outcome} {service}")
    print("END OF SLOT")
    print(f"generated={result.generated} accepted={result.accepted} rejected={result.rejected} served={result.served} accepted-but-unserved={result.accepted_but_unserved}")
    print(f"accepted revenue={result.accepted_revenue:.2f} served revenue={result.served_revenue:.2f}")
    for context_id, context_result in result.pricing_by_context.items():
        print(f"Context {context_id}: factor={context_result.decision.pricing_factor:.2f} accepted revenue={context_result.accepted_revenue:.2f} LinUCB update={context_result.linucb_updated}")
    frozen = all(audit.pricing_factor == result.pricing_by_context[audit.context_id].decision.pricing_factor for audit in result.request_audit)
    print(f"factor stayed fixed for all 15 mini-slots: {frozen}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
