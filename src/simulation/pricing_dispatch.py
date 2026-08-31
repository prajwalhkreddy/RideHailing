"""Controlled one-slot pricing, customer acceptance, and dispatch integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np

from src.charging.energy import EnergyParameters
from src.dispatch.dispatch import DriverWaitObservation, dispatch_requests
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.supply import aggregate_grid_supply
from src.pricing.customer import draw_customer_acceptance, offered_fare
from src.pricing.linucb import DisjointLinUCB, PricingDecision
from src.pricing.reward import ContextRevenueAccumulator, revenue_opportunity_reward, slot_accepted_revenue
from src.pricing.scaler import DEFAULT_PRICING_CONTEXT_SCALER
from src.pricing.state import build_pricing_context


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
    acceptance_probability: float
    customer_accepted: bool
    served: bool


@dataclass(frozen=True)
class ContextPricingResult:
    decision: PricingDecision
    accepted_revenue: float
    generated: int
    accepted: int
    linucb_updated: bool
    raw_revenue_per_opportunity: float | None
    normalized_reward: float | None
    reward_clipped: bool
    raw_predicted_demand: float
    nonnegative_predicted_demand: float
    scaled_predicted_demand: float
    raw_supply: float
    scaled_supply: float
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
    linucb_updates_performed: int
    request_audit: tuple[RequestPricingAudit, ...]
    driver_wait_observations: tuple[DriverWaitObservation, ...]


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
) -> PricingDispatchSlotResult:
    """Run exactly one main slot, selecting once and updating at slot end.

    Every supplied context is active and receives a decision. It receives an
    update only when at least one request creates a pricing opportunity. An
    empty ``context_inputs`` mapping creates neither a decision nor an update.
    """
    if not isinstance(acceptance_rng, np.random.Generator):
        raise ValueError("acceptance_rng must be an explicit numpy.random.Generator.")
    if not isinstance(mini_slots_per_main_slot, int) or mini_slots_per_main_slot <= 0:
        raise ValueError("mini_slots_per_main_slot must be positive.")

    items = list(requests)
    if len({request.request_id for request in items}) != len(items):
        raise ValueError("Request IDs must be unique within a slot.")
    unknown_contexts = {request.origin_grid for request in items} - set(context_inputs)
    if unknown_contexts:
        raise ValueError(f"Requests lack active pricing contexts: {sorted(unknown_contexts)}")

    supply = aggregate_grid_supply(fleet.vehicles, fleet.valid_grid_ids).set_index("grid_id")
    decisions: dict[int, PricingDecision] = {}
    accumulators: dict[int, ContextRevenueAccumulator] = {}
    for context_id, inputs in sorted(context_inputs.items()):
        if context_id not in fleet.valid_grid_ids:
            raise ValueError(f"Pricing context {context_id} is not a canonical GridID.")
        context = build_pricing_context(
            inputs.predicted_demand,
            float(supply.at[context_id, "supply_total"]),
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
        fare = offered_fare(request.base_fare, decision.pricing_factor)
        acceptance = draw_customer_acceptance(
            decision.pricing_factor,
            float(supply.at[context_id, "supply_total"]),
            context_input.predicted_demand,
            acceptance_rng,
        )
        request.pricing_factor = decision.pricing_factor
        request.offered_fare = fare
        request.acceptance_probability = acceptance.probability
        request.customer_accepted = acceptance.accepted
        accumulators[context_id].add(fare, acceptance.accepted)
        if acceptance.accepted:
            accepted_requests.append(request)

    driver_wait_observations: list[DriverWaitObservation] = []
    for mini_slot in range(mini_slots_per_main_slot):
        arrivals = [request for request in accepted_requests if request.request_time == mini_slot]
        if arrivals:
            dispatch_requests(
                arrivals, fleet, neighbour_lookup, default_trip_duration_minutes,
                mini_slots_per_main_slot, energy_parameters,
                driver_wait_observations,
            )
        fleet.advance_mini_slot()
        if mini_slot_callback is not None:
            mini_slot_callback(mini_slot)

    context_results: dict[int, ContextPricingResult] = {}
    for context_id, decision in decisions.items():
        accumulator = accumulators[context_id]
        reward = None
        if accumulator.request_count > 0:
            reward = revenue_opportunity_reward(accumulator.accepted_revenue, accumulator.request_count)
            learner.update(decision.context, decision.arm_index, reward.normalized_reward)
        else:
            learner.discard_pending_observation(decision.arm_index)
        context_results[context_id] = ContextPricingResult(
            decision=decision,
            accepted_revenue=accumulator.accepted_revenue,
            generated=accumulator.request_count,
            accepted=accumulator.accepted_count,
            linucb_updated=reward is not None,
            raw_revenue_per_opportunity=None if reward is None else reward.raw_revenue_per_opportunity,
            normalized_reward=None if reward is None else reward.normalized_reward,
            reward_clipped=False if reward is None else reward.clipped,
            raw_predicted_demand=float(context_inputs[context_id].predicted_demand),
            nonnegative_predicted_demand=max(0.0, float(context_inputs[context_id].predicted_demand)),
            scaled_predicted_demand=float(decision.context[0]),
            raw_supply=float(supply.at[context_id, "supply_total"]),
            scaled_supply=float(decision.context[1]),
            demand_negative_clipped=float(context_inputs[context_id].predicted_demand) < 0.0,
            demand_upper_clipped=float(context_inputs[context_id].predicted_demand) > DEFAULT_PRICING_CONTEXT_SCALER.demand_ref_p99,
            supply_upper_clipped=float(supply.at[context_id, "supply_total"]) > DEFAULT_PRICING_CONTEXT_SCALER.supply_ref_p99,
        )

    audits = tuple(
        RequestPricingAudit(
            request_id=request.request_id,
            context_id=request.origin_grid,
            request_time=request.request_time,
            base_fare=float(request.base_fare),
            pricing_factor=float(request.pricing_factor),
            offered_fare=float(request.offered_fare),
            acceptance_probability=float(request.acceptance_probability),
            customer_accepted=bool(request.customer_accepted),
            served=request.status is RequestStatus.ASSIGNED,
        )
        for request in sorted(items, key=lambda value: (value.request_time, value.request_id))
    )
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
        linucb_updates_performed=sum(result.linucb_updated for result in context_results.values()),
        request_audit=audits,
        driver_wait_observations=tuple(driver_wait_observations),
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
