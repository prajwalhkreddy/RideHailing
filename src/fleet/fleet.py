"""Reproducible fleet initialization and minimal vehicle-state transitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from src.fleet.state import VehicleState, VehicleStatus


def mini_slots_per_main_slot(main_slot_minutes: int, mini_slot_minutes: int) -> int:
    """Validate and derive the one authoritative simulator timing relationship."""
    if not isinstance(main_slot_minutes, int) or not isinstance(mini_slot_minutes, int):
        raise ValueError("Simulation slot durations must be integers in minutes.")
    if main_slot_minutes <= 0 or mini_slot_minutes <= 0 or main_slot_minutes % mini_slot_minutes:
        raise ValueError("main_slot_minutes must be a positive whole multiple of mini_slot_minutes.")
    return main_slot_minutes // mini_slot_minutes


def initialize_fleet(
    fleet_size: int,
    valid_grid_ids: Iterable[int],
    random_seed: int,
    initial_energy_level: float = 1.0,
    initialization_method: str = "uniform_valid_grid",
    initial_energy_levels: Iterable[float] | None = None,
) -> list[VehicleState]:
    """Create the provisional, seed-reproducible all-IDLE fleet baseline.

    The uniform selection over valid GridIDs is an engineering baseline, not a
    demand-derived research methodology.  The named method parameter provides
    a stable boundary for a later approved distribution strategy.
    """
    grid_ids = np.array(sorted(set(valid_grid_ids)), dtype=np.int64)
    if not isinstance(fleet_size, int) or fleet_size <= 0:
        raise ValueError("fleet_size must be a positive integer.")
    if not len(grid_ids):
        raise ValueError("At least one valid GridID is required to initialize a fleet.")
    if initialization_method != "uniform_valid_grid":
        raise ValueError(f"Unsupported fleet initialization method: {initialization_method}")
    if not isinstance(initial_energy_level, (int, float)) or initial_energy_level < 0:
        raise ValueError("initial_energy_level must be a non-negative numeric placeholder.")
    rng = np.random.default_rng(random_seed)
    assigned_grids = rng.choice(grid_ids, size=fleet_size, replace=True)
    energies = list(initial_energy_levels) if initial_energy_levels is not None else [float(initial_energy_level)] * fleet_size
    if len(energies) != fleet_size or any(not isinstance(energy, (int, float)) or energy < 0 for energy in energies):
        raise ValueError("initial_energy_levels must contain one non-negative value per vehicle.")
    fleet = [
        VehicleState(
            vehicle_id=vehicle_id,
            current_grid=int(grid_id),
            trip_status=VehicleStatus.IDLE,
            destination=None,
            remaining_travel_time=0,
            current_action="idle",
            energy_level=float(energies[vehicle_id]),
        )
        for vehicle_id, grid_id in enumerate(assigned_grids)
    ]
    validate_fleet(fleet, grid_ids)
    return fleet


def validate_fleet(fleet: Iterable[VehicleState], valid_grid_ids: Iterable[int], expected_size: int | None = None) -> None:
    """Check vehicle IDs, per-vehicle state, and optional fleet-size invariant."""
    vehicles = list(fleet)
    grid_ids = set(valid_grid_ids)
    if expected_size is not None and len(vehicles) != expected_size:
        raise ValueError(f"Fleet contains {len(vehicles)} vehicles; expected {expected_size}.")
    vehicle_ids = [vehicle.vehicle_id for vehicle in vehicles]
    if len(vehicle_ids) != len(set(vehicle_ids)):
        raise ValueError("Fleet vehicle_id values must be unique.")
    for vehicle in vehicles:
        vehicle.validate(grid_ids)


@dataclass
class Fleet:
    """Fleet mutation boundary for future dispatch without implementing dispatch."""

    vehicles: list[VehicleState]
    valid_grid_ids: frozenset[int]
    mini_slot_minutes: int

    def __post_init__(self) -> None:
        if not self.valid_grid_ids:
            raise ValueError("Fleet requires canonical valid GridIDs.")
        if not isinstance(self.mini_slot_minutes, int) or self.mini_slot_minutes <= 0:
            raise ValueError("mini_slot_minutes must be a positive integer.")
        validate_fleet(self.vehicles, self.valid_grid_ids)

    def vehicle(self, vehicle_id: int) -> VehicleState:
        """Return a vehicle or reject an unknown identifier."""
        for vehicle in self.vehicles:
            if vehicle.vehicle_id == vehicle_id:
                return vehicle
        raise ValueError(f"Unknown vehicle_id: {vehicle_id}")

    def assign_busy(self, vehicle_id: int, destination: int, travel_duration_minutes: int) -> None:
        """Apply the future-dispatch IDLE -> BUSY transition contract."""
        vehicle = self.vehicle(vehicle_id)
        if vehicle.trip_status is not VehicleStatus.IDLE:
            raise ValueError("Only IDLE vehicles can be assigned a trip.")
        if destination not in self.valid_grid_ids:
            raise ValueError("Trip destination must be a canonical valid GridID.")
        if not isinstance(travel_duration_minutes, int) or travel_duration_minutes <= 0:
            raise ValueError("travel_duration_minutes must be a positive integer.")
        vehicle.trip_status = VehicleStatus.BUSY
        vehicle.destination = destination
        vehicle.remaining_travel_time = travel_duration_minutes
        vehicle.current_action = "transporting"
        vehicle.validate(self.valid_grid_ids)

    def advance_mini_slot(self) -> None:
        """Advance BUSY vehicle travel by exactly one configured mini-slot."""
        for vehicle in self.vehicles:
            if vehicle.trip_status is not VehicleStatus.BUSY:
                continue
            vehicle.remaining_travel_time = max(0, vehicle.remaining_travel_time - self.mini_slot_minutes)
            if vehicle.remaining_travel_time == 0:
                # BUSY validation guarantees destination is a valid GridID.
                vehicle.current_grid = vehicle.destination  # type: ignore[assignment]
                vehicle.trip_status = VehicleStatus.IDLE
                vehicle.destination = None
                vehicle.current_action = "idle"
            vehicle.validate(self.valid_grid_ids)
