# Episode25 state-matched dynamic-value review

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

| group | cases | changed_immediate_driver | changed_immediate_assignment | any_state_difference | partial_recovery | full_recovery | net_positive | median_immediate_sacrifice | median_recovery | median_net | best_net | worst_net |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CONTROL | 2 | 0 | 0 | 0 | 0 | 0 | 0 | -0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ONE_BELOW | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 1.11770992211952 | 1.7763568394002505e-14 | -1.1177099221195022 | -1.1177099221192748 | -1.1177099221195022 |
| TWO_OR_MORE_BELOW | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2.7942748052988087 | 5.3290705182007514e-14 | -2.7942748052987554 | -2.2354198442390043 | -3.3531297663585065 |

## Case-level Q and outcomes

| request_id | stratum | q_dqn | q_highest | q_difference | immediate_revenue_difference | recovery | net_revenue_difference | classification |
|---|---|---|---|---|---|---|---|---|
| 2 | ONE_BELOW | 169.53175354003906 | 169.0518035888672 | 0.479949951171875 | -1.11770992211952 | 1.7763568394002505e-14 | -1.1177099221195022 | NO_STATE_EFFECT |
| 663 | CONTROL | 129.26776123046875 | 129.26776123046875 | 0.0 | 0.0 | 0.0 | 0.0 | NO_STATE_EFFECT |
| 531 | ONE_BELOW | 140.96746826171875 | 140.3028106689453 | 0.6646575927734375 | -1.11770992211952 | 1.7763568394002505e-14 | -1.1177099221195022 | NO_STATE_EFFECT |
| 921 | ONE_BELOW | 152.84674072265625 | 150.9054412841797 | 1.9412994384765625 | -1.11770992211952 | 2.4513724383723456e-13 | -1.1177099221192748 | NO_STATE_EFFECT |
| 0 | TWO_BELOW | 135.9452362060547 | 135.40953063964844 | 0.53570556640625 | -2.235419844239047 | 4.263256414560601e-14 | -2.2354198442390043 | NO_STATE_EFFECT |
| 987 | THREE_PLUS | 100.17749786376952 | 100.05280303955078 | 0.12469482421873579 | -3.3531297663585704 | 6.394884621840902e-14 | -3.3531297663585065 | NO_STATE_EFFECT |
| 559 | ONE_BELOW | 150.07179260253906 | 148.63467407226562 | 1.4371185302734375 | -1.11770992211952 | 1.7763568394002505e-14 | -1.1177099221195022 | NO_STATE_EFFECT |
| 595 | CONTROL | 129.26776123046875 | 129.26776123046875 | 0.0 | 0.0 | 0.0 | 0.0 | NO_STATE_EFFECT |

## Interpretation and limits

The bounded outcomes do not justify treating policy differences as demonstrated long-term benefit. Inspect horizon_summary.csv for any transient state differences and recovery, rather than only terminal fingerprints. No population proportion is inferred from six divergence cases. Positive Q preference for a lower action is not itself realized dynamic value; q_value_vs_realized_value.csv shows the measured comparison. There is no evidence here sufficient to establish a reliable Q ranking of beneficial downstream effects.

Longer training recommendation: CONDITIONAL. Review broader state coverage and at least one routing-boundary horizon before attributing a dynamic advantage or approving longer training. This review neither proves that dynamic value is impossible nor changes the previous full-day finding that Highest Feasible outperformed Episode25. The current research conclusion is unchanged, so root/current-state documentation is not rewritten.

## Validation and artifacts

Focused tests cover deep-copy/RNG isolation, instrumentation compilation and protected-date guards. Actual integration assertions cover identical initial states, parent nonmutation, immutable fixture hash, exact prefix replay, one focal intervention and two identical-action control replays across all five horizons. Relevant existing suites are recorded in existing_tests.json and tests_*.txt. No optimizer or replay training updates occur.

Files: selected_counterfactual_cases.csv; all_divergence_candidates.csv; selection_rule.json; state_match_verification.csv; counterfactual_outcomes.csv; horizon_summary.csv; q_value_vs_realized_value.csv; aggregate_dynamic_value.csv; test_results.txt; verification.json. Driver differences, subsequent assignment signatures, location/supply/commitment/charging/routing differences and discounted revenue differences are available in the horizon tables. Assigned-driver signatures preserve deterministic comparisons but are not a complete exported vehicle trajectory.

DYNAMIC_VALUE_EVIDENCE=NONE

LONGER_TRAINING_RECOMMENDATION=CONDITIONAL

EPISODE26=NOT_STARTED

## Direct answer

Across6 lower-action cases,0 changed the assigned driver,0 changed immediate assignment success,0 changed the fingerprinted operational state at any measured horizon,0 recovered sacrifice and0 had net positive value. Four one-below cases each lost$1.117710; the two larger-gap cases lost$2.235420 and$3.353130, respectively. Losses persisted through H100; only floating-point residuals below1e-8 appeared in recovery. Q differences favored the lower action in all6 cases (range 0.124695–1.941299), opposite the measured revenue advantage. Both controls were identical. There is no demonstrated beneficial dynamic value in this sample. Whether credible value exists elsewhere remains unresolved.

Tests:3 focused new tests plus existing suites[23, 57, 123, 239],zero failures/errors;10 identical-action integration horizon checks. No production changes.
