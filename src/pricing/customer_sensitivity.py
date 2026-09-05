"""Standalone proposed historical-sensitivity customer response model."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import truncnorm


@dataclass(frozen=True)
class SensitivityParameters:
    weather_code: float
    period: int
    p_base: float
    d_base: float
    epsilon_mean: float
    epsilon_std_population: float


@dataclass(frozen=True)
class HistoricalCustomerDecision:
    weather_code: float
    period: int
    p_base: float
    d_base: float
    actual_distance: float
    alpha: float
    epsilon_customer: float
    p_dispatch: float
    p_max: float
    accepted: bool
    sensitivity_lookup_level: str = "exact"


@dataclass(frozen=True)
class ResolvedSensitivityParameters:
    parameters: SensitivityParameters
    fallback_level_used: str
    requested_weather_code: float
    requested_period: int


def _finite_positive(value: float, name: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0:
        raise ValueError(f"{name} must be finite and strictly positive.")
    return numeric


def sample_positive_truncated_normal(
    mu: float, sigma: float, rng: np.random.Generator,
) -> float:
    """Draw one finite positive value from Normal(mu, sigma) conditioned on > 0."""
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng must be an explicit numpy.random.Generator.")
    mean, standard_deviation = float(mu), float(sigma)
    if not math.isfinite(mean) or mean < 0:
        raise ValueError("epsilon_mean must be finite and non-negative.")
    if not math.isfinite(standard_deviation) or standard_deviation < 0:
        raise ValueError("epsilon_std_population must be finite and non-negative.")
    if standard_deviation == 0:
        if mean <= 0:
            raise ValueError("A zero-variance sensitivity group requires epsilon_mean > 0.")
        return mean

    lower_standardized = -mean / standard_deviation
    sampled = float(truncnorm.rvs(
        lower_standardized, np.inf, loc=mean, scale=standard_deviation,
        random_state=rng,
    ))
    if not math.isfinite(sampled):
        raise ValueError("Truncated-Normal sampling produced a non-finite sensitivity.")
    if sampled <= 0:
        # Numerical guard only: the mathematical distribution is strictly above zero.
        sampled = float(np.nextafter(0.0, 1.0))
    return sampled


def dispatch_price(p_base: float, alpha: float) -> float:
    """Return the standalone offered price P_dispatch = P_base * alpha."""
    base = _finite_positive(p_base, "P_base")
    factor = _finite_positive(alpha, "alpha")
    offered = base * factor
    if not math.isfinite(offered):
        raise ValueError("P_dispatch is non-finite.")
    return float(offered)


def maximum_price(
    p_base: float, d_base: float, actual_distance: float, epsilon_customer: float,
) -> float:
    """Return P_max using the approved signed relative-distance formula."""
    base_price = _finite_positive(p_base, "P_base")
    base_distance = _finite_positive(d_base, "D_base")
    epsilon = _finite_positive(epsilon_customer, "epsilon_customer")
    distance = float(actual_distance)
    if not math.isfinite(distance) or distance < 0:
        raise ValueError("actual_distance must be finite and non-negative.")
    result = base_price + (((distance - base_distance) / base_distance) * base_price / epsilon)
    if not math.isfinite(result):
        raise ValueError("P_max is non-finite.")
    return float(result)


class HistoricalCustomerSensitivityModel:
    """Read-only W,T parameter lookup, sampling, and standalone acceptance."""

    REQUIRED_COLUMNS = (
        "WeatherCode", "Period", "P_base", "D_base",
        "epsilon_mean", "epsilon_std_population",
    )

    def __init__(
        self, groups: pd.DataFrame, rng: np.random.Generator,
        fallback_groups: pd.DataFrame | None = None, fallback_mode: str = "error",
    ) -> None:
        if not isinstance(rng, np.random.Generator):
            raise ValueError("rng must be an explicit numpy.random.Generator.")
        if missing := set(self.REQUIRED_COLUMNS) - set(groups.columns):
            raise ValueError(f"Sensitivity artifact lacks columns: {sorted(missing)}")
        parameters = groups[list(self.REQUIRED_COLUMNS)].copy(deep=True)
        if parameters.empty or parameters.duplicated(["WeatherCode", "Period"]).any():
            raise ValueError("Sensitivity groups must be non-empty and unique by WeatherCode, Period.")
        self._parameters: dict[tuple[float, int], SensitivityParameters] = {}
        for row in parameters.itertuples(index=False):
            weather = float(row.WeatherCode)
            period_value = float(row.Period)
            if not math.isfinite(weather) or not period_value.is_integer() or not 0 <= period_value <= 47:
                raise ValueError("Sensitivity artifact contains an invalid WeatherCode or Period.")
            p_base = _finite_positive(row.P_base, "P_base")
            d_base = _finite_positive(row.D_base, "D_base")
            mean, sigma = float(row.epsilon_mean), float(row.epsilon_std_population)
            if not math.isfinite(mean) or mean < 0 or not math.isfinite(sigma) or sigma < 0:
                raise ValueError("Sensitivity artifact contains invalid group parameters.")
            if sigma == 0 and mean <= 0:
                raise ValueError("A zero-variance sensitivity group requires epsilon_mean > 0.")
            period = int(period_value)
            self._parameters[(weather, period)] = SensitivityParameters(
                weather, period, p_base, d_base, mean, sigma,
            )
        self.rng = rng
        if fallback_mode not in {"error", "hierarchical"}:
            raise ValueError("sensitivity fallback mode must be error or hierarchical.")
        self.fallback_mode = fallback_mode
        self._period_parameters: dict[int, SensitivityParameters] = {}
        self._weather_parameters: dict[float, SensitivityParameters] = {}
        self._global_parameters: SensitivityParameters | None = None
        if fallback_groups is not None:
            required = {"fallback_level", "WeatherCode", "Period", "P_base", "D_base", "epsilon_mean", "epsilon_std_population"}
            if missing := required - set(fallback_groups.columns):
                raise ValueError(f"Fallback sensitivity artifact lacks columns: {sorted(missing)}")
            for row in fallback_groups.itertuples(index=False):
                level = str(row.fallback_level)
                weather = None if pd.isna(row.WeatherCode) else float(row.WeatherCode)
                period = None if pd.isna(row.Period) else int(row.Period)
                parameters = SensitivityParameters(
                    float("nan") if weather is None else weather,
                    -1 if period is None else period,
                    _finite_positive(row.P_base, "P_base"), _finite_positive(row.D_base, "D_base"),
                    float(row.epsilon_mean), float(row.epsilon_std_population),
                )
                if not math.isfinite(parameters.epsilon_mean) or parameters.epsilon_mean < 0 or not math.isfinite(parameters.epsilon_std_population) or parameters.epsilon_std_population < 0:
                    raise ValueError("Fallback sensitivity statistics must be finite and non-negative.")
                if level == "period" and weather is None and period is not None:
                    self._period_parameters[period] = parameters
                elif level == "weather" and weather is not None and period is None:
                    self._weather_parameters[weather] = parameters
                elif level == "global" and weather is None and period is None:
                    if self._global_parameters is not None:
                        raise ValueError("Fallback sensitivity artifact contains duplicate global rows.")
                    self._global_parameters = parameters
                else:
                    raise ValueError("Fallback sensitivity row keys do not match its level.")
        if fallback_mode == "hierarchical" and self._global_parameters is None:
            raise ValueError("Hierarchical sensitivity fallback requires a global fallback row.")

    @classmethod
    def from_parquet(
        cls, artifact_path: str | Path, rng: np.random.Generator,
        fallback_artifact_path: str | Path | None = None, fallback_mode: str = "error",
    ) -> "HistoricalCustomerSensitivityModel":
        fallback = None if fallback_artifact_path is None else pd.read_parquet(Path(fallback_artifact_path))
        return cls(pd.read_parquet(Path(artifact_path)), rng, fallback, fallback_mode)

    def resolve_parameters(self, weather_code: float, period: int) -> ResolvedSensitivityParameters:
        """Resolve one internally consistent parameter record by the fixed hierarchy."""
        weather = float(weather_code)
        if not math.isfinite(weather) or isinstance(period, bool) or not isinstance(period, (int, np.integer)):
            raise ValueError("WeatherCode must be finite and Period must be an integer in 0..47.")
        period_value = int(period)
        if not 0 <= period_value <= 47:
            raise ValueError("WeatherCode must be finite and Period must be an integer in 0..47.")
        exact = self._parameters.get((weather, period_value))
        if exact is not None:
            return ResolvedSensitivityParameters(exact, "exact", weather, period_value)
        if self.fallback_mode == "error":
            raise KeyError(f"No historical sensitivity group for WeatherCode={weather}, Period={period}.")
        if period_value in self._period_parameters:
            return ResolvedSensitivityParameters(self._period_parameters[period_value], "period", weather, period_value)
        if weather in self._weather_parameters:
            return ResolvedSensitivityParameters(self._weather_parameters[weather], "weather", weather, period_value)
        if self._global_parameters is None:
            raise KeyError(f"No hierarchical sensitivity fallback for WeatherCode={weather}, Period={period}.")
        return ResolvedSensitivityParameters(self._global_parameters, "global", weather, period_value)

    def parameters_for(self, weather_code: float, period: int) -> SensitivityParameters:
        return self.resolve_parameters(weather_code, period).parameters

    def sample_epsilon(self, weather_code: float, period: int) -> float:
        parameters = self.parameters_for(weather_code, period)
        return sample_positive_truncated_normal(
            parameters.epsilon_mean, parameters.epsilon_std_population, self.rng,
        )

    def evaluate(
        self, weather_code: float, period: int, actual_distance: float, alpha: float,
    ) -> HistoricalCustomerDecision:
        resolved = self.resolve_parameters(weather_code, period)
        return self.evaluate_resolved(resolved, actual_distance, alpha)

    def evaluate_resolved(
        self, resolved: ResolvedSensitivityParameters, actual_distance: float, alpha: float,
    ) -> HistoricalCustomerDecision:
        parameters = resolved.parameters
        epsilon = sample_positive_truncated_normal(
            parameters.epsilon_mean, parameters.epsilon_std_population, self.rng,
        )
        offered = dispatch_price(parameters.p_base, alpha)
        customer_maximum = maximum_price(
            parameters.p_base, parameters.d_base, actual_distance, epsilon,
        )
        return HistoricalCustomerDecision(
            resolved.requested_weather_code, resolved.requested_period, parameters.p_base,
            parameters.d_base, float(actual_distance), float(alpha), epsilon,
            offered, customer_maximum, offered <= customer_maximum,
            resolved.fallback_level_used,
        )
