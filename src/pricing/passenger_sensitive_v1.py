"""Global-reference passenger feasibility and explicit positive calibration provider."""
from dataclasses import dataclass
import numpy as np
import pandas as pd

P_BASE_USD = 21.34586956773507
L_BASE_KM = 4.856998243316242
ACTIONS = (.85, .90, .95, 1., 1.05, 1.10, 1.15)
CANDIDATE_PRICES = np.array(ACTIONS) * P_BASE_USD
P_PLATFORM_MIN = float(CANDIDATE_PRICES[0])
P_PLATFORM_MAX = float(CANDIDATE_PRICES[-1])

def guard_date(value, *, calibration=False):
    t = pd.Timestamp(value)
    end = pd.Timestamp('2026-03-16' if calibration else '2026-03-17')
    if t.tz is not None or not pd.Timestamp('2026-01-01') <= t < end:
        raise ValueError('V1 protected-date boundary: calibration through March15; development March16 only.')
    return t

def maximum_price(distance_km, epsilon):
    if not np.isfinite([distance_km, epsilon]).all() or distance_km < 0 or epsilon <= 0:
        raise ValueError('Finite nonnegative km distance and positive epsilon required.')
    pc = P_BASE_USD + (P_BASE_USD / epsilon) * ((distance_km - L_BASE_KM) / L_BASE_KM)
    if not np.isfinite(pc):
        raise ValueError('Nonfinite passenger maximum price.')
    return float(pc)

def effective_threshold(raw_preference):
    """Project-defined threshold; not an action-price clipping operation."""
    if not np.isfinite(raw_preference):
        raise ValueError("Finite raw passenger preference required.")
    return max(P_PLATFORM_MIN, float(raw_preference))

def feasible_mask(pc):
    if not np.isfinite(pc):
        raise ValueError('Finite passenger maximum required.')
    return CANDIDATE_PRICES <= pc

@dataclass(frozen=True)
class EpsilonDraw:
    raw: float
    value: float
    minimum: float

class PositiveEpsilonProvider:
    """Empirical row resampling, with a required explicit floor; no runtime abs()."""
    def __init__(self, values, epsilon_min, *, rng, provenance, frozen=False):
        self.values = np.asarray(values, dtype=np.float64)
        if self.values.ndim != 1 or not len(self.values) or not np.isfinite(self.values).all() or (self.values <= 0).any():
            raise ValueError('Nonempty finite positive empirical support required.')
        if epsilon_min is None or isinstance(epsilon_min, bool) or not np.isfinite(epsilon_min) or epsilon_min <= 0:
            raise ValueError('Explicit calibrated positive epsilon_min required; no fallback.')
        if not isinstance(rng, np.random.Generator) or not isinstance(provenance, dict) or not provenance:
            raise ValueError('Caller-owned RNG and calibration provenance required.')
        guard_date(provenance['calibration_start'], calibration=True)
        guard_date(provenance['calibration_last_timestamp'], calibration=True)
        if provenance.get("sampling_family") == "TRUNCATED_EMPIRICAL_RESAMPLING":
            lo, hi = provenance["positive_support_lower"], provenance["positive_support_upper"]
            if not np.isfinite([lo, hi]).all() or not 0 < lo <= hi or epsilon_min != lo:
                raise ValueError("Approved truncated support lower bound required; no additional floor.")
            if (self.values < lo).any() or (self.values > hi).any():
                raise ValueError("Values outside approved positive support.")
        self.epsilon_min = float(epsilon_min)
        self.rng = rng
        self.provenance = dict(provenance)
        self.frozen = bool(frozen)

    def sample(self):
        raw = float(self.values[self.rng.integers(len(self.values))])
        value = max(raw, self.epsilon_min)
        if not np.isfinite(value) or value < self.epsilon_min:
            raise ValueError('Invalid positive epsilon draw.')
        return EpsilonDraw(raw, value, self.epsilon_min)

    def require_training_ready(self):
        if (not self.frozen or self.provenance.get('epsilon_min_status') != 'FROZEN'
            or self.provenance.get('epsilon_min') != self.epsilon_min):
            raise ValueError('epsilon_min unresolved: long/final V1 training is blocked.')
