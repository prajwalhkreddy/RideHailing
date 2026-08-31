"""NB9 grid/main-slot operational statistics and incremental EWMA state.

The plan defines the observed measures and EWMA equation.  Alpha, first-
observation initialization, population SD, and no-observation carry-forward
are deliberately configurable engineering baselines, not final methodology.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Collection, Iterable, Mapping

import numpy as np
import pandas as pd

from src.dispatch.request import RequestState, RequestStatus
from src.dispatch.dispatch import DriverWaitObservation


@dataclass(frozen=True)
class FareObservation:
    """An externally supplied fare outcome; only successful observations count."""

    grid_id: int
    fare: float
    successful: bool = True


@dataclass(frozen=True)
class EWMAState:
    """Carried state from completed slot t to t+1 for one canonical grid."""

    ewma_fare: float | None = None
    ewma_wait: float | None = None
    ewma_std_fare: float | None = None
    ewma_std_wait: float | None = None


@dataclass(frozen=True)
class GridSlotStatistics:
    """Current slot measures plus the carried/updated EWMA routing features."""

    grid_id: int
    slot_id: int
    fare_count: int
    mean_fare: float | None
    std_fare: float | None
    wait_count: int
    mean_wait: float | None
    std_wait: float | None
    ewma_fare: float | None
    ewma_wait: float | None
    ewma_std_fare: float | None
    ewma_std_wait: float | None
    charging_available: float | None = None
    charging_wait: float | None = None


def _validate_alpha(alpha: float) -> None:
    if not isinstance(alpha, (int, float)) or not 0 < alpha <= 1:
        raise ValueError("ewma_alpha must be in (0, 1].")


def _validated_values(values: Iterable[float], name: str) -> list[float]:
    result = [float(value) for value in values]
    if any(not math.isfinite(value) or value < 0 for value in result):
        raise ValueError(f"{name} observations must be finite and non-negative.")
    return result


class OperationalStatistics:
    """Incremental grid-level NB9 state without pricing, EV, or routing logic."""

    def __init__(self, valid_grid_ids: Collection[int], ewma_alpha: float, ewma_initialization: str = "first_observation") -> None:
        _validate_alpha(ewma_alpha)
        if ewma_initialization != "first_observation":
            raise ValueError("Only the provisional first_observation EWMA initialization is supported.")
        self.valid_grid_ids = tuple(sorted(set(valid_grid_ids)))
        if not self.valid_grid_ids:
            raise ValueError("Operational statistics require canonical valid GridIDs.")
        self.ewma_alpha = float(ewma_alpha)
        self.ewma_initialization = ewma_initialization
        self.ewma_state = {grid_id: EWMAState() for grid_id in self.valid_grid_ids}

    def update_slot(
        self,
        slot_id: int,
        fare_observations: Iterable[FareObservation] = (),
        requests: Iterable[RequestState] = (),
        charging_observations: Mapping[int, tuple[bool, float]] | None = None,
        driver_wait_observations: Iterable[DriverWaitObservation] = (),
    ) -> list[GridSlotStatistics]:
        """Aggregate a completed main slot and update EWMAs once per grid.

        Unserved requests intentionally contribute no waiting observation: the
        dispatch baseline has no finalized wait duration for them.  Real fares
        must arrive from a later pricing/dispatch integration as explicit
        successful-trip observations; this module creates none itself.
        """
        if not isinstance(slot_id, int) or slot_id < 0:
            raise ValueError("slot_id must be a non-negative integer.")
        fares = {grid_id: [] for grid_id in self.valid_grid_ids}
        waits = {grid_id: [] for grid_id in self.valid_grid_ids}
        valid = set(self.valid_grid_ids)
        charging = dict(charging_observations or {})
        if not set(charging).issubset(valid):
            raise ValueError("Charging observations reference invalid GridIDs.")
        for available, wait in charging.values():
            if not isinstance(available, bool) or not isinstance(wait, (int, float)) or not math.isfinite(wait) or wait < 0:
                raise ValueError("Charging observations require boolean availability and non-negative wait.")
        for observation in fare_observations:
            if observation.grid_id not in valid:
                raise ValueError("Fare observation references an invalid GridID.")
            if observation.successful:
                fares[observation.grid_id].extend(_validated_values([observation.fare], "Fare"))
        for observation in driver_wait_observations:
            if observation.grid_id not in valid:
                raise ValueError("Driver waiting observation references an invalid GridID.")
            waits[observation.grid_id].extend(_validated_values([observation.wait_minutes], "Wait"))

        results: list[GridSlotStatistics] = []
        for grid_id in self.valid_grid_ids:
            fare_count, mean_fare, std_fare = _summarize(fares[grid_id])
            wait_count, mean_wait, std_wait = _summarize(waits[grid_id])
            previous = self.ewma_state[grid_id]
            updated = EWMAState(
                ewma_fare=_update_ewma(previous.ewma_fare, mean_fare, self.ewma_alpha),
                ewma_wait=_update_ewma(previous.ewma_wait, mean_wait, self.ewma_alpha),
                ewma_std_fare=_update_ewma(previous.ewma_std_fare, std_fare, self.ewma_alpha),
                ewma_std_wait=_update_ewma(previous.ewma_std_wait, std_wait, self.ewma_alpha),
            )
            self.ewma_state[grid_id] = updated
            charging_available, charging_wait = charging.get(grid_id, (None, None))
            results.append(GridSlotStatistics(
                grid_id=grid_id, slot_id=slot_id,
                fare_count=fare_count, mean_fare=mean_fare, std_fare=std_fare,
                wait_count=wait_count, mean_wait=mean_wait, std_wait=std_wait,
                ewma_fare=updated.ewma_fare, ewma_wait=updated.ewma_wait,
                ewma_std_fare=updated.ewma_std_fare, ewma_std_wait=updated.ewma_std_wait,
                # NB10 is the only producer; non-station grids remain missing.
                charging_available=charging_available, charging_wait=charging_wait,
            ))
        return results


def _summarize(values: list[float]) -> tuple[int, float | None, float | None]:
    """Return count/mean/population-SD; absence remains explicitly missing."""
    if not values:
        return 0, None, None
    array = np.asarray(values, dtype=np.float64)
    return len(array), float(array.mean()), float(array.std(ddof=0))


def _update_ewma(previous: float | None, current: float | None, alpha: float) -> float | None:
    """Apply first-observation initialization or carry the prior EWMA forward."""
    if current is None:
        return previous
    return current if previous is None else alpha * current + (1 - alpha) * previous


def routing_feature_frame(records: Iterable[GridSlotStatistics]) -> pd.DataFrame:
    """Export operational routing *features*, never routing probabilities."""
    rows = [record.__dict__ for record in records]
    columns = ["grid_id", "slot_id", "mean_fare", "std_fare", "ewma_fare", "ewma_std_fare", "mean_wait", "std_wait", "ewma_wait", "ewma_std_wait", "charging_available", "charging_wait"]
    return pd.DataFrame(rows)[columns] if rows else pd.DataFrame(columns=columns)
