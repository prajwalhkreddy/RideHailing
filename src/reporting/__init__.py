"""Read-only tables and figures derived from completed simulation results."""

from pathlib import Path


VALIDATION_RUN_NAME = "validation_50v_4g_48slots_seed42"
FIGURE_DPI = 240


def ensure_reporting_directories(root: str | Path) -> dict[str, Path]:
    base = Path(root) / "results"
    paths = {
        "validation": base / "validation" / VALIDATION_RUN_NAME,
        "pricing_figures": base / "figures" / "pricing",
        "customer_figures": base / "figures" / "customer_response",
        "dispatch_figures": base / "figures" / "dispatch",
        "pricing_tables": base / "tables" / "pricing",
        "customer_tables": base / "tables" / "customer_response",
        "dispatch_tables": base / "tables" / "dispatch",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def safe_ratio(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else float(numerator / denominator)
