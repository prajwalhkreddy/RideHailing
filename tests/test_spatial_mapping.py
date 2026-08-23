"""Tests for persisted-compatible mappings, invalid points, and neighbors."""

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box
import unittest

from src.spatial.mapping import (
    assign_grid_ids_by_zone_legacy,
    assign_points_to_grid,
    build_neighbor_map,
)


class SpatialMappingTests(unittest.TestCase):
    def test_legacy_zone_assignment_is_seeded_and_valid(self) -> None:
        trips = pd.DataFrame({"PULocationID": [1, 1, 2, 1]})
        lookup = {1: [0, 1], 2: [2]}
        first = assign_grid_ids_by_zone_legacy(trips, "PULocationID", "PUGridID", lookup, np.random.default_rng(43))
        second = assign_grid_ids_by_zone_legacy(trips, "PULocationID", "PUGridID", lookup, np.random.default_rng(43))
        self.assertEqual(first["PUGridID"].tolist(), second["PUGridID"].tolist())
        self.assertTrue(set(first["PUGridID"]).issubset({0, 1, 2}))

    def test_points_outside_or_invalid_are_not_silently_assigned(self) -> None:
        grid = gpd.GeoDataFrame({"GridID": [0]}, geometry=[box(-1000, -1000, 1000, 1000)], crs="EPSG:3857")
        points = pd.DataFrame({"lon": [0.0, 200.0, None], "lat": [0.0, 95.0, 0.0]})
        assigned = assign_points_to_grid(points, "lon", "lat", grid)
        self.assertEqual(assigned.iloc[0], 0)
        self.assertTrue(pd.isna(assigned.iloc[1]))
        self.assertTrue(pd.isna(assigned.iloc[2]))

    def test_neighbor_map_excludes_diagonals_and_self_links(self) -> None:
        grid = gpd.GeoDataFrame(
            {"GridID": [0, 1, 2], "Row": [0, 0, 1], "Column": [0, 1, 0]},
            geometry=[box(0, 1, 1, 2), box(1, 1, 2, 2), box(0, 0, 1, 1)],
            crs="EPSG:2263",
        )
        neighbors = build_neighbor_map(grid)
        self.assertEqual(
            set(map(tuple, neighbors[["GridID", "NeighbourGridID"]].to_numpy())),
            {(0, 1), (0, 2), (1, 0), (2, 0)},
        )
