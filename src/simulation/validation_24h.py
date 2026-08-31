"""Controlled 24-hour small-fleet health validation, not a thesis experiment."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters
from src.charging.stations import ChargingInfrastructure, ChargingStation
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.pricing.linucb import PRICING_FACTORS, DisjointLinUCB
from src.popularity.destination import (
    POPULARITY_ENCODING, PopularityThresholds, apply_popularity_levels,
    fit_popularity_thresholds, trailing_dropoff_average,
)
from src.routing.baseline import ACTION_ORDER, CandidateUtilityInput, RoutingAction, RoutingParameters
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters
from src.simulation.multi_slot import MultiSlotResult, TemporalSlotInput, run_multi_slot_simulation
from src.simulation.pricing_dispatch import PricingContextInput
from src.simulation.statistics import OperationalStatistics


DEMAND_SOURCE = "controlled_validation_fixture"
POPULARITY_SOURCE = "deterministic_dropoff_history_trailing_6slot_global_quintiles"
FEDERATION_SCHEDULE_STATUS = "validation_only_not_final"
VALIDATION_FLEET_SIZE = 50
VALIDATION_GRID_COUNT = 4


@dataclass(frozen=True)
class Validation24hReport:
    result: MultiSlotResult
    summary_table: pd.DataFrame
    trajectory_signature: tuple[tuple[Any, ...], ...]
    initial_energy_kwh: float
    final_energy_kwh: float
    passenger_energy_consumed_kwh: float
    repositioning_energy_consumed_kwh: float
    charging_energy_gained_kwh: float
    energy_accounting_error_kwh: float
    factor_counts: dict[float, int]
    routing_action_counts: dict[str, int]
    grid_policy_source_counts: dict[str, int]
    invariant_failures: tuple[str, ...]
    nan_count: int
    energy_bound_failures: int
    probability_failures: int
    fleet_size: int
    active_grid_count: int
    seed: int
    popularity_thresholds: PopularityThresholds
    popularity_table: pd.DataFrame
    scaling_summary: dict[str, dict[str, float]]
    scaling_clip_counts: dict[str, int]
    linucb_conditioning: dict[float, dict[str, float | int | bool]]
    context_norm_shares: dict[str, dict[str, float]]
    reward_summary: dict[str, dict[str, float]]
    reward_clip_count: int
    cold_start_assignments: tuple[float, ...]
    cold_start_rewards: tuple[float | None, ...]
    normal_selection_begins_at: int | None

    @property
    def passed(self) -> bool:
        return not self.invariant_failures and self.nan_count == 0 and self.energy_bound_failures == 0 and self.probability_failures == 0


def _directional_map() -> pd.DataFrame:
    return pd.DataFrame([
        (0, 2, "north"), (0, 1, "east"),
        (1, 3, "north"), (1, 0, "west"),
        (2, 0, "south"), (2, 3, "east"),
        (3, 1, "south"), (3, 2, "west"),
    ], columns=["GridID", "NeighbourGridID", "Direction"])


def _empirical_request(slot: int, sequence: int, grid: int) -> RequestState:
    request_id = slot * 100 + grid * 10 + sequence
    request_time = sequence * 2
    historical_pickup = datetime(2026, 1, 1, 8, 0) + timedelta(minutes=request_time * 2, seconds=17)
    duration = (6., 10., 18., 34.)[sequence % 4]
    miles = (1., 2., 3., 5.)[sequence % 4]
    destination = (grid + 1) % VALIDATION_GRID_COUNT
    return RequestState(
        request_id, request_time, grid, destination, base_fare=10. + 2 * grid + sequence,
        source_trip_id=request_id, empirical_pickup_datetime=historical_pickup,
        empirical_dropoff_datetime=historical_pickup + timedelta(minutes=duration),
        trip_duration_minutes=duration, trip_distance_miles=miles,
        trip_distance_km=miles * 1.609344,
        empirical_within_slot_offset_seconds=float(request_time * 120 + 17),
    )


def _validation_popularity(slot_count: int) -> tuple[pd.DataFrame, PopularityThresholds]:
    """Create deterministic prior/current drop-off history without look-ahead."""
    start = pd.Timestamp("2026-01-01")
    rows = []
    for slot in range(-12, slot_count + 1):
        timestamp = start + pd.Timedelta(minutes=30 * slot)
        for grid in range(VALIDATION_GRID_COUNT):
            rows.append((timestamp, grid, int(((slot + 12) * (grid + 1) + 2 * grid) % 11)))
    moving = trailing_dropoff_average(pd.DataFrame(rows, columns=["TimeSlot", "GridID", "dropoff_count"]))
    reference = moving.loc[moving.TimeSlot < start, "dropoff_ma_3h"]
    thresholds = fit_popularity_thresholds(reference, reference_start=start - pd.Timedelta(hours=6), reference_end_exclusive=start)
    applied = apply_popularity_levels(moving, thresholds)
    validation = applied.loc[(applied.TimeSlot >= start) & (applied.TimeSlot <= start + pd.Timedelta(minutes=30 * slot_count))].reset_index(drop=True)
    if validation[["popularity_level", "popularity_value"]].isna().any().any():
        raise ValueError("Validation popularity requires deterministic pre-window initialization.")
    return validation, thresholds


def _build_inputs(slot_count: int, popularity_table: pd.DataFrame) -> list[TemporalSlotInput]:
    utility = CandidateUtilityInput(15., 0., .1)
    vehicle_utilities = {
        vehicle_id: {action: utility for action in ACTION_ORDER}
        for vehicle_id in range(VALIDATION_FLEET_SIZE)
    }
    inputs: list[TemporalSlotInput] = []
    for slot in range(slot_count):
        demand = {grid: float(18 + 4 * np.sin((slot + grid) * np.pi / 12)) for grid in range(VALIDATION_GRID_COUNT)}
        next_time = pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=30 * (slot + 1))
        next_rows = popularity_table.loc[popularity_table.TimeSlot == next_time]
        popularity = dict(zip(next_rows.GridID.astype(int), next_rows.popularity_value.astype(float)))
        requests = [_empirical_request(slot, sequence, grid) for grid in range(VALIDATION_GRID_COUNT) for sequence in range(8)]
        inputs.append(TemporalSlotInput(requests, demand, popularity, vehicle_utilities))
    return inputs


def run_small_fleet_validation(slot_count: int, *, seed: int = 42) -> Validation24hReport:
    """Run the deterministic controlled fixture for smoke or 24-hour validation."""
    grids = tuple(range(VALIDATION_GRID_COUNT))
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
    vehicles = [
        VehicleState(vehicle_id, vehicle_id % VALIDATION_GRID_COUNT, VehicleStatus.IDLE, None, 0, "idle", 6. if vehicle_id < 8 else 40. + vehicle_id % 20)
        for vehicle_id in range(VALIDATION_FLEET_SIZE)
    ]
    fleet = Fleet(vehicles, frozenset(grids), 2)
    initial_energy = float(sum(vehicle.energy_level for vehicle in vehicles))
    learning = RoutingLearningParameters(learning_rate=.001, local_observation_capacity=32, batch_size=8, local_epochs=1)
    local_learners = {vehicle_id: LocalRoutingLearner(vehicle_id, learning, seed=seed + vehicle_id) for vehicle_id in range(VALIDATION_FLEET_SIZE)}
    common = local_learners[0].policy_model.get_weights()
    for local in local_learners.values():
        local.reset_from_global_weights(common)
    global_policy = LocalRoutingLearner(VALIDATION_FLEET_SIZE, learning, seed=seed + VALIDATION_FLEET_SIZE)
    global_policy.reset_from_global_weights(common)
    infrastructure = ChargingInfrastructure(
        [ChargingStation(0, 0, 60, 30), ChargingStation(1, 3, 60, 30)],
        {grid: (float(grid % 2), float(grid // 2)) for grid in grids}, random_seed=seed,
    )
    neighbours = {grid: tuple(sorted(set(_directional_map().loc[_directional_map().GridID == grid, "NeighbourGridID"].astype(int)))) for grid in grids}
    initial_probabilities = {grid: [.2] * 5 for grid in grids}
    pricing_learner = DisjointLinUCB(1.)
    popularity_table, popularity_thresholds = _validation_popularity(slot_count)
    initial_rows = popularity_table.loc[popularity_table.TimeSlot == pd.Timestamp("2026-01-01")]
    initial_popularity = dict(zip(initial_rows.GridID.astype(int), initial_rows.popularity_value.astype(float)))
    result = run_multi_slot_simulation(
        start_time=datetime(2026, 1, 1), slot_inputs=_build_inputs(slot_count, popularity_table), slot_count=slot_count,
        initial_pricing_contexts={grid: PricingContextInput(18., [.2] * 5, initial_popularity[grid]) for grid in grids},
        initial_grid_policy_probabilities=initial_probabilities,
        federation_slots=set(range(3, slot_count, 4)), learner=pricing_learner,
        acceptance_rng=np.random.default_rng(seed), fleet=fleet, neighbour_lookup=neighbours,
        directional_neighbour_map=_directional_map(), statistics_engine=OperationalStatistics(grids, .3),
        charging_infrastructure=infrastructure, energy_parameters=energy,
        routing_parameters=RoutingParameters(15., 3., 30.), local_learners=local_learners,
        global_policy_learner=global_policy, default_trip_duration_minutes=2,
    )
    return _audit_validation(result, fleet, infrastructure, initial_energy, energy, seed, pricing_learner, local_learners, global_policy, popularity_thresholds, popularity_table)


def _audit_validation(result, fleet, infrastructure, initial_energy, energy, seed, pricing_learner, local_learners, global_policy, popularity_thresholds, popularity_table) -> Validation24hReport:
    failures: list[str] = []
    nan_count = energy_bound_failures = probability_failures = 0
    factor_counts: Counter[float] = Counter()
    actions: Counter[str] = Counter()
    policy_sources: Counter[str] = Counter()
    previous_energy = initial_energy
    rows: list[dict[str, Any]] = []
    for slot in result.slots:
        if slot.generated != slot.accepted + slot.rejected or slot.accepted != slot.served + slot.accepted_but_unserved:
            failures.append(f"slot {slot.slot_index}: request accounting")
        if sum(slot.fleet_counts.values()) != VALIDATION_FLEET_SIZE:
            failures.append(f"slot {slot.slot_index}: fleet accounting")
        expected_energy = previous_energy + slot.charging_energy_gained_kwh - slot.passenger_energy_consumed_kwh - slot.repositioning_energy_consumed_kwh
        if not np.isclose(expected_energy, slot.total_energy_kwh, rtol=1e-9, atol=1e-8):
            failures.append(f"slot {slot.slot_index}: energy accounting")
        previous_energy = slot.total_energy_kwh
        if not slot.charging_capacity_valid or not slot.queue_membership_valid:
            failures.append(f"slot {slot.slot_index}: charging integrity")
        if not slot.routing_decisions_valid:
            failures.append(f"slot {slot.slot_index}: routing validity")
        if slot.minimum_energy_kwh < 0 or slot.maximum_energy_kwh > energy.battery_capacity_kwh:
            energy_bound_failures += 1
        probability_failures += sum(
            not np.isfinite(value) or not 0. <= value <= 1.
            for value in slot.acceptance_probabilities
        )
        numeric = [slot.accepted_revenue, slot.served_revenue, slot.total_energy_kwh, slot.minimum_energy_kwh, slot.maximum_energy_kwh]
        nan_count += sum(not np.isfinite(value) for value in numeric)
        for factor in slot.pricing_factors.values():
            if factor not in PRICING_FACTORS:
                failures.append(f"slot {slot.slot_index}: pricing arm")
            factor_counts[factor] += 1
        if not set(slot.pricing_popularity.values()).issubset(set(POPULARITY_ENCODING.values())):
            failures.append(f"slot {slot.slot_index}: popularity encoding")
        actions.update(slot.routing_action_counts)
        for policy in slot.grid_policy.values():
            policy_sources[policy.source] += 1
            if policy.probabilities.shape != (5,) or not np.isfinite(policy.probabilities).all() or (policy.probabilities < 0).any() or not np.isclose(policy.probabilities.sum(), 1.):
                probability_failures += 1
        for statistic in slot.statistics:
            for value in (statistic.mean_fare, statistic.std_fare, statistic.mean_wait, statistic.std_wait, statistic.ewma_fare, statistic.ewma_std_fare, statistic.ewma_wait, statistic.ewma_std_wait):
                if value is not None and (not np.isfinite(value) or value < 0):
                    nan_count += 1
        rows.append({
            "slot_index": slot.slot_index, "timestamp": slot.timestamp,
            "generated": slot.generated, "accepted": slot.accepted, "rejected": slot.rejected,
            "served": slot.served, "accepted_but_unserved": slot.accepted_but_unserved,
            "accepted_revenue": slot.accepted_revenue, "served_revenue": slot.served_revenue,
            "idle": slot.fleet_counts["idle"], "busy": slot.fleet_counts["busy"], "charging": slot.fleet_counts["charging"],
            "total_energy_kwh": slot.total_energy_kwh,
            "mean_soc": slot.total_energy_kwh / (VALIDATION_FLEET_SIZE * energy.battery_capacity_kwh),
            "minimum_energy_kwh": slot.minimum_energy_kwh,
            "maximum_energy_kwh": slot.maximum_energy_kwh,
            "passenger_energy_kwh": slot.passenger_energy_consumed_kwh,
            "repositioning_energy_kwh": slot.repositioning_energy_consumed_kwh,
            "charging_energy_kwh": slot.charging_energy_gained_kwh,
            "charging_active": slot.charging_active, "charging_queued": slot.charging_queued,
            "max_queue": slot.maximum_station_queue_length,
            "mean_queue": slot.mean_station_queue_length,
            "maximum_remaining_busy_minutes": slot.maximum_remaining_busy_minutes,
            "completed_driver_waits": len(slot.driver_wait_observations),
            "nonzero_driver_waits": sum(item.wait_minutes > 0 for item in slot.driver_wait_observations),
            "routing_observations": slot.local_observations, "learners_trained": slot.learners_trained,
            "federated": slot.federation_requested, "federation_participants": slot.federation_participants,
            "federation_samples": slot.federation_samples,
            "policy_current_mean": sum(item.source == "current_vehicle_mean" for item in slot.grid_policy.values()),
            "policy_carry_forward": sum(item.source == "carry_forward" for item in slot.grid_policy.values()),
            "policy_initialization": sum(item.source == "initialization" for item in slot.grid_policy.values()),
        })
    final_energy = result.slots[-1].total_energy_kwh
    passenger = float(sum(slot.passenger_energy_consumed_kwh for slot in result.slots))
    reposition = float(sum(slot.repositioning_energy_consumed_kwh for slot in result.slots))
    charging = float(sum(slot.charging_energy_gained_kwh for slot in result.slots))
    accounting_error = float(final_energy - (initial_energy + charging - passenger - reposition))
    if not np.isclose(accounting_error, 0., atol=1e-8):
        failures.append("cumulative energy accounting")
    if any(not np.isfinite(value).all() for value in (*pricing_learner.A, *pricing_learner.b)):
        failures.append("pricing learner finiteness")
    if any(not np.isfinite(weight).all() for local in (*local_learners.values(), global_policy) for weight in local.policy_model.get_weights()):
        failures.append("policy weight finiteness")
    signature = tuple((s.generated, s.accepted, s.served, round(s.accepted_revenue, 8), tuple(sorted(s.fleet_counts.items())), round(s.total_energy_kwh, 8), tuple(sorted(s.pricing_factors.items())), s.federation_requested) for s in result.slots)
    context_audits = [audit for slot in result.slots for audit in slot.pricing_context_audit.values()]
    def distribution(field: str) -> dict[str, float]:
        values = np.asarray([audit[field] for audit in context_audits], dtype=np.float64)
        return {
            "min": float(values.min()), "median": float(np.median(values)),
            "p95": float(np.percentile(values, 95)), "p99": float(np.percentile(values, 99)),
            "max": float(values.max()),
        }
    scaling_summary = {
        "demand_raw": distribution("raw_predicted_demand"),
        "demand_scaled": distribution("scaled_predicted_demand"),
        "supply_raw": distribution("raw_supply"),
        "supply_scaled": distribution("scaled_supply"),
    }
    scaling_clip_counts = {
        "contexts": len(context_audits),
        "negative_demand": sum(bool(audit["demand_negative_clipped"]) for audit in context_audits),
        "upper_demand": sum(bool(audit["demand_upper_clipped"]) for audit in context_audits),
        "upper_supply": sum(bool(audit["supply_upper_clipped"]) for audit in context_audits),
    }
    conditioning = {}
    for arm, count, matrix in zip(PRICING_FACTORS, pricing_learner.update_counts, pricing_learner.A):
        eigenvalues = np.linalg.eigvalsh(matrix)
        condition = float(np.linalg.cond(matrix))
        conditioning[arm] = {
            "update_count": int(count), "condition_number": condition,
            "minimum_eigenvalue": float(eigenvalues.min()), "maximum_eigenvalue": float(eigenvalues.max()),
            "finite": bool(np.isfinite(condition) and np.isfinite(eigenvalues).all()),
        }
    accumulated_diagonal = sum((np.diag(matrix) - 1. for matrix in pricing_learner.A), start=np.zeros(8))
    scaled_components = np.asarray([
        accumulated_diagonal[0], accumulated_diagonal[1], accumulated_diagonal[2:7].sum(), accumulated_diagonal[7],
    ])
    raw_components = np.asarray([
        sum(float(audit["raw_predicted_demand"]) ** 2 for audit in context_audits),
        sum(float(audit["raw_supply"]) ** 2 for audit in context_audits),
        scaled_components[2], scaled_components[3],
    ])
    component_names = ("demand_squared", "supply_squared", "routing_probabilities_squared", "popularity_squared")
    context_norm_shares = {
        "raw": {name: float(value / raw_components.sum()) for name, value in zip(component_names, raw_components)},
        "scaled": {name: float(value / scaled_components.sum()) for name, value in zip(component_names, scaled_components)},
    }
    raw_rewards = np.asarray([
        value for slot in result.slots for value in slot.pricing_raw_opportunity_reward.values() if value is not None
    ], dtype=np.float64)
    normalized_rewards = np.asarray([
        value for slot in result.slots for value in slot.pricing_normalized_reward.values() if value is not None
    ], dtype=np.float64)
    reward_summary = {
        "raw_revenue_per_opportunity": {
            "min": float(raw_rewards.min()), "median": float(np.median(raw_rewards)),
            "p95": float(np.percentile(raw_rewards, 95)), "max": float(raw_rewards.max()),
        },
        "normalized_reward": {
            "min": float(normalized_rewards.min()), "median": float(np.median(normalized_rewards)),
            "p95": float(np.percentile(normalized_rewards, 95)), "max": float(normalized_rewards.max()),
        },
    }
    decision_rows = [
        (factor, slot.pricing_cold_start[grid], slot.pricing_normalized_reward[grid])
        for slot in result.slots for grid, factor in sorted(slot.pricing_factors.items())
    ]
    cold_rows = [row for row in decision_rows if row[1]]
    normal_start = next((index for index, row in enumerate(decision_rows, 1) if not row[1]), None)
    return Validation24hReport(
        result, pd.DataFrame(rows), signature, initial_energy, final_energy, passenger, reposition, charging,
        accounting_error, dict(factor_counts), dict(actions), dict(policy_sources), tuple(failures), nan_count,
        energy_bound_failures, probability_failures, VALIDATION_FLEET_SIZE, VALIDATION_GRID_COUNT, seed,
        popularity_thresholds, popularity_table, scaling_summary, scaling_clip_counts, conditioning, context_norm_shares,
        reward_summary, sum(slot.pricing_reward_clipped[grid] for slot in result.slots for grid in slot.pricing_reward_clipped),
        tuple(row[0] for row in cold_rows[:7]), tuple(row[2] for row in cold_rows[:7]), normal_start,
    )


def write_validation_artifacts(report: Validation24hReport, root: str | Path) -> tuple[Path, ...]:
    """Write concise aggregate tables and diagnostic plots."""
    root_path = Path(root)
    table_dir, figure_dir = root_path / "results/tables", root_path / "results/figures"
    table_dir.mkdir(parents=True, exist_ok=True); figure_dir.mkdir(parents=True, exist_ok=True)
    summary_path = table_dir / "validation_24h_summary.csv"
    factors_path = table_dir / "validation_24h_pricing_factors.csv"
    report.summary_table.to_csv(summary_path, index=False)
    pd.DataFrame(sorted(report.factor_counts.items()), columns=["pricing_factor", "selection_count"]).to_csv(factors_path, index=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = [summary_path, factors_path]
    plots = (
        (["idle", "busy", "charging"], "Fleet status", "vehicles", "validation_24h_fleet_status.png"),
        (["total_energy_kwh"], "Fleet energy", "kWh", "validation_24h_energy.png"),
        (["generated", "accepted", "served"], "Requests", "requests", "validation_24h_requests.png"),
        (["accepted_revenue"], "Accepted revenue", "fare units", "validation_24h_revenue.png"),
    )
    for columns, title, ylabel, filename in plots:
        figure, axis = plt.subplots(figsize=(8, 4))
        for column in columns:
            axis.plot(report.summary_table["slot_index"], report.summary_table[column], label=column)
        axis.set(title=title, xlabel="30-minute slot", ylabel=ylabel); axis.legend(); figure.tight_layout()
        path = figure_dir / filename; figure.savefig(path, dpi=120); plt.close(figure); paths.append(path)
    return tuple(paths)
