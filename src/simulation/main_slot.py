"""One complete 30-minute orchestration over frozen project components."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters, requires_charging
from src.charging.stations import ChargingInfrastructure
from src.dispatch.request import RequestState, RequestStatus
from src.dispatch.contention import DriverContentionInputs
from src.dispatch.dispatch import DISPATCH_MODEL_LEGACY
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleStatus
from src.fleet.supply import aggregate_grid_supply
from src.pricing.linucb import DisjointLinUCB
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel
from src.routing.baseline import (
    ACTION_ORDER, CandidateUtilityInput, RoutingAction, RoutingDecision,
    RoutingParameters, RoutingState, RoutingTransition, build_grid_routing_features,
    build_routing_state, execute_reposition, select_action,
)
from src.routing.federated import FederatedRoundResult, aggregate_policy_updates
from src.routing.learning import LocalRoutingLearner, action_mask_array
from src.simulation.grid_policy import GridPolicyProbabilities, aggregate_grid_policy_probabilities
from src.simulation.pricing_dispatch import PricingContextInput, PricingDispatchSlotResult, run_pricing_dispatch_slot
from src.simulation.statistics import EWMAState, FareObservation, GridSlotStatistics, OperationalStatistics


@dataclass(frozen=True)
class RoutingAudit:
    vehicle_id: int
    state: RoutingState
    decision: RoutingDecision
    transition: RoutingTransition


@dataclass(frozen=True)
class ChargingSlotSummary:
    energy_before_kwh: float
    energy_after_kwh: float
    active_vehicle_count: int
    queued_vehicle_count: int
    presented_vehicle_count: int
    passenger_energy_consumed_kwh: float
    repositioning_energy_consumed_kwh: float
    charging_energy_gained_kwh: float


@dataclass(frozen=True)
class LocalLearningSummary:
    observations_collected: int
    learners_trained: int
    sample_counts: dict[int, int]


@dataclass(frozen=True)
class NextPricingContext:
    predicted_demand: float
    current_supply: int
    routing_probabilities: np.ndarray
    popularity: float
    probability_source: str
    eligible_vehicle_vectors: int


@dataclass(frozen=True)
class MainSlotResult:
    pricing_dispatch: PricingDispatchSlotResult
    statistics: tuple[GridSlotStatistics, ...]
    ewma_state: dict[int, EWMAState]
    charging: ChargingSlotSummary
    routing_audit: tuple[RoutingAudit, ...]
    routing_action_counts: dict[str, int]
    local_learning: LocalLearningSummary
    federated: FederatedRoundResult | None
    next_grid_policy: dict[int, GridPolicyProbabilities]
    next_pricing_contexts: dict[int, NextPricingContext]
    stage_order: tuple[str, ...]


def _present_low_energy_vehicles(
    fleet: Fleet,
    infrastructure: ChargingInfrastructure,
    energy: EnergyParameters,
    arrival_order_start: int,
) -> int:
    presented = 0
    for offset, vehicle in enumerate(sorted(fleet.vehicles, key=lambda item: item.vehicle_id)):
        if vehicle.vehicle_id not in infrastructure.vehicle_station and vehicle.trip_status is not VehicleStatus.BUSY and requires_charging(vehicle, energy):
            infrastructure.present_vehicle(vehicle, energy, arrival_order_start + offset)
            presented += 1
    return presented


def run_main_slot(
    *,
    slot_id: int,
    requests: Iterable[RequestState],
    pricing_context_inputs: Mapping[int, PricingContextInput],
    next_predicted_demand: Mapping[int, float],
    next_popularity: Mapping[int, float],
    learner: DisjointLinUCB,
    fleet: Fleet,
    neighbour_lookup: Mapping[int, Iterable[int]],
    directional_neighbour_map: pd.DataFrame,
    statistics_engine: OperationalStatistics,
    charging_infrastructure: ChargingInfrastructure,
    energy_parameters: EnergyParameters,
    routing_parameters: RoutingParameters,
    utility_inputs_by_vehicle: Mapping[int, Mapping[RoutingAction | str, CandidateUtilityInput]],
    local_learners: Mapping[int, LocalRoutingLearner],
    global_policy_learner: LocalRoutingLearner,
    default_trip_duration_minutes: int,
    mini_slots_per_main_slot: int,
    acceptance_rng: np.random.Generator,
    federate: bool,
    federation_round_index: int = 0,
    previous_grid_probabilities: Mapping[int, Sequence[float] | np.ndarray] | None = None,
    initial_grid_policy_probabilities: Mapping[int, Sequence[float] | np.ndarray] | None = None,
    customer_response_model: str = "eq31",
    historical_customer_model: HistoricalCustomerSensitivityModel | None = None,
    weather_code: float | None = None,
    period: int | None = None,
    simulation_timestamp: datetime | None = None,
    reward_model: str = "legacy_normalized_accepted_revenue",
    supply_model: str = "legacy_all_statuses",
    pricing_decision_mode: str = "legacy_grid",
    grid_lookup: pd.DataFrame | None = None,
    popularity_table: pd.DataFrame | None = None,
    sensitivity_fallback: str = "error",
    linucb_reward_scaling: str = "none",
    dispatch_model: str = DISPATCH_MODEL_LEGACY,
    contention_inputs: DriverContentionInputs | None = None,
) -> MainSlotResult:
    """Coordinate one slot and stop immediately before next-slot pricing selection."""
    if set(next_predicted_demand) != set(pricing_context_inputs) or set(next_popularity) != set(pricing_context_inputs):
        raise ValueError("Next demand and popularity must cover exactly the active pricing grids.")
    if tuple(statistics_engine.valid_grid_ids) != tuple(sorted(fleet.valid_grid_ids)):
        raise ValueError("NB9 and fleet canonical GridIDs must match.")

    stage_order: list[str] = []
    energy_before = float(sum(vehicle.energy_level for vehicle in fleet.vehicles))
    presented = _present_low_energy_vehicles(fleet, charging_infrastructure, energy_parameters, slot_id * mini_slots_per_main_slot)
    charging_energy_gained = 0.0

    def advance_charging(mini_slot: int) -> None:
        nonlocal presented, charging_energy_gained
        presented += _present_low_energy_vehicles(
            fleet, charging_infrastructure, energy_parameters,
            slot_id * mini_slots_per_main_slot + mini_slot,
        )
        before = sum(vehicle.energy_level for vehicle in fleet.vehicles)
        charging_infrastructure.advance_mini_slot(fleet.vehicles, fleet.mini_slot_minutes, energy_parameters)
        charging_energy_gained += sum(vehicle.energy_level for vehicle in fleet.vehicles) - before

    pricing_result = run_pricing_dispatch_slot(
        requests, pricing_context_inputs, learner, fleet, neighbour_lookup,
        default_trip_duration_minutes, mini_slots_per_main_slot, acceptance_rng,
        energy_parameters, mini_slot_callback=advance_charging,
        customer_response_model=customer_response_model,
        historical_customer_model=historical_customer_model,
        weather_code=weather_code, period=period,
        simulation_timestamp=simulation_timestamp,
        reward_model=reward_model,
        supply_model=supply_model,
        pricing_decision_mode=pricing_decision_mode,
        grid_lookup=grid_lookup,
        popularity_table=popularity_table,
        sensitivity_fallback=sensitivity_fallback,
        linucb_reward_scaling=linucb_reward_scaling,
        dispatch_model=dispatch_model,
        contention_inputs=contention_inputs,
    )
    stage_order.append("pricing_acceptance_dispatch")
    stage_order.append("nb10_charging")

    request_items = list(requests)
    passenger_energy_consumed = float(sum(request.passenger_energy_kwh or 0.0 for request in request_items))
    fares = [
        FareObservation(request.origin_grid, float(request.offered_fare))
        for request in request_items if request.status is RequestStatus.ASSIGNED
    ]
    slot_statistics = statistics_engine.update_slot(
        slot_id, fares, request_items, charging_infrastructure.charging_observations(),
        pricing_result.driver_wait_observations,
    )
    stage_order.append("nb9_statistics")

    supply_before_routing = aggregate_grid_supply(fleet.vehicles, fleet.valid_grid_ids)
    routing_features = build_grid_routing_features(next_predicted_demand, supply_before_routing, slot_statistics)
    routing_audits: list[RoutingAudit] = []
    for vehicle in sorted(fleet.vehicles, key=lambda item: item.vehicle_id):
        if vehicle.trip_status is not VehicleStatus.IDLE or requires_charging(vehicle, energy_parameters):
            continue
        if vehicle.vehicle_id not in utility_inputs_by_vehicle or vehicle.vehicle_id not in local_learners:
            raise ValueError(f"Eligible vehicle {vehicle.vehicle_id} lacks utility inputs or a local learner.")
        state = build_routing_state(vehicle, routing_features, directional_neighbour_map)
        if any(
            feature is not None and (
                feature.mean_fare is None or feature.std_fare is None
                or feature.mean_wait is None or feature.std_wait is None
            )
            for feature in state.action_features.values()
        ):
            # No completed dispatch wait means no instantaneous NB9 sample.
            # Preserve that missingness instead of fabricating zero utility input.
            continue
        decision = select_action(state, utility_inputs_by_vehicle[vehicle.vehicle_id], energy_parameters)
        transition = execute_reposition(vehicle, state, decision.chosen_action, routing_parameters, energy_parameters)
        local_learners[vehicle.vehicle_id].record_observation(
            state, decision.chosen_action,
            action_mask=action_mask_array(state),
            utility_vector=np.asarray([
                np.nan if decision.utility_vector[action] is None else decision.utility_vector[action]
                for action in ACTION_ORDER
            ], dtype=np.float32),
            slot_id=slot_id,
        )
        routing_audits.append(RoutingAudit(vehicle.vehicle_id, state, decision, transition))
    stage_order.append("nb11_routing")

    # A move may cross the charging threshold; register that existing NB10 state.
    presented += _present_low_energy_vehicles(fleet, charging_infrastructure, energy_parameters, (slot_id + 1) * mini_slots_per_main_slot)

    trained = 0
    for vehicle_id, local in sorted(local_learners.items()):
        loss = local.train_for_slot(slot_id)
        trained += int(loss is not None)
    learning_summary = LocalLearningSummary(
        observations_collected=len(routing_audits),
        learners_trained=trained,
        sample_counts={vehicle_id: local.local_sample_count for vehicle_id, local in sorted(local_learners.items())},
    )
    stage_order.append("nb12_training")

    federated_result: FederatedRoundResult | None = None
    if federate:
        exports = [local.export_local_update() for _, local in sorted(local_learners.items())]
        federated_result = aggregate_policy_updates(exports, round_index=federation_round_index)
        if federated_result.updated:
            global_policy_learner.reset_from_global_weights(federated_result.weights)
            for local in local_learners.values():
                local.reset_from_global_weights(federated_result.weights)
    stage_order.append("nb13_federation")

    next_supply = aggregate_grid_supply(fleet.vehicles, fleet.valid_grid_ids)
    next_features = build_grid_routing_features(next_predicted_demand, next_supply, slot_statistics)
    vehicle_probabilities: dict[int, list[np.ndarray]] = defaultdict(list)
    for vehicle in sorted(fleet.vehicles, key=lambda item: item.vehicle_id):
        if vehicle.trip_status is VehicleStatus.IDLE and not requires_charging(vehicle, energy_parameters):
            state = build_routing_state(vehicle, next_features, directional_neighbour_map)
            vehicle_probabilities[vehicle.current_grid].append(global_policy_learner.policy_probabilities(state))
    grid_policy = aggregate_grid_policy_probabilities(
        pricing_context_inputs.keys(), vehicle_probabilities,
        previous_grid_probabilities=previous_grid_probabilities,
        initial_grid_policy_probabilities=initial_grid_policy_probabilities,
    )
    stage_order.append("global_policy_probabilities")

    supply_by_grid = next_supply.set_index("grid_id")
    next_contexts = {
        grid_id: NextPricingContext(
            predicted_demand=float(next_predicted_demand[grid_id]),
            current_supply=int(supply_by_grid.at[grid_id, "supply_total"]),
            routing_probabilities=policy.probabilities.copy(),
            popularity=float(next_popularity[grid_id]),
            probability_source=policy.source,
            eligible_vehicle_vectors=policy.vehicle_vector_count,
        )
        for grid_id, policy in grid_policy.items()
    }
    stage_order.append("next_pricing_inputs")
    action_counts = Counter(audit.decision.chosen_action.value for audit in routing_audits)
    repositioning_energy_consumed = float(sum(
        audit.transition.energy_before_kwh - audit.transition.energy_after_kwh for audit in routing_audits
    ))
    return MainSlotResult(
        pricing_dispatch=pricing_result,
        statistics=tuple(slot_statistics),
        ewma_state=dict(statistics_engine.ewma_state),
        charging=ChargingSlotSummary(
            energy_before_kwh=energy_before,
            energy_after_kwh=float(sum(vehicle.energy_level for vehicle in fleet.vehicles)),
            active_vehicle_count=sum(len(station.active_vehicle_ids) for station in charging_infrastructure.stations.values()),
            queued_vehicle_count=sum(len(station.queue) for station in charging_infrastructure.stations.values()),
            presented_vehicle_count=presented,
            passenger_energy_consumed_kwh=passenger_energy_consumed,
            repositioning_energy_consumed_kwh=repositioning_energy_consumed,
            charging_energy_gained_kwh=charging_energy_gained,
        ),
        routing_audit=tuple(routing_audits),
        routing_action_counts=dict(action_counts),
        local_learning=learning_summary,
        federated=federated_result,
        next_grid_policy=grid_policy,
        next_pricing_contexts=next_contexts,
        stage_order=tuple(stage_order),
    )
