import unittest
import pickle
import numpy as np
from src.routing.privacy import account, solve_multiplier, clip_updates, noisy_mean

class PrivacyTests(unittest.TestCase):
    def test_accounting_and_targets(self):
        for target in [8,4,2]:
            s=solve_multiplier(target)
            a=account(s,576)
            self.assertAlmostEqual(a['epsilon'],target,places=10)
            np.testing.assert_allclose(a['cumulative_RDP'],576*np.array(a['per_round_RDP']))
            self.assertLess(account(s,575)['epsilon'],a['epsilon'])
        self.assertAlmostEqual(account(3,7,orders=[2])['cumulative_RDP'][0],7/9)
    def test_replacement_sensitivity_and_clipping(self):
        v,n=clip_updates([[3,4],[0,0],[-3,-4]])
        np.testing.assert_allclose(n,[5,0,5])
        np.testing.assert_allclose(np.linalg.norm(v,axis=1),[1,0,1])
        self.assertAlmostEqual(np.linalg.norm(v[0]-v[2])/7,2/7)
    def test_noise_scale_and_deterministic_private_resume(self):
        class Capture:
            def normal(self,loc,scale,size):
                self.scale=scale;return np.zeros(size)
        r=Capture();np.testing.assert_array_equal(noisy_mean(np.array([6.,9.]),3,4,r),[2,3]);self.assertAlmostEqual(r.scale,8/3)
        rng=np.random.default_rng(123);state=pickle.loads(pickle.dumps(rng.bit_generator.state));a=noisy_mean(np.zeros(10),7,4,rng)
        restored=np.random.default_rng();restored.bit_generator.state=state
        np.testing.assert_array_equal(a,noisy_mean(np.zeros(10),7,4,restored))
    def test_dp_boundary_preserves_local_optimizer_and_chronology(self):
        from scripts.train_temporal_routing import update_slot,flatten,P
        from scripts.train_dp_temporal_routing import update
        from src.routing.learning import build_routing_policy_model,RoutingLearningParameters
        model=build_routing_policy_model(RoutingLearningParameters(),seed=42)
        w=flatten(model.get_weights()); rng=np.random.default_rng(5)
        X=rng.normal(size=(4,169)).astype('float32');M=np.ones((4,9),bool);Y=np.array([0,1,2,3],np.int32)
        ids=np.array([0,1,0,2]);slots=np.array([0,0,1,2])
        class NoNoise:
            def normal(self,loc,scale,size):return np.zeros(size)
        a=[np.zeros((3,P),np.float32),np.zeros((3,P),np.float32),np.zeros(3,np.int64),[[],[],[]]]
        b=[x.copy() if isinstance(x,np.ndarray) else [h.copy() for h in x] for x in a]
        expected,_=update_slot(0,w,*a,ids,slots,X,M,Y,batch_clients=64)
        actual,row,norms=update(0,w,*b,ids,slots,X,M,Y,1.,NoNoise())
        self.assertTrue((norms<1).all())
        np.testing.assert_allclose(actual,expected,rtol=1e-6,atol=3e-8)
        for x,y in zip(a[:3],b[:3]):np.testing.assert_array_equal(x,y)
        self.assertEqual(a[3],b[3]);self.assertEqual(row['model_available_slot'],1)
        with self.assertRaises(ValueError):update(576,w,*b,ids,slots,X,M,Y,1.,NoNoise())

    def test_cross_entropy_uses_log_space_without_clipping(self):
        import tensorflow as tf
        from scripts.train_dp_temporal_routing import metrics
        class ExtremeLogits:
            def __call__(self,x,training=False):
                return tf.constant([[-1000.,1000.,0,0,0,0,0,0,0],[1000.,-1000.,0,0,0,0,0,0,0]])
        values,actions=metrics(ExtremeLogits(),np.zeros((2,169)),np.ones((2,9),bool),np.array([0,1]),'TEST')
        self.assertEqual(values['CE'],2000.)
        self.assertEqual(values['Brier'],2.)
        self.assertEqual(values['invalid_action_count'],0)

    def test_invalid_inputs_rejected(self):
        for v in [0,-1,np.inf,np.nan]:
            with self.assertRaises(ValueError): account(v,576)
        with self.assertRaises(ValueError): clip_updates([[np.nan]])
        with self.assertRaises(ValueError): account(3,1,orders=[1])

if __name__=='__main__':unittest.main()
