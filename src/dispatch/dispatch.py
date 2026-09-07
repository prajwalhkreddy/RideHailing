"""Deterministic FCFS baseline dispatch over canonical local supply."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Collection, Iterable, Mapping

from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleStatus
from src.charging.energy import EnergyParameters, deduct_passenger_trip_energy, energy_consumed_kwh, requires_charging
from src.dispatch.contention import ContentionEvaluation, DriverContentionInputs, evaluate_request_contention


DISPATCH_MODEL_LEGACY = "legacy_fcfs_lowest_id"
DISPATCH_MODEL_CONTENTION = "driver_contention"
DISPATCH_MODELS = (DISPATCH_MODEL_LEGACY, DISPATCH_MODEL_CONTENTION)


PASSENGER_ENERGY_FEASIBILITY = "existing_check"


@dataclass(frozen=True)
class DriverWaitObservation:
    """One driver-idle episode completed by a dispatch."""

    vehicle_id: int
    grid_id: int
    wait_minutes: float
    idle_start_time: datetime | None = None
    dispatch_time: datetime | None = None


def build_neighbour_lookup(neighbour_map, valid_grid_ids: Collection[int]) -> dict[int, tuple[int, ...]]:
    """Load the frozen direct-neighbour artifact without redefining adjacency."""
    required = {"GridID", "NeighbourGridID"}
    if missing := required - set(neighbour_map.columns):
        raise ValueError(f"Neighbour artifact lacks columns: {sorted(missing)}")
    valid = set(valid_grid_ids)
    lookup: dict[int, tuple[int, ...]] = {}
    for grid_id in valid:
        values = neighbour_map.loc[neighbour_map["GridID"] == grid_id, "NeighbourGridID"].astype(int).tolist()
        if not set(values).issubset(valid):
            raise ValueError("Neighbour artifact contains invalid GridIDs.")
        lookup[grid_id] = tuple(sorted(set(values)))
    return lookup


def find_eligible_vehicle(request: RequestState, fleet: Fleet, neighbour_lookup: Mapping[int, Iterable[int]], energy_parameters: EnergyParameters | None = None):
    """Find lowest-ID idle supply: same grid, then direct neighbours only."""
    required_energy = None if energy_parameters is None or request.trip_distance_km is None else energy_consumed_kwh(request.trip_distance_km, energy_parameters)
    eligible = lambda vehicle: vehicle.trip_status is VehicleStatus.IDLE and (energy_parameters is None or (not requires_charging(vehicle, energy_parameters) and (required_energy is None or vehicle.energy_level >= required_energy)))
    same_grid = [vehicle for vehicle in fleet.vehicles if eligible(vehicle) and vehicle.current_grid == request.origin_grid]
    if same_grid:
        return min(same_grid, key=lambda vehicle: vehicle.vehicle_id)
    neighbours = set(neighbour_lookup.get(request.origin_grid, ()))
    neighbouring = [vehicle for vehicle in fleet.vehicles if eligible(vehicle) and vehicle.current_grid in neighbours]
    return min(neighbouring, key=lambda vehicle: vehicle.vehicle_id) if neighbouring else None


def eligible_local_vehicles(
    request: RequestState, fleet: Fleet, neighbour_lookup: Mapping[int, Iterable[int]],
    energy_parameters: EnergyParameters, vehicles_by_grid: Mapping[int, Iterable] | None = None,
):
    """Return all feasible IDLE vehicles in the origin/direct-neighbour pool."""
    required_energy = None if request.trip_distance_km is None else energy_consumed_kwh(request.trip_distance_km, energy_parameters)
    candidate_grids = {request.origin_grid, *(int(value) for value in neighbour_lookup.get(request.origin_grid, ()))}
    source = fleet.vehicles if vehicles_by_grid is None else (
        vehicle for grid in candidate_grids for vehicle in vehicles_by_grid.get(grid, ())
    )
    return [
        vehicle for vehicle in source
        if vehicle.current_grid in candidate_grids
        and vehicle.trip_status is VehicleStatus.IDLE
        and vehicle.current_action not in {"charging", "charging_queue"}
        and not requires_charging(vehicle, energy_parameters)
        and (required_energy is None or vehicle.energy_level >= required_energy)
    ]


def dispatch_requests(
    requests: Iterable[RequestState],
    fleet: Fleet,
    neighbour_lookup: Mapping[int, Iterable[int]],
    default_trip_duration_minutes: int,
    mini_slots_per_main_slot: int,
    energy_parameters: EnergyParameters | None = None,
    driver_wait_observations: list[DriverWaitObservation] | None = None,
    dispatch_model: str = DISPATCH_MODEL_LEGACY,
    contention_inputs: DriverContentionInputs | None = None,
    contention_observer: Callable[[ContentionEvaluation], None] | None = None,
    slot_start_time: datetime | None = None,
) -> dict[str, int]:
    """Immediately process PENDING requests in FCFS mini-slot/request-ID order.

    This is the approved engineering baseline.  Search failures are terminal
    UNSERVED results; no multi-mini-slot persistence or queue is introduced.
    """
    if isinstance(default_trip_duration_minutes, bool) or not isinstance(default_trip_duration_minutes, (int, float)) or default_trip_duration_minutes <= 0:
        raise ValueError("default_trip_duration_minutes must be a positive compatibility fallback.")
    if dispatch_model not in DISPATCH_MODELS:
        raise ValueError(f"dispatch_model must be one of {DISPATCH_MODELS}.")
    if dispatch_model == DISPATCH_MODEL_CONTENTION and contention_inputs is None:
        raise ValueError("driver_contention dispatch requires explicit current NB11 contention inputs.")
    ordered = sorted(requests, key=lambda request: (request.request_time, request.request_id))
    vehicles_by_grid: dict[int, list] = defaultdict(list)
    if dispatch_model == DISPATCH_MODEL_CONTENTION:
        for vehicle in fleet.vehicles:
            vehicles_by_grid[vehicle.current_grid].append(vehicle)
    if len({request.request_id for request in ordered}) != len(ordered):
        raise ValueError("Request IDs must be unique within a dispatch batch.")
    for request in ordered:
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
        if request.status is not RequestStatus.PENDING:
            raise ValueError("Dispatch accepts only PENDING requests.")
        selected_evaluation = None
        if dispatch_model == DISPATCH_MODEL_LEGACY:
            vehicle = find_eligible_vehicle(request, fleet, neighbour_lookup, energy_parameters)
        else:
            assert contention_inputs is not None
            candidates = eligible_local_vehicles(
                request, fleet, neighbour_lookup, contention_inputs.energy_parameters, vehicles_by_grid,
            )
            request.eligible_vehicle_count = len(candidates)
            evaluations = [
                evaluate_request_contention(
                    vehicle=candidate, request=request,
                    routing_features=contention_inputs.routing_features,
                    directional_neighbour_map=contention_inputs.directional_neighbour_map,
                    alternative_inputs=contention_inputs.utility_inputs_by_vehicle[candidate.vehicle_id],
                    energy=contention_inputs.energy_parameters,
                    centroids=contention_inputs.centroids,
                    pickup_reference=contention_inputs.pickup_distance_ref,
                )
                for candidate in candidates
            ]
            if contention_observer is not None:
                for evaluation in evaluations:
                    contention_observer(evaluation)
            contenders = [evaluation for evaluation in evaluations if evaluation.contends]
            request.contender_count = len(contenders)
            selected_evaluation = min(
                contenders,
                key=lambda value: (value.pickup_distance, -value.request_utility, value.vehicle_id),
                default=None,
            )
            vehicle = None if selected_evaluation is None else fleet.vehicle(selected_evaluation.vehicle_id)
        if vehicle is None:
            request.status = RequestStatus.UNSERVED
        else:
            if vehicle.idle_wait_grid is None:
                raise ValueError("Selected IDLE vehicle lacks an active driver-wait episode.")
            completed_wait = DriverWaitObservation(
                vehicle.vehicle_id, vehicle.idle_wait_grid, float(vehicle.idle_wait_minutes),
                None if slot_start_time is None else slot_start_time + timedelta(minutes=request.request_time * fleet.mini_slot_minutes) - timedelta(minutes=vehicle.idle_wait_minutes),
                None if slot_start_time is None else slot_start_time + timedelta(minutes=request.request_time * fleet.mini_slot_minutes),
            )
            duration = request.trip_duration_minutes if request.trip_duration_minutes is not None else float(default_trip_duration_minutes)
            energy_before = vehicle.energy_level
            consumed = None
            if energy_parameters is not None and request.trip_distance_km is not None:
                consumed = deduct_passenger_trip_energy(vehicle, request.trip_distance_km, energy_parameters)
            fleet.assign_busy(vehicle.vehicle_id, request.destination_grid, duration)
            if driver_wait_observations is not None:
                driver_wait_observations.append(completed_wait)
            request.status = RequestStatus.ASSIGNED
            request.assigned_vehicle_id = vehicle.vehicle_id
            request.assigned_vehicle_origin_grid = vehicle.current_grid
            if selected_evaluation is not None:
                request.selected_vehicle_origin_grid = selected_evaluation.vehicle_origin_grid
                request.selected_pickup_distance = selected_evaluation.pickup_distance
                request.selected_pickup_distance_unit = selected_evaluation.pickup_distance_unit
                request.selected_request_utility = selected_evaluation.request_utility
                request.selected_best_alternative_utility = selected_evaluation.best_alternative_utility
                request.selected_utility_margin = selected_evaluation.utility_margin
            request.wait_time = 0
            if request.trip_duration_minutes is not None:
                request.trip_start_minute = float(request.request_time * fleet.mini_slot_minutes)
                request.busy_until_minute = request.trip_start_minute + duration
            if consumed is not None:
                request.passenger_energy_kwh = consumed
                request.passenger_energy_before_kwh = energy_before
                request.passenger_energy_after_kwh = vehicle.energy_level
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
    summary = request_summary(ordered)
    if summary["requests_total"] != summary["requests_served"] + summary["requests_unserved"]:
        raise ValueError("Request dispatch counts do not reconcile.")
    return summary


def request_summary(requests: Iterable[RequestState]) -> dict[str, int]:
    """Return the NB8 baseline total/served/unserved reconciliation counts."""
    items = list(requests)
    served = sum(request.status is RequestStatus.ASSIGNED for request in items)
    unserved = sum(request.status is RequestStatus.UNSERVED for request in items)
    pending = sum(request.status is RequestStatus.PENDING for request in items)
    if pending:
        raise ValueError("Request summary requires all requests to be resolved.")
    return {"requests_total": len(items), "requests_served": served, "requests_unserved": unserved}
