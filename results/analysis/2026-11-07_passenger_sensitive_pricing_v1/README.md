# Passenger-Sensitive Pricing V1

## 1. Executive Status

`PASSENGER_SENSITIVE_PRICING_V1_CANONICAL_DOCUMENT = YES`

| Item | Status |
| --- | --- |
| Methodology | IMPLEMENTED / VALIDATED |
| Sensitivity calibration | FROZEN |
| Sensitivity sampling | FROZEN |
| Request-level architecture | FROZEN |
| Bellman semantics | CORRECTED / FROZEN |
| Training completed through | EPISODE 25 |
| Technical invariants | PASS |
| Numerical stability | YES |
| Learning signal | YES |
| Policy stability | NO |
| Convergence | NO |
| Action-dominance risk | HIGH |
| DQN incremental dynamic value | UNRESOLVED |
| Further training | AWAITING_ACADEMIC_REVIEW |
| Protected final evaluation | UNTOUCHED |

## 2. Research Objective

The original consolidated formulation connected passenger sensitivity and actual OD distance L_gg′ to a raw passenger preference, platform price boundaries, DQN pricing factors, an acceptance threshold and downstream dispatch. V1 asks whether a request-level learned pricing policy adds dynamic value beyond simple feasible-price rules when interacting with driver availability and future fleet state. Historical signed sensitivity and earlier formulations remain traceable; simulated acceptance is not an identified causal willingness-to-pay response.

## 3. Original Formulation and Requested Decisions

Evidence hierarchy used throughout: **Level 1**, consolidated Passenger-Sensitive Dynamic Pricing formulation, supplies original objectives/proposals only; **Level 2**, approved reconciliation and Bellman decisions, supersedes conflicting proposals; **Level 3**, persisted CSV/JSON, controls numerical results; **Level 4**, historical Record-029, provisional calibration and superseded training, supplies provenance only. The original requirement inventory below follows the approved consolidation request and existing V1 specification; equation numbering is not independently verified. This inventory does not imply every original proposal was implemented unchanged.

| Original formulation requirement | Final V1 resolution | Status | Canonical section |
| --- | --- | --- | --- |
| 1. Define P_base | Frozen global reference 21.34586956773507 USD | RESOLVED | §8 |
| 2. Define L_gg′ | Actual request OD distance in km | RESOLVED | §8 |
| 3. Define L_base | Frozen reference 4.856998243316242 km | RESOLVED | §8 |
| 4. Epsilon sign/magnitude | Historical signed values preserved; positive absolute proxy for V1 | RESOLVED | §7 |
| 5. Epsilon calibration | Jan1–Mar15 VALID finite nonzero; abs first, then positive quantiles | RESOLVED | §7 |
| 6. Passenger preference | P_base-scaled P_raw_c expression | RESOLVED | §8 |
| 7. Effective threshold | max(platform minimum, P_raw_c) | RESOLVED | §9 |
| 8. NYC/platform limits | Project platform bounds; statutory NYC rule NOT ESTABLISHED | RESOLVED | §9 |
| 9. alpha_min / alpha_max | 0.85 / 1.15 project design choices | RESOLVED | §10 |
| 10. DQN factors | Seven factors, 0.05 spacing | RESOLVED | §10 |
| 11. Final offer | P_offer = a * P_base | RESOLVED | §9 |
| 12. Acceptance | P_offer <= P_accept_c | RESOLVED | §9 |
| 13. Exceeded threshold | Mask before selection; ORIGINAL PROPOSAL SUPERSEDED where raw-only rejection was used | SUPERSEDED | §12 |
| 14. d_min | Not used; sufficient NYC minimum-distance basis not established | NOT_USED | §9 |
| 15. Sensitivity distribution | Signed, absolute, supported and T0–T3 comparison persisted | RESOLVED | §7 |
| 16. Negative/unusual P_raw_c | Persisted raw/effective categories; negative raw values retained diagnostically | RESOLVED | §15 |
| 17. Four diagnostic groups | G1–G4 aggregate diagnostics persisted, historical raw-threshold outcomes identified | RESOLVED | §15 |
| 18. Arm coverage | Dataset justification MODERATE; not uniquely derived | RESOLVED | §10 |
| 19. Outcome categories | Feasible offer, assigned, accepted-unmatched; defensive invalid/no-action | RESOLVED | §12 |
| 20. Request OD/distance logging | Saved request-level validation CSVs contain request pricing/masking evidence | RESOLVED | §15 |
| 21. End-to-end workflow | Request-level algorithm below | RESOLVED | §14 |
| 22. Pre-coding unresolved decisions | Implementation choices frozen; causal interpretation and incremental DQN value remain unresolved research questions | UNRESOLVED | §27 |

## 4. Academic-Review Feedback

Each feedback response below is supported by the reconciliation validation and analysis summary linked at the end of this section.

| Academic-review feedback | Resolution in V1 |
| --- | --- |
| Overall formulation/document acceptable | Consolidated framework retained, with explicit project implementation decisions. |
| Section V must explain sensitivity distribution, random sampling and truncation; truncation need not be symmetric | Signed, absolute and supported distributions documented; T0–T3 comparison includes asymmetric probability cuts; empirical row resampling specified. |
| Negative sensitivity may occur; absolute values acceptable | Historical signed observations preserved; V1 uses positive sensitivity magnitude after date/VALID filtering. |
| Effective preference should use max(NYC minimum price, passenger-preference expression) | Project operationalizes platform minimum as 0.85×P_base and P_accept_c=max(platform minimum,P_raw_c); this is not a verified statutory NYC minimum. |
| Pricing factors need dataset justification | Coverage and distance-conditioned evidence reported; MODERATE justification for a bounded experiment, not unique optimal endpoints. |

`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED = NO`  
`V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION = YES`

The available consolidated formulation contains the P_base-scaled adjustment. The review accepted the overall document, but equation numbering cannot be mapped unambiguously across historical documents. An explicit project decision resolves the intended expression; it does not verify the equation number.

Evidence: [review_feedback_validation.json](review_feedback_reconciliation/review_feedback_validation.json) and [analysis_summary.json](review_feedback_reconciliation/analysis_summary.json).

## 5. Final V1 Decisions

Active contract: positive sensitivity magnitude, inclusive positive support, empirical resampling, scaled raw preference, platform-min protected threshold, masked request-level DQN and gamma0.99/request. `d_min=NOT_USED`. No methodology changes are made by this documentation consolidation.

[Concise active methodology](METHODOLOGY.md)

## 6. Data and Temporal Boundaries

V1 calibration: **Jan1–Mar15 only**. Training: **March1–15**. March16: **development only**. March17–31: **protected final hierarchical evaluation**. Historical full-period Record-029 remains separately preserved; no historical numerical artifacts change.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

## 7. Passenger Sensitivity

Sources: [sensitivity_distribution_summary.csv](review_feedback_reconciliation/sensitivity_distribution_summary.csv), [sensitivity_truncation_comparison.csv](review_feedback_reconciliation/sensitivity_truncation_comparison.csv), and [restricted_calibration_support.json](restricted_calibration_support.json).

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

| distribution | N | mean | SD | median |
| --- | --- | --- | --- | --- |
| SIGNED_HISTORICAL_SENSITIVITY | 8685488 | 0.640620734577789 | 7.106334709447966 | 0.762119875337521 |
| POSITIVE_V1_BEHAVIOURAL_PROXY_BEFORE_SUPPORT | 8685488 | 1.4146378807714861 | 6.993510391395895 | 0.8201258184287152 |
| POSITIVE_V1_SUPPORTED_T0 | 8598805 | 1.0952985082713345 | 1.8173002121616255 | 0.8201228772641369 |

Date restriction and VALID/finite/nonzero selection precede the absolute-value transformation; positive quantiles follow it. Signed historical support is not applied before abs(). Historical negative values remain valid historical evidence. V1 runtime receives sampled positive magnitudes, not signed sensitivities.

T0 is symmetric in nominal tail probability, **not** numerical epsilon magnitude. Asymmetric alternatives were considered: T1=P0.5–P99, T2=P1–P99.5, T3=P1–P99. T0–T3 did not establish a superior alternative; T0 remains frozen. Duplicate empirical values make exact retained/tail percentages differ slightly from nominal percentages. The bounds regularize reciprocal sensitivity while preserving the central empirical distribution; excluded observations are not relabelled invalid.

`epsilon_min` is the support lower bound itself. **No additional floor** is active; P0.5/P1/P2.5/P5 post-support floor candidates are historical diagnostics. **TRUNCATED_EMPIRICAL_RESAMPLING** samples supported rows with replacement, preserving empirical duplicate frequencies and shape/skew/tails within support, using a caller-controlled deterministic seed. The global positive pool is used; no parametric family, Gaussian fit, or unsupported time-group model is imposed.

| candidate | lower | upper | retained_N | retained_pct | epsilon_mean | epsilon_SD | epsilon_median | no_offer_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T0 | 0.017809913104763053 | 27.324599740032788 | 8598805 | 99.00197893313536 | 1.0952985082713345 | 1.8173002121616255 | 0.8201228772641369 | 0.0 |
| T1 | 0.017809913104763053 | 14.266571518308252 | 8555302 | 98.50110897626017 | 1.0019966552151045 | 1.2364511117325305 | 0.8180437415878093 | 0.0 |
| T2 | 0.03214336441012345 | 27.324599740032788 | 8555281 | 98.5008671936453 | 1.1007459868683243 | 1.8203073174930835 | 0.8221144799085167 | 0.0 |
| T3 | 0.03214336441012345 | 14.266571518308252 | 8511778 | 97.99999723677011 | 1.0069948871105217 | 1.237625957545162 | 0.8201258184287152 | 0.0 |

## 8. Passenger Price Preference

```text
P_base = 21.34586956773507 USD
L_base = 4.856998243316242 km
L_gg_prime = actual passenger OD distance in km
P_raw_c = P_base + (P_base / epsilon_c) * ((L_gg_prime - L_base) / L_base)
P_platform_min = 0.85 * P_base
P_platform_max = 1.15 * P_base
P_accept_c = max(P_platform_min, P_raw_c)
P_offer = a * P_base
feasible action: P_offer <= P_accept_c
```

P_raw_c is raw passenger preference; P_accept_c is the effective passenger acceptance threshold. Historical Pc/Pmax names are aliases only in their dated source context, not competing active formulas. The upper offer bound is enforced by the largest configured action, 1.15; P_raw_c/P_accept_c are not upper-clipped. The expression lacking the P_base adjustment multiplier is **SUPERSEDED_HISTORICAL_FORMULATION**.

## 9. Platform Price Limits and Effective Acceptance Threshold

The former condition `P_offer <= P_raw_c` produced **61.746289%** no-feasible/no-offer outcomes: **SUPERSEDED_RAW_THRESHOLD_DIAGNOSTIC**. Under `P_offer <= max(0.85*P_base,P_raw_c)`, valid-request no-feasible rate is **0%**, by construction because the minimum arm remains feasible. This is not evidence of improved real-world demand. No post-selection clipping is performed. `d_min = NOT_USED`; no deterministic minimum-distance fare rule is active.

The original d_min proposal was not supported sufficiently to implement a NYC minimum-distance/flat-fare mechanism. No statutory NYC rule is asserted.

## 10. DQN Pricing Actions

Actions remain **[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]**. Dataset justification is **MODERATE**. Coverage of observed fare/P_base in 0.85–1.15 is **14.379973%**, measured on all 8,692,819 cleaned **Jan1–Mar15** fares in the saved factor study—not March16 development requests and not only supported epsilon rows. This period distinction avoids mislabelling “development-fare coverage.” Distance-band evidence uses km after converting historical miles. Exact endpoints and 5% spacing are project design choices; neither empirical optimization nor a full-market fare envelope is claimed.

`alpha_min = 0.85`; `alpha_max = 1.15`. Source: [pricing_factor_dataset_justification.csv](review_feedback_reconciliation/pricing_factor_dataset_justification.csv).

## 11. Request-Level DQN Architecture

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

Hidden layers use ReLU. Optimizer/replay settings are specified below.

## 12. State, Masking, Replay and Reward

The unchanged 13D context does not append passenger attributes. They constrain the feasible action set before selection and target maximization. Masked-out Q values cannot win; terminal transitions have no bootstrap. Empty masks are defensive invariant/data-quality cases only.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

## 13. Bellman Discount Semantics

Saved diagnostic context: 37,111 requests / 16 slots = 2,319.4375 requests per slot (2,319.44 displayed); P95 request gap was 2 seconds.

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

`OLD_TIME_AWARE_DISCOUNT = SUPERSEDED`. Sources: [bellman_discount_comparison.csv](bellman_discount_correction/bellman_discount_comparison.csv), [effective_horizon.json](bellman_discount_correction/effective_horizon.json).

## 14. Final End-to-End Algorithm

1. Receive the chronological request.
2. Determine OD and actual L_gg_prime in km.
3. Sample positive passenger sensitivity magnitude from the approved empirical support.
4. Compute P_raw_c.
5. Compute P_accept_c.
6. Construct the seven candidate fares.
7. Mask infeasible actions.
8. Construct the unchanged 13D state.
9. Use epsilon-greedy DQN selection among feasible actions (greedy for development).
10. Set P_offer = selected factor × P_base.
11. Apply downstream driver eligibility and dispatch.
12. Record assignment-time P_offer reward, or zero if accepted-unmatched.
13. Construct the transition to the next chronological actionable request; terminal has no bootstrap.
14. Use masked Bellman maximization with gamma = 0.99 per request transition.
15. Perform eight optimizer updates only at each completed warm slot boundary.
16. Maintain Jan1–Mar15 calibration, March1–15 training, March16 development and protected March17–31 boundaries.

## 15. Implementation Validation

Saved reconciliation reports **57 focused tests passed**; later Bellman correction reports **37 passed**. These are different validation stages, not an asserted non-overlapping total. Authoritative staged training reports zero hard-invariant violations. Sources: [reconciliation validation](review_feedback_reconciliation/review_feedback_validation.json), [Bellman decision](bellman_discount_correction/discount_methodology_decision.json), [completion record](staged_training_002/stage_ep25_complete.json).

### Original four-group diagnostic

The diagnostics were computed and persisted in [epsilon_four_group_diagnostics.csv](epsilon_four_group_diagnostics.csv), with definitions in [pricing_v1_spec.json](pricing_v1_spec.json): G1 distance below L_base / epsilon below 1; G2 below / epsilon at least 1; G3 distance at least L_base / epsilon below 1; G4 at least / epsilon at least 1. These inspect raw equation behaviour across distance/sensitivity regimes. Their raw Pc/no-feasible columns predate the effective-threshold correction and are **SUPERSEDED_RAW_THRESHOLD_DIAGNOSTIC**, not current no-offer rates. Detailed group values are available in the saved V1 calibration artifacts and are not reproduced here.

### Negative and unusually low raw preference

[raw_vs_effective_preference_summary.csv](review_feedback_reconciliation/raw_vs_effective_preference_summary.csv) preserves negative, nonpositive, positive-below-minimum and boundary categories. Applying P_accept_c does not remove negative P_raw_c from that diagnostic. The following are literal T0 source rows (overlapping categories must not be added):

| candidate | category | N | percentage |
| --- | --- | --- | --- |
| T0 | raw_lt_0 | 1229215 | 14.2951840401079 |
| T0 | raw_le_0 | 1229215 | 14.2951840401079 |
| T0 | raw_positive_below_min | 4080228 | 47.451105124491136 |
| T0 | raw_equal_min_tolerance | 0 | 0.0 |
| T0 | raw_within_platform_bounds | 958180 | 11.143176290193813 |
| T0 | raw_above_max | 2331182 | 27.110534545207155 |
| T0 | effective_min_protection_applied | 5309443 | 61.746289164599034 |

Request OD/distance, raw/effective preference and mask evidence: [request-level reconciliation validation](review_feedback_reconciliation/request_level_review_feedback_validation.csv). These are saved checks, not a new run.

## 16. Staged Training Protocol

`staged_training_002` is authoritative: fresh online/target/Adam/replay/exploration/RNG/counters, seed42. Neither staged_training_001 nor historical pre-reformulation Episode25 was loaded. Stages1/2/3 completed Episodes1,2–10,11–25. Episode1→2 restored replay37,111, updates128, epsilon0.997568; Episode10→11 restored replay100,000, updates1280, epsilon0.97568. Network, target, Adam, chronological replay order, learner/action RNG, replay RNG, counters and persisted scheduler were verified. The full deque serializes oldest-to-newest order; no separate circular cursor is required. Episode25 finished with3200 updates and epsilon0.9392. All stage technical gates PASS; no protected-date access or development learner mutation.

## 17. Episode 1 Results

One authoritative training table, copied exactly from [stage_summary.csv](staged_training_002/stage_summary.csv); rates are fractions. It contains all three milestones to avoid competing tables.

| episode | requests | assignments | assignment_rate | revenue | choice_rate | forced_rate | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 37111 | 33528 | 0.9034518067419364 | 642375.1277170705 | 0.3415968311282369 | 0.6584031688717631 | 37111 | 128 | 0.997568 | 4.12795352935791 | 39.37099838256836 | 20.916427612304688 | 24.33213622868061 | 1723.7844172339624 | 1797.625860512767 | 1725.6982792303747 |
| 10 | 39488 | 31657 | 0.8016865883306321 | 606587.7100932841 | 0.3226803079416531 | 0.6773196920583469 | 100000 | 1280 | 0.97568 | 55.03794479370117 | 130.9333953857422 | 11.20116901397705 | 8.368096370249987 | 1528.8378225371955 | 1561.104081800609 | 1479.3690870844543 |
| 25 | 51654 | 22536 | 0.4362876059937275 | 435187.8485187203 | 0.286463778216595 | 0.7135362217834049 | 100000 | 3200 | 0.9392 | 138.2930450439453 | 196.00808715820312 | 12.567835807800293 | 13.262940563261509 | 838.0126914780998 | 841.8086214690959 | 722.3233429145478 |

Episode1 review PASS; early finite Q below MC is not failure.

## 18. Episode 10 Results

Episode10 scientific review **PASS**. See the single table in §17. Numerical stability and learning signal were observed; convergence was not established.

## 19. Episode 25 Results

Episode25 technical **PASS**. See §17 for exact results. Current interpretation: NUMERICALLY_STABLE=YES; LEARNING_SIGNAL=YES; Q_SCALE_TREND=APPROACHING_RETURN_SCALE; POLICY_STABLE=NO; CONVERGED=NO. Different training dates are not controlled performance comparisons.

## 20. Fixed March16 Development Evaluation

Identical **March16 00:00–02:00** fixture; this is the direct checkpoint comparison. Literal [development_evaluation.csv](staged_training_002/development_evaluation.csv) values:

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q | learner_unchanged |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982381959126 | 54330.57451727768 | 19.61631258848888 | 0.4506694855532064 | 0.5493305144467935 | 3.10725998878479 | 33.48653793334961 | True |
| 10 | 2838 | 2792 | 0.9837914023960536 | 56855.79088714074 | 20.32821764648258 | 0.4506694855532064 | 0.5493305144467935 | 58.99930191040039 | 104.06543731689452 | True |
| 25 | 2838 | 2786 | 0.981677237491191 | 56419.26785448056 | 20.220284866955804 | 0.45066948555320646 | 0.5493305144467935 | 147.33767700195312 | 199.55938720703125 | True |

No learner mutation; reused development fixture, not protected final evaluation.

## 21. Q, TD, Loss and MC-Return Diagnostics

| episode | kind | N | mean_G | median_G | mean_selected_Q | median_selected_Q | MAE_Q_G | correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | training | 512 | 1723.7844172339624 | 1797.625860512767 | -1.9138621091842651 | -1.9691829681396484 | 1725.6982792303747 | -0.1769950055292727 |
| 1 | development | 512 | 1844.543321878771 | 1923.1035561987323 | 2.950186967849731 | 1.41369891166687 | 1841.5931349245127 | 0.0541167532018389 |
| 2 | training | 512 | 951.5163951391892 | 946.0823375788256 | -5.52747917175293 | -5.965036392211914 | 957.0438741847552 | -0.0452926587138035 |
| 3 | training | 512 | 1113.5402675551782 | 1087.268488877642 | 1.687744379043579 | -0.016710240393877 | 1111.8525233162477 | 0.2570051960233475 |
| 4 | training | 512 | 791.87360233267 | 785.1545887623122 | 3.572866439819336 | 1.4406996965408323 | 788.307896683741 | -0.0334617347610846 |
| 5 | training | 512 | 870.2043713476216 | 830.6409957646157 | 11.249441146850586 | 10.989211082458496 | 858.9549310883215 | -0.0770081364101783 |
| 6 | training | 512 | 969.1404768615328 | 962.309128104318 | 12.123449325561523 | 11.244009971618652 | 957.0170271961696 | 0.1493381381941144 |
| 7 | training | 512 | 1771.863825103815 | 1822.9247172207115 | 29.626771926879883 | 28.290069580078125 | 1742.304147872948 | 0.2351187526104314 |
| 8 | training | 512 | 1379.9318383828972 | 1384.8568938768112 | 29.0412540435791 | 28.459117889404297 | 1350.908765019391 | 0.3206197661572436 |
| 9 | training | 512 | 1720.810579904896 | 1842.5318093948 | 44.959739685058594 | 35.72077941894531 | 1675.8751365387684 | 0.3181479844070212 |
| 10 | training | 512 | 1528.8378225371955 | 1561.104081800609 | 49.738243103027344 | 48.15941619873047 | 1479.3690870844543 | 0.1208448865635501 |
| 10 | development | 512 | 1931.4234052606323 | 2000.306301985868 | 58.38206100463867 | 54.22560119628906 | 1873.1609932059869 | 0.1160127392087612 |
| 11 | training | 512 | 1541.3446465189377 | 1716.2522111741382 | 55.07241439819336 | 53.81820297241211 | 1486.5437158380494 | 0.46903787693883897 |
| 12 | training | 512 | 1275.1961654025968 | 1242.9300768565945 | 53.987117767333984 | 53.945186614990234 | 1221.3662387346803 | 0.31138270180943123 |
| 13 | training | 512 | 1110.2607460890072 | 902.332777770352 | 59.028709411621094 | 55.070533752441406 | 1051.4388943170093 | 0.734539089952802 |
| 14 | training | 512 | 1158.2622527964613 | 1097.277958130962 | 57.813621520996094 | 54.9453239440918 | 1100.6111269647506 | 0.4123747132058548 |
| 15 | training | 512 | 1251.7881246988654 | 1277.2853835618798 | 70.49057006835938 | 70.31169891357422 | 1181.5041516661531 | 0.4088148976269405 |
| 16 | training | 512 | 699.0748891011415 | 675.9519961456857 | 64.71783447265625 | 64.82748413085938 | 634.6126702651917 | 0.23419805646758143 |
| 17 | training | 512 | 1379.391493519863 | 1425.0656233263635 | 87.4944076538086 | 86.62220764160156 | 1292.2560581018179 | 0.6596076838395831 |
| 18 | training | 512 | 1579.8103288364684 | 1760.0937468715792 | 96.92030334472656 | 97.47256469726562 | 1483.164842766444 | 0.6160908338925936 |
| 19 | training | 512 | 1419.266237742304 | 1486.2584925757465 | 104.46434020996094 | 104.95255279541016 | 1315.1600907738684 | 0.5235160820639642 |
| 20 | training | 512 | 829.5700879242715 | 819.4831465816578 | 98.03633880615234 | 97.78824615478516 | 731.883880138069 | 0.2820693128901575 |
| 21 | training | 512 | 1280.6568175407428 | 1266.4058353286591 | 115.1433334350586 | 114.31388854980469 | 1165.9205358345412 | 0.2144216866651364 |
| 22 | training | 512 | 1053.0823199294114 | 1056.6835005775984 | 112.59097290039062 | 111.98492431640625 | 940.9198412887358 | 0.440300557728774 |
| 23 | training | 512 | 557.4249920761574 | 511.7847580453305 | 93.43147277832031 | 89.21627044677734 | 464.5118199210041 | 0.4625686019291065 |
| 24 | training | 512 | 1337.0202909930067 | 1335.8419215435433 | 152.3071746826172 | 151.23330688476562 | 1185.2169098274908 | 0.6462482769963303 |
| 25 | training | 512 | 838.0126914780998 | 841.8086214690959 | 116.19981384277344 | 114.1672592163086 | 722.3233429145478 | 0.3573547288750529 |
| 25 | development | 512 | 1916.4838858749636 | 1991.2820598378285 | 147.06478881835938 | 153.3709716796875 | 1770.0806637186874 | 0.0023902998397779336 |

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

## 22. Choice vs Forced Requests

A **forced request** has K=1 feasible arm; a **choice request** has K≥2. Episode25 development has1,559 forced and1,279 choice requests (choice rate0.450669486). Choice counts for factors0.85/0.90/0.95/1.00/1.05/1.10/1.15 are **78/75/36/17/62/991/20**. Factor1.10 dominates the current greedy choice policy: approximately92.60% for K=7 and90% for K=6; K=5 selects1.05 in78.125%; K=4 is mixed. Concentration is not inherently optimal. Policy interpretation uses greedy choice results, not exploratory training counts or forced actions. Entropy and feasible-count summaries remain in the saved artifacts.

## 23. Action-Dominance Diagnostic

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

Sources: [action_dominance_decision.json](staged_training_002/action_dominance_diagnostic/action_dominance_decision.json) and [highest_feasible_comparison.csv](staged_training_002/action_dominance_diagnostic/highest_feasible_comparison.csv).

## 24. Baseline Comparison

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.26785448056 | 20.220284866955804 | 20.2509934868918 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.00619162552 | 20.724974031154186 | 20.764855473022735 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.04278836108 | 18.143989132574806 | 18.143989132574806 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441113054 | 19.515901257012747 | 19.538425351697505 | 91 | 0 |

Literal [baseline_comparison.csv](staged_training_002/action_dominance_diagnostic/baseline_comparison.csv). Highest-feasible minus DQN: 2794 − 2786 = **8 assignments**; 58017.00619162552 − 56419.26785448056 = **1597.73833714496 USD**, displayed as **$1,597.74**. This finding applies to this fixture only.

## 25. What the Results Currently Show

The implemented formulas, support construction, masks, replay/cadence, exact stage continuation, finite diagnostics and fixed-fixture results are verified in saved artifacts. The four baseline runs reproduce identical fixture inputs and preserve checkpoint/learner fingerprints. Immediate monotonicity and high dominance risk are established within this model.

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

Highest-feasible outperformed Episode25 on the fixed fixture. DQN incremental dynamic value remains unresolved; further runs are paused for academic review.

## 26. What the Results Do NOT Establish

Causal willingness-to-pay elasticity, converged/optimal pricing, DQN superiority, universal highest-feasible long-term dominance, policy stability and final hierarchical evaluation are not established. A fixed development fixture cannot substitute for held-out evaluation.

Also NOT ESTABLISHED: protected-period generalization, optimality of action endpoints, necessity of an additional epsilon floor, or a need for d_min.

## 27. Current Open Research Question

Does request-level DQN add nontrivial dynamic value beyond the highest-feasible baseline under this reward/environment? **UNRESOLVED**. No new run is authorized.

## 28. Items for Academic Review

1. Is positive absolute sensitivity with empirical truncation/resampling acceptable?
2. Is the selected positive P0.5–P99.5 support methodology acceptable?
3. Is P_accept_c = max(platform minimum, P_raw_c) acceptable?
4. Is the 0.85–1.15 factor set sufficiently justified?
5. Is gamma = 0.99 per request the appropriate Bellman interpretation?
6. Given high action-dominance pressure, should training continue, reward/environment be reconsidered, or highest-feasible become a formal benchmark?
7. What evidence is required before claiming DQN adds dynamic value?

## 29. Protected Final Evaluation

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`. March17–31 remains untouched. This task reads saved summaries only; no simulation, training, checkpoint load or new analysis. March16 remains development-only.

## 30. Superseded / Historical Formulations

| Date/Stage | Formulation/result | Why superseded | Current replacement |
| --- | --- | --- | --- |
| Record-029 historical | Signed historical support | Preserved historical purpose; not V1 positive calibration | Separate positive V1 support |
| Provisional V1 | Signed support before abs | Wrong operation order | Abs before positive quantiles |
| Earlier historical guide | Equation without P_base multiplier | SUPERSEDED_HISTORICAL_FORMULATION | Scaled consolidated equation |
| Raw-threshold diagnostic | 61.746289% no-offer | Raw-only threshold superseded | Platform-min protected P_accept_c |
| Pre-reformulation Episode25 | Old pricing learner | Different acceptance/replay contract | Fresh staged_training_002 |
| staged_training_001 | Time-aware discount | Near-undiscounted horizon accumulation | Request-step gamma0.99 |


## 31. Authoritative Evidence Map

### Authoritative Result Sources

| Topic | Source of truth | Notes |
| --- | --- | --- |
| Sensitivity calibration | [sensitivity_distribution_summary.csv](review_feedback_reconciliation/sensitivity_distribution_summary.csv) | Numerical/decision provenance |
| Exact positive support | [restricted_calibration_support.json](restricted_calibration_support.json) | Numerical/decision provenance |
| Bellman correction | [discount_methodology_decision.json](bellman_discount_correction/discount_methodology_decision.json) | Numerical/decision provenance |
| Episode1/10/25 | [stage_summary.csv](staged_training_002/stage_summary.csv) | Numerical/decision provenance |
| March16 fixed development | [development_evaluation.csv](staged_training_002/development_evaluation.csv) | Numerical/decision provenance |
| MC calibration | [mc_return_calibration.csv](staged_training_002/mc_return_calibration.csv) | Numerical/decision provenance |
| Action dominance | [README.md](staged_training_002/action_dominance_diagnostic/README.md) | Numerical/decision provenance |
| Historical Record029 | [README.md](../2026-10-09_price_distance_sensitivity_record029_full_jan_mar/README.md) | Numerical/decision provenance |
| Stage2 continuation | [continuation_state_verification.json](staged_training_002/continuation_state_verification.json) | Numerical/decision provenance |
| Stage3 continuation | [stage3_continuation_state_verification.json](staged_training_002/stage3_continuation_state_verification.json) | Numerical/decision provenance |
| Checkpoint completion | [stage_ep25_complete.json](staged_training_002/stage_ep25_complete.json) | Numerical/decision provenance |


| Action frequency | [action_frequency_by_feasible_count.csv](staged_training_002/action_frequency_by_feasible_count.csv) | Greedy/development versus training distinguished |
| Active implementation | [METHODOLOGY.md](METHODOLOGY.md) | Specification; canonical narrative here |
| Protection / current status | [stage_ep25_complete.json](staged_training_002/stage_ep25_complete.json) | Saved completion/protection record, no new evaluation |

## 32. Artifact Index

Read this canonical narrative first, then [active implementation specification](METHODOLOGY.md), [short meeting summary](ACADEMIC_REVIEW_SUMMARY.md), and the narrow artifact reports linked in §31.

[Documentation consistency check](documentation_consistency_check.json) records literal source-to-document numerical comparisons. Numerical evidence remains unchanged.

### Professor-review request-level March16 acceptance export

The Episode25 fixed-development request export reconciles with the authoritative aggregate and persisted action order. See the [detailed request CSV](staged_training_002/professor_review/episode25_march16_request_level_acceptance.csv), [summary CSV](staged_training_002/professor_review/episode25_march16_request_level_acceptance_summary.csv), and [data dictionary](staged_training_002/professor_review/episode25_march16_request_level_acceptance_DATA_DICTIONARY.md).

## Original Formulation Coverage Checklist

| Original requirement | Status |
| --- | --- |
| 1. Define P_base | RESOLVED |
| 2. Define L_gg′ | RESOLVED |
| 3. Define L_base | RESOLVED |
| 4. Epsilon sign/magnitude | RESOLVED |
| 5. Epsilon calibration | RESOLVED |
| 6. Passenger preference | RESOLVED |
| 7. Effective threshold | RESOLVED |
| 8. NYC/platform limits | RESOLVED |
| 9. alpha_min / alpha_max | RESOLVED |
| 10. DQN factors | RESOLVED |
| 11. Final offer | RESOLVED |
| 12. Acceptance | RESOLVED |
| 13. Exceeded threshold | SUPERSEDED |
| 14. d_min | NOT_USED |
| 15. Sensitivity distribution | RESOLVED |
| 16. Negative/unusual P_raw_c | RESOLVED |
| 17. Four diagnostic groups | RESOLVED |
| 18. Arm coverage | RESOLVED |
| 19. Outcome categories | RESOLVED |
| 20. Request OD/distance logging | RESOLVED |
| 21. End-to-end workflow | RESOLVED |
| 22. Pre-coding unresolved decisions | UNRESOLVED |

```text
PASSENGER_SENSITIVE_PRICING_V1_IMPLEMENTED = YES
ACADEMIC_REVIEW_FEEDBACK_RECONCILED = YES
POSITIVE_EPSILON_SUPPORT_FROZEN = YES
TRUNCATED_EMPIRICAL_RESAMPLING_FROZEN = YES
EFFECTIVE_PASSENGER_THRESHOLD_FROZEN = YES
REQUEST_LEVEL_ARCHITECTURE_FROZEN = YES
STATE_13D_UNCHANGED = YES
REQUEST_STEP_GAMMA_099_FROZEN = YES
STAGED_TRAINING_THROUGH_EP25_COMPLETE = YES
TECHNICAL_INVARIANTS_PASS = YES
NUMERICALLY_STABLE = YES
LEARNING_SIGNAL = YES
Q_SCALE_TREND = APPROACHING_RETURN_SCALE
POLICY_STABLE = NO
CONVERGED = NO
ACTION_DOMINANCE_RISK = HIGH
DQN_ADDS_NONTRIVIAL_DYNAMIC_VALUE = UNRESOLVED
LONGER_TRAINING_AUTHORIZED = NO
AWAITING_ACADEMIC_REVIEW = YES
PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES
```
