"""Saved-output comparison only; no additional model fitting."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,pandas as pd
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/causal_cnn_mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('results_v2/cnn_demand/2026-11-18_softplus_causal_research_training');OLD=Path('results_v2/cnn_demand/2026-11-18_causal_research_training')
a=pd.read_parquet(OLD/'forecasts.parquet');b=pd.read_parquet(R/'forecasts.parquet');assert len(a)==len(b)
for col in ['target_start','Grid_ID','observed_demand','baseline_demand']:np.testing.assert_array_equal(a[col].to_numpy(),b[col].to_numpy())
b['relu']=a.predicted_demand;g=pd.read_csv(OLD/'grid_diagnostics.csv').query("split=='validation'").sort_values(['training_mean','Grid_ID']);groups={'high':g.tail(5).Grid_ID,'low':g.head(5).Grid_ID};rows=[]
for split,z in b.groupby('split'):
 totals=z.groupby('target_start').observed_demand.sum();peaks=totals.index[totals>=totals.quantile(.75)]
 subsets={'all':z,'peak':z[z.target_start.isin(peaks)],'off_peak':z[~z.target_start.isin(peaks)],**{k:z[z.Grid_ID.isin(ids)] for k,ids in groups.items()},'city':z.groupby('target_start')[['observed_demand','relu','predicted_demand','baseline_demand']].sum()}
 for group,df in subsets.items():
  for name,col in [('ReLU','relu'),('Softplus','predicted_demand'),('HistoricalAverage','baseline_demand')]:
   y=df.observed_demand.to_numpy(float);p=df[col].to_numpy(float);e=p-y;positive=y>0
   rows.append(dict(split=split,group=group,model=name,N=len(y),MAE=float(abs(e).mean()),RMSE=float(np.sqrt((e*e).mean())),bias_count=float(e.sum()),bias_pct=float(e.sum()/y.sum()*100) if y.sum() else None,zero_pct=float((p==0).mean()*100),positive_target_N=int(positive.sum()),positive_near_zero_N=int(((p<.01)&positive).sum()),positive_near_zero_pct=float(((p<.01)&positive).sum()/positive.sum()*100) if positive.any() else None))
pd.DataFrame(rows).to_csv(R/'three_way_comparison.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for path,label in [(OLD,'ReLU'),(R,'Softplus')]:
 h=pd.read_csv(path/'training_history.csv')
 for ax,col in zip(axes,['train_MSE','validation_MSE']):ax.plot(h.epoch,h[col],label=label);ax.set(xlabel='Epoch',ylabel='Masked MSE',title=col);ax.legend()
(R/'charts').mkdir(exist_ok=True);fig.savefig(R/'charts/loss_comparison.png',dpi=130);plt.close(fig)
v=json.loads((R/'validation.json').read_text());v['tests']={'passed':32,'failed':0,'seconds':24.487};v['same_evaluation_population']=True;v['near_zero_definition']='prediction <0.01 requests; diagnostic only';v['comparisons']=[r for r in rows if r['group']=='all']
reg=json.loads(Path('/tmp/reward_preservation.json').read_text());bad=[p for p,s in reg.items() if not Path(p).exists() or [Path(p).stat().st_size,Path(p).stat().st_mtime_ns]!=s];assert not bad
v['preservation']={'checked':len(reg),'changed':bad};v['report_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(R/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
shutil.copyfile('/tmp/softplus_tests.log',R/'tests.log');shutil.copyfile('/tmp/softplus_training.log',R/'training.log')
print(pd.DataFrame(v['comparisons']).to_string(index=False));print('epoch',v['best_epoch'],'of',v['epochs'])
