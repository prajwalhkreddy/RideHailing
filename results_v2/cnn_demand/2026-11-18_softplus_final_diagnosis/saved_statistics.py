import pandas as pd,numpy as np,json
from pathlib import Path
p=Path('results_v2/cnn_demand/2026-11-18_softplus_causal_research_training');o=Path('results_v2/cnn_demand/2026-11-18_softplus_final_diagnosis')
d=pd.read_parquet(p/'forecasts.parquet'); rows=[];summary={}
for s,g in d.groupby('split'):
 y=g.observed_demand.to_numpy(dtype=float);z=g.predicted_demand.to_numpy(dtype=float);b=g.baseline_demand.to_numpy(dtype=float);ae=abs(z-y);se=(z-y)**2
 summary[s]={'N':len(g),'zero_target_pct':float(np.mean(y==0)*100),'actual_mean':float(y.mean()),'prediction_mean':float(z.mean()),'baseline_mean':float(b.mean()),'positive_target_quantiles':np.quantile(y[y>0],[.5,.9,.99,1]).tolist(),'prediction_quantiles':np.quantile(z,[0,.5,.9,.99,1]).tolist(),'MAE':float(ae.mean()),'RMSE':float(np.sqrt(se.mean())),'baseline_MAE':float(abs(b-y).mean()),'baseline_RMSE':float(np.sqrt(np.mean((b-y)**2)))}
 city=g.groupby('target_start').observed_demand.sum();peak=g.target_start.isin(city[city>=city.quantile(.75)].index).to_numpy()
 groups={'zero':y==0,'positive':y>0,'low_actual_1_10':(y>0)&(y<=10),'medium_actual_10_100':(y>10)&(y<=100),'high_actual_above100':y>100,'high_training_grids':g.Grid_ID.isin([27,37,28,46,36]).to_numpy(),'low_training_grids':g.Grid_ID.isin([57,120,132,140,141]).to_numpy(),'peak':peak,'offpeak':~peak}
 for name,m in groups.items():
  rows.append(dict(split=s,group=name,N=int(m.sum()),MAE=float(ae[m].mean()),RMSE=float(np.sqrt(se[m].mean())),absolute_error_share_pct=float(ae[m].sum()/ae.sum()*100),squared_error_share_pct=float(se[m].sum()/se.sum()*100)))
pd.DataFrame(rows).to_csv(o/'error_concentration.csv',index=False)
(o/'saved_prediction_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2));print(pd.DataFrame(rows).to_string(index=False))
