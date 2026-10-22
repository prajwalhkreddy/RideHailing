import unittest
import math
import numpy as np
import pandas as pd
from src.routing.operational_interface import UtilityConfig,OperationalRouting,u1,u2,u3
from tests.test_operational_grid_state import fixture


def router():
    base='data/processed/spatial_3km_jan_mar_2026/'
    return OperationalRouting(pd.read_parquet(base+'neighbour_map.parquet'),pd.read_parquet(base+'charging_stations.parquet'),UtilityConfig(.01,.01,.01))


class RoutingTests(unittest.TestCase):
    def test_u1(self):
        self.assertAlmostEqual(u1(10,10,2,sigma_floor=.01),.5)
        self.assertAlmostEqual(u1(8,10,2,sigma_floor=.01),.8413447460685429)
        self.assertGreater(u1(10,12,2,sigma_floor=.01),u1(10,8,2,sigma_floor=.01))
        self.assertEqual(u1(10,10,0,sigma_floor=.01),.5)
        with self.assertRaises(ValueError):u1(10,10,0,sigma_floor=None)
    def test_u2(self):
        self.assertAlmostEqual(u2(.1,10),1-math.exp(-1))
        self.assertGreater(u2(.2,10),u2(.1,10));self.assertGreater(u2(.1,20),u2(.1,10))
        self.assertEqual(u2(0,10),0);self.assertLess(u2(1e300,1e300),1)
        with self.assertRaises(ValueError):u2(-1,1)
    def test_u3(self):
        self.assertAlmostEqual(u3(10,20,wait_floor_minutes=.01),1-math.exp(-.5))
        self.assertTrue(math.isfinite(u3(10,0,wait_floor_minutes=.01)))
        with self.assertRaises(ValueError):u3(10,0,wait_floor_minutes=None)
    def test_cost(self):
        c=router().config
        self.assertEqual(c.cost(0),0);self.assertAlmostEqual(c.cost(3000),.03)
        self.assertAlmostEqual(c.cost(3000*math.sqrt(2)),.03*math.sqrt(2))
    def test_mask_tie_and_formula(self):
        r=router();r.config=UtilityConfig(.01,.01,0);e=fixture()
        d=r.decide(e,e.timestamp,grid=0,energy_kwh=50,minimum_energy_kwh=10,p_min=10,w_max_minutes=1,h_max_minutes=1,energy_per_km=.15)
        self.assertEqual(d.action_index,0);self.assertAlmostEqual(d.score,.5+1-math.exp(-1));self.assertEqual(r.label(d,0),0)
        self.assertLess(len(r.candidates(0)),9)
    def test_charging_equality_next_hop(self):
        r=router();e=fixture();d=r.decide(e,e.timestamp,grid=0,energy_kwh=30,minimum_energy_kwh=30,p_min=10,w_max_minutes=1,h_max_minutes=1,energy_per_km=.15)
        self.assertEqual(d.branch,'CHARGING');self.assertIn(d.final_grid,set(r.stations.grid_id))
        self.assertEqual(r.candidates(0)[d.action_index][0],d.next_grid)
        self.assertLessEqual(d.distance_m,3000*math.sqrt(2));self.assertNotEqual(d.next_grid,d.final_grid)
        self.assertEqual(r.label(d,0),d.action_index)
    def test_unreachable_energy(self):
        r=router();e=fixture()
        with self.assertRaises(ValueError):r.decide(e,e.timestamp,grid=0,energy_kwh=0,minimum_energy_kwh=30,p_min=10,w_max_minutes=1,h_max_minutes=1,energy_per_km=.15)
    def test_navigation_is_timed_not_teleport(self):
        from types import SimpleNamespace
        from src.fleet.state import VehicleStatus
        r=router();e=fixture()
        d=r.decide(e,e.timestamp,grid=0,energy_kwh=30,minimum_energy_kwh=30,p_min=10,w_max_minutes=1,h_max_minutes=1,energy_per_km=.15)
        v=SimpleNamespace(current_grid=0,energy_level=30,trip_status=VehicleStatus.IDLE,abandon_idle_wait=lambda:None)
        minutes=r.start_next_hop(v,d,speed_kmph=15,energy_per_km=.15)
        self.assertEqual(v.current_grid,0);self.assertEqual(v.destination,d.next_grid)
        self.assertEqual(v.trip_status,VehicleStatus.BUSY)
        self.assertAlmostEqual(minutes,d.distance_m/1000/15*60)
        self.assertAlmostEqual(v.energy_level,30-d.distance_m/1000*.15)
    def test_state_order_and_timing(self):
        r=router();e=fixture();x,mask=r.encode(e,e.timestamp,0)
        self.assertEqual(x.shape,(169,));np.testing.assert_equal(x[:3],[10,2,1]);np.testing.assert_equal(x[27:],4)
        for a in range(9):np.testing.assert_equal(x[a*3:a*3+3],[10,2,1] if mask[a] else [0,0,0])
        with self.assertRaises(ValueError):r.encode(e,e.timestamp,0,expected_dimension=155)
        with self.assertRaises(ValueError):r.encode(e,e.timestamp+pd.Timedelta(minutes=30),0)
        with self.assertRaises(ValueError):r.encode(e,e.timestamp,1212)
    def test_network_mask_and_fedavg(self):
        from src.routing.learning import build_routing_policy_model,RoutingLearningParameters,masked_softmax,POLICY_ARCHITECTURE_VERSION
        from src.routing.baseline import ACTION_ORDER
        from src.routing.federated import aggregate_policy_updates
        m=build_routing_policy_model(RoutingLearningParameters(),seed=1)
        self.assertEqual(m.input_shape,(None,169));self.assertEqual(m.output_shape,(None,9))
        mask=np.array([True,False,True,False,False,False,False,False,False]);p=masked_softmax(np.arange(9),mask)
        self.assertEqual(p[~mask].sum(),0);self.assertAlmostEqual(float(p.sum()),1)
        weights=m.get_weights();updates=[]
        for ident,n,value in [(1,1,1),(2,3,3),(3,0,100)]:
            updates.append(dict(vehicle_id=ident,sample_count=n,weights=[np.full_like(w,value) for w in weights],state_dimension=169,action_order=[a.value for a in ACTION_ORDER],architecture_version=POLICY_ARCHITECTURE_VERSION))
        out=aggregate_policy_updates(updates,round_index=0);m.set_weights(out.weights)
        for w in m.get_weights():np.testing.assert_allclose(w,2.5)
        self.assertEqual(out.metadata.skipped_zero_sample_vehicle_ids,(3,))
        self.assertTrue(np.isfinite(m(np.zeros((1,169)),training=False)).all())

if __name__=='__main__':unittest.main()
