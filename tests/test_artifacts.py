"""Persistence/reload validation for the authoritative grid artifact contract."""

import tempfile
import unittest

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from src.spatial.artifacts import load_grid_artifacts, save_grid_artifacts, validate_grid_artifacts
from src.spatial.mapping import build_neighbor_map


class ArtifactTests(unittest.TestCase):
    def test_artifacts_reload_with_consistent_mask_mapping_and_neighbours(self) -> None:
        grid = gpd.GeoDataFrame(
            {
                "GridID": [0, 1],
                "OriginalGridID": [10, 11],
                "Row": [0, 0],
                "Column": [0, 1],
                "ValidMask": [True, True],
                "CentroidX": [0.5, 1.5],
                "CentroidY": [0.5, 0.5],
            },
            geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
            crs="EPSG:2263",
        )
        mapping = pd.DataFrame({"LocationID": [1, 2], "GridID": [0, 1]})
        mask = np.array([[1, 1]], dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            save_grid_artifacts(directory, grid, mask, mapping, build_neighbor_map(grid), {"grid_size_meters": 3000})
            validation = validate_grid_artifacts(directory)
            reloaded = load_grid_artifacts(directory)
        self.assertEqual(validation["valid_cells"], 2)
        self.assertEqual(validation["neighbor_links"], 2)
        self.assertEqual(reloaded["grid"]["GridID"].tolist(), [0, 1])
        self.assertEqual(reloaded["zone_to_grids"], {1: [0], 2: [1]})
