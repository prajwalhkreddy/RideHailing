"""Vehicle-level state contract for the fleet-supply milestone."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Collection


class VehicleStatus(str, Enum):
    """Approved vehicle availability states; charging dynamics are deferred."""

    IDLE = "IDLE"
    BUSY = "BUSY"
    CHARGING = "CHARGING"


@dataclass
class VehicleState:
    """Mutable state needed by future dispatch and EV modules.

    ``energy_level`` is deliberately only a valid placeholder here.  Neither
    consumption nor charging behaviour is part of this fleet-state milestone.
    """

    vehicle_id: int
    current_grid: int
    trip_status: VehicleStatus
    destination: int | None
    remaining_travel_time: float
    current_action: str
    energy_level: float
    idle_wait_minutes: float = 0.0
    idle_wait_grid: int | None = None

    def start_idle_wait(self) -> None:
        """Start a new driver-idle waiting episode in the current grid."""
        if self.trip_status is not VehicleStatus.IDLE:
            raise ValueError("Only an IDLE vehicle can start an idle-wait episode.")
        self.idle_wait_minutes = 0.0
        self.idle_wait_grid = self.current_grid

    def abandon_idle_wait(self) -> None:
        """End an active wait without producing a completed observation."""
        self.idle_wait_minutes = 0.0
        self.idle_wait_grid = None

    def advance_idle_wait(self, duration_minutes: float) -> None:
        """Accumulate one completed interval for a continuously IDLE vehicle."""
        if self.trip_status is not VehicleStatus.IDLE or self.idle_wait_grid is None:
            return
        if self.idle_wait_grid != self.current_grid:
            raise ValueError("Active idle-wait grid must match the vehicle current grid.")
        self.idle_wait_minutes += duration_minutes

    def validate(self, valid_grid_ids: Collection[int]) -> None:
        """Validate state against canonical GridIDs and status invariants."""
        grids = set(valid_grid_ids)
        if not isinstance(self.vehicle_id, int) or self.vehicle_id < 0:
            raise ValueError("vehicle_id must be a non-negative integer.")
        if not isinstance(self.trip_status, VehicleStatus):
            raise ValueError("trip_status must be a VehicleStatus value.")
        if self.current_grid not in grids:
            raise ValueError("current_grid must be a canonical valid GridID.")
        if isinstance(self.remaining_travel_time, bool) or not isinstance(self.remaining_travel_time, (int, float)) or not math.isfinite(self.remaining_travel_time) or self.remaining_travel_time < 0:
            raise ValueError("remaining_travel_time must be finite non-negative minutes.")
        if not isinstance(self.current_action, str) or not self.current_action:
            raise ValueError("current_action must be a non-empty string.")
        if not isinstance(self.energy_level, (int, float)) or not math.isfinite(self.energy_level) or self.energy_level < 0:
            raise ValueError("energy_level must be a finite non-negative value.")
        if not isinstance(self.idle_wait_minutes, (int, float)) or not math.isfinite(self.idle_wait_minutes) or self.idle_wait_minutes < 0:
            raise ValueError("idle_wait_minutes must be finite and non-negative.")
        if self.idle_wait_grid is not None and self.idle_wait_grid not in grids:
            raise ValueError("idle_wait_grid must be a canonical valid GridID when active.")
        if self.idle_wait_grid is not None and (self.trip_status is not VehicleStatus.IDLE or self.idle_wait_grid != self.current_grid):
            raise ValueError("Only an IDLE vehicle may have an active wait in its current grid.")
        if self.idle_wait_grid is None and self.idle_wait_minutes != 0:
            raise ValueError("An inactive idle-wait episode must have zero minutes.")
        if self.trip_status is VehicleStatus.BUSY:
            if self.destination not in grids or self.remaining_travel_time <= 0:
                raise ValueError("BUSY vehicles require a valid destination and positive remaining travel time.")
        elif self.destination is not None or self.remaining_travel_time != 0:
            raise ValueError("IDLE and CHARGING vehicles cannot retain a trip destination or travel time.")
