"""Opt-in Record-030 pricing interface; empirical-response integration is pending."""
from dataclasses import dataclass
import math
from typing import Mapping

BLOCKER = (
    'Record-030 experiment blocked: runtime historical_sensitivity samples positive '
    'truncated Normal and divides by epsilon in maximum_price; it does not implement '
    'the frozen signed Record-029 empirical sampler or its passenger-response adapter.'
)

@dataclass(frozen=True)
class TimePricingPolicy:
    mode: str = 'BASELINE'
    daytime_factor: float = 1.0
    other_factor: float = 1.0

    def __post_init__(self):
        if self.mode not in {'BASELINE', 'EXPERIMENT_A', 'TIME_OF_DAY'}:
            raise ValueError('Unknown time pricing policy mode')
        for value in (self.daytime_factor, self.other_factor):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('Time pricing factors must be finite positive numbers')
        if self.mode != 'TIME_OF_DAY' and (self.daytime_factor != 1 or self.other_factor != 1):
            raise ValueError('BASELINE and EXPERIMENT_A require unit factors')

    @classmethod
    def from_config(cls, config: Mapping):
        if set(config) - {'mode', 'daytime_factor', 'other_factor'}:
            raise ValueError('Unknown time pricing policy configuration key')
        return cls(**config)

    def apply(self, existing_factor: float, hour: int) -> float:
        """Multiply the existing selected factor; never derive a factor from SD."""
        if isinstance(hour, bool) or not isinstance(hour, int) or not 0 <= hour <= 23:
            raise ValueError('hour must be an integer from 0 through 23')
        if not math.isfinite(existing_factor) or existing_factor <= 0:
            raise ValueError('existing factor must be finite and positive')
        factor = self.daytime_factor if 8 <= hour <= 19 else self.other_factor
        return existing_factor * factor

    def require_runtime_support(self):
        """Fail before any simulator mutation, including for the experimental control."""
        if self.mode != 'BASELINE':
            raise RuntimeError(BLOCKER)
