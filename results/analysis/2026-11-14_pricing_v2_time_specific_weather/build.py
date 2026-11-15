"""Independent within-time weather grouping; no simulation or training."""
from pathlib import Path
import hashlib,json,itertools
import numpy as np,pandas as pd
from scipy.cluster.hierarchy import linkage,cut_tree
from scipy.spatial.distance import pdist,squareform
from sklearn.metrics import silhouette_score,adjusted_rand_score
O=Path(__file__).resolve().parent
OLD=Path('results/analysis/2026-11-14_pricing_v2_weather_time_conditioning')
C=Path('results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json')
T={'T1':[0,4],'T2':[4,6],'T3':[6,16],'T4':[16,24]}
VERSION='WEATHER_TIME_CONDITIONED_V2_2026_11_14'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def js(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n')
def time_group(h):
 if not isinstance(h,(int,np.integer)) or not 0<=h<24:raise ValueError('Invalid hour')
 return 'T1' if h<4 else 'T2' if h<6 else 'T3' if h<16 else 'T4'
def labels(x,k):
 if k==1:return np.zeros(len(x),int)
 if k==len(x):return np.arange(len(x))
 return cut_tree(linkage(pdist(x),method='average'),n_clusters=k).ravel()
def quality(x,k):
 l=labels(x,k);d=squareform(pdist(x));u=np.triu(np.ones(d.shape,bool),1);s=l[:,None]==l
 return l,dict(silhouette=float(silhouette_score(x,l)) if 1<k<len(x) else None,minimum_cluster_codes=int(np.bincount(l).min()),within_distance=float(d[u&s].mean()) if (u&s).any() else None,between_distance=float(d[u&~s].mean()) if (u&~s).any() else None)
def choose(rows):
 # Explicit conservative engineering criteria, not inferential statistical thresholds.
 good=[r for r in rows if r['K']>1 and r['silhouette'] is not None and r['silhouette']>=.25 and r['minimum_cluster_codes']>=2 and r['stability_median']>=.75 and r['stability_p10']>=.5]
 if not good:return None
 peak=max(r['silhouette'] for r in good)
 return min((r for r in good if r['silhouette']>=peak-.02),key=lambda r:r['K'])
def summary(a):
 q=np.quantile(a,[.05,.25,.5,.75,.95,.99]);return dict(N=len(a),mean=float(a.mean()),median=float(q[2]),SD=float(a.std()),P05=q[0],P25=q[1],P75=q[3],P95=q[4],P99=q[5],minimum=float(a.min()),maximum=float(a.max()),SD_lt4=bool(a.std()<4))
def main():
 c=json.loads(C.read_text())
 for p,h in c['source_hashes'].items():assert sha(p)==h,p
 assert sha(c['population_path'])==c['population_sha256']
 sourcehash={str(C):sha(C),c['population_path']:c['population_sha256'],str(OLD/'weather_code_time_statistics.csv'):sha(OLD/'weather_code_time_statistics.csv')}
 policy=dict(primary_N=100,secondary_N=50,selection='Silhouette>=0.25, no single-code clusters, median perturbation ARI>=0.75, P10 ARI>=0.50. Among eligible cuts within0.02 silhouette of best, choose smallest K. Otherwise T_GROUP_POOLED_FALLBACK.',criteria_status='PROJECT_ENGINEERING_ACCEPTANCE_CRITERIA_NOT_STATISTICAL_SIGNIFICANCE',bootstrap='20 date-block resamples per T, seed42; same dates weighted across codes',feature_perturbation='20 independent 1% multiplicative perturbations, seed42',support_variations=[50,100],date_subset='alternating chronological dates; also exclude codes with<5 dates',fallback_minimum_N=5000)
 js(O/'selection_protocol.json',policy)
 f=pd.read_parquet(c['population_path'],columns=['epsilon','is_runtime_candidate','pickup_timestamp','weather_code','hour','r_P']);assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
 f=f.loc[f.is_runtime_candidate].copy();assert len(f)==5779213 and np.isfinite(f.epsilon).all() and f.epsilon.ge(0).all() and f.r_P.abs().ge(.05).all();f['weather_code']=f.weather_code.astype(int);f['T_group']=f.hour.map(time_group);f['date']=f.pickup_timestamp.dt.normalize();f['sq']=f.epsilon**2
 stats=pd.read_csv(OLD/'weather_code_time_statistics.csv');stats.to_csv(O/'weather_code_time_statistics.csv',index=False);assert int(stats.N.sum())==len(f)
 daily=f.groupby(['T_group','date','weather_code']).agg(N=('epsilon','size'),total=('epsilon','sum'),sq=('sq','sum')).reset_index()
 candidates=[];stability=[];mapping=[];selected={};rng=np.random.default_rng(42);ranges=[]
 for t in T:
  base=stats.loc[(stats.T_group==t)&stats.N.ge(100)].sort_values('weather_code');codes=base.weather_code.astype(int).tolist();x=base[['mean','SD']].to_numpy();ranges.append(dict(T_group=t,mean_min=float(x[:,0].min()),mean_max=float(x[:,0].max()),SD_min=float(x[:,1].min()),SD_max=float(x[:,1].max())))
  variations=[];secondary=stats.loc[(stats.T_group==t)&stats.N.ge(50)].sort_values('weather_code');variations.append(('N50',secondary.weather_code.astype(int).tolist(),secondary[['mean','SD']].to_numpy()))
  good=base.loc[base.distinct_dates.ge(5)];variations.append(('exclude_dates_lt5',good.weather_code.astype(int).tolist(),good[['mean','SD']].to_numpy()))
  dd=daily.loc[daily.T_group==t].copy();dates=sorted(dd.date.unique());all_dates=np.array(dates)
  def aggregate(weights):
   z=dd.copy();z['w']=z.date.map(weights).fillna(0);z[['N','total','sq']]=z[['N','total','sq']].multiply(z.w,axis=0);g=z.groupby('weather_code')[['N','total','sq']].sum();g=g.loc[g.N.ge(100)];g['mean']=g.total/g.N;g['SD']=np.sqrt(np.maximum(0,g.sq/g.N-g['mean']**2));return g.index.astype(int).tolist(),g[['mean','SD']].to_numpy()
  for i in range(20):
   counts=rng.multinomial(len(dates),np.full(len(dates),1/len(dates)));cc,xx=aggregate(dict(zip(dates,counts)));variations.append(('date_bootstrap_'+str(i),cc,xx))
  for parity in [0,1]:
   cc,xx=aggregate({d:1 for d in dates[parity::2]});variations.append(('alternating_dates_'+str(parity),cc,xx))
  for i in range(20):variations.append(('feature_1pct_'+str(i),codes,x*(1+rng.uniform(-.01,.01,x.shape))))
  tr=[]
  for k in range(1,len(codes)+1):
   ll,q=quality(x,k);aris=[]
   for name,cc,xx in variations:
    common=sorted(set(codes)&set(cc))
    if len(cc)<k or len(common)<3:continue
    alt=labels(xx,k);a=[ll[codes.index(v)] for v in common];b=[alt[cc.index(v)] for v in common];ari=float(adjusted_rand_score(a,b));aris.append(ari);pairs=list(itertools.combinations(range(len(a)),2));agree=sum((a[i]==a[j])==(b[i]==b[j]) for i,j in pairs)/len(pairs)
    stability.append(dict(T_group=t,K=k,check=name,common_codes=len(common),ARI=ari,co_membership_agreement=agree))
   r=dict(T_group=t,K=k,**q,represented_N=int(base.N.sum()),minimum_code_dates=int(base.distinct_dates.min()),membership=json.dumps([np.asarray(codes)[ll==i].tolist() for i in sorted(set(ll))]),stability_median=float(np.median(aris)),stability_p10=float(np.quantile(aris,.1)),deterministic_rerun=bool(np.array_equal(ll,labels(x,k))))
   candidates.append(r);tr.append(r)
  win=choose(tr);selected[t]=None if win is None else win['K'];ll=None if win is None else labels(x,win['K'])
  for code in sorted(f.weather_code.unique()):
   found=stats.loc[(stats.T_group==t)&(stats.weather_code==code)];row=found.iloc[0] if len(found) else None;supported=row is not None and row.N>=100
   group=f'{t}_G{int(ll[codes.index(code)])+1}' if win is not None and supported else ''
   mapping.append(dict(raw_weather_code=int(code),T_group=t,time_specific_weather_group=group,N=int(row.N) if row is not None else 0,distinct_dates=int(row.distinct_dates) if row is not None else 0,mean_epsilon=float(row['mean']) if row is not None else None,sd_epsilon=float(row.SD) if row is not None else None,support_status='SUPPORTED' if supported else 'LOW_SUPPORT_OR_UNOBSERVED',assignment_type='CLUSTERED' if group else 'T_GROUP_POOLED_FALLBACK' if win is None else 'CELL_FALLBACK',cluster_stability=win['stability_median'] if group else None,fallback_required=not bool(group)))
 pd.DataFrame(candidates).to_csv(O/'weather_cluster_candidates.csv',index=False);pd.DataFrame(stability).to_csv(O/'weather_cluster_stability.csv',index=False);pd.DataFrame(ranges).to_csv(O/'feature_ranges.csv',index=False);mf=pd.DataFrame(mapping);mf.to_csv(O/'weather_time_group_mapping.csv',index=False)
 # Explicit raw-code weather-only fallback avoids implying permanent cross-time group identity.
 out=Path('data/interim/pricing_v2_sensitivity/time_specific_weather_2026_11_14');out.mkdir(exist_ok=True)
 supports=[]
 def save(sid,a,members,t,level):
  a=np.asarray(a,dtype='<f8');path=out/(sid+'.npy');np.save(path,a,allow_pickle=False);supports.append(dict(support_id=sid,member_raw_weather_codes=json.dumps(members),T_group=t,level=level,path=str(path),support_hash=sha(path),**summary(a)))
 save('GLOBAL',f.epsilon.to_numpy(),sorted(f.weather_code.unique().tolist()),'ALL',3)
 for t in T:save(t+'_POOLED',f.loc[f.T_group==t,'epsilon'].to_numpy(),sorted(f.loc[f.T_group==t,'weather_code'].unique().tolist()),t,2)
 for code,g in f.groupby('weather_code'):save('RAW_'+str(code),g.epsilon.to_numpy(),[int(code)],'ALL',1)
 for group,g in mf.loc[mf.time_specific_weather_group!=''].groupby('time_specific_weather_group'):
  t=g.T_group.iloc[0];members=g.raw_weather_code.tolist();save(group,f.loc[(f.T_group==t)&f.weather_code.isin(members),'epsilon'].to_numpy(),members,t,0)
 pd.DataFrame(supports).to_csv(O/'conditional_support_manifest.csv',index=False);pd.DataFrame(supports).drop(columns=['path']).to_csv(O/'conditional_support_statistics.csv',index=False)
 contract=dict(methodology_version=VERSION,population_version=c['methodology_version'],denominator_rule=c['denominator_rule'],epsilon_policy='finite nonnegative; no sign transformation or new truncation',T_group_definitions=T,feature_definition='independent per-T mean and population SD',support_rule=policy,distance_metric='sqrt(delta_mean^2+delta_SD^2)',feature_scaling='UNSCALED',clustering_method='deterministic average linkage sorted raw codes',cluster_selection_rule=policy['selection'],stability_rule=policy,selected_K_per_T=selected,mapping=mapping,mapping_hash=sha(O/'weather_time_group_mapping.csv'),conditional_support_manifest_hash=sha(O/'conditional_support_manifest.csv'),fallback_policy={'version':'TIME_SPECIFIC_RAW_WEATHER_FALLBACK_1','minimum_N':5000,'levels':['exact time-specific group','same raw weather code pooled across T','T pooled','global'],'ungroupable_T':'Explicit T_GROUP_POOLED_FALLBACK bypasses raw-weather fallback to avoid reintroducing unsupported weather separation within that T','unknown_code':'explicit T-only then global fallback','rationale':'No permanent behavioural group exists across T; weather-only means same raw code, not union of changing cluster memberships.'},source_artifacts=list(sourcehash),source_hashes=sourcehash,P_base=c['P_base'],L_base=c['L_base'],canonical_contract=str(C),sampling='EMPIRICAL_RESAMPLING_WITH_REPLACEMENT',minimum_runtime_epsilon='positive required by unchanged inverse-epsilon threshold; observed zero count0',status='FROZEN_OFFLINE_NOT_RUNTIME_VALIDATED')
 assert (f.epsilon>0).all();js(O/'weather_time_grouping_contract.json',contract)
 trajectory=[]
 for code,g in mf.groupby('raw_weather_code'):
  row={'weather_code':int(code)};peers=[]
  for t in T:
   r=g.loc[g.T_group==t].iloc[0];row[t+'_group']=r.time_specific_weather_group or r.assignment_type
   peers.append(set(mf.loc[(mf.T_group==t)&(mf.time_specific_weather_group==r.time_specific_weather_group)&(mf.time_specific_weather_group!=''),'raw_weather_code'])-{code})
  observed=g.N.ge(100).sum();same=sum(peers[i]==peers[j] for i,j in itertools.combinations(range(4),2));row['pattern']='INSUFFICIENT_SUPPORT' if observed<4 else 'STABLE_ACROSS_TIME' if same==6 else 'PARTIALLY_TIME_DEPENDENT' if same else 'STRONGLY_TIME_DEPENDENT';trajectory.append(row)
 pd.DataFrame(trajectory).to_csv(O/'weather_time_trajectory.csv',index=False);js(O/'build_verification.json',dict(N=len(f),source_hashes_verified=True,selected_K_per_T=selected,March17_31_untouched=True,training_started=False));print(selected)
if __name__=='__main__':main()
