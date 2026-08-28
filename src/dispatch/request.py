"""Passenger-request state contract for the deterministic dispatch baseline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import math
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
    base_fare: float | None = None
    pricing_factor: float | None = None
    offered_fare: float | None = None
    acceptance_probability: float | None = None
    customer_accepted: bool | None = None
    source_trip_id: int | None = None
    empirical_pickup_datetime: datetime | None = None
    empirical_dropoff_datetime: datetime | None = None
    trip_duration_minutes: float | None = None
    trip_distance_miles: float | None = None
    trip_distance_km: float | None = None
    empirical_within_slot_offset_seconds: float | None = None
    trip_start_minute: float | None = None
    busy_until_minute: float | None = None
    passenger_energy_kwh: float | None = None
    passenger_energy_before_kwh: float | None = None
    passenger_energy_after_kwh: float | None = None

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
        if self.base_fare is not None:
            base = float(self.base_fare)
            if not math.isfinite(base) or base < 0:
                raise ValueError("base_fare must be finite and non-negative.")
        empirical_values = (self.empirical_pickup_datetime, self.empirical_dropoff_datetime, self.trip_duration_minutes, self.trip_distance_miles, self.trip_distance_km)
        if any(value is not None for value in empirical_values) or self.source_trip_id is not None:
            if self.source_trip_id is None or any(value is None for value in empirical_values) or self.base_fare is None:
                raise ValueError("Empirical requests require source identity, timestamps, duration, both distance units, and base fare.")
            if not isinstance(self.source_trip_id, int) or self.source_trip_id < 0:
                raise ValueError("source_trip_id must be a non-negative integer.")
            duration, miles, km = float(self.trip_duration_minutes), float(self.trip_distance_miles), float(self.trip_distance_km)
            if not all(math.isfinite(value) for value in (duration, miles, km)) or duration <= 0 or miles < 0 or km < 0:
                raise ValueError("Empirical duration must be positive and distances finite and non-negative.")
            if not math.isclose(km, miles * 1.609344, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("trip_distance_km must be the one-time conversion from TLC miles.")
            timestamp_duration = (self.empirical_dropoff_datetime - self.empirical_pickup_datetime).total_seconds() / 60.0
            if not math.isclose(duration, timestamp_duration, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("Empirical trip duration must equal dropoff minus pickup.")
            if self.empirical_within_slot_offset_seconds is not None:
                offset = float(self.empirical_within_slot_offset_seconds)
                if not math.isfinite(offset) or not 0 <= offset < 1800:
                    raise ValueError("Empirical within-slot offset must be in [0, 1800) seconds.")
                pickup = self.empirical_pickup_datetime
                expected_offset = (pickup.minute % 30) * 60 + pickup.second + pickup.microsecond / 1_000_000
                if not math.isclose(offset, expected_offset, rel_tol=0, abs_tol=1e-9):
                    raise ValueError("Within-slot offset must come from the same empirical pickup timestamp.")
                if self.request_time != int(offset // 120):
                    raise ValueError("request_time must be the empirical two-minute mini-slot index.")
        energy_values = (self.passenger_energy_kwh, self.passenger_energy_before_kwh, self.passenger_energy_after_kwh)
        if any(value is not None for value in energy_values):
            if any(value is None for value in energy_values) or self.status is not RequestStatus.ASSIGNED:
                raise ValueError("Passenger-energy audit requires a served request and complete before/after values.")
            consumed, before, after = (float(value) for value in energy_values)  # type: ignore[arg-type]
            if not all(math.isfinite(value) and value >= 0 for value in (consumed, before, after)) or not math.isclose(before - consumed, after):
                raise ValueError("Passenger-energy audit does not reconcile.")
        audit_values = (self.pricing_factor, self.offered_fare, self.acceptance_probability)
        if any(value is not None for value in audit_values) or self.customer_accepted is not None:
            if self.base_fare is None or any(value is None for value in audit_values) or not isinstance(self.customer_accepted, bool):
                raise ValueError("Priced requests require the complete pricing and acceptance audit.")
            factor, offered, probability = (float(value) for value in audit_values)  # type: ignore[arg-type]
            if not all(math.isfinite(value) for value in (base, factor, offered, probability)):
                raise ValueError("Request pricing values must be finite.")
            if base < 0 or factor <= 0 or offered < 0 or not 0 <= probability <= 1:
                raise ValueError("Request pricing values are outside their valid ranges.")
        if self.status is RequestStatus.PENDING:
            if self.assigned_vehicle_id is not None or self.wait_time is not None:
                raise ValueError("PENDING requests cannot have assignment or wait-time results.")
        elif self.status is RequestStatus.ASSIGNED:
            if not isinstance(self.assigned_vehicle_id, int) or self.assigned_vehicle_id < 0 or self.wait_time is None:
                raise ValueError("ASSIGNED requests require vehicle_id and wait_time.")
            if self.wait_time < 0:
                raise ValueError("wait_time cannot be negative.")
            if self.trip_start_minute is not None or self.busy_until_minute is not None:
                if self.trip_start_minute is None or self.busy_until_minute is None or self.trip_duration_minutes is None:
                    raise ValueError("Trip timing audit must be complete.")
                if not math.isclose(self.busy_until_minute - self.trip_start_minute, self.trip_duration_minutes):
                    raise ValueError("busy_until_minute must equal start plus empirical duration.")
        elif self.assigned_vehicle_id is not None or self.wait_time is not None:
            raise ValueError("UNSERVED requests do not fabricate assignment or wait time.")
