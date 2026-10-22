#!/usr/bin/env python3
"""Run only the two-slot controlled migration fixture; never a real episode."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
from tests.test_final_production_runner import fixture_runner,fixture_requests
from src.simulation.final_production import validate_final_contract


def main():
    output=ROOT/'results/analysis/2026-10-21_hierarchical_runner_migration'
    output.mkdir(parents=True,exist_ok=True)
    protected=[ROOT/p for p in ['data/processed/grid_lookup.parquet','data/processed/grid_metadata.json','models/routing_policy/jan_mar_2026_3km_169x64x32x9/best.keras','results/analysis/2026-10-19_operational_grid_state/dqn_ready_forecasts.parquet','data/processed/customer_price_sensitivity_2026_01.parquet','data/processed/customer_price_sensitivity_fallback_2026_01.parquet','config/config.yaml']]
    def hashes():
        return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    before=hashes();x=fixture_runner()
    for slot in range(2):x.run_slot(fixture_requests(x,slot),terminal=slot==1,train_dqn=True)
    assert len(x.fleet.vehicles)==3 and len(x.dqn.replay)==4 and x.dqn.training_steps==0
    assert [r['assigned'] for r in x.reports]==[2,0]
    assert x.charging_events[-1]['timestamp']=='2026-03-16 00:42:00'
    assert before==hashes()
    pd.DataFrame(x.reports).to_csv(output/'runner_fixture_trace.csv',index=False)
    pd.DataFrame(x.charging_events).to_csv(output/'timed_charging_validation.csv',index=False)
    def save(name,data): (output/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    contract=dict(entrypoint='src.simulation.production.ProductionExperiment',implementation='src.simulation.final_production.ProductionExperiment',grid_version='true_3km_v1',grid_count=142,raster=[16,16],routing_architecture=[169,64,32,9],routing_status='PROVISIONAL_ROUTING_BASELINE',pricing_architecture=[13,64,64,7],pricing_actions=[.85,.90,.95,1.,1.05,1.10,1.15],main_slot_minutes=30,mini_slot_minutes=2,operational_coefficients=dict(alpha=.3,beta=.3,delta=.3,kappa=.3),F_hat_0=0,H_hat_0=0,passenger_acceptance='behavioural_E_threshold',reward='gross offered fare at accepted successful assignment',incoming='passenger commitments known before t, arrivals in (t,t+30min]',previous_dispatch='assignments in completed t-1',initial_dispatch='explicit empty pre-episode assignment history',request_generation='existing rounded nonnegative J_hat counts and intact empirical January trip sampling; unsupported origins reported',charging='timed shortest-path multi-hop selected-station arrival; FCFS queue; existing power and release settings',federation='existing sample-weighted aggregate_policy_updates at slot boundary; empty updates are no-op during this no-routing-training fixture',driver_H_max='explicit charging_wait_preference_minutes required; persisted profiles lack this field',normalization='identity',event_order=['published causal t sources','13D OD pricing state and DQN action','actual within-slot arrival offset','behavioural acceptance','FCFS dispatch and assignment reward','timed movement and trip completion; ongoing charging/queue events','utility routing/charging navigation decisions','completed-slot operational observations','existing FedAvg aggregation of explicit updates, if supplied','publish t+1 operational state','construct t+1 pricing state','store OD transition','optional DQN warm-up/training check'])
    save('runner_contract.json',contract)
    save('legacy_dependency_removal.json',dict(legacy_entrypoint='src.simulation.production.LegacyProductionExperiment',legacy_guard='retained in explicit legacy class; public final class independently validates contracts',replaced=['1213-grid domain','51x52 CNN tensor access','155-input/five-action policy assumptions','legacy context scaler','legacy fare-count/wait state','legacy model-path errors','zero-time ChargingInfrastructure.present_vehicle'],retained_semantics=['existing FCFS matching algorithm (legacy_fcfs_lowest_id names matching, not spatial/state adapter)','behavioural E customer model','January intact-trip generation','energy and station capacity settings'],zero_time_old_path='LegacyProductionExperiment -> run_main_slot -> ChargingInfrastructure.present_vehicle',final_path='ProductionExperiment.route_idle -> timed next-hop -> advance_until -> TimedChargingInfrastructure.admit_arrived',protected_sha256=before))
    meta=json.loads((ROOT/'data/processed/grid_metadata.json').read_text());checks={}
    for name,kw in [('routing155',dict(routing_input=155)),('routing5',dict(routing_output=5)),('pricing12',dict(pricing_input=12)),('wrong_actions',dict(pricing_actions=(1.,))),('zero_time_charging',dict(timed_charging=False)),('missing_operational',dict(operational_state=False))]:
        try:validate_final_contract(meta,**kw)
        except ValueError:checks[name]='REJECTED'
        else:raise AssertionError(name)
    for name,patch in [('legacy_grid',dict(valid_grid_count=1213)),('legacy_raster',dict(raster_rows=51,raster_columns=52))]:
        try:validate_final_contract(dict(meta,**patch))
        except ValueError:checks[name]='REJECTED'
        else:raise AssertionError(name)
    profiles=pd.read_parquet(ROOT/'data/processed/driver_preferences_seed42.parquet')
    missing='charging_wait_preference_minutes' not in profiles.columns
    save('startup_validation.json',dict(final_interface_fixture='PASS',compatibility_rejections=checks,fixture_slots=2,fixture_vehicles=3,fixture_requests=4,assigned=2,completed=2,replay_transitions=4,optimizer_updates=0,fixture_H_max_minutes=10,fixture_H_max_status='TEST_ONLY_NOT_PRODUCTION_APPROVAL',default_driver_profile_columns=list(profiles.columns),FINAL_HIERARCHICAL_RUNNER_READY='NO' if missing else 'YES',blocker='Approved charging_wait_preference_minutes (H_i_max) per-driver source/value is absent from persisted driver profiles.' if missing else None,protected_artifacts_unchanged=True,real_four_slot_episode_run=False))
    print(json.dumps(dict(reports=x.reports,charging=x.charging_events,production_H_max_missing=missing)))

if __name__=='__main__':main()
