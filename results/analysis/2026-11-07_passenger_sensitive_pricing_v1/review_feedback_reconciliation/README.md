# Academic-Review Feedback Reconciliation — COMPLETE

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

## Original feedback and resolution

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

## Final sensitivity and truncation

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

| distribution | N | mean | SD | median |
| --- | --- | --- | --- | --- |
| SIGNED_HISTORICAL_SENSITIVITY | 8685488 | 0.640621 | 7.106335 | 0.762120 |
| POSITIVE_V1_BEHAVIOURAL_PROXY_BEFORE_SUPPORT | 8685488 | 1.414638 | 6.993510 | 0.820126 |
| POSITIVE_V1_SUPPORTED_T0 | 8598805 | 1.095299 | 1.817300 | 0.820123 |

T0 is symmetric in nominal tail probability, **not** numerical epsilon magnitude. Asymmetric alternatives were considered: T1=P0.5–P99, T2=P1–P99.5, T3=P1–P99. T0–T3 did not establish a superior alternative; T0 remains frozen. Duplicate empirical values make exact retained/tail percentages differ slightly from nominal percentages. The bounds regularize reciprocal sensitivity while preserving the central empirical distribution; excluded observations are not relabelled invalid.

`epsilon_min` is the support lower bound itself. **No additional floor** is active; P0.5/P1/P2.5/P5 post-support floor candidates are historical diagnostics. **TRUNCATED_EMPIRICAL_RESAMPLING** samples supported rows with replacement, preserving empirical duplicate frequencies and shape/skew/tails within support, using a caller-controlled deterministic seed. The global positive pool is used; no parametric family, Gaussian fit, or unsupported time-group model is imposed.

| candidate | lower | upper | retained_N | retained_pct | epsilon_mean | epsilon_SD | epsilon_median | no_offer_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T0 | 0.017810 | 27.324600 | 8598805 | 99.001979 | 1.095299 | 1.817300 | 0.820123 | 0.000000 |
| T1 | 0.017810 | 14.266572 | 8555302 | 98.501109 | 1.001997 | 1.236451 | 0.818044 | 0.000000 |
| T2 | 0.032143 | 27.324600 | 8555281 | 98.500867 | 1.100746 | 1.820307 | 0.822114 | 0.000000 |
| T3 | 0.032143 | 14.266572 | 8511778 | 97.999997 | 1.006995 | 1.237626 | 0.820126 | 0.000000 |

## Final equation and threshold

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

The former condition `P_offer <= P_raw_c` produced **61.746289%** no-feasible/no-offer outcomes: **SUPERSEDED_RAW_THRESHOLD_DIAGNOSTIC**. Under `P_offer <= max(0.85*P_base,P_raw_c)`, valid-request no-feasible rate is **0%**, by construction because the minimum arm remains feasible. This is not evidence of improved real-world demand. No post-selection clipping is performed. `d_min = NOT_USED`; no deterministic minimum-distance fare rule is active.

## Dataset justification

Actions remain **[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]**. Dataset justification is **MODERATE**. Coverage of observed fare/P_base in 0.85–1.15 is **14.379973%**, measured on all 8,692,819 cleaned **Jan1–Mar15** fares in the saved factor study—not March16 development requests and not only supported epsilon rows. This period distinction avoids mislabelling “development-fare coverage.” Distance-band evidence uses km after converting historical miles. Exact endpoints and 5% spacing are project design choices; neither empirical optimization nor a full-market fare envelope is claimed.

## Current request-level contract

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

## Reconciliation validation and subsequent work

Saved review_feedback_validation.json reports PASS and57 focused tests, with a400-request bounded fixture,390 assignments, zero no-offers/optimizer updates, and fleet5000 conserved. Its “long training not started” and fresh-untrained flags describe the reconciliation date, not the present: subsequent corrected staged training completed Episode25. The later Bellman correction supersedes the time-aware contract used in older fixture tables; historical CSVs remain unchanged.

[V1 hub](../README.md) · [Methodology](../METHODOLOGY.md) · [Academic review summary](../ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](README.md) · [Bellman correction](../bellman_discount_correction/README.md) · [Authoritative staged training](../staged_training_002/README.md) · [Action dominance](../staged_training_002/action_dominance_diagnostic/README.md)

## Retained artifacts

Sensitivity distribution/truncation CSVs; excluded_tail_summary.csv; raw_vs_effective_preference_summary.csv; feasible_arm_before_after.csv; pricing_factor_dataset_justification.csv; distance/time-group coverage; request/transition/slot validation CSVs; signed and positive distribution PNGs; analysis_summary.json, fixture_validation.json, review_feedback_validation.json and focused_tests.log retain numerical provenance. No historical artifacts were rewritten.
