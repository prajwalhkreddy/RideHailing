"""Final 142-grid hierarchical orchestrator; legacy runner is separate.

No implicit model training at startup. Private charging preferences are required.
"""
from pathlib import Path
from dataclasses import replace
import json
import numpy as np,pandas as pd,geopandas as gpd,yaml
from src.pricing.dqn_contract import (ROOT,FEATURES,Snapshot,DispatchLedger,PricingStateBuilder,behavioural_model,artifact_snapshots,passenger_commitment,completed_request_outcomes)
from src.rl.pricing_dqn import PricingDQN,ACTIONS,DQNConfig,PricingAction
from src.routing.configuration import configured_interfaces
from src.simulation.temporal_protocol import assert_training_update_allowed,assert_final_training_checkpoint,training_update_allowed
from src.routing.federated import aggregate_policy_updates
from src.routing.final_state import RoutingState
from src.routing.learning import load_final_policy,masked_softmax,LocalPolicyObservation
from src.dispatch.request import RequestState,RequestStatus
from src.dispatch.generation import build_empirical_od_distribution,generate_requests
from src.dispatch.dispatch import dispatch_requests,build_neighbour_lookup,DISPATCH_MODEL_LEGACY
from src.fleet.fleet import Fleet,validate_fleet
from src.fleet.state import VehicleStatus
from src.charging.energy import EnergyParameters,initialize_ev_fleet,requires_charging
from src.charging.stations import stations_from_definition
from src.charging.timed import TimedChargingInfrastructure
from src.simulation.operational_state import charging_grid_observations


def validate_final_contract(meta,routing_input=169,routing_output=9,pricing_input=13,pricing_actions=ACTIONS,timed_charging=True,operational_state=True):
    if meta.get('grid_version')!='true_3km_v1' or meta.get('valid_grid_count')!=142 or meta.get('raster_rows')!=16 or meta.get('raster_columns')!=16:raise ValueError('Final grid requires true_3km_v1, 142 grids, 16x16 raster.')
    if (routing_input,routing_output)!=(169,9):raise ValueError('Final routing requires 169 inputs and 9 outputs; legacy incompatible.')
    if pricing_input!=13 or tuple(pricing_actions)!=ACTIONS:raise ValueError('Final pricing requires 13 inputs and frozen seven actions.')
    if not operational_state:raise ValueError('Canonical operational-state interface required.')
    if not timed_charging:raise ValueError('Timed charging adapter required; zero-time adapter rejected.')

def validate_driver_profiles(profiles, vehicle_ids):
    """Validate all current fleet members as EV-capable; never infer H_i_max."""
    cols=['vehicle_id','price_preference','wait_preference','charging_wait_preference_minutes']
    if not set(cols).issubset(profiles.columns):
        raise ValueError('PROJECT_CONFIG_DECISION_REQUIRED: explicit charging_wait_preference_minutes (H_i_max) per driver is missing; no substitution of W_i_max.')
    profiles=profiles[cols].copy()
    if profiles.vehicle_id.duplicated().any() or not set(vehicle_ids).issubset(profiles.vehicle_id):
        raise ValueError('Driver preferences missing/duplicated.')
    numeric=profiles.to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (numeric<0).any():
        raise ValueError('Finite nonnegative driver preferences required.')
    if (profiles.charging_wait_preference_minutes<=0).any():
        raise ValueError('H_i_max must be strictly positive, finite minutes.')
    return profiles

class ProductionExperiment:
    def __init__(self,root=ROOT,*,seed=42,fleet_size=5000,start='2026-03-16 00:00',fleet=None,driver_profiles=None,dqn_checkpoint=None):
        self.root=Path(root).resolve()
        if self.root!=ROOT:raise ValueError('Final configured interfaces require the active project root.')
        self.config=yaml.safe_load((self.root/'config/config.yaml').read_text());self.timestamp=pd.Timestamp(start);self.clock=self.timestamp
        if self.timestamp.tz is not None or self.timestamp!=self.timestamp.floor('30min'):raise ValueError('Aligned timezone-naive start required.')
        meta=json.loads((self.root/'data/processed/grid_metadata.json').read_text());validate_final_contract(meta)
        base=self.root/'data/processed/spatial_3km_jan_mar_2026';self.base=base
        required=[self.root/'data/processed/grid_lookup.parquet',base/'neighbour_map.parquet',base/'charging_stations.parquet',self.root/'models/routing_policy/jan_mar_2026_3km_169x64x32x9/best.keras',self.root/'results/analysis/2026-10-19_operational_grid_state/dqn_ready_forecasts.parquet']
        for path in required:
            if not path.is_file():raise FileNotFoundError(f'Missing final production component: {path}')
        self.grid=gpd.read_parquet(required[0]);self.neighbours=pd.read_parquet(required[1]);station_defs=pd.read_parquet(required[2])
        self.operational,self.routing=configured_interfaces(self.grid,self.neighbours,station_defs,self.timestamp)
        if self.operational is None:raise ValueError('Canonical operational state required.')
        if dqn_checkpoint is not None:assert_final_training_checkpoint(dqn_checkpoint)
        self.policy=load_final_policy(required[3]);self.dqn=PricingDQN.load(dqn_checkpoint) if dqn_checkpoint else PricingDQN(DQNConfig(seed=seed))
        if self.dqn.config.seed!=seed:raise ValueError('DQN seed must match episode seed.')
        validate_final_contract(meta,self.policy.input_shape[-1],self.policy.output_shape[-1],self.dqn.online.input_shape[-1],ACTIONS)
        self.energy=EnergyParameters(**self.config['energy']);self.energy.validate()
        self.fleet=fleet or Fleet(initialize_ev_fleet(fleet_size,range(142),seed,self.energy,self.config['simulation']['initialization_method']),frozenset(range(142)),2)
        self.fleet_size=len(self.fleet.vehicles)
        if self.fleet.valid_grid_ids!=frozenset(range(142)) or self.fleet.mini_slot_minutes!=2:raise ValueError('Fleet requires final domain and two-minute clock.')
        validate_fleet(self.fleet.vehicles,range(142),self.fleet_size)
        profiles=driver_profiles if driver_profiles is not None else pd.read_parquet(self.root/'data/processed/driver_preferences_seed42.parquet')
        profiles=validate_driver_profiles(profiles,[v.vehicle_id for v in self.fleet.vehicles])
        self.profiles=profiles.set_index('vehicle_id')
        centroids={int(r.GridID):(float(r.CentroidX),float(r.CentroidY)) for r in self.grid.itertuples()}
        self.charging=TimedChargingInfrastructure(stations_from_definition(station_defs,self.config['charging']['station_max_power_kw'],self.energy.charging_power_kw),centroids,random_seed=seed)
        validate_final_contract(meta,timed_charging=self.charging.timed_navigation)
        self.customer=behavioural_model(np.random.default_rng(seed),self.timestamp);self.lookup=build_neighbour_lookup(self.neighbours,range(142))
        self.ledger=DispatchLedger();self.ledger.complete_slot(self.timestamp-pd.Timedelta(minutes=30),self.timestamp,[])
        self.od=None;self.request_rng=np.random.default_rng(np.random.SeedSequence(seed).spawn(1)[0]);self.unsupported_demand={}
        self.passengers={};self.missions={};self.routing_experiences=[];self.routing_experiences_by_vehicle={};self.charging_events=[];self.reports=[];self.request_id=0;self.slot_index=0
        artifact_snapshots(self.timestamp);artifact_snapshots(self.timestamp+pd.Timedelta(minutes=30))
        self.current_states=self._state_sources()

    def _state_sources(self):
        t=self.timestamp;forecast,popularity=artifact_snapshots(t);vectors=[];masks={}
        for g in range(142):
            state=RoutingState.from_producer(self.routing,self.operational,t,g);vectors.append(state.values);masks[g]=state.mask
        logits=self.policy(np.stack(vectors),training=False).numpy()
        probs={g:masked_softmax(logits[g],masks[g]) for g in range(142)}
        commitments=[]
        for vid,c in self.passengers.items():
            v=self.fleet.vehicle(vid)
            if v.trip_status is not VehicleStatus.BUSY or v.destination!=c.destination:raise ValueError('Active passenger commitment/fleet mismatch.')
            if pd.Timestamp(c.dropoff_at)<=t:raise ValueError('Unprocessed passenger arrival.')
            if not np.isclose(v.remaining_travel_time,(pd.Timestamp(c.dropoff_at)-t).total_seconds()/60,atol=1e-8):raise ValueError('Passenger arrival clock mismatch.')
            commitments.append(c)
        return PricingStateBuilder(forecast,self.ledger,commitments,Snapshot(t,t,probs,t),popularity,masks)

    def requests_for_slot(self):
        """Preserve forecast-count / intact January empirical-trip generation."""
        if self.od is None:
            trips=pd.read_parquet(self.base/'trips_jan_mar_2026.parquet',
                columns=['PUGridID','DOGridID','tpep_pickup_datetime','tpep_dropoff_datetime','trip_distance','fare_amount'],
                filters=[('tpep_pickup_datetime','>=',pd.Timestamp('2026-01-01')),('tpep_pickup_datetime','<',pd.Timestamp('2026-02-01'))])
            self.od=build_empirical_od_distribution(trips,range(142))
        forecast,_=artifact_snapshots(self.timestamp)
        counts={g:int(np.rint(max(0.,forecast.get(g,self.timestamp)))) for g in range(142)}
        # Existing generation requires empirical support; expose omissions explicitly.
        self.unsupported_demand={g:n for g,n in counts.items() if n and g not in self.od.origin_row_positions}
        counts={g:(n if g in self.od.origin_row_positions else 0) for g,n in counts.items()}
        requests=generate_requests(counts,self.od,range(142),15,None,self.request_id,rng=self.request_rng)
        self.request_id+=len(requests)
        return requests

    def _continue_charging(self,vehicle):
        station_id=self.missions[vehicle.vehicle_id];target=self.charging.stations[station_id].grid_id
        if vehicle.current_grid==target:
            self.charging.admit_arrived(vehicle,station_id,self.energy,len(self.charging_events));self.missions.pop(vehicle.vehicle_id)
            self.charging_events.append(dict(timestamp=str(self.clock),vehicle=vehicle.vehicle_id,event=vehicle.current_action,grid=vehicle.current_grid))
        else:
            if target not in self.routing.paths(vehicle.current_grid):raise ValueError('Charging station unreachable.')
            _,action=self.routing.paths(vehicle.current_grid)[target];next_grid,distance=self.routing.candidates(vehicle.current_grid)[action]
            from src.routing.operational_interface import LocalDecision
            decision=LocalDecision(action,next_grid,target,'CHARGING',0.,distance,station_id)
            self.routing.start_next_hop(vehicle,decision,speed_kmph=self.config['routing']['speed_kmph'],energy_per_km=self.energy.consumption_rate_kwh_per_km)
            vehicle.current_action='charging_travel'
            self.charging_events.append(dict(timestamp=str(self.clock),vehicle=vehicle.vehicle_id,event='charging_travel',grid=vehicle.current_grid,next_grid=next_grid,distance_m=distance))

    def advance_until(self,end):
        """Split mini-slots at exact travel arrivals; no zero-time location jump."""
        end=pd.Timestamp(end);completed=0
        if end<self.clock:raise ValueError('Clock cannot reverse.')
        while self.clock<end:
            busy=[v for v in self.fleet.vehicles if v.trip_status is VehicleStatus.BUSY]
            # Passenger commitments carry the authoritative absolute event time.
            # Repeated float-minute subtraction can leave a positive residue at
            # an exact boundary, so derive each countdown from that fixed time.
            for vehicle in busy:
                commitment=self.passengers.get(vehicle.vehicle_id)
                if commitment is not None:
                    if vehicle.destination!=commitment.destination:
                        raise ValueError('Passenger destination/event mismatch.')
                    nanoseconds=(pd.Timestamp(commitment.dropoff_at)-self.clock).value
                    if nanoseconds<=0:
                        raise ValueError('Due passenger event was not processed before clock advancement.')
                    vehicle.remaining_travel_time=nanoseconds/60e9
            remaining=(end-self.clock).value/60e9
            charging_times=[max(1e-9,(self.energy.charging_release_energy_kwh-v.energy_level)*60/(self.energy.charging_power_kw*self.energy.charging_efficiency)) for v in self.fleet.vehicles if v.current_action=='charging']
            delta=min([remaining]+[v.remaining_travel_time for v in busy]+charging_times)
            if delta<=0 or not np.isfinite(delta):raise ValueError('Invalid movement clock.')
            next_clock=end if delta==remaining else self.clock+pd.Timedelta(round(delta*60e9),unit="ns")
            arrivals=[]
            for vehicle in busy:
                commitment=self.passengers.get(vehicle.vehicle_id)
                if commitment is not None:
                    if pd.Timestamp(commitment.dropoff_at)<=next_clock:
                        # A float-timed hop can share the same nanosecond event
                        # boundary. Complete all passenger events due there,
                        # using Fleet's normal arrival transition exactly once.
                        vehicle.remaining_travel_time=delta
                        arrivals.append(vehicle.vehicle_id)
                    elif vehicle.remaining_travel_time<=delta:
                        raise ValueError('Future passenger event would complete before its timestamp.')
                elif vehicle.remaining_travel_time<=delta:
                    arrivals.append(vehicle.vehicle_id)
            prior_dest={v.vehicle_id:v.destination for v in busy}
            self.fleet.advance_time(delta)
            self.charging.advance_mini_slot(self.fleet.vehicles,delta,self.energy)
            self.clock=next_clock
            for vid in arrivals:
                v=self.fleet.vehicle(vid)
                if v.trip_status is not VehicleStatus.IDLE or v.current_grid!=prior_dest[vid]:raise ValueError('Arrival location/status mismatch.')
                if vid in self.passengers:self.passengers.pop(vid);completed+=1
                if vid in self.missions:self._continue_charging(v)
            validate_fleet(self.fleet.vehicles,range(142),self.fleet_size)
        return completed

    def route_idle(self):
        counts=np.zeros(9,int);charging=0
        for v in sorted(self.fleet.vehicles,key=lambda v:v.vehicle_id):
            if v.trip_status is not VehicleStatus.IDLE or v.vehicle_id in self.charging.vehicle_station:continue
            profile=self.profiles.loc[v.vehicle_id];g=v.current_grid
            s=RoutingState.from_producer(self.routing,self.operational,self.timestamp,g)
            decision=self.routing.decide(self.operational,self.timestamp,grid=g,energy_kwh=v.energy_level,minimum_energy_kwh=self.energy.battery_capacity_kwh*self.energy.charging_trigger_soc,p_min=profile.price_preference,w_max_minutes=profile.wait_preference,h_max_minutes=profile.charging_wait_preference_minutes,energy_per_km=self.energy.consumption_rate_kwh_per_km)
            label=self.routing.label(decision,g);counts[label]+=1
            observation=LocalPolicyObservation(s.values,label,s.mask,slot_id=self.slot_index)
            self.routing_experiences.append(observation)
            self.routing_experiences_by_vehicle.setdefault(v.vehicle_id,[]).append(observation)
            if decision.branch=='CHARGING':
                charging+=1;self.missions[v.vehicle_id]=decision.station_id;self._continue_charging(v)
            else:
                self.routing.start_next_hop(v,decision,speed_kmph=self.config['routing']['speed_kmph'],energy_per_km=self.energy.consumption_rate_kwh_per_km)
                if decision.action_index:v.current_action='repositioning'
        return counts,charging

    def run_slot(self,requests=None,*,terminal=False,train_dqn=False,routing_updates=(),routing_data_generation=False):
        t=self.timestamp;end=t+pd.Timedelta(minutes=30)
        if routing_data_generation:
            assert_training_update_allowed(t)
            if train_dqn or routing_updates:raise ValueError('Routing generation freezes pricing and routing weights.')
        if train_dqn or routing_updates:assert_training_update_allowed(t)
        if self.clock!=t:raise ValueError('Slot/clock mismatch.')
        if not (routing_data_generation and terminal):
            artifact_snapshots(end)  # No out-of-period terminal source for routing-only generation.
        requests=self.requests_for_slot() if requests is None else list(requests)
        if len({r.request_id for r in requests})!=len(requests):raise ValueError('Duplicate request IDs.')
        weather=pd.read_parquet(self.base/'demand_master_jan_mar_2026.parquet',columns=['GridID','WeatherCode'],filters=[('TimeSlot','==',t)]).set_index('GridID')
        if len(weather)!=142 or weather.index.duplicated().any():raise ValueError('Weather unavailable.')
        selected={};states={};od_rewards={};accepted=0;assigned=0;completed=0;assignment_times={}
        for request in requests:request.validate(range(142),15)
        for mini in range(15):
            for r in sorted((r for r in requests if r.request_time==mini),key=lambda r:(r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id)):
                offset=r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120
                completed+=self.advance_until(t+pd.Timedelta(seconds=offset))
                key=(r.origin_grid,r.destination_grid)
                if key not in selected:
                    states[key]=self.current_states.build(*key,t);selected[key]=self.dqn.select_action(states[key]) if not routing_data_generation else PricingAction(3,1.0,0.0,False);od_rewards[key]=0.
                action=selected[key];resolved=self.customer.resolve_parameters(float(weather.loc[r.origin_grid,'WeatherCode']),t.hour*2+t.minute//30)
                response=self.customer.evaluate_resolved(resolved,r.trip_distance_miles,action.pricing_factor)
                r.base_fare=response.p_base;r.pricing_factor=action.pricing_factor;r.offered_fare=response.p_dispatch;r.customer_accepted=response.accepted;r.customer_model='historical_sensitivity'
                r.weather_code=response.weather_code;r.period=response.period;r.historical_p_base=response.p_base;r.historical_d_base=response.d_base;r.epsilon_customer=response.epsilon_customer;r.p_max=response.p_max
                r.validate(range(142),15)
                if response.accepted:
                    accepted+=1
                    dispatch_requests([r],self.fleet,self.lookup,2,15,energy_parameters=self.energy,dispatch_model=DISPATCH_MODEL_LEGACY,slot_start_time=t.to_pydatetime())
                    if r.status is RequestStatus.ASSIGNED:
                        if r.assigned_vehicle_id in self.passengers or r.assigned_vehicle_id in self.missions:raise ValueError('Conflicting assignment.')
                        commitment=passenger_commitment(r,t)
                        self.passengers[r.assigned_vehicle_id]=replace(commitment,committed_at=self.clock,dropoff_at=self.clock+pd.Timedelta(minutes=r.trip_duration_minutes))
                        assignment_times[r.request_id]=self.clock
                        assigned+=1;od_rewards[key]+=r.offered_fare
            completed+=self.advance_until(t+pd.Timedelta(minutes=2*(mini+1)))
        outcomes=completed_request_outcomes(requests,t)
        outcomes=[replace(o,assigned_at=assignment_times[o.request_id]) if o.request_id in assignment_times else o for o in outcomes]
        reward=self.ledger.complete_slot(t,end,outcomes)
        if not np.isclose(reward,sum(od_rewards.values()),rtol=1e-12):raise ValueError('Reward reconciliation failed.')
        routing_counts,charging_decisions=self.route_idle()
        self.operational.complete_slot(slot_start=t,completed_at=end,requests=requests,charging_waits=charging_grid_observations(self.charging))
        federation=aggregate_policy_updates(routing_updates,round_index=self.slot_index)
        if federation.updated:self.policy.set_weights(federation.weights)
        self.timestamp=end;self.slot_index+=1
        if not (routing_data_generation and terminal):self.current_states=self._state_sources()
        replay_before=len(self.dqn.replay)
        if not routing_data_generation and training_update_allowed(t):
            for key,action in selected.items():self.dqn.store(states[key],action.action_index,od_rewards[key],self.current_states.build(*key,end),terminal)
        training=self.dqn.train_step() if train_dqn else None
        validate_fleet(self.fleet.vehicles,range(142),self.fleet_size)
        report=dict(timestamp=str(t),requests=len(requests),accepted=accepted,rejected=len(requests)-accepted,assigned=assigned,unmatched=accepted-assigned,reward=reward,completed=completed,transitions=len(self.dqn.replay)-replay_before,replay_size=len(self.dqn.replay),routing_actions=routing_counts.tolist(),charging_decisions=charging_decisions,fleet_size=self.fleet_size,unsupported_forecast_demand=sum(self.unsupported_demand.values()),federated_updates=federation.metadata.participating_updates,training=training,terminal=terminal)
        self.reports.append(report);return report

    def run(self,slot_count,*,train_dqn=False):
        if not isinstance(slot_count,int) or not 1<=slot_count<=8:raise ValueError('Short final runner requires 1..8 slots.')
        return [self.run_slot(terminal=i==slot_count-1,train_dqn=train_dqn) for i in range(slot_count)]


def run_production_preflight(root,slot_count,*,seed=42,driver_profiles=None):
    import time
    started=time.perf_counter()
    experiment=ProductionExperiment(root,seed=seed,driver_profiles=driver_profiles)
    experiment.run(slot_count)
    return experiment,time.perf_counter()-started


def write_preflight_artifacts(experiment,output_dir,runtime_seconds):
    output=Path(output_dir);output.mkdir(parents=True,exist_ok=True)
    trace=output/'runner_trace.csv';pd.DataFrame(experiment.reports).to_csv(trace,index=False)
    metadata=output/'runner_metadata.json'
    metadata.write_text(json.dumps(dict(grid_version='true_3km_v1',runtime_seconds=runtime_seconds,slots=len(experiment.reports),training_steps=experiment.dqn.training_steps),indent=2)+'\n')
    return trace,metadata
