"""Short real-interface integration; controlled requests, not performance data."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd,geopandas as gpd,yaml
from src.pricing.dqn_contract import (ROOT,FEATURES,Snapshot,DispatchLedger,PricingStateBuilder,behavioural_model,artifact_snapshots,passenger_commitment,completed_request_outcomes,incoming,mean_routing_response)
from src.rl.pricing_dqn import PricingDQN,ReplayBuffer,ACTIONS,action_index,bellman_targets
from src.routing.configuration import configured_interfaces
from src.routing.final_state import RoutingState
from src.routing.learning import load_final_policy,masked_softmax
from src.dispatch.request import RequestState,RequestStatus
from src.dispatch.dispatch import dispatch_requests,build_neighbour_lookup,DISPATCH_MODEL_LEGACY
from src.fleet.fleet import Fleet,validate_fleet
from src.fleet.state import VehicleState,VehicleStatus
from src.charging.energy import EnergyParameters


def run_fixture(forced_action=None):
    if forced_action is not None:forced_action=action_index(forced_action)
    mode='greedy' if forced_action is None else f'forced_{forced_action}'
    start=pd.Timestamp('2026-03-16 00:00');origins=(0,1,2);destinations={0:1,1:2,2:0};base=ROOT/'data/processed/spatial_3km_jan_mar_2026'
    cfg=yaml.safe_load((ROOT/'config/config.yaml').read_text());energy=EnergyParameters(**cfg['energy'])
    neighbours=pd.read_parquet(base/'neighbour_map.parquet');stations=pd.read_parquet(base/'charging_stations.parquet')
    producer,routing=configured_interfaces(gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet'),neighbours,stations,start)
    policy=load_final_policy(ROOT/'models/routing_policy/jan_mar_2026_3km_169x64x32x9/best.keras')
    dqn=PricingDQN.load(ROOT/'models/pricing_dqn/standalone_13x64x64x7_fixture');steps_before=dqn.training_steps
    # Isolated integration replay: never mix synthetic training checkpoint records.
    dqn.replay=ReplayBuffer(dqn.config.replay_capacity,42)
    customer=behavioural_model(np.random.default_rng(42),start)
    fleet=Fleet([VehicleState(i,g,VehicleStatus.IDLE,None,0,'idle',60.) for i,g in enumerate(origins)],frozenset(range(142)),2)
    lookup=build_neighbour_lookup(neighbours,range(142));ledger=DispatchLedger();ledger.complete_slot(start-pd.Timedelta(minutes=30),start,[])
    active=[];trace=[];details=[];vectors=[];reconciliation=[];conservation=[];request_id=0
    def build(t):
        forecast,pop=artifact_snapshots(t);probabilities={};masks={}
        for g in origins:
            s=RoutingState.from_producer(routing,producer,t,g)
            probabilities[g]=mean_routing_response([masked_softmax(policy(s.values[None,:],training=False).numpy()[0],s.mask)],s.mask);masks[g]=s.mask
        routing_snapshot=Snapshot(t,t,probabilities,t)
        commitments=[c for c in active if pd.Timestamp(c.dropoff_at)>t]
        result=PricingStateBuilder(forecast,ledger,commitments,routing_snapshot,pop,masks)
        expected=np.zeros(142,int)
        for c in commitments:
            v=fleet.vehicle(c.vehicle_id);assert v.trip_status is VehicleStatus.BUSY and v.destination==c.destination
            assert abs(v.remaining_travel_time-(pd.Timestamp(c.dropoff_at)-t).total_seconds()/60)<1e-8
            if t<pd.Timestamp(c.dropoff_at)<=t+pd.Timedelta(minutes=30):expected[c.destination]+=1
        np.testing.assert_array_equal(incoming(commitments,t),expected)
        return {g:result.build(g,destinations[g],t) for g in origins}
    states=build(start)
    for slot in range(4):
        t=start+pd.Timedelta(minutes=30*slot);end=t+pd.Timedelta(minutes=30)
        weather=pd.read_parquet(base/'demand_master_jan_mar_2026.parquet',columns=['TimeSlot','GridID','WeatherCode'],filters=[('TimeSlot','==',t)])
        if len(weather)!=142 or weather.GridID.duplicated().any():raise ValueError('Weather lookup unavailable.')
        period=t.hour*2+t.minute//30;requests=[];by_origin={};decisions={};assigned_ids=set()
        for g in origins:
            action=dqn.select_action(states[g],explore=False).action_index if forced_action is None else forced_action
            decisions[g]=action;resolved=customer.resolve_parameters(float(weather.set_index('GridID').loc[g,'WeatherCode']),period)
            group=[]
            for j,ratio in enumerate([1.,1.,.5]):
                distance=resolved.parameters.d_base*ratio
                result=customer.evaluate_resolved(resolved,distance,ACTIONS[action])
                r=RequestState(request_id,0,g,destinations[g],base_fare=result.p_base,pricing_factor=ACTIONS[action],offered_fare=result.p_dispatch,customer_accepted=result.accepted,
                    customer_model="historical_sensitivity",weather_code=result.weather_code,period=period,historical_p_base=result.p_base,historical_d_base=result.d_base,epsilon_customer=result.epsilon_customer,p_max=result.p_max,
                    source_trip_id=request_id,empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=40)).to_pydatetime(),trip_duration_minutes=40.,trip_distance_miles=distance,trip_distance_km=distance*1.609344)
                request_id+=1;group.append(r);requests.append(r)
                details.append(dict(mode=mode,timestamp=t,request_id=r.request_id,origin=g,destination=r.destination_grid,P_base=result.p_base,P_disp=result.p_dispatch,distance_miles=distance,E=result.epsilon_customer,threshold=result.p_max,accepted=result.accepted))
                assert result.p_dispatch==result.p_base*ACTIONS[action]
            by_origin[g]=group
        accepted=[r for r in requests if r.customer_accepted]
        dispatch_requests(accepted,fleet,lookup,40,15,energy_parameters=energy,dispatch_model=DISPATCH_MODEL_LEGACY,slot_start_time=t.to_pydatetime())
        for r in requests:
            assigned=r.status is RequestStatus.ASSIGNED
            if assigned:
                assert r.customer_accepted and r.assigned_vehicle_id not in assigned_ids
                assigned_ids.add(r.assigned_vehicle_id);v=fleet.vehicle(r.assigned_vehicle_id)
                assert v.trip_status is VehicleStatus.BUSY and v.destination==r.destination_grid
                active.append(passenger_commitment(r,t))
            elif not r.customer_accepted:assert r.assigned_vehicle_id is None
            details[-len(requests)+requests.index(r)].update(assigned=assigned,assigned_vehicle=r.assigned_vehicle_id,reward=r.offered_fare if assigned else 0.)
        for mini in range(15):
            now=t+pd.Timedelta(minutes=2*(mini+1))
            due=[c for c in active if pd.Timestamp(c.dropoff_at)==now]
            fleet.advance_mini_slot();validate_fleet(fleet.vehicles,range(142),3)
            for c in due:
                v=fleet.vehicle(c.vehicle_id);assert v.current_grid==c.destination and v.trip_status is VehicleStatus.IDLE
            conservation.append(dict(mode=mode,timestamp=str(now),vehicles=3,idle=sum(v.trip_status is VehicleStatus.IDLE for v in fleet.vehicles),busy=sum(v.trip_status is VehicleStatus.BUSY for v in fleet.vehicles)))
        reward=ledger.complete_slot(t,end,completed_request_outcomes(requests,t));independent=sum(r.offered_fare for r in requests if r.status is RequestStatus.ASSIGNED)
        assert reward==independent
        producer.complete_slot(slot_start=t,completed_at=end,requests=requests,charging_waits={})
        expected=np.bincount([r.origin_grid for r in requests if r.status is RequestStatus.ASSIGNED],minlength=142)
        np.testing.assert_array_equal(ledger.previous(end),expected)
        next_states=build(end)
        reconciliation.append(dict(mode=mode,timestamp=t,accepted=len(accepted),assigned=len(assigned_ids),rejected=len(requests)-len(accepted),unmatched=len(accepted)-len(assigned_ids),ledger_reward=reward,independent_reward=independent,difference=reward-independent))
        for g in origins:
            group=by_origin[g];od_reward=sum(r.offered_fare for r in group if r.status is RequestStatus.ASSIGNED);done=slot==3
            dqn.store(states[g],decisions[g],od_reward,next_states[g],done)
            state_id=f'{mode}_{slot}_{g}'
            trace.append(dict(mode=mode,timestamp=t,origin_grid=g,destination_grid=destinations[g],state_id=state_id,J_hat=states[g][0],J_disp_prev=states[g][1],incoming=states[g][2],pricing_action=decisions[g],pricing_factor=ACTIONS[decisions[g]],P_base=group[0].base_fare,P_disp=group[0].offered_fare,accepted_count=sum(bool(r.customer_accepted) for r in group),successful_dispatch_count=int(expected[g]),reward=od_reward,replay_size=len(dqn.replay),done=done))
            for which,vector in [('state',states[g]),('next_state',next_states[g])]:vectors.append(dict(state_id=state_id,kind=which,**dict(zip(FEATURES,vector))))
        states=next_states
    assert len(dqn.replay)==12 and sum(r[4] for r in dqn.replay.items)==3
    for r in list(dqn.replay.items)[-3:]:assert np.isclose(bellman_targets([r[2]],[r[4]],np.full((1,7),999.),.99)[0],r[2])
    assert dqn.training_steps==steps_before
    return dict(trace=trace,requests=details,states=vectors,reward=reconciliation,fleet=conservation,steps=steps_before,replay=12,mode=mode)
