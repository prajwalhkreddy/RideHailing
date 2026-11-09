# Passenger-Sensitive Pricing V1

## 1. Current Status

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

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

## 2. Original Research Objective

The original consolidated formulation connected passenger sensitivity and actual OD distance L_gg′ to a raw passenger preference, platform price boundaries, DQN pricing factors, an acceptance threshold and downstream dispatch. V1 asks whether a request-level learned pricing policy adds dynamic value beyond simple feasible-price rules when interacting with driver availability and future fleet state. Historical signed sensitivity and earlier formulations remain traceable; simulated acceptance is not an identified causal willingness-to-pay response.

## 3. Academic-Review Feedback

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

## 4. Final V1 Methodology

Active contract: positive sensitivity magnitude, inclusive positive support, empirical resampling, scaled raw preference, platform-min protected threshold, masked request-level DQN and gamma0.99/request. `d_min=NOT_USED`. No methodology changes are made by this documentation consolidation.

[Concise active methodology](METHODOLOGY.md)

## 5. Sensitivity Source and Distribution

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

| distribution | N | mean | SD | median |
| --- | --- | --- | --- | --- |
| SIGNED_HISTORICAL_SENSITIVITY | 8685488 | 0.640621 | 7.106335 | 0.762120 |
| POSITIVE_V1_BEHAVIOURAL_PROXY_BEFORE_SUPPORT | 8685488 | 1.414638 | 6.993510 | 0.820126 |
| POSITIVE_V1_SUPPORTED_T0 | 8598805 | 1.095299 | 1.817300 | 0.820123 |

## 6. Absolute-Value Transformation

Date restriction and VALID/finite/nonzero selection precede the absolute-value transformation; positive quantiles follow it. Signed historical support is not applied before abs(). Historical negative values remain valid historical evidence. V1 runtime receives sampled positive magnitudes, not signed sensitivities.

## 7. Truncation and Sampling

T0 is symmetric in nominal tail probability, **not** numerical epsilon magnitude. Asymmetric alternatives were considered: T1=P0.5–P99, T2=P1–P99.5, T3=P1–P99. T0–T3 did not establish a superior alternative; T0 remains frozen. Duplicate empirical values make exact retained/tail percentages differ slightly from nominal percentages. The bounds regularize reciprocal sensitivity while preserving the central empirical distribution; excluded observations are not relabelled invalid.

`epsilon_min` is the support lower bound itself. **No additional floor** is active; P0.5/P1/P2.5/P5 post-support floor candidates are historical diagnostics. **TRUNCATED_EMPIRICAL_RESAMPLING** samples supported rows with replacement, preserving empirical duplicate frequencies and shape/skew/tails within support, using a caller-controlled deterministic seed. The global positive pool is used; no parametric family, Gaussian fit, or unsupported time-group model is imposed.

| candidate | lower | upper | retained_N | retained_pct | epsilon_mean | epsilon_SD | epsilon_median | no_offer_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T0 | 0.017810 | 27.324600 | 8598805 | 99.001979 | 1.095299 | 1.817300 | 0.820123 | 0.000000 |
| T1 | 0.017810 | 14.266572 | 8555302 | 98.501109 | 1.001997 | 1.236451 | 0.818044 | 0.000000 |
| T2 | 0.032143 | 27.324600 | 8555281 | 98.500867 | 1.100746 | 1.820307 | 0.822114 | 0.000000 |
| T3 | 0.032143 | 14.266572 | 8511778 | 97.999997 | 1.006995 | 1.237626 | 0.820126 | 0.000000 |

## 8. Passenger Preference Equation

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

## 9. Platform Minimum / Effective Threshold

The former condition `P_offer <= P_raw_c` produced **61.746289%** no-feasible/no-offer outcomes: **SUPERSEDED_RAW_THRESHOLD_DIAGNOSTIC**. Under `P_offer <= max(0.85*P_base,P_raw_c)`, valid-request no-feasible rate is **0%**, by construction because the minimum arm remains feasible. This is not evidence of improved real-world demand. No post-selection clipping is performed. `d_min = NOT_USED`; no deterministic minimum-distance fare rule is active.

## 10. Pricing Factors and Dataset Justification

Actions remain **[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]**. Dataset justification is **MODERATE**. Coverage of observed fare/P_base in 0.85–1.15 is **14.379973%**, measured on all 8,692,819 cleaned **Jan1–Mar15** fares in the saved factor study—not March16 development requests and not only supported epsilon rows. This period distinction avoids mislabelling “development-fare coverage.” Distance-band evidence uses km after converting historical miles. Exact endpoints and 5% spacing are project design choices; neither empirical optimization nor a full-market fare envelope is claimed.

## 11. Request-Level DQN Architecture

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

## 12. State and Action Mask

The unchanged 13D context does not append passenger attributes. They constrain the feasible action set before selection and target maximization. Masked-out Q values cannot win; terminal transitions have no bootstrap. Empty masks are defensive invariant/data-quality cases only.

## 13. Replay and Reward

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

## 14. Bellman Discount Correction

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

## 15. Superseded Time-Aware Training

| Superseded formulation/evidence | Reason and retained provenance |
| --- | --- |
| Signed support before absolute transformation | Wrong operation order for the positive V1 proxy; superseded_signed_first_calibration remains historical. |
| Raw-only P_offer≤P_raw_c | 61.746289% no-offer diagnostic superseded by effective threshold; original saved figures remain. |
| Older equation without P_base adjustment multiplier | SUPERSEDED_HISTORICAL_FORMULATION; consolidated scaled expression explicitly frozen by project decision. |
| Time-aware request gamma0.99^(delta_t/30) | Near-undiscounted accumulation and artificial-horizon aliasing; corrected gamma0.99/request. |
| staged_training_001 | SUPERSEDED_TIME_AWARE_DISCOUNT_DIAGNOSTIC; technically valid evidence, not active model. |
| Pre-reformulation Episode25 | Earlier pricing/acceptance/replay contract; not comparable active V1 and not resumed. Dated current-state and academic-review historical sections preserve results. |

The historical Record-029 package remains provenance, not a new V1 calibration. No historical numerical artifacts are deleted or overwritten.

## 16. Authoritative Staged Training

`staged_training_002` is authoritative: fresh online/target/Adam/replay/exploration/RNG/counters, seed42. Neither staged_training_001 nor historical pre-reformulation Episode25 was loaded. Stages1/2/3 completed Episodes1,2–10,11–25. Episode1→2 restored replay37,111, updates128, epsilon0.997568; Episode10→11 restored replay100,000, updates1280, epsilon0.97568. Network, target, Adam, chronological replay order, learner/action RNG, replay RNG, counters and persisted scheduler were verified. The full deque serializes oldest-to-newest order; no separate circular cursor is required. Episode25 finished with3200 updates and epsilon0.9392. All stage technical gates PASS; no protected-date access or development learner mutation.

## 17. Episode1 Results

| stage | episode | requests | choice_rate | forced_rate | assignments | assignment_rate | revenue | mean_offer | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE | dev_revenue | dev_assignments | dev_assignment_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP1 | 1 | 37111 | 0.341597 | 0.658403 | 33528 | 0.903452 | 642375.127717 | 19.089227 | 37111 | 128 | 0.997568 | 4.127954 | 39.370998 | 20.916428 | 24.332136 | 1723.784417 | 1797.625861 | 1725.698279 | 54330.574517 | 2767 | 0.974982 |

Stage1 review PASS; finite early Q below MC is not failure.


## 18. Episode10 Results

| stage | episode | requests | choice_rate | forced_rate | assignments | assignment_rate | revenue | mean_offer | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE | dev_revenue | dev_assignments | dev_assignment_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP10 | 10 | 39488 | 0.322680 | 0.677320 | 31657 | 0.801687 | 606587.710093 | 19.030274 | 100000 | 1280 | 0.975680 | 55.037945 | 130.933395 | 11.201169 | 8.368096 | 1528.837823 | 1561.104082 | 1479.369087 | 56855.790887 | 2792 | 0.983791 |

Stage2 review PASS; numerical stability and learning signal YES, policy stability at that interim review UNCLEAR, convergence NO.


## 19. Episode25 Results

| stage | episode | requests | choice_rate | forced_rate | assignments | assignment_rate | revenue | mean_offer | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE | dev_revenue | dev_assignments | dev_assignment_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP25 | 25 | 51654 | 0.286464 | 0.713536 | 22536 | 0.436288 | 435187.848519 | 18.929737 | 100000 | 3200 | 0.939200 | 138.293045 | 196.008087 | 12.567836 | 13.262941 | 838.012691 | 841.808621 | 722.323343 | 56419.267854 | 2786 | 0.981677 |

Technical PASS. Current review interpretation is recorded below; training assignment rate cannot be compared causally across different episode dates.


## 20. Fixed March16 Development Evaluation

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982 | 54330.574517 | 19.616313 | 0.450669 | 0.549331 | 3.107260 | 33.486538 |
| 10 | 2838 | 2792 | 0.983791 | 56855.790887 | 20.328218 | 0.450669 | 0.549331 | 58.999302 | 104.065437 |
| 25 | 2838 | 2786 | 0.981677 | 56419.267854 | 20.220285 | 0.450669 | 0.549331 | 147.337677 | 199.559387 |

The fixed March16 fixture has2,838 requests, environment/sensitivity seed424242, 00:00–02:00, greedy actions and unchanged learner fingerprints. Episode10→25 revenue fell **$56,855.79→$56,419.27** (approximately−0.77%); assignments2792→2786 and assignment rate decreased approximately0.21 percentage points. Episode25 is not an improvement over Episode10. Training episodes have different source dates/conditions: their assignment rates are not a controlled comparison.

No development replay writes, optimizer/target mutation, epsilon decay or training-RNG mutation occurred. This is a reused development fixture, not final held-out evaluation. March17–31 remains untouched.

## 21. Q / TD / Loss / MC Return Diagnostics

| episode | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4.127954 | 39.370998 | 20.916428 | 24.332136 | 1723.784417 | 1797.625861 | 1725.698279 |
| 10 | 55.037945 | 130.933395 | 11.201169 | 8.368096 | 1528.837823 | 1561.104082 | 1479.369087 |
| 25 | 138.293045 | 196.008087 | 12.567836 | 13.262941 | 838.012691 | 841.808621 | 722.323343 |

| episode | kind | N | mean_G | median_G | mean_selected_Q | median_selected_Q | MAE_Q_G | correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | training | 512 | 1723.784417 | 1797.625861 | -1.913862 | -1.969183 | 1725.698279 | -0.176995 |
| 1 | development | 512 | 1844.543322 | 1923.103556 | 2.950187 | 1.413699 | 1841.593135 | 0.054117 |
| 10 | training | 512 | 1528.837823 | 1561.104082 | 49.738243 | 48.159416 | 1479.369087 | 0.120845 |
| 10 | development | 512 | 1931.423405 | 2000.306302 | 58.382061 | 54.225601 | 1873.160993 | 0.116013 |
| 25 | training | 512 | 838.012691 | 841.808621 | 116.199814 | 114.167259 | 722.323343 | 0.357355 |
| 25 | development | 512 | 1916.483886 | 1991.282060 | 147.064789 | 153.370972 | 1770.080664 | 0.002390 |

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

## 22. Choice vs Forced Requests

A **forced request** has K=1 feasible arm; a **choice request** has K≥2. Episode25 development has1,559 forced and1,279 choice requests (choice rate0.450669486). Choice counts for factors0.85/0.90/0.95/1.00/1.05/1.10/1.15 are **78/75/36/17/62/991/20**. Factor1.10 dominates the current greedy choice policy: approximately92.60% for K=7 and90% for K=6; K=5 selects1.05 in78.125%; K=4 is mixed. Concentration is not inherently optimal. Policy interpretation uses greedy choice results, not exploratory training counts or forced actions. Entropy and feasible-count summaries remain in the saved artifacts.

## 23. Action-Dominance Diagnostic

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

## 24. Baseline Comparison

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.267854 | 20.220285 | 20.250993 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.006192 | 20.724974 | 20.764855 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.042788 | 18.143989 | 18.143989 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441 | 19.515901 | 19.538425 | 91 | 0 |

## 25. Current Scientific Interpretation

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

## 26. What Is Proven

The implemented formulas, support construction, masks, replay/cadence, exact stage continuation, finite diagnostics and fixed-fixture results are verified in saved artifacts. The four baseline runs reproduce identical fixture inputs and preserve checkpoint/learner fingerprints. Immediate monotonicity and high dominance risk are established within this model.

## 27. What Is Not Proven

Causal willingness-to-pay elasticity, converged/optimal pricing, DQN superiority, universal highest-feasible long-term dominance, policy stability and final hierarchical evaluation are not established. A fixed development fixture cannot substitute for held-out evaluation.

## 28. Open Research Question

1. Is positive absolute sensitivity with empirical truncation/resampling an acceptable behavioural proxy, given the absence of observed rejected-offer response labels?
2. Is `max(platform minimum, P_raw_c)` an acceptable effective passenger acceptance threshold, including its guaranteed minimum feasible arm?
3. Is the fixed0.85–1.15 factor set acceptable with moderate dataset justification and limited fare coverage?
4. Is gamma0.99 per request the preferred interpretation after moving the decision boundary to individual requests, given its request-intensity-dependent elapsed horizon?
5. With highest-feasible outperforming Episode25 DQN on March16, should longer training proceed first, should reward/environment structure be reconsidered, or should highest-feasible become a formal benchmark?
6. What evidence—across controlled fixtures, uncertainty and operational tradeoffs—should be required before claiming nontrivial DQN dynamic value?

These are questions for academic review, not decisions or authorization for another run.

## 29. Protected Final Evaluation

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`. March17–31 remains untouched. This task reads saved summaries only; no simulation, training, checkpoint load or new analysis. March16 remains development-only.

## 30. Artifact Index

### Authoritative Result Sources

| Topic | Source |
| --- | --- |
| Sensitivity calibration | [README.md](review_feedback_reconciliation/README.md) |
| Exact positive support | [restricted_calibration_support.json](restricted_calibration_support.json) |
| Bellman correction | [README.md](bellman_discount_correction/README.md) |
| Episode1/10/25 | [stage_summary.csv](staged_training_002/stage_summary.csv) |
| March16 fixed development | [development_evaluation.csv](staged_training_002/development_evaluation.csv) |
| MC calibration | [mc_return_calibration.csv](staged_training_002/mc_return_calibration.csv) |
| Action dominance | [README.md](staged_training_002/action_dominance_diagnostic/README.md) |
| Historical Record029 | [README.md](../2026-10-09_price_distance_sensitivity_record029_full_jan_mar/README.md) |
| Stage2 continuation | [continuation_state_verification.json](staged_training_002/continuation_state_verification.json) |
| Stage3 continuation | [stage3_continuation_state_verification.json](staged_training_002/stage3_continuation_state_verification.json) |
| Checkpoint completion | [stage_ep25_complete.json](staged_training_002/stage_ep25_complete.json) |

[V1 hub](README.md) · [Methodology](METHODOLOGY.md) · [Academic review summary](ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](review_feedback_reconciliation/README.md) · [Bellman correction](bellman_discount_correction/README.md) · [Authoritative staged training](staged_training_002/README.md) · [Action dominance](staged_training_002/action_dominance_diagnostic/README.md)

Numerical CSV/JSON artifacts remain unchanged. Values here are rounded presentations of persisted values. Current review labels supersede provisional automated labels without rewriting their provenance.
