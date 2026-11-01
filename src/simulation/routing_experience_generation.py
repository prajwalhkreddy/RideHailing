"""Resumable real routing-data collection; neutral behaviour pricing only."""
from pathlib import Path
import pickle,json,hashlib
import numpy as np,pandas as pd,pyarrow as pa,pyarrow.parquet as pq
from src.simulation.final_production import ProductionExperiment
from src.routing.final_state import RoutingState
from src.fleet.state import VehicleStatus
from src.simulation.temporal_protocol import assert_training_update_allowed

class RoutingExperienceExperiment(ProductionExperiment):
    def __init__(self,**kwargs):
        super().__init__(start='2026-03-01',seed=42,**kwargs)
        self.pending=[];self.experience_id=0;self.in_idle_decisions=False
        # Memoize identical published inputs within one boundary, without refitting.
        state_fn=self.routing.state;encode_fn=self.routing.encode
        state_cache={};encode_cache={}
        def state(producer,t):
            key=pd.Timestamp(t)
            if key not in state_cache:
                state_cache.clear();state_cache[key]=state_fn(producer,t)
            return state_cache[key]
        def encode(producer,t,g,*,expected_dimension=None):
            key=(pd.Timestamp(t),g,expected_dimension)
            if encode_cache and next(iter(encode_cache))[0]!=key[0]:encode_cache.clear()
            if key not in encode_cache:encode_cache[key]=encode_fn(producer,t,g,expected_dimension=expected_dimension)
            v,m=encode_cache[key];return v.copy(),m.copy()
        self.routing.state=state;self.routing.encode=encode
    def record(self,driver,g,state,label,kind):
        assert_training_update_allowed(self.timestamp)
        if self.timestamp>=pd.Timestamp('2026-03-16'):raise ValueError('Out-of-period experience.')
        if state.values.shape!=(169,) or state.mask.shape!=(9,) or not np.isfinite(state.values).all() or not 0<=label<9 or not state.mask[label]:raise ValueError('Invalid routing experience.')
        if np.any(state.values[:27].reshape(9,3)[~state.mask]!=0):raise ValueError('Invalid placeholder triple.')
        self.pending.append(dict(experience_id=self.experience_id,driver_id=driver,timestamp=self.timestamp,current_grid=g,state_169=state.values.tolist(),action_mask_9=state.mask.tolist(),label_action_0_to_8=label,decision_type=kind,event_offset_minutes=(self.clock-self.timestamp).total_seconds()/60))
        self.experience_id+=1
    def route_idle(self):
        origins={v.vehicle_id:(v.current_grid,v.energy_level<=self.energy.battery_capacity_kwh*self.energy.charging_trigger_soc) for v in self.fleet.vehicles if v.trip_status is VehicleStatus.IDLE}
        self.in_idle_decisions=True
        try:result=super().route_idle()
        finally:self.in_idle_decisions=False
        for vid,observations in self.routing_experiences_by_vehicle.items():
            for o in observations:
                g,charging=origins[vid];self.record(vid,g,RoutingState(o.state,o.action_mask),o.chosen_action_index,'EV_CHARGING_NEXT_HOP' if charging else 'REPOSITION')
        self.routing_experiences.clear();self.routing_experiences_by_vehicle.clear()
        return result
    def _continue_charging(self,v):
        g=v.current_grid
        state=RoutingState.from_producer(self.routing,self.operational,self.timestamp,g) if not self.in_idle_decisions else None
        super()._continue_charging(v)
        if state is not None and v.trip_status is VehicleStatus.BUSY:
            label=next(a for a,(dest,d) in self.routing.candidates(g).items() if dest==v.destination)
            self.record(v.vehicle_id,g,state,label,'EV_CHARGING_NEXT_HOP')
    def run_slot(self,requests=None,**kwargs):
        if not getattr(self,'final_behavioral_diagnostics',False):return super().run_slot(requests,**kwargs)
        from src.dispatch.request import RequestStatus
        from src.pricing.empirical_sensitivity import EmpiricalCustomerSensitivityModel
        if not isinstance(self.customer,EmpiricalCustomerSensitivityModel):raise ValueError('Final empirical sampler required.')
        requests=self.requests_for_slot() if requests is None else list(requests)
        idle=np.bincount([v.current_grid for v in self.fleet.vehicles if v.trip_status is VehicleStatus.IDLE],minlength=142)
        report=super().run_slot(requests,**kwargs)
        if report['requests']!=report['accepted']+report['rejected'] or report['accepted']!=report['assigned']+report['unmatched']:raise ValueError('Passenger accounting failed.')
        for r in requests:
            if r.pricing_factor!=1.:raise ValueError('Neutral generation pricing required.')
            if r.status is RequestStatus.ASSIGNED and r.offered_fare<float(self.profiles.loc[r.assigned_vehicle_id,'price_preference']):raise ValueError('Driver price gate violated.')
        e=np.array([r.epsilon_customer for r in requests]);pm=np.array([r.p_max for r in requests]);pb=np.array([r.historical_p_base for r in requests])
        if len(e) and (not np.isfinite(e).all() or np.any(e<=0) or not np.isfinite(pm).all()):raise ValueError('Invalid passenger numerical values.')
        report.update(epsilon_min=float(e.min()) if len(e) else None,
            epsilon_P0_1=float(np.quantile(e,.001)) if len(e) else None,
            epsilon_P1=float(np.quantile(e,.01)) if len(e) else None,
            epsilon_P5=float(np.quantile(e,.05)) if len(e) else None,
            epsilon_median=float(np.median(e)) if len(e) else None,
            P_max_min=float(pm.min()) if len(pm) else None,P_max_max=float(pm.max()) if len(pm) else None,
            P_max_above_2base=int((pm>2*pb).sum()),P_max_above_5base=int((pm>5*pb).sum()),
            driver_price_assignment_violations=0)
        by_grid={g:dict(timestamp=report['timestamp'],grid=g,requests=0,idle_at_slot_start=int(idle[g]),assignments=0,accepted_unserved=0) for g in range(142)}
        for r in requests:
            row=by_grid[r.origin_grid];row['requests']+=1
            row['assignments']+=int(r.status is RequestStatus.ASSIGNED)
            row['accepted_unserved']+=int(r.customer_accepted and r.status is not RequestStatus.ASSIGNED)
        report['grid_supply_diagnostics']=list(by_grid.values())
        return report

    def checkpoint(self,path):
        fields=['fleet','charging','operational','ledger','passengers','missions','timestamp','clock','slot_index','request_id','experience_id','reports','unsupported_demand','reserve_assignment_rejections','reserve_rejected_request_ids']
        data={k:getattr(self,k) for k in fields}
        data['reachability_contract']='EV_POST_MOVEMENT_STATION_REACHABILITY'
        data['behavioral_contract_identity']=getattr(self,'behavioral_contract_identity',None)
        data['reserve_reposition_rejections']=getattr(self.routing,'reserve_reposition_rejections',0)
        data['request_rng_state']=self.request_rng.bit_generator.state;data['customer_rng_state']=self.customer.rng.bit_generator.state
        # Only the previous completed slot is needed by the causal pricing state.
        data['ledger'].completed={k:v for k,v in data['ledger'].completed.items() if k>=self.timestamp-pd.Timedelta(minutes=30)}
        temp=Path(str(path)+'.tmp');temp.write_bytes(pickle.dumps(data,protocol=5));temp.replace(path)
    def restore(self,path):
        data=pickle.loads(Path(path).read_bytes()) # Only this locally generated checkpoint is accepted.
        if data.pop('reachability_contract',None)!='EV_POST_MOVEMENT_STATION_REACHABILITY':raise ValueError('Superseded pre-reachability checkpoint; clean initialization required.')
        if data.pop('behavioral_contract_identity',None)!=getattr(self,'behavioral_contract_identity',None):raise ValueError('Behavioral checkpoint contract mismatch.')
        self.routing.reserve_reposition_rejections=data.pop('reserve_reposition_rejections',0)
        self.request_rng.bit_generator.state=data.pop('request_rng_state');self.customer.rng.bit_generator.state=data.pop('customer_rng_state')
        for k,v in data.items():setattr(self,k,v)
        if self.timestamp<pd.Timestamp('2026-03-16'):self.current_states=self._state_sources()

SCHEMA=pa.schema([('experience_id',pa.int64()),('driver_id',pa.int64()),('timestamp',pa.timestamp('ns')),('current_grid',pa.int64()),('state_169',pa.list_(pa.float32(),169)),('action_mask_9',pa.list_(pa.bool_(),9)),('label_action_0_to_8',pa.int64()),('decision_type',pa.string()),('event_offset_minutes',pa.float64())])

def _atomic_json(path, value):
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,default=str)+'\n');temp.replace(path)

def generate(root,*,stop_after_slot=720,checkpoint_every_slots=8,resume=False,validation_only=False,final_behavioral=False):
    """Checkpoint is the commit authority; partitions beyond it are tentative."""
    import signal,fcntl
    if not isinstance(stop_after_slot,int) or not 1<=stop_after_slot<=720:raise ValueError('Stop boundary must be 1..720 slots.')
    if not isinstance(checkpoint_every_slots,int) or checkpoint_every_slots<1:raise ValueError('Positive checkpoint interval required.')
    root=Path(root)
    if final_behavioral:
        suffix='_validation' if validation_only else ''
        data=root/f'data/processed/routing_experiences_mar01_mar15_2026_final_behavioral{suffix}'
        out=root/'results/analysis/2026-10-29_final_behavioral_routing_generation'
        if validation_only:out=out/'prelaunch'
        if validation_only and stop_after_slot>2:raise ValueError('Final prelaunch capped at two clean slots.')
    elif validation_only:
        data=root/'data/processed/routing_experiences_reachability_short_validation';out=root/'results/analysis/2026-10-25_ev_station_reachability_contract/short_validation'
        if stop_after_slot>8:raise ValueError('Short validation is capped at eight slots.')
    else:
        data=root/'data/processed/routing_experiences_mar01_mar15_2026_reachability';out=root/'results/analysis/2026-10-25_routing_generation_reachability'
    data.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    lock=(data/'generation.lock').open('a')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close();raise RuntimeError('Another generation process holds the lock.')
    cp=data/'generation_checkpoint.pkl'
    if resume and not cp.exists():lock.close();raise FileNotFoundError('Resume checkpoint required.')
    if final_behavioral and not resume and (cp.exists() or any(data.glob('slot_*.parquet'))):
        lock.close();raise ValueError('Clean final launch refuses existing checkpoint/partitions; explicit resume required.')
    if final_behavioral:
        import os
        _atomic_json(data/'process.json',dict(pid=os.getpid(),namespace=str(data),resume=resume))
        temp=data/'generation.pid.tmp';temp.write_text(str(os.getpid())+'\n');temp.replace(data/'generation.pid')
    stop=[]
    def request_stop(signum,frame):stop.append(signum)
    handlers={sig:signal.signal(sig,request_stop) for sig in (signal.SIGINT,signal.SIGTERM)}
    x=None;committed=0;committed_time=None;committed_experiences=0
    try:
        x=RoutingExperienceExperiment()
        if final_behavioral:
            from src.pricing.empirical_sensitivity import EmpiricalCustomerSensitivityModel
            if not isinstance(x.customer,EmpiricalCustomerSensitivityModel):raise ValueError('Empirical passenger contract inactive.')
            files=['data/processed/passenger_empirical_absolute_epsilon_2026_01.parquet','data/processed/passenger_empirical_absolute_epsilon_2026_01.json','src/pricing/empirical_sensitivity.py','src/pricing/customer_sensitivity.py','src/dispatch/dispatch.py','src/simulation/final_production.py','data/processed/driver_preferences_seed42.parquet']
            x.behavioral_contract_identity={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files}
            x.final_behavioral_diagnostics=True
            _atomic_json(out/'active_upstream_identity.json',x.behavioral_contract_identity)
        if cp.exists():x.restore(cp)
        committed=x.slot_index;committed_time=x.timestamp;committed_experiences=x.experience_id
        if stop_after_slot<committed:raise ValueError('Requested stop precedes committed checkpoint.')
        # Reconcile summaries from checkpoint reports, never from an ahead-of-checkpoint CSV.
        rows=[];expected_id=0
        for i,r in enumerate(x.reports):
            f=pq.read_table(data/f'slot_{i:04d}.parquet',columns=['experience_id','decision_type','driver_id']).to_pandas()
            if not np.array_equal(f.experience_id.to_numpy(),np.arange(expected_id,expected_id+len(f))):raise ValueError('Duplicate or noncontiguous committed experience IDs.')
            expected_id+=len(f)
            c=f.decision_type.value_counts()
            rows.append(dict(slot=i,timestamp=r['timestamp'],requests=r['requests'],accepted=r['accepted'],rejected=r['rejected'],assignments=r['assigned'],accepted_unmatched=r['unmatched'],routing_decisions=len(f),charging_decisions=r['charging_decisions'],experiences=len(f),REPOSITION=int(c.get('REPOSITION',0)),EV_CHARGING_NEXT_HOP=int(c.get('EV_CHARGING_NEXT_HOP',0)),fleet_count=r['fleet_size']))
        if sum(r['experiences'] for r in rows)!=x.experience_id:raise ValueError('Checkpoint/partition count mismatch.')
        diagnostic_keys=['epsilon_min','epsilon_P0_1','epsilon_P1','epsilon_P5','epsilon_median','P_max_min','P_max_max','P_max_above_2base','P_max_above_5base','price_ineligible_candidate_count','requests_with_any_price_ineligible_candidate','accepted_requests_unmatched_due_to_no_price_eligible_driver','driver_price_assignment_violations']
        def publish(status):
            if final_behavioral:
                for row,report in zip(rows,x.reports):row.update({k:report.get(k) for k in diagnostic_keys})
                grid_rows=[item for report in x.reports for item in report.get('grid_supply_diagnostics',[])]
                tmp=out/'grid_slot_supply.csv.tmp';pd.DataFrame(grid_rows).to_csv(tmp,index=False);tmp.replace(out/'grid_slot_supply.csv')
            frame=pd.DataFrame(rows)
            tmp=out/'experience_generation_summary.csv.tmp';frame.to_csv(tmp,index=False);tmp.replace(out/'experience_generation_summary.csv')
            if len(frame):
                frame['day']=pd.to_datetime(frame.timestamp).dt.date
                daily=frame.groupby('day').agg(slots_completed=('slot','size'),requests=('requests','sum'),accepted=('accepted','sum'),rejected=('rejected','sum'),assignments=('assignments','sum'),accepted_unmatched=('accepted_unmatched','sum'),routing_decisions=('routing_decisions','sum'),charging_decisions=('charging_decisions','sum'),experiences=('experiences','sum'),REPOSITION=('REPOSITION','sum'),EV_CHARGING_NEXT_HOP=('EV_CHARGING_NEXT_HOP','sum'),fleet_count=('fleet_count','min'))
                if final_behavioral:
                    for key in ['P_max_above_2base','P_max_above_5base','price_ineligible_candidate_count','requests_with_any_price_ineligible_candidate','accepted_requests_unmatched_due_to_no_price_eligible_driver','driver_price_assignment_violations']:
                        daily[key]=frame.groupby('day')[key].sum()
                    daily['epsilon_min']=frame.groupby('day').epsilon_min.min()
                    daily['P_max_min']=frame.groupby('day').P_max_min.min();daily['P_max_max']=frame.groupby('day').P_max_max.max()
                tmp=out/'daily_generation_summary.csv.tmp';daily.to_csv(tmp);tmp.replace(out/'daily_generation_summary.csv')
            value=dict(status=status,completed_slots=x.slot_index,timestamp=str(x.timestamp),experiences=x.experience_id,fleet_count=len(x.fleet.vehicles),checkpoint_path=str(cp.relative_to(root)),checkpoint_every_slots=checkpoint_every_slots,pricing_replay=0,pricing_optimizer_updates=0,reserve_assignment_rejections=x.reserve_assignment_rejections,reserve_rejected_requests=len(x.reserve_rejected_request_ids),reserve_reposition_rejections=getattr(x.routing,'reserve_reposition_rejections',0))
            _atomic_json(out/'generation_checkpoint_manifest.json',dict(value,checkpoint_sha256=hashlib.sha256(cp.read_bytes()).hexdigest(),committed_partition_range=[0,x.slot_index-1],commit_authority='atomic generation_checkpoint.pkl; reconcile manifest from checkpoint on resume'))
            if final_behavioral:value.update(passenger_sampler='EMPIRICAL_WITH_REPLACEMENT',driver_price_gate=True,neutral_pricing_factor=1.0,namespace=str(data))
            _atomic_json(out/'generation_status.json',value)
            return value
        if not cp.exists():x.checkpoint(cp)
        publish('RUNNING')
        print(json.dumps(dict(event='RESUME',timestamp=str(x.timestamp),slots_completed=committed,experiences=x.experience_id,checkpoint_path=str(cp))),flush=True)
        while x.slot_index<stop_after_slot and not stop:
            slot=x.slot_index;t=x.timestamp
            assert_training_update_allowed(t)
            report=x.run_slot(terminal=slot==719,routing_data_generation=True)
            assert len(x.dqn.replay)==0 and x.dqn.training_steps==0
            table=pa.Table.from_pylist(x.pending,schema=SCHEMA)
            target=data/f'slot_{slot:04d}.parquet'
            # Only uncommitted crash remnants can exist here. Deterministic replay
            # must reproduce them exactly, never silently overwrite different data.
            if target.exists():
                if not pq.read_table(target).equals(table):raise ValueError(f'Uncommitted partition differs on replay: {target.name}')
            else:
                temp=target.with_suffix('.tmp');pq.write_table(table,temp,compression='zstd');temp.replace(target)
            counts={kind:sum(r['decision_type']==kind for r in x.pending) for kind in ['REPOSITION','EV_CHARGING_NEXT_HOP']}
            rows.append(dict(slot=slot,timestamp=str(t),requests=report['requests'],accepted=report['accepted'],rejected=report['rejected'],assignments=report['assigned'],accepted_unmatched=report['unmatched'],routing_decisions=len(x.pending),charging_decisions=report['charging_decisions'],experiences=len(x.pending),fleet_count=report['fleet_size'],**counts))
            x.pending.clear();x.charging_events.clear()
            if x.slot_index-committed>=checkpoint_every_slots or x.timestamp.date()!=t.date() or stop or x.slot_index==stop_after_slot:
                x.checkpoint(cp)
                committed=x.slot_index;committed_time=x.timestamp;committed_experiences=x.experience_id
                value=publish('COMPLETE' if committed==720 else 'PAUSED_ON_SIGNAL' if stop else 'PAUSED_AT_REQUESTED_BOUNDARY' if committed==stop_after_slot else 'RUNNING')
                print(json.dumps(dict(value,requests=sum(r['requests'] for r in rows),assignments=sum(r['assignments'] for r in rows))),flush=True)
        if stop and x.slot_index==committed:publish('PAUSED_ON_SIGNAL')
        elif x.slot_index==stop_after_slot:publish('COMPLETE' if committed==720 else 'PAUSED_AT_REQUESTED_BOUNDARY')
        return data
    except Exception as e:
        failure=dict(status='BLOCKED',completed_slots=committed,timestamp=str(committed_time),experiences=committed_experiences,last_valid_checkpoint=str(cp),error=f'{type(e).__name__}: {e}')
        _atomic_json(out/'generation_status.json',failure);print(json.dumps(failure),flush=True)
        raise
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
        fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
