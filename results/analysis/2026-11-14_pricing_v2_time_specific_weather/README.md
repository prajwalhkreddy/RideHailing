# V2 time-specific weather sensitivity

**Offline mapping frozen; runtime and full-day validation in progress. Training has not started.** No launch readiness is asserted until the conditioned baselines and all gates pass.

## Population and representation

The unchanged canonical population contains5,779,213 finite nonnegative epsilon observations from Jan1–Mar15. Source hashes were verified before use. P_base=22.354198442390455 USD; L_base=4.616983790655043 km; epsilon=r_L/r_P with abs(r_P)>=0.05. Negative values are excluded from runtime support, never converted to magnitudes. No denominator recalibration, new tail truncation or parametric refit occurred. March16 is development-only; March17–31 remains protected.

T1=[00,04), T2=[04,06), T3=[06,16), T4=[16,24). Within each T, weather codes are represented by observed mean and population SD only. Saved post-denominator statistics were reused; the immutable population was read only to aggregate daily moments for bounded stability checks and construct exact empirical supports. No population was rebuilt.

The previous permanent weather mapping was rejected because omitting individual T groups substantially changed memberships. This analysis deliberately allows different membership across T. It does not impose cross-time partition agreement.

## Selection protocol

`selection_protocol.json` was written before candidate selection. Primary support N>=100; secondary N>=50. Missing cells are absent from linkage, not imputed. Euclidean distance is sqrt(delta_mean²+delta_SD²), unscaled, within T only. Codes are sorted; average linkage is deterministic.

Conservative project engineering criteria require silhouette>=0.25, no single-code clusters, median perturbation ARI>=0.75 and P10 ARI>=0.50. Among qualifying cuts within0.02 silhouette of the best, the smaller K wins. These are transparent operational acceptance criteria, not significance tests or universal scientific thresholds. If no nontrivial cut qualifies, the T group uses pooled fallback.

Each candidate is checked under N50 support; removal of codes with fewer than5 distinct dates;20 date-block bootstrap resamples; two alternating chronological date subsets; and20 independent ±1% feature perturbations. Random operations use seed42. Date blocks preserve shared-day exposure across codes; bootstrap statistics use exact daily sums/squared sums, not sampled synthetic trips. Perturbation agreement uses common codes when a sparse code disappears. Different check types and common-code counts remain visible; aggregate stability does not imply event-level generalization for rare weather.

## Frozen time-specific result

| T | K | Result |
|---|---:|---|
|T1|2|T1_G1={1,2,3,5,7,8,9,12,14,16}; T1_G2={13,15}|
|T2|Not selected|T_GROUP_POOLED_FALLBACK|
|T3|Not selected|T_GROUP_POOLED_FALLBACK|
|T4|Not selected|T_GROUP_POOLED_FALLBACK|

T1 K2 silhouette0.671885; within/between distances0.336939/0.995018; median/P10 ARI1.000000/0.569454. Its minimum cluster has two raw codes. K2 median/P10 ARI for T2 are0.818602/−0.118644, T3 0.069379/−0.078431, and T4 0.640950/−0.077163. No candidate in those T groups satisfies the full rule. Pooled fallback is therefore a deliberate supported outcome, not forced K=1 clustering.

`weather_time_group_mapping.csv` contains all56 raw-code/T combinations. Unobserved cells have N=0 and missing statistics; these rows document runtime handling and do not fabricate observations. Codes13,17,21 are reassessed independently: code13 participates in T1; code17 has observed T2 support and code21 T3 support, but those T groups use pooled fallback. T1 codes17/21 have no supported membership.

Group identifiers are T-scoped. Cross-time trajectories compare member sets/handling, not numeric group labels. Their descriptive classifications must be read with the fact that T2–T4 have no frozen weather partition; fallback does not prove weather equivalence.

## Empirical supports and fallback

All supports preserve source order and duplicate frequencies and are sampled uniformly with replacement. No parametric approximation is introduced. Binary files are stored under `data/interim/pricing_v2_sensitivity/time_specific_weather_2026_11_14/`; each has a SHA256 manifest entry and numerical summary.

| Support | N | Mean | Population SD |
|---|---:|---:|---:|
|T1_G1|431,018|2.067628|2.398784|
|T1_G2|1,669|2.587603|3.195333|
|T1 pooled|432,687|2.069634|2.402580|
|T2 pooled|108,740|2.446397|2.561349|
|T3 pooled|2,544,533|1.822830|2.058783|
|T4 pooled|2,693,253|1.724723|1.807488|
|Global|5,779,213|1.807321|1.990089|

The manifest includes2 group supports,4 T-pooled supports,14 raw-weather supports and1 global support (21 total). These overlap by design; their counts must not be summed as unique observations.

The retained runtime eligibility threshold is5,000 observations, distinct from N100 feature support. Levels:

0. Exact time-specific group support, if eligible.
1. Same **raw weather code** pooled across T, if eligible. A permanent behavioural group cannot be used because memberships are time-specific.
2. T-pooled support.
3. Global support.

An explicitly ungroupable T uses T_GROUP_POOLED_FALLBACK directly (level2, then3). Applying a raw-weather fallback there would reintroduce the weather differentiation just rejected by the within-T evidence. For a missing cell in a grouped T, the full hierarchy applies. Unknown integer codes have explicit T/global handling; missing/nonfinite codes fail closed.

T1_G2 is retained as a diagnostic empirical support but is below5,000, so codes13/15 use their eligible raw-weather fallback pools at runtime. `fallback_required` in the mapping marks absence of a supported cluster assignment; actual support eligibility and fallback level are resolved separately and recorded for every draw. No zero epsilon occurs; the unchanged inverse-epsilon price formula still rejects zero rather than inventing a replacement.

## Runtime and version isolation

`ConditionedV2SensitivityProvider` requires a pinned grouping-contract hash, verifies mapping/support manifests and binaries, and refuses context-free sampling. Each request supplies actual raw weather at its origin/slot and its timestamp; one draw is reused for every candidate price. The request audit records raw code, T, T-scoped group, support ID/hash, fallback level and epsilon. Fallback counters are persisted with RNG state.

Sensitivity version is WEATHER_TIME_CONDITIONED_V2. Grouping version, mapping hash, support-manifest hash and fallback-policy version are checkpointed. Pooled-only checkpoints cannot restore into this provider. The request-price validation branch recognizes the conditional customer-model name and applies the unchanged V2 formula, action limits and feasibility checks.

## Development fixture and baselines

The separate `results/training/pricing_v2_staged_training_001/weather_conditioned/` namespace preserves all pooled-control evidence. The immutable request sequence and initial fleet are reused and verified against the existing control fixture; all48 March16 forecast/popularity/weather snapshots are checked. The new fixture freezes73,754 weather/time/support selections and epsilon draws, reproduced exactly after RNG reset. Baseline policies receive identical selections and draws.

The first baseline attempt stopped at request validation because the new customer-model name was missing from the recognized V2 branch. That narrow integration issue was corrected; failure evidence is retained. Full-day highest/lowest/neutral runs and exact repeats are pending completion. No completed result or authoritative baseline is claimed yet.

## Files and tests

`weather_code_time_statistics.csv`, `feature_ranges.csv`, `weather_cluster_candidates.csv`, `weather_cluster_stability.csv`, `weather_time_trajectory.csv`, `weather_time_group_mapping.csv`, `weather_time_grouping_contract.json`, `conditional_support_manifest.csv`, `conditional_support_statistics.csv`, and `build_verification.json` provide the complete offline record. `test_results.txt` and scoped regression logs record validation. Runtime/fixture/baseline and launch evidence belongs in the separate conditioned run folder. Do not launch DQN training during this task.

## Completed runtime tests

23 focused time-specific grouping/runtime tests passed, including a real two-request simulator boundary and checkpoint round-trip/mismatch checks without optimizer updates. Existing related41, focused57, reconciled broader123 and expanded applicable239 tests passed after the request-model correction; counts overlap. Full-day baseline reproducibility remains pending. `runtime_cell_support_selection.csv` records all56 actual support selections and runtime fallback flags, including the undersized T1_G2 fallback.

## Completed full-day validation

**READY_TO_LAUNCH_V2_STAGE25. Training has NOT started.** All three conditioned policies completed48 slots and exact full repeats with the same73,754 request/context/epsilon records, unchanged initial fleet and validated dependencies. Full request tables matched exactly across repeats; no optimizer updates occurred. Fleet conservation and reward/feasibility checks passed. The versioned harness verification passed. March17–31 remains untouched.

| Policy | Assignments | Revenue USD | Unmatched |
|---|---:|---:|---:|
|HIGHEST_FEASIBLE|59768|1261843.087417|13986|
|LOWEST_FEASIBLE|57912|1100389.889166|15842|
|NEUTRAL_1_00_WITH_EXISTING_FALLBACK|58804|1186509.438666|14950|

23 focused tests and the41/57/123/239 scoped suites passed (overlapping coverage). Conditional support selection and per-request epsilon sequences are identical across policies. Charging entry/exit counts in the baseline table are observed at slot boundaries; detailed event count is separately recorded. Read `prelaunch_verification.json` and `baseline_manifest.json` for hashes. Readiness is not authorization to start training in this task.
