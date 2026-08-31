#!/usr/bin/env python3
"""Run and persist the 24-hour small-fleet validation twice for replay proof."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.simulation.validation_24h import (
    DEMAND_SOURCE, FEDERATION_SCHEDULE_STATUS, POPULARITY_SOURCE,
    run_small_fleet_validation, write_validation_artifacts,
)


def main() -> int:
    first = run_small_fleet_validation(48, seed=42)
    second = run_small_fleet_validation(48, seed=42)
    deterministic = first.trajectory_signature == second.trajectory_signature
    artifacts = write_validation_artifacts(first, ROOT)
    table = first.summary_table
    generated, accepted, rejected = int(table.generated.sum()), int(table.accepted.sum()), int(table.rejected.sum())
    served, unserved = int(table.served.sum()), int(table.accepted_but_unserved.sum())
    print("24-HOUR SMALL-FLEET VALIDATION:", "PASS" if first.passed and deterministic else "FAIL")
    print(f"SIMULATION slots={len(first.result.slots)} fleet={first.fleet_size} active_grids={first.active_grid_count} seed={first.seed}")
    print(f"DEMAND_SOURCE={DEMAND_SOURCE} POPULARITY_SOURCE={POPULARITY_SOURCE}")
    print(f"FEDERATION_SCHEDULE_STATUS={FEDERATION_SCHEDULE_STATUS} slots={list(range(3, 48, 4))}")
    thresholds = first.popularity_thresholds
    validation_popularity = first.popularity_table.loc[first.popularity_table.TimeSlot < first.result.end_time]
    print(f"POPULARITY thresholds=({thresholds.q20:.6f},{thresholds.q40:.6f},{thresholds.q60:.6f},{thresholds.q80:.6f}) duplicates={thresholds.duplicates_present} ma_range=({validation_popularity.dropoff_ma_3h.min():.6f},{validation_popularity.dropoff_ma_3h.max():.6f})")
    print(f"POPULARITY levels={validation_popularity.popularity_level.value_counts().reindex(['Very Low','Low','Medium','High','Very High'], fill_value=0).to_dict()} values={validation_popularity.popularity_value.value_counts().sort_index().to_dict()}")
    print("POPULARITY_AUDIT", validation_popularity.head(8).to_dict("records"))
    print("SCALING_DISTRIBUTIONS", first.scaling_summary)
    count = first.scaling_clip_counts["contexts"]
    print("SCALING_CLIPS", {
        **first.scaling_clip_counts,
        "negative_demand_percentage": 100 * first.scaling_clip_counts["negative_demand"] / count,
        "upper_demand_percentage": 100 * first.scaling_clip_counts["upper_demand"] / count,
        "upper_supply_percentage": 100 * first.scaling_clip_counts["upper_supply"] / count,
    })
    print("LINUCB_CONDITIONING", first.linucb_conditioning)
    print("CONTEXT_NORM_SHARES", first.context_norm_shares)
    print("COLD_START", {"assignments": first.cold_start_assignments, "observed_rewards": first.cold_start_rewards, "normal_selection_begins_at": first.normal_selection_begins_at})
    reward_updates = sum(item["update_count"] for item in first.linucb_conditioning.values())
    print("PRICING_REWARD", {**first.reward_summary, "clip_count": first.reward_clip_count, "clip_percentage": 100 * first.reward_clip_count / reward_updates})
    print(f"REQUESTS generated={generated} accepted={accepted} rejected={rejected} served={served} accepted_but_unserved={unserved} acceptance_rate={accepted/generated:.4f} service_rate={served/generated:.4f}")
    print(f"REVENUE accepted={table.accepted_revenue.sum():.2f} served={table.served_revenue.sum():.2f}")
    print(f"FLEET mean_idle={table.idle.mean():.2f} mean_busy={table.busy.mean():.2f} mean_charging={table.charging.mean():.2f}")
    print(f"ENERGY initial={first.initial_energy_kwh:.6f} passenger={first.passenger_energy_consumed_kwh:.6f} reposition={first.repositioning_energy_consumed_kwh:.6f} charging={first.charging_energy_gained_kwh:.6f} final={first.final_energy_kwh:.6f} mean_soc={table.mean_soc.mean():.4f} min_vehicle={table.minimum_energy_kwh.min():.4f} max_vehicle={table.maximum_energy_kwh.max():.4f} error={first.energy_accounting_error_kwh:.3e}")
    print(f"CHARGING max_queue={int(table.max_queue.max())} mean_queue={table.mean_queue.mean():.3f} max_concurrent={int(table.charging_active.max())}")
    print(f"PRICING factor_counts={first.factor_counts}")
    fare_values = [value for slot in first.result.slots for statistic in slot.statistics for value in (statistic.mean_fare, statistic.ewma_fare) if value is not None]
    wait_values = [value for slot in first.result.slots for statistic in slot.statistics for value in (statistic.mean_wait, statistic.ewma_wait) if value is not None]
    print(f"NB9 fare_range=({min(fare_values):.4f},{max(fare_values):.4f}) wait_range=({min(wait_values):.4f},{max(wait_values):.4f})")
    completed_waits = [item for slot in first.result.slots for item in slot.driver_wait_observations]
    wait_minutes = [item.wait_minutes for item in completed_waits]
    wait_rows = [statistic for slot in first.result.slots for statistic in slot.statistics if statistic.wait_count]
    wait_utilities = [value for slot in first.result.slots for value in slot.routing_wait_utilities]
    print(f"DRIVER_WAIT observations={len(wait_minutes)} grids={len({item.grid_id for item in completed_waits})} min={min(wait_minutes):.4f} mean={sum(wait_minutes)/len(wait_minutes):.4f} max={max(wait_minutes):.4f} nonzero={sum(value > 0 for value in wait_minutes)}")
    print(f"DRIVER_WAIT_NB9 mean_range=({min(row.mean_wait for row in wait_rows):.4f},{max(row.mean_wait for row in wait_rows):.4f}) sd_range=({min(row.std_wait for row in wait_rows):.4f},{max(row.std_wait for row in wait_rows):.4f}) ewma_range=({min(row.ewma_wait for row in wait_rows):.4f},{max(row.ewma_wait for row in wait_rows):.4f}) utility_unique={len(set(round(value, 10) for value in wait_utilities))}")
    print(f"ROUTING actions={first.routing_action_counts} longest_busy_minutes={table.maximum_remaining_busy_minutes.max():.2f}")
    print(f"LEARNING pricing_updates={first.result.slots[-1].pricing_updates_after} nb12_training_updates={int(table.learners_trained.sum())} federation_rounds={int(table.federated.sum())}")
    print(f"GRID_POLICY sources={first.grid_policy_source_counts}")
    print(f"STABILITY deterministic_replay={deterministic} nan={first.nan_count} invariant_failures={len(first.invariant_failures)} energy_bound_failures={first.energy_bound_failures} probability_failures={first.probability_failures}")
    print("ARTIFACTS", *[str(path.relative_to(ROOT)) for path in artifacts], sep="\n- ")
    return 0 if first.passed and deterministic else 2


if __name__ == "__main__":
    raise SystemExit(main())
