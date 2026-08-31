"""Short four-slot temporal driver around the completed main-slot orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingInfrastructure
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.supply import aggregate_grid_supply
from src.pricing.linucb import DisjointLinUCB
from src.routing.baseline import CandidateUtilityInput, RoutingAction, RoutingParameters
from src.routing.learning import LocalRoutingLearner
from src.simulation.grid_policy import GridPolicyProbabilities
from src.simulation.main_slot import run_main_slot
from src.simulation.pricing_dispatch import PricingContextInput
from src.dispatch.dispatch import DriverWaitObservation
from src.simulation.statistics import EWMAState, GridSlotStatistics, OperationalStatistics


PASSENGER_TRIP_ENERGY_STATUS = "implemented_existing_contract"


@dataclass(frozen=True)
class TemporalSlotInput:
    """Exogenous data made available for one slot boundary only."""

    requests: Sequence[RequestState]
    next_predicted_demand: Mapping[int, float]
    next_popularity: Mapping[int, float]
    utility_inputs_by_vehicle: Mapping[int, Mapping[RoutingAction | str, CandidateUtilityInput]]


@dataclass(frozen=True)
class TemporalSlotSummary:
    slot_index: int
    timestamp: datetime
    mini_slot_count: int
    pricing_factors: dict[int, float]
    pricing_popularity: dict[int, float]
    pricing_cold_start: dict[int, bool]
    pricing_raw_opportunity_reward: dict[int, float | None]
    pricing_normalized_reward: dict[int, float | None]
    pricing_reward_clipped: dict[int, bool]
    pricing_context_audit: dict[int, dict[str, float | bool]]
    generated: int
    accepted: int
    rejected: int
    served: int
    accepted_but_unserved: int
    accepted_revenue: float
    served_revenue: float
    acceptance_outcomes: tuple[bool, ...]
    acceptance_probabilities: tuple[float, ...]
    driver_wait_observations: tuple[DriverWaitObservation, ...]
    fleet_counts: dict[str, int]
    supply_by_grid: dict[int, dict[str, int]]
    total_energy_kwh: float
    minimum_energy_kwh: float
    maximum_energy_kwh: float
    passenger_energy_consumed_kwh: float
    repositioning_energy_consumed_kwh: float
    charging_energy_gained_kwh: float
    charging_active: int
    charging_queued: int
    maximum_station_queue_length: int
    mean_station_queue_length: float
    charging_capacity_valid: bool
    queue_membership_valid: bool
    maximum_remaining_busy_minutes: float
    statistics: tuple[GridSlotStatistics, ...]
    ewma_state: dict[int, EWMAState]
    routing_action_counts: dict[str, int]
    routing_decisions_valid: bool
    routing_wait_utilities: tuple[float, ...]
    local_observations: int
    learners_trained: int
    local_sample_counts: dict[int, int]
    federation_requested: bool
    federation_participants: int
    federation_samples: int
    global_updated: bool
    global_weight_norm_before: float
    global_weight_norm_after: float
    grid_policy: dict[int, GridPolicyProbabilities]
    pricing_updates_before: int
    pricing_updates_after: int


@dataclass(frozen=True)
class MultiSlotResult:
    start_time: datetime
    end_time: datetime
    slots: tuple[TemporalSlotSummary, ...]
    passenger_trip_energy_status: str


def _weight_norm(learner: LocalRoutingLearner) -> float:
    return float(sum(np.linalg.norm(weight) for weight in learner.policy_model.get_weights()))


def run_multi_slot_simulation(
    *,
    start_time: datetime,
    slot_inputs: Sequence[TemporalSlotInput],
    slot_count: int | None = None,
    initial_pricing_contexts: Mapping[int, PricingContextInput],
    initial_grid_policy_probabilities: Mapping[int, Sequence[float] | np.ndarray],
    federation_slots: Iterable[int],
    learner: DisjointLinUCB,
    acceptance_rng: np.random.Generator,
    fleet: Fleet,
    neighbour_lookup: Mapping[int, Iterable[int]],
    directional_neighbour_map: pd.DataFrame,
    statistics_engine: OperationalStatistics,
    charging_infrastructure: ChargingInfrastructure,
    energy_parameters: EnergyParameters,
    routing_parameters: RoutingParameters,
    local_learners: Mapping[int, LocalRoutingLearner],
    global_policy_learner: LocalRoutingLearner,
    default_trip_duration_minutes: int,
    mini_slots_per_main_slot: int = 15,
) -> MultiSlotResult:
    """Execute N consecutive slots while reusing every mutable state owner."""
    count = len(slot_inputs) if slot_count is None else slot_count
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0 or len(slot_inputs) != count:
        raise ValueError("slot_count must be positive and equal the number of slot inputs.")
    if mini_slots_per_main_slot != 15 or fleet.mini_slot_minutes != 2:
        raise ValueError("The controlled temporal run requires 15 two-minute mini-slots.")
    if not isinstance(acceptance_rng, np.random.Generator):
        raise ValueError("acceptance_rng must be one explicit persistent numpy Generator.")
    scheduled = set(federation_slots)
    if any(isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < count for index in scheduled):
        raise ValueError(f"Federation slots must be explicit indices in 0..{count - 1}.")

    current_contexts = dict(initial_pricing_contexts)
    previous_grid_probabilities: dict[int, np.ndarray] | None = None
    summaries: list[TemporalSlotSummary] = []
    for slot_index, slot_input in enumerate(slot_inputs):
        # Only this boundary's explicitly supplied forecast/popularity is passed.
        updates_before = int(learner.update_counts.sum())
        global_before = _weight_norm(global_policy_learner)
        result = run_main_slot(
            slot_id=slot_index,
            requests=slot_input.requests,
            pricing_context_inputs=current_contexts,
            next_predicted_demand=slot_input.next_predicted_demand,
            next_popularity=slot_input.next_popularity,
            learner=learner,
            fleet=fleet,
            neighbour_lookup=neighbour_lookup,
            directional_neighbour_map=directional_neighbour_map,
            statistics_engine=statistics_engine,
            charging_infrastructure=charging_infrastructure,
            energy_parameters=energy_parameters,
            routing_parameters=routing_parameters,
            utility_inputs_by_vehicle=slot_input.utility_inputs_by_vehicle,
            local_learners=local_learners,
            global_policy_learner=global_policy_learner,
            default_trip_duration_minutes=default_trip_duration_minutes,
            mini_slots_per_main_slot=mini_slots_per_main_slot,
            acceptance_rng=acceptance_rng,
            federate=slot_index in scheduled,
            federation_round_index=slot_index,
            previous_grid_probabilities=previous_grid_probabilities,
            initial_grid_policy_probabilities=initial_grid_policy_probabilities,
        )
        previous_grid_probabilities = {
            grid_id: policy.probabilities.copy() for grid_id, policy in result.next_grid_policy.items()
        }
        current_contexts = {
            grid_id: PricingContextInput(
                context.predicted_demand, context.routing_probabilities.copy(), context.popularity,
            )
            for grid_id, context in result.next_pricing_contexts.items()
        }
        supply = aggregate_grid_supply(fleet.vehicles, fleet.valid_grid_ids)
        by_grid = {
            int(row.grid_id): {
                "total": int(row.supply_total), "idle": int(row.supply_idle),
                "busy": int(row.supply_busy), "charging": int(row.supply_charging),
            }
            for row in supply.itertuples(index=False)
        }
        counts = {
            name: int(sum(values[name] for values in by_grid.values()))
            for name in ("idle", "busy", "charging")
        }
        energies = np.asarray([vehicle.energy_level for vehicle in fleet.vehicles], dtype=np.float64)
        federation = result.federated
        queue_ids = [entry.vehicle_id for station in charging_infrastructure.stations.values() for entry in station.queue]
        active_charging_ids = [vehicle_id for station in charging_infrastructure.stations.values() for vehicle_id in station.active_vehicle_ids]
        queue_lengths = [len(station.queue) for station in charging_infrastructure.stations.values()]
        routing_valid = all(
            audit.decision.valid_action_mask[audit.decision.chosen_action]
            and audit.transition.action is audit.decision.chosen_action
            and audit.decision.utility_vector[audit.decision.chosen_action]
            == max(value for value in audit.decision.utility_vector.values() if value is not None)
            for audit in result.routing_audit
        )
        summaries.append(TemporalSlotSummary(
            slot_index=slot_index,
            timestamp=start_time + timedelta(minutes=30 * slot_index),
            mini_slot_count=mini_slots_per_main_slot,
            pricing_factors={grid: item.decision.pricing_factor for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_popularity={grid: float(item.decision.context[-1]) for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_cold_start={grid: item.decision.cold_start for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_raw_opportunity_reward={grid: item.raw_revenue_per_opportunity for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_normalized_reward={grid: item.normalized_reward for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_reward_clipped={grid: item.reward_clipped for grid, item in result.pricing_dispatch.pricing_by_context.items()},
            pricing_context_audit={
                grid: {
                    "raw_predicted_demand": item.raw_predicted_demand,
                    "nonnegative_predicted_demand": item.nonnegative_predicted_demand,
                    "scaled_predicted_demand": item.scaled_predicted_demand,
                    "raw_supply": item.raw_supply,
                    "scaled_supply": item.scaled_supply,
                    "demand_negative_clipped": item.demand_negative_clipped,
                    "demand_upper_clipped": item.demand_upper_clipped,
                    "supply_upper_clipped": item.supply_upper_clipped,
                }
                for grid, item in result.pricing_dispatch.pricing_by_context.items()
            },
            generated=result.pricing_dispatch.generated,
            accepted=result.pricing_dispatch.accepted,
            rejected=result.pricing_dispatch.rejected,
            served=result.pricing_dispatch.served,
            accepted_but_unserved=result.pricing_dispatch.accepted_but_unserved,
            accepted_revenue=result.pricing_dispatch.accepted_revenue,
            served_revenue=result.pricing_dispatch.served_revenue,
            acceptance_outcomes=tuple(audit.customer_accepted for audit in result.pricing_dispatch.request_audit),
            acceptance_probabilities=tuple(audit.acceptance_probability for audit in result.pricing_dispatch.request_audit),
            driver_wait_observations=result.pricing_dispatch.driver_wait_observations,
            fleet_counts=counts,
            supply_by_grid=by_grid,
            total_energy_kwh=float(energies.sum()),
            minimum_energy_kwh=float(energies.min()),
            maximum_energy_kwh=float(energies.max()),
            passenger_energy_consumed_kwh=result.charging.passenger_energy_consumed_kwh,
            repositioning_energy_consumed_kwh=result.charging.repositioning_energy_consumed_kwh,
            charging_energy_gained_kwh=result.charging.charging_energy_gained_kwh,
            charging_active=result.charging.active_vehicle_count,
            charging_queued=result.charging.queued_vehicle_count,
            maximum_station_queue_length=max(queue_lengths, default=0),
            mean_station_queue_length=float(np.mean(queue_lengths)) if queue_lengths else 0.0,
            charging_capacity_valid=all(station.active_reserved_power_kw <= station.max_power_kw for station in charging_infrastructure.stations.values()),
            queue_membership_valid=(len(queue_ids) == len(set(queue_ids)) and len(active_charging_ids) == len(set(active_charging_ids)) and set(queue_ids).isdisjoint(active_charging_ids)),
            maximum_remaining_busy_minutes=max((vehicle.remaining_travel_time for vehicle in fleet.vehicles if vehicle.trip_status.value == "BUSY"), default=0.0),
            statistics=result.statistics,
            ewma_state=result.ewma_state,
            routing_action_counts=result.routing_action_counts,
            routing_decisions_valid=routing_valid,
            routing_wait_utilities=tuple(
                component.wait
                for audit in result.routing_audit
                for component in audit.decision.components.values()
                if component is not None
            ),
            local_observations=result.local_learning.observations_collected,
            learners_trained=result.local_learning.learners_trained,
            local_sample_counts=result.local_learning.sample_counts,
            federation_requested=slot_index in scheduled,
            federation_participants=0 if federation is None else federation.metadata.participating_updates,
            federation_samples=0 if federation is None else federation.metadata.total_sample_count,
            global_updated=False if federation is None else federation.updated,
            global_weight_norm_before=global_before,
            global_weight_norm_after=_weight_norm(global_policy_learner),
            grid_policy={grid: GridPolicyProbabilities(grid, policy.probabilities.copy(), policy.source, policy.vehicle_vector_count) for grid, policy in result.next_grid_policy.items()},
            pricing_updates_before=updates_before,
            pricing_updates_after=int(learner.update_counts.sum()),
        ))
    return MultiSlotResult(
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30 * len(summaries)),
        slots=tuple(summaries),
        passenger_trip_energy_status=PASSENGER_TRIP_ENERGY_STATUS,
    )


def run_four_slot_simulation(**kwargs) -> MultiSlotResult:
    """Compatibility wrapper retaining the completed four-slot public API."""
    if "slot_count" in kwargs:
        raise ValueError("run_four_slot_simulation fixes slot_count at four.")
    return run_multi_slot_simulation(slot_count=4, **kwargs)
