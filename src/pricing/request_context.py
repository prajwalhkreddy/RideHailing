"""Pure construction of the proposed request-level 8D pricing context."""

from __future__ import annotations

from datetime import datetime
import math
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel, ResolvedSensitivityParameters
from src.pricing.scaler import DEFAULT_PRICING_CONTEXT_SCALER, PricingContextScaler


REQUEST_PRICING_CONTEXT_FEATURE_ORDER = (
    "scaled_predicted_demand", "scaled_corrected_supply", "relevant_od_routing_probability",
    "destination_popularity", "scaled_trip_distance_km", "scaled_P_base",
    "scaled_time", "weather_severity",
)
REQUEST_PRICING_CONTEXT_DIMENSION = len(REQUEST_PRICING_CONTEXT_FEATURE_ORDER)
ROUTING_PROBABILITY_ORDER = ("STAY", "NORTH", "EAST", "SOUTH", "WEST")
WEATHER_SEVERITY: Mapping[int, float] = {
    1: 0.00, 2: 0.00, 3: 0.00,
    5: 0.25, 7: 0.25, 14: 0.25,
    8: 0.50, 15: 0.50, 21: 0.50,
    9: 0.75, 12: 0.75,
    13: 1.00, 16: 1.00,
}


def grid_positions(grid_lookup: pd.DataFrame) -> dict[int, tuple[int, int]]:
    required = {"GridID", "Row", "Column"}
    if missing := required - set(grid_lookup.columns):
        raise ValueError(f"Grid lookup lacks request-context columns: {sorted(missing)}")
    rows = grid_lookup[["GridID", "Row", "Column"]]
    if rows.empty or rows["GridID"].duplicated().any() or rows[["Row", "Column"]].duplicated().any() or rows.isna().any().any():
        raise ValueError("Grid lookup positions must be non-empty, complete, and unique.")
    return {
        int(item.GridID): (int(item.Row), int(item.Column))
        for item in rows.itertuples(index=False)
    }


def relevant_od_routing_probability(
    origin_grid: int,
    destination_grid: int,
    routing_probabilities: Sequence[float] | np.ndarray,
    grid_lookup: pd.DataFrame | Mapping[int, tuple[int, int]],
) -> float:
    """Return NB12 probability mass along all Manhattan-reducing directions."""
    probabilities = np.asarray(routing_probabilities, dtype=np.float64)
    if probabilities.shape != (5,) or not np.isfinite(probabilities).all() or (probabilities < 0).any():
        raise ValueError("Routing probabilities must be five finite non-negative values.")
    if not np.isclose(probabilities.sum(), 1.0, rtol=1e-7, atol=1e-8):
        raise ValueError("Routing probabilities must sum to one.")
    positions = grid_positions(grid_lookup) if isinstance(grid_lookup, pd.DataFrame) else grid_lookup
    if origin_grid not in positions or destination_grid not in positions:
        raise KeyError("Origin and destination must exist in the canonical grid lookup.")
    origin_row, origin_column = positions[origin_grid]
    destination_row, destination_column = positions[destination_grid]
    if (origin_row, origin_column) == (destination_row, destination_column):
        result = probabilities[0]
    else:
        indices: list[int] = []
        if destination_row < origin_row:
            indices.append(1)
        elif destination_row > origin_row:
            indices.append(3)
        if destination_column > origin_column:
            indices.append(2)
        elif destination_column < origin_column:
            indices.append(4)
        result = probabilities[indices].sum()
    value = float(result)
    if not 0.0 <= value <= 1.0:
        raise ValueError("Relevant OD routing probability must be within [0,1].")
    return value


def destination_popularity(
    popularity_table: pd.DataFrame | Mapping[int, float], simulation_timestamp: datetime, destination_grid: int,
) -> float:
    """Read the frozen current-slot, destination-grid popularity encoding."""
    if not isinstance(popularity_table, pd.DataFrame):
        if destination_grid not in popularity_table:
            raise KeyError(f"No cached destination popularity for GridID={destination_grid}.")
        value = float(popularity_table[destination_grid])
        if not math.isfinite(value) or value not in {0.0, 0.25, 0.5, 0.75, 1.0}:
            raise ValueError("Destination popularity must use the frozen five-level encoding.")
        return value
    required = {"TimeSlot", "GridID", "popularity_value"}
    if missing := required - set(popularity_table.columns):
        raise ValueError(f"Popularity artifact lacks request-context columns: {sorted(missing)}")
    timestamp = pd.Timestamp(simulation_timestamp)
    if timestamp.tz is not None or timestamp != timestamp.floor("30min"):
        raise ValueError("Pricing timestamp must be a timezone-naive 30-minute slot boundary.")
    times = pd.to_datetime(popularity_table["TimeSlot"], errors="coerce")
    matches = popularity_table.loc[
        (times == timestamp) & (popularity_table["GridID"] == destination_grid), "popularity_value"
    ]
    if len(matches) != 1:
        raise KeyError(f"Expected one popularity row for TimeSlot={timestamp} and GridID={destination_grid}.")
    value = float(matches.iloc[0])
    if not math.isfinite(value) or value not in {0.0, 0.25, 0.5, 0.75, 1.0}:
        raise ValueError("Destination popularity must use the frozen five-level encoding.")
    return value


def weather_severity(weather_code: float) -> float:
    numeric = float(weather_code)
    if not math.isfinite(numeric) or not numeric.is_integer() or int(numeric) not in WEATHER_SEVERITY:
        raise ValueError(f"Unknown WeatherCode for pricing severity: {weather_code}.")
    return WEATHER_SEVERITY[int(numeric)]


def build_request_pricing_context(
    *,
    request: RequestState,
    predicted_demand: float,
    corrected_supply: float,
    routing_probabilities: Sequence[float] | np.ndarray,
    simulation_timestamp: datetime,
    weather_code: float,
    grid_lookup: pd.DataFrame | Mapping[int, tuple[int, int]],
    popularity_table: pd.DataFrame | Mapping[int, float],
    historical_customer_model: HistoricalCustomerSensitivityModel,
    resolved_sensitivity: ResolvedSensitivityParameters | None = None,
    scaler: PricingContextScaler = DEFAULT_PRICING_CONTEXT_SCALER,
) -> np.ndarray:
    """Construct context only; perform no selection, sampling, acceptance, or dispatch."""
    if request.trip_distance_km is None:
        raise ValueError("Request-level pricing context requires trip_distance_km.")
    timestamp = pd.Timestamp(simulation_timestamp)
    if timestamp.tz is not None or timestamp != timestamp.floor("30min"):
        raise ValueError("Pricing timestamp must be a timezone-naive 30-minute slot boundary.")
    period = int(timestamp.hour * 2 + timestamp.minute // 30)
    if not 0 <= period <= 47:
        raise ValueError("Period must be an integer in 0..47.")
    resolved = resolved_sensitivity or historical_customer_model.resolve_parameters(float(weather_code), period)
    if resolved.requested_weather_code != float(weather_code) or resolved.requested_period != period:
        raise ValueError("Resolved sensitivity context does not match current WeatherCode and Period.")
    parameters = resolved.parameters
    context = np.asarray([
        scaler.scale_demand(predicted_demand),
        scaler.scale_supply(corrected_supply),
        relevant_od_routing_probability(
            request.origin_grid, request.destination_grid, routing_probabilities, grid_lookup,
        ),
        destination_popularity(popularity_table, timestamp.to_pydatetime(), request.destination_grid),
        scaler.scale_distance(request.trip_distance_km),
        scaler.scale_base_price(parameters.p_base),
        period / 47.0,
        weather_severity(weather_code),
    ], dtype=np.float64)
    if context.shape != (REQUEST_PRICING_CONTEXT_DIMENSION,) or not np.isfinite(context).all():
        raise ValueError("Request pricing context must be a finite eight-element vector.")
    if (context < 0).any() or (context > 1).any():
        raise ValueError("Request pricing context features must lie within [0,1].")
    return context
