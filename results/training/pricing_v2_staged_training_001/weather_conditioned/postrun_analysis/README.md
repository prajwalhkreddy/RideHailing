# Weather/time-conditioned V2: completed Episode25 review

**V2_STAGE25_REVIEW_REQUIRED.** Episodes1–25 completed; no Episode26 was run. Episode25 does not beat Highest Feasible on assignments or revenue. No demonstrated beneficial dynamic effect is established.

## Frozen method and experimental scope

Runtime version `WEATHER_TIME_CONDITIONED_V2`; grouping `WEATHER_TIME_CONDITIONED_V2_2026_11_14`. Canonical Jan1–Mar15 empirical population:5,779,213 nonnegative observations, with actual zero count0. P_base=22.354198442390455 USD; L_base=4.616983790655043 km. Epsilon=r_L/r_P; inclusive abs(r_P)>=0.05. Negatives are excluded, not absolute-transformed. No new trimming, floor, distribution fitting or clustering was performed. Sampling is empirical with replacement, retaining duplicate frequencies. Runtime inverse preference is P_base+(P_base/epsilon)*r_L; acceptance threshold=max(0.85P_base,raw preference). Seven factors0.85–1.15 remain unchanged.

T1 uses its two time-specific groups. T2/T3/T4 deliberately use T-pooled support. Runtime minimum support5000: exact time-specific group, then same raw-weather pool, then time pool, then global. Explicitly pooled T2–T4 bypass the raw-weather fallback. T1_G2 has insufficient runtime support and falls back to raw-weather pools; codes17/21 fall back to T1 pool when applicable. No silent fallback is permitted.

## Duration, state and training

Training:16×30-minute slots=8h per episode,5000 vehicles,25 episodes. Development:48×30-minute slots=24h on March16. This retains the established request-level training horizon while strengthening development to a full day. The artificial 8h terminal boundary is an acknowledged limitation, not an optimized horizon. Historical continuous slot-based pricing used720 chronological slots; request-level V1 used16-slot training and its historical4-slot/2h development fixture.

13→64→64→7 network; gamma0.99 per actionable request transition; Adam lr0.001; batch64; replay100000; warmup1000;8 updates per warm slot; tau0.005. Epsilon1→0.05 over50000 updates. Learner seed42; development seed424242; persisted episode-specific environment seeds. Routing, request-level gross successful-assignment reward, masks and state are unchanged. Training dates remain March1–15, March16 development-only, March17–31 protected and untouched by this task.

Fixture SHA256:`c23f815ab8dd573b958e83260b442ab428255325bffc8ac83fdbfcf77e1177a6`. All six evaluations contain73,754 identical request IDs and identical conditioning hashes. The pinned evaluation implementation asserts epsilon/context equality, initial fleet identity and immutable input dependencies. No policies or fixtures were regenerated.

## Completion, integrity and resume

All six checkpoints loaded successfully, validating online/target architecture, finite weights and optimizer variables, Adam iteration counts, replay structure, learner/replay/sensitivity RNG identities, conditional version and contract hashes. Config/fixture/support/mapping/fallback hashes match. Current payload SHA256 fingerprints are in analysis_summary.json; no creation-time payload digest existed, so these establish present integrity/readability rather than independent historical authentication.

The initial process was interrupted during Episode4 after completing Episodes2–3 in volatile learner state. Episode1 was the latest durable checkpoint. Detached continuation restored Episode1:128 updates,37,111 replay rows,epsilon0.997568. Episode1 was not repeated. Interrupted later metrics were archived and excluded; Episodes2 onward were recomputed from the durable checkpoint under the recorded episode-boundary seed-reset contract. Resetting the next environment/sensitivity seed is prescribed; learner/replay RNG and optimizer were restored, not freshly initialized.

RESUME_CONTINUITY_VALIDATED=YES at checkpoint/accounting level. The committed output contains each episode1–25 once,128 updates each, cumulative3200; replay equals min(cumulative requests,100000), ending100000; epsilon0.9392. Expected slots=400 inferred from the fixed16-slot loop and completion assertions. Full per-slot IDs and all historical replay transitions were not persisted, limiting independent row-level duplicate verification.

Total training requests=1,118,214; assignments=684,815; revenue=$13,877,455.10. Request=assigned+unmatched in every episode. Training revenue is not a controlled comparison because source conditions and exploration vary.

## Authoritative fixed-fixture result

These are **WEATHER_CONDITIONED_V2_AUTHORITATIVE_BASELINE** results. Earlier POOLED_V2_CONTROL outputs remain historical and were not substituted.

| policy | requests | assignments | assignment_rate | revenue | revenue_per_request | unmatched | choice_requests | forced_requests | charging_events | invalid_masks | passenger_threshold_violations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EP25_DQN | 73754 | 59632 | 0.808526 | 1237868.209587 | 16.783743 | 14122 | 27719 | 46035 | 1956 | 0 | 0 |
| HIGHEST_FEASIBLE | 73754 | 59768 | 0.81037 | 1261843.087417 | 17.108809 | 13986 | 27719 | 46035 | 1947 | 0 | 0 |
| LOWEST_FEASIBLE | 73754 | 57912 | 0.785205 | 1100389.889166 | 14.919732 | 15842 | 27719 | 46035 | 1969 | 0 | 0 |
| NEUTRAL_1_00_WITH_EXISTING_FALLBACK | 73754 | 58804 | 0.797299 | 1186509.438666 | 16.087391 | 14950 | 27719 | 46035 | 1912 | 0 | 0 |

EP25 assignment gap=-136; revenue gap=$-23,974.88 (-1.9000%). Beats Highest Feasible assignments: **NO**. Beats revenue: **NO**.

## Checkpoint policy results

| episode | assignments | assignment_rate | revenue | unmatched | no_price_eligible_driver | mean_offer | revenue_gap_pct |
|---|---|---|---|---|---|---|---|
| 1 | 59483 | 0.806505 | 1215799.027175 | 14271 | 14232 | 20.359191 | -3.648953 |
| 5 | 58741 | 0.796445 | 1212224.590844 | 15013 | 14990 | 20.508372 | -3.932224 |
| 10 | 59133 | 0.80176 | 1242327.872176 | 14621 | 14609 | 20.85429 | -1.546564 |
| 15 | 59024 | 0.800282 | 1207495.560163 | 14730 | 14701 | 20.376346 | -4.306996 |
| 20 | 58498 | 0.79315 | 1214751.732978 | 15256 | 15242 | 20.582751 | -3.73195 |
| 25 | 59632 | 0.808526 | 1237868.209587 | 14122 | 14108 | 20.593465 | -1.899989 |

Complete action counts, forced/choice counts, fleet hashes, SOC ranges and charging entry/exit counts are retained in checkpoint_comparison.csv and episode25_comparison.csv. Fleet hashes identify end states, not complete vehicle-state reconstructions.

## Value calibration

| mean_absolute_TD_error | episode | MC_mean | MC_median | MC_SD | Q_mean | Q_median | Q_MC_MAE | pearson | spearman | mean_loss |
|---|---|---|---|---|---|---|---|---|---|---|
| 25.711905 | 1 | 1645.657596 | 1766.329497 | 377.355453 | 4.948951 | 1.169399 | 1640.708645 | -0.26555 | -0.231994 | 24.948024 |
| 11.879737 | 5 | 1640.770867 | 1736.930566 | 387.081403 | 21.899254 | 16.463179 | 1618.87328 | 0.327795 | 0.445826 | 11.798644 |
| 11.187555 | 10 | 1681.519212 | 1774.123102 | 389.099644 | 46.349937 | 43.677134 | 1635.173167 | 0.406356 | 0.557267 | 8.985096 |
| 10.328012 | 15 | 1634.404827 | 1721.878969 | 377.505724 | 80.776111 | 80.850639 | 1553.636018 | 0.597814 | 0.624769 | 12.336013 |
| 13.228838 | 20 | 1644.186887 | 1715.045153 | 402.468935 | 113.995835 | 114.231934 | 1530.205325 | 0.664376 | 0.66324 | 12.32658 |
| 15.426876 | 25 | 1675.510871 | 1758.160467 | 378.660176 | 160.045404 | 156.325089 | 1515.494469 | 0.578645 | 0.623872 | 16.275244 |

Q_CALIBRATION=POOR, despite improving scale/MAE and positive final correlations. Selected Q remains far below Monte Carlo return. LEARNING_SIGNAL=YES: finite losses and value predictions change, but this does not establish superior pricing or convergence. Exploration remains0.9392 and only3200 updates have occurred.

## Policy stability and action dominance

| from_episode | to_episode | all_agreement_pct | choice_agreement_pct | changed_pct | action_distribution_total_variation | revenue_change | assignment_change |
|---|---|---|---|---|---|---|---|
| 1 | 5 | 66.542832 | 10.97803 | 33.457168 | 0.254305 | -3574.436331 | -742 |
| 5 | 10 | 69.333189 | 18.40254 | 30.666811 | 0.279158 | 30103.281332 | 392 |
| 10 | 15 | 72.504542 | 26.840795 | 27.495458 | 0.269152 | -34832.312013 | -109 |
| 15 | 20 | 66.283863 | 10.288971 | 33.716137 | 0.314925 | 7256.172814 | -526 |
| 20 | 25 | 77.856116 | 41.080126 | 22.143884 | 0.14425 | 23116.476609 | 1134 |
| 10 | 25 | 81.600998 | 51.04441 | 18.399002 | 0.121973 | -4459.662589 | 499 |
| 15 | 25 | 73.033327 | 28.247772 | 26.966673 | 0.255606 | 30372.649424 | 608 |

POLICY_STABILITY=PARTIAL: all-request agreement is inflated by forced requests. EP20→25 choice agreement is41.08%, so the discretionary policy is not stable. Among choice requests, EP25 equals Highest Feasible 42.9994%, one action below 40.8565%, and at least two below 16.1442%. Mean/median rank below: 0.879830/1. Choice factor counts (0.85…1.15):[3053, 502, 4031, 5089, 692, 7634, 6718].

Passenger masks form a prefix of the ordered actions: lowering price preserves passenger feasibility. At a fixed fleet state, driver eligibility is monotone in offered price because dispatch rejects fares below each driver minimum (src/dispatch/dispatch.py:65–70). Consequently maximum feasible price weakly expands eligible drivers and raises immediate reward conditional on successful dispatch. This fixed-state immediate property does not prove long-term dominance: selecting a different driver can change later state.

DYNAMIC_VALUE_EVIDENCE=NONE for **demonstrated beneficial dynamic effects**. The first20 deterministic below-highest choice cases are in bounded_policy_difference_cases.csv. They show outcomes under different complete policy trajectories, not state-matched interventions. Assigned-driver identity, paired trajectories, later supply and commitments were not saved for DQN; no causal claim follows from reward differences in this table. No expensive counterfactual simulation was run. A separately scoped state-matched counterfactual diagnostic is the recommended next step before claiming dynamic value or extending training.

## Weather/time usage and empirical membership

| T_group | raw_weather_code | time_specific_weather_group | support_id | fallback_level | requests |
|---|---|---|---|---|---|
| T1 | 3 | T1_G1 | T1_G1 | 0 | 4089 |
| T2 | 3 | T_GROUP_POOLED_FALLBACK | T2_POOLED | 2 | 1812 |
| T3 | 3 | T_GROUP_POOLED_FALLBACK | T3_POOLED | 2 | 1633 |
| T3 | 5 | T_GROUP_POOLED_FALLBACK | T3_POOLED | 2 | 25724 |
| T3 | 8 | T_GROUP_POOLED_FALLBACK | T3_POOLED | 2 | 1879 |
| T3 | 9 | T_GROUP_POOLED_FALLBACK | T3_POOLED | 2 | 2521 |
| T4 | 3 | T_GROUP_POOLED_FALLBACK | T4_POOLED | 2 | 17053 |
| T4 | 5 | T_GROUP_POOLED_FALLBACK | T4_POOLED | 2 | 11842 |
| T4 | 8 | T_GROUP_POOLED_FALLBACK | T4_POOLED | 2 | 3536 |
| T4 | 9 | T_GROUP_POOLED_FALLBACK | T4_POOLED | 2 | 3665 |

Usage is for the common March16 evaluation fixture, not all training requests (training context usage was not persisted). Every fixture epsilon was checked for membership in its selected immutable support and support hashes verified. All evaluations reproduce the same context hash. Absent categories have zero observed usage, not fabricated fallback observations.

## Charging and invariants

Training charging events=1383; episodes with charging=23/25. CHARGING_COVERAGE=EXERCISED.

| episode | charging_events | vehicles_entering_charging | vehicles_leaving_charging | soc_min | soc_max | fleet_conserved |
|---|---|---|---|---|---|---|
| 1 | 1947 | 838 | 690 | 3.927373 | 75.0 | True |
| 5 | 2054 | 838 | 669 | 7.645013 | 75.0 | True |
| 10 | 1857 | 807 | 657 | 4.899372 | 75.0 | True |
| 15 | 2078 | 848 | 695 | 6.077318 | 75.0 | True |
| 20 | 1934 | 833 | 669 | 5.856444 | 75.0 | True |
| 25 | 1956 | 854 | 684 | 7.170126 | 75.0 | True |

Entry/exit counts are distinct vehicles observed at slot boundaries, not a complete event transition ledger. Training entry/exit counts were not persisted. Runtime finite/nonnegative SOC and fleet5000 assertions passed. Saved evaluation results contain zero masked-action, passenger-threshold and no-feasible-action violations. Persisted actions/rewards reconcile assignments and revenue; checkpoint replay loads and optimizer cadence pass. Routing/charging validity relies on the completed runtime guards and focused regression coverage, not an independently saved routing-event audit. No evidence of V1 or pooled-only learner contamination.

## Evidence gaps

- Training per-episode forced/choice/action distributions
- Training per-episode selected-Q and absolute-TD distributions/max Q
- Independent persisted slot-level and complete transition-ID audit
- Paired state-matched driver/trajectory/supply/commitment counterfactuals
- Per-training-episode charging entry/exit vehicles
- Original checkpoint payload digests: current digests are post-run fingerprints, not independent creation-time authentication

These fields cannot be honestly reconstructed from aggregate loss/reward summaries. No training or full-day simulation was rerun to fill them. Numerical stability is supported by recorded finite summaries and checkpoint state, with these audit limits.

## Tests

| stage | passed | failures | errors | skipped | exit_code |
|---|---|---|---|---|---|
| focused | 23 | 0 | 0 | 0 | 0 |
| B | 41 | 0 | 0 | 0 | 0 |
| C | 57 | 0 | 0 | 0 | 0 |
| D | 123 | 0 | 0 | 0 | 0 |
| E | 239 | 0 | 0 | 0 | 0 |
| resume | 2 | 0 | 0 | 0 | 0 |

Exact safe commands and logs are in tests.json and tests_*.txt; overlapping suites are not unique-test counts. No unrestricted discovery was used.

## Review decision and files

NUMERICAL_STABILITY=YES; LEARNING_SIGNAL=YES; Q_CALIBRATION=POOR; POLICY_STABILITY=PARTIAL; DYNAMIC_VALUE_EVIDENCE=NONE; CHARGING_COVERAGE=EXERCISED; CONVERGED=NO; READY_FOR_LONGER_TRAINING=REVIEW_REQUIRED.

The next decision is whether bounded state-matched counterfactual evidence justifies more training against Highest Feasible. No Episode26 or held-out evaluation is authorized by this analysis. See analysis_summary.json, checkpoint_comparison.csv, episode25_comparison.csv, training_trends.csv, value_calibration_review.csv, policy_stability.csv, weather_support_usage.csv, bounded_policy_difference_cases.csv and training_and_development_trends.png. Analysis uses immutable persisted inputs; source methodology/checkpoints were not changed.

**V2_STAGE25_REVIEW_REQUIRED**

## Complete committed training episode metrics

| episode | requests | assignments | assignment_rate | revenue | unmatched | optimizer_updates | exploration_epsilon | mean_loss | median_loss | P95_loss | replay_size | charging_events |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 37111 | 33828 | 0.911536 | 679986.773869 | 3283 | 128 | 0.997568 | 24.948024 | 25.142941 | 29.814028 | 37111 | 34 |
| 2 | 43973 | 22141 | 0.503514 | 449294.799074 | 21832 | 128 | 0.995136 | 19.23451 | 19.310905 | 23.37133 | 81084 | 23 |
| 3 | 61355 | 36873 | 0.600978 | 747143.25683 | 24482 | 128 | 0.992704 | 16.419611 | 16.210793 | 19.496311 | 100000 | 129 |
| 4 | 53778 | 22869 | 0.425248 | 464276.58287 | 30909 | 128 | 0.990272 | 14.496017 | 14.501884 | 17.217825 | 100000 | 26 |
| 5 | 43901 | 20337 | 0.463247 | 412221.478667 | 23564 | 128 | 0.98784 | 11.798644 | 11.641236 | 14.361029 | 100000 | 27 |
| 6 | 69394 | 36250 | 0.522379 | 736862.560966 | 33144 | 128 | 0.985408 | 10.328799 | 10.263849 | 11.986736 | 100000 | 124 |
| 7 | 34172 | 32183 | 0.941794 | 647369.762922 | 1989 | 128 | 0.982976 | 9.866435 | 9.789958 | 11.791876 | 100000 | 45 |
| 8 | 40133 | 29180 | 0.727082 | 589691.460101 | 10953 | 128 | 0.980544 | 9.481933 | 9.471059 | 11.370933 | 100000 | 47 |
| 9 | 4265 | 4001 | 0.938101 | 79373.052409 | 264 | 128 | 0.978112 | 8.962592 | 8.865635 | 11.309476 | 100000 | 0 |
| 10 | 39488 | 32368 | 0.819692 | 651368.929024 | 7120 | 128 | 0.97568 | 8.985096 | 8.975527 | 10.640354 | 100000 | 58 |
| 11 | 34907 | 28173 | 0.807087 | 573176.178292 | 6734 | 128 | 0.973248 | 9.127393 | 8.973785 | 11.359604 | 100000 | 47 |
| 12 | 36064 | 24755 | 0.686419 | 501270.545872 | 11309 | 128 | 0.970816 | 9.401318 | 9.373501 | 11.791691 | 100000 | 31 |
| 13 | 42037 | 24760 | 0.589005 | 503752.979609 | 17277 | 128 | 0.968384 | 10.605089 | 10.466339 | 13.666615 | 100000 | 46 |
| 14 | 26446 | 15999 | 0.604969 | 323437.308713 | 10447 | 128 | 0.965952 | 11.333592 | 11.098603 | 14.40745 | 100000 | 1 |
| 15 | 62847 | 42287 | 0.672856 | 856553.645687 | 20560 | 128 | 0.96352 | 12.336013 | 12.066446 | 15.146857 | 100000 | 138 |
| 16 | 53956 | 20573 | 0.381292 | 417841.324155 | 33383 | 128 | 0.961088 | 11.595113 | 11.583367 | 14.432492 | 100000 | 21 |
| 17 | 44891 | 33067 | 0.736606 | 670773.490981 | 11824 | 128 | 0.958656 | 11.630806 | 11.576037 | 14.415483 | 100000 | 65 |
| 18 | 15681 | 12972 | 0.827243 | 266111.084518 | 2709 | 128 | 0.956224 | 10.992313 | 10.999888 | 12.742427 | 100000 | 13 |
| 19 | 52768 | 39719 | 0.75271 | 804353.239194 | 13049 | 128 | 0.953792 | 11.888546 | 11.848876 | 14.800216 | 100000 | 95 |
| 20 | 63400 | 28314 | 0.446593 | 578397.001338 | 35086 | 128 | 0.95136 | 12.32658 | 12.190123 | 14.80364 | 100000 | 61 |
| 21 | 34198 | 23732 | 0.693959 | 480351.48697 | 10466 | 128 | 0.948928 | 13.06952 | 12.831558 | 16.324085 | 100000 | 24 |
| 22 | 59252 | 34050 | 0.574664 | 692286.053852 | 25202 | 128 | 0.946496 | 11.99105 | 11.980358 | 14.141756 | 100000 | 93 |
| 23 | 40996 | 12360 | 0.301493 | 249165.484388 | 28636 | 128 | 0.944064 | 11.9518 | 11.900406 | 14.274164 | 100000 | 0 |
| 24 | 71547 | 50470 | 0.70541 | 1025188.130186 | 21077 | 128 | 0.941632 | 13.133361 | 12.809989 | 17.109382 | 100000 | 202 |
| 25 | 51654 | 23554 | 0.455996 | 477208.486669 | 28100 | 128 | 0.9392 | 16.275244 | 16.09255 | 20.583484 | 100000 | 33 |

Loss decreases initially, reaches its lowest mean near Episode9, and rises again toward Episode25; this is not evidence of convergence. All episodes have128 updates. No training action/Q/TD distribution is inferred from these aggregates.
