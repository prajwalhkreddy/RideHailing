# End-to-End Diagnostic Review

## Executive Diagnostic Summary

- VERIFIED_IMPLEMENTATION_BEHAVIOR: existing epoch-200 CNN evaluation, request arithmetic, outcome identities and training counters are consolidated.
- MODEL_EFFECTIVENESS_LIMITATION: historical demand baseline outperforms CNN; routing probabilities underperform masked training-prior predictions.
- SOURCE_CONTRACT_UNRESOLVED: elasticity orientation, sign treatment, sampling support and P_max equation remain open.
- KNOWN_IMPLEMENTATION_DEFECT: FCFS does not enforce the hard driver minimum-price gate.
- ACTIVE_IMPLEMENTATION_DIAGNOSTIC / NOT_SOURCE_VALIDATED_ACCEPTANCE_ANALYSIS applies to all passenger calculations here.
- Seven-factor comparisons reuse all 2,838 saved passenger realizations; no RNG draw or simulator run occurred.
- PARTIALLY_COMPLETE: final CNN grid/time aggregates and exact grid-slot idle supply are unavailable within permitted saved summaries.
- Current routing experiences, central/FedAvg checkpoints, adequacy result, pricing checkpoint and March16 diagnostic are pre-correction provenance, not final thesis results for a corrected contract.
- Pricing convergence is not established; 718 updates leave epsilon at 0.986358.
- Approximately 500 episodes is guidance for experimentation, not an approved protocol or convergence criterion.
- Retraining remains paused pending upstream contract resolution and focused validation.
- FUTURE_PHASE: differential privacy follows a validated non-private baseline.
- No regeneration, model loading/training, simulator execution, protected-period data access or methodology change occurred.

## 1. Demand Prediction

**CNN_VALID_BUT_HISTORICAL_BASELINE_SUPERIOR**. Epoch200 MAE/RMSE/R²: 5.242741 / 18.292800 / 0.961007. Historical baseline: 3.314528 / 16.271804 / 0.969147.

Mean observed demand 18.157497; mean prediction 17.016261; mean bias -1.141236. RMSE divided by mean actual demand is **100.7452%**; this is not MAPE. Aggregate underprediction coexists with overprediction at zero-demand cells.

Saved final demand-band errors show:

| demand_band | N | observed_mean | bias | RMSE |
| --- | --- | --- | --- | --- |
| (724.31,1764] | 505 | 1001.401980 | -89.485407 | 180.723106 |
| (228,724.31] | 2014 | 423.019364 | -11.670028 | 83.724630 |
| (53,228] | 2470 | 99.191903 | -1.267662 | 29.776103 |

Final highest-error grids and half-hour periods: **NOT YET AVAILABLE**. Existing grid summaries describe epoch100, so they are not mislabeled epoch200. Required grid/time CSVs explicitly record availability, not fabricated errors. Only existing aggregate CNN reports were read; no final-test forecast rows or March17–31 data were opened. Existing CNN reports historically include that interval; this task does not claim it was never evaluated.

## 2. Passenger Price Sensitivity and Acceptance

Classification: **SOURCE_CONTRACT_UNRESOLVED**. Current calibration uses abs(relative price deviation / relative distance deviation), whereas active acceptance uses inverse E. Conflicting project notes do not establish source validity. Active behavioural sampling is positive-truncated Normal; no reinterpretation is made.

`P_dispatch = factor * P_base`; `P_max = P_base + P_base*((L-L_base)/L_base)/E`; accept iff `P_dispatch <= P_max`. Runtime references are weather/half-hour-resolved, not the old global Record-029 references.

P_max mean/sample SD/median: **25.617178 / 167.774111 / 19.770191** USD. Sampled E mean/sample SD/median: 5.649157 / 4.748094 / 4.564241. Complete requested percentiles and extrema are in passenger_pmax_summary.json; all SDs in passenger summaries use ddof=1.

| factor | requests | accepted | rejected | acceptance_percentage | mean_candidate_dispatch_price | simplified_mean_fare_times_acceptance | status | simplified_rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.850000 | 2838 | 2032 | 806 | 71.599718 | 17.810635 | 12.752364 | NOT_FINAL_SYSTEM_REVENUE | 1 |
| 0.900000 | 2838 | 1745 | 1093 | 61.486963 | 18.858319 | 11.595408 | NOT_FINAL_SYSTEM_REVENUE | 2 |
| 0.950000 | 2838 | 1279 | 1559 | 45.066949 | 19.906004 | 8.971028 | NOT_FINAL_SYSTEM_REVENUE | 3 |
| 1.000000 | 2838 | 953 | 1885 | 33.579986 | 20.953688 | 7.036245 | NOT_FINAL_SYSTEM_REVENUE | 4 |
| 1.050000 | 2838 | 816 | 2022 | 28.752643 | 22.001372 | 6.325976 | NOT_FINAL_SYSTEM_REVENUE | 5 |
| 1.100000 | 2838 | 727 | 2111 | 25.616631 | 23.049057 | 5.904392 | NOT_FINAL_SYSTEM_REVENUE | 6 |
| 1.150000 | 2838 | 652 | 2186 | 22.973925 | 24.096741 | 5.535967 | NOT_FINAL_SYSTEM_REVENUE | 7 |

**NOT_FINAL_SYSTEM_REVENUE**: the simplified score is mean candidate fare × empirical acceptance probability. It ignores driver eligibility, supply, unserved demand, operating costs and future state effects. It is not even the mean accepted fare contribution when price and acceptance covary; it is the requested simplified product. Ranking does not select an optimal DQN action.

Price gap P_max−actual dispatch price: mean 6.965659, sample SD 167.776835, median 0.924919; positive/zero/negative = 1801/0/1037. Full overall/accepted/rejected summaries are in passenger_price_gap_summary.json. Positive gap is not directly collectible revenue.

## 3. Passenger and Driver Outcome Separation

Generated2838 = accepted1801 + passenger-rejected1037. Accepted1801 = assigned1801 + unmatched0. All saved decisions match the current acceptance formula. Passenger rejection is distinct from counterfactual driver-price ineligibility, supply failure and other dispatch failure. No accepted-unmatched cases occurred, so observed supply/other failure counts are zero.

Hard gate counterfactual: 1801 checked,884 pass,917 fail (**50.916158%**). **KNOWN_IMPLEMENTATION_DEFECT**: the gate is not enforced. These failures overlap successful assignments; they are not additional rejections or a prediction of replacement-driver outcomes. Implement the gate together with the resolved passenger contract before final regeneration; no correction is made here.

## 4. Driver Preferences and Supply

Existing 5000 profiles: P_min (USD) and W_pref (minutes):

| variable | count | mean | sample_SD | min | P10 | P25 | median | P75 | P90 | P95 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P_min | 5000 | 20.090871 | 9.405899 | 3.950961 | 7.240016 | 11.901685 | 19.972552 | 28.340191 | 33.188511 | 34.866573 | 36.526114 |
| W_pref | 5000 | 14.958925 | 8.638062 | 0.009433 | 3.060007 | 7.458378 | 15.148304 | 22.269512 | 26.920674 | 28.555272 | 29.999311 |

Profile price_preference is the active P_min argument to price utility; wait_preference supplies W_i_max. No independent P_pref appears in the active profile contract. Instantaneous U1/U2: **NOT RETAINED IN EXISTING DIAGNOSTICS**. Assigned-driver summaries are ride-weighted, not unique-driver-weighted, and include P_dispatch−P_min in driver_preference_diagnostics.json.

**GRID_SLOT_IDLE_SUPPLY_NOT_RETAINED**. Request-time origin-plus-neighbor idle counts cannot be treated as slot-start grid supply. Exact deficits/excess supply, entering/leaving vehicles and reposition trajectories are **NOT YET AVAILABLE**. supply_demand_diagnostics.json preserves observed origin-grid/slot requests, assignments, rejected/unmatched counts and assigned destination flows. Destination flows are not measured arrival times.

## 5. Fleet and EV Configuration

Active default fleet: **5000 EV / 0 non-EV;100% EV**; verified against profile count and the production all-EV initializer, not inferred from an unspecified mix. Battery75kWh. Configured reference minimum7.5kWh; operational charging threshold20%×75=15kWh, a distinct quantity. Explicit profile H_i_max=10 minutes for all5000. Post-movement requirement: `E_current−E_movement >= minimum station-route energy(destination)`, equality allowed, no arbitrary added margin. fleet_configuration.json preserves configured energy values. No charging redesign or simulation occurred.

## 6. Routing and Federated Learning

3,257,840 experiences: March1–12 train2,618,033; March13–15 validation639,807. Network169→64→32→9. Central accuracy92.1855%, CE0.407089; FedAvg accuracy85.3673%, CE0.538560; majority baseline93.8993%. Five rounds,5000 active clients,one local epoch, sample-weighted aggregation. Saved aggregation checks pass; no zero-sample clients occurred in this run, so zero exclusions is not evidence of a faulty exclusion rule.

**ROUTING_PROBABILITIES_INFORMATIVE = NO**: FedAvg CE/Brier0.538560/0.245881 versus masked training-prior0.352059/0.117621. Classification MODEL_EFFECTIVENESS_LIMITATION. Implementation/aggregation correctness does not establish useful probability predictions. Current experiences, central/FedAvg checkpoints and adequacy measurements remain pre-correction provenance; retain them without declaring final methodology-dependent results.

## 7. Pricing DQN and Training Adequacy

Completed March1–15:1,705,916 requests;536,483 accepted;1,169,433 rejected;395,492 assigned;140,991 unmatched; gross assignment-time revenue7,490,773.984343884. Replay288,181 transitions;100,000 retained;718 optimizer updates;epsilon0.986358. Source: saved training_status and cadence artifacts. No replay or checkpoint payload was opened.

| factor | count | percentage |
| --- | --- | --- |
| 0.850000 | 41644 | 14.450640 |
| 0.900000 | 42053 | 14.592565 |
| 0.950000 | 41119 | 14.268463 |
| 1.000000 | 40891 | 14.189346 |
| 1.050000 | 40882 | 14.186223 |
| 1.100000 | 40850 | 14.175119 |
| 1.150000 | 40742 | 14.137643 |

Counts represent pricing decisions/transitions, not request counts. Checkpoint: `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4`.

**COMPLETED_PRICING_TRAINING_RUN / TRAINING_SCHEDULE_MISMATCH / NOT_FINAL_NONPRIVATE_BASELINE**. One update per completed half-hour slot after1000 replay entries:720slots−2warm-up=718updates. Epsilon1→0.05 over50000 optimizer updates needs5264/26316/47369/50000 updates for0.90/0.50/0.10/0.05. One update per5transitions is only a proposal, not implemented or frozen.

March16 greedy development:2838requests,1801accepted/assigned,revenue33721.11; OD-slot actions196 at0.85 and908 at0.90. Fixed1.00 comparator revenue19996.38. This does not establish convergence or general superiority. The pricing checkpoint and development comparison remain pre-correction provenance.

Approximately500 episodes was suggested as a starting point. Eight-hour episodes imply16slots and8000slots for500episodes; twelve-hour episodes imply24slots and12000slots. Episode count is not convergence proof; slots are not optimizer updates. Episode length, resets, start-state sampling, repeated historical periods, replay persistence, cadence, epsilon compatibility and stopping criteria remain open.

## 8. Privacy Status

**FUTURE_PHASE**. FedAvg alone is not differential privacy. Required decisions: private unit; clipping threshold C; per-example/update clipping semantics; noise mechanism and multiplier; epsilon_DP and delta_DP; accountant/cumulative privacy loss; utility comparison before/after privacy. None is implemented or frozen by this review.

## 9. Validation Checklist

| Requirement | Evidence | Status | Next_Action |
| --- | --- | --- | --- |
| CNN actual-vs-predicted | cnn_diagnostics.json | VERIFIED | Retain historical baseline comparison |
| CNN MAE/RMSE/R² | cnn_diagnostics.json | VERIFIED | Retain historical baseline comparison |
| CNN relative error | cnn_diagnostics.json | VERIFIED | Retain historical baseline comparison |
| CNN concentrated errors | cnn_error_by_grid.csv; cnn_error_by_time.csv; demand-band evidence | PARTIALLY_COMPLETE | Final spatial/time summaries unavailable without protected forecast access |
| P_max distribution | passenger_pmax_summary.json; passenger_acceptance_by_factor.csv; rejection_breakdown.json | VERIFIED | Interpret only as active implementation diagnostics |
| acceptance at seven factors | passenger_pmax_summary.json; passenger_acceptance_by_factor.csv; rejection_breakdown.json | VERIFIED | Interpret only as active implementation diagnostics |
| passenger decision consistency | passenger_pmax_summary.json; passenger_acceptance_by_factor.csv; rejection_breakdown.json | VERIFIED | Interpret only as active implementation diagnostics |
| passenger vs driver rejection | passenger_pmax_summary.json; passenger_acceptance_by_factor.csv; rejection_breakdown.json | VERIFIED | Interpret only as active implementation diagnostics |
| epsilon/P_max source equation | Conflicting project equations | SOURCE_UNRESOLVED | Resolve authoritative contract |
| P_min hard eligibility | 917/1801 assigned rides violate counterfactual gate | KNOWN_DEFECT | Bundle gate and acceptance corrections |
| P_min distribution | driver_preference_diagnostics.json | VERIFIED | No preference changes |
| W_pref distribution | driver_preference_diagnostics.json | VERIFIED | No preference changes |
| grid supply analysis | GRID_SLOT_IDLE_SUPPLY_NOT_RETAINED | PARTIALLY_COMPLETE | Retain grid request/assignment flows; no new simulation |
| EV/non-EV fleet count | fleet_configuration.json | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| routing centralized model | routing_learning_summary.json | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| FedAvg aggregation | routing_learning_summary.json | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| pricing-factor frequencies | pricing_action_distribution.csv | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| reward accounting | saved training and March16 assignment-fare totals | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| replay buffer | 288181 transitions;100000 retained | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| optimizer updates | 718 | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| epsilon schedule | 0.986358 final | VERIFIED | Preserve pre-correction evidence; verified execution is not effectiveness |
| routing probability adequacy | routing_learning_summary.json; pricing_training_summary.json | KNOWN_LIMITATION | Resolve upstream contracts before new training |
| DQN convergence | routing_learning_summary.json; pricing_training_summary.json | KNOWN_LIMITATION | Resolve upstream contracts before new training |
| multi-episode training protocol | 500 episodes suggested only | SOURCE_UNRESOLVED | Freeze protocol and cadence before implementation |
| privacy | FedAvg alone is not DP | FUTURE_PHASE | Establish non-private baseline first |

Checks are evidence consolidation, not new model tests. All saved inputs used by analytical aggregation have SHA-256 entries in validation_checklist.json. Request identities, formula decisions, seven-factor counts and profile coverage were checked. No training/generation occurred. Missing requested detail is explicit rather than triggering expensive work.

## 10. Open Methodology Decisions

- passenger elasticity orientation.
- signed vs absolute treatment.
- sampling support.
- exact P_max equation.
- multi-episode DQN protocol.
- optimizer-update cadence.
- convergence/stopping rule.

These require methodology agreement. Approximately500episodes and proposed update cadence are not frozen. Current downstream artifacts remain useful evidence of the pre-correction configuration; they are not deleted and are not final thesis results for a corrected contract.

## 11. Recommended Next Actions

1. Resolve authoritative passenger epsilon/P_max contract.
2. Freeze orientation, sign/absolute treatment, sampling support and exact P_max equation.
3. Implement corrected passenger contract if required.
4. Implement hard P_dispatch >= P_min driver eligibility.
5. Validate passenger and driver decisions with focused fixtures.
6. Regenerate March1–15 routing experiences ONCE under corrected contracts.
7. Retrain central routing and FedAvg.
8. Re-evaluate routing probability adequacy against empirical-prior baseline.
9. Define/freeze DQN multi-episode protocol.
10. Freeze optimizer cadence and epsilon compatibility.
11. Retrain pricing from deterministic seed42.
12. Use March16 only for development/convergence diagnostics.
13. Freeze final non-private baseline.
14. Only then access March17–31 for final evaluation.
15. Implement/evaluate DP afterward.

No listed action was executed. Diagnostic order remains demand predictor → passenger sensitivity/P_max → passenger versus driver decisions → supply/repositioning → action/reward → replay/optimizer/convergence → non-private baseline → privacy. Avoid simultaneous unvalidated module changes; validate the agreed upstream correction bundle before regeneration.

## Evidence and artifacts

All newly generated files are in this folder. JSONs record the detailed statistics; CSVs record seven-factor acceptance, pricing-action frequencies and explicit CNN-detail availability. Source evidence was limited to saved CNN summaries, March16 request diagnostics, acceptance source-resolution and methodology-alignment reports, final routing/pricing reports, adequacy reports, active profiles/configuration and the minimal fleet-construction path. Existing historical path names are preserved solely as provenance in validation_checklist.json.

**END_TO_END_DIAGNOSTIC_REVIEW_READY = YES** means consolidation is complete with explicitly documented availability limits; it does not authorize regeneration or retraining.
