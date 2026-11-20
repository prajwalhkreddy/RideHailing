"""Opt-in observed-OD orchestration; unchanged request/dispatch/EV mechanics."""
from dataclasses import replace
from collections import defaultdict
from src.simulation import historical_request_replay as historical
import numpy as np,pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.pricing.slot_v3 import allowed,FittedSensitivity,pmax
from src.pricing.weighted_binned_sampler import load_sensitivity
from src.rl.od_pricing_dqn import ODPricingDQN
from src.pricing.od_contract import VERSION, load_support, pairs_from_support, od_states
from src.pricing.dispatch_reward import REWARD_VERSION, reconcile_dispatch_rewards
from src.dispatch.dispatch import dispatch_requests,DISPATCH_MODEL_LEGACY
from src.dispatch.request import RequestStatus
from src.pricing.slot_v3_request import V3Request
from src.pricing.dqn_contract import passenger_commitment,completed_request_outcomes
from src.simulation.operational_state import charging_grid_observations
from src.fleet.fleet import validate_fleet
class ODPricingRuntime:
 def __init__(self,*,start,routing_checkpoint,seed=42,od_support=None,sensitivity_contract=None,master_math=False,operational=False,utc_inputs=None,fallback_contract=None,information_contract=None,multi_episode=False,evaluation_mode=False,**engine_kwargs):
  self.multi_episode=bool(multi_episode);self.evaluation_mode=bool(evaluation_mode)
  if evaluation_mode and not multi_episode:raise ValueError("Evaluation requires versioned orchestration")
  from src.simulation.information_cutoff import validate_manifest
  import json
  from pathlib import Path
  from src.pricing.prospective_binned_sampler import VERSION as PROSPECTIVE
  if information_contract is not None:
   validate_manifest(information_contract)
   hierarchy=engine_kwargs.get('driver_hierarchy')
   if hierarchy is not None and hierarchy.mode!='UTILITY':
    if information_contract['artifacts']['routing'].get('kind')!='FRESH_ONLINE' or not hasattr(hierarchy,'provenance'):raise ValueError('Prospective learned hierarchy requires an online-learning provenance contract')
    if hierarchy.provenance!=json.loads(Path(information_contract['artifacts']['routing']['path']).read_text()):raise ValueError('Online initialization/provenance mismatch')
    from src.routing.online_provenance import utc
    if multi_episode:
     from src.simulation.multi_episode_od import validate_start
     validate_start(start,hierarchy,evaluation_mode)
    elif utc(start)!=utc(hierarchy.provenance['experiment_start']) or hierarchy.round!=0:raise ValueError('Fresh experiment start mismatch')
   required={'sensitivity','od_support','routing','forecast','popularity','operational_prior','driver_profiles'}
   if not required.issubset(information_contract['artifacts']):raise ValueError('Incomplete active fitted provenance')
   for role,path in [('sensitivity',sensitivity_contract),('routing',routing_checkpoint)]:
    if path is None or Path(information_contract['artifacts'][role]['path']).resolve()!=Path(path).resolve():raise ValueError('Active artifact/provenance mismatch')
   if engine_kwargs.get('research_routing',False)!=(information_contract['artifacts']['routing'].get('kind') in {'NONLEARNED','FRESH_ONLINE'}):raise ValueError('Routing lineage/mode mismatch')
   for role,active in [('driver_profiles','data/processed/driver_preferences_seed42.parquet'),('operational_prior','data/processed/spatial_3km_jan_mar_2026/fare_bootstrap_legacy_cutoff.parquet')]:
    if Path(information_contract['artifacts'][role]['path']).resolve()!=Path(active).resolve():raise ValueError('Inherited input/provenance mismatch')
   if 'driver_profiles' in engine_kwargs:raise ValueError('Prospective profiles require persisted verified source')
   if utc_inputs is not None:
    pop=json.loads(Path(information_contract['artifacts']['popularity']['path']).read_text())
    if {int(k):v for k,v in pop.items()}!=utc_inputs['popularity']:raise ValueError('Popularity/provenance mismatch')
   support_record=json.loads(Path(information_contract['artifacts']['od_support']['path']).read_text())
   if od_support!=support_record:raise ValueError('OD support/provenance mismatch')
   if utc_inputs is None or Path(utc_inputs['baseline_provenance']['artifact_path']).resolve()!=Path(information_contract['artifacts']['forecast']['path']).resolve():raise ValueError('Forecast/provenance mismatch')
  if sensitivity_contract is not None and json.loads(Path(sensitivity_contract).read_text()).get('version')==PROSPECTIVE and information_contract is None:raise ValueError('Prospective sensitivity requires information-cutoff contract')
  if information_contract is None and hasattr(engine_kwargs.get('driver_hierarchy'),'provenance'):raise ValueError('Online routing requires complete information contract')
  self.information_contract=information_contract
  if operational:
   raise ValueError("CAUSAL_OD_OPERATION_BLOCKED: verified operational forecast availability is absent; UTC research persistence availability is assumed only")
  from src.pricing.unseen_od import validate
  self.fallback_contract=validate(fallback_contract)
  self.fallback_audit=[]
  self.system_revenue=0.
  self.master_math=bool(master_math)
  self.checkpoint_phase="FRESH_START";self.episode=0;self.seed=seed;self.routing_checkpoint_path=str(routing_checkpoint)
  self.utc_mode=utc_inputs is not None
  if self.utc_mode:
   from src.simulation.master_od_contract import utc
   start=utc(start);master_math=True
  historical._time(start,self.utc_mode)
  self.master_math=bool(master_math)
  if 'dqn_checkpoint' in engine_kwargs:raise ValueError('V3 cannot load legacy learner')
  self.engine=ProductionExperiment(start=start,routing_checkpoint=routing_checkpoint,frozen_routing=True,seed=seed,utc_inputs=utc_inputs,**engine_kwargs)
  if self.master_math:
   from src.simulation.master_operational_state import MasterOperationalGridState
   self.engine.operational.__class__=MasterOperationalGridState
  self.demand_state=historical.initial_state(start,utc_mode=self.utc_mode);self.demand_audit=[]
  self.od_support=load_support() if od_support is None else od_support;self.pairs=pairs_from_support(self.od_support)
  self.learner=ODPricingDQN(seed,master_math=self.master_math,utc_mode=self.utc_mode,exploration_contract="MASTER_UPDATE_STAIRCASE_V1" if multi_episode else "HISTORICAL_LINEAR_V1");self.provider=FittedSensitivity(seed+1) if sensitivity_contract is None else load_sensitivity(sensitivity_contract,seed+1);self.states=od_states(self.engine,self.pairs);self.audit=[];self.slot_audit=[];self.slots=0;self.reward_version=REWARD_VERSION;self.environment_reward=0.
 def run_slot(self,requests=None,*,policy=None,weather_code=None):
  if self.slots>=16:raise ValueError("Episode finished")
  if self.checkpoint_phase not in {"FRESH_START","OD_POST_SLOT_COMMIT"}:raise ValueError("Incomplete OD slot")
  self.checkpoint_phase="IN_SLOT"
  result=self._run_slot(requests,policy=policy,weather_code=weather_code)
  self.checkpoint_phase="OD_POST_SLOT_COMMIT"
  return result
 def _run_slot(self,requests=None,*,policy=None,weather_code=None):
  e=self.engine;t=historical._time(e.timestamp,self.utc_mode);end=t+pd.Timedelta(minutes=30)
  if self.slots>=16:raise ValueError('Episode finished')
  if e.clock!=t:raise ValueError('Slot clock mismatch')
  # OD support is historical and fixed before current requests are inspected.
  actions={d:int(policy(d,s.copy())) for d,s in self.states.items()} if policy else dict(zip(self.states,self.learner.select_actions(list(self.states.values()))))
  if any(a not in range(7) for a in actions.values()):raise ValueError('Invalid action')
  if requests is None:
   requests,demand_report=historical.realize(self.demand_state,t,self.pairs,utc_mode=self.utc_mode,fallback_contract=self.fallback_contract);demand_mode=historical.PROTOCOL
  else:
   requests=list(requests);demand_report=dict(realized_requests=len(requests));demand_mode='EXPLICIT_REQUEST_FIXTURE'
  requests=[V3Request.adapt(r) for r in requests]
  if len({r.request_id for r in requests})!=len(requests):raise ValueError('Duplicate request IDs')
  for r in requests:
   r.validate(range(142),15)
   if (r.origin_grid,r.destination_grid) not in self.states and self.fallback_contract is None:raise ValueError("Unsupported request OD")
  local_t=t.tz_convert("America/New_York").tz_localize(None) if self.utc_mode else t
  if weather_code is None and self.utc_mode:
   weather_code=e.utc_inputs["realized_weather"][str(t)]
  if weather_code is None:
   w=pd.read_parquet(e.base/'demand_master_jan_mar_2026.parquet',columns=['GridID','WeatherCode'],filters=[('TimeSlot','==',t)]).set_index('GridID')
   if len(w)!=142 or w.index.duplicated().any():raise ValueError('Incomplete weather')
  reward={d:0. for d in actions};times={};rows=[]
  for mini in range(15):
   for r in sorted((x for x in requests if x.request_time==mini),key=lambda r:(r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id)):
    offset=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else mini*120
    e.advance_until(t+pd.Timedelta(seconds=offset));d=(r.origin_grid,r.destination_grid);fallback=d not in actions;factor=self.fallback_contract['factor'] if fallback else self.provider.contract['actions'][actions[d]];offer=factor*self.provider.contract['P_base'];code=weather_code if weather_code is not None else float(w.loc[r.origin_grid,'WeatherCode']);draw=self.provider.draw(code,local_t if self.utc_mode else e.clock);ceiling=pmax(r.trip_distance_km,draw['epsilon'],self.provider.contract);accepted=offer<=ceiling
    if fallback:
     from src.pricing.unseen_od import ReferencePriceRequest
     r.__class__=ReferencePriceRequest
    r.base_fare=self.provider.contract['P_base'];r.pricing_factor=factor;r.offered_fare=offer;r.customer_accepted=bool(accepted);r.customer_model=self.fallback_contract['version'] if fallback else 'SOURCE_ALIGNED_SLOT_PRICING_V3';r.epsilon_customer=draw['epsilon'];r.p_max=ceiling
    outcome='PASSENGER_REJECTED';contribution=0.
    if accepted:
     contribution=0.
     dispatch_requests([r],e.fleet,e.lookup,2,15,energy_parameters=e.energy,dispatch_model=DISPATCH_MODEL_LEGACY,slot_start_time=(e.clock-pd.Timedelta(minutes=r.request_time*2)).to_pydatetime() if self.utc_mode else t.to_pydatetime(),station_reserve=e.station_reserve,reserve_observer=e.record_reserve_rejection,driver_minimum_prices=e.profiles.price_preference)
     outcome='ACCEPTED_BUT_UNMATCHED'
     if r.status is RequestStatus.ASSIGNED:
      if r.assigned_vehicle_id in e.passengers or r.assigned_vehicle_id in e.missions:raise ValueError('Duplicate assignment')
      c=passenger_commitment(r,t) if not self.utc_mode else _utc_commitment(r,e.clock);e.passengers[r.assigned_vehicle_id]=replace(c,committed_at=e.clock,dropoff_at=e.clock+pd.Timedelta(minutes=r.trip_duration_minutes));times[r.request_id]=e.clock;outcome='ACCEPTED_AND_ASSIGNED';contribution=offer
      if not fallback:reward[d]+=offer
    else:r.status=RequestStatus.UNSERVED
    # Separate pricing taxonomy preserves the frozen dispatch lifecycle enum.
    r.pricing_outcome=outcome
    rows.append(dict(request_id=r.request_id,slot=str(t),origin_grid=d[0],destination_grid=d[1],od_context=d,is_fallback=fallback,fallback_contract=self.fallback_contract['version'] if fallback else None,factor=factor,P_offer=offer,weather_code=code,**draw,L=r.trip_distance_km,L_base=self.provider.contract['L_base'],P_base=self.provider.contract['P_base'],P_max=ceiling,accepted=bool(accepted),dispatch_outcome=outcome,reward_contribution=contribution,demand_protocol=demand_mode,source_trip_id=r.source_trip_id,source_pickup=str(r.empirical_pickup_datetime),source_dropoff=str(r.empirical_dropoff_datetime),source_file_month=getattr(r,'source_file_month',None),source_prepared_row=getattr(r,'source_prepared_row',None),observed_fare=getattr(r,'observed_fare',None),trip_duration_minutes=r.trip_duration_minutes,reason='offer<=raw ceiling' if accepted else 'offer>raw ceiling'))
   e.advance_until(t+pd.Timedelta(minutes=2*(mini+1)))
  outcomes=completed_request_outcomes(requests,t) if not self.utc_mode else _utc_outcomes(requests,t,times);outcomes=[replace(x,assigned_at=times[x.request_id]) if x.assigned else x for x in outcomes];e.ledger.complete_slot(t,end,outcomes)
  e.route_idle();e.operational.complete_slot(slot_start=t,completed_at=end,requests=requests,charging_waits=charging_grid_observations(e.charging));e.timestamp=end;e.slot_index+=1
  terminal=self.slots==15
  # Even terminal states use actual post-slot state; targets never bootstrap there.
  if getattr(e,"driver_hierarchy",None) is not None:e.driver_hierarchy.finish_slot(t,end)
  e.current_states=e._state_sources();next_states=od_states(e,self.pairs)
  contributions,totals=reconcile_dispatch_rewards([dict(row,destination_context=row['od_context']) for row in rows],list(actions)+sorted({row['od_context'] for row in rows if row['is_fallback']}))
  if any(not np.isclose(totals[d],reward[d],rtol=1e-12,atol=1e-9) for d in actions):raise ValueError("OD reward mismatch")
  self.environment_reward=sum(totals[d] for d in actions)
  fallback_rows=[r for r in rows if r['is_fallback']]
  fallback_revenue=sum(totals[d] for d in totals if d not in actions)
  self.system_revenue=sum(totals.values())
  if not np.isclose(self.system_revenue,self.environment_reward+fallback_revenue,rtol=1e-12,atol=1e-9):raise ValueError('System revenue mismatch')
  self.fallback_audit.append(dict(slot=str(t),requests=len(fallback_rows),accepted=sum(r['accepted'] for r in fallback_rows),assigned=sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in fallback_rows),fallback_revenue=fallback_revenue,supported_reward=self.environment_reward,total_system_revenue=self.system_revenue))
  for row,contribution in zip(rows,contributions):row.update(reward_contribution=contribution,reward_contract=REWARD_VERSION)
  grouped=defaultdict(list)
  for row in rows:grouped[row['od_context']].append(row)
  for d in actions:
   rr=grouped[d];acc=sum(r['accepted'] for r in rr);assigned=sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in rr)
   self.learner.store(self.states[d],actions[d],reward[d],next_states[d],terminal,identity=(t,*d))
   self.slot_audit.append(dict(slot=str(t),origin_grid=d[0],destination_grid=d[1],od_context=d,action=actions[d],factor=self.provider.contract['actions'][actions[d]],generated=len(rr),accepted=acc,rejected=len(rr)-acc,assigned=assigned,accepted_unmatched=acc-assigned,learning_reward=reward[d],reward_contract=REWARD_VERSION,accepted_revenue=sum(r['P_offer'] for r in rr if r['accepted']),assignment_revenue=sum(r['P_offer'] for r in rr if r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED'),mean_offer=np.mean([r['P_offer'] for r in rr]) if rr else 0.,transitions=1,terminal=terminal,next_state_timestamp=str(end)))
  historical.commit(self.demand_state,t,len(rows),demand_report,demand_mode,utc_mode=self.utc_mode)
  self.demand_audit.append(dict(slot=str(t),protocol=demand_mode,**demand_report))
  self.states=next_states;self.slots+=1;self.audit.extend(rows);validate_fleet(e.fleet.vehicles,range(142),e.fleet_size)
  return rows


def _utc_commitment(r,when):
 from src.pricing.dqn_contract import PassengerCommitment
 return PassengerCommitment(r.assigned_vehicle_id,r.destination_grid,when,when+pd.Timedelta(minutes=r.trip_duration_minutes))

def _utc_outcomes(requests,t,times):
 from src.pricing.dqn_contract import DispatchOutcome
 return [DispatchOutcome(r.request_id,r.origin_grid,times.get(r.request_id,t+pd.Timedelta(seconds=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120)),r.customer_accepted is True,r.status is RequestStatus.ASSIGNED,r.offered_fare if r.status is RequestStatus.ASSIGNED else 0.) for r in requests]
