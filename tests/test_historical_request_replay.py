"""Forecast-independent replay and bounded production-component integration."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from tests.test_od_pricing import runtime
from src.pricing.od_contract import od_states
from src.simulation.historical_request_replay import replay_requests, read_slot, PROTOCOL
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.v3_checkpoint_codec import encode


def frame(slot='2026-03-12', n=4, *, utc_mode=False):
    if utc_mode: raise AssertionError('Legacy fixture expects naive mode')
    t=pd.Timestamp(slot)
    return pd.DataFrame(dict(tpep_pickup_datetime=[t+pd.Timedelta(seconds=17)]*n,
        tpep_dropoff_datetime=[t+pd.Timedelta(minutes=150,seconds=17)]*n,
        PUGridID=[0]*n,DOGridID=[1]*n,trip_distance=[30/1.609344]*(n-1)+[.01/1.609344] if n else [],
        fare_amount=[20.]*n,source_file_month=[3]*n,source_prepared_row=list(range(n))))


class ReplayTests(unittest.TestCase):
    def test_attributes_order_and_conservation(self):
        f=frame();f.loc[1,'tpep_pickup_datetime']+=pd.Timedelta(microseconds=123)
        a,report=replay_requests(f.iloc[::-1],'2026-03-12',[(0,1)])
        self.assertEqual(report['realized_requests'],4)
        self.assertEqual([r.source_prepared_row for r in a],[0,2,3,1])
        for r in a:
            row=f.iloc[r.source_prepared_row]
            self.assertEqual(r.trip_distance_miles,row.trip_distance);self.assertEqual(r.base_fare,row.fare_amount)
            self.assertEqual((r.origin_grid,r.destination_grid),(row.PUGridID,row.DOGridID))
            self.assertEqual(pd.Timestamp(r.empirical_pickup_datetime),row.tpep_pickup_datetime)
        self.assertEqual(report,replay_requests(f,'2026-03-12',[(0,1)])[1])
    def test_source_file_month_is_provenance_not_pickup_filter(self):
        f=frame();f['source_file_month']=2
        rows,report=replay_requests(f,'2026-03-12',[(0,1)])
        self.assertEqual(report['realized_requests'],4)
        self.assertTrue(all(r.source_file_month==2 for r in rows))

    def test_invalid_and_unsupported(self):
        f=frame();f.loc[0,'fare_amount']=-1
        r,m=replay_requests(f,'2026-03-12',[(0,1)]);self.assertEqual((len(r),m['excluded_invalid_trip_rows']),(3,1))
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED'):replay_requests(frame(),'2026-03-12',[(1,1)])
        f=frame();f.loc[1,'source_prepared_row']=0
        with self.assertRaises(ValueError):replay_requests(f,'2026-03-12',[(0,1)])
    def test_protected_before_read(self):
        with patch('src.simulation.historical_request_replay.pd.read_parquet') as read:
            with self.assertRaises(ValueError):read_slot('2026-03-17')
            read.assert_not_called()
        with self.assertRaises(ValueError):replay_requests(frame(),'2026-03-13',[(0,1)])
    def test_forecast_volume_independence_and_no_lookahead(self):
        observed=[]
        for forecast,count in [(7.25,4),(100.75,4),(7.25,2)]:
            r=runtime();r.engine.current_states.forecast.values[0]=forecast;r.states=od_states(r.engine,r.pairs)
            decisions=[]
            def policy(od,state):decisions.append((od,state.copy()));return 0
            def read(t, *, utc_mode=False):
                self.assertFalse(utc_mode)
                self.assertEqual(len(decisions),len(r.pairs))
                return frame(t,count)
            with patch('src.simulation.historical_request_replay.read_slot',side_effect=read):rows=r.run_slot(policy=policy,weather_code=1)
            value=next(s[0] for pair,s in decisions if pair==(0,1));observed.append((value,len(rows)))
            self.assertEqual(r.demand_state['requests_consumed'],len(rows))
            self.assertAlmostEqual(sum(x['reward_contribution'] for x in rows),r.environment_reward)
            self.assertAlmostEqual(sum(x[2] for x in r.learner.replay),r.environment_reward)
            self.assertTrue(all(x['reward_contribution']==0 for x in rows if x['dispatch_outcome']!='ACCEPTED_AND_ASSIGNED'))
        self.assertEqual(observed,[(7.25,4),(100.75,4),(7.25,2)])
    def test_historical_replay_resume(self):
        r=runtime()
        with patch('src.simulation.historical_request_replay.read_slot',side_effect=frame):
            r.run_slot(weather_code=1)
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'checkpoint';save_od_checkpoint(r,p);other=load_od_checkpoint(p)
                for obj in (r,other):obj.run_slot(weather_code=1)
                self.assertEqual(encode(r.audit),encode(other.audit))
                self.assertEqual(encode(r.demand_state),encode(other.demand_state))
                self.assertEqual(encode(r.demand_audit),encode(other.demand_audit))
                self.assertEqual(encode(list(r.learner.replay)),encode(list(other.learner.replay)))
                self.assertEqual(encode(r.engine.fleet),encode(other.engine.fleet))
                self.assertEqual(r.demand_state['requests_consumed'],8)
                other.demand_state['protocol']='FORECAST_DRIVEN'
                with self.assertRaises(ValueError):save_od_checkpoint(other,Path(tmp)/'wrong')
    def test_batched_action_rng_equivalence(self):
        r=runtime();a=r.learner;state=copy.deepcopy(a.rng.bit_generator.state)
        expected=[a.select_action(s) for s in r.states.values()]
        a.rng.bit_generator.state=state
        self.assertEqual(a.select_actions(list(r.states.values())),expected)

if __name__=='__main__':unittest.main()
