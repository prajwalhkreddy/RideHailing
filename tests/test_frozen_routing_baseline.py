import unittest
import numpy as np,pandas as pd,geopandas as gpd
from src.routing.configuration import configured_interfaces
class FrozenBaselineTests(unittest.TestCase):
    def test_cost_and_initialization_wiring(self):
        b='data/processed/spatial_3km_jan_mar_2026/'
        p,r=configured_interfaces(gpd.read_parquet('data/processed/grid_lookup.parquet'),pd.read_parquet(b+'neighbour_map.parquet'),pd.read_parquet(b+'charging_stations.parquet'),'2026-02-01')
        self.assertEqual(p.parameters.alpha,.3);self.assertEqual(p.parameters.beta,.3)
        self.assertEqual(p.parameters.delta,.3);self.assertEqual(p.parameters.kappa,.3)
        self.assertTrue((p.state_for(p.timestamp)[['F_hat','H_hat']]==0).all().all())
        self.assertEqual(r.config.cost(0),0)
        self.assertAlmostEqual(r.config.cost(3000*np.sqrt(2)),.25)
        self.assertAlmostEqual(r.config.cost(3000),.25/np.sqrt(2))
        from tests.test_operational_grid_state import request
        t=p.timestamp;s=p.complete_slot(slot_start=t,completed_at=t+pd.Timedelta(minutes=30),requests=[request(10),request(20)],charging_waits={0:10})
        self.assertAlmostEqual(s.iloc[0].F_hat,.3*2/30);self.assertAlmostEqual(s.iloc[0].H_hat,3)
if __name__=='__main__':unittest.main()
