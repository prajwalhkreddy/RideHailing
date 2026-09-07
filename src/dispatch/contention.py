"""Final request-specific driver contention using the approved NB11 utility."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Iterable, Mapping

import pandas as pd

from src.charging.energy import EnergyParameters, energy_consumed_kwh
from src.dispatch.request import RequestState
from src.fleet.state import VehicleState

if TYPE_CHECKING:
    from src.routing.baseline import CandidateUtilityInput, GridRoutingFeatures, RoutingAction


@dataclass(frozen=True)
class ContentionEvaluation:
    vehicle_id: int
    vehicle_origin_grid: int
    pickup_distance: float
    pickup_distance_unit: str
    pickup_wait_preference: float
    normalized_trip_energy_burden: float
    request_utility: float
    best_alternative_utility: float
    contends: bool

    @property
    def utility_margin(self) -> float:
        return self.request_utility - self.best_alternative_utility


@dataclass(frozen=True)
class DriverContentionInputs:
    routing_features: Mapping[int, GridRoutingFeatures]
    directional_neighbour_map: pd.DataFrame
    utility_inputs_by_vehicle: Mapping[int, Mapping[RoutingAction | str, CandidateUtilityInput]]
    energy_parameters: EnergyParameters
    centroids: Mapping[int, tuple[float, float]]
    pickup_distance_ref: float
    pickup_distance_unit: str = "EPSG:2263 feet"

    @classmethod
    def from_grid_geometry(
        cls, *, routing_features: Mapping[int, GridRoutingFeatures],
        directional_neighbour_map: pd.DataFrame,
        utility_inputs_by_vehicle: Mapping[int, Mapping[RoutingAction | str, CandidateUtilityInput]],
        energy_parameters: EnergyParameters, grid_lookup: pd.DataFrame,
        neighbour_lookup: Mapping[int, Iterable[int]],
    ) -> "DriverContentionInputs":
        centroids, unit = grid_centroids(grid_lookup)
        return cls(
            routing_features, directional_neighbour_map, utility_inputs_by_vehicle,
            energy_parameters, centroids,
            pickup_distance_reference(centroids, neighbour_lookup), unit,
        )


def grid_centroids(grid_lookup: pd.DataFrame) -> tuple[dict[int, tuple[float, float]], str]:
    required = {"GridID", "CentroidX", "CentroidY"}
    if missing := required - set(grid_lookup.columns):
        raise ValueError(f"Grid lookup lacks centroid columns: {sorted(missing)}")
    rows = grid_lookup[list(required)]
    if rows.empty or rows["GridID"].duplicated().any() or rows.isna().any().any():
        raise ValueError("Canonical grid centroids must be complete and unique.")
    values = {
        int(row.GridID): (float(row.CentroidX), float(row.CentroidY))
        for row in rows.itertuples(index=False)
    }
    if not all(math.isfinite(value) for point in values.values() for value in point):
        raise ValueError("Canonical grid centroids must be finite.")
    return values, "EPSG:2263 feet"


def centroid_distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return float(math.hypot(first[0] - second[0], first[1] - second[1]))


def pickup_distance_reference(
    centroids: Mapping[int, tuple[float, float]], neighbour_lookup: Mapping[int, Iterable[int]],
) -> float:
    distances = [
        centroid_distance(centroids[grid], centroids[int(neighbour)])
        for grid, neighbours in neighbour_lookup.items() for neighbour in neighbours
    ]
    if not distances or not all(math.isfinite(value) and value > 0 for value in distances):
        raise ValueError("A positive geometry-only direct-neighbour pickup reference is required.")
    return max(distances)


def pickup_wait_preference(pickup_distance: float, reference: float) -> float:
    if not math.isfinite(pickup_distance) or pickup_distance < 0 or not math.isfinite(reference) or reference <= 0:
        raise ValueError("Pickup distance and reference must be finite with valid positive reference.")
    return float(1.0 - min(1.0, max(0.0, pickup_distance / reference)))


def normalized_trip_energy_burden(trip_energy_required: float, battery_capacity: float) -> float:
    if not math.isfinite(trip_energy_required) or trip_energy_required < 0 or not math.isfinite(battery_capacity) or battery_capacity <= 0:
        raise ValueError("Trip energy must be non-negative and battery capacity positive.")
    return float(min(1.0, max(0.0, trip_energy_required / battery_capacity)))


def evaluate_request_contention(
    *, vehicle: VehicleState, request: RequestState,
    routing_features: Mapping[int, GridRoutingFeatures], directional_neighbour_map: pd.DataFrame,
    alternative_inputs: Mapping[RoutingAction | str, CandidateUtilityInput],
    energy: EnergyParameters, centroids: Mapping[int, tuple[float, float]], pickup_reference: float,
) -> ContentionEvaluation:
    from src.routing.baseline import CandidateUtilityInput, build_routing_state, candidate_utility, evaluate_action_utilities

    if request.offered_fare is None or request.trip_distance_km is None:
        raise ValueError("Contention requires offered fare and passenger-trip distance.")
    state = build_routing_state(vehicle, routing_features, directional_neighbour_map)
    _, alternatives = evaluate_action_utilities(state, alternative_inputs, energy)
    best_alternative = max(component.total for component in alternatives.values() if component is not None)
    distance = 0.0 if vehicle.current_grid == request.origin_grid else centroid_distance(
        centroids[vehicle.current_grid], centroids[request.origin_grid],
    )
    wait_preference = pickup_wait_preference(distance, pickup_reference)
    energy_burden = normalized_trip_energy_burden(
        energy_consumed_kwh(request.trip_distance_km, energy), energy.battery_capacity_kwh,
    )
    request_input = CandidateUtilityInput(float(request.offered_fare), wait_preference, energy_burden)
    request_utility = candidate_utility(routing_features[request.origin_grid], request_input, vehicle.energy_level, energy).total
    return ContentionEvaluation(
        vehicle.vehicle_id, vehicle.current_grid, distance, "EPSG:2263 feet",
        wait_preference, energy_burden, request_utility, best_alternative,
        request_utility >= best_alternative,
    )
