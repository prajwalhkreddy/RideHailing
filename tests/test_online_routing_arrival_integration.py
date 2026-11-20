"""Regression for the mixed-fleet arrival blocker; no gradients or data replay."""
import unittest
from types import SimpleNamespace
import pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus

class MixedArrivalTests(unittest.TestCase):
    def engine(self,is_ev):
        e=object.__new__(ProductionExperiment)
        e.clock=pd.Timestamp('2026-03-12T04:00Z')
        v=VehicleState(0,0,VehicleStatus.BUSY,1,1.,'passenger_trip',0.)
        v.is_ev=is_ev
        e.fleet=Fleet([v],frozenset(range(142)),2)
        e.fleet_size=1;e.passengers={};e.missions={};e.energy=None
        e.charging=SimpleNamespace(advance_mini_slot=lambda *args:None)
        e.station_reserve=lambda grid:1.
        return e

    def test_non_ev_arrival_requires_no_battery_reserve(self):
        e=self.engine(False)
        e.advance_until(e.clock+pd.Timedelta(minutes=1))
        self.assertEqual(e.fleet.vehicle(0).current_grid,1)
        self.assertIs(e.fleet.vehicle(0).trip_status,VehicleStatus.IDLE)

    def test_ev_without_station_reserve_still_rejected(self):
        e=self.engine(True)
        with self.assertRaisesRegex(ValueError,'Post-movement station reachability'):
            e.advance_until(e.clock+pd.Timedelta(minutes=1))

    def test_ev_sufficient_reserve_and_utc_arrival(self):
        e=self.engine(True);e.fleet.vehicle(0).energy_level=1.
        end=e.clock+pd.Timedelta(minutes=1)
        e.advance_until(end)
        self.assertEqual(e.clock,end)
        self.assertEqual(e.fleet.vehicle(0).current_grid,1)

    def test_historical_missing_identity_remains_ev(self):
        e=self.engine(True);del e.fleet.vehicle(0).is_ev
        with self.assertRaisesRegex(ValueError,'Post-movement station reachability'):
            e.advance_until(e.clock+pd.Timedelta(minutes=1))

    def test_non_ev_never_queries_station_reserve(self):
        e=self.engine(False)
        def forbidden(grid):raise AssertionError('Non-EV reserve queried')
        e.station_reserve=forbidden
        e.advance_until(e.clock+pd.Timedelta(minutes=1))

    def test_failure_diagnostics(self):
        import json
        e=self.engine(True)
        with self.assertRaises(ValueError) as error:e.advance_until(e.clock+pd.Timedelta(minutes=1))
        d=json.loads(str(error.exception).split('. ',1)[1])
        self.assertEqual(d['vehicle_type'],'EV');self.assertEqual(d['reserve_kwh'],1.)
        self.assertEqual(d['destination'],1);self.assertEqual(d['vehicle_id'],0)
        self.assertEqual(d['event_timestamp'],'2026-03-12 04:01:00+00:00')
