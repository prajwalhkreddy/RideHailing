"""Synthetic, deterministic tests for NB1-compatible grid construction."""

import geopandas as gpd
from shapely.geometry import box
import unittest

from src.spatial.grid import build_grid, validate_grid


def synthetic_zones() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        {"LocationID": [1, 2]},
        geometry=[box(0, 0, 100, 100), box(100, 0, 200, 100)],
        crs="EPSG:2263",
    )


class GridTests(unittest.TestCase):
    def test_grid_ids_follow_north_then_west_ordering(self) -> None:
        result = build_grid(synthetic_zones(), 100)
        grid = result.grid.sort_values("GridID")
        self.assertEqual(result.generated_cell_count, 2)
        self.assertEqual(grid["GridID"].tolist(), [0, 1])
        self.assertEqual(grid["Row"].tolist(), [0, 0])
        self.assertEqual(grid["Column"].tolist(), [0, 1])
        self.assertEqual(result.zone_grid_mapping[["LocationID", "GridID"]].values.tolist(), [[1, 0], [2, 1]])
        validate_grid(grid)

    def test_grid_size_is_parameterized(self) -> None:
        result = build_grid(synthetic_zones(), 200)
        self.assertEqual(result.generated_cell_count, 1)
        self.assertEqual(len(result.grid), 1)
