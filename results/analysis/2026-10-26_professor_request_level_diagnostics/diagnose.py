"""One instrumented replay of the existing March16 greedy development fixture."""
from pathlib import Path
import sys,json,hashlib
from collections import deque
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.simulation.final_production import ProductionExperiment
import src.simulation.final_production as runner
from src.rl.pricing_dqn import ACTIONS,PricingAction
from src.dispatch.request import RequestStatus
from src.fleet.state import VehicleStatus
OUT=Path(__file__).resolve().parent
CP=ROOT/'models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4/dqn'
ROUTING=ROOT/'models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras'
STATUS=['ACTIVE_IMPLEMENTATION_DIAGNOSTIC','NOT_SOURCE_VALIDATED_ACCEPTANCE_ANALYSIS']
def save(n,v):(OUT/n).write_text(json.dumps(v,indent=2,default=str)+'\n')
def digest(x):return hashlib.sha256(b''.join(v.numpy().tobytes() for v in x)).hexdigest()
def model_state(x):return (digest(x.dqn.online.variables),digest(x.dqn.target.variables),digest(x.dqn.online.optimizer.variables),digest(x.policy.variables),x.dqn.training_steps,len(x.dqn.replay),json.dumps(x.dqn.rng.bit_generator.state),json.dumps(x.dqn.replay.rng.bit_generator.state))
def main():
 if (OUT/'request_level_diagnostics.parquet').exists():raise RuntimeError('Completed output exists; do not repeat simulation.')
 source=json.loads((ROOT/'results/analysis/2026-10-26_pricing_training_adequacy/march16_greedy_diagnostic.json').read_text())
 original=runner.artifact_snapshots
 def guarded(t):
  assert pd.Timestamp('2026-03-16')<=pd.Timestamp(t)<pd.Timestamp('2026-03-17')
  return original(t)
 runner.artifact_snapshots=guarded
 x=ProductionExperiment(start='2026-03-16',seed=42,dqn_checkpoint=CP,routing_checkpoint=ROUTING,frozen_routing=True);before=model_state(x)
 select=x.dqn.select_action
 def greedy(state,**kw):
  a=select(state,explore=False);return PricingAction(a.action_index,a.pricing_factor,0.,False)
 x.dqn.select_action=greedy
 def forbidden(*a,**kw):raise AssertionError('No replay insertion/optimizer updates permitted')
 x.dqn.store=forbidden;x.dqn.train_step=forbidden
 evaluate=x.customer.evaluate_resolved;pending=deque();observations={};rows=[]
 def observed_evaluate(resolved,distance,factor):
  r=pending.popleft();assert r.trip_distance_miles==distance
  locality={r.origin_grid,*x.lookup.get(r.origin_grid,())}
  count=sum(v.trip_status is VehicleStatus.IDLE and v.current_grid in locality for v in x.fleet.vehicles)
  observations[r.request_id]=dict(idle_candidate_count=int(count),timestamp=x.clock,lookup_level=resolved.fallback_level_used)
  return evaluate(resolved,distance,factor)
 x.customer.evaluate_resolved=observed_evaluate
 for slot in range(4):
  start=x.timestamp;req=x.requests_for_slot()
  signature=hashlib.sha256(repr([(r.request_id,r.origin_grid,r.destination_grid,r.request_time,r.trip_distance_miles,r.trip_duration_minutes) for r in req]).encode()).hexdigest()
  assert signature==source['request_signatures'][slot]
  ordered=sorted(req,key=lambda r:(r.request_time,r.empirical_within_slot_offset_seconds if r.empirical_within_slot_offset_seconds is not None else r.request_time*120,r.request_id));pending.extend(ordered)
  report=x.run_slot(req,terminal=slot==3,train_dqn=False);assert not pending and model_state(x)==before
  for r in req:
   assigned=r.status is RequestStatus.ASSIGNED;accepted=bool(r.customer_accepted);unmatched=accepted and not assigned
   minimum=float(x.profiles.loc[r.assigned_vehicle_id,'price_preference']) if assigned else None
   gate=bool(r.offered_fare>=minimum) if assigned and minimum is not None else None
   o=observations[r.request_id]
   rows.append(dict(request_id=r.request_id,timestamp=o['timestamp'],slot_timestamp=start,origin_grid=r.origin_grid,destination_grid=r.destination_grid,WeatherCode=r.weather_code,half_hour=r.period,sensitivity_lookup_level=o['lookup_level'],sampled_passenger_elasticity=r.epsilon_customer,P_base=r.historical_p_base,pricing_action_index=ACTIONS.index(r.pricing_factor),pricing_factor=r.pricing_factor,P_disp=r.offered_fare,trip_distance=r.trip_distance_miles,L_base=r.historical_d_base,P_max_current_implementation=r.p_max,passenger_accepted=accepted,passenger_rejected=not accepted,idle_candidate_count=o['idle_candidate_count'],assigned_vehicle_id=r.assigned_vehicle_id if assigned else None,assigned_driver_P_i_min=minimum,current_code_price_gate_pass=gate,assigned=assigned,unmatched=unmatched,final_outcome='ACCEPTED_ASSIGNED' if assigned else 'ACCEPTED_UNMATCHED' if unmatched else 'PASSENGER_REJECTED',unmatched_diagnostic='ZERO_LOCAL_IDLE_CANDIDATES' if unmatched and not o['idle_candidate_count'] else 'LOCAL_IDLE_EXISTED_OTHER_ELIGIBILITY_OR_FEASIBILITY_FAILURE' if unmatched else 'NOT_APPLICABLE'))
  print(json.dumps(dict(slot=slot+1,requests=report['requests'],accepted=report['accepted'],assigned=report['assigned'])),flush=True)
 f=pd.DataFrame(rows).sort_values(['timestamp','request_id']).reset_index(drop=True)
 assert len(f)==2838 and f.request_id.is_unique and f.timestamp.between(pd.Timestamp('2026-03-16'),pd.Timestamp('2026-03-16 02:00'),inclusive='left').all()
 formula=f.P_base+f.P_base*((f.trip_distance-f.L_base)/f.L_base)/f.sampled_passenger_elasticity
 assert np.allclose(formula,f.P_max_current_implementation,rtol=1e-12,atol=1e-12)
 inconsistent=int((f.passenger_accepted!=(f.P_disp<=f.P_max_current_implementation)).sum());assert inconsistent==0
 A=int(f.passenger_accepted.sum());D=int(f.assigned.sum());U=int(f.unmatched.sum());assert len(f)==A+f.passenger_rejected.sum() and A==D+U
 assert A==source['accepted'] and D==source['assignments'] and np.isclose(f.loc[f.assigned,'P_disp'].sum(),source['revenue'],rtol=1e-12)
 f['assigned_vehicle_id']=f.assigned_vehicle_id.astype('Int64');f['current_code_price_gate_pass']=f.current_code_price_gate_pass.astype('boolean');f.to_parquet(OUT/'request_level_diagnostics.parquet',index=False)
 def grouped(col):
  g=f.groupby(col,observed=True).agg(generated=('request_id','size'),accepted=('passenger_accepted','sum'),rejected=('passenger_rejected','sum'));g['acceptance_percentage']=100*g.accepted/g.generated;return g
 factors=grouped('pricing_factor').reindex(ACTIONS,fill_value=0);factors.loc[factors.generated.eq(0),'acceptance_percentage']=np.nan;factors.to_csv(OUT/'acceptance_by_pricing_factor.csv')
 grouped(['WeatherCode','half_hour']).to_csv(OUT/'acceptance_by_weather.csv')
 f['distance_bucket']=pd.cut(f.trip_distance,[0,1,3,5,10,np.inf],labels=['0–1 miles','>1–3 miles','>3–5 miles','>5–10 miles','>10 miles'],include_lowest=True)
 grouped('distance_bucket').to_csv(OUT/'acceptance_by_distance.csv')
 moments={}
 for key,mask in [('accepted',f.passenger_accepted),('rejected',f.passenger_rejected)]:
  z=f[mask];moments[key]=dict(elasticity_mean=float(z.sampled_passenger_elasticity.mean()),elasticity_median=float(z.sampled_passenger_elasticity.median()),P_disp_mean=float(z.P_disp.mean()),P_max_mean=float(z.P_max_current_implementation.mean()))
 save('acceptance_summary.json',dict(status=STATUS,fixture='Existing March16 greedy adequacy fixture; same final pricing checkpoint, fresh seed42 fleet/operational state, 4slots00:00–02:00, exact request signatures matched',generated=len(f),accepted=A,rejected=len(f)-A,acceptance_percentage=100*A/len(f),formula_decision_inconsistencies=inconsistent,independent_formula_recomputation='PASS',by_acceptance=moments,optimizer_updates_before=718,optimizer_updates_after=x.dqn.training_steps,model_optimizer_rng_unchanged=model_state(x)==before,protected_evaluation_accessed=False,simulations_run=1))
 unmatched=f[f.unmatched].unmatched_diagnostic.value_counts().to_dict()
 save('dispatch_summary.json',dict(status=STATUS,accepted=A,assigned=D,unmatched=U,identity_pass=True,unmatched_breakdown=unmatched,zero_idle_candidates=int(((f.unmatched)&(f.idle_candidate_count==0)).sum()),idle_candidates_existed=int(((f.unmatched)&(f.idle_candidate_count>0)).sum()),unresolved_from_diagnostics=0,idle_candidate_definition='At actual request arrival, before acceptance/dispatch: IDLE vehicles in origin or direct-neighbor grids. Does not apply energy/reserve or any nonexistent price gate.',revenue=float(f.loc[f.assigned,'P_disp'].sum())))
 known=f[f.assigned & f.assigned_driver_P_i_min.notna()];violations=known[known.P_disp<known.assigned_driver_P_i_min]
 save('driver_price_gate_counterfactual.json',dict(status=STATUS,assigned_checked=len(known),assigned_missing_P_i_min=D-len(known),satisfying=len(known)-len(violations),violating=len(violations),violation_percentage=100*len(violations)/len(known) if len(known) else None,driver_field='Persisted driver profile price_preference, used as P_i_min by existing routing utility; no dispatch gate added.',equality_passes=True,interpretation='Counterfactual check of actual selected assignments only; not a rerun estimating replacement drivers or corrected-policy outcomes.',example_request_ids=violations.request_id.head(5).tolist()))
 examples=[]
 for label,z in [('accepted_assigned',f[f.assigned]),('rejected',f[f.passenger_rejected]),('accepted_unmatched',f[f.unmatched]),('assigned_price_gate_violation',violations)]:
  z=z.head(5).copy();z.insert(0,'example_category',label);examples.append(z)
 pd.concat(examples).to_csv(OUT/'representative_requests.csv',index=False)
 print(json.dumps(dict(generated=len(f),accepted=A,rejected=len(f)-A,assigned=D,unmatched=U,gate_checked=len(known),gate_violations=len(violations),moments=moments)),flush=True)
if __name__=='__main__':main()
