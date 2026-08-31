#!/usr/bin/env python3
"""Tiny standalone contextual LinUCB pricing demonstration."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.data.config import load_config
from src.pricing.customer import draw_customer_acceptance, offered_fare
from src.pricing.linucb import DisjointLinUCB
from src.pricing.reward import ContextRevenueAccumulator, revenue_opportunity_reward, slot_accepted_revenue
from src.pricing.state import PRICING_CONTEXT_FEATURE_ORDER, build_pricing_context


def main() -> int:
    config = load_config(ROOT / "config/config.yaml")
    pricing = config["pricing"]
    learner = DisjointLinUCB(alpha=pricing["linucb_alpha"])
    context = build_pricing_context(20., 10., [.20, .40, .25, .05, .10], .8)
    decision = learner.select(context)
    rng = np.random.default_rng(pricing["acceptance_seed"])
    revenue = ContextRevenueAccumulator()
    before_a = [matrix.copy() for matrix in learner.A]
    before_b = [vector.copy() for vector in learner.b]

    request_rows = []
    for base_fare in (100., 200., 150.):
        fare = offered_fare(base_fare, decision.pricing_factor)
        acceptance = draw_customer_acceptance(decision.pricing_factor, supply=10., potential_demand=20., rng=rng)
        revenue.add(fare, acceptance.accepted)
        request_rows.append((base_fare, fare, acceptance.probability, acceptance.accepted))

    reward = revenue_opportunity_reward(revenue.accepted_revenue, revenue.request_count)
    learner.update(decision.context, decision.arm_index, reward.normalized_reward)
    selected_changed = not np.array_equal(learner.A[decision.arm_index], before_a[decision.arm_index]) and not np.array_equal(learner.b[decision.arm_index], before_b[decision.arm_index])
    nonselected_unchanged = all(np.array_equal(learner.A[index], before_a[index]) and np.array_equal(learner.b[index], before_b[index]) for index in range(7) if index != decision.arm_index)
    slot_total = slot_accepted_revenue([revenue.accepted_revenue])

    assert selected_changed and nonselected_unchanged and slot_total == revenue.accepted_revenue
    print("STANDALONE CONTEXTUAL LINUCB PRICING: PASS")
    print(f"context order: {PRICING_CONTEXT_FEATURE_ORDER}")
    print(f"context: {context.tolist()}")
    print(f"LinUCB scores: {decision.scores.round(6).tolist()}")
    print(f"selected factor: {decision.pricing_factor:.2f}")
    for base, fare, probability, accepted in request_rows:
        print(f"base={base:.2f}; offered={fare:.2f}; p_accept={probability:.6f}; accepted={accepted}")
    print(f"context accepted revenue: {revenue.accepted_revenue:.2f}; slot total: {slot_total:.2f}")
    print(f"raw opportunity revenue: {reward.raw_revenue_per_opportunity:.6f}; normalized reward: {reward.normalized_reward:.6f}")
    print(f"selected A/b changed: {selected_changed}; nonselected arms unchanged: {nonselected_unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
