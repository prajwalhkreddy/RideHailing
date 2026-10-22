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
    def checkpoint(self,path):
        fields=['fleet','charging','operational','ledger','passengers','missions','timestamp','clock','slot_index','request_id','experience_id','reports','unsupported_demand']
        data={k:getattr(self,k) for k in fields}
        data['request_rng_state']=self.request_rng.bit_generator.state;data['customer_rng_state']=self.customer.rng.bit_generator.state
        # Only the previous completed slot is needed by the causal pricing state.
        data['ledger'].completed={k:v for k,v in data['ledger'].completed.items() if k>=self.timestamp-pd.Timedelta(minutes=30)}
        temp=Path(str(path)+'.tmp');temp.write_bytes(pickle.dumps(data,protocol=5));temp.replace(path)
    def restore(self,path):
        data=pickle.loads(Path(path).read_bytes()) # Only this locally generated checkpoint is accepted.
        self.request_rng.bit_generator.state=data.pop('request_rng_state');self.customer.rng.bit_generator.state=data.pop('customer_rng_state')
        for k,v in data.items():setattr(self,k,v)
        if self.timestamp<pd.Timestamp('2026-03-16'):self.current_states=self._state_sources()

SCHEMA=pa.schema([('experience_id',pa.int64()),('driver_id',pa.int64()),('timestamp',pa.timestamp('ns')),('current_grid',pa.int64()),('state_169',pa.list_(pa.float32(),169)),('action_mask_9',pa.list_(pa.bool_(),9)),('label_action_0_to_8',pa.int64()),('decision_type',pa.string()),('event_offset_minutes',pa.float64())])

def generate(root,*,stop_after_slot=720):
    if not isinstance(stop_after_slot,int) or not 1<=stop_after_slot<=720:raise ValueError('Stop boundary must be 1..720 slots.')
    root=Path(root);data=root/'data/processed/routing_experiences_mar01_mar15_2026';out=root/'results/analysis/2026-10-21_simulator_derived_routing_policy'
    data.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    x=RoutingExperienceExperiment();cp=data/'generation_checkpoint.pkl'
    if cp.exists():x.restore(cp)
    completed=x.slot_index
    rows=pd.read_csv(out/'experience_generation_summary.csv').to_dict('records')[:completed] if (out/'experience_generation_summary.csv').exists() else []
    try:
        while x.slot_index<stop_after_slot:
            slot=x.slot_index;t=x.timestamp
            assert_training_update_allowed(t)
            report=x.run_slot(terminal=slot==719,routing_data_generation=True)
            assert len(x.dqn.replay)==0 and x.dqn.training_steps==0
            table=pa.Table.from_pylist(x.pending,schema=SCHEMA)
            target=data/f'slot_{slot:04d}.parquet';temp=target.with_suffix('.tmp');pq.write_table(table,temp,compression='zstd');temp.replace(target)
            counts={kind:sum(r['decision_type']==kind for r in x.pending) for kind in ['REPOSITION','EV_CHARGING_NEXT_HOP']}
            rows.append(dict(slot=slot,timestamp=str(t),requests=report['requests'],assignments=report['assigned'],routing_decisions=len(x.pending),charging_decisions=report['charging_decisions'],experiences=len(x.pending),**counts))
            x.pending.clear();x.charging_events.clear()
            pd.DataFrame(rows).to_csv(out/'experience_generation_summary.csv',index=False)
            daily=pd.DataFrame(rows);daily['day']=pd.to_datetime(daily.timestamp).dt.date;daily.groupby('day').agg(slots_completed=('slot','size'),requests=('requests','sum'),assignments=('assignments','sum'),routing_decisions=('routing_decisions','sum'),charging_decisions=('charging_decisions','sum'),experiences=('experiences','sum')).to_csv(out/'daily_generation_summary.csv')
            x.checkpoint(cp)
            print(json.dumps(dict(slot=slot+1,timestamp=str(t),requests=report['requests'],experiences=len(table),total_experiences=x.experience_id)),flush=True)
    except Exception as e:
        (out/'generation_status.json').write_text(json.dumps(dict(status='BLOCKED',completed_slots=x.slot_index if x.timestamp==x.clock else completed,last_valid_checkpoint=str(cp),error=f'{type(e).__name__}: {e}'),indent=2)+'\n')
        raise
    (out/'generation_status.json').write_text(json.dumps(dict(status='COMPLETE' if x.slot_index==720 else 'PAUSED_AT_REQUESTED_BOUNDARY',completed_slots=x.slot_index,timestamp=str(x.timestamp),experiences=x.experience_id,pricing_replay=0,pricing_optimizer_updates=0),indent=2)+'\n')
    return data
