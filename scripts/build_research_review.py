"""Documentation-only review figures/tables from saved permitted evidence. No model calls."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'results_v2/publication'; F=O/'figures'; T=O/'tables'
F.mkdir(parents=True,exist_ok=True);T.mkdir(exist_ok=True)
manifest=[];sources={}
def read(p):
 p=R/p;sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return pd.read_csv(p) if p.suffix=='.csv' else json.loads(p.read_text())
def save(name,fig,source,caption):
 fig.suptitle(caption,fontsize=11);fig.tight_layout(rect=(0,.035,1,.95));fig.text(.01,.005,'Source: '+source,fontsize=5)
 for ext in ('svg','png'):fig.savefig(F/(name+'.'+ext),dpi=180)
 plt.close(fig);manifest.append(dict(figure=name,source=source,caption=caption))
def table(name,d):d.to_csv(T/(name+'.csv'),index=False)
C='results_v2/cnn_demand/';P='results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration/';S='results_v2/passenger_sensitivity/2026-11-17_methodology_decision/'
fig,ax=plt.subplots(1,2,figsize=(10,4));metrics=[]
for i,(v,label) in enumerate([('causal_research_training','ReLU'),('softplus_causal_research_training','Softplus')]):
 base=C+'2026-11-18_'+v+'/';h=read(base+'training_history.csv');ax[i].plot(h.epoch,h.train_MSE,label='Training');ax[i].plot(h.epoch,h.validation_MSE,label='Validation');ax[i].set(yscale='log',xlabel='Epoch',ylabel='Masked MSE (requests²)',title=label);ax[i].legend()
 m=read(base+'metrics.csv');m['experiment']=label;metrics.append(m)
save('cnn_training_loss',fig,C,'Jan–Feb training; March 1–15 validation — saved epoch losses')
m=pd.concat(metrics);table('cnn_metrics',m)
fig,ax=plt.subplots(1,2,figsize=(10,4))
for j,split in enumerate(['validation','development']):
 rows=m[(m.split==split)&((m.model=='CNN')|(m.experiment=='Softplus'))];labels=[r.experiment if r.model=='CNN' else 'Historical mean' for r in rows.itertuples()]
 x=np.arange(len(rows));ax[j].bar(x-.18,rows.MAE,.36,label='MAE');ax[j].bar(x+.18,rows.RMSE,.36,label='RMSE');ax[j].set(xticks=x,xticklabels=labels,ylabel='Requests / grid / 30 minutes',title=split);ax[j].legend()
save('cnn_baseline_comparison',fig,C,'Identical valid-grid populations; development = March 16, not final test')
fpath=C+'2026-11-18_softplus_causal_research_training/forecasts.parquet';sources[fpath]=hashlib.sha256((R/fpath).read_bytes()).hexdigest();d=pd.read_parquet(R/fpath)
local=d.target_start.dt.tz_convert('America/New_York');assert local.min()>=pd.Timestamp('2026-03-01',tz='America/New_York') and local.max()<pd.Timestamp('2026-03-17',tz='America/New_York')
for split in ['validation','development']:
 a=d[d.split==split];n=len(a);err=a.predicted_demand-a.observed_demand;expected=m[(m.experiment=='Softplus')&(m.model=='CNN')&(m.split==split)].iloc[0]
 assert np.isclose(abs(err).mean(),expected.MAE) and np.isclose(np.sqrt((err**2).mean()),expected.RMSE)
city=d.groupby(['split','target_start'])[['observed_demand','predicted_demand','baseline_demand']].sum().reset_index();table('cnn_city_counts',city)
fig,ax=plt.subplots(figsize=(10,4));a=city[city.split=='development'];
for col,label in [('observed_demand','Actual'),('predicted_demand','Softplus'),('baseline_demand','Historical mean')]:ax.plot(a.target_start,a[col],label=label)
ax.set(xlabel='Target start (UTC)',ylabel='City requests / 30 minutes');ax.legend();save('cnn_city_development',fig,fpath,'March 16 New York development — city totals')
fig,ax=plt.subplots(1,2,figsize=(10,4))
for axis,g in zip(ax,[27,57]):
 a=d[(d.split=='development')&(d.Grid_ID==g)]
 for col,label in [('observed_demand','Actual'),('predicted_demand','Softplus'),('baseline_demand','Historical mean')]:axis.plot(a.target_start,a[col],label=label)
 axis.set(title=f'Grid {g}',xlabel='UTC target start',ylabel='Requests / 30 minutes');axis.legend(fontsize=7)
save('cnn_high_low_grids',fig,fpath,'March 16 — representative training-ranked high (27) and low (57) demand grids')
gridpath='data/processed/spatial_3km_jan_mar_2026/grid_raster_mapping.parquet';grid=pd.read_parquet(R/gridpath);print('grid columns',grid.columns.tolist())
# Raster coordinates are persisted; never infer cell positions from Grid_ID.
row=next(c for c in grid if c.lower() in ('row','raster_row'));col=next(c for c in grid if c.lower() in ('col','column','raster_col'));gid=next(c for c in grid if c.lower() in ('grid_id','gridid'))
sources[gridpath]=hashlib.sha256((R/gridpath).read_bytes()).hexdigest();a=d[d.split=='development'];a=a[a.target_start==a.target_start.min()].merge(grid,left_on='Grid_ID',right_on=gid)
fig,axes=plt.subplots(1,3,figsize=(11,4));vmax=a.observed_demand.max()
for axis,field,title in zip(axes,['observed_demand','predicted_demand','error'],['Actual','Softplus','Actual − predicted']):
 a['error']=a.observed_demand-a.predicted_demand;z=np.full((16,16),np.nan);z[a[row].astype(int),a[col].astype(int)]=a[field];im=axis.imshow(z,cmap='coolwarm' if field=='error' else 'viridis',vmin=-vmax if field=='error' else 0,vmax=vmax);axis.set(title=title,xlabel='Raster column',ylabel='Raster row');fig.colorbar(im,ax=axis,shrink=.7,label='Requests')
save('cnn_spatial_error',fig,fpath,'March 16 00:00–00:30 NY — persisted true-grid raster')
w=read(S+'weighting_comparison.csv');table('sensitivity_weighting',w)
fig,ax=plt.subplots(figsize=(10,4))
for name,g in w.groupby('weighting'):ax.errorbar(np.arange(len(g))+(0.07 if name=='uniform_bins' else -.07),g['mean'],yerr=g.SD,fmt='o',label=name)
ax.set(xticks=np.arange(w.condition.nunique()),xticklabels=w.condition.unique(),ylabel='Sensitivity mean ± population SD');ax.tick_params(axis='x',rotation=30);ax.legend();save('sensitivity_weighting',fig,S+'weighting_comparison.csv','Jan 1–March 15 descriptive comparison; overlapping conditioning pools')
c=read('results_v2/simulation/2026-11-17_prospective_acceptance_v1/sampling_contract.json');stats=[];fig,ax=plt.subplots(figsize=(10,4))
for name,p in c['conditions'].items():
 v=np.asarray(p['values']);weights=np.asarray(p['probabilities']);order=np.argsort(v);ax.step(v[order],np.cumsum(weights[order]),where='post',label=name);mean=float(weights@v);stats.append(dict(pool=name,mean=mean,SD=float(np.sqrt(weights@((v-mean)**2))),minimum=v.min(),maximum=v.max(),represented_requests=sum(p['request_counts'])))
ax.set(xlabel='Positive binned sensitivity (dimensionless)',ylabel='Request-weighted empirical CDF');ax.legend(fontsize=6,ncol=2);save('sensitivity_conditional_support',fig,'prospective_acceptance_v1/sampling_contract.json','January–February prospective pools; no parametric tails');table('prospective_sensitivity',pd.DataFrame(stats))
a=read(S+'assigned_population_proportions.csv');table('sensitivity_group_proportions',a);fig,ax=plt.subplots(figsize=(8,4));ax.bar(a.assigned_condition,a.fraction*100);ax.set(ylabel='Population (%)');ax.tick_params(axis='x',rotation=30);save('sensitivity_group_counts',fig,S+'assigned_population_proportions.csv','Jan 1–March 15 assigned groups — disjoint population shares')
a=read(S+'acceptance_impact.csv');fig,axes=plt.subplots(1,2,figsize=(10,4))
for ax,method in zip(axes,['uniform_bins','request_count_weighted_bins']):
 b=a[(a.condition=='GLOBAL')&(a.method==method)&(a.distance_km.isin([3.,10.,30.]))]
 for distance,g in b.groupby('distance_km'):ax.plot(g.factor,g.acceptance,'o-',label=f'{distance:g} km')
 ax.set(title=method.replace('_',' '),xlabel='Offered factor',ylabel='Acceptance probability');ax.legend(fontsize=8)
save('sensitivity_acceptance',fig,S+'acceptance_impact.csv','Jan1–March15 saved diagnostics; population probabilities, not causal willingness-to-pay')
v=read(P+'validation.json');ep=read(P+'episode_metrics.csv');slots=read(P+'slot_metrics.json');table('completed_episode_results',ep)
assert len(slots)==32 and v['episodes']==2 and slots[-1]['updates']==256 and sum(len(s['losses']) for s in slots)==256
assert np.isclose(ep.revenue.sum(),ep.supported_reward.sum()+ep.fallback_revenue.sum())
fig,ax=plt.subplots(1,2,figsize=(10,4));x=np.arange(len(ep))
for i,field in enumerate(['requests','accepted','assigned']):ax[0].bar(x+(i-1)*.25,ep[field],.25,label=field)
ax[0].set(xticks=x,xticklabels=ep.episode,xlabel='Episode',ylabel='Requests');ax[0].legend();ax[1].bar(ep.episode,ep.revenue/ep.requests);ax[1].set(xlabel='Episode',ylabel='Revenue / eligible request (USD)');save('dqn_episode_outcomes',fig,P+'episode_metrics.csv','March 1 00:00–16:00 NY — exploratory training, not policy evaluation')
fig,ax=plt.subplots(2,2,figsize=(10,7));s=np.arange(1,33)
ax[0,0].plot(s,[r['epsilon_after'] for r in slots]);ax[0,0].set(xlabel='Elapsed slot',ylabel='Exploration epsilon')
loss=np.array([l for r in slots for l in r['losses']]);ax[0,1].plot(np.arange(1,len(loss)+1),loss,lw=.6);ax[0,1].set(yscale='log',xlabel='Pricing optimizer update',ylabel='Half-squared Bellman loss')
ax[1,0].plot(s,[r['replay']['retained'] for r in slots]);ax[1,0].set(ylabel='Retained replay transitions',xlabel='Elapsed slot')
ax[1,1].plot(s,[r['replay']['zero_reward_fraction']*100 for r in slots]);ax[1,1].set(ylabel='Zero-reward replay (%)',xlabel='Elapsed slot')
save('dqn_learning_replay',fig,P+'slot_metrics.json','March 1 training diagnostics — 256 optimizer and soft-target updates')
fig,ax=plt.subplots(1,2,figsize=(10,4));ax[0].plot(s,[r['routing_updates'] for r in slots],label='Local updates');ax[0].set(xlabel='Slot',ylabel='Local updates');ax[1].plot(s,[r['federation_round'] for r in slots]);ax[1].set(xlabel='Slot',ylabel='Cumulative equal-client rounds');save('federation_progress',fig,P+'slot_metrics.json','March 1 — genuine local updates, NONPRIVATE federation')
control='results_v2/federated_learning/2026-11-17_online_routing_rng_retry_002/control_comparison.csv';a=read(control);table('routing_control',a);fig,ax=plt.subplots(1,2,figsize=(10,4));ax[0].plot(a.slot,a.mean_abs_probability_difference,'o-');ax[0].set(xlabel='March 12 slot',ylabel='Mean absolute probability difference');ax[1].plot(a.slot,a.revenue_difference,'o-');ax[1].set(xlabel='March 12 slot',ylabel='Learned − control revenue (USD)');save('routing_control',fig,control,'Routing changes; unchanged physical outcomes under private utility and exploratory pricing')
fig,ax=plt.subplots(1,2,figsize=(10,4));ax[0].bar(ep.episode,ep.supported_reward,label='Supported reward');ax[0].bar(ep.episode,ep.fallback_revenue,bottom=ep.supported_reward,label='Fallback revenue');ax[0].set(xlabel='Episode',ylabel='USD');ax[0].legend();ax[1].bar(ep.episode,ep.charging_events);ax[1].set(xlabel='Episode',ylabel='Charging event records');save('simulation_reconciliation',fig,P+'episode_metrics.csv','Seven charging records are not seven completed sessions')
table('figure_manifest',pd.DataFrame(manifest));(O/'figure_sources.json').write_text(json.dumps(sources,indent=2))
print('figures',len(manifest),'metrics and chronology checks passed')
