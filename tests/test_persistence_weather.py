import unittest
import numpy as np
import pandas as pd
from tests.test_cnn_causal_timing import fixture
from src.demand.persistence_weather import *

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.meta=contract(120)
        self.weather=pd.DataFrame(dict(Datetime=pd.date_range('2025-12-31',periods=72,freq='h'),WeatherCode=1.,Temperature=np.arange(72,dtype=float),WindSpeed=3.))
    def test_availability_age_and_no_target_leakage(self):
        a=select_weather(self.weather,['2026-01-01 00:00'],self.meta)
        self.assertEqual(a.observation_age_minutes.iloc[0],150)
        self.assertLessEqual(a.assumed_available_at.iloc[0],a.issued_at.iloc[0])
        changed=self.weather.copy();changed.loc[changed.Datetime>='2026-01-01 03:00','Temperature']=9999
        pd.testing.assert_frame_equal(a,select_weather(changed,['2026-01-01 00:00'],self.meta))
    def test_missing_and_fallback(self):
        self.weather.loc[self.weather.Datetime=='2026-01-01 02:00','Temperature']=np.nan
        a=select_weather(self.weather,['2026-01-01'],self.meta)
        self.assertEqual(a.observation_age_minutes.iloc[0],210)
        with self.assertRaises(ValueError):select_weather(self.weather,['2025-12-30'],self.meta)
    def test_dst(self):
        w=self.weather.copy();w.Datetime=pd.date_range('2026-03-07',periods=72,freq='h')
        a=select_weather(w,['2026-03-08 03:00'],self.meta)
        self.assertEqual(a.issued_at.iloc[0].isoformat(),'2026-03-08T01:30:00-05:00')
        self.assertEqual(a.observation_time.iloc[0].isoformat(),'2026-03-08T04:00:00+00:00')
    def test_tensor_and_determinism(self):
        d,g=fixture();x,y,s,b=build_persistence(d,g,self.weather,self.meta)
        xx,yy,ss,bb=build_persistence(d,g,self.weather,self.meta)
        np.testing.assert_array_equal(x,xx);np.testing.assert_array_equal(y,yy)
        self.assertEqual(x.shape,(6,7,16,16));self.assertEqual(len(b),0)
        self.assertTrue((s.weather_mode==VERSION).all())
        mask=np.zeros((16,16),bool);mask[g.Row,g.Column]=True;self.assertFalse(x[:,:,~mask].any())
    def test_checkpoint_od_and_operational_rejection(self):
        selected=select_weather(self.weather,['2026-01-01'],self.meta)
        frame=pd.concat([selected]*142,ignore_index=True);frame['Grid_ID']=range(142);frame['predicted_demand']=.125
        ck=dict(version=VERSION,weather_contract_sha256=fingerprint(self.meta))
        self.assertEqual(validate_persistence_forecast(frame,self.meta,ck,'2026-01-01',research=True)[0],.125)
        for bad in [{},dict(version=ORACLE,weather_contract_sha256=fingerprint(self.meta))]:
            with self.assertRaises(ValueError):validate_persistence_forecast(frame,self.meta,bad,'2026-01-01',research=True)
        with self.assertRaises(ValueError):validate_persistence_forecast(frame,self.meta,ck,'2026-01-01')
        with self.assertRaises(ValueError):validate_persistence_forecast(frame,self.meta,ck,'2026-01-01 00:30',research=True)
        frame['assumed_available_at']=frame.target_start
        with self.assertRaises(ValueError):validate_persistence_forecast(frame,self.meta,ck,'2026-01-01',research=True)
    def test_invalid_contract(self):
        with self.assertRaises(ValueError):contract(0)
        with self.assertRaises(ValueError):select_weather(self.weather,['2026-01-01'],dict(self.meta,version=ORACLE))
