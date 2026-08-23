#!/usr/bin/env python3
"""Demonstrate NB10 Part 1 battery transitions without station infrastructure."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.charging.energy import (
    apply_distance_energy, charge_vehicle, energy_consumed_kwh,
    energy_parameters_from_config, enter_charging, requires_charging,
)
from src.data.config import load_config
from src.fleet.state import VehicleState, VehicleStatus


def vehicle(energy_kwh: float) -> VehicleState:
    return VehicleState(0, 10, VehicleStatus.IDLE, None, 0, "idle", energy_kwh)


def main() -> int:
    """Run the specified 100-km movement and low-energy charging examples."""
    try:
        parameters = energy_parameters_from_config(load_config(ROOT / "config/config.yaml"))
        ev = vehicle(parameters.initial_energy_kwh)
        consumed = apply_distance_energy(ev, 100, parameters)
        if (consumed, ev.energy_level) != (15.0, 45.0):
            raise ValueError("100-km distance energy demonstration failed.")
        low_energy = vehicle(6.5)
        if not requires_charging(low_energy, parameters):
            raise ValueError("Low-energy EV did not require charging.")
        enter_charging(low_energy, parameters)
        gained = charge_vehicle(low_energy, 2, parameters)
        if abs(gained - 0.9) > 1e-9 or abs(low_energy.energy_level - 7.4) > 1e-9 or low_energy.trip_status is not VehicleStatus.CHARGING:
            raise ValueError("Two-minute charging demonstration failed.")
        low_energy.energy_level = 74.5
        gained = charge_vehicle(low_energy, 2, parameters)
        if abs(gained - 0.5) > 1e-9 or low_energy.energy_level != 75.0 or low_energy.trip_status is not VehicleStatus.IDLE:
            raise ValueError("Capacity cap/release demonstration failed.")
        print("NB10 EV ENERGY: PASS")
        print("start=60.0 kWh; 100 km × 0.15 kWh/km = 15.0 kWh; remaining=45.0 kWh")
        print("low-energy=6.5 kWh -> CHARGING; 30 kW × 0.90 × (2/60) h = +0.9 kWh -> 7.4 kWh")
        print("capacity/release: 74.5 kWh + 0.9 kWh -> capped at 75.0 kWh -> IDLE")
        return 0
    except (KeyError, ValueError) as error:
        print(f"NB10 EV ENERGY FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
