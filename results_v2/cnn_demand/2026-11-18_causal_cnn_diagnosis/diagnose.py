"""Saved-artifact diagnosis only; no fitting, tensor regeneration or simulation."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
R=Path('results_v2/cnn_demand/2026-11-18_causal_research_training');O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
f=pd.read_parquet(R/'forecasts.parquet');cfg=json.loads((R/'configuration.json').read_text());v=json.loads((R/'validation.json').read_text());fc=json.loads((R/'forecast_contract.json').read_text());history=pd.read_csv(R/'training_history.csv');timing=pd.read_csv(R/'sample_timing.csv');recorded=pd.read_csv(R/'metrics.csv')
assert sha(R/'forecasts.parquet')==fc['forecast_sha256'];assert sha(fc['model_path'])==v['checkpoint_sha256']
assert all(sha(p)==h for p,h in cfg['provenance']['source_hashes'].items())
assert not f.duplicated(['target_start','Grid_ID']).any()
assert (f.groupby('target_start').Grid_ID.agg(lambda x:set(x)==set(range(142)))).all()
for c in ['issued_at','target_start','target_end','feature_cutoff','observation_time','assumed_available_at']:f[c]=pd.to_datetime(f[c],utc=True)
assert (f.target_end-f.target_start==pd.Timedelta(minutes=30)).all();assert (f.target_start-f.issued_at==pd.Timedelta(minutes=30)).all();assert (f.feature_cutoff==f.issued_at).all();assert (f.assumed_available_at<=f.issued_at).all()
assert (f.target_start.dt.tz_convert('America/New_York').dt.tz_localize(None)<pd.Timestamp('2026-03-17')).all()
assert np.isfinite(f[['observed_demand','predicted_demand','baseline_demand']]).all().all();assert (f[['observed_demand','predicted_demand','baseline_demand']]>=0).all().all();assert (f.observed_demand%1==0).all()
rows=[];breakdown=[];spatial=[]
def stats(z,col):
 y=z.observed_demand.to_numpy(float);p=z[col].to_numpy(float);e=p-y
 return dict(N=len(z),mean_actual=float(y.mean()),mean_predicted=float(p.mean()),actual_total=float(y.sum()),predicted_total=float(p.sum()),count_bias=float(e.sum()),bias_pct=float(100*e.sum()/y.sum()) if y.sum() else None,mean_error=float(e.mean()),MAE=float(abs(e).mean()),RMSE=float(np.sqrt((e*e).mean())),under_pct=float(100*(e<0).mean()),over_pct=float(100*(e>0).mean()),equal_pct=float(100*(e==0).mean()),zero_prediction_pct=float(100*(p==0).mean()),positive_actual_zero_prediction_N=int(((y>0)&(p==0)).sum()),squared_error=float((e*e).sum()))
grid=pd.read_csv(R/'grid_diagnostics.csv');rank=grid[grid.split=='validation'].sort_values(['training_mean','Grid_ID']);groups={'low_5_training_grids':rank.head(5).Grid_ID.tolist(),'high_5_training_grids':rank.tail(5).Grid_ID.tolist()}
for split,z in f.groupby('split'):
 for model,col in [('CNN','predicted_demand'),('HistoricalAverage','baseline_demand')]:
  st=stats(z,col);old=recorded[(recorded.split==split)&(recorded.model==model)].iloc[0];assert abs(st['MAE']-old.MAE)<1e-10 and abs(st['RMSE']-old.RMSE)<1e-10
  rows.append(dict(split=split,model=model,**st))
 # Positive-demand empirical bands; zeros separate to avoid tied zero quantiles.
 q=np.quantile(z.loc[z.observed_demand>0,'observed_demand'],[.5,.9,.99]);conditions={'zero':z.observed_demand==0,'positive_le_P50':(z.observed_demand>0)&(z.observed_demand<=q[0]),'P50_to_P90':(z.observed_demand>q[0])&(z.observed_demand<=q[1]),'P90_to_P99':(z.observed_demand>q[1])&(z.observed_demand<=q[2]),'above_P99':z.observed_demand>q[2]}
 city=z.groupby('target_start')[['observed_demand','predicted_demand','baseline_demand']].sum();threshold=city.observed_demand.quantile(.75);peaks=city.index[city.observed_demand>=threshold]
 conditions.update({k:z.Grid_ID.isin(ids) for k,ids in groups.items()});conditions.update(peak_actual_city_top_quartile=z.target_start.isin(peaks),off_peak=~z.target_start.isin(peaks),positive_actual=z.observed_demand>0)
 for group,sel in conditions.items():
  for model,col in [('CNN','predicted_demand'),('HistoricalAverage','baseline_demand')]:breakdown.append(dict(split=split,group=group,model=model,positive_quantile_edges=str(q.tolist()),**stats(z[sel],col)))
 for model,col in [('CNN','predicted_demand'),('HistoricalAverage','baseline_demand')]:breakdown.append(dict(split=split,group='city_totals',model=model,**stats(city,col)))
 for t,a in z.groupby('target_start'):
  top=a.nlargest(5,'observed_demand');spatial.append(dict(split=split,target_start=t,actual_top5=float(top.observed_demand.sum()),cnn_at_actual_top5=float(top.predicted_demand.sum()),baseline_at_actual_top5=float(top.baseline_demand.sum()),actual_total=float(a.observed_demand.sum()),cnn_total=float(a.predicted_demand.sum()),baseline_total=float(a.baseline_demand.sum()),actual_max=float(a.observed_demand.max()),cnn_max=float(a.predicted_demand.max())))
pd.DataFrame(rows).to_csv(O/'metric_bias_reconciliation.csv',index=False);pd.DataFrame(breakdown).to_csv(O/'error_breakdown.csv',index=False);pd.DataFrame(spatial).to_csv(O/'spatial_peak_diagnostics.csv',index=False)
best=history.loc[history.validation_MSE.idxmin()];assert best.epoch==50;assert abs(best.validation_MSE-v['best_validation_MSE'])<1e-9
sources=['src/demand/causal_timing.py','src/demand/persistence_weather.py','src/demand/final_cnn.py','scripts/train_causal_research_cnn.py']
result=dict(classification='B_MODEL_GENERALIZATION_BIAS',scope='No confirmed numerical implementation defect in inspected path; causal attribution to architecture or normalization not established',metrics=rows,best_epoch=int(best.epoch),best_validation_MSE=float(best.validation_MSE),epoch50_train_streaming_MSE=float(best.train_MSE),epoch60_train_streaming_MSE=float(history.iloc[-1].train_MSE),epoch60_validation_MSE=float(history.iloc[-1].validation_MSE),checkpoint_hash_matches=True,source_hashes_match=True,source_sha256={p:sha(p) for p in sources},saved_forecast_sha256=sha(R/'forecasts.parquet'),checkpoint_sha256=sha(fc['model_path']),groups=groups,new_training=False,inference=False,protected_data_accessed=False,baseline_equals_inverse_scaled_history_feature='By construction; float32 channel precision',limitations=['Training tensors and per-sample scaling arrays not persisted; no new full tensor reconstruction performed','Predictions are reproduced from saved export, not regenerated from weights','Weather publication/vintage assumed','March16 is development, not final test'])
(O/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(pd.DataFrame(rows)[['split','model','mean_actual','mean_predicted','bias_pct','under_pct','over_pct','zero_prediction_pct']].to_string(index=False))
print(pd.DataFrame(breakdown).query("model=='CNN' and group in ['positive_actual','above_P99','city_totals']")[['split','group','N','mean_error','RMSE','under_pct','squared_error']].to_string(index=False))
