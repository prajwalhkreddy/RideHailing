import unittest,tempfile
from pathlib import Path
import numpy as np
from tests.test_operational_grid_state import fixture
from tests.test_operational_routing import router
from src.routing.final_state import RoutingState,STATE_FEATURE_ORDER,encode_routing_state
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters,load_final_policy,LocalRoutingLearner
from src.routing.configuration import require_production_configuration,historical_priors

class FinalConfigurationTests(unittest.TestCase):
    def test_exact_order(self):
        r=router();p=fixture();s=RoutingState.from_producer(r,p,p.timestamp,0)
        x=encode_routing_state(s)
        self.assertEqual(len(x),169);self.assertEqual(STATE_FEATURE_ORDER[:3],('STAY.mu','STAY.sigma','STAY.F_hat'))
        self.assertEqual(STATE_FEATURE_ORDER[24:27],('NW.mu','NW.sigma','NW.F_hat'))
        self.assertEqual(STATE_FEATURE_ORDER[27], 'H_hat.Grid_ID_0');self.assertEqual(STATE_FEATURE_ORDER[-1],'H_hat.Grid_ID_141')
        self.assertEqual(sum('H_hat' in f for f in STATE_FEATURE_ORDER),142)
        self.assertFalse(any('fare_count' in f or 'charging_wait' in f for f in STATE_FEATURE_ORDER))
        for i in range(9):np.testing.assert_equal(x[3*i:3*i+3],[10,2,1] if s.mask[i] else [0,0,0])
    def test_required_configuration(self):
        import json
        data=require_production_configuration()
        for key in ('alpha','beta','delta','kappa'):self.assertEqual(data[key]['value'],.3)
        self.assertEqual(data['F_hat_initialization']['value'],0)
        self.assertEqual(data['H_hat_initialization']['value'],0)
        with tempfile.TemporaryDirectory() as d:
            data['delta']['value']=None
            path=Path(d)/'config.json';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'PROJECT_CONFIG_DECISION_REQUIRED'):require_production_configuration(path)
    def test_priors(self):
        with self.assertRaises(ValueError):historical_priors('2026-01-01',F_hat_0=1,H_hat_0=1)
        with self.assertRaises(ValueError):historical_priors('2026-02-01',F_hat_0=None,H_hat_0=1)
        p,t=historical_priors('2026-02-01',F_hat_0=1,H_hat_0=1)
        self.assertEqual(len(p),142);self.assertTrue(np.isfinite(p.to_numpy()).all())
    def test_serialization_and_old_checkpoint(self):
        import tensorflow as tf
        m=build_routing_policy_model(RoutingLearningParameters(),seed=1)
        self.assertEqual(m.input_shape,(None,169));self.assertEqual(m.output_shape,(None,9))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'model.keras';m.save(path);reloaded=load_final_policy(path)
            for a,b in zip(m.get_weights(),reloaded.get_weights()):np.testing.assert_array_equal(a,b)
            old=tf.keras.Sequential([tf.keras.Input((155,)),tf.keras.layers.Dense(64),tf.keras.layers.Dense(32),tf.keras.layers.Dense(9)])
            path=Path(d)/'old.keras';old.save(path)
            with self.assertRaisesRegex(ValueError,'SUPERSEDED'):load_final_policy(path)
    def test_no_legacy_state(self):
        from tests.test_routing_learning import _state
        with self.assertRaisesRegex(ValueError,'Legacy'):encode_routing_state(_state())

if __name__=='__main__':unittest.main()
