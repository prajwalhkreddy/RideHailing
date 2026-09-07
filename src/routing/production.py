"""Reproducible production initialization contracts for NB11/NB12/NB13."""

from __future__ import annotations

from collections.abc import Iterator, Iterable, Mapping
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.pricing.historical_sensitivity import TRAINING_END_EXCLUSIVE, TRAINING_START
from src.charging.energy import EnergyParameters, energy_consumed_kwh
from src.fleet.state import VehicleState
from src.routing.baseline import (
    ACTION_ORDER, CandidateUtilityInput, RoutingAction, RoutingParameters,
    RoutingState, valid_action_mask,
)
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters
from src.simulation.statistics import EWMAState, OperationalStatistics


PROFILE_GENERATION_VERSION = "driver-preferences-v1"


def normalized_dod_degradation_penalty(
    projected_energy_kwh: float,
    energy: EnergyParameters,
) -> float:
    """Return the production normalized DOD-based degradation penalty.

    Chauhan & Jain's G2V DOD term is proportional to the recharge energy.
    The project normalizes that term by recharge from its frozen charging
    threshold to full capacity.  This is not measured SOH loss and does not
    include the paper's separate temperature-dependent component.
    """
    energy.validate()
    projected = float(projected_energy_kwh)
    if not np.isfinite(projected):
        raise ValueError("projected_energy_kwh must be finite.")
    maximum_recharge = energy.battery_capacity_kwh * (1.0 - energy.charging_trigger_soc)
    if maximum_recharge <= 0:
        raise ValueError("DOD normalization requires a charging threshold below full SOC.")
    return float(np.clip(
        (energy.battery_capacity_kwh - projected) / maximum_recharge,
        0.0,
        1.0,
    ))


def production_profile_utility_inputs(
    profiles: pd.DataFrame,
    vehicles: Iterable[VehicleState],
    energy: EnergyParameters,
    routing: RoutingParameters,
) -> dict[int, dict[RoutingAction, CandidateUtilityInput]]:
    """Assemble runtime/action-dependent production NB11 utility inputs."""
    required = {"vehicle_id", "price_preference", "wait_preference"}
    if missing := required - set(profiles.columns):
        raise ValueError(f"Driver profiles lack columns: {sorted(missing)}")
    if profiles["vehicle_id"].duplicated().any():
        raise ValueError("Driver profiles must be unique by vehicle_id.")
    vehicle_energy = {int(vehicle.vehicle_id): float(vehicle.energy_level) for vehicle in vehicles}
    if set(profiles["vehicle_id"].astype(int)) != set(vehicle_energy):
        raise ValueError("Production driver profiles must exactly cover the runtime fleet.")
    routing.validate()
    movement_energy = energy_consumed_kwh(routing.reposition_distance_km, energy)
    result: dict[int, dict[RoutingAction, CandidateUtilityInput]] = {}
    for row in profiles.itertuples(index=False):
        vehicle_id = int(row.vehicle_id)
        current_energy = vehicle_energy[vehicle_id]
        by_action: dict[RoutingAction, CandidateUtilityInput] = {}
        for action in ACTION_ORDER:
            projected = current_energy if action is RoutingAction.STAY else current_energy - movement_energy
            by_action[action] = CandidateUtilityInput(
                float(row.price_preference),
                float(row.wait_preference),
                normalized_dod_degradation_penalty(projected, energy),
            )
        result[vehicle_id] = by_action
    return result


class RuntimeProductionUtilityInputs(Mapping[int, Mapping[RoutingAction, CandidateUtilityInput]]):
    """Lazily assemble NB11 inputs from each vehicle's current energy state."""

    def __init__(
        self, profiles: pd.DataFrame, vehicles: Iterable[VehicleState],
        energy: EnergyParameters, routing: RoutingParameters,
    ) -> None:
        required = {"vehicle_id", "price_preference", "wait_preference"}
        if missing := required - set(profiles.columns):
            raise ValueError(f"Driver profiles lack columns: {sorted(missing)}")
        if profiles["vehicle_id"].duplicated().any():
            raise ValueError("Driver profiles must be unique by vehicle_id.")
        self._profiles = {
            int(row.vehicle_id): (float(row.price_preference), float(row.wait_preference))
            for row in profiles.itertuples(index=False)
        }
        self._vehicles = {int(vehicle.vehicle_id): vehicle for vehicle in vehicles}
        if set(self._profiles) != set(self._vehicles):
            raise ValueError("Production driver profiles must exactly cover the runtime fleet.")
        energy.validate()
        routing.validate()
        self._energy = energy
        self._move_energy_kwh = energy_consumed_kwh(routing.reposition_distance_km, energy)

    def __len__(self) -> int:
        return len(self._profiles)

    def __iter__(self) -> Iterator[int]:
        return iter(self._profiles)

    def __getitem__(self, vehicle_id: int) -> Mapping[RoutingAction, CandidateUtilityInput]:
        price, wait = self._profiles[int(vehicle_id)]
        current = float(self._vehicles[int(vehicle_id)].energy_level)
        return {
            action: CandidateUtilityInput(
                price, wait,
                normalized_dod_degradation_penalty(
                    current if action is RoutingAction.STAY else current - self._move_energy_kwh,
                    self._energy,
                ),
            )
            for action in ACTION_ORDER
        }


def valid_training_fares(trips: pd.DataFrame) -> pd.Series:
    """Return finite positive fares with pickup timestamps strictly pre-cutoff."""
    required = {"tpep_pickup_datetime", "fare_amount"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack driver-profile columns: {sorted(missing)}")
    pickup = pd.to_datetime(trips["tpep_pickup_datetime"], errors="coerce")
    fare = pd.to_numeric(trips["fare_amount"], errors="coerce")
    valid = pickup.notna() & (pickup >= TRAINING_START) & (pickup < TRAINING_END_EXCLUSIVE) & np.isfinite(fare) & (fare > 0)
    result = fare.loc[valid].astype("float64").reset_index(drop=True)
    if result.empty:
        raise ValueError("No valid pre-cutoff fare observations remain for driver profiles.")
    return result


def generate_driver_profiles(trips: pd.DataFrame, vehicle_ids: Iterable[int], *, seed: int = 42) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Sample one persistent price/wait preference for each production driver."""
    ids = np.asarray(list(vehicle_ids), dtype=np.int64)
    if ids.ndim != 1 or len(ids) == 0 or len(np.unique(ids)) != len(ids) or (ids < 0).any():
        raise ValueError("vehicle_ids must be a non-empty unique sequence of non-negative IDs.")
    fares = valid_training_fares(trips)
    mean, sigma = float(fares.mean()), float(fares.std(ddof=0))
    low, high = max(0.0, mean - sigma), mean + sigma
    rng = np.random.default_rng(seed)
    profiles = pd.DataFrame({
        "vehicle_id": ids,
        "price_preference": rng.uniform(low, high, len(ids)),
        "wait_preference": rng.uniform(0.0, 30.0, len(ids)),
    })
    return profiles, {"fare_valid_row_count": len(fares), "mu_price": mean, "sigma_price": sigma, "price_low": low, "price_high": high}


def build_fare_bootstrap(trips: pd.DataFrame, valid_grid_ids: Iterable[int]) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Build pre-cutoff pickup-grid fare priors with a global fallback."""
    if "PUGridID" not in trips:
        raise ValueError("Trips lack fare-bootstrap column PUGridID.")
    pickup = pd.to_datetime(trips["tpep_pickup_datetime"], errors="coerce")
    fare = pd.to_numeric(trips["fare_amount"], errors="coerce")
    grid = pd.to_numeric(trips["PUGridID"], errors="coerce")
    valid = pickup.notna() & (pickup >= TRAINING_START) & (pickup < TRAINING_END_EXCLUSIVE) & np.isfinite(fare) & (fare > 0) & np.isfinite(grid) & (grid % 1 == 0)
    work = pd.DataFrame({"grid_id": grid.loc[valid].astype("int64"), "fare": fare.loc[valid].astype("float64")})
    grids = tuple(sorted(set(int(value) for value in valid_grid_ids)))
    work = work.loc[work.grid_id.isin(grids)]
    if work.empty:
        raise ValueError("No finite positive pre-cutoff fares remain for the historical bootstrap.")
    global_mean, global_std = float(work.fare.mean()), float(work.fare.std(ddof=0))
    if not np.isfinite([global_mean, global_std]).all():
        raise ValueError("Global historical fare bootstrap is non-finite.")
    grouped = work.groupby("grid_id", observed=True).fare.agg(historical_fare_count="size", mean_fare="mean", std_fare=lambda values: values.std(ddof=0))
    rows = []
    for grid_id in grids:
        if grid_id in grouped.index and np.isfinite(grouped.loc[grid_id, ["mean_fare", "std_fare"]].to_numpy(dtype=float)).all():
            row = grouped.loc[grid_id]
            rows.append((grid_id, int(row.historical_fare_count), float(row.mean_fare), float(row.std_fare), "grid"))
        else:
            rows.append((grid_id, 0, global_mean, global_std, "global_fallback"))
    result = pd.DataFrame(rows, columns=["grid_id", "historical_fare_count", "mean_fare", "std_fare", "source_level"])
    return result, {"global_valid_row_count": len(work), "global_mean_fare": global_mean, "global_std_fare": global_std, "grid_level_rows": int((result.source_level == "grid").sum()), "global_fallback_rows": int((result.source_level == "global_fallback").sum())}


def initialize_nb9_fare_prior(statistics: OperationalStatistics, bootstrap: pd.DataFrame) -> None:
    """Initialize fare EWMA fields without emitting any current observation."""
    if set(bootstrap.grid_id.astype(int)) != set(statistics.valid_grid_ids):
        raise ValueError("Fare bootstrap must cover every NB9 grid exactly once.")
    for row in bootstrap.itertuples(index=False):
        prior = statistics.ewma_state[int(row.grid_id)]
        statistics.ewma_state[int(row.grid_id)] = EWMAState(float(row.mean_fare), prior.ewma_wait, float(row.std_fare), prior.ewma_std_wait)


def profile_utility_inputs(profiles: pd.DataFrame, normalized_penalties: Mapping[int, float]) -> dict[int, dict[RoutingAction, CandidateUtilityInput]]:
    """Adapt static profiles plus an existing runtime penalty to all actions."""
    required = {"vehicle_id", "price_preference", "wait_preference"}
    if missing := required - set(profiles.columns):
        raise ValueError(f"Driver profiles lack columns: {sorted(missing)}")
    result = {}
    for row in profiles.itertuples(index=False):
        vehicle_id = int(row.vehicle_id)
        if vehicle_id not in normalized_penalties:
            raise ValueError(f"Vehicle {vehicle_id} lacks its runtime normalized degradation penalty.")
        candidate = CandidateUtilityInput(float(row.price_preference), float(row.wait_preference), float(normalized_penalties[vehicle_id]))
        result[vehicle_id] = {action: candidate for action in ACTION_ORDER}
    return result


def uniform_valid_action_probabilities(state: RoutingState) -> np.ndarray:
    """Return the neutral first-slot distribution, independent of model logits."""
    mask = valid_action_mask(state)
    array = np.asarray([mask[action] for action in ACTION_ORDER], dtype=bool)
    probabilities = np.zeros(len(ACTION_ORDER), dtype=np.float64)
    probabilities[array] = 1.0 / int(array.sum())
    return probabilities


def initialize_common_policy_learners(vehicle_ids: Iterable[int], parameters: RoutingLearningParameters, *, seed: int = 42) -> tuple[dict[int, LocalRoutingLearner], LocalRoutingLearner]:
    """Give every local learner and the global learner one identical seed state."""
    ids = tuple(int(value) for value in vehicle_ids)
    common = LocalRoutingLearner(-1, parameters, seed=seed)
    weights = common.policy_model.get_weights()
    locals_ = {}
    for vehicle_id in ids:
        learner = LocalRoutingLearner(vehicle_id, parameters, seed=seed)
        learner.reset_from_global_weights(weights)
        locals_[vehicle_id] = learner
    global_learner = LocalRoutingLearner(-1, parameters, seed=seed)
    global_learner.reset_from_global_weights(weights)
    return locals_, global_learner


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
