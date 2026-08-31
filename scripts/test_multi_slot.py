#!/usr/bin/env python3
"""Run the controlled four-slot temporal simulation; no full-scale data."""

from __future__ import annotations

from datetime import datetime, timedelta
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
from src.routing.baseline import CandidateUtilityInput, RoutingAction, RoutingParameters
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters
from src.simulation.multi_slot import TemporalSlotInput, run_four_slot_simulation
from src.simulation.pricing_dispatch import PricingContextInput
from src.simulation.statistics import OperationalStatistics


def main() -> int:
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
    learning = RoutingLearningParameters(local_observation_capacity=16, batch_size=16)
    locals_ = {i: LocalRoutingLearner(i, learning, seed=20 + i) for i in range(4)}
    common = locals_[0].policy_model.get_weights()
    for local in locals_.values():
        local.reset_from_global_weights(common)
    global_policy = LocalRoutingLearner(99, learning, seed=99)
    global_policy.reset_from_global_weights(common)
    low, high = CandidateUtilityInput(10., 0., .1), CandidateUtilityInput(100., 0., .1)
    def empirical_request(request_id: int, request_time: int, origin: int, fare: float, miles: float) -> RequestState:
        pickup = datetime(2026, 1, 1) + timedelta(minutes=request_id)
        return RequestState(
            request_id, request_time, origin, origin, base_fare=fare, source_trip_id=request_id,
            empirical_pickup_datetime=pickup, empirical_dropoff_datetime=pickup + timedelta(minutes=18),
            trip_duration_minutes=18., trip_distance_miles=miles, trip_distance_km=miles * 1.609344,
        )

    slots = [TemporalSlotInput(
        requests=[empirical_request(2 * t, 14 if t == 0 else 10, 0, 10., 1.), empirical_request(2 * t + 1, 14 if t == 0 else 10, 1, 20., 2.)],
        next_predicted_demand={0: 100. + t, 1: 80. + t},
        next_popularity={0: .8 + .01 * t, 1: .6 + .01 * t},
        utility_inputs_by_vehicle={
            1: {RoutingAction.STAY: low, RoutingAction.EAST: low},
            2: {RoutingAction.STAY: low if t in (0, 2) else high, RoutingAction.WEST: low if t in (0, 2) else high},
            3: {RoutingAction.STAY: low, RoutingAction.EAST: low},
        },
    ) for t in range(4)]
    fleet = Fleet([
        VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 6.),
        VehicleState(1, 0, VehicleStatus.IDLE, None, 0, "idle", 40.),
        VehicleState(2, 1, VehicleStatus.IDLE, None, 0, "idle", 40.),
        VehicleState(3, 0, VehicleStatus.IDLE, None, 0, "idle", 40.),
    ], frozenset((0, 1)), 2)
    learner = DisjointLinUCB(1.)
    initial_a_trace = float(sum(np.trace(matrix) for matrix in learner.A))
    result = run_four_slot_simulation(
        start_time=datetime(2026, 1, 1), slot_inputs=slots,
        initial_pricing_contexts={0: PricingContextInput(100., [.2] * 5, .8), 1: PricingContextInput(80., [.2] * 5, .6)},
        initial_grid_policy_probabilities={0: [.2] * 5, 1: [.2] * 5}, federation_slots={1, 3},
        learner=learner, acceptance_rng=np.random.default_rng(3), fleet=fleet,
        neighbour_lookup={0: (1,), 1: (0,)},
        directional_neighbour_map=pd.DataFrame({"GridID": [0, 1], "NeighbourGridID": [1, 0], "Direction": ["east", "west"]}),
        statistics_engine=OperationalStatistics([0, 1], .3),
        charging_infrastructure=ChargingInfrastructure([ChargingStation(0, 0, 30, 30)], {0: (0., 0.), 1: (1., 0.)}),
        energy_parameters=energy, routing_parameters=RoutingParameters(15., 3., 30.),
        local_learners=locals_, global_policy_learner=global_policy, default_trip_duration_minutes=2,
    )
    print("Slot | Time  | Generated | Accepted | Served | Accepted Revenue | Federated | Idle | Busy | Charging")
    for slot in result.slots:
        print(f"{slot.slot_index:>4} | {slot.timestamp:%H:%M} | {slot.generated:>9} | {slot.accepted:>8} | {slot.served:>6} | {slot.accepted_revenue:>16.2f} | {str(slot.federation_requested):>9} | {slot.fleet_counts['idle']:>4} | {slot.fleet_counts['busy']:>4} | {slot.fleet_counts['charging']:>8}")
    print("Representative grid 1")
    for slot in result.slots:
        policy = slot.grid_policy[1]
        print(f"slot {slot.slot_index}: factor={slot.pricing_factors[1]:.2f} source={policy.source} vector={policy.probabilities.tolist()}")
    final_a_trace = float(sum(np.trace(matrix) for matrix in learner.A))
    print("fleet_energy_kwh:", [round(slot.total_energy_kwh, 6) for slot in result.slots])
    print(f"LinUCB A trace: initial={initial_a_trace:.2f} final={final_a_trace:.2f} changed={not np.isclose(initial_a_trace, final_a_trace)}")
    print(f"passenger_trip_energy_status={result.passenger_trip_energy_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
