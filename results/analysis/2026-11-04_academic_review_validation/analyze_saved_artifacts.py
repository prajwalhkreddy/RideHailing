from pathlib import Path
import json,ast
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('results/analysis/2026-11-04_academic_review_validation')
def dump(name,x):
 (R/name).write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
def save(name):
 plt.tight_layout();plt.savefig(R/name,dpi=160);plt.close()
def qstats(x):
 q=np.quantile(x,[0,.01,.05,.25,.5,.75,.95,.99,1]);return dict(zip(['min','P1','P5','P25','median','P75','P95','P99','max'],map(float,q)),mean=float(np.mean(x)))
print('HISTORICAL_READ',flush=True)
h=pd.read_parquet('data/processed/price_distance_sensitivity_record029/cleaned_price_distance_jan_mar_2026.parquet',columns=['fare','trip_distance'])
assert len(h)==10620409 and h.trip_distance.between(0,100,inclusive='right').all()
h['trip_distance_km']=h.trip_distance*1.609344
edges=[0,1,2,3,3.17,4,5,7.5,10,15,np.inf];labels=['0–1','1–2','2–3','3–3.17','3.17–4','4–5','5–7.5','7.5–10','10–15','15+']
h['bin']=pd.cut(h.trip_distance_km,edges,labels=labels,right=True)
rows=[]
for name,g in h.groupby('bin',observed=True):
 rows.append(dict(distance_bin_km=str(name),N=len(g),mean_trip_distance_km=g.trip_distance_km.mean(),median_trip_distance_km=g.trip_distance_km.median(),mean_fare_USD=g.fare.mean(),median_fare_USD=g.fare.median(),min_fare_USD=g.fare.min(),P10_fare_USD=g.fare.quantile(.1),P90_fare_USD=g.fare.quantile(.9),max_fare_USD=g.fare.max(),unique_fare_values=g.fare.nunique()))
b=pd.DataFrame(rows);assert b.N.sum()==len(h);b.to_csv(R/'historical_distance_fare_bins_km.csv',index=False)
short=h[h.trip_distance_km<=3]
common=short.fare.value_counts().head(10)
repeated=[]
for fare,n in common.items():
 g=short[short.fare==fare];repeated.append(dict(fare_USD=float(fare),N=int(n),percentage_short=100*n/len(short),unique_trip_distances=int(g.trip_distance_km.nunique()),minimum_trip_distance_km=g.trip_distance_km.min(),maximum_trip_distance_km=g.trip_distance_km.max()))
summary=dict(N=len(h),source='data/processed/price_distance_sensitivity_record029/cleaned_price_distance_jan_mar_2026.parquet',source_unit='miles; retained only as source provenance',reporting_unit='km',bin_rule='(lower,upper]; last (15,infinity)',distance_distribution_km=qstats(h.trip_distance_km),short_trip_counts={str(v):int((h.trip_distance_km<=v).sum()) for v in [1,2,3,3.17]},short_fare_distribution_USD=qstats(short.fare),short_unique_fares=int(short.fare.nunique()),short_top_exact_fares=repeated,global_mean_fare_USD=h.fare.mean(),interpretation='Repeated exact fares do not establish a minimum-fare tariff. Inspect changing bin means/medians, wide within-bin ranges and shared fare values. No inferred cleaning or pricing rule.')
dump('distance_fare_summary.json',summary)
s=h.iloc[np.linspace(0,len(h)-1,100000,dtype=int)]
fig,ax=plt.subplots(figsize=(9,5));hb=ax.hexbin(s.trip_distance_km,s.fare,gridsize=100,bins='log',mincnt=1,cmap='viridis');fig.colorbar(hb,ax=ax,label='Sample observations (log colour)');ax.set(xlabel='Historical trip distance (km)',ylabel='TLC fare_amount (USD)',title='Historical distance and fare: Jan–Mar 2026\nDeterministic 100,000-row display; full-population statistics in CSV');save('distance_vs_historical_fare_km.png')
del h,short,s
print('CNN_SAVED_PREDICTIONS',flush=True)
p='models/cnn/jan_mar_2026_3km_30min_continued/test_predictions.parquet';f=pd.read_parquet(p);a=f.observed_demand.to_numpy(float);v=f.predicted_demand.to_numpy(float);e=a-v
mse=np.mean(e**2);rmse=np.sqrt(mse)
row=dict(source=p,start=str(f.forecast_timestamp.min()),end=str(f.forecast_timestamp.max()),N=len(f),valid_grids=f.Grid_ID.nunique(),mean_actual=a.mean(),mean_predicted=v.mean(),MAE=np.abs(e).mean(),MSE=mse,RMSE=rmse,R2=1-np.sum(e**2)/np.sum((a-a.mean())**2),NRMSE_percentage=100*rmse/a.mean(),volume_error_percentage=100*abs(v.sum()-a.sum())/a.sum(),actual_total=a.sum(),predicted_total=v.sum(),**{'error_'+k:val for k,val in qstats(e).items()},error_positive_percentage=100*np.mean(e>1e-12),error_negative_percentage=100*np.mean(e< -1e-12),error_approximately_zero_percentage=100*np.mean(np.abs(e)<=1e-12),error_zero_tolerance=1e-12)
assert len(f)==768*142
saved=json.loads(Path('results/analysis/2026-10-19_final_cnn_performance_diagnosis/summary.json').read_text())['continued_test']
for k in ['MAE','RMSE','R2']:np.testing.assert_allclose(row[k],saved[k],rtol=1e-10)
pd.DataFrame([row]).to_csv(R/'cnn_validation_summary.csv',index=False)
fig,ax=plt.subplots(figsize=(7,6));hb=ax.hexbin(a,v,gridsize=90,mincnt=1,bins='log');fig.colorbar(hb,ax=ax,label='Grid-slot observations (log colour)');lim=max(a.max(),v.max());ax.plot([0,lim],[0,lim],'k--',label='Equality');ax.set(xlabel='Actual demand per grid-slot',ylabel='Saved predicted demand per grid-slot',title='Final CNN: saved March 16–31 evaluation');ax.legend();save('cnn_actual_vs_predicted.png')
fig,ax=plt.subplots(figsize=(9,5));ax.hist(e,bins=160,log=True);ax.axvline(0,color='black',linestyle='--');ax.set(xlabel='Actual − predicted demand',ylabel='Grid-slot count (log scale)',title='Saved CNN prediction errors: full error range\nPositive = underprediction; negative = overprediction');save('cnn_prediction_error_distribution.png')
print('DQN_SAVED_METRICS',flush=True)
d=pd.read_csv('models/pricing_dqn/final_nonprivate_multiepisode_seed42/episode_metrics.csv');d=d[(d.episode<=25)&(d.slots_completed==16)].copy();assert len(d)==25 and list(d.episode)==list(range(1,26))
d['assignment_rate']=d.assignments/d.requests;d['accepted_assignment_rate']=d.assignments/d.accepted;d['rejection_rate']=d.rejected/d.requests;d['mean_offered_price_USD']='NOT PERSISTED';d['median_offered_price_USD']='NOT PERSISTED'
counts=np.array([ast.literal_eval(x) for x in d.action_counts]);assert counts.shape==(25,7)
for i,factor in enumerate([.85,.90,.95,1,1.05,1.1,1.15]):
 d[f'action_{factor:.2f}_count']=counts[:,i];d[f'action_{factor:.2f}_percentage']=100*counts[:,i]/counts.sum(axis=1)
d['action_count_unit']='OD-context pricing decisions; not request count';d.to_csv(R/'dqn_episode_summary.csv',index=False)
for file,y,label,title in [('dqn_reward_by_episode.png','revenue','Gross assigned fare / reward (USD)','Authoritative training episodes 1–25: early trend only')]:
 fig,ax=plt.subplots(figsize=(9,5));ax.plot(d.episode,d[y],marker='o');ax.set(xlabel='Complete episode',ylabel=label,title=title);save(file)
fig,ax=plt.subplots(figsize=(9,5));ax.plot(d.episode,100*d.acceptance_rate,'o-',label='Accepted');ax.plot(d.episode,100*d.rejection_rate,'o-',label='Rejected');ax.set(xlabel='Complete episode',ylabel='Percentage of generated requests',title='Passenger responses through episode 25');ax.legend();save('acceptance_rejection_by_episode.png')
fig,ax=plt.subplots(figsize=(9,4));ax.set(xlim=(1,25),xlabel='Complete episode',ylabel='Mean offered price (USD)',title='Average offered price by episode');ax.text(.5,.5,'NOT PERSISTED\nNo episode-level offered-price series is available.\nRevenue / assignments is not substituted for offered price.',ha='center',va='center',transform=ax.transAxes);ax.set_yticks([]);save('average_offered_price_by_episode.png')
fig,ax=plt.subplots(figsize=(10,5))
for i,factor in enumerate([.85,.9,.95,1,1.05,1.1,1.15]):ax.plot(d.episode,100*counts[:,i]/counts.sum(axis=1),label=f'{factor:.2f}')
ax.set(xlabel='Complete episode',ylabel='Percentage of OD-context action selections',title='Training pricing-factor frequency (epsilon-greedy)');ax.legend(ncol=7,fontsize=8);save('pricing_action_frequency_by_episode.png')
fig,ax=plt.subplots(figsize=(9,5));ax.plot(d.optimizer_updates,d.mean_loss,'o-',label='Saved episode-mean loss at ending update')
mon={}
for ep in [10,25]:
 m=json.loads(Path(f'results/analysis/2026-10-31_final_nonprivate_pricing_training/monitoring_episode_{ep:04d}.json').read_text());mon[str(ep)]=m;ax.scatter(m['optimizer_updates'],m['mean_loss'],s=80,marker='x',label=f'Episode {ep} saved monitor')
ax.set(xlabel='Cumulative optimizer updates at checkpoint',ylabel='Saved mean Huber loss',title='Q-network loss: checkpoint summaries, not per-update history');ax.legend(fontsize=8);save('q_loss_by_update.png')
dump('dqn_review_summary.json',dict(complete_episodes=25,slots=400,totals={k:float(d[k].sum()) for k in ['requests','accepted','rejected','assignments','unmatched','revenue']},episode25=d.iloc[-1].to_dict(),monitoring=mon,pricing_policy_converged=False,partial_episode26_excluded=True))
print('SAVED_ANALYSIS_COMPLETE',flush=True)
