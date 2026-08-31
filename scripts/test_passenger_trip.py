#!/usr/bin/env python3
"""Demonstrate empirical passenger duration and one-time EV energy use."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charging.energy import EnergyParameters
from src.dispatch.dispatch import dispatch_requests
from src.dispatch.request import RequestState
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus


def main() -> int:
    pickup = datetime(2026, 1, 1, 0, 28)
    miles, duration = 5., 18.
    request = RequestState(
        0, 14, 0, 1, base_fare=25., source_trip_id=123,
        empirical_pickup_datetime=pickup,
        empirical_dropoff_datetime=pickup + timedelta(minutes=duration),
        trip_duration_minutes=duration,
        trip_distance_miles=miles,
        trip_distance_km=miles * 1.609344,
    )
    vehicle = VehicleState(0, 0, VehicleStatus.IDLE, None, 0, "idle", 40.)
    fleet = Fleet([vehicle], frozenset((0, 1)), 2)
    energy = EnergyParameters(75, 60, 7.5, .15, 30, .9, 75, .5, .05, .5, .7, .2)
    before = vehicle.energy_level
    dispatch_requests([request], fleet, {0: (1,), 1: (0,)}, 2, 15, energy)
    print(f"source_trip_id={request.source_trip_id} pickup={request.empirical_pickup_datetime} dropoff={request.empirical_dropoff_datetime}")
    print(f"assigned={request.assigned_vehicle_id is not None} duration_minutes={request.trip_duration_minutes} busy_until_minute={request.busy_until_minute}")
    print(f"distance_miles={request.trip_distance_miles} distance_km={request.trip_distance_km}")
    print(f"energy_before={before:.6f} passenger_energy={request.passenger_energy_kwh:.6f} energy_after={vehicle.energy_level:.6f}")
    after_assignment = vehicle.energy_level
    for step in range(1, 10):
        fleet.advance_mini_slot()
        absolute_time = pickup + timedelta(minutes=2 * step)
        print(f"time={absolute_time:%H:%M} status={vehicle.trip_status.value} energy={vehicle.energy_level:.6f}")
        if step < 9:
            assert vehicle.trip_status is VehicleStatus.BUSY
        assert vehicle.energy_level == after_assignment
    print(f"completed_at_or_after={pickup + timedelta(minutes=duration):%H:%M} final_grid={vehicle.current_grid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
