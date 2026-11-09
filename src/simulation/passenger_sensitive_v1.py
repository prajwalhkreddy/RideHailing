"""Opt-in V1 request-pricing boundary; frozen operational interfaces reused."""
from dataclasses import replace
import hashlib
import numpy as np
import pandas as pd
from src.simulation.final_production import ProductionExperiment
from src.pricing.passenger_sensitive_v1 import P_BASE_USD,L_BASE_KM,ACTIONS,CANDIDATE_PRICES,maximum_price,feasible_mask,guard_date,effective_threshold,P_PLATFORM_MIN,P_PLATFORM_MAX
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN,ActionableRequestLinker
from src.dispatch.request import RequestStatus
from src.dispatch.dispatch import dispatch_requests,DISPATCH_MODEL_LEGACY
from src.pricing.dqn_contract import completed_request_outcomes,passenger_commitment,artifact_snapshots
from src.simulation.operational_state import charging_grid_observations
from src.fleet.fleet import validate_fleet

class PassengerSensitiveExperiment(ProductionExperiment):
    def __init__(self,*,provider,learner=None,seed=42,start='2026-03-12 15:30',routing_checkpoint,validation_only=True,**kwargs):
        guard_date(start)
        if 'dqn_checkpoint' in kwargs:raise ValueError('No legacy DQN checkpoint allowed in V1.')
        if not validation_only:provider.require_training_ready()
        super().__init__(seed=seed,start=start,routing_checkpoint=routing_checkpoint,frozen_routing=True,**kwargs)
        self.dqn=learner if learner is not None else PassengerSensitiveDQN()
        if not isinstance(self.dqn,PassengerSensitiveDQN):raise ValueError('V1 learner required.')
        self.provider=provider;self.validation_only=validation_only
        self.linker=ActionableRequestLinker(self.dqn);self.request_audit=[];self.episode_finished=False

    def run_slot(self,requests=None,*,terminal=False,train_dqn=False,explore_pricing=True):
        t=guard_date(self.timestamp);end=t+pd.Timedelta(minutes=30)
        if self.episode_finished:raise ValueError('Episode already terminal; reset environment before continuation.')
        if train_dqn:
            self.provider.require_training_ready()
            if self.validation_only:raise ValueError('Validation fixture cannot train.')
            guard_date(t,calibration=True)
        if self.clock!=t:raise ValueError('Slot clock mismatch.')
        if not terminal:artifact_snapshots(end)
        requests=self.requests_for_slot() if requests is None else list(requests)
        if len({r.request_id for r in requests})!=len(requests):raise ValueError('Duplicate request IDs.')
        for r in requests:r.validate(range(142),15)
        rows=[];contexts={};assignment_times={};completed=0;assigned=0;offers=0;no_offer=0
        price_rejections=[];price_unmatched=0;before=len(self.linker.audit)
        for mini in range(15):
            ordered=sorted((r for r in requests if r.request_time==mini),key=lambda r:(r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id))
            for r in ordered:
                offset=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120
                completed+=self.advance_until(t+pd.Timedelta(seconds=offset))
                key=(r.origin_grid,r.destination_grid)
                if key not in contexts:contexts[key]=self.current_states.build(*key,t)
                state=contexts[key];draw=self.provider.sample();raw_pc=maximum_price(r.trip_distance_km,draw.value);pc=effective_threshold(raw_pc);mask=feasible_mask(pc)
                action=self.dqn.select_action(state,mask,explore=explore_pricing)
                reward=0.;eligible=None
                row=dict(Request_ID=r.request_id,timestamp=str(self.clock),slot=self.slot_index+1,Origin_Grid_ID=r.origin_grid,Destination_Grid_ID=r.destination_grid,state_sha256=hashlib.sha256(state.tobytes()).hexdigest(),state_13d=state.tolist(),L_gg_km=r.trip_distance_km,L_base_km=L_BASE_KM,epsilon_raw=draw.raw,epsilon_min=draw.minimum,epsilon_c=draw.value,P_base_USD=P_BASE_USD,P_c_USD=pc,P_raw_c=raw_pc,P_accept_c=pc,P_platform_min=P_PLATFORM_MIN,P_platform_max=P_PLATFORM_MAX,signed_source_epsilon=None,feasible_action_count=int(mask.sum()))
                for i,label in enumerate(['085','090','095','100','105','110','115']):row['action_'+label+'_price']=float(CANDIDATE_PRICES[i]);row['mask_'+label]=bool(mask[i])
                if action is None:
                    no_offer+=1;r.status=RequestStatus.UNSERVED
                    outcome='NO_FEASIBLE_PRICING_ACTION';r.v1_pricing_outcome=outcome
                    row.update(selected_action_index=None,selected_factor=None,P_offer_USD=None,passenger_status='NOT_OFFERED')
                else:
                    offers+=1;offered=action.pricing_factor*P_BASE_USD
                    if offered>pc:raise ValueError('Invariant: selected offer exceeds passenger maximum.')
                    r.base_fare=P_BASE_USD;r.pricing_factor=action.pricing_factor;r.offered_fare=offered;r.customer_accepted=True;r.customer_model='passenger_sensitive_v1'
                    r.v1_epsilon_c=draw.value;r.v1_epsilon_min=draw.minimum;r.v1_pc_usd=pc;r.v1_raw_pc_usd=raw_pc
                    price_before=len(price_rejections)
                    dispatch_requests([r],self.fleet,self.lookup,2,15,energy_parameters=self.energy,dispatch_model=DISPATCH_MODEL_LEGACY,slot_start_time=t.to_pydatetime(),station_reserve=self.station_reserve,reserve_observer=self.record_reserve_rejection,driver_minimum_prices=self.profiles.price_preference,price_observer=lambda req,vehicle:price_rejections.append(req.request_id))
                    if r.status is RequestStatus.ASSIGNED:
                        if r.assigned_vehicle_id in self.passengers or r.assigned_vehicle_id in self.missions:raise ValueError('Duplicate assignment.')
                        commitment=passenger_commitment(r,t)
                        self.passengers[r.assigned_vehicle_id]=replace(commitment,committed_at=self.clock,dropoff_at=self.clock+pd.Timedelta(minutes=r.trip_duration_minutes))
                        assignment_times[r.request_id]=self.clock;assigned+=1;reward=offered;eligible=True;outcome='OFFERED_ACCEPTED_ASSIGNED'
                    elif len(price_rejections)>price_before:
                        price_unmatched+=1;eligible=False;outcome='OFFERED_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER'
                    else:eligible=False;outcome='OFFERED_ACCEPTED_OTHER_UNMATCHED'
                    r.v1_pricing_outcome=outcome
                    row.update(selected_action_index=action.action_index,selected_factor=action.pricing_factor,P_offer_USD=offered,passenger_status='ACCEPTED')
                self.linker.observe(r.request_id,state,None if action is None else action.action_index,reward,self.clock,mask)
                row.update(pricing_outcome=outcome,driver_price_eligible=eligible,assignment_status=r.status is RequestStatus.ASSIGNED,reward=reward,transition_created=False)
                rows.append(row)
            completed+=self.advance_until(t+pd.Timedelta(minutes=2*(mini+1)))
        if terminal:self.linker.finish_episode(end);self.episode_finished=True
        outcomes=completed_request_outcomes(requests,t)
        outcomes=[replace(o,assigned_at=assignment_times[o.request_id]) if o.assigned else o for o in outcomes]
        reward=self.ledger.complete_slot(t,end,outcomes)
        if not np.isclose(reward,sum(r['reward'] for r in rows),rtol=1e-12):raise ValueError('Reward reconciliation failed.')
        routing_counts,charging_decisions=self.route_idle()
        self.operational.complete_slot(slot_start=t,completed_at=end,requests=requests,charging_waits=charging_grid_observations(self.charging))
        self.timestamp=end;self.slot_index+=1
        if not terminal:self.current_states=self._state_sources()
        self.request_audit.extend(rows)
        links={a['Request_ID']:a for a in self.linker.audit}
        for row in self.request_audit:
            if row['Request_ID'] in links:row.update(transition_created=True,**{k:links[row['Request_ID']][k] for k in ['next_actionable_request_id','delta_t_minutes','gamma_eff','done']})
        updates=self.dqn.complete_slot(t) if train_dqn else []
        validate_fleet(self.fleet.vehicles,range(142),self.fleet_size)
        report=dict(timestamp=str(t),requests_seen=len(requests),offers_generated=offers,no_feasible_pricing_action=no_offer,offered_passenger_accepted=offers,offered_passenger_rejected=0,assigned=assigned,accepted_unmatched=offers-assigned,accepted_no_price_eligible_driver=price_unmatched,transitions_added=len(self.linker.audit)-before,optimizer_updates=len(updates),slot_request_count=len(requests),slot_actionable_request_count=offers,slot_no_offer_count=no_offer,slot_transitions_added=len(self.linker.audit)-before,slot_optimizer_updates=len(updates),reward=reward,completed=completed,fleet_size=len(self.fleet.vehicles),routing_actions=routing_counts.tolist(),charging_decisions=charging_decisions,pending_transition=self.linker.pending is not None)
        self.reports.append(report);return report
