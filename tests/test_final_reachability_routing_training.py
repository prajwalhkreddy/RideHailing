"""Focused checks of the final real-data routing training pipeline."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import tensorflow as tf
from scripts.train_final_reachability_routing import CACHE, DATA, MODEL, OUT, compiled_step
from src.routing.learning import LocalRoutingLearner, RoutingLearningParameters, load_final_policy
from src.simulation.temporal_protocol import assert_training_update_allowed

class FinalRoutingTrainingTests(unittest.TestCase):
    def test_complete_cached_loader_and_chronological_boundary(self):
        meta=json.loads((OUT/'dataset_validation.json').read_text())
        self.assertEqual(meta['experiences'],3257840)
        self.assertEqual(meta['slots'],720)
        self.assertEqual(meta['train_n'],2618033)
        self.assertEqual(meta['validation_n'],639807)
        x,m,y,ids=[np.load(CACHE/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']]
        self.assertEqual(x.shape,(3257840,169));self.assertEqual(m.shape,(3257840,9))
        for j in range(0,len(y),65536):
            z=slice(j,j+65536)
            self.assertTrue(np.isfinite(x[z]).all())
            self.assertTrue(((ids[z]>=0)&(ids[z]<5000)).all())
            self.assertTrue(((y[z]>=0)&(y[z]<9)).all())
            self.assertTrue(m[z][np.arange(len(y[z])),y[z]].all())
        counts=pd.read_csv(OUT/'routing_action_support.csv')
        np.testing.assert_array_equal(counts.train,np.bincount(y[:meta['train_n']],minlength=9))
        np.testing.assert_array_equal(counts.validation,np.bincount(y[meta['train_n']:],minlength=9))
        for slot,expected in [(0,'2026-03-01'),(575,'2026-03-12 23:30'),(576,'2026-03-13'),(719,'2026-03-15 23:30')]:
            f=pq.read_table(DATA/f'slot_{slot:04d}.parquet',columns=['timestamp']).to_pandas()
            self.assertTrue((f.timestamp==pd.Timestamp(expected)).all())
        with self.assertRaises(ValueError):assert_training_update_allowed('2026-03-17')

    def test_compiled_update_matches_existing_eager_masked_loss(self):
        params=RoutingLearningParameters();eager=LocalRoutingLearner(0,params,seed=42);compiled=LocalRoutingLearner(0,params,seed=42)
        compiled.reset_from_global_weights(eager.policy_model.get_weights())
        x=np.load(CACHE/'X.npy',mmap_mode='r')[:32].copy();m=np.load(CACHE/'M.npy',mmap_mode='r')[:32].copy();y=np.load(CACHE/'Y.npy',mmap_mode='r')[:32].copy()
        with tf.GradientTape() as tape:
            loss=eager._batch_loss(tf.constant(x),tf.constant(y),tf.constant(m),training=True)
        eager.optimizer.apply_gradients(zip(tape.gradient(loss,eager.policy_model.trainable_variables),eager.policy_model.trainable_variables))
        compiled.optimizer.build(compiled.policy_model.trainable_variables)
        actual=compiled_step(compiled.policy_model,compiled.optimizer)(x,m,y)
        np.testing.assert_allclose(actual.numpy(),loss.numpy(),rtol=1e-6)
        for a,b in zip(eager.policy_model.get_weights(),compiled.policy_model.get_weights()):np.testing.assert_allclose(a,b,rtol=1e-5,atol=1e-6)

    def test_checkpoint_reload_and_masked_predictions(self):
        model=load_final_policy(MODEL/'central.keras')
        self.assertEqual(model.input_shape[-1],169);self.assertEqual(model.output_shape[-1],9)
        n=json.loads((OUT/'dataset_validation.json').read_text())['train_n']
        x=np.load(CACHE/'X.npy',mmap_mode='r')[n:n+64];m=np.load(CACHE/'M.npy',mmap_mode='r')[n:n+64]
        logits=model(x,training=False).numpy()
        probs=tf.nn.softmax(np.where(m,logits,-np.inf)).numpy()
        self.assertTrue(np.isfinite(probs).all());self.assertTrue((probs[~m]==0).all())
        self.assertTrue(m[np.arange(len(m)),probs.argmax(1)].all())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'model.keras';model.save(path);loaded=load_final_policy(path)
            np.testing.assert_array_equal(logits,loaded(x,training=False).numpy())
        # Central resume checkpoints preserve Adam's iteration and slot state.
        original=tf.keras.models.load_model(MODEL/'central.keras')
        self.assertEqual(int(original.optimizer.iterations.numpy()),(n+31)//32)

    def test_selected_aggregate_contract(self):
        selection=json.loads((OUT/'routing_model_selection.json').read_text())
        self.assertEqual(selection['status'],'SIMULATOR_DERIVED_ROUTING_BASELINE')
        self.assertTrue(selection['checkpoint'].endswith('fedavg_round_5.keras'))
        model=load_final_policy(MODEL/'fedavg_round_5.keras')
        self.assertEqual(model.input_shape[-1],169);self.assertEqual(model.output_shape[-1],9)
        history=pd.read_csv(OUT/'fedavg_round_metrics.csv')
        self.assertEqual(history['round'].tolist(),[1,2,3,4,5])
        self.assertTrue((history.active_participants==5000).all())
        self.assertTrue((history.training_examples==2618033).all())
        metrics=json.loads((OUT/'routing_validation_metrics.json').read_text())
        counts=pd.read_csv(OUT/'routing_action_support.csv')
        for name in ['central','final_fedavg']:
            result=metrics[name]
            self.assertEqual(result['N'],639807)
            self.assertEqual(result['invalid_action_count'],0)
            self.assertEqual(result['valid_action_prediction_rate'],1.)
            self.assertTrue(np.isfinite(result['cross_entropy']))
            np.testing.assert_array_equal(result['action_support'],counts.validation)
            self.assertEqual(sum(result['predicted_counts']),639807)
        n=2618033
        x=np.load(CACHE/'X.npy',mmap_mode='r')[n:n+64];m=np.load(CACHE/'M.npy',mmap_mode='r')[n:n+64]
        probs=tf.nn.softmax(np.where(m,model(x,training=False).numpy(),-np.inf)).numpy()
        self.assertTrue(np.isfinite(probs).all());self.assertTrue((probs[~m]==0).all())
        self.assertTrue(m[np.arange(len(m)),probs.argmax(1)].all())

if __name__=='__main__':unittest.main()
