# Academic Review Validation Package

## Passenger-Sensitive Pricing V1 — Post-Review Implementation and Results

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

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

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

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

Actions remain **[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]**. Dataset justification is **MODERATE**. Coverage of observed fare/P_base in 0.85–1.15 is **14.379973%**, measured on all 8,692,819 cleaned **Jan1–Mar15** fares in the saved factor study—not March16 development requests and not only supported epsilon rows. This period distinction avoids mislabelling “development-fare coverage.” Distance-band evidence uses km after converting historical miles. Exact endpoints and 5% spacing are project design choices; neither empirical optimization nor a full-market fare envelope is claimed.

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

### Staged training results

| episode | requests | assignments | assignment_rate | revenue | forced_rate | choice_rate | replay_size | optimizer_updates | exploration_epsilon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 37111 | 33528 | 0.903452 | 642375.127717 | 0.658403 | 0.341597 | 37111 | 128 | 0.997568 |
| 10 | 39488 | 31657 | 0.801687 | 606587.710093 | 0.677320 | 0.322680 | 100000 | 1280 | 0.975680 |
| 25 | 51654 | 22536 | 0.436288 | 435187.848519 | 0.713536 | 0.286464 | 100000 | 3200 | 0.939200 |

| episode | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4.127954 | 39.370998 | 20.916428 | 24.332136 | 1723.784417 | 1797.625861 | 1725.698279 |
| 10 | 55.037945 | 130.933395 | 11.201169 | 8.368096 | 1528.837823 | 1561.104082 | 1479.369087 |
| 25 | 138.293045 | 196.008087 | 12.567836 | 13.262941 | 838.012691 | 841.808621 | 722.323343 |

### Fixed March16 results

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982 | 54330.574517 | 19.616313 | 0.450669 | 0.549331 | 3.107260 | 33.486538 |
| 10 | 2838 | 2792 | 0.983791 | 56855.790887 | 20.328218 | 0.450669 | 0.549331 | 58.999302 | 104.065437 |
| 25 | 2838 | 2786 | 0.981677 | 56419.267854 | 20.220285 | 0.450669 | 0.549331 | 147.337677 | 199.559387 |

The fixed March16 fixture has2,838 requests, environment/sensitivity seed424242, 00:00–02:00, greedy actions and unchanged learner fingerprints. Episode10→25 revenue fell **$56,855.79→$56,419.27** (approximately−0.77%); assignments2792→2786 and assignment rate decreased approximately0.21 percentage points. Episode25 is not an improvement over Episode10. Training episodes have different source dates/conditions: their assignment rates are not a controlled comparison.

No development replay writes, optimizer/target mutation, epsilon decay or training-RNG mutation occurred. This is a reused development fixture, not final held-out evaluation. March17–31 remains untouched.

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

### Action dominance and baseline comparison

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.267854 | 20.220285 | 20.250993 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.006192 | 20.724974 | 20.764855 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.042788 | 18.143989 | 18.143989 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441 | 19.515901 | 19.538425 | 91 | 0 |

### Review interpretation and unresolved question

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

1. Is positive absolute sensitivity with empirical truncation/resampling an acceptable behavioural proxy, given the absence of observed rejected-offer response labels?
2. Is `max(platform minimum, P_raw_c)` an acceptable effective passenger acceptance threshold, including its guaranteed minimum feasible arm?
3. Is the fixed0.85–1.15 factor set acceptable with moderate dataset justification and limited fare coverage?
4. Is gamma0.99 per request the preferred interpretation after moving the decision boundary to individual requests, given its request-intensity-dependent elapsed horizon?
5. With highest-feasible outperforming Episode25 DQN on March16, should longer training proceed first, should reward/environment structure be reconsidered, or should highest-feasible become a formal benchmark?
6. What evidence—across controlled fixtures, uncertainty and operational tradeoffs—should be required before claiming nontrivial DQN dynamic value?

These are questions for academic review, not decisions or authorization for another run.

[V1 hub](../2026-11-07_passenger_sensitive_pricing_v1/README.md) · [Methodology](../2026-11-07_passenger_sensitive_pricing_v1/METHODOLOGY.md) · [Academic review summary](../2026-11-07_passenger_sensitive_pricing_v1/ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/README.md) · [Bellman correction](../2026-11-07_passenger_sensitive_pricing_v1/bellman_discount_correction/README.md) · [Authoritative staged training](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/README.md) · [Action dominance](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/action_dominance_diagnostic/README.md)

<details>
<summary>Historical review record — superseded pricing results and provisional decisions</summary>

The following dated content is preserved verbatim as provenance. Statements that V1 was blocked, uncalibrated, untrained, detached/running, time-aware, or awaiting earlier decisions are SUPERSEDED by the current section. Historical pre-reformulation Episode25 is not corrected V1 Episode25. Other subsystem results are not re-audited here.


## 1. Scope

This package validates the current implementation against the newly available consolidated DQN pricing roadmap. It contains one exact reconstruction of a historical training slot, historical descriptive statistics, and existing DQN/CNN/DP evidence. No methodology, frozen model, driver profile, production source, training protocol or checkpoint was changed. No optimizer update, retraining, hyperparameter search or long training resume occurred. The single reconstructed slot inserted transitions only into a disposable in-memory replay buffer; nothing was saved back to the learner namespace.

The complete cleaned Jan–Mar historical population is permitted for descriptive analysis. The already-defined CNN test predictions are also permitted. March17–31 remains untouched by hierarchical RL training, routing training, policy selection, integrated simulation or final service/revenue evaluation. Those boundaries differ from historical data analysis and CNN-only evaluation.

## 2. Current Architecture

True 3 km grid (142 valid cells, 16×16 raster) → saved CNN forecasts → public 13D pricing state → 13→64→64→7 DQN → seven factors 0.85/0.90/0.95/1.00/1.05/1.10/1.15 → contextual empirical passenger P_max → inclusive passenger acceptance → independent driver-price, local supply and EV feasibility → deterministic FCFS assignment → movement, timed charging and operational updates.

The frozen temporal-FedAvg 169→64→32→9 routing network supplies probabilities to the pricing state. Physical reposition/charging actions still use the existing operational utility decisions. Pricing selects one action per observed OD pair per half-hour and reuses it for requests with that OD. Reward is the sum of gross successfully assigned fares at assignment time; rejected and accepted-unmatched requests contribute zero. This is DQN, not a bandit or actor–critic learner.

## 3. Distance-Unit Validation

**NO_ISSUE_UNIT_INVARIANT.** All new review distances use km; TLC source miles appear only as explicit raw provenance. The historical global L_base is **4.856998243316242 km**; the 3 km grid cell side is a separate geometric quantity.

A deterministic first-10,000-row historical sample contains 9,992 VALID epsilon rows. Converting both trip and reference distances to km gives relative-deviation maximum/mean absolute differences 1.77636e-15/6.21e-17, with zero discrepancies above 1e-12. Epsilon differences peak at 4.14957e-12; three exceed an absolute-only 1e-12 test because of denominator amplification, but **zero fail combined relative/absolute 1e-12 tolerance**. Native-unit epsilon exactly reproduces the stored sample.

For all 2,996 selected runtime requests, independent km-based P_max differs from recorded P_max by at most 1.13687e-13 USD (mean 1.17515e-15); zero tolerance failures or decision changes. Grid geometry is EPSG:32118, native metres, verified 3.0×3.0 km; cardinal/diagonal/STAY movement is 3.0/4.242640687119286/0 km. No numerical unit correction or unit-driven retraining is indicated. See `distance_unit_validation.json`.

## 4. Historical vs Runtime Pricing References

| concept | historical_Record029 | runtime | same_or_different | why | methodological_impact |
| --- | --- | --- | --- | --- | --- |
| P_base | One global 21.34586956773507 USD | Resolved contextual mean fare; selected slot 20.321533859249936 USD | DIFFERENT | Exact WeatherCode × half-hour context, then period/weather/global fallback | A historical global base must not replace the runtime base |
| L_base_km | Price-conditioned global 4.856998243316242 km (479,000 reference trips) | Resolved contextual mean trip distance; selected slot 5.289170703620971 km | DIFFERENT | Runtime reference is the context mean, not the historical ±$1 subset | Reference-distance changes alter P_max even though unit conversion does not |
| epsilon definition | Signed relative_price_deviation / relative_distance_deviation | Positive abs(relative_distance_deviation / relative_price_deviation) | DIFFERENT | Reciprocal orientation plus absolute value and different reference population | Historical signed epsilon cannot be inserted directly into runtime P_max |
| epsilon sampling | Historical empirical distribution; archived support decisions | Uniform empirical row resampling with replacement within resolved pool | DIFFERENT | Duplicate-value frequencies preserved; caller-owned NumPy RNG | No Gaussian approximation, artificial floor or historical support substitution |
| P_max equation | Rearranging historical signed definition gives P_base*(1+epsilon_historical*r_distance) | P_base*(1+r_distance/epsilon_runtime), exactly the roadmap equation | DIFFERENT_EPSILON_CONVENTION | Historical epsilon and runtime epsilon have different definitions | FORMULA_ALGEBRA_EQUIVALENT refers to runtime versus roadmap, not interchangeable historical epsilon |
| Units | TLC miles in source; all reported distances converted to km | Trip and contextual reference both miles internally; km reporting | UNIT_INVARIANT | Same conversion in numerator/reference cancels | No numerical unit correction or retraining indicated |
| Denominator treatment | Strict distance gap <0.00804672 km unresolved; rows retained | Runtime positive empirical epsilon, no positive-epsilon floor or clipping | DIFFERENT | Historical resolution rule does not redefine current behavioural sampler | No silent transfer of historical filtering/support into runtime |

**FORMULA_ALGEBRA_EQUIVALENT = YES** means runtime versus the roadmap equation with the runtime epsilon convention. **REFERENCE_CONVENTION_IDENTICAL = NO**. These are separate statements. The reciprocal signed historical epsilon is not interchangeable with the positive runtime epsilon. Full derivation and source hierarchy are in [methodology_reconciliation.md](methodology_reconciliation.md).

## 5. Request-Level Pricing Fixture

**Episode25, slot9 (one-based), 2026-03-12 15:30:00–16:00**, source March12 within the training period. Reconstruction began at the committed slot8 checkpoint `models/pricing_dqn/final_nonprivate_multiepisode_seed42/episode_0025/checkpoint_0008_98717f4d`. Environment seed **3405943863**, learner seed **42**, saved optimizer updates **3128**, epsilon-greedy exploration **0.940568**. The exploration probability is distinct from the per-request behavioural epsilon.

All checkpoint payload hashes passed before and after. Simulator, learner and request/customer/Python/NumPy RNG states were restored. All comparable saved slot fields matched exactly, including requests, acceptance, assignments, fare reward, replay size, routing actions and charging decisions. No optimizer update was executed; online weights were checked unchanged. Post-slot optimizer fields are intentionally not reproduced. No later slot was replayed.

`request_level_pricing_full.csv` contains **2,996 actual generated requests**, with every required field and observational feasible-driver counts. `request_level_pricing_review_sample.csv` has **300** deterministic rows, stratified by actual outcome, factor and P_max/base relation before filling by evenly spaced rows. It is an inspection sample, not a population-weighted estimator. All seven factors and the existing accepted/rejected/accepted-unmatched categories are represented.

`L_GG_km` is the intact empirical requested trip distance, **not centroid displacement or grid-cell side**. `Timestamp` is the slot start; request IDs preserve the restored run identity. Runtime references in this slot are P_base=20.3215338592499 USD and L_base=5.28917070362097 km. Provenance and exact saved-report comparisons are in `request_fixture_provenance.json`.

## 6. Passenger Acceptance Validation

Active rule: **ACCEPT iff P_offer ≤ P_max**; equality accepts. Recorded outcomes are retained separately from independent recomputation using the km-converted distance terms. Decisions have no comparison tolerance. Approximate categories elsewhere use absolute 1e-9 USD only for descriptive reporting.

Requests **2,996**; accepted **719 (23.998665%)**; rejected **2277 (76.001335%)**. **Decision mismatches: 0. Exact equality cases: 0. Missing or nonfinite numeric fields: 0.** Equality behavior is verified from the inclusive code rule; this slot has no empirical equality case. Offered fares equal contextual base × selected factor. P_max has 165 negative values; the unchanged signed distance term permits them, and no clamp was introduced.

## 7. Offered Price vs P_max

| min_USD | P5_USD | median_USD | P95_USD | max_USD | mean_USD |
| --- | --- | --- | --- | --- | --- |
| -1260.06 | -26.808 | 5.79806 | 21.6088 | 1871.34 | 5.42691 |

P_offer below / approximately equal / above P_max: **719 / 0 / 2277**. The plot includes every request and an equality line. Symmetric-log axes preserve negative and extreme P_max values without clipping. A discount relative to base can still be rejected when the offered fare exceeds that passenger's threshold.

![Offered price versus threshold](offered_price_vs_pmax.png)

## 8. P_base vs P_max

| category | N | percentage | acceptance_percentage | mean_trip_distance_km | median_trip_distance_km |
| --- | --- | --- | --- | --- | --- |
| BELOW | 2365 | 78.9386 | 5.5814 | 2.30157 | 2.14043 |
| APPROX_EQUAL | 0 | 0 | — | — | — |
| ABOVE | 631 | 21.0614 | 93.0269 | 11.6097 | 8.72264 |

Pricing-factor counts by category:

| category | 0.85 | 0.9 | 0.95 | 1.0 | 1.05 | 1.1 | 1.15 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BELOW | 427 | 512 | 377 | 55 | 528 | 261 | 205 |
| APPROX_EQUAL | — | — | — | — | — | — | — |
| ABOVE | 156 | 117 | 67 | 63 | 67 | 59 | 102 |

With positive runtime epsilon, the sign of P_max−P_base equals the sign of trip distance−runtime L_base. Most trips in this selected slot are below the **contextual** reference distance; that is sufficient to explain P_max below base without invoking a unit bug. No historical global base was substituted.

![Contextual base versus threshold](pbase_vs_pmax.png)

## 9. Historical Distance vs Fare

All **10,620,409** cleaned Jan–Mar trips are used, retaining the existing 0<source distance≤100 raw miles validity decision (maximum equivalent 160.9344 km). TLC `fare_amount` is USD. Conversion to km precedes all bins and short-trip counts. Intervals are `(lower, upper]`; final bin is `>15 km`. No epsilon validity/support filter is applied to this descriptive source analysis.

| distance_bin_km | N | mean_trip_distance_km | median_trip_distance_km | mean_fare_USD | median_fare_USD | min_fare_USD | P10_fare_USD | P90_fare_USD | max_fare_USD | unique_fare_values |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0–1 | 901393 | 0.678405 | 0.772485 | 10.0844 | 6.5 | 0.01 | 4.4 | 18.19 | 1000.03 | 8056 |
| 1–2 | 2403813 | 1.51275 | 1.51278 | 10.1547 | 8.6 | 0.01 | 6.5 | 14.62 | 890 | 5959 |
| 2–3 | 1946097 | 2.47047 | 2.4462 | 13.9956 | 12.19 | 0.01 | 9.3 | 19.8 | 581 | 6486 |
| 3–3.17 | 247751 | 3.07654 | 3.05775 | 16.2668 | 14.2 | 0.01 | 11.4 | 22.6 | 199.9 | 4606 |
| 3.17–4 | 1026012 | 3.5467 | 3.54056 | 18.0035 | 16.3 | 0.01 | 12.8 | 25.19 | 250 | 6700 |
| 4–5 | 827565 | 4.46258 | 4.44179 | 21.0957 | 19.1 | 0.01 | 14.9 | 29.54 | 300 | 7091 |
| 5–7.5 | 1088715 | 6.09063 | 6.00285 | 25.5276 | 23.3 | 0.01 | 17.7 | 35.23 | 480.9 | 8072 |
| 7.5–10 | 569702 | 8.64558 | 8.5778 | 30.9289 | 28.5 | 0.01 | 22.6 | 41.89 | 496.5 | 7853 |
| 10–15 | 678050 | 12.3666 | 12.2793 | 37.2672 | 35.2 | 0.01 | 28.16 | 49.2 | 900 | 8403 |
| 15+ | 931311 | 23.8391 | 22.4343 | 59.404 | 56.5 | 0.01 | 38.74 | 75.98 | 2555.2 | 12132 |

Distance distribution (km):

| min | P1 | P5 | P25 | median | P75 | P95 | P99 | max | mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.0160934 | 0.241402 | 0.804672 | 1.73809 | 3.04166 | 6.16379 | 20.3099 | 31.4788 | 160.822 | 5.58293 |

Short-trip counts:

| maximum_trip_distance_km | N |
| --- | --- |
| 1 | 901393 |
| 2 | 3305206 |
| 3 | 5251303 |
| 3.17 | 5499054 |

The density display uses 100,000 deterministic evenly spaced source rows for readability; **all table statistics use the full population**. Earlier mile-based analyses were numerically valid, but do not by themselves answer the distinct 3–3.17 **km** question.

![Historical distance and fare](distance_vs_historical_fare_km.png)

## 10. Fare-Floor Investigation

The data do **not** support constant fares throughout distances below 3 km. Median fares increase from **$6.50** (0–1 km) to **$8.60** (1–2 km) and **$12.19** (2–3 km); corresponding means are $10.0844/$10.1547/$13.9956. The **3–3.17 km** bin contains **247,751 trips**, mean **$16.266758**, median **$14.20**, P10/P90 **$11.40/$22.60**, and **4,606 distinct fares**. The adjacent 3.17–4 km bin has median $16.30. These summaries show a rising distance/fare pattern, not evidence of a unique structural break exactly at 3 or 3.17 km.

Below 3 km there are **8,719 distinct fares** and a broad distribution. Repeated exact fares occur across many short distances:

| fare_USD | N | percentage_short | unique_trip_distances | minimum_trip_distance_km | maximum_trip_distance_km |
| --- | --- | --- | --- | --- | --- |
| 8.6 | 368907 | 7.02506 | 185 | 0.0160934 | 2.99338 |
| 7.9 | 367309 | 6.99463 | 169 | 0.0160934 | 2.89682 |
| 9.3 | 361882 | 6.89128 | 186 | 0.0160934 | 2.99338 |
| 7.2 | 350446 | 6.67351 | 161 | 0.0160934 | 2.99338 |
| 10 | 347816 | 6.62342 | 186 | 0.0160934 | 2.99338 |

Repeated fares are consistent with discrete metering, rounding or heterogeneous fare schedules; they do not establish a single minimum-fare rule. Retained minimum fares of $0.01 and wide maxima also rule out asserting a universal positive floor from these summaries. No tariff/legal claim, source removal or pricing-rule change is made. A formal structural-break or tariff-origin study would be separate work.

## 11. Driver Price Preference

**ACTUAL_IMPLEMENTATION:** `src/dispatch/dispatch.py::find_eligible_vehicle` requires **P_offer ≥ driver.price_preference**, equality eligible, after local availability/energy/reserve checks. `src/routing/production.py::generate_driver_profiles` creates one persistent preference per driver from **Uniform(max(0, μ−σ), μ+σ)** using seed42, not 0.85×contextual P_base. Metadata records μ=$20.233906794701575, population σ=$16.299856940413804, bounds **$3.934049854287771–$36.53376373511538**, from 2,898,376 valid pre-cutoff fares. All **5,000** profiles persist unchanged.

| min_USD | P1_USD | P5_USD | median_USD | mean_USD | P95_USD | P99_USD | max_USD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3.95096 | 4.31882 | 5.59532 | 19.9726 | 20.0909 | 34.8666 | 36.2485 | 36.5261 |

For this slot there is one actual contextual P_base, **$20.3215338592499**. Each of the 5,000 preferences is normalized once against that base, not the historical global base. Ratio median/mean/min/max are **0.982827/0.988649/0.194422/1.797409**. Counts below 0.85×base / approximately equal / between 0.85×base and base / at-or-above base are **2065 / 0 / 493 / 2442**. Complete quantiles and ratio values are in `driver_preference_summary.csv`.

**OPEN_RESEARCH_DECISION:** whether the intended driver lower bound should be 0.85×P_base, P_base, or the present empirical-calibrated uniform support, and whether an upper bound is intended. The observed 2,065 preferences below 0.85×this context base demonstrate that 0.85 is **not an implemented driver floor**. The minimum DQN action factor is a separate concept. No preference changed.

## 12. Passenger / Driver / Supply Outcomes

| outcome | N | percentage_total | percentage_accepted |
| --- | --- | --- | --- |
| PASSENGER_REJECTED | 2277 | 76.0013 | — |
| PASSENGER_ACCEPTED_ASSIGNED | 572 | 19.0921 | 79.5549 |
| PASSENGER_ACCEPTED_NO_PRICE_ELIGIBLE_DRIVER | 147 | 4.90654 | 20.4451 |
| PASSENGER_ACCEPTED_OTHER_UNMATCHED | 0 | 0 | 0 |

All categories sum to the complete request count. Accepted requests sum to assigned plus both unmatched categories. Observational driver eligibility is checked at each request's real decision time against IDLE origin/direct-neighbour supply, charging trigger, passenger energy and destination-station reserve, then its price gate. Rejected requests are inspected counterfactually without dispatching them. No additional RNG draw or fleet mutation is introduced by this observation.

For accepted-unmatched requests, NO_PRICE_ELIGIBLE requires at least one non-price-feasible candidate but zero passing price candidates; zero non-price-feasible candidates instead belongs to OTHER_UNMATCHED. This slot has no latter cases. The original slot report independently records 147 price-related unmatched requests. Candidate price rejections total 70,250 across 704 requests; these are neither unique passenger rejections nor unsuccessful assignments. Availability and passenger willingness to pay are distinct constraints.

## 13. DQN Learning Through Episode25

Only complete authoritative episodes1–25 are included; partial episode26 and the accelerated diagnostic are excluded. Protocol remains **500 episodes ×16 slots**, eight updates per warm slot, 13→64→64→7, Adam0.001, batch64, replay100,000, warmup1,000, gamma0.99, tau0.005, seed42. No new updates occurred.

Totals: **1,118,214 requests, 303,794 accepted, 814,420 rejected, 247,251 assigned**, revenue/reward **$4,791,417.80**. Different training windows/fleet trajectories prevent interpreting raw episode changes as a controlled causal policy improvement.

The complete per-episode table is `dqn_episode_summary.csv`: request/assignment/acceptance denominators are explicit; seven pricing-factor counts and percentages are **OD-context selections**, not request counts. Episode-level mean/median offered prices are **NOT PERSISTED**. The requested offered-price figure explicitly displays this gap; revenue/assignments is not substituted.

Saved monitoring points:

| episode | optimizer_updates | epsilon | mean_loss | mean_abs_Q | q_max | terminal_selected_Q_mean | terminal_mean_reward | bootstrap_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 1272 | 0.975832 | 29.0768 | 141.654 | 586.098 | 147.015 | 26.5002 | 0.806625 |
| 25 | 3192 | 0.939352 | 41.9088 | 328.287 | 1122.2 | 338.099 | 26.0306 | 0.893636 |

Q probes use saved monitoring conventions; episode Q summaries use their separately documented last512 replay states and are not identical probe populations. Loss is checkpoint/episode-mean loss at the cumulative update count, not an invented per-update trace. Elevated terminal Q relative to terminal reward remains a calibration concern. Episode10/25 fixed-development revenue previously fell from $23,981.01 to $20,595.95; this is saved supporting evidence only, not a new development run.

**25_EPISODES = EARLY_TREND_ONLY. PRICING_POLICY_CONVERGED = NO.**

![Episode reward](dqn_reward_by_episode.png)
![Acceptance and rejection](acceptance_rejection_by_episode.png)
![Offered-price availability](average_offered_price_by_episode.png)
![Pricing action frequency](pricing_action_frequency_by_episode.png)
![Saved loss checkpoints](q_loss_by_update.png)

## 14. CNN Demand Validation

The **existing saved final continued CNN** (selected epoch200) is evaluated from saved predictions only: **2026-03-16 00:00:00 through 2026-03-31 23:30:00**, 768 half-hours ×142 valid grids = **109,056 observations**. No new inference, training, fitting or model selection. This is the already-defined CNN evaluation; it does not consume the protected hierarchical evaluation.

| N | mean_actual | mean_predicted | MAE | MSE | RMSE | R2 | NRMSE_percentage | volume_error_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 109056 | 18.1575 | 17.0163 | 5.24274 | 334.627 | 18.2928 | 0.961007 | 100.745 | 6.2852 |

NRMSE=RMSE/mean(actual demand)×100 uses the **same grid-slot observations**. Actual/predicted totals are **1,980,184/1,855,725.399678**; volume error is computed separately from aggregate totals. NRMSE **100.745164%** is much larger than volume error **6.285204%**: positive/negative local errors can cancel in totals, so aggregate accuracy must not be presented as low per-cell RMSE. No universal 10–15% acceptance threshold is imposed. The saved historical-average benchmark remains better on MAE/RMSE/R².

Errors are actual−predicted (positive means underprediction):

| min | P1 | P5 | median | mean | P95 | P99 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -270.32 | -30.5798 | -8.05306 | 0 | 1.14124 | 13.2144 | 46.76 | 991.598 |

Positive / negative / approximately zero shares: **34.223702% / 35.843053% / 29.933245%**, absolute zero tolerance1e-12. All error values remain in the histogram; logarithmic count axis only.

![CNN actual versus predicted](cnn_actual_vs_predicted.png)
![CNN prediction errors](cnn_prediction_error_distribution.png)

## 15. Differential Privacy Comparison

**CURRENT_DP_DIAGNOSTIC** reuses existing results only. This is conditional central driver-level Gaussian DP at a trusted aggregator, fixed public participation, replacement of one driver's entire history, clipping C=1, delta=1e-5,576 rounds and no subsampling amplification. It is not local DP, membership privacy or secure aggregation. Only the noisy model transcript is covered; these internal unnoised validation statistics are not a DP release.

| model | accuracy | CE | Brier | ECE | non_STAY_accuracy | non_STAY_CE | invalid_action_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NON_PRIVATE | 0.949363 | 0.291658 | 0.093054 | 0.015838 | 0.00619544 | 5.14056 | 0 |
| DP_EPS8 | 0.900448 | 0.830102 | 0.184402 | 0.0498286 | 0.0056948 | 10.3952 | 0 |
| DP_EPS4 | 0.875446 | 2.04232 | 0.248193 | 0.119384 | 0.051128 | 29.4164 | 0 |
| DP_EPS2 | 0.723496 | 19.5224 | 0.550814 | 0.274712 | 0.0529428 | 211.53 | 0 |

The saved ε≈8/4/2 variants all degrade probability quality relative to the non-private model; they are not endorsed final settings. Their joint-release accounting is ε=9.53367213, delta=1e-5. No DP training or service evaluation was rerun here.

**PAPER_SPECIFIC_DP_REGIMES_COMPLETE = NO. PAPER_ALPHA_VALUES = NOT YET IDENTIFIED.** The consolidated roadmap explicitly omits alpha's mathematical meaning and numeric settings. The five existing PDFs in `notebooks/plan/papers/` were narrowly searched for differential-privacy definitions; none identifies the requested LOW/HIGH regimes. Search evidence is in `paper_definition_search.json`. The accountant's Rényi order alpha is not assumed to be the requested paper's alpha. Supplying the exact paper/section is a review gap, not proof of an implementation failure.

## 16. Items Fully Answered

Request-level DQN action-to-price mapping, inclusive passenger rule, exact training-slot provenance, km-equivalent P_max, below-base threshold explanation, separate driver/supply outcomes, actual driver preference distribution, full-population km fare/distance bins, repeated fare behavior, 25-episode saved metrics/action frequencies/loss, correctly normalized saved CNN metrics, and scoped existing DP comparison are documented. Historical/runtime reference differences are explicit. Ten requested figure files are present; the unpersisted offered-price series is honestly marked unavailable.

## 17. Items Still Pending

Episode mean/median offered-price histories were not persisted and cannot be reconstructed from existing aggregate revenue. Longer-run convergence, repeated-seed robustness, final policy selection and protected hierarchical evaluation remain outside this task. The referenced paper's LOW/HIGH regimes and alpha definition/values are unavailable. A minimum-fare tariff or exact structural-break claim is not established by descriptive bins. No guessed values or unsupported completion claims fill these gaps.

## 18. Questions Requiring Research Confirmation

1. Should the current contextual references remain, or is a flat global reference intended? Current behavior was validated, not changed.
2. Is below-base and potentially negative P_max acceptable under the signed distance term? No clamp is currently applied.
3. Is a driver lower bound of 0.85×base, base, or the current uniform support intended, and is an upper bound required?
4. What convergence and reward-quality criteria should govern the unchanged 500-episode protocol? This review does not authorize continuation or redesign.
5. Which exact paper, LOW/HIGH regimes and alpha definitions/values should be used for the paper-specific privacy comparison?
6. If a fare floor is a research assumption, which tariff/source definition establishes it? The historical tables alone do not.

Implementation work after decisions may include agreed instrumentation, protocol changes or paper-specific settings under a separate task. No research parameter is selected here.

## 19. Artifact Index

| artifact | purpose |
| --- | --- |
| request_level_pricing_full.csv | All2,996 reconstructed requests; original and recomputed outcomes |
| request_level_pricing_review_sample.csv | 300 deterministic inspection rows |
| request_validation_summary.json | Acceptance, unit equivalence and price-category checks |
| request_fixture_provenance.json | Checkpoint/seed/RNG restoration and original report equality |
| historical_distance_fare_bins_km.csv | Full10,620,409-row distance/fare aggregation |
| distance_fare_summary.json | Distance quantiles, short counts and repeated fares |
| driver_preference_summary.csv | 5,000 preferences; USD and contextual normalized quantiles |
| passenger_driver_conflicts.csv | Four exhaustive request outcome categories |
| dqn_episode_summary.csv | Authoritative complete episodes1–25; missing fields explicit |
| dqn_review_summary.json | Saved totals and episode10/25 monitoring evidence |
| cnn_validation_summary.csv | Same-observation metrics and full error summary |
| distance_unit_validation.json | Bounded historical numerical and actual grid checks |
| methodology_reconciliation.md | Historical/runtime convention table and derivation |
| source_index.csv | Exact targeted source paths and authority/status |
| paper_definition_search.json | Bounded existing-paper search and unresolved definitions |

The ten PNGs embedded above are presentation outputs only. `request_reconstruction.log`, `request_analysis.log` and `saved_analysis.log` record bounded execution. Source CSV/Parquet/model/JSON artifacts were opened read-only. No frozen model artifact is copied or replaced. `validation_checks.json` records the focused final checks. Reproduction scripts in this directory are analysis-only; rerunning the slot reconstruction is unnecessary once its valid output exists.

## 20. Current Review Status

- `REQUEST_LEVEL_PRICING_VALIDATED = YES`
- `PASSENGER_DECISION_MISMATCH_COUNT = 0`
- `DISTANCE_FARE_KM_ANALYSIS_COMPLETE = YES`
- `DRIVER_CONSTRAINT_DOCUMENTED = YES`
- `DQN_25_EPISODE_REVIEW_COMPLETE = YES`
- `PRICING_POLICY_CONVERGED = NO`
- `CNN_NORMALIZED_VALIDATION_COMPLETE = YES`
- `CURRENT_DP_DIAGNOSTIC_COMPLETE = YES`
- `PAPER_SPECIFIC_DP_REGIMES_COMPLETE = NO`
- `PAPER_ALPHA_VALUES = NOT YET IDENTIFIED`
- `PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`
- `CURRENT_ACADEMIC_REVIEW_PACKAGE_READY = YES`

**Focused validation: 36 checks passed, 0 failed.** All ten figures were visually reviewed.

Package readiness means that all calculable current-review evidence is assembled and provenance checked; it does **not** mean paper-specific privacy settings, missing historical logging, pricing convergence or research ambiguities are resolved.


## Passenger-Sensitive Pricing V1 — Post-Review Methodology Decisions

Dated 2026-11-07. **PRIOR IMPLEMENTATION VALIDATION** above remains valid for its original runtime; **NEW VERSION-1 METHODOLOGY** below is a specification blocked before implementation. The earlier request-level findings are not overwritten.

Passenger-Sensitive Pricing V1 is the active **implementation specification**, but implementation is **BLOCKED** at its mandatory action-granularity preflight. Existing runtime has not been converted. Global P_base_USD=21.34586956773507; global L_base_km=4.856998243316242; L_gg_prime=actual passenger OD distance in km. Positive behavioural epsilon requires a calibrated epsilon_min; no calibration has run. TLC completed trips do not identify passenger acceptance elasticity. Planned proxy, if real response labels are absent: abs(Record-029 epsilon), Jan1–Mar15 only; historical signed evidence remains unchanged.

Required V1 equation: `P_c = P_base + (P_base/epsilon_c)*((L_gg_prime-L_base)/L_base)`. Seven experimental factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15] are not empirical NYC fare extrema. Mask candidate fare<=P_c **before** selection, equality feasible; empty mask means **no offer**, not passenger rejection. No passenger lower-bound f(), contextual bases, post-selection clipping or d_min rule is authorized.

Current implementation chooses one action per OD/slot **before** each passenger's epsilon/P_c exists, then stores one aggregated OD transition requiring an action. Passenger-specific masking and no-action handling therefore require an explicit decision/replay-contract change. No code/provider/mask or fresh learner was implemented; tests and calibration did not proceed. Old episode25 is **PRE_REFORMULATION_PRICING_PROVENANCE**. Its checkpoints remain unchanged and were not loaded. A fresh DQN is required after the gates; long training has not started. March17–31 remains untouched by calibration, training, selection or hierarchical evaluation.

[Version-1 specification and blocker](../2026-11-07_passenger_sensitive_pricing_v1/README.md).


## Passenger-Sensitive Pricing V1 — Request-Level Architecture Decision

## Academic Review Feedback Incorporated

Dated2026-11-07. Prior findings above are historical/pre-reformulation evidence. Review feedback on (1) distribution, sampling and asymmetric truncation; (2) permitted absolute values; (3) minimum-protected threshold; and (4) dataset justification of seven factors is incorporated.

Academic-review reconciliation is complete under an explicit project implementation decision. Equation-number provenance remains unverified (`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED=NO`); `V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION=YES`. Historical formulation without the P_base adjustment multiplier is superseded, not rewritten.

V1 uses positive absolute Record-029 sensitivity as a behavioural calibration proxy, not causal acceptance elasticity. Restrict Jan1–Mar15 VALID finite/nonzero first, then abs(), then inclusive positive P0.5–P99.5: [0.017809913104763053, 27.324599740032788], N=8,598,805. Truncated empirical row resampling with replacement preserves duplicate mass, caller-controlled seed; global pool. T0 retained after four bounded asymmetric comparisons. epsilon_min is the support lower bound; no extra floor. Signed historical artifacts remain unchanged.

Raw preference is `P_base+(P_base/epsilon)*((L-L_base)/L_base)` with unchanged global references21.34586956773507 USD and4.856998243316242km. Effective threshold is `max(0.85*P_base,P_raw)`; all action masks use it. The seven factors0.85–1.15 remain; dataset justification is MODERATE for bounded reference-price exploration, weak for uniquely determining exact endpoints/spacing. Jan1–Mar15 fare coverage inside that interval is14.379973%; it is not a statutory NYC fare minimum or a full-market envelope.

The former61.746289% raw-rule no-offer rate is `SUPERSEDED_BY_EFFECTIVE_THRESHOLD_REFORMULATION`; revised valid calibration no-offer=0%. Historical raw diagnostics remain. No post-selection action clipping or d_min. Request-level13D state/replay, masked Bellman target, gamma=0.99 per request transition and8/warm-slot cadence retained. Bounded fixture400 requests, 390 assignments, 0 no-offers, zero optimizer updates; 57 focused tests passed. At reconciliation completion no training had started; the subsequently authorized staged run is tracked below; old checkpoints not resumed. March16 development-only; March17–31 untouched. [Reconciliation](../2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/README.md).

<!-- V1_STAGED_001_STATUS -->
## Passenger-Sensitive Pricing V1 Detached Stage1

Historical staged_training_001 execution decision (superseded time-aware discount): three separate detached stages. Stage1 initializes fresh and stops after Episode1 plus fixed March16 development evaluation. The prior attached partial attempt is preserved and not resumed. Each subsequent stage requires a later saved-artifact review. No automatic chaining, no Codex polling. Convergence=NO; March17–31 untouched. Current metrics are in the status file; see [staged report](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_001/README.md).


## Active V1 request-step discount correction

**ACTIVE: gamma=0.99 per actionable request transition**, including same-timestamp requests. Terminal target is reward only; elapsed time remains diagnostic metadata. Gamma value unchanged; application semantics changed. Next state remains the next chronological actionable request; all masks, 13D state, rewards, cadence (8/warm slot), and other frozen parameters remain unchanged.

The old 0.99^(delta_t_minutes/30) rule is SUPERSEDED: near-unity discounts accumulated episode revenue and high horizon aliasing. `staged_training_001 = SUPERSEDED_TIME_AWARE_DISCOUNT_DIAGNOSTIC`; its artifacts/checkpoint remain unchanged. Offline comparison supports the correction: mean/median MC 1725.825875/1799.281877 versus 315510.192211/322877.321850; horizon correlation is materially reduced, not eliminated. Residual terminal exposure is 1.236830%.

Fresh staged_training_002 Episode1 only is authorized after focused tests; no old checkpoint resume, no automatic Stage2. March1–15 training, March16 fixed development, March17–31 protected. Execution status is recorded in `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/training_status.json`; methodology evidence is in `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/bellman_discount_correction/README.md`.

## Corrected V1 Episode25 completed review

| episode | revenue | assignments | assignment_rate | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 54330.57451727768 | 2767 | 0.974982381959126 | 19.61631258848888 | 0.4506694855532064 | 0.5493305144467935 | 3.10725998878479 | 33.48653793334961 |
| 10 | 56855.79088714074 | 2792 | 0.9837914023960536 | 20.32821764648258 | 0.4506694855532064 | 0.5493305144467935 | 58.99930191040039 | 104.06543731689452 |
| 25 | 56419.26785448056 | 2786 | 0.981677237491191 | 20.220284866955804 | 0.4506694855532064 | 0.5493305144467935 | 147.33767700195312 | 199.55938720703125 |

```json
{
  "Q_SCALE_TREND": "UNCLEAR",
  "NUMERICALLY_STABLE": "YES",
  "POLICY_STABLE": "UNCLEAR",
  "LEARNING_SIGNAL": "UNCLEAR",
  "CONVERGED": "NO",
  "optimizer_updates": 3200,
  "exploration_epsilon": 0.9392,
  "protected_period_untouched": true,
  "policy_movement_available": false,
  "review_basis": "Descriptive Episode10\u219225 changes in Q/MC relative gap, MAE, TD and loss jointly; no convergence or causal performance claim.",
  "later_training_authorized": false
}
```

Full choice/all-action and feasible-count distributions are in development_ep01_ep10_ep25_comparison.csv, ep25_development_action_by_feasible_count.csv and ep25_development_choice_policy.csv under the staged_training_002 report. MC calibration is retained per episode, including 15, 20, 25 and Episode25 development. No equality of Q and MC is required. Exact Episode10→25 per-request policy movement is unavailable because Episode10 did not retain those request records; aggregate policy movement is descriptive only. No Episodes26+ launched; March17–31 untouched.

</details>
