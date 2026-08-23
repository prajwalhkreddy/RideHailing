"""Deterministic FCFS baseline dispatch over canonical local supply."""

from __future__ import annotations

from collections import defaultdict
from typing import Collection, Iterable, Mapping

from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleStatus
from src.charging.energy import EnergyParameters, requires_charging


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
    eligible = lambda vehicle: vehicle.trip_status is VehicleStatus.IDLE and (energy_parameters is None or not requires_charging(vehicle, energy_parameters))
    same_grid = [vehicle for vehicle in fleet.vehicles if eligible(vehicle) and vehicle.current_grid == request.origin_grid]
    if same_grid:
        return min(same_grid, key=lambda vehicle: vehicle.vehicle_id)
    neighbours = set(neighbour_lookup.get(request.origin_grid, ()))
    neighbouring = [vehicle for vehicle in fleet.vehicles if eligible(vehicle) and vehicle.current_grid in neighbours]
    return min(neighbouring, key=lambda vehicle: vehicle.vehicle_id) if neighbouring else None


def dispatch_requests(
    requests: Iterable[RequestState],
    fleet: Fleet,
    neighbour_lookup: Mapping[int, Iterable[int]],
    default_trip_duration_minutes: int,
    mini_slots_per_main_slot: int,
    energy_parameters: EnergyParameters | None = None,
) -> dict[str, int]:
    """Immediately process PENDING requests in FCFS mini-slot/request-ID order.

    This is the approved engineering baseline.  Search failures are terminal
    UNSERVED results; no multi-mini-slot persistence or queue is introduced.
    """
    if not isinstance(default_trip_duration_minutes, int) or default_trip_duration_minutes <= 0:
        raise ValueError("default_trip_duration_minutes must be a positive integer placeholder.")
    ordered = sorted(requests, key=lambda request: (request.request_time, request.request_id))
    if len({request.request_id for request in ordered}) != len(ordered):
        raise ValueError("Request IDs must be unique within a dispatch batch.")
    for request in ordered:
        request.validate(fleet.valid_grid_ids, mini_slots_per_main_slot)
        if request.status is not RequestStatus.PENDING:
            raise ValueError("Dispatch accepts only PENDING requests.")
        vehicle = find_eligible_vehicle(request, fleet, neighbour_lookup, energy_parameters)
        if vehicle is None:
            request.status = RequestStatus.UNSERVED
        else:
            fleet.assign_busy(vehicle.vehicle_id, request.destination_grid, default_trip_duration_minutes)
            request.status = RequestStatus.ASSIGNED
            request.assigned_vehicle_id = vehicle.vehicle_id
            request.wait_time = 0
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
