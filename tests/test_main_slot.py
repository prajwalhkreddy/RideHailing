"""Controlled tests for one complete main-slot orchestration."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingInfrastructure, ChargingStation
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import DisjointLinUCB
from src.routing.baseline import ACTION_ORDER, CandidateUtilityInput, RoutingAction, RoutingParameters
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters
from src.simulation.main_slot import run_main_slot
from src.simulation.pricing_dispatch import PricingContextInput
from src.simulation.statistics import OperationalStatistics


class MainSlotOrchestrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        self.routing = RoutingParameters(15., 3., 30.)
        self.learning = RoutingLearningParameters(learning_rate=.001, local_observation_capacity=8, batch_size=8, local_epochs=1)
        self.directional = pd.DataFrame({
            "GridID": [0, 1], "NeighbourGridID": [1, 0], "Direction": ["east", "west"],
        })
        self.contexts = {
            0: PricingContextInput(10., (.2, .2, .2, .2, .2), .8),
            1: PricingContextInput(10., (.2, .2, .2, .2, .2), .6),
        }

    def _learners(self, ids=(0, 1, 2)):
        learners = {vehicle_id: LocalRoutingLearner(vehicle_id, self.learning, seed=10 + vehicle_id) for vehicle_id in ids}
        common = learners[ids[0]].policy_model.get_weights()
        common[-1] = np.array([0., 0., 100., 0., 0.], dtype=np.float32)  # Global policy strongly prefers EAST when valid.
        for learner in learners.values():
            learner.reset_from_global_weights(common)
        global_policy = LocalRoutingLearner(99, self.learning, seed=99)
        global_policy.reset_from_global_weights(common)
        return learners, global_policy

    @staticmethod
    def _utility_inputs():
        preference = CandidateUtilityInput(10., 0., .1)
        return {
            1: {RoutingAction.STAY: preference, RoutingAction.EAST: preference},
            2: {RoutingAction.STAY: preference, RoutingAction.WEST: preference},
        }

    def _run(self):
        vehicles = [
            VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 6.),
            VehicleState(1, 0, VehicleStatus.IDLE, None, 0, "idle", 40.),
            VehicleState(2, 1, VehicleStatus.IDLE, None, 0, "idle", 40.),
        ]
        fleet = Fleet(vehicles, frozenset((0, 1)), 2)
        infrastructure = ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.), 1: (1., 0.)}, random_seed=3)
        requests = [RequestState(0, 0, 0, 0, base_fare=10.), RequestState(1, 0, 1, 1, base_fare=20.)]
        learners, global_policy = self._learners()
        pricing = DisjointLinUCB(1.)
        result = run_main_slot(
            slot_id=0, requests=requests, pricing_context_inputs=self.contexts,
            next_predicted_demand={0: 12., 1: 8.}, next_popularity={0: .8, 1: .6},
            learner=pricing, fleet=fleet, neighbour_lookup={0: (1,), 1: (0,)},
            directional_neighbour_map=self.directional,
            statistics_engine=OperationalStatistics([0, 1], .3),
            charging_infrastructure=infrastructure, energy_parameters=self.energy,
            routing_parameters=self.routing, utility_inputs_by_vehicle=self._utility_inputs(),
            local_learners=learners, global_policy_learner=global_policy,
            default_trip_duration_minutes=2, mini_slots_per_main_slot=15,
            acceptance_rng=np.random.default_rng(0), federate=True, federation_round_index=0,
            initial_grid_policy_probabilities={0: [.2] * 5, 1: [.2] * 5},
        )
        return result, requests, fleet, infrastructure, learners, global_policy, pricing

    def test_complete_order_pricing_nb9_nb11_nb12_nb13_and_next_state(self) -> None:
        result, requests, _, _, _, _, pricing = self._run()
        self.assertEqual(result.stage_order, (
            "pricing_acceptance_dispatch", "nb10_charging", "nb9_statistics", "nb11_routing",
            "nb12_training", "nb13_federation", "global_policy_probabilities", "next_pricing_inputs",
        ))
        self.assertEqual((result.pricing_dispatch.generated, result.pricing_dispatch.accepted, result.pricing_dispatch.rejected), (2, 2, 0))
        self.assertEqual((result.pricing_dispatch.served, result.pricing_dispatch.accepted_but_unserved), (2, 0))
        self.assertEqual(pricing.update_counts.sum(), 2)
        self.assertTrue(all(request.offered_fare is not None for request in requests))
        self.assertEqual(set(result.next_pricing_contexts), {0, 1})
        self.assertEqual(pricing.selection_counts.sum(), 2)  # No next-slot factor selected.

    def test_nb9_uses_served_offered_fares_and_nb10_advances_once_per_mini_slot(self) -> None:
        result, _, fleet, infrastructure, _, _, _ = self._run()
        stats = {row.grid_id: row for row in result.statistics}
        self.assertEqual((stats[0].fare_count, stats[0].mean_fare, stats[0].wait_count), (1, 8.5, 1))
        self.assertEqual((stats[1].fare_count, stats[1].mean_fare, stats[1].wait_count), (1, 18., 1))
        self.assertEqual(stats[0].ewma_fare, stats[0].mean_fare)
        self.assertAlmostEqual(fleet.vehicle(0).energy_level, 6. + 15 * .9)
        self.assertEqual(result.charging.presented_vehicle_count, 1)
        self.assertEqual(result.charging.active_vehicle_count, 1)
        self.assertIn(0, infrastructure.vehicle_station)

    def test_nb11_controls_actual_movement_and_charging_vehicle_is_excluded(self) -> None:
        result, _, fleet, _, _, global_policy, _ = self._run()
        self.assertEqual({audit.vehicle_id for audit in result.routing_audit}, {1, 2})
        self.assertNotIn(0, {audit.vehicle_id for audit in result.routing_audit})
        for audit in result.routing_audit:
            valid_utilities = {action: value for action, value in audit.decision.utility_vector.items() if value is not None}
            self.assertEqual(audit.decision.chosen_action, max(valid_utilities, key=lambda action: (valid_utilities[action], -ACTION_ORDER.index(action))))
            self.assertEqual(audit.transition.action, audit.decision.chosen_action)
            self.assertEqual(fleet.vehicle(audit.vehicle_id).current_grid, audit.transition.destination_grid)
        vehicle_one = next(audit for audit in result.routing_audit if audit.vehicle_id == 1)
        policy_argmax = ACTION_ORDER[int(np.argmax(global_policy.policy_probabilities(vehicle_one.state)))]
        self.assertEqual(policy_argmax, RoutingAction.EAST)
        self.assertEqual(vehicle_one.decision.chosen_action, RoutingAction.STAY)
        self.assertNotEqual(policy_argmax, vehicle_one.transition.action)

    def test_nb12_labels_are_nb11_actions_and_fedavg_exports_only_models(self) -> None:
        result, _, _, _, learners, _, _ = self._run()
        self.assertEqual((result.local_learning.observations_collected, result.local_learning.learners_trained), (2, 2))
        for audit in result.routing_audit:
            observation = learners[audit.vehicle_id].observations._items[-1]
            self.assertEqual(observation.chosen_action_index, ACTION_ORDER.index(audit.decision.chosen_action))
            self.assertFalse(hasattr(observation, "reward"))
            self.assertFalse(hasattr(observation, "next_state"))
            with self.assertRaisesRegex(ValueError, "at most once"):
                learners[audit.vehicle_id].train_for_slot(0)
        self.assertTrue(result.federated.updated)
        self.assertEqual((result.federated.metadata.submitted_updates, result.federated.metadata.participating_updates, result.federated.metadata.total_sample_count), (3, 2, 2))
        self.assertTrue(all({"weights", "sample_count", "vehicle_id", "state_dimension", "action_order", "architecture_version"} == set(local.export_local_update()) for local in learners.values()))

    def test_next_global_probabilities_are_masked_grid_means_with_audit_sources(self) -> None:
        result, _, _, _, _, _, _ = self._run()
        for grid_id, context in result.next_pricing_contexts.items():
            self.assertAlmostEqual(float(context.routing_probabilities.sum()), 1.)
            self.assertTrue((context.routing_probabilities >= 0).all())
            self.assertEqual((context.predicted_demand, context.popularity), ((12., .8) if grid_id == 0 else (8., .6)))
        self.assertEqual((result.next_pricing_contexts[0].probability_source, result.next_pricing_contexts[0].eligible_vehicle_vectors), ("current_vehicle_mean", 2))
        self.assertEqual((result.next_pricing_contexts[1].probability_source, result.next_pricing_contexts[1].eligible_vehicle_vectors), ("initialization", 0))
        self.assertEqual(result.next_pricing_contexts[0].routing_probabilities[ACTION_ORDER.index(RoutingAction.NORTH)], 0.)
        np.testing.assert_allclose(result.next_pricing_contexts[1].routing_probabilities, [.2] * 5)

    def test_all_zero_federation_is_no_update_and_initializes_empty_grid_policy(self) -> None:
        vehicle = VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 6.)
        fleet = Fleet([vehicle], frozenset((0,)), 2)
        infrastructure = ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.)})
        learners, global_policy = self._learners(ids=(0,))
        context = {0: PricingContextInput(1., [1., 0., 0., 0., 0.], .5)}
        result = run_main_slot(
            slot_id=0, requests=[], pricing_context_inputs=context,
            next_predicted_demand={0: 1.}, next_popularity={0: .5}, learner=DisjointLinUCB(1.),
            fleet=fleet, neighbour_lookup={0: ()}, directional_neighbour_map=pd.DataFrame(columns=["GridID", "NeighbourGridID", "Direction"]),
            statistics_engine=OperationalStatistics([0], .3), charging_infrastructure=infrastructure,
            energy_parameters=self.energy, routing_parameters=self.routing, utility_inputs_by_vehicle={},
            local_learners=learners, global_policy_learner=global_policy, default_trip_duration_minutes=2,
            mini_slots_per_main_slot=15, acceptance_rng=np.random.default_rng(0), federate=True,
            initial_grid_policy_probabilities={0: [1., 0., 0., 0., 0.]},
        )
        self.assertFalse(result.federated.updated)
        self.assertEqual(result.federated.metadata.total_sample_count, 0)
        self.assertEqual((result.next_grid_policy[0].source, result.next_grid_policy[0].vehicle_vector_count), ("initialization", 0))
        np.testing.assert_array_equal(result.next_grid_policy[0].probabilities, [1., 0., 0., 0., 0.])


if __name__ == "__main__":
    unittest.main()
