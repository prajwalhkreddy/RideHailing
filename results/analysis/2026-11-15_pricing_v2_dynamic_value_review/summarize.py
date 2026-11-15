from pathlib import Path
import json
import numpy as np,pandas as pd
O=Path(__file__).resolve().parent
f=pd.read_csv(O/'counterfactual_outcomes.csv');cases=pd.read_csv(O/'selected_counterfactual_cases.csv');v=json.loads((O/'verification.json').read_text());assert v['status']=='PASS'
a=f[f.branch=='DQN'].set_index(['request_id','horizon']);b=f[f.branch=='HIGHEST'].set_index(['request_id','horizon']);assert a.index.equals(b.index)
rows=[]
for key,x in a.iterrows():
 y=b.loc[key];rid,h=key;immediate=float(x.immediate_reward-y.immediate_reward);net=float(x.revenue-y.revenue);recovery=net-immediate;different=x.state_hash!=y.state_hash
 label='NO_STATE_EFFECT' if not different else 'STATE_DIFFERENCE_NO_BENEFIT'
 if recovery>1e-8 and net< -1e-8:label='PARTIAL_RECOVERY'
 if recovery>1e-8 and abs(net)<=1e-8:label='FULL_RECOVERY'
 if net>1e-8:label='NET_POSITIVE_DYNAMIC_VALUE'
 rows.append(dict(request_id=rid,horizon=h,stratum=x.stratum,immediate_revenue_difference=immediate,recovery=recovery,net_revenue_difference=net,discounted_reward_difference=x.discounted_reward-y.discounted_reward,assignment_difference=x.assignments-y.assignments,unmatched_difference=x.unmatched-y.unmatched,immediate_driver_changed=str(x.immediate_driver)!=str(y.immediate_driver),immediate_assignment_changed=x.immediate_assignment!=y.immediate_assignment,state_difference=different,location_difference=x.location_hash!=y.location_hash,available_supply_difference=x.available_supply-y.available_supply,incoming_commitments_difference=x.incoming_commitments-y.incoming_commitments,charging_events_difference=x.charging_events-y.charging_events,routing_difference=x.routing_hash!=y.routing_hash,subsequent_assignments_changed=x.subsequent_drivers!=y.subsequent_drivers,rng_equal=x.rng_hash==y.rng_hash,classification=label))
r=pd.DataFrame(rows);r.to_csv(O/'horizon_summary.csv',index=False);last=r[r.horizon==100].copy();last['comparison_group']=np.where(last.stratum=='CONTROL','CONTROL',np.where(last.stratum=='ONE_BELOW','ONE_BELOW','TWO_OR_MORE_BELOW'))
agg=[]
for name,g in last.groupby('comparison_group'):
 allh=r[r.request_id.isin(g.request_id)]
 agg.append(dict(group=name,cases=len(g),changed_immediate_driver=int(g.immediate_driver_changed.sum()),changed_immediate_assignment=int(g.immediate_assignment_changed.sum()),any_state_difference=int(allh.groupby('request_id').state_difference.any().sum()),partial_recovery=int(g.classification.eq('PARTIAL_RECOVERY').sum()),full_recovery=int(g.classification.eq('FULL_RECOVERY').sum()),net_positive=int(g.classification.eq('NET_POSITIVE_DYNAMIC_VALUE').sum()),median_immediate_sacrifice=float(-g.immediate_revenue_difference.median()),median_recovery=float(g.recovery.median()),median_net=float(g.net_revenue_difference.median()),best_net=float(g.net_revenue_difference.max()),worst_net=float(g.net_revenue_difference.min())))
agg=pd.DataFrame(agg);agg.to_csv(O/'aggregate_dynamic_value.csv',index=False)
q=cases.merge(last,on=['request_id','stratum']);q['q_difference']=q.q_dqn-q.q_highest;q.to_csv(O/'q_value_vs_realized_value.csv',index=False)
controls=r[r.stratum=='CONTROL'];assert not controls.state_difference.any() and controls.net_revenue_difference.eq(0).all() and controls.rng_equal.all()
tests=json.loads((O/'existing_tests.json').read_text());assert all(x['exit_code']==0 for x in tests)
v.update(dynamic_value_evidence='NONE' if not last[last.stratum!='CONTROL'].recovery.gt(1e-8).any() else 'WEAK',longer_training_recommendation='CONDITIONAL',matched_control_horizon_checks=len(controls),existing_test_suites=tests,limitations=['Only first March16 slot and initial fleet','No slot-boundary routing decisions','No inference about longer horizons or other weather/time conditions'])
(O/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
def table(x):return '| '+' | '.join(x.columns)+' |\n|'+'|'.join(['---']*len(x.columns))+'|\n'+'\n'.join('| '+' | '.join(str(y) for y in row)+' |' for row in x.itertuples(index=False,name=None))+'\n'
text='''# Episode25 state-matched dynamic-value review

Training remains stopped; Episode26 NOT_STARTED. March17–31 untouched. This diagnostic does not modify production, training, sensitivity supports, the fixture or historical evaluations.

## Design and scope

No exact simulator snapshots were persisted. A single prefix of the frozen March16 Episode25 greedy trajectory was reconstructed from its original initial fleet, weather, epsilon generator and checkpoint. Every prefix action, epsilon and immediate reward was checked against the saved authoritative records. No Highest Feasible baseline or full day was rerun.

Selection was frozen before outcomes: within the first30-minute slot, select up to four evenly spaced chronological cases in each rank-below-highest stratum and two choice-request controls, requiring100 later requests in the same slot. Only one two-below and one three-plus case satisfy this bounded frame. Six divergence cases and two controls were studied. This initial-fleet/T1 sample is deliberately small and cannot establish behavior across dayparts, congested later states or routing boundaries. Demand/supply/Q-margin/outcome selection was not used. All-day divergence metadata is in all_divergence_candidates.csv; unknown DQN driver IDs and full simulator fingerprints outside the reconstructed sample remain missing.

## State-matched implementation

The diagnostic constructs instrumented functions from the actual runtime method, adding pre/post-request callbacks only. Production source is unchanged and its SHA256 is frozen in selection_rule.json. Immediately before the focal action, the environment and remaining request context are deep-copied independently for each branch. Frozen models and empirical support arrays are shared read-only; fleet, commitments, charging, operational/routing mutable state and RNGs are copied. Semantic physical-state fingerprints and provider RNG fingerprints match before branching; parent fingerprints remain unchanged afterward. Only the focal action is overridden. The already-drawn focal epsilon is reused without advancing its RNG twice. Subsequent actions use the same greedy Episode25 model on each branch state, with common exogenous requests and epsilon stream.

H0 includes the focal request; H1/H5/H25/H100 add that many subsequent actionable requests. Movement and charging advance at the existing event/mini-slot times. The final observation stops immediately after request100; it does not run the next slot-boundary routing decision. Routing-state differences within these horizons therefore cannot establish future routing benefits. Copy-isolation checks and identical-action controls validate the actual replay path.

## Quantitative definitions

All differences are DQN minus focal Highest Feasible. Immediate sacrifice is negative immediate revenue difference (actual dispatch revenue, not merely offered fare). Recovery=net cumulative revenue difference−immediate revenue difference. Tolerance1e-8 USD handles numerical equality only.

NO_STATE_EFFECT: physical simulator states match and no positive recovery. STATE_DIFFERENCE_NO_BENEFIT: states differ without positive recovery. PARTIAL_RECOVERY: positive recovery but net remains negative. FULL_RECOVERY: positive recovery and net is zero within tolerance. NET_POSITIVE_DYNAMIC_VALUE: net exceeds tolerance. These outcome classes are descriptive, not invalidity/cleaning rules. Physical state excludes historical accumulated reward and audit lists, so operational reconvergence can occur despite an enduring revenue gap. Discounted rewards use gamma0.99 per actionable request. Classification uses undiscounted revenue; discounted differences are reported separately.

## H100 results

'''+table(agg)+'\n## Case-level Q and outcomes\n\n'+table(q[['request_id','stratum','q_dqn','q_highest','q_difference','immediate_revenue_difference','recovery','net_revenue_difference','classification']])
text+='''
## Interpretation and limits

The bounded outcomes do not justify treating policy differences as demonstrated long-term benefit. Inspect horizon_summary.csv for any transient state differences and recovery, rather than only terminal fingerprints. No population proportion is inferred from six divergence cases. Positive Q preference for a lower action is not itself realized dynamic value; q_value_vs_realized_value.csv shows the measured comparison. There is no evidence here sufficient to establish a reliable Q ranking of beneficial downstream effects.

Longer training recommendation: CONDITIONAL. Review broader state coverage and at least one routing-boundary horizon before attributing a dynamic advantage or approving longer training. This review neither proves that dynamic value is impossible nor changes the previous full-day finding that Highest Feasible outperformed Episode25. The current research conclusion is unchanged, so root/current-state documentation is not rewritten.

## Validation and artifacts

Focused tests cover deep-copy/RNG isolation, instrumentation compilation and protected-date guards. Actual integration assertions cover identical initial states, parent nonmutation, immutable fixture hash, exact prefix replay, one focal intervention and two identical-action control replays across all five horizons. Relevant existing suites are recorded in existing_tests.json and tests_*.txt. No optimizer or replay training updates occur.

Files: selected_counterfactual_cases.csv; all_divergence_candidates.csv; selection_rule.json; state_match_verification.csv; counterfactual_outcomes.csv; horizon_summary.csv; q_value_vs_realized_value.csv; aggregate_dynamic_value.csv; test_results.txt; verification.json. Driver differences, subsequent assignment signatures, location/supply/commitment/charging/routing differences and discounted revenue differences are available in the horizon tables. Assigned-driver signatures preserve deterministic comparisons but are not a complete exported vehicle trajectory.

'''+f"DYNAMIC_VALUE_EVIDENCE={v['dynamic_value_evidence']}\n\nLONGER_TRAINING_RECOMMENDATION=CONDITIONAL\n\nEPISODE26=NOT_STARTED\n"
(O/'README.md').write_text(text)
print(agg.to_string(index=False));print(v['dynamic_value_evidence'])
