"""Authoritative, stateful production simulation assembly.

This module loads reviewed production artifacts and wires existing model
components.  It contains no validation fixtures and no substitute inputs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from src.charging.energy import energy_parameters_from_config, initialize_ev_fleet
from src.charging.stations import ChargingInfrastructure, stations_from_definition, validate_station_definition
from src.data.config import load_config
from src.data.weather import load_processed_weather
from src.dispatch.contention import ContentionEvaluation, DriverContentionInputs, grid_centroids
from src.dispatch.dispatch import DISPATCH_MODEL_CONTENTION
from src.dispatch.generation import build_empirical_od_distribution, generate_requests
from src.fleet.fleet import Fleet, validate_fleet
from src.fleet.state import VehicleStatus
from src.fleet.supply import aggregate_grid_supply
from src.pricing.customer_sensitivity import HistoricalCustomerSensitivityModel
from src.pricing.linucb import DisjointLinUCB
from src.pricing.reward import REQUEST_REWARD_REF, REQUEST_REWARD_SCALING_TRAINING
from src.pricing.scaler import PricingContextScaler
from src.routing.baseline import (
    ACTION_ORDER, CandidateUtilityInput, RoutingAction, RoutingParameters,
    build_grid_routing_features,
)
from src.routing.learning import LocalRoutingLearner, routing_learning_parameters_from_config
from src.routing.production import (
    initialize_common_policy_learners, initialize_nb9_fare_prior,
    normalized_dod_degradation_penalty, sha256_file,
)
from src.simulation.main_slot import MainSlotResult, run_main_slot
from src.simulation.pricing_dispatch import (
    CUSTOMER_MODEL_HISTORICAL, PRICING_DECISION_MODE_REQUEST,
    REWARD_MODEL_SERVED, SUPPLY_MODEL_CORRECTED, PricingContextInput,
)
from src.simulation.statistics import GridSlotStatistics, OperationalStatistics


PRODUCTION_START = datetime(2026, 1, 25, 19, 0)
PRODUCTION_END_EXCLUSIVE = datetime(2026, 2, 1)
PRODUCTION_SLOT_COUNT = 298
FLEET_SIZE = 5000
EXPECTED_GRID_COUNT = 1213
EXPECTED_HASHES = {
    "cnn_predictions": "28959a92e1d4ee816fe09d817d91991f737f9d21c558e9c791bb9e76e533efe3",
    "cnn_model": "f4e093906f7c8d65a570dd8d8f174bc9aa2cf3888867e3434ad3a139ed529b78",
    "sensitivity": "2f9554665ced24d0cecfe136b9f7d3dd29d99ec2b4248c930909bbe6cf1b0088",
    "sensitivity_fallback": "8d511bb09421154b2185935db204af8497c42dd729db39333cb323fc0649e826",
    "pricing_scaler": "fcb617109b31408401d42dad2af96aee4ab7cc19c44d94d9ce080959a7215dff",
    "driver_profiles": "dcb422e5e492f44a85815aad5f22a50f833f7071a67a126edf09a09270c0764d",
    "fare_bootstrap": "38d9503b38b34c00f13ee39b4238ad197add0014a0c26d1d552c7da450ca0560",
    "routing_initialization": "d6b74cf700dd0a85890b878e992f689bb7c29715ea9c5974a53ec3cd187d9c75",
}


@dataclass(frozen=True)
class ProductionSource:
    path: str
    role: str
    authority: str
    sha256: str
    rows: int | None = None
    grids: int | None = None
    timestamps: int | None = None


@dataclass
class ProductionSlotReport:
    slot_index: int
    timestamp: str
    cnn_input_timestamp: str
    cnn_target_timestamp: str
    cnn_prediction_index: int
    routing_probability_source: str
    generated: int
    accepted: int
    rejected: int
    served: int
    accepted_unserved: int
    linucb_selections: int
    linucb_updates: int
    raw_served_revenue: float
    scaled_learning_reward: float
    fare_observations: int
    completed_waits: int
    nonzero_waits: int
    wait_min: float | None
    wait_median: float | None
    wait_mean: float | None
    wait_p95: float | None
    wait_max: float | None
    real_wait_history_grids: int
    runtime_fare_update_grids: int
    nb11_observations: int
    nb12_participants: int
    zero_observation_clients: int
    nb13_rounds: int
    global_parameter_change_norm: float
    action_stay: int
    action_north: int
    action_east: int
    action_south: int
    action_west: int
    mean_p_stay: float
    mean_p_north: float
    mean_p_east: float
    mean_p_south: float
    mean_p_west: float
    reposition_starts: int
    reposition_completions: int
    repositioning_at_boundary: int
    eligible_evaluations: int
    contenders: int
    zero_eligible_requests: int
    eligible_zero_contender_requests: int
    same_grid_assignments: int
    neighbour_assignments: int
    wait_real_candidates: int
    wait_neutral_candidates: int
    degradation_count: int
    degradation_min: float | None
    degradation_median: float | None
    degradation_mean: float | None
    degradation_p95: float | None
    degradation_max: float | None
    fleet_idle: int
    fleet_busy: int
    fleet_charging: int
    period: int
    arm_085: int
    arm_090: int
    arm_095: int
    arm_100: int
    arm_105: int
    arm_110: int
    arm_115: int
    busy_passenger: int
    busy_repositioning: int
    charging_active: int
    charging_queued: int
    charging_entered: int
    charging_completed: int
    energy_min: float
    energy_median: float
    energy_mean: float
    energy_p5: float
    energy_p95: float
    energy_max: float


def _hash(path: Path) -> str:
    return sha256_file(path)


def _json_fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _weight_distance(before: Iterable[np.ndarray], after: Iterable[np.ndarray]) -> float:
    return float(np.sqrt(sum(np.square(a.astype(np.float64) - b.astype(np.float64)).sum() for a, b in zip(before, after))))


class ProductionExperiment:
    """One causally persistent authoritative production experiment."""

    def __init__(self, root: str | Path, *, seed: int = 42, fleet_size: int = FLEET_SIZE) -> None:
        self.root = Path(root).resolve()
        self.seed = int(seed)
        self.fleet_size = int(fleet_size)
        if self.fleet_size != FLEET_SIZE:
            raise ValueError("Authoritative production execution requires fleet_size=5000.")
        self.config = load_config(self.root / "config/config.yaml")
        self.paths = self._paths()
        self._validate_frozen_hashes()
        self._load_sources_once()
        self._initialize_state_once()
        self.slot_index = 0
        self.next_request_id = 0
        self.current_contexts = self._initial_contexts()
        self.previous_grid_probabilities: dict[int, np.ndarray] | None = None
        self.repositioning_from_previous: set[int] = set()
        self.reports: list[ProductionSlotReport] = []
        self.wait_values: list[float] = []
        self.degradation_values: list[float] = []
        self.previous_charging_members = 0
        self.representative_grids = tuple(
            self.fare_bootstrap.nlargest(5, "historical_fare_count").grid_id.astype(int)
        )
        self.fare_diagnostics: list[dict[str, Any]] = []
        self.routing_grid_diagnostics: list[dict[str, Any]] = []

    def _paths(self) -> dict[str, Path]:
        return {
            "cnn_predictions": self.root / "models/demand/cnn_predictions.npy",
            "cnn_model": self.root / "models/demand/cnn_model.keras",
            "cnn_times": self.root / "data/processed/cnn/time_test.npy",
            "grid": self.root / "data/processed/grid_lookup.parquet",
            "neighbours": self.root / "data/processed/neighbour_map.parquet",
            "cleaned_trips": self.root / "data/processed/cleaned_trips.parquet",
            "weather": self.root / "data/processed/weather/nyc_weather_processed_2026_01.parquet",
            "popularity": self.root / "data/processed/destination_popularity_2026_01.parquet",
            "sensitivity": self.root / "data/processed/customer_price_sensitivity_2026_01.parquet",
            "sensitivity_fallback": self.root / "data/processed/customer_price_sensitivity_fallback_2026_01.parquet",
            "pricing_scaler": self.root / "config/pricing_context_scaler.json",
            "driver_profiles": self.root / "data/processed/driver_preferences_seed42.parquet",
            "fare_bootstrap": self.root / "data/processed/nb9_fare_bootstrap_2026_01_25_1830.parquet",
            "routing_initialization": self.root / "models/routing/nb12_nb13_common_initialization_seed42.npz",
            "charging_stations": self.root / "data/processed/charging_stations_2026_01.parquet",
        }

    def _validate_frozen_hashes(self) -> None:
        for name, expected in EXPECTED_HASHES.items():
            path = self.paths[name]
            if not path.is_file():
                raise FileNotFoundError(f"Missing production-authoritative {name}: {path}")
            actual = _hash(path)
            if actual != expected:
                raise ValueError(f"Production {name} SHA mismatch: expected {expected}, got {actual}")
        for name, path in self.paths.items():
            if not path.is_file():
                raise FileNotFoundError(f"Missing production-authoritative {name}: {path}")

    def _load_sources_once(self) -> None:
        self.grid = pd.read_parquet(self.paths["grid"])
        if len(self.grid) != EXPECTED_GRID_COUNT or self.grid.GridID.nunique() != EXPECTED_GRID_COUNT:
            raise ValueError("Production grid must contain exactly 1,213 unique GridIDs.")
        self.grid_ids = tuple(sorted(self.grid.GridID.astype(int)))
        self.directional = pd.read_parquet(self.paths["neighbours"])
        required_neighbours = {"GridID", "NeighbourGridID", "Direction"}
        if missing := required_neighbours - set(self.directional.columns):
            raise ValueError(f"Production neighbour map lacks columns: {sorted(missing)}")
        self.neighbour_lookup = {
            grid: tuple(sorted(self.directional.loc[self.directional.GridID == grid, "NeighbourGridID"].astype(int).unique()))
            for grid in self.grid_ids
        }
        self.predictions = np.load(self.paths["cnn_predictions"])
        self.cnn_input_timestamps = pd.DatetimeIndex(np.load(self.paths["cnn_times"]))
        self.cnn_target_timestamps = self.cnn_input_timestamps + pd.Timedelta(minutes=30)
        if self.predictions.shape[0] != len(self.cnn_input_timestamps) or self.predictions.ndim != 4 or self.predictions.shape[-1] != 1:
            raise ValueError("CNN prediction/timestamp artifacts are incompatible.")
        if len(self.cnn_target_timestamps) != PRODUCTION_SLOT_COUNT or self.cnn_input_timestamps.duplicated().any() or self.cnn_target_timestamps.duplicated().any() or not self.cnn_target_timestamps.is_monotonic_increasing:
            raise ValueError("CNN production input/target timestamps must contain 298 unique increasing pairs.")
        if self.cnn_target_timestamps[0] != pd.Timestamp(PRODUCTION_START) or self.cnn_target_timestamps[-1] != pd.Timestamp(PRODUCTION_END_EXCLUSIVE) - pd.Timedelta(minutes=30):
            raise KeyError("CNN target timestamps do not cover the authoritative 298-slot production window.")
        positions = self.grid.set_index("GridID")[["Row", "Column"]].astype(int)
        for index, timestamp in enumerate(self.cnn_target_timestamps):
            frame = self.predictions[index, :, :, 0]
            values = np.asarray([frame[row.Row, row.Column] for row in positions.itertuples()], dtype=float)
            if len(values) != EXPECTED_GRID_COUNT or not np.isfinite(values).all():
                raise ValueError(f"CNN prediction lacks finite coverage for all valid grids at {timestamp}.")
        self.trips = pd.read_parquet(self.paths["cleaned_trips"])
        self.od = build_empirical_od_distribution(self.trips, self.grid_ids)
        self.popularity = pd.read_parquet(self.paths["popularity"])
        popularity_times = pd.to_datetime(self.popularity.TimeSlot)
        for timestamp in self.cnn_target_timestamps:
            rows = self.popularity.loc[popularity_times == timestamp]
            if len(rows) != EXPECTED_GRID_COUNT or set(rows.GridID.astype(int)) != set(self.grid_ids) or rows.popularity_value.isna().any():
                raise KeyError(f"Missing production destination popularity at {timestamp}.")
        self.weather = load_processed_weather(self.paths["weather"], "2026-01")
        self.profiles = pd.read_parquet(self.paths["driver_profiles"])
        ids = self.profiles.vehicle_id.astype(int)
        if len(ids) != FLEET_SIZE or ids.nunique() != FLEET_SIZE or set(ids) != set(range(FLEET_SIZE)):
            raise ValueError("Production driver profiles must contain IDs 0..4999 exactly once.")
        self.fare_bootstrap = pd.read_parquet(self.paths["fare_bootstrap"])
        if len(self.fare_bootstrap) != EXPECTED_GRID_COUNT or set(self.fare_bootstrap.grid_id.astype(int)) != set(self.grid_ids):
            raise ValueError("Production fare bootstrap must cover exactly 1,213 grids.")
        self.station_definition = pd.read_parquet(self.paths["charging_stations"])
        validate_station_definition(self.station_definition, self.grid_ids, self.config["charging"]["number_of_charging_stations"])
        self.scaler = PricingContextScaler.load(self.paths["pricing_scaler"])
        self.manifest = self._source_manifest()

    def _source_manifest(self) -> dict[str, dict[str, Any]]:
        counts = {
            "cnn_model": (None, None, None),
            "cnn_predictions": (None, EXPECTED_GRID_COUNT, len(self.cnn_target_timestamps)),
            "cnn_times": (len(self.cnn_input_timestamps), None, len(self.cnn_input_timestamps)),
            "grid": (len(self.grid), EXPECTED_GRID_COUNT, None),
            "neighbours": (len(self.directional), EXPECTED_GRID_COUNT, None),
            "cleaned_trips": (len(self.trips), self.trips.PUGridID.nunique(), None),
            "weather": (len(self.weather), None, self.weather.Datetime.nunique()),
            "popularity": (len(self.popularity), self.popularity.GridID.nunique(), self.popularity.TimeSlot.nunique()),
            "sensitivity": (len(pd.read_parquet(self.paths["sensitivity"])), None, None),
            "sensitivity_fallback": (len(pd.read_parquet(self.paths["sensitivity_fallback"])), None, None),
            "pricing_scaler": (None, None, None),
            "driver_profiles": (len(self.profiles), None, None),
            "fare_bootstrap": (len(self.fare_bootstrap), self.fare_bootstrap.grid_id.nunique(), None),
            "routing_initialization": (None, None, None),
            "charging_stations": (len(self.station_definition), self.station_definition.grid_id.nunique(), None),
        }
        roles = {
            "cnn_model": "frozen demand model", "cnn_predictions": "held-out demand forecast",
            "cnn_times": "production timestamp mapping",
            "grid": "canonical spatial grid", "neighbours": "canonical directional adjacency",
            "cleaned_trips": "empirical request source", "weather": "production weather context",
            "popularity": "causal destination popularity", "sensitivity": "customer sensitivity",
            "sensitivity_fallback": "hierarchical sensitivity fallback", "pricing_scaler": "8D context scaler",
            "driver_profiles": "persistent driver preferences", "fare_bootstrap": "pre-cutoff NB9 fare prior",
            "routing_initialization": "common NB12/NB13 initial weights", "charging_stations": "charging network",
        }
        return {
            name: asdict(ProductionSource(
                str(path.relative_to(self.root)), roles[name], "production-authoritative", _hash(path),
                *counts[name],
            ))
            for name, path in self.paths.items()
        }

    def _initialize_state_once(self) -> None:
        energy = energy_parameters_from_config(self.config)
        self.energy = energy
        self.routing = RoutingParameters(**self.config["routing"])
        self.routing.validate()
        vehicles = initialize_ev_fleet(self.fleet_size, self.grid_ids, self.seed, energy, self.config["simulation"]["initialization_method"])
        self.fleet = Fleet(vehicles, frozenset(self.grid_ids), self.config["simulation"]["mini_slot_minutes"])
        centroids, _ = grid_centroids(self.grid)
        stations = stations_from_definition(self.station_definition, self.config["charging"]["station_max_power_kw"], energy.charging_power_kw)
        self.charging = ChargingInfrastructure(stations, centroids, random_seed=self.seed)
        self.statistics = OperationalStatistics(self.grid_ids, .30)
        initialize_nb9_fare_prior(self.statistics, self.fare_bootstrap)
        if any(state.ewma_wait is not None or state.ewma_std_wait is not None for state in self.statistics.ewma_state.values()):
            raise ValueError("Production NB9 wait history must begin empty.")
        seed_sequence = np.random.SeedSequence(self.seed)
        request_seed, customer_seed, acceptance_seed = seed_sequence.spawn(3)
        self.request_rng = np.random.default_rng(request_seed)
        self.customer_rng = np.random.default_rng(customer_seed)
        self.acceptance_rng = np.random.default_rng(acceptance_seed)
        self.customer = HistoricalCustomerSensitivityModel.from_parquet(
            self.paths["sensitivity"], self.customer_rng,
            self.paths["sensitivity_fallback"], "hierarchical",
        )
        self.linucb = DisjointLinUCB(alpha=1.0, random_seed=self.seed)
        learning = routing_learning_parameters_from_config(self.config)
        self.local_learners, self.global_policy = initialize_common_policy_learners(range(self.fleet_size), learning, seed=self.seed)
        with np.load(self.paths["routing_initialization"]) as saved:
            weights = [saved[f"weight_{index}"] for index in range(len(saved.files))]
        self.global_policy.reset_from_global_weights(weights)
        for learner in self.local_learners.values():
            learner.reset_from_global_weights(weights)
        self.utility_inputs = _LiveProductionUtilityInputs(self.profiles, self.fleet, self.energy, self.routing)
        self.initial_probabilities = self._uniform_valid_grid_probabilities()

    def _uniform_valid_grid_probabilities(self) -> dict[int, np.ndarray]:
        direction_index = {"north": 1, "east": 2, "south": 3, "west": 4}
        result = {}
        for grid_id in self.grid_ids:
            mask = np.zeros(5, dtype=bool)
            mask[0] = True
            for direction in self.directional.loc[self.directional.GridID == grid_id, "Direction"]:
                mask[direction_index[str(direction).lower()]] = True
            probabilities = np.zeros(5, dtype=float)
            probabilities[mask] = 1. / mask.sum()
            result[grid_id] = probabilities
        return result

    def _demand(self, timestamp: datetime) -> dict[int, float]:
        target = pd.Timestamp(timestamp)
        if target not in self.cnn_target_timestamps:
            raise KeyError(f"Missing production CNN target prediction for {timestamp}.")
        prediction = self.predictions[self.cnn_target_timestamps.get_loc(target), :, :, 0]
        return {
            int(row.GridID): float(prediction[int(row.Row), int(row.Column)])
            for row in self.grid[["GridID", "Row", "Column"]].itertuples(index=False)
        }

    def _request_counts(self, demand: Mapping[int, float]) -> dict[int, int]:
        return {
            grid: int(np.rint(max(0., value))) if grid in self.od.origin_row_positions else 0
            for grid, value in demand.items()
        }

    def _popularity(self, timestamp: datetime) -> dict[int, float]:
        rows = self.popularity.loc[pd.to_datetime(self.popularity.TimeSlot) == pd.Timestamp(timestamp)]
        if len(rows) != EXPECTED_GRID_COUNT:
            raise KeyError(f"Missing complete destination popularity for {timestamp}.")
        return dict(zip(rows.GridID.astype(int), rows.popularity_value.astype(float)))

    def _weather_code(self, timestamp: datetime) -> float:
        hour = pd.Timestamp(timestamp).floor("h")
        rows = self.weather.loc[self.weather.Datetime == hour, "WeatherCode"]
        if len(rows) != 1 or not np.isfinite(float(rows.iloc[0])):
            raise KeyError(f"Missing production weather for {hour}.")
        return float(rows.iloc[0])

    def _initial_contexts(self) -> dict[int, PricingContextInput]:
        demand, popularity = self._demand(PRODUCTION_START), self._popularity(PRODUCTION_START)
        return {grid: PricingContextInput(demand[grid], self.initial_probabilities[grid].copy(), popularity[grid]) for grid in self.grid_ids}

    def _statistics_snapshot(self) -> list[GridSlotStatistics]:
        charging = self.charging.charging_observations()
        return [
            GridSlotStatistics(
                grid, max(0, self.slot_index - 1), 0, None, None, 0, None, None,
                state.ewma_fare, state.ewma_wait, state.ewma_std_fare, state.ewma_std_wait,
                *(charging.get(grid, (None, None))),
            )
            for grid, state in self.statistics.ewma_state.items()
        ]

    def _contention_inputs(self, current_demand: Mapping[int, float]) -> DriverContentionInputs:
        features = build_grid_routing_features(current_demand, aggregate_grid_supply(self.fleet.vehicles, self.grid_ids), self._statistics_snapshot())
        return DriverContentionInputs.from_grid_geometry(
            routing_features=features, directional_neighbour_map=self.directional,
            utility_inputs_by_vehicle=self.utility_inputs, energy_parameters=self.energy,
            grid_lookup=self.grid, neighbour_lookup=self.neighbour_lookup,
        )

    def run_slot(self) -> ProductionSlotReport:
        timestamp = PRODUCTION_START + timedelta(minutes=30 * self.slot_index)
        if timestamp >= PRODUCTION_END_EXCLUSIVE:
            raise ValueError("Production slot exceeds the authoritative held-out window.")
        next_timestamp = timestamp + timedelta(minutes=30)
        current_demand = self._demand(timestamp)
        next_demand = self._demand(next_timestamp)
        next_popularity = self._popularity(next_timestamp)
        counts = self._request_counts(current_demand)
        request_rng_before = _json_fingerprint(self.request_rng.bit_generator.state)
        requests = generate_requests(counts, self.od, self.grid_ids, 15, None, self.next_request_id, rng=self.request_rng)
        request_rng_after = _json_fingerprint(self.request_rng.bit_generator.state)
        if requests and request_rng_before == request_rng_after:
            raise RuntimeError("Persistent production request RNG did not advance.")
        self.next_request_id += len(requests)
        evaluations: list[ContentionEvaluation] = []
        before_weights = [weight.copy() for weight in self.global_policy.policy_model.get_weights()]
        routing_source = "uniform_valid_initialization" if self.slot_index == 0 else "updated_global_policy"
        result = run_main_slot(
            slot_id=self.slot_index, requests=requests,
            pricing_context_inputs=self.current_contexts,
            next_predicted_demand=next_demand, next_popularity=next_popularity,
            learner=self.linucb, fleet=self.fleet, neighbour_lookup=self.neighbour_lookup,
            directional_neighbour_map=self.directional, statistics_engine=self.statistics,
            charging_infrastructure=self.charging, energy_parameters=self.energy,
            routing_parameters=self.routing, utility_inputs_by_vehicle=self.utility_inputs,
            local_learners=self.local_learners, global_policy_learner=self.global_policy,
            default_trip_duration_minutes=self.config["dispatch"]["default_trip_duration_minutes"],
            mini_slots_per_main_slot=15, acceptance_rng=self.acceptance_rng,
            federate=True, federation_round_index=self.slot_index,
            previous_grid_probabilities=self.previous_grid_probabilities,
            initial_grid_policy_probabilities=self.initial_probabilities,
            customer_response_model=CUSTOMER_MODEL_HISTORICAL,
            historical_customer_model=self.customer, weather_code=self._weather_code(timestamp),
            period=timestamp.hour * 2 + timestamp.minute // 30, simulation_timestamp=timestamp,
            reward_model=REWARD_MODEL_SERVED, supply_model=SUPPLY_MODEL_CORRECTED,
            pricing_decision_mode=PRICING_DECISION_MODE_REQUEST, grid_lookup=self.grid,
            popularity_table=self.popularity, sensitivity_fallback="hierarchical",
            linucb_reward_scaling=REQUEST_REWARD_SCALING_TRAINING,
            dispatch_model=DISPATCH_MODEL_CONTENTION,
            contention_inputs=self._contention_inputs(current_demand),
            contention_observer=evaluations.append,
        )
        after_weights = self.global_policy.policy_model.get_weights()
        report = self._build_report(timestamp, routing_source, requests, evaluations, result, before_weights, after_weights)
        statistics = {row.grid_id: row for row in result.statistics}
        bootstrap = self.fare_bootstrap.set_index("grid_id")
        for grid_id in self.representative_grids:
            row, prior = statistics[grid_id], bootstrap.loc[grid_id]
            self.fare_diagnostics.append({
                "slot_index": self.slot_index, "timestamp": timestamp.isoformat(), "grid_id": grid_id,
                "historical_count": int(prior.historical_fare_count),
                "historical_mean": float(prior.mean_fare), "historical_std": float(prior.std_fare),
                "observed_count": row.fare_count, "observed_mean": row.mean_fare,
                "observed_std": row.std_fare, "ewma_mean": row.ewma_fare, "ewma_std": row.ewma_std_fare,
            })
            policy = result.next_grid_policy[grid_id]
            self.routing_grid_diagnostics.append({
                "slot_index": self.slot_index, "timestamp": timestamp.isoformat(), "grid_id": grid_id,
                **{f"p_{name.lower()}": float(value) for name, value in zip(("STAY", "NORTH", "EAST", "SOUTH", "WEST"), policy.probabilities)},
            })
        self.previous_grid_probabilities = {grid: policy.probabilities.copy() for grid, policy in result.next_grid_policy.items()}
        self.current_contexts = {
            grid: PricingContextInput(context.predicted_demand, context.routing_probabilities.copy(), context.popularity)
            for grid, context in result.next_pricing_contexts.items()
        }
        self.repositioning_from_previous = {audit.vehicle_id for audit in result.routing_audit if audit.decision.chosen_action is not RoutingAction.STAY}
        self.reports.append(report)
        self.slot_index += 1
        self._validate_slot_invariants(result, requests)
        return report

    def _build_report(self, timestamp, routing_source, requests, evaluations, result: MainSlotResult, before_weights, after_weights) -> ProductionSlotReport:
        pricing = result.pricing_dispatch
        action = Counter(result.routing_action_counts)
        policy_mean = np.mean(np.stack([item.probabilities for item in result.next_grid_policy.values()]), axis=0)
        waits = [item for item in pricing.driver_wait_observations]
        wait_values = np.asarray([item.wait_minutes for item in waits], dtype=float)
        assigned = [request for request in requests if request.assigned_vehicle_id is not None]
        real_candidates = sum(
            1 for audit in result.routing_audit for candidate in audit.state.action_features.values()
            if candidate is not None and ((candidate.mean_wait is not None and candidate.std_wait is not None) or (candidate.ewma_wait is not None and candidate.ewma_std_wait is not None))
        )
        valid_candidates = sum(sum(audit.decision.valid_action_mask.values()) for audit in result.routing_audit)
        move_energy = self.routing.reposition_distance_km * self.energy.consumption_rate_kwh_per_km
        degradation_values = np.asarray([
            normalized_dod_degradation_penalty(
                audit.transition.energy_before_kwh if action is RoutingAction.STAY else audit.transition.energy_before_kwh - move_energy,
                self.energy,
            )
            for audit in result.routing_audit
            for action, valid in audit.decision.valid_action_mask.items() if valid
        ], dtype=float)
        if not np.isfinite(degradation_values).all() or ((degradation_values < 0) | (degradation_values > 1)).any():
            raise RuntimeError("Production NB11 degradation penalties must be finite and within [0,1].")
        self.wait_values.extend(wait_values.tolist())
        self.degradation_values.extend(degradation_values.tolist())
        wait_stats = _distribution(wait_values)
        degradation_stats = _distribution(degradation_values)
        federation = result.federated
        prediction_index = self.cnn_target_timestamps.get_loc(pd.Timestamp(timestamp))
        arm_counts = Counter(int(request.selected_arm) for request in requests)
        energies = np.asarray([vehicle.energy_level for vehicle in self.fleet.vehicles], dtype=float)
        active = result.charging.active_vehicle_count
        queued = result.charging.queued_vehicle_count
        charging_members = active + queued
        completed = self.previous_charging_members + result.charging.presented_vehicle_count - charging_members
        self.previous_charging_members = charging_members
        return ProductionSlotReport(
            self.slot_index, timestamp.isoformat(),
            self.cnn_input_timestamps[prediction_index].isoformat(),
            self.cnn_target_timestamps[prediction_index].isoformat(), int(prediction_index),
            routing_source,
            pricing.generated, pricing.accepted, pricing.rejected, pricing.served, pricing.accepted_but_unserved,
            pricing.linucb_selections_performed, pricing.linucb_updates_performed,
            pricing.served_revenue, pricing.linucb_learning_reward,
            sum(row.fare_count for row in result.statistics), len(waits), sum(item.wait_minutes > 0 for item in waits),
            wait_stats["min"], wait_stats["median"], wait_stats["mean"], wait_stats["p95"], wait_stats["max"],
            sum(state.ewma_wait is not None for state in result.ewma_state.values()),
            sum(row.fare_count > 0 for row in result.statistics),
            result.local_learning.observations_collected,
            0 if federation is None else federation.metadata.participating_updates,
            self.fleet_size - (0 if federation is None else federation.metadata.participating_updates),
            int(federation is not None), _weight_distance(before_weights, after_weights),
            action["STAY"], action["NORTH"], action["EAST"], action["SOUTH"], action["WEST"],
            *[float(value) for value in policy_mean],
            sum(value for key, value in action.items() if key != "STAY"), len(self.repositioning_from_previous),
            sum(vehicle.current_action == "repositioning" for vehicle in self.fleet.vehicles),
            len(evaluations), sum(item.contends for item in evaluations),
            sum((request.eligible_vehicle_count or 0) == 0 for request in requests if request.customer_accepted),
            sum((request.eligible_vehicle_count or 0) > 0 and (request.contender_count or 0) == 0 for request in requests if request.customer_accepted),
            sum(request.selected_vehicle_origin_grid == request.origin_grid for request in assigned),
            sum(request.selected_vehicle_origin_grid != request.origin_grid for request in assigned),
            real_candidates, valid_candidates - real_candidates,
            len(degradation_values), degradation_stats["min"], degradation_stats["median"],
            degradation_stats["mean"], degradation_stats["p95"], degradation_stats["max"],
            sum(vehicle.trip_status is VehicleStatus.IDLE for vehicle in self.fleet.vehicles),
            sum(vehicle.trip_status is VehicleStatus.BUSY for vehicle in self.fleet.vehicles),
            sum(vehicle.trip_status is VehicleStatus.CHARGING for vehicle in self.fleet.vehicles),
            timestamp.hour * 2 + timestamp.minute // 30,
            *[arm_counts[index] for index in range(7)],
            sum(vehicle.trip_status is VehicleStatus.BUSY and vehicle.current_action == "transporting" for vehicle in self.fleet.vehicles),
            sum(vehicle.trip_status is VehicleStatus.BUSY and vehicle.current_action == "repositioning" for vehicle in self.fleet.vehicles),
            active, queued, result.charging.presented_vehicle_count, completed,
            float(energies.min()), float(np.median(energies)), float(energies.mean()),
            float(np.percentile(energies, 5)), float(np.percentile(energies, 95)), float(energies.max()),
        )

    def _validate_slot_invariants(self, result: MainSlotResult, requests) -> None:
        pricing = result.pricing_dispatch
        if pricing.generated != pricing.accepted + pricing.rejected or pricing.accepted != pricing.served + pricing.accepted_but_unserved:
            raise RuntimeError("Production request accounting invariant failed.")
        if pricing.generated != pricing.linucb_selections_performed or pricing.generated != pricing.linucb_updates_performed:
            raise RuntimeError("Production LinUCB selection/update invariant failed.")
        if int(self.linucb.pending_cold_start.sum()) != 0:
            raise RuntimeError("Production LinUCB has pending reservations.")
        if not np.isclose(pricing.served_revenue, sum(float(request.raw_served_revenue) for request in requests)):
            raise RuntimeError("Production served revenue invariant failed.")
        if not np.isclose(pricing.linucb_learning_reward, pricing.served_revenue / REQUEST_REWARD_REF):
            raise RuntimeError("Production reward scaling invariant failed.")
        validate_fleet(self.fleet.vehicles, self.grid_ids, self.fleet_size)
        numeric = np.asarray([vehicle.energy_level for vehicle in self.fleet.vehicles] + [pricing.served_revenue, pricing.linucb_learning_reward])
        if not np.isfinite(numeric).all():
            raise RuntimeError("Production state contains NaN or infinity.")

    def run(self, slot_count: int) -> list[ProductionSlotReport]:
        if not isinstance(slot_count, int) or slot_count <= 0 or self.slot_index + slot_count > PRODUCTION_SLOT_COUNT:
            raise ValueError("slot_count must remain within the 298-slot held-out target window.")
        return [self.run_slot() for _ in range(slot_count)]

    def reproducibility_state(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "slots_completed": self.slot_index,
            "request_rng": _json_fingerprint(self.request_rng.bit_generator.state),
            "customer_rng": _json_fingerprint(self.customer_rng.bit_generator.state),
            "acceptance_rng": _json_fingerprint(self.acceptance_rng.bit_generator.state),
            "linucb_updates": int(self.linucb.update_counts.sum()),
            "trajectory_sha256": _json_fingerprint([asdict(report) for report in self.reports]),
        }


class _LiveProductionUtilityInputs(Mapping[int, Mapping[RoutingAction, Any]]):
    """Resolve action penalties from each vehicle's energy at access time."""

    def __init__(self, profiles: pd.DataFrame, fleet: Fleet, energy, routing) -> None:
        self.profiles = {
            int(row.vehicle_id): (float(row.price_preference), float(row.wait_preference))
            for row in profiles.itertuples(index=False)
        }
        self.fleet = fleet
        self.energy = energy
        self.routing = routing
        self.movement_energy = routing.reposition_distance_km * energy.consumption_rate_kwh_per_km

    def __len__(self) -> int:
        return len(self.profiles)

    def __iter__(self):
        return iter(self.profiles)

    def __getitem__(self, vehicle_id: int):
        if vehicle_id not in self.profiles:
            raise KeyError(vehicle_id)
        price, wait = self.profiles[vehicle_id]
        current_energy = self.fleet.vehicle(vehicle_id).energy_level
        return {
            action: CandidateUtilityInput(
                price, wait,
                normalized_dod_degradation_penalty(
                    current_energy if action is RoutingAction.STAY else current_energy - self.movement_energy,
                    self.energy,
                ),
            )
            for action in ACTION_ORDER
        }


def run_production_preflight(root: str | Path, slot_count: int, *, seed: int = 42) -> tuple[ProductionExperiment, float]:
    started = time.perf_counter()
    experiment = ProductionExperiment(root, seed=seed)
    experiment.run(slot_count)
    return experiment, time.perf_counter() - started


def _distribution(values: Iterable[float]) -> dict[str, float | None]:
    array = np.asarray(list(values), dtype=float)
    if not len(array):
        return {name: None for name in ("min", "p25", "median", "mean", "p75", "p90", "p95", "p99", "max")}
    return {
        "min": float(array.min()), "p25": float(np.percentile(array, 25)),
        "median": float(np.median(array)), "mean": float(array.mean()),
        "p75": float(np.percentile(array, 75)), "p90": float(np.percentile(array, 90)),
        "p95": float(np.percentile(array, 95)), "p99": float(np.percentile(array, 99)),
        "max": float(array.max()),
    }


def write_preflight_artifacts(experiment: ProductionExperiment, output_dir: str | Path, runtime_seconds: float) -> tuple[Path, Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports = [asdict(report) for report in experiment.reports]
    frame = pd.DataFrame(reports)
    totals = {
        key: float(frame[key].sum()) for key in (
            "generated", "accepted", "rejected", "served", "accepted_unserved",
            "linucb_selections", "linucb_updates", "raw_served_revenue", "scaled_learning_reward",
        )
    }
    summary = {
        "configuration": {
            "seed": experiment.seed, "fleet_size": experiment.fleet_size, "slots": len(reports),
            "evaluation_start": PRODUCTION_START.isoformat(),
            "evaluation_end_exclusive": (
                pd.Timestamp(reports[-1]["timestamp"]) + pd.Timedelta(minutes=30)
            ).isoformat(),
            "available_held_out_target_slots": PRODUCTION_SLOT_COUNT,
            "cnn_target_timestamp_mapping": "cnn_input_timestamp + 30 minutes",
        },
        "runtime_seconds": runtime_seconds,
        "requests_per_second": totals["generated"] / runtime_seconds,
        "totals": totals,
        "driver_wait_minutes": {"count": len(experiment.wait_values), **_distribution(experiment.wait_values)},
        "nb11_degradation_penalty": {"count": len(experiment.degradation_values), **_distribution(experiment.degradation_values)},
        "source_manifest": experiment.manifest,
    }
    summary_path, slot_path, reproducibility_path = output / "summary.json", output / "per_slot.csv", output / "reproducibility.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    frame.to_csv(slot_path, index=False)
    arm_columns = ["slot_index", "timestamp", "period", "arm_085", "arm_090", "arm_095", "arm_100", "arm_105", "arm_110", "arm_115", "raw_served_revenue", "scaled_learning_reward"]
    frame[arm_columns].to_csv(output / "linucb_factors.csv", index=False)
    routing_columns = ["slot_index", "timestamp", "nb11_observations", "nb12_participants", "zero_observation_clients", "nb13_rounds", "global_parameter_change_norm", "action_stay", "action_north", "action_east", "action_south", "action_west", "mean_p_stay", "mean_p_north", "mean_p_east", "mean_p_south", "mean_p_west"]
    frame[routing_columns].to_csv(output / "routing_rounds.csv", index=False)
    wait_columns = ["slot_index", "timestamp", "completed_waits", "nonzero_waits", "real_wait_history_grids", "wait_real_candidates", "wait_neutral_candidates", "wait_min", "wait_median", "wait_mean", "wait_p95", "wait_max"]
    frame[wait_columns].to_csv(output / "nb9_wait.csv", index=False)
    fleet_columns = ["slot_index", "timestamp", "fleet_idle", "busy_passenger", "busy_repositioning", "fleet_charging", "charging_active", "charging_queued", "charging_entered", "charging_completed", "energy_min", "energy_median", "energy_mean", "energy_p5", "energy_p95", "energy_max"]
    frame[fleet_columns].to_csv(output / "fleet_states.csv", index=False)
    pd.DataFrame(experiment.fare_diagnostics).to_csv(output / "nb9_fare_representative.csv", index=False)
    pd.DataFrame(experiment.routing_grid_diagnostics).to_csv(output / "routing_grid_representative.csv", index=False)
    reproducibility_path.write_text(json.dumps(experiment.reproducibility_state(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path, slot_path, reproducibility_path
