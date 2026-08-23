#!/usr/bin/env python3
"""Demonstrate NB9 main-slot statistics/EWMA with a small synthetic scenario."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.config import load_config
from src.dispatch.request import RequestState, RequestStatus
from src.simulation.statistics import FareObservation, OperationalStatistics, routing_feature_frame


def assigned(request_id: int, origin: int, wait: int) -> RequestState:
    """Create explicit synthetic successful-dispatch observations for the demo."""
    return RequestState(request_id, 0, origin, origin, RequestStatus.ASSIGNED, request_id, wait)


def main() -> int:
    """Check first-observation, EWMA formula, and missing-data carry-forward."""
    try:
        config = load_config(ROOT / "config/config.yaml")
        engine = OperationalStatistics([10, 20, 30], **config["statistics"])
        slot_one = engine.update_slot(
            1,
            fare_observations=[FareObservation(10, 100), FareObservation(10, 120), FareObservation(10, 140)],
            requests=[assigned(0, 10, 0), assigned(1, 10, 2), assigned(2, 10, 4), RequestState(3, 0, 20, 20, RequestStatus.UNSERVED)],
        )
        slot_two = engine.update_slot(
            2,
            fare_observations=[FareObservation(10, 160), FareObservation(10, 180)],
            requests=[assigned(4, 10, 6), assigned(5, 10, 8)],
        )
        one = {record.grid_id: record for record in slot_one}
        two = {record.grid_id: record for record in slot_two}
        if (one[10].mean_fare, one[10].std_fare, one[10].mean_wait, one[10].std_wait) != (120.0, (800 / 3) ** 0.5, 2.0, (8 / 3) ** 0.5):
            raise ValueError("Slot-one population statistics do not match the deterministic example.")
        if abs(two[10].ewma_fare - 135.0) > 1e-9 or abs(two[10].ewma_wait - 3.5) > 1e-9:
            raise ValueError("Slot-two EWMA formula does not match alpha=0.30.")
        if two[20].ewma_fare is not None or two[20].ewma_wait is not None or two[30].ewma_fare is not None:
            raise ValueError("Never-observed grids must remain uninitialized.")
        if any(record.charging_available is not None or record.charging_wait is not None for record in slot_two):
            raise ValueError("Charging context must remain unavailable before NB10.")
        print("NB9 STATISTICS: PASS")
        print("slot_1_grid_10: mean_fare=120.0, std_fare=16.3299, mean_wait=2.0, std_wait=1.6330, ewma_fare=120.0, ewma_wait=2.0")
        print("slot_2_grid_10: mean_fare=170.0, mean_wait=7.0, ewma_fare=135.0, ewma_wait=3.5")
        print("no_observation_grids: EWMA remains missing; charging context missing")
        print(f"routing_feature_rows: {len(routing_feature_frame(slot_two))}")
        return 0
    except (KeyError, ValueError) as error:
        print(f"NB9 STATISTICS FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
