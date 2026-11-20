"""One bounded causal research CNN; protected March17–31 never loaded."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
os.environ.setdefault('MPLCONFIGDIR','/tmp/causal_cnn_mpl')
import sys,json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,tensorflow as tf
from src.demand.persistence_weather import build_persistence,contract,fingerprint,VERSION
from src.demand.causal_timing import CHANNELS
from src.demand.final_cnn import build_model,predict_batches,metrics
from src.simulation.utc_od_inputs import forecast
R=ROOT/'results_v2/cnn_demand/2026-11-18_causal_research_training'
M=ROOT/'models/cnn/causal_persistence_120min_2026_seed42_v1'
def dump(p,v):p.write_text(json.dumps(v,indent=2,default=str)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def framehash(d):return hashlib.sha256(pd.util.hash_pandas_object(d,index=False).values.tobytes()).hexdigest()
def main():
 if (M/'training_started.json').exists():raise RuntimeError('Existing attempt: do not retrain automatically')
 R.mkdir(parents=True,exist_ok=True);M.mkdir(parents=True,exist_ok=True)
 tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism();tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
 base=ROOT/'data/processed/spatial_3km_jan_mar_2026';dp=base/'demand_master_jan_mar_2026.parquet';wp=base/'weather_jan_mar_2026.parquet';gp=ROOT/'data/processed/grid_lookup.parquet'
 d=pd.read_parquet(dp,filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-03-17'))])
 w=pd.read_parquet(wp,filters=[('Datetime','<',pd.Timestamp('2026-03-17'))]);g=pd.read_parquet(gp,columns=['GridID','Row','Column']).sort_values('GridID')
 meta=contract(120);x,y,s,bad=build_persistence(d,g,w,meta);mask=np.zeros((16,16),bool);mask[g.Row,g.Column]=True
 assert x.shape==(3598,7,16,16) and mask.sum()==142 and not x[:,:,~mask].any() and np.isfinite(x).all()
 assert (s.assumed_available_at<=s.issued_at).all() and (s.target_start-s.issued_at==pd.Timedelta(minutes=30)).all()
 assert len(bad)==284 and bad.Demand.sum()==0
 assert np.array_equal(y,np.load(ROOT/'results_v2/cnn_demand/2026-11-17_causal_timing/Y_development.npy',mmap_mode='r'))
 ix={k:np.flatnonzero((s.split==k)&s.eligible) for k in ['train','validation','test']}
 assert [len(ix[k]) for k in ix]==[2830,718,48]
 s['evaluation_role']=s.split.replace({'test':'development_only_not_final_test'});s.to_csv(R/'sample_timing.csv',index=False)
 provenance=dict(demand_path=str(dp.relative_to(ROOT)),demand_selected_rows=len(d),demand_selected_sha256=framehash(d),weather_path=str(wp.relative_to(ROOT)),weather_selected_rows=len(w),weather_selected_sha256=framehash(w),grid_sha256=sha(gp),mask_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),X_sha256=hashlib.sha256(x.tobytes()).hexdigest(),Y_sha256=hashlib.sha256(y.tobytes()).hexdigest(),protected_labels_read=False,fingerprints_scope='Selected permitted rows; full protected-period files not hashed',source_hashes={p:sha(ROOT/p) for p in ['src/demand/causal_timing.py','src/demand/persistence_weather.py','src/demand/final_cnn.py','scripts/train_causal_research_cnn.py','config/final_temporal_protocol.json']})
 cfg=dict(version=VERSION,weather_contract_sha256=fingerprint(meta),weather_contract=meta,channels=list(CHANNELS),shape=list(x.shape),architecture='Conv2D 7->14->7->1, 3x3 same ReLU, valid-grid mask',optimizer='Adam',learning_rate=.001,batch_size=64,max_epochs=100,patience=10,seed=42,shuffle=False,loss='142-valid-cell masked MSE',selection='minimum March1-15 validation MSE',train='Jan1-Feb28; two no-history samples excluded',validation='March1-15, 718 elapsed-time slots',development='March16 only; NOT final test',final_test='March17-31 protected; not accessed',framework=tf.__version__,provenance=provenance)
 dump(R/'configuration.json',cfg);dump(M/'forecast_metadata.json',cfg);dump(R/'preflight.json',dict(status='PASS',eligible_counts={k:len(v) for k,v in ix.items()},dst_nonexistent_rows=284,dst_excluded_demand=0,request_total=float(y.sum(dtype=float)),finite=True,causal_history=True,assumed_weather=True,protected_period_accessed=False))
 # Original-unit baseline reconstructed from the identical causal history channel.
 # Demand SD uses only completed Jan-Feb intervals available at issuance.
 train=s.split.eq('train').to_numpy();vv=y[train,0][:,mask].astype(float);sums=np.cumsum(vv.sum(axis=1));squares=np.cumsum((vv*vv).sum(axis=1));n=s.history_training_slots.to_numpy(int)
 scale=np.ones(len(s));j=n>0;mean=sums[n[j]-1]/(n[j]*142);scale[j]=np.sqrt(np.maximum(squares[n[j]-1]/(n[j]*142)-mean**2,0));scale[scale==0]=1
 baseline=x[:,6:7].astype(float)*scale[:,None,None,None]
 model=build_model(mask);dump(M/'training_started.json',dict(seed=42,start=time.time(),attempt=1));best=np.inf;wait=0;hist=[]
 print('PREFLIGHT PASS; training single configuration',flush=True)
 for epoch in range(1,101):
  model.reset_metrics()
  for indices in [ix['train'][i:i+64] for i in range(0,len(ix['train']),64)]:model.train_on_batch(x[indices],y[indices])
  loss=float(model.metrics[0].result().numpy());vp=predict_batches(model,x[ix['validation']]);vm=metrics(y[ix['validation']],vp,mask);vl=vm['RMSE']**2
  if not np.isfinite([loss,vl]).all() or any(not np.isfinite(a).all() for a in model.get_weights()):raise ValueError('Nonfinite training')
  if vl<best:best=vl;best_epoch=epoch;wait=0;model.save(M/'best.keras')
  else:wait+=1
  hist.append(dict(epoch=epoch,train_MSE=loss,validation_MSE=vl,validation_MAE=vm['MAE'],validation_RMSE=vm['RMSE'],best_epoch=best_epoch));pd.DataFrame(hist).to_csv(R/'training_history.csv',index=False)
  if epoch==1 or epoch%10==0 or wait==10:print(f'epoch={epoch} train_MSE={loss:.6f} val_MSE={vl:.6f} best={best_epoch}',flush=True)
  if wait>=10:break
 selected=tf.keras.models.load_model(M/'best.keras');reloaded=tf.keras.models.load_model(M/'best.keras');np.testing.assert_array_equal(selected(x[ix['validation'][:2]]).numpy(),reloaded(x[ix['validation'][:2]]).numpy())
 comparisons=[];frames=[];gridrows=[];cityrows=[];mapping=g[['GridID','Row','Column']].to_dict('records');modelhash=sha(M/'best.keras')
 for split in ['train','validation','test']:
  ii=ix[split];p=predict_batches(selected,x[ii]);actual=y[ii];bp=baseline[ii];label='development' if split=='test' else split
  for name,pred in [('CNN',p),('HistoricalAverage',bp)]:
   comparisons.append(dict(split=label,model=name,slots=len(ii),grid_time_N=len(ii)*142,**metrics(actual,pred,mask)))
   err=pred.sum(axis=(1,2,3))-actual.sum(axis=(1,2,3));cityrows.append(dict(split=label,model=name,MAE=float(abs(err).mean()),RMSE=float(np.sqrt((err**2).mean())),mean_signed_error=float(err.mean())))
  if split=='train':continue
  f=s.iloc[ii].loc[:,['issued_at','target_start','target_end','feature_cutoff','observation_time','assumed_available_at']].iloc[np.repeat(np.arange(len(ii)),142)].reset_index(drop=True)
  for col in f:f[col]=pd.to_datetime(f[col],utc=True)
  f['Grid_ID']=np.tile(g.GridID,len(ii));f['predicted_demand']=p[:,0,g.Row,g.Column].ravel();f['observed_demand']=actual[:,0,g.Row,g.Column].ravel();f['baseline_demand']=bp[:,0,g.Row,g.Column].ravel();f['split']=label;frames.append(f)
  for row in g.itertuples(index=False):
   yy=actual[:,0,row.Row,row.Column];pp=p[:,0,row.Row,row.Column];bb=bp[:,0,row.Row,row.Column]
   gridrows.append(dict(split=label,Grid_ID=row.GridID,training_mean=float(y[train,0,row.Row,row.Column].mean()),actual_mean=float(yy.mean()),CNN_MAE=float(abs(pp-yy).mean()),CNN_RMSE=float(np.sqrt(((pp-yy)**2).mean())),baseline_MAE=float(abs(bb-yy).mean()),baseline_RMSE=float(np.sqrt(((bb-yy)**2).mean()))))
 allf=pd.concat(frames,ignore_index=True);allf.to_parquet(R/'forecasts.parquet',index=False);pd.DataFrame(comparisons).to_csv(R/'metrics.csv',index=False);pd.DataFrame(gridrows).to_csv(R/'grid_diagnostics.csv',index=False);pd.DataFrame(cityrows).to_csv(R/'city_metrics.csv',index=False)
 bundle=dict(weather_contract=meta,checkpoint_metadata=dict(version=VERSION,weather_contract_sha256=fingerprint(meta)),channels=list(CHANNELS),grid_ids=list(range(142)),forecasts={str(t):f for t,f in allf.groupby('target_start')})
 for t in bundle['forecasts']:forecast(bundle,pd.Timestamp(t))
 dump(R/'forecast_contract.json',dict(version=VERSION,weather_contract=meta,checkpoint_metadata=bundle['checkpoint_metadata'],channels=list(CHANNELS),grid_ids=list(range(142)),mapping=mapping,grid_sha256=provenance['grid_sha256'],mask_sha256=provenance['mask_sha256'],model_path=str((M/'best.keras').relative_to(ROOT)),model_sha256=modelhash,preprocessing_sha256=provenance['source_hashes'],forecast_sha256=sha(R/'forecasts.parquet'),units='fractional requests/grid/30 elapsed minutes',all_export_timestamps_validated_by='src.simulation.utc_od_inputs.forecast',operational_availability_verified=False))
 dump(R/'validation.json',dict(status='COMPLETE',epochs=len(hist),best_epoch=best_epoch,best_validation_MSE=best,checkpoint_sha256=modelhash,checkpoint_reload_exact=True,export_intervals_validated=len(bundle['forecasts']),protected_period_accessed=False,final_test_performed=False,training_runs=1,metrics=comparisons,city_metrics=cityrows))
 print('COMPLETE '+json.dumps(dict(epochs=len(hist),best_epoch=best_epoch,metrics=comparisons)),flush=True)
if __name__=='__main__':main()
