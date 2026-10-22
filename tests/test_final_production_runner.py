"""Short final-runner integration, never the four-slot historical episode."""
import unittest
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.simulation.final_production import ProductionExperiment,validate_final_contract
from src.pricing.dqn_contract import ROOT
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
from src.dispatch.request import RequestState
from src.charging.stations import ChargingStation
from src.charging.timed import TimedChargingInfrastructure


def fixture_runner():
    base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
    stations=pd.read_parquet(base/'charging_stations.parquet')
    neighbors=pd.read_parquet(base/'neighbour_map.parquet')
    target=int(stations.grid_id.iloc[0])
    origin=int(neighbors[neighbors.NeighbourGridID==target].iloc[0].GridID)
    fleet=Fleet([VehicleState(i,g,VehicleStatus.IDLE,None,0,'idle',e) for i,g,e in [(0,0,60.),(1,1,60.),(2,origin,15.)]],frozenset(range(142)),2)
    profiles=pd.DataFrame(dict(vehicle_id=[0,1,2],price_preference=[0.,0.,0.],wait_preference=[10.,10.,10.],charging_wait_preference_minutes=[10.,10.,10.]))
    return ProductionExperiment(fleet=fleet,driver_profiles=profiles)


def fixture_requests(runner,slot):
    t=runner.timestamp
    return [RequestState(slot*10+i,0,g,1-g,base_fare=20.,source_trip_id=slot*10+i,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=40)).to_pydatetime(),trip_duration_minutes=40.,trip_distance_miles=10.,trip_distance_km=16.09344) for i,g in enumerate([0,1])]


class FinalRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner=fixture_runner();x=cls.runner
        cls.initial=x.current_states.build(0,1,x.timestamp)
        cls.first=x.run_slot(fixture_requests(x,0),train_dqn=True)
        cls.next=x.current_states.build(0,1,x.timestamp)
        cls.departure_grid=x.fleet.vehicle(2).current_grid
        cls.departure_status=x.fleet.vehicle(2).trip_status
        cls.second=x.run_slot(fixture_requests(x,1),terminal=True,train_dqn=True)

    def test_final_entrypoint(self):
        from src.simulation.production import ProductionExperiment as public,LegacyProductionExperiment
        self.assertIs(public,ProductionExperiment);self.assertIsNot(public,LegacyProductionExperiment)

    def test_startup_contracts(self):
        meta=json.loads((ROOT/'data/processed/grid_metadata.json').read_text())
        validate_final_contract(meta)
        for change in [dict(valid_grid_count=1213),dict(raster_rows=51,raster_columns=52),dict(grid_version='legacy')]:
            with self.assertRaises(ValueError):validate_final_contract(dict(meta,**change))
        for change in [dict(routing_input=155),dict(routing_output=5),dict(pricing_input=12),dict(pricing_actions=(1.,)),dict(timed_charging=False),dict(operational_state=False)]:
            with self.assertRaises(ValueError):validate_final_contract(meta,**change)

    def test_replay_and_assignment_reward(self):
        x=self.runner
        self.assertEqual([self.first['assigned'],self.second['assigned']],[2,0])
        self.assertGreater(self.first['reward'],0);self.assertEqual(self.second['reward'],0)
        self.assertEqual(len(x.dqn.replay),4);self.assertEqual(x.dqn.training_steps,0)
        self.assertEqual(sum(r[4] for r in x.dqn.replay.items),2)
        self.assertAlmostEqual(sum(r[2] for r in x.dqn.replay.items),self.first['reward'],places=6)
        for s,a,r,n,d in x.dqn.replay.items:
            self.assertEqual(s.shape,(13,));self.assertEqual(n.shape,(13,));self.assertTrue(0<=a<7)

    def test_past_dispatch_and_known_incoming(self):
        self.assertEqual(self.initial[1],0);self.assertEqual(self.initial[2],0)
        self.assertEqual(self.next[1],1);self.assertEqual(self.next[2],1)
        self.assertEqual(self.second['completed'],2)
        self.assertEqual(len(self.runner.fleet.vehicles),3)
        self.assertEqual(len(self.runner.passengers),0)
        with self.assertRaises(ValueError):self.runner.current_states.build(0,1,pd.Timestamp('2026-03-16 01:30'))

    def test_masked_nine_actions(self):
        x=self.runner
        for g in range(142):
            s=x.current_states.build(g,0,x.timestamp)
            self.assertEqual(len(s[3:12]),9);self.assertAlmostEqual(sum(s[3:12]),1.,places=6)
            for action in set(range(9))-set(x.routing.candidates(g)):self.assertEqual(s[3+action],0)

    def test_timed_charging_path(self):
        x=self.runner;events=x.charging_events
        travel=events[0];arrival=events[-1]
        self.assertEqual(self.departure_status,VehicleStatus.BUSY)
        self.assertEqual(self.departure_grid,travel['grid'])
        self.assertNotEqual(travel['grid'],arrival['grid'])
        self.assertAlmostEqual((pd.Timestamp(arrival['timestamp'])-pd.Timestamp(travel['timestamp'])).total_seconds()/60,12.)
        self.assertEqual(x.fleet.vehicle(2).current_action,'charging')
        self.assertAlmostEqual(x.fleet.vehicle(2).energy_level,22.65)
        with self.assertRaises(ValueError):x.charging.present_vehicle(x.fleet.vehicle(2))

    def test_queue_wait_and_release(self):
        # Isolated one-car-power station exercises contention without changing production capacity.
        x=self.runner;infra=TimedChargingInfrastructure([ChargingStation(0,0,30.,30.)],{0:(0.,0.)})
        vehicles=[VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',15.) for i in (100,101)]
        for i,v in enumerate(vehicles):infra.admit_arrived(v,0,x.energy,i)
        self.assertEqual(vehicles[1].current_action,'charging_queue')
        infra.advance_mini_slot(vehicles,2.,x.energy)
        self.assertEqual(infra.stations[0].queue[0].wait_minutes,2.)
        self.assertEqual(vehicles[1].energy_level,15.)
        vehicles[0].energy_level=74.55
        infra.advance_mini_slot(vehicles,1.,x.energy)
        self.assertEqual(vehicles[0].trip_status,VehicleStatus.IDLE)
        self.assertEqual(vehicles[1].current_action,'charging')
        self.assertEqual(vehicles[1].energy_level,15.)
        infra.advance_mini_slot(vehicles,1.,x.energy)
        self.assertAlmostEqual(vehicles[1].energy_level,15.45)

    def test_multihop_preserves_station_and_elapsed_time(self):
        x=fixture_runner();v=x.fleet.vehicle(2)
        station=next(iter(x.charging.stations.values()))
        # Explicit test mission exercises more than one edge of the real graph.
        origin=next(g for g in range(142) if x.routing.paths(g)[station.grid_id][0]>7000)
        v.current_grid=origin;v.start_idle_wait();v.energy_level=15.
        distance=x.routing.paths(origin)[station.grid_id][0]
        x.missions[v.vehicle_id]=station.station_id;x._continue_charging(v)
        self.assertEqual(v.current_grid,origin)
        end=x.clock+pd.Timedelta(minutes=distance/1000/x.config['routing']['speed_kmph']*60+1)
        x.advance_until(end)
        self.assertEqual(v.current_grid,station.grid_id)
        self.assertEqual(v.current_action,'charging')
        self.assertGreater(len(x.charging_events),2)
        elapsed=(pd.Timestamp(x.charging_events[-1]['timestamp'])-pd.Timestamp(x.charging_events[0]['timestamp'])).total_seconds()/60
        self.assertAlmostEqual(elapsed,distance/1000/x.config['routing']['speed_kmph']*60,places=6)

    def test_actual_pickup_offset_and_warmup_training_call(self):
        from unittest.mock import patch
        x=fixture_runner();r=fixture_requests(x,0)[0]
        r.empirical_within_slot_offset_seconds=90.
        r.empirical_pickup_datetime=(x.timestamp+pd.Timedelta(seconds=90)).to_pydatetime()
        r.empirical_dropoff_datetime=(x.timestamp+pd.Timedelta(minutes=41,seconds=30)).to_pydatetime()
        with patch.object(x.dqn,'train_step',wraps=x.dqn.train_step) as training:
            x.run_slot([r],train_dqn=True)
            training.assert_called_once()
        self.assertEqual(x.passengers[0].committed_at,pd.Timestamp('2026-03-16 00:01:30'))
        self.assertEqual(x.passengers[0].dropoff_at,pd.Timestamp('2026-03-16 00:41:30'))
        self.assertAlmostEqual(x.fleet.vehicle(0).remaining_travel_time,11.5)

    def test_no_instant_remote_admission(self):
        x=self.runner
        infra=TimedChargingInfrastructure([ChargingStation(0,0,30.,30.)],{0:(0.,0.)})
        v=VehicleState(100,1,VehicleStatus.IDLE,None,0,'idle',15.)
        with self.assertRaises(ValueError):infra.admit_arrived(v,0,x.energy,0)

if __name__=='__main__':unittest.main()
