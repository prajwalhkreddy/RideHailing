"""Passenger absolute-time boundary regressions; no model training."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np,pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.fleet.state import VehicleState,VehicleStatus
from src.fleet.fleet import Fleet
from src.pricing.dqn_contract import PassengerCommitment,DispatchLedger,Snapshot,incoming

class BoundaryTests(unittest.TestCase):
    def make(self):
        x=ProductionExperiment.__new__(ProductionExperiment);x.timestamp=pd.Timestamp('2026-03-01 00:30');x.clock=x.timestamp;x.fleet_size=5000
        x.fleet=Fleet([VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(5000)],frozenset(range(142)),2)
        x.energy=object();x.charging=SimpleNamespace(advance_mini_slot=lambda *args:None);x.passengers={};x.missions={}
        t=pd.Timestamp('2026-03-01 01:00')
        for i,arrival in enumerate([t-pd.Timedelta(seconds=1),t,t+pd.Timedelta(minutes=2),t+pd.Timedelta(minutes=30)]):
            duration=(arrival-x.clock).total_seconds()/60;x.fleet.assign_busy(i,i+1,duration)
            x.passengers[i]=PassengerCommitment(i,i+1,x.clock,arrival)
        return x,t
    def advance(self,x,t):
        completed=0
        # Many fractional steps reproduce accumulated subtraction exposure.
        for seconds in [17,37,109,173,233,389,563,719,877,1021,1249,1433,1667]:
            completed+=x.advance_until(pd.Timestamp('2026-03-01 00:30')+pd.Timedelta(seconds=seconds))
        # Inject the observed residual representation without changing event times.
        x.fleet.vehicle(1).remaining_travel_time+=1.608400912456176e-12
        completed+=x.advance_until(t)
        return completed
    def test_boundary_and_incoming(self):
        x,t=self.make();self.assertEqual(self.advance(x,t),2)
        for i in [0,1]:
            v=x.fleet.vehicle(i);self.assertEqual(v.current_grid,i+1);self.assertEqual(v.trip_status,VehicleStatus.IDLE);self.assertNotIn(i,x.passengers)
        self.assertEqual(set(x.passengers),{2,3})
        counts=incoming(x.passengers.values(),t)
        self.assertEqual(counts[1],0);self.assertEqual(counts[2],0);self.assertEqual(counts[3],1);self.assertEqual(counts[4],1)
        self.assertEqual(x.advance_until(t),0)
        self.assertEqual(x.advance_until(t+pd.Timedelta(minutes=2)),1)
        self.assertEqual(x.advance_until(t+pd.Timedelta(minutes=30)),1)
        self.assertEqual(len(x.passengers),0);self.assertEqual(len(x.fleet.vehicles),5000)
    def test_state_publication_after_due_arrivals(self):
        x,t=self.make();self.advance(x,t);x.timestamp=t
        x.ledger=DispatchLedger();x.ledger.complete_slot(t-pd.Timedelta(minutes=30),t,[])
        forecast=Snapshot(t,t,{g:1. for g in range(142)},t);pop=Snapshot(t,t,{g:0. for g in range(142)},t)
        x.operational=object();x.routing=object();x.policy=lambda a,training:SimpleNamespace(numpy=lambda:np.zeros((142,9)))
        rs=SimpleNamespace(values=np.zeros(169),mask=np.ones(9,dtype=bool))
        with patch('src.simulation.final_production.artifact_snapshots',return_value=(forecast,pop)),patch('src.simulation.final_production.RoutingState.from_producer',return_value=rs):
            builder=x._state_sources();self.assertEqual(builder.build(3,0,t)[2],1)
    def test_future_not_processed_early(self):
        x,t=self.make();x.advance_until(t-pd.Timedelta(nanoseconds=1))
        self.assertIn(1,x.passengers);self.assertEqual(x.fleet.vehicle(1).trip_status,VehicleStatus.BUSY)
        x.advance_until(t);self.assertNotIn(1,x.passengers)
    def test_coincident_float_hop_and_absolute_passenger_event(self):
        x,_=self.make();start=x.clock
        x.passengers[0]=PassengerCommitment(0,1,start,start+pd.Timedelta(seconds=6))
        x.fleet.vehicle(0).remaining_travel_time=.1
        x.fleet.assign_busy(4,5,.1-1e-16)
        self.assertEqual(x.advance_until(start+pd.Timedelta(seconds=7)),1)
        self.assertNotIn(0,x.passengers)
        self.assertEqual(x.fleet.vehicle(0).current_grid,1)
        self.assertEqual(x.fleet.vehicle(4).current_grid,5)

    def test_destination_inconsistency_still_fails(self):
        x,t=self.make();x.fleet.vehicle(0).destination=9
        with self.assertRaisesRegex(ValueError,'destination/event mismatch'):x.advance_until(t)
    def test_due_commitment_still_fails_closed(self):
        x,t=self.make();x.passengers[0]=PassengerCommitment(0,1,x.clock-pd.Timedelta(minutes=1),x.clock)
        with self.assertRaisesRegex(ValueError,'Due passenger event'):x.advance_until(t)

class ResumeArtifactTests(unittest.TestCase):
    def paths(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        return root/'data/processed/routing_experiences_mar01_mar15_2026',root/'results/analysis/2026-10-21_passenger_arrival_boundary_fix'
    def test_checkpoint_resume_and_fleet(self):
        from src.simulation.routing_experience_generation import RoutingExperienceExperiment
        data,_=self.paths();x=RoutingExperienceExperiment.__new__(RoutingExperienceExperiment)
        x.request_rng=np.random.default_rng(42);x.customer=SimpleNamespace(rng=np.random.default_rng(42));x._state_sources=lambda:None
        x.restore(data/'generation_checkpoint.pkl')
        self.assertEqual(x.timestamp,pd.Timestamp('2026-03-01 03:00'));self.assertEqual(x.slot_index,6)
        self.assertEqual(len(x.fleet.vehicles),5000);self.assertEqual(len({v.vehicle_id for v in x.fleet.vehicles}),5000)
        self.assertTrue(all(pd.Timestamp(c.dropoff_at)>x.timestamp for c in x.passengers.values()))
        self.assertTrue(np.isfinite(x.operational.state_for(x.timestamp)[['mu','sigma','F_hat','H_hat']]).all().all())
    def test_append_once_original_preserved(self):
        import hashlib,json
        data,out=self.paths();diag=json.loads((out/'arrival_failure_diagnosis.json').read_text())
        self.assertEqual(hashlib.sha256((data/'slot_0000.parquet').read_bytes()).hexdigest(),diag['initial_hashes']['slot_0000.parquet'])
        ids=np.concatenate([pd.read_parquet(data/f'slot_{i:04d}.parquet',columns=['experience_id']).experience_id.to_numpy() for i in range(6)])
        np.testing.assert_array_equal(ids,np.arange(len(ids)))
        self.assertFalse((data/'slot_0006.parquet').exists())
    def test_repeated_boundary_observations(self):
        import json
        _,out=self.paths();d=json.loads((out/'resume_boundary_observations.json').read_text())
        for t in pd.date_range('2026-03-01 01:00','2026-03-01 03:00',freq='30min'):self.assertIn(str(t),d['boundaries'])
        self.assertEqual(len(d['affected_arrivals']),2)
        for r in d['affected_arrivals']:self.assertTrue(r['commitment_cleared']);self.assertEqual(r['status'],'IDLE');self.assertEqual(r['arrival_time'],'2026-03-01 01:00:00')

if __name__=='__main__':unittest.main()
