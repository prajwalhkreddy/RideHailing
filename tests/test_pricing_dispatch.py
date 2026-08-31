"""Deterministic tests for one-slot pricing/acceptance/dispatch integration."""

from __future__ import annotations

import unittest

import numpy as np

from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import DisjointLinUCB
from src.simulation.pricing_dispatch import PricingContextInput, run_pricing_dispatch_slot


class PricingDispatchIntegrationTests(unittest.TestCase):
    contexts = {
        0: PricingContextInput(2.0, (0.2, 0.4, 0.2, 0.1, 0.1), 0.8),
        1: PricingContextInput(2.0, (0.4, 0.2, 0.1, 0.2, 0.1), 0.6),
    }
    neighbours = {0: (1,), 1: (0,)}

    @staticmethod
    def fleet(*grids: int) -> Fleet:
        vehicles = [VehicleState(i, grid, VehicleStatus.IDLE, None, 0, "idle", 1.0) for i, grid in enumerate(grids)]
        return Fleet(vehicles, frozenset((0, 1)), 2)

    @staticmethod
    def request(request_id: int, time: int, origin: int, destination: int, fare: float) -> RequestState:
        return RequestState(request_id, time, origin, destination, base_fare=fare)

    def run_slot(self, requests, fleet, seed=0, contexts=None, learner=None):
        return run_pricing_dispatch_slot(
            requests, self.contexts if contexts is None else contexts,
            learner or DisjointLinUCB(alpha=1.0), fleet, self.neighbours,
            default_trip_duration_minutes=2, mini_slots_per_main_slot=15,
            acceptance_rng=np.random.default_rng(seed),
        )

    def test_factor_selected_once_per_context_frozen_and_updated_only_at_end(self) -> None:
        learner = DisjointLinUCB(alpha=1.0)
        requests = [self.request(i, i % 15, 0, 1, 10.0 + i) for i in range(5)]
        result = self.run_slot(requests, self.fleet(0, 0), learner=learner)
        factor = result.pricing_by_context[0].decision.pricing_factor
        self.assertEqual(learner.selection_counts.sum(), 2)
        self.assertEqual(learner.update_counts.sum(), 1)
        self.assertEqual(result.linucb_updates_performed, 1)
        self.assertTrue(all(a.pricing_factor == factor for a in result.request_audit))
        self.assertEqual(result.pricing_by_context[0].generated, 5)
        self.assertEqual(result.pricing_by_context[1].generated, 0)
        self.assertEqual(result.pricing_by_context[1].accepted_revenue, 0.0)
        self.assertFalse(result.pricing_by_context[1].linucb_updated)

    def test_request_pricing_acceptance_is_seeded_and_drawn_exactly_once(self) -> None:
        first = [self.request(i, i, 0, 1, 10.0) for i in range(4)]
        second = [self.request(i, i, 0, 1, 10.0) for i in range(4)]
        result_a = self.run_slot(first, self.fleet(0), seed=12)
        result_b = self.run_slot(second, self.fleet(0), seed=12)
        self.assertEqual([a.customer_accepted for a in result_a.request_audit], [a.customer_accepted for a in result_b.request_audit])
        for request, audit in zip(first, result_a.request_audit):
            self.assertEqual(request.base_fare, 10.0)
            self.assertAlmostEqual(audit.offered_fare, audit.base_fare * audit.pricing_factor)
            self.assertEqual(request.acceptance_probability, audit.acceptance_probability)
        rng = np.random.default_rng(12)
        for _ in first:
            rng.random()
        expected_next = rng.random()
        actual_rng = np.random.default_rng(12)
        third = [self.request(i, i, 0, 1, 10.0) for i in range(4)]
        run_pricing_dispatch_slot(third, self.contexts, DisjointLinUCB(1.0), self.fleet(0), self.neighbours, 2, 15, actual_rng)
        self.assertEqual(actual_rng.random(), expected_next)

    def test_rejected_never_dispatches_or_changes_vehicle(self) -> None:
        request = self.request(0, 0, 0, 1, 25.0)
        fleet = self.fleet(0)
        result = self.run_slot([request], fleet, seed=4)
        self.assertEqual((result.accepted, result.rejected, result.served), (0, 1, 0))
        self.assertFalse(request.customer_accepted)
        self.assertEqual(request.status, RequestStatus.PENDING)
        vehicle = fleet.vehicle(0)
        self.assertEqual((vehicle.current_grid, vehicle.trip_status), (0, VehicleStatus.IDLE))
        self.assertEqual((result.accepted_revenue, result.served_revenue), (0.0, 0.0))

    def test_accepted_dispatch_failure_keeps_accepted_reward(self) -> None:
        request = self.request(0, 0, 0, 1, 100.0)
        result = self.run_slot([request], self.fleet(), seed=0)
        self.assertEqual((result.generated, result.accepted, result.rejected), (1, 1, 0))
        self.assertEqual((result.served, result.accepted_but_unserved), (0, 1))
        self.assertGreater(result.accepted_revenue, 0.0)
        self.assertEqual(result.served_revenue, 0.0)
        self.assertEqual(result.accepted_revenue, result.pricing_by_context[0].accepted_revenue)

    def test_accepted_and_served_uses_existing_vehicle_transition(self) -> None:
        request = self.request(0, 0, 0, 1, 20.0)
        fleet = self.fleet(0)
        result = self.run_slot([request], fleet, seed=0)
        self.assertEqual((result.served, result.accepted_but_unserved), (1, 0))
        self.assertEqual(request.status, RequestStatus.ASSIGNED)
        self.assertEqual(request.assigned_vehicle_id, 0)
        self.assertEqual(fleet.vehicle(0).current_grid, 1)
        self.assertEqual(result.served_revenue, result.accepted_revenue)

    def test_multiple_context_feedback_is_separate_and_counts_reconcile(self) -> None:
        learner = DisjointLinUCB(alpha=1.0)
        requests = [self.request(0, 0, 0, 1, 10.0), self.request(1, 1, 1, 0, 30.0)]
        before = [[matrix.copy() for matrix in learner.A], [vector.copy() for vector in learner.b]]
        result = self.run_slot(requests, self.fleet(0, 1), seed=0, learner=learner)
        self.assertEqual(result.generated, result.accepted + result.rejected)
        self.assertEqual(result.accepted, result.served + result.accepted_but_unserved)
        self.assertAlmostEqual(result.accepted_revenue, sum(c.accepted_revenue for c in result.pricing_by_context.values()))
        self.assertLessEqual(result.served_revenue, result.accepted_revenue)
        self.assertEqual(result.linucb_updates_performed, 2)
        selected = {context.decision.arm_index for context in result.pricing_by_context.values()}
        for arm_index in set(range(7)) - selected:
            np.testing.assert_array_equal(learner.A[arm_index], before[0][arm_index])
            np.testing.assert_array_equal(learner.b[arm_index], before[1][arm_index])

    def test_active_zero_request_context_gets_zero_update_but_no_context_gets_none(self) -> None:
        learner = DisjointLinUCB(alpha=1.0)
        result = self.run_slot([], self.fleet(), contexts={0: self.contexts[0]}, learner=learner)
        self.assertEqual((result.generated, result.accepted_revenue, result.linucb_updates_performed), (0, 0.0, 0))
        self.assertEqual(learner.update_counts.sum(), 0)
        self.assertEqual(learner.pending_cold_start.sum(), 0)
        empty_learner = DisjointLinUCB(alpha=1.0)
        empty = self.run_slot([], self.fleet(), contexts={}, learner=empty_learner)
        self.assertEqual((empty.generated, empty.linucb_updates_performed), (0, 0))
        self.assertEqual((empty_learner.selection_counts.sum(), empty_learner.update_counts.sum()), (0, 0))

    def test_reward_uses_all_generated_and_includes_accepted_but_unserved(self) -> None:
        requests = [self.request(i, i % 15, 0, 1, 10.) for i in range(10)]
        result = self.run_slot(requests, self.fleet(), seed=0, contexts={0: self.contexts[0]})
        context = result.pricing_by_context[0]
        expected_raw = context.accepted_revenue / 10
        self.assertEqual(context.generated, 10)
        self.assertEqual(context.accepted, result.accepted_but_unserved)
        self.assertAlmostEqual(context.raw_revenue_per_opportunity, expected_raw)
        self.assertAlmostEqual(context.normalized_reward, min(1., expected_raw / 73.))
        self.assertAlmostEqual(result.accepted_revenue, sum(a.offered_fare for a in result.request_audit if a.customer_accepted))


if __name__ == "__main__":
    unittest.main()
