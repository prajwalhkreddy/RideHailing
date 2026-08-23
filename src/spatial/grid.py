"""NB1-compatible authoritative square-grid construction."""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
from shapely.geometry import box


@dataclass(frozen=True)
class GridBuildResult:
    """Authoritative grid and its NB1 zone intersection mapping."""

    grid: gpd.GeoDataFrame
    zone_grid_mapping: gpd.GeoDataFrame
    generated_cell_count: int


def load_taxi_zones(path: str, metric_crs: str) -> gpd.GeoDataFrame:
    """Load, validate, and project the complete NYC taxi-zone shapefile.

    Legacy reference: NB1 reads ``taxi_zones.shp`` and transforms it to
    EPSG:2263 before deriving the regular-grid bounds. Invalid or missing
    geometries are rejected rather than repaired because NB1 only validates
    them and does not specify a repair rule.
    """
    zones = gpd.read_file(path)
    if "LocationID" not in zones.columns:
        raise ValueError(f"Taxi-zone source lacks LocationID: {path}")
    if zones.crs is None:
        raise ValueError(f"Taxi-zone source has no CRS: {path}")
    if zones.geometry.isna().any():
        raise ValueError("Taxi-zone source contains missing geometries.")
    if (~zones.geometry.is_valid).any():
        raise ValueError("Taxi-zone source contains invalid geometries.")
    return zones.to_crs(metric_crs)


def build_grid(taxi_zones: gpd.GeoDataFrame, size_meters: int) -> GridBuildResult:
    """Build the exact NB1 regular grid and zone-intersection representation.

    NB1 methodology: derive bounds from projected taxi zones; make full square
    cells with ``np.arange``; retain every cell with any intersection (the
    notebook's overlap threshold is commented out); deduplicate GridID/
    LocationID pairs; then assign sequential GridIDs North-to-South and
    West-to-East. ``size_meters`` is parameterized but defaults to 3000.
    """
    if size_meters <= 0:
        raise ValueError("Grid size must be positive.")
    if taxi_zones.crs is None:
        raise ValueError("Taxi zones must have a projected CRS before grid construction.")

    xmin, ymin, xmax, ymax = taxi_zones.total_bounds
    x_coords = np.arange(xmin, xmax + size_meters, size_meters)
    y_coords = np.arange(ymin, ymax + size_meters, size_meters)
    cells = [
        box(x, y, x + size_meters, y + size_meters)
        for x in x_coords[:-1]
        for y in y_coords[:-1]
    ]
    generated = gpd.GeoDataFrame({"GridID": np.arange(len(cells))}, geometry=cells, crs=taxi_zones.crs)
    overlay = gpd.overlay(
        generated[["GridID", "geometry"]],
        taxi_zones[["LocationID", "geometry"]],
        how="intersection",
    )
    if overlay.empty:
        raise ValueError("Grid construction produced no taxi-zone intersections.")
    overlay = overlay.drop_duplicates(subset=["GridID", "LocationID"]).copy()

    valid = generated.loc[generated["GridID"].isin(overlay["GridID"].unique())].copy()
    centroids = valid.geometry.centroid
    valid["_centroid_x"] = centroids.x
    valid["_centroid_y"] = centroids.y
    valid = valid.sort_values(["_centroid_y", "_centroid_x"], ascending=[False, True]).reset_index(drop=True)
    valid["OriginalGridID"] = valid["GridID"].astype(np.int32)
    valid["GridID"] = np.arange(len(valid), dtype=np.int32)
    legacy_to_final = dict(zip(valid["OriginalGridID"], valid["GridID"], strict=True))
    overlay["GridID"] = overlay["GridID"].map(legacy_to_final).astype(np.int32)

    centroids = valid.geometry.centroid
    valid["CentroidX"] = centroids.x
    valid["CentroidY"] = centroids.y
    x_lookup = {x: index for index, x in enumerate(np.sort(valid["CentroidX"].unique()))}
    y_lookup = {y: index for index, y in enumerate(np.sort(valid["CentroidY"].unique())[::-1])}
    valid["Row"] = valid["CentroidY"].map(y_lookup).astype(np.int16)
    valid["Column"] = valid["CentroidX"].map(x_lookup).astype(np.int16)
    valid["ValidMask"] = True
    valid = valid[["GridID", "OriginalGridID", "Row", "Column", "ValidMask", "CentroidX", "CentroidY", "geometry"]]
    mapping = overlay[["LocationID", "GridID", "geometry"]].sort_values(["LocationID", "GridID"]).reset_index(drop=True)
    validate_grid(valid)
    return GridBuildResult(valid, mapping, len(generated))


def validate_grid(grid: gpd.GeoDataFrame) -> None:
    """Validate the persisted grid's geometry and stable spatial indexing."""
    required = {"GridID", "Row", "Column", "ValidMask", "CentroidX", "CentroidY", "geometry"}
    missing = required - set(grid.columns)
    if missing:
        raise ValueError(f"Grid lacks required columns: {sorted(missing)}")
    if grid.crs is None or grid.crs.to_string() != "EPSG:2263":
        raise ValueError(f"Grid CRS must be EPSG:2263, got {grid.crs}")
    if grid.empty or not grid["GridID"].is_unique:
        raise ValueError("GridIDs must be non-empty and unique.")
    expected = np.arange(len(grid))
    if not np.array_equal(np.sort(grid["GridID"].to_numpy()), expected):
        raise ValueError("GridIDs must be sequential from zero.")
    if grid.geometry.isna().any() or (~grid.geometry.is_valid).any():
        raise ValueError("Grid contains missing or invalid geometries.")
    if grid[["Row", "Column"]].duplicated().any():
        raise ValueError("Grid has duplicate Row/Column positions.")
    if not grid["ValidMask"].all():
        raise ValueError("Authoritative grid may contain only valid cells.")
