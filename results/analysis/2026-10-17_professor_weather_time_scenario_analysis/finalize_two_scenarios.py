"""Professor-approved analytical weather mapping; no epsilon reconstruction."""
from pathlib import Path
import os,hashlib
os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl_record030')
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;R=O.parents[2];D=R/'data/processed/price_distance_sensitivity_record029'
names={1:'Clear',2:'Fair',3:'Cloudy',5:'Fog',7:'Light Rain',8:'Rain',9:'Heavy Rain',12:'Sleet',13:'Heavy Sleet',14:'Light Snowfall',15:'Snowfall',16:'Heavy Snowfall',17:'Rain Shower',21:'Snow Shower'}
clear={1,2,3,5};mapping={c:'CLEAR' if c in clear else 'RAIN' for c in names}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
protected=[D,R/'src',R/'config',R/'results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar']+list((R/'results/analysis').glob('2026-10-13_record030*'))
hashes={p:sha(p) for b in protected for p in b.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
x=pd.read_parquet(D/'authoritative_epsilon_jan_mar_2026.parquet',columns=['source_row_index','weather_code','hour','epsilon_status','epsilon']);x=x[x.epsilon_status.eq('VALID')&x.epsilon.between(-12.890744316473482,15.442447741158892)].copy()
assert len(x)==10505278 and x.source_row_index.is_unique and set(x.weather_code)==set(names)
x['original_weather_name']=x.weather_code.map(names);x['final_weather_scenario']=x.weather_code.map(mapping);assert x.final_weather_scenario.notna().all()
x['period']=x.hour.map(lambda h:['00-05','06-11','12-17','18-23'][int(h)//6])
def st(g):
 a=g.epsilon.to_numpy();q=np.quantile(a,[.05,.25,.5,.75,.95]);codes=sorted(g.weather_code.unique());return dict(weather_code=';'.join(map(str,codes)),original_weather_name=';'.join(names[c] for c in codes),final_weather_scenario=g.final_weather_scenario.iloc[0],N=len(a),mean_epsilon=a.mean(),median_epsilon=q[2],population_SD=a.std(ddof=0),P05=q[0],P25=q[1],P75=q[3],P95=q[4])
counts=x.weather_code.value_counts();m=pd.DataFrame([dict(weather_code=c,original_weather_name=names[c],final_weather_scenario=mapping[c],scenario_interpretation='NON-PRECIPITATION CONDITIONS' if c in clear else 'PRECIPITATION CONDITIONS, including liquid, frozen and mixed precipitation',N=int(counts[c]),percentage_of_supported_population=100*counts[c]/len(x)) for c in names]);m.to_csv(O/'final_weather_2scenario_mapping.csv',index=False)
f=pd.DataFrame([st(g) for _,g in x.groupby('final_weather_scenario')]);f['percentage']=100*f.N/len(x);f['Combined_Population_SD']=f.population_SD;f['Decision']=np.where(f.population_SD<4,'ACCEPT','EXCLUDE');f.to_csv(O/'final_clear_rain_statistics.csv',index=False)
h=pd.DataFrame([dict(hour=int(hour),**st(g)) for (_,hour),g in x.groupby(['final_weather_scenario','hour'])]);h.to_csv(O/'final_clear_rain_hourly_statistics.csv',index=False)
t=pd.DataFrame([dict(six_hour_period=period,**st(g)) for (_,period),g in x.groupby(['final_weather_scenario','period'])]);t.to_csv(O/'final_clear_rain_six_hour_statistics.csv',index=False)
old=pd.DataFrame([dict(definition='OLD_LITERAL',**st(x[x.weather_code.eq(c)])) for c in [1,8]]);comp=pd.concat([old,pd.DataFrame([dict(definition='FINAL_ANALYTICAL',**st(g)) for _,g in x.groupby('final_weather_scenario')])],ignore_index=True);comp.to_csv(O/'old_vs_final_clear_rain_comparison.csv',index=False)
assert len(h)==48 and len(t)==8 and f.N.sum()==h.N.sum()==t.N.sum()==m.N.sum()==len(x)
for scenario,g in x.groupby('final_weather_scenario'):
 z=h[h.final_weather_scenario.eq(scenario)];assert set(z.hour)==set(range(24));mu=np.average(z.mean_epsilon,weights=z.N);sd=np.sqrt(np.average(z.population_SD**2+(z.mean_epsilon-mu)**2,weights=z.N));row=f[f.final_weather_scenario.eq(scenario)].iloc[0];np.testing.assert_allclose([mu,sd],[row.mean_epsilon,row.population_SD],rtol=1e-12)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
for col,label,fn in [('mean_epsilon','Mean passenger price-distance sensitivity','mean'),('population_SD','Population SD of passenger price-distance sensitivity','sd')]:
 fig,ax=plt.subplots(figsize=(11,5))
 for scenario,color in [('CLEAR','#2166ac'),('RAIN','#b35806')]:
  z=h[h.final_weather_scenario.eq(scenario)].set_index('hour').reindex(range(24));line,=ax.plot(z.index,z[col],'-o',label=scenario.title(),color=color);np.testing.assert_equal(line.get_ydata(),z[col].values)
 ax.set(xlabel='Hour of day',ylabel=label,xticks=range(24),title=label+'\nFinal analytical weather scenarios; frozen P0.5–P99.5 support');ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(O/f'charts/final_clear_rain_hourly_{fn}.png',dpi=300);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,5))
for ax,col,label in zip(axes,['mean_epsilon','population_SD'],['Mean','Population SD']):
 for j,(scenario,color) in enumerate([('CLEAR','#2166ac'),('RAIN','#b35806')]):
  z=t[t.final_weather_scenario.eq(scenario)].sort_values('six_hour_period');bars=ax.bar(np.arange(4)+(j-.5)*.36,z[col],.36,label=scenario.title(),color=color);np.testing.assert_equal([b.get_height() for b in bars],z[col].values)
 ax.set(xticks=range(4),xticklabels=['00–05','06–11','12–17','18–23'],xlabel='Six-hour presentation period',ylabel=label);ax.grid(axis='y',alpha=.2)
axes[0].legend(loc='upper center',bbox_to_anchor=(.5,1.13),ncol=2,frameon=False);fig.suptitle('Final analytical Clear/Rain scenarios\nFrozen P0.5–P99.5 support');fig.tight_layout();fig.savefig(O/'charts/final_clear_rain_six_hour_comparison.png',dpi=300);plt.close(fig)
def table(df):
 return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(f'{v:.6f}' if isinstance(v,float) else str(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))
archive=O/'README_supported_clustering_diagnostic.md'
if not archive.exists():archive.write_text((O/'README.md').read_text())
text='''# Final professor-approved two-scenario passenger sensitivity analysis

## Final Two Weather Scenarios

The original dataset contains 14 Meteostat weather codes. For the final passenger-sensitivity analysis these are consolidated into two analytical scenarios:

- **CLEAR (display: Clear)** = non-precipitation conditions: 1 Clear, 2 Fair, 3 Cloudy, 5 Fog.
- **RAIN (display: Rain)** = precipitation conditions, including liquid, frozen and mixed precipitation: 7 Light Rain, 8 Rain, 9 Heavy Rain, 12 Sleet, 13 Heavy Sleet, 14 Light Snowfall, 15 Snowfall, 16 Heavy Snowfall, 17 Rain Shower, 21 Snow Shower.

“Clear” does not imply literally clear skies for every observation. “Rain” is an analytical precipitation label and includes snow/sleet. Original Meteostat code/name remain retained for traceability. This is the professor-approved analytical mapping, not the earlier data-driven K=2 split.

## Population and unchanged method

Use existing authoritative epsilon with epsilon_status=VALID and inclusive frozen support [−12.890744316473482,15.442447741158892]: **10,505,278 observations**. Epsilon is not recomputed. Record-029 references, denominator treatment and simulation methodology remain unchanged. No runtime weather classification or passenger acceptance is modified by this analysis.

## Final pooled results and strict SD rule

'''+table(f[['final_weather_scenario','N','percentage','mean_epsilon','median_epsilon','population_SD','Decision']])+'''

Population SD is computed directly from all constituent supported observations (ddof=0), not averaged over weather-code SDs. Independent pooled-hour variance checks include between-hour mean differences. ACCEPT iff SD<4, EXCLUDE iff SD≥4; decisions use unrounded values. Both scenarios pass independently.

## Hourly and six-hour presentation

Each final scenario has observations in all 24 hours: 48 hourly rows total. There are eight six-hour rows, using 00–05, 06–11, 12–17 and 18–23. These are presentation periods only, not the frozen simulation time groups. The new plots use these final pooled observations, never the old literal code-1/code-8 curves.

## Old versus final scope

The old literal comparison selected only codes 1 and 8: 3,050,121+215,014=3,265,135 observations. The final mapping covers every supported code and adds **7,240,143** observations to the reporting scope, without changing support or source rows. Increases are 6,563,335 in Clear and 676,808 in Rain.

'''+table(comp[['definition','final_weather_scenario','N','mean_epsilon','median_epsilon','population_SD']])+'''

## Traceability and files

Every new CSV retains weather_code, original_weather_name and final_weather_scenario. In pooled aggregate rows, weather_code and original_weather_name are aligned semicolon-separated constituent lists, because a pooled statistic has multiple original codes; no single original code is fabricated. The mapping CSV has one row per original code. The original authoritative Parquet remains unchanged; added labels exist only in the analytical working frame and outputs.

- final_weather_2scenario_mapping.csv: exhaustive one-to-one original-code mapping, counts and percentages.
- final_clear_rain_statistics.csv: final pooled summaries and strict decisions.
- final_clear_rain_hourly_statistics.csv: 48 observed scenario/hour summaries.
- final_clear_rain_six_hour_statistics.csv: eight presentation summaries.
- old_vs_final_clear_rain_comparison.csv: literal versus analytical scopes on the same support.
- charts/final_clear_rain_hourly_mean.png and charts/final_clear_rain_hourly_sd.png: final hourly plots.
- charts/final_clear_rain_six_hour_comparison.png: mean and population SD panels.
- finalize_two_scenarios.py: reproduction entry point for this final representation.

## Diagnostic provenance

The previous Heavy Snowfall versus all-other-weather K=2 mapping, manual three-bucket references, unrestricted analysis and their figures/CSVs are retained as diagnostic history only. They are NOT the final weather representation. Prior supported-clustering README is preserved as README_supported_clustering_diagnostic.md; unrestricted report remains README_unrestricted_diagnostic.md. Earlier reproduction scripts reproduce historical diagnostics and must not be mistaken for the current final mapping.

## Validation and interpretation

CLEAR+RAIN counts, original-code counts, hourly counts and six-hour counts each reconcile to 10,505,278. All 14 codes map exactly once; source_row_index is unique and final labels are exhaustive, so no supported observation is dropped or duplicated. Protected source/Record-029/Record-030/runtime/config hashes were checked unchanged. Figure values match their CSV statistics. All calculations are descriptive; no predictive/RL training or causal willingness-to-pay inference is performed.
'''
for p,v in hashes.items():assert sha(p)==v,str(p)
(O/'README.md').write_text(text)
print(f.to_string(index=False));print('PASS counts, unique identifiers, all hours, direct/pooled SD, plot values, protected hashes')
