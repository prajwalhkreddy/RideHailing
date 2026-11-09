"""Frozen V1 staged execution/monitoring only; no methodology or update changes."""
from pathlib import Path
import json,hashlib,pickle,os,time,signal,fcntl,traceback
from dataclasses import asdict
import numpy as np,pandas as pd
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN,masked_targets
from src.pricing.passenger_sensitive_v1 import PositiveEpsilonProvider,feasible_mask,P_BASE_USD,ACTIONS
from src.simulation.passenger_sensitive_v1 import PassengerSensitiveExperiment
R=Path(__file__).parent;V=R.parent;M=Path('models/pricing_dqn/passenger_sensitive_v1_seed42/staged_training_001')
PROTOCOL=Path('results/analysis/2026-10-31_final_pricing_training_protocol/episode_protocol.json')
ROUTE=Path('models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras')
ROUTE_HASH='db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a'
def js(p,x):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v),allow_nan=False)+'\n');tmp.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def weights(model):return hashlib.sha256(b''.join(x.tobytes() for x in model.get_weights())).hexdigest()
def fingerprint(d):
 h=hashlib.sha256()
 for v in d.online.weights+d.target.weights+list(d.online.optimizer.variables):h.update(v.numpy().tobytes())
 h.update(pickle.dumps((list(d.replay.items),d.replay.rng.bit_generator.state,d.rng.bit_generator.state,d.training_steps)))
 return h.hexdigest()
def write(name,rows):pd.DataFrame(rows).to_csv(R/(name+'.csv'),index=False)
def finite(x):
 if not np.isfinite(x).all():raise ValueError('Nonfinite learner diagnostics')
def mc_returns(rewards,gammas,dones):
 g=np.empty(len(rewards));running=0.
 for i in range(len(g)-1,-1,-1):
  running=rewards[i]+(0 if dones[i] else gammas[i]*running);g[i]=running
 return g
class EvaluationView(PassengerSensitiveDQN):
 """Read-only shared network view: transition store is deliberately a no-op."""
 def __init__(self,d):
  self.online=d.online;self.target=d.target;self.config=d.config;self.training_steps=d.training_steps;self.rng=d.rng
 def store(self,*args):pass
 def complete_slot(self,*args):raise RuntimeError('Development optimization prohibited')

def provider(seed):
 s=json.loads((V/'restricted_calibration_support.json').read_text())
 assert (s['positive_support_lower'],s['positive_support_upper'])==(.017809913104763053,27.324599740032788)
 return PositiveEpsilonProvider(np.load(V/'positive_epsilon_calibration.npy',mmap_mode='r'),s['positive_support_lower'],rng=np.random.default_rng(seed),provenance=s,frozen=True)

def attach_monitor(d):
 original=d.select_action;train=d.train_step;d.monitor_actions=[];d.monitor_updates=[];cache={}
 def select(state,mask,*,explore=True):
  key=np.asarray(state,dtype=np.float32).tobytes()
  if key not in cache:cache[key]=d.online(np.asarray(state,dtype=np.float32)[None,:],training=False).numpy()[0]
  q=cache[key];finite(q)
  a=original(state,mask,explore=explore)
  if a is None:raise ValueError('Empty mask on valid V1 request')
  if not mask[a.action_index]:raise ValueError('Masked action violation')
  d.monitor_actions.append(dict(selected_Q=float(q[a.action_index]),greedy_action=int(np.argmax(np.where(mask,q,-np.inf))),explored=a.explored))
  return a
 def step():
  result=train()
  if result is not None:
   finite([result['loss']]);d.monitor_updates.append(dict(update=d.training_steps,loss=result['loss']))
  return result
 d.select_action=select;d.train_step=step;d.monitor_cache=cache

def policy_metrics(frame,episode,kind,policyrows,freqrows):
 n=len(frame)
 for k in range(1,8):
  f=frame[frame.feasible_action_count==k];counts=np.bincount(f.selected_action_index.to_numpy(int),minlength=7);p=counts[counts>0]/len(f) if len(f) else np.array([])
  entropy=float(-(p*np.log(p)).sum()) if len(f) and k>=2 else None
  greedy=np.bincount(f.greedy_action.to_numpy(int),minlength=7) if len(f) else np.zeros(7)
  row=dict(episode=episode,kind=kind,feasible_arms=k,requests=len(f),percentage=100*len(f)/n if n else 0,assignments=int(f.assignment_status.sum()),assignment_rate=float(f.assignment_status.mean()) if len(f) else None,mean_reward=float(f.reward.mean()) if len(f) else None,mean_selected_factor=float(f.selected_factor.mean()) if len(f) else None,mean_offer=float(f.P_offer_USD.mean()) if len(f) else None,entropy=entropy,normalized_entropy=entropy/np.log(k) if entropy is not None else None,greedy_action_concentration=float(greedy.max()/len(f)) if len(f) and k>=2 else None,exploration_action_share=float(f.explored.mean()) if len(f) else None)
  policyrows.append(row)
  for j,c in enumerate(counts):freqrows.append(dict(episode=episode,kind=kind,feasible_arms=k,factor=ACTIONS[j],N=int(c),share=float(c/len(f)) if len(f) else None))

def episode_metrics(x,d,episode,kind,losses,policyrows,freqrows):
 f=pd.DataFrame(x.request_audit);mon=pd.DataFrame(x.dqn.monitor_actions);assert len(f)==len(mon)
 for c in mon:f[c]=mon[c].to_numpy()
 t=pd.DataFrame(x.linker.audit);assert len(t)==len(f) and int(t.done.sum())==1
 assert t.Request_ID.is_unique and f.Request_ID.is_unique
 assert list(t.Request_ID)==list(f.Request_ID)
 assert list(t.next_actionable_request_id.iloc[:-1].astype(int))==list(f.Request_ID.iloc[1:])
 assert (t.gamma_eff.gt(0)&t.gamma_eff.le(1)).all()
 assert np.allclose(t.gamma_eff,.99**(t.delta_t_minutes/30))
 assert (f.P_offer_USD<=f.P_accept_c).all() and f.feasible_action_count.ge(1).all()
 assert np.isclose(f.reward.sum(),f.loc[f.assignment_status,'P_offer_USD'].sum(),rtol=1e-12)
 for row in t.itertuples():
  if not row.done and not any(row.next_action_mask):raise ValueError('Invalid next mask')
 policy_metrics(f,episode,kind,policyrows,freqrows)
 # Bounded deterministic evenly spaced trajectory sample; current checkpoint Q versus realized full returns.
 g=mc_returns(t.reward.to_numpy(),t.gamma_eff.to_numpy(),t.done.to_numpy())
 idx=np.linspace(0,len(f)-1,min(512,len(f)),dtype=int);s=np.stack(f.state_13d.iloc[idx]);actions=f.selected_action_index.iloc[idx].to_numpy(int)
 q=d.online(s,training=False).numpy();finite(q);selected=q[np.arange(len(idx)),actions];gg=g[idx];err=np.abs(selected-gg)
 mc=dict(episode=episode,kind=kind,N=len(idx),mean_G=float(gg.mean()),median_G=float(np.median(gg)),P95_G=float(np.quantile(gg,.95)),mean_selected_Q=float(selected.mean()),median_selected_Q=float(np.median(selected)),MAE_Q_G=float(err.mean()),median_absolute_error=float(np.median(err)),relative_median_calibration_ratio=float(np.median(selected)/np.median(gg)) if np.median(gg)!=0 else None,correlation=float(np.corrcoef(selected,gg)[0,1]) if np.std(selected)>0 and np.std(gg)>0 else None)
 np.savez_compressed(R/f'mc_probe_{kind}_{episode:02d}.npz',Q=selected,G=gg)
 no_price=int((f.pricing_outcome=='OFFERED_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER').sum());unmatched=int((~f.assignment_status).sum())
 summary=dict(episode=episode,kind=kind,source_start=str(pd.Timestamp(x.timestamp)-pd.Timedelta(minutes=30*x.slot_index)),source_end=str(x.timestamp),requests_seen=len(f),offers_generated=len(f),no_feasible_action=0,assignments=int(f.assignment_status.sum()),accepted_unmatched=unmatched,no_price_eligible_driver=no_price,other_unmatched=unmatched-no_price,revenue=float(f.reward.sum()),assignment_rate=float(f.assignment_status.mean()),mean_offer=float(f.P_offer_USD.mean()),median_offer=float(f.P_offer_USD.median()),transitions_added=len(t) if kind=='training' else 0,replay_size=len(d.replay),optimizer_updates_cumulative=d.training_steps,exploration_epsilon=d.epsilon,choice_request_rate=float(f.feasible_action_count.ge(2).mean()),forced_request_rate=float(f.feasible_action_count.eq(1).mean()),mean_abs_Q=float(np.abs(q).mean()),max_abs_Q=float(np.abs(q).max()),mean_loss=float(np.mean(losses)) if losses else None)
 for j,a in enumerate(ACTIONS):summary[f'action_{a}']=int(f.selected_action_index.eq(j).sum());summary[f'choice_action_{a}']=int((f.selected_action_index.eq(j)&f.feasible_action_count.ge(2)).sum())
 for k in range(1,8):summary[f'feasible_{k}']=int(f.feasible_action_count.eq(k).sum())
 # Replay diagnostics: fixed index rule without consuming replay RNG.
 rr=list(d.replay.items);ri=np.linspace(0,len(rr)-1,min(512,len(rr)),dtype=int);z=[rr[i] for i in ri]
 states=np.stack([a[0] for a in z]);nxt=np.stack([a[3] for a in z]);acts=np.array([a[1] for a in z]);rew=np.array([a[2] for a in z]);done=np.array([a[4] for a in z]);masks=np.stack([a[5] for a in z]);dt=np.array([a[6] for a in z])
 qq=d.online(states,training=False).numpy();targets=masked_targets(rew,done,d.target(nxt,training=False).numpy(),masks,dt);finite(qq);finite(targets)
 sq=qq[np.arange(len(z)),acts];td=np.abs(targets-sq)
 qrow=dict(episode=episode,kind=kind,N=len(z),mean_abs_Q=float(np.abs(qq).mean()),median_abs_Q=float(np.median(np.abs(qq))),P95_abs_Q=float(np.quantile(np.abs(qq),.95)),max_abs_Q=float(np.abs(qq).max()),Q_min=float(qq.min()),Q_max=float(qq.max()),mean_selected_Q=float(sq.mean()),median_selected_Q=float(np.median(sq)),nonfinite_Q_count=0)
 tdrow=dict(episode=episode,kind=kind,mean_target=float(targets.mean()),median_target=float(np.median(targets)),mean_abs_TD=float(td.mean()),median_abs_TD=float(np.median(td)),P95_abs_TD=float(np.quantile(td,.95)),mean_loss=float(np.mean(losses)) if losses else None,median_loss=float(np.median(losses)) if losses else None,max_loss=float(np.max(losses)) if losses else None,nonfinite_loss_count=0,nonfinite_target_count=0)
 return summary,qrow,tdrow,mc

def main():
 M.mkdir(parents=True,exist_ok=True);lock=(M/'writer.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (M/'initialization.json').exists():raise RuntimeError('Existing staged initialization: do not silently restart or load any checkpoint')
 assert sha(ROUTE)==ROUTE_HASH
 protocol=json.loads(PROTOCOL.read_text());specs=protocol['starts'][:25];assert protocol['slots']==16
 for s in specs:assert pd.Timestamp('2026-03-01')<=pd.Timestamp(s['start']) and pd.Timestamp(s['start'])+pd.Timedelta(hours=8)<=pd.Timestamp('2026-03-16')
 d=PassengerSensitiveDQN();attach_monitor(d);assert not len(d.replay) and d.training_steps==0 and d.epsilon==1 and weights(d.online)==weights(d.target)
 d.save(M/'initial');init=dict(INITIALIZATION_SOURCE='FRESH',OLD_EP25_CHECKPOINT_LOADED='NO',online_hash=weights(d.online),target_hash=weights(d.target),checkpoint_hash=sha(M/'initial'/'online.keras'),seed=42);js(M/'initialization.json',init)
 js(R/'run_config.json',dict(**init,config=asdict(d.config),episodes=specs,slots_per_episode=16,stop_after=25,protocol_source=str(PROTOCOL),protocol_sha256=sha(PROTOCOL),routing=str(ROUTE),routing_sha256=ROUTE_HASH,development={'start':'2026-03-16','slots':4,'environment_seed':424242,'epsilon_seed':424242},epsilon_seed_rule='Use authoritative per-episode environment_seed with independent NumPy Generator; fixed424242 for development',stage2_rule='Persist checkpoint10; manual evidence review before allowing episode11; no automatic methodology changes'))
 names=['episode_summary','slot_summary','stage_summary','q_diagnostics','td_diagnostics','mc_return_calibration','feasible_arm_policy_summary','action_frequency_by_feasible_count','development_evaluation','loss_by_update'];data={n:[] for n in names}
 inv={k:0 for k in ['masked_action_violations','passenger_threshold_violations','nonfinite_Q','nonfinite_loss','nonfinite_target','invalid_gamma','invalid_next_mask','optimizer_cadence_violations','protected_date_access','development_mutation','old_checkpoint_loaded']};js(R/'invariant_summary.json',inv)
 stop=[]
 for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,lambda s,f:stop.append(s))
 cp=str(M/'initial');ep=0;x=None
 def persist():
  for k,v in data.items():
   if v:write(k,v)
  js(R/'invariant_summary.json',inv)
 def status(name,stage=None,summary=None):
  r=summary or {};z=dict(status=name,pid=os.getpid(),stage=stage or ('STAGE1' if ep==1 else 'STAGE2' if ep<=10 else 'STAGE3'),episode=ep,slot=0 if x is None else x.slot_index,requests_seen=sum(a['requests_seen'] for a in x.reports) if x else 0,transitions=sum(a['transitions_added'] for a in x.reports) if x else 0,replay_size=len(d.replay),optimizer_updates=d.training_steps,exploration_epsilon=d.epsilon,revenue=sum(a['reward'] for a in x.reports) if x else 0,assignments=sum(a['assigned'] for a in x.reports) if x else 0,choice_request_rate=r.get('choice_request_rate'),mean_abs_Q=r.get('mean_abs_Q'),max_abs_Q=r.get('max_abs_Q'),mean_loss=r.get('mean_loss'),mean_abs_TD=r.get('mean_abs_TD'),last_checkpoint=cp,invariant_status='PASS' if not any(inv.values()) else 'FAIL',protected_period_untouched=True)
  js(R/'training_status.json',z);print(json.dumps(z),flush=True)
 try:
  for spec in specs:
   ep=spec['episode'];d.monitor_actions=[];d.monitor_updates=[];d.monitor_cache.clear()
   x=PassengerSensitiveExperiment(provider=provider(spec['environment_seed']),learner=d,seed=spec['environment_seed'],start=spec['start'],routing_checkpoint=ROUTE,validation_only=False)
   rh=weights(x.policy);status('EPISODE_INITIALIZED')
   for j in range(16):
    assert pd.Timestamp('2026-03-01')<=x.timestamp<pd.Timestamp('2026-03-16')
    d.monitor_cache.clear();before=d.training_steps;u=len(d.monitor_updates)
    rep=x.run_slot(terminal=j==15,train_dqn=True)
    expected=8 if len(d.replay)>=1000 else 0
    if d.training_steps-before!=expected:inv['optimizer_cadence_violations']+=1;raise ValueError('Optimizer cadence')
    assert rep['fleet_size']==5000 and weights(x.policy)==rh
    finite([v.energy_level for v in x.fleet.vehicles]);assert all(v.energy_level>=0 for v in x.fleet.vehicles)
    for model in [d.online,d.target]:
     for w in model.get_weights():finite(w)
    if rep['no_feasible_pricing_action']:inv['masked_action_violations']+=1;raise ValueError('Unexpected empty mask')
    slot=dict(episode=ep,slot=j+1,**rep,replay_size=len(d.replay),optimizer_updates_cumulative=d.training_steps,exploration_epsilon=d.epsilon,mean_loss=float(np.mean([z['loss'] for z in d.monitor_updates[u:]])) if len(d.monitor_updates)>u else None)
    data['slot_summary'].append(slot);data['loss_by_update'].extend(dict(episode=ep,slot=j+1,**v) for v in d.monitor_updates[u:]);persist();status('SLOT_COMPLETED')
    if stop:cp=str(M/f'stopped_ep{ep:03d}_slot{j+1:02d}');d.save(cp);status('STOPPED_SAFE');return
   summary,qr,td,mc=episode_metrics(x,d,ep,'training',[z['loss'] for z in d.monitor_updates],data['feasible_arm_policy_summary'],data['action_frequency_by_feasible_count'])
   summary.update(training_samples_drawn=len(d.monitor_updates)*64,total_training_samples_drawn=d.training_steps*64,total_transitions_added=sum(v['transitions_added'] for v in data['episode_summary'])+summary['transitions_added'])
   summary['replay_sampling_reuse_ratio']=summary['total_training_samples_drawn']/summary['total_transitions_added']
   data['episode_summary'].append(summary);data['q_diagnostics'].append(qr);data['td_diagnostics'].append(td);data['mc_return_calibration'].append(mc)
   # Episode checkpoints also preserve intervening completed work; stage names exact.
   cp=str(M/f'episode_{ep:03d}');d.save(cp);persist();status('EPISODE_COMPLETE',summary={**summary,**td})
   if ep in [1,10,25]:
    before=fingerprint(d);view=EvaluationView(d);attach_monitor(view)
    dev=PassengerSensitiveExperiment(provider=provider(424242),learner=view,seed=424242,start='2026-03-16',routing_checkpoint=ROUTE,validation_only=True)
    for j in range(4):
     assert pd.Timestamp('2026-03-16')<=dev.timestamp<pd.Timestamp('2026-03-16 02:00')
     view.monitor_cache.clear();dev.run_slot(terminal=j==3,train_dqn=False,explore_pricing=False)
     if fingerprint(d)!=before:inv['development_mutation']+=1;raise ValueError('Development learner mutation')
    ds,dq,dt,dm=episode_metrics(dev,d,ep,'development',[],data['feasible_arm_policy_summary'],data['action_frequency_by_feasible_count']);ds['learner_fingerprint_before']=before;ds['learner_fingerprint_after']=fingerprint(d);ds['learner_unchanged']=True
    data['development_evaluation'].append(ds);data['q_diagnostics'].append(dq);data['td_diagnostics'].append(dt);data['mc_return_calibration'].append(dm)
    stage=dict(stage=f'EP{ep}',episode=ep,requests=summary['requests_seen'],choice_rate=summary['choice_request_rate'],forced_rate=summary['forced_request_rate'],assignments=summary['assignments'],assignment_rate=summary['assignment_rate'],revenue=summary['revenue'],mean_offer=summary['mean_offer'],replay_size=len(d.replay),optimizer_updates=d.training_steps,exploration_epsilon=d.epsilon,mean_abs_Q=qr['mean_abs_Q'],max_abs_Q=qr['max_abs_Q'],mean_abs_TD=td['mean_abs_TD'],mean_loss=td['mean_loss'],MC_return_mean=mc['mean_G'],Q_MC_MAE=mc['MAE_Q_G'],dev_revenue=ds['revenue'],dev_assignments=ds['assignments'],dev_assignment_rate=ds['assignment_rate'],stage_status='PASS' if ep!=10 else 'PENDING_REVIEW')
    data['stage_summary'].append(stage);persist();status('STAGE_PASS' if ep!=10 else 'STAGE2_REVIEW_REQUIRED',summary={**summary,**td})
    if ep==10:
     while not (R/'stage2_decision.json').exists():
      if stop:status('STOPPED_SAFE');return
      time.sleep(5)
     dec=json.loads((R/'stage2_decision.json').read_text());stage['stage_status']=dec['status'];persist()
     if dec['status']!='PASS':status('WARN_REVIEW_REQUIRED',summary=summary);return
    del dev,view
   del x;x=None
  status('COMPLETE',summary=summary)
 except BaseException as exc:
  # Any unknown failure is still a hard gate failure; never report it as passing.
  inv['runtime_invariant_failure']=1;persist()
  failcp=M/f'failure_ep{ep:03d}_slot{0 if x is None else x.slot_index:02d}'
  try:d.save(failcp);cp=str(failcp)
  except Exception:pass
  js(R/'failure.json',dict(error=repr(exc),traceback=traceback.format_exc(),episode=ep,last_checkpoint=cp));status('FAILED');raise
if __name__=='__main__':main()
