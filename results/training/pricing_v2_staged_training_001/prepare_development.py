"""Frozen full-day development fixture and baseline evaluation. Never trains."""
from pathlib import Path
from dataclasses import asdict
import copy, hashlib, json, pickle, time, traceback, subprocess
import numpy as np
import pandas as pd
from src.pricing.passenger_sensitive_v2 import V2EmpiricalSensitivityProvider, sha256
from src.pricing.dqn_contract import artifact_snapshots
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
from src.rl.pricing_dqn import DQNConfig, PricingAction, ACTIONS, validate_state
from src.simulation.passenger_sensitive_v1 import PassengerSensitiveExperiment

O=Path(__file__).resolve().parent
ROUTE=Path('models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras')
SEED=424242

def js(path,obj):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n');tmp.replace(path)
def digest(obj):
 return hashlib.sha256(json.dumps(obj,sort_keys=True,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)).encode()).hexdigest()
def fleet_state(env):return [asdict(v) for v in env.fleet.vehicles]
def provider():
 cfg=json.loads(Path('config/passenger_sensitivity_v2_validation.json').read_text())
 return V2EmpiricalSensitivityProvider(rng=np.random.default_rng(SEED),expected_contract_sha256=cfg['expected_contract_sha256'])
class EvaluationPolicy(PassengerSensitiveDQN):
 """Policy-only adapter: no networks/optimizer/replay updates for baselines."""
 def __init__(self,policy,learner=None):
  self.policy=policy;self.learner=learner;self.config=DQNConfig();self.training_steps=0;self.replay=[];self.q=[]
 def select_action(self,state,mask,*,explore=False):
  validate_state(state)
  if explore:raise ValueError('Evaluation exploration prohibited')
  ix=np.flatnonzero(mask)
  if not len(ix):raise ValueError('Empty mask')
  if self.learner is None:
   a=int(ix[-1] if self.policy=='HIGHEST_FEASIBLE' else ix[0] if self.policy=='LOWEST_FEASIBLE' else ix[np.argmin(abs(np.asarray(ACTIONS)[ix]-1))])
  else:
   q=self.learner.online(np.asarray(state)[None,:],training=False).numpy()[0]
   if not np.isfinite(q).all():raise ValueError('Nonfinite evaluation Q')
   a=int(ix[np.argmax(q[ix])]);self.q.append(float(q[a]))
  return PricingAction(a,ACTIONS[a],0.,False)
 def store(self,*args):pass
 def train_step(self):raise RuntimeError('Evaluation cannot optimize')
 def complete_slot(self,*args):raise RuntimeError('Evaluation cannot optimize')

def environment(p,policy):
 return PassengerSensitiveExperiment(provider=p,learner=policy,seed=SEED,start='2026-03-16',routing_checkpoint=ROUTE,validation_only=True,passenger_sensitivity_version='v2')
def dependencies():
 paths=['config/config.yaml','config/passenger_sensitivity_v2_validation.json','data/processed/grid_metadata.json','data/processed/grid_lookup.parquet','data/processed/spatial_3km_jan_mar_2026/neighbour_map.parquet','data/processed/spatial_3km_jan_mar_2026/charging_stations.parquet','data/processed/driver_preferences_seed42.parquet',str(ROUTE)]
 return {p:sha256(p) for p in paths}
def validate_requests(slots):
 ids=[]
 if len(slots)!=48:raise ValueError('Expected48 slots')
 for j,rs in enumerate(slots):
  t=pd.Timestamp('2026-03-16')+pd.Timedelta(minutes=30*j)
  for r in rs:
   r.validate(range(142),15);ids.append(r.request_id)
   if not np.isfinite(r.trip_distance_km) or r.trip_distance_km<0:raise ValueError('Invalid distance')
   at=t+pd.Timedelta(seconds=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else 120*r.request_time)
   if not pd.Timestamp('2026-03-16')<=at<pd.Timestamp('2026-03-17'):raise ValueError('Development date violation')
 if len(set(ids))!=len(ids) or sorted(ids)!=list(range(len(ids))):raise ValueError('Corrupt request IDs')
 return len(ids)
def create_fixture(p):
 manifest=O/'march16_v2_full_day_fixture_manifest.json';binary=O/'march16_fixture.pkl'
 if manifest.exists():return load_fixture()
 if binary.exists():raise ValueError('Uncommitted fixture; inspect before retry')
 env=environment(p,EvaluationPolicy('HIGHEST_FEASIBLE'));initial=fleet_state(env);initial_hash=digest(initial)
 assert len(initial)==5000 and not env.passengers and not env.missions
 slots=[];snapshots=[];suppressed=[]
 for j,t in enumerate(pd.date_range('2026-03-16',periods=48,freq='30min')):
  # Request generator depends on timestamp, request counter and independent RNG, not simulated fleet.
  env.timestamp=t
  f,pop=artifact_snapshots(t)
  weather=pd.read_parquet(env.base/'demand_master_jan_mar_2026.parquet',columns=['GridID','WeatherCode'],filters=[('TimeSlot','==',t)]).sort_values('GridID')
  snapshots.append(dict(timestamp=str(t),forecast=digest(f.values),popularity=digest(pop.values),weather=digest(weather.to_dict('records'))))
  rs=env.requests_for_slot();slots.append(sorted(rs,key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else 120*r.request_time,r.request_id)))
  suppressed.append(sum(env.unsupported_demand.values()))
 n=validate_requests(slots);p.rng=np.random.default_rng(SEED);epsilon=p.sample_many(n)
 assert np.isfinite(epsilon).all() and (epsilon>0).all()
 # Generate again from independent request RNG reset; exact request dataclass identity.
 first=digest([[asdict(x) for x in a] for a in slots]);env.request_id=0;env.request_rng=np.random.default_rng(np.random.SeedSequence(SEED).spawn(1)[0])
 rebuilt=[]
 for j,t in enumerate(pd.date_range('2026-03-16',periods=48,freq='30min')):
  env.timestamp=t;rebuilt.append(sorted(env.requests_for_slot(),key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else 120*r.request_time,r.request_id)))
 assert first==digest([[asdict(x) for x in a] for a in rebuilt]);assert digest(fleet_state(env))==initial_hash
 payload={'slots':slots,'epsilon':epsilon,'initial_fleet':initial};binary.write_bytes(pickle.dumps(payload,protocol=5))
 m=dict(fixture_version='V2_FULL_DAY_MARCH16_001',start_inclusive='2026-03-16',end_exclusive='2026-03-17',request_count=n,request_hash=first,fixture_sha256=sha256(binary),epsilon_sequence_sha256=hashlib.sha256(epsilon.tobytes()).hexdigest(),initial_fleet_hash=initial_hash,seed=SEED,support_hash=p.support_hash,contract_hash=p.contract_hash,dependencies=dependencies(),snapshots=snapshots,unsupported_forecast_counts=suppressed,implementation_hash=sha256(__file__),git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_note='Canonical generator samples intact January empirical trips; March16 simulated arrival times. No claim of observed March16 taxi-trip replay.',request_rng_end=env.request_rng.bit_generator.state,sensitivity_rng_end=p.rng.bit_generator.state)
 js(manifest,m);js(O/'march16_v2_fixture_verification.json',dict(status='PASS',reconstruction_exact=True,slots=48,N=n,initial_fleet=5000,protected_access=False,training_started=False))
 return payload,m

def load_fixture():
 m=json.loads((O/'march16_v2_full_day_fixture_manifest.json').read_text());p=O/'march16_fixture.pkl'
 if sha256(p)!=m['fixture_sha256'] or dependencies()!=m['dependencies']:raise ValueError('Fixture/dependency hash mismatch')
 f=pickle.loads(p.read_bytes())
 if validate_requests(f['slots'])!=m['request_count']:raise ValueError('Fixture count mismatch')
 return f,m

def evaluate(p,fixture,m,policy,learner=None):
 if p.support_hash!=m['support_hash'] or p.contract_hash!=m['contract_hash']:raise ValueError('Sensitivity identity mismatch')
 start=time.monotonic();p.rng=np.random.default_rng(SEED);view=EvaluationPolicy(policy,learner);env=environment(p,view)
 if digest(fleet_state(env))!=m['initial_fleet_hash']:raise ValueError('Fleet reset mismatch')
 events=[];entered=set();left=set();previous=set();soc_min=1e99;soc_max=0
 for j,rs in enumerate(fixture['slots']):
  env.run_slot(copy.deepcopy(rs),terminal=j==47,train_dqn=False,explore_pricing=False)
  soc=np.asarray([v.energy_level for v in env.fleet.vehicles]);assert np.isfinite(soc).all() and (soc>=0).all()
  soc_min=min(soc_min,float(soc.min()));soc_max=max(soc_max,float(soc.max()))
  current={v.vehicle_id for v in env.fleet.vehicles if v.current_action in ('charging','charging_queue')};entered.update(current-previous);left.update(previous-current);previous=current
  assert view.training_steps==0 and len(view.replay)==0 and len(env.fleet.vehicles)==5000
  js(O/'baseline_progress.json',dict(policy=policy,slots_completed=j+1,training=False))
 f=pd.DataFrame(env.request_audit);np.testing.assert_array_equal(f.epsilon_c.to_numpy(),fixture['epsilon'])
 assert f.Request_ID.is_unique and len(f)==m['request_count'] and np.isfinite(f[['P_raw_c','P_accept_c','reward']]).all().all()
 assert (f.P_offer_USD<=f.P_accept_c).all() and f.feasible_action_count.ge(1).all()
 reward=float(f.reward.sum());assert np.isclose(reward,f.loc[f.assignment_status,'P_offer_USD'].sum(),rtol=1e-12)
 counts=np.bincount(f.selected_action_index.astype(int),minlength=7).tolist()
 summary=dict(policy=policy,requests=len(f),actionable_requests=len(f),offers=len(f),accepted=len(f),rejected=0,assignments=int(f.assignment_status.sum()),assignment_rate=float(f.assignment_status.mean()),revenue=reward,unmatched=int((~f.assignment_status).sum()),no_price_eligible_driver=int(f.pricing_outcome.eq('OFFERED_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER').sum()),invalid_masks=0,no_feasible_actions=0,passenger_threshold_violations=0,forced_requests=int(f.feasible_action_count.eq(1).sum()),choice_requests=int(f.feasible_action_count.gt(1).sum()),action_counts=json.dumps(counts),action_percentages=json.dumps((np.array(counts)*100/len(f)).tolist()),charging_events=len(env.charging_events),vehicles_entering_charging=len(entered),vehicles_leaving_charging=len(left),soc_min=soc_min,soc_max=soc_max,fleet_conserved=True,final_fleet_hash=digest(fleet_state(env)),outcome_hash=digest(f[['Request_ID','selected_action_index','assignment_status','reward','pricing_outcome']].to_dict('records')),optimizer_updates=0,runtime_seconds=time.monotonic()-start)
 assert sha256(O/'march16_fixture.pkl')==m['fixture_sha256']
 return summary,f,view.q

def main():
 try:
  p=provider();f,m=create_fixture(p);rows=[];repro=[]
  for policy in ['HIGHEST_FEASIBLE','LOWEST_FEASIBLE','NEUTRAL_1_00_WITH_EXISTING_FALLBACK']:
   a,_,_=evaluate(p,f,m,policy);b,_,_=evaluate(p,f,m,policy)
   assert {k:v for k,v in a.items() if k!='runtime_seconds'}=={k:v for k,v in b.items() if k!='runtime_seconds'},'Baseline reproducibility mismatch'
   rows.append(a);repro.append(dict(policy=policy,exact_match=True,first_hash=a['outcome_hash'],repeat_hash=b['outcome_hash']))
   pd.DataFrame(rows).to_csv(O/'v2_full_day_baseline_comparison.csv',index=False);pd.DataFrame(repro).to_csv(O/'v2_full_day_baseline_reproducibility.csv',index=False)
  js(O/'baseline_manifest.json',dict(status='FROZEN',fixture_sha256=m['fixture_sha256'],comparison_sha256=sha256(O/'v2_full_day_baseline_comparison.csv'),reproducibility_sha256=sha256(O/'v2_full_day_baseline_reproducibility.csv'),training=False))
 except BaseException as e:
  js(O/'baseline_failure.json',dict(status='FAILED',reason=str(e),traceback=traceback.format_exc(),training=False));raise
if __name__=='__main__':main()
