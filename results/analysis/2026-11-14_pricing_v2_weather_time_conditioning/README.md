# V2 time-preserving weather grouping — evidence and launch gate

**V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_TEMPORAL_CLUSTER_INSTABILITY**

Training has not started. The requested representation is resolved and implemented in this offline analysis. No weather mapping is frozen: the best-separated candidate is sensitive to which time groups are represented. No conditional sampler, conditional support, authoritative fixture or baseline was activated from an unapproved mapping. The pooled runtime remains a control only. This is an evidence-based stop, not a return to the earlier representation ambiguity.

## Population and scope

All declared canonical source hashes were verified before reading the existing materialization. The 5,779,213 runtime candidates remain unchanged: Jan1 inclusive–Mar16 exclusive; P_base=22.354198442390455 USD; L_base=4.616983790655043 km; epsilon=r_L/r_P; abs(r_P)>=0.05; finite nonnegative support. The population mean/median/population SD reproduce 1.8073206996/1.1543559036/1.9900893312. No recalibration, absolute transformation, clipping, parametric refit or new tail restriction occurred. March16 did not select groups; March17–31 was not read. Historical V1 and Record-029 artifacts were not edited.

## Representation and missing features

T1=[00,04), T2=[04,06), T3=[06,16), T4=[16,24), unchanged. Each raw code has observed N, distinct dates, mean, population SD, median, P05/P25/P75/P95/P99 and min/max per T group. N>=100 is the primary feature-support diagnostic; N>=50 is secondary. N is not a clustering feature. Missing cells are absent, never filled.

Before linkage, `preclustering_support_rule.json` records the strict-majority overlap rule: at least three of four supported T groups. Pairwise distance is sqrt(sum of squared mean/SD differences divided by the number of shared features). Raw Euclidean distance and compared features are also saved. With three-group leave-one-out diagnostics, overlap requires two remaining groups. Leave-one-out uses the same eligible raw-code set, avoiding confounding the test with admission of sparse codes.

Eleven codes have all four groups. Codes13,17,21 have only2,1,1 supported groups, respectively, and are excluded from linkage. The reusable implementation also deterministically removes incompatible codes if three-group coverage does not yield three-group pairwise overlap: lowest supported-group count, then lowest N, then descending code. That removal path was not needed for these11 codes.

Unscaled observed means range1.5070–2.7540; SDs1.4878–3.2130. SD differences contribute77.17% of total pairwise squared distance. This influence is explicit, not concealed by automatic standardization; both families remain in the reviewed unscaled representation. Changing scaling to improve separation would be a new analysis decision, not a silent correction.

## Candidate cuts and temporal robustness

Average-linkage hierarchical clustering uses the complete supported distance matrix, sorted raw codes and no weather names. All K=1–11 cuts are saved; silhouette is undefined for K=1 and K=11, not assigned zero. K=1 and all-singleton trivial stability do not establish meaningful separation.

| K | silhouette | minimum member-code count | interpretation |
|---|---:|---:|---|
|2|0.283434|3|Less separation; poor perturbation stability|
|3|0.316692|2|Best-separated diagnostic candidate, temporally sensitive|
|4|0.275347|1|Lower separation, introduces singleton|
|5–10|0.089669–0.251921|1|Lower separation, singleton groups|

Diagnostic K=3 memberships are **not a frozen runtime mapping**:

| Candidate group | Raw codes |
|---|---|
|1|1,2,3,8,12,14|
|2|5,9,16|
|3|7,15|

These represent5,760,945 observations. Support thresholds50/100/200 give identical membership; excluding codes with fewer than5 represented dates also preserves the partition on common codes. Those results must not be mistaken for temporal robustness.

| Omitted T group | adjusted Rand index | pair co-memberships changed (of55) |
|---|---:|---:|
|T1|0.257871|18 (32.73%)|
|T2|0.369342|19 (34.55%)|
|T3|0.427828|16 (29.09%)|
|T4|0.735031|7 (12.73%)|

The decision does not invent a statistical ARI significance threshold. It weighs the best silhouette against substantial membership changes in three of four temporal perturbations, weaker alternative cuts, and limited independent date support. The full profile may support operational groupings, but the present evidence does not justify describing this particular cut as a stable authoritative taxonomy. An explicit review accepting a temporally sensitive operational partition, or a separately approved stability investigation, is required before freezing it. No K is forced merely because an older analysis used three groups.

## Hourly and low-support evidence

The validated candidate-C hourly artifact was reused, not rebuilt:211 observed cells, total5,779,213, maximum SD3.582856. All are below4. SD<4 is only an internal diagnostic and never selects K.

Available hourly pairwise mean/SD differences provide an independent view of temporal consistency: median normalized distance is0.311799 within candidate groups versus0.373428 between groups. Within-group distances extend to0.574396, overlapping between-group distances. Thus hourly evidence does not erase the observed temporal ambiguity. These comparisons use only shared hours with N>=100 and do not impute or cluster hourly vectors.

| Low-overlap code | N | dates | supported T groups | proposed handling |
|---|---:|---:|---|---|
|13|14,817|4|T1,T4|Explicit pooled fallback; not activated|
|17|495|1|T2|Explicit pooled fallback; not activated|
|21|2,956|1|T3|Explicit pooled fallback; not activated|

Nearest-group distances are retained in `low_support_nearest_group_diagnostics.csv`, but insufficient shared time coverage prevents normal membership assignment. Code16 has four represented dates and only two dates per T group; its high trip count does not establish independent weather-event replication.

## Runtime and fallback status

Required sensitivity version: WEATHER_TIME_CONDITIONED_V2; required sampler: conditional empirical resampling with replacement. Current installed runtime: pooled V2 control. No pooled checkpoint is reinterpreted as conditioned V2.

The existing stronger fallback contract remains weather×T → weather-only → T-only → global, with at least5,000 observations for conditional-support eligibility. This is documented in `../2026-11-14_pricing_v2_weather_clustering_resolved/WEATHER_CLUSTER_VALIDATION.md`; the new task expressly preserves stronger conflicting authoritative rules. N100 governs behavioural feature reliability, not replacement of that runtime threshold. No fallback is activated in this task without a frozen mapping.

`weather_code_group_mapping.csv` accounts for all14 codes but leaves authoritative weather_group blank and labels candidate memberships NOT_APPROVED_FOR_RUNTIME. `weather_grouping_contract.json` records number_of_groups=null and mapping={}, not a deployable empty mapping. No conditional-support manifest/statistics or weather-conditioned baseline CSV is fabricated. Their prerequisite failed, so they have not been created.

## Verification and remaining work

Focused tests cover boundaries, shared-feature distances, normalization, missingness, deterministic linkage/overlap removal, population/moment reconciliation, reused hourly counts, low-support handling, diagnostic selection reproducibility and the blocked launch contract. Applicable existing sensitivity/pricing/routing/simulator/checkpoint suites are run with the prior explicitly scoped commands; unrestricted discovery is not used. Test evidence is in `test_results.txt`, `regression_results.json` and `regression_*.txt`. These do not claim validation of an unimplemented conditional runtime.

The run-local harness remains fail-closed. No training, checkpoint migration, full-day baseline run or protected-date evaluation occurred. The saved pooled fixture/partial baseline evidence remains unchanged. Integration, conditional support construction, full-day fixture/baselines and conditional checkpoint tests are pending a defensible mapping. Do not launch Episode1.

## Key artifacts

- `analyze.py`, `review.py`: reproducible offline calculations and evidence review.
- `weather_code_time_statistics.csv`, `weather_pairwise_distances.csv`, `clustering_distance_matrix.csv`: observed features and distances.
- `weather_cluster_candidates.csv`, `weather_cluster_stability.csv`, `candidate_temporal_membership_changes.csv`: all candidate cuts and perturbations.
- `feature_family_distance_contribution.csv`, `hourly_candidate_consistency.csv`, `reused_weather_hour_diagnostics.csv`: scaling/hourly diagnostics.
- `low_support_nearest_group_diagnostics.csv`, `weather_code_group_mapping.csv`: complete code accounting, explicitly unfrozen.
- `weather_grouping_contract.json`, `analysis_verification.json`, `verification.json`, `runtime_conditioning_verification.json`, `prelaunch_verification.json`: provenance and precise blocked status.

Final test results:18 new grouping tests;32 combined grouping/preparation/gate tests; existing related41, focused57, reconciled broader123 and expanded239 all passed with zero failures/errors. Counts overlap. Conditional integration, checkpoint-isolation and full-day baseline reproducibility tests remain pending because no conditional implementation was activated. Source/runtime/control-fixture hashes were rechecked unchanged after analysis.
