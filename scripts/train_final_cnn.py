"""One reproducible final CNN run. No legacy checkpoint or RL changes."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
os.environ.setdefault('MPLCONFIGDIR','/tmp/final_cnn_matplotlib')
from pathlib import Path
import sys,json,hashlib,random,shutil,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import geopandas as gpd
import tensorflow as tf
from src.demand.final_cnn import *
D=ROOT/'data/processed/cnn_jan_mar_2026_3km_30min'
M=ROOT/'models/cnn/jan_mar_2026_3km_30min'
R=ROOT/'results/analysis/2026-10-19_final_jan_mar_3km_cnn'
SOURCE=ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def dump(path,obj):path.write_text(json.dumps(obj,indent=2,default=str)+'\n')

def main():
    if (R/'metrics.json').exists():
        print('Completed evaluation exists; refusing unnecessary retraining.');return
    if (M/'training_started.json').exists():
        raise RuntimeError('A training attempt already exists. Inspect its checkpoint/history before authorizing technical-failure recovery.')
    for p in (D,M,R,R/'charts'):p.mkdir(parents=True,exist_ok=True)
    protected=json.loads((ROOT/'results/analysis/2026-10-19_true_3km_grid_activation/protected_fingerprints.json').read_text())
    for path,expected in protected.items():assert sha(ROOT/path)==expected,path
    dump(R/'protected_artifacts.json',protected)
    random.seed(42);np.random.seed(42);tf.keras.utils.set_random_seed(42)
    tf.config.experimental.enable_op_determinism()
    tf.config.threading.set_intra_op_parallelism_threads(4);tf.config.threading.set_inter_op_parallelism_threads(2)
    d=pd.read_parquet(SOURCE).sort_values(['TimeSlot','GridID']).reset_index(drop=True)
    grid=gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet').sort_values('GridID')
    validate_source(d,grid)
    mask=np.zeros((16,16),dtype='float32');mask[grid.Row,grid.Column]=1
    assert mask.sum()==142
    contract={'dataset_version':'jan_mar_2026_3km_30min_v1','grid_version':'true_3km_v1','valid_grids':142,'raster':[16,16],
              'period':[str(START),str(END)],'forecast_minutes':30,'forecast_status':'DOCUMENTED_ADAPTATION',
              'forecast_timestamp':'start of target interval [t,t+30min); issued for next main slot',
              'target_unit':'requests/grid/30min','sources':{'demand':str(SOURCE.relative_to(ROOT)),'demand_sha256':sha(SOURCE),'grid_sha256':sha(ROOT/'data/processed/grid_lookup.parquet')}}
    splits={name:{'start_inclusive':str(a),'end_exclusive':str(b),'slots':int((b-a)/pd.Timedelta(minutes=30))} for name,(a,b) in SPLITS.items()}
    contract['split_definition']=splits
    lookup,slot,overall,seasonal,preprocess=fit_preprocessing(d)
    preprocess={**contract,**preprocess}
    # Check representative timestamps before building complete tensors.
    sample_times=pd.to_datetime(['2026-01-01','2026-01-30 12:00','2026-02-28 23:30','2026-03-01','2026-03-15 23:30','2026-03-16','2026-03-24','2026-03-31 23:30'],format='mixed')
    sx,sy,sh,st=tensors(d.loc[d.TimeSlot.isin(sample_times)],lookup,slot,overall,preprocess)
    assert sx.shape==(8,7,16,16) and sy.shape==(8,1,16,16)
    assert not sx[:,:,mask==0].any() and not sy[:,:,mask==0].any()
    sample_model=build_model(mask)
    sp=sample_model(sx[:2],training=False).numpy()
    assert sp.shape==(2,1,16,16) and np.isfinite(sp).all() and (sp>=0).all()
    # Reinitialize with the same seed after shape-only checks; no optimizer update above.
    tf.keras.backend.clear_session();tf.keras.utils.set_random_seed(42)
    dump(R/'fail_fast_validation.json',{'status':'PASS','samples':[{'forecast_timestamp':str(t),'target_total':int(sy[i].sum())} for i,t in enumerate(st)],'channels':CHANNELS,'mask_valid':142,'mask_unused':114})
    print('FAIL-FAST PASS: source, 8 timestamps, feature/target masks, architecture',flush=True)
    lookup.to_parquet(D/'historical_average_demand.parquet',index=False)
    slot.to_parquet(D/'historical_average_slot_fallback.parquet',index=False)
    overall.to_parquet(D/'historical_average_grid_fallback.parquet',index=False)
    seasonal.to_parquet(D/'seasonal_baseline.parquet',index=False)
    np.save(D/'valid_mask.npy',mask)
    dump(D/'dataset_metadata.json',{**contract,'source_slots':4320,'source_requests':11006194,'dense_rows':613440})
    dump(D/'preprocessing_config.json',preprocess)
    dump(D/'split_definition.json',{**contract,'partitions':splits})
    dump(D/'feature_specification.json',{**contract,'channel_order':CHANNELS,'encoding':preprocess['encoding'],'missing_cells':'Zero after scaling; excluded from loss and metrics','weather_availability':'Retrospective observed forecast-time weather; live forecast requires ex ante weather.'})
    dump(D/'grid_mapping_reference.json',{**contract,'path':'data/processed/grid_lookup.parquet','mask':'valid_mask.npy','mapping':grid[['GridID','Row','Column']].to_dict('records')})
    arrays={};histories={};timestamps={}
    for name,(a,b) in SPLITS.items():
        x,y,h,t=tensors(d.loc[d.TimeSlot.ge(a)&d.TimeSlot.lt(b)],lookup,slot,overall,preprocess)
        arrays[name]=(x,y);histories[name]=h;timestamps[name]=t
        np.save(D/f'X_{name}.npy',x);np.save(D/f'Y_{name}.npy',y);np.save(D/f'forecast_timestamp_{name}.npy',t.to_numpy())
    training={**contract,'architecture':[7,14,7,1],'kernel_size':3,'stride':1,'padding':'same','activations':'ReLU including output','parameter_origin':'PROJECT IMPLEMENTATION for unspecified kernel/training settings',
              'loss':'masked MSE /142 valid cells','optimizer':'Adam','learning_rate':.001,'batch_size':64,'max_epochs':100,'early_stopping_patience':10,'seed':42,'batch_order':'chronological, no shuffle','checkpoint_selection':'lowest validation masked MSE','framework':tf.__version__,'device':'TensorFlow available device','test_evaluation_count':1}
    dump(M/'training_config.json',training)
    model=build_model(mask)
    with (R/'model_architecture.txt').open('w') as f:model.summary(print_fn=lambda line:f.write(line+'\n'))
    dump(M/'training_started.json',{'seed':42,'started':time.time(),'configuration_count':1})
    xtrain,ytrain=arrays['train'];xval,yval=arrays['validation']
    best=float('inf');best_epoch=0;wait=0;history=[]
    for epoch in range(1,101):
        model.reset_metrics()
        for i in range(0,len(xtrain),64):model.train_on_batch(xtrain[i:i+64],ytrain[i:i+64])
        train_loss=float(model.metrics[0].result().numpy())
        validation_pred=predict_batches(model,xval)
        vm=metrics(yval,validation_pred,mask);loss=vm['RMSE']**2
        if not np.isfinite([train_loss,loss]).all():raise RuntimeError('Non-finite training/validation loss')
        improved=loss<best
        if improved:
            best=loss;best_epoch=epoch;wait=0;model.save(M/'best.keras')
            dump(M/'best_checkpoint.json',{'best_epoch':epoch,'validation_MSE':best})
        else:wait+=1
        history.append({'epoch':epoch,'train_masked_MSE':train_loss,'validation_masked_MSE':loss,'validation_MAE':vm['MAE'],'validation_RMSE':vm['RMSE'],'best_checkpoint':improved})
        pd.DataFrame(history).to_csv(R/'training_history.csv',index=False)
        print(f'Epoch {epoch:03d}: train_MSE={train_loss:.5f} val_MAE={vm["MAE"]:.5f} val_RMSE={vm["RMSE"]:.5f} best={best_epoch}',flush=True)
        if wait>=10:break
    selected=keras.models.load_model(M/'best.keras')
    val_metrics=metrics(yval,predict_batches(selected,xval),mask)
    # TEST is evaluated only after checkpoint selection has finished.
    xtest,ytest=arrays['test'];pred=predict_batches(selected,xtest)
    test_metrics=metrics(ytest,pred,mask)
    historical_metrics=metrics(ytest,histories['test'],mask)
    # Seasonal: train weekday/half-hour mean across grids, broadcast spatially.
    keys=pd.DataFrame({'DayOfWeek':timestamps['test'].dayofweek,'slot_of_day':timestamps['test'].hour*2+timestamps['test'].minute//30})
    season_values=keys.merge(seasonal,on=['DayOfWeek','slot_of_day'],how='left').seasonal_average.to_numpy()
    assert np.isfinite(season_values).all()
    season_pred=season_values[:,None,None,None]*mask[None,None,:,:]
    seasonal_metrics=metrics(ytest,season_pred,mask)
    comparisons=pd.DataFrame([{'model':name,**v} for name,v in [('CNN',test_metrics),('HistoricalAverage',historical_metrics),('Seasonal',seasonal_metrics)]])
    comparisons.to_csv(R/'baseline_comparison.csv',index=False)
    pd.DataFrame([{'split':'validation',**val_metrics},{'split':'test',**test_metrics}]).to_csv(R/'metrics.csv',index=False)
    forecasts=forecast_frame(pred,ytest,timestamps['test'],grid)
    forecasts.to_parquet(R/'test_predictions.parquet',index=False)
    shutil.copy2(R/'test_predictions.parquet',R/'dqn_ready_forecasts.parquet')
    for name in ['preprocessing_config.json','split_definition.json','feature_specification.json','historical_average_demand.parquet']:
        shutil.copy2(D/name,R/name)
    for name in ['preprocessing_config.json','split_definition.json','dataset_metadata.json','grid_mapping_reference.json']:
        shutil.copy2(D/name,M/name)
    shutil.copy2(R/'training_history.csv',M/'training_history.csv')
    plot_diagnostics(ytest,pred,timestamps['test'],mask)
    for path,expected in protected.items():assert sha(ROOT/path)==expected,path
    result={**contract,'best_epoch':best_epoch,'epochs_run':len(history),'validation':val_metrics,'test':test_metrics,'historical_average':historical_metrics,'seasonal':seasonal_metrics,
            'cnn_beats_both_on_mae_and_rmse':all(test_metrics[k]<b[k] for b in [historical_metrics,seasonal_metrics] for k in ['MAE','RMSE']),
            'forecast_rows':len(forecasts),'forecast_timestamps':len(timestamps['test']),'checkpoint_sha256':sha(M/'best.keras'),'protected_artifacts_unchanged':True,'test_evaluations':1,
            'test_prediction_range':[float(pred[:,0,mask.astype(bool)].min()),float(pred[:,0,mask.astype(bool)].max())],
            'test_observed_range':[float(ytest.min()),float(ytest.max())]}
    dump(R/'metrics.json',result)
    print(json.dumps(result,indent=2),flush=True)


def plot_diagnostics(y,p,t,mask):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    totals=y.sum(axis=(1,2,3));indices=[0,len(t)//2,int(totals.argmax())]
    for label,i in zip(['first','middle','highest_demand'],indices):
        fig,axes=plt.subplots(1,3,figsize=(12,4),layout='constrained')
        maximum=max(float(y[i].max()),float(p[i].max()))
        for ax,values,title in zip(axes,[y[i,0],p[i,0],abs(y[i,0]-p[i,0])],['Observed','Predicted','Absolute error']):
            im=ax.imshow(np.ma.masked_where(mask==0,values),vmin=0,vmax=maximum if title!='Absolute error' else None,cmap='viridis')
            ax.set_title(title);ax.set_xlabel('Raster column');ax.set_ylabel('Raster row');fig.colorbar(im,ax=ax,label='Requests / 30 min')
        fig.suptitle(f'TEST forecast interval begins {t[i]}')
        fig.savefig(R/'charts'/f'test_maps_{label}.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,4),layout='constrained');ax.plot(t,totals,label='Observed',lw=1);ax.plot(t,p.sum(axis=(1,2,3)),label='CNN',lw=1)
    import matplotlib.dates as mdates
    locator=mdates.AutoDateLocator(minticks=4,maxticks=8)
    ax.xaxis.set_major_locator(locator);ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.set(xlabel='Forecast timestamp',ylabel='Total requests / 30 min',title='TEST total demand: observed and selected CNN');ax.legend();fig.savefig(R/'charts/test_total_demand.png',dpi=150);plt.close(fig)

if __name__=='__main__':main()
