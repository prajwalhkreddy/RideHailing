"""Demand-to-request generation with January 2026 empirical OD sampling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState


MILES_TO_KM = 1.609344
MAIN_SLOT_MINUTES = 30
MINI_SLOT_MINUTES = 2


def historical_bucket_start(pickup_datetime) -> pd.Timestamp:
    """Floor an empirical pickup to its historical 30-minute bucket."""
    pickup = pd.Timestamp(pickup_datetime)
    if pd.isna(pickup):
        raise ValueError("Empirical pickup timestamp must be valid.")
    return pickup.floor(f"{MAIN_SLOT_MINUTES}min")


def empirical_within_slot_offset_seconds(pickup_datetime) -> float:
    """Return the pickup's offset within its historical half-hour bucket."""
    pickup = pd.Timestamp(pickup_datetime)
    offset = float((pickup - historical_bucket_start(pickup)).total_seconds())
    if not 0 <= offset < MAIN_SLOT_MINUTES * 60:
        raise ValueError("Empirical pickup offset must lie within one 30-minute slot.")
    return offset


def empirical_mini_slot_index(pickup_datetime) -> int:
    """Map empirical within-slot position to one of fifteen two-minute slots."""
    index = int(empirical_within_slot_offset_seconds(pickup_datetime) // (MINI_SLOT_MINUTES * 60))
    if not 0 <= index < MAIN_SLOT_MINUTES // MINI_SLOT_MINUTES:
        raise ValueError("Empirical mini-slot index must be in 0..14.")
    return index


@dataclass(frozen=True)
class EmpiricalTripRecord:
    source_trip_id: int
    origin_grid: int
    destination_grid: int
    pickup_datetime: pd.Timestamp
    dropoff_datetime: pd.Timestamp
    duration_minutes: float
    distance_miles: float
    distance_km: float
    base_fare: float


@dataclass(frozen=True)
class EmpiricalODDistribution:
    """January empirical ``P(DOGridID | PUGridID)`` counts and samplers."""

    destinations: dict[int, np.ndarray]
    probabilities: dict[int, np.ndarray]
    origin_counts: dict[int, int]
    total_trips: int
    od_pair_count: int
    empirical_trips: pd.DataFrame | None = None
    origin_row_positions: dict[int, np.ndarray] | None = None
    source_trip_count: int | None = None
    excluded_invalid_trip_count: int = 0

    def sample_destination(self, origin_grid: int, rng: np.random.Generator) -> int:
        """Sample an unmodified empirical destination for one origin request."""
        if origin_grid not in self.destinations:
            raise ValueError(f"No empirical January OD distribution exists for origin GridID {origin_grid}.")
        return int(rng.choice(self.destinations[origin_grid], p=self.probabilities[origin_grid]))

    def sample_trip(self, origin_grid: int, rng: np.random.Generator) -> EmpiricalTripRecord:
        """Sample one intact empirical row, preserving its joint trip fields."""
        if self.empirical_trips is None or self.origin_row_positions is None or origin_grid not in self.origin_row_positions:
            raise ValueError(f"No empirical trip-record sampler exists for origin GridID {origin_grid}.")
        position = int(rng.choice(self.origin_row_positions[origin_grid]))
        row = self.empirical_trips.iloc[position]
        return EmpiricalTripRecord(
            source_trip_id=int(row["source_trip_id"]),
            origin_grid=int(row["PUGridID"]), destination_grid=int(row["DOGridID"]),
            pickup_datetime=pd.Timestamp(row["tpep_pickup_datetime"]),
            dropoff_datetime=pd.Timestamp(row["tpep_dropoff_datetime"]),
            duration_minutes=float(row["trip_duration_minutes"]),
            distance_miles=float(row["trip_distance_miles"]),
            distance_km=float(row["trip_distance_km"]), base_fare=float(row["fare_amount"]),
        )


def build_empirical_od_distribution(trips: pd.DataFrame, valid_grid_ids: Collection[int]) -> EmpiricalODDistribution:
    """Construct exact January OD conditional distributions from frozen trips.

    This is the approved research-data-based baseline.  It only reads the
    frozen ``PUGridID``/``DOGridID`` assignments; no spatial stage is rebuilt.
    """
    required = {"PUGridID", "DOGridID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "trip_distance", "fare_amount"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack empirical OD columns: {sorted(missing)}")
    valid = set(valid_grid_ids)
    source = trips[list(required)].copy()
    source.insert(0, "source_trip_id", np.arange(len(source), dtype=np.int64))
    source["trip_duration_minutes"] = (pd.to_datetime(source["tpep_dropoff_datetime"]) - pd.to_datetime(source["tpep_pickup_datetime"])).dt.total_seconds() / 60.0
    source["trip_distance_miles"] = pd.to_numeric(source["trip_distance"], errors="coerce")
    source["trip_distance_km"] = source["trip_distance_miles"] * MILES_TO_KM
    numeric = source[["trip_duration_minutes", "trip_distance_miles", "trip_distance_km", "fare_amount"]].to_numpy(dtype=np.float64)
    valid_rows = np.isfinite(numeric).all(axis=1) & (source["trip_duration_minutes"] > 0) & (source["trip_distance_miles"] >= 0) & (source["fare_amount"] >= 0)
    empirical = source.loc[valid_rows].reset_index(drop=True)
    if empirical.empty:
        raise ValueError("No valid empirical trips remain after duration/distance/fare runtime validation.")
    od = empirical[["PUGridID", "DOGridID"]].copy()
    if od.isna().any().any():
        raise ValueError("Frozen trips contain missing PUGridID/DOGridID values.")
    od = od.astype({"PUGridID": "int64", "DOGridID": "int64"})
    empirical = empirical.astype({"PUGridID": "int64", "DOGridID": "int64"})
    if not set(od["PUGridID"]).issubset(valid) or not set(od["DOGridID"]).issubset(valid):
        raise ValueError("Frozen trips contain OD GridIDs outside the canonical grid.")
    counts = od.groupby(["PUGridID", "DOGridID"], observed=True).size().rename("count").reset_index().sort_values(["PUGridID", "DOGridID"])
    destinations: dict[int, np.ndarray] = {}
    probabilities: dict[int, np.ndarray] = {}
    origin_counts: dict[int, int] = {}
    for origin, group in counts.groupby("PUGridID", sort=True, observed=True):
        destination_values = group["DOGridID"].to_numpy(dtype=np.int64)
        count_values = group["count"].to_numpy(dtype=np.int64)
        total = int(count_values.sum())
        destinations[int(origin)] = destination_values
        probabilities[int(origin)] = (count_values / total).astype(np.float64)
        origin_counts[int(origin)] = total
    positions = {
        int(origin): group.index.to_numpy(dtype=np.int64)
        for origin, group in empirical.groupby("PUGridID", sort=True, observed=True)
    }
    distribution = EmpiricalODDistribution(
        destinations, probabilities, origin_counts, int(len(od)), int(len(counts)),
        empirical, positions, int(len(source)), int(len(source) - len(empirical)),
    )
    if sum(distribution.origin_counts.values()) != distribution.total_trips:
        raise ValueError("Empirical OD counts do not reconcile with source trips.")
    return distribution


def generate_requests(
    grid_demand: Mapping[int, int],
    od_distribution: EmpiricalODDistribution,
    valid_grid_ids: Collection[int],
    mini_slots_per_main_slot: int,
    random_seed: int | None,
    request_id_start: int = 0,
    *,
    rng: np.random.Generator | None = None,
) -> list[RequestState]:
    """Generate exactly one request per integer demand unit.

    The sampled row's empirical position within its historical half-hour maps
    deterministically to the corresponding two-minute simulated mini-slot.
    Origins are processed in GridID order, then requests are ordered FCFS.
    """
    valid = set(valid_grid_ids)
    if mini_slots_per_main_slot <= 0:
        raise ValueError("mini_slots_per_main_slot must be positive.")
    if mini_slots_per_main_slot != MAIN_SLOT_MINUTES // MINI_SLOT_MINUTES:
        raise ValueError("Empirical arrival mapping requires 15 two-minute mini-slots.")
    if not isinstance(request_id_start, int) or request_id_start < 0:
        raise ValueError("request_id_start must be non-negative.")
    if rng is not None and random_seed is not None:
        raise ValueError("Supply either random_seed or a persistent rng, not both.")
    if rng is None:
        if random_seed is None:
            raise ValueError("Request generation requires random_seed or a persistent rng.")
        rng = np.random.default_rng(random_seed)
    elif not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be a numpy.random.Generator.")
    requests: list[RequestState] = []
    request_id = request_id_start
    for origin_grid, demand in sorted(grid_demand.items()):
        if origin_grid not in valid:
            raise ValueError("Demand contains a non-canonical origin GridID.")
        if not isinstance(demand, (int, np.integer)) or demand < 0:
            raise ValueError("Grid demand must be a non-negative integer count.")
        for _ in range(int(demand)):
            trip = od_distribution.sample_trip(int(origin_grid), rng)
            offset_seconds = empirical_within_slot_offset_seconds(trip.pickup_datetime)
            requests.append(RequestState(
                request_id=request_id,
                request_time=empirical_mini_slot_index(trip.pickup_datetime),
                origin_grid=int(origin_grid),
                destination_grid=trip.destination_grid,
                base_fare=trip.base_fare,
                source_trip_id=trip.source_trip_id,
                empirical_pickup_datetime=trip.pickup_datetime.to_pydatetime(),
                empirical_dropoff_datetime=trip.dropoff_datetime.to_pydatetime(),
                trip_duration_minutes=trip.duration_minutes,
                trip_distance_miles=trip.distance_miles,
                trip_distance_km=trip.distance_km,
                empirical_within_slot_offset_seconds=offset_seconds,
            ))
            request_id += 1
    if len(requests) != sum(int(value) for value in grid_demand.values()):
        raise ValueError("Generated request count does not reconcile with supplied demand.")
    for request in requests:
        request.validate(valid, mini_slots_per_main_slot)
    return sorted(requests, key=lambda request: (request.request_time, request.request_id))


def validate_od_distribution(distribution: EmpiricalODDistribution, valid_grid_ids: Collection[int]) -> None:
    """Validate OD probabilities and source-count reconciliation."""
    valid = set(valid_grid_ids)
    if sum(distribution.origin_counts.values()) != distribution.total_trips:
        raise ValueError("Empirical OD distribution no longer reconciles with source trip counts.")
    for origin, destinations in distribution.destinations.items():
        probabilities = distribution.probabilities.get(origin)
        if origin not in valid or probabilities is None or not set(destinations).issubset(valid):
            raise ValueError("Empirical OD distribution references invalid GridIDs.")
        if len(destinations) != len(probabilities) or not np.isclose(probabilities.sum(), 1.0):
            raise ValueError("Empirical OD probabilities must sum to one per origin.")
