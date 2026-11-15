# Full-day dynamic-value opportunity audit

Episode26 NOT_STARTED. March17–31 UNTOUCHED. No training, support rebuilding, clustering or baseline rerun occurred.

## Findings

The full-day screen contains **15,800** lower-than-highest choice decisions. Eligibility changes in **74.50%**; a different driver is selected with both branches assigned in **24.11%**; assignment success changes in **9.72%**. The latter two mutually exclusive categories total **33.82%**. Immediate assignment opportunities are therefore frequent, but beneficial downstream value is not established.

The 20 genuinely divergent rollouts comprise 17 driver-change and three outcome-change cases. All 20 still differ in vehicle locations/destinations and SOC at the final boundary, not merely in diagnostic caches. One case partially recovers revenue, one fully recovers, and **none is net-positive** at any observed horizon. Q ranks zero cases correctly against terminal undiscounted revenue (19 incorrect, one realized tie), and zero against discounted rewards (20 incorrect). Q-advantage versus net-revenue correlation is **−0.165**, descriptive only.

The two recovery cases are both T4 at 16:00. Request 38704 sacrifices $25.707328 initially and recovers the same amount: net zero within numerical tolerance. Request 37757 recovers $15.647939 of a $25.707328 sacrifice, leaving a $10.059389 loss. Both remain worse on discounted reward. This changes the earlier bounded-review evidence from NONE to **WEAK**, but does not justify simply extending training. **LONGER_TRAINING_RECOMMENDATION = NO** on the present evidence; Episode26 remains NOT_STARTED.

The deterministic sample covers hours 0, 4, 5, 6, 7 and 16; all four T/support groups; raw weather codes 3, 8 and 5; two demand quartiles and three supply quartiles. It does **not** cover the peak-demand quartile or every hour. Accordingly, the full-day immediate counts are comprehensive, while future-value findings are bounded and cannot establish population-wide dominance or rule out later benefits.

## Method

Stage A reconstructs the frozen Episode25 March16 greedy trajectory exactly once (73,754 requests). Every DQN action, epsilon and reward matches saved authoritative request evidence; the final fleet hash matches. For all lower-than-highest choice requests, both immediate outcomes are evaluated from the same live fleet using the existing read-only dispatcher selector and copied request price. Eligible sets include local/direct-neighbour idle supply satisfying battery, trip energy, destination reserve and driver-minimum-price constraints. The actual dispatch must match the lower-price prediction. Thus no different-trajectory baseline is used as a same-state substitute. Full pre-decision semantic state fingerprints are retained. Action indices 0–6 correspond respectively to factors 0.85,0.90,0.95,1.00,1.05,1.10,1.15; price differences and all revenue differences are DQN minus Highest Feasible in USD. Both actions use the same sampled epsilon and passenger acceptance threshold.

The future-value-blind selection rule retains up to five distinct hour/action-gap/type/weather strata per T group (maximum 20 genuine divergence cases), two eligibility-only comparisons and two identical-action controls. The last slot is screened but not selected because a full subsequent slot would cross the protected boundary. Snapshots are retained during Stage A; no counterfactual rollout begins until full-day reproduction passes. Demand/supply quartiles are descriptive qcut bins of all screened requests, with duplicate edges dropped; selection is chronological rather than outcome-favorable. Demand/supply and support coverage are reported for the selected cases, but there is no enforced demand/supply-quartile quota; early occurrences within each time group can be overrepresented. Sample fractions are not population prevalence estimates of beneficial value.

Stage B deep-copies mutable simulator state and RNGs; shares frozen models/support arrays read-only; changes only the focal action; then applies the same greedy model in both branches. Focal epsilon is reused without a second RNG draw. Unlike the earlier bounded review, tail reconstruction retains earlier within-slot request states, rewards and accounting, executes normal slot-end ledger/routing/operational updates, and continues one full next slot. Every unchanged DQN branch must reproduce the authoritative boundary fingerprints. Identical-action controls must match all observed horizons. H0 includes the focal request; H25/H100 add subsequent actionable requests where available. ONE_FULL_SLOT_AFTER_BOUNDARY also crosses the following boundary. No remaining-day rollouts are used.

## Full-day immediate opportunities

| Metric | Value |
|---|---|
| genuine_cases_with_any_observed_recovery | 2.0 |
| genuine_cases_with_any_observed_net_positive | 0.0 |
| assigned_driver_changed_both_assigned | 3809.0 |
| assigned_driver_changed_both_assigned_pct | 24.107595 |
| any_immediate_assignment_divergence_pct | 33.822785 |
| q_advantage_realized_value_correlation | -0.165246 |
| q_discounted_correct | 0.0 |
| q_discounted_incorrect | 20.0 |
| screened | 15800.0 |
| one_below | 11325.0 |
| two_or_more | 4475.0 |
| eligibility_changed | 11771.0 |
| eligibility_changed_pct | 74.5 |
| driver_changed | 5344.0 |
| driver_changed_pct | 33.822785 |
| outcome_changed | 1535.0 |
| outcome_changed_pct | 9.71519 |
| genuine_rollouts | 20.0 |
| persist_boundary | 20.0 |
| partial | 1.0 |
| full | 1.0 |
| net_positive | 0.0 |
| q_correct | 0.0 |
| q_incorrect | 19.0 |

Detailed breakdowns by T/hour/demand/supply/support/action gap are in opportunity_summary.csv. Driver-change counts include transitions to/from no assigned driver; outcome-change counts are a subset, not additive. Eligibility-only changes do not necessarily change the selected driver.

## Bounded downstream outcomes

| case_type | N | partial | full | net_positive | q_correct | q_incorrect |
|---|---|---|---|---|---|---|
| ASSIGNED_DRIVER_CHANGED | 17 | 0 | 0 | 0 | 0 | 17 |
| ASSIGNMENT_OUTCOME_CHANGED | 3 | 1 | 1 | 0 | 0 | 2 |
| CONTROL | 2 | 0 | 0 | 0 | 0 | 0 |
| DRIVER_ELIGIBILITY_SET_CHANGED_ONLY | 2 | 0 | 0 | 0 | 0 | 2 |

| case_type | median_recovery | median_net | best_net | worst_net |
|---|---|---|---|---|
| ASSIGNED_DRIVER_CHANGED | 0.0 | -4.47084 | -1.11771 | -110.653282 |
| ASSIGNMENT_OUTCOME_CHANGED | 15.647939 | -10.059389 | -0.0 | -20.118779 |
| CONTROL | 0.0 | 0.0 | 0.0 | 0.0 |
| DRIVER_ELIGIBILITY_SET_CHANGED_ONLY | -0.0 | -1.11771 | -1.11771 | -1.11771 |

Case-level summary recovery classifications use ONE_FULL_SLOT_AFTER_BOUNDARY; the horizon table also retains transient gains/losses and the counts table reports any observed recovery separately. Recovery = cumulative DQN-minus-highest revenue difference minus the immediate difference. PARTIAL means positive recovery with negative net; FULL means positive recovery and net zero within 1e-8 USD; NET_POSITIVE requires positive net beyond tolerance. NO_STATE_EFFECT means equal state without recovery; otherwise no recovery is STATE_DIFFERENCE_NO_RECOVERY. Discounted reward differences use gamma 0.99 per actionable request and are reported separately. Q-ranking correctness is provided against both undiscounted net revenue and discounted rewards; finite-horizon realized returns do not include a terminal value estimate. Reconvergence is checked at recorded horizons only; exact between-horizon time is unknown. The full state fingerprint includes routing caches/diagnostic fields, so location/destination, SOC, supply, commitment and routing columns must be read alongside it; routing_fingerprint_difference is an internal routing-state/cache comparison, not a count of changed routing actions; strict fingerprint persistence alone is not proof of meaningful operational persistence.

## Structural interpretation

Lower prices cannot expand driver eligibility under the implemented minimum-price test. Both compared actions are passenger-feasible, so lowering an already feasible price cannot improve passenger acceptance. Higher feasible price weakly expands eligible supply and increases conditional immediate fare; if dispatch succeeds at lower price it can succeed at higher price. It can select another driver, however, changing subsequent supply and routing. Successful fares also update grid-level mu and sigma in operational.complete_slot; routing consumes these quantities through U1. In the current slot order, routing precedes complete_slot, so the newly updated fare statistics can affect subsequent states/routing; this is one reason to retain the full following slot. Consequently, even an unchanged assigned driver can produce later operational-state differences through fare-dependent updates. The full-day screen identifies immediate assignment opportunities, not every possible delayed mechanism. The eligibility-only comparisons exercise this additional path but do not exhaustively cover same-driver requests. Therefore these immediate properties alone do not prove global mathematical dominance.

Only realized downstream recovery or net gain supports beneficial dynamic value. Q ranking and differing state are not sufficient. q_value_realized_value.csv retains Q differences and realized outcomes. A bounded deterministic selected sample cannot establish general policy optimality or unbiased average benefit.

## Validation and files

Focused tests cover cloned RNG/branch isolation, compilation of boundary-preserving runtime instrumentation, driver-set expansion/assigned-driver changes, and protected dates. Actual integration guards validate initial fingerprints, unchanged DQN boundary reproduction, identical-action controls and immutable fixture hash. Four infrastructure tests, four reporting tests and applicable 23/57/123/239 suites passed; logs and exact commands are retained. Source runtime and training artifacts were not modified.

Full screening: full_day_immediate_opportunity.csv and opportunity_summary.csv. Selection: selection_rule.json, selected_divergent_cases.csv. Branch data: routing_boundary_counterfactuals.csv, horizon_differences.csv, reconvergence_analysis.csv. Value: q_value_realized_value.csv, dynamic_value_summary.csv. Validation: stage_a_verification.json, test_results.txt, existing_tests.json, verification.json.

DYNAMIC_VALUE_OPPORTUNITY=MEANINGFUL

DYNAMIC_VALUE_EVIDENCE=WEAK

LONGER_TRAINING_RECOMMENDATION=NO

No automatic training extension. MEANINGFUL refers to immediate assignment-state opportunities, not established economic benefit. WEAK evidence means at least one sampled downstream recovery; it does not imply a net-profitable lower action. Longer training is not recommended solely from differing states; a conditional recommendation requires demonstrated net-positive sampled value. This finite, chronological sample does not prove global Highest Feasible dominance, and longer unobserved effects remain unresolved.
