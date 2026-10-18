"""Supported-population clarification; preserve unrestricted diagnostic files."""
from pathlib import Path
import ast,hashlib,itertools,os
import numpy as np,pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];D=ROOT/'data/processed/price_distance_sensitivity_record029'
NAMES={1:'Clear',2:'Fair',3:'Cloudy',5:'Fog',7:'Light Rain',8:'Rain',9:'Heavy Rain',12:'Sleet',13:'Heavy Sleet',14:'Light Snowfall',15:'Snowfall',16:'Heavy Snowfall',17:'Rain Shower',21:'Snow Shower'}
source=(OUT/'reproduce_analysis.py').read_text()
for node in ast.parse(source).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['sha','stats','scenarios','pairs','cluster','table']:
  code=ast.get_source_segment(source,node)
  if node.name in ['pairs','cluster']:code=code.replace('.csv', '_supported.csv')
  exec(code)
protected=[D,ROOT/'src',ROOT/'config',ROOT/'results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar']+list((ROOT/'results/analysis').glob('2026-10-13_record030*'))
files=[p for b in protected for p in b.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
# Preserve every previous numerical output, including supported scenario summaries.
files+=list(OUT.glob('*.csv'));hashes={p:sha(p) for p in files}
x=pd.read_parquet(D/'authoritative_epsilon_jan_mar_2026.parquet',columns=['epsilon_status','epsilon','weather_code','hour']);assert x.epsilon_status.eq('VALID').sum()==10611392
x=x[x.epsilon_status.eq('VALID')&x.epsilon.between(-12.890744316473482,15.442447741158892)].copy();assert len(x)==10505278
x['time_period']=x.hour.map(lambda h:f'T{int(h)//6+1}')
w,wa=scenarios(x,False);t,ta=scenarios(x,True)
for name,f in [('weather',w),('weather_time',t)]:
 old=pd.read_csv(OUT/f'{name}_scenario_statistics_supported.csv');pd.testing.assert_frame_equal(f,old,check_dtype=False,rtol=1e-12,atol=1e-12)
wp=pairs(w,'weather');tp=pairs(t,'weather_time');we,wc,wk,wl=cluster(w,wa,'weather',8);te,tc,tk,tl=cluster(t,ta,'weather_time',12)
manual=[]
for name,codes in [('NON-PRECIPITATION',[1,2,3,5]),('RAIN',[7,8,9,17]),('SNOW/FROZEN',[12,13,14,15,16,21])]:
 r=dict(group=name,weather_codes=';'.join(map(str,codes)),**stats(x.loc[x.weather_code.isin(codes),'epsilon']));r['Decision']='ACCEPT' if r['population_SD']<4 else 'EXCLUDE';manual.append(r)
man=pd.DataFrame(manual);man.to_csv(OUT/'manual_3bucket_reference_check_supported.csv',index=False)
print('WEATHER K\n',we.to_string(index=False));print('TIME K\n',te.to_string(index=False));print('INITIAL',wk,tk)
for name,c in [('weather',wc),('weather_time',tc)]:
 for k in [2,3,4]:print(name,k,c[c.K.eq(k)][['Member_Scenarios','Total_N','Combined_Population_SD']].to_string(index=False))
print('CLOSEST',wp.head(5).to_string(index=False));print('MANUAL',man[['group','N','mean_epsilon','population_SD']].to_string(index=False));print('TIME max',t.population_SD.max())
for p,h in hashes.items():assert sha(p)==h,str(p)
print('PASS: preserved existing artifacts, pooled direct checks, counts; supported scenarios reused unchanged')
# Recommendation is explicitly justified by complexity/support comparisons, not score alone.
assert wk==tk==2
assert wc.Decision.eq('ACCEPT').all() and tc.Decision.eq('ACCEPT').all()
archive=OUT/'README_unrestricted_diagnostic.md'
if not archive.exists():archive.write_text((OUT/'README.md').read_text())
pooled=stats(x.epsilon)
parts=['# Supported weather/time scenario analysis — clarified decision population',
'## 1. Professor clarification and authority\nThe strict combined population SD < 4 decision rule applies AFTER the already-frozen empirical support restriction. PRIMARY decision population is 10,505,278 supported VALID observations; unrestricted VALID N=10,611,392 is retained ONLY as diagnostic evidence of tail sensitivity. Support was frozen before this weather clustering decision and was not introduced merely to make SD < 4 pass. No epsilon, support, reference or behavioural method changed.',
'## 2. Populations and unchanged scenario definitions\nInclusive support: [−12.890744316473482,15.442447741158892]; epsilon_status=VALID. All 14 original labels remain unchanged. There are 48 observed weather × six-hour scenarios: T1 00–05, T2 06–11, T3 12–17, T4 18–23. These remain presentation periods and do not replace frozen simulation T groups. Missing scenarios are not fabricated. Existing supported scenario CSVs were independently verified and reused byte-for-byte.',
'## 3. Supported weather results\nAll 14 individual weather scenarios satisfy strict SD<4.\n\n'+table(w[['weather_code','weather_name','N','mean_epsilon','median_epsilon','population_SD']]),
'## 4. Similarity and clustering implementation\nUnscaled Euclidean distance=sqrt((mean_A−mean_B)^2+(SD_A−SD_B)^2); average-linkage agglomerative clustering, equal scenario weights in feature geometry, population weighting only for combined statistics. Weather names do not enter assignments. Same K ranges as before: weather 2–8; weather/time 2–12. Closest supported pairs:\n\n'+table(wp.head(5)[['Scenario_A','Scenario_B','Euclidean_Distance']])+'\n\nThese are descriptive statistical similarities, not tested equivalence of full distributions.',
'## 5. Candidate K comparison and recommendation\nAll clusters at every evaluated K pass the strict pooled SD rule. That rule alone does not determine a useful K. For weather, K2 silhouette=0.798705 with minimum N=16,123; K3=0.608023 separates Heavy Sleet; K4=0.462833 additionally separates shower scenarios. K3/K4 increase fragmentation without improving silhouette. K5–8 also score below K2 and add groups. K2 is recommended because simplicity, separation and support agree, not because a numeric maximum is automatically approved. Its minority group is only about 0.15% of the population, so transportability still needs review.\n\n'+table(we)+'\n\nAll-weather pooled supported SD is '+f'{pooled["population_SD"]:.6f}'+', also below 4. K1 has no silhouette and was outside the prescribed evaluation range; the SD condition alone cannot establish that two distributions are necessary. K2 is a candidate scenario representation, not a uniquely identified natural partition or a frozen downstream model.',
'## 6. Recommended weather-only candidate\nCluster 1: codes 1,2,3,5,7,8,9,12,13,14,15,17,21. Cluster 2: code16 Heavy Snowfall. Original labels/codes remain in the recommended mapping.\n\n'+table(wc[wc.K.eq(2)][['Cluster_ID','Member_Weather_Codes','Total_N','Combined_Mean','Combined_Median','Combined_Population_SD','Decision']]),
'## 7. True combined SD and acceptance\nPooled mean=sum(n_i*mu_i)/N. Pooled variance=sum(n_i*(SD_i²+(mu_i−mu_pool)²))/N; population SD is its square root. Between-scenario mean differences are included. Medians are calculated from underlying supported observations. Each unique pooled mean/SD was verified against direct observations. ACCEPT strictly means SD<4 on supported data, with no rounding for decisions. No supported candidate clusters were EXCLUDE. Acceptance under this criterion does not approve a grouping methodology or justify a simulation change.',
'## 8. Weather × time candidate and whether time helps\nAll 48 individual scenarios pass; maximum SD='+f'{t.population_SD.max():.6f}'+'. K2 silhouette=0.653741, below weather-only 0.798705; cross-analysis scores concern different scenario units and are descriptive rather than a formal improvement test. K3=0.500042 and K4=0.459027 add subdivisions; K8–12 introduce a 619-observation cluster below the existing N≥1,000 candidate-support preference. No observations are excluded for sparseness.\n\n'+table(te)+'\n\nRecommended time diagnostic K2 isolates W16_T4 (Heavy Snowfall 18–23), N=9,746, SD=2.347770; all remaining scenarios pool to N=10,495,532, SD=1.443476. Thus Heavy Snowfall 00–17 joins the broad cluster, whereas weather-only isolates the whole code. Time reveals variation but does not improve global separation or justify extra grouping complexity on this evidence. Weather-only K2 is the simpler candidate to take for sign-off.\n\n'+table(tc[tc.K.eq(2)][['Cluster_ID','Total_N','Combined_Mean','Combined_Median','Combined_Population_SD','Decision']]),
'## 9. Manual three-bucket reference\nReference only, not automatically approved. All three pass SD<4, but semantic labels did not drive the data-derived clusters. Closest pairs cross semantic families (Cloudy–Snowfall; Sleet–Light Snowfall).\n\n'+table(man[['group','N','mean_epsilon','median_epsilon','population_SD','Decision']]),
'## 10. Professor-facing answers and sign-off\nA: all 14 weather scenarios have SD<4. B: closest is Cloudy–Snowfall, followed by Sleet–Light Snowfall. C: recommend weather-only K2 as a candidate. D/E: pooled SDs 1.443171 and 2.172872, both strictly passing. F: manual three buckets pass, but that alone does not validate semantic grouping. G: time changes some membership but lowers silhouette and does not materially improve the case for a richer representation. H: take weather-only K2 to the professor, alongside the passing manual reference and the caveat that K1 also meets the SD threshold. Final group count, average linkage, support adequacy and downstream distribution representation still require approval.',
'## 11. Diagnostic provenance and file guide\nCurrent decision outputs are the 11 requested CSVs ending `_supported.csv`. The original weather/time supported statistics are unchanged; new supported pairwise, K evaluations, pooled-cluster summaries, recommended mappings and manual reference are added. Recommended mappings preserve original_weather_code, original_weather_name and original_time_period.\n\nEarlier unsuffixed clustering CSVs, `*_valid.csv`, `scenario_sample_size_audit.csv`, and the four existing charts describe the unrestricted diagnostic population ONLY. Their no-acceptable-clustering conclusion is superseded for current decision-making, not deleted or numerically altered. The full earlier report is preserved as README_unrestricted_diagnostic.md. Existing charts are not supported-population decision figures. Do not run legacy reproduce_analysis.py/finalize_presentation.py to produce a current decision report: use update_supported_analysis.py, which implements this clarification.',
'## 12. Validation and scope\nVerified VALID N=10,611,392 and supported N=10,505,278; weather and weather/time supported counts reconcile. Each row maps to one original weather code and one presentation period. Existing scenario values were checked against source observations. Direct-vs-pooled means/SDs agree. Protected-file hashes and all earlier CSV hashes were unchanged after analysis. No epsilon values, support bounds, Record-029/030 files, simulator, acceptance or pricing were changed. No predictive or joint model training performed: records were pooled only for descriptive summaries. Clustering is exploratory analysis; DQN/RL is outside scope.']
(OUT/'README.md').write_text('\n\n'.join(parts)+'\n')
print('Weather-only K2 recommended after K2/K3/K4 and support/complexity comparison; historical README archived.')
