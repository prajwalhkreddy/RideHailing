"""Approved two-episode orchestration pilot; refuses the remaining 33 episodes."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
import sys,json,time,hashlib,resource,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,tensorflow as tf
from scripts import run_full_od_development as previous
from scripts.run_full_od_development import old,CHANNELS,timing,contract,select_weather,BASELINE,fingerprint
from src.simulation.multi_episode_od import *
from src.simulation.multi_episode_rng import advance_with_environment_rng as advance_episode
from src.routing.online_provenance import OnlineHierarchy,validate,MULTI_VERSION,SOURCES,weight_hash
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import boundary,load_od_checkpoint
from src.simulation.information_cutoff import validate_manifest
from src.routing.learning import LocalRoutingLearner
OUT=Path('results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration')
MODELS=Path('models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42')
def write(name,x):
 OUT.mkdir(parents=True,exist_ok=True);(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inputs(m,start):
 a=m['artifacts'];table=pd.read_csv(a['forecast']['path']);targets=pd.date_range(pd.Timestamp(start),periods=17,freq='30min')
 w=pd.read_parquet(old.BASE/'weather_jan_mar_2026.parquet',filters=[('Datetime','>=',pd.Timestamp(start).tz_convert('UTC').tz_localize(None)-pd.Timedelta(days=1)),('Datetime','<',pd.Timestamp(start).tz_convert('UTC').tz_localize(None)+pd.Timedelta(hours=9))])
 weather=contract(120);selected=select_weather(w,targets,weather);frames={};realized={}
 for t,row in zip(targets,selected.to_dict('records')):
  local=t.tz_convert('America/New_York');f=table[table.period==local.hour*2+local.minute//30][['Grid_ID','predicted_demand']].copy()
  for key in list(timing(t))+['observation_time','assumed_available_at']:f[key]=row[key]
  frames[str(t)]=f
  code=pd.read_parquet(old.BASE/'demand_master_jan_mar_2026.parquet',columns=['WeatherCode'],filters=[('TimeSlot','==',local.tz_localize(None))])
  assert len(code)==142 and code.WeatherCode.nunique()==1
  realized[str(t)]=int(code.WeatherCode.iloc[0])
 return dict(forecast_protocol=BASELINE,baseline_provenance=dict(method='January grid/local-half-hour arithmetic mean',training_start='2026-01-01',training_end_exclusive='2026-02-01',available_at='2026-02-01T05:00Z',artifact_path=a['forecast']['path'],artifact_sha256=a['forecast']['sha256']),weather_contract=weather,checkpoint_metadata=dict(version=BASELINE,weather_contract_sha256=fingerprint(weather)),channels=list(CHANNELS),grid_ids=list(range(142)),forecasts=frames,realized_weather=realized,popularity={int(k):v for k,v in json.loads(Path(a['popularity']['path']).read_text()).items()},popularity_available_at=pd.Timestamp('2026-02-01T05:00Z'))

def prepare():
 base=Path('results_v2/pricing_dqn/2026-11-20_full_episode_development/provenance')
 c=json.loads((base/'routing_initialization.json').read_text());c.update(version=MULTI_VERSION,experiment_start=str(START),experience_end_exclusive=str(END),activation='Approved chronological 35-episode protocol; execution cap two episodes')
 c['source_sha256']={p:sha(p) for p in SOURCES}
 write('routing_initialization.json',c)
 m=json.loads((base/'information_contract.json').read_text());m['version']='CHRONOLOGICAL_INFORMATION_CUTOFF_V2'
 m['artifacts']['routing'].update(path=str((OUT/'routing_initialization.json').resolve()),sha256=sha(OUT/'routing_initialization.json'),methodology_version=MULTI_VERSION)
 m['permitted_cutoffs'].update(routing=str(START),forecast=str(START))
 write('information_contract.json',m);validate(c);validate_manifest(m)
 config=json.loads(Path('results_v2/pricing_dqn/2026-11-20_training_protocol_decision/proposed_configuration.json').read_text())
 config.update(status='APPROVED_IMPLEMENTATION_PILOT',launch_authorized=False,pilot_episode_cap=2)
 config['source_sha256']={p:sha(p) for p in SOURCES+['src/rl/od_pricing_dqn.py','src/simulation/multi_episode_od.py','src/simulation/information_cutoff.py','scripts/run_multi_episode_od_pilot.py','src/simulation/multi_episode_rng.py','src/simulation/od_development_evaluation.py']}
 write('frozen_configuration.json',config)
 write('temporal_boundaries.json',[dict(episode=i+1,start=str(episode_bounds(i)[0]),end=str(episode_bounds(i)[1])) for i in range(35)])
 return c,m

def factory(m):
 support=json.loads(Path(m['artifacts']['od_support']['path']).read_text())
 def create(start,h,evaluation_mode=False):
  return ODPricingRuntime(start=start,routing_checkpoint=m['artifacts']['routing']['path'],research_routing=True,information_contract=m,seed=42,utc_inputs=inputs(m,start),od_support=support,sensitivity_contract=m['artifacts']['sensitivity']['path'],fallback_contract=old.POLICY,driver_hierarchy=h,ev_share=.1,multi_episode=True,evaluation_mode=evaluation_mode)
 return create

def load(path,m):
 meta=json.loads((Path(path)/'manifest.json').read_text())
 return load_od_checkpoint(path,master_math=True,utc_mode=True,fallback_contract=old.POLICY,information_contract=m,hierarchy_contract=meta['hierarchy'],ev_composition=meta['ev_composition'],multi_episode=True)

def step(r):
 previous.LEARNING.clear();t=time.perf_counter();eps=r.learner.epsilon
 rows=r.run_slot();boundary(r)
 grads=[];apply=r.learner.online.optimizer.apply_gradients
 def checked(pairs,*args,**kwargs):
  pairs=list(pairs);norm=float(tf.linalg.global_norm([g for g,v in pairs]));assert np.isfinite(norm);grads.append(norm);return apply(pairs,*args,**kwargs)
 r.learner.online.optimizer.apply_gradients=checked
 try:losses=[r.learner.train_step() for _ in range(8)] if len(r.learner.replay)>=1000 else []
 finally:r.learner.online.optimizer.apply_gradients=apply
 assert all(np.isfinite(losses)) and len(grads)==len(losses)
 assert all(x[4]==(r.slots==16) for x in list(r.learner.replay)[-len(r.pairs):])
 assert np.isclose(sum(x['reward_contribution'] for x in rows),r.system_revenue)
 assert len(r.engine.fleet.vehicles)==5000 and sum(v.is_ev for v in r.engine.fleet.vehicles)==500
 assert all(np.isfinite(v.energy_level) and 0<=v.energy_level<=r.engine.energy.battery_capacity_kwh for v in r.engine.fleet.vehicles)
 assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<16*1024**3
 d=dict(episode=getattr(r,'episode_offset',0)//16+1,slot=r.slots,requests=len(rows),accepted=sum(x['accepted'] for x in rows),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in rows),reward=r.environment_reward,revenue=r.system_revenue,fallback_revenue=r.system_revenue-r.environment_reward,epsilon_before=eps,epsilon_after=r.learner.epsilon,updates=r.learner.training_steps,losses=losses,gradient_norms=grads,routing_updates=sum(x[1] for x in previous.LEARNING),routing_samples=sum(x[2] for x in previous.LEARNING),federation_round=r.engine.driver_hierarchy.round,charging_events=len(r.engine.charging_events),seconds=time.perf_counter()-t,replay=replay_diagnostics(r),rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 print(json.dumps({k:d[k] for k in ['episode','slot','requests','updates','epsilon_after','seconds']}),flush=True)
 return d

def run(mode):
 LocalRoutingLearner.train_for_slot=previous.observed_train
 if mode=='prepare':prepare();return
 c=json.loads((OUT/'routing_initialization.json').read_text());m=json.loads((OUT/'information_contract.json').read_text());validate(c);validate_manifest(m)
 for p,h in json.loads((OUT/'frozen_configuration.json').read_text())['source_sha256'].items():
  if sha(p)!=h:raise ValueError('Changed pilot source: '+p)
 make=factory(m)
 if mode=='recover':
  r=load(MODELS/'milestone',m)
  assert previous.digests(r)==json.loads((OUT/'episode1_digest.json').read_text())
  r=advance_episode(r,make)
  assert previous.digests(r)==json.loads((OUT/'episode2_initial_digest.json').read_text())
  d=step(r)
  assert previous.digests(r)==json.loads((OUT/'episode2_slot1_digest.json').read_text())
  expected=json.loads((OUT/'slot_metrics.json').read_text())[16]
  assert d['losses']==expected['losses'] and d['gradient_norms']==expected['gradient_norms']
  write('recovery_validation.json',dict(status='PASS',cross_episode_reset_exact=True,episode2_first_slot_exact=True,losses_gradients_exact=True,additional_slots=1));return
 if mode not in {'primary','resume'}:raise ValueError('Unknown mode')
 if mode=='primary' and (OUT/'slot_metrics.json').exists():raise FileExistsError('Existing pilot evidence; use recovery, never silently overwrite')
 if mode=='resume':
  r=load(MODELS/'latest',m)
  finished=getattr(r,'episode_offset',0)+r.slots
  previous_metrics=(OUT/'slot_metrics.json').read_text()
  (OUT/('interrupted_slot_metrics_'+str(time.time_ns())+'.json')).write_text(previous_metrics)
  metrics=json.loads(previous_metrics)[:finished]
  resets=json.loads((OUT/'reset_checks.json').read_text()) if (OUT/'reset_checks.json').exists() else []
 else:
  previous.initialize_experiment_rng(42);h=OnlineHierarchy(c,updates_enabled=True);r=make(START,h)
  metrics=[];resets=[]
 began=time.perf_counter();initial_ep=getattr(r,'episode_offset',0)//16
 for ep in range(initial_ep,2):
  if ep>getattr(r,'episode_offset',0)//16:
   r=advance_episode(r,make);resets.append(r.reset_evidence);write('reset_checks.json',resets);write('episode2_initial_digest.json',previous.digests(r))
  for i in range(r.slots,16):
   d=step(r);metrics.append(d);write('slot_metrics.json',metrics)
   if ep==1 and i==0:write('episode2_slot1_digest.json',previous.digests(r))
   if r.slots%4==0:retain_checkpoint(r,MODELS)
  write(f'episode{ep+1}_request_reconciliation.json',dict(demand=r.demand_audit,source_requests=len(r.audit),rejected=sum(not x['accepted'] for x in r.audit),accepted=sum(x['accepted'] for x in r.audit),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in r.audit)))
  if ep==0:
   if not (MODELS/'milestone').exists():retain_checkpoint(r,MODELS,'milestone')
   write('episode1_digest.json',previous.digests(r))
 write('pilot_validation.json',dict(status='COMPLETED_PENDING_RECOVERY',episodes=2,slots=32,updates=r.learner.training_steps,epsilon=r.learner.epsilon,routing_updates=sum(x['routing_updates'] for x in metrics),federation_round=r.engine.driver_hierarchy.round,seconds=time.perf_counter()-began,peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint_bytes=sum(f.stat().st_size for f in MODELS.rglob('*') if f.is_file()),protected_access=False,remaining_episodes_started=False))
if __name__=='__main__':
 try:run(sys.argv[1])
 except Exception as e:
  import traceback
  write('blocker_'+sys.argv[1]+'.json',dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc()));raise
