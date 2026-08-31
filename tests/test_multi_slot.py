"""Focused temporal-continuity tests for the controlled four-slot driver."""

from __future__ import annotations

from datetime import datetime, timedelta
import unittest

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingInfrastructure, ChargingStation
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import DisjointLinUCB
from src.routing.baseline import CandidateUtilityInput, RoutingAction, RoutingParameters
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters
from src.simulation.multi_slot import PASSENGER_TRIP_ENERGY_STATUS, TemporalSlotInput, run_four_slot_simulation
from src.simulation.pricing_dispatch import PricingContextInput
from src.simulation.statistics import OperationalStatistics


class MultiSlotTemporalTests(unittest.TestCase):
    def build(self, seed=3, duration=2):
        energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        learning = RoutingLearningParameters(learning_rate=.001, local_observation_capacity=16, batch_size=16, local_epochs=1)
        locals_ = {vehicle_id: LocalRoutingLearner(vehicle_id, learning, seed=20 + vehicle_id) for vehicle_id in range(3)}
        common = locals_[0].policy_model.get_weights()
        for local in locals_.values():
            local.reset_from_global_weights(common)
        global_policy = LocalRoutingLearner(99, learning, seed=99)
        global_policy.reset_from_global_weights(common)
        fleet = Fleet([
            VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 6.),
            VehicleState(1, 0, VehicleStatus.IDLE, None, 0, "idle", 40.),
            VehicleState(2, 1, VehicleStatus.IDLE, None, 0, "idle", 40.),
        ], frozenset((0, 1)), 2)
        low = CandidateUtilityInput(10., 0., .1)
        high = CandidateUtilityInput(100., 0., .1)
        inputs = []
        for slot in range(4):
            second = low if slot in (0, 2) else high
            inputs.append(TemporalSlotInput(
                requests=[RequestState(slot * 2, 0, 0, 0, base_fare=10.), RequestState(slot * 2 + 1, 0, 1, 1, base_fare=20.)],
                next_predicted_demand={0: 100. + slot, 1: 80. + slot},
                next_popularity={0: .8 + .01 * slot, 1: .6 + .01 * slot},
                utility_inputs_by_vehicle={
                    1: {RoutingAction.STAY: low, RoutingAction.EAST: low},
                    2: {RoutingAction.STAY: second, RoutingAction.WEST: second},
                },
            ))
        rng = np.random.default_rng(seed)
        pricing = DisjointLinUCB(1.)
        statistics = OperationalStatistics([0, 1], .3)
        charging = ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.), 1: (1., 0.)}, random_seed=7)
        result = run_four_slot_simulation(
            start_time=datetime(2026, 1, 1, 0, 0), slot_inputs=inputs,
            initial_pricing_contexts={0: PricingContextInput(100., [.2] * 5, .8), 1: PricingContextInput(80., [.2] * 5, .6)},
            initial_grid_policy_probabilities={0: [.2] * 5, 1: [.2] * 5}, federation_slots={1, 3},
            learner=pricing, acceptance_rng=rng, fleet=fleet, neighbour_lookup={0: (1,), 1: (0,)},
            directional_neighbour_map=pd.DataFrame({"GridID": [0, 1], "NeighbourGridID": [1, 0], "Direction": ["east", "west"]}),
            statistics_engine=statistics, charging_infrastructure=charging, energy_parameters=energy,
            routing_parameters=RoutingParameters(15., 3., 30.), local_learners=locals_, global_policy_learner=global_policy,
            default_trip_duration_minutes=duration,
        )
        return result, fleet, pricing, rng, statistics, charging, locals_, global_policy

    def test_four_slots_exact_time_and_no_premature_pricing(self) -> None:
        result, _, pricing, _, _, _, _, _ = self.build()
        self.assertEqual(len(result.slots), 4)
        self.assertEqual([slot.timestamp for slot in result.slots], [result.start_time + timedelta(minutes=30 * i) for i in range(4)])
        self.assertEqual(result.end_time, result.start_time + timedelta(hours=2))
        self.assertTrue(all(slot.mini_slot_count == 15 for slot in result.slots))
        self.assertEqual([slot.pricing_updates_before for slot in result.slots], [0, 2, 4, 6])
        self.assertEqual([slot.pricing_updates_after for slot in result.slots], [2, 4, 6, 8])
        self.assertEqual(int(pricing.selection_counts.sum()), 8)

    def test_rng_is_one_stream_and_full_replay_is_deterministic(self) -> None:
        first, _, _, rng, _, _, _, _ = self.build(seed=3)
        second, *_ = self.build(seed=3)
        trajectory_a = [(slot.acceptance_outcomes, slot.pricing_factors, slot.routing_action_counts) for slot in first.slots]
        trajectory_b = [(slot.acceptance_outcomes, slot.pricing_factors, slot.routing_action_counts) for slot in second.slots]
        self.assertEqual(trajectory_a, trajectory_b)
        control = np.random.default_rng(3)
        for _ in range(8):
            control.random()
        self.assertEqual(rng.random(), control.random())

    def test_fleet_nb9_learning_and_charging_state_persist(self) -> None:
        result, fleet, _, _, statistics, charging, learners, _ = self.build()
        np.testing.assert_allclose([slot.total_energy_kwh for slot in result.slots], [99.05, 112.55, 126.05, 139.55])
        self.assertTrue(all(slot.charging_active == 1 for slot in result.slots))
        self.assertIn(0, charging.vehicle_station)
        self.assertEqual(fleet.vehicle(0).trip_status, VehicleStatus.CHARGING)
        rows0 = [{row.grid_id: row for row in slot.statistics}[0] for slot in result.slots]
        self.assertEqual(rows0[1].ewma_fare, .3 * rows0[1].mean_fare + .7 * rows0[0].ewma_fare)
        self.assertEqual(statistics.ewma_state[0], result.slots[-1].ewma_state[0])
        self.assertTrue(all(result.slots[i].local_sample_counts[1] < result.slots[i + 1].local_sample_counts[1] for i in range(3)))
        self.assertEqual(learners[1]._trained_slots, {0, 1, 2, 3})

    def test_nb11_authority_federation_schedule_and_global_persistence(self) -> None:
        result, _, _, _, _, _, learners, _ = self.build()
        self.assertEqual([slot.federation_requested for slot in result.slots], [False, True, False, True])
        self.assertEqual([slot.global_updated for slot in result.slots], [False, True, False, True])
        self.assertEqual(result.slots[0].global_weight_norm_before, result.slots[0].global_weight_norm_after)
        self.assertEqual(result.slots[2].global_weight_norm_before, result.slots[2].global_weight_norm_after)
        for local in learners.values():
            exported = local.export_local_update()
            self.assertNotIn("rewards", exported)
            self.assertNotIn("next_states", exported)
        self.assertEqual(result.slots[0].routing_action_counts, {"STAY": 1, "WEST": 1})
        # No completed driver waits in a candidate grid means no fabricated
        # instantaneous NB9 wait value and therefore no NB11 decision that slot.
        self.assertEqual(result.slots[1].routing_action_counts, {})

    def test_grid_policy_initialization_then_mean_then_latest_carry_forward(self) -> None:
        result, *_ = self.build()
        grid_one = [slot.grid_policy[1] for slot in result.slots]
        self.assertEqual([item.source for item in grid_one[:3]], ["initialization", "current_vehicle_mean", "current_vehicle_mean"])
        self.assertEqual([item.vehicle_vector_count for item in grid_one[:3]], [0, 1, 1])
        self.assertFalse(np.allclose(grid_one[2].probabilities, [.2] * 5))

    def test_passenger_energy_limitation_and_busy_state_can_cross_boundaries(self) -> None:
        self.assertEqual(PASSENGER_TRIP_ENERGY_STATUS, "implemented_existing_contract")
        # Existing placeholder duration, not a new travel-time model: 122 minutes spans this controlled run.
        energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
        learning = RoutingLearningParameters(local_observation_capacity=4, batch_size=4)
        local = LocalRoutingLearner(0, learning, seed=1)
        global_policy = LocalRoutingLearner(9, learning, seed=2)
        global_policy.reset_from_global_weights(local.policy_model.get_weights())
        fleet = Fleet([VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 40.)], frozenset((0,)), 2)
        slots = [TemporalSlotInput(
            requests=[RequestState(0, 14, 0, 0, base_fare=10.)] if i == 0 else [],
            next_predicted_demand={0: 100.}, next_popularity={0: .5}, utility_inputs_by_vehicle={},
        ) for i in range(4)]
        result = run_four_slot_simulation(
            start_time=datetime(2026, 1, 1), slot_inputs=slots,
            initial_pricing_contexts={0: PricingContextInput(100., [1., 0., 0., 0., 0.], .5)},
            initial_grid_policy_probabilities={0: [1., 0., 0., 0., 0.]}, federation_slots=set(),
            learner=DisjointLinUCB(1.), acceptance_rng=np.random.default_rng(0), fleet=fleet,
            neighbour_lookup={0: ()}, directional_neighbour_map=pd.DataFrame(columns=["GridID", "NeighbourGridID", "Direction"]),
            statistics_engine=OperationalStatistics([0], .3),
            charging_infrastructure=ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.)}),
            energy_parameters=energy, routing_parameters=RoutingParameters(15., 3., 30.), local_learners={0: local},
            global_policy_learner=global_policy, default_trip_duration_minutes=122,
        )
        self.assertEqual(result.slots[0].fleet_counts["busy"], 1)
        self.assertEqual(result.slots[1].fleet_counts["busy"], 1)
        self.assertEqual(result.passenger_trip_energy_status, "implemented_existing_contract")


if __name__ == "__main__":
    unittest.main()
