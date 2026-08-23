"""Configuration loading for the reproducible first data/spatial milestone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOP_LEVEL_KEYS = {"data", "grid", "random_seed", "time"}


def load_config(path: str | Path = "config/config.yaml") -> dict[str, Any]:
    """Load and validate research-stage configuration.

    The first milestone keeps the NB1 3,000 m square grid as the default but
    reads all research parameters from configuration. Relative data paths are
    resolved by the caller against the repository root.

    Args:
        path: YAML configuration path.

    Returns:
        A validated configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If required settings or the NB1-compatible grid contract
            are absent or invalid.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    if not isinstance(config, dict):
        raise ValueError(f"Configuration must be a mapping: {config_path}")
    missing = REQUIRED_TOP_LEVEL_KEYS - set(config)
    if missing:
        raise ValueError(f"Configuration missing required sections: {sorted(missing)}")

    grid = config["grid"]
    if grid.get("geometry") != "square":
        raise ValueError("First milestone supports only the NB1 square-grid methodology.")
    if not isinstance(grid.get("size_meters"), int) or grid["size_meters"] <= 0:
        raise ValueError("grid.size_meters must be a positive integer.")
    if grid.get("metric_crs") != "EPSG:2263":
        raise ValueError("grid.metric_crs must be EPSG:2263 for NB1 compatibility.")
    if config["time"].get("interval_minutes") != 30:
        raise ValueError("time.interval_minutes must remain 30 for this milestone.")
    if not isinstance(config["random_seed"], int):
        raise ValueError("random_seed must be an integer.")
    if not isinstance(config["data"].get("month"), str):
        raise ValueError("data.month must be a string such as '2026-01'.")
    if "simulation" in config:
        simulation = config["simulation"]
        required_simulation = {"fleet_size", "main_slot_minutes", "mini_slot_minutes", "initialization_method"}
        if not isinstance(simulation, dict) or (missing := required_simulation - set(simulation)):
            raise ValueError(f"simulation configuration missing keys: {sorted(missing)}")
        if not isinstance(simulation["fleet_size"], int) or simulation["fleet_size"] <= 0:
            raise ValueError("simulation.fleet_size must be a positive integer.")
        main, mini = simulation["main_slot_minutes"], simulation["mini_slot_minutes"]
        if not isinstance(main, int) or not isinstance(mini, int) or main <= 0 or mini <= 0 or main % mini:
            raise ValueError("simulation main_slot_minutes must be a positive whole multiple of mini_slot_minutes.")
        if simulation["initialization_method"] != "uniform_valid_grid":
            raise ValueError("simulation.initialization_method must be uniform_valid_grid for this baseline.")
    if "dispatch" in config:
        dispatch = config["dispatch"]
        required_dispatch = {"arrival_method", "search_method", "contention_method", "default_trip_duration_minutes"}
        if not isinstance(dispatch, dict) or (missing := required_dispatch - set(dispatch)):
            raise ValueError(f"dispatch configuration missing keys: {sorted(missing)}")
        if dispatch["arrival_method"] != "uniform_seeded_mini_slot" or dispatch["search_method"] != "same_grid_then_direct_neighbours" or dispatch["contention_method"] != "fcfs_mini_slot_then_request_id":
            raise ValueError("dispatch configuration is incompatible with the approved baseline.")
        if not isinstance(dispatch["default_trip_duration_minutes"], int) or dispatch["default_trip_duration_minutes"] <= 0:
            raise ValueError("dispatch.default_trip_duration_minutes must be a positive integer.")
    if "statistics" in config:
        statistics = config["statistics"]
        if not isinstance(statistics, dict) or set(statistics) != {"ewma_alpha", "ewma_initialization"}:
            raise ValueError("statistics configuration must contain ewma_alpha and ewma_initialization.")
        alpha = statistics["ewma_alpha"]
        if not isinstance(alpha, (int, float)) or not 0 < alpha <= 1:
            raise ValueError("statistics.ewma_alpha must be in (0, 1].")
        if statistics["ewma_initialization"] != "first_observation":
            raise ValueError("statistics.ewma_initialization must be first_observation for this baseline.")
    if "energy" in config:
        energy = config["energy"]
        required_energy = {"battery_capacity_kwh", "initial_energy_kwh", "minimum_energy_kwh", "consumption_rate_kwh_per_km", "charging_power_kw", "charging_efficiency", "charging_release_energy_kwh", "mean_initial_soc", "initial_soc_std", "initial_soc_min", "initial_soc_max", "charging_trigger_soc"}
        if not isinstance(energy, dict) or (missing := required_energy - set(energy)):
            raise ValueError(f"energy configuration missing keys: {sorted(missing)}")
        values = [energy[key] for key in required_energy]
        if not all(isinstance(value, (int, float)) for value in values):
            raise ValueError("energy configuration values must be numeric.")
        capacity = energy["battery_capacity_kwh"]
        if capacity <= 0 or energy["consumption_rate_kwh_per_km"] < 0 or energy["charging_power_kw"] < 0:
            raise ValueError("energy capacity must be positive; rates cannot be negative.")
        if not 0 < energy["charging_efficiency"] <= 1:
            raise ValueError("energy.charging_efficiency must be in (0, 1].")
        for key in ("initial_energy_kwh", "minimum_energy_kwh", "charging_release_energy_kwh"):
            if not 0 <= energy[key] <= capacity:
                raise ValueError(f"energy.{key} must be within battery capacity.")
        if not 0 <= energy["initial_soc_min"] <= energy["mean_initial_soc"] <= energy["initial_soc_max"] <= 1 or energy["initial_soc_std"] < 0:
            raise ValueError("energy initial SOC bounds/mean/std are invalid.")
        if not 0 < energy["charging_trigger_soc"] <= 1:
            raise ValueError("energy.charging_trigger_soc must be in (0, 1].")
    if "charging" in config:
        charging = config["charging"]
        if not isinstance(charging, dict) or set(charging) != {"number_of_charging_stations", "station_max_power_kw"}:
            raise ValueError("charging configuration must contain number_of_charging_stations and station_max_power_kw.")
        if not isinstance(charging["number_of_charging_stations"], int) or charging["number_of_charging_stations"] <= 0:
            raise ValueError("charging.number_of_charging_stations must be a positive integer.")
        if not isinstance(charging["station_max_power_kw"], (int, float)) or charging["station_max_power_kw"] <= 0:
            raise ValueError("charging.station_max_power_kw must be positive.")
    if "routing" in config:
        routing = config["routing"]
        if not isinstance(routing, dict) or set(routing) != {"speed_kmph", "reposition_distance_km", "max_reposition_minutes"}:
            raise ValueError("routing configuration must contain speed_kmph, reposition_distance_km, max_reposition_minutes.")
        if not all(isinstance(routing[key], (int, float)) and routing[key] > 0 for key in routing):
            raise ValueError("routing configuration values must be positive.")
    return config
