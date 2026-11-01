"""One authorized four-slot combined validation; no optimization or training."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from src.simulation.final_production import ProductionExperiment
import src.simulation.final_production as runner
from src.rl.pricing_dqn import PricingAction
from src.dispatch.request import RequestStatus
from src.fleet.fleet import Fleet,validate_fleet
from src.fleet.state import VehicleStatus
O=Path(__file__).resolve().parent;R=O.parents[2]
def save(n,v):(O/n).write_text(json.dumps(v,indent=2,default=str)+'\n')
def digest(v):return hashlib.sha256(b''.join(x.numpy().tobytes() for x in v)).hexdigest()
def state(x):return (digest(x.dqn.online.variables),digest(x.dqn.target.variables),digest(x.dqn.online.optimizer.variables),digest(x.policy.variables),x.dqn.training_steps,len(x.dqn.replay))
def main():
 marker=O/'march16_started.json'
 if marker.exists():raise RuntimeError('Run already started; inspect existing evidence before any retry.')
 marker.write_text('{"runs_started":1}\n')
 old=json.loads((R/'results/analysis/2026-10-26_pricing_training_adequacy/march16_greedy_diagnostic.json').read_text())
 snapshots=runner.artifact_snapshots
 def guarded(t):
  assert pd.Timestamp('2026-03-16')<=pd.Timestamp(t)<pd.Timestamp('2026-03-17')
  return snapshots(t)
 runner.artifact_snapshots=guarded
 cp=R/'models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4/dqn'
 routing=R/'models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras'
 x=ProductionExperiment(start='2026-03-16',seed=42,dqn_checkpoint=cp,routing_checkpoint=routing,frozen_routing=True);before=state(x)
 select=x.dqn.select_action
 def greedy(s,**kw):
  a=select(s,explore=False);return PricingAction(a.action_index,a.pricing_factor,0.,False)
 x.dqn.select_action=greedy
 def forbidden(*a,**k):raise AssertionError('Training/replay updates prohibited')
 x.dqn.store=forbidden;x.dqn.train_step=forbidden
 advance=Fleet.advance_time;movement_checks=0
 def checked_advance(fleet,minutes):
  nonlocal movement_checks
  before={v.vehicle_id:(v.current_grid,v.destination,v.remaining_travel_time,v.trip_status) for v in fleet.vehicles}
  advance(fleet,minutes)
  for v in fleet.vehicles:
   g,d,t,status=before[v.vehicle_id]
   if v.current_grid!=g:
    assert status is VehicleStatus.BUSY and v.current_grid==d and t<=minutes+1e-9
   assert np.isfinite(v.energy_level) and v.energy_level>=0
  movement_checks+=1
 Fleet.advance_time=checked_advance
 rows=[];reports=[]
 for i in range(4):
  t=x.timestamp;requests=x.requests_for_slot()
  sig=hashlib.sha256(repr([(r.request_id,r.origin_grid,r.destination_grid,r.request_time,r.trip_distance_miles,r.trip_duration_minutes) for r in requests]).encode()).hexdigest()
  assert sig==old['request_signatures'][i]
  report=x.run_slot(requests,terminal=i==3,train_dqn=False);reports.append(report);assert state(x)==before
  validate_fleet(x.fleet.vehicles,range(142),5000)
  for r in requests:
   resolved=x.customer.resolve_parameters(r.weather_code,r.period);pool=x.customer.pool_for(resolved);assert np.any(pool==r.epsilon_customer)
   assigned=r.status is RequestStatus.ASSIGNED
   if assigned:assert r.offered_fare>=float(x.profiles.loc[r.assigned_vehicle_id,'price_preference'])
   rows.append(dict(request_id=r.request_id,slot_timestamp=str(t),WeatherCode=r.weather_code,Period=r.period,requested_context=[r.weather_code,r.period],resolved_context=[resolved.parameters.weather_code,resolved.parameters.period],fallback_level=resolved.fallback_level_used,epsilon=r.epsilon_customer,P_base=r.historical_p_base,D_base=r.historical_d_base,distance=r.trip_distance_miles,P_disp=r.offered_fare,P_max=r.p_max,accepted=r.customer_accepted,assigned=assigned))
  print(json.dumps(dict(slot=i+1,requests=report['requests'],accepted=report['accepted'],assigned=report['assigned'])),flush=True)
 f=pd.DataFrame(rows);assert len(f)==2838 and f.request_id.is_unique and np.isfinite(f.P_max).all()
 assert np.allclose(f.P_max,f.P_base*(1+(f.distance-f.D_base)/f.D_base/f.epsilon))
 assert (f.accepted==(f.P_disp<=f.P_max)).all()
 accepted=int(f.accepted.sum());assigned=int(f.assigned.sum());unmatched=accepted-assigned
 revenue=sum(z['reward'] for z in reports);assert np.isclose(revenue,f.loc[f.assigned,'P_disp'].sum(),rtol=1e-12)
 f.to_parquet(O/'march16_request_diagnostics.parquet',index=False)
 summary=dict(requests=len(f),accepted=accepted,rejected=len(f)-accepted,assigned=assigned,unmatched=unmatched,revenue=revenue,fleet_count=len(x.fleet.vehicles),charging_decisions=sum(z['charging_decisions'] for z in reports),charging_events=len(x.charging.events) if hasattr(x.charging,'events') else 'NOT_AVAILABLE',movement_checks=movement_checks,no_teleportation=True,no_negative_energy=True,accounting_pass=True,all_P_max_finite=True,all_draws_in_resolved_empirical_pool=True,driver_price_violations=0,optimizer_updates=0,models_unchanged=True,March17_31_untouched=True,slots_completed=4,setup='Existing seed42 greedy development setup; prior pricing/routing checkpoints used frozen as provenance, no optimization.')
 for k in ['price_ineligible_candidate_count','requests_with_any_price_ineligible_candidate','accepted_requests_unmatched_due_to_no_price_eligible_driver']:summary[k]=sum(z[k] for z in reports)
 save('march16_combined_validation.json',summary)
 a=f.P_max;stats=dict(mean=float(a.mean()),sample_SD=float(a.std(ddof=1)),min=float(a.min()),median=float(a.median()),max=float(a.max()),**{f'P{q}':float(a.quantile(q/100)) for q in [.1,.5,1,5,95,99]})
 save('march16_pmax_distribution.json',dict(old=dict(mean=25.6171775630085,sample_SD=167.77411131538014,median=19.770190593614135),new=stats,pass_criterion='Finite P_max and empirical pool membership; lower SD not required.'))
 pd.DataFrame([dict(factor=a,accepted=int((f.P_base*a<=f.P_max).sum()),rejected=int((f.P_base*a>f.P_max).sum()),acceptance_percentage=100*(f.P_base*a<=f.P_max).mean()) for a in [.85,.9,.95,1,1.05,1.1,1.15]]).to_csv(O/'march16_acceptance_by_factor.csv',index=False)
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
