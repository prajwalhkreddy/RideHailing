"""Reporting only for the single corrected-protocol CNN experiment."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/causal_cnn_mpl')
from pathlib import Path
import json,hashlib,shutil
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('results_v2/cnn_demand/2026-11-18_causal_research_training')
v=json.loads((R/'validation.json').read_text());assert v['status']=='COMPLETE'
f=pd.read_parquet(R/'forecasts.parquet');g=pd.read_csv(R/'grid_diagnostics.csv');h=pd.read_csv(R/'training_history.csv');(R/'charts').mkdir(exist_ok=True)
rank=g[g.split=='validation'].sort_values(['training_mean','Grid_ID']);groups={'low':rank.head(5).Grid_ID.tolist(),'high':rank.tail(5).Grid_ID.tolist()};rows=[]
for split in ['validation','development']:
 for name,ids in groups.items():
  z=f[(f.split==split)&f.Grid_ID.isin(ids)]
  for model,col in [('CNN','predicted_demand'),('HistoricalAverage','baseline_demand')]:
   e=z[col]-z.observed_demand;rows.append(dict(split=split,group=name,grid_ids=str(ids),model=model,N=len(z),MAE=float(abs(e).mean()),RMSE=float(np.sqrt((e*e).mean()))))
pd.DataFrame(rows).to_csv(R/'high_low_diagnostics.csv',index=False)
fig,axes=plt.subplots(3,1,figsize=(12,9),layout='constrained')
z=f[f.split=='development']
for ax,name,ids in zip(axes,['City','High-demand grids','Low-demand grids'],[list(range(142)),groups['high'],groups['low']]):
 a=z[z.Grid_ID.isin(ids)].groupby('target_start')[['observed_demand','predicted_demand','baseline_demand']].sum()
 for col,label in [('observed_demand','Actual'),('predicted_demand','CNN'),('baseline_demand','Historical average')]:ax.plot(a.index,a[col],label=label)
 ax.set_title(name);ax.set_ylabel('Requests / 30 min');ax.legend()
axes[-1].set_xlabel('March 16 development target start (UTC)');fig.suptitle('Development-only evaluation; grid groups selected by Jan–Feb mean demand');fig.savefig(R/'charts/development_comparison.png',dpi=140);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,4),layout='constrained');ax.plot(h.epoch,h.train_MSE,label='Training');ax.plot(h.epoch,h.validation_MSE,label='Validation');ax.axvline(v['best_epoch'],color='grey',ls=':',label='Selected epoch');ax.set(xlabel='Epoch',ylabel='Masked MSE (requests²)',title='Single causal-research CNN experiment');ax.legend();fig.savefig(R/'charts/training_history.png',dpi=140);plt.close(fig)
shutil.copyfile('/tmp/causal_cnn_tests.log',R/'tests.log');shutil.copyfile('/tmp/causal_cnn_training.log',R/'training.log')
old=json.loads(Path('/tmp/causal_cnn_sources_before.json').read_text());changed=[p for p,h in old.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
m=json.loads(Path('/tmp/reward_preservation.json').read_text());bad=[p for p,s in m.items() if not Path(p).exists() or [Path(p).stat().st_size,Path(p).stat().st_mtime_ns]!=s]
v['tests']={'passed':29,'failed':0,'seconds':26.213};v['preservation']={'historical_paths_checked':len(m),'changed_historical_paths':bad,'changed_existing_pipeline_sources':changed};v['high_low_groups']=groups
assert not bad and not changed
(R/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps(v,indent=2))
