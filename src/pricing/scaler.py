"""Deterministic preprocessing for the approved bounded LinUCB context."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np


DEFAULT_SCALER_METADATA_PATH = Path(__file__).resolve().parents[2] / "config/pricing_context_scaler.json"


@dataclass(frozen=True)
class PricingContextScaler:
    """Apply fixed log1p/P99 transforms without fitting on runtime data."""

    demand_ref_p99: float
    supply_ref_p99: float
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name, value in (("demand_ref_p99", self.demand_ref_p99), ("supply_ref_p99", self.supply_ref_p99)):
            if isinstance(value, bool) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite.")

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any]) -> "PricingContextScaler":
        return cls(float(metadata["demand_ref_p99"]), float(metadata["supply_ref_p99"]), dict(metadata))

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


DEFAULT_PRICING_CONTEXT_SCALER = PricingContextScaler.load()
