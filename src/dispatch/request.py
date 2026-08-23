"""Passenger-request state contract for the deterministic dispatch baseline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Collection


class RequestStatus(str, Enum):
    """Lifecycle states used before later pricing and wait-statistics modules."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    UNSERVED = "UNSERVED"


@dataclass
class RequestState:
    """One generated passenger request.

    ``request_time`` is the zero-based mini-slot index in the current main
    slot.  This is sufficient for the baseline's FCFS ordering and does not
    introduce a broader simulation-clock representation.
    """

    request_id: int
    request_time: int
    origin_grid: int
    destination_grid: int
    status: RequestStatus = RequestStatus.PENDING
    assigned_vehicle_id: int | None = None
    wait_time: int | None = None

    def validate(self, valid_grid_ids: Collection[int], mini_slots_per_main_slot: int) -> None:
        """Validate canonical spatial references and request lifecycle state."""
        grids = set(valid_grid_ids)
        if not isinstance(self.request_id, int) or self.request_id < 0:
            raise ValueError("request_id must be a non-negative integer.")
        if not isinstance(self.request_time, int) or not 0 <= self.request_time < mini_slots_per_main_slot:
            raise ValueError("request_time must be a valid mini-slot index.")
        if self.origin_grid not in grids or self.destination_grid not in grids:
            raise ValueError("Request origin_grid and destination_grid must be canonical valid GridIDs.")
        if not isinstance(self.status, RequestStatus):
            raise ValueError("status must be a RequestStatus value.")
        if self.status is RequestStatus.PENDING:
            if self.assigned_vehicle_id is not None or self.wait_time is not None:
                raise ValueError("PENDING requests cannot have assignment or wait-time results.")
        elif self.status is RequestStatus.ASSIGNED:
            if not isinstance(self.assigned_vehicle_id, int) or self.assigned_vehicle_id < 0 or self.wait_time is None:
                raise ValueError("ASSIGNED requests require vehicle_id and wait_time.")
            if self.wait_time < 0:
                raise ValueError("wait_time cannot be negative.")
        elif self.assigned_vehicle_id is not None or self.wait_time is not None:
            raise ValueError("UNSERVED requests do not fabricate assignment or wait time.")

