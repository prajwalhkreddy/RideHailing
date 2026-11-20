import unittest,tempfile
from pathlib import Path
import numpy as np
import tensorflow as tf
from src.demand.softplus_cnn import build_model
from src.demand.final_cnn import build_model as relu
class SoftplusTests(unittest.TestCase):
 def test_initialization_and_original_compatibility(self):
  mask=np.zeros((16,16),np.float32);mask.flat[:142]=1
  tf.keras.utils.set_random_seed(42);a=relu(mask)
  tf.keras.utils.set_random_seed(42);b=build_model(mask)
  for x,y in zip(a.get_weights(),b.get_weights()):np.testing.assert_array_equal(x,y)
  self.assertEqual(a.get_layer('conv_3').get_config()['activation'],'relu');self.assertEqual(b.get_layer('conv_3').get_config()['activation'],'softplus')
  for name in ['conv_1','conv_2']:self.assertEqual(a.get_layer(name).get_config(),b.get_layer(name).get_config())
 def test_negative_gradient_and_mask(self):
  mask=np.zeros((16,16),np.float32);mask.flat[:142]=1;b=build_model(mask)
  z=tf.Variable(np.full((1,1,16,16),-2.,np.float32))
  with tf.GradientTape() as tape:
   p=b.get_layer('conv_3').activation(z)*mask[None,None];loss=b.loss(tf.ones_like(p),p)
  grad=tape.gradient(loss,z).numpy()[0,0]
  self.assertTrue((grad[mask==1]<0).all());self.assertTrue((grad[mask==0]==0).all())
  out=b(np.ones((2,7,16,16),np.float32)).numpy();self.assertEqual(out.shape,(2,1,16,16));self.assertTrue(np.isfinite(out).all());self.assertTrue((out>=0).all());self.assertFalse(out[:,:,mask==0].any())
 def test_reload_identity(self):
  b=build_model(np.ones((16,16)));x=np.ones((1,7,16,16),np.float32)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'model.keras';b.save(p);c=tf.keras.models.load_model(p,compile=False);np.testing.assert_array_equal(b(x).numpy(),c(x).numpy());self.assertEqual(c.get_layer('conv_3').get_config()['activation'],'softplus')
