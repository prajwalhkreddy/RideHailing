"""Pricing-decision reporting from immutable temporal validation summaries."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.pricing.linucb import PRICING_FACTORS
from src.reporting import FIGURE_DPI, safe_ratio
from src.simulation.validation_24h import Validation24hReport


PRICING_COLUMNS = (
    "slot_index", "timestamp", "grid_id", "raw_predicted_demand", "scaled_predicted_demand",
    "raw_supply", "scaled_supply", "p_stay", "p_north", "p_east", "p_south", "p_west",
    "popularity", "selected_pricing_factor", "generated_requests", "accepted_requests",
    "rejected_requests", "accepted_revenue", "raw_revenue_per_opportunity", "normalized_reward",
    "reward_clipped", "linucb_selection_mode",
)


def pricing_decision_table(report: Validation24hReport) -> pd.DataFrame:
    """Return one validated row per active grid/context decision."""
    rows = []
    for slot in report.result.slots:
        for grid_id, factor in sorted(slot.pricing_factors.items()):
            audit = slot.pricing_context_audit[grid_id]
            vector = np.asarray(audit["routing_probabilities"], dtype=np.float64)
            generated = slot.pricing_generated[grid_id]
            accepted = slot.pricing_accepted[grid_id]
            rows.append({
                "slot_index": slot.slot_index, "timestamp": slot.timestamp, "grid_id": grid_id,
                "raw_predicted_demand": audit["raw_predicted_demand"],
                "scaled_predicted_demand": audit["scaled_predicted_demand"],
                "raw_supply": audit["raw_supply"], "scaled_supply": audit["scaled_supply"],
                "p_stay": vector[0], "p_north": vector[1], "p_east": vector[2],
                "p_south": vector[3], "p_west": vector[4], "popularity": slot.pricing_popularity[grid_id],
                "selected_pricing_factor": factor, "generated_requests": generated,
                "accepted_requests": accepted, "rejected_requests": generated - accepted,
                "accepted_revenue": slot.pricing_accepted_revenue[grid_id],
                "raw_revenue_per_opportunity": slot.pricing_raw_opportunity_reward[grid_id],
                "normalized_reward": slot.pricing_normalized_reward[grid_id],
                "reward_clipped": slot.pricing_reward_clipped[grid_id],
                "linucb_selection_mode": "COLD_START" if slot.pricing_cold_start[grid_id] else "LINUCB",
            })
    table = pd.DataFrame(rows, columns=PRICING_COLUMNS)
    validate_pricing_table(table)
    return table


def validate_pricing_table(table: pd.DataFrame) -> None:
    if tuple(table.columns) != PRICING_COLUMNS or table.empty:
        raise ValueError("Pricing reporting table has an invalid schema or no decisions.")
    if not set(table.selected_pricing_factor).issubset(PRICING_FACTORS):
        raise ValueError("Pricing report contains an unapproved pricing factor.")
    bounded = table[["scaled_predicted_demand", "scaled_supply", "popularity", "normalized_reward"]]
    if not np.isfinite(bounded).all().all() or not ((bounded >= 0) & (bounded <= 1)).all().all():
        raise ValueError("Pricing report contains non-finite or unbounded approved features/rewards.")
    probabilities = table[["p_stay", "p_north", "p_east", "p_south", "p_west"]].to_numpy(dtype=float)
    if not np.isfinite(probabilities).all() or (probabilities < 0).any() or not np.allclose(probabilities.sum(axis=1), 1.):
        raise ValueError("Pricing report contains invalid routing probabilities.")
    if not (table.generated_requests == table.accepted_requests + table.rejected_requests).all():
        raise ValueError("Pricing report request counts do not reconcile.")


def pricing_factor_summary(table: pd.DataFrame) -> pd.DataFrame:
    grouped = table.groupby("selected_pricing_factor", observed=True, sort=True)
    rows = []
    for factor in PRICING_FACTORS:
        group = grouped.get_group(factor) if factor in grouped.groups else table.iloc[0:0]
        generated, accepted = int(group.generated_requests.sum()), int(group.accepted_requests.sum())
        rows.append({
            "pricing_factor": factor, "decisions": len(group), "generated": generated,
            "accepted": accepted, "rejected": int(group.rejected_requests.sum()),
            "acceptance_rate": safe_ratio(accepted, generated),
            "accepted_revenue": float(group.accepted_revenue.sum()),
            "mean_raw_reward": float(group.raw_revenue_per_opportunity.mean()),
            "mean_normalized_reward": float(group.normalized_reward.mean()),
        })
    return pd.DataFrame(rows)


def pricing_reward_summary(table: pd.DataFrame) -> pd.DataFrame:
    return table.groupby("selected_pricing_factor", observed=True).normalized_reward.agg(
        count="count", mean="mean", median="median", std="std", min="min", max="max",
    ).reindex(PRICING_FACTORS).reset_index().rename(columns={"selected_pricing_factor": "pricing_factor"})


def _plot_context() -> None:
    import matplotlib
    matplotlib.use("Agg")


def plot_pricing(table: pd.DataFrame, output_dir: str | Path) -> tuple[Path, ...]:
    _plot_context()
    import matplotlib.pyplot as plt
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    note = "50 vehicles | 4 grids | 48 slots | seed 42 | engineering validation only"
    paths = []

    counts = table.selected_pricing_factor.value_counts().reindex(PRICING_FACTORS, fill_value=0)
    fig, ax = plt.subplots(figsize=(8.2, 4.8)); ax.bar([str(v) for v in PRICING_FACTORS], counts.values)
    ax.set(title="Pricing Factor Selection — 24-Hour Integration Validation\n" + note, xlabel="Pricing factor", ylabel="Pricing decisions")
    ax.bar_label(ax.containers[0]); fig.tight_layout(); path = output / "pricing_arm_selection_frequency.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    for grid_id, group in table.groupby("grid_id", sort=True):
        ax.plot(group.slot_index, group.selected_pricing_factor, marker="o", markersize=2.5, linewidth=1, label=f"Grid {grid_id}")
    ax.set(title="Observed Pricing Factor by Grid and Slot\n" + note, xlabel="Main slot", ylabel="Pricing factor", yticks=PRICING_FACTORS)
    ax.legend(ncol=4); fig.tight_layout(); path = output / "pricing_factor_over_time.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    rewards = pricing_reward_summary(table)
    fig, ax = plt.subplots(figsize=(8.2, 4.8)); ax.bar([str(v) for v in rewards.pricing_factor], rewards["mean"])
    ax.set(title="Observed Mean Normalized Reward by Pricing Factor\nSequential contextual-bandit data; not an optimality comparison", xlabel="Pricing factor", ylabel="Mean normalized reward")
    fig.tight_layout(); path = output / "pricing_reward_by_factor.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    fig, ax = plt.subplots(figsize=(8.2, 4.8)); delta = table.scaled_predicted_demand - table.scaled_supply
    scatter = ax.scatter(delta, table.selected_pricing_factor, c=table.slot_index, s=20, alpha=.75)
    ax.set(title="Pricing Factor Across Scaled Demand–Supply Contexts\nDescriptive engineering validation; no causal interpretation", xlabel="Scaled demand − scaled supply", ylabel="Selected pricing factor", yticks=PRICING_FACTORS)
    fig.colorbar(scatter, ax=ax, label="Main slot"); fig.tight_layout(); path = output / "demand_supply_pricing.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)
    return tuple(paths)
