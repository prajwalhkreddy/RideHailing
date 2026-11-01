"""Small FCFS price-gate fixtures; no simulator period or model execution."""
import ast
import unittest
from pathlib import Path
import pandas as pd
import yaml
from src.dispatch.dispatch import dispatch_requests
from src.dispatch.request import RequestState, RequestStatus
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.charging.energy import EnergyParameters

ROOT=Path(__file__).resolve().parents[1]
class DriverPriceGateTests(unittest.TestCase):
    def run_case(self, fare, minima, reserve=0., origin=0, destination=1):
        energy=EnergyParameters(**yaml.safe_load((ROOT/'config/config.yaml').read_text())['energy'])
        fleet=Fleet([VehicleState(i,origin,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(len(minima))],frozenset(range(142)),2)
        r=RequestState(0,0,origin,destination,offered_fare=float(fare),base_fare=float(fare),source_trip_id=0,empirical_pickup_datetime=pd.Timestamp("2026-03-16"),empirical_dropoff_datetime=pd.Timestamp("2026-03-16 00:10"),customer_accepted=True,pricing_factor=1.,customer_model="historical_sensitivity",weather_code=1.,period=0,historical_p_base=float(fare),historical_d_base=1.,epsilon_customer=1.,p_max=float(fare),trip_distance_miles=1.,trip_distance_km=1.609344,trip_duration_minutes=10.)
        rejected=[]
        summary=dispatch_requests([r],fleet,{},2,15,energy_parameters=energy,station_reserve=lambda g:reserve,driver_minimum_prices=dict(enumerate(minima)),price_observer=lambda r,v:rejected.append(v.vehicle_id))
        self.assertEqual(len(fleet.vehicles),len(minima));self.assertTrue(r.customer_accepted)
        self.assertEqual(summary['requests_total'],summary['requests_served']+summary['requests_unserved'])
        for i in rejected:
            v=fleet.vehicle(i);self.assertEqual(v.energy_level,60.);self.assertIs(v.trip_status,VehicleStatus.IDLE);self.assertIsNone(v.destination)
        return r,fleet,rejected,summary
    def test_above(self):self.assertEqual(self.run_case(11,[10])[0].assigned_vehicle_id,0)
    def test_equality(self):self.assertEqual(self.run_case(10,[10])[0].assigned_vehicle_id,0)
    def test_below_no_energy_or_trip(self):
        r,f,c,s=self.run_case(9,[10]);self.assertIs(r.status,RequestStatus.UNSERVED);self.assertIsNone(r.assigned_vehicle_id);self.assertIsNone(r.passenger_energy_kwh);self.assertEqual(c,[0])
    def test_fcfs_fallback(self):self.assertEqual(self.run_case(10,[11,10,9])[0].assigned_vehicle_id,1)
    def test_all_ineligible_unmatched_not_passenger_rejected(self):
        r,f,c,s=self.run_case(9,[10,11]);self.assertTrue(r.customer_accepted);self.assertEqual(s['requests_unserved'],1);self.assertEqual(c,[0,1])
    def test_station_reachability_still_blocks_price_eligible(self):self.assertIs(self.run_case(20,[10],reserve=60)[0].status,RequestStatus.UNSERVED)
    def test_station_equality_allowed(self):self.assertIs(self.run_case(20,[10],reserve=60-1.609344*.15)[0].status,RequestStatus.ASSIGNED)
    def test_bad_profile_fails_closed(self):
        for minimum in [float('nan'),float('inf'),-1]:
            with self.subTest(minimum=minimum),self.assertRaises(ValueError):self.run_case(10,[minimum])
    def test_march16_saved_violations(self):
        f=pd.read_parquet(ROOT/'results/analysis/2026-10-26_professor_request_level_diagnostics/request_level_diagnostics.parquet')
        cases=f[f.assigned & (f.P_disp<f.assigned_driver_P_i_min)].head(5)
        self.assertEqual(len(cases),5)
        for z in cases.itertuples():
            with self.subTest(request_id=z.request_id):
                r,*_=self.run_case(z.P_disp,[z.assigned_driver_P_i_min],origin=int(z.origin_grid),destination=int(z.destination_grid));self.assertIs(r.status,RequestStatus.UNSERVED)
                r,*_=self.run_case(z.P_disp,[z.assigned_driver_P_i_min,z.P_disp],origin=int(z.origin_grid),destination=int(z.destination_grid));self.assertEqual(r.assigned_vehicle_id,1)
    def test_neighbor_fallback_preserves_spatial_priority(self):
        from src.dispatch.dispatch import find_eligible_vehicle
        fleet=Fleet([VehicleState(i,g,VehicleStatus.IDLE,None,0,'idle',60.) for i,g in [(0,0),(1,1),(2,2)]],frozenset(range(142)),2)
        r=RequestState(0,0,0,2,offered_fare=10.)
        self.assertEqual(find_eligible_vehicle(r,fleet,{0:[1]},driver_minimum_prices={0:11.,1:10.,2:0.}).vehicle_id,1)
    def test_missing_driver_minimum_rejected(self):
        from src.dispatch.dispatch import find_eligible_vehicle
        fleet=Fleet([VehicleState(0,0,VehicleStatus.IDLE,None,0,'idle',60.)],frozenset(range(142)),2)
        with self.assertRaises(KeyError):find_eligible_vehicle(RequestState(0,0,0,1,offered_fare=10.),fleet,{},driver_minimum_prices={})
    def test_production_dispatch_always_supplies_profile_gate(self):
        tree=ast.parse((ROOT/'src/simulation/final_production.py').read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dispatch_requests']
        self.assertEqual(len(calls),1)
        kw={k.arg:ast.unparse(k.value) for k in calls[0].keywords}
        self.assertEqual(kw['driver_minimum_prices'],'self.profiles.price_preference')
        self.assertIn('price_observer',kw)
