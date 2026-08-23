"""NB10 battery-energy operations, without road/station travel modelling.

Ding et al. (IEEE TIA 2023, Table I) supplies the adopted capacity, 60-kWh
starting-energy reference, 7.5-kWh reference minimum, consumption, and power.
The supervisor-aligned operational baseline supplies truncated initial SOC and
the <=20% charging trigger; full-charge release remains provisional.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from src.fleet.fleet import initialize_fleet
from src.fleet.state import VehicleState, VehicleStatus


@dataclass(frozen=True)
class EnergyParameters:
    """Config-backed EV energy constants for the current deterministic model."""

    battery_capacity_kwh: float
    initial_energy_kwh: float
    minimum_energy_kwh: float
    consumption_rate_kwh_per_km: float
    charging_power_kw: float
    charging_efficiency: float
    charging_release_energy_kwh: float
    mean_initial_soc: float
    initial_soc_std: float
    initial_soc_min: float
    initial_soc_max: float
    charging_trigger_soc: float

    def validate(self) -> None:
        """Validate physically bounded parameters without adding infrastructure."""
        values = self.__dict__
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values.values()):
            raise ValueError("EV energy parameters must be finite numeric values.")
        if self.battery_capacity_kwh <= 0 or self.consumption_rate_kwh_per_km < 0 or self.charging_power_kw < 0:
            raise ValueError("Battery capacity must be positive; consumption rate and charging power cannot be negative.")
        if not 0 < self.charging_efficiency <= 1:
            raise ValueError("charging_efficiency must be in (0, 1].")
        if not 0 <= self.initial_soc_min <= self.mean_initial_soc <= self.initial_soc_max <= 1 or self.initial_soc_std < 0:
            raise ValueError("Initial SOC mean/std/bounds are invalid.")
        if not 0 < self.charging_trigger_soc <= 1:
            raise ValueError("charging_trigger_soc must be in (0, 1].")
        if not 0 <= self.initial_energy_kwh <= self.battery_capacity_kwh:
            raise ValueError("initial_energy_kwh must be within battery capacity.")
        if not 0 <= self.minimum_energy_kwh <= self.battery_capacity_kwh:
            raise ValueError("minimum_energy_kwh must be within battery capacity.")
        if not 0 <= self.charging_release_energy_kwh <= self.battery_capacity_kwh:
            raise ValueError("charging_release_energy_kwh must be within battery capacity.")


def energy_parameters_from_config(config: dict) -> EnergyParameters:
    """Build validated energy settings from the sole project configuration source."""
    parameters = EnergyParameters(**config["energy"])
    parameters.validate()
    return parameters


def initial_energy(parameters: EnergyParameters) -> float:
    """Return Ding et al.'s 60-kWh reference, not fleet-wide SOC initialization."""
    parameters.validate()
    return float(parameters.initial_energy_kwh)


def sample_initial_socs(fleet_size: int, parameters: EnergyParameters, random_seed: int) -> np.ndarray:
    """Reproducibly sample supervisor-aligned truncated-normal initial SOCs."""
    parameters.validate()
    if not isinstance(fleet_size, int) or fleet_size <= 0:
        raise ValueError("fleet_size must be a positive integer.")
    rng = np.random.default_rng(random_seed)
    values: list[float] = []
    while len(values) < fleet_size:
        draws = rng.normal(parameters.mean_initial_soc, parameters.initial_soc_std, size=max(16, (fleet_size - len(values)) * 2))
        values.extend(float(value) for value in draws if parameters.initial_soc_min <= value <= parameters.initial_soc_max)
    return np.asarray(values[:fleet_size], dtype=np.float64)


def initialize_ev_fleet(fleet_size: int, valid_grid_ids, random_seed: int, parameters: EnergyParameters, initialization_method: str = "uniform_valid_grid") -> list[VehicleState]:
    """Initialize existing VehicleState objects with sampled SOC × capacity energy."""
    socs = sample_initial_socs(fleet_size, parameters, random_seed)
    return initialize_fleet(fleet_size, valid_grid_ids, random_seed, initialization_method=initialization_method, initial_energy_levels=socs * parameters.battery_capacity_kwh)


def validate_vehicle_energy(vehicle: VehicleState, parameters: EnergyParameters) -> None:
    """Ensure the existing VehicleState energy field remains within capacity."""
    parameters.validate()
    if not isinstance(vehicle.energy_level, (int, float)) or not math.isfinite(vehicle.energy_level):
        raise ValueError("Vehicle energy_level must be finite.")
    if not 0 <= vehicle.energy_level <= parameters.battery_capacity_kwh:
        raise ValueError("Vehicle energy_level must remain within [0, battery_capacity_kwh].")


def energy_consumed_kwh(distance_km: float, parameters: EnergyParameters) -> float:
    """Calculate distance-based consumption; distance is supplied by future routing."""
    parameters.validate()
    if not isinstance(distance_km, (int, float)) or not math.isfinite(distance_km) or distance_km < 0:
        raise ValueError("distance_km must be a finite non-negative input from the travel layer.")
    return float(distance_km * parameters.consumption_rate_kwh_per_km)


def requires_charging(vehicle: VehicleState, parameters: EnergyParameters) -> bool:
    """Return whether an EV is strictly below the configured minimum energy."""
    validate_vehicle_energy(vehicle, parameters)
    return vehicle.energy_level <= parameters.battery_capacity_kwh * parameters.charging_trigger_soc


def enter_charging(vehicle: VehicleState, parameters: EnergyParameters) -> None:
    """Transition an available low-energy vehicle into CHARGING.

    This milestone does not decide where it charges.  A BUSY vehicle cannot be
    moved into a station state mid-trip; invoke after its travel transition.
    """
    validate_vehicle_energy(vehicle, parameters)
    if vehicle.trip_status is VehicleStatus.BUSY:
        raise ValueError("A BUSY vehicle must complete its movement before entering CHARGING.")
    if not requires_charging(vehicle, parameters):
        raise ValueError("Vehicle energy is not below the charging minimum.")
    vehicle.trip_status = VehicleStatus.CHARGING
    vehicle.current_action = "charging"


def apply_distance_energy(vehicle: VehicleState, distance_km: float, parameters: EnergyParameters) -> float:
    """Deduct travel energy explicitly and send a low available EV to CHARGING.

    It is intentionally restricted to a completed/available vehicle because
    route distance and vehicle completion will be integrated in a later stage.
    """
    parameters.validate()
    validate_vehicle_energy(vehicle, parameters)
    if vehicle.trip_status is not VehicleStatus.IDLE:
        raise ValueError("Apply distance energy only after the existing BUSY travel transition completes and before charging begins.")
    consumed = energy_consumed_kwh(distance_km, parameters)
    if consumed > vehicle.energy_level:
        raise ValueError("Movement is impossible because it would make vehicle energy negative.")
    vehicle.energy_level -= consumed
    if requires_charging(vehicle, parameters):
        enter_charging(vehicle, parameters)
    return consumed


def charging_energy_gain_kwh(charging_duration_minutes: float, parameters: EnergyParameters) -> float:
    """Derive charging energy from configured kW and explicit charging duration."""
    parameters.validate()
    if not isinstance(charging_duration_minutes, (int, float)) or not math.isfinite(charging_duration_minutes) or charging_duration_minutes < 0:
        raise ValueError("charging_duration_minutes must be finite and non-negative.")
    return float(parameters.charging_power_kw * parameters.charging_efficiency * (charging_duration_minutes / 60.0))


def charge_vehicle(vehicle: VehicleState, charging_duration_minutes: float, parameters: EnergyParameters) -> float:
    """Apply capped charging energy and release at the configured threshold.

    ``charging_release_energy_kwh=75`` means full charge is required.  This is
    provisional engineering behaviour, not a Ding et al. research parameter.
    """
    validate_vehicle_energy(vehicle, parameters)
    if vehicle.trip_status is not VehicleStatus.CHARGING:
        raise ValueError("Only CHARGING vehicles can receive charging energy.")
    gain = charging_energy_gain_kwh(charging_duration_minutes, parameters)
    before = vehicle.energy_level
    vehicle.energy_level = min(parameters.battery_capacity_kwh, before + gain)
    if vehicle.energy_level >= parameters.charging_release_energy_kwh:
        vehicle.trip_status = VehicleStatus.IDLE
        vehicle.current_action = "idle"
    return float(vehicle.energy_level - before)
