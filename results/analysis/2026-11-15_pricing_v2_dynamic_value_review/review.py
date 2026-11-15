"""Bounded same-state diagnostic. No production edits, training or full-day replay."""
import sys,copy,inspect,textwrap,types,pickle,hashlib,json
from pathlib import Path
from dataclasses import asdict
import numpy as np,pandas as pd
O=Path(__file__).resolve().parent;P=Path('results/training/pricing_v2_staged_training_001/weather_conditioned').resolve();sys.path.insert(0,str(P))
import prepare_development as prep
import src.simulation.passenger_sensitive_v1 as runtime
from src.rl.pricing_dqn import PricingAction,ACTIONS
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN
HORIZONS=(0,1,5,25,100)
class StopReview(Exception):pass

def sha(x):return hashlib.sha256(pickle.dumps(x,protocol=5)).hexdigest()
def physical(env):
 return dict(clock=str(env.clock),fleet=[asdict(x) for x in env.fleet.vehicles],passengers=env.passengers,missions=env.missions,charging=env.charging.__dict__,operational=env.operational.__dict__,routing=env.routing.__dict__,current_states=env.current_states.__dict__)
def canonical(x):
 if isinstance(x,np.ndarray):return dict(array=x.tolist(),dtype=str(x.dtype))
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,dict):return {str(k):canonical(v) for k,v in sorted(x.items(),key=lambda kv:str(kv[0]))}
 if isinstance(x,(list,tuple)):return [canonical(v) for v in x]
 if isinstance(x,(set,frozenset)):return sorted([canonical(v) for v in x],key=str)
 if isinstance(x,(str,int,float,bool,type(None))):return x
 if isinstance(x,pd.Timestamp):return str(x)
 if isinstance(x,np.random.Generator):return canonical(x.bit_generator.state)
 if isinstance(x,(pd.DataFrame,pd.Series)):return canonical(x.to_dict())
 from enum import Enum
 if isinstance(x,Enum):return x.value
 if hasattr(x,'__dict__'):return canonical(x.__dict__)
 return str(x)
def state_hash(env):return hashlib.sha256(json.dumps(canonical(physical(env)),sort_keys=True).encode()).hexdigest()
def clone(env):
 memo={id(env.pricing):env.pricing,id(env.policy):env.policy,id(env.dqn.learner):env.dqn.learner}
 # Immutable support arrays are shared; generators and mutable simulator objects are copied.
 def arrays(x):
  if isinstance(x,np.ndarray):memo[id(x)]=x
  elif isinstance(x,dict):
   for v in x.values():arrays(v)
  elif isinstance(x,(tuple,list)):
   for v in x:arrays(v)
 arrays(env.provider.__dict__)
 return copy.deepcopy(env,memo)

def instrument():
 src=textwrap.dedent(inspect.getsource(runtime.PassengerSensitiveExperiment.run_slot))
 src=src.replace('def run_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=True):','def diagnostic_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=False):')
 src=src.replace('action=self.dqn.select_action(state,mask,explore=explore_pricing)','self.review_before(locals())\n            action=self.dqn.select_action(state,mask,explore=explore_pricing)')
 src=src.replace('rows.append(row)','rows.append(row)\n            self.review_after(locals())')
 ns=dict(vars(runtime));exec(compile(src,'<diagnostic_slot>','exec'),ns)
 tail=src.replace('def diagnostic_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=False):','def diagnostic_tail(self,snapshot):')
 start=tail.index('    t=guard_date');end=tail.index('    for mini in range(15):')
 tail=tail[:start]+'''    t=snapshot['t'];end=snapshot['end'];terminal=False;train_dqn=False;explore_pricing=False
    requests=snapshot['remaining'];weather_context=snapshot['weather_context'];contexts=snapshot['contexts']
    rows=[];assignment_times={};completed=0;assigned=0;offers=0;no_offer=0;price_rejections=[];price_unmatched=0;before=len(self.linker.audit)
'''+tail[end:]
 tail=tail.replace('for mini in range(15):',"for mini in range(snapshot['mini'],15):")
 tail=tail.replace("if weather_context is not None:\n                draw,conditioning=", "if r.request_id==snapshot['focal_id']:\n                draw,conditioning=snapshot['draw'],snapshot['conditioning']\n            elif weather_context is not None:\n                draw,conditioning=")
 exec(compile(tail,'<diagnostic_tail>','exec'),ns)
 return ns['diagnostic_slot'],ns['diagnostic_tail']

class Policy(prep.EvaluationPolicy):
 def __init__(self,model):super().__init__('GREEDY_DQN',model);self.override=None
 def select_action(self,state,mask,*,explore=False):
  q=self.learner.online(np.asarray(state)[None,:],training=False).numpy()[0];ix=np.flatnonzero(mask)
  a=int(ix[np.argmax(q[ix])]) if self.override is None else self.override
  self.override=None;assert mask[a];return PricingAction(a,ACTIONS[a],0.,False)

def setup():
 fixture,m=prep.load_fixture();p=prep.provider();d=PassengerSensitiveDQN.load(P/'checkpoints/episode_025',sensitivity_provider=p)
 p.rng=np.random.default_rng(prep.SEED);p.fallback_counts={str(i):0 for i in range(4)}
 view=Policy(types.SimpleNamespace(online=d.online));env=prep.environment(p,view);assert prep.digest(prep.fleet_state(env))==m['initial_fleet_hash']
 return fixture,m,env

def main():
 fixture,m,env=setup();original_hash=prep.sha256(P/'march16_fixture.pkl');slot,tail=instrument()
 base=pd.read_parquet(P/'HIGHEST_FEASIBLE_requests.parquet');a=pd.read_csv(P/'development_actions_ep25.csv');assert np.array_equal(a.Request_ID,base.Request_ID)
 merged=base.merge(a[['Request_ID','selected_action_index']],on='Request_ID',suffixes=('_highest','_dqn'),validate='one_to_one');merged['rank_below']=merged.feasible_action_count-1-merged.selected_action_index_dqn
 candidates=merged[merged.rank_below>0].copy();candidates['rank_band']=np.where(candidates.rank_below==1,'ONE_BELOW',np.where(candidates.rank_below==2,'TWO_BELOW','THREE_PLUS'));candidates['immediate_offered_fare_difference']=.05*candidates.rank_below*env.pricing.P_BASE_USD
 candidates['dqn_driver_id']=pd.NA;candidates['simulator_state_fingerprint']=pd.NA
 candidates.to_csv(O/'all_divergence_candidates.csv',index=False)
 ordered=sorted(fixture['slots'][0],key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id))
 ids=[r.request_id for r in ordered];eligible=merged[merged.Request_ID.isin(ids[:-101])].copy();eligible['position']=eligible.Request_ID.map({x:i for i,x in enumerate(ids)});eligible=eligible.sort_values('position')
 selected=[]
 for name,mask in [('ONE_BELOW',eligible.rank_below==1),('TWO_BELOW',eligible.rank_below==2),('THREE_PLUS',eligible.rank_below>=3),('CONTROL',eligible.rank_below==0)]:
  g=eligible[mask & eligible.feasible_action_count.gt(1)];n=min(4 if name!='CONTROL' else 2,len(g))
  if n:
   for i in np.linspace(0,len(g)-1,n,dtype=int):selected.append(dict(request_id=int(g.iloc[i].Request_ID),stratum=name,position=int(g.iloc[i].position)))
 selection={x['request_id']:x for x in selected};assert selected
 prep.js(O/'selection_rule.json',dict(rule='First-slot bounded review. Four evenly rank-spaced chronological cases per rank band; two choice controls; require100 later requests in same slot. No outcome-based selection.',cases=selected,horizons=list(HORIZONS),limitations='T1 and midnight initial fleet only; no slot-boundary routing intervention; no population extrapolation.',runtime_source_sha256=prep.sha256('src/simulation/passenger_sensitive_v1.py')))
 outcome=[];matches=[];cases=[];prefix_count=0
 def before(loc):
  nonlocal prefix_count
  r=loc['r'];idx=prefix_count;assert r.request_id==ids[idx]
  expected=merged.set_index('Request_ID').loc[r.request_id]
  assert loc['draw'].value==expected.epsilon_c
  q=env.dqn.learner.online(np.asarray(loc['state'])[None,:],training=False).numpy()[0];dqn=int(np.flatnonzero(loc['mask'])[np.argmax(q[loc['mask']])]);assert dqn==expected.selected_action_index_dqn
  if r.request_id not in selection:return
  env.review_before=None;env.review_after=None
  original_state=state_hash(env);rng_before=sha(env.provider.rng.bit_generator.state)
  snapshot=dict(t=loc['t'],end=loc['end'],remaining=ordered[idx:],weather_context=loc['weather_context'],contexts=loc['contexts'],mini=loc['mini'],focal_id=r.request_id,draw=loc['draw'],conditioning=loc['conditioning'])
  outputs={}
  for branch,action in [('DQN',dqn),('HIGHEST',int(np.flatnonzero(loc['mask'])[-1]))]:
   child=clone(env);ss=copy.deepcopy(snapshot);assert state_hash(child)==original_state;assert sha(child.provider.rng.bit_generator.state)==rng_before
   assert child.fleet is not env.fleet and child.fleet.vehicles[0] is not env.fleet.vehicles[0]
   child.dqn.override=action;records=[];initial_charging=len(child.charging_events)
   def noop(loc):pass
   def after(z):
    records.append(dict(request_id=z['r'].request_id,assigned=z['row']['assignment_status'],driver=z['r'].assigned_vehicle_id,reward=z['row']['reward']))
    h=len(records)-1
    if h in HORIZONS:
     reward=np.array([x['reward'] for x in records]);out=dict(request_id=r.request_id,stratum=selection[r.request_id]['stratum'],branch=branch,horizon=h,assignments=sum(x['assigned'] for x in records),unmatched=sum(not x['assigned'] for x in records),revenue=float(reward.sum()),discounted_reward=float((reward*.99**np.arange(len(reward))).sum()),immediate_driver=records[0]['driver'],immediate_assignment=records[0]['assigned'],immediate_reward=records[0]['reward'],offered_fare=action*0.05*child.pricing.P_BASE_USD+.85*child.pricing.P_BASE_USD,state_hash=state_hash(child),location_hash=sha([(v.vehicle_id,v.current_grid,v.destination) for v in child.fleet.vehicles]),available_supply=sum(str(v.trip_status.value).lower()=='idle' for v in child.fleet.vehicles),incoming_commitments=len(child.passengers),charging_events=len(child.charging_events)-initial_charging,routing_hash=hashlib.sha256(json.dumps(canonical(child.routing.__dict__),sort_keys=True).encode()).hexdigest(),subsequent_drivers=sha([x['driver'] for x in records[1:]]),rng_hash=sha(child.provider.rng.bit_generator.state))
     outcome.append(out);outputs[(branch,h)]=out
    if h==100:raise StopReview()
   child.review_before=noop;child.review_after=after
   try:tail(child,ss)
   except StopReview:pass
   else:raise AssertionError('Bound not reached')
  assert state_hash(env)==original_state and sha(env.provider.rng.bit_generator.state)==rng_before
  matches.append(dict(request_id=r.request_id,state_hash=original_state,initial_states_equal=True,rng_equal=True,parent_unchanged=True,isolated=True))
  if selection[r.request_id]['stratum']=='CONTROL':
   for h in HORIZONS:
    aa=outputs['DQN',h];bb=outputs['HIGHEST',h];assert all(aa[k]==bb[k] for k in aa if k!='branch')
  cases.append(dict(**selection[r.request_id],timestamp=str(env.clock),origin=r.origin_grid,destination=r.destination_grid,distance_km=r.trip_distance_km,weather_code=loc['conditioning']['raw_weather_code'],T_group=loc['conditioning']['T_group'],epsilon=loc['draw'].value,feasible_actions=np.flatnonzero(loc['mask']).tolist(),dqn_factor=ACTIONS[dqn],highest_factor=ACTIONS[int(np.flatnonzero(loc['mask'])[-1])],q_dqn=float(q[dqn]),q_highest=float(q[np.flatnonzero(loc['mask'])[-1]]),state_fingerprint=original_state,assigned_driver_dqn=outputs['DQN',0]['immediate_driver']))
  env.review_before=before;env.review_after=after_parent
  pd.DataFrame(outcome).to_csv(O/'counterfactual_outcomes.csv',index=False);pd.DataFrame(cases).to_csv(O/'selected_counterfactual_cases.csv',index=False);pd.DataFrame(matches).to_csv(O/'state_match_verification.csv',index=False)
 def after_parent(loc):
  nonlocal prefix_count
  expected=a.set_index('Request_ID').loc[loc['r'].request_id];assert np.isclose(loc['row']['reward'],expected.reward)
  prefix_count+=1
  if prefix_count>max(x['position'] for x in selected):raise StopReview()
 env.review_before=before;env.review_after=after_parent
 try:slot(env,copy.deepcopy(fixture['slots'][0]),explore_pricing=False)
 except StopReview:pass
 assert len(cases)==len(selected) and prep.sha256(P/'march16_fixture.pkl')==original_hash
 prep.js(O/'verification.json',dict(status='PASS',cases=len(cases),controls=sum(x['stratum']=='CONTROL' for x in cases),prefix_requests=prefix_count,fixture_unchanged=True,same_state=True,protected_access=False,training_started=False,episode26='NOT_STARTED'))
 print('COUNTERFACTUAL_COMPLETE',len(cases))
if __name__=='__main__':main()
