"""Deterministic persisted-evidence report. No simulator/model imports or execution."""
from pathlib import Path
import json,hashlib,mmap,re,shutil,zipfile,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
V=ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3';O=V/'review_ep01_ep10';T=V/'training';E=T/'episode_001';S=T/'stage_ep02_ep10'
CP=ROOT/'models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10/episode_010'
NA='NOT_AVAILABLE_FROM_PERSISTED_V3_ARTIFACTS'
CAVEAT='Sequential chronological windows; not controlled policy comparisons. Demand, weather, fleet and policy can all change.'
prov=[];charts=[];sources={}
def md(df):
 return '| '+' | '.join(map(str,df.columns))+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(str(x).replace('|','/') for x in row)+' |' for row in df.itertuples(index=False,name=None))
def rel(p):return str(Path(p).relative_to(ROOT))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def source(p):
 p=Path(p)
 if rel(p) not in sources:sources[rel(p)]=sha(p)
 return rel(p)
def js(p):source(p);return json.loads(Path(p).read_text())
def csv(p):source(p);return pd.read_csv(p)
def writej(name,d): (O/name).write_text(json.dumps(d,indent=2,allow_nan=False,default=str)+'\n')
def table(name,df,inputs,aggregation,filters='Episodes1–10 only'):
 p=O/name;df.to_csv(p,index=False)
 prov.append(dict(output_filename=name,source_artifact=';'.join(source(x) for x in inputs),source_columns=';'.join(df.columns.astype(str)),row_count=len(df),aggregation=aggregation,filters=filters,episode_range='1–10',sha256=sha(p)))
 return df
def unpack(x):
 if not isinstance(x,dict):return x
 if x['type']=='float':return float.fromhex(x['hex'])
 if x['type']=='dict':return {unpack(k):unpack(v) for k,v in x['items']}
 if x['type']=='list':return [unpack(v) for v in x['items']]
 raise ValueError('Unsupported report-only primitive')
def extract_list(mm,start):
 # Bounded buffer decoding: never load the full runtime/environment JSON.
 marker=b'"items": [';pos=mm.find(marker,start)+len(marker);buf='';cursor=0;decoder=json.JSONDecoder()
 while True:
  if cursor>len(buf)-4096:
   buf=buf[cursor:]+mm[pos:pos+1048576].decode();pos+=1048576;cursor=0
  while cursor<len(buf) and buf[cursor] in ' ,\r\n':cursor+=1
  if buf[cursor]==']':return
  try:x,end=decoder.raw_decode(buf,cursor)
  except json.JSONDecodeError:
   buf=buf[cursor:]+mm[pos:pos+1048576].decode();pos+=1048576;cursor=0;continue
  yield unpack(x);cursor=end
def episode(ts):return ((pd.to_datetime(ts)-pd.Timestamp('2026-03-01')).dt.total_seconds()//(8*3600)).astype(int)+1
def combined(name):
 a=csv(E/name);b=csv(S/name)
 z=pd.concat([a,b],ignore_index=True);assert not z.slot.duplicated().any();z['episode']=episode(z.slot);assert z.episode.between(1,10).all();return z

def main():
 O.mkdir(exist_ok=True);(O/'charts').mkdir(exist_ok=True);(O/'tables').mkdir(exist_ok=True)
 contract=js(V/'methodology_contract.json');manifest=js(CP/'manifest.json');runtime=CP/'runtime.json'
 assert manifest['episode']==10 and manifest['slot']==16 and manifest['optimizer_updates']==1224 and manifest['replay_size']==22720
 assert sha(runtime)==manifest['component_hashes']['runtime.json'];source(runtime)
 request_path=O/'tables/request_level_audit.parquet';context_path=O/'tables/context_slot_audit.csv'
 if not request_path.exists():
  with runtime.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
   hits=[x.start() for x in re.finditer(rb'\["audit", ',mm)]
   start=next(x for x in hits if b'"request_id"' in mm[x:x+160])
   req=pd.DataFrame(extract_list(mm,start));ctx=pd.DataFrame(extract_list(mm,mm.find(b'["slot_audit", ')))
  req['episode']=episode(req.slot);ctx['episode']=episode(ctx.slot)
  assert req.episode.between(1,10).all() and ctx.episode.between(1,10).all()
  req=req.merge(ctx[['slot','destination_context','action']],on=['slot','destination_context'],validate='many_to_one')
  req['origin']=NA;req.to_parquet(request_path,index=False);ctx.to_csv(context_path,index=False)
 else:req=pd.read_parquet(request_path);ctx=pd.read_csv(context_path)
 for p,df in [(request_path,req),(context_path,ctx)]:prov.append(dict(output_filename=rel(p).split('review_ep01_ep10/')[1],source_artifact=rel(runtime),source_columns='runtime.audit;runtime.slot_audit',row_count=len(df),aggregation='Primitive JSON extraction; join action by slot/destination; origin unavailable',filters='checkpoint Episode10 cumulative audit only',episode_range='1–10',sha256=sha(p)))
 slots=combined('slot_metrics.csv');learn=combined('learning_metrics.csv');trans=combined('transition_metrics.csv');reward=combined('reward_reconciliation.csv');ops=combined_ops();fleet=combined('fleet_health.csv');routing=combined('routing_health.csv')
 assert len(slots)==160 and len(ctx)==22720 and len(req)==slots.requests.sum()
 assert req.request_id.is_unique and (req.accepted==(req.P_offer<=req.P_max)).all()
 assert np.allclose(req.P_offer,req.factor*contract['P_base'],rtol=1e-14,atol=1e-12)
 assert (slots.requests==slots.accepted+slots.rejected).all() and (slots.accepted==slots.assignments+slots.accepted_unmatched).all()
 assert np.allclose(reward.accepted_offers,reward.reward,rtol=1e-12,atol=1e-8) and np.allclose(reward.reward,reward.replay_reward,rtol=1e-12,atol=1e-8)
 assert np.array_equal(trans.replay_size,np.arange(1,161)*142)
 expected=8*np.maximum(0,np.arange(1,161)-7);assert np.array_equal(learn.optimizer_updates,expected)
 assert np.allclose(learn.epsilon,1-.95*expected/50000,rtol=0,atol=2e-16)
 rows=[]
 for e,g in slots.groupby('episode'):
  rr=req[req.episode==e];ll=learn[learn.episode==e];tt=trans[trans.episode==e];cc=ctx[ctx.episode==e]
  d=dict(episode=int(e),start_timestamp=g.slot.min(),end_timestamp=g.slot.max(),**{k:int(g[k].sum()) for k in ['requests','accepted','rejected','assignments','accepted_unmatched']},accepted_revenue=float(g.accepted_revenue.sum()),mean_offered_price=float(rr.P_offer.mean()),transitions=int(tt.transitions.sum()),replay_size_end=int(tt.replay_size.iloc[-1]),optimizer_updates_end=int(ll.optimizer_updates.iloc[-1]),optimizer_updates_episode=int(ll.updates.sum()),epsilon_end=float(ll.epsilon.iloc[-1]),mean_loss=float(ll.mean_loss.dropna().mean()),mean_abs_Q=NA,max_abs_Q=NA,mean_abs_TD=NA)
  for k,num,den in [('acceptance_rate','accepted','requests'),('dispatch_success_among_accepted','assignments','accepted'),('overall_assignment_rate','assignments','requests')]:d[k]=d[num]/d[den]
  assert len(rr)==d['requests'] and int(rr.accepted.sum())==d['accepted']
  assert np.isclose(cc.accepted_revenue.sum(),d['accepted_revenue'],rtol=1e-12,atol=1e-8)
  rows.append(d)
 ep=table('episode_summary.csv',pd.DataFrame(rows),[E/'slot_metrics.csv',S/'slot_metrics.csv',E/'learning_metrics.csv',S/'learning_metrics.csv',runtime],'Sum slot counts/rewards; request-weighted offer mean; mean recorded warm-slot mean losses')
 aa=ctx.groupby(['episode','action','factor'],as_index=False).agg(contexts_selected=('destination_context','size'),requests_exposed=('generated','sum'),accepted=('accepted','sum'),rejected=('rejected','sum'),accepted_revenue=('accepted_revenue','sum'),assignments=('assigned','sum'),accepted_unmatched=('accepted_unmatched','sum'))
 def economics(a):
  a['P_offer']=a.factor*contract['P_base'];a['acceptance_rate']=a.accepted/a.requests_exposed;a['accepted_revenue_per_exposed_request']=a.accepted_revenue/a.requests_exposed;a['accepted_revenue_per_accepted_request']=a.accepted_revenue/a.accepted;return a
 aa=economics(aa);a=economics(aa.groupby(['action','factor'],as_index=False)[['contexts_selected','requests_exposed','accepted','rejected','accepted_revenue','assignments','accepted_unmatched']].sum())
 assert np.allclose(a.factor,contract['actions'],rtol=0,atol=1e-15)
 table('action_by_episode.csv',aa,[runtime],'Sum context audits by episode/action; derived ratios')
 table('action_summary.csv',a,[runtime],'Sum context audits by action; derived ratios')
 funnel=ep[['episode','requests','accepted','rejected','assignments','accepted_unmatched','acceptance_rate','dispatch_success_among_accepted','overall_assignment_rate']].copy();funnel['accepted_unmatched_rate']=funnel.accepted_unmatched/funnel.accepted
 table('acceptance_dispatch_summary.csv',funnel,[runtime,E/'slot_metrics.csv',S/'slot_metrics.csv'],'Outcome counts and conditional rates; unmatched causes unavailable')
 sens=req.groupby(['sensitivity_condition','family']).agg(requests=('request_id','size'),accepted=('accepted','sum'),epsilon_mean=('epsilon','mean'),epsilon_SD=('epsilon',lambda x:x.std(ddof=0)),epsilon_median=('epsilon','median'),epsilon_P95=('epsilon',lambda x:x.quantile(.95)),epsilon_P99=('epsilon',lambda x:x.quantile(.99))).reset_index();sens['acceptance_rate']=sens.accepted/sens.requests
 table('sensitivity_runtime_summary.csv',sens,[runtime],'Direct saved request draws; population SD and linear empirical quantiles; not refitting')
 weather=req.groupby(['weather_code','T_group','sensitivity_condition','family','fallback_level']).agg(requests=('request_id','size'),accepted=('accepted','sum')).reset_index();weather['acceptance_rate']=weather.accepted/weather.requests
 weather['selection_reason']=np.where(weather.T_group.isin(['T2','T3','T4']),'DENSE_SCENARIO_POOLING_DUE_TO_CLUSTER_INSTABILITY',np.where(weather.fallback_level>0,'SPARSE_ELIGIBILITY_FALLBACK','T1_GROUP'))
 table('weather_group_runtime_summary.csv',weather,[runtime],'Actual request weather/time/condition/fallback; T2–T4 level2 is pooling, not sparse')
 table('learning_summary.csv',ep[['episode','optimizer_updates_episode','optimizer_updates_end','epsilon_end','mean_loss','mean_abs_Q','max_abs_Q','mean_abs_TD']],[E/'learning_metrics.csv',S/'learning_metrics.csv'],'Mean saved slot-average loss; Q/TD unavailable')
 table('replay_optimizer_summary.csv',ep[['episode','transitions','replay_size_end','optimizer_updates_episode','optimizer_updates_end','epsilon_end']],[E/'transition_metrics.csv',S/'transition_metrics.csv',E/'learning_metrics.csv',S/'learning_metrics.csv'],'End-of-episode counters; differences for per-episode updates')
 for n,d,inp in [('tables/slot_summary.csv',slots,[E/'slot_metrics.csv',S/'slot_metrics.csv']),('tables/learning_slots.csv',learn,[E/'learning_metrics.csv',S/'learning_metrics.csv']),('tables/operational_trace.csv',ops,[E/'operational_state_trace.csv',S/'operational_state_trace.csv']),('tables/fleet_health.csv',fleet,[E/'fleet_health.csv',S/'fleet_health.csv']),('tables/routing_health.csv',routing,[E/'routing_health.csv',S/'routing_health.csv'])]:table(n,d,inp,'Concatenate nonoverlapping stages; episode from chronology')
 counts=req.groupby('slot').size();selected=counts.sub(counts.median()).abs().sort_values(kind='stable').index[0];sample=req[req.slot==selected].sort_values('request_id');sample=sample.iloc[np.linspace(0,len(sample)-1,min(300,len(sample)),dtype=int)]
 table('tables/request_validation_sample.csv',sample,[runtime],'Choose earliest slot nearest median request count; up to300 evenly spaced sorted request IDs')
 writej('request_validation.json',dict(N=len(req),mismatch_count=int((req.accepted!=(req.P_offer<=req.P_max)).sum()),origin=NA,driver_rejection_causes='REQUEST_LEVEL_DRIVER_REJECTION_DIAGNOSTIC_NOT_AVAILABLE',sample_slot=selected,sample_N=len(sample),request_log='tables/request_level_audit.parquet'))
 totals={k:int(ep[k].sum()) for k in ['requests','accepted','rejected','assignments','accepted_unmatched','transitions']};totals['accepted_revenue']=float(ep.accepted_revenue.sum())
 final=dict(replay_size=int(manifest['replay_size']),optimizer_updates=int(manifest['optimizer_updates']),epsilon=manifest['exploration_epsilon'])
 gates=[js(E/'health_gate.json'),js(S/'health_gate.json')];assert all(g[k]=='PASS' for g in gates for k in ['TECHNICAL_INVARIANTS','NUMERICAL_STABILITY','CHECKPOINT_VALID','ROUTING_FROZEN','FLEET_INVARIANTS'])
 assert routing.checkpoint_sha256.nunique()==1 and routing.frozen.all()
 assert np.isfinite(ops[['mu','sigma','F_hat','H_hat']]).all().all() and len(ops)==160*142
 validation=dict(status='PASS',episode_scope=list(range(1,11)),requests_reconcile=True,acceptance_mismatches=0,dispatch_reconcile=True,reward_reconcile=True,transitions=22720,optimizer_cadence=True,epsilon_schedule=True,routing_weights_unchanged=True,operational_finite=True,no_simulator_instantiated=True,March17_31='UNTOUCHED',post_ep10_metrics_used=False)
 writej('numerical_reconciliation.json',validation);writej('technical_validation_summary.json',dict(**validation,saved_health_gates=gates,scope='Saved training validations plus deterministic reporting reconciliations; no new execution tests'))
 summary=dict(status='PAUSED_AFTER_EPISODE10_FOR_REVIEW',classification='EARLY_TRAINING_REVIEW',episodes=list(range(1,11)),checkpoint=rel(CP),window='2026-03-01 00:00 → 2026-03-04 07:30',final_timestamp='2026-03-04 08:00:00',totals=totals,final=final,learning_started='YES',converged='NOT_ESTABLISHED',policy_stable='NOT_ESTABLISHED',DP='NOT_IMPLEMENTED',unmatched_causes='CAUSE_NOT_PERSISTED')
 writej('review_summary.json',summary)
 create_charts(ep,a,aa,funnel,sens,slots,learn,sample)
 documentation(ep,a,sens,summary,contract,validation)
 for record in prov:
  details=[]
  for item in record['source_artifact'].split(';'):
   if not item:continue
   sp=ROOT/item
   if sp.suffix=='.csv':
    sf=pd.read_csv(sp);details.append(dict(path=item,columns=list(sf.columns),rows=len(sf)))
   else:details.append(dict(path=item,columns='runtime.audit/runtime.slot_audit' if sp==runtime else 'Named persisted JSON/document fields',rows=len(req) if sp==runtime else None))
  record['source_columns']=json.dumps(details)
 table('artifact_provenance.csv',pd.DataFrame(prov),[],'Output-specific lineage; source hashes in source_manifest.json')
 for chart in charts:
  df=pd.read_csv(ROOT/chart['source_file']);chart['source_columns']=list(df.columns);chart['source_rows']=len(df)
  chart['aggregation'] += '; funnel counts=sum episodes; rejection_rate=rejected/requests; slot_index=chronological1..160; cumulative_reward=cumsum; share=contexts/episode_total; Pmax_minus_Pbase=P_max-P_base; request sample deterministic; learning rows updates>0'
 writej('source_manifest.json',sources);writej('chart_manifest.json',charts)
 print(json.dumps(dict(totals=totals,charts=len(charts),episodes=len(ep))))

def combined_ops():
 z=pd.concat([csv(E/'operational_state_trace.csv'),csv(S/'operational_state_trace.csv')],ignore_index=True);z['episode']=episode(z.slot);assert z.episode.between(1,10).all();return z
def create_charts(ep,a,aa,funnel,sens,slots,learn,sample):
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 def plot(cid,title,df,src,x,ys,ylabel,kind='line',episode_plot=False):
  fig,ax=plt.subplots(figsize=(10,5.8));labels=ys if isinstance(ys,list) else [ys]
  if kind=='scatter':
   for accepted,color in [(False,'#c65b53'),(True,'#23887f')]:
    g=df[df.accepted==accepted];ax.scatter(g[x],g[labels[0]],s=12,alpha=.6,label='Accepted' if accepted else 'Rejected',color=color)
   bounds=[min(df[x].min(),df[labels[0]].min()),max(df[x].max(),df[labels[0]].max())];ax.plot(bounds,bounds,'--',color='gray',label='Equality')
  elif kind=='heat':
   mat=df.pivot(index='action',columns='episode',values=labels[0]);im=ax.imshow(mat,aspect='auto',cmap='viridis');ax.set_xticks(range(10),range(1,11));ax.set_yticks(range(7),range(7));fig.colorbar(im,ax=ax,label=ylabel)
  else:
   for i,y in enumerate(labels):
    if kind=='bar':ax.bar(np.arange(len(df))+(i-(len(labels)-1)/2)*.8/len(labels),df[y],width=.8/len(labels),label=y.replace('_',' '));ax.set_xticks(range(len(df)),df[x],rotation=35 if len(df)>7 or x=='sensitivity_condition' else 0,ha='right' if x=='sensitivity_condition' else 'center')
    else:ax.plot(df[x],df[y],marker='o' if len(df)<=10 else None,lw=1.4,label=y.replace('_',' '))
  ax.set(title=title,xlabel=x.replace('_',' ').title(),ylabel=ylabel);ax.grid(axis='y',alpha=.18)
  if len(labels)>1 or kind=='scatter':ax.legend(fontsize=8)
  if episode_plot:fig.text(.5,.01,'Sequential windows, not controlled comparisons: demand, weather, fleet, routing and policy may all change.',ha='center',fontsize=8)
  fig.tight_layout(rect=(0,.04,1,1));png=O/'charts'/f'{cid}.png';pdf=png.with_suffix('.pdf');fig.savefig(png,dpi=160);fig.savefig(pdf);plt.close(fig)
  charts.append(dict(chart_id=cid,title=title,source_file=rel(O/src),source_columns=[x]+labels+(['accepted'] if kind=='scatter' else []),filter='Episodes1–10; representative deterministic sample only for request scatter',aggregation='Display persisted reporting table'+('; normalise contexts within episode' if cid=='action_share_by_episode' else ''),rows_used=len(df),episode_range='1–10',png_file=rel(png),pdf_file=rel(pdf),SHA256_png=sha(png),SHA256_pdf=sha(pdf),interpretation=CAVEAT if episode_plot else 'Descriptive observations; no causal optimality claim'))
 plot('request_funnel','Requests and recorded outcomes: Episodes1–10',pd.DataFrame({'outcome':['Requests','Accepted','Rejected','Assigned','Accepted unmatched'],'count':[ep.requests.sum(),ep.accepted.sum(),ep.rejected.sum(),ep.assignments.sum(),ep.accepted_unmatched.sum()]}),'acceptance_dispatch_summary.csv','outcome','count','Requests',kind='bar')
 for cid,ys,label in [('requests_by_episode','requests','Requests'),('accepted_revenue_by_episode','accepted_revenue','Accepted offered revenue (USD)'),('replay_size_by_episode','replay_size_end','Transitions'),('optimizer_updates_by_episode','optimizer_updates_episode','Optimizer updates'),('epsilon_by_episode','epsilon_end','Exploration probability'),('loss_by_episode','mean_loss','Mean recorded warm-slot Huber loss')]:plot(cid,cid.replace('_',' ').title(),ep,'episode_summary.csv','episode',ys,label,kind='bar' if cid=='requests_by_episode' else 'line',episode_plot=True)
 ff=funnel.copy();ff['rejection_rate']=ff.rejected/ff.requests
 plot('acceptance_rejection_by_episode','Passenger acceptance and rejection',ff,'acceptance_dispatch_summary.csv','episode',['acceptance_rate','rejection_rate'],'Fraction of requests',episode_plot=True)
 plot('assignment_unmatched_by_episode','Accepted requests: assigned vs unmatched',funnel,'acceptance_dispatch_summary.csv','episode',['assignments','accepted_unmatched'],'Requests',kind='bar',episode_plot=True)
 cum=slots.copy();cum['slot_index']=range(1,161);cum['cumulative_accepted_revenue']=cum.accepted_revenue.cumsum()
 plot('cumulative_accepted_revenue','Cumulative accepted offered revenue',cum,'tables/slot_summary.csv','slot_index','cumulative_accepted_revenue','USD',episode_plot=True)
 plot('reward_by_slot','Accepted offered reward by slot',cum,'tables/slot_summary.csv','slot_index','accepted_revenue','USD',episode_plot=True)
 plot('action_frequency_by_episode','Destination-context action frequency',aa,'action_by_episode.csv','episode','contexts_selected','Contexts selected',kind='heat',episode_plot=True)
 shares=aa.copy();shares['share']=shares.contexts_selected/shares.groupby('episode').contexts_selected.transform('sum')
 plot('action_share_by_episode','Destination-context action share',shares,'action_by_episode.csv','episode','share','Share',kind='heat',episode_plot=True)
 for cid,y,label in [('overall_action_frequency','contexts_selected','Contexts'),('action_acceptance_rate','acceptance_rate','Accepted / exposed'),('action_revenue_per_exposed_request','accepted_revenue_per_exposed_request','USD / exposed request'),('action_accepted_revenue','accepted_revenue','Accepted offered revenue (USD)')]:plot(cid,cid.replace('_',' ').title(),a,'action_summary.csv','action',y,label,kind='bar')
 for cid,y,label in [('loss_vs_optimizer_update','mean_loss','Mean eight-update slot loss'),('epsilon_vs_optimizer_update','epsilon','Exploration probability')]:plot(cid,cid.replace('_',' ').title(),learn[learn.updates>0],'tables/learning_slots.csv','optimizer_updates',y,label,episode_plot=True)
 plot('sensitivity_condition_volume','Exercised sensitivity-condition volume',sens,'sensitivity_runtime_summary.csv','sensitivity_condition','requests','Requests',kind='bar')
 plot('sensitivity_condition_acceptance','Acceptance by exercised sensitivity condition',sens,'sensitivity_runtime_summary.csv','sensitivity_condition','acceptance_rate','Accepted / requests',kind='bar')
 plot('P_offer_vs_Pmax','Saved requests: offered fare vs raw passenger ceiling',sample,'tables/request_validation_sample.csv','P_max','P_offer','Offered fare (USD)',kind='scatter')
 plot('P_base_vs_Pmax','Saved requests: common base fare vs raw passenger ceiling',sample,'tables/request_validation_sample.csv','P_max','P_base','Base fare (USD)',kind='scatter')
 d=sample.copy();d['P_max_minus_P_base']=d.P_max-d.P_base;d['sample_row']=range(len(d))
 plot('Pmax_minus_Pbase','Raw ceiling minus base fare: deterministic sample',d,'tables/request_validation_sample.csv','sample_row','P_max_minus_P_base','USD')

def documentation(ep,a,sens,summary,c,validation):
 total=summary['totals'];fin=summary['final'];status_snapshot=(json.loads((O/'post_ep10_provenance_snapshot.json').read_text())['status'] if (O/'post_ep10_provenance_snapshot.json').exists() else json.loads((T/'stage_ep11_ep25/training_status.json').read_text()))
 # Preserve a single provenance-only status snapshot; never feed later metrics into review.
 writej('post_ep10_provenance_snapshot.json',dict(classification='POST_EP10_UNPLANNED_CONTINUATION_NOT_USED_FOR_REVIEW',status=status_snapshot,excluded_from_all_review_metrics=True))
 docs=['Combined_DQN_Pricing_Validation_and_Implementation_Roadmap.docx','Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx','Price_Elasticity_Weather_Scenario_Analysis_Explained.docx']
 docrows=[]
 for name in docs:
  p=ROOT/'notebooks/plan'/name;source(p)
  with zipfile.ZipFile(p) as z:tree=ET.fromstring(z.read('word/document.xml'));txt='\n'.join(x.text or '' for x in tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
  (O/'tables'/f'{p.stem}_source_extract.txt').write_text(txt)
  docrows.append(dict(source=rel(p),status='READ_EXACT_AVAILABLE_FILE',sha256=sha(p)))
 docrows.append(dict(source='PhD_Meeting_Discussion_Detailed_Explanation.pdf',status='NOT_FOUND_IN_PROJECT; consolidated roadmap explicitly references the meeting PDF; not independently verified',sha256='NOT_AVAILABLE'))
 table('tables/source_authority.csv',pd.DataFrame(docrows),[ROOT/'notebooks/plan'/n for n in docs],'Exact available source documents; missing requested PDF disclosed')
 cnnpath=ROOT/'results/analysis/2026-10-19_final_cnn_performance_diagnosis/continuation_history.csv';cnn=csv(cnnpath);last=cnn.sort_values('epoch').iloc[-1]
 cnnrow=pd.DataFrame([dict(model='CNN frozen epoch200',split='March1–15 VALIDATION',epoch=int(last.epoch),MAE=last.validation_MAE,RMSE=last.validation_RMSE,MSE=last.validation_MSE,N=720*142,R2='NOT_PREVIOUSLY_VALIDATED',NRMSE='NOT_PREVIOUSLY_VALIDATED',volume_error='NOT_PREVIOUSLY_VALIDATED',actual_vs_predicted_chart='NOT_REUSED_PROTECTED_TEST_POPULATION')])
 table('tables/cnn_validation_reused.csv',cnnrow,[cnnpath,ROOT/'results/analysis/2026-10-19_final_jan_mar_3km_cnn/split_definition.json'],'Reuse saved final-epoch March1–15 validation only; no test rows or protected charts')
 routing=js(ROOT/'results/analysis/2026-10-31_final_routing_freeze_validation/final_routing_readiness.json')
 writej('tables/frozen_routing_readiness_reference.json',routing)
 fare=ROOT/'results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_vs_distance_hexbin.png'
 if fare.exists():source(fare)
 unavailable=[('request origin',NA),('driver rejection counts','REQUEST_LEVEL_DRIVER_REJECTION_DIAGNOSTIC_NOT_AVAILABLE'),('unmatched causes','CAUSE_NOT_PERSISTED'),('per-episode Q/TD/target diagnostics',NA),('CNN NRMSE/R2/volume and safe actual-vs-predicted plot','NOT_PREVIOUSLY_VALIDATED'),('privacy epsilon/delta/noise/clipping/accounting','NOT_APPLICABLE_TO_CURRENT_BASELINE'),('independent meeting PDF','REQUESTED_SOURCE_NOT_FOUND')]
 lim=pd.DataFrame(unavailable,columns=['diagnostic','status']);table('tables/09_limitations.csv',lim,[CP/'manifest.json'],'Persisted field inventory; do not infer unavailable values')
 questions=['Is the wide empirical fare-support action range acceptable given observed acceptance/revenue?','Is the grouping and selected parametric sensitivity approach acceptable?','Is slot-level accepted-revenue the desired objective?','Should accepted-but-unmatched revenue remain in pricing reward?','Are16-slot/8-hour terminal segments appropriate?','What horizon and fixed evaluation are required for convergence/stability claims?','Is fixed development evaluation needed before further training?','What evidence is required before Differential Privacy?']
 table('tables/10_open_review_questions.csv',pd.DataFrame({'question':questions,'decision':'UNRESOLVED_REVIEWER_DECISION'}),[ROOT/'notebooks/plan'/docs[0]],'Evidence-based questions, no decisions invented')
 method=pd.DataFrame([('version',c['version']),('P_base_USD',c['P_base']),('L_base_km',c['L_base']),('fare_support_USD','6.60–94.70'),('state',','.join(c['state_features'])),('actions',json.dumps(c['actions'])),('reward','Accepted offered revenue including unmatched; rejected zero'),('acceptance','P_offer <= P_base+(P_base/epsilon)*(L-L_base)/L_base'),('transition','One destination per30min slot;142 contexts'),('gamma',c['gamma']),('episode_slots',c['episode_slots']),('privacy','NON_PRIVATE')],columns=['item','definition'])
 table('tables/01_methodology.csv',method,[V/'methodology_contract.json',V/'fare_bounds_contract.json'],'Frozen definitions, no recomputation')
 for src,dst in [('episode_summary.csv','02_episode_summary.csv'),('acceptance_dispatch_summary.csv','03_passenger_funnel.csv'),('action_summary.csv','04_action_economics.csv'),('action_by_episode.csv','05_action_by_episode.csv'),('learning_summary.csv','06_learning.csv'),('sensitivity_runtime_summary.csv','07_sensitivity.csv')]:
  table('tables/'+dst,pd.read_csv(O/src),[O/src],'Identical numbered review-table copy')
 table('tables/08_technical_status.csv',pd.DataFrame([(k,str(v)) for k,v in validation.items()],columns=['check','result']),[E/'health_gate.json',S/'health_gate.json',O/'numerical_reconciliation.json'],'Saved validation plus report consistency checks')
 common=f'''<!-- V3_REVIEW_CURRENT_BEGIN -->
SOURCE_ALIGNED_SLOT_PRICING_V3 = PAUSED_AFTER_EPISODE10_FOR_REVIEW (scientific review scope; not a claim that a live process was stopped).

AUTHORITATIVE_EPISODES = 1–10
TRAINING_WINDOW = {summary['window']}
FINAL_RUNTIME_TIMESTAMP = {summary['final_timestamp']}
EP01_EP10_REQUESTS = {total['requests']}
EP01_EP10_ACCEPTED = {total['accepted']}
EP01_EP10_REJECTED = {total['rejected']}
EP01_EP10_ASSIGNMENTS = {total['assignments']}
EP01_EP10_ACCEPTED_UNMATCHED = {total['accepted_unmatched']}
EP01_EP10_ACCEPTED_REVENUE_USD = {total['accepted_revenue']:.10f}
REPLAY_SIZE = {fin['replay_size']}
OPTIMIZER_UPDATES = {fin['optimizer_updates']}
EPSILON = {fin['epsilon']!r}
AUTHORITATIVE_CHECKPOINT = {summary['checkpoint']}
POST_EP10 = POST_EP10_UNPLANNED_CONTINUATION_NOT_USED_FOR_REVIEW; PRESERVED_AS_PROVENANCE_NOT_USED; NOT_AUTHORIZED_FOR_REVIEW.
MARCH17_31 = UNTOUCHED
BROADER_REGRESSION_BASELINE = 181 passed / 0 failed / 0 errors (existing evidence, not rerun).
NEXT_STEP = ACADEMIC_REVIEW_OF_EPISODE1_TO_10_RESULTS
<!-- V3_REVIEW_CURRENT_END -->
'''
 # Identical authoritative block makes literal cross-document validation unambiguous.
 paths=[ROOT/'README.md',V/'README.md',T/'README.md',S/'README.md',O/'README.md']
 chronology='''## Completed implementation chronology

Methodology/fare/fitted-family freeze → V3 implementation and bounded validation → historical regression isolation (181-pass baseline) → full-runtime checkpoint equivalence → Episode1 complete → Episodes2–10 complete → authoritative scientific review at Episode10. Earlier readiness/blocked statements are historical, superseded snapshots. No current regression/checkpoint blocker is asserted.
'''
 sourcegap='''## Source authority and reporting scope

The exact consolidated roadmap, latest dynamic-pricing clarification and weather-scenario explanation were read; extracted texts and hashes are in tables/source_authority.csv and source_manifest.json. The separately requested PhD_Meeting_Discussion_Detailed_Explanation.pdf was not found in the project. Its source numbering/content is not independently verified; the consolidated roadmap explicitly describes incorporating the meeting explanation. This is a disclosed source-document gap, not invented evidence.
'''
 actiontext=md(a[['action','factor','P_offer','requests_exposed','acceptance_rate','accepted_revenue_per_exposed_request']])
 body=f'''# Episodes1–10 academic review

## Executive summary

{common}
EARLY_TRAINING_REVIEW. Training completed through Episode10 with no recorded failure; saved gates support numerical stability, checkpoint validity and unchanged routing. LEARNING_STARTED=YES. CONVERGED=NOT_ESTABLISHED. POLICY_STABLE=NOT_ESTABLISHED. No fixed policy evaluation supports superiority, optimality or production-readiness claims.

Stage2 totals are Episodes2–10 only: requests269726; accepted62459; rejected207267; assignments48862; accepted-unmatched13597; accepted revenue1592945.6USD. The common block above correctly adds Episode1 using saved artifacts.

{sourcegap}
## Passenger acceptance, offers and dispatch

Actions are selected proactively for142 destination contexts before each30-minute slot; requests inherit the context action. Common frozen P_base={c['P_base']}USD, L_base={c['L_base']}km. P_offer=alpha*P_base. P_max=P_base+(P_base/epsilon)*(L−L_base)/L_base. Actual accepted boolean is preserved; all saved requests satisfy the inclusive comparison (zero mismatches). The checkpoint's primitive request audit was extracted without constructing runtime objects or drawing samples. Full audit: tables/request_level_audit.parquet. Sample: earliest slot nearest median request volume; up to300 evenly spaced request IDs. Origin is unavailable; other acceptance inputs and joined slot/context action are retained. P_offer/P_max plots use this deterministic actual sample and linear axes without clipping.

Passenger rejection is distinct from accepted-but-unmatched. Assignment counts describe dispatch, not completed rides. CAUSE_NOT_PERSISTED; no causal explanation of unmatched counts is inferred. Driver eligibility in src/dispatch/dispatch.py:find_eligible_vehicle requires offered fare >= persisted profiles.price_preference for an otherwise eligible vehicle. src/simulation/slot_pricing_v3.py passes engine.profiles.price_preference. No hypothetical0.85*P_base driver rule is substituted. REQUEST_LEVEL_DRIVER_REJECTION_DIAGNOSTIC_NOT_AVAILABLE.

## Action economics and reward

{actiontext}

The observed price/acceptance/revenue trade-off is descriptive; action exposures differ by context and time. The most frequent or highest-revenue action is not declared best. Reward is accepted offered revenue including accepted-unmatched, not served/platform realised earnings. Slot accepted offers, reward, replay reward and context sums reconcile to legitimate floating-point summation tolerance.

## Learning and chronology

{CAVEAT} This caveat appears on every episode-comparison chart. Loss is the saved mean of eight updates per warm slot, not a complete per-update trace. Episode means average those equal-sized update blocks. Q/TD, target statistics, online-target differences and weight-change norms were not persisted per episode: {NA}. Loss does not establish Q magnitude or convergence. Warmup1000, eight updates per warm slot, Episode1 updates72 and Episode10 cumulative1224 are reconciled; epsilon follows cumulative optimizer updates only.

## Sensitivity and weather/time

Runtime tables include only exercised conditions, using saved request draws directly for SD/quantiles. Frozen families: GLOBAL/RAW_15/T3_POOLED/T4_POOLED truncated normal; RAW_13/T1_G1/T1_POOLED lognormal; T2_POOLED generalized gamma. T2–T4 are DENSE_SCENARIO_POOLING_DUE_TO_CLUSTER_INSTABILITY, not sparse fallback. T1 raw/pool eligibility fallbacks are recorded separately; fallback_level is retained without misleading relabelling. Family-fit errors in methodology_contract.json remain limitations; T1 median overestimation is approximately20% in the saved fit comparisons. Runtime quantiles summarize saved draws, not a refit or proof of exact empirical fit.

## Operational, routing, fleet and causal state

Routing checkpoint/hash is recorded in tables/routing_health.csv. Routing169D→64→32→9 remains frozen; action order STAY,N,NE,E,SE,S,SW,W,NW. Saved valid15D next-state checks include the nine-probability block; no pricing-induced routing training. Existing routing-readiness evidence (MODEST / UNCERTAIN BUT POSITIVE; non-STAY signal INCONCLUSIVE) is reproduced in tables/frozen_routing_readiness_reference.json, including its limitations; public-state label nonidentifiability remains a concern. Operational traces contain finite mu/sigma/F_hat/H_hat for all observed boundaries. Persistent evolution is supported by the full-runtime continuation contract and saved gates; it is not independently inferred merely from smooth plotted values. Fleet health reports conserved counts, active commitments/missions and cumulative charging-event counters. Event counts are not charging completions or durations. Dedicated per-cause energy/double-assignment counts were not saved; only runtime hard checks/gates are asserted.

Drop-off uses frozen causal lagged moving-average destination counts, normalized at the current boundary, with carry-forward/historical initialization. No future data are introduced. Detailed probability histories are not regenerated; saved state and technical validations are the evidence.

## CNN and historical fare evidence

Reuse only saved epoch200 March1–15 validation from continuation_history.csv and the declared split: tables/cnn_validation_reused.csv. MAE/RMSE and population are traceable there. R²/NRMSE/volume error and an authoritative safe-population actual-versus-predicted chart were not persisted in these validation artifacts: NOT_PREVIOUSLY_VALIDATED. Existing CNN TEST charts span March16–31 and were not opened/reused. No CNN retraining/inference was run.

Historical fare-distance investigation is linked, not recalculated: results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_vs_distance_hexbin.png (historical calibration context, not V3 training results). V3 numerical fare support is exclusively the pinned fare_bounds_contract.json; broad empirical bounds are project-approved, not statutory limits or proof of economic optimality.

## Privacy and limitations

CURRENT_V3_BASELINE=NON_PRIVATE. DIFFERENTIAL_PRIVACY=NOT_IMPLEMENTED/NOT_EVALUATED; privacy epsilon/delta/noise/clipping/accounting and privacy-versus-utility are NOT_APPLICABLE_TO_CURRENT_BASELINE. Only Episodes1–10 are scientifically reviewed. Episode11 and partial12 provenance is excluded from all numerical review inputs. No protected-period generalization or convergence is tested. Request origins and driver/dispatch cause diagnostics are unavailable; source PDF and CNN validation visualization gaps remain explicit. Selected sensitivity fits are approximations. Later process status is a provenance snapshot, not a claimed operational stop.

## Questions for Academic Review

'''+ '\n'.join(f'{i+1}. {q}' for i,q in enumerate(questions))+'''\n
## Files and reproducibility

Run `MPLCONFIGDIR=/tmp/v3_review_mpl /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/report_v3_ep01_ep10.py` from the project root. This reads saved Episode10 evidence only; no model or simulator imports. artifact_provenance.csv, source_manifest.json and chart_manifest.json give filters, columns, counts, aggregation and hashes. Numbered tables01–10 and charts are provided in tables/ and charts/. Reporting tests validate scope, reconciliations, unavailable fields and documentation consistency.\n'''
 (O/'README.md').write_text(body)
 for path in paths[:-1]:
  old=path.read_text() if path.exists() else ''
  if path==ROOT/'README.md':
   # Remove superseded V3 status preamble, retaining explicitly historical V2 material.
   cut=old.find('## Consolidated V2 academic review');old=old[cut:] if cut>=0 else old
   path.write_text('# Current V3 review status\n\n'+common+'\nPrimary review: '+rel(O/'README.md')+'\n\n'+chronology+'\n## Historical development context (not current status)\n\n'+old)
  elif path==V/'README.md':
   path.write_text('# Source-aligned slot pricing V3 — current review\n\n'+common+'\nPrimary narrative: [Episodes1–10 review](review_ep01_ep10/README.md).\n\n'+chronology+'\nFrozen scientific contracts remain in the JSON/CSV files in this folder. Prior bounded/test counts are preserved in their original artifacts; they are not training performance. Checkpoint schema V3_FULL_RUNTIME_1; full-state continuation has no simulator resets. See review for actual per-episode results, gaps, fit limitations and source authority.\n')
  elif path==S/'README.md':path.write_text('# Stage2 complete — included in review\n\n'+common+'\nStage2 ONLY (Episodes2–10): requests269726; accepted62459; rejected207267; assignments48862; accepted-unmatched13597; accepted revenue1592945.6USD. Status COMPLETED; failure null; all persisted technical health gates PASS. Episode10 checkpoint is authoritative. Raw artifacts remain unchanged.\n')
  else:path.write_text('# Training stage index\n\n'+common+'\nEpisode1: March1 00:00–07:30; models/pricing_dqn/source_aligned_slot_pricing_v3/episode_001/episode_001. Stage2: March1 08:00–March4 07:30, authoritative Episode10 path above. Stage3: post-review-boundary continuation, excluded provenance. Full-state resume after review requires a new explicit decision; no automatic continuation is authorized by this reporting task.\n')
 ep1=ep.iloc[0];(E/'README.md').write_text('# Episode1 completed\n\n'+md(ep1.to_frame('value').reset_index())+'\n\nIncluded in the Episodes1–10 review; no failure. Original checkpoint and outputs preserved. Review: ../../review_ep01_ep10/README.md\n')
 (T/'stage_ep11_ep25/README.md').write_text('# POST_EP10_UNPLANNED_CONTINUATION_NOT_USED_FOR_REVIEW\n\nAll artifacts are preserved provenance and excluded from review tables, charts, totals and conclusions. The reporting-time persisted status records episode '+str(status_snapshot['episode'])+', slot '+str(status_snapshot['slot'])+', latest completed episode '+str(status_snapshot['latest_completed_episode'])+', status '+status_snapshot['status']+'. Episode12 is partial, not complete. This is a saved-status snapshot, not live process verification; this task neither stopped nor signalled the process. Scientific review remains Episode10. The continuation had prior overnight launch authorization, but the latest reporting instruction classifies it as unplanned/excluded for scientific review. No historical artifacts were erased.\n')
 agreement=all(common in p.read_text() for p in paths)
 writej('documentation_consistency_check.json',dict(status='PASS' if agreement else 'FAIL',paths=[rel(p) for p in paths],literal_common_block=True if agreement else False,process_pause_claimed=False,scientific_review_pause=True));assert agreement
 # Audit active dependencies without rewriting historical V2 READMEs.
 links=[V/'fare_bounds_contract.json',V/'conditional_distribution_contract.json',V/'weather_group_contract.json',V/'state_contract.json',V/'pricing_version_interface_contract.json']
 table('tables/active_contract_readme_audit.csv',pd.DataFrame([dict(contract=source(p),status='Frozen contract retained; current review backlink provided in V3 README',historical_readmes='Not rewritten') for p in links]),links,'Status/backlink audit only; no methodology changes')

if __name__=='__main__':main()
