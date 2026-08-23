#!/usr/bin/env python3
"""Run one controlled requests/dispatch integration scenario; no full simulation."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data.config import load_config
from src.charging.energy import energy_parameters_from_config, initialize_ev_fleet
from src.dispatch.dispatch import build_neighbour_lookup, dispatch_requests, request_summary
from src.dispatch.generation import build_empirical_od_distribution, generate_requests, validate_od_distribution
from src.fleet.fleet import Fleet, initialize_fleet, mini_slots_per_main_slot, validate_fleet
from src.fleet.supply import aggregate_grid_supply, validate_grid_supply


def main() -> int:
    """Exercise approved OD generation and local FCFS dispatch at configured scale."""
    try:
        config = load_config(ROOT / "config/config.yaml")
        processed = ROOT / config["data"]["processed_dir"]
        grid_path, neighbour_path, trips_path = processed / "grid_lookup.parquet", processed / "neighbour_map.parquet", processed / "cleaned_trips.parquet"
        missing = [str(path) for path in (grid_path, neighbour_path, trips_path) if not path.is_file()]
        if missing:
            raise FileNotFoundError("Dispatch requires frozen grid/trip artifacts: " + ", ".join(missing))
        valid_grid_ids = sorted(pd.read_parquet(grid_path, columns=["GridID"])["GridID"].astype(int).tolist())
        neighbours = build_neighbour_lookup(pd.read_parquet(neighbour_path), valid_grid_ids)
        trips = pd.read_parquet(trips_path, columns=["PUGridID", "DOGridID"])
        od = build_empirical_od_distribution(trips, valid_grid_ids)
        validate_od_distribution(od, valid_grid_ids)
        simulation, dispatch_config = config["simulation"], config["dispatch"]
        mini_slots = mini_slots_per_main_slot(simulation["main_slot_minutes"], simulation["mini_slot_minutes"])
        vehicles = initialize_ev_fleet(simulation["fleet_size"], valid_grid_ids, config["random_seed"], energy_parameters_from_config(config), simulation["initialization_method"])
        fleet = Fleet(vehicles, frozenset(valid_grid_ids), simulation["mini_slot_minutes"])
        initial_supply = aggregate_grid_supply(fleet.vehicles, valid_grid_ids)

        # Controlled stress input: one empirical origin, not a January replay.
        origin = max(od.origin_counts, key=od.origin_counts.get)
        requests = generate_requests({origin: 500}, od, valid_grid_ids, mini_slots, config["random_seed"])
        summaries: list[dict[str, int]] = []
        peak_busy = 0
        for mini_slot in range(mini_slots):
            arrivals = [request for request in requests if request.request_time == mini_slot]
            if arrivals:
                summaries.append(dispatch_requests(arrivals, fleet, neighbours, dispatch_config["default_trip_duration_minutes"], mini_slots))
            busy_now = sum(vehicle.trip_status.value == "BUSY" for vehicle in fleet.vehicles)
            peak_busy = max(peak_busy, busy_now)
            fleet.advance_mini_slot()
        summary = request_summary(requests)
        final_supply = aggregate_grid_supply(fleet.vehicles, valid_grid_ids)
        validate_fleet(fleet.vehicles, valid_grid_ids, simulation["fleet_size"])
        validate_grid_supply(final_supply, simulation["fleet_size"], valid_grid_ids)
        service_rate = summary["requests_served"] / summary["requests_total"] if summary["requests_total"] else 0.0
        print("REQUESTS + DISPATCH: PASS")
        print(f"od_source_trips: {od.total_trips}")
        print(f"od_pairs: {od.od_pair_count}")
        print(f"controlled_origin_grid: {origin}")
        print(f"requests_total: {summary['requests_total']}")
        print(f"requests_served: {summary['requests_served']}")
        print(f"requests_unserved: {summary['requests_unserved']}")
        print(f"service_rate: {service_rate:.4f}")
        print(f"fleet_before: idle={int(initial_supply.supply_idle.sum())}, busy={int(initial_supply.supply_busy.sum())}, charging={int(initial_supply.supply_charging.sum())}")
        print(f"peak_busy_after_dispatch: {peak_busy}")
        print(f"fleet_after_mini_slots: idle={int(final_supply.supply_idle.sum())}, busy={int(final_supply.supply_busy.sum())}, charging={int(final_supply.supply_charging.sum())}")
        return 0
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"REQUESTS + DISPATCH FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
