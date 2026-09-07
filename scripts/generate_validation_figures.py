#!/usr/bin/env python3
"""Generate compact tables and figures from the deterministic validation run."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pricing.linucb import PRICING_FACTORS
from src.reporting import VALIDATION_RUN_NAME, ensure_reporting_directories, safe_ratio
from src.reporting.customer_response import (
    customer_acceptance_summary, customer_response_table, plot_customer_response,
)
from src.reporting.dispatch import dispatch_metric_summary, dispatch_summary_table, plot_dispatch
from src.reporting.pricing import (
    plot_pricing, pricing_decision_table, pricing_factor_summary, pricing_reward_summary,
)
from src.simulation.validation_24h import Validation24hReport, run_small_fleet_validation


EXPECTED_TOTALS = {"generated": 1536, "accepted": 1159, "rejected": 377, "served": 1065, "accepted_unserved": 94}
EXPECTED_FACTORS = {0.85: 23, 0.90: 24, 0.95: 23, 1.00: 29, 1.05: 28, 1.10: 30, 1.15: 35}


def _write_csv(frame, path: Path) -> None:
    frame.to_csv(path, index=False, float_format="%.12g", date_format="%Y-%m-%dT%H:%M:%S", lineterminator="\n")


def _summary(report: Validation24hReport, pricing, dispatch) -> dict[str, object]:
    totals = {name: int(dispatch[name].sum()) for name in ("generated", "accepted", "rejected", "served", "accepted_unserved")}
    counts = pricing.selected_pricing_factor.value_counts().reindex(PRICING_FACTORS, fill_value=0)
    return {
        "run_name": VALIDATION_RUN_NAME, "seed": report.seed, "vehicles": report.fleet_size,
        "grids": report.active_grid_count, "slots": len(report.result.slots),
        "main_slot_minutes": 30, "mini_slot_minutes": 2, **totals,
        "acceptance_rate": safe_ratio(totals["accepted"], totals["generated"]),
        "service_rate": safe_ratio(totals["served"], totals["generated"]),
        "dispatch_success_rate": safe_ratio(totals["served"], totals["accepted"]),
        "pricing_selection_counts": {f"{factor:.2f}": int(counts[factor]) for factor in PRICING_FACTORS},
        "pricing_reward": {
            "raw_min": report.reward_summary["raw_revenue_per_opportunity"]["min"],
            "raw_median": report.reward_summary["raw_revenue_per_opportunity"]["median"],
            "raw_p95": report.reward_summary["raw_revenue_per_opportunity"]["p95"],
            "raw_max": report.reward_summary["raw_revenue_per_opportunity"]["max"],
            "normalized_min": report.reward_summary["normalized_reward"]["min"],
            "normalized_median": report.reward_summary["normalized_reward"]["median"],
            "normalized_p95": report.reward_summary["normalized_reward"]["p95"],
            "normalized_max": report.reward_summary["normalized_reward"]["max"],
            "clipping_count": report.reward_clip_count,
        },
        "energy_reconciliation_error": report.energy_accounting_error_kwh,
        "regression_metadata": {"baseline_tests": 175, "fixture": "engineering_validation_only"},
    }


def generate_reporting(root: str | Path = ROOT, report: Validation24hReport | None = None, *, plots: bool = True) -> tuple[Path, ...]:
    """Build deterministic artifacts without mutating the supplied report."""
    root_path = Path(root)
    validation = run_small_fleet_validation(48, seed=42) if report is None else report
    if (validation.seed, validation.fleet_size, validation.active_grid_count, len(validation.result.slots)) != (42, 50, 4, 48):
        raise ValueError("Reporting requires the exact 50v/4g/48-slot/seed-42 validation fixture.")
    paths = ensure_reporting_directories(root_path)
    pricing = pricing_decision_table(validation)
    customer = customer_response_table(validation)
    dispatch = dispatch_summary_table(validation)
    summary = _summary(validation, pricing, dispatch)
    actual_totals = {name: summary[name] for name in EXPECTED_TOTALS}
    actual_factors = {factor: int((pricing.selected_pricing_factor == factor).sum()) for factor in PRICING_FACTORS}
    if actual_totals != EXPECTED_TOTALS or actual_factors != EXPECTED_FACTORS:
        raise ValueError(f"Validation reporting regression mismatch: totals={actual_totals}, factors={actual_factors}")
    if not validation.passed:
        raise ValueError(f"Validation invariants failed: {validation.invariant_failures}")

    artifacts = []
    table_specs = (
        (pricing, paths["validation"] / "pricing_decisions.csv"),
        (customer, paths["validation"] / "customer_response.csv"),
        (dispatch, paths["validation"] / "dispatch_summary.csv"),
        (pricing_factor_summary(pricing), paths["pricing_tables"] / "pricing_factor_summary.csv"),
        (pricing_reward_summary(pricing), paths["pricing_tables"] / "pricing_reward_summary.csv"),
        (customer_acceptance_summary(customer), paths["customer_tables"] / "customer_acceptance_summary.csv"),
        (dispatch_metric_summary(dispatch), paths["dispatch_tables"] / "dispatch_summary.csv"),
    )
    for frame, path in table_specs:
        _write_csv(frame, path); artifacts.append(path)
    summary_path = paths["validation"] / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"); artifacts.append(summary_path)

    figure_paths = ()
    if plots:
        figure_paths = (
            *plot_pricing(pricing, paths["pricing_figures"]),
            *plot_customer_response(customer, paths["customer_figures"]),
            *plot_dispatch(dispatch, paths["dispatch_figures"]),
        )
        artifacts.extend(figure_paths)
    source_by_group = {
        "pricing": "results/validation/validation_50v_4g_48slots_seed42/pricing_decisions.csv",
        "customer_response": "results/validation/validation_50v_4g_48slots_seed42/customer_response.csv",
        "dispatch": "results/validation/validation_50v_4g_48slots_seed42/dispatch_summary.csv",
    }
    manifest = {
        str(path.relative_to(root_path)): source_by_group[path.parent.name]
        for path in figure_paths
    }
    manifest_path = paths["validation"] / "figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"); artifacts.append(manifest_path)
    return tuple(artifacts)


def main() -> int:
    artifacts = generate_reporting()
    print("VALIDATION REPORTING: PASS")
    for path in artifacts:
        print(f"- {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
