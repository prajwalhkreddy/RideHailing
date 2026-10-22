"""Charging-wait profile validation without calibration or model execution."""
import math,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
import numpy as np
import pandas as pd
from src.simulation.final_production import validate_driver_profiles,ProductionExperiment
from src.routing.operational_interface import u3
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus

class HimaxTests(unittest.TestCase):
    def profile(self,h=2.):
        return pd.DataFrame(dict(vehicle_id=[0],price_preference=[5.],wait_preference=[8.],charging_wait_preference_minutes=[h]))
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'PROJECT_CONFIG_DECISION_REQUIRED'):
            validate_driver_profiles(self.profile().drop(columns='charging_wait_preference_minutes'),[0])
    def test_invalid(self):
        for h in [None,np.nan,np.inf,-np.inf,0.,-1.]:
            with self.subTest(h=h),self.assertRaises((ValueError,TypeError)):validate_driver_profiles(self.profile(h),[0])
    def test_coverage(self):
        with self.assertRaises(ValueError):validate_driver_profiles(self.profile(),[1])
    def test_serialization(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test_only.parquet';self.profile().to_parquet(p,index=False)
            pd.testing.assert_frame_equal(validate_driver_profiles(pd.read_parquet(p),[0]),self.profile())
    def test_u3_hand_values(self):
        self.assertAlmostEqual(u3(2.,10.,wait_floor_minutes=1e-6),0.18126924692201818)
        self.assertAlmostEqual(u3(20.,10.,wait_floor_minutes=1e-6),0.8646647167633873)
        self.assertGreater(u3(20.,10.,wait_floor_minutes=1e-6),u3(2.,10.,wait_floor_minutes=1e-6))
        self.assertEqual(u3(2.,0.,wait_floor_minutes=1e-6),1.)
    def test_profile_value_forwarded(self):
        x=ProductionExperiment.__new__(ProductionExperiment)
        x.fleet=Fleet([VehicleState(0,0,VehicleStatus.IDLE,None,0,'idle',15.)],frozenset(range(142)),2)
        x.profiles=validate_driver_profiles(self.profile(7.),[0]).set_index('vehicle_id')
        x.timestamp=pd.Timestamp('2026-03-16');x.operational=object();x.slot_index=0
        x.charging=SimpleNamespace(vehicle_station={});x.energy=SimpleNamespace(battery_capacity_kwh=75.,charging_trigger_soc=.2,consumption_rate_kwh_per_km=.15)
        decision=SimpleNamespace(branch='CHARGING',station_id=0)
        x.routing=Mock();x.routing.decide.return_value=decision;x.routing.label.return_value=0
        x.routing_experiences=[];x.routing_experiences_by_vehicle={};x.missions={};x._continue_charging=Mock()
        state=SimpleNamespace(values=np.zeros(169),mask=np.ones(9,dtype=bool))
        with patch('src.simulation.final_production.RoutingState.from_producer',return_value=state):x.route_idle()
        self.assertEqual(x.routing.decide.call_args.kwargs['h_max_minutes'],7.)
        self.assertNotEqual(x.routing.decide.call_args.kwargs['h_max_minutes'],8.)

if __name__=='__main__':unittest.main()
