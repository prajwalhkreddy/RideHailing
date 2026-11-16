# Episodes1–10 academic review

## Executive summary

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

EARLY_TRAINING_REVIEW. Training completed through Episode10 with no recorded failure; saved gates support numerical stability, checkpoint validity and unchanged routing. LEARNING_STARTED=YES. CONVERGED=NOT_ESTABLISHED. POLICY_STABLE=NOT_ESTABLISHED. No fixed policy evaluation supports superiority, optimality or production-readiness claims.

Stage2 totals are Episodes2–10 only: requests269726; accepted62459; rejected207267; assignments48862; accepted-unmatched13597; accepted revenue1592945.6USD. The common block above correctly adds Episode1 using saved artifacts.

## Source authority and reporting scope

The exact consolidated roadmap, latest dynamic-pricing clarification and weather-scenario explanation were read; extracted texts and hashes are in tables/source_authority.csv and source_manifest.json. The separately requested PhD_Meeting_Discussion_Detailed_Explanation.pdf was not found in the project. Its source numbering/content is not independently verified; the consolidated roadmap explicitly describes incorporating the meeting explanation. This is a disclosed source-document gap, not invented evidence.

## Passenger acceptance, offers and dispatch

Actions are selected proactively for142 destination contexts before each30-minute slot; requests inherit the context action. Common frozen P_base=22.354198442390455USD, L_base=4.616983790655043km. P_offer=alpha*P_base. P_max=P_base+(P_base/epsilon)*(L−L_base)/L_base. Actual accepted boolean is preserved; all saved requests satisfy the inclusive comparison (zero mismatches). The checkpoint's primitive request audit was extracted without constructing runtime objects or drawing samples. Full audit: tables/request_level_audit.parquet. Sample: earliest slot nearest median request volume; up to300 evenly spaced request IDs. Origin is unavailable; other acceptance inputs and joined slot/context action are retained. P_offer/P_max plots use this deterministic actual sample and linear axes without clipping.

Passenger rejection is distinct from accepted-but-unmatched. Assignment counts describe dispatch, not completed rides. CAUSE_NOT_PERSISTED; no causal explanation of unmatched counts is inferred. Driver eligibility in src/dispatch/dispatch.py:find_eligible_vehicle requires offered fare >= persisted profiles.price_preference for an otherwise eligible vehicle. src/simulation/slot_pricing_v3.py passes engine.profiles.price_preference. No hypothetical0.85*P_base driver rule is substituted. REQUEST_LEVEL_DRIVER_REJECTION_DIAGNOSTIC_NOT_AVAILABLE.

## Action economics and reward

| action | factor | P_offer | requests_exposed | acceptance_rate | accepted_revenue_per_exposed_request |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.2952465514256313 | 6.6000000000000005 | 43093 | 0.762420810804539 | 5.031977351309943 |
| 1 | 0.9520955711377048 | 21.28333333333333 | 42130 | 0.3381675765487776 | 7.197333254213148 |
| 2 | 1.6089445908497786 | 35.96666666666667 | 40473 | 0.1649741803177427 | 5.933571352094814 |
| 3 | 2.265793610561852 | 50.65 | 44206 | 0.1130163326245306 | 5.724277247432475 |
| 4 | 2.922642630273926 | 65.33333333333334 | 41160 | 0.08841107871720116 | 5.776190476190478 |
| 5 | 3.5794916499859992 | 80.01666666666667 | 39641 | 0.07499810801947479 | 6.0010986100249735 |
| 6 | 4.236340669698073 | 94.7 | 43116 | 0.05847017348548103 | 5.537125429075054 |

The observed price/acceptance/revenue trade-off is descriptive; action exposures differ by context and time. The most frequent or highest-revenue action is not declared best. Reward is accepted offered revenue including accepted-unmatched, not served/platform realised earnings. Slot accepted offers, reward, replay reward and context sums reconcile to legitimate floating-point summation tolerance.

## Learning and chronology

Sequential chronological windows; not controlled policy comparisons. Demand, weather, fleet and policy can all change. This caveat appears on every episode-comparison chart. Loss is the saved mean of eight updates per warm slot, not a complete per-update trace. Episode means average those equal-sized update blocks. Q/TD, target statistics, online-target differences and weight-change norms were not persisted per episode: NOT_AVAILABLE_FROM_PERSISTED_V3_ARTIFACTS. Loss does not establish Q magnitude or convergence. Warmup1000, eight updates per warm slot, Episode1 updates72 and Episode10 cumulative1224 are reconciled; epsilon follows cumulative optimizer updates only.

## Sensitivity and weather/time

Runtime tables include only exercised conditions, using saved request draws directly for SD/quantiles. Frozen families: GLOBAL/RAW_15/T3_POOLED/T4_POOLED truncated normal; RAW_13/T1_G1/T1_POOLED lognormal; T2_POOLED generalized gamma. T2–T4 are DENSE_SCENARIO_POOLING_DUE_TO_CLUSTER_INSTABILITY, not sparse fallback. T1 raw/pool eligibility fallbacks are recorded separately; fallback_level is retained without misleading relabelling. Family-fit errors in methodology_contract.json remain limitations; T1 median overestimation is approximately20% in the saved fit comparisons. Runtime quantiles summarize saved draws, not a refit or proof of exact empirical fit.

## Operational, routing, fleet and causal state

Routing checkpoint/hash is recorded in tables/routing_health.csv. Routing169D→64→32→9 remains frozen; action order STAY,N,NE,E,SE,S,SW,W,NW. Saved valid15D next-state checks include the nine-probability block; no pricing-induced routing training. Existing routing-readiness evidence (MODEST / UNCERTAIN BUT POSITIVE; non-STAY signal INCONCLUSIVE) is reproduced in tables/frozen_routing_readiness_reference.json, including its limitations; public-state label nonidentifiability remains a concern. Operational traces contain finite mu/sigma/F_hat/H_hat for all observed boundaries. Persistent evolution is supported by the full-runtime continuation contract and saved gates; it is not independently inferred merely from smooth plotted values. Fleet health reports conserved counts, active commitments/missions and cumulative charging-event counters. Event counts are not charging completions or durations. Dedicated per-cause energy/double-assignment counts were not saved; only runtime hard checks/gates are asserted.

Drop-off uses frozen causal lagged moving-average destination counts, normalized at the current boundary, with carry-forward/historical initialization. No future data are introduced. Detailed probability histories are not regenerated; saved state and technical validations are the evidence.

## CNN and historical fare evidence

Reuse only saved epoch200 March1–15 validation from continuation_history.csv and the declared split: tables/cnn_validation_reused.csv. MAE/RMSE and population are traceable there. R²/NRMSE/volume error and an authoritative safe-population actual-versus-predicted chart were not persisted in these validation artifacts: NOT_PREVIOUSLY_VALIDATED. Existing CNN TEST charts span March16–31 and were not opened/reused. No CNN retraining/inference was run.

Historical fare-distance investigation is linked, not recalculated: results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_vs_distance_hexbin.png (historical calibration context, not V3 training results). V3 numerical fare support is exclusively the pinned fare_bounds_contract.json; broad empirical bounds are project-approved, not statutory limits or proof of economic optimality.

## Privacy and limitations

CURRENT_V3_BASELINE=NON_PRIVATE. DIFFERENTIAL_PRIVACY=NOT_IMPLEMENTED/NOT_EVALUATED; privacy epsilon/delta/noise/clipping/accounting and privacy-versus-utility are NOT_APPLICABLE_TO_CURRENT_BASELINE. Only Episodes1–10 are scientifically reviewed. Episode11 and partial12 provenance is excluded from all numerical review inputs. No protected-period generalization or convergence is tested. Request origins and driver/dispatch cause diagnostics are unavailable; source PDF and CNN validation visualization gaps remain explicit. Selected sensitivity fits are approximations. Later process status is a provenance snapshot, not a claimed operational stop.

## Questions for Academic Review

1. Is the wide empirical fare-support action range acceptable given observed acceptance/revenue?
2. Is the grouping and selected parametric sensitivity approach acceptable?
3. Is slot-level accepted-revenue the desired objective?
4. Should accepted-but-unmatched revenue remain in pricing reward?
5. Are16-slot/8-hour terminal segments appropriate?
6. What horizon and fixed evaluation are required for convergence/stability claims?
7. Is fixed development evaluation needed before further training?
8. What evidence is required before Differential Privacy?

## Files and reproducibility

Run `MPLCONFIGDIR=/tmp/v3_review_mpl /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/report_v3_ep01_ep10.py` from the project root. This reads saved Episode10 evidence only; no model or simulator imports. artifact_provenance.csv, source_manifest.json and chart_manifest.json give filters, columns, counts, aggregation and hashes. Numbered tables01–10 and charts are provided in tables/ and charts/. Reporting tests validate scope, reconciliations, unavailable fields and documentation consistency.
