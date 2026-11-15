"""One fixed DQN trajectory; read-only immediate screen, then bounded branches."""
import sys,copy,inspect,textwrap,json,hashlib,pickle
from pathlib import Path
import numpy as np,pandas as pd
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O.parent/'2026-11-15_pricing_v2_dynamic_value_review'))
import review as prior
from review import prep,runtime,Policy,clone,state_hash,canonical,StopReview
from src.dispatch.dispatch import find_eligible_vehicle
from src.fleet.state import VehicleStatus
from src.charging.energy import requires_charging,energy_consumed_kwh
P=prior.P

def eligible(env,r,price):
 grids={r.origin_grid,*env.lookup.get(r.origin_grid,())};energy=energy_consumed_kwh(r.trip_distance_km,env.energy);reserve=env.station_reserve(r.destination_grid)
 return {v.vehicle_id for v in env.fleet.vehicles if v.current_grid in grids and v.trip_status is VehicleStatus.IDLE and not requires_charging(v,env.energy) and v.energy_level>=energy and v.energy_level-energy>=reserve and env.profiles.price_preference[v.vehicle_id]<=price}
def pick(env,r,price):
 req=copy.copy(r);req.offered_fare=price
 v=find_eligible_vehicle(req,env.fleet,env.lookup,env.energy,env.station_reserve,driver_minimum_prices=env.profiles.price_preference)
 return None if v is None else v.vehicle_id

def methods():
 src=textwrap.dedent(inspect.getsource(runtime.PassengerSensitiveExperiment.run_slot))
 src=src.replace('def run_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=True):','def diagnostic_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=False):')
 src=src.replace('action=self.dqn.select_action(state,mask,explore=explore_pricing)','self.review_before(locals())\n            action=self.dqn.select_action(state,mask,explore=explore_pricing)')
 src=src.replace('rows.append(row)','rows.append(row)\n            self.review_after(locals())')
 ns=dict(vars(runtime));exec(compile(src,'<opportunity_slot>','exec'),ns)
 tail=src.replace('def diagnostic_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=False):','def diagnostic_tail(self,snapshot):')
 start=tail.index('    t=guard_date');end=tail.index('    for mini in range(15):')
 tail=tail[:start]+'''    t=snapshot['t'];end=snapshot['end'];terminal=False;train_dqn=False;explore_pricing=False
    requests=snapshot['requests'];weather_context=snapshot['weather_context'];contexts=snapshot['contexts'];rows=snapshot['rows'];assignment_times=snapshot['assignment_times']
    completed=snapshot['completed'];assigned=snapshot['assigned'];offers=snapshot['offers'];no_offer=snapshot['no_offer'];price_rejections=snapshot['price_rejections'];price_unmatched=snapshot['price_unmatched'];before=snapshot['before']
'''+tail[end:]
 tail=tail.replace('for mini in range(15):',"for mini in range(snapshot['mini'],15):")
 tail=tail.replace('if r.request_time==mini)',"if r.request_time==mini and r.request_id in snapshot['remaining_ids'])")
 tail=tail.replace("if weather_context is not None:\n                draw,conditioning=", "if r.request_id==snapshot['focal_id']:\n                draw,conditioning=snapshot['draw'],snapshot['conditioning']\n            elif weather_context is not None:\n                draw,conditioning=")
 exec(compile(tail,'<opportunity_tail>','exec'),ns)
 return ns['diagnostic_slot'],ns['diagnostic_tail']

def frozen_snapshot(env,z,slot_index,action,high,q):
 callbacks=(env.review_before,env.review_after);env.review_before=None;env.review_after=None
 child=clone(env);env.review_before,env.review_after=callbacks
 fields=['t','end','requests','weather_context','contexts','rows','assignment_times','completed','assigned','offers','no_offer','price_rejections','price_unmatched','before','mini','draw','conditioning']
 snap=copy.deepcopy({k:z[k] for k in fields});ordered=sorted(z['requests'],key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id));ids=[r.request_id for r in ordered];pos=ids.index(z['r'].request_id)
 snap.update(focal_id=z['r'].request_id,remaining_ids=set(ids[pos:]))
 return dict(env=child,snapshot=snap,slot_index=slot_index,dqn=action,highest=high,q_dqn=float(q[action]),q_highest=float(q[high]),initial_hash=state_hash(child))

def main():
 fixture,m,env=prior.setup();original=prep.sha256(P/'march16_fixture.pkl');slot,tail=methods()
 expected=pd.read_csv(P/'development_actions_ep25.csv').set_index('Request_ID');base=pd.read_parquet(P/'HIGHEST_FEASIBLE_requests.parquet').set_index('Request_ID')
 screen=[];saved=[];counts={t:0 for t in ['T1','T2','T3','T4']};seen=set();elig_saved=0;controls=0;current=0;processed=0;case_lookup={};reference_boundaries={}
 prep.js(O/'selection_rule.json',dict(genuine='First five distinct (hour,rank gap,divergence type,raw weather) strata per T group; cap20. Selected only from actual driver/outcome divergence.',comparisons='First two eligibility-only cases and first two identical highest-action choice controls.',horizons=['H0','H25','H100','NEXT_SLOT_BOUNDARY','ONE_FULL_SLOT_AFTER_BOUNDARY'],excluded='Final slot cannot cross a full subsequent slot without protected-period access; retain screen but not rollout.',method='Selection during screening is outcome-blind with respect to future value; branches begin only after full-day reproduction passes.'))
 def before(z):
  nonlocal elig_saved,controls
  r=z['r'];q=env.dqn.learner.online(np.asarray(z['state'])[None,:],training=False).numpy()[0];ix=np.flatnonzero(z['mask']);a=int(ix[np.argmax(q[ix])]);high=int(ix[-1]);assert a==int(expected.loc[r.request_id,'selected_action_index']);assert z['draw'].value==base.loc[r.request_id,'epsilon_c']
  if len(ix)<2:return
  if a==high:
   if controls<2 and current<47:
    s=frozen_snapshot(env,z,current,a,high,q);s['case_type']='CONTROL';saved.append(s);controls+=1
   return
  lowprice=env.pricing.P_BASE_USD*prior.ACTIONS[a];highprice=env.pricing.P_BASE_USD*prior.ACTIONS[high]
  lowset=eligible(env,r,lowprice);highset=eligible(env,r,highprice);assert lowset<=highset
  lv=pick(env,r,lowprice);hv=pick(env,r,highprice);assert (lv is None or lv in lowset) and (hv is None or hv in highset)
  outcome=(lv is None)!=(hv is None);changed=lv!=hv
  category='ASSIGNMENT_OUTCOME_CHANGED' if outcome else 'ASSIGNED_DRIVER_CHANGED' if changed else 'DRIVER_ELIGIBILITY_SET_CHANGED_ONLY' if lowset!=highset else 'NO_IMMEDIATE_STATE_DIFFERENCE'
  fingerprint=state_hash(env)
  row=dict(request_id=r.request_id,timestamp=str(env.clock),slot=current+1,hour=env.clock.hour,T_group=z['conditioning']['T_group'],weather_code=z['conditioning']['raw_weather_code'],support_id=z['conditioning']['support_id'],origin=r.origin_grid,destination=r.destination_grid,distance_km=r.trip_distance_km,epsilon=z['draw'].value,feasible_actions=json.dumps(ix.tolist()),dqn_action=a,highest_action=high,rank_gap=high-a,offered_price_difference=lowprice-highprice,passenger_acceptance_both=True,eligible_dqn=len(lowset),eligible_highest=len(highset),eligibility_changed=lowset!=highset,assigned_dqn=lv is not None,assigned_highest=hv is not None,driver_dqn=lv,driver_highest=hv,driver_changed=changed,assignment_outcome_changed=outcome,revenue_dqn=lowprice if lv is not None else 0.,revenue_highest=highprice if hv is not None else 0.,state_fingerprint=fingerprint,classification=category,demand=len(z['requests']),supply=sum(v.trip_status is VehicleStatus.IDLE for v in env.fleet.vehicles))
  screen.append(row);case_lookup[r.request_id]=row
  key=(row['T_group'],row['hour'],row['rank_gap'],category,row['weather_code'])
  choose=False
  if changed and current<47 and counts[row['T_group']]<5 and key not in seen:counts[row['T_group']]+=1;seen.add(key);choose=True
  elif category=='DRIVER_ELIGIBILITY_SET_CHANGED_ONLY' and current<47 and elig_saved<2:elig_saved+=1;choose=True
  if choose:
   s=frozen_snapshot(env,z,current,a,high,q);s['case_type']=category;saved.append(s)
 def after(z):
  nonlocal processed
  r=z['r'];assert np.isclose(z['row']['reward'],expected.loc[r.request_id,'reward']);processed+=1
  if r.request_id in case_lookup:assert r.assigned_vehicle_id==case_lookup[r.request_id]['driver_dqn']
 env.review_before=before;env.review_after=after
 for current in range(48):
  slot(env,copy.deepcopy(fixture['slots'][current]),terminal=current==47,explore_pricing=False)
  reference_boundaries[current]=state_hash(env)
  pd.DataFrame(screen).to_csv(O/'full_day_immediate_opportunity.csv',index=False)
  prep.js(O/'progress.json',dict(stage='A',slots_completed=current+1,screened=len(screen),snapshots=len(saved)))
 assert processed==73754 and prep.digest(prep.fleet_state(env))==pd.read_csv(P/'development_evaluations.csv').set_index('episode').loc[25,'final_fleet_hash']
 f=pd.DataFrame(screen);assert len(f)==int(((expected.feasible_action_count-1)>expected.selected_action_index).sum())
 summary=[]
 f['demand_quantile']=pd.qcut(f.demand,4,duplicates='drop').astype(str);f['supply_quantile']=pd.qcut(f.supply,4,duplicates='drop').astype(str);f.to_csv(O/'full_day_immediate_opportunity.csv',index=False)
 for column in ['T_group','hour','demand_quantile','supply_quantile','support_id','rank_gap']:
  for key,g in f.groupby(column):summary.append(dict(dimension=column,value=str(key),N=len(g),eligible_changed=int(g.eligibility_changed.sum()),driver_changed=int(g.driver_changed.sum()),outcome_changed=int(g.assignment_outcome_changed.sum())))
 pd.DataFrame(summary).to_csv(O/'opportunity_summary.csv',index=False)
 prep.js(O/'stage_a_verification.json',dict(status='PASS',requests=processed,screened=len(f),full_day_final_fleet_matches=True,reward_sequence_matches=True,action_sequence_matches=True,snapshots=len(saved)))
 results=[];selected=[]
 for case_no,c in enumerate(saved):
  s=c['snapshot'];focal=s['focal_id'];records_by_branch={}
  selected.append(dict(request_id=focal,case_type=c['case_type'],slot=c['slot_index']+1,q_dqn=c['q_dqn'],q_highest=c['q_highest'],dqn_action=c['dqn'],highest_action=c['highest'],state_fingerprint=c['initial_hash']))
  for branch,action in [('DQN',c['dqn']),('HIGHEST',c['highest'])]:
   child=clone(c['env']);ss=copy.deepcopy(s);assert state_hash(child)==c['initial_hash'];assert child.provider.rng.bit_generator.state==c['env'].provider.rng.bit_generator.state
   child.dqn.override=action;rewards=[];assigned=[];drivers=[];initial_events=len(child.charging_events)
   def capture(label):
    w=np.asarray(rewards);row=dict(request_id=focal,case_type=c['case_type'],branch=branch,horizon=label,requests=len(w),assignments=sum(assigned),unmatched=len(w)-sum(assigned),revenue=float(w.sum()),discounted_reward=float((w*.99**np.arange(len(w))).sum()),immediate_revenue=rewards[0],immediate_driver=drivers[0],state_hash=state_hash(child),locations_hash=prior.sha([(v.vehicle_id,v.current_grid,v.destination) for v in child.fleet.vehicles]),soc_hash=prior.sha([v.energy_level for v in child.fleet.vehicles]),supply=sum(v.trip_status is VehicleStatus.IDLE for v in child.fleet.vehicles),commitments=len(child.passengers),charging_events=len(child.charging_events)-initial_events,routing_hash=hashlib.sha256(json.dumps(canonical(child.routing.__dict__),sort_keys=True).encode()).hexdigest(),subsequent_drivers_hash=prior.sha(drivers[1:]),rng_hash=prior.sha(child.provider.rng.bit_generator.state))
    results.append(row);records_by_branch[branch,label]=row
   def nop(z):pass
   def observe(z):
    rewards.append(z['row']['reward']);assigned.append(z['row']['assignment_status']);drivers.append(z['r'].assigned_vehicle_id)
    n=len(rewards)-1
    if n in [0,25,100]:capture('H'+str(n))
   child.review_before=nop;child.review_after=observe
   tail(child,ss);capture('NEXT_SLOT_BOUNDARY')
   if branch=='DQN':assert state_hash(child)==reference_boundaries[c['slot_index']]
   nextslot=c['slot_index']+1
   slot(child,copy.deepcopy(fixture['slots'][nextslot]),terminal=nextslot==47,explore_pricing=False);capture('ONE_FULL_SLOT_AFTER_BOUNDARY')
   if branch=='DQN':assert state_hash(child)==reference_boundaries[nextslot]
  if c['case_type']=='CONTROL':
   for branch,label in records_by_branch:
    if branch!='DQN':continue
    a=records_by_branch[branch,label];b=records_by_branch['HIGHEST',label];assert all(a[k]==b[k] for k in a if k!='branch')
  pd.DataFrame(results).to_csv(O/'routing_boundary_counterfactuals.csv',index=False);pd.DataFrame(selected).to_csv(O/'selected_divergent_cases.csv',index=False)
  prep.js(O/'progress.json',dict(stage='B',cases_completed=case_no+1,cases=len(saved)))
 assert prep.sha256(P/'march16_fixture.pkl')==original
 prep.js(O/'verification.json',dict(status='PASS',screened=len(f),driver_changed=int(f.driver_changed.sum()),outcome_changed=int(f.assignment_outcome_changed.sum()),eligibility_changed=int(f.eligibility_changed.sum()),cases=len(saved),fixture_unchanged=True,controls_passed=controls,episode26='NOT_STARTED',protected_access=False))
 print('AUDIT_COMPLETE')
if __name__=='__main__':main()
