#!/usr/bin/env python3
"""Demonstrate empirical pickup-position mapping to simulated mini-slots."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charging.energy import EnergyParameters
from src.dispatch.dispatch import dispatch_requests
from src.dispatch.generation import empirical_mini_slot_index, empirical_within_slot_offset_seconds, historical_bucket_start
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus


def main() -> int:
    print("Historical pickup | Bucket | Offset | Mini-slot | Simulated arrival")
    for value in ("08:01:20", "08:07:40", "08:17:43", "08:29:20"):
        pickup = datetime.fromisoformat(f"2026-01-01 {value}")
        offset = empirical_within_slot_offset_seconds(pickup)
        index = empirical_mini_slot_index(pickup)
        print(f"{value} | {historical_bucket_start(pickup):%H:%M} | {offset:.0f}s | {index} | 00:{index * 2:02d}")

    pickup = datetime(2026, 1, 1, 8, 28, 20)
    request = RequestState(
        0, empirical_mini_slot_index(pickup), 0, 1, base_fare=25., source_trip_id=0,
        empirical_pickup_datetime=pickup, empirical_dropoff_datetime=pickup + timedelta(minutes=18),
        trip_duration_minutes=18., trip_distance_miles=5., trip_distance_km=8.04672,
        empirical_within_slot_offset_seconds=empirical_within_slot_offset_seconds(pickup),
    )
    fleet = Fleet([VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 40.)], frozenset((0, 1)), 2)
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
    dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, energy)
    fleet.advance_mini_slot()
    print(f"cross-boundary trip: simulated_start=00:28 busy_until=00:46 status_at_00:30={fleet.vehicle(0).trip_status.value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
