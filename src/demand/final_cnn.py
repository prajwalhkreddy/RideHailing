"""Final true-3km Jan–Mar forecast-time CNN contract; isolated from legacy NB5."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras

CHANNELS = ('DayOfWeek','Hour','PeriodWithinHour','WeatherType','Temperature','WindSpeed','HistoricalAverageDemandDistribution')
START=pd.Timestamp('2026-01-01'); TRAIN_END=pd.Timestamp('2026-03-01'); VAL_END=pd.Timestamp('2026-03-16'); END=pd.Timestamp('2026-04-01')
SPLITS={'train':(START,TRAIN_END),'validation':(TRAIN_END,VAL_END),'test':(VAL_END,END)}

def validate_source(d, grid):
    slots=pd.date_range(START,END,freq='30min',inclusive='left')
    assert len(grid)==142 and set(grid.GridID)==set(range(142))
    assert grid.crs.to_epsg()==32118 and grid[['Row','Column']].max().tolist()==[15,15]
    bounds=grid.geometry.bounds
    np.testing.assert_allclose(bounds.maxx-bounds.minx,3000,rtol=0,atol=1e-6)
    np.testing.assert_allclose(bounds.maxy-bounds.miny,3000,rtol=0,atol=1e-6)
    assert len(d)==613440 and not d[['TimeSlot','GridID']].duplicated().any()
    assert pd.DatetimeIndex(sorted(d.TimeSlot.unique())).equals(slots)
    assert (d.groupby('TimeSlot').GridID.nunique()==142).all()
    assert set(d.GridID)==set(range(142))
    assert d.groupby(d.TimeSlot.dt.month).Demand.sum().to_dict()=={1:3699644,2:3377979,3:3928571}
    assert (d.Demand>=0).all() and np.isfinite(d.select_dtypes('number')).all().all()
    positions=grid.set_index('GridID')
    assert (d.Row.to_numpy()==positions.loc[d.GridID,'Row'].to_numpy()).all()
    assert (d.Column.to_numpy()==positions.loc[d.GridID,'Column'].to_numpy()).all()
    assert (d.groupby('TimeSlot')[['Temperature','WindSpeed','WeatherCode']].nunique()==1).all().all()
    assert (d.DayOfWeek==d.TimeSlot.dt.dayofweek).all()
    assert (d.Hour==d.TimeSlot.dt.hour).all()
    assert (d.PeriodWithinHour==d.TimeSlot.dt.minute//30).all()


def fit_preprocessing(d):
    train=d.loc[d.TimeSlot.ge(START)&d.TimeSlot.lt(TRAIN_END)].copy()
    train['slot_of_day']=train.Hour*2+train.PeriodWithinHour
    lookup=train.groupby(['GridID','DayOfWeek','slot_of_day']).Demand.mean().rename('historical_average').reset_index()
    slot=train.groupby(['GridID','slot_of_day']).Demand.mean().rename('slot_average').reset_index()
    overall=train.groupby('GridID').Demand.mean().rename('grid_average').reset_index()
    temporal=train.drop_duplicates('TimeSlot')
    scalers={}
    for col in ['Temperature','WindSpeed']:
        scalers[col]={'mean':float(temporal[col].mean()),'std':float(temporal[col].std(ddof=0)) or 1.0}
    raw=raw_features(train,lookup,slot,overall)
    scalers['HistoricalAverageDemandDistribution']={'scale':float(raw[:,-1].std()) or 1.0}
    config={'fit_start':str(START),'fit_end_exclusive':str(TRAIN_END),'fit_slots':2832,
            'scalers':scalers,'imputation':'None: all source weather values present; fail on missing values',
            'encoding':{'DayOfWeek':'Monday=0 through Sunday=6, divided by6','Hour':'forecast hour/23',
                        'PeriodWithinHour':'minute00=0, minute30=1','WeatherType':'original Meteostat numeric code /27; deterministic legacy one-plane representation',
                        'Temperature':'TRAIN hourly mean/std z-score','WindSpeed':'TRAIN hourly mean/std z-score',
                        'HistoricalAverageDemandDistribution':'TRAIN group mean, divided by TRAIN historical-plane population SD'},
            'fallback':['GridID+weekday+half-hour-of-day TRAIN mean','GridID+half-hour-of-day TRAIN mean','GridID TRAIN mean','zero only without TRAIN history']}
    seasonal=train.groupby(['DayOfWeek','slot_of_day']).Demand.mean().rename('seasonal_average').reset_index()
    return lookup,slot,overall,seasonal,config


def raw_features(d,lookup,slot,overall):
    work=d[['GridID','TimeSlot','WeatherCode','Temperature','WindSpeed']].copy()
    work['DayOfWeek']=work.TimeSlot.dt.dayofweek;work['Hour']=work.TimeSlot.dt.hour
    work['PeriodWithinHour']=work.TimeSlot.dt.minute//30;work['slot_of_day']=work.Hour*2+work.PeriodWithinHour
    work=work.merge(lookup,on=['GridID','DayOfWeek','slot_of_day'],how='left',sort=False,validate='many_to_one')
    work=work.merge(slot,on=['GridID','slot_of_day'],how='left',sort=False,validate='many_to_one')
    work=work.merge(overall,on='GridID',how='left',sort=False,validate='many_to_one')
    h=work.historical_average.fillna(work.slot_average).fillna(work.grid_average).fillna(0)
    return np.column_stack([work.DayOfWeek,work.Hour,work.PeriodWithinHour,work.WeatherCode,work.Temperature,work.WindSpeed,h]).astype('float32')


def tensors(d,lookup,slot,overall,config):
    d=d.sort_values(['TimeSlot','GridID']).reset_index(drop=True)
    timestamps=pd.DatetimeIndex(d.TimeSlot.unique())
    raw=raw_features(d,lookup,slot,overall)
    scaled=raw.copy();scaled[:,0]/=6;scaled[:,1]/=23;scaled[:,3]/=27
    for i,col in [(4,'Temperature'),(5,'WindSpeed')]:
        v=config['scalers'][col];scaled[:,i]=(scaled[:,i]-v['mean'])/v['std']
    scaled[:,6]/=config['scalers']['HistoricalAverageDemandDistribution']['scale']
    ti=np.repeat(np.arange(len(timestamps)),142);r=d.Row.to_numpy();c=d.Column.to_numpy()
    x=np.zeros((len(timestamps),7,16,16),dtype='float32');y=np.zeros((len(timestamps),1,16,16),dtype='float32')
    x[ti,:,r,c]=scaled;y[ti,0,r,c]=d.Demand.to_numpy()
    historical=np.zeros_like(y);historical[ti,0,r,c]=raw[:,6]
    assert np.isfinite(x).all() and np.isfinite(y).all()
    np.testing.assert_array_equal(y.sum(axis=(1,2,3),dtype=np.float64),d.groupby('TimeSlot').Demand.sum().to_numpy())
    return x,y,historical,timestamps

@keras.utils.register_keras_serializable(package='FinalCNN')
class ValidGridMask(keras.layers.Layer):
    def __init__(self, mask, **kwargs):
        super().__init__(**kwargs);self.mask_values=np.asarray(mask,dtype='float32').tolist()
    def call(self,inputs):return inputs*tf.constant(self.mask_values,dtype=inputs.dtype)[None,None,:,:]
    def get_config(self):return {**super().get_config(),'mask':self.mask_values}

@keras.utils.register_keras_serializable(package='FinalCNN')
class MaskedMSE(keras.losses.Loss):
    def __init__(self,mask,**kwargs):
        super().__init__(**kwargs);self.mask_values=np.asarray(mask,dtype='float32').tolist()
    def call(self,y_true,y_pred):
        mask=tf.constant(self.mask_values,dtype=y_pred.dtype)[None,None,:,:]
        return tf.reduce_sum(tf.square(y_pred-y_true)*mask,axis=(1,2,3))/tf.reduce_sum(mask)
    def get_config(self):return {**super().get_config(),'mask':self.mask_values}

def build_model(mask):
    inputs=keras.Input((7,16,16),name='forecast_features')
    x=keras.layers.Permute((2,3,1))(inputs)
    for i,n in enumerate([14,7,1]):
        x=keras.layers.Conv2D(n,3,strides=1,padding='same',activation='relu',name=f'conv_{i+1}')(x)
    x=keras.layers.Permute((3,1,2))(x)
    outputs=ValidGridMask(mask,name='valid_grid_mask')(x)
    model=keras.Model(inputs,outputs,name='FinalJanMar3km30minCNN')
    model.compile(optimizer=keras.optimizers.Adam(.001),loss=MaskedMSE(mask))
    return model

def predict_batches(model,x,batch_size=64):
    return np.concatenate([model(x[i:i+batch_size],training=False).numpy() for i in range(0,len(x),batch_size)])

def metrics(y,p,mask):
    actual=y[:,0,mask.astype(bool)].astype('float64');pred=p[:,0,mask.astype(bool)].astype('float64')
    error=pred-actual
    return {'MAE':float(np.abs(error).mean()),'RMSE':float(np.sqrt(np.square(error).mean())),
            'R2':float(1-np.square(error).sum()/np.square(actual-actual.mean()).sum())}


def forecast_frame(predictions,targets,timestamps,grid,split='test'):
    g=grid.sort_values('GridID');r=g.Row.to_numpy();c=g.Column.to_numpy()
    frame=pd.DataFrame({'forecast_timestamp':np.repeat(timestamps.to_numpy(),142),'Grid_ID':np.tile(g.GridID.to_numpy(),len(timestamps)),
                        'predicted_demand':predictions[:,0,r,c].ravel(),'observed_demand':targets[:,0,r,c].ravel(),'split':split})
    assert len(frame)==len(timestamps)*142 and not frame[['forecast_timestamp','Grid_ID']].duplicated().any()
    assert np.isfinite(frame.predicted_demand).all() and frame.predicted_demand.ge(0).all()
    assert (frame.groupby('forecast_timestamp').Grid_ID.nunique()==142).all()
    return frame

class FinalDemandPredictor:
    """Load frozen preprocessing/model; callers supply forecast-time weather.

    Input table has TimeSlot, GridID, Row, Column, WeatherCode, Temperature,
    WindSpeed and placeholder Demand=0. Demand is ignored by the feature builder.
    The timestamp is the beginning of the predicted 30-minute interval.
    """
    def __init__(self,model_dir,dataset_dir):
        model_dir=Path(model_dir);d=Path(dataset_dir)
        self.model=keras.models.load_model(model_dir/'best.keras')
        self.config=json.loads((d/'preprocessing_config.json').read_text())
        self.mapping=json.loads((d/'grid_mapping_reference.json').read_text())['mapping']
        self.lookup=pd.read_parquet(d/'historical_average_demand.parquet')
        self.slot=pd.read_parquet(d/'historical_average_slot_fallback.parquet')
        self.overall=pd.read_parquet(d/'historical_average_grid_fallback.parquet')
    def predict(self,forecast_rows,grid):
        if grid.sort_values('GridID')[['GridID','Row','Column']].to_dict('records') != self.mapping:
            raise ValueError('Inference grid must match the frozen 142-grid raster mapping.')
        if forecast_rows[['TimeSlot','GridID']].duplicated().any() or not (forecast_rows.groupby('TimeSlot').GridID.nunique()==142).all():
            raise ValueError('Inference requires exactly one row per valid grid and timestamp.')
        if set(forecast_rows.GridID)!=set(range(142)) or not (forecast_rows.TimeSlot==forecast_rows.TimeSlot.dt.floor('30min')).all():
            raise ValueError('Inference requires valid GridIDs and half-hour timestamps.')
        positions=grid.set_index('GridID')
        if not (forecast_rows.Row.to_numpy()==positions.loc[forecast_rows.GridID,'Row'].to_numpy()).all() or not (forecast_rows.Column.to_numpy()==positions.loc[forecast_rows.GridID,'Column'].to_numpy()).all():
            raise ValueError('Inference row/column mapping differs from frozen grid.')
        x,y,_,times=tensors(forecast_rows,self.lookup,self.slot,self.overall,self.config)
        result=forecast_frame(predict_batches(self.model,x),y,times,grid,split='inference')
        return result.drop(columns=['observed_demand','split'])
