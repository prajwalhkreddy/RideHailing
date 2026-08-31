"""NB11 utility-based routing/repositioning; no learning or rewards."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
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


@dataclass(frozen=True)
class CandidateUtilityInput:
    """Explicit vehicle preference/degradation inputs for one candidate grid."""
    price_preference: float
    wait_preference: float
    normalized_degradation_penalty: float


@dataclass(frozen=True)
class UtilityComponents:
    price: float
    wait: float
    charging: float
    total: float


@dataclass(frozen=True)
class RoutingDecision:
    """Auditable NB11 observation for later supervised policy learning."""
    state: RoutingState
    chosen_action: RoutingAction
    valid_action_mask: dict[RoutingAction, bool]
    utility_vector: dict[RoutingAction, float | None]
    components: dict[RoutingAction, UtilityComponents | None]


@dataclass(frozen=True)
class DegradationParameters:
    """All-explicit Chauhan/Jain parameters; the project supplies no defaults."""
    proportionality_constant_a: float
    activation_energy_ea: float
    gas_constant_r: float
    ambient_temperature_k: float
    thermal_resistance: float
    charging_power_kw: float
    discharging_power_kw: float
    slot_duration: float
    slot_count: int
    battery_replacement_cost: float
    battery_capacity_kwh: float
    charging_duration: float
    discharging_duration: float
    battery_investment_cost: float
    battery_life_cycles: float
    dod_increment: float


@dataclass(frozen=True)
class DegradationCost:
    temperature_power_k: float
    capacity_fading_rate: float
    cumulative_capacity_fading: float
    temperature_cost: float
    dod_cost: float
    total_cost: float


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


def _finite(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def price_utility(price_preference: float, mean_price: float, sigma_price: float, sigma_multiplier: float = 1.0) -> float:
    """Increasing linear utility over mean price +/- one sigma by default."""
    preference, mean = _finite(price_preference, "price_preference"), _finite(mean_price, "mean_price")
    sigma, multiplier = _finite(sigma_price, "sigma_price"), _finite(sigma_multiplier, "sigma_multiplier")
    if sigma < 0 or multiplier <= 0:
        raise ValueError("sigma_price must be non-negative and sigma_multiplier positive.")
    lower, upper = mean - multiplier * sigma, mean + multiplier * sigma
    if upper == lower:
        return 0.0 if preference < lower else 1.0
    return float(min(1.0, max(0.0, (preference - lower) / (upper - lower))))


def wait_utility(wait_preference: float, mean_wait: float, sigma_wait: float, sigma_multiplier: float = 1.0) -> float:
    """Decreasing linear utility: lower preferred waiting time is better."""
    preference, mean = _finite(wait_preference, "wait_preference"), _finite(mean_wait, "mean_wait")
    sigma, multiplier = _finite(sigma_wait, "sigma_wait"), _finite(sigma_multiplier, "sigma_multiplier")
    if sigma < 0 or multiplier <= 0:
        raise ValueError("sigma_wait must be non-negative and sigma_multiplier positive.")
    lower, upper = mean - multiplier * sigma, mean + multiplier * sigma
    if upper == lower:
        return 1.0 if preference <= lower else 0.0
    return float(min(1.0, max(0.0, (upper - preference) / (upper - lower))))


def charging_time_to_full_minutes(current_energy_kwh: float, energy: EnergyParameters) -> float:
    """Time to full using NB10's effective power = power * efficiency."""
    energy.validate()
    current = _finite(current_energy_kwh, "current_energy_kwh")
    if not 0 <= current <= energy.battery_capacity_kwh:
        raise ValueError("current_energy_kwh must be within battery capacity.")
    effective_power = energy.charging_power_kw * energy.charging_efficiency
    required = energy.battery_capacity_kwh - current
    if effective_power == 0:
        return 0.0 if required == 0 else math.inf
    return required / effective_power * 60.0


def charging_time_utility(current_energy_kwh: float, energy: EnergyParameters) -> float:
    """Return 1 - T_charge/T_max from the NB10 SOC threshold to full."""
    threshold_energy = energy.charging_trigger_soc * energy.battery_capacity_kwh
    maximum = charging_time_to_full_minutes(threshold_energy, energy)
    current = charging_time_to_full_minutes(current_energy_kwh, energy)
    if maximum == 0 or not math.isfinite(maximum):
        raise ValueError("A finite positive maximum charging time is required.")
    return float(min(1.0, max(0.0, 1.0 - current / maximum)))


def battery_degradation_cost(parameters: DegradationParameters) -> DegradationCost:
    """Compute Chauhan/Jain equations (14)-(20) from explicit inputs only."""
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in parameters.__dict__.values()):
        raise ValueError("All degradation parameters must be finite numeric values.")
    if (parameters.proportionality_constant_a < 0 or parameters.gas_constant_r <= 0 or
            parameters.battery_capacity_kwh <= 0 or parameters.slot_duration < 0 or parameters.slot_count < 0 or
            parameters.battery_life_cycles <= 0 or parameters.dod_increment <= 0 or
            min(parameters.charging_duration, parameters.discharging_duration,
                parameters.charging_power_kw, parameters.discharging_power_kw) < 0):
        raise ValueError("Degradation parameters violate the paper equation domains.")
    power_temperature = parameters.ambient_temperature_k + parameters.thermal_resistance * parameters.charging_power_kw
    if power_temperature <= 0:
        raise ValueError("Tpower must be positive Kelvin.")
    fading_rate = parameters.proportionality_constant_a * math.exp(
        (-parameters.activation_energy_ea / parameters.gas_constant_r) / power_temperature
    )
    cumulative_fading = fading_rate * parameters.slot_duration * parameters.slot_count
    temperature_cost = cumulative_fading / parameters.battery_capacity_kwh * parameters.battery_replacement_cost
    level_cost = parameters.battery_investment_cost / (2.0 * parameters.battery_life_cycles * parameters.battery_capacity_kwh * parameters.dod_increment)
    dod_cost = level_cost * (parameters.charging_duration * parameters.charging_power_kw + parameters.discharging_duration * parameters.discharging_power_kw)
    return DegradationCost(power_temperature, fading_rate, cumulative_fading, temperature_cost, dod_cost, temperature_cost + dod_cost)


def charging_utility(current_energy_kwh: float, energy: EnergyParameters, normalized_degradation_penalty: float) -> float:
    """Subtract an explicit normalized penalty; raw degradation cost is invalid here."""
    penalty = _finite(normalized_degradation_penalty, "normalized_degradation_penalty")
    if not 0 <= penalty <= 1:
        raise ValueError("normalized_degradation_penalty must already be normalized to [0, 1].")
    return float(min(1.0, max(0.0, charging_time_utility(current_energy_kwh, energy) - penalty)))


def candidate_utility(features: GridRoutingFeatures, inputs: CandidateUtilityInput, current_energy_kwh: float, energy: EnergyParameters) -> UtilityComponents:
    """Calculate the three isolated components and fixed equal-weight total."""
    if features.mean_fare is None or features.std_fare is None or features.mean_wait is None or features.std_wait is None:
        raise ValueError("Candidate utility requires mean/std fare and waiting statistics.")
    price = price_utility(inputs.price_preference, features.mean_fare, features.std_fare)
    wait = wait_utility(inputs.wait_preference, features.mean_wait, features.std_wait)
    charging = charging_utility(current_energy_kwh, energy, inputs.normalized_degradation_penalty)
    return UtilityComponents(price, wait, charging, (price + wait + charging) / 3.0)


def select_action(state: RoutingState, utility_inputs: Mapping[RoutingAction | str, CandidateUtilityInput], energy: EnergyParameters) -> RoutingDecision:
    """Evaluate valid candidates and choose maximum total utility with fixed ties."""
    mask = valid_action_mask(state)
    inputs = {RoutingAction(key): value for key, value in utility_inputs.items()}
    missing = [action.value for action in ACTION_ORDER if mask[action] and action not in inputs]
    if missing:
        raise ValueError(f"Utility inputs are required for every valid candidate: {missing}.")
    components: dict[RoutingAction, UtilityComponents | None] = {}
    utilities: dict[RoutingAction, float | None] = {}
    for action in ACTION_ORDER:
        feature = state.action_features[action]
        component = candidate_utility(feature, inputs[action], state.energy_level, energy) if feature is not None else None
        components[action] = component
        utilities[action] = component.total if component is not None else None
    chosen = max((action for action in ACTION_ORDER if mask[action]), key=lambda action: (utilities[action], -ACTION_ORDER.index(action)))
    return RoutingDecision(state, chosen, mask, utilities, components)


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
        vehicle.abandon_idle_wait()
        vehicle.current_grid = destination.grid_id
        apply_distance_energy(vehicle, distance, energy)
        if vehicle.trip_status is VehicleStatus.IDLE:
            # Reposition arrival is instantaneous in the existing movement model.
            vehicle.start_idle_wait()
    return RoutingTransition(vehicle.vehicle_id, action, origin, vehicle.current_grid, distance, duration, before_energy, vehicle.energy_level, before_status, vehicle.trip_status)
