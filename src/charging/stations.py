"""NB10 station placement and power-limited FCFS charging infrastructure.

Station placement uses frozen January pickup/dropoff activity.  Station power,
nearest-centroid choice, FCFS contention, and 0.90 efficiency are approved
project decisions; this module intentionally omits road travel and stations'
physical/queue-capacity assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Collection, Iterable, Mapping

import numpy as np
import pandas as pd

from src.charging.energy import EnergyParameters, charge_vehicle, enter_charging, requires_charging
from src.fleet.state import VehicleState, VehicleStatus


STATION_COLUMNS = ["station_id", "grid_id", "pickup_count", "dropoff_count", "popularity"]


def build_station_definition(trips: pd.DataFrame, valid_grid_ids: Collection[int], number_of_stations: int) -> pd.DataFrame:
    """Select top historical grids by pickups plus dropoffs, with stable ties."""
    if not isinstance(number_of_stations, int) or number_of_stations <= 0:
        raise ValueError("number_of_stations must be a positive integer.")
    required = {"PUGridID", "DOGridID"}
    if missing := required - set(trips.columns):
        raise ValueError(f"Trips lack station-placement fields: {sorted(missing)}")
    valid = sorted(set(valid_grid_ids))
    if number_of_stations > len(valid):
        raise ValueError("number_of_stations cannot exceed the canonical valid-grid count.")
    source = trips[["PUGridID", "DOGridID"]]
    pickup = source.groupby("PUGridID", observed=True).size().rename("pickup_count")
    dropoff = source.groupby("DOGridID", observed=True).size().rename("dropoff_count")
    if not set(pickup.index).issubset(valid) or not set(dropoff.index).issubset(valid):
        raise ValueError("Frozen trips contain non-canonical station-placement GridIDs.")
    definition = pd.DataFrame({"grid_id": valid}).join(pickup, on="grid_id").join(dropoff, on="grid_id")
    definition[["pickup_count", "dropoff_count"]] = definition[["pickup_count", "dropoff_count"]].fillna(0).astype("int64")
    definition["popularity"] = definition["pickup_count"] + definition["dropoff_count"]
    definition = definition.sort_values(["popularity", "grid_id"], ascending=[False, True], kind="stable").head(number_of_stations).reset_index(drop=True)
    definition.insert(0, "station_id", np.arange(len(definition), dtype=np.int64))
    return definition[STATION_COLUMNS]


def save_station_definition(path: str | Path, definition: pd.DataFrame) -> None:
    """Persist the auditable top-station definition as a stable processed artifact."""
    validate_station_definition(definition, set(definition["grid_id"]))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    definition.to_parquet(target, index=False)


def validate_station_definition(definition: pd.DataFrame, valid_grid_ids: Collection[int], expected_count: int | None = None) -> None:
    """Validate auditable station ranking, counts, and deterministic IDs."""
    if definition.columns.tolist() != STATION_COLUMNS:
        raise ValueError("Station definition schema is incompatible with NB10.")
    if expected_count is not None and len(definition) != expected_count:
        raise ValueError("Station definition count does not match configuration.")
    if definition["station_id"].tolist() != list(range(len(definition))):
        raise ValueError("Station IDs must be sequential in popularity-rank order.")
    if not set(definition["grid_id"]).issubset(set(valid_grid_ids)) or definition["grid_id"].duplicated().any():
        raise ValueError("Station definition references invalid or duplicate GridIDs.")
    if (definition[["pickup_count", "dropoff_count", "popularity"]] < 0).any().any() or not (definition["popularity"] == definition["pickup_count"] + definition["dropoff_count"]).all():
        raise ValueError("Station popularity must reconcile with pickup and dropoff counts.")
    ranked = definition.sort_values(["popularity", "grid_id"], ascending=[False, True], kind="stable")
    if ranked["station_id"].tolist() != list(range(len(definition))):
        raise ValueError("Station rank must use popularity descending then lower GridID.")


@dataclass
class QueueEntry:
    """One queue state entry; wait is maintained in configured simulation minutes."""

    vehicle_id: int
    arrival_order: int
    random_priority: float
    wait_minutes: float = 0.0


@dataclass
class ChargingStation:
    """Power-only station state; active EVs reserve per-EV kW, no charger count."""

    station_id: int
    grid_id: int
    max_power_kw: float
    vehicle_charging_power_kw: float
    active_vehicle_ids: set[int] = field(default_factory=set)
    queue: list[QueueEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.station_id < 0 or self.grid_id < 0 or self.max_power_kw <= 0 or self.vehicle_charging_power_kw <= 0:
            raise ValueError("Charging station IDs and power values must be positive/valid.")

    @property
    def active_reserved_power_kw(self) -> float:
        return len(self.active_vehicle_ids) * self.vehicle_charging_power_kw

    @property
    def charging_available(self) -> bool:
        return self.active_reserved_power_kw + self.vehicle_charging_power_kw <= self.max_power_kw

    @property
    def charging_wait(self) -> float:
        """Mean wait of currently queued EVs; 0.0 when the FCFS queue is empty."""
        return float(np.mean([entry.wait_minutes for entry in self.queue])) if self.queue else 0.0


class ChargingInfrastructure:
    """Nearest-station selection, FCFS queue, power reservation, and release."""

    def __init__(self, stations: Iterable[ChargingStation], grid_centroids: Mapping[int, tuple[float, float]], random_seed: int = 42) -> None:
        station_list = list(stations)
        self.stations = {station.station_id: station for station in station_list}
        if not self.stations or len(self.stations) != len(station_list):
            raise ValueError("At least one uniquely identified charging station is required.")
        self.grid_centroids = dict(grid_centroids)
        if any(station.grid_id not in self.grid_centroids for station in self.stations.values()):
            raise ValueError("Charging station lacks a canonical grid centroid.")
        self.vehicle_station: dict[int, int] = {}
        self.rng = np.random.default_rng(random_seed)

    def nearest_station(self, vehicle: VehicleState) -> ChargingStation:
        """Choose projected-centroid nearest station; ties resolve by station_id."""
        if vehicle.current_grid not in self.grid_centroids:
            raise ValueError("Vehicle current grid lacks a canonical centroid.")
        x, y = self.grid_centroids[vehicle.current_grid]
        return min(self.stations.values(), key=lambda station: ((x - self.grid_centroids[station.grid_id][0]) ** 2 + (y - self.grid_centroids[station.grid_id][1]) ** 2, station.station_id))

    def present_vehicle(self, vehicle: VehicleState, parameters: EnergyParameters, arrival_order: int) -> ChargingStation:
        """Present a low-energy EV to nearest station with zero travel-time/energy model.

        Current grid becomes the selected station grid for infrastructure state;
        this is a zero-time, zero-energy placeholder only, not routing travel.
        """
        if vehicle.vehicle_id in self.vehicle_station:
            raise ValueError("Vehicle is already active or queued at a charging station.")
        if not requires_charging(vehicle, parameters):
            raise ValueError("Only vehicles below E_min enter the charging workflow.")
        station = self.nearest_station(vehicle)
        enter_charging(vehicle, parameters)
        vehicle.current_grid = station.grid_id
        self.vehicle_station[vehicle.vehicle_id] = station.station_id
        if station.charging_available:
            station.active_vehicle_ids.add(vehicle.vehicle_id)
            vehicle.current_action = "charging"
        else:
            station.queue.append(QueueEntry(vehicle.vehicle_id, arrival_order, float(self.rng.random())))
            station.queue.sort(key=lambda entry: (entry.arrival_order, entry.random_priority, entry.vehicle_id))
            vehicle.current_action = "charging_queue"
        return station

    def advance_mini_slot(self, vehicles: Iterable[VehicleState], duration_minutes: float, parameters: EnergyParameters) -> None:
        """Increment queue waits, charge active EVs, release power, and promote FCFS."""
        if duration_minutes < 0:
            raise ValueError("Charging mini-slot duration must be non-negative.")
        vehicle_by_id = {vehicle.vehicle_id: vehicle for vehicle in vehicles}
        for station in self.stations.values():
            for entry in station.queue:
                entry.wait_minutes += duration_minutes
            released: list[int] = []
            for vehicle_id in sorted(station.active_vehicle_ids):
                vehicle = vehicle_by_id.get(vehicle_id)
                if vehicle is None:
                    raise ValueError("Active charging vehicle is absent from fleet state.")
                charge_vehicle(vehicle, duration_minutes, parameters)
                if vehicle.trip_status is VehicleStatus.IDLE:
                    released.append(vehicle_id)
            for vehicle_id in released:
                station.active_vehicle_ids.remove(vehicle_id)
                self.vehicle_station.pop(vehicle_id, None)
            while station.queue and station.charging_available:
                entry = station.queue.pop(0)
                vehicle = vehicle_by_id.get(entry.vehicle_id)
                if vehicle is None:
                    raise ValueError("Queued charging vehicle is absent from fleet state.")
                station.active_vehicle_ids.add(vehicle.vehicle_id)
                vehicle.current_action = "charging"

    def charging_observations(self) -> dict[int, tuple[bool, float]]:
        """Expose station-grid availability and mean current queue wait for NB9."""
        return {station.grid_id: (station.charging_available, station.charging_wait) for station in self.stations.values()}


def stations_from_definition(definition: pd.DataFrame, max_power_kw: float, vehicle_charging_power_kw: float) -> list[ChargingStation]:
    """Instantiate power-only station state from persisted placement definitions."""
    return [ChargingStation(int(row.station_id), int(row.grid_id), float(max_power_kw), float(vehicle_charging_power_kw)) for row in definition.itertuples(index=False)]
