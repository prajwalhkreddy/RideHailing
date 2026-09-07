"""Controlled one-slot pricing, customer acceptance, and dispatch integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.dispatch.contention import ContentionEvaluation, DriverContentionInputs
from src.dispatch.dispatch import (
    DISPATCH_MODEL_CONTENTION, DISPATCH_MODEL_LEGACY, DISPATCH_MODELS,
    DriverWaitObservation, dispatch_requests,
)
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.supply import aggregate_grid_supply
from src.pricing.customer import draw_customer_acceptance, offered_fare
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel
from src.pricing.linucb import DisjointLinUCB, PricingDecision
from src.pricing.reward import (
    REQUEST_REWARD_REF, REQUEST_REWARD_SCALING_MODES, REQUEST_REWARD_SCALING_NONE,
    ContextRevenueAccumulator, request_learning_reward, revenue_opportunity_reward,
    slot_accepted_revenue,
)
from src.pricing.request_context import build_request_pricing_context, grid_positions
from src.pricing.scaler import DEFAULT_PRICING_CONTEXT_SCALER
from src.pricing.supply import build_raw_pricing_supply
from src.pricing.state import build_pricing_context


CUSTOMER_MODEL_EQ31 = "eq31"
CUSTOMER_MODEL_HISTORICAL = "historical_sensitivity"
CUSTOMER_RESPONSE_MODELS = (CUSTOMER_MODEL_EQ31, CUSTOMER_MODEL_HISTORICAL)
REWARD_MODEL_LEGACY = "legacy_normalized_accepted_revenue"
REWARD_MODEL_SERVED = "served_dispatch_revenue"
REWARD_MODELS = (REWARD_MODEL_LEGACY, REWARD_MODEL_SERVED)
SUPPLY_MODEL_LEGACY = "legacy_all_statuses"
SUPPLY_MODEL_CORRECTED = "idle_plus_incoming"
SUPPLY_MODELS = (SUPPLY_MODEL_LEGACY, SUPPLY_MODEL_CORRECTED)
PRICING_DECISION_MODE_LEGACY = "legacy_grid"
PRICING_DECISION_MODE_REQUEST = "request_8d"
PRICING_DECISION_MODES = (PRICING_DECISION_MODE_LEGACY, PRICING_DECISION_MODE_REQUEST)


@dataclass(frozen=True)
class PricingContextInput:
    """Externally supplied runtime inputs for one grid pricing context."""

    predicted_demand: float
    routing_probabilities: Sequence[float]
    popularity: float


@dataclass(frozen=True)
class RequestPricingAudit:
    request_id: int
    context_id: int
    request_time: int
    base_fare: float
    pricing_factor: float
    offered_fare: float
    acceptance_probability: float | None
    customer_accepted: bool
    served: bool
    customer_model: str
    weather_code: float | None
    period: int | None
    historical_p_base: float | None
    historical_d_base: float | None
    actual_distance_miles: float | None
    epsilon_customer: float | None
    p_max: float | None
    origin_grid: int
    destination_grid: int
    pricing_context: np.ndarray | None
    selected_arm: int | None
    linucb_reward: float | None
    final_status: str
    sensitivity_lookup_level: str | None
    raw_served_revenue: float | None
    linucb_learning_reward: float | None
    eligible_vehicle_count: int | None
    contender_count: int | None
    selected_vehicle_id: int | None
    selected_vehicle_origin_grid: int | None
    selected_pickup_distance: float | None
    selected_pickup_distance_unit: str | None
    selected_request_utility: float | None
    selected_best_alternative_utility: float | None
    selected_utility_margin: float | None


@dataclass(frozen=True)
class ContextPricingResult:
    decision: PricingDecision
    accepted_revenue: float
    generated: int
    accepted: int
    rejected: int
    served: int
    accepted_but_unserved: int
    served_revenue: float
    reward_model: str
    linucb_reward: float | None
    linucb_updated: bool
    raw_revenue_per_opportunity: float | None
    normalized_reward: float | None
    reward_clipped: bool
    raw_predicted_demand: float
    nonnegative_predicted_demand: float
    scaled_predicted_demand: float
    raw_supply: float
    scaled_supply: float
    supply_model: str
    idle_supply: int | None
    incoming_supply: int | None
    demand_negative_clipped: bool
    demand_upper_clipped: bool
    supply_upper_clipped: bool


@dataclass(frozen=True)
class PricingDispatchSlotResult:
    pricing_by_context: dict[int, ContextPricingResult]
    generated: int
    accepted: int
    rejected: int
    served: int
    accepted_but_unserved: int
    accepted_revenue: float
    served_revenue: float
    reward_model: str
    linucb_updates_performed: int
    request_audit: tuple[RequestPricingAudit, ...]
    driver_wait_observations: tuple[DriverWaitObservation, ...]
    pricing_decision_mode: str
    linucb_selections_performed: int
    linucb_reward_scaling: str
    request_reward_ref: float | None
    raw_request_served_revenue: float | None
    linucb_learning_reward: float | None
    dispatch_model: str


@dataclass(frozen=True)
class PendingRequestPricingDecision:
    request_id: int
    context: np.ndarray
    decision: PricingDecision
    offered_fare: float
    accepted: bool


def _request_audit(request: RequestState) -> RequestPricingAudit:
    return RequestPricingAudit(
        request_id=request.request_id,
        context_id=request.origin_grid,
        request_time=request.request_time,
        base_fare=float(request.base_fare),
        pricing_factor=float(request.pricing_factor),
        offered_fare=float(request.offered_fare),
        acceptance_probability=None if request.acceptance_probability is None else float(request.acceptance_probability),
        customer_accepted=bool(request.customer_accepted),
        served=request.status is RequestStatus.ASSIGNED,
        customer_model=str(request.customer_model),
        weather_code=request.weather_code,
        period=request.period,
        historical_p_base=request.historical_p_base,
        historical_d_base=request.historical_d_base,
        actual_distance_miles=request.trip_distance_miles if request.customer_model == CUSTOMER_MODEL_HISTORICAL else None,
        epsilon_customer=request.epsilon_customer,
        p_max=request.p_max,
        origin_grid=request.origin_grid,
        destination_grid=request.destination_grid,
        pricing_context=None if request.pricing_context is None else np.asarray(request.pricing_context, dtype=np.float64),
        selected_arm=request.selected_arm,
        linucb_reward=request.linucb_reward,
        final_status=request.status.value,
        sensitivity_lookup_level=request.sensitivity_lookup_level,
        raw_served_revenue=request.raw_served_revenue,
        linucb_learning_reward=request.linucb_learning_reward,
        eligible_vehicle_count=request.eligible_vehicle_count,
        contender_count=request.contender_count,
        selected_vehicle_id=request.assigned_vehicle_id,
        selected_vehicle_origin_grid=request.selected_vehicle_origin_grid,
        selected_pickup_distance=request.selected_pickup_distance,
        selected_pickup_distance_unit=request.selected_pickup_distance_unit,
        selected_request_utility=request.selected_request_utility,
        selected_best_alternative_utility=request.selected_best_alternative_utility,
        selected_utility_margin=request.selected_utility_margin,
    )


def _run_request_pricing_dispatch_slot(
    *, items: list[RequestState], context_inputs: Mapping[int, PricingContextInput],
    learner: DisjointLinUCB, fleet: Fleet, neighbour_lookup: Mapping[int, Iterable[int]],
    default_trip_duration_minutes: int, mini_slots_per_main_slot: int,
    acceptance_rng: np.random.Generator, energy_parameters: EnergyParameters | None,
    mini_slot_callback: Callable[[int], None] | None, customer_response_model: str,
    historical_customer_model: HistoricalCustomerSensitivityModel, weather_code: float,
    period: int, simulation_timestamp: datetime, corrected_supply: pd.DataFrame,
    grid_lookup: pd.DataFrame, popularity_table: pd.DataFrame,
    linucb_reward_scaling: str, dispatch_model: str,
    contention_inputs: DriverContentionInputs | None,
    contention_observer: Callable[[ContentionEvaluation], None] | None,
) -> PricingDispatchSlotResult:
    """Select every request first, dispatch accepted requests, then update each once."""
    timestamp = pd.Timestamp(simulation_timestamp)
    derived_period = timestamp.hour * 2 + timestamp.minute // 30
    if period != derived_period:
        raise ValueError("Configured Period must match the request-level pricing timestamp.")
    times = pd.to_datetime(popularity_table.get("TimeSlot"), errors="coerce")
    if len(times) != len(popularity_table) or pd.isna(times).any():
        raise ValueError("Popularity artifact requires valid TimeSlot values.")
    slot_rows = popularity_table.loc[times == timestamp, ["GridID", "popularity_value"]]
    if slot_rows.empty or slot_rows["GridID"].duplicated().any():
        raise ValueError("Request-level pricing requires unique destination popularity for the current slot.")
    popularity_by_destination = dict(zip(slot_rows.GridID.astype(int), slot_rows.popularity_value.astype(float)))
    positions = grid_positions(grid_lookup)
    ordered = sorted(items, key=lambda value: (value.request_time, value.request_id))
    selected: dict[int, tuple[np.ndarray, PricingDecision, object]] = {}
    for request in ordered:
        if request.status is not RequestStatus.PENDING or request.base_fare is None:
            raise ValueError("Request-level pricing accepts only complete PENDING generated requests.")
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
        inputs = context_inputs[request.origin_grid]
        resolved = historical_customer_model.resolve_parameters(float(weather_code), int(period))
        context = build_request_pricing_context(
            request=request, predicted_demand=inputs.predicted_demand,
            corrected_supply=float(corrected_supply.at[request.origin_grid, "total_supply"]),
            routing_probabilities=inputs.routing_probabilities,
            simulation_timestamp=simulation_timestamp, weather_code=weather_code,
            grid_lookup=positions, popularity_table=popularity_by_destination,
            historical_customer_model=historical_customer_model,
            resolved_sensitivity=resolved,
        )
        selected[request.request_id] = (context, learner.select(context), resolved)

    pending: list[PendingRequestPricingDecision] = []
    accepted_requests: list[RequestState] = []
    for request in ordered:
        context, decision, resolved = selected[request.request_id]
        inputs = context_inputs[request.origin_grid]
        if customer_response_model == CUSTOMER_MODEL_EQ31:
            fare = offered_fare(request.base_fare, decision.pricing_factor)
            acceptance = draw_customer_acceptance(
                decision.pricing_factor, float(corrected_supply.at[request.origin_grid, "total_supply"]),
                inputs.predicted_demand, acceptance_rng,
            )
            accepted, probability = acceptance.accepted, acceptance.probability
            request.customer_model = CUSTOMER_MODEL_EQ31
        else:
            if request.trip_distance_miles is None:
                raise ValueError("historical_sensitivity mode requires request trip_distance_miles.")
            historical = historical_customer_model.evaluate_resolved(
                resolved, request.trip_distance_miles, decision.pricing_factor,
            )
            fare, accepted, probability = historical.p_dispatch, historical.accepted, None
            request.customer_model = CUSTOMER_MODEL_HISTORICAL
            request.weather_code, request.period = historical.weather_code, historical.period
            request.historical_p_base, request.historical_d_base = historical.p_base, historical.d_base
            request.epsilon_customer, request.p_max = historical.epsilon_customer, historical.p_max
            request.sensitivity_lookup_level = historical.sensitivity_lookup_level
        request.pricing_factor, request.offered_fare = decision.pricing_factor, fare
        request.acceptance_probability, request.customer_accepted = probability, accepted
        request.pricing_context, request.selected_arm = tuple(context.tolist()), decision.arm_index
        pending.append(PendingRequestPricingDecision(request.request_id, context.copy(), decision, float(fare), bool(accepted)))
        if accepted:
            accepted_requests.append(request)

    driver_wait_observations: list[DriverWaitObservation] = []
    for mini_slot in range(mini_slots_per_main_slot):
        arrivals = [request for request in accepted_requests if request.request_time == mini_slot]
        if arrivals:
            dispatch_requests(
                arrivals, fleet, neighbour_lookup, default_trip_duration_minutes,
                mini_slots_per_main_slot, energy_parameters, driver_wait_observations,
                dispatch_model, contention_inputs,
                contention_observer,
                simulation_timestamp,
            )
        fleet.advance_mini_slot()
        if mini_slot_callback is not None:
            mini_slot_callback(mini_slot)

    by_id = {request.request_id: request for request in ordered}
    for item in pending:
        request = by_id[item.request_id]
        raw_reward = item.offered_fare if item.accepted and request.status is RequestStatus.ASSIGNED else 0.0
        learning_reward = request_learning_reward(raw_reward, linucb_reward_scaling)
        learner.update(item.context, item.decision.arm_index, learning_reward)
        request.raw_served_revenue = raw_reward
        request.linucb_learning_reward = learning_reward
        request.linucb_reward = learning_reward
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
    audits = tuple(_request_audit(request) for request in ordered)
    accepted = sum(audit.customer_accepted for audit in audits)
    served = sum(audit.served for audit in audits)
    accepted_revenue = float(sum(audit.offered_fare for audit in audits if audit.customer_accepted))
    served_revenue = float(sum(audit.offered_fare for audit in audits if audit.served))
    result = PricingDispatchSlotResult(
        pricing_by_context={}, generated=len(audits), accepted=accepted,
        rejected=len(audits) - accepted, served=served,
        accepted_but_unserved=accepted - served, accepted_revenue=accepted_revenue,
        served_revenue=served_revenue, reward_model=REWARD_MODEL_SERVED,
        linucb_updates_performed=len(pending), request_audit=audits,
        driver_wait_observations=tuple(driver_wait_observations),
        pricing_decision_mode=PRICING_DECISION_MODE_REQUEST,
        linucb_selections_performed=len(selected),
        linucb_reward_scaling=linucb_reward_scaling,
        request_reward_ref=REQUEST_REWARD_REF if linucb_reward_scaling != REQUEST_REWARD_SCALING_NONE else None,
        raw_request_served_revenue=served_revenue,
        linucb_learning_reward=float(sum(float(a.linucb_learning_reward) for a in audits)),
        dispatch_model=dispatch_model,
    )
    if result.generated != result.linucb_selections_performed or result.generated != result.linucb_updates_performed:
        raise ValueError("Every request-level selection must receive exactly one final update.")
    if not np.isclose(sum(float(a.raw_served_revenue) for a in audits), result.served_revenue):
        raise ValueError("Raw request rewards must equal served P_dispatch revenue exactly.")
    expected_learning = request_learning_reward(result.served_revenue, linucb_reward_scaling)
    if not np.isclose(sum(float(a.linucb_learning_reward) for a in audits), expected_learning):
        raise ValueError("Request learning rewards do not reconcile with the configured linear scale.")
    return result


def run_pricing_dispatch_slot(
    requests: Iterable[RequestState],
    context_inputs: Mapping[int, PricingContextInput],
    learner: DisjointLinUCB,
    fleet: Fleet,
    neighbour_lookup: Mapping[int, Iterable[int]],
    default_trip_duration_minutes: int,
    mini_slots_per_main_slot: int,
    acceptance_rng: np.random.Generator,
    energy_parameters: EnergyParameters | None = None,
    mini_slot_callback: Callable[[int], None] | None = None,
    customer_response_model: str = CUSTOMER_MODEL_EQ31,
    historical_customer_model: HistoricalCustomerSensitivityModel | None = None,
    weather_code: float | None = None,
    period: int | None = None,
    simulation_timestamp: datetime | None = None,
    reward_model: str = REWARD_MODEL_LEGACY,
    supply_model: str = SUPPLY_MODEL_LEGACY,
    pricing_decision_mode: str = PRICING_DECISION_MODE_LEGACY,
    grid_lookup: pd.DataFrame | None = None,
    popularity_table: pd.DataFrame | None = None,
    sensitivity_fallback: str = "error",
    linucb_reward_scaling: str = REQUEST_REWARD_SCALING_NONE,
    dispatch_model: str = DISPATCH_MODEL_LEGACY,
    contention_inputs: DriverContentionInputs | None = None,
    contention_observer: Callable[[ContentionEvaluation], None] | None = None,
) -> PricingDispatchSlotResult:
    """Run exactly one main slot, selecting once and updating at slot end.

    Every supplied context is active and receives a decision. It receives an
    update only when at least one request creates a pricing opportunity. An
    empty ``context_inputs`` mapping creates neither a decision nor an update.
    """
    if not isinstance(acceptance_rng, np.random.Generator):
        raise ValueError("acceptance_rng must be an explicit numpy.random.Generator.")
    if customer_response_model not in CUSTOMER_RESPONSE_MODELS:
        raise ValueError(f"customer_response_model must be one of {CUSTOMER_RESPONSE_MODELS}.")
    if reward_model not in REWARD_MODELS:
        raise ValueError(f"reward_model must be one of {REWARD_MODELS}.")
    if supply_model not in SUPPLY_MODELS:
        raise ValueError(f"supply_model must be one of {SUPPLY_MODELS}.")
    if pricing_decision_mode not in PRICING_DECISION_MODES:
        raise ValueError(f"pricing_decision_mode must be one of {PRICING_DECISION_MODES}.")
    if sensitivity_fallback not in {"error", "hierarchical"}:
        raise ValueError("sensitivity_fallback must be error or hierarchical.")
    if linucb_reward_scaling not in REQUEST_REWARD_SCALING_MODES:
        raise ValueError(f"linucb_reward_scaling must be one of {REQUEST_REWARD_SCALING_MODES}.")
    if dispatch_model not in DISPATCH_MODELS:
        raise ValueError(f"dispatch_model must be one of {DISPATCH_MODELS}.")
    if dispatch_model == DISPATCH_MODEL_CONTENTION and contention_inputs is None:
        raise ValueError("driver_contention requires explicit current NB11 contention inputs.")
    if pricing_decision_mode != PRICING_DECISION_MODE_REQUEST and linucb_reward_scaling != REQUEST_REWARD_SCALING_NONE:
        raise ValueError("LinUCB request reward scaling applies only to request_8d pricing.")
    if pricing_decision_mode != PRICING_DECISION_MODE_REQUEST and dispatch_model != DISPATCH_MODEL_LEGACY:
        raise ValueError("driver_contention dispatch applies only to request_8d pricing.")
    if pricing_decision_mode == PRICING_DECISION_MODE_REQUEST:
        if supply_model != SUPPLY_MODEL_CORRECTED:
            raise ValueError("request_8d pricing requires supply_model=idle_plus_incoming.")
        if reward_model != REWARD_MODEL_SERVED:
            raise ValueError("request_8d pricing requires reward_model=served_dispatch_revenue.")
        if historical_customer_model is None or grid_lookup is None or popularity_table is None:
            raise ValueError("request_8d pricing requires sensitivity, grid, and popularity artifacts.")
        if weather_code is None or period is None or simulation_timestamp is None:
            raise ValueError("request_8d pricing requires WeatherCode, Period, and simulation timestamp.")
        if not {"TimeSlot", "GridID", "popularity_value"}.issubset(popularity_table.columns):
            raise ValueError("request_8d pricing requires the frozen destination-popularity schema.")
        if historical_customer_model.fallback_mode != sensitivity_fallback:
            raise ValueError("Configured sensitivity_fallback must match the initialized customer model.")
    if supply_model == SUPPLY_MODEL_CORRECTED and simulation_timestamp is None:
        raise ValueError("idle_plus_incoming supply requires the pricing decision timestamp.")
    if customer_response_model == CUSTOMER_MODEL_HISTORICAL:
        if historical_customer_model is None:
            raise ValueError("historical_sensitivity mode requires one initialized historical customer model.")
        if weather_code is None or period is None or simulation_timestamp is None:
            raise ValueError("historical_sensitivity mode requires WeatherCode, Period, and simulation timestamp.")
    if not isinstance(mini_slots_per_main_slot, int) or mini_slots_per_main_slot <= 0:
        raise ValueError("mini_slots_per_main_slot must be positive.")

    items = list(requests)
    if len({request.request_id for request in items}) != len(items):
        raise ValueError("Request IDs must be unique within a slot.")
    unknown_contexts = {request.origin_grid for request in items} - set(context_inputs)
    if unknown_contexts:
        raise ValueError(f"Requests lack active pricing contexts: {sorted(unknown_contexts)}")

    fleet_supply = aggregate_grid_supply(fleet.vehicles, fleet.valid_grid_ids).set_index("grid_id")
    corrected_supply = None
    if supply_model == SUPPLY_MODEL_CORRECTED:
        corrected_supply = build_raw_pricing_supply(
            fleet.vehicles, fleet.valid_grid_ids, simulation_timestamp,
            main_slot_minutes=mini_slots_per_main_slot * fleet.mini_slot_minutes,
        ).set_index("grid_id")
    if pricing_decision_mode == PRICING_DECISION_MODE_REQUEST:
        return _run_request_pricing_dispatch_slot(
            items=items, context_inputs=context_inputs, learner=learner, fleet=fleet,
            neighbour_lookup=neighbour_lookup,
            default_trip_duration_minutes=default_trip_duration_minutes,
            mini_slots_per_main_slot=mini_slots_per_main_slot, acceptance_rng=acceptance_rng,
            energy_parameters=energy_parameters, mini_slot_callback=mini_slot_callback,
            customer_response_model=customer_response_model,
            historical_customer_model=historical_customer_model, weather_code=float(weather_code),
            period=int(period), simulation_timestamp=simulation_timestamp,
            corrected_supply=corrected_supply, grid_lookup=grid_lookup, popularity_table=popularity_table,
            linucb_reward_scaling=linucb_reward_scaling,
            dispatch_model=dispatch_model, contention_inputs=contention_inputs,
            contention_observer=contention_observer,
        )
    decisions: dict[int, PricingDecision] = {}
    accumulators: dict[int, ContextRevenueAccumulator] = {}
    for context_id, inputs in sorted(context_inputs.items()):
        if context_id not in fleet.valid_grid_ids:
            raise ValueError(f"Pricing context {context_id} is not a canonical GridID.")
        context = build_pricing_context(
            inputs.predicted_demand,
            float(
                fleet_supply.at[context_id, "supply_total"]
                if corrected_supply is None else corrected_supply.at[context_id, "total_supply"]
            ),
            inputs.routing_probabilities,
            inputs.popularity,
        )
        decisions[context_id] = learner.select(context)
        accumulators[context_id] = ContextRevenueAccumulator()

    accepted_requests: list[RequestState] = []
    for request in sorted(items, key=lambda value: (value.request_time, value.request_id)):
        if request.status is not RequestStatus.PENDING:
            raise ValueError("Integrated slot accepts only PENDING generated requests.")
        if request.base_fare is None:
            raise ValueError("Every integrated request must provide its existing base_fare.")
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
        context_id = request.origin_grid
        decision = decisions[context_id]
        context_input = context_inputs[context_id]
        if customer_response_model == CUSTOMER_MODEL_EQ31:
            fare = offered_fare(request.base_fare, decision.pricing_factor)
            acceptance = draw_customer_acceptance(
                decision.pricing_factor,
                float(fleet_supply.at[context_id, "supply_total"]),
                context_input.predicted_demand,
                acceptance_rng,
            )
            accepted, probability = acceptance.accepted, acceptance.probability
            request.customer_model = CUSTOMER_MODEL_EQ31
        else:
            if request.trip_distance_miles is None:
                raise ValueError("historical_sensitivity mode requires request trip_distance_miles.")
            try:
                historical = historical_customer_model.evaluate(  # type: ignore[union-attr]
                    float(weather_code), int(period), request.trip_distance_miles,
                    decision.pricing_factor,
                )
            except KeyError as error:
                raise KeyError(
                    f"Missing historical sensitivity group: WeatherCode={weather_code}, "
                    f"Period={period}, simulation_timestamp={simulation_timestamp.isoformat()}."
                ) from error
            fare, accepted, probability = historical.p_dispatch, historical.accepted, None
            request.customer_model = CUSTOMER_MODEL_HISTORICAL
            request.weather_code = historical.weather_code
            request.period = historical.period
            request.historical_p_base = historical.p_base
            request.historical_d_base = historical.d_base
            request.epsilon_customer = historical.epsilon_customer
            request.p_max = historical.p_max
        request.pricing_factor = decision.pricing_factor
        request.offered_fare = fare
        request.acceptance_probability = probability
        request.customer_accepted = accepted
        accumulators[context_id].add(fare, accepted)
        if accepted:
            accepted_requests.append(request)

    driver_wait_observations: list[DriverWaitObservation] = []
    for mini_slot in range(mini_slots_per_main_slot):
        arrivals = [request for request in accepted_requests if request.request_time == mini_slot]
        if arrivals:
            dispatch_requests(
                arrivals, fleet, neighbour_lookup, default_trip_duration_minutes,
                mini_slots_per_main_slot, energy_parameters,
                driver_wait_observations,
                slot_start_time=simulation_timestamp,
            )
        fleet.advance_mini_slot()
        if mini_slot_callback is not None:
            mini_slot_callback(mini_slot)

    context_results: dict[int, ContextPricingResult] = {}
    for context_id, decision in decisions.items():
        accumulator = accumulators[context_id]
        raw_context_supply = float(
            fleet_supply.at[context_id, "supply_total"]
            if corrected_supply is None else corrected_supply.at[context_id, "total_supply"]
        )
        served_requests = [
            request for request in items
            if request.origin_grid == context_id and request.status is RequestStatus.ASSIGNED
        ]
        context_served_revenue = float(sum(float(request.offered_fare) for request in served_requests))
        legacy_reward = None
        linucb_reward = None
        if accumulator.request_count > 0:
            if reward_model == REWARD_MODEL_LEGACY:
                legacy_reward = revenue_opportunity_reward(accumulator.accepted_revenue, accumulator.request_count)
                linucb_reward = legacy_reward.normalized_reward
            else:
                linucb_reward = context_served_revenue
            learner.update(decision.context, decision.arm_index, linucb_reward)
        else:
            learner.discard_pending_observation(decision.arm_index)
        context_rejected = accumulator.request_count - accumulator.accepted_count
        context_accepted_unserved = accumulator.accepted_count - len(served_requests)
        context_results[context_id] = ContextPricingResult(
            decision=decision,
            accepted_revenue=accumulator.accepted_revenue,
            generated=accumulator.request_count,
            accepted=accumulator.accepted_count,
            rejected=context_rejected,
            served=len(served_requests),
            accepted_but_unserved=context_accepted_unserved,
            served_revenue=context_served_revenue,
            reward_model=reward_model,
            linucb_reward=linucb_reward,
            linucb_updated=linucb_reward is not None,
            raw_revenue_per_opportunity=None if legacy_reward is None else legacy_reward.raw_revenue_per_opportunity,
            normalized_reward=None if legacy_reward is None else legacy_reward.normalized_reward,
            reward_clipped=False if legacy_reward is None else legacy_reward.clipped,
            raw_predicted_demand=float(context_inputs[context_id].predicted_demand),
            nonnegative_predicted_demand=max(0.0, float(context_inputs[context_id].predicted_demand)),
            scaled_predicted_demand=float(decision.context[0]),
            raw_supply=raw_context_supply,
            scaled_supply=float(decision.context[1]),
            supply_model=supply_model,
            idle_supply=None if corrected_supply is None else int(corrected_supply.at[context_id, "idle_supply"]),
            incoming_supply=None if corrected_supply is None else int(corrected_supply.at[context_id, "incoming_supply"]),
            demand_negative_clipped=float(context_inputs[context_id].predicted_demand) < 0.0,
            demand_upper_clipped=float(context_inputs[context_id].predicted_demand) > DEFAULT_PRICING_CONTEXT_SCALER.demand_ref_p99,
            supply_upper_clipped=raw_context_supply > DEFAULT_PRICING_CONTEXT_SCALER.supply_ref_p99,
        )

    audits = tuple(_request_audit(request) for request in sorted(items, key=lambda value: (value.request_time, value.request_id)))
    accepted = sum(audit.customer_accepted for audit in audits)
    served = sum(audit.served for audit in audits)
    accepted_revenue = slot_accepted_revenue(result.accepted_revenue for result in context_results.values())
    served_revenue = float(sum(audit.offered_fare for audit in audits if audit.served))
    result = PricingDispatchSlotResult(
        pricing_by_context=context_results,
        generated=len(audits),
        accepted=accepted,
        rejected=len(audits) - accepted,
        served=served,
        accepted_but_unserved=accepted - served,
        accepted_revenue=accepted_revenue,
        served_revenue=served_revenue,
        reward_model=reward_model,
        linucb_updates_performed=sum(result.linucb_updated for result in context_results.values()),
        request_audit=audits,
        driver_wait_observations=tuple(driver_wait_observations),
        pricing_decision_mode=PRICING_DECISION_MODE_LEGACY,
        linucb_selections_performed=len(decisions),
        linucb_reward_scaling=REQUEST_REWARD_SCALING_NONE,
        request_reward_ref=None,
        raw_request_served_revenue=None,
        linucb_learning_reward=None,
        dispatch_model=DISPATCH_MODEL_LEGACY,
    )
    if result.generated != result.accepted + result.rejected:
        raise ValueError("Generated request counts do not reconcile.")
    if result.accepted != result.served + result.accepted_but_unserved:
        raise ValueError("Accepted request counts do not reconcile.")
    if not np.isclose(result.accepted_revenue, sum(a.offered_fare for a in audits if a.customer_accepted)):
        raise ValueError("Accepted revenue does not reconcile with request audit.")
    if result.served_revenue > result.accepted_revenue and not np.isclose(result.served_revenue, result.accepted_revenue):
        raise ValueError("Served revenue cannot exceed accepted revenue.")
    return result
