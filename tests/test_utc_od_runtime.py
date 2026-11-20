import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.demand.causal_timing import CHANNELS,timing
from src.demand.persistence_weather import contract,fingerprint,VERSION
from src.simulation.master_od_contract import utc
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.historical_request_replay import replay_requests
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
from tests.test_od_pricing import evidence,ROUTING
from src.pricing.od_contract import support_from_trips

def inputs(start):
    m=contract(120);frames={};weather={}
    for t in pd.date_range(utc(start),periods=17,freq='30min'):
        info=timing(t);obs=t-pd.Timedelta(hours=3)
        frames[str(t)]=pd.DataFrame(dict(Grid_ID=range(142),predicted_demand=.25,observation_time=obs,assumed_available_at=obs+pd.Timedelta(hours=2),**info))
        weather[str(t)]=1
    return dict(weather_contract=m,checkpoint_metadata=dict(version=VERSION,weather_contract_sha256=fingerprint(m)),channels=list(CHANNELS),grid_ids=list(range(142)),forecasts=frames,realized_weather=weather,popularity={i:0. for i in range(142)},popularity_available_at=utc('2026-02-01'))

def runtime(start='2026-03-08 01:30'):
    return ODPricingRuntime(start=start,routing_checkpoint=ROUTING,utc_inputs=inputs(start),od_support=support_from_trips(evidence()),fleet=Fleet([VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(2)],frozenset(range(142)),2),driver_profiles=pd.DataFrame(dict(vehicle_id=range(2),price_preference=[0.]*2,wait_preference=[10.]*2,charging_wait_preference_minutes=[10.]*2)))

def trips():
    return pd.DataFrame(dict(tpep_pickup_datetime=pd.to_datetime(['2026-03-08 01:59','2026-03-08 01:31']),tpep_dropoff_datetime=pd.to_datetime(['2026-03-08 04:09','2026-03-08 04:01']),PUGridID=[0,0],DOGridID=[1,1],trip_distance=[30.,30.],fare_amount=[20.,20.],source_file_month=[3,3],source_prepared_row=[2,1]))

class UTCRuntimeTests(unittest.TestCase):
    def test_dst_requests_and_resume(self):
        a=runtime('2026-03-08 01:00');f=trips();f['tpep_pickup_datetime']=pd.to_datetime(['2026-03-08 01:29','2026-03-08 01:01']);f['tpep_dropoff_datetime']=pd.to_datetime(['2026-03-08 03:39','2026-03-08 03:31']);requests,report=replay_requests(f,a.engine.timestamp,a.pairs,utc_mode=True)
        self.assertEqual([r.trip_duration_minutes for r in requests],[90,70])
        self.assertEqual([r.request_time for r in requests],[0,14])
        a.run_slot(requests,policy=lambda d,s:0)
        self.assertEqual(a.engine.timestamp,utc('2026-03-08 01:30'))
        self.assertEqual(len(a.engine.passengers),2)
        self.assertEqual(sum(r['reward_contribution'] for r in a.audit),a.environment_reward)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'utc';save_od_checkpoint(a,p)
            with self.assertRaises(ValueError):load_od_checkpoint(p,master_math=True)
            b=load_od_checkpoint(p,master_math=True,utc_mode=True)
            for r in [a,b]:
                for index in range(3):
                    r.run_slot([],policy=lambda d,s:0)
                    if index==1:self.assertEqual(r.states[(1,1)][2],2)
            self.assertEqual(a.engine.timestamp,b.engine.timestamp)
            self.assertEqual(a.engine.passengers,{})
            self.assertEqual(a.learner.identities,b.learner.identities)
            for x,y in zip(a.engine.fleet.vehicles,b.engine.fleet.vehicles):self.assertEqual(vars(x),vars(y))
            for d in a.states:np.testing.assert_array_equal(a.states[d],b.states[d])
    def test_termination_and_ordinary_control(self):
        a=runtime('2026-03-12')
        for _ in range(16):a.run_slot([],policy=lambda d,s:0)
        self.assertEqual(a.engine.timestamp,utc('2026-03-12 08:00'))
        self.assertTrue(all(r[4] for r in list(a.learner.replay)[-len(a.pairs):]))
        with self.assertRaises(ValueError):a.run_slot([])
    def test_forecast_reject(self):
        a=inputs('2026-03-08 01:30');a['checkpoint_metadata']['version']='ORACLE'
        from src.simulation.utc_od_inputs import forecast
        with self.assertRaises(ValueError):forecast(a,utc('2026-03-08 01:30'))

    def test_charging_reposition_and_elapsed_wait(self):
        a=runtime();e=a.engine;v=e.fleet.vehicle(0);station=next(iter(e.charging.stations.values()))
        v.current_grid=station.grid_id;v.energy_level=5.;v.abandon_idle_wait()
        e.charging.admit_arrived(v,station.station_id,e.energy,0)
        other=e.fleet.vehicle(1);other.start_idle_wait()
        initial=v.energy_level
        e.advance_until(utc('2026-03-08 03:00'))
        self.assertAlmostEqual(v.energy_level-initial,e.energy.charging_power_kw*e.energy.charging_efficiency*.5)
        self.assertEqual(v.trip_status,VehicleStatus.CHARGING)
        self.assertEqual(other.idle_wait_minutes,30.)
    def test_reposition_across_dst(self):
        from src.routing.operational_interface import LocalDecision
        a=runtime();e=a.engine;e.advance_until(utc('2026-03-08 01:59'))
        v=e.fleet.vehicle(0);action,(dest,distance)=next(iter(e.routing.edges[v.current_grid].items()))
        before=v.energy_level
        duration=e.routing.start_next_hop(v,LocalDecision(action,dest,dest,'REPOSITION',0.,distance),speed_kmph=e.config['routing']['speed_kmph'],energy_per_km=e.energy.consumption_rate_kwh_per_km)
        v.current_action='repositioning';end=e.clock+pd.Timedelta(minutes=duration)
        e.advance_until(end)
        self.assertEqual(v.trip_status,VehicleStatus.IDLE);self.assertEqual(v.current_grid,dest)
        self.assertGreaterEqual(e.clock.tz_convert('America/New_York').hour,3)
        self.assertAlmostEqual(before-v.energy_level,distance/1000*e.energy.consumption_rate_kwh_per_km)

    def test_request_loading_and_forecast_timing(self):
        from unittest.mock import patch
        from src.simulation.utc_od_inputs import forecast
        a=runtime()
        with patch('src.simulation.historical_request_replay.read_slot',return_value=trips()):
            a.run_slot(policy=lambda d,s:0)
        self.assertEqual(a.demand_audit[0]['source_rows'],2)
        self.assertEqual(a.demand_state['requests_consumed'],2)
        self.assertTrue(all(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in a.audit))
        data=inputs('2026-03-08 01:30');t=utc('2026-03-08 01:30')
        data['forecasts'][str(t)]['target_start']=t+pd.Timedelta(minutes=30)
        with self.assertRaises(ValueError):forecast(data,t)
    def test_charging_checkpoint_across_dst(self):
        from src.simulation.v3_checkpoint_codec import encode
        a=runtime('2026-03-08 01:00');e=a.engine;v=e.fleet.vehicle(0);station=next(iter(e.charging.stations.values()))
        v.current_grid=station.grid_id;v.energy_level=5.;v.abandon_idle_wait()
        e.charging.admit_arrived(v,station.station_id,e.energy,0)
        a.run_slot([],policy=lambda d,s:0)
        self.assertEqual(v.trip_status,VehicleStatus.CHARGING)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'charging';save_od_checkpoint(a,p)
            b=load_od_checkpoint(p,master_math=True,utc_mode=True)
            for r in [a,b]:r.run_slot([],policy=lambda d,s:0)
            self.assertEqual(a.engine.timestamp,utc('2026-03-08 03:00'))
            self.assertEqual(encode(a.engine.charging),encode(b.engine.charging))
            self.assertEqual(encode(a.engine.fleet),encode(b.engine.fleet))
            self.assertLessEqual(a.engine.fleet.vehicle(0).energy_level,a.engine.energy.battery_capacity_kwh)
