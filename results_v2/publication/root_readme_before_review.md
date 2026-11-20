## Historical checkpoint consolidation — 2026-11-18

Retired 134 superseded V3 per-slot recovery payload sets (938 files; 219.43 GiB allocated). Repository allocation fell from approximately327.22 to107.65 GiB. Completed episode checkpoints, authoritative Episode10, review metrics, manifests, current CNN comparisons and all current research evidence remain. Retired slot directories contain metadata/tombstones and are no longer resumable. No active configuration was redirected. Twelve bounded tests and four retained-model loading checks passed. See `results_v2/repository_maintenance/2026-11-18_checkpoint_consolidation/README.md` for exact deletions, retention policy and unresolved candidates.

## Storage maintenance and final-Softplus CNN — 2026-11-18

Controlled cleanup removed only 180 untracked unopened bytecode files (2.35 MiB); protected research artifacts remain. Large V3 checkpoint families require an explicit retention decision. One fresh seed42 output-only Softplus run selected epoch42 and stopped at52. Validation MAE/RMSE 7.013677/26.027186 modestly improves ReLU 7.107571/26.145924 but remains worse than historical-average 3.518426/18.226779. Thirty-two focused tests passed. Weather availability remains assumed; March17–31 untouched; no March12 prospective promotion or DQN training. Evidence: `results_v2/cnn_demand/2026-11-18_softplus_causal_research_training/README.md` and `results_v2/repository_maintenance/2026-11-18_safe_cleanup/README.md`. Next: bounded no-training near-zero/feature-scale diagnosis.

## Corrected causal-research CNN — 2026-11-18

One bounded seed-42 run completed: best epoch 50, early stopping at 60. CNN validation MAE/RMSE 7.107571/26.145924 versus causal historical-average 3.518426/18.226779. March16 development also favors the baseline. The new checkpoint is research-only under the assumed 120-minute weather protocol; March17–31 remains protected. Its March1–15 model-selection lineage is incompatible with the February28-cutoff prospective March12 run. No runtime behavior was changed. See `results_v2/cnn_demand/2026-11-18_causal_research_training/README.md`. Next: bounded residual diagnosis, not DQN training.

## Routing-to-pricing coupling validation — 2026-11-18

Bounded validation confirms that next-slot global routing probabilities enter the nine routing dimensions of the 13D OD pricing state and change unchanged-network Q outputs. Private utility still chooses physical driver actions. The prior fully exploratory, zero-pricing-update control therefore need not differ in assignments or revenue. Fifteen focused tests passed; no training was initiated. Evidence: `results_v2/federated_learning/2026-11-18_hierarchical_coupling_validation/README.md`. A frozen, separately authorized joint-learning protocol remains the next step.

## Online-routing reproducibility and control — 18 November 2026

The RNG discrepancy was the separately unseeded TensorFlow global Generator.
Research-run initialization now seeds it once; resume restores it. Historical
runtime behavior and scientific settings are unchanged. All 50 focused tests
passed. The four-slot learned run, independent repeat and checkpoint/resume
matched exactly, including RNG state. The matched no-update control completed:
routing probabilities changed, but dispatch/revenue/movement aggregates did not.
There were 19,342 genuine local updates and four NONPRIVATE FedAvg rounds;
pricing optimization remained disabled. No policy-improvement claim is made.
[Evidence and limitations](results_v2/federated_learning/2026-11-17_online_routing_rng_retry_002/README.md).

## Online-routing retry 001 — 17 November 2026

The mixed-fleet arrival reserve guard now exempts explicit non-EVs while retaining
historical EV safety. All 46 focused tests passed. The four-slot real-data run
completed with 19,342 genuine local updates and four equal-client NONPRIVATE
FedAvg rounds; checkpoint/resume matched exactly. The independent fresh repeat
stopped at slot1 because only the global RNG fingerprint differed. All other
compared state fingerprints matched. The no-update control was not run.
Pricing optimization remains disabled. Next: resolve RNG-state reproducibility
before continuing the bounded validation; no extended training is authorized.
[Retry evidence](results_v2/federated_learning/2026-11-17_online_routing_retry_001/README.md).

## Bounded online-routing attempt — 17 November 2026

The first real-data mixed-fleet attempt passed provenance/startup checks but
stopped before completing slot 1 at the post-arrival station-reserve guard.
An isolated regression confirms that this guard incorrectly applies EV battery
requirements to non-EVs. No routing or pricing optimizer update occurred.
Control/repeat/resume were not run after the safety stop. Forty existing tests
passed; the new non-EV arrival regression fails while the EV rejection passes.
Production code and historical artifacts are unchanged. Next: correct arrival
reserve applicability, preserve EV safety, and retry the bounded protocol.
[Attempt evidence](results_v2/federated_learning/2026-11-17_online_routing_experiment/README.md).

## Prospective online routing — 17 November 2026

A fresh-only routing initialization and online-experience provenance contract now
supports the versioned equal-client next-slot FedAvg interface. Historical learned
lineage remains rejected; prior sample-weighted and utility modes are preserved.
Updates remain off by default. Validation uses synthetic parameter updates and
small fixtures, with no gradient training or experiment launch. FedAvg is nonprivate;
weather availability and development-tuning limitations remain.
[Contract and evidence](results_v2/federated_learning/2026-11-17_prospective_online_routing/README.md).

## Hierarchical research interfaces — 17 November 2026

Opt-in driver-local routing/FedAvg lifecycle, deterministic mixed-EV composition
and a thin Gymnasium OD adapter are implemented and fixture-tested. Updates are
disabled by default; FedAvg is explicitly nonprivate. Historical V3 and the
non-learned research baseline remain available. Learned prospective activation
still requires an online-policy provenance contract. No training experiment ran.
[Architecture and bounded evidence](results_v2/simulation/2026-11-17_hierarchical_interfaces/README.md).

## Prospective utility-baseline acceptance — 17 November 2026

The opt-in non-learned private-utility routing baseline completed March12’s four-slot
engineering acceptance with 5,000 vehicles and January–February sensitivity.
All 4,137 eligible requests reconciled; 996 assignments produced $21,934.5083968848.
Deterministic repeat/resume and 48 focused tests passed; no training occurred.
The earlier learned-routing lineage remains blocked and unchanged. This research
baseline does not establish policy effectiveness or verified weather availability.
[Evidence](results_v2/simulation/2026-11-17_prospective_utility_acceptance/README.md).

## Prospective OD information cutoff — 17 November 2026

The versioned January–February request-weighted sensitivity calibration contains
5,457,435 observations (weighted mean 1.725916, population SD 0.426314).
Prospective startup is **blocked**: the routing snapshot’s direct updates end
before March12, but its generated training requests inherit CNN model selection
using March1–15 validation. The new information guard rejects this lineage.
No prospective replay or training ran; earlier retrospective acceptance evidence
remains unchanged. Grouping/reference choices remain development-tuned.
[Cutoff evidence and next step](results_v2/simulation/2026-11-17_prospective_acceptance_v1/README.md).

## Real-data OD acceptance gate — 17 November 2026

March12 00:00–02:00 NY bounded research acceptance completed all four slots and
4,137 eligible requests. Explicit `VALID_UNSEEN_OD_REFERENCE_PRICE_V1` served two
January-unseen pairs at factor 1.0, without expanding support or adding fallback
DQN transitions. Total revenue $22,254.5750635514 includes $44.7083968848 fallback
revenue. Repeat/resume passed; no training occurred. January historical-average
forecasts are a labeled baseline, not trained CNN output. Frozen sensitivity remains
retrospectively calibrated through March15; prospective information timing remains
unresolved. [Preflight evidence](results_v2/simulation/2026-11-17_end_to_end_acceptance/FALLBACK_ACCEPTANCE.md).

## UTC OD research runtime

`OD_AWARE_UTC_ELAPSED_V1` now integrates UTC request/event flow, master mathematics
and checkpoint restoration through the inherited engine. DST trip, charging and
repositioning checks pass; 42 bounded tests passed. Historical V3 is unchanged.
Operational forecasts remain blocked by unverified weather availability; no training
was performed. [Evidence and input contract](results_v2/simulation/2026-11-17_utc_od_runtime/README.md).

## Earlier OD mathematical correction status (temporal limitation superseded)

Opt-in `master_math=True` implements previous-mean absolute-deviation EWMA and
half squared Bellman loss. UTC boundary helpers are tested, but the inherited
engine/ledger clock migration remains incomplete. Operational startup fails closed;
no training started. Historical V3 is unchanged.
[Contract, validation and exact remaining work](results_v2/simulation/2026-11-17_master_math_temporal/README.md).

A separate observation-persistence CNN baseline now uses UTC source labels, shared
NY elapsed-time mapping and an explicit 120-minute assumed availability lag.
Publication/vintage provenance remains unverified; operational export is blocked.
Historical CNN, OD and weighted sensitivity remain unchanged.
[Protocol and validation](results_v2/cnn_demand/2026-11-17_observation_persistence/README.md).

# Master-alignment implementation status

The methodology authority is `notebooks/plan/masterdocument/MASTER DOCUMENT1.docx`
(16 November 2026). Opt-in `FEASIBLE_OD_PRICING_V1` adds a shared 13D DQN with
origin–destination states/actions/replay and preserves `SUCCESSFUL_DISPATCH_REWARD_V1`.
The January observed-support mask contains 9,572 pairs. Assignment-only rewards
reconcile across request, OD, environment and replay. Historical V3 is unchanged.

New OD full-runtime checkpoints use `FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_3`, including
optimizer/replay/RNG, fleet, operational state and feasibility metadata; historical
15D or incompatible reward checkpoints are rejected. The earlier reward-only
adapter still has learner-only checkpoints. No training was performed.

[OD implementation and commands](src/pricing/README.md) ·
[OD validation](results_v2/pricing_dqn/2026-11-17_feasible_od_validation/README.md) ·
[earlier reward validation](results_v2/pricing_dqn/README.md).

The new primary `HISTORICAL_REQUEST_REPLAY_V1` protocol uses eligible observed
pickups, independently of CNN forecasts, with versioned demand-cursor persistence.
Historical V3 forecast-driven generation remains unchanged.
[Protocol and reproduction](src/simulation/README.md) ·
[Replay validation](results_v2/simulation/2026-11-17_historical_request_replay/README.md).

Remaining master gaps include unsupported-OD handling, stricter OD significance,
empirical pricing bounds, observed-pickup proxy limitations, sensitivity/weather support, CNN information availability,
EWMA deviation, Bellman loss and full hierarchy/privacy integration.

Repository conventions: `src/` implementation, `scripts/` execution, `config/`
configuration, `tests/` validation, `models/` checkpoints, `data/` datasets,
`notebooks/` specifications, `results/` historical evidence, and `results_v2/`
new master-alignment evidence. Use snake_case paths/functions, PascalCase classes,
UPPER_SNAKE_CASE constants and dated descriptive run directories. Preserve history.

Provisional `PROVISIONAL_BINNED_EMPIRICAL_SENSITIVITY_V1` is opt-in for the OD
runtime. It preserves common references and existing weather/T1–T4 groups;
continuous Temperature/WindSpeed conditioning and final calibration remain open.
Historical V3 stays the default. [Evidence, limitations and tests](results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/README.md).

[Bounded calibration decision evidence](results_v2/passenger_sensitivity/2026-11-17_methodology_decision/README.md) compares bin weighting, references, temporal weather evidence and acceptance. No final calibration or active behavior changed.

Approved request-count weighting is implemented as explicit
`REQUEST_COUNT_WEIGHTED_BINNED_SENSITIVITY_V1`, with finite empirical resampling,
unchanged provisional references and historical-mode preservation.
[Weighted contract and validation](results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration/README.md). No training performed.

[CNN timing correction](results_v2/cnn_demand/2026-11-17_causal_timing/README.md) provides chronological history, explicit one-slot-ahead timestamps and DST-safe civil-time handling. The versioned dataset is oracle-weather-only; operational weather availability and timezone alignment remain unresolved. No training or forecast replacement occurred.

# Historical V3 review status

<!-- V3_REVIEW_CURRENT_BEGIN -->
SOURCE_ALIGNED_SLOT_PRICING_V3 = PAUSED_AFTER_EPISODE10_FOR_REVIEW (scientific review scope; not a claim that a live process was stopped).

AUTHORITATIVE_EPISODES = 1–10
TRAINING_WINDOW = 2026-03-01 00:00 → 2026-03-04 07:30
FINAL_RUNTIME_TIMESTAMP = 2026-03-04 08:00:00
EP01_EP10_REQUESTS = 293819
EP01_EP10_ACCEPTED = 67908
EP01_EP10_REJECTED = 225911
EP01_EP10_ASSIGNMENTS = 53357
EP01_EP10_ACCEPTED_UNMATCHED = 14551
EP01_EP10_ACCEPTED_REVENUE_USD = 1727639.7333333334
REPLAY_SIZE = 22720
OPTIMIZER_UPDATES = 1224
EPSILON = 0.9767440000000001
AUTHORITATIVE_CHECKPOINT = models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10/episode_010
POST_EP10 = POST_EP10_UNPLANNED_CONTINUATION_NOT_USED_FOR_REVIEW; PRESERVED_AS_PROVENANCE_NOT_USED; NOT_AUTHORIZED_FOR_REVIEW.
MARCH17_31 = UNTOUCHED
BROADER_REGRESSION_BASELINE = 181 passed / 0 failed / 0 errors (existing evidence, not rerun).
NEXT_STEP = ACADEMIC_REVIEW_OF_EPISODE1_TO_10_RESULTS
<!-- V3_REVIEW_CURRENT_END -->

Primary review: results/analysis/2026-11-15_source_aligned_slot_pricing_v3/review_ep01_ep10/README.md

## Completed implementation chronology

Methodology/fare/fitted-family freeze → V3 implementation and bounded validation → historical regression isolation (181-pass baseline) → full-runtime checkpoint equivalence → Episode1 complete → Episodes2–10 complete → authoritative scientific review at Episode10. Earlier readiness/blocked statements are historical, superseded snapshots. No current regression/checkpoint blocker is asserted.

## Historical development context (not current status)

## Consolidated V2 academic review — 15 November 2026

[Visual and results package](results/review/2026-11-15_v2_methodology_results_review/README.md): current weather/time handling, Episode25 comparisons, Q calibration, and full-day dynamic-value evidence. Dynamic opportunity **MEANINGFUL**, realized evidence **WEAK**, longer-training recommendation **NO**; this latest audit supersedes earlier NONE/CONDITIONAL snapshots below. Reporting coverage gaps are explicitly listed; no completeness claim is made. Episode26 not started; March17–31 untouched.

## Current V2 Episode25 result — 2026-11-15

V1 STATUS: historical, unchanged. V2 SENSITIVITY/RUNTIME: frozen weather/time-conditioned empirical V2, validated; T1 groups and T2–T4 pooled fallback unchanged. V2 TRAINING: COMPLETED Episode25,3200 updates,replay100000,epsilon0.9392. Training16 slots/8h; development48 slots/24h,73,754 frozen March16 requests. Authoritative run: `results/training/pricing_v2_staged_training_001/weather_conditioned/`; latest checkpoint `checkpoints/episode_025`.

EP25 DQN: 59,632 assignments,$1,237,868.21; Highest Feasible: 59,768,$1,261,843.09. Gaps:-136 assignments and$-23,974.88 (-1.9000%). Q calibration POOR; policy stability PARTIAL; demonstrated beneficial dynamic value NONE; charging EXERCISED. Numerical stability and learning signal YES; convergence NO. Checkpoint/accounting resume continuity validated, with missing full slot/transition audit explicitly documented. Tests23/41/57/123/239/2 passed,zero failures/errors. March17–31 untouched.

Current research question: does a below-highest action create beneficial future value? Next step: review bounded state-matched counterfactual diagnostics and evidence gaps before longer training. No Episode26 launched. Full authoritative narrative: [V2 run review](results/training/pricing_v2_staged_training_001/README.md). **V2_STAGE25_REVIEW_REQUIRED**. Earlier status entries below are historical snapshots.

## Detached V2 continuation

TRAINING: RUNNING_IN_BACKGROUND (launch-time status). PID: 11952. Target: Episode25; no Episode26. Resume checkpoint: `/Users/prajwalhk/Keerthi/Implementation/results/training/pricing_v2_staged_training_001/weather_conditioned/checkpoints/episode_001`. Restored Episode1 / 128 updates / replay37,111 / epsilon0.997568; continuation starts Episode2 under the saved episode-boundary environment-seed contract. Episodes2–3 metrics from the interrupted attempt lacked durable learner checkpoints and are preserved in `weather_conditioned/interrupted_attempt_before_resume/`; they are not appended twice to the continued trajectory. Training remains 16×30 minutes (8h); development remains 48×30 minutes (24h). Frozen configuration unchanged.

`weather_conditioned/detached_resume.py` uses an exclusive OS writer lock and independent session, stdin `/dev/null`, and append-only `training.log`. Checkpoint payloads and runtime identities were validated; two focused resume/lock tests pass. Manual monitoring: `results/training/pricing_v2_staged_training_001/weather_conditioned/training_status.json` and `training.log`. No final training results are claimed. March17–31 remains protected.

## Authoritative V2 episode-duration decision

Training retains **16 × 30-minute slots = 8 simulated hours**, for Episodes 1–25 only. Development evaluation retains **48 × 30-minute slots = 24 hours** on the frozen March16 fixture. This preserves the established experimental design rather than introducing episode duration as another V2 variable; it is not a newly optimized horizon. The artificial 8-hour terminal boundary remains an acknowledged modelling limitation. Request-step gamma=0.99 and eight optimizer updates per completed warm slot remain unchanged. The full-day development trajectory provides fixed policy comparisons. Learner seed is 42; development seed is 424242; training uses the persisted per-episode seeds. March17–31 remains protected. Launch is authorized following verification; no training completion is claimed here.

# Ride-Hailing Platform Simulation

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

Remaining blocker: no frozen full-day V2 request/epsilon/fleet fixture, reproducible full-day baselines or automated fresh25-episode harness/effective run config yet exists. Prepare and validate those prerequisites next; no training or baseline recomputation was authorized in this reconciliation task. V1 remains historical; V2 runtime remains INTEGRATED_VALIDATED_NOT_TRAINED. March17–31 remains untouched. See [reconciliation report](results/training/pricing_v2_staged_training_001/README.md).


## Current V2 training status — 14 November 2026

V2 sensitivity is reviewed and runtime-integrated with exact empirical resampling; runtime status remains INTEGRATED_VALIDATED_NOT_TRAINED. The authorized fresh Episodes1–25 run has **not started**: broader preflight found test/fixture-contract conflicts (111 tests,2 failures,7 errors), although57 focused tests pass and all six recorded runtime implementation hashes match. No new V2 checkpoint or full-day benchmark exists. Learning, calibration and dynamic-value results remain unavailable. V1 Episode25 is historical and unchanged. March17–31 remains untouched.

See the [authoritative launch-gate report](results/training/pricing_v2_staged_training_001/README.md). Next: reconcile stale test fixtures/contracts without weakening invariants, rerun preflight, then complete the fixed full-day fixture and automated execution harness. Status: **V2_TRAINING_BLOCKED_PREFLIGHT_TEST_CONTRACT_CONFLICT**. Earlier READY_FOR_V2_TRAINING described bounded smoke validation, not a passing broader training gate.

## Passenger-Sensitive Pricing V1

Canonical documentation: [Passenger-Sensitive Pricing V1](results/analysis/2026-11-07_passenger_sensitive_pricing_v1/README.md).
Methodology, sensitivity sampling and request-level architecture are frozen.
Bellman semantics are corrected and frozen.
Authoritative staged training completed through Episode25.
Technical invariants PASS; numerically stable with learning signal.
Policy stability NO; convergence NO.
Action-dominance risk HIGH; DQN incremental dynamic value UNRESOLVED.
Further training AWAITING_ACADEMIC_REVIEW; no continuation authorized.
March16 is development-only; March17–31 remains protected and untouched.
Earlier pricing descriptions below are historical, not current run instructions.

## Prior project status — 1 November 2026

Final CNN implementation/evaluation is complete; the historical baseline remains superior. Passenger acceptance and driver/EV contracts are frozen. Final temporal routing is frozen and ready for pricing, with modest/uncertain positive aggregate signal and weak rare-action performance. Pricing DQN is implemented; authoritative8-update results are reviewed through episode25, **not converged**. Conditional model-only DP routing variants and conservative RDP accounting are complete; trusted raw diagnostics are not DP releases. Historical sections below retain earlier statuses as provenance; this prior summary is superseded for pricing by the dated Version-1 status above.

### Current Resume Point

Authoritative pricing training is paused for current-state academic review. [Current-state review package](results/analysis/2026-11-01_current_state_review/README.md) consolidates saved evidence through episode25. Later partial episode26 is preserved and excluded. No pricing training was resumed by the DP routing comparison. March17–31 untouched.

### Routing Model Status

FINAL_ROUTING_MODEL_FROZEN=YES; ROUTING_READY_FOR_PRICING=YES. Qualification: MODEST / UNCERTAIN BUT POSITIVE. The current temporal freeze supersedes earlier readiness-NO descriptions.

### Pricing Model Status

Methodology-faithful500×16×8 protocol unchanged. Preliminary25-episode findings show worsening terminal calibration, increasing bootstrap dominance and deteriorating fixed development revenue/assignments between episodes10 and25. No final policy or convergence is claimed. Accelerated128-update results remain diagnostic only.

### Open Methodology Decisions / Next Step

Non-private temporal routing remains frozen. [DP routing comparison](results/analysis/2026-11-01_differential_privacy_comparison/README.md) completes three isolated privacy variants, RDP accounting and before/after held-out comparison. Pricing DQN remains preliminary/non-converged and paused. Secure aggregation, robustness/attack evaluation and production privacy hardening remain pending. March17–31 untouched.

## 1. Project overview

This modular research implementation studies NYC ride-hailing demand forecasting, passenger acceptance, fleet dispatch/movement, EV charging, utility-based repositioning, federated routing-policy learning and dynamic pricing. The active source period is **January–March 2026**. Offline demand prediction and online operations share a versioned spatial/temporal contract.

The pricing DQN is the pricing learning component. Lower-level U1/U2/U3 rules select driver/EV movements; a separate routing network learns these decisions. Plain sample-weighted FedAvg aggregates local routing models, whose nine masked probabilities feed the pricing state. Routing probabilities do not replace utility-selected movement. Privacy/security and adversarial layers remain later research stages.

NB1–NB13 implementation history remains useful provenance. Legacy January-only, LinUCB, 1,213-grid and five-action results are not final-system performance evidence. The former 298-slot experiment is superseded by the chronological protocol below.

## 2. Current implementation status

| Component | Status | Current scope |
| --- | --- | --- |
| Jan–Mar spatial/data foundation | COMPLETE / FROZEN | 11,006,194 requests; true 3 km, 142 grids |
| CNN preprocessing/training/inference | COMPLETE | TRAIN-only preprocessing; epoch 200; historical-average baseline remains superior |
| Record-029 and final analytical weather scenarios | FROZEN OFFLINE | Signed descriptive sensitivity; separate from runtime behavioural E |
| Fleet, empirical requests, FCFS dispatch | IMPLEMENTED / INTEGRATION VALIDATED | 5,000 vehicles; intact January empirical trip sampling driven by forecasts |
| Operational grid state | FROZEN / VALIDATED | Causal mu, sigma, F_hat, H_hat |
| Driver/EV utilities and timed charging | IMPLEMENTED / VALIDATED | Nine actions, multihop charging, no teleportation |
| Routing architecture and plain FedAvg | IMPLEMENTED | 169→64→32→9; selected real-data FedAvg; probability adequacy fails |
| Pricing contract and DQN | IMPLEMENTED / VALIDATED | Identity-normalized 13D state; seven actions |
| Final hierarchical runner | STARTUP / SHORT EPISODE VALIDATED | Public final interfaces; legacy runner isolated |
| March-16 four-slot episode | COMPLETE, INTEGRATION ONLY | One optimizer update; checkpoint quarantined |
| Passenger-arrival boundary correction | COMPLETE / VALIDATED | Absolute-time completion selection; 9 focused tests |
| Simulator-derived routing collection | COMPLETE | 720/720 slots; 3,257,840 clean reachability experiences |
| Routing/FedAvg and pricing training | COMPLETED RUNS / LIMITATIONS | Routing probability gate fails; pricing schedule mismatch; no final baseline |
| Protected hierarchical evaluation | PENDING | March 17–31, no updates |
| Privacy, security, robustness and final ablations | PENDING | Not implied by plain single-process FedAvg |

## 3. High-level architecture

```text
Yellow Taxi + Taxi Zones + Meteostat
    -> true 3 km / half-hour aggregation -> CNN J_hat
    -> pricing state [demand, dispatch history, incoming, routing p, popularity]
    -> pricing DQN -> offered fare -> behavioural-E passenger acceptance
    -> FCFS dispatch -> passenger/vehicle movement and timed charging
    -> completed-slot operational mu / sigma / F_hat / H_hat
    -> U1/U2/U3 driver decisions -> local routing-policy learning
    -> plain sample-weighted FedAvg -> global routing probabilities
    -> next pricing state / assignment-time reward / replay
    -> later privacy, security and robustness experiments
```

NB11 supplies utility labels, NB12 learns masked routing probabilities, and NB13 aggregates weights/counts. Pricing DQN learns Q-values over fare factors. These are different learning and decision responsibilities.

## 4. Repository layout

```text
config/                 Runtime configuration
data/raw/               Externally supplied taxi and taxi-zone inputs
data/interim/           Reserved intermediate data area
data/processed/         Versioned stage artifacts (grid, weather, demand, CNN, stations)
models/demand/          Legacy NB5 provenance
models/cnn/             Final 3-km CNN checkpoints
models/routing/         Frozen NB12/NB13 common initialization and metadata
models/pricing/         Legacy pricing artifacts
models/pricing_dqn/     Preserved fixtures and completed schedule-mismatched pricing run
models/routing_policy/ Selected simulator-derived FedAvg and legacy checkpoints
outputs/figures/        NB5 figures
outputs/metrics/        Reserved metrics outputs
outputs/logs/           Reserved execution logs
results/validation/     Historical engineering/production validation
results/analysis/       Dated authoritative module/status reports
src/                    Importable implementation packages
scripts/                Stage build, validation, and deterministic demonstration scripts
tests/                  Unit tests using small synthetic/deterministic fixtures
notebooks/legacy/       Unmodified legacy notebooks, when supplied
notebooks/plan/         Implementation and charging planning documents/reference paper
```

Important source packages:

| Package | Responsibility |
| --- | --- |
| `src/data/` | YAML configuration, taxi loading/filtering, legacy-compatible weather handling |
| `src/spatial/` | Grid construction, zone/grid mapping, neighbours, persisted spatial artifacts |
| `src/demand/` | Demand aggregation/contracts, NB4 tensors, NB5 model, inference |
| `src/fleet/` | Vehicle state, fleet transitions, and grid supply |
| `src/dispatch/` | Request state, empirical OD generation, deterministic dispatch |
| `src/simulation/` | Grid/main-slot operational statistics and EWMA state |
| `src/charging/` | EV energy operations and charging station infrastructure |
| `src/routing/` | NB11 utility routing, NB12 local policy learning, and NB13 policy FedAvg |
| `src/pricing/` | Standalone pricing context, LinUCB, customer acceptance, and revenue payoff |

## 5. Data and external inputs

The demand population uses existing valid-zone preparation, **not** Record-029 fare/distance cleaning. Source-file month and actual pickup month differ at boundaries; the following are pickup-calendar-month counts.

| Month | Source requests | Half-hour slots |
| --- | ---: | ---: |
| January | 3,699,644 | 1,488 |
| February | 3,377,979 | 1,344 |
| March | 3,928,571 | 1,488 |
| Total | **11,006,194** | **4,320** |

Dense demand has **613,440 = 4,320 × 142** grid/time rows, including zero-demand cells. LocationID records lack point coordinates; seeded within-zone intersection-grid sampling remains a spatial approximation. Timestamps retain the existing naive convention. Persisted monthly Meteostat weather is reused; passenger analytical CLEAR/RAIN is not CNN weather encoding.

| Spatial contract | Active value |
| --- | --- |
| CRS / units | EPSG:32118 / metres |
| Cell / area | 3,000×3,000 m / 9 km² |
| Valid IDs / raster | 0–141 / 16×16; 114 unused positions masked |
| Actions | STAY, N, NE, E, SE, S, SW, W, NW |
| Topology | 958 directed non-STAY links; mean 6.746479 neighbours; connected, zero isolated cells |
| Distances | STAY 0 m; cardinal 3,000 m; diagonal 4,242.640687119286 m |
| Active geometry | [grid_lookup.parquet](data/processed/grid_lookup.parquet) |
| Versioned foundation | [spatial_3km_jan_mar_2026](data/processed/spatial_3km_jan_mar_2026/) |

EPSG:2263 used US survey feet: old 3,000-unit cells measured **914.401829 m**, with 1,213 cells on 51×52. Those artifacts are **SUPERSEDED / PROVENANCE ONLY**, preserved in `data/processed/legacy_914m_provenance/`. The corrected geometry is measured, not inferred from a variable name. Fifteen provisional charging-station identities occupy four new cells; straight-line adjacency does not establish road/bridge connectivity.

[Spatial migration, reconciliation and artifact manifest](results/analysis/2026-10-19_true_3km_grid_activation/README.md)

## 6. Stage-by-stage implementation

### 6.1 Record-029 descriptive sensitivity and weather scenarios

Source price is TLC `fare_amount` in USD. For source-valid Jan–Mar trips with `0 < trip_distance <= 100 miles`:

```text
P_base = 21.34586956773507 USD
tau_P = ±1 USD
L_base = 3.01799878914405 miles
reference support = 479,000 trips with abs(fare - P_base) <= 1
 epsilon = ((P - P_base) / P_base) / ((L - L_base) / L_base)
```

The ±$1 reference is a project methodology choice, not minimum-SD selection. All **10,620,409** cleaned trips remain historical observations. The 0.01-mile measurement-resolution rule marks `abs(L−L_base) < 0.005 mile` as unresolved denominator (9,017 rows); this is an absolute distance gap, not a relative-price threshold. **10,611,392** have VALID epsilon. Inclusive empirical P0.5–P99.5 support is **[−12.890744316473482, 15.442447741158892]**, containing **10,505,278** (approximately 99%) VALID observations. No universal L_min is adopted; tails remain valid history, excluded only from simulation support. This signed ratio is descriptive, not causal elasticity or willingness-to-pay, and **does not enter runtime behavioural acceptance E**.

| Final analytical scenario | Original weather codes | Supported N | Population SD |
| --- | --- | ---: | ---: |
| CLEAR | 1, 2, 3, 5 | 9,613,456 | 1.440831 |
| RAIN | 7, 8, 9, 12, 13, 14, 15, 16, 17, 21 | 891,822 | 1.484481 |

CLEAR includes fair/cloudy/fog; RAIN includes snow/sleet and showers. Original labels remain traceable. Both have all 24 hours (48 rows total). These analytical groups cover the full supported population and supersede literal code-1/code-8 reporting; they are separate from CNN weather representation and runtime acceptance. Earlier Record-029 T1–T4 empirical sampling artifacts remain offline analysis provenance, not the runtime E sampler.

[Final weather scenario evidence](results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/README.md); [Record-029 technical record](results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar/README.md).

### 6.2 CNN demand forecasting

The final CNN is **7→14→7→1**, three 3×3, stride-1, same-padded ReLU convolutions, with valid-cell masking. External tensors are `[B,7,16,16]` to `[B,1,16,16]`. Channels are DayOfWeek, Hour, PeriodWithinHour, WeatherType, Temperature, WindSpeed and HistoricalAverageDemandDistribution. The last plane and learned scalers use January–February TRAIN data only; invalid cells are masked out of loss/metrics. WeatherType retains normalized original code, not CLEAR/RAIN.

J_hat forecasts the next **30-minute** interval (DOCUMENTED_ADAPTATION from the paper's 10-minute horizon); the timestamp labels that interval with no additional target shift. The original CNN split is Jan–Feb TRAIN **2,832 slots**, March 1–15 VALIDATION **720**, March 16–31 TEST **768**. This original CNN test is distinct from the later hierarchical holdout.

| Model / original TEST (109,056 valid grid/time rows) | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Epoch-100 CNN | 6.072322 | 20.485018 | 0.951101 |
| Epoch-200 CNN (selected continuation) | 5.242741 | 18.292800 | 0.961007 |
| TRAIN historical-average baseline | **3.314528** | **16.271804** | **0.969147** |

Epoch-100 **validation**, not test, MAE/RMSE were 6.380307/23.061298. The saved continuation reached best epoch 200; it is not proof of convergence. **CNN_VALID_BUT_HISTORICAL_BASELINE_SUPERIOR** remains the finding. Final checkpoint: `models/cnn/jan_mar_2026_3km_30min_continued/best.keras`. Separate March 1–15 RL forecasts contain **102,240 = 720×142** rows. Historical observed weather is a retrospective condition; live deployment needs issuance-time weather forecasts.

[CNN contract and original evaluation](results/analysis/2026-10-19_final_jan_mar_3km_cnn/README.md); [Continuation and baseline diagnosis](results/analysis/2026-10-19_final_cnn_performance_diagnosis/README.md).

### 6.3 Operational state and driver/EV decisions

State for t is published from completed t−1 observations. `mu` and `sigma` are successful-assignment mean-fare and population-price-SD EWMAs (PROJECT_IMPLEMENTATION_DECISIONS, not manuscript-exact): new estimate = coefficient × observed statistic + (1−coefficient) × prior estimate. Empty-price observations carry the prior.

```text
F_hat(g,t) = delta * (N_disp(g,t-1)/30) + (1-delta)*F_hat(g,t-1)
H_hat(g,t) = kappa * H(g,t-1) + (1-kappa)*H_hat(g,t-1)
U1 = 1 - Phi((P_i_min - mu)/sigma)
U2 = 1 - exp(-F_hat * W_i_max)
U3 = 1 - exp(-H_i_max/H_hat)
non-charging action = argmax(U1 + U2 - C_rep)
charging destination = argmax(U3 - C_rep)
C_rep = 0.25 * movement_metres/(3000*sqrt(2))
```

F_hat units are successful dispatches/minute, H_hat and private wait allowances are minutes. Alpha=beta=delta=kappa=**0.3**, F_hat_0=H_hat_0=**0**; sigma safeguard **1e−6 USD**, H_hat safeguard **1e−6 minutes**. Missing charging observations carry prior H_hat. Historical mu/sigma priors are available after January 25 18:30; earlier starts fail closed. Older reports' null parameters are superseded by the final configuration.

Movement cost is STAY 0, cardinal ≈0.176777, diagonal 0.25; full charging-path cost can exceed 0.25. Energy equal to the threshold enters charging. Charging navigation is timed multihop; no remote admission or teleportation. Existing 15 km/h movement gives cardinal 12 minutes and diagonal 16.970563 minutes.

**H_i_max=10.0 minutes** is explicitly persisted for **5,000/5,000** production profiles (`H_i_max_minutes` and corresponding runtime `charging_wait_preference_minutes`). Source status is VARIABLE_ONLY_NO_CALIBRATION; decision is PROJECT_CALIBRATION. A constant avoids unsupported driver heterogeneity. Missing/null/nonfinite/nonpositive values reject; no fallback. U3(10,10)=**0.6321205588285577**. Planned sensitivity [5,10,20] minutes has not run.

[Operational state](results/analysis/2026-10-19_operational_grid_state/README.md); [Driver/EV interface](results/analysis/2026-10-20_driver_ev_routing_state/README.md); [Frozen routing configuration](results/analysis/2026-10-20_final_routing_configuration/README.md); [H_i_max resolution](results/analysis/2026-10-21_himax_resolution/README.md).

### 6.4 Routing network and FedAvg

State is **169D = 9×[mu,sigma,F_hat] + H_hat for all 142 grids**. Canonical action indices 0..8 are STAY/N/NE/E/SE/S/SW/W/NW. The **169→64→32→9** network masks invalid actions before normalization. Plain FedAvg is sample-count weighted; zero-sample clients are excluded. No privacy guarantee follows from weights-only aggregation.

Selected: `models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras`, **SIMULATOR_DERIVED_ROUTING_BASELINE**. Train March1–12:2,618,033 experiences; validation March13–15:639,807. Central accuracy92.1855%, CE0.407089; final FedAvg accuracy85.3673%, CE0.538560; majority baseline93.8993%. Five rounds,5,000 driver clients, sample weighting and reload were verified. The global model is selected by the federated architecture, not superior accuracy. **ROUTING_EFFECTIVENESS_CONCERN = YES**.

The new held-out probability gate also fails: FedAvg CE/Brier0.538560/0.245881 versus masked March1–12 empirical-prior0.352059/0.117621. **ROUTING_PROBABILITIES_INFORMATIVE = NO**. No routing model was replaced or retrained.

The former synthetic checkpoint (3,408 controlled examples) is **SUPERSEDED_FOR_FINAL_NON_PRIVATE_TRAINING / PROVENANCE_ONLY**; its validation is not comparable across datasets.

[Final routing/FedAvg evidence](results/analysis/2026-10-25_final_simulator_routing_training/README.md); [probability gate](results/analysis/2026-10-26_professor_alignment_pricing_gate/routing_probability_adequacy.json); [historical synthetic evidence](results/analysis/2026-10-20_final_routing_policy/README.md).

### 6.5 Passenger acceptance, pricing contract and DQN

Runtime baseline is `behavioural_E_threshold`, using the separately verified legacy January positive Normal(mean, population SD) conditioned on E>0. Its metadata describes absolute price-distance-ratio calibration; no transformation of Record-029 signed epsilon occurs. Runtime P_base and D_base resolve weather/half-hour TLC fare/distance means via exact → period → weather → global fallback, with January 25 18:30 training cutoff. Runtime P_base is **not** the Record-029 global reference.

```text
P_disp = factor * runtime P_base
P_max = P_base + ((distance-D_base)/D_base) * P_base/E
accept iff P_disp <= P_max
state = [J_hat(g,t), J_disp(g,t-1), I(g,t),
         p_STAY,p_N,p_NE,p_E,p_SE,p_S,p_SW,p_W,p_NW,
         destination_popularity(g',t)]
```

**Professor-alignment caveat:** active positive-truncated-Normal parameters vary across243 weather/half-hour groups; they are not the analytical Clear/Rain scenario means/SDs. Global fallback parent mu/SD are1.1686292254531307/4.714371140724867. Bounds are(0,infinity), seeded persistent RNG. The P_base multiplier above is present; exact source approval is unresolved. Legacy calibration defines abs(relative_price/relative_distance), whereas the active inverse-E acceptance corresponds to the opposite ratio. The active FCFS path also lacks a hard `P_disp >= P_i_min` check; U1 is not that check. These are blockers, not silently corrected equations/rules.

The **13D state uses identity normalization**. J_disp is previous completed-slot successful assignments, not F_hat. I counts already-known passenger commitments arriving in **(t,t+30min]**, excluding reposition/charging and unknown future assignments. Routing p is the full nine-action vector; popularity is the regenerated lagged ordinal feature, not a probability distribution.

Action indices 0..6 map to **[0.85,0.90,0.95,1.00,1.05,1.10,1.15]**. Reward is gross accepted **and successfully assigned** fare at assignment time; rejected/unmatched/failed requests yield zero. No utility, charging or reposition cost is deducted. An OD action is held within its slot; reward is attributed to that OD rather than duplicated across transitions.

| Pricing DQN setting | Frozen value |
| --- | --- |
| Network | 13→64 ReLU→64 ReLU→7 raw Q-values |
| Gamma / Adam LR | 0.99 / 0.001 |
| Batch / loss | 64 / Huber |
| Replay capacity / warmup | 100,000 / 1,000 |
| Soft-target tau / seed | 0.005 / 42 |
| Exploration | 1.0→0.05 linearly over 50,000 **optimizer updates** |
| Target | terminal r; otherwise r + gamma*max Q_target(next_state) |

This is standard DQN, not Double DQN. Warmup does not advance epsilon. The standalone synthetic fixture ran 100 updates, loss **3.50116517→0.15600096**; it is implementation evidence only.

The bounded integration fixture used three vehicles and 36 controlled requests per four-slot run. Greedy factor1.10 rejected all 36. Forced factor1.00 accepted 24, rejected 12, assigned 6, unmatched 18, reward **$128.03439281400887**. Combined replay 24 transitions; no simulator optimizer update. These are branch tests, not historical performance.

[Acceptance/state/reward contract](results/analysis/2026-10-20_pricing_contract_and_dqn_state/README.md); [Standalone DQN](results/analysis/2026-10-21_standalone_pricing_dqn/README.md); [Controlled integration fixture](results/analysis/2026-10-21_pricing_dqn_simulator_integration/README.md).

### 6.6 Final hierarchical runner, episode and arrival correction

`src.simulation.production.ProductionExperiment` exposes the final runner; `LegacyProductionExperiment` retains the historical implementation. Final execution uses 142 grids,169D/9-output routing,13D/7-action pricing, causal state, FCFS matching, timed passenger/reposition/charging movement, assignment rewards and replay. The migration's old H_i_max startup blocker is superseded by explicit profile calibration and successful startup.

The March16 00:00–02:00 **four-slot** real-flow integration run used forecast counts and intact January empirical OD trips: **2,838 requests**, **1,121 accepted/assigned**, **1,717 rejected**, **0 accepted-unmatched**, gross revenue **$22,532.11609157535**, exactly reconciled per slot. Replay **1,104**, one optimizer update; epsilon1.0 during action selection, **0.999981** afterward. Action-decision counts were **[153,170,158,153,138,171,161]**. There were 14,946 STAY and 4,005 reposition decisions,913 passenger completions and 208 terminal passenger commitments. Forty-nine unsupported-origin forecast units were reported separately, not counted as generated requests. No charging events occurred; prior timed-charging tests cover that path. Fleet stayed 5,000, ending 4,298 IDLE/702 BUSY; state/replay/weights remained finite.

The checkpoint is **SHORT_HIERARCHICAL_INTEGRATION_CHECKPOINT / NOT_FINAL_TRAINING_CHECKPOINT / DO_NOT_CONTINUE_FOR_FINAL_EXPERIMENTS**. It is integration proof, not learned pricing performance.

During March1 collection, vehicles 918/4561 scheduled at 01:00 retained tiny positive floating-minute countdowns at the same publication timestamp. `ProductionExperiment.advance_until` now selects due passenger completions by unchanged absolute timestamps, including coincident movement events. Arrivals <=t complete and commitments clear before publication; future arrivals remain pending. I(g,t),30/2-minute timing, utilities and pricing are unchanged. Nine focused regressions pass, including t−1second/t/t+2min/t+30min, fail-closed checks, fleet conservation and append-once resume.

Collection uses factor **1.00**, P_disp=runtime P_base, without pricing replay/training. Initial slot:3,494 requests,494 assignments,4,570 reposition experiences,0 charging experiences,4,570 active/430 zero-experience drivers; labels **[3505,74,113,289,114,296,15,148,16]**. After correction, six slots contain 27,009 experiences, no duplicate IDs, finite 169D states,9-element masks and valid labels; 5,000 unique vehicles. This six-slot milestone is historical; complete clean generation and subsequent training are recorded below.

[Runner migration (historical blocker)](results/analysis/2026-10-21_hierarchical_runner_migration/README.md); [Successful four-slot episode](results/analysis/2026-10-21_first_short_hierarchical_dqn_episode/README.md); [Arrival correction](results/analysis/2026-10-21_passenger_arrival_boundary_fix/README.md); [Historical collection and preserved blocked-attempt history](results/analysis/2026-10-21_simulator_derived_routing_policy/README.md).

### 6.6A Completed generation and pricing runs

Old pre-reachability generation:680/720 slots,3,077,890 experiences; **SUPERSEDED_PRE_REACHABILITY_RESERVE_GENERATION / PROVENANCE_ONLY / DO_NOT_USE_FOR_FINAL_ROUTING_TRAINING** because it lacked post-movement station reachability.

Final clean March1–15 generation:720/720 slots,3,257,840 experiences,5,000 conserved vehicles,1,705,916 requests,301,920 assignments. Reserve candidate exclusions57, distinct affected requests3, reposition exclusions0. Rule: `E_current-E_movement >= minimum_station_route_energy(destination)`, equality allowed, no margin; **PROJECT_PHYSICAL_FEASIBILITY_CONSTRAINT**. [Constraint evidence](results/analysis/2026-10-25_ev_station_reachability_contract/README.md); completed counts are verified in the final routing-training report linked above.

Completed pricing run:1,705,916 requests =536,483 accepted +1,169,433 rejected;536,483 accepted =395,492 assigned +140,991 unmatched. Revenue **$7,490,773.984343884**;288,181 transitions;100,000 replay capacity;718 optimizer updates;epsilon0.986358. Checkpoint `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4` is **COMPLETED_PRICING_TRAINING_RUN / TRAINING_SCHEDULE_MISMATCH / NOT_FINAL_NONPRIVATE_BASELINE**, retained unchanged.

One optimizer update per slot after warm-up yielded718 updates against a50,000-update decay horizon (~70 equivalent passes, not authorized). The March16 00:00–02:00 development-only greedy check produced2,838 requests,1,801 accepted/assigned,$33,721.11 revenue; action counts[196,908,0,0,0,0,0]. Saved-state greedy counts were[4295,5705,0,0,0,0,0]. Fixed1.00 revenue was$19,996.38. The68.64% difference is limited to this two-hour matched development window, **not convergence or general superiority**. Optimizer count stayed718.

The conditional cadence proposal excludes the first1000 transitions, then updates once per5 newly committed transitions with deterministic remainder: floor((288181−1000)/5)=57,436, remainder1. This would reachepsilon0.05 at50,000 updates at that volume. Prerequisites fail, so **no PROJECT_TRAINING_CADENCE is frozen or implemented**. Actual new-run volume may differ; all other DQN settings remain frozen.

### Professor Discussion Requirements / Verification Status

| Requirement | Status | Evidence / next action |
|---|---|---|
| Passenger elasticity sampling | VERIFIED | Active legacy positive truncated Normal, weather/half-hour calibration; not the two analytical scenario distributions. Source alignment remains open. |
| Acceptance equation | VERIFICATION_REQUIRED | Active equation tested; exact professor/paper equation not established. |
| P_base multiplier | VERIFICATION_REQUIRED | Multiplier is present and dimensionally correct in active code; source/calibration orientation unresolved. |
| Passenger rejection vs dispatch failure | VERIFIED | Completed-run accounting identities pass; categories remain distinct. |
| P_disp >= P_i_min | IMPLEMENTATION_REQUIRED | Absent from active FCFS eligibility, independent of U1. |
| 13D DQN state / incoming supply | VERIFIED | Exact ordered13 features; commitments strictly before t, arrivals in(t,t+30min]. |
| Routing utilities / EWMA | VERIFICATION_REQUIRED | Existing frozen formulas/reports preserved; no new numerical revalidation in this narrow gate. |
| FL aggregation | VERIFIED | Existing final training report verifies five driver-client sample-weighted rounds, zero-client exclusion and reload; no new FL executed. |
| Routing convergence/probabilities | KNOWN_LIMITATION | FedAvg worse than masked training-action prior on held-out CE/Brier; informative=NO. |
| Pricing convergence | KNOWN_LIMITATION | 718 updates; schedule mismatch; two-hour development advantage is not convergence. |
| Non-private baseline before DP | VERIFICATION_REQUIRED | Completed run retained but NOT_FINAL_NONPRIVATE_BASELINE; resolve prerequisites before corrected retrain. |
| DP mechanism | FUTURE_PHASE | Specify clipping, noise, epsilon_DP, delta_DP, accounting and privacy–utility trade-off after validated non-private baseline. |
| Consistent evaluation periods/metrics | VERIFIED | Jan–Feb CNN train; Mar1–15 RL; Mar16 development; Mar17–31 protected. Development results not final evaluation. |

[Full professor gate and exact blockers](results/analysis/2026-10-26_professor_alignment_pricing_gate/README.md). Corrected retraining has not run; no protected evaluation or DP mechanism was executed.

### 6.7 Historical NB1–NB13 implementation reference

<details>
<summary>Preserved legacy stage documentation — not current run instructions or final contracts</summary>

The following stage descriptions predate the active Jan–Mar/142-grid/DQN system. Their “current”, “final”, “production”, validation counts and commands refer to that historical milestone only. Do not execute these builders against current artifacts; sections 5–7 and 10 supersede their spatial/model/runtime assumptions.


#### Legacy 6.1 Spatial preparation (NB1-NB2)

| Item | Current contract |
| --- | --- |
| Purpose | Build canonical grid, map zone-based trips to GridIDs, and persist downstream spatial artifacts |
| Modules | `src/data/taxi.py`, `src/spatial/grid.py`, `src/spatial/mapping.py`, `src/spatial/artifacts.py` |
| Script | `python scripts/build_grid.py [--validate] [--force]` |
| Inputs | Raw Yellow Taxi parquet and Taxi Zone shapefile |
| Outputs | `cleaned_trips.parquet`, `grid_lookup.parquet`, `grid_mask.npy`, `zone_grid_mapping.parquet`, `zone_to_grids.pkl`, `neighbour_map.parquet`, `grid_metadata.json` |
| Validation | Spatial schemas, mask dimensions, canonical IDs, mappings, and neighbour links |

`cleaned_trips.parquet` contains cleaned taxi fields plus `PUGridID` and `DOGridID`. The random generator is seeded with `random_seed + month_number` (42 + 1 for January) to reproduce the legacy zone-to-candidate-grid allocation. This mapping is an approximation introduced by the coordinate limitation, not an observed trip coordinate assignment.

#### Legacy 6.2 Weather preparation

| Item | Current contract |
| --- | --- |
| Purpose | Reproduce the legacy hourly weather utility input for NB3 |
| Modules | `src/data/weather.py` |
| Script | `python scripts/build_weather.py [--validate] [--force]` |
| Provider | Meteostat **1.7.6** using `Hourly(Point(...), start, end).fetch()` |
| Location | 40.7128, -74.0060, altitude 10 m |
| Period | 2026-01-01 00:00:00 through 2026-01-31 23:59:59 |
| Outputs | `data/processed/weather/nyc_weather_processed_2026_01.parquet`, `weather_metadata_2026_01.json` |

The processed table has 744 hourly rows and exactly `Datetime`, `Temperature`, `WindSpeed`, and `WeatherCode`. It retains Meteostat `temp`, `wspd`, and `coco`, renames them, sorts timestamps, forward-fills missing values, and backward-fills any remaining leading values. It adds no interpolation, normalization, lags, or derived weather variables.

Both taxi and weather timestamps are intentionally timezone-naive to reproduce the legacy behaviour. Their temporal alignment remains a research assumption requiring an explicit future decision.

#### Legacy 6.3 NB3 demand master

| Item | Current contract |
| --- | --- |
| Purpose | Create complete half-hourly grid-level pickup-demand records with weather and calendar features |
| Modules | `src/demand/aggregation.py`, `src/demand/contracts.py` |
| Script | `python scripts/build_demand_master.py [--validate] [--force]` |
| Inputs | Cleaned trips, canonical grid artifacts, processed weather |
| Outputs | `demand_master_2026_01.parquet`, `demand_master_2026_01_metadata.json` |

The authoritative NB3 table has 1,488 half-hour slots x 1,213 GridIDs = **1,804,944 rows** and these 14 columns:

```text
TimeSlot, GridID, Demand, Row, Column, Temperature, WindSpeed, WeatherCode,
DayOfWeek, Hour, Minute, Period, TimeIndex, HistoricalDemand
```

Demand is the pickup count by `(TimeSlot, PUGridID)`; dropoff GridID is not used for the target. The January-filtered pickup total is **3,699,633**. This is five fewer than the cleaned-trip total because five trips fall outside the January pickup-time boundary. `HistoricalDemand` is a strictly earlier expanding mean by `GridID`, `DayOfWeek`, and `Period`; it does not use current or future demand. NB3 applies no normalization.

#### Legacy 6.4 NB4 CNN dataset

| Item | Current contract |
| --- | --- |
| Purpose | Convert the frozen NB3 table into legacy-compatible spatial tensors |
| Module | `src/demand/tensors.py` |
| Script | `python scripts/build_cnn_dataset.py [--validate] [--force]` |
| Input | `data/processed/demand_master_2026_01.parquet` plus canonical grid artifacts |
| Output directory | `data/processed/cnn/` |

Feature-channel order is fixed:

```text
0 HistoricalDemand   1 Temperature   2 WindSpeed   3 WeatherCode
4 DayOfWeek          5 Hour          6 Period
```

For each ordered time `t`, the feature map is at `t` and the raw pickup-demand target is at `t+1`. The full unsplit shapes are `X = (1487, 7, 51, 52)` and `y = (1487, 1, 51, 52)`, stored as `float32`. Invalid grid positions are zero padded. The split is chronological and unshuffled: 1,189 training samples and 298 test samples.

Persisted artifacts are `X_train.npy`, `y_train.npy`, `X_test.npy`, `y_test.npy`, `time_train.npy`, `time_test.npy`, and `metadata.pkl`.

#### Legacy 6.5 NB5 CNN demand model

| Item | Current contract |
| --- | --- |
| Purpose | Train/validate the legacy CNN demand baseline and expose inference helpers |
| Modules | `src/demand/model.py`, `src/demand/inference.py` |
| Script | `python scripts/train_cnn.py [--validate] [--force]` |
| Input | Persisted NB4 dataset |
| Model artifacts | `models/demand/` |
| Figures | `outputs/figures/` |

The network is `Conv2D(32, 3x3, ReLU) -> Conv2D(64, 3x3, ReLU) -> Conv2D(32, 3x3, ReLU) -> Conv2D(1, 1x1, linear)`, all with same padding. It has 39,041 parameters. Channel-wise normalization is fitted on `X_train` only; targets are not normalized. Training requests up to 50 epochs, batch size 32, shuffled 20% validation split, and early stopping on validation loss (patience 5, restore best weights).

Persisted artifacts are `normalization.pkl`, `cnn_model.keras`, `cnn_metrics.csv`, `cnn_predictions.npy`, `cnn_history.pkl`, and `cnn_provenance.json`. The current saved metrics are RMSE 2.5915691905, MAE 0.6337751746, MAPE 83.4894835949%, and R² 0.8985528946. The legacy baseline intentionally includes padded positions in normalization, loss, and metrics.

#### Legacy 6.6 Fleet baseline

| Item | Current contract |
| --- | --- |
| Purpose | Represent seed-reproducible vehicle and grid supply state |
| Modules | `src/fleet/state.py`, `src/fleet/fleet.py`, `src/fleet/supply.py` |
| Demonstration | `python scripts/test_fleet_state.py` |

The configured fleet contains 5,000 vehicles, initially sampled uniformly over valid GridIDs. This is a provisional engineering baseline. Each `VehicleState` carries `vehicle_id`, `current_grid`, `trip_status`, `destination`, `remaining_travel_time`, `current_action`, and `energy_level`. The implemented statuses are `IDLE`, `BUSY`, and `CHARGING`. A busy vehicle has a valid destination and positive remaining duration; completing travel returns it to `IDLE` at its destination.

#### Legacy 6.7 Requests, OD generation, and dispatch

| Item | Current contract |
| --- | --- |
| Modules | `src/dispatch/request.py`, `src/dispatch/generation.py`, `src/dispatch/dispatch.py` |
| Demonstration | `python scripts/test_dispatch.py` |
| Source | Frozen January trip rows containing OD, timestamps, distance, and fare |

The frozen processed table contains 3,699,638 source trips. Runtime empirical sampling preserves one source row's `PUGridID`, `DOGridID`, pickup/drop-off timestamps, duration, distance, and base fare together rather than independently resampling its fields. The source NB2 policy did not filter duration or fare; runtime validation therefore excludes non-positive duration, negative/non-finite distance, and negative/non-finite fare candidates without clipping or rebuilding the parquet. In the current artifact, 44,612 rows have non-positive duration, 38,793 have negative fare, and distance has no negative or non-finite rows; accounting for overlap, 83,405 rows are excluded from runtime sampling.

One request is generated per integer grid-demand unit. The empirical pickup timestamp's absolute historical date and time are not replayed. Instead, its offset from the start of its original 30-minute bucket determines the corresponding simulated two-minute mini-slot: `floor(within_slot_offset_seconds / 120)`. For example, `08:17:43` is 17 minutes 43 seconds into the `08:00` bucket, maps to mini-slot 8, and arrives at minute 16 of whichever simulated main slot is active. Requests are then processed FCFS by `(request_time, request_id)`. The mini-slot controls simulated arrival discretization only; it is not passenger-trip duration.

Empirical-row selection remains seeded. Arrival placement consumes no random draw, and customer acceptance retains its separate explicit RNG stream.

Production uses `driver_contention`: accepted requests are announced to eligible `IDLE` drivers in the origin and direct canonical neighbours, excluding charging/threshold, insufficient-energy, and in-transit vehicles. Its request utility reuses NB11's equal-weight price/wait/charging structure. A driver contends when request utility is at least its best valid outside-option utility. The platform ranks contenders by shortest pickup distance, then descending request utility with utility-tie handling, and finally vehicle ID; assignment is immediate. Requests remain FCFS by `(request_time, request_id)`, and zero contenders means unserved. The earlier lowest-ID origin/neighbor policy remains legacy-only. Served empirical requests use their paired pickup/dropoff duration, and completion moves the vehicle to the paired destination. The configured default duration remains only a compatibility fallback for synthetic/manual requests lacking empirical fields.

**Waiting-time semantics:** NB9/NB11 waiting means driver/vehicle idle time in a grid before receiving a dispatch, not passenger waiting time. An available IDLE vehicle begins an episode at zero in its current grid and gains two minutes after each completed mini-slot that it remains IDLE. Dispatch closes the episode and records its completed duration against the vehicle's waiting grid, including when a neighboring vehicle serves the request. Main-slot boundaries and NB11 STAY do not reset it. BUSY trip time, charging time, and reposition travel are not idle waiting. Passenger-trip and charging completion start a new zero-minute episode at the available grid. A MOVE abandons the origin episode without fabricating a completed observation; the vehicle remains unavailable during its 12-minute reposition, and its destination idle clock begins only on arrival.

NYC TLC `trip_distance` is retained as `trip_distance_miles` for source audit. Kilometres are the simulation's canonical operational distance unit, converted exactly once as `trip_distance_km = trip_distance_miles * 1.609344`. At successful assignment, before the vehicle transitions from `IDLE` to `BUSY`, passenger energy is deducted exactly once with the existing consumption rate: `trip_distance_km * 0.15 kWh/km`. The request records before, consumed, and after energy. Mini-slot advancement does not deduct it again. A completed low-energy vehicle enters the existing NB10 charging workflow; BUSY vehicles cannot charge or reposition.

#### Legacy 6.8 NB9 operational statistics

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/statistics.py` |
| Demonstration | `python scripts/test_statistics.py` |

Fare state begins from a pre-cutoff `PUGridID` historical bootstrap, using grid-level population mean/SD and a global historical fallback where required. For every grid/main slot, NB9 then records served fares and completed driver-idle dispatch waits, with separate counts, means, and population standard deviations (`ddof=0`), plus `ewma_fare`, `ewma_std_fare`, `ewma_wait`, and `ewma_std_wait`. Current observations update the state with `alpha = 0.30`; no observation carries it forward. A vehicle that remains idle has not completed an episode and creates no fake observation. Candidate grids with no current or EWMA wait history receive `U_wait = 0.5` only at NB11 utility evaluation. Charging availability and queue-wait context are carried where supplied.

```text
EWMA_next = (1 - alpha) * EWMA_previous + alpha * current_observation
```

Alpha, initialization, population SD, and no-observation behaviour are provisional engineering decisions.

#### Legacy 6.9 NB10A EV energy

| Item | Current contract |
| --- | --- |
| Module | `src/charging/energy.py` |
| Demonstration | `python scripts/test_energy.py` |

The code adopts selected Table I values from Ding et al.: 75 kWh battery capacity, 60 kWh reference initial energy, 7.5 kWh reference minimum, 0.15 kWh/km consumption, and 30 kW charging power. The operational fleet initialization is instead a seeded truncated-normal SOC distribution: mean 0.50, SD 0.05, bounds [0.50, 0.70]. The charging trigger is SOC <= 0.20 (energy <= 15 kWh), so it must not be confused with the 7.5 kWh literature reference. Charging efficiency is 0.90; release occurs at 75 kWh (full charge), which is provisional.

#### Legacy 6.10 NB10B charging infrastructure

| Item | Current contract |
| --- | --- |
| Module | `src/charging/stations.py` |
| Script | `python scripts/build_charging_stations.py [--validate] [--force]` |
| Demonstration | `python scripts/test_charging_infrastructure.py` |
| Artifact | `data/processed/charging_stations_2026_01.parquet` |

Fifteen station grids are selected by descending pickup-plus-dropoff popularity (with lower GridID resolving a tie). A station has a 3,000 kW power limit and each active EV reserves 30 kW. It uses a power-only representation rather than a physical charger count. Nearest-station selection uses projected grid-centroid distance, charging queues are FCFS by arrival order with seeded random priority for simultaneous arrivals, and queued wait increments by mini-slot duration. Charging gain is `power * efficiency * hours` and is capped at battery capacity.

#### Legacy 6.11 NB11 utility-based routing/repositioning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/baseline.py` |
| Demonstration | `python scripts/test_routing_baseline.py` |

Only eligible `IDLE` vehicles not requiring charging may reposition. The fixed action order is `[STAY, NORTH, EAST, SOUTH, WEST]`; absent boundary neighbours are invalid and masked. For each valid candidate, NB11 calculates normalized price, decreasing waiting-time, and charging utilities, then uses `U_total = (U_price + U_wait + U_charge) / 3`. The actual decision is `state -> component utilities -> equal-weight total utility -> maximum valid utility -> STAY or MOVE`, with fixed action order breaking ties. Explicit price/wait preferences and an explicitly normalized degradation penalty are required; production values are not fabricated. Production NB11 uses the normalized DOD-related battery degradation component derived from Chauhan & Jain, referenced to charging from the frozen 20% SOC threshold to 100%; its separate temperature-dependent component is not modeled. The utility vector is audit data, not Q-values or probabilities. NB11 is not DQN or Q-learning.

Production uses 5,000 seed-42 persistent driver profiles. Price preference is generated from the pre-cutoff fare distribution; preferred idle-wait duration is sampled from `Uniform(0,30 minutes)`. Both are fixed per vehicle. These are synthetic project assumptions, not measured individual NYC-driver traits, passenger waiting, or a cap on actual idle time. When a candidate grid has no causal wait history, NB11 assigns only that candidate's normalized wait component the neutral value `0.5`; this creates no NB9 observation and is replaced when current or EWMA wait statistics exist.

The baseline uses 15 km/h, a 3 km repositioning threshold, and <=30-minute feasibility. Thus a non-stay movement takes 12 minutes, consumes 0.45 kWh, remains unavailable to dispatch during movement, and begins destination idle waiting only after arrival. NB11 has no reward or learning logic.

The authoritative production assembler is `src/simulation/production.py`, invoked by `scripts/run_production_experiment.py`. It loads and hashes production-authoritative artifacts, initializes the historical fare prior once with empty causal wait history, uses uniform-valid routing probabilities only for the first slot, and then preserves fleet, persistent RNG streams, LinUCB, NB9, NB11 operational state, NB12/NB13, charging, repositioning, and learned routing probabilities across boundaries. Missing or incompatible authoritative inputs fail fast; no validation-fixture fallback exists. It writes compact slot, learning, wait, fleet, source-manifest, and reproducibility artifacts.

The frozen CNN is one-step-ahead: each saved prediction produced from `X_test[i]` is keyed in production by the target timestamp `time_test[i] + 30 minutes`. The 298 held-out targets therefore cover 2026-01-25 19:00 inclusive through 2026-02-01 00:00 exclusive; the stored `time_test` array retains its original X/input timestamp meaning.

#### Legacy 6.12 NB12 local supervised routing-policy learning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/learning.py` |
| Demonstration | `python scripts/test_local_routing_learning.py` |

Each participating vehicle has a local supervised learner trained from the actual `(state, chosen_action)` observations produced by NB11. The fixed deterministic `float32` state vector has **87** elements:

```text
vehicle.current_grid, vehicle.energy_level,

for each action in [STAY, NORTH, EAST, SOUTH, WEST]:
  valid, grid_id, predicted_demand,
  supply_total, supply_idle, supply_busy, supply_charging,
  mean_fare, std_fare, ewma_fare, ewma_std_fare,
  mean_wait, std_wait, ewma_wait, ewma_std_wait,
  charging_available, charging_wait
```

An invalid candidate has an all-zero block, including `valid=0`; `valid` remains a separate action mask. A missing `charging_available` within an otherwise valid candidate is encoded as -1. The common architecture is:

```text
87 -> Dense(64, ReLU) -> Dense(32, ReLU) -> Dense(5, linear)
```

The shared architecture is:

```text
87 -> Dense(64, ReLU) -> Dense(32, ReLU) -> 5 action logits
```

Invalid logits are excluded before softmax, so invalid actions have probability zero and valid probabilities sum to one. The supervised target is NB11's chosen action, not its utility vector, and training minimizes sparse categorical cross-entropy/negative log likelihood. Local observations contain state, chosen action, and action mask; an optional utility vector and slot ID are audit-only. Training runs at most once at the end of each 30-minute main slot, and zero observations produce no update.

Each vehicle retains a bounded local observation buffer. Federation-ready export contains only copied policy weights, vehicle ID, sample count, state dimension, action order, and architecture version; raw local observations are never exported.

#### Legacy 6.13 NB13 federated routing-policy aggregation

| Item | Current contract |
| --- | --- |
| Module | `src/routing/federated.py` |
| Demonstration | `python scripts/test_federated_routing.py` |

One synchronous federated round consumes corrected-NB12 export payloads, validates state dimension, action order, architecture version, tensor count/shapes, finite weights, and non-negative integer sample counts, then computes each global tensor as `sum(n_i * theta_i) / sum(n_i)`. Zero-sample clients are validated but excluded. If every submitted client has zero samples, the round returns an explicit no-update result with no fabricated weights.

The common and local policies share the same `87 -> 64 -> 32 -> 5 logits` architecture, so aggregated weights load directly into fresh NB12 learners. Production performs one round after each main slot using only clients with new observations, applies sample-count-weighted FedAvg, and redistributes the global model. The interface aggregates weights only; raw states, chosen actions, masks, utilities, trajectories, and rewards are neither required nor transmitted. This baseline does not claim differential privacy, secure aggregation, client-failure simulation, or production communication behavior.

#### Legacy 6.14 Contextual pricing and historical customer acceptance

| Item | Current contract |
| --- | --- |
| Modules | `src/pricing/state.py`, `linucb.py`, `customer.py`, `reward.py` |
| Demonstration | `python scripts/test_pricing.py` |

Production pricing uses one request-level decision from a disjoint-arm contextual LinUCB learner with `alpha = 1.0`. The fixed 8D feature order is `[scaled predicted demand, scaled idle_plus_incoming supply, relevant OD routing probability, lagged destination popularity, scaled trip distance in kilometres, scaled historical P_base(W,T), Period/47, categorical weather severity]`. The fixed arms are `[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]`. Each arm maintains `A = I` and `b = 0`, is scored with `theta^T x + alpha * sqrt(x^T A^-1 x)`, and only the selected arm receives the request's finalized feedback. A deterministic global cold start assigns each arm until all have an actual reward observation; later numeric score ties use the seeded RNG. There is no epsilon-greedy exploration. The earlier grid-level eight-feature interface remains only as a clearly separated legacy compatibility mode.

**Pricing popularity semantics:** popularity is destination attractiveness from empirical drop-off activity, not pickup demand, predicted demand, supply, combined pickup/drop-off activity, or charging-station popularity. Trips are attributed by `DOGridID` and the 30-minute slot containing `tpep_dropoff_datetime`. For grid `g` and slot `t`, the feature uses a strictly lagged simple mean of observed drop-off counts in slots `t-6` through `t-1`—a three-hour window—with all available prior slots used during warm-up. Observed zero-drop-off grid-slots remain zeros; unavailable pre-period history remains unavailable rather than being fabricated.

Fixed global `Q20/Q40/Q60/Q80` thresholds are fitted only on the chronological reference/training period and then applied unchanged to test/runtime data. Inclusive upper boundaries produce `Very Low`, `Low`, `Medium`, `High`, and `Very High`, encoded respectively as `0`, `0.25`, `0.5`, `0.75`, and `1`. Duplicate thresholds are retained and the same deterministic inequalities still apply. The label remains in the popularity artifact for audit while the eighth LinUCB feature receives only its scalar encoding, preserving the eight-dimensional context.

#### Pricing context scaling

Only demand and supply are transformed. Raw frozen-CNN demand is clipped at zero, transformed as `log1p(max(0, demand)) / log1p(45.085255432128896)`, then clipped to `[0,1]`. The denominator is the P99 of non-negative frozen-CNN predictions produced by inference on the existing chronological training/reference tensors (2026-01-01 00:00 through 2026-01-25 18:00); held-out predictions were not used. Negative raw demand remains available in diagnostics alongside its non-negative and scaled values.

Supply retains the existing `supply_total` semantics and is transformed as `log1p(supply_total) / log1p(9)`, then clipped to `[0,1]`. The reference value `9` is the P99 reproduced from the configured seed-42 uniform initialization of 5,000 vehicles over 1,213 canonical grids. This initialization distribution does not capture later endogenous vehicle concentration caused by dispatch, repositioning, or charging. Values above the fixed reference are therefore clipped to one and clipping counts/rates are recorded; the scaler is never dynamically refitted.

Routing probabilities and the five-level popularity value are unchanged. The deterministic parameters, artifact hashes, fitting provenance, transforms, clipping policy, and methodology version are persisted in `config/pricing_context_scaler.json`. LinUCB `alpha = 1.0` remains provisional and has not been optimized for the scaled context; scaling behaviour must stabilize before alpha sensitivity analysis.

The January artifact uses the frozen cleaned-trip destination and drop-off timestamp fields. No pre-January drop-off observation exists locally, so all January 1 00:00 grid moving averages are unavailable; January 1 00:30 uses only the observed 00:00 counts, and the history expands until six slots are available. This is an explicit initialization limitation, not future filling. The static charging-station field named `popularity` remains the separate whole-month `pickup_count + dropoff_count` ranking and is never used as the pricing feature.

#### Offline historical customer sensitivity — Phase 1

**Current final offline passenger elasticity:** See the [clean-reference final analysis](results/analysis/2026-10-03_elasticity_clean_reference_final/README.md) and `data/processed/elasticity_v2/final_elasticity_clean_reference_methodology.json`. It uses the cleaned Jan–Mar 2026 population, global mean fare and distance references, signed relative-change elasticity, and actual Clear/Rain/Snowfall conditions. The [current L_base diagnostic](results/analysis/2026-10-04_lbase_diagnostic_final_weather/README.md) compares alternative references without replacing the final method. No clustering, trimming or imputation enters the final method.

M10 was a historical development stage and is superseded for this offline analysis. This final offline result does not change production behavior; the existing production implementation described below remains separate.

`src/pricing/historical_sensitivity.py` and `scripts/build_customer_sensitivity.py` build the pre-cutoff sensitivity inputs later consumed by production. Training trips before the exclusive `2026-01-25 18:30` boundary are pooled by `(WeatherCode, Period)`. Source-valid rows require positive finite `fare_amount` and positive finite TLC `trip_distance` no greater than 100 miles. Within each group, `P_base` and `D_base` are the respective means. An observation enters the ratio only when `abs(trip_distance - D_base) >= 0.01` mile, matching source resolution; retained observations use `epsilon = abs(((P-P_base)/P_base) / ((D-D_base)/D_base))`. The group and hierarchical-fallback tables retain population/sample SD and diagnostic quantiles. These build-stage rules are not epsilon clipping or winsorization; runtime positive-truncated sampling and `P_max` evaluation occur separately.

Production resolves sensitivity hierarchically for `(WeatherCode, Period)` using `exact -> Period -> Weather -> Global`, samples epsilon from the stored mean/population SD with a positive lower-truncated Normal draw, and computes `P_dispatch = P_base * alpha` and `P_max = P_base + (((D-D_base)/D_base) * P_base / epsilon_customer)`. The request is accepted exactly when `P_dispatch <= P_max`. Resolution and sampling occur once per request and retain the complete sensitivity/price audit. The ordinary Eq.31 response remains a legacy comparison mode, not the production configuration.

Phase 4A adds a reusable unscaled pricing-supply feature: `Supply(g,t) = currently IDLE vehicles in g + BUSY vehicles with a known passenger destination g and expected completion in the upcoming 30-minute slot`. The incoming window follows existing mini-slot completion semantics, `(slot_start, slot_end]`; charging and charging-queue vehicles are excluded. Phase 4B exposes this value through the `idle_plus_incoming` supply selector and places it in the unchanged second position of the eight-feature LinUCB context. The existing log1p/P99 transform remains unchanged. Recalibration preserves the original deterministic initialization reference convention; because all 5,000 initialized vehicles are IDLE, the corrected and legacy P99 references are both 9 across 1,213 grid observations. Remaining context features are unchanged.

The offered fare is the empirical base fare multiplied by the selected factor. Production feedback is finalized after dispatch: a served request contributes its recorded dispatch fare, while rejected and accepted-but-unserved requests contribute zero. The learner receives `raw_served_revenue / (BASE_PRICE_REF_P99 * 1.15)` using the frozen training-reference scale without clipping; raw served revenue remains the economic diagnostic. Every priced request receives exactly one update and no pending reservation remains after a slot.

LinUCB state is copy-exportable/importable in memory. Scaling is applied once at the methodology-derived pricing-context boundary; the LinUCB equations and eight-dimensional state contract are unchanged.

#### Legacy 6.15 One-slot pricing, acceptance, and dispatch

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/pricing_dispatch.py` |
| Demonstration | `python scripts/test_pricing_dispatch.py` |

In production, each generated request receives its own 8D context and one pricing selection when it arrives within the 30-minute slot. It retains the empirical base fare and records factor, offered fare, sensitivity resolution, acceptance decision, dispatch outcome, and finalized reward. Processing order is `request context -> pricing -> historical-sensitivity acceptance -> contention dispatch -> served-revenue feedback`; rejected requests never enter dispatch.

Raw served revenue includes only accepted requests successfully assigned by dispatch. Accepted-but-unserved and rejected requests yield zero learning reward. The production runner validates one selection and one finalized update per generated request and fails if any reservation remains pending.

#### Legacy 6.16 One-main-slot orchestration and grid policy aggregation

| Item | Current contract |
| --- | --- |
| Modules | `src/simulation/main_slot.py`, `grid_policy.py` |
| Demonstration | `python scripts/test_main_slot.py` |

One main slot executes pricing/customer acceptance/contention dispatch across 15 mini-slots; NB10 charging advancement and NB9 end-slot statistics; NB11 maximum-utility routing and 12-minute movement; NB12 local supervised observation/training; NB13 FedAvg and redistribution; global-policy inference; and next-slot pricing-input construction. Production supplies aligned frozen-CNN demand and lagged popularity, and performs one federated round per main slot.

The grid routing probability supplied to pricing uses an explicit **project baseline aggregation rule**, not a professor- or paper-prescribed formula. The global NB12/NB13 policy first produces an individually masked `[STAY, NORTH, EAST, SOUTH, WEST]` probability vector for every eligible idle vehicle from its real 87-D routing state. These probability vectors are averaged arithmetically within each grid. One vehicle uses its vector unchanged. A grid with zero eligible vehicles carries its previous grid vector; first use without history requires explicit initialization. This aggregation is a learned policy tendency only and may be revisited in sensitivity analysis. **NB11 maximum utility remains the sole source of actual repositioning actions.**

#### Legacy 6.17 Short temporal simulation

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/multi_slot.py` |
| Demonstration | `python scripts/test_multi_slot.py` |

The controlled temporal driver invokes the completed one-slot orchestrator exactly four times, advancing timestamps by 30 minutes. It reuses the same fleet and charging infrastructure, LinUCB learner, acceptance RNG stream, NB9 EWMA engine, local NB12 learners, and global policy learner. The latest grid probability becomes the next zero-vehicle carry-forward value. Federation slots are an explicit caller-supplied set rather than a claimed final cadence. Each slot receives only its explicitly supplied boundary forecast, popularity, requests, and utility inputs; no later realized outcome is inspected.

#### Legacy 6.18 24-hour small-fleet validation

The temporal driver now supports an arbitrary positive slot count while retaining the four-slot compatibility wrapper. A deterministic **SMALL-FLEET VALIDATION** runs 48 consecutive 30-minute slots with 50 vehicles and four active grids. It is an integration-health milestone, not the final thesis experiment and not evidence that the 5,000-vehicle January simulation is complete.

The fixture uses controlled deterministic demand/popularity and retains an explicit federation schedule for engineering tests. Production instead uses authoritative held-out inputs and one federated round per slot. Two fixture runs produced identical aggregate trajectories. Run it with `python scripts/test_validation_24h.py`.

### Reproducible validation reporting

Run `python scripts/generate_validation_figures.py` to reproduce the compact pricing, customer-response, and dispatch reporting package from the deterministic 50-vehicle, four-grid, 48-slot, seed-42 engineering validation. The script consumes completed simulator results, validates reporting invariants, and writes one-row-per-pricing-context and one-row-per-slot datasets under `results/validation/validation_50v_4g_48slots_seed 42/`, human-readable summaries under `results/tables/{pricing,customer_response,dispatch}/`, and 240-DPI figures under `results/figures/{pricing,customer_response,dispatch}/`. `summary.json` records the run configuration and reconciled totals; `figure_manifest.json` maps every figure to its compact source CSV.

These artifacts describe integration behaviour only. They are not results from the intended 5,000-vehicle January experiment, do not establish causal pricing effects, and do not identify an optimal pricing factor.

The completed Phase 7D production validation uses aligned frozen-CNN targets, authoritative popularity, a 5,000-vehicle fleet, and one NB13 round per slot. Its machine output is under `results/validation/phase7d_48slot_final_integrated_seed 42/`; the dated professor-review package is under `results/validation/2026-09-08_48slot_run/`. The older Phase 7C-4 output used misaligned prediction timestamps and is invalid for scientific performance interpretation; Phase 7C-6 is the corrected aligned preflight.

Passenger-trip duration and energy now use the intact sampled empirical TLC row. Busy state is temporally persistent across mini-slot and main-slot boundaries, and passenger energy remains deducted once across those advances. No centroid distance, grid-hop estimate, assumed speed, or external route model is used.

### Production validation status

The latest integrated validation is Phase 7D: 48 consecutive aligned target slots from **2026-01-25 19:00 inclusive to 2026-01-26 19:00 exclusive**, seed 42, fleet 5,000. All accounting/numerical gates passed, a fresh two-slot replay matched exactly, and the latest full regression passes **258 tests**. Status is **`READY_FOR_PHASE_8A`**. Machine output is in `results/validation/phase7d_48slot_final_integrated_seed 42/`; the dated chart/table package is in `results/validation/2026-09-08_48slot_run/`. The next proposed authoritative experiment is the complete 298-target held-out window ending 2026-02-01 00:00 exclusive.


</details>

## 7. Configuration reference

[config/config.yaml](config/config.yaml) selects active paths; [final temporal protocol](config/final_temporal_protocol.json) governs chronological use. Numeric project choices must not be cited as manuscript calibrations.

| Decision | Value | Classification |
| --- | --- | --- |
| CNN horizon | 30 minutes instead of source10 | DOCUMENTED_ADAPTATION |
| mu/sigma recurrences | Assignment-fare mean/population-SD EWMA | PROJECT_IMPLEMENTATION_DECISION |
| alpha, beta, delta, kappa | 0.3 each | PROJECT_CALIBRATION |
| F_hat_0, H_hat_0 | 0, 0 | PROJECT INITIALIZATION |
| sigma/H_hat safeguards | 1e−6 USD / minutes | PROJECT NUMERICAL SAFEGUARDS |
| Reposition coefficient | 0.25 normalized distance | PROJECT_CALIBRATION |
| H_i_max baseline | 10 minutes, explicit profiles | PROJECT_CALIBRATION, not manuscript-derived |
| H_i_max sensitivity | [5,10,20] minutes | PLANNED, not run |
| Pricing actions | 0.85–1.15, seven factors | PROJECT EXPERIMENTAL DESIGN |
| Record-029 cleaning/reference/support | <=100mi, ±$1, empirical P0.5–P99.5 | PROJECT METHODOLOGY DECISIONS |

### Frozen hierarchical temporal protocol

| Role | Inclusive slot-start range | Slots |
| --- | --- | ---: |
| CNN TRAIN | Jan1 00:00–Feb28 23:30 | 2,832 |
| Hierarchical RL development/training | Mar1 00:00–Mar15 23:30 | 720 |
| Integration/development exclusion | Mar16 00:00–23:30 | 48 |
| Final hierarchical evaluation | Mar17 00:00–Mar31 23:30 | 720 |

March16 was used for integration/debugging and one DQN optimizer update; it is excluded from final training/evaluation. March17–31 is protected prospectively for hierarchical evaluation, not claimed never examined in the original CNN evaluation. No model updates, feature fitting, threshold/hyperparameter tuning or checkpoint selection may use it. Guards reject updates on March16 and later and in evaluation mode, before slot mutation. Final pricing training must restart reproducibly from seed 42, not the March16 checkpoint. March1–15 reuses the original CNN validation interval intentionally for RL development.

[Temporal protocol, forecast availability and quarantine evidence](results/analysis/2026-10-21_final_temporal_protocol/README.md).

## 8. Fresh-machine installation

### Prerequisites

- Git (or an extracted repository archive)
- Conda/Miniconda/Anaconda
- Python 3.12-compatible platform and sufficient disk/RAM for the Jan–Mar taxi Parquets and generated arrays
- Internet access only when building/rebuilding Meteostat weather

```bash
git clone <repository-url>
cd Implementation
```

The intended Conda environment is named `ridehailing-phd`. The repository's current `environment.yml` defines only Python 3.12, `requirements.txt` is intentionally empty, and `requirements-lock.txt` contains machine-local build paths. Consequently, none of these files is currently a one-command portable environment specification.

Create the environment and install the previously recorded working dependency set (not a portable lock or a fresh-install verification):

```bash
conda create -n ridehailing-phd python=3.12 -y
conda activate ridehailing-phd

python -m pip install \
  numpy==1.26.4 scipy==1.14.1 pandas==3.0.5 pyarrow==25.0.0 \
  geopandas==1.1.4 shapely==2.1.2 pyproj==3.7.2 \
  PyYAML==6.0.3 scikit-learn==1.9.0 matplotlib==3.11.1 \
  mapclassify==2.8.1 meteostat==1.7.6 \
  tensorflow==2.16.2 keras==3.15.1
```

The explicit NumPy/SciPy/mapclassify/TensorFlow pins are important: newer incompatible combinations previously broke TensorFlow in the working environment. Current saved artifacts were built on macOS ARM, but the code makes no Apple-Silicon-specific installation claim; verify TensorFlow on the target machine.

```bash
python -m pip check
python -c "import tensorflow as tf; print(tf.__version__); print(tf.reduce_sum(tf.ones((2, 2))))"
python -c "import meteostat, numpy, scipy; print(meteostat.__version__, numpy.__version__, scipy.__version__)"
```

Run all commands from the repository root; imports use `src` directly rather than an editable package installation. For local module/scripts:

```bash
export PYTHONPATH=.
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=/tmp/ridehailing-matplotlib
python -c "import src; import pandas, pyarrow, geopandas, yaml; print('imports OK')"
```

The repository URL is installation-specific; `<repository-url>` above is a placeholder, not a claimed remote. A fully portable dependency lock remains unresolved. No installation or expensive workflow was executed for this documentation change.

## 9. Required data placement

Existing artifacts should be reused. Raw rebuilding is not needed to resume collection. Fresh reconstruction requires the January, February and March Yellow Taxi Parquets under `data/raw/yellow_taxi/`, the complete Taxi Zone shapefile/sidecars under `data/raw/taxi_zones/`, and existing monthly weather artifacts. Network access is needed only to fetch absent weather.

Current execution requires the142-grid foundation, Jan empirical request source, saved forecasts/popularity, historical fare/base lookups, behavioural-E calibration, explicit driver profiles, station/navigation artifacts and selected simulator-derived global routing model. Exact availability paths are recorded in [training input availability](results/analysis/2026-10-21_final_temporal_protocol/training_input_availability.json). Missing required inputs fail closed. Record-029's global P_base is not a replacement for runtime fare lookup.

## 10. Running Locally — reproducible workflow

Commands below are verified against existing entrypoints; they are **instructions, not runs performed for this update**. Commands that simulate/train write artifacts and require the corresponding stage to be intentionally started. Use a new output directory for any new experiment.

### Lightweight checks and current artifact validation

```bash
python -B -m unittest tests.test_final_temporal_protocol tests.test_passenger_arrival_boundary -q
python -B scripts/test_final_cnn.py
```

These use persisted artifacts; the arrival artifact tests describe the current six-slot checkpoint and may need an explicitly updated expectation after later generation. CNN validation does not retrain. See section12 for historical test evidence rather than assuming all suites are lightweight.

```bash
python -B scripts/activate_true_3km_foundation.py
```

The grid command takes its validate-only branch **only when** the existing `results/analysis/2026-10-19_true_3km_grid_activation/activation_complete.json` exists. Otherwise it builds/migrates artifacts; do not use it as a generic read-only command on an unprepared checkout. It also checks historical fingerprints, so later intentional artifact changes require interpretation of provenance failures.

### Existing CNN inference

No stable standalone inference CLI currently exists for this workflow; it is invoked through `src.demand.final_cnn.FinalDemandPredictor(model_dir, dataset_dir).predict(forecast_rows, grid)`. Use the epoch-200 model directory and `data/processed/cnn_jan_mar_2026_3km_30min/`. Input columns are TimeSlot, GridID, Row, Column, WeatherCode, Temperature, WindSpeed and ignored placeholder Demand; exactly142 mapped rows per aligned forecast timestamp. Output is a forecast DataFrame; the caller chooses persistence. Reuse the already saved forecasts for simulation. `scripts/train_final_cnn.py` is a training entrypoint, not an inference shortcut.

### Short development runner (inference-only)

```bash
python -B scripts/run_production_experiment.py --slots 4 --seed 42 --output results/local_hierarchical_dev
```

This existing CLI runs1–8 slots from its fixed March16 00:00 development start, defaults to **no DQN training**, and writes `runner_trace.csv`/`runner_metadata.json`. It loads the active fleet/profiles, forecasts, operational priors and selected simulator-derived routing checkpoint. It is not the final March17–31 evaluation launcher, nor a reproduction of the historical one-update episode. `--driver-profiles` accepts an explicit compatible Parquet. No start-date/training switch is exposed by this CLI.

### Completed runs and current blocked resume point

Routing generation and routing/FedAvg training are complete; do not rerun their historical launch commands. The pricing CLI `scripts/train_final_nonprivate_pricing.py` exists and completed720 slots. Its checkpoint/resume machinery remains available, but it must not be used to imply a corrected schedule or restart a completed experiment.

Corrected pricing retraining is blocked by the [professor gate](results/analysis/2026-10-26_professor_alignment_pricing_gate/README.md). No retraining/evaluation command is prescribed until acceptance-source alignment, hard driver-price eligibility and routing probability adequacy are resolved. March17–31 remains protected. Prior launch logs/PID files are historical records, not evidence of an active process.

### Broad tests / legacy workflows

`python -m unittest discover -s tests -q` is the existing unittest discovery command, but is **not certified as a safe current lightweight suite**: historical tests include training fixtures and old-domain assumptions. Use focused suites for current interfaces. Legacy builders and commands retained in section6.7 are provenance, not active reconstruction instructions.

## 11. Generated artifacts and model status

| Artifact | Status / use |
| --- | --- |
| [Epoch-200 CNN](models/cnn/jan_mar_2026_3km_30min_continued/best.keras) | FINAL FORECAST CHECKPOINT; historical-average baseline superior |
| [Legacy synthetic routing model](models/routing_policy/jan_mar_2026_3km_169x64x32x9/best.keras) | SUPERSEDED_FOR_FINAL_NON_PRIVATE_TRAINING / PROVENANCE_ONLY |
| [Selected global routing model](models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras) | SIMULATOR_DERIVED_ROUTING_BASELINE; probability adequacy limitation |
| [Completed pricing checkpoint](models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4/) | TRAINING_SCHEDULE_MISMATCH / NOT_FINAL_NONPRIVATE_BASELINE |
| [Standalone pricing fixture](models/pricing_dqn/standalone_13x64x64x7_fixture/) | IMPLEMENTATION FIXTURE ONLY |
| [March16 pricing checkpoint](models/pricing_dqn/first_short_hierarchical_20260316_0000_0200_seed42/) | INTEGRATION ONLY; do not continue for final experiments |
| [Routing generation checkpoint](data/processed/routing_experiences_mar01_mar15_2026/generation_checkpoint.pkl) | SUPERSEDED_PRE_REACHABILITY_RESERVE_GENERATION / PROVENANCE_ONLY |
| [RL-period forecasts](data/processed/cnn_jan_mar_2026_3km_30min/j_hat_epoch200_3km_142grids_mar01_15_2026_horizon30min.parquet) | 102,240 rows, March1–15 |
| [Original test-period forecasts](results/analysis/2026-10-19_operational_grid_state/dqn_ready_forecasts.parquet) | 109,056 rows, March16–31; protocol determines allowed use |
| [Driver profiles](data/processed/driver_preferences_seed42.parquet) | Explicit H_i_max 10,5,000 profiles |

Do not reuse the old ~914m/1,213-grid/51×52 artifacts, five-action or155D routing models, old-grid CNN/simulation results, synthetic routing policy as final, or integration DQN as final training initialization. Preserve them for provenance only.

## 12. Testing and evidence

The following are **recorded stage results**, not tests rerun for this README. Suites overlap; do not sum them as unique project tests.

| Stage | Recorded tests passed | Evidence |
| --- | ---: | --- |
| Final CNN | 22 | [Report](results/analysis/2026-10-19_final_jan_mar_3km_cnn/README.md) |
| Operational grid state | 36 | [Report](results/analysis/2026-10-19_operational_grid_state/README.md) |
| Driver/EV interface | 22 | [Report](results/analysis/2026-10-20_driver_ev_routing_state/README.md) |
| Routing configuration | 34 | [Report](results/analysis/2026-10-20_final_routing_configuration/README.md) |
| Synthetic routing policy | 35 | [Report](results/analysis/2026-10-20_final_routing_policy/README.md) |
| Pricing contract/state | 16 | [Report](results/analysis/2026-10-20_pricing_contract_and_dqn_state/README.md) |
| Standalone DQN | 23 | [Report](results/analysis/2026-10-21_standalone_pricing_dqn/README.md) |
| DQN simulator integration | 29 | [Report](results/analysis/2026-10-21_pricing_dqn_simulator_integration/README.md) |
| Runner migration | 70 | [Report](results/analysis/2026-10-21_hierarchical_runner_migration/README.md) |
| H_i_max | 9 | [Report](results/analysis/2026-10-21_himax_resolution/README.md) |
| Temporal protocol | 7 | [Report](results/analysis/2026-10-21_final_temporal_protocol/README.md) |
| Arrival boundary/resume | 9 | [Report](results/analysis/2026-10-21_passenger_arrival_boundary_fix/README.md) |

The four-slot episode additionally reconciled every slot reward, valid states/actions/replay, fleet conservation and checkpoint reload. Boundary-resume validation checked finite 169D states, nine-entry masks, allowed labels, contiguous unique IDs and unchanged first-slot hashes. Earlier 258-test legacy regression is historical, not a current whole-project pass count.

## 13. Reproducibility boundaries


The code centralizes seed 42 and uses deterministic ordering where possible: GridID ordering; zone-to-grid mapping; fleet placement; empirical trip-row sampling; empirical pickup-to-mini-slot mapping; initial SOC sampling; simultaneous charging priority; and NB12 state/action encoding. Customer acceptance uses its own explicit persistent RNG. NB4 uses a chronological split, and NB5 fits normalization on training features only.

The saved grid, weather, demand, tensor, station, and CNN provenance metadata provide artifact-level traceability. TensorFlow training is configured for best-effort deterministic behaviour, but identical training results should not be assumed bit-for-bit across operating systems, devices, TensorFlow builds, or CPU kernels.

The canonical temporal JSON, dated module reports and per-artifact metadata govern current reproducibility. Generation checkpoints preserve fleet, charging, operational state, commitments/missions, identifiers and RNG states; load only trusted locally generated checkpoints. Atomic file replacement is used, but retain matching slot/checkpoint files and validate integrity after interruptions. No bitwise cross-platform guarantee is inferred from a seed.

## 14. Research assumptions and limitations

- CNN underperforms the TRAIN historical-average baseline; final evaluation must report that baseline.
- Historically observed weather is not an issuance-time weather forecast. Naive taxi/weather alignment remains an inherited assumption.
- Zone-to-grid sampling approximates unavailable trip coordinates; projected neighbours and charging paths do not certify road connectivity.
- Selected simulator-derived FedAvg is below majority accuracy and worse than the masked training prior on CE/Brier. Complete clean experiences do not establish routing probability adequacy.
- March16 is contaminated for final evaluation and excluded. March17–31 is a prospective hierarchical holdout, not historically unseen by CNN reporting.
- H_i_max, operational coefficients and normalized movement-cost coefficient are project calibrations. Planned sensitivities are not results.
- Four-slot real-flow integration did not trigger charging; focused tests, not that episode, validate timed queue/navigation behavior.
- Runtime requests sample intact January empirical trips with forecast-driven counts; unsupported origins are explicitly reported. This is not replay of every actual March request.
- Plain FedAvg implementation does not establish differential privacy, secure aggregation or attack resistance. Those experiments remain pending.
- No final learned pricing-DQN performance or causal real-world optimal-pricing claim is supported.
- Dependency lock portability remains unresolved. The resumable long-period pricing launcher exists and completed720 slots; corrected cadence is unimplemented and final evaluation remains a separate future task.

## 15. Methodology provenance


Not all values in this repository have the same evidentiary status. Methodology authority is, in order: the corrected final implementation process; supervisor clarifications; cited mathematical sources for degradation, LinUCB pricing, and ordinary customer acceptance; and the broader execution plan where not superseded. NB1-NB5 compatibility decisions preserve the legacy notebooks. Unresolved modelling choices remain explicitly provisional.

For EV energy, the adopted Table I reference is: Zhaohao Ding et al., *Pricing Based Charging Navigation Scheme for Highway Transportation to Enhance Renewable Generation Integration*, IEEE Transactions on Industry Applications (2023). The code adopts its documented capacity, reference energy, consumption, and charging-power values; it does not claim that every operational SOC, queue, or release rule is literature-derived.

Current final/frozen reports supersede earlier blocked/provisional statuses only for the resolved module. In particular, H_i_max resolution supersedes migration startup blockage; arrival correction supersedes collection's original01:00 blocker; the epoch-200 continuation supersedes epoch 100 as active CNN. The final 169D state supersedes the spatial migration's interim 155D state. Numeric validation/test partitions are not conflated.

[Final hierarchical implementation audit](results/analysis/2026-10-18_final_hierarchical_rl_repo_audit/FINAL_IMPLEMENTATION_AUDIT.md) provides historical gap context; the newer dated reports linked above determine current status. Earlier clustering/literal-weather comparisons and reversed elasticity formulations must not replace Record-029 or the final analytical scenarios.

## 16. Pending work and roadmap

1. **Resolve professor-alignment blockers:** establish acceptance source/calibration semantics; approve/implement hard driver-price eligibility; resolve held-out routing-probability adequacy. No automatic model substitution.
2. **Approve corrected pricing cadence only after gates pass:** one update per5 eligible new transitions, exactly-once counters/remainder, all other settings unchanged. Not yet frozen or implemented.
3. **Corrected non-private pricing training:** only after approval, reset seed42 and run one March1–15 pass; use March16 inference-only development checks before freezing a final baseline. Completed prior run remains provenance.
4. **Final non-private evaluation:** March17–31 only, frozen inference/logging and no updates. Compare appropriate frozen fixed-price/LinUCB baselines without treating legacy-domain results as like-for-like.
5. **Privacy:** implement/finalize differential privacy, accounting and secure aggregation; plain FedAvg alone is insufficient.
6. **Robustness/adversarial evaluation:** poisoning, Sybil, strategic/malicious updates and robust aggregation.
7. **Ablations/sensitivity:** H_i_max 5/10/20 minutes, CNN versus historical-average demand, and only methodology-supported remaining ablations.
8. **Final experiments:** multiple seeds, uncertainty/statistical summaries, thesis tables/figures and transparent interpretation. No final claims before these stages.

**ROOT_README_CURRENT = YES** for the documented state, with the explicit unresolved implementation/setup limitations above. This is not a claim that the research programme is complete.

<!-- V1_STAGED_001_STATUS -->


## V2 full-day dynamic-value audit — 15 November 2026

[Audit and evidence](results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/README.md): the exact Episode25 March16 replay screened 15,800 lower-price choices. Immediate assignment divergence occurs in 33.82%; 20 genuinely divergent cases were rolled across two boundaries, alongside two eligibility-only comparisons and two passing identical-action controls. One partial recovery, one full recovery, and zero net-positive cases were observed. Q favored the lower action in all 20, but was incorrect in 19 with one undiscounted tie; all 20 discounted comparisons were unfavorable.

DYNAMIC_VALUE_OPPORTUNITY = **MEANINGFUL** (immediate state changes); DYNAMIC_VALUE_EVIDENCE = **WEAK** (bounded recovery, no net gain); LONGER_TRAINING_RECOMMENDATION = **NO** on the present evidence. These supersede the earlier bounded-review NONE/CONDITIONAL evidence and recommendation. The chronological sample does not cover every hour or the peak-demand quartile and is not proof of global Highest Feasible dominance. Do not simply extend training; any further investigation requires a separate scoped decision. Episode26 remains **NOT_STARTED**. March17–31 remains **UNTOUCHED**. No production, calibration, training or baseline artifact was changed by this audit.
