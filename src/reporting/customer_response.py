"""Aggregated customer-response reporting without per-request persistence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.pricing.customer import customer_acceptance_probability
from src.pricing.linucb import PRICING_FACTORS
from src.reporting import FIGURE_DPI, safe_ratio
from src.simulation.validation_24h import Validation24hReport


CUSTOMER_COLUMNS = (
    "slot_index", "timestamp", "grid_id", "pricing_factor", "generated_requests",
    "accepted_requests", "rejected_requests", "acceptance_rate", "accepted_revenue",
    "raw_revenue_per_opportunity", "normalized_reward", "mean_acceptance_probability",
    "min_acceptance_probability", "max_acceptance_probability",
)


def customer_response_table(report: Validation24hReport) -> pd.DataFrame:
    rows = []
    for slot in report.result.slots:
        for grid_id, factor in sorted(slot.pricing_factors.items()):
            generated, accepted = slot.pricing_generated[grid_id], slot.pricing_accepted[grid_id]
            probability = slot.pricing_acceptance_probability_summary[grid_id]
            rows.append({
                "slot_index": slot.slot_index, "timestamp": slot.timestamp, "grid_id": grid_id,
                "pricing_factor": factor, "generated_requests": generated, "accepted_requests": accepted,
                "rejected_requests": generated - accepted, "acceptance_rate": safe_ratio(accepted, generated),
                "accepted_revenue": slot.pricing_accepted_revenue[grid_id],
                "raw_revenue_per_opportunity": slot.pricing_raw_opportunity_reward[grid_id],
                "normalized_reward": slot.pricing_normalized_reward[grid_id],
                "mean_acceptance_probability": None if probability is None else probability[0],
                "min_acceptance_probability": None if probability is None else probability[1],
                "max_acceptance_probability": None if probability is None else probability[2],
            })
    table = pd.DataFrame(rows, columns=CUSTOMER_COLUMNS)
    if not (table.generated_requests == table.accepted_requests + table.rejected_requests).all():
        raise ValueError("Customer-response counts do not reconcile.")
    rates = table.acceptance_rate.to_numpy(dtype=float)
    if not np.isfinite(rates).all() or ((rates < 0) | (rates > 1)).any():
        raise ValueError("Customer-response rates are invalid.")
    return table


def customer_acceptance_summary(table: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor in PRICING_FACTORS:
        group = table.loc[table.pricing_factor == factor]
        generated, accepted = int(group.generated_requests.sum()), int(group.accepted_requests.sum())
        rows.append({
            "pricing_factor": factor, "generated": generated, "accepted": accepted,
            "rejected": int(group.rejected_requests.sum()), "acceptance_rate": safe_ratio(accepted, generated),
        })
    return pd.DataFrame(rows)


def plot_customer_response(table: pd.DataFrame, output_dir: str | Path) -> tuple[Path, ...]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    summary = customer_acceptance_summary(table)
    paths = []

    fig, ax = plt.subplots(figsize=(8.2, 4.8)); bars = ax.bar([str(v) for v in summary.pricing_factor], summary.acceptance_rate)
    ax.set(title="Observed Acceptance Rate by Pricing Factor\nAggregate accepted/generated; engineering validation", xlabel="Pricing factor", ylabel="Acceptance rate", ylim=(0, 1))
    ax.bar_label(bars, labels=[f"{rate:.1%}\nn={count}" for rate, count in zip(summary.acceptance_rate, summary.generated)], fontsize=7)
    fig.tight_layout(); path = output / "acceptance_rate_by_factor.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    x = np.arange(len(PRICING_FACTORS)); width = .26
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(x - width, summary.generated, width, label="Generated"); ax.bar(x, summary.accepted, width, label="Accepted"); ax.bar(x + width, summary.rejected, width, label="Rejected")
    ax.set(title="Observed Customer Response by Pricing Factor\nEngineering validation", xlabel="Pricing factor", ylabel="Requests", xticks=x, xticklabels=[str(v) for v in PRICING_FACTORS]); ax.legend()
    fig.tight_layout(); path = output / "customer_response_by_factor.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    factors = np.asarray(PRICING_FACTORS)
    ratios = (0.25, 0.5, 1.0, 2.0)
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for ratio in ratios:
        probabilities = [customer_acceptance_probability(factor, ratio, 1.) for factor in factors]
        ax.plot(factors, probabilities, marker="o", label=f"V/O = {ratio:g}")
    ax.set(title="Illustrative Sensitivity Curve Using Fixed Supply–Demand Ratios\nMathematical illustration; not observed simulation data", xlabel="Pricing factor", ylabel="Expected acceptance probability", ylim=(0, 1), xticks=PRICING_FACTORS)
    ax.legend(title="Fixed ratio"); fig.tight_layout(); path = output / "customer_acceptance_sensitivity_example.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)
    return tuple(paths)
