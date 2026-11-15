## Consolidated V2 academic review — 15 November 2026

[Visual and results package](../../review/2026-11-15_v2_methodology_results_review/README.md): current weather/time handling, Episode25 comparisons, Q calibration, and full-day dynamic-value evidence. Dynamic opportunity **MEANINGFUL**, realized evidence **WEAK**, longer-training recommendation **NO**; this latest audit supersedes earlier NONE/CONDITIONAL snapshots below. Reporting coverage gaps are explicitly listed; no completeness claim is made. Episode26 not started; March17–31 untouched.

## Current V2 Episode25 result — 2026-11-15

V1 STATUS: historical, unchanged. V2 SENSITIVITY/RUNTIME: frozen weather/time-conditioned empirical V2, validated; T1 groups and T2–T4 pooled fallback unchanged. V2 TRAINING: COMPLETED Episode25,3200 updates,replay100000,epsilon0.9392. Training16 slots/8h; development48 slots/24h,73,754 frozen March16 requests. Authoritative run: `results/training/pricing_v2_staged_training_001/weather_conditioned/`; latest checkpoint `checkpoints/episode_025`.

EP25 DQN: 59,632 assignments,$1,237,868.21; Highest Feasible: 59,768,$1,261,843.09. Gaps:-136 assignments and$-23,974.88 (-1.9000%). Q calibration POOR; policy stability PARTIAL; demonstrated beneficial dynamic value NONE; charging EXERCISED. Numerical stability and learning signal YES; convergence NO. Checkpoint/accounting resume continuity validated, with missing full slot/transition audit explicitly documented. Tests23/41/57/123/239/2 passed,zero failures/errors. March17–31 untouched.

Current research question: does a below-highest action create beneficial future value? Next step: review bounded state-matched counterfactual diagnostics and evidence gaps before longer training. No Episode26 launched. Full authoritative narrative: [V2 run review](../../../results/training/pricing_v2_staged_training_001/README.md). **V2_STAGE25_REVIEW_REQUIRED**. Earlier status entries below are historical snapshots.

## Detached V2 continuation

TRAINING: RUNNING_IN_BACKGROUND (launch-time status). PID: 11952. Target: Episode25; no Episode26. Resume checkpoint: `/Users/prajwalhk/Keerthi/Implementation/results/training/pricing_v2_staged_training_001/weather_conditioned/checkpoints/episode_001`. Restored Episode1 / 128 updates / replay37,111 / epsilon0.997568; continuation starts Episode2 under the saved episode-boundary environment-seed contract. Episodes2–3 metrics from the interrupted attempt lacked durable learner checkpoints and are preserved in `weather_conditioned/interrupted_attempt_before_resume/`; they are not appended twice to the continued trajectory. Training remains 16×30 minutes (8h); development remains 48×30 minutes (24h). Frozen configuration unchanged.

`weather_conditioned/detached_resume.py` uses an exclusive OS writer lock and independent session, stdin `/dev/null`, and append-only `training.log`. Checkpoint payloads and runtime identities were validated; two focused resume/lock tests pass. Manual monitoring: `results/training/pricing_v2_staged_training_001/weather_conditioned/training_status.json` and `training.log`. No final training results are claimed. March17–31 remains protected.

## Authoritative V2 episode-duration decision

Training retains **16 × 30-minute slots = 8 simulated hours**, for Episodes 1–25 only. Development evaluation retains **48 × 30-minute slots = 24 hours** on the frozen March16 fixture. This preserves the established experimental design rather than introducing episode duration as another V2 variable; it is not a newly optimized horizon. The artificial 8-hour terminal boundary remains an acknowledged modelling limitation. Request-step gamma=0.99 and eight optimizer updates per completed warm slot remain unchanged. The full-day development trajectory provides fixed policy comparisons. Learner seed is 42; development seed is 424242; training uses the persisted per-episode seeds. March17–31 remains protected. Launch is authorized following verification; no training completion is claimed here.

# Current-State Hierarchical RL Implementation Review

## Current V2 conditional launch gate — 14 November 2026

**READY_TO_LAUNCH_V2_STAGE25. TRAINING: NOT YET STARTED.** This supersedes prior pending-baseline and global-mapping blockers. V2 sensitivity is WEATHER/TIME CONDITIONED with TIME-SPECIFIC grouping. T1_G1={1,2,3,5,7,8,9,12,14,16}, T1_G2={13,15}; T2/T3/T4 use explicit T_GROUP_POOLED_FALLBACK. Global pooled V2 remains CONTROL/FALLBACK. The retained support threshold and four fallback levels remain documented; undersized T1_G2 uses raw-weather fallback. All48 March16 slots completed for highest/lowest/neutral policies and exact repeats;73,754 requests per run. The conditioned fixture, supports, mapping, checkpoints and future harness are hash/version bound. No training or March17–31 access occurred. See `results/training/pricing_v2_staged_training_001/weather_conditioned/README.md` and `results/analysis/2026-11-14_pricing_v2_time_specific_weather/README.md` for full evidence. Stop here; do not launch Episode1 in this task.

## Current V2 time-specific weather conditioning — 14 November 2026

**V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_BASELINES_PENDING. TRAINING: NOT YET STARTED.** This supersedes the global-mapping instability blocker. The permanent global mapping was not forced into runtime.

V2 SENSITIVITY: WEATHER/TIME CONDITIONED. WEATHER GROUPING: TIME-SPECIFIC. SAMPLING: CONDITIONAL EMPIRICAL RESAMPLING. POOLED V2: CONTROL/FALLBACK.

Frozen T1 groups: T1_G1={1,2,3,5,7,8,9,12,14,16}; T1_G2={13,15}. T2/T3/T4 use explicit T_GROUP_POOLED_FALLBACK because no candidate passed the within-time separation/stability rule. T boundaries remain00–03/04–05/06–15/16–23. Codes17/21 have no T1 assignment. Every raw code/T pair has explicit handling in `results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_group_mapping.csv`.

T1 K2 silhouette0.671885, median/P10 perturbation ARI1.0/0.569454. Exact T1_G1 support N431,018; T1_G2 N1,669 falls below the retained5,000 runtime gate and uses same-raw-code pooled fallback. Other levels are T-pooled then global. Explicitly ungroupable T groups use T-pooled directly. Global N5,779,213, frozen references and denominator rule are unchanged.

The separate versioned provider is integrated; pooled checkpoints are not conditional checkpoints. The conditioned March16 fixture contains73,754 reproducible context/support/draw records. Full-day conditioned baseline repeats are still pending; no launch readiness is claimed. No DQN training or protected March17–31 data access occurred. V1 historical artifacts remain untouched.

Analysis: `results/analysis/2026-11-14_pricing_v2_time_specific_weather/README.md`. Conditioned preparation: `results/training/pricing_v2_staged_training_001/weather_conditioned/`. The pooled fixture/partial baseline remains control evidence in its original folder.

## Current V2 weather-conditioning decision — 14 November 2026

**V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_TEMPORAL_CLUSTER_INSTABILITY. TRAINING: NOT YET STARTED.** This supersedes the earlier representation blocker; the representation is now resolved.

Required sensitivity: WEATHER/TIME CONDITIONED. Representation: unscaled T1–T4 behavioural mean/SD, average linkage using normalized shared-feature Euclidean distances, minimum3 shared supported groups (N>=100). Sampling remains intended CONDITIONAL EMPIRICAL RESAMPLING; global pooled support is CONTROL/FALLBACK only. The installed pooled runtime has not been relabelled as conditional.

No final weather mapping is frozen. Best-separated diagnostic K=3: candidate1={1,2,3,8,12,14}, candidate2={5,9,16}, candidate3={7,15}. Codes13,17,21 lack temporal overlap and have proposed explicit fallback handling. The candidate silhouette is0.316692, but omitting T1/T2/T3 changes29–35% of pair co-memberships (ARI0.258–0.428). Support-threshold stability alone does not justify a final freeze. Larger cuts have lower separation and singleton groups. **These memberships are diagnostic, not runtime assignments.**

Existing stronger fallback policy is weather×T → weather-only → T-only → global, with5,000-observation support eligibility; N100 is the feature diagnostic. No conditional support is activated. March16 weather-conditioned fixture/baselines: NOT CREATED because mapping freeze failed. Pooled fixture/partial-run evidence remains control history. Harness: BLOCKED before provider or fixture loading. March17–31 untouched; V1 unchanged. No DQN training or full-day simulation was launched in this grouping task.

Evidence: `results/analysis/2026-11-14_pricing_v2_weather_time_conditioning/README.md`. Next: review whether the observed temporal instability is acceptable for an explicitly operational partition, or authorize a bounded alternative stability analysis. Do not silently select K by silhouette alone. Conditional integration and launch validation remain pending.

## Authoritative weather-conditioning launch gate — 14 November 2026

**V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_NOT_READY. TRAINING: NOT YET STARTED.** This status supersedes the preparation-only and historical preflight statuses below.

Required V2 sensitivity: **WEATHER/TIME CONDITIONED**, with **CONDITIONAL EMPIRICAL RESAMPLING**. The implemented pooled provider and any pooled fixture/baseline preparation are **POOLED_V2_CONTROL** only, not authoritative training evidence. Weather-conditioned March16 baselines, conditional supports and a frozen weather mapping do not yet exist. No training launch is authorized. The pooled baseline process was interrupted for this changed requirement; its fixture and partial evidence are preserved, with zero completed baseline pairs claimed.

The latest reviewed clustering representation is `SCENARIO_MEAN_SD_FROM_INDIVIDUAL_OBSERVATIONS`: one unscaled pooled mean/SD pair per raw weather code, Euclidean average linkage. It explicitly classifies hourly vectors as historical. Its final mapping is header-only, predates the corrected denominator population, and cannot be reused as an accepted mapping. The new time-preserving requirement therefore needs a representation decision; no hourly-to-T-group conversion has been silently adopted. A replacement numerical rule for choosing K is also needed after removing the old SD acceptance gate. SD<4 is now an internal stability diagnostic only.

Existing T groups are T1=[00,04), T2=[04,06), T3=[06,16), T4=[16,24). Existing support policy is at least5,000 observations, with weather×time → weather-only → time-only → global fallback. This differs from the shorter example hierarchy in the addendum; existing decisions are retained pending a valid mapping. No semantic grouping, forced K=3, imputation or parametric refit has been introduced.

Next: resolve the representation/cluster-selection contract, validate a mapping on the corrected Jan1–Mar15 population, create conditional supports with date coverage and hashes, integrate auditable per-request draws and version-isolated checkpoints, then freeze the conditional full-day fixture and reproducible baselines. Only after focused/regression tests and documentation pass can launch readiness be reconsidered. March16 remains development-only; March17–31 remains untouched. No V1 historical artifact or frozen sensitivity reference was changed.

Preparation tests passed:14 new orchestration/fixture/launch-gate unit tests; existing related41, focused57, broader123 and expanded239 tests also passed. These are pooled/preparation checks, **not conditional-sampler validation**. See `weather_conditioning_launch_gate.json` and `prelaunch_verification.json` in the run folder.

## Current V2 preflight reconciliation — 14 November 2026

V2 TRAINING STATUS: **V2_TRAINING_BLOCKED_FULL_DAY_FIXTURE_AND_EXECUTION_HARNESS_NOT_PREPARED**; **TRAINING_NOT_YET_STARTED**. Historical test-contract conflicts are resolved with test/fixture-only changes. Focused57, exact broader123 and expanded applicable239 tests pass with zero failures/errors/skips. No production behavior or any of the six recorded V2 hashes changed. Contract/support/source hashes and48 March16 snapshots pass recheck. Unrestricted historical discovery is not certified safe and was not run.

Remaining blocker: no frozen full-day V2 request/epsilon/fleet fixture, reproducible full-day baselines or automated fresh25-episode harness/effective run config yet exists. Prepare and validate those prerequisites next; no training or baseline recomputation was authorized in this reconciliation task. V1 remains historical; V2 runtime remains INTEGRATED_VALIDATED_NOT_TRAINED. March17–31 remains untouched. See [reconciliation report](../../training/pricing_v2_staged_training_001/README.md).


## Latest pricing status

See the [canonical V1 README](../2026-11-07_passenger_sensitive_pricing_v1/README.md) for all methodology and results. Training through Episode25: technical PASS, numerically stable, learning signal YES; policy stability NO, convergence NO. Action-dominance risk HIGH; dynamic value UNRESOLVED. Further training AWAITING_ACADEMIC_REVIEW. Protected final evaluation untouched.

This pricing documentation update does not reassess other subsystem status. Earlier numerical review artifacts remain unchanged in this folder.

## Current V2 launch gate — 14 November 2026

V2 empirical sensitivity runtime remains INTEGRATED_VALIDATED_NOT_TRAINED. Fresh Episodes1–25 did not launch:57 focused tests pass, but111 broader preflight tests report2 failures and7 errors involving outdated fixtures/contracts. No new checkpoint, full-day benchmark or learning result exists. V1 remains historical; protected March17–31 remains untouched. Reconcile test contracts and rerun preflight before launch. [Evidence and next steps](../../training/pricing_v2_staged_training_001/README.md).


## V2 full-day dynamic-value audit — 15 November 2026

[Audit and evidence](../2026-11-15_pricing_v2_dynamic_opportunity_audit/README.md): the exact Episode25 March16 replay screened 15,800 lower-price choices. Immediate assignment divergence occurs in 33.82%; 20 genuinely divergent cases were rolled across two boundaries, alongside two eligibility-only comparisons and two passing identical-action controls. One partial recovery, one full recovery, and zero net-positive cases were observed. Q favored the lower action in all 20, but was incorrect in 19 with one undiscounted tie; all 20 discounted comparisons were unfavorable.

DYNAMIC_VALUE_OPPORTUNITY = **MEANINGFUL** (immediate state changes); DYNAMIC_VALUE_EVIDENCE = **WEAK** (bounded recovery, no net gain); LONGER_TRAINING_RECOMMENDATION = **NO** on the present evidence. These supersede the earlier bounded-review NONE/CONDITIONAL evidence and recommendation. The chronological sample does not cover every hour or the peak-demand quartile and is not proof of global Highest Feasible dominance. Do not simply extend training; any further investigation requires a separate scoped decision. Episode26 remains **NOT_STARTED**. March17–31 remains **UNTOUCHED**. No production, calibration, training or baseline artifact was changed by this audit.
