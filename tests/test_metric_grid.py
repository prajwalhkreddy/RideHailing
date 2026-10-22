"""Candidate metric-grid tests; no active artifacts are written."""
import unittest
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box
from src.spatial.metric_grid import build_metric_grid,validate_metric_grid,build_metric_neighbors,topology_summary

class MetricGridTests(unittest.TestCase):
    def zones(self):
        return gpd.GeoDataFrame({'LocationID':[1]},geometry=[box(300000,50000,309000,59000)],crs='EPSG:32118')
    def test_dimensions_and_area(self):
        g=build_metric_grid(self.zones()).grid
        self.assertEqual(len(g),9)
        self.assertTrue(np.allclose(g.area,9e6))
        self.assertEqual(validate_metric_grid(g)['width_min_m'],3000)
    def test_deterministic_ids(self):
        z=self.zones();z2=z.copy();z2.LocationID=2;z2.geometry=z2.geometry.translate(xoff=12000)
        both=pd.concat([z,z2]);a=build_metric_grid(both);b=build_metric_grid(both.iloc[::-1])
        self.assertEqual(a.grid.geometry.to_wkb().tolist(),b.grid.geometry.to_wkb().tolist())
        pd.testing.assert_frame_equal(a.raster,b.raster)
    def test_raster_reversible_and_holes(self):
        z=self.zones();z2=z.copy();z2.LocationID=2;z2.geometry=z2.geometry.translate(xoff=15000)
        result=build_metric_grid(pd.concat([z,z2]));r=result.raster
        self.assertTrue(r.loc[~r.ValidMask,'GridID'].isna().all());self.assertGreater((~r.ValidMask).sum(),0)
        self.assertFalse(r[['Row','Column']].duplicated().any())
        self.assertEqual(set(r.GridID.dropna()),set(result.grid.GridID))
    def test_cardinal_neighbors(self):
        g=build_metric_grid(self.zones()).grid;n=build_metric_neighbors(g,'cardinal')
        self.assertEqual(len(n),24);self.assertTrue(np.allclose(n.DistanceMeters,3000))
        self.assertEqual(set(n[n.GridID==4].NeighbourGridID),{1,3,5,7})
    def test_diagonal_neighbors(self):
        g=build_metric_grid(self.zones()).grid;n=build_metric_neighbors(g,'8way')
        self.assertEqual(len(n),40);self.assertEqual(len(n[n.GridID==4]),8)
        self.assertTrue(np.allclose(n[n.Direction.isin(['NE','SE','SW','NW'])].DistanceMeters,3000*np.sqrt(2)))
    def test_boundary_masks(self):
        g=build_metric_grid(self.zones()).grid
        for top,degree in [('cardinal',2),('8way',3)]:
            n=build_metric_neighbors(g,top);self.assertEqual(len(n[n.GridID==0]),degree)
            self.assertEqual(topology_summary(g,n,top)['boundary_grids'],8)
            self.assertNotIn('N',set(n[n.GridID==0].Direction))
    def test_reject_wrong_geometry(self):
        g=build_metric_grid(self.zones()).grid;g.geometry=g.geometry.scale(.3048,.3048,origin='center')
        with self.assertRaises(ValueError):validate_metric_grid(g)
    def test_feet_input_converted_not_relabelled(self):
        a=build_metric_grid(self.zones());b=build_metric_grid(self.zones().to_crs('EPSG:2263'))
        self.assertEqual(len(a.grid),len(b.grid));self.assertEqual(validate_metric_grid(b.grid)['width_min_m'],3000)
    def test_reject_feet_construction_crs(self):
        with self.assertRaises(ValueError):build_metric_grid(self.zones(),construction_crs='EPSG:2263')
    def test_isolated_cell(self):
        z=self.zones();z.geometry=[box(300000,50000,301000,51000)]
        g=build_metric_grid(z).grid;n=build_metric_neighbors(g,'8way')
        self.assertEqual(topology_summary(g,n,'8way')['isolated_grids'],[0])
