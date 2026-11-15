"""Explicit future launch only. Import and --verify never train."""
import copy,json,pickle,hashlib,os,traceback,time,argparse
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN,masked_targets
from src.pricing.passenger_sensitive_v1 import guard_date
from src.simulation.passenger_sensitive_v1 import PassengerSensitiveExperiment
from src.pricing.passenger_sensitive_v2 import sha256
from src.pricing.passenger_sensitive_v2_conditioned import VERSION,DEFAULT_GROUPING
from prepare_development import O,ROUTE,SEED,provider,load_fixture,evaluate,js,digest
CHECKPOINTS=(1,5,10,15,20,25)
PROTOCOL=Path('results/analysis/2026-10-31_final_pricing_training_protocol/episode_protocol.json')

def fingerprint(d):
 h=hashlib.sha256()
 for v in list(d.online.weights)+list(d.target.weights)+list(d.online.optimizer.variables):h.update(v.numpy().tobytes())
 h.update(pickle.dumps((list(d.replay.items),d.replay.rng.bit_generator.state,d.rng.bit_generator.state,d.training_steps,d.sensitivity_provider.state_dict())))
 return h.hexdigest()
def mc_returns(rewards,gamma=.99):
 if not np.isfinite(rewards).all():raise ValueError('Nonfinite reward')
 out=np.empty(len(rewards));v=0.
 for i in range(len(rewards)-1,-1,-1):v=float(rewards[i])+gamma*v;out[i]=v
 return out

def validate_episode(spec):
 t=guard_date(spec['start'],calibration=True);end=t+pd.Timedelta(hours=8)
 if t<pd.Timestamp('2026-03-01') or end>pd.Timestamp('2026-03-16'):raise ValueError('Training episode crosses permitted boundary')

def guarded_evaluation(d,operation):
 before=fingerprint(d)
 result=operation()
 if fingerprint(d)!=before:raise ValueError('Evaluation mutated training state')
 return result

def validate_continuation(metadata,config_hash,fixture_hash,support_hash):
 required={'methodology_version','sensitivity_version','episode','next_episode','update','config_sha256','fixture_manifest_sha256','support_sha256'}
 required.update({'weather_time_grouping_version','mapping_hash','conditional_support_manifest_hash','fallback_policy_version','grouping_contract_hash'})
 if not required.issubset(metadata):raise ValueError('Missing continuation metadata')
 if metadata['sensitivity_version']!=VERSION or metadata['support_sha256']!=support_hash or metadata['config_sha256']!=config_hash or metadata['fixture_manifest_sha256']!=fixture_hash:
  raise ValueError('Incompatible continuation identity')
 contract=json.loads(Path(DEFAULT_GROUPING).read_text())
 for key,expected in {'weather_time_grouping_version':contract['methodology_version'],'mapping_hash':contract['mapping_hash'],'conditional_support_manifest_hash':contract['conditional_support_manifest_hash'],'fallback_policy_version':contract['fallback_policy']['version'],'grouping_contract_hash':sha256(DEFAULT_GROUPING)}.items():
  if metadata[key]!=expected:raise ValueError('Conditional continuation mismatch')
 if metadata['episode'] not in CHECKPOINTS or metadata['next_episode']!=metadata['episode']+1:raise ValueError('Invalid continuation episode')

def schedule(run_episode,checkpoint,evaluate_checkpoint,status,start_episode=1):
 """Pure orchestration tested with mocks; hard failures never continue."""
 last=start_episode-1
 try:
  status('RUNNING',last,None)
  for episode in range(start_episode,26):
   run_episode(episode)
   if episode in CHECKPOINTS:
    checkpoint(episode);last=episode;evaluate_checkpoint(episode)
  status('COMPLETED',25,None)
 except BaseException as exc:
  status('FAILED_HARD_INVARIANT',last,{'reason':str(exc),'traceback':traceback.format_exc()});raise

def verify():
 gate=json.loads((O/'prelaunch_verification.json').read_text())
 if gate.get('verdict')!='READY_TO_LAUNCH_V2_STAGE25':raise ValueError('Conditional launch gate not ready')
 cfg=json.loads((O/'training_harness_config.json').read_text())
 if cfg['passenger_sensitivity_version']!=VERSION or cfg['stop_after']!=25 or cfg['checkpoint_episodes']!=list(CHECKPOINTS):raise ValueError('Conditional harness contract mismatch')
 for key in ['sensitivity_version','weather_time_grouping_version','mapping_hash','conditional_support_manifest_hash','fallback_policy_version','grouping_contract_hash']:
  if cfg['sensitivity_identity'].get(key)!=gate['sensitivity_identity'].get(key):raise ValueError('Conditional identity mismatch: '+key)
 if cfg['sensitivity_identity']['grouping_contract_hash']!=sha256(DEFAULT_GROUPING):raise ValueError('Grouping contract changed')
 contract=json.loads(Path(DEFAULT_GROUPING).read_text());directory=Path(DEFAULT_GROUPING).parent
 for name,key in [('weather_time_group_mapping.csv','mapping_hash'),('conditional_support_manifest.csv','conditional_support_manifest_hash')]:
  if sha256(directory/name)!=cfg['sensitivity_identity'][key]:raise ValueError('Mapping/support manifest changed')
 for row in pd.read_csv(directory/'conditional_support_manifest.csv').to_dict('records'):
  if sha256(row['path'])!=row['support_hash']:raise ValueError('Support changed')
 for path,h in cfg['implementation_hashes'].items():
  if sha256(path)!=h:raise ValueError('Implementation changed: '+path)
 if cfg['protocol_sha256']!=sha256(PROTOCOL):raise ValueError('Episode schedule changed')
 for spec in cfg['episodes']:validate_episode(spec)
 fixture,m=load_fixture();b=json.loads((O/'baseline_manifest.json').read_text())
 if b['status']!='FROZEN' or b['fixture_sha256']!=m['fixture_sha256'] or b['comparison_sha256']!=sha256(O/'weather_conditioned_baseline_comparison.csv') or b['reproducibility_sha256']!=sha256(O/'v2_full_day_baseline_reproducibility.csv'):raise ValueError('Conditional baseline mismatch')
 if m['fixture_version']!=VERSION:raise ValueError('Pooled fixture prohibited')
 for key in ['mapping_hash','conditional_support_manifest_hash','fallback_policy_version','grouping_contract_hash']:
  if m['sensitivity_identity'][key]!=cfg['sensitivity_identity'][key]:raise ValueError('Fixture sensitivity changed')
 return cfg,fixture,m

def run_resume(checkpoint_path):
 cfg,fixture,m=verify()
 cp=O/'checkpoints'
 checkpoint_path=Path(checkpoint_path)
 meta=json.loads((checkpoint_path/'continuation.json').read_text())
 validate_continuation(meta,sha256(O/'training_harness_config.json'),sha256(O/'march16_v2_full_day_fixture_manifest.json'),cfg['sensitivity_identity']['empirical_support_sha256'])
 p=provider();p.training_authorized=True;p.require_training_ready()
 d=PassengerSensitiveDQN.load(checkpoint_path,sensitivity_provider=p)
 if asdict(d.config)!=cfg['dqn_config'] or d.training_steps!=meta['update']:raise ValueError('Restored config/update mismatch')
 completed=meta['episode']
 dev=copy.copy(p);dev.training_authorized=False;dev.rng=np.random.default_rng(SEED)
 rows=committed_rows('episode_metrics.csv',completed);evals=committed_rows('development_evaluations.csv',completed);values=committed_rows('value_calibration.csv',completed);context={'episode':completed+1,'slot':0,'last_safe_checkpoint':str(checkpoint_path)};losses=[]
 baseline=pd.read_csv(O/'weather_conditioned_baseline_comparison.csv').set_index('policy').loc['HIGHEST_FEASIBLE']
 # Instrument optimizer calls without changing update equations or sampled batches.
 original=d.train_step
 def checked_step():
  old_target=d.target.get_weights();before=d.training_steps;result=original()
  if result is not None:
   if not np.isfinite(result['loss']) or d.training_steps!=before+1:raise ValueError('Invalid optimizer update')
   for old,new,online in zip(old_target,d.target.get_weights(),d.online.get_weights()):
    if not np.isfinite(new).all() or not np.allclose(new,(1-d.config.soft_target_tau)*old+d.config.soft_target_tau*online,rtol=1e-6,atol=1e-7):raise ValueError('Target update corruption')
   losses.append(result['loss'])
  return result
 d.train_step=checked_step
 def status(name,completed,failure):
  js(O/'training_status.json',dict(status=name,completed_episode=completed,**context,pid=os.getpid(),replay_size=len(d.replay),optimizer_updates=d.training_steps,exploration_epsilon=d.epsilon,failure=failure,training_started=True,resumed=True,resume_checkpoint=str(checkpoint_path),current_episode=context['episode'],current_slot=context['slot'],target_episode=25,slots_per_episode=16,minutes_per_slot=30,simulated_hours_per_episode=8,latest_checkpoint=context['last_safe_checkpoint'],last_update=datetime.now(timezone.utc).isoformat()))
  if name!='RUNNING' or (completed==0 and context['slot']==0):print(name,flush=True)
 def episode(ep):
  context.update(episode=ep,slot=0);spec=cfg['episodes'][ep-1];validate_episode(spec);p.rng=np.random.default_rng(spec['environment_seed']);losses.clear();started=time.monotonic();before=d.training_steps
  x=PassengerSensitiveExperiment(provider=p,learner=d,seed=spec['environment_seed'],start=spec['start'],routing_checkpoint=ROUTE,validation_only=False,passenger_sensitivity_version=VERSION)
  for j in range(16):
   context['slot']=j+1;u=d.training_steps;r=x.run_slot(terminal=j==15,train_dqn=True)
   if d.training_steps-u!=(8 if len(d.replay)>=d.config.minimum_replay_size else 0):raise ValueError('Optimizer cadence violation')
   if r['assigned']+r['accepted_unmatched']!=r['offers_generated'] or r['fleet_size']!=5000 or r['no_feasible_pricing_action']:raise ValueError('Slot accounting invariant')
   if any(not np.isfinite(v.energy_level) or v.energy_level<0 for v in x.fleet.vehicles):raise ValueError('Invalid EV state')
   for model in [d.online,d.target]:
    if any(not np.isfinite(w).all() for w in model.get_weights()):raise ValueError('Nonfinite network')
   status('RUNNING',ep-1,None)
  f=pd.DataFrame(x.request_audit)
  if not f.Request_ID.is_unique or len(x.linker.audit)!=len(f) or x.linker.pending is not None:raise ValueError('Replay linkage corruption')
  if (f.epsilon_c<=0).any() or not np.isfinite(f[['epsilon_c','reward','P_raw_c']]).all().all() or (f.P_offer_USD>f.P_accept_c).any():raise ValueError('Request contract invariant')
  revenue=float(f.reward.sum())
  if not np.isclose(revenue,f.loc[f.assignment_status,'P_offer_USD'].sum(),rtol=1e-12):raise ValueError('Assignment accounting')
  rows.append(dict(episode=ep,requests=len(f),assignments=int(f.assignment_status.sum()),revenue=revenue,unmatched=int((~f.assignment_status).sum()),replay_size=len(d.replay),optimizer_updates=d.training_steps-before,cumulative_optimizer_updates=d.training_steps,exploration_epsilon=d.epsilon,mean_loss=float(np.mean(losses)) if losses else None,median_loss=float(np.median(losses)) if losses else None,P95_loss=float(np.quantile(losses,.95)) if losses else None,charging_events=len(x.charging_events),runtime_seconds=time.monotonic()-started))
  pd.DataFrame(rows).to_csv(O/'episode_metrics.csv',index=False)
  print(f'EPISODE_{ep}_COMPLETED',flush=True)
 def checkpoint(ep):
  path=cp/f'episode_{ep:03d}';d.save(path)
  js(path/'continuation.json',dict(methodology_version=p.grouping['methodology_version'],sensitivity_version=VERSION,episode=ep,next_episode=ep+1,update=d.training_steps,config_sha256=sha256(O/'training_harness_config.json'),fixture_manifest_sha256=sha256(O/'march16_v2_full_day_fixture_manifest.json'),support_sha256=p.support_hash,**{k:cfg['sensitivity_identity'][k] for k in ['weather_time_grouping_version','mapping_hash','conditional_support_manifest_hash','fallback_policy_version','grouping_contract_hash']},continuation='Episode-boundary reset; next environment and sensitivity RNG use next persisted environment_seed. Learner/replay RNG and optimizer are in versioned checkpoint.'))
  context['last_safe_checkpoint']=str(path)
  pd.DataFrame([r for r in rows if r['episode'] in CHECKPOINTS]).to_csv(O/'checkpoint_metrics.csv',index=False)
  print(f'EPISODE_{ep}_CHECKPOINT_SAVED',flush=True)
 def development(ep):
  summary,f,q=guarded_evaluation(d,lambda:evaluate(dev,fixture,m,'GREEDY_DQN',d))
  g=mc_returns(f.reward.to_numpy());q=np.asarray(q)
  if len(g)!=len(q) or not np.isfinite(q).all():raise ValueError('Calibration length/finite failure')
  corr=float(np.corrcoef(q,g)[0,1]) if np.std(q)>0 and np.std(g)>0 else None
  rank=float(spearmanr(q,g).statistic) if corr is not None else None
  states=np.stack(f.state_13d);masks=f[['mask_'+v for v in ['085','090','095','100','105','110','115']]].to_numpy(bool)
  tq=np.concatenate([d.target(states[i:i+4096],training=False).numpy() for i in range(0,len(states),4096)])
  next_q=np.vstack([tq[1:],np.zeros((1,7))]);next_masks=np.vstack([masks[1:],np.zeros((1,7),bool)]);dones=np.zeros(len(f),bool);dones[-1]=True
  targets=masked_targets(f.reward.to_numpy(),dones,next_q,next_masks,np.zeros(len(f)),.99)
  values.append(dict(mean_absolute_TD_error=float(np.abs(targets-q).mean()),episode=ep,MC_mean=float(g.mean()),MC_median=float(np.median(g)),MC_SD=float(g.std()),Q_mean=float(q.mean()),Q_median=float(np.median(q)),Q_MC_MAE=float(np.abs(q-g).mean()),pearson=corr,spearman=rank))
  summary.update(episode=ep,revenue_difference=float(summary['revenue']-baseline.revenue),assignment_difference=int(summary['assignments']-baseline.assignments));evals.append(summary)
  pd.DataFrame(evals).to_csv(O/'development_evaluations.csv',index=False);pd.DataFrame(values).to_csv(O/'value_calibration.csv',index=False)
  f[['Request_ID','selected_action_index','feasible_action_count','reward']].to_csv(O/f'development_actions_ep{ep:02d}.csv',index=False)
 schedule(episode,checkpoint,development,status,start_episode=completed+1)

def committed_rows(name,completed):
 path=O/name
 if not path.exists():return []
 return pd.read_csv(path).query('episode <= @completed').to_dict('records')
