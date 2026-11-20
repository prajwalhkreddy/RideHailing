"""Four-slot joint OD pricing/routing pilot; inherited eight-update cadence."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
import sys,json,hashlib,time,resource,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,tensorflow as tf
from src.routing.online_provenance import OnlineHierarchy,validate,weight_hash
from src.routing.learning import LocalRoutingLearner
from src.simulation.information_cutoff import validate_manifest
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint,boundary
from src.simulation.v3_checkpoint_codec import encode
from src.simulation.v3_checkpoint import rng_bundle
from src.demand.causal_timing import CHANNELS,timing
from src.demand.persistence_weather import contract,fingerprint,select_weather
from src.simulation.utc_od_inputs import BASELINE
import scripts.validate_od_fallback_acceptance as old
OUT=Path(os.environ.get('ONLINE_ROUTING_EXPERIMENT_OUT','results_v2/pricing_dqn/2026-11-18_joint_learning_pilot'))
PROV=Path(os.environ.get('ONLINE_ROUTING_PROVENANCE','results_v2/federated_learning/2026-11-17_online_routing_retry_001'))
def write(name,data):
 (OUT/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def hash_value(x):
 h=hashlib.sha256()
 for chunk in json.JSONEncoder(sort_keys=True,separators=(',',':')).iterencode(encode(x)):h.update(chunk.encode())
 return h.hexdigest()
def inputs(m):
 a=m['artifacts'];table=pd.read_csv(a['forecast']['path']);targets=pd.date_range('2026-03-12T04:00Z',periods=5,freq='30min')
 w=pd.read_parquet(old.BASE/'weather_jan_mar_2026.parquet',filters=[('Datetime','>=',pd.Timestamp('2026-03-11')),('Datetime','<',pd.Timestamp('2026-03-12 07:00'))])
 weather=contract(120);selected=select_weather(w,targets,weather);frames={};realized={}
 for t,row in zip(targets,selected.to_dict('records')):
  local=t.tz_convert('America/New_York');f=table[table.period==local.hour*2+local.minute//30][['Grid_ID','predicted_demand']].copy()
  for key in list(timing(t))+['observation_time','assumed_available_at']:f[key]=row[key]
  frames[str(t)]=f
  code=pd.read_parquet(old.BASE/'demand_master_jan_mar_2026.parquet',columns=['WeatherCode'],filters=[('TimeSlot','==',local.tz_localize(None))])
  assert len(code)==142 and code.WeatherCode.nunique()==1
  realized[str(t)]=int(code.WeatherCode.iloc[0])
 return dict(forecast_protocol=BASELINE,baseline_provenance=dict(method='January grid/local-half-hour arithmetic mean',training_start='2026-01-01',training_end_exclusive='2026-02-01',available_at='2026-02-01T05:00Z',artifact_path=a['forecast']['path'],artifact_sha256=a['forecast']['sha256']),weather_contract=weather,checkpoint_metadata=dict(version=BASELINE,weather_contract_sha256=fingerprint(weather)),channels=list(CHANNELS),grid_ids=list(range(142)),forecasts=frames,realized_weather=realized,popularity={int(k):v for k,v in json.loads(Path(a['popularity']['path']).read_text()).items()},popularity_available_at=pd.Timestamp('2026-02-01T05:00Z'))

def initialize_experiment_rng(seed):
 # Research-run entry only. Keras seeding does not initialize this separate generator.
 tf.keras.utils.set_random_seed(seed)
 tf.random.set_global_generator(tf.random.Generator.from_seed(seed,alg='philox'))

def rng_domains():return {k:hash_value(v) for k,v in rng_bundle().items()}

def digests(r):
 h=r.engine.driver_hierarchy;s=h.snapshot()
 # Hash each client separately: avoid a second giant encoded snapshot in memory.
 clients={str(d):hash_value(v) for d,v in sorted(s.pop('locals').items())}
 return dict(runtime=old.digest_state(r),hierarchy=hash_value(s),local_parameters_and_optimizers=hash_value(clients),charging=hash_value(r.engine.charging),global_rng=hash_value(rng_bundle()),global_rng_domains=rng_domains(),pricing_weights=weight_hash(r.learner.online.get_weights()),pricing_optimizer=hash_value([v.numpy() for v in r.learner.online.optimizer.variables]))

LEARNING=[]
original_train=LocalRoutingLearner.train_for_slot

def observed_train(self,slot):
 before=self.gradient_updates;count=self.local_sample_count;start=time.perf_counter()
 original_apply=self.optimizer.apply_gradients
 def checked_apply(pairs,*args,**kw):
  pairs=list(pairs)
  if any(g is None or not bool(tf.reduce_all(tf.math.is_finite(g))) for g,v in pairs):raise ValueError('Nonfinite local gradient')
  return original_apply(pairs,*args,**kw)
 self.optimizer.apply_gradients=checked_apply
 try:loss=original_train(self,slot)
 finally:self.optimizer.apply_gradients=original_apply
 if loss is None or not np.isfinite(loss) or any(not np.isfinite(x).all() for x in self.policy_model.get_weights()):raise ValueError('Invalid genuine local update')
 LEARNING.append((float(loss),self.gradient_updates-before,self.local_sample_count-count,time.perf_counter()-start))
 if len(LEARNING)%1000==0:print('local updates',len(LEARNING),'slot',slot+1,flush=True)
 return loss

def run(mode):
 OUT.mkdir(parents=True,exist_ok=True)
 stages={'process_initial':rng_domains()}
 if mode!='resume':initialize_experiment_rng(42)
 stages['run_initialized']=rng_domains();write(mode+'_rng_stages.json',stages)
 c=json.loads((PROV/'routing_initialization.json').read_text());m=json.loads((PROV/'information_contract.json').read_text());validate(c);validate_manifest(m)
 LocalRoutingLearner.train_for_slot=observed_train
 support=json.loads(Path(m['artifacts']['od_support']['path']).read_text());bundle=inputs(m)
 if mode=='resume':
  meta=json.loads((OUT/'recovery_checkpoint/manifest.json').read_text())
  r=load_od_checkpoint(OUT/'recovery_checkpoint',master_math=True,utc_mode=True,fallback_contract=old.POLICY,information_contract=m,hierarchy_contract=meta['hierarchy'],ev_composition=meta['ev_composition'])
 else:
  hierarchy=OnlineHierarchy(c,updates_enabled=mode!='control');stages['routing_model_initialized']=rng_domains()
  import src.simulation.final_production as production
  fleet_initializer=production.initialize_ev_fleet
  def observed_fleet(*args,**kwargs):
   fleet=fleet_initializer(*args,**kwargs);stages['fleet_initialized']=rng_domains();return fleet
  production.initialize_ev_fleet=observed_fleet
  r=ODPricingRuntime(start=c['experiment_start'],routing_checkpoint=m['artifacts']['routing']['path'],research_routing=True,information_contract=m,seed=42,utc_inputs=bundle,od_support=support,sensitivity_contract=m['artifacts']['sensitivity']['path'],fallback_contract=old.POLICY,driver_hierarchy=hierarchy,ev_share=.1)
  production.initialize_ev_fleet=fleet_initializer
 stages['before_slots']=rng_domains();write(mode+'_rng_stages.json',stages)
 e=r.engine;h=e.driver_hierarchy
 assert len(e.fleet.vehicles)==5000 and sum(v.is_ev for v in e.fleet.vehicles)==500
 if mode=='primary':
  write('configuration.json',dict(configuration=dict(rng_contract='EXPLICIT_RESEARCH_GLOBAL_RNG_INIT_V1',tensorflow_generator='philox_seed42_once_at_fresh_run_entry',start=c['experiment_start'],end=c['experience_end_exclusive'],slots=4,mini_slot_seconds=120,fleet=5000,evs=500,seed=42,pricing_updates=True,pricing_updates_per_warm_slot=8,episode_target_slots=16,pilot_truncation_slots=4,routing_updates=True,control='same fresh weights, updates disabled',pricing_config=vars(r.learner.config)),routing_initialization=c,information_contract=m,git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),git_status=subprocess.check_output(['git','status','--short','--untracked-files=no'],text=True),script_sha256=old.sha(__file__),initial_state=digests(r),forecast_weather_assumption='120-minute persistence; realized request weather remains retrospective context',model_selection_caveat=c['development_tuning']))
  write('preflight.json',dict(status='PASSED',fresh_hash=weight_hash(h._global.get_weights()),fleet=5000,EV=500,non_EV=4500,protected_dates_accessed=False,pricing_optimizer_updates=0))
 checks=[];metrics=[];probs=[]
 expected=None if mode in ('primary','control') else json.loads((OUT/'primary_checks.json').read_text())
 if mode=='resume':assert digests(r)==expected[1], 'Immediate restored state mismatch'
 pricing_initial=weight_hash(r.learner.online.get_weights())
 for i in range(r.slots,4):
  LEARNING.clear();start=time.perf_counter();before=h._global.get_weights();pre_probs=np.stack([e.current_states.routing.values[g] for g in range(142)])
  rows=r.run_slot();elapsed=time.perf_counter()-start
  boundary(r)
  pricing_before=r.learner.training_steps
  epsilon_before=r.learner.epsilon
  losses=[r.learner.train_step() for _ in range(8)] if len(r.learner.replay)>=r.learner.config.minimum_replay_size else []
  assert all(x is not None and np.isfinite(x) for x in losses)
  assert r.learner.training_steps-pricing_before==len(losses)
  assert all(np.isfinite(w).all() for net in (r.learner.online,r.learner.target) for w in net.get_weights())
  assert all(not row[4] for row in r.learner.replay), 'Four-slot pilot is truncation of 16-slot design'
  assert np.isclose(sum(x[2] for x in list(r.learner.replay)[-len(r.pairs):]),r.environment_reward)
  after=h._global.get_weights();post_probs=np.stack([e.current_states.routing.values[g] for g in range(142)])
  assert np.isfinite(post_probs).all() and (post_probs>=0).all() and np.allclose(post_probs.sum(axis=1),1)
  for g in range(142):assert np.all(post_probs[g][~e.current_states.action_masks[g]]==0)
  assert all(x['accepted']==(x['P_offer']<=x['P_max']) for x in rows)
  assert np.isclose(sum(x['reward_contribution'] for x in rows),r.system_revenue,rtol=1e-12,atol=1e-9)
  assert sum(v.is_ev for v in e.fleet.vehicles)==500
  assert all(np.isfinite(v.energy_level) and 0<=v.energy_level<=e.energy.battery_capacity_kwh+1e-8 for v in e.fleet.vehicles)
  assert all(v.energy_level==0 and v.vehicle_id not in e.charging.vehicle_station for v in e.fleet.vehicles if not v.is_ev)
  assert int(r.learner.online.optimizer.iterations.numpy())==r.learner.training_steps and weight_hash(r.learner.online.get_weights())!=pricing_initial
  current=[o for memory in h._memory.values() for o in memory if o.slot_id==i]
  local_steps=sum(x[1] for x in LEARNING);samples=sum(x[2] for x in LEARNING)
  norm=float(np.sqrt(sum(np.sum((a.astype(float)-b)**2) for a,b in zip(after,before))))
  if mode!='control':
   assert local_steps>0 and norm>0
   participants=[l for l in h._locals.values() if i in l._trained_slots]
   average=[np.mean(np.stack([l.policy_model.get_weights()[k] for l in participants]),axis=0,dtype=np.float64) for k in range(len(after))]
   assert all(np.allclose(a,b,rtol=1e-6,atol=1e-7) for a,b in zip(after,average)), 'Equal-client aggregation mismatch'
  else:assert local_steps==0 and norm==0
  item=dict(pricing_updates=r.learner.training_steps,pricing_losses=losses,epsilon_before=epsilon_before,epsilon_after=r.learner.epsilon,slot=i+1,start=str(e.timestamp-pd.Timedelta(minutes=30)),end=str(e.timestamp),requests=len(rows),accepted=sum(x['accepted'] for x in rows),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in rows),fallback_requests=sum(x['is_fallback'] for x in rows),revenue=r.system_revenue,participants=len(LEARNING),new_experiences=len(current),trained_sample_presentations=samples,optimizer_updates=local_steps,mean_loss=float(np.mean([x[0] for x in LEARNING])) if LEARNING else None,max_loss=max([x[0] for x in LEARNING],default=None),global_update_l2=norm,global_sha256=weight_hash(after),global_version=h.global_version,federation_round=h.round,available_at=str(h.available_at),mean_absolute_probability_change=float(np.abs(post_probs-pre_probs).mean()),routing_action_counts=np.bincount([o.chosen_action_index for o in current],minlength=9).tolist(),charging_events=len(e.charging_events),repositioning_vehicles=sum(v.current_action=='repositioning' for v in e.fleet.vehicles),ev_energy_sum=sum(v.energy_level for v in e.fleet.vehicles if v.is_ev),replay_size=len(r.learner.replay),seconds=elapsed,local_optimizer_seconds=sum(x[3] for x in LEARNING),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  metrics.append(item);probs.append(post_probs);state=digests(r);checks.append(state)
  stages['after_slot_'+str(i+1)]=rng_domains();write(mode+'_rng_stages.json',stages)
  if expected is not None:assert state==expected[i], 'Determinism mismatch at slot '+str(i+1)+': '+str([k for k in state if state[k]!=expected[i][k]])
  write(mode+'_metrics.json',metrics);write(mode+'_checks.json',checks)
  pd.DataFrame(metrics).to_csv(OUT/(mode+'_slot_metrics.csv'),index=False)
  np.savez_compressed(OUT/(mode+'_probabilities.npz'),values=np.stack(probs))
  print(mode,'slot',i+1,'complete',len(rows),'requests',local_steps,'updates',round(elapsed,2),'seconds',flush=True)
  if mode=='primary' and i==1:save_od_checkpoint(r,OUT/'recovery_checkpoint');print('slot2 checkpoint saved',flush=True)
 if mode=='primary':save_od_checkpoint(r,OUT/'final_checkpoint')
 assert len(r.audit)==4137 and sum(x['is_fallback'] for x in r.audit)==2
 pd.DataFrame(r.demand_audit).to_csv(OUT/(mode+'_request_reconciliation.csv'),index=False)
 write(mode+'_complete.json',dict(status='PASSED',slots=4,requests=len(r.audit),total_revenue=sum(x['total_system_revenue'] for x in r.fallback_audit),accepted=sum(x['accepted'] for x in r.audit),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in r.audit),pricing_updates=r.learner.training_steps,final_state=checks[-1]))
if __name__=='__main__':
 mode=sys.argv[1]
 try:run(mode)
 except Exception as e:
  OUT.mkdir(parents=True,exist_ok=True);write(mode+'_blocker.json',dict(type=type(e).__name__,message=str(e)));raise
