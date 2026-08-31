#!/usr/bin/env python3
"""Tiny deterministic demonstration of one complete 30-minute main slot."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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


def main() -> int:
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
    learning = RoutingLearningParameters(learning_rate=.001, local_observation_capacity=8, batch_size=8, local_epochs=1)
    learners = {vehicle_id: LocalRoutingLearner(vehicle_id, learning, seed=10 + vehicle_id) for vehicle_id in range(3)}
    weights = learners[0].policy_model.get_weights()
    weights[-1] = np.array([0., 0., 100., 0., 0.], dtype=np.float32)
    for local in learners.values():
        local.reset_from_global_weights(weights)
    global_policy = LocalRoutingLearner(99, learning, seed=99)
    global_policy.reset_from_global_weights(weights)
    fleet = Fleet([
        VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 6.),
        VehicleState(1, 0, VehicleStatus.IDLE, None, 0, "idle", 40.),
        VehicleState(2, 1, VehicleStatus.IDLE, None, 0, "idle", 40.),
    ], frozenset((0, 1)), 2)
    infrastructure = ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.), 1: (1., 0.)}, random_seed=3)
    preference = CandidateUtilityInput(10., 0., .1)
    result = run_main_slot(
        slot_id=0,
        requests=[RequestState(0, 0, 0, 0, base_fare=10.), RequestState(1, 0, 1, 1, base_fare=20.)],
        pricing_context_inputs={
            0: PricingContextInput(10., [.2] * 5, .8),
            1: PricingContextInput(10., [.2] * 5, .6),
        },
        next_predicted_demand={0: 12., 1: 8.}, next_popularity={0: .8, 1: .6},
        learner=DisjointLinUCB(1.), fleet=fleet, neighbour_lookup={0: (1,), 1: (0,)},
        directional_neighbour_map=pd.DataFrame({"GridID": [0, 1], "NeighbourGridID": [1, 0], "Direction": ["east", "west"]}),
        statistics_engine=OperationalStatistics([0, 1], .3), charging_infrastructure=infrastructure,
        energy_parameters=energy, routing_parameters=RoutingParameters(15., 3., 30.),
        utility_inputs_by_vehicle={
            1: {RoutingAction.STAY: preference, RoutingAction.EAST: preference},
            2: {RoutingAction.STAY: preference, RoutingAction.WEST: preference},
        },
        local_learners=learners, global_policy_learner=global_policy,
        default_trip_duration_minutes=2, mini_slots_per_main_slot=15,
        acceptance_rng=np.random.default_rng(0), federate=True, federation_round_index=0,
        initial_grid_policy_probabilities={0: [.2] * 5, 1: [.2] * 5},
    )
    pricing = result.pricing_dispatch
    print("START SLOT")
    print("Pricing:", {grid: item.decision.pricing_factor for grid, item in pricing.pricing_by_context.items()})
    print(f"Mini-slots: generated={pricing.generated} accepted={pricing.accepted} served={pricing.served}")
    print("NB9:", {row.grid_id: (row.mean_fare, row.mean_wait, row.ewma_fare) for row in result.statistics})
    print(f"NB10: active={result.charging.active_vehicle_count} queued={result.charging.queued_vehicle_count} energy={result.charging.energy_before_kwh:.2f}->{result.charging.energy_after_kwh:.2f}")
    print("NB11:", {audit.vehicle_id: audit.decision.chosen_action.value for audit in result.routing_audit})
    first = result.routing_audit[0]
    policy_argmax = ACTION_ORDER[int(np.argmax(global_policy.policy_probabilities(first.state)))]
    print(f"Role distinction: global argmax={policy_argmax.value}, NB11 actual={first.transition.action.value}")
    print(f"NB12: observations={result.local_learning.observations_collected} trained={result.local_learning.learners_trained}")
    print(f"NB13: participants={result.federated.metadata.participating_updates} samples={result.federated.metadata.total_sample_count} updated={result.federated.updated}")
    print("NEXT STATE")
    for grid, context in result.next_pricing_contexts.items():
        print(f"grid={grid} supply={context.current_supply} probabilities={context.routing_probabilities.tolist()} source={context.probability_source} vectors={context.eligible_vehicle_vectors} popularity={context.popularity} demand={context.predicted_demand}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
