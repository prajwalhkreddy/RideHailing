"""Leakage-safe destination-popularity processing."""

from src.popularity.destination import (
    POPULARITY_ENCODING, POPULARITY_LEVELS, PopularityThresholds,
    aggregate_dropoffs, apply_popularity_levels, build_destination_popularity,
    fit_popularity_thresholds, trailing_dropoff_average,
)

__all__ = [
    "POPULARITY_ENCODING", "POPULARITY_LEVELS", "PopularityThresholds",
    "aggregate_dropoffs", "apply_popularity_levels", "build_destination_popularity",
    "fit_popularity_thresholds", "trailing_dropoff_average",
]
