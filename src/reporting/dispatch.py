"""Request-flow and dispatch reporting from completed validation slots."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.reporting import FIGURE_DPI, safe_ratio
from src.simulation.validation_24h import Validation24hReport


DISPATCH_COLUMNS = (
    "slot_index", "timestamp", "generated", "accepted", "rejected", "served",
    "accepted_unserved", "acceptance_rate", "service_rate", "dispatch_success_rate",
)


def dispatch_summary_table(report: Validation24hReport) -> pd.DataFrame:
    rows = []
    for slot in report.result.slots:
        rows.append({
            "slot_index": slot.slot_index, "timestamp": slot.timestamp, "generated": slot.generated,
            "accepted": slot.accepted, "rejected": slot.rejected, "served": slot.served,
            "accepted_unserved": slot.accepted_but_unserved,
            "acceptance_rate": safe_ratio(slot.accepted, slot.generated),
            "service_rate": safe_ratio(slot.served, slot.generated),
            "dispatch_success_rate": safe_ratio(slot.served, slot.accepted),
        })
    table = pd.DataFrame(rows, columns=DISPATCH_COLUMNS)
    validate_dispatch_table(table)
    return table


def validate_dispatch_table(table: pd.DataFrame) -> None:
    if table.empty or not (table.generated == table.accepted + table.rejected).all():
        raise ValueError("Dispatch generated/accepted/rejected counts do not reconcile.")
    if not (table.accepted == table.served + table.accepted_unserved).all():
        raise ValueError("Dispatch accepted/served/unserved counts do not reconcile.")
    if not (table.generated == table.rejected + table.served + table.accepted_unserved).all():
        raise ValueError("Dispatch terminal request outcomes do not reconcile.")
    rates = table[["acceptance_rate", "service_rate", "dispatch_success_rate"]].to_numpy(dtype=float)
    if not np.isfinite(rates).all() or ((rates < 0) | (rates > 1)).any():
        raise ValueError("Dispatch report contains invalid rates.")


def dispatch_metric_summary(table: pd.DataFrame) -> pd.DataFrame:
    generated, accepted = int(table.generated.sum()), int(table.accepted.sum())
    values = (
        ("generated", generated), ("accepted", accepted), ("rejected", int(table.rejected.sum())),
        ("served", int(table.served.sum())), ("accepted_unserved", int(table.accepted_unserved.sum())),
        ("acceptance_rate", safe_ratio(accepted, generated)),
        ("dispatch_success_rate", safe_ratio(int(table.served.sum()), accepted)),
        ("service_rate", safe_ratio(int(table.served.sum()), generated)),
    )
    return pd.DataFrame(values, columns=["metric", "value"])


def plot_dispatch(table: pd.DataFrame, output_dir: str | Path) -> tuple[Path, ...]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    totals = table[["generated", "accepted", "rejected", "served", "accepted_unserved"]].sum()
    paths = []

    labels = ["Generated", "Accepted", "Served", "Rejected", "Accepted\nbut unserved"]
    values = [totals.generated, totals.accepted, totals.served, totals.rejected, totals.accepted_unserved]
    fig, ax = plt.subplots(figsize=(8.2, 4.8)); bars = ax.bar(labels, values)
    ax.set(title="Request Funnel — 24-Hour Engineering Validation", ylabel="Requests"); ax.bar_label(bars)
    fig.tight_layout(); path = output / "request_funnel.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    labels = ["Served", "Customer rejected", "Accepted but unserved"]
    values = [totals.served, totals.rejected, totals.accepted_unserved]
    fig, ax = plt.subplots(figsize=(8.2, 4.8)); bars = ax.bar(labels, values)
    ax.set(title="Terminal Request Outcomes — Engineering Validation", ylabel="Requests"); ax.bar_label(bars)
    fig.tight_layout(); path = output / "request_outcomes.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for column, label in (("acceptance_rate", "Acceptance rate"), ("dispatch_success_rate", "Dispatch success rate"), ("service_rate", "Service rate")):
        ax.plot(table.slot_index, table[column], marker="o", markersize=2.5, linewidth=1, label=label)
    ax.set(title="Observed Request Rates by Main Slot", xlabel="Main slot", ylabel="Rate", ylim=(0, 1)); ax.legend()
    fig.tight_layout(); path = output / "service_rates_over_time.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for column in ("generated", "accepted", "served"):
        ax.plot(table.slot_index, table[column], marker="o", markersize=2.5, linewidth=1, label=column.title())
    ax.set(title="Observed Request Flow by Main Slot", xlabel="Main slot", ylabel="Requests"); ax.legend()
    fig.tight_layout(); path = output / "request_flow_over_time.png"; fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig); paths.append(path)
    return tuple(paths)
