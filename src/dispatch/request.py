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
    assigned_vehicle_origin_grid: int | None = None
    wait_time: int | None = None
    base_fare: float | None = None
    pricing_factor: float | None = None
    offered_fare: float | None = None
    acceptance_probability: float | None = None
    customer_accepted: bool | None = None
    customer_model: str | None = None
    weather_code: float | None = None
    period: int | None = None
    historical_p_base: float | None = None
    historical_d_base: float | None = None
    epsilon_customer: float | None = None
    p_max: float | None = None
    pricing_context: tuple[float, ...] | None = None
    selected_arm: int | None = None
    linucb_reward: float | None = None
    raw_served_revenue: float | None = None
    linucb_learning_reward: float | None = None
    sensitivity_lookup_level: str | None = None
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
    eligible_vehicle_count: int | None = None
    contender_count: int | None = None
    selected_vehicle_origin_grid: int | None = None
    selected_pickup_distance: float | None = None
    selected_pickup_distance_unit: str | None = None
    selected_request_utility: float | None = None
    selected_best_alternative_utility: float | None = None
    selected_utility_margin: float | None = None

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
        contention_counts = (self.eligible_vehicle_count, self.contender_count)
        contention_selected = (
            self.selected_vehicle_origin_grid, self.selected_pickup_distance,
            self.selected_pickup_distance_unit,
            self.selected_request_utility, self.selected_best_alternative_utility,
            self.selected_utility_margin,
        )
        if any(value is not None for value in contention_counts + contention_selected):
            if any(value is None for value in contention_counts):
                raise ValueError("Contention audit requires eligible and contender counts.")
            eligible, contenders = contention_counts
            if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (eligible, contenders)) or contenders > eligible:
                raise ValueError("Contention counts must be non-negative integers with contenders <= eligible.")
            if self.assigned_vehicle_id is None:
                if any(value is not None for value in contention_selected) or contenders != 0:
                    raise ValueError("Unassigned contention requests cannot retain a selected contender.")
            else:
                if any(value is None for value in contention_selected) or contenders == 0:
                    raise ValueError("Assigned contention requests require a complete selected-contender audit.")
                grid, distance, unit, request_utility, alternative, margin = contention_selected
                if grid not in grids or any(not math.isfinite(float(value)) for value in (distance, request_utility, alternative, margin)):
                    raise ValueError("Selected contention audit values must be finite and use a canonical grid.")
                if unit != "EPSG:2263 feet":
                    raise ValueError("Selected pickup distance must retain its projected canonical-grid unit.")
                if float(distance) < 0 or not math.isclose(float(margin), float(request_utility) - float(alternative)):
                    raise ValueError("Selected contention distance/margin is invalid.")
        audit_values = (self.pricing_factor, self.offered_fare)
        historical_values = (
            self.weather_code, self.period, self.historical_p_base, self.historical_d_base,
            self.epsilon_customer, self.p_max,
        )
        if any(value is not None for value in audit_values + historical_values) or self.customer_accepted is not None or self.customer_model is not None:
            if self.base_fare is None or any(value is None for value in audit_values) or not isinstance(self.customer_accepted, bool):
                raise ValueError("Priced requests require the complete pricing and acceptance audit.")
            factor, offered = (float(value) for value in audit_values)  # type: ignore[arg-type]
            if not all(math.isfinite(value) for value in (base, factor, offered)):
                raise ValueError("Request pricing values must be finite.")
            if base < 0 or factor <= 0 or offered < 0:
                raise ValueError("Request pricing values are outside their valid ranges.")
            if self.customer_model == "eq31":
                if self.acceptance_probability is None or any(value is not None for value in historical_values):
                    raise ValueError("Eq.31 requests require probability and no historical-sensitivity audit.")
                probability = float(self.acceptance_probability)
                if not math.isfinite(probability) or not 0 <= probability <= 1:
                    raise ValueError("Eq.31 acceptance probability must be finite and in [0, 1].")
            elif self.customer_model == "historical_sensitivity":
                if self.acceptance_probability is not None or any(value is None for value in historical_values):
                    raise ValueError("Historical-sensitivity requests require the complete deterministic audit.")
                weather, period, p_base, d_base, epsilon, p_max = historical_values
                numeric = tuple(float(value) for value in (weather, p_base, d_base, epsilon, p_max))
                if not all(math.isfinite(value) for value in numeric) or numeric[1] <= 0 or numeric[2] <= 0 or numeric[3] <= 0:
                    raise ValueError("Historical-sensitivity audit values are invalid.")
                if isinstance(period, bool) or not isinstance(period, int) or not 0 <= period <= 47:
                    raise ValueError("Historical-sensitivity Period must be an integer in 0..47.")
            else:
                raise ValueError("Priced requests require a recognized customer_model.")
        request_level_values = (
            self.pricing_context, self.selected_arm, self.linucb_reward,
            self.raw_served_revenue, self.linucb_learning_reward, self.sensitivity_lookup_level,
        )
        if any(value is not None for value in request_level_values):
            if self.pricing_context is None or self.selected_arm is None:
                raise ValueError("Request-level pricing requires its context and selected arm.")
            if len(self.pricing_context) != 8 or not all(math.isfinite(float(value)) and 0 <= float(value) <= 1 for value in self.pricing_context):
                raise ValueError("Request-level pricing context must contain eight finite bounded values.")
            if isinstance(self.selected_arm, bool) or not isinstance(self.selected_arm, int) or not 0 <= self.selected_arm < 7:
                raise ValueError("Request-level selected_arm must be an index in 0..6.")
            if self.linucb_reward is not None and (not math.isfinite(float(self.linucb_reward)) or self.linucb_reward < 0):
                raise ValueError("Request-level LinUCB reward must be finite and non-negative.")
            for name, value in (("raw_served_revenue", self.raw_served_revenue), ("linucb_learning_reward", self.linucb_learning_reward)):
                if value is not None and (not math.isfinite(float(value)) or value < 0):
                    raise ValueError(f"Request-level {name} must be finite and non-negative.")
            if self.linucb_reward is not None and self.linucb_learning_reward is not None and not math.isclose(self.linucb_reward, self.linucb_learning_reward):
                raise ValueError("linucb_reward must retain the request learning-reward value.")
            if self.sensitivity_lookup_level is not None and self.sensitivity_lookup_level not in {"exact", "period", "weather", "global"}:
                raise ValueError("Sensitivity lookup level is invalid.")
        if self.status is RequestStatus.PENDING:
            if self.assigned_vehicle_id is not None or self.assigned_vehicle_origin_grid is not None or self.wait_time is not None:
                raise ValueError("PENDING requests cannot have assignment or wait-time results.")
        elif self.status is RequestStatus.ASSIGNED:
            if not isinstance(self.assigned_vehicle_id, int) or self.assigned_vehicle_id < 0 or self.assigned_vehicle_origin_grid not in grids or self.wait_time is None:
                raise ValueError("ASSIGNED requests require vehicle_id and wait_time.")
            if self.wait_time < 0:
                raise ValueError("wait_time cannot be negative.")
            if self.trip_start_minute is not None or self.busy_until_minute is not None:
                if self.trip_start_minute is None or self.busy_until_minute is None or self.trip_duration_minutes is None:
                    raise ValueError("Trip timing audit must be complete.")
                if not math.isclose(self.busy_until_minute - self.trip_start_minute, self.trip_duration_minutes):
                    raise ValueError("busy_until_minute must equal start plus empirical duration.")
        elif self.assigned_vehicle_id is not None or self.assigned_vehicle_origin_grid is not None or self.wait_time is not None:
            raise ValueError("UNSERVED requests do not fabricate assignment or wait time.")
