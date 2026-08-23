"""Demand-to-request generation with January 2026 empirical OD sampling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState


@dataclass(frozen=True)
class EmpiricalODDistribution:
    """January empirical ``P(DOGridID | PUGridID)`` counts and samplers."""

    destinations: dict[int, np.ndarray]
    probabilities: dict[int, np.ndarray]
    origin_counts: dict[int, int]
    total_trips: int
    od_pair_count: int

    def sample_destination(self, origin_grid: int, rng: np.random.Generator) -> int:
        """Sample an unmodified empirical destination for one origin request."""
        if origin_grid not in self.destinations:
            raise ValueError(f"No empirical January OD distribution exists for origin GridID {origin_grid}.")
        return int(rng.choice(self.destinations[origin_grid], p=self.probabilities[origin_grid]))


def build_empirical_od_distribution(trips: pd.DataFrame, valid_grid_ids: Collection[int]) -> EmpiricalODDistribution:
    """Construct exact January OD conditional distributions from frozen trips.

    This is the approved research-data-based baseline.  It only reads the
    frozen ``PUGridID``/``DOGridID`` assignments; no spatial stage is rebuilt.
    """
    required = {"PUGridID", "DOGridID"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack empirical OD columns: {sorted(missing)}")
    valid = set(valid_grid_ids)
    od = trips[["PUGridID", "DOGridID"]].copy()
    if od.isna().any().any():
        raise ValueError("Frozen trips contain missing PUGridID/DOGridID values.")
    od = od.astype({"PUGridID": "int64", "DOGridID": "int64"})
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
    distribution = EmpiricalODDistribution(destinations, probabilities, origin_counts, int(len(od)), int(len(counts)))
    if sum(distribution.origin_counts.values()) != distribution.total_trips:
        raise ValueError("Empirical OD counts do not reconcile with source trips.")
    return distribution


def generate_requests(
    grid_demand: Mapping[int, int],
    od_distribution: EmpiricalODDistribution,
    valid_grid_ids: Collection[int],
    mini_slots_per_main_slot: int,
    random_seed: int,
    request_id_start: int = 0,
) -> list[RequestState]:
    """Generate exactly one request per integer demand unit.

    Mini-slot placement is the approved engineering baseline: a seeded uniform
    draw over ``0..mini_slots_per_main_slot-1``.  Origins are processed in
    GridID order, then requests are ordered FCFS by mini-slot and request ID.
    """
    valid = set(valid_grid_ids)
    if mini_slots_per_main_slot <= 0:
        raise ValueError("mini_slots_per_main_slot must be positive.")
    if not isinstance(request_id_start, int) or request_id_start < 0:
        raise ValueError("request_id_start must be non-negative.")
    rng = np.random.default_rng(random_seed)
    requests: list[RequestState] = []
    request_id = request_id_start
    for origin_grid, demand in sorted(grid_demand.items()):
        if origin_grid not in valid:
            raise ValueError("Demand contains a non-canonical origin GridID.")
        if not isinstance(demand, (int, np.integer)) or demand < 0:
            raise ValueError("Grid demand must be a non-negative integer count.")
        for _ in range(int(demand)):
            requests.append(RequestState(
                request_id=request_id,
                request_time=int(rng.integers(0, mini_slots_per_main_slot)),
                origin_grid=int(origin_grid),
                destination_grid=od_distribution.sample_destination(int(origin_grid), rng),
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
