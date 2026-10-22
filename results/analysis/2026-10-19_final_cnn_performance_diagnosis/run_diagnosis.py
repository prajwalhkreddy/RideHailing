"""Focused diagnostics and one gated continuation; preserves all original artifacts."""
from pathlib import Path
import os,sys,json,hashlib,random
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
os.environ.setdefault('MPLCONFIGDIR','/tmp/final_cnn_matplotlib')
import numpy as np
import pandas as pd
import geopandas as gpd
import tensorflow as tf
from src.demand.final_cnn import (CHANNELS,SPLITS,TRAIN_END,fit_preprocessing,tensors,metrics,predict_batches,forecast_frame)
R=Path(__file__).resolve().parent
D=ROOT/'data/processed/cnn_jan_mar_2026_3km_30min'
OLD=ROOT/'results/analysis/2026-10-19_final_jan_mar_3km_cnn'
MODEL=ROOT/'models/cnn/jan_mar_2026_3km_30min/best.keras'
NEW=ROOT/'models/cnn/jan_mar_2026_3km_30min_continued'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,default=str)+'\n')
def stats(x):
 x=np.asarray(x,dtype='float64');return dict(min=float(x.min()),max=float(x.max()),mean=float(x.mean()),std=float(x.std()))
def main():
 if (R/'summary.json').exists():print('Diagnosis already complete; no repeated continuation.');return
 if (R/'continuation_started.json').exists():raise RuntimeError('Prior continuation started; inspect and reuse before any further training.')
 original={str(p.relative_to(ROOT)):sha(p) for base in [D,OLD,MODEL.parent] for p in base.rglob('*') if p.is_file()}
 dump(R/'original_fingerprints.json',original)
 random.seed(42);np.random.seed(42);tf.keras.utils.set_random_seed(42)
 tf.config.experimental.enable_op_determinism();tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
 source=pd.read_parquet(ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet').sort_values(['TimeSlot','GridID']).reset_index(drop=True)
 grid=gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet').sort_values('GridID')
 mask=np.load(D/'valid_mask.npy');valid=mask.astype(bool)
 assert mask.sum()==142 and (~valid).sum()==114
 lookup,slot,overall,seasonal,config=fit_preprocessing(source)
 for name,df in [('historical_average_demand',lookup),('historical_average_slot_fallback',slot),('historical_average_grid_fallback',overall),('seasonal_baseline',seasonal)]:
  pd.testing.assert_frame_equal(df,pd.read_parquet(D/f'{name}.parquet'))
 saved_config=json.loads((D/'preprocessing_config.json').read_text());assert config['scalers']==saved_config['scalers']
 # Independent train-only grouping above; heldout perturbation proves fit exclusion.
 changed=source.copy();changed.loc[changed.TimeSlot>=TRAIN_END,['Demand','Temperature','WindSpeed','WeatherCode']]=100000
 l2,s2,o2,se2,c2=fit_preprocessing(changed)
 for a,b in [(lookup,l2),(slot,s2),(overall,o2),(seasonal,se2)]:pd.testing.assert_frame_equal(a,b)
 assert c2['scalers']==config['scalers'];del changed,l2,s2,o2,se2
 arrays={};hist={};times={};integrity=[]
 for name,(a,b) in SPLITS.items():
  sub=source.loc[source.TimeSlot.ge(a)&source.TimeSlot.lt(b)]
  x,y,h,t=tensors(sub,lookup,slot,overall,config)
  np.testing.assert_array_equal(x,np.load(D/f'X_{name}.npy'))
  np.testing.assert_array_equal(y,np.load(D/f'Y_{name}.npy'))
  np.testing.assert_array_equal(t.to_numpy(),np.load(D/f'forecast_timestamp_{name}.npy'))
  assert not x[:,:,~valid].any() and not y[:,:,~valid].any()
  scale=config['scalers']['HistoricalAverageDemandDistribution']['scale']
  for i in [0,len(t)//2,len(t)-1]:
   error=float(np.max(np.abs(x[i,6,valid]-h[i,0,valid]/scale)))
   assert error==0
   integrity.append(dict(split=name,forecast_timestamp=str(t[i]),scaled_channel_max_error=error,valid_cells=142,target_total=int(y[i].sum())))
  arrays[name]=(x,y);hist[name]=h;times[name]=t
 pd.DataFrame(integrity).to_csv(R/'channel_integrity.csv',index=False)
 # Explicit fallback fixtures use a real timestamp; no final data changed.
 from src.demand.final_cnn import raw_features
 sample=source.iloc[:142]
 fallback=raw_features(sample,lookup.iloc[:0],slot,overall)[:,-1]
 np.testing.assert_allclose(fallback,slot.loc[slot.slot_of_day==0].sort_values('GridID').slot_average,rtol=1e-6)
 np.testing.assert_allclose(raw_features(sample,lookup.iloc[:0],slot.iloc[:0],overall)[:,-1],overall.grid_average,rtol=1e-6)
 assert not raw_features(sample,lookup.iloc[:0],slot.iloc[:0],overall.iloc[:0])[:,-1].any()
 f=pd.read_parquet(OLD/'test_predictions.parquet').sort_values(['forecast_timestamp','Grid_ID']).reset_index(drop=True)
 assert len(f)==768*142 and not f[['forecast_timestamp','Grid_ID']].duplicated().any()
 assert pd.DatetimeIndex(f.forecast_timestamp.unique()).equals(times['test'])
 assert (f.groupby('forecast_timestamp').Grid_ID.nunique()==142).all()
 r=grid.Row.to_numpy();c=grid.Column.to_numpy()
 np.testing.assert_array_equal(f.observed_demand.to_numpy(),arrays['test'][1][:,0,r,c].ravel())
 f['historical_prediction']=hist['test'][:,0,r,c].ravel()
 oldpred=np.zeros_like(arrays['test'][1]);oldpred[:,0,r,c]=f.predicted_demand.to_numpy().reshape(768,142)
 comparison=pd.read_csv(OLD/'baseline_comparison.csv').set_index('model')
 for name,p in [('CNN',oldpred),('HistoricalAverage',hist['test'])]:
  measured=metrics(arrays['test'][1],p,mask)
  for k,v in measured.items():np.testing.assert_allclose(v,comparison.loc[name,k],rtol=1e-10)
 model=tf.keras.models.load_model(MODEL)
 conv=[layer for layer in model.layers if isinstance(layer,tf.keras.layers.Conv2D)]
 assert len(conv)==3 and [x.filters for x in conv]==[14,7,1]
 assert all(x.kernel_size==(3,3) and x.strides==(1,1) and x.padding=='same' and x.activation==tf.keras.activations.relu for x in conv)
 assert model.input_shape==(None,7,16,16) and model.output_shape==(None,1,16,16)
 np.testing.assert_array_equal(model.layers[-1].mask_values,mask)
 np.testing.assert_array_equal(model.loss.mask_values,mask)
 truth=np.zeros((2,1,16,16),dtype='float32');test=truth.copy();test[:,:,valid]=1;test[:,:,~valid]=99999
 assert float(model.loss(truth,test))==1
 # Loss sample reduction and differentiation: invalid cells cannot contribute.
 variable=tf.Variable(test)
 with tf.GradientTape() as tape:loss=model.loss(truth,variable)
 gradient=tape.gradient(loss,variable).numpy()
 assert not gradient[:,:,~valid].any()
 np.testing.assert_allclose(gradient[:,:,valid],1/142,rtol=1e-6)
 assert model.optimizer.__class__.__name__=='Adam'
 assert int(model.optimizer.iterations)==4500
 np.testing.assert_allclose(float(model.optimizer.learning_rate.numpy()),.001,rtol=1e-6)
 numerical=[]
 for i,name in enumerate(CHANNELS):numerical.append({'variable':name,**stats(arrays['train'][0][:,i,valid])})
 numerical.append({'variable':'target',**stats(arrays['train'][1][:,0,valid])})
 numerical.append({'variable':'historical_lookup_unscaled',**stats(hist['train'][:,0,valid])})
 pd.DataFrame(numerical).to_csv(R/'train_numerical_ranges.csv',index=False)
 history=pd.read_csv(OLD/'training_history.csv').set_index('epoch')
 history.loc[[1,10,25,50,75,90,100]].to_csv(R/'training_history_checkpoints.csv')
 trend={}
 for span in [10,20]:
  before=float(history.loc[100-span,'validation_masked_MSE']);after=float(history.loc[100,'validation_masked_MSE'])
  trend[f'last_{span}_epochs']={'from_epoch':100-span,'to_epoch':100,'from_MSE':before,'to_MSE':after,'absolute_change':after-before,'percentage_change':100*(after/before-1)}
 improving=bool((history.loc[81:100,'validation_masked_MSE'].diff().dropna()<0).all())
 assert int(history.validation_masked_MSE.idxmin())==100
 # Materiality is descriptive, stated before continuation; not a tuned threshold.
 gate=improving and trend['last_20_epochs']['percentage_change'] < -1
 diagnostics=prediction_diagnostics(f,'original')
 grid_errors=grid_diagnostics(f)
 checks={'train_only_fit_verified':True,'heldout_perturbation_invariant':True,'exact_saved_tensors_verified':True,'same_test_targets_and_mask':True,'fallbacks_verified':True,'mask_and_gradient_verified':True,'saved_architecture_verified':True,'optimizer_iterations_restored':4500,'lr':float(model.optimizer.learning_rate.numpy()),'zero_prediction_share_valid_test':float((f.predicted_demand==0).mean()),'zero_prediction_share_positive_targets':float((f.loc[f.observed_demand>0,'predicted_demand']==0).mean()),'historical_scale':config['scalers']['HistoricalAverageDemandDistribution']['scale']}
 dump(R/'precontinuation_checks.json',{'checks':checks,'trend':trend,'classification':'TRAINING_TRUNCATED' if gate else 'CONVERGED','gate':gate,'materiality_interpretation':'Continuous final20 improvements and >1% relative validation MSE reduction; diagnostic criterion, no hyperparameter selection.'})
 print('GATES PASS',json.dumps(trend),'continuation',gate,flush=True)
 if not gate:raise RuntimeError('Continuation not warranted; finish diagnostic decision without training.')
 NEW.mkdir(parents=True,exist_ok=True)
 dump(R/'continuation_started.json',{'original_checkpoint_sha256':sha(MODEL),'start_epoch':100,'maximum_additional_epochs':100,'seed':42,'patience':10,'optimizer_restored':True})
 # Preserve optimizer slots/iteration, never recompile or reinitialize model.
 model.save(NEW/'best.keras')
 best=float(history.loc[100,'validation_masked_MSE']);best_epoch=100;wait=0;continuation=[]
 xtrain,ytrain=arrays['train'];xval,yval=arrays['validation']
 for epoch in range(101,201):
  model.reset_metrics()
  for i in range(0,len(xtrain),64):model.train_on_batch(xtrain[i:i+64],ytrain[i:i+64])
  trainloss=float(model.metrics[0].result().numpy())
  val=metrics(yval,predict_batches(model,xval),mask);val_loss=val['RMSE']**2
  assert np.isfinite([trainloss,val_loss]).all()
  improved=val_loss<best
  if improved:best=val_loss;best_epoch=epoch;wait=0;model.save(NEW/'best.keras')
  else:wait+=1
  continuation.append({'epoch':epoch,'train_MSE':trainloss,'validation_MSE':val_loss,'validation_MAE':val['MAE'],'validation_RMSE':val['RMSE'],'best_checkpoint':improved})
  pd.DataFrame(continuation).to_csv(R/'continuation_history.csv',index=False)
  print(f'Epoch {epoch}: train_MSE={trainloss:.5f} val_RMSE={val["RMSE"]:.5f} best={best_epoch}',flush=True)
  if wait>=10:break
 selected=tf.keras.models.load_model(NEW/'best.keras')
 pred=predict_batches(selected,arrays['test'][0]) # One continued-checkpoint TEST inference.
 finalmetrics=metrics(arrays['test'][1],pred,mask)
 finalframe=forecast_frame(pred,arrays['test'][1],times['test'],grid)
 finalframe['historical_prediction']=f.historical_prediction.to_numpy()
 finaldiag=prediction_diagnostics(finalframe,'continued')
 # Compact supported downstream artifact saved with the separate model, never overwriting canonical forecasts.
 finalframe.drop(columns='historical_prediction').to_parquet(NEW/'test_predictions.parquet',index=False)
 rows=[{'model':name,**comparison.loc[name].to_dict()} for name in ['CNN','HistoricalAverage','Seasonal']]
 rows.append({'model':'CNN_continued',**finalmetrics});pd.DataFrame(rows).to_csv(R/'baseline_comparison.csv',index=False)
 for path,h in original.items():assert sha(ROOT/path)==h,path
 baseline_wins=all(comparison.loc['HistoricalAverage',key]<finalmetrics[key] for key in ['MAE','RMSE'])
 summary={'checks':checks,'trend':trend,'initial_classification':'TRAINING_TRUNCATED','continuation_run':True,'additional_epochs':len(continuation),'best_epoch':best_epoch,'best_validation_RMSE':best**.5,'continued_test':finalmetrics,'historical_baseline':comparison.loc['HistoricalAverage'].to_dict(),'historical_baseline_still_wins':bool(baseline_wins),'decision':'D. CNN_VALID_BUT_HISTORICAL_BASELINE_SUPERIOR' if baseline_wins else 'C. TRAINING_TRUNCATED_AND_CONTINUED','original_prediction_diagnostics':diagnostics,'continued_prediction_diagnostics':finaldiag,'grid_diagnostics':grid_errors,'original_artifacts_unchanged':True,'continued_test_evaluations':1,'model_path':str((NEW/'best.keras').relative_to(ROOT)),'canonical_model_not_replaced':True}
 dump(R/'summary.json',summary)
 dump(NEW/'continuation_metadata.json',{**summary,'source_model':str(MODEL.relative_to(ROOT)),'config_unchanged_from':'models/cnn/jan_mar_2026_3km_30min/training_config.json'})
 print(json.dumps(summary,indent=2),flush=True)


def prediction_diagnostics(f,label):
 actual=f.observed_demand.to_numpy(dtype=float);summary=[]
 for name,col in [('CNN','predicted_demand'),('HistoricalAverage','historical_prediction')]:
  pred=f[col].to_numpy(dtype=float)
  summary.append({'model':name,'mean_prediction':pred.mean(),'mean_observed':actual.mean(),'total_prediction':pred.sum(),'total_observed':actual.sum(),'prediction_observation_ratio':pred.sum()/actual.sum(),'correlation':np.corrcoef(actual,pred)[0,1],'zero_prediction_share':float((pred==0).mean())})
 pd.DataFrame(summary).to_csv(R/f'{label}_prediction_summary.csv',index=False)
 # Use observed-count quantiles, remove ties explicitly; keep zero-demand separate.
 positive=actual[actual>0];cuts=np.unique(np.quantile(positive,[0,.25,.5,.75,.9,.95,.99,1]))
 bands=[('zero',actual==0)]
 for i,(a,b) in enumerate(zip(cuts[:-1],cuts[1:])):
  bands.append((f'{"[" if i==0 else "("}{a:g},{b:g}]',(actual>=a if i==0 else actual>a)&(actual<=b)))
 rows=[]
 for band,idx in bands:
  for name,col in [('CNN','predicted_demand'),('HistoricalAverage','historical_prediction')]:
   obs=actual[idx];p=f.loc[idx,col].to_numpy(dtype=float);e=p-obs
   rows.append({'demand_band':band,'model':name,'N':len(obs),'observed_mean':obs.mean(),'predicted_mean':p.mean(),'bias':e.mean(),'MAE':abs(e).mean(),'RMSE':np.sqrt((e**2).mean())})
 pd.DataFrame(rows).to_csv(R/f'{label}_demand_quantile_errors.csv',index=False)
 # Compare spatial peak magnitudes, not a causal claim about convolution smoothing.
 by=f.groupby('forecast_timestamp')
 peaks=by[['observed_demand','predicted_demand','historical_prediction']].max()
 return {'models':summary,'positive_target_quantile_boundaries':cuts.tolist(),'mean_spatial_peak_observed':float(peaks.observed_demand.mean()),'mean_spatial_peak_CNN':float(peaks.predicted_demand.mean()),'mean_spatial_peak_historical':float(peaks.historical_prediction.mean())}


def grid_diagnostics(f):
 rows=[]
 for g,v in f.groupby('Grid_ID'):
  rows.append({'Grid_ID':int(g),'CNN_MAE':float(abs(v.predicted_demand-v.observed_demand).mean()),'baseline_MAE':float(abs(v.historical_prediction-v.observed_demand).mean()),'mean_observed':float(v.observed_demand.mean())})
 errors=pd.DataFrame(rows);errors['difference']=errors.CNN_MAE-errors.baseline_MAE
 # Narrow spatial dependency solely to identify Manhattan-intersecting cells.
 zones=gpd.read_file(ROOT/'data/raw/taxi_zones/taxi_zones.shp').to_crs('EPSG:32118')
 borough=next(c for c in zones.columns if c.lower()=='borough')
 manhattan=zones.loc[zones[borough]=='Manhattan'].geometry.union_all()
 grid=gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet').sort_values('GridID')
 errors['manhattan_fraction_of_cell_area']=[g.intersection(manhattan).area/g.area for g in grid.geometry]
 errors['intersects_manhattan']=errors.manhattan_fraction_of_cell_area>1e-10
 errors.to_csv(R/'grid_error_comparison.csv',index=False)
 top=pd.concat([errors.nsmallest(10,'difference').assign(ranking='smallest_difference'),errors.nlargest(10,'difference').assign(ranking='largest_degradation')])
 top.to_csv(R/'grid_error_extremes.csv',index=False)
 positive=errors.difference.clip(lower=0)
 high=errors.mean_observed>=errors.mean_observed.quantile(.75)
 return {'improved_grids':int((errors.difference<0).sum()),'degraded_grids':int((errors.difference>0).sum()),'top10_degraded_intersect_manhattan':int(errors.nlargest(10,'difference').intersects_manhattan.sum()),'positive_MAE_excess_share_manhattan_intersecting':float(positive[errors.intersects_manhattan].sum()/positive.sum()),'positive_MAE_excess_share_top_quartile_demand_grids':float(positive[high].sum()/positive.sum()),'geography_definition':'Positive polygon overlap with existing Manhattan taxi zones; not exclusive borough assignment.'}
if __name__=='__main__':main()
