"""Trip-to-grid mappings and square-grid neighbor construction."""

from __future__ import annotations

from collections.abc import Mapping

import geopandas as gpd
import numpy as np
import pandas as pd


def build_zone_to_grids(zone_grid_mapping: pd.DataFrame) -> dict[int, list[int]]:
    """Build the NB1 ``LocationID -> [GridID]`` lookup in deterministic order."""
    required = {"LocationID", "GridID"}
    if missing := required - set(zone_grid_mapping.columns):
        raise ValueError(f"Zone-grid mapping lacks columns: {sorted(missing)}")
    clean = zone_grid_mapping[["LocationID", "GridID"]].drop_duplicates().sort_values(["LocationID", "GridID"])
    return {
        int(zone): [int(grid) for grid in grids]
        for zone, grids in clean.groupby("LocationID", sort=True)["GridID"]
    }


def assign_grid_ids_by_zone_legacy(
    trips: pd.DataFrame,
    zone_column: str,
    output_column: str,
    zone_to_grids: Mapping[int, list[int]],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Apply NB2's seeded random zone-to-grid assignment exactly by group.

    The 2026 Yellow Taxi release has LocationIDs but no longitude/latitude.
    NB2 therefore samples one intersecting GridID per trip within each taxi
    zone, using an RNG seeded with ``random_seed + month``. This is a legacy
    compatibility representation, not a coordinate-derived assignment.
    """
    if zone_column not in trips.columns:
        raise ValueError(f"Trips lack zone column {zone_column!r}.")
    values = np.empty(len(trips), dtype=np.int32)
    for zone_id, indices in trips.groupby(zone_column, sort=True).groups.items():
        grids = zone_to_grids.get(int(zone_id))
        if not grids:
            raise ValueError(f"No grid mapping for {zone_column}={zone_id}.")
        values[np.asarray(indices)] = rng.choice(grids, size=len(indices))
    result = trips.copy()
    result[output_column] = values
    return result


def assign_points_to_grid(
    points: pd.DataFrame,
    longitude_column: str,
    latitude_column: str,
    grid: gpd.GeoDataFrame,
) -> pd.Series:
    """Map WGS84 points to GridIDs, leaving invalid/outside points unmapped.

    This function supports future coordinate-bearing sources and test fixtures.
    It intentionally does not substitute a nearest grid: an invalid or outside
    point remains nullable so the caller can report and handle it explicitly.
    """
    for column in (longitude_column, latitude_column):
        if column not in points.columns:
            raise ValueError(f"Point data lack coordinate column {column!r}.")
    longitude = pd.to_numeric(points[longitude_column], errors="coerce")
    latitude = pd.to_numeric(points[latitude_column], errors="coerce")
    valid = longitude.between(-180, 180) & latitude.between(-90, 90)
    output = pd.Series(pd.NA, index=points.index, dtype="Int32")
    if not valid.any():
        return output
    spatial_points = gpd.GeoDataFrame(
        {"_source_index": points.index[valid]},
        geometry=gpd.points_from_xy(longitude[valid], latitude[valid]),
        crs="EPSG:4326",
    ).to_crs(grid.crs)
    joined = gpd.sjoin(spatial_points, grid[["GridID", "geometry"]], how="left", predicate="within")
    if joined["_source_index"].duplicated().any():
        raise ValueError("A point matched more than one grid cell.")
    output.loc[joined["_source_index"]] = joined["GridID"].astype("Int32").to_numpy()
    return output


def build_neighbor_map(grid: gpd.GeoDataFrame) -> pd.DataFrame:
    """Create deterministic four-direction neighbors for the square grid.

    Legacy notebooks do not define a neighbor artifact. The first milestone
    therefore records the minimal geometric convention needed downstream:
    valid cells sharing a full grid edge are neighbors; diagonal touching is
    excluded. Ordering is North, East, South, West for reproducibility.
    """
    by_position = {
        (int(row.Row), int(row.Column)): int(row.GridID)
        for row in grid[["GridID", "Row", "Column"]].itertuples(index=False)
    }
    directions = (("north", -1, 0), ("east", 0, 1), ("south", 1, 0), ("west", 0, -1))
    rows: list[dict[str, int | str]] = []
    for item in grid.sort_values("GridID")[["GridID", "Row", "Column"]].itertuples(index=False):
        for direction, row_delta, column_delta in directions:
            neighbor = by_position.get((int(item.Row) + row_delta, int(item.Column) + column_delta))
            if neighbor is not None:
                rows.append({"GridID": int(item.GridID), "NeighbourGridID": neighbor, "Direction": direction})
    neighbor_map = pd.DataFrame(rows, columns=["GridID", "NeighbourGridID", "Direction"])
    validate_neighbor_map(neighbor_map, set(grid["GridID"].astype(int)))
    return neighbor_map


def validate_neighbor_map(neighbor_map: pd.DataFrame, valid_grid_ids: set[int]) -> None:
    """Verify grid-neighbor references, no self-links, and deterministic uniqueness."""
    expected = {"GridID", "NeighbourGridID", "Direction"}
    if missing := expected - set(neighbor_map.columns):
        raise ValueError(f"Neighbour map lacks columns: {sorted(missing)}")
    if not set(neighbor_map["GridID"]).issubset(valid_grid_ids):
        raise ValueError("Neighbour map contains an invalid source GridID.")
    if not set(neighbor_map["NeighbourGridID"]).issubset(valid_grid_ids):
        raise ValueError("Neighbour map contains an invalid neighbour GridID.")
    if (neighbor_map["GridID"] == neighbor_map["NeighbourGridID"]).any():
        raise ValueError("Neighbour map contains self-neighbours.")
    if neighbor_map[["GridID", "NeighbourGridID"]].duplicated().any():
        raise ValueError("Neighbour map contains duplicate links.")
