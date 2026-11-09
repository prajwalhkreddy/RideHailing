from pathlib import Path
import json
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;V=R.parent
s=json.loads((R/'training_status.json').read_text()) if (R/'training_status.json').exists() else dict(status='INITIALIZING',episode=0,slot=0)
def read(n):
 p=R/(n+'.csv')
 return pd.read_csv(p) if p.exists() and p.stat().st_size>1 else pd.DataFrame()
ep=read('episode_summary');st=read('stage_summary');dev=read('development_evaluation');q=read('q_diagnostics');td=read('td_diagnostics');mc=read('mc_return_calibration');pol=read('feasible_arm_policy_summary')
def table(f):
 if f.empty:return 'Not reached.\n'
 return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(f'{v:.7g}' if isinstance(v,float) else str(v) for v in row)+' |' for row in f.itertuples(index=False,name=None))+'\n'
def plot(f,x,y,name,title):
 if f.empty:return
 fig,ax=plt.subplots(figsize=(9,4));ax.plot(f[x],f[y],marker='o',ms=3);ax.set(xlabel=x,ylabel=y,title=title);fig.tight_layout();fig.savefig(R/name,dpi=140);plt.close(fig)
for y,name in [('revenue','training_revenue_by_episode.png'),('assignment_rate','training_assignment_rate_by_episode.png'),('choice_request_rate','choice_request_rate_by_episode.png')]:plot(ep,'episode',y,name,'V1 staged training — '+y)
for y,name in [('revenue','development_revenue_stage_checkpoints.png'),('assignment_rate','development_assignment_stage_checkpoints.png')]:plot(dev,'episode',y,name,'Fixed March16 greedy development — '+y)
if not q.empty:plot(q[q.kind=='training'],'episode','mean_abs_Q','q_magnitude_by_episode.png','Deterministic bounded replay Q probe')
if not td.empty:plot(td[td.kind=='training'],'episode','mean_abs_TD','td_error_by_episode.png','Deterministic bounded replay absolute TD error')
loss=read('loss_by_update');plot(loss,'update','loss','loss_by_update.png','V1 optimizer loss')
for prefix,name,title in [('action_','action_frequency_by_episode.png','All requests: selected factors'),('choice_action_','choice_request_action_frequency_by_episode.png','Choice requests only: selected factors'),('feasible_','feasible_arm_count_by_episode.png','Feasible-arm counts')]:
 if ep.empty:continue
 cols=[c for c in ep if c.startswith(prefix)];fig,ax=plt.subplots(figsize=(9,4))
 for c in cols:ax.plot(ep.episode,ep[c],label=c.removeprefix(prefix))
 ax.set(xlabel='Episode',ylabel='Request count',title=title);ax.legend(ncol=7,fontsize=8);fig.tight_layout();fig.savefig(R/name,dpi=140);plt.close(fig)
for i in [1,10,25]:
 p=R/f'mc_probe_training_{i:02d}.npz'
 if not p.exists():continue
 z=np.load(p);fig,ax=plt.subplots(figsize=(6,5));ax.scatter(z['G'],z['Q'],s=8,alpha=.5);lim=max(np.max(z['G']),np.max(z['Q']));ax.plot([0,lim],[0,lim],ls='--',color='black');ax.set(xlabel='Realized discounted return G',ylabel='Checkpoint selected-action Q',title=f'Episode{i}: Q versus realized return');fig.tight_layout();fig.savefig(R/f'q_vs_mc_return_ep{i:02d}.png',dpi=140);plt.close(fig)
reached=int(ep.episode.max()) if not ep.empty else 0
stage=str(s.get('status'));failed=stage=='FAILED';complete=stage=='COMPLETE'
summary=f'''Fresh Passenger-Sensitive Pricing V1 staged training: **{stage}**. Completed episodes={reached}; current episode={s.get('episode')}, slot={s.get('slot')}. One fresh seed42 learner; no old checkpoint resumed. This invocation is Episode1 only; later stages require separate authorization. Choice and forced requests are reported separately. Convergence=NO; numerical/policy stability remain UNCLEAR until stage evidence is reviewed. March17–31 untouched. Training beyond25 not started. See [staged report](LINK).'''
choice='Not yet available' if ep.empty else str(ep.iloc[-1].choice_request_rate)
head=['Purpose','Frozen Methodology','Fresh Initialization','Training Data Boundary','Training Protocol','Request-Level Replay','Feasible-Arm Distribution','Choice vs Forced Requests','Episode 1 Smoke Test','Episode 10 Diagnostic','Episode 25 Review','Q / TD / Loss Diagnostics','Monte-Carlo Return Calibration','Replay Utilization','Fixed March16 Development Evaluation','Stage-Gate Decisions','Training Stability Assessment','Convergence Status','Protected Evaluation Status','Artifact Index']
texts=[summary.replace('LINK','README.md'),'Positive truncated empirical support[0.017809913104763053,27.324599740032788], no extra floor; global references unchanged; raw preference P_base-scaled equation; P_accept=max(0.85*P_base,P_raw). Seven factors0.85–1.15.13D state and all frozen model/dispatch interfaces unchanged.','Fresh online/target/Adam/replay/RNG/counters seed42. Initialization hashes and exact source in run_config.json and model initialization.json; no prior pricing checkpoint loaded.','Authoritative saved March1–15 episode schedule, first25 only; exact start/end per episode in run_config.json/episode_summary.csv. March16 fixed development only.','16×30min slots;8 updates/warm slot after1000 finalized transitions; no request-count decay or updates. Same learner persists. Three monitoring-adapter preflight tests passed.','Next chronological actionable request; masks stored; gamma=.99 per request transition; terminal reward only.','See feasible_arm_policy_summary.csv and action_frequency_by_feasible_count.csv; K1..7 separate.','Forced K1; choice K>=2. Entropy/normalized entropy/greedy concentration restricted to K>=2. Current completed-episode choice rate: '+choice,table(st[st.episode==1]) if not st.empty else 'Not reached.',table(st[st.episode==10]) if not st.empty else 'Not reached.',table(st[st.episode==25]) if not st.empty else 'Not reached.','Fixed deterministic evenly spaced sample up to512 replay entries per episode. Does not consume training RNG. Finite checks on model weights, Q, targets, losses. See q_diagnostics.csv/td_diagnostics.csv and loss_by_update.csv.',table(mc) if not mc.empty else 'Not yet available. Full chronological reward/gamma chain is computed; checkpoint Q compared on deterministic up-to512 trajectory samples. Q is not judged against immediate fare alone.','Sampled examples=64×optimizer updates; cumulative reuse ratio divides by cumulative transitions added, not current capped replay size.','Fixed March16 00:00–02:00,4 slots, environment/provider seed424242, full request flow, greedy. EvaluationView store is a no-op: no replay writes. Full weights/Adam/replay/RNG/counter fingerprint must match before/after each slot. Local trajectory audit is not replay.',table(st),'UNCLEAR pending completed stage diagnostics. Hard failure stops immediately; each stage terminates; a separate invocation reviews it before the next detached launch. No automatic parameter changes.','CONVERGED=NO by protocol;25 episodes cannot establish convergence.','March17–31 excluded. March16 not used for training; fixed diagnostics only.','run_config.json, training_status.json, invariant_summary.json, training.log; episode/slot/stage metrics; Q/TD/MC metrics; policy-by-feasible-count metrics; development_evaluation.csv; applicable plots; fresh per-episode checkpoints. Missing later-stage rows/plots mean NOT_REACHED, never inferred results.']
mapping=dict(zip(head,texts))
mapping['Detached Execution Model']='Only Stage1 Episode1 is enabled for this corrected namespace. Each worker evaluates March16, checkpoints, writes its completion marker and terminates. No automatic next-stage launch; no active Codex polling.'
mapping['Request-Step Discount']='gamma_eff=0.99 per actionable request transition, including equal timestamps. Terminal target is reward only.'
mapping['Numerical Stability']=mapping.pop('Training Stability Assessment')
mapping['Policy Stability']='UNCLEAR until separate saved-artifact stage review. Choice requests only are used to assess policy diversity.'
mapping['Protected Final Evaluation']=mapping.pop('Protected Evaluation Status')
head=['Purpose','Frozen Methodology','Fresh Initialization','Training Data Boundary','Training Protocol','Detached Execution Model','Request-Level Replay','Request-Step Discount','Feasible-Arm Distribution','Choice vs Forced Requests','Episode 1 Smoke Test','Episode 10 Diagnostic','Episode 25 Review','Q / TD / Loss Diagnostics','Monte-Carlo Return Calibration','Replay Utilization','March16 Development Evaluation','Stage-Gate Decisions','Numerical Stability','Policy Stability','Convergence Status','Protected Final Evaluation','Artifact Index']
mapping['March16 Development Evaluation']=mapping['Fixed March16 Development Evaluation']
texts=[mapping[k] for k in head]
(R/'README.md').write_text('# Passenger-Sensitive Pricing V1 — Staged Fresh Training\n\n'+'\n\n'.join(f'## {i}. {h}\n\n{t}' for i,(h,t) in enumerate(zip(head,texts),1))+'\n')
print('STAGE_REPORT_UPDATED',stage,reached)
