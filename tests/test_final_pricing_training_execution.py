"""Focused final-launch persistence, identity, temporal and ownership checks."""
import unittest,tempfile,json,subprocess,sys,os
from pathlib import Path
from types import SimpleNamespace
import numpy as np,pandas as pd
from src.simulation.final_pricing_training import (ROOT,ROUTING,MODEL,FIELDS,identity,checkpoint,restore,lock_writer,weights_hash)
from src.rl.pricing_dqn import PricingDQN,validate_state
from src.routing.learning import load_final_policy,masked_softmax
from src.simulation.temporal_protocol import assert_training_update_allowed

class FinalPricingExecutionTests(unittest.TestCase):
    def test_selected_routing_identity_and_probabilities(self):
        rid=identity();self.assertEqual(rid['status'],'SIMULATOR_DERIVED_ROUTING_BASELINE')
        model=load_final_policy(ROUTING);self.assertEqual(model.input_shape[-1],169);self.assertEqual(model.output_shape[-1],9)
        mask=np.array([1,1,0,0,0,0,0,0,0],bool)
        probs=masked_softmax(model(np.zeros((1,169),np.float32),training=False).numpy()[0],mask)
        self.assertTrue(np.isfinite(probs).all());self.assertEqual(len(probs),9);self.assertAlmostEqual(sum(probs),1.)
        self.assertTrue((probs[~mask]==0).all());validate_state(np.r_[0.,0.,0.,probs,.5])
    def test_seed42_clean_initialization(self):
        a=PricingDQN();b=PricingDQN()
        self.assertEqual(weights_hash(a.online),weights_hash(b.online));self.assertEqual(weights_hash(a.online),weights_hash(a.target))
        self.assertEqual((len(a.replay),a.training_steps,a.epsilon),(0,0,1.))
    def test_full_checkpoint_exact_optimizer_resume(self):
        x=SimpleNamespace(**{k:None for k in FIELDS})
        x.slot_index=1;x.timestamp=pd.Timestamp('2026-03-01 00:30');x.clock=x.timestamp;x.dqn=PricingDQN()
        x.request_rng=np.random.default_rng(42);x.customer=SimpleNamespace(rng=np.random.default_rng(42));x.routing=SimpleNamespace();x._state_sources=lambda:None
        state=np.r_[1.,0.,0.,1.,np.zeros(8),.5]
        for i in range(1000):x.dqn.store(state,i%7,float(i%20),state,False)
        x.dqn.train_step()
        with tempfile.TemporaryDirectory() as d:
            checkpoint(x,Path(d),identity())
            y=SimpleNamespace(dqn=None,routing=SimpleNamespace(),request_rng=np.random.default_rng(),customer=SimpleNamespace(rng=np.random.default_rng()),_state_sources=lambda:None)
            restore(y,Path(d),identity())
            self.assertEqual((y.slot_index,len(y.dqn.replay),y.dqn.training_steps),(1,1000,1))
            self.assertEqual(x.dqn.select_action(state),y.dqn.select_action(state))
            self.assertEqual(x.dqn.train_step(),y.dqn.train_step())
            self.assertEqual(weights_hash(x.dqn.online),weights_hash(y.dqn.online))
            self.assertEqual(weights_hash(x.dqn.target),weights_hash(y.dqn.target))
            for a,b in zip(x.dqn.online.optimizer.variables,y.dqn.online.optimizer.variables):np.testing.assert_array_equal(a.numpy(),b.numpy())
            with self.assertRaises(ValueError):restore(y,Path(d),dict(identity(),sha256='wrong'))
    def test_writer_lock(self):
        with tempfile.TemporaryDirectory() as d:
            f=lock_writer(Path(d))
            try:
                with self.assertRaises(RuntimeError):lock_writer(Path(d))
            finally:f.close()
            f=lock_writer(Path(d));f.close()
    def test_failed_background_launch_preserves_pid(self):
        # Use isolated validation namespace; production namespace is never touched.
        p=MODEL.with_name(MODEL.name+'_prelaunch');pid=p/'process.json'
        before=pid.read_bytes()
        result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/train_final_nonprivate_pricing.py'),'--background','--validation-only','--stop-after-slot','2'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.assertNotEqual(result.returncode,0);self.assertEqual(before,pid.read_bytes())
    def test_temporal_cutoff(self):
        assert_training_update_allowed('2026-03-15 23:30')
        for t in ['2026-03-16 00:00','2026-03-17 00:00','2026-03-31 23:30']:
            with self.assertRaises(ValueError):assert_training_update_allowed(t)

    def test_terminal_slot_does_not_read_march16_sources(self):
        from unittest.mock import patch,Mock
        from src.simulation.final_production import ProductionExperiment
        x=SimpleNamespace(timestamp=pd.Timestamp('2026-03-15 23:30'),clock=pd.Timestamp('2026-03-15 23:30'),frozen_routing=True,base=Path('/unused'),fleet=SimpleNamespace(vehicles=[]),fleet_size=0,slot_index=719,reports=[],unsupported_demand={})
        x.advance_until=lambda t:0;x.route_idle=lambda:(np.zeros(9,int),0)
        x.ledger=SimpleNamespace(complete_slot=lambda *args:0.)
        x.operational=SimpleNamespace(complete_slot=lambda **kwargs:None)
        x.dqn=PricingDQN();x.charging=SimpleNamespace()
        x._state_sources=Mock(side_effect=AssertionError('March16 source accessed'))
        weather=pd.DataFrame(dict(GridID=range(142),WeatherCode=[1]*142))
        with patch('src.simulation.final_production.pd.read_parquet',return_value=weather),patch('src.simulation.final_production.artifact_snapshots',side_effect=AssertionError('future source')),patch('src.simulation.final_production.charging_grid_observations',return_value={}):
            result=ProductionExperiment.run_slot(x,[],terminal=True,train_dqn=True)
        self.assertEqual(x.timestamp,pd.Timestamp('2026-03-16'));self.assertEqual(result['federated_updates'],0)
        x._state_sources.assert_not_called()
    def test_frozen_runner_rejects_updates_and_late_training(self):
        from src.simulation.final_production import ProductionExperiment
        x=SimpleNamespace(timestamp=pd.Timestamp('2026-03-01'),frozen_routing=True)
        with self.assertRaises(ValueError):ProductionExperiment.run_slot(x,[],routing_updates=({'weights':[]},))
        x.timestamp=pd.Timestamp('2026-03-16')
        with self.assertRaises(ValueError):ProductionExperiment.run_slot(x,[],train_dqn=True)

if __name__=='__main__':unittest.main()
