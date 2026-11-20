import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from src.simulation.master_od_contract import ewma, utc, slot, arrival_slot, request_order
from src.simulation.operational_state import SmoothingParameters
from src.rl.od_pricing_dqn import ODPricingDQN
from src.rl.pricing_dqn import DQNConfig, bellman_targets
from tests.test_od_pricing import runtime, requests
from src.simulation.master_operational_state import MasterOperationalGridState
from src.simulation.od_pricing_checkpoint import save_od_checkpoint, load_od_checkpoint

class MasterMathTests(unittest.TestCase):
    def test_operational_rejects_before_loading_artifacts(self):
        from src.simulation.od_pricing_runtime import ODPricingRuntime
        with self.assertRaisesRegex(ValueError,"CAUSAL_OD_OPERATION_BLOCKED"):
            ODPricingRuntime(start="2026-03-12",routing_checkpoint="unused",master_math=True,operational=True)

    def test_previous_mean_deviation(self):
        p=SmoothingParameters(.3,.3,.3,.3,.01)
        np.testing.assert_allclose(ewma([10,2,1,4],[20,30],10,p),[14.5,5.9,.72,5.8])
        np.testing.assert_allclose(ewma([10,2,1,4],[],None,p),[10,2,.7,4])
        self.assertEqual(ewma([10,0,0,0],[10],0,p)[1],0)
    def test_dst_and_elapsed_arrival(self):
        start=slot('2026-03-08 01:30');end=start+pd.Timedelta(minutes=30)
        self.assertEqual(end.tz_convert('America/New_York').hour,3)
        a,s=arrival_slot('2026-03-08 01:55',10)
        self.assertEqual(a.tz_convert('America/New_York').strftime('%H:%M'),'03:05')
        self.assertEqual(s,end)
        a,_=arrival_slot('2026-03-12 23:55',10)
        self.assertEqual(a.tz_convert('America/New_York').day,13)
        with self.assertRaises(Exception):utc('2026-03-08 02:15')
    def test_request_order_and_duration(self):
        f=pd.DataFrame(dict(tpep_pickup_datetime=['2026-03-08 01:59','2026-03-08 01:31'],tpep_dropoff_datetime=['2026-03-08 03:09','2026-03-08 03:01'],source_file_month=[3,3],source_prepared_row=[2,1]))
        g=request_order(f,'2026-03-08 01:30')
        self.assertEqual(g.mini_slot.tolist(),[0,14]);self.assertEqual(g.duration_minutes.tolist(),[30,10]);self.assertEqual(len(f),len(g))
    def test_squared_loss_and_resume(self):
        c=DQNConfig(batch_size=2,minimum_replay_size=2)
        a=ODPricingDQN(master_math=True,config=c)
        for net in [a.online,a.target]:net.set_weights([np.zeros_like(v) for v in net.get_weights()])
        state=np.zeros(13,np.float32);state[3]=1
        self.assertIsNone(a.train_step())
        for i in range(2):a.store(state,0,4,state,True,identity=('2026-03-12',0,i))
        self.assertEqual(a.train_step(),8.)
        for o,t in zip(a.online.get_weights(),a.target.get_weights()):np.testing.assert_allclose(t,.005*o)
        with tempfile.TemporaryDirectory() as tmp:
            tmp=str(Path(tmp)/"learner");a.save(tmp)
            with self.assertRaises(ValueError):ODPricingDQN.load(tmp)
            b=ODPricingDQN.load(tmp,master_math=True)
            self.assertEqual(a.train_step(),b.train_step())
            for x,y in zip(a.online.get_weights(),b.online.get_weights()):np.testing.assert_array_equal(x,y)
        np.testing.assert_allclose(bellman_targets([1,2],np.array([False,True]),np.ones((2,7))*3,.99),[3.97,2])
    def test_math_runtime_checkpoint(self):
        # Existing bounded fixture, with explicit new mode; no production episode.
        a=runtime();a.master_math=True;a.engine.operational.__class__=MasterOperationalGridState;a.learner=ODPricingDQN(master_math=True)
        a.run_slot(requests(a.engine.timestamp),policy=lambda d,s:0,weather_code=1)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'checkpoint';save_od_checkpoint(a,path)
            with self.assertRaises(ValueError):load_od_checkpoint(path)
            b=load_od_checkpoint(path,master_math=True)
            for r in [a,b]:r.run_slot([],policy=lambda d,s:0,weather_code=1)
            np.testing.assert_array_equal(a.engine.operational._state,b.engine.operational._state)
            for k in a.states:np.testing.assert_array_equal(a.states[k],b.states[k])
            self.assertEqual(a.learner.identities,b.learner.identities)
