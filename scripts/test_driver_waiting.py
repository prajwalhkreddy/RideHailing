#!/usr/bin/env python3
"""Controlled driver-idle waiting demonstration; no passenger-wait semantics."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.dispatch.dispatch import DriverWaitObservation
from src.simulation.statistics import OperationalStatistics


def main() -> None:
    waits = [
        DriverWaitObservation(1, 0, 6),  # idle 10:00, dispatch 10:06
        DriverWaitObservation(2, 1, 6),  # reposition arrival 10:12, dispatch 10:18
        DriverWaitObservation(3, 0, 6),  # idle 10:28, dispatch 10:34
    ]
    rows = OperationalStatistics([0, 1], .3).update_slot(0, driver_wait_observations=waits)
    for row in rows:
        print(f"grid={row.grid_id} mean_wait={row.mean_wait} std_wait={row.std_wait} ewma_wait={row.ewma_wait}")


if __name__ == "__main__":
    main()
