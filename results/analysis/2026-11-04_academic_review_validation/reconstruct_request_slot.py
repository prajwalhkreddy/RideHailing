from pathlib import Path
import os,json,pickle,random,hashlib
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import numpy as np,pandas as pd
from src.simulation.multiepisode_pricing import reset,FIELDS,FINAL,OUT,sha,RID
from src.rl.pricing_dqn import PricingDQN,ACTIONS
from src.fleet.state import VehicleStatus
from src.charging.energy import requires_charging,energy_consumed_kwh
from src.dispatch.request import RequestStatus
R=Path('results/analysis/2026-11-04_academic_review_validation')
if (R/'request_fixture_provenance.json').exists():
 raise SystemExit('Completed reconstruction already exists; reuse it instead of rerunning.')
cp=FINAL/'episode_0025/checkpoint_0008_98717f4d'
meta=json.loads((cp/'manifest.json').read_text())
for f,h in meta['files'].items():assert sha(cp/f)==h
state=pickle.loads((cp/'simulator.pkl').read_bytes())
spec=json.loads((OUT/'episode_protocol.json').read_text())['starts'][24]
print('RESTORE',spec,flush=True)
x=reset(spec,None)
for k in FIELDS:setattr(x,k,state[k])
x.dqn=PricingDQN.load(cp/'dqn')
x.request_rng.bit_generator.state=state['request_rng'];x.customer.rng.bit_generator.state=state['customer_rng'];random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng']);x.routing.reserve_reposition_rejections=state['reserve_reposition_rejections'];x.od=None;x.current_states=x._state_sources()
assert x.dqn.training_steps==3128 and x.slot_index==8
weights=[a.copy() for a in x.dqn.online.get_weights()]
t=x.timestamp;requests=x.requests_for_slot()
ordered=sorted(requests,key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id))
obs={};counter=[0];cls=type(x.customer);orig=cls.evaluate_resolved

def observed(self,*a,**kw):
 response=orig(self,*a,**kw)
 r=ordered[counter[0]];counter[0]+=1
 grids={r.origin_grid,*x.lookup.get(r.origin_grid,())}
 energy=energy_consumed_kwh(r.trip_distance_km,x.energy);reserve=x.station_reserve(r.destination_grid)
 candidates=[v for v in x.fleet.vehicles if v.current_grid in grids and v.trip_status is VehicleStatus.IDLE and not requires_charging(v,x.energy) and v.energy_level>=energy and v.energy_level-energy>=reserve]
 eligible=sum(response.p_dispatch>=float(x.profiles.loc[v.vehicle_id,'price_preference']) for v in candidates)
 obs[r.request_id]={'nonprice_feasible_driver_count':len(candidates),'price_eligible_driver_count':eligible}
 return response
cls.evaluate_resolved=observed
print('REPLAY_SLOT',str(t),'REQUESTS',len(requests),flush=True)
try:report=x.run_slot(requests=requests,train_dqn=False,explore_pricing=True)
finally:cls.evaluate_resolved=orig
assert counter[0]==len(requests) and x.dqn.training_steps==3128
for a,b in zip(weights,x.dqn.online.get_weights()):np.testing.assert_array_equal(a,b)
ptr=json.loads((FINAL/'episode_0025/CURRENT.json').read_text())
finished=pickle.loads((FINAL/'episode_0025'/ptr['directory']/'simulator.pkl').read_bytes())
expected=finished['reports'][8]
compare={k:report[k]==v for k,v in expected.items() if k in report}
if not all(compare.values()):
 (R/'replay_failure.json').write_text(json.dumps({'expected':expected,'observed':report,'comparison':compare},indent=2,default=str));raise AssertionError(compare)
rows=[]
for r in requests:
 o=obs[r.request_id];accepted=bool(r.customer_accepted);assigned=r.status is RequestStatus.ASSIGNED
 outcome='PASSENGER_REJECTED' if not accepted else 'PASSENGER_ACCEPTED_ASSIGNED' if assigned else 'PASSENGER_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER' if o['nonprice_feasible_driver_count']>0 and o['price_eligible_driver_count']==0 else 'PASSENGER_ACCEPTED_OTHER_UNMATCHED'
 rows.append(dict(Episode_ID=25,Slot_ID=9,Timestamp=str(t),Request_ID=r.request_id,Origin_Grid_ID=r.origin_grid,Destination_Grid_ID=r.destination_grid,epsilon_used=r.epsilon_customer,P_base_USD=r.historical_p_base,trip_distance_miles_RAW=r.trip_distance_miles,trip_distance_km=r.trip_distance_km,L_GG_km=r.trip_distance_km,runtime_L_base_km=r.historical_d_base*1.609344,historical_global_L_base_km=3.01799878914405*1.609344,distance_difference_km=(r.trip_distance_miles-r.historical_d_base)*1.609344,relative_distance_deviation=(r.trip_distance_miles-r.historical_d_base)/r.historical_d_base,P_max_USD=r.p_max,DQN_action_index=ACTIONS.index(r.pricing_factor),pricing_factor=r.pricing_factor,P_offer_USD=r.offered_fare,recorded_passenger_decision='ACCEPT' if accepted else 'REJECT',recomputed_passenger_decision='ACCEPT' if r.offered_fare<=r.p_max else 'REJECT',any_price_eligible_driver=o['price_eligible_driver_count']>0,successful_assignment=assigned,unmatched_reason=outcome,**o))
f=pd.DataFrame(rows)
assert (f.recorded_passenger_decision==f.recomputed_passenger_decision).all()
f.to_csv(R/'request_level_pricing_full.csv',index=False)
source={'episode':25,'slot':9,'timestamp':str(t),'checkpoint':str(cp.relative_to(Path.cwd())) if cp.is_absolute() else str(cp),'environment_seed':spec['environment_seed'],'learner_seed':42,'optimizer_updates_at_slot_start':3128,'epsilon':meta['epsilon'],'pricing_mode':'epsilon_greedy','saved_report_match':compare,'report':report,'original_report':expected,'no_optimizer_updates':True,'weights_unchanged':True,'checkpoint_files_unchanged':all(sha(cp/f)==h for f,h in meta['files'].items())}
(R/'request_fixture_provenance.json').write_text(json.dumps(source,indent=2,default=str)+'\n')
print('COMPLETE',len(f),report,flush=True)
