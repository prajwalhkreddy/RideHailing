import unittest
import numpy as np,tensorflow as tf
from scripts.train_temporal_routing import local_step,flatten,unpack,P,update_slot
from scripts.train_final_behavioral_routing import compiled_step
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters
class TemporalTests(unittest.TestCase):
 def test_batched_adam_matches_existing_steps(self):
  model=build_routing_policy_model(RoutingLearningParameters(),seed=42);w=flatten(model.get_weights());opt=tf.keras.optimizers.Adam(.001);opt.build(model.trainable_variables);step=compiled_step(model,opt);rng=np.random.default_rng(3);x=rng.normal(size=(1,4,169)).astype('float32');mask=np.ones((1,4,9),bool);y=np.array([[0,3,2,1]],np.int32);m=np.zeros((1,P),np.float32);v=m.copy()
  for t in range(2):
   model.set_weights(unpack(w));loss=step(x[0],mask[0],y[0]);new,m,v,l=local_step(tf.constant(w),tf.constant(x),tf.constant(mask),tf.constant(y),tf.ones((1,4)),tf.constant(m),tf.constant(v),tf.constant([t],tf.int64));np.testing.assert_allclose(new.numpy()[0],flatten(model.get_weights()),rtol=1e-5,atol=2e-7);np.testing.assert_allclose(l.numpy()[0],loss.numpy(),rtol=1e-5);w=new.numpy()[0];m=m.numpy();v=v.numpy()
 def test_temporal_scope_and_equal_aggregation(self):
  model=build_routing_policy_model(RoutingLearningParameters(),seed=42);w=flatten(model.get_weights());rng=np.random.default_rng(4);x=rng.normal(size=(4,169)).astype('float32');mask=np.ones((4,9),bool);y=np.array([0,1,2,3],np.int32);ids=np.array([0,1,0,2]);slots=np.array([0,0,1,2]);m=np.zeros((3,P),np.float32);v=m.copy();it=np.zeros(3,np.int64);history=[[],[],[]]
  z,r=update_slot(0,w,m,v,it,history,ids,slots,x,mask,y,batch_clients=2);self.assertEqual(r['participants'],2);self.assertEqual(r['aggregation_weight_total'],2);self.assertEqual(history,[[0],[1],[]]);self.assertEqual(r['model_available_slot'],1);np.testing.assert_array_equal(it,[1,1,0]);before=z.copy()
  z,r=update_slot(1,z,m,v,it,history,ids,slots,x,mask,y,batch_clients=2);self.assertEqual(r['participants'],1);self.assertEqual(r['local_examples'],2);self.assertEqual(r['max_source_slot'],1);self.assertEqual(history[2],[]);np.testing.assert_array_equal(it,[2,1,0])
 def test_parallel_clients_equal_independent_average(self):
  model=build_routing_policy_model(RoutingLearningParameters(),seed=42);w=flatten(model.get_weights());rng=np.random.default_rng(8);x=rng.normal(size=(2,3,169)).astype('float32');mask=np.ones((2,3,9),bool);y=np.array([[0,1,2],[2,4,5]],np.int32);z=np.zeros((2,P),np.float32)
  both=local_step(tf.constant(w),tf.constant(x),tf.constant(mask),tf.constant(y),tf.ones((2,3)),tf.constant(z),tf.constant(z),tf.zeros(2,tf.int64))[0].numpy();individual=[]
  for i in range(2):
   a=local_step(tf.constant(w),tf.constant(x[i:i+1]),tf.constant(mask[i:i+1]),tf.constant(y[i:i+1]),tf.ones((1,3)),tf.constant(z[:1]),tf.constant(z[:1]),tf.zeros(1,tf.int64))[0].numpy()[0];individual.append(a)
  np.testing.assert_allclose(both.astype(float).mean(0),np.array(individual).astype(float).mean(0),rtol=1e-5,atol=2e-7)
if __name__=='__main__':unittest.main()
