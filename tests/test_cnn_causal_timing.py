import unittest
import numpy as np
import pandas as pd
from src.demand.causal_timing import *

def fixture(times=None):
 g=pd.DataFrame({'GridID':range(142),'Row':np.arange(142)//16,'Column':np.arange(142)%16})
 times=pd.date_range('2026-01-01',periods=6,freq='30min') if times is None else pd.DatetimeIndex(times)
 rows=[]
 for i,t in enumerate(times):
  for row in g.itertuples(index=False):rows.append(dict(TimeSlot=t,GridID=row.GridID,Row=row.Row,Column=row.Column,Demand=float(i+row.GridID),WeatherCode=1,Temperature=2.,WindSpeed=3.))
 return pd.DataFrame(rows),g

class CausalTimingTests(unittest.TestCase):
 def test_no_future_or_self_inclusion(self):
  d,g=fixture();x,y,t,_=build_oracle(d,g);changed=d.copy();changed.loc[changed.TimeSlot>=pd.Timestamp('2026-01-01 01:00'),'Demand']=1e8;changed.loc[changed.TimeSlot>pd.Timestamp('2026-01-01 01:00'),'Temperature']=1e6
  xx,_,_,_=build_oracle(changed,g);np.testing.assert_array_equal(x[:3],xx[:3]);self.assertEqual(list(t.history_training_slots[:3]),[0,0,1]);self.assertEqual(list(t.eligible[:3]),[False,False,True])
 def test_validation_targets_never_fit(self):
  d,g=fixture(['2026-02-28 22:00','2026-02-28 22:30','2026-03-01','2026-03-01 00:30','2026-03-16']);x,_,_,_=build_oracle(d,g);d.loc[d.TimeSlot>='2026-03-01','Demand']=1e9;xx,_,_,_=build_oracle(d,g);np.testing.assert_array_equal(x,xx)
 def test_dst_elapsed_and_quarantine(self):
  t=timing('2026-03-08 03:00');self.assertEqual(t['issued_at'].hour,1);self.assertEqual(t['issued_at'].minute,30);self.assertEqual(t['target_start']-t['issued_at'],STEP)
  with self.assertRaises(Exception):civil('2026-03-08 02:00')
  d,g=fixture(['2026-03-08 01:30','2026-03-08 02:00','2026-03-08 02:30','2026-03-08 03:00']);x,_,t,bad=build_oracle(d,g);self.assertEqual(len(bad),284);self.assertEqual(len(t),2)
 def test_shape_mask_and_determinism(self):
  d,g=fixture();x,y,t,_=build_oracle(d,g);xx,yy,tt,_=build_oracle(d,g);np.testing.assert_array_equal(x,xx);np.testing.assert_array_equal(y,yy);pd.testing.assert_frame_equal(t,tt)
  self.assertEqual(x.shape,(6,7,16,16));mask=np.zeros((16,16),bool);mask[g.Row,g.Column]=True;self.assertFalse(x[:,:,~mask].any());self.assertFalse(y[:,:,~mask].any());self.assertEqual(float(y.sum()),float(d.Demand.sum()))
 def test_forecast_interface_and_oracle_rejection(self):
  meta=dict(version=VERSION,timezone=ZONE);t=timing('2026-03-12 00:30');f=pd.DataFrame(dict(Grid_ID=range(142),predicted_demand=[.25]*142,**{k:[v]*142 for k,v in t.items()}))
  self.assertEqual(validate_forecast(f,meta,'2026-03-12 00:30',operational=False)[0],.25)
  with self.assertRaises(ValueError):validate_forecast(f,meta,'2026-03-12 00:30')
  with self.assertRaises(ValueError):validate_forecast(f,meta,'2026-03-12 01:00',operational=False)
  with self.assertRaises(ValueError):validate_forecast(f,{},'2026-03-12 00:30',operational=False)
  dst=timing('2026-03-08 03:00');df=pd.DataFrame(dict(Grid_ID=range(142),predicted_demand=[.25]*142,**{k:[v]*142 for k,v in dst.items()}))
  with self.assertRaisesRegex(ValueError,'DST'):validate_forecast(df,meta,'2026-03-08 03:00',operational=False)
  f['predicted_demand']=-1
  with self.assertRaises(ValueError):validate_forecast(f,meta,'2026-03-12 00:30',operational=False)
 def test_weather_missing_and_geometry_reject(self):
  d,g=fixture();d.loc[0,'Temperature']=np.nan
  with self.assertRaises(ValueError):build_oracle(d,g)
  d,g=fixture();d.loc[0,'Row']=15
  with self.assertRaises(ValueError):build_oracle(d,g)
