"""Persisted-artifact-only reporting. No simulator/model/clustering imports."""
from pathlib import Path
import hashlib,json,shutil,textwrap,re,zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
A=R/'results/analysis'; T=R/'results/training/pricing_v2_staged_training_001/weather_conditioned'
CAL=A/'2026-11-13_pricing_recalibration_decision_analysis'; DIST=A/'2026-11-14_pricing_v2_sensitivity_distribution_selection'; W=A/'2026-11-14_pricing_v2_time_specific_weather'; DEN=A/'2026-11-14_pricing_v2_denominator_rule_selection'; DYN=A/'2026-11-15_pricing_v2_dynamic_opportunity_audit'
manifest={}; index=[]
CURRENT='CURRENT_AUTHORITATIVE'; HIST='HISTORICAL_SUPERSEDED'; DIAG='DIAGNOSTIC_ONLY'
plt.rcParams.update({'font.size':11,'axes.titlesize':14,'axes.labelsize':11,'figure.dpi':130,'savefig.dpi':160,'axes.spines.top':False,'axes.spines.right':False})
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def src(p):
 p=Path(p).resolve(); rel=str(p.relative_to(R))
 assert not any(x in rel for x in ['mar17','mar31','march17','march31'])
 if rel not in manifest:manifest[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
 return p

def csv(p):return pd.read_csv(src(p))
def js(p):return json.loads(src(p).read_text())
def row(i,title,sources,status=CURRENT,notes='',output=None,existing=''):
 paths=[str(src(p).relative_to(R)) for p in sources]
 index.append(dict(visual_id=i,title=title,requested_by_source='Attached academic-review checklist '+i,current_source_artifact=';'.join(paths),current_or_historical=status,existing_figure_path=existing,regenerate_required=not bool(existing),final_output_path=output or f'charts/{i}.png',notes=notes))
def finish(i,title,sources,scope,status=CURRENT,notes='',fig=None):
 fig=fig or plt.gcf();fig.suptitle(title,fontsize=15,y=.985)
 fig.text(.02,.015,scope+'\n'+status+' | '+Path(sources[0]).name,fontsize=8,color='#444')
 fig.tight_layout(rect=(0,.075,1,.93));path=f'{"appendix" if status==HIST else "charts"}/{i}.png';fig.savefig(O/path);
 if i=='SUMMARY':fig.savefig(O/'review_summary.pdf')
 plt.close(fig)
 row(i,title,sources,status,scope+' | '+notes,path)
def panel(i,title,lines,sources,scope,status=CURRENT):
 fig,ax=plt.subplots(figsize=(11,6));ax.axis('off')
 ax.text(.02,.96,'\n\n'.join(textwrap.fill(str(s),105) for s in lines),va='top',fontsize=12,linespacing=1.4)
 finish(i,title,sources,scope,status,fig=fig)
def line(i,title,d,x,ys,unit,sources,scope,status=CURRENT):
 fig,ax=plt.subplots(figsize=(10,5))
 for y in ys:ax.plot(d[x],d[y],marker='o',ms=3,label=y)
 ax.set(xlabel=x.replace('_',' '),ylabel=unit);
 if all(d[y].min()>=0 for y in ys):ax.set_ylim(bottom=0)
 ax.legend();ax.grid(alpha=.2)
 finish(i,title,sources,scope,status,fig=fig)
def missing(i,title,sources,note):
 row(i,title,sources,DIAG,note,output='');index[-1]['final_output_path']='';index[-1]['coverage_status']='MISSING'
def reuse(i,title,p,scope,note=''):
 target=f'charts/{i}.png';shutil.copy2(src(p),O/target);row(i,title,[p],CURRENT,scope+'; '+note,target,str(p.relative_to(R)))
P=js(DIST/'pricing_v2_sensitivity_contract.json');pb=P['P_base'];lb=P['L_base'];scope='Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD'
b=csv(CAL/'array_a/array_a_verified.csv'); b=b[b.lower_distance_km>=1.5]
assert b.N.sum()==6967155
for i,y,title in [('A1','N','Empirical distance probability by 0.5-km bin'),('A2','N','Trip count by 0.5-km distance bin')]:
 fig,ax=plt.subplots(figsize=(10,5));v=b[y]/b.N.sum() if i=='A1' else b[y];ax.bar(b.centre_km,v,width=.45);ax.set(xlabel='Distance (km)',ylabel='Probability mass' if i=='A1' else 'Trips');ax.axvline(1.5,color='k',ls='--');ax.axvline(75,color='k',ls='--');finish(i,title,[CAL/'array_a/array_a_verified.csv'],scope+' | N=6,967,155; retained [1.5,75) km',fig=fig)
fig,ax=plt.subplots(figsize=(10,5));ax.plot(b.actual_mean_distance_km,b.mean_fare,label='Bin mean fare');ax.axhline(pb,color='C1',ls='--',label='P_base');ax.axvline(lb,color='C2',ls='--',label='L_base');ax.axvspan(1.5,75,color='C0',alpha=.05);ax.set(xlabel='Distance (km)',ylabel='Mean fare (USD)');ax.legend();finish('A3','Distance and mean fare: frozen reference crossing',[CAL/'array_a/array_a_verified.csv',DIST/'pricing_v2_sensitivity_contract.json'],scope+' | P_base originates from [1,75) km, applied unchanged',fig=fig)
fig,ax=plt.subplots(figsize=(10,5));ax.fill_between(b.centre_km,b.P5_fare,b.P95_fare,alpha=.2,label='P05–P95');ax.fill_between(b.centre_km,b.P25_fare,b.P75_fare,alpha=.35,label='P25–P75');ax.plot(b.centre_km,b.median_fare,label='Median');ax.set(xlabel='Distance (km)',ylabel='Fare (USD)');ax.legend();finish('A4','Fare quantile bands by distance',[CAL/'array_a/array_a_verified.csv'],scope+' | Sparse bins retained; not a trip-level boxplot',fig=fig)
panel('A5','Frozen fare and distance references',[f'P_base = {pb} USD; L_base = {lb} km','Current analytical distance range: 1.5 ≤ L < 75 km; N=6,967,155.', 'P_base provenance uses [1,75) km. No recalibration is performed for this review.','TLC source distance is miles; conversion is ×1.609344 before kilometre filtering.'],[DIST/'pricing_v2_sensitivity_contract.json',DIST/'population_reconciliation.csv'],scope)
# Persisted raw ratio array; lightweight histogram only, no epsilon recalculation.
rawpath=CAL/'intermediate/new_e_B_INTERPOLATED.npy';raw=np.load(src(rawpath),mmap_mode='r')
# This historical array is [1,75), and must not be conflated with current scope.
fig,axs=plt.subplots(1,2,figsize=(12,5));axs[0].hist(raw[np.isfinite(raw)],bins=np.linspace(-10,20,121));axs[0].set(xlabel='Signed epsilon (central view −10 to 20)',ylabel='Count');vals=np.abs(raw[np.isfinite(raw)]);axs[1].hist(vals[vals>0],bins=np.geomspace(vals[vals>0].min(),vals.max(),100));axs[1].set(xscale='log',yscale='log',xlabel='|epsilon| (full positive magnitude range)',ylabel='Count (log)');finish('B1','Historical raw ratio: central view and full magnitude tails',[rawpath], 'Jan 1–Mar 15 | Historical [1,75) km array; no denominator screen',HIST,fig=fig)
gap=csv(CAL/'zero_denominator/price_gap_bands.csv');gap=gap[(gap.P_definition=='EXACT')&(gap.scope=='ARRAY_RANGE')]
line('B2','Near-reference fare observations and ratio sensitivity',gap,'relative_gap_le',['N'],'Cumulative observations',[CAL/'zero_denominator/price_gap_bands.csv'], 'Jan 1–Mar 15 | Historical [1,75) km; cumulative |r_P| bands',DIAG)
d=csv(DEN/'global_distribution_comparison.csv');d=d[d.rule_id.isin(['BASELINE','A','B','C'])].copy();d['rule']=d.rule_id.map({'BASELINE':'No screen','A':'$0.50','B':'$1.00','C':'5% frozen'})
line('B3','Denominator candidates: nonnegative epsilon dispersion',d,'rule',['SD','P99'],'Epsilon (dimensionless)',[DEN/'global_distribution_comparison.csv'],scope+' | Candidate diagnostics; C is frozen',DIAG)
pop=csv(DIST/'population_reconciliation.csv').iloc[0]
panel('B4','Population reconciliation', [f'Already-cleaned Jan 1–Mar 15 cache: {int(pop.source_cache_N):,}',f'Current [1.5,75) km source: {int(pop.source_population_N):,}',f'Denominator unresolved: {int(pop.denominator_unresolved_N):,} → retained in historical materialization, not runtime',f'Denominator resolved: {int(pop.denominator_resolved_N):,}',f'Negative excluded from runtime: {int(pop.negative_epsilon_N):,}',f'Final nonnegative empirical population: {int(pop.final_nonnegative_candidate_N):,}'],[DIST/'population_reconciliation.csv'],scope)
line('B5','Before/after denominator screening: location, spread and tail',d[d.rule_id.isin(['BASELINE','C'])],'rule',['mean','median','SD','P99'],'Epsilon (dimensionless)',[DEN/'global_distribution_comparison.csv'],scope+' | Nonnegative subset in each scenario; no sign transformation',DIAG)
for i,n,title in [('C1','density_comparison','Nonnegative sensitivity density comparison'),('C2','pooled_distribution_diagnostics','Empirical distribution and CDF diagnostics'),('C3','cdf_comparison','Held-out CDF comparison'),('C4','qq_comparison','Candidate Q–Q comparisons'),('C6','central_quantile_comparison','Candidate quantile comparison')]:reuse(i,title,DIST/f'charts/{n}.png',scope,'Pooled marginal of unchanged current population; conditional runtime selection differs')
f=csv(DIST/'distribution_fit_comparison.csv');fig,ax=plt.subplots(figsize=(10,5));ax.bar(f.candidate,f.KS_descriptive);ax.set(ylabel='Held-out descriptive CDF distance',xlabel='Candidate representation');finish('C5','Empirical resampling best supported by held-out CDF fidelity',[DIST/'distribution_fit_comparison.csv'],scope+' | FIT 4,623,641; validation 1,155,572; random-row split',fig=fig)
w=csv(W/'weather_code_time_statistics.csv')
for i,y in [('D1','mean'),('D2','SD')]:
 fig,ax=plt.subplots(figsize=(11,5))
 for t,g in w.groupby('T_group'):ax.plot(g.weather_code,g[y],marker='o',label=t)
 ax.set(xticks=sorted(w.weather_code.unique()),xlabel='Actual weather code',ylabel=f'Epsilon {y} (dimensionless)');ax.legend();finish(i,f'Raw-weather epsilon {y} by time group',[W/'weather_code_time_statistics.csv'],scope+' | Observed cells only; SD ddof=0',fig=fig)
x=w.pivot(index='weather_code',columns='T_group',values='N');fig,ax=plt.subplots(figsize=(7,8));im=ax.imshow(np.log10(x.fillna(0)+1),aspect='auto');ax.set(xticks=range(4),xticklabels=x.columns,yticks=range(len(x)),yticklabels=x.index,xlabel='Time group',ylabel='Weather code')
for r in range(len(x)):
 for c in range(4):
  v=x.iloc[r,c];lab='absent' if pd.isna(v) else f'{int(v):,}\n'+('<50' if v<50 else '50–99' if v<100 else '≥100');ax.text(c,r,lab,ha='center',va='center',fontsize=7,color='black',bbox=dict(facecolor='white',alpha=.7,edgecolor='none'))
fig.colorbar(im,ax=ax,label='log10(N+1)');finish('D3','Observed support and support tiers',[W/'weather_code_time_statistics.csv'],scope,fig=fig)
g=w[w.T_group=='T1'];fig,ax=plt.subplots(figsize=(10,5));g2={13,15}
for _,z in g.iterrows():ax.scatter(z['mean'],z.SD,color='C1' if z.weather_code in g2 else 'C0');ax.annotate(str(int(z.weather_code)),(z['mean'],z.SD),xytext=({1:(-20,-13),2:(10,-15),3:(-16,12),8:(10,18),9:(-20,23),14:(-10,-20)}.get(int(z.weather_code),(5,6))),textcoords='offset points',arrowprops=dict(arrowstyle='-',lw=.5,color='gray'))
ax.set(xlabel='Mean epsilon',ylabel='Population SD epsilon');ax.text(.02,.95,'Blue: G1; orange: G2\n17/21: unsupported T1 → fallback',transform=ax.transAxes,va='top');finish('D4','Frozen T1 grouping in mean–SD feature space',[W/'weather_code_time_statistics.csv',W/'weather_time_group_mapping.csv'],scope+' | G2 does not meet runtime N≥5,000',fig=fig)
missing('D5','Actual frozen T1 hierarchical dendrogram',[W/'build.py',W/'weather_time_grouping_contract.json'],'Linkage was computed but not persisted. No clustering rerun permitted; membership plot D4 is not a substitute dendrogram.')
k=csv(W/'weather_cluster_candidates.csv');line('D6','T1 cluster selection: K=2 frozen',k[k.T_group=='T1'],'K',['silhouette','stability_median','stability_p10'],'Descriptive score / ARI',[W/'weather_cluster_candidates.csv'],scope+' | Stability and support gates; SD<4 is not a hard criterion',DIAG)
m=csv(W/'runtime_cell_support_selection.csv');tab=m.pivot(index='raw_weather_code',columns='T_group',values='support_id');fig,ax=plt.subplots(figsize=(12,7));ax.axis('off');table=ax.table(cellText=tab.values,rowLabels=tab.index,colLabels=tab.columns,loc='center');table.auto_set_font_size(False);table.set_fontsize(9);table.scale(1,1.5);finish('D7','Actual runtime support lookup by weather and time',[W/'runtime_cell_support_selection.csv'],scope+' | T1_G2 uses raw-code fallback; T2–T4 pooled',fig=fig)
panel('D8','Weather/time sampling decision flow',['Raw weather code + request timestamp → T group','T1 supported group and N≥5,000 → exact group empirical support','Otherwise T1: eligible same-code pooled support → T pooled → global','T2/T3/T4: T pooled directly → global if needed','Uniform row resampling with replacement preserves duplicate frequencies','One epsilon per request → acceptance ceiling → action feasibility mask'],[W/'weather_time_grouping_contract.json',W/'runtime_cell_support_selection.csv'],scope)
s=csv(W/'conditional_support_statistics.csv');s=s[s.support_id.isin(['T1_G1','T1_G2','T2_POOLED','T3_POOLED','T4_POOLED','GLOBAL'])]
fig,ax=plt.subplots(figsize=(11,5));xx=np.arange(len(s));ax.vlines(xx,s.P05,s.P95,color='C0');ax.vlines(xx,s.P25,s.P75,lw=8,color='C0');ax.scatter(xx,s['median'],color='black',label='Median');ax.set(xticks=xx,xticklabels=s.support_id,ylabel='Epsilon (P05–P95; thick IQR)');ax.legend();finish('D9','Conditional empirical support comparison',[W/'conditional_support_statistics.csv'],scope+' | G2 diagnostic only (N=1,669); runtime uses fallback',fig=fig)
reqpath=T/'HIGHEST_FEASIBLE_requests.parquet';req=pd.read_parquet(src(reqpath));assert len(req)==73754
assert pd.to_datetime(req.timestamp).dt.date.astype(str).eq('2026-03-16').all()
devscope='March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2'
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,col in zip(axs,['P_raw_c','P_accept_c']):
 v=req[col].dropna();ax.hist(v,bins=100);ax.set(xlabel=col+' (USD; symlog)',ylabel='Requests',xscale='symlog',yscale='log')
finish('E1','Raw preference and effective acceptance ceiling',[reqpath],devscope+' | Full range; symlog handles negative raw preference',fig=fig)
fig,ax=plt.subplots(figsize=(9,5));cnt=req.feasible_action_count.value_counts().reindex(range(1,8),fill_value=0);ax.bar(cnt.index,cnt);ax.set(xlabel='Feasible pricing arms',ylabel='Requests',xticks=range(1,8));finish('E2','Request-level feasible-action count',[reqpath],devscope,fig=fig)
mask=[f'mask_{x}' for x in ['085','090','095','100','105','110','115']];factors=[.85,.9,.95,1,1.05,1.1,1.15];fig,ax=plt.subplots(figsize=(9,5));ax.bar([str(a) for a in factors],req[mask].mean()*100);ax.set(xlabel='Pricing factor × P_base',ylabel='Model-feasible requests (%)',ylim=(0,105));finish('E3','Model feasibility across the seven pricing factors',[reqpath],devscope+' | Feasible does not mean dispatched or served',fig=fig)
act=csv(T/'development_actions_ep25.csv');counts=act.selected_action_index.value_counts().reindex(range(7),fill_value=0)
for i in ['E4','I3']:
 fig,ax=plt.subplots(figsize=(9,5));ax.bar([str(a) for a in factors],counts);ax.set(xlabel='Pricing factor × P_base',ylabel='Episode25 greedy requests');finish(i,'Episode25 greedy action coverage',[T/'development_actions_ep25.csv'],devscope,fig=fig)
panel('E5','Acceptance floor and action-space maximum',[f'P_raw = P_base + (P_base / epsilon) × ((L − L_base)/L_base)', 'P_accept = max(0.85 × P_base, P_raw). The acceptance floor is applied; no upper clipping of P_raw is performed.','P_offer is one of seven factors × P_base; highest configured action is 1.15 × P_base.','E1 shows the actual pre-floor and post-floor distributions. Upper-clipped preference histogram: NOT_APPLICABLE_CURRENT_RUNTIME.'],[reqpath],devscope)
# Diagram rendered from explicit nodes, not generative artwork.
fig,ax=plt.subplots(figsize=(13,10));ax.axis('off');nodes=['Historical data → CNN forecast','Operational state + weather/time lookup','Conditional empirical epsilon sample','Passenger acceptance ceiling','Seven actions + feasibility mask','13D request-level DQN → offer','Driver eligibility / FCFS dispatch','Fleet → routing / repositioning → charging','Next request / pricing state','TRAIN: replay → Bellman update\nDEV March16: greedy, no optimizer update']
for j,t in enumerate(nodes):
 y=.94-j*.091;ax.text(.5,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.5',facecolor='#e8f0f6',edgecolor='#31516a'),fontsize=11)
 if j<9:ax.annotate('',xy=(.5,y-.059),xytext=(.5,y-.027),arrowprops=dict(arrowstyle='->'))
finish('F1','Current hierarchical pricing workflow',[T/'training_harness_config.json',T/'verification.json',W/'weather_time_grouping_contract.json'], 'V2 | Frozen routing; train 16 slots/episode; March16 development 48 slots',fig=fig)
ep=csv(T/'episode_metrics.csv');ep['assignment_rate']=ep.assignments/ep.requests;v=csv(T/'value_calibration.csv');escope='Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons'
for i,title,df,ys,unit in [('G1','Training revenue',ep,['revenue'],'USD'),('G2','Training assignment rate',ep,['assignment_rate'],'Assigned / requested'),('G3','Training loss',ep,['mean_loss','median_loss','P95_loss'],'Loss'),('G4','Development TD error',v,['mean_absolute_TD_error'],'Absolute TD error'),('G5','Development Q magnitude',v,['Q_mean','Q_median'],'Q (reward units)'),('G6','Exploration schedule',ep,['exploration_epsilon'],'Exploration epsilon'),('G7','Replay occupancy',ep,['replay_size'],'Transitions'),('G9','Training charging events',ep,['charging_events'],'Events')]:line(i,title,df,'episode',ys,unit,[T/('episode_metrics.csv' if df is ep else 'value_calibration.csv')],escope if df is ep else devscope)
de=csv(T/'development_evaluations.csv');base=csv(T/'weather_conditioned_baseline_comparison.csv');hf=base[base.policy=='HIGHEST_FEASIBLE'].iloc[0]
fig,ax=plt.subplots(figsize=(11,5));ac=np.array([json.loads(x) for x in de.action_counts]);ax.stackplot(de.episode,*(ac/ac.sum(axis=1)[:,None]).T,labels=[str(a) for a in factors]);ax.legend(ncol=7,loc='upper center');ax.set(xlabel='Checkpoint episode',ylabel='Greedy action share');finish('G8','Fixed-development action-frequency evolution',[T/'development_evaluations.csv'],devscope+' | Training per-episode action counts not persisted in episode table',fig=fig)
for i,y,title,unit in [('H1','revenue','Fixed-development checkpoint revenue','USD'),('H2','assignments','Fixed-development checkpoint assignments','Assignments')]:
 fig,ax=plt.subplots(figsize=(10,5));ax.plot(de.episode,de[y],marker='o',label='DQN');ax.axhline(hf[y],ls='--',label='Highest Feasible',color='C1');ax.set(xlabel='Checkpoint episode',ylabel=unit,ylim=(0,max(de[y].max(),hf[y])*1.1));ax.legend();finish(i,title,[T/'development_evaluations.csv',T/'weather_conditioned_baseline_comparison.csv'],devscope,fig=fig)
z=de[de.episode==25].iloc[0];comp=pd.concat([pd.DataFrame([z]),base],ignore_index=True);fig,axs=plt.subplots(1,2,figsize=(13,5));labs=['EP25 DQN','Highest','Lowest','Neutral']
# Explicit policy ordering.
comp=pd.DataFrame([z,*[base[base.policy==p].iloc[0] for p in ['HIGHEST_FEASIBLE','LOWEST_FEASIBLE','NEUTRAL_1_00_WITH_EXISTING_FALLBACK']]])
for ax,col,unit in zip(axs,['assignments','revenue'],['Assignments','Revenue (USD)']):ax.bar(labs,comp[col]);ax.set(ylabel=unit);ax.tick_params(axis='x',rotation=15)
finish('H3','Episode25 and fixed policy baselines',[T/'development_evaluations.csv',T/'weather_conditioned_baseline_comparison.csv'],devscope,fig=fig)
choice=act[act.feasible_action_count>1];gap=choice.feasible_action_count-1-choice.selected_action_index;pos=[int((gap==0).sum()),int((gap==1).sum()),int((gap>=2).sum())];fig,ax=plt.subplots(figsize=(9,5));ax.bar(['Highest','One below','Two or more below'],np.array(pos)/len(choice)*100);ax.set(ylabel='Choice requests (%)');finish('I1','Position relative to highest feasible action',[T/'development_actions_ep25.csv'],devscope+f' | Choice-only N={len(choice):,}',fig=fig)
st=csv(T/'postrun_analysis/policy_stability.csv');st['pair']=st.from_episode.astype(str)+'→'+st.to_episode.astype(str);line('I2','Checkpoint action agreement',st,'pair',['all_agreement_pct','choice_agreement_pct'],'Agreement (%)',[T/'postrun_analysis/policy_stability.csv'],devscope)
missing('J1','Selected-Q versus state-matched Monte-Carlo return scatter',[T/'value_calibration.csv',T/'postrun_analysis/analyze.py'],'Only aggregate Q/MC moments persisted; request-level pairs unavailable. Generating pairs would require an evaluation rerun, prohibited here.')
line('J2','Q and Monte-Carlo return means',v,'episode',['Q_mean','MC_mean'],'Reward units',[T/'value_calibration.csv'],devscope)
line('J3','Q versus Monte-Carlo error',v,'episode',['Q_MC_MAE'],'Mean absolute error (reward units)',[T/'value_calibration.csv'],devscope)
q=csv(DYN/'q_value_realized_value.csv');q=q[q.case_type.isin(['ASSIGNED_DRIVER_CHANGED','ASSIGNMENT_OUTCOME_CHANGED'])];assert len(q)==20
ver=js(DYN/'verification.json');co=ver['counts'];fig,ax=plt.subplots(figsize=(9,5));ax.bar(['Correct','Incorrect','Tie'],[co['q_correct'],co['q_incorrect'],20-co['q_correct']-co['q_incorrect']]);ax.set(ylabel='Genuine divergent cases');finish('J4','Q ranking versus realized counterfactual value',[DYN/'verification.json'],devscope+' | 20 bounded cases; all discounted comparisons unfavorable',DIAG,fig=fig)
fig,ax=plt.subplots(figsize=(11,5));ax.barh(['Screened','Eligibility changed','Different driver, both assigned','Assignment outcome changed'],[co['screened'],co['eligibility_changed'],co['assigned_driver_changed_both_assigned'],co['outcome_changed']]);ax.set(xlabel='Requests');finish('K1','Full-day immediate dynamic-opportunity screen',[DYN/'verification.json'],devscope+' | Screened=15,800; branches are not an additive/nested funnel',DIAG,fig=fig)
fig,ax=plt.subplots(figsize=(10,5));ax.bar(['Across boundary','Partial recovery','Full recovery','Net-positive'],[co['persist_boundary'],co['partial'],co['full'],co['net_positive']]);ax.set(ylabel='Cases');finish('K2','Bounded state-matched dynamic outcomes',[DYN/'verification.json'],devscope+' | 20 genuine cases; outcomes overlap, not additive',DIAG,fig=fig)
fig,ax=plt.subplots(figsize=(10,5));ax.scatter(q.q_difference,q.net_revenue_difference);ax.axhline(0,color='gray');ax.set(xlabel='Q(lower DQN) − Q(highest feasible)',ylabel='Realized net revenue difference (USD)');finish('K3','Q advantage versus realized net value',[DYN/'q_value_realized_value.csv'],devscope+' | 20 cases; descriptive correlation, not causation',DIAG,fig=fig)
fig,ax=plt.subplots(figsize=(13,5));xx=np.arange(len(q));ax.bar(xx-.2,q.immediate_revenue_difference,width=.4,label='Immediate difference');ax.bar(xx+.2,q.recovery,width=.4,label='Downstream recovery');ax.set(xticks=xx,xticklabels=q.request_id.astype(str),ylabel='Revenue difference (USD)',xlabel='Request ID');ax.tick_params(axis='x',rotation=60);ax.legend();finish('K4','Immediate sacrifice and downstream recovery',[DYN/'q_value_realized_value.csv'],devscope+' | Chronological bounded selection, not prevalence estimation',DIAG,fig=fig)
panel('K5','Dynamic opportunity is not established profitable value',[f'DYNAMIC_VALUE_OPPORTUNITY = {ver["DYNAMIC_VALUE_OPPORTUNITY"]}',f'DYNAMIC_VALUE_EVIDENCE = {ver["DYNAMIC_VALUE_EVIDENCE"]}',f'LONGER_TRAINING_RECOMMENDATION = {ver["LONGER_TRAINING_RECOMMENDATION"]}','20 genuine divergent cases: one partial recovery, one full recovery, zero net-positive.', 'Bounded sample excludes peak-demand quartile. This is not proof of universal Highest Feasible dominance.'],[DYN/'verification.json'],devscope,DIAG)
panel('L1','Persisted correctness evidence and protected boundaries',[f'Suites passed: '+', '.join(str(x['passed']) for x in ver['tests'])+' (overlapping suites; do not sum).',f'New audit infrastructure/report tests: {ver["new_infrastructure_tests_passed"]} / {ver["new_reporting_tests_passed"]}; identical-action controls: {ver["controls_passed"]}.',f'Failures={ver["failures"]}; errors={ver["errors"]}.','Fixed replay: request/actions/rewards/final fleet reconciled; fixture unchanged.','Episode26 NOT_STARTED. March17–31 UNTOUCHED.','These are saved test results, not a new whole-project regression run.'],[DYN/'verification.json',T/'resume_validation.json',T/'verification.json'], 'Evidence through November 15, 2026')
fig,axs=plt.subplots(2,2,figsize=(14,10));axs[0,0].bar(['EP25','Highest feasible'],[z.revenue,hf.revenue]);axs[0,0].set(ylabel='March16 revenue (USD)',title='Fixed full-day comparison');axs[0,1].bar(['Highest','−1 arm','−2+ arms'],np.array(pos)/len(choice)*100);axs[0,1].set(ylabel='Choice requests (%)',title='Episode25 action position');axs[1,0].bar(['Mean Q','Mean MC'],[v.iloc[-1].Q_mean,v.iloc[-1].MC_mean]);axs[1,0].set(ylabel='Reward units',title='Value calibration remains poor');axs[1,1].axis('off');axs[1,1].text(0,1,'5,779,213 nonnegative observations\nT1 weather groups; T2–T4 pooled\nG2 runtime fallback (N<5,000)\n\nDynamic opportunity: MEANINGFUL\nDynamic evidence: WEAK\nExtend training: NO\n\nSaved tests: zero failures/errors\nMarch17–31 untouched',va='top',fontsize=13);finish('SUMMARY','V2 academic review — current evidence at Episode25',[T/'development_evaluations.csv',T/'value_calibration.csv',DYN/'verification.json',W/'conditional_support_statistics.csv'],devscope+' | Development results, not final holdout performance',fig=fig)
# Save exact small source tables for self-contained review, without large datasets.
for name,df in [('calibration_bins',b),('population_flow',pd.DataFrame([pop])),('denominator_comparison',d),('weather_time_statistics',w),('support_statistics',s),('training_metrics',ep),('development_comparison',comp),('q_calibration',v),('dynamic_cases',q)]:df.to_csv(O/'tables'/f'{name}.csv',index=False)
pd.DataFrame(index).to_csv(O/'visual_index.csv',index=False)
coverage=[]
for it in index:
 status=it.get('coverage_status') or ('PRESENT_HISTORICAL' if it['current_or_historical']==HIST else 'PRESENT_CURRENT')
 coverage.append({'request/source':it['requested_by_source'],'requested_visual_or_analysis':it['title'],'current_corresponding_visual':it['final_output_path'],'status':status,'notes':it['notes']})
coverage.append({'request/source':'E5 upper clipping','requested_visual_or_analysis':'Upper-clipped raw preference distribution','current_corresponding_visual':'charts/E5.png','status':'NOT_APPLICABLE_CURRENT_RUNTIME','notes':'Only acceptance floor and bounded action space; no raw preference upper clip.'})
pd.DataFrame(coverage).to_csv(O/'requested_visual_coverage.csv',index=False)
(O/'source_manifest.json').write_text(json.dumps({'sources':manifest,'read_policy':'Explicit scoped persisted artifacts only; no simulation/model loading/training/holdout reads','version':'WEATHER_TIME_CONDITIONED_V2','calibration_dates':'2026-01-01 through 2026-03-15','development_date':'2026-03-16','units':{'fare':'USD','distance':'km','epsilon':'dimensionless'},'note':'Earlier source-package pending statuses are historical; completed run verification establishes current status.'},indent=2))
print('FIGURES',sum(bool(x['final_output_path']) for x in index),'GAPS',sum(c['status']=='MISSING' for c in coverage))
