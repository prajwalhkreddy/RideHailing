import unittest
import numpy as np
import pandas as pd
from src.pricing.binned_sensitivity import binned_elasticity,require_runtime_approved,VERSION,historical_pool

class BinnedEstimatorTests(unittest.TestCase):
    def test_formula_and_mean(self):
        f=pd.DataFrame({'distance_km':[1.6,1.7],'fare':[10.,14.]})
        r=binned_elasticity(f,p_base=20.,l_base=2.).iloc[0]
        self.assertEqual(r.bin_lower_km,1.5);self.assertEqual(r.mean_fare,12.)
        self.assertEqual(r.n_requests,2);self.assertAlmostEqual(r.epsilon,.625)
    def test_edges(self):
        f=pd.DataFrame({'distance_km':[1.999,2.,2.5],'fare':[10.]*3})
        self.assertEqual(list(binned_elasticity(f,p_base=20.,l_base=3.).bin_lower_km),[1.5,2.,2.5])
    def test_common_references(self):
        f=pd.DataFrame({'distance_km':[2.,3.],'fare':[10.,30.],'group':['a','b']})
        r=binned_elasticity(f,p_base=20.,l_base=2.5,group_columns=['group'])
        self.assertEqual(list(r.P_base),[20.,20.]);self.assertEqual(list(r.L_base_km),[2.5,2.5])
    def test_exact_zero_and_near_zero(self):
        f=pd.DataFrame({'distance_km':[1.5,2.5],'fare':[20.,20.00002]})
        r=binned_elasticity(f,p_base=20.,l_base=3.)
        self.assertTrue(np.isnan(r.epsilon.iloc[0]));self.assertEqual(r.status.iloc[0],'UNDEFINED_EXACT_ZERO_PRICE_DENOMINATOR')
        self.assertTrue(np.isfinite(r.epsilon.iloc[1]));self.assertGreater(abs(r.epsilon.iloc[1]),100000)
    def test_negative_and_zero_not_silently_removed(self):
        r=binned_elasticity(pd.DataFrame({'distance_km':[1.5,2.],'fare':[30.,30.]}),p_base=20.,l_base=2.)
        self.assertEqual(list(r.status),['NEGATIVE_ELASTICITY','ZERO_ELASTICITY'])
    def test_provisional_cannot_activate(self):
        for approved in (False,True):
            with self.assertRaises(ValueError):require_runtime_approved(dict(version=VERSION,runtime_approved=approved))
    def test_invalid_source_and_references(self):
        f=pd.DataFrame({'distance_km':[2.],'fare':[float('nan')]})
        with self.assertRaises(ValueError):binned_elasticity(f,p_base=20.,l_base=2.)
        with self.assertRaises(ValueError):binned_elasticity(f,p_base=0.,l_base=2.)

class HistoricalPoolTests(unittest.TestCase):
    def test_raw_pool_spans_time_and_time_pool_spans_weather(self):
        f=pd.DataFrame({'weather_code':[13,13,1],'T_group':['T1','T3','T1']})
        self.assertEqual(len(historical_pool(f,'RAW_13',{})),2)
        self.assertEqual(len(historical_pool(f,'T1_POOLED',{})),2)
        self.assertEqual(len(historical_pool(f,'T1_G1',{(1,'T1'):'T1_G1'})),1)
        with self.assertRaises(ValueError):historical_pool(f,'UNDEFINED',{})
