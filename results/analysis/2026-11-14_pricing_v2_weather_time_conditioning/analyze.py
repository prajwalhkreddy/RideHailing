"""Time-preserving V2 grouping diagnostics; never reads development/test trip data."""
from pathlib import Path
import json,hashlib,itertools
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage,cut_tree
from scipy.spatial.distance import squareform
from sklearn.metrics import silhouette_score,adjusted_rand_score
O=Path(__file__).resolve().parent
C=Path('results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json')
T={'T1':[0,4],'T2':[4,6],'T3':[6,16],'T4':[16,24]}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def js(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False,default=lambda a:a.item() if isinstance(a,np.generic) else str(a))+'\n')
def tg(hour):
 if not 0<=hour<24:raise ValueError('Invalid hour')
 return 'T1' if hour<4 else 'T2' if hour<6 else 'T3' if hour<16 else 'T4'
def pair(a,b,threshold=100,omit=None):
 shared=[t for t in T if t!=omit and t in a and t in b and a[t]['N']>=threshold and b[t]['N']>=threshold]
 sq=[(a[t][f]-b[t][f])**2 for t in shared for f in ['mean','SD']]
 raw=float(np.sqrt(sum(sq))) if sq else None
 return shared,raw,raw/np.sqrt(len(sq)) if sq else None

def matrix(stats,threshold=100,omit=None,eligible=None):
 # Majority of four groups (3); leave-one-out keeps majority of remaining three (2).
 overlap=3 if omit is None else 2
 codes=sorted(c for c,a in stats.items() if sum(x['N']>=threshold for t,x in a.items() if t!=omit)>=overlap)
 if eligible is not None:codes=[c for c in codes if c in eligible]
 # Requiring >=3/4 support alone can still leave a pair with only2 shared groups.
 # Remove least temporally supported / least observed member of an incompatible pair, reproducibly.
 while True:
  bad=[(a,b) for a,b in itertools.combinations(codes,2) if len(pair(stats[a],stats[b],threshold,omit)[0])<overlap]
  if not bad:break
  contenders=set(sum(([a,b] for a,b in bad),[]))
  drop=min(contenders,key=lambda c:(sum(x['N']>=threshold for t,x in stats[c].items() if t!=omit),sum(x['N'] for x in stats[c].values()),-c))
  codes.remove(drop)
 d=np.zeros((len(codes),len(codes)))
 for i,j in itertools.combinations(range(len(codes)),2):d[i,j]=d[j,i]=pair(stats[codes[i]],stats[codes[j]],threshold,omit)[2]
 return codes,d

def partition(d,k):
 if k==1:return np.zeros(len(d),dtype=int)
 if k==len(d):return np.arange(len(d))
 return cut_tree(linkage(squareform(d,checks=True),method='average'),n_clusters=k).ravel()
def main():
 c=json.loads(C.read_text())
 for p,h in c['source_hashes'].items():assert sha(p)==h,p
 assert sha(c['population_path'])==c['population_sha256']
 f=pd.read_parquet(c['population_path'])
 assert f.pickup_timestamp.ge('2026-01-01').all() and f.pickup_timestamp.lt('2026-03-16').all()
 f=f.loc[f.is_runtime_candidate,['pickup_timestamp','weather_code','hour','epsilon','r_P']].copy()
 assert len(f)==5779213 and np.isfinite(f.epsilon).all() and f.epsilon.ge(0).all() and f.r_P.abs().ge(.05).all()
 assert f.weather_code.notna().all() and np.equal(f.weather_code,f.weather_code.astype(int)).all()
 f['weather_code']=f.weather_code.astype(int);f['T_group']=f.hour.map(tg);f['date']=f.pickup_timestamp.dt.date
 rows=[];stats={}
 for (code,t),g in f.groupby(['weather_code','T_group'],sort=True):
  a=g.epsilon.to_numpy();q=np.quantile(a,[.05,.25,.5,.75,.95,.99]);r=dict(weather_code=int(code),T_group=t,N=len(a),distinct_dates=g.date.nunique(),mean=float(a.mean()),SD=float(a.std()),median=float(q[2]),P05=q[0],P25=q[1],P75=q[3],P95=q[4],P99=q[5],minimum=float(a.min()),maximum=float(a.max()),N_ge100=len(a)>=100,N_ge50=len(a)>=50,SD_lt4=a.std()<4)
  rows.append(r);stats.setdefault(int(code),{})[t]=r
 pd.DataFrame(rows).to_csv(O/'weather_code_time_statistics.csv',index=False)
 support={c:dict(N=sum(a['N'] for a in ts.values()),dates=int(f.loc[f.weather_code.eq(c),'date'].nunique()),T_groups=[t for t,a in ts.items() if a['N']>=100]) for c,ts in stats.items()}
 rule=dict(T_group_definitions=T,primary_N=100,secondary_N=50,minimum_shared_T_groups=3,minimum_overlap_reason='Strict majority of four approved time groups; no fabricated values. Pairwise-incompatible codes removed by lower supported-group count, then lower N, then descending code.',normalization='sqrt(sum squared mean/SD differences / compared_feature_count)',leave_one_out_overlap=2,features='unscaled',support=support)
 js(O/'preclustering_support_rule.json',rule)
 codes,d=matrix(stats);pairs=[]
 for a,b in itertools.combinations(sorted(stats),2):
  shared,raw,norm=pair(stats[a],stats[b]);pairs.append(dict(weather_code_a=a,weather_code_b=b,shared_T_groups='|'.join(shared),compared_feature_count=2*len(shared),raw_distance=raw,normalized_distance=norm,support_flag='SUPPORTED' if len(shared)>=3 else 'INSUFFICIENT_OVERLAP'))
 pd.DataFrame(pairs).to_csv(O/'weather_pairwise_distances.csv',index=False)
 pd.DataFrame(d,index=codes,columns=codes).to_csv(O/'clustering_distance_matrix.csv')
 candidates=[];stability=[]
 for k in range(1,len(codes)+1):
  labels=partition(d,k);same=labels[:,None]==labels[None,:];upper=np.triu(np.ones_like(d,dtype=bool),1)
  scores=[]
  perturbations=[('omit_'+t,100,t,codes) for t in T]+[('N50',50,None,None),('N200',200,None,None),('exclude_dates_lt5',100,None,[c for c in codes if support[c]['dates']>=5])]
  for name,n,omit,subset in perturbations:
   cc,dd=matrix(stats,n,omit,subset);common=sorted(set(codes)&set(cc))
   if k>len(cc) or len(common)<2:continue
   ll=partition(dd,k);ari=float(adjusted_rand_score([labels[codes.index(c)] for c in common],[ll[cc.index(c)] for c in common]));scores.append(ari)
   stability.append(dict(K=k,check=name,N_codes=len(cc),common_codes=len(common),ARI=ari,membership=json.dumps({str(c):int(l) for c,l in zip(cc,ll)},sort_keys=True)))
  candidates.append(dict(K=k,memberships=json.dumps([list(np.asarray(codes)[labels==i].astype(int).tolist()) for i in sorted(set(labels))]),silhouette=float(silhouette_score(d,labels,metric='precomputed')) if 1<k<len(codes) else None,minimum_cluster_codes=int(np.bincount(labels).min()),represented_N=sum(support[c]['N'] for c in codes),excluded_codes=json.dumps(sorted(set(stats)-set(codes))),within_distance=float(d[upper&same].mean()) if (upper&same).any() else None,between_distance=float(d[upper&~same].mean()) if (upper&~same).any() else None,minimum_stability_ARI=min(scores),median_stability_ARI=float(np.median(scores))))
 pd.DataFrame(candidates).to_csv(O/'weather_cluster_candidates.csv',index=False);pd.DataFrame(stability).to_csv(O/'weather_cluster_stability.csv',index=False)
 hourly=Path('results/analysis/2026-11-14_pricing_v2_denominator_rule_selection/weather_hour_secondary_diagnostics.csv');h=pd.read_csv(hourly);h=h.loc[(h.record_type=='cell')&(h.rule_id=='C')].copy();assert int(h.N.sum())==len(f)
 h.to_csv(O/'reused_weather_hour_diagnostics.csv',index=False)
 js(O/'analysis_verification.json',dict(source_hashes_verified=True,source_hashes={**c['source_hashes'],str(C):sha(C),c['population_path']:sha(c['population_path']),str(hourly):sha(hourly)},N=len(f),mean=f.epsilon.mean(),median=f.epsilon.median(),SD=f.epsilon.std(ddof=0),codes=codes,excluded_codes=sorted(set(stats)-set(codes)),mean_range=[min(r['mean'] for r in rows),max(r['mean'] for r in rows)],SD_range=[min(r['SD'] for r in rows),max(r['SD'] for r in rows)],hourly_cells=len(h),hourly_max_SD=h.SD.max(),March17_31_untouched=True))
 print(pd.DataFrame(candidates)[['K','silhouette','minimum_cluster_codes','minimum_stability_ARI','median_stability_ARI']].to_string(index=False));print('eligible',codes,'low support',sorted(set(stats)-set(codes)))
if __name__=='__main__':main()
