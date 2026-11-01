"""Focused checks for the corrected-behavior dataset and frozen baseline models."""
import json,tempfile,unittest
from pathlib import Path
import numpy as np,pandas as pd,pyarrow.parquet as pq
from scripts.train_final_behavioral_routing import CACHE,DATA,MODEL,OUT
from src.routing.learning import load_final_policy
from src.simulation.temporal_protocol import assert_training_update_allowed

class FinalBehavioralTrainingTests(unittest.TestCase):
 def test_complete_chronological_loader(self):
  meta=json.loads((OUT/'dataset_validation.json').read_text());split=json.loads((OUT/'routing_split.json').read_text());self.assertEqual(meta['experiences'],3303289);self.assertEqual(meta['slots'],720);self.assertEqual(split['train_slots'],576);self.assertEqual(split['validation_slots'],144)
  X,M,Y,I=[np.load(CACHE/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']]
  self.assertEqual(X.shape,(3303289,169));self.assertEqual(M.shape,(3303289,9))
  for start in range(0,len(Y),65536):
   x=X[start:start+65536];m=M[start:start+65536];y=Y[start:start+65536];ids=I[start:start+65536]
   self.assertTrue(np.isfinite(x).all());self.assertTrue(((y>=0)&(y<9)).all());self.assertTrue(m[np.arange(len(y)),y].all());self.assertTrue(((ids>=0)&(ids<5000)).all())
  s=pd.read_csv(OUT/'routing_action_support.csv');n=meta['train_n'];np.testing.assert_array_equal(s.train,np.bincount(Y[:n],minlength=9));np.testing.assert_array_equal(s.validation,np.bincount(Y[n:],minlength=9))
  for i,t in [(0,'2026-03-01'),(575,'2026-03-12 23:30'),(576,'2026-03-13'),(719,'2026-03-15 23:30')]:self.assertTrue((pd.read_parquet(DATA/f'slot_{i:04d}.parquet',columns=['timestamp']).timestamp==pd.Timestamp(t)).all())
  with self.assertRaises(ValueError):assert_training_update_allowed('2026-03-16')
 def test_compiled_step_matches_existing_masked_loss(self):
  import tensorflow as tf
  from src.routing.learning import LocalRoutingLearner,RoutingLearningParameters
  from scripts.train_final_behavioral_routing import compiled_step
  p=RoutingLearningParameters();a=LocalRoutingLearner(0,p,seed=42);b=LocalRoutingLearner(0,p,seed=42);b.reset_from_global_weights(a.policy_model.get_weights())
  x=np.load(CACHE/'X.npy',mmap_mode='r')[:32].copy();m=np.load(CACHE/'M.npy',mmap_mode='r')[:32].copy();y=np.load(CACHE/'Y.npy',mmap_mode='r')[:32].copy()
  with tf.GradientTape() as tape:loss=a._batch_loss(tf.constant(x),tf.constant(y),tf.constant(m),training=True)
  a.optimizer.apply_gradients(zip(tape.gradient(loss,a.policy_model.trainable_variables),a.policy_model.trainable_variables));b.optimizer.build(b.policy_model.trainable_variables)
  actual=compiled_step(b.policy_model,b.optimizer)(x,m,y);np.testing.assert_allclose(actual.numpy(),loss.numpy(),rtol=1e-6)
  for wa,wb in zip(a.policy_model.get_weights(),b.policy_model.get_weights()):np.testing.assert_allclose(wa,wb,rtol=1e-5,atol=1e-6)
 def test_models_masking_reload(self):
  n=json.loads((OUT/'dataset_validation.json').read_text())['train_n'];x=np.load(CACHE/'X.npy',mmap_mode='r')[n:n+64];m=np.load(CACHE/'M.npy',mmap_mode='r')[n:n+64]
  for name in ['central.keras','fedavg_round_5.keras']:
   model=load_final_policy(MODEL/name);self.assertEqual((model.input_shape[-1],model.output_shape[-1]),(169,9));z=model(x,training=False).numpy();masked=np.where(m,z,-np.inf);self.assertTrue(m[np.arange(len(m)),masked.argmax(1)].all())
   with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'model.keras';model.save(p);reload=load_final_policy(p);np.testing.assert_array_equal(z,reload(x,training=False).numpy())
 def test_rounds_prior_and_selection(self):
  n=json.loads((OUT/'dataset_validation.json').read_text())['train_n'];h=pd.read_csv(OUT/'fedavg_round_metrics.csv');self.assertEqual(h['round'].tolist(),[1,2,3,4,5]);self.assertTrue((h.training_examples==n).all());self.assertTrue((h.active_participants==5000).all())
  result=json.loads((OUT/'routing_probability_adequacy.json').read_text());Y=np.load(CACHE/'Y.npy',mmap_mode='r');counts=np.bincount(Y[:n],minlength=9);np.testing.assert_allclose(result['training_action_prior'],counts/counts.sum())
  selected=json.loads((OUT/'routing_model_selection.json').read_text());self.assertEqual(selected['FINAL_BEHAVIORAL_ROUTING_MODEL_READY'],'YES');self.assertTrue(selected['checkpoint'].endswith('fedavg_round_5.keras'))
  for name in ['central_validation.json','fedavg_validation.json']:
   v=json.loads((OUT/name).read_text());v=v.get('final_metrics',v);self.assertEqual(v['invalid_action_count'],0);self.assertEqual(v['majority_action_from_training'],int(counts.argmax()));self.assertEqual(v['N'],len(Y)-n)
