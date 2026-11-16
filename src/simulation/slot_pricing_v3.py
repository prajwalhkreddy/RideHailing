"""Opt-in V3 orchestrator: frozen operational engine, proactive slot pricing."""
from dataclasses import replace
import numpy as np,pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.pricing.slot_v3 import allowed,FittedSensitivity,DropoffProbability,destination_states,pmax
from src.rl.slot_pricing_v3 import SlotDQN
from src.dispatch.dispatch import dispatch_requests,DISPATCH_MODEL_LEGACY
from src.dispatch.request import RequestStatus
from src.pricing.slot_v3_request import V3Request
from src.pricing.dqn_contract import passenger_commitment,completed_request_outcomes
from src.simulation.operational_state import charging_grid_observations
from src.fleet.fleet import validate_fleet
class SlotPricingV3:
 def __init__(self,*,start,routing_checkpoint,seed=42,**engine_kwargs):
  self.checkpoint_phase="FRESH_START";self.episode=0;self.seed=seed;self.routing_checkpoint_path=str(routing_checkpoint)
  allowed(start)
  if 'dqn_checkpoint' in engine_kwargs:raise ValueError('V3 cannot load legacy learner')
  self.engine=ProductionExperiment(start=start,routing_checkpoint=routing_checkpoint,frozen_routing=True,seed=seed,**engine_kwargs)
  self.learner=SlotDQN(seed);self.provider=FittedSensitivity(seed+1);self.dropoff=DropoffProbability();self.states=destination_states(self.engine,self.dropoff);self.audit=[];self.slot_audit=[];self.slots=0
 def run_slot(self,requests=None,*,policy=None,weather_code=None):
  self.checkpoint_phase="IN_SLOT"
  result=self._run_slot(requests,policy=policy,weather_code=weather_code)
  self.checkpoint_phase="POST_SLOT_COMMIT"
  return result
 def _run_slot(self,requests=None,*,policy=None,weather_code=None):
  e=self.engine;t=allowed(e.timestamp);end=t+pd.Timedelta(minutes=30)
  if self.slots>=16:raise ValueError('Episode finished')
  if e.clock!=t:raise ValueError('Slot clock mismatch')
  # No request data are passed to action selection; all142 contexts fixed first.
  actions={d:int(policy(d,s.copy()) if policy else self.learner.select_action(s)) for d,s in self.states.items()}
  if any(a not in range(7) for a in actions.values()):raise ValueError('Invalid action')
  requests=[V3Request.adapt(r) for r in (e.requests_for_slot() if requests is None else list(requests))]
  if len({r.request_id for r in requests})!=len(requests):raise ValueError('Duplicate request IDs')
  for r in requests:r.validate(range(142),15)
  if weather_code is None:
   w=pd.read_parquet(e.base/'demand_master_jan_mar_2026.parquet',columns=['GridID','WeatherCode'],filters=[('TimeSlot','==',t)]).set_index('GridID')
   if len(w)!=142 or w.index.duplicated().any():raise ValueError('Incomplete weather')
  reward={d:0. for d in actions};times={};rows=[]
  for mini in range(15):
   for r in sorted((x for x in requests if x.request_time==mini),key=lambda r:(r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id)):
    offset=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else mini*120
    e.advance_until(t+pd.Timedelta(seconds=offset));d=r.destination_grid;factor=self.provider.contract['actions'][actions[d]];offer=factor*self.provider.contract['P_base'];code=weather_code if weather_code is not None else float(w.loc[r.origin_grid,'WeatherCode']);draw=self.provider.draw(code,e.clock);ceiling=pmax(r.trip_distance_km,draw['epsilon'],self.provider.contract);accepted=offer<=ceiling
    r.base_fare=self.provider.contract['P_base'];r.pricing_factor=factor;r.offered_fare=offer;r.customer_accepted=bool(accepted);r.customer_model='SOURCE_ALIGNED_SLOT_PRICING_V3';r.epsilon_customer=draw['epsilon'];r.p_max=ceiling
    outcome='PASSENGER_REJECTED';contribution=0.
    if accepted:
     contribution=offer;reward[d]+=offer
     dispatch_requests([r],e.fleet,e.lookup,2,15,energy_parameters=e.energy,dispatch_model=DISPATCH_MODEL_LEGACY,slot_start_time=t.to_pydatetime(),station_reserve=e.station_reserve,reserve_observer=e.record_reserve_rejection,driver_minimum_prices=e.profiles.price_preference)
     outcome='ACCEPTED_BUT_UNMATCHED'
     if r.status is RequestStatus.ASSIGNED:
      if r.assigned_vehicle_id in e.passengers or r.assigned_vehicle_id in e.missions:raise ValueError('Duplicate assignment')
      c=passenger_commitment(r,t);e.passengers[r.assigned_vehicle_id]=replace(c,committed_at=e.clock,dropoff_at=e.clock+pd.Timedelta(minutes=r.trip_duration_minutes));times[r.request_id]=e.clock;outcome='ACCEPTED_AND_ASSIGNED'
    else:r.status=RequestStatus.UNSERVED
    # Separate pricing taxonomy preserves the frozen dispatch lifecycle enum.
    r.pricing_outcome=outcome
    rows.append(dict(request_id=r.request_id,slot=str(t),destination_context=d,factor=factor,P_offer=offer,weather_code=code,**draw,L=r.trip_distance_km,L_base=self.provider.contract['L_base'],P_base=self.provider.contract['P_base'],P_max=ceiling,accepted=bool(accepted),dispatch_outcome=outcome,reward_contribution=contribution,reason='offer<=raw ceiling' if accepted else 'offer>raw ceiling'))
   e.advance_until(t+pd.Timedelta(minutes=2*(mini+1)))
  outcomes=completed_request_outcomes(requests,t);outcomes=[replace(x,assigned_at=times[x.request_id]) if x.assigned else x for x in outcomes];e.ledger.complete_slot(t,end,outcomes)
  e.route_idle();e.operational.complete_slot(slot_start=t,completed_at=end,requests=requests,charging_waits=charging_grid_observations(e.charging));e.timestamp=end;e.slot_index+=1
  terminal=self.slots==15
  # Even terminal states use actual post-slot state; targets never bootstrap there.
  e.current_states=e._state_sources();next_states=destination_states(e,self.dropoff)
  for d in actions:
   rr=[r for r in rows if r['destination_context']==d];acc=sum(r['accepted'] for r in rr);assigned=sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in rr)
   self.learner.store(self.states[d],actions[d],reward[d],next_states[d],terminal)
   self.slot_audit.append(dict(slot=str(t),destination_context=d,action=actions[d],factor=self.provider.contract['actions'][actions[d]],generated=len(rr),accepted=acc,rejected=len(rr)-acc,assigned=assigned,accepted_unmatched=acc-assigned,accepted_revenue=reward[d],assignment_revenue=sum(r['P_offer'] for r in rr if r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED'),mean_offer=np.mean([r['P_offer'] for r in rr]) if rr else 0.,transitions=1,terminal=terminal,next_state_timestamp=str(end)))
  self.states=next_states;self.slots+=1;self.audit.extend(rows);validate_fleet(e.fleet.vehicles,range(142),e.fleet_size)
  return rows
