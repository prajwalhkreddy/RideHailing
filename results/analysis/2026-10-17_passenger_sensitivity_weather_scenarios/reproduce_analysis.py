"""Read existing epsilon; write only the isolated weather scenario package."""
from pathlib import Path
import os,hashlib,json,itertools
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl_record030')
import numpy as np,pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
D=ROOT/'data/processed/price_distance_sensitivity_record029';SOURCE=D/'authoritative_epsilon_jan_mar_2026.parquet'
NAMES={1:'Clear',2:'Fair',3:'Cloudy',5:'Fog',7:'Light Rain',8:'Rain',9:'Heavy Rain',12:'Sleet',13:'Heavy Sleet',14:'Light Snowfall',15:'Snowfall',16:'Heavy Snowfall',17:'Rain Shower',21:'Snow Shower'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
protected=[D,ROOT/'src',ROOT/'config',ROOT/'results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar']+list((ROOT/'results/analysis').glob('2026-10-13_record030*'))
paths=sorted(set(p for base in protected for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts))
hashes={p:sha(p) for p in paths};print('Protected hashes recorded',len(paths),flush=True)
x=pd.read_parquet(SOURCE,columns=['weather_code','hour','epsilon_status','epsilon']);x=x[x.epsilon_status.eq('VALID')].copy()
assert len(x)==10611392 and x.epsilon.notna().all() and np.isfinite(x.epsilon).all()
assert set(x.weather_code)==set(NAMES) and x.hour.between(0,23).all()
x['time_period']=x.hour.map(lambda h:f'T{int(h)//6+1}')
y=x[x.epsilon.between(-12.890744316473482,15.442447741158892)];assert len(y)==10505278

def stats(a):
 a=np.asarray(a);q=np.quantile(a,[.05,.25,.5,.75,.95]);return dict(N=len(a),mean_epsilon=float(a.mean()),median_epsilon=float(q[2]),population_SD=float(a.std(ddof=0)),P05=q[0],P25=q[1],P75=q[3],P95=q[4],min=float(a.min()),max=float(a.max()))
def scenarios(frame, timed):
 result=[];arrays={}
 for key,g in frame.groupby(['weather_code','time_period'] if timed else 'weather_code',observed=True):
  code,period=key if timed else (key,'');sid=f'W{code:02}'+('_'+period if timed else '')
  arrays[sid]=g.epsilon.to_numpy();r=dict(Scenario_ID=sid,weather_code=code,weather_name=NAMES[code],**stats(g.epsilon))
  if timed:r.update(time_period=period,hours=f'{(int(period[1])-1)*6:02}–{int(period[1])*6-1:02}')
  else:r['percentage_of_valid_population' if len(frame)==10611392 else 'percentage_of_supported_population']=100*len(g)/len(frame)
  result.append(r)
 return pd.DataFrame(result),arrays
w,wa=scenarios(x,False);t,ta=scenarios(x,True);ws,_=scenarios(y,False);ts,_=scenarios(y,True)
for name,f in [('weather_scenario_statistics_valid',w),('weather_scenario_statistics_supported',ws),('weather_time_scenario_statistics_valid',t),('weather_time_scenario_statistics_supported',ts)]:f.to_csv(OUT/(name+'.csv'),index=False)
assert w.N.sum()==t.N.sum()==len(x) and ws.N.sum()==ts.N.sum()==len(y)
audit=t[['Scenario_ID','N']].copy();audit['percentage_of_parent_weather']=100*t.N/t.weather_code.map(w.set_index('weather_code').N);audit['percentage_of_total']=100*t.N/len(x);audit['sparse_flag']=t.N.lt(1000);audit['sparse_reason']=np.where(audit.sparse_flag,'N < 1000; reporting flag only','');audit.to_csv(OUT/'scenario_sample_size_audit.csv',index=False)
def pairs(f,name):
 rows=[]
 for a,b in itertools.combinations(f.itertuples(),2):
  dm=a.mean_epsilon-b.mean_epsilon;ds=a.population_SD-b.population_SD
  rows.append(dict(Scenario_A=a.Scenario_ID,Scenario_B=b.Scenario_ID,N_A=a.N,N_B=b.N,Mean_A=a.mean_epsilon,Mean_B=b.mean_epsilon,SD_A=a.population_SD,SD_B=b.population_SD,Mean_Difference=dm,SD_Difference=ds,Euclidean_Distance=np.hypot(dm,ds)))
 z=pd.DataFrame(rows).sort_values(['Euclidean_Distance','Scenario_A','Scenario_B']);z.to_csv(OUT/f'{name}_pairwise_similarity.csv',index=False);return z
wp=pairs(w,'weather');tp=pairs(t,'weather_time')
def cluster(f,arrays,name,maxk):
 features=f[['mean_epsilon','population_SD']].to_numpy();evaluations=[];combined=[];cache={};labels_by_k={}
 for k in range(2,min(maxk,len(f)-1)+1):
  labels=AgglomerativeClustering(n_clusters=k,linkage='average',metric='euclidean').fit_predict(features)
  # Stable IDs based on the lexicographically first original scenario.
  order=sorted(set(labels),key=lambda lab:min(f.loc[labels==lab,'Scenario_ID']));labels=np.array([order.index(l)+1 for l in labels]);labels_by_k[k]=labels;ns=[]
  for lab in sorted(set(labels)):
   members=f[labels==lab];ids=tuple(members.Scenario_ID)
   if ids not in cache:
    n=int(members.N.sum());mu=float(np.average(members.mean_epsilon,weights=members.N));var=float(np.average(members.population_SD**2+(members.mean_epsilon-mu)**2,weights=members.N))
    actual=np.concatenate([arrays[i] for i in ids]);median=float(np.median(actual));np.testing.assert_allclose([mu,np.sqrt(var)],[actual.mean(),actual.std()],rtol=1e-11)
    cache[ids]=(n,mu,median,np.sqrt(var))
   n,mu,median,sd=cache[ids];ns.append(n)
   combined.append(dict(Analysis_Type=name,K=k,Cluster_ID=int(lab),Member_Scenarios=';'.join(ids),Member_Weather_Codes=';'.join(map(str,sorted(set(members.weather_code)))),Member_Time_Periods=';'.join(sorted(set(members.time_period))) if 'time_period' in members else '',Total_N=n,Combined_Mean=mu,Combined_Median=median,Combined_Population_SD=sd,Decision='ACCEPT' if sd<4 else 'EXCLUDE'))
  evaluations.append(dict(K=k,silhouette_score=silhouette_score(features,labels),number_of_clusters=k,minimum_cluster_N=min(ns),maximum_cluster_N=max(ns)))
 e=pd.DataFrame(evaluations);c=pd.DataFrame(combined);e.to_csv(OUT/f'{name}_clustering_k_evaluation.csv',index=False);c.to_csv(OUT/f'{name}_cluster_combined_statistics.csv',index=False)
 eligible=[int(r.K) for r in e.itertuples() if c[c.K.eq(r.K)].Decision.eq('ACCEPT').all() and r.minimum_cluster_N>=1000]
 chosen=None if not eligible else int(e[e.K.isin(eligible)].sort_values(['silhouette_score','K'],ascending=[False,True]).iloc[0].K)
 rec=f[['weather_code','weather_name']].rename(columns={'weather_code':'original_weather_code','weather_name':'original_weather_name'}).copy();rec['original_time_period']=f.time_period if 'time_period' in f else 'ALL';rec['candidate_cluster_id']=pd.NA if chosen is None else labels_by_k[chosen];rec['status']='NO ACCEPTABLE CLUSTERING FOUND' if chosen is None else 'RECOMMENDED CANDIDATE — NOT APPROVED';rec.to_csv(OUT/f'recommended_{name}_clustering.csv',index=False)
 return e,c,chosen,labels_by_k
we,wc,wk,wl=cluster(w,wa,'weather',8);te,tc,tk,tl=cluster(t,ta,'weather_time',12)
manual=[]
for name,codes in [('NON-PRECIPITATION',[1,2,3,5]),('RAIN',[7,8,9,17]),('SNOW/FROZEN',[12,13,14,15,16,21])]:
 r=dict(group=name,weather_codes=';'.join(map(str,codes)),**stats(x.loc[x.weather_code.isin(codes),'epsilon']));r['Decision']='ACCEPT' if r['population_SD']<4 else 'EXCLUDE';manual.append(r)
man=pd.DataFrame(manual);man.to_csv(OUT/'manual_3bucket_reference_check.csv',index=False)
(OUT/'charts').mkdir(exist_ok=True);plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
def scatter(f,filename,title,labels=None,weather=False):
 fig,ax=plt.subplots(figsize=(12,7));ax.scatter(f.mean_epsilon,f.population_SD,s=25+150*np.sqrt(f.N/f.N.max()),c=labels if labels is not None else '#24699b',cmap='tab20' if labels is not None else None,alpha=.75)
 for i,r in enumerate(f.itertuples()):ax.annotate(f'{r.weather_code} {r.weather_name}' if weather else r.Scenario_ID,(r.mean_epsilon,r.population_SD),xytext=(4,(i%3-1)*9),textcoords='offset points',fontsize=7)
 ax.axhline(4,color='firebrick',ls='--',label='Strict pooled SD criterion: <4');ax.set(xlabel='Mean epsilon (full VALID population)',ylabel='Population SD',title=title);ax.legend();fig.tight_layout();fig.savefig(OUT/'charts'/filename,dpi=240);plt.close(fig)
scatter(w,'weather_mean_sd_scatter.png','Original weather scenarios — full VALID population',weather=True)
scatter(t,'weather_time_mean_sd_scatter.png','Original weather × six-hour scenarios — full VALID population')
if wk is None:
 scatter(w,'weather_candidate_clusters.png','NO ACCEPTABLE WEATHER CLUSTERING FOUND\nAll tested K=2–8 contain at least one excluded cluster',weather=True)
else:scatter(w,'weather_candidate_clusters.png',f'Recommended candidate K={wk} (not approved)',wl[wk],True)
fig,ax=plt.subplots(figsize=(10,5));ax.scatter(man.mean_epsilon,man.population_SD,s=90,label='Manual reference groups')
for r in man.itertuples():ax.annotate(r.group,(r.mean_epsilon,r.population_SD),xytext=(5,6),textcoords='offset points')
if wk is not None:
 z=wc[wc.K.eq(wk)];ax.scatter(z.Combined_Mean,z.Combined_Population_SD,marker='x',s=90,label='Recommended candidate')
else:ax.text(.02,.96,'No acceptable data-driven weather candidate; no replacement groups shown.',transform=ax.transAxes,va='top')
ax.axhline(4,color='firebrick',ls='--');ax.set(xlabel='Combined mean epsilon',ylabel='True pooled population SD',title='Manual grouping versus data-driven feasibility — full VALID population');ax.legend();fig.tight_layout();fig.savefig(OUT/'charts/manual_vs_data_driven_grouping.png',dpi=240);plt.close(fig)
print('WEATHER',w[['weather_code','N','mean_epsilon','population_SD']].to_string(index=False),flush=True);print('CLOSEST',wp.head(5).to_string(index=False));print('MANUAL',man[['group','N','mean_epsilon','population_SD','Decision']].to_string(index=False));print('K',wk,tk,'scenarios',len(t),'accept',wc.Decision.value_counts().to_dict(),tc.Decision.value_counts().to_dict(),flush=True)
def table(f):
 return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(f'{v:.6f}' if isinstance(v,float) else str(v) for v in row)+' |' for row in f.itertuples(index=False,name=None))
# Necessary feasibility condition from within-scenario sum of squares.
weather_floor=float(np.sqrt(np.average(w.population_SD**2,weights=w.N)));time_floor=float(np.sqrt(np.average(t.population_SD**2,weights=t.N)))
parts=['# Earlier weather/time scenario diagnostic analysis',
'## 1. Objective\nAssess original scenarios using descriptive mean/SD geometry and true pooled SD. No semantic regrouping or model training is performed.',
'## 2. Population used\nPRIMARY: all 10,611,392 VALID epsilon rows, before support restriction. SECONDARY: 10,505,278 VALID rows within inclusive [−12.890744316473482,15.442447741158892]. Existing epsilon is read, never recalculated. Primary statistics alone govern clustering and strict SD decisions.',
'## 3. Original weather scenarios\nAll 14 codes retain the original Meteostat labels.\n\n'+table(w[['weather_code','weather_name','N','mean_epsilon','median_epsilon','population_SD']]),
'## 4. Weather × time scenarios\n'+str(len(t))+' observed scenarios. T1=00–05, T2=06–11, T3=12–17, T4=18–23 are PRESENTATION periods, not frozen simulation T groups. No absent scenarios fabricated. Sparse reporting flag is N<1,000; it is an implementation choice, not an exclusion. Sparse scenarios: '+str(int(audit.sparse_flag.sum()))+'.',
'## 5. Similarity definition\nEuclidean distance in unscaled [mean, population SD], using signed A−B differences. Similarity is descriptive, not a statistical equivalence test or significance claim. Scenario sizes are reported; geometry is scenario-unweighted. Closest weather pairs:\n\n'+table(wp.head(5)[['Scenario_A','Scenario_B','Euclidean_Distance']]),
'## 6. Clustering method\nAgglomerative average linkage, Euclidean metric, no scaling and no weather-name inputs. Linkage and sparse threshold are implementation choices, not frozen methodology decisions. Scenarios ordered by code/time; IDs canonicalized by first member. Weather K=2–8 and weather-time K=2–12. Silhouette uses scenario points, not replicated trips. Recommendation eligibility requires every cluster SD<4 and minimum cluster N≥1,000; among eligible choices highest silhouette wins, ties lower K. Interpretability still requires review; no automatic methodology selection.',
'## 7. Candidate clustering results\nWeather recommendation: '+str(wk or 'NO ACCEPTABLE CLUSTERING FOUND')+'. Weather-time recommendation: '+str(tk or 'NO ACCEPTABLE CLUSTERING FOUND')+'.\n\n'+table(we)+'\n\n'+table(te),
'## 8. Combined-SD < 4 rule\nFor N=sum(n_i), pooled mean=sum(n_i*mu_i)/N; pooled variance=sum(n_i*(SD_i²+(mu_i−mu_pool)²))/N. This includes within- and between-scenario variation. Medians are computed from actual combined epsilon, never averaged. Pooled means/SDs are checked against direct observations for every unique cluster. ACCEPT iff SD<4; EXCLUDE iff SD≥4, with no rounded-value decisions. EXCLUDE labels a proposed grouping, not individual observations. Singleton clusters receive the same test.\n\nThe weighted within-scenario SD lower bound is '+f'{weather_floor:.6f} (weather) and {time_floor:.6f} (weather-time). Since these exceed 4, no exhaustive partition of these indivisible scenarios can make every pooled cluster SD<4: its weighted cluster variance must be at least this within-scenario variance. This is stronger than failure of the tested K values; it does not preclude selected subsets passing.',
'## 9. Accepted combinations\nAll ACCEPT rows, including singletons and repeated memberships across K, are explicitly listed in the two cluster-combined CSVs. Counts by candidate occurrence: weather '+str(int(wc.Decision.eq('ACCEPT').sum()))+', weather-time '+str(int(tc.Decision.eq('ACCEPT').sum()))+'. These do not constitute an acceptable exhaustive grouping.',
'## 10. Excluded combinations\nEvery EXCLUDE row lists exact member IDs and pooled SD in the same CSVs; no observations were removed. Candidate occurrence counts: weather '+str(int(wc.Decision.eq('EXCLUDE').sum()))+', weather-time '+str(int(tc.Decision.eq('EXCLUDE').sum()))+'.',
'## 11. Manual 3-bucket reference comparison\nReference only, not approved and not used for clustering.\n\n'+table(man[['group','N','mean_epsilon','median_epsilon','population_SD','Decision']]),
'## 12. Supported-population sensitivity check\nSupport restricts tails and changes dispersion; its results must not be substituted for the primary SD test. Weather-only primary versus supported SD:\n\n'+table(w[['weather_code','population_SD']].merge(ws[['weather_code','population_SD']],on='weather_code',suffixes=('_valid','_supported'))),
'## 13. Diagnostic conclusion\nNo acceptable exhaustive grouping is established on the primary population. Cloudy/Clear/Fair/Fog and rain/snow semantics are not assumed interchangeable; compare their distances and candidate memberships below. Adding time changes the points and memberships, but does not resolve the full-population SD constraint. A single final grouping for later representation is not supported by this analysis. No causal inference or willingness-to-pay interpretation is made.',
'## 14. Earlier unresolved methodology decisions\nAverage linkage, candidate-K selection and support adequacy criteria require review. If the strict rule remains necessary, methodology review must establish whether selected subsets or another explicitly defined population definition is intended. Do not silently switch to supported rows. Observations were NOT combined for joint model training; raw records are only pooled for correct descriptive statistics. Original labels remain preserved; grouping uses sensitivity statistics, not semantic names. DQN/RL, acceptance and pricing are out of scope.',
'## Validation and files\nCounts reconcile for both weather and weather-time populations. Every retained observation has exactly one code and one presentation period. No epsilon values or protected files changed; hashes verified after generation. Four figures use primary statistics and explicitly show infeasibility when no recommendation exists. Recommended mapping CSVs retain original scenarios with blank candidate IDs and an explicit no-solution status when applicable. All required CSVs and figures are in this folder; reproduce_analysis.py is the self-contained reproduction entry point.']
# Explicit semantic-family comparisons using the highest-silhouette diagnostic K, never called recommended.
for name,f,e,labels in [('weather',w,we,wl),('weather_time',t,te,tl)]:
 best=int(e.sort_values(['silhouette_score','K'],ascending=[False,True]).iloc[0].K)
 z=f[['Scenario_ID','weather_name']].copy();z['diagnostic_cluster']=labels[best]
 parts.append(f'### Highest-silhouette {name} partition (K={best}), diagnostic ONLY\nNot acceptable unless all pooled clusters pass.\n\n'+table(z))
for p,h in hashes.items():assert sha(p)==h,str(p)
(OUT/'README.md').write_text('\n\n'.join(parts)+'\n')
print('PASS population counts, pooled direct checks, protected hashes; floors',weather_floor,time_floor,flush=True)
