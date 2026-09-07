"""Deterministic tests for one-slot pricing/acceptance/dispatch integration."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import DisjointLinUCB
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel
from src.pricing.customer_sensitivity import sample_positive_truncated_normal as actual_sensitivity_sample
from src.simulation.pricing_dispatch import (
    CUSTOMER_MODEL_HISTORICAL, PRICING_DECISION_MODE_REQUEST,
    REWARD_MODEL_SERVED, PricingContextInput, SUPPLY_MODEL_CORRECTED,
    run_pricing_dispatch_slot,
)
from src.pricing.supply import build_raw_pricing_supply as actual_raw_pricing_supply
from src.pricing.scaler import DEFAULT_PRICING_CONTEXT_SCALER


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

    @staticmethod
    def empirical_request(request_id: int, miles: float, fare: float = 999.) -> RequestState:
        pickup = datetime(2026, 1, 1, 0, 1)
        return RequestState(
            request_id, 0, 0, 1, base_fare=fare, source_trip_id=request_id,
            empirical_pickup_datetime=pickup,
            empirical_dropoff_datetime=pickup + timedelta(minutes=10),
            trip_duration_minutes=10., trip_distance_miles=miles,
            trip_distance_km=miles * 1.609344,
            empirical_within_slot_offset_seconds=60.,
        )

    @staticmethod
    def historical_model(seed: int = 20, sigma: float = 0.) -> HistoricalCustomerSensitivityModel:
        groups = pd.DataFrame({
            "WeatherCode": [1.], "Period": [0], "P_base": [20.], "D_base": [4.],
            "epsilon_mean": [1.], "epsilon_std_population": [sigma],
        })
        return HistoricalCustomerSensitivityModel(groups, np.random.default_rng(seed))

    def run_historical(
        self, requests, fleet, *, model=None, acceptance_seed=99,
        learner=None, reward_model="legacy_normalized_accepted_revenue",
    ):
        return run_pricing_dispatch_slot(
            requests, {0: self.contexts[0]}, learner or DisjointLinUCB(alpha=1.), fleet,
            self.neighbours, 2, 15, np.random.default_rng(acceptance_seed),
            customer_response_model=CUSTOMER_MODEL_HISTORICAL,
            historical_customer_model=model or self.historical_model(),
            weather_code=1., period=0,
            simulation_timestamp=datetime(2026, 1, 1),
            reward_model=reward_model,
        )

    def run_request_mode(self, requests, fleet, *, learner=None, model=None, reward_scaling="none"):
        grid = pd.DataFrame({"GridID": [0, 1], "Row": [0, 0], "Column": [0, 1]})
        popularity = pd.DataFrame({
            "TimeSlot": [datetime(2026, 1, 1)] * 2,
            "GridID": [0, 1], "popularity_value": [.25, .75],
        })
        return run_pricing_dispatch_slot(
            requests, {0: PricingContextInput(2., (.1, .2, .3, .15, .25), .8)},
            learner or DisjointLinUCB(1.), fleet,
            self.neighbours, 2, 15, np.random.default_rng(99),
            customer_response_model=CUSTOMER_MODEL_HISTORICAL,
            historical_customer_model=model or self.historical_model(),
            weather_code=1., period=0, simulation_timestamp=datetime(2026, 1, 1),
            reward_model=REWARD_MODEL_SERVED, supply_model=SUPPLY_MODEL_CORRECTED,
            pricing_decision_mode=PRICING_DECISION_MODE_REQUEST,
            grid_lookup=grid, popularity_table=popularity,
            linucb_reward_scaling=reward_scaling,
        )

    def test_request_mode_selects_each_request_then_updates_exactly_once_after_dispatch(self) -> None:
        served = self.empirical_request(0, 4.); served.destination_grid = 0
        unserved = self.empirical_request(1, 4.)
        rejected = self.empirical_request(2, 2.)
        learner = DisjointLinUCB(1.)
        original_select, original_update = learner.select, learner.update
        selected_count = 0

        def select(context):
            nonlocal selected_count
            selected_count += 1
            self.assertEqual(np.asarray(context).shape, (8,))
            return original_select(context)

        def update(context, arm, reward):
            self.assertEqual(selected_count, 3)
            self.assertNotEqual(served.status, RequestStatus.PENDING)
            self.assertEqual(unserved.status, RequestStatus.UNSERVED)
            self.assertEqual(rejected.status, RequestStatus.PENDING)
            return original_update(context, arm, reward)

        with patch.object(learner, "select", side_effect=select) as selections, patch.object(
            learner, "update", side_effect=update,
        ) as updates:
            result = self.run_request_mode([served, unserved, rejected], self.fleet(0), learner=learner)
        self.assertEqual((selections.call_count, updates.call_count), (3, 3))
        self.assertEqual((result.generated, result.accepted, result.rejected), (3, 2, 1))
        self.assertEqual((result.served, result.accepted_but_unserved), (1, 1))
        self.assertEqual((result.linucb_selections_performed, result.linucb_updates_performed), (3, 3))
        self.assertEqual([audit.selected_arm for audit in result.request_audit], [0, 1, 2])
        self.assertEqual([audit.pricing_factor for audit in result.request_audit], [.85, .90, .95])
        self.assertEqual([audit.linucb_reward for audit in result.request_audit], [17., 0., 0.])
        self.assertEqual(sum(audit.linucb_reward for audit in result.request_audit), result.served_revenue)
        for audit, call in zip(result.request_audit, updates.call_args_list):
            np.testing.assert_array_equal(call.args[0], audit.pricing_context)
            self.assertEqual((call.args[1], call.args[2]), (audit.selected_arm, audit.linucb_reward))
        self.assertEqual(learner.pending_cold_start.sum(), 0)

    def test_request_mode_same_origin_builds_independent_destination_distance_contexts(self) -> None:
        first = self.empirical_request(0, 4.); first.destination_grid = 0
        second = self.empirical_request(1, 8.); second.destination_grid = 1
        result = self.run_request_mode([first, second], self.fleet())
        one, two = result.request_audit
        self.assertEqual((one.origin_grid, two.origin_grid), (0, 0))
        self.assertFalse(np.array_equal(one.pricing_context, two.pricing_context))
        self.assertNotEqual(one.pricing_context[2], two.pricing_context[2])
        self.assertNotEqual(one.pricing_context[3], two.pricing_context[3])
        self.assertNotEqual(one.pricing_context[4], two.pricing_context[4])
        self.assertIsNot(one.pricing_context, two.pricing_context)

    def test_request_mode_cold_start_sequence_is_deterministic_and_customer_rng_is_separate(self) -> None:
        first = [self.empirical_request(i, 4.) for i in range(10)]
        second = [self.empirical_request(i, 4.) for i in range(10)]
        a, b = DisjointLinUCB(1., random_seed=8), DisjointLinUCB(1., random_seed=8)
        result_a = self.run_request_mode(first, self.fleet(), learner=a, model=self.historical_model(7, .5))
        result_b = self.run_request_mode(second, self.fleet(), learner=b, model=self.historical_model(7, .5))
        self.assertEqual([x.selected_arm for x in result_a.request_audit], [x.selected_arm for x in result_b.request_audit])
        self.assertEqual([x.epsilon_customer for x in result_a.request_audit], [x.epsilon_customer for x in result_b.request_audit])
        self.assertEqual(a.selection_counts.tolist(), b.selection_counts.tolist())

    def test_request_mode_rejects_incompatible_supply_and_reward(self) -> None:
        request = self.empirical_request(0, 4.)
        common = dict(
            requests=[request], context_inputs={0: self.contexts[0]}, learner=DisjointLinUCB(1.),
            fleet=self.fleet(), neighbour_lookup=self.neighbours, default_trip_duration_minutes=2,
            mini_slots_per_main_slot=15, acceptance_rng=np.random.default_rng(1),
            pricing_decision_mode=PRICING_DECISION_MODE_REQUEST,
        )
        with self.assertRaisesRegex(ValueError, "idle_plus_incoming"):
            run_pricing_dispatch_slot(**common)
        common["supply_model"] = SUPPLY_MODEL_CORRECTED
        common["simulation_timestamp"] = datetime(2026, 1, 1)
        with self.assertRaisesRegex(ValueError, "served_dispatch_revenue"):
            run_pricing_dispatch_slot(**common)

    def test_request_mode_resolves_fallback_once_for_context_price_and_pmax(self) -> None:
        fallback = pd.DataFrame({
            "fallback_level": ["period", "global"],
            "WeatherCode": [np.nan, np.nan], "Period": [0, pd.NA],
            "P_base": [40., 60.], "D_base": [8., 12.],
            "epsilon_mean": [2., 5.], "epsilon_std_population": [0., 0.],
            "sample_count": [10, 20],
        })
        model = HistoricalCustomerSensitivityModel(
            pd.DataFrame({
                "WeatherCode": [1.], "Period": [0], "P_base": [20.], "D_base": [4.],
                "epsilon_mean": [1.], "epsilon_std_population": [0.],
            }), np.random.default_rng(7), fallback, "hierarchical",
        )
        request = self.empirical_request(0, 8.)
        grid = pd.DataFrame({"GridID": [0, 1], "Row": [0, 0], "Column": [0, 1]})
        popularity = pd.DataFrame({
            "TimeSlot": [datetime(2026, 1, 1)] * 2, "GridID": [0, 1],
            "popularity_value": [.25, .75],
        })
        with patch.object(model, "resolve_parameters", wraps=model.resolve_parameters) as lookup:
            result = run_pricing_dispatch_slot(
                [request], {0: PricingContextInput(2., (.1, .2, .3, .15, .25), .8)},
                DisjointLinUCB(1.), self.fleet(0), self.neighbours, 2, 15, np.random.default_rng(99),
                customer_response_model=CUSTOMER_MODEL_HISTORICAL,
                historical_customer_model=model, weather_code=2., period=0,
                simulation_timestamp=datetime(2026, 1, 1), reward_model=REWARD_MODEL_SERVED,
                supply_model=SUPPLY_MODEL_CORRECTED,
                pricing_decision_mode=PRICING_DECISION_MODE_REQUEST,
                grid_lookup=grid, popularity_table=popularity, sensitivity_fallback="hierarchical",
            )
        audit = result.request_audit[0]
        lookup.assert_called_once_with(2., 0)
        self.assertEqual((audit.sensitivity_lookup_level, audit.historical_p_base, audit.historical_d_base), ("period", 40., 8.))
        self.assertAlmostEqual(audit.pricing_context[5], DEFAULT_PRICING_CONTEXT_SCALER.scale_base_price(40.))
        self.assertEqual((audit.offered_fare, audit.p_max), (34., 40.))

    def test_request_mode_training_reference_scales_only_learning_updates(self) -> None:
        from src.pricing.reward import REQUEST_REWARD_REF

        served = self.empirical_request(0, 4.); served.destination_grid = 0
        unserved = self.empirical_request(1, 4.)
        rejected = self.empirical_request(2, 2.)
        learner = DisjointLinUCB(1.)
        original_update = learner.update
        with patch.object(learner, "update", wraps=original_update) as updates:
            result = self.run_request_mode(
                [served, unserved, rejected], self.fleet(0), learner=learner,
                reward_scaling="training_reference",
            )
        audits = result.request_audit
        self.assertEqual([audit.raw_served_revenue for audit in audits], [17., 0., 0.])
        self.assertEqual([audit.linucb_learning_reward for audit in audits], [17. / REQUEST_REWARD_REF, 0., 0.])
        self.assertEqual([audit.linucb_reward for audit in audits], [17. / REQUEST_REWARD_REF, 0., 0.])
        self.assertEqual([call.args[2] for call in updates.call_args_list], [17. / REQUEST_REWARD_REF, 0., 0.])
        self.assertEqual(result.served_revenue, 17.)
        self.assertEqual(result.raw_request_served_revenue, 17.)
        self.assertEqual(result.linucb_learning_reward, 17. / REQUEST_REWARD_REF)
        self.assertEqual(result.request_reward_ref, REQUEST_REWARD_REF)
        self.assertEqual(result.linucb_updates_performed, 3)

    def test_request_mode_none_preserves_raw_learning_reward(self) -> None:
        request = self.empirical_request(0, 4.); request.destination_grid = 0
        result = self.run_request_mode([request], self.fleet(0), reward_scaling="none")
        audit = result.request_audit[0]
        self.assertEqual((audit.raw_served_revenue, audit.linucb_learning_reward, audit.linucb_reward), (17., 17., 17.))
        self.assertIsNone(result.request_reward_ref)

    def test_served_reward_counts_only_final_served_offers_and_updates_once(self) -> None:
        served = self.empirical_request(0, 4., fare=999.)
        accepted_unserved = self.empirical_request(1, 4., fare=999.)
        rejected = self.empirical_request(2, 2., fare=999.)
        requests = [served, accepted_unserved, rejected]
        learner = DisjointLinUCB(alpha=1.)
        original_update = learner.update

        def update_after_dispatch(context, arm_index, reward):
            self.assertEqual(served.status, RequestStatus.ASSIGNED)
            self.assertEqual(accepted_unserved.status, RequestStatus.UNSERVED)
            self.assertEqual(rejected.status, RequestStatus.PENDING)
            return original_update(context, arm_index, reward)

        with patch.object(learner, "update", side_effect=update_after_dispatch) as update:
            result = self.run_historical(
                requests, self.fleet(0), learner=learner,
                reward_model=REWARD_MODEL_SERVED,
            )
        context = result.pricing_by_context[0]
        self.assertEqual((context.generated, context.accepted, context.rejected), (3, 2, 1))
        self.assertEqual((context.served, context.accepted_but_unserved), (1, 1))
        self.assertEqual(context.accepted_revenue, 34.)
        self.assertEqual(context.served_revenue, 17.)
        self.assertEqual(context.linucb_reward, 17.)
        self.assertEqual(context.reward_model, REWARD_MODEL_SERVED)
        self.assertIsNone(context.normalized_reward)
        self.assertEqual(result.served_revenue, 17.)
        self.assertNotEqual(result.served_revenue, 999. * context.decision.pricing_factor)
        update.assert_called_once()
        self.assertEqual(update.call_args.args[2], 17.)
        self.assertEqual(learner.update_counts[context.decision.arm_index], 1)
        np.testing.assert_allclose(
            learner.b[context.decision.arm_index], context.decision.context * 17.,
        )

    def test_served_reward_sums_two_offers_once(self) -> None:
        result = self.run_historical(
            [self.empirical_request(0, 4.), self.empirical_request(1, 4.)],
            self.fleet(0, 0), reward_model=REWARD_MODEL_SERVED,
        )
        context = result.pricing_by_context[0]
        self.assertEqual((context.served, context.accepted_but_unserved, context.rejected), (2, 0, 0))
        self.assertEqual((context.served_revenue, context.linucb_reward), (34., 34.))
        self.assertEqual(result.served_revenue, sum(a.offered_fare for a in result.request_audit if a.served))

    def test_served_reward_updates_with_zero_when_nothing_is_served(self) -> None:
        learner = DisjointLinUCB(alpha=1.)
        result = self.run_historical(
            [self.empirical_request(0, 4.)], self.fleet(), learner=learner,
            reward_model=REWARD_MODEL_SERVED,
        )
        context = result.pricing_by_context[0]
        self.assertEqual((context.accepted, context.served, context.accepted_but_unserved), (1, 0, 1))
        self.assertEqual((context.served_revenue, context.linucb_reward), (0., 0.))
        self.assertEqual(learner.update_counts.sum(), 1)

    def test_historical_mode_uses_artifact_base_miles_and_complete_audit(self) -> None:
        request = self.empirical_request(0, 4., fare=999.)
        result = self.run_historical([request], self.fleet(0))
        audit = result.request_audit[0]
        self.assertEqual((audit.customer_model, audit.weather_code, audit.period), ("historical_sensitivity", 1., 0))
        self.assertEqual((audit.historical_p_base, audit.historical_d_base), (20., 4.))
        self.assertEqual(audit.actual_distance_miles, 4.)
        self.assertEqual(audit.epsilon_customer, 1.)
        self.assertEqual(audit.offered_fare, 20. * audit.pricing_factor)
        self.assertEqual(audit.p_max, 20.)
        self.assertNotEqual(audit.offered_fare, request.base_fare * audit.pricing_factor)

    def test_historical_rejection_is_never_passed_to_dispatch_and_equality_accepts(self) -> None:
        rejected = self.empirical_request(0, 2.)
        equal = self.empirical_request(1, 3.4)
        from src.dispatch.dispatch import dispatch_requests as actual_dispatch
        with patch("src.simulation.pricing_dispatch.dispatch_requests", wraps=actual_dispatch) as dispatch:
            result = self.run_historical([rejected, equal], self.fleet(0))
        dispatched_ids = [request.request_id for call in dispatch.call_args_list for request in call.args[0]]
        self.assertNotIn(rejected.request_id, dispatched_ids)
        self.assertIn(equal.request_id, dispatched_ids)
        self.assertFalse(rejected.customer_accepted)
        self.assertEqual(rejected.status, RequestStatus.PENDING)
        self.assertTrue(equal.customer_accepted)
        self.assertEqual(result.request_audit[1].offered_fare, result.request_audit[1].p_max)

    def test_historical_samples_once_per_request_and_does_not_consume_eq31_rng(self) -> None:
        requests = [self.empirical_request(index, 3.7) for index in range(8)]
        acceptance_rng = np.random.default_rng(123)
        expected_rng = np.random.default_rng(123)
        with patch(
            "src.pricing.customer_sensitivity.sample_positive_truncated_normal",
            wraps=actual_sensitivity_sample,
        ) as sensitivity_sample:
            result = run_pricing_dispatch_slot(
                requests, {0: self.contexts[0]}, DisjointLinUCB(1.), self.fleet(),
                self.neighbours, 2, 15, acceptance_rng,
                customer_response_model=CUSTOMER_MODEL_HISTORICAL,
                historical_customer_model=self.historical_model(seed=7, sigma=.5),
                weather_code=1., period=0, simulation_timestamp=datetime(2026, 1, 1),
            )
        self.assertEqual(sensitivity_sample.call_count, len(requests))
        self.assertEqual(len([audit.epsilon_customer for audit in result.request_audit]), len(requests))
        self.assertEqual(acceptance_rng.random(), expected_rng.random())

    def test_historical_same_seed_reproduces_runtime_acceptance_sequence(self) -> None:
        first = [self.empirical_request(index, 3.7) for index in range(20)]
        second = [self.empirical_request(index, 3.7) for index in range(20)]
        result_a = self.run_historical(first, self.fleet(), model=self.historical_model(55, .5))
        result_b = self.run_historical(second, self.fleet(), model=self.historical_model(55, .5))
        self.assertEqual(
            [(audit.epsilon_customer, audit.customer_accepted) for audit in result_a.request_audit],
            [(audit.epsilon_customer, audit.customer_accepted) for audit in result_b.request_audit],
        )

    def test_historical_missing_group_reports_slot_context(self) -> None:
        with self.assertRaisesRegex(KeyError, "WeatherCode=2.*Period=0.*2026-01-01T00:00:00"):
            run_pricing_dispatch_slot(
                [self.empirical_request(0, 4.)], {0: self.contexts[0]}, DisjointLinUCB(1.),
                self.fleet(), self.neighbours, 2, 15, np.random.default_rng(1),
                customer_response_model=CUSTOMER_MODEL_HISTORICAL,
                historical_customer_model=self.historical_model(), weather_code=2., period=0,
                simulation_timestamp=datetime(2026, 1, 1),
            )

    def test_historical_artifact_is_loaded_once_not_per_request(self) -> None:
        groups = pd.DataFrame({
            "WeatherCode": [1.], "Period": [0], "P_base": [20.], "D_base": [4.],
            "epsilon_mean": [1.], "epsilon_std_population": [0.],
        })
        with patch("src.pricing.customer_sensitivity.pd.read_parquet", return_value=groups) as read:
            model = HistoricalCustomerSensitivityModel.from_parquet("frozen.parquet", np.random.default_rng(1))
            self.run_historical([self.empirical_request(0, 4.), self.empirical_request(1, 4.)], self.fleet(), model=model)
        from pathlib import Path
        read.assert_called_once_with(Path("frozen.parquet"))

    def test_corrected_supply_reuses_idle_incoming_and_changes_only_context_position(self) -> None:
        vehicles = [
            VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 50.),
            VehicleState(1, 1, VehicleStatus.BUSY, 0, 10., "transporting", 50.),
            VehicleState(2, 0, VehicleStatus.BUSY, 0, 31., "transporting", 50.),
            VehicleState(3, 0, VehicleStatus.CHARGING, None, 0, "charging", 10.),
        ]
        legacy_fleet = Fleet([VehicleState(**vars(vehicle)) for vehicle in vehicles], frozenset((0, 1)), 2)
        corrected_fleet = Fleet([VehicleState(**vars(vehicle)) for vehicle in vehicles], frozenset((0, 1)), 2)
        legacy = run_pricing_dispatch_slot(
            [], {0: self.contexts[0]}, DisjointLinUCB(1.), legacy_fleet,
            self.neighbours, 2, 15, np.random.default_rng(1),
        )
        with patch(
            "src.simulation.pricing_dispatch.build_raw_pricing_supply",
            wraps=actual_raw_pricing_supply,
        ) as supply_builder:
            corrected = run_pricing_dispatch_slot(
                [], {0: self.contexts[0]}, DisjointLinUCB(1.), corrected_fleet,
                self.neighbours, 2, 15, np.random.default_rng(1),
                supply_model=SUPPLY_MODEL_CORRECTED,
                simulation_timestamp=datetime(2026, 1, 1),
            )
        supply_builder.assert_called_once()
        before = legacy.pricing_by_context[0]
        after = corrected.pricing_by_context[0]
        self.assertEqual((before.raw_supply, after.raw_supply), (3., 2.))
        self.assertEqual((after.idle_supply, after.incoming_supply), (1, 1))
        self.assertAlmostEqual(after.scaled_supply, np.log1p(2.) / np.log1p(9.))
        self.assertAlmostEqual(before.scaled_supply, np.log1p(3.) / np.log1p(9.))
        np.testing.assert_array_equal(before.decision.context[[0, 2, 3, 4, 5, 6, 7]], after.decision.context[[0, 2, 3, 4, 5, 6, 7]])
        self.assertEqual(before.decision.context.shape, after.decision.context.shape)

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
