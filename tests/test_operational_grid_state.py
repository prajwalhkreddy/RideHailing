import unittest
from types import SimpleNamespace as NS
import geopandas as gpd
import numpy as np
import pandas as pd
from src.simulation.operational_state import OperationalGridState, SmoothingParameters, charging_grid_observations
from src.dispatch.request import RequestStatus


def fixture():
    grid = gpd.read_parquet('data/processed/grid_lookup.parquet')
    priors = pd.DataFrame(dict(Grid_ID=range(142),mu=10.,sigma=2.,F_hat=1.,H_hat=4.))
    return OperationalGridState(grid, priors, first_timestamp='2026-02-01',
        prior_as_of='2026-01-31', parameters=SmoothingParameters(.3,.3,.5,.25,.01))


def request(price, status=RequestStatus.ASSIGNED, grid=0):
    return NS(origin_grid=grid, offered_fare=price, status=status, assigned_vehicle_id=1)


class OperationalTests(unittest.TestCase):
    def test_recurrences_and_population(self):
        e=fixture()
        r=e.complete_slot(slot_start=e.timestamp,completed_at=e.timestamp+pd.Timedelta(minutes=30),
            requests=[request(10),request(20),request(999,RequestStatus.PENDING),request(999,RequestStatus.UNSERVED)],charging_waits={0:8})
        a=r.iloc[0]
        self.assertEqual(a.successful_dispatch_count,2)
        self.assertAlmostEqual(a.mu,11.5);self.assertAlmostEqual(a.sigma,2.9)
        self.assertAlmostEqual(a.F_hat,.5+1/30);self.assertAlmostEqual(a.H_hat,5)
        self.assertEqual(len(r),142)
    def test_empty(self):
        e=fixture(); r=e.complete_slot(slot_start=e.timestamp,completed_at=e.timestamp+pd.Timedelta(minutes=30))
        self.assertTrue(np.isfinite(r[['mu','sigma','F_hat','H_hat']]).all().all())
        self.assertEqual(r.iloc[0].mu,10);self.assertEqual(r.iloc[0].sigma,2)
        self.assertEqual(r.iloc[0].F_hat,.5);self.assertEqual(r.iloc[0].H_hat,4)
    def test_timing(self):
        e=fixture();before=e.state_for(e.timestamp)
        with self.assertRaises(ValueError):e.state_for(e.timestamp+pd.Timedelta(minutes=30))
        with self.assertRaises(ValueError):e.complete_slot(slot_start=e.timestamp,completed_at=e.timestamp)
        pd.testing.assert_frame_equal(before,e.state_for(e.timestamp))
        t=e.timestamp;e.complete_slot(slot_start=t,completed_at=t+pd.Timedelta(minutes=30))
        with self.assertRaises(ValueError):e.complete_slot(slot_start=t,completed_at=t+pd.Timedelta(minutes=30))
    def test_bad_grid_and_atomicity(self):
        e=fixture();before=e.state_for(e.timestamp)
        with self.assertRaises(ValueError):e.complete_slot(slot_start=e.timestamp,completed_at=e.timestamp+pd.Timedelta(minutes=30),requests=[request(1,grid=1212)])
        pd.testing.assert_frame_equal(before,e.state_for(e.timestamp))
    def test_colocated_stations(self):
        x=NS(stations={1:NS(grid_id=0,queue=[NS(wait_minutes=2)]),2:NS(grid_id=0,queue=[NS(wait_minutes=8),NS(wait_minutes=8)]),3:NS(grid_id=1,queue=[])})
        self.assertEqual(charging_grid_observations(x),{0:6.,1:0.})
    def test_explicit_config(self):
        with self.assertRaises(ValueError):SmoothingParameters(.3,.3,None,.25,.01)
    def test_floor_does_not_change_sigma(self):
        e=fixture();e._state['sigma']=0
        r=e.state_for(e.timestamp)
        self.assertTrue((r.sigma==0).all());self.assertTrue((r.sigma_for_denominator==.01).all())
    def test_no_future_prior_and_legacy_domain(self):
        g=gpd.read_parquet('data/processed/grid_lookup.parquet')
        p=pd.DataFrame(dict(Grid_ID=range(142),mu=10.,sigma=2.,F_hat=1.,H_hat=4.))
        kw=dict(first_timestamp='2026-02-01',prior_as_of='2026-02-02',parameters=SmoothingParameters(.3,.3,.5,.25,.01))
        with self.assertRaises(ValueError):OperationalGridState(g,p,**kw)
        g.loc[0,'GridID']=1212;kw['prior_as_of']='2026-01-01'
        with self.assertRaises(ValueError):OperationalGridState(g,p,**kw)

if __name__=='__main__':unittest.main()
