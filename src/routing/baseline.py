"""NB11 deterministic routing/repositioning baseline; no learning or rewards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

import pandas as pd

from src.charging.energy import EnergyParameters, apply_distance_energy, requires_charging
from src.fleet.state import VehicleState, VehicleStatus
from src.simulation.statistics import GridSlotStatistics


class RoutingAction(str, Enum):
    STAY = "STAY"
    NORTH = "NORTH"
    EAST = "EAST"
    SOUTH = "SOUTH"
    WEST = "WEST"


ACTION_ORDER = (RoutingAction.STAY, RoutingAction.NORTH, RoutingAction.EAST, RoutingAction.SOUTH, RoutingAction.WEST)


@dataclass(frozen=True)
class RoutingParameters:
    speed_kmph: float
    reposition_distance_km: float
    max_reposition_minutes: float

    def duration_minutes(self) -> float:
        if self.speed_kmph <= 0 or self.reposition_distance_km < 0 or self.max_reposition_minutes <= 0:
            raise ValueError("Routing speed/distance/feasibility settings must be positive.")
        return self.reposition_distance_km / self.speed_kmph * 60.0

    def validate(self) -> None:
        if self.duration_minutes() > self.max_reposition_minutes:
            raise ValueError("Repositioning movement exceeds the configured feasibility threshold.")


@dataclass(frozen=True)
class GridRoutingFeatures:
    grid_id: int
    predicted_demand: float | None
    supply_total: int | None
    supply_idle: int | None
    supply_busy: int | None
    supply_charging: int | None
    mean_fare: float | None
    std_fare: float | None
    ewma_fare: float | None
    ewma_std_fare: float | None
    mean_wait: float | None
    std_wait: float | None
    ewma_wait: float | None
    ewma_std_wait: float | None
    charging_available: bool | None
    charging_wait: float | None


@dataclass(frozen=True)
class RoutingState:
    vehicle_id: int
    current_grid: int
    energy_level: float
    current_features: GridRoutingFeatures
    action_features: dict[RoutingAction, GridRoutingFeatures | None]


@dataclass(frozen=True)
class RoutingTransition:
    vehicle_id: int
    action: RoutingAction
    origin_grid: int
    destination_grid: int
    distance_km: float
    duration_minutes: float
    energy_before_kwh: float
    energy_after_kwh: float
    status_before: VehicleStatus
    status_after: VehicleStatus


def build_grid_routing_features(predicted_demand: Mapping[int, float], supply: pd.DataFrame, statistics: list[GridSlotStatistics]) -> dict[int, GridRoutingFeatures]:
    """Combine frozen grid-level demand/supply/NB9 records into routing features."""
    supply_by_grid = supply.set_index("grid_id").to_dict("index")
    result: dict[int, GridRoutingFeatures] = {}
    for item in statistics:
        values = supply_by_grid.get(item.grid_id, {})
        result[item.grid_id] = GridRoutingFeatures(item.grid_id, predicted_demand.get(item.grid_id), values.get("supply_total"), values.get("supply_idle"), values.get("supply_busy"), values.get("supply_charging"), item.mean_fare, item.std_fare, item.ewma_fare, item.ewma_std_fare, item.mean_wait, item.std_wait, item.ewma_wait, item.ewma_std_wait, item.charging_available, item.charging_wait)
    return result


def build_routing_state(vehicle: VehicleState, features: Mapping[int, GridRoutingFeatures], neighbour_map: pd.DataFrame) -> RoutingState:
    """Construct current-grid/neighbour-grid/vehicle routing state for NB11."""
    if vehicle.current_grid not in features:
        raise ValueError("Current grid lacks routing features.")
    actions: dict[RoutingAction, GridRoutingFeatures | None] = {RoutingAction.STAY: features[vehicle.current_grid]}
    directions = {"north": RoutingAction.NORTH, "east": RoutingAction.EAST, "south": RoutingAction.SOUTH, "west": RoutingAction.WEST}
    rows = neighbour_map[neighbour_map["GridID"] == vehicle.current_grid]
    for direction, action in directions.items():
        match = rows[rows["Direction"] == direction]
        actions[action] = features.get(int(match.iloc[0]["NeighbourGridID"])) if len(match) else None
    return RoutingState(vehicle.vehicle_id, vehicle.current_grid, vehicle.energy_level, features[vehicle.current_grid], actions)


def valid_action_mask(state: RoutingState) -> dict[RoutingAction, bool]:
    """Mask invalid boundary actions while keeping STAY valid everywhere."""
    return {action: state.action_features[action] is not None for action in ACTION_ORDER}


def select_action(state: RoutingState, action_scores: Mapping[RoutingAction | str, float]) -> RoutingAction:
    """Choose highest externally supplied valid score with fixed action-order ties."""
    mask = valid_action_mask(state)
    scores = {RoutingAction(key): float(value) for key, value in action_scores.items()}
    if not all(action in scores for action in ACTION_ORDER):
        raise ValueError("Action scores must include STAY, NORTH, EAST, SOUTH, and WEST.")
    return max((action for action in ACTION_ORDER if mask[action]), key=lambda action: (scores[action], -ACTION_ORDER.index(action)))


def execute_reposition(vehicle: VehicleState, state: RoutingState, action: RoutingAction, parameters: RoutingParameters, energy: EnergyParameters) -> RoutingTransition:
    """Apply one feasible action, its 3-km energy use, and a structured transition."""
    parameters.validate()
    if vehicle.trip_status is not VehicleStatus.IDLE or requires_charging(vehicle, energy):
        raise ValueError("Only idle vehicles not requiring charging can reposition.")
    destination = state.action_features[action]
    if destination is None:
        raise ValueError("Cannot execute a masked routing action.")
    before_energy, before_status, origin = vehicle.energy_level, vehicle.trip_status, vehicle.current_grid
    distance = 0.0 if action is RoutingAction.STAY else parameters.reposition_distance_km
    duration = 0.0 if action is RoutingAction.STAY else parameters.duration_minutes()
    if action is not RoutingAction.STAY:
        vehicle.current_grid = destination.grid_id
        apply_distance_energy(vehicle, distance, energy)
    return RoutingTransition(vehicle.vehicle_id, action, origin, vehicle.current_grid, distance, duration, before_energy, vehicle.energy_level, before_status, vehicle.trip_status)
