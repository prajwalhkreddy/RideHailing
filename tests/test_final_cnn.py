"""Focused final forecast-time CNN tests; no training in this suite."""
import unittest
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import tensorflow as tf
from src.demand.final_cnn import *
D=Path('data/processed/cnn_jan_mar_2026_3km_30min')
R=Path('results/analysis/2026-10-19_final_jan_mar_3km_cnn')
class FinalCNNTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d=pd.read_parquet('data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet')
  cls.grid=gpd.read_parquet('data/processed/grid_lookup.parquet')
  cls.lookup=pd.read_parquet(D/'historical_average_demand.parquet')
  cls.slot=pd.read_parquet(D/'historical_average_slot_fallback.parquet')
  cls.overall=pd.read_parquet(D/'historical_average_grid_fallback.parquet')
  cls.config=json.loads((D/'preprocessing_config.json').read_text())
  cls.mask=np.load(D/'valid_mask.npy')
 def test_source_and_grid(self):validate_source(self.d,self.grid)
 def test_partitions_and_shapes(self):
  for name,n in [('train',2832),('validation',720),('test',768)]:
   x=np.load(D/f'X_{name}.npy',mmap_mode='r');y=np.load(D/f'Y_{name}.npy',mmap_mode='r')
   t=pd.DatetimeIndex(np.load(D/f'forecast_timestamp_{name}.npy'))
   self.assertEqual(x.shape,(n,7,16,16));self.assertEqual(y.shape,(n,1,16,16))
   a,b=SPLITS[name];self.assertTrue(t.equals(pd.date_range(a,b,freq='30min',inclusive='left')))
   self.assertTrue(np.isfinite(x).all());self.assertFalse(x[:,:,self.mask==0].any());self.assertFalse(y[:,:,self.mask==0].any())
 def test_exact_feature_order_and_time_weather(self):
  self.assertEqual(CHANNELS,('DayOfWeek','Hour','PeriodWithinHour','WeatherType','Temperature','WindSpeed','HistoricalAverageDemandDistribution'))
  t=pd.Timestamp('2026-03-16 14:30');sample=self.d.loc[self.d.TimeSlot==t]
  x,y,h,times=tensors(sample,self.lookup,self.slot,self.overall,self.config)
  self.assertEqual(times[0],t)
  values=x[0,:,int(sample.iloc[0].Row),int(sample.iloc[0].Column)]
  expected=[t.dayofweek/6,t.hour/23,1,sample.iloc[0].WeatherCode/27]
  np.testing.assert_allclose(values[:4],expected,rtol=1e-6)
  for idx,col in [(4,'Temperature'),(5,'WindSpeed')]:
   sc=self.config['scalers'][col];self.assertAlmostEqual(float(values[idx]),(sample.iloc[0][col]-sc['mean'])/sc['std'],places=5)
 def test_no_target_shift(self):
  for name in SPLITS:
   y=np.load(D/f'Y_{name}.npy',mmap_mode='r');times=pd.DatetimeIndex(np.load(D/f'forecast_timestamp_{name}.npy'))
   expected=self.d.groupby('TimeSlot').Demand.sum().reindex(times)
   np.testing.assert_array_equal(y.sum(axis=(1,2,3)),expected.to_numpy())
 def test_train_only_fit_and_heldout_target_perturbation(self):
  changed=self.d.copy();changed.loc[changed.TimeSlot>=TRAIN_END,['Demand','Temperature','WindSpeed']]=999999
  l,s,o,season,c=fit_preprocessing(changed)
  pd.testing.assert_frame_equal(l,self.lookup);pd.testing.assert_frame_equal(s,self.slot);pd.testing.assert_frame_equal(o,self.overall)
  self.assertEqual(c['scalers'],self.config['scalers'])
 def test_grid_specific_lookup_and_fallbacks(self):
  train=self.d.loc[self.d.TimeSlot<TRAIN_END].copy();train['slot_of_day']=train.Hour*2+train.PeriodWithinHour
  expected=train.groupby(['GridID','DayOfWeek','slot_of_day']).Demand.mean().rename('historical_average').reset_index()
  pd.testing.assert_frame_equal(expected,self.lookup)
  sample=self.d.iloc[:142]
  raw=raw_features(sample,self.lookup.iloc[:0],self.slot,self.overall)
  expected=self.slot.loc[self.slot.slot_of_day==0].sort_values('GridID').slot_average
  np.testing.assert_allclose(raw[:,-1],expected,rtol=1e-6)
  raw=raw_features(sample,self.lookup.iloc[:0],self.slot.iloc[:0],self.overall)
  np.testing.assert_allclose(raw[:,-1],self.overall.grid_average,rtol=1e-6)
 def test_no_target_in_feature_transform(self):
  sample=self.d.iloc[-142:].copy();x,*_=tensors(sample,self.lookup,self.slot,self.overall,self.config)
  sample.Demand=999999;y,*_=tensors(sample,self.lookup,self.slot,self.overall,self.config)
  np.testing.assert_array_equal(x,y)
 def test_model_contract_and_loss_mask(self):
  model=build_model(self.mask)
  conv=[l for l in model.layers if isinstance(l,keras.layers.Conv2D)]
  self.assertEqual([l.filters for l in conv],[14,7,1])
  self.assertTrue(all(l.kernel_size==(3,3) and l.padding=='same' and l.activation==keras.activations.relu for l in conv))
  out=model(np.zeros((2,7,16,16),dtype='float32')).numpy()
  self.assertEqual(out.shape,(2,1,16,16));self.assertTrue((out>=0).all());self.assertFalse(out[:,:,self.mask==0].any())
  truth=np.zeros_like(out);pred=np.ones_like(out);loss=MaskedMSE(self.mask)
  self.assertAlmostEqual(float(loss(truth,pred)),1.)
  pred[:,:,self.mask==0]=10000
  self.assertAlmostEqual(float(loss(truth,pred)),1.)
 def test_saved_forecast_contract(self):
  f=pd.read_parquet(R/'dqn_ready_forecasts.parquet')
  self.assertEqual(len(f),768*142);self.assertEqual(f.forecast_timestamp.nunique(),768)
  self.assertEqual(set(f.Grid_ID),set(range(142)))
  self.assertFalse(f[['forecast_timestamp','Grid_ID']].duplicated().any())
  self.assertTrue(np.isfinite(f.predicted_demand).all());self.assertTrue(f.predicted_demand.ge(0).all())
  self.assertTrue((f.groupby('forecast_timestamp').Grid_ID.nunique()==142).all())
  expected=pd.date_range(VAL_END,END,freq='30min',inclusive='left')
  self.assertTrue(pd.DatetimeIndex(f.forecast_timestamp.drop_duplicates()).equals(expected))
 def test_saved_metrics_reproduce_without_second_inference(self):
  f=pd.read_parquet(R/'test_predictions.parquet');m=json.loads((R/'metrics.json').read_text())
  error=f.predicted_demand.to_numpy(dtype=float)-f.observed_demand.to_numpy(dtype=float)
  self.assertAlmostEqual(abs(error).mean(),m['test']['MAE'])
  self.assertAlmostEqual(np.sqrt((error**2).mean()),m['test']['RMSE'])
  self.assertEqual(m['test_evaluations'],1)
 def test_frozen_inference_interface_and_wrong_grid_rejection(self):
  predictor=FinalDemandPredictor('models/cnn/jan_mar_2026_3km_30min',D)
  # Synthetic future input; no repeated TEST evaluation or target use.
  sample=self.d.iloc[:142].copy();sample.TimeSlot=pd.Timestamp('2026-04-01');sample.Demand=0
  f=predictor.predict(sample,self.grid)
  self.assertEqual(f.columns.tolist(),['forecast_timestamp','Grid_ID','predicted_demand'])
  self.assertEqual(len(f),142);self.assertTrue(np.isfinite(f.predicted_demand).all())
  wrong=self.grid.copy();wrong.loc[0,'Row']=99
  with self.assertRaisesRegex(ValueError,'grid'):predictor.predict(sample,wrong)
 def test_weather_source_required_no_imputation_and_frozen_scalers(self):
  for month in ['01','02','03']:
   meta=json.loads(Path(f'data/processed/weather/weather_metadata_2026_{month}.json').read_text())
   self.assertTrue(all(v==0 for v in meta['missing_values']['before_fill'].values()))
  train=self.d.loc[self.d.TimeSlot<TRAIN_END].drop_duplicates('TimeSlot')
  for name in ['Temperature','WindSpeed']:
   self.assertAlmostEqual(self.config['scalers'][name]['mean'],train[name].mean())
   self.assertAlmostEqual(self.config['scalers'][name]['std'],train[name].std(ddof=0))
