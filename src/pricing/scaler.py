"""Deterministic preprocessing for the approved bounded LinUCB context."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


DEFAULT_SCALER_METADATA_PATH = Path(__file__).resolve().parents[2] / "config/pricing_context_scaler.json"


def fit_supply_reference_p99(
    raw_supply, observation_times, training_start_inclusive, training_end_exclusive,
) -> float:
    """Fit the existing P99 reference using chronology-safe raw observations."""
    values = np.asarray(raw_supply, dtype=np.float64)
    times = pd.to_datetime(np.asarray(observation_times), errors="coerce")
    start, cutoff = pd.Timestamp(training_start_inclusive), pd.Timestamp(training_end_exclusive)
    if values.ndim != 1 or times.ndim != 1 or len(values) != len(times) or not len(values):
        raise ValueError("Supply calibration values and timestamps must be aligned non-empty vectors.")
    if not np.isfinite(values).all() or (values < 0).any() or pd.isna(times).any():
        raise ValueError("Supply calibration observations must be finite, non-negative, and timestamped.")
    if start.tz is not None or cutoff.tz is not None or not start < cutoff:
        raise ValueError("Supply calibration boundaries must be ordered and timezone-naive.")
    training = values[(times >= start) & (times < cutoff)]
    if not len(training):
        raise ValueError("No training/reference supply observations precede the cutoff.")
    reference = float(np.percentile(training, 99))
    if not np.isfinite(reference) or reference <= 0:
        raise ValueError("Supply P99 reference must be finite and positive.")
    return reference


def fit_base_price_reference_p99(
    weather_codes, periods, observation_times, sensitivity_groups,
    training_start_inclusive, training_end_exclusive,
) -> float:
    """Fit request-weighted P99 after mapping each reference row to P_base(W,T)."""
    weather = np.asarray(weather_codes, dtype=np.float64)
    period_values = np.asarray(periods, dtype=np.float64)
    times = pd.to_datetime(np.asarray(observation_times), errors="coerce")
    if weather.ndim != 1 or period_values.ndim != 1 or times.ndim != 1:
        raise ValueError("Base-price calibration inputs must be one-dimensional.")
    if not len(weather) or len(weather) != len(period_values) or len(weather) != len(times):
        raise ValueError("Base-price calibration inputs must be aligned and non-empty.")
    if not np.isfinite(weather).all() or not np.isfinite(period_values).all() or pd.isna(times).any():
        raise ValueError("Base-price calibration context must be finite and timestamped.")
    if ((period_values < 0) | (period_values > 47) | (period_values % 1 != 0)).any():
        raise ValueError("Base-price calibration Period must be an integer in 0..47.")
    start, cutoff = pd.Timestamp(training_start_inclusive), pd.Timestamp(training_end_exclusive)
    if start.tz is not None or cutoff.tz is not None or not start < cutoff:
        raise ValueError("Base-price calibration boundaries must be ordered and timezone-naive.")
    required = {"WeatherCode", "Period", "P_base"}
    if missing := required - set(sensitivity_groups.columns):
        raise ValueError(f"Sensitivity groups lack base-price columns: {sorted(missing)}")
    groups = sensitivity_groups[list(required)].copy()
    if groups.duplicated(["WeatherCode", "Period"]).any():
        raise ValueError("P_base lookup must be unique by WeatherCode and Period.")
    selected = (times >= start) & (times < cutoff)
    observations = pd.DataFrame({
        "WeatherCode": weather[selected], "Period": period_values[selected].astype(np.int64),
    })
    if observations.empty:
        raise ValueError("No base-price observations precede the training cutoff.")
    mapped = observations.merge(groups, on=["WeatherCode", "Period"], how="left", validate="many_to_one")
    values = mapped["P_base"].to_numpy(dtype=np.float64)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Every calibration observation requires a finite positive P_base(W,T).")
    return float(np.percentile(values, 99))


@dataclass(frozen=True)
class PricingContextScaler:
    """Apply fixed log1p/P99 transforms without fitting on runtime data."""

    demand_ref_p99: float
    supply_ref_p99: float
    metadata: Mapping[str, Any] | None = None
    distance_ref_p99_km: float | None = None
    base_price_ref_p99: float | None = None

    def __post_init__(self) -> None:
        for name, value in (("demand_ref_p99", self.demand_ref_p99), ("supply_ref_p99", self.supply_ref_p99)):
            if isinstance(value, bool) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite.")
        for name, value in (("distance_ref_p99_km", self.distance_ref_p99_km), ("base_price_ref_p99", self.base_price_ref_p99)):
            if value is not None and (isinstance(value, bool) or not np.isfinite(value) or value <= 0):
                raise ValueError(f"{name} must be positive and finite when provided.")

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any]) -> "PricingContextScaler":
        return cls(
            float(metadata["demand_ref_p99"]), float(metadata["supply_ref_p99"]), dict(metadata),
            None if "distance_ref_p99_km" not in metadata else float(metadata["distance_ref_p99_km"]),
            None if "base_price_ref_p99" not in metadata else float(metadata["base_price_ref_p99"]),
        )

    @classmethod
    def load(cls, path: str | Path = DEFAULT_SCALER_METADATA_PATH) -> "PricingContextScaler":
        with Path(path).open(encoding="utf-8") as handle:
            return cls.from_metadata(json.load(handle))

    def scale_demand(self, raw_demand: float) -> float:
        value = float(raw_demand)
        if not np.isfinite(value):
            raise ValueError("Raw predicted demand must be finite.")
        nonnegative = max(0.0, value)
        return float(np.clip(np.log1p(nonnegative) / np.log1p(self.demand_ref_p99), 0.0, 1.0))

    def scale_supply(self, raw_supply: float) -> float:
        value = float(raw_supply)
        if not np.isfinite(value) or value < 0:
            raise ValueError("Raw supply must be finite and non-negative.")
        return float(np.clip(np.log1p(value) / np.log1p(self.supply_ref_p99), 0.0, 1.0))

    def scale_distance(self, distance_km: float) -> float:
        value = float(distance_km)
        if not np.isfinite(value) or value < 0:
            raise ValueError("Trip distance must be finite, non-negative, and expressed in kilometres.")
        if self.distance_ref_p99_km is None:
            raise ValueError("Pricing scaler has no approved distance_ref_p99_km.")
        return float(np.clip(np.log1p(value) / np.log1p(self.distance_ref_p99_km), 0.0, 1.0))

    def scale_base_price(self, p_base: float) -> float:
        value = float(p_base)
        if not np.isfinite(value) or value <= 0:
            raise ValueError("P_base must be finite and strictly positive.")
        if self.base_price_ref_p99 is None:
            raise ValueError("Pricing scaler has no approved base_price_ref_p99.")
        return float(np.clip(np.log1p(value) / np.log1p(self.base_price_ref_p99), 0.0, 1.0))


DEFAULT_PRICING_CONTEXT_SCALER = PricingContextScaler.load()
DEFAULT_DISTANCE_REF_P99_KM = float(DEFAULT_PRICING_CONTEXT_SCALER.distance_ref_p99_km)
DEFAULT_BASE_PRICE_REF_P99 = float(DEFAULT_PRICING_CONTEXT_SCALER.base_price_ref_p99)
