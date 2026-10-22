#!/usr/bin/env python3
"""Run an authoritative short production experiment and save compact output."""

from __future__ import annotations

import argparse
import json
import pandas as pd
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.simulation.production import run_production_preflight, write_preflight_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slots", type=int, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--driver-profiles", type=Path, help="Explicit approved profiles including charging_wait_preference_minutes")
    args = parser.parse_args()
    experiment, runtime = run_production_preflight(ROOT, args.slots, seed=args.seed, driver_profiles=pd.read_parquet(args.driver_profiles) if args.driver_profiles else None)
    payload = {
        "runtime_seconds": runtime,
        "reproducibility": {"seed": args.seed, "grid_version": "true_3km_v1"},
        "slots": experiment.reports,
    }
    if args.output is not None:
        payload["artifacts"] = [str(path) for path in write_preflight_artifacts(experiment, args.output, runtime)]
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
