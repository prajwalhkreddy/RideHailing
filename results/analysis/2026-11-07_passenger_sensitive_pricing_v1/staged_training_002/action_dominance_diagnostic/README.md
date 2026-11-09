# Passenger-Sensitive Pricing V1: bounded action-dominance diagnostic

**ACTION_DOMINANCE_RISK=HIGH**; **DQN_ADDS_NONTRIVIAL_DYNAMIC_VALUE=UNRESOLVED**; recommendation **METHODOLOGY_REVIEW**. No training or methodology change.

## Scope and reproducibility

Episode25 saved development actions are the first evidence. Four sequential, inference-only policies use the exact fixed March16 00:00–02:00 fixture: environment/provider seed424242, 2,838 requests each, 5,000 vehicles, four slots. Request IDs/order/timestamps/OD/distance/epsilon sequences match across all runs. DQN replay reproduces saved Episode25 actions, assignment count and revenue. Checkpoint SHA256 and complete learner fingerprint (online/target/optimizer/replay/RNG/counter) remain unchanged. No updates, replay writes, checkpoint saves or protected March17–31 access. In-memory diagnostic selectors/hooks do not edit source files or change production behavior. The real dispatcher advances each sequential policy once; alternative arms are inspected read-only before that dispatch.

## Structural findings

1. **Passenger monotonicity YES**: `src/pricing/passenger_sensitive_v1.py:34` uses `candidate_price <= P_accept`; `src/simulation/passenger_sensitive_v1.py` rejects any above-threshold selection and sets accepted=True for offered feasible requests. Both feasible arms are accepted by construction; no residual stochastic demand response exists within that mask.
2. **Driver eligibility monotonicity YES**: `src/dispatch/dispatch.py:52` filters idle/local/energy/reserve candidates independently of fare, then requires offered_fare >= driver minimum. Increasing fare weakly expands the complete locally eligible set. Same-grid priority then lowest vehicle ID can change selected driver; the implementation need not examine neighbours once same-grid supply exists. Thus the selected/visited candidate list is not itself the nested-set claim.
3. **Conditional immediate reward monotonicity YES**: successful assignment earns offered fare; unassigned earns zero. For the identical pre-request fleet and feasible-arm pair, a previously assignable request remains assignable, while conditional fare strictly rises. This establishes the requested immediate-dominance definition, not long-term dominance.

## Saved greedy versus maximum feasible

| K | N | highest_pct | one_below_pct | other_pct | mean_factor_gap | factor_0.85_N | factor_0.9_N | factor_0.95_N | factor_1.0_N | factor_1.05_N | factor_1.1_N | factor_1.15_N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_CHOICE | 1279 | 12.3534 | 78.577 | 9.06959 | 0.0524629 | 78 | 75 | 36 | 17 | 62 | 991 | 20 |
| 2 | 59 | 59.322 | 40.678 | 0 | 0.020339 | 24 | 35 | 0 | 0 | 0 | 0 | 0 |
| 3 | 71 | 47.8873 | 16.9014 | 35.2113 | 0.043662 | 25 | 12 | 34 | 0 | 0 | 0 | 0 |
| 4 | 46 | 36.9565 | 4.34783 | 58.6957 | 0.0695652 | 8 | 19 | 2 | 17 | 0 | 0 | 0 |
| 5 | 32 | 78.125 | 0 | 21.875 | 0.0328125 | 0 | 7 | 0 | 0 | 25 | 0 | 0 |
| 6 | 30 | 90 | 10 | 0 | 0.005 | 0 | 0 | 0 | 0 | 3 | 27 | 0 |
| 7 | 1041 | 1.92123 | 92.6033 | 5.4755 | 0.0560999 | 21 | 2 | 0 | 0 | 34 | 964 | 20 |

There are 1,279 choice requests and 1,559 forced requests. Highest-feasible selection=12.353401%; one-below=78.577013%; average factor gap=0.05246286. Highest arm is K−1 because feasibility is a contiguous price prefix; no alternate mask definition is introduced.

## Full frozen-fleet counterfactual

All 1,279 choice requests, all feasible arms, and 23,179 feasible ordered low/high pairs were checked. Candidate reconstruction was independently matched against the active `find_eligible_vehicle` for every arm. Counts below are opportunities on the *DQN pre-dispatch trajectory*, not simultaneous assignments or counterfactual sequential totals. Driver counts include all eligible same-grid/direct-neighbour vehicles before priority selection. No availability resampling is used.

| action_index | factor | immediate_fare | feasible_choice_requests | passenger_accepted | requests_with_eligible_driver | total_eligible_drivers | immediate_reward_opportunity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.85 | 18.144 | 1279 | 1279 | 1254 | 97898 | 22752.6 |
| 1 | 0.9 | 19.2113 | 1279 | 1279 | 1268 | 106024 | 24359.9 |
| 2 | 0.95 | 20.2786 | 1220 | 1220 | 1212 | 111008 | 24577.6 |
| 3 | 1 | 21.3459 | 1149 | 1149 | 1143 | 112927 | 24398.3 |
| 4 | 1.05 | 22.4132 | 1103 | 1103 | 1097 | 117346 | 24587.2 |
| 5 | 1.1 | 23.4805 | 1071 | 1071 | 1068 | 122461 | 25077.1 |
| 6 | 1.15 | 24.5478 | 1041 | 1041 | 1041 | 128853 | 25554.2 |

All arms select the same assigned driver for 588/1,279 (45.973417%). At least one pair shares an assigned driver for 98.045348%. Any feasible-arm assignment change occurs for 689/1,279 (53.870211%). All-arm unmatched requests=2. These categories distinguish any-pair versus all-arm comparisons and are not all mutually exclusive.

| lower_factor | higher_factor | N | unmatched_to_assigned | assigned_driver_changed | same_assigned_driver | both_unmatched | unmatched_to_assigned_pct_of_step_requests | assigned_driver_changed_pct_of_step_requests | same_assigned_driver_pct_of_step_requests | both_unmatched_pct_of_step_requests |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.85 | 0.9 | 1279 | 14 | 212 | 1042 | 11 | 1.09461 | 16.5754 | 81.4699 | 0.860047 |
| 0.9 | 0.95 | 1220 | 3 | 139 | 1070 | 8 | 0.245902 | 11.3934 | 87.7049 | 0.655738 |
| 0.95 | 1 | 1149 | 1 | 141 | 1001 | 6 | 0.0870322 | 12.2715 | 87.1192 | 0.522193 |
| 1 | 1.05 | 1103 | 0 | 130 | 967 | 6 | 0 | 11.786 | 87.67 | 0.543971 |
| 1.05 | 1.1 | 1071 | 2 | 105 | 961 | 3 | 0.186741 | 9.80392 | 89.7292 | 0.280112 |
| 1.1 | 1.15 | 1041 | 3 | 362 | 676 | 0 | 0.288184 | 34.7743 | 64.9376 | 0 |

Step percentages use requests for which both adjacent arms are feasible; request-level any-change counts are deduplicated across steps. No matched-to-unmatched reversal is possible at the same frozen fleet under this eligibility rule.

## Same-assignment does not imply identical future state

Higher fare for the same driver/request leaves immediate physical movement, energy deduction, trip duration and destination unchanged (`dispatch_requests`, `passenger_commitment`). **It does not leave the whole future state unchanged except revenue.** `src/simulation/operational_state.py:113–117` updates successful-fare mean/std and smoothed mu/sigma. For the same assignment set of size m in an origin grid, changing one fare by d raises next mu by alpha*d/m; sigma can also change. `src/routing/operational_interface.py:25–27,133` feeds mu/sigma into the price-related routing utility. `src/routing/final_state.py:6` also places them in the 169D routing input; `src/simulation/final_production.py:88–102` feeds routing probabilities into the subsequent 13D pricing context.

Routing uses previous operational estimates during the immediate end-of-slot route call, then updated estimates affect later state/decisions. Even if the resulting discrete route coincides, operational state is not identical. Therefore **0 choice requests are established as strict long-term dominances under the stated identical-future-state condition**; the same-driver percentages above establish only immediate/physical equivalence. This is a limitation of the premise, not proof that price feedback makes the DQN useful.

If higher price changes unmatched→assigned or selected driver, additional pathways include removal of idle supply, vehicle-specific energy/position, passenger commitments, destination arrivals, successful-dispatch counts/F_hat, completed dispatch ledger and future routing/supply context. External forecast demand is not changed by fare in this comparison. Assignment-changing requests are consequently not the only possible future-state tradeoff.

## Sequential baselines

| policy | requests | assignments | revenue | mean_offered_fare | mean_assigned_fare | passenger_feasibility_violations | driver_unmatched | price_unmatched | other_unmatched | fleet_size | charging_decisions | active_passenger_commitments | fleet_energy_sum | optimizer_updates | fleet_BUSY | fleet_IDLE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DQN | 2838 | 2786 | 56419.3 | 20.2203 | 20.251 | 0 | 52 | 52 | 0 | 5000 | 0 | 358 | 197403 | 0 | 784 | 4216 |
| HIGHEST_FEASIBLE | 2838 | 2794 | 58017 | 20.725 | 20.7649 | 0 | 44 | 44 | 0 | 5000 | 0 | 358 | 197375 | 0 | 791 | 4209 |
| LOWEST_FEASIBLE | 2838 | 2688 | 48771 | 18.144 | 18.144 | 0 | 150 | 150 | 0 | 5000 | 0 | 358 | 197500 | 0 | 812 | 4188 |
| NEUTRAL_1_OR_LOWER | 2838 | 2747 | 53672.1 | 19.5159 | 19.5384 | 0 | 91 | 91 | 0 | 5000 | 0 | 358 | 197448 | 0 | 777 | 4223 |

Mean offered fare averages all offered requests; mean assigned fare averages successful assignments. Neutral selects 1.00 where feasible, otherwise the nearest feasible lower arm. These are deterministic model outcomes on one two-hour fixture, not causal real-world pricing evidence or an optimum claim. Full-fleet final counts/energy are reported; trajectories may diverge across policies. Highest-feasible beats or matches DQN on both revenue and assignments: True.

## Interpretation and limits

The passenger mask preserves acceptance for higher feasible prices, eligibility weakly increases, and immediate reward rises. This creates substantial structural pressure toward the upper feasible arm. A baseline comparison is essential before interpreting increasing Q or action concentration as nontrivial learned pricing. The operational fare-feedback and supply pathways prevent a general proof of long-term dominance. One fixed fixture cannot establish generalization or dynamic value; additional methodology review should precede automatic further training. No reward penalty, acceptance redesign, preference change, action change or retraining is performed here.

See action_dominance_decision.json, highest_feasible_comparison.csv, action_counterfactual_summary.csv, assignment_step_comparison.csv, baseline_comparison.csv and checkpoint_integrity.json. Only this diagnostic package and the staged README link were written.

## Current academic-review status

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

This report remains a bounded diagnostic; no methodology was changed. The current review labels do not convert immediate monotonicity into a universal long-term dominance claim.

[V1 hub](../../README.md) · [Methodology](../../METHODOLOGY.md) · [Academic review summary](../../ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../../review_feedback_reconciliation/README.md) · [Bellman correction](../../bellman_discount_correction/README.md) · [Authoritative staged training](../README.md) · [Action dominance](README.md)
