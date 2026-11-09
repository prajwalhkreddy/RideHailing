# Passenger-Sensitive Pricing V1 — Academic Review Summary

Documentation consolidation from persisted evidence; no computation or methodology change.

## 1. Objective

The original consolidated formulation connected passenger sensitivity and actual OD distance L_gg′ to a raw passenger preference, platform price boundaries, DQN pricing factors, an acceptance threshold and downstream dispatch. V1 asks whether a request-level learned pricing policy adds dynamic value beyond simple feasible-price rules when interacting with driver availability and future fleet state. Historical signed sensitivity and earlier formulations remain traceable; simulated acceptance is not an identified causal willingness-to-pay response.

## 2. Changes Following Review Feedback

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

## 3. Final Methodology

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

## 4. Sensitivity Distribution and Sampling

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

| distribution | N | mean | SD | median |
| --- | --- | --- | --- | --- |
| SIGNED_HISTORICAL_SENSITIVITY | 8685488 | 0.640621 | 7.106335 | 0.762120 |
| POSITIVE_V1_BEHAVIOURAL_PROXY_BEFORE_SUPPORT | 8685488 | 1.414638 | 6.993510 | 0.820126 |
| POSITIVE_V1_SUPPORTED_T0 | 8598805 | 1.095299 | 1.817300 | 0.820123 |

T0 is symmetric in nominal tail probability, **not** numerical epsilon magnitude. Asymmetric alternatives were considered: T1=P0.5–P99, T2=P1–P99.5, T3=P1–P99. T0–T3 did not establish a superior alternative; T0 remains frozen. Duplicate empirical values make exact retained/tail percentages differ slightly from nominal percentages. The bounds regularize reciprocal sensitivity while preserving the central empirical distribution; excluded observations are not relabelled invalid.

`epsilon_min` is the support lower bound itself. **No additional floor** is active; P0.5/P1/P2.5/P5 post-support floor candidates are historical diagnostics. **TRUNCATED_EMPIRICAL_RESAMPLING** samples supported rows with replacement, preserving empirical duplicate frequencies and shape/skew/tails within support, using a caller-controlled deterministic seed. The global positive pool is used; no parametric family, Gaussian fit, or unsupported time-group model is imposed.

## 5. Request-Level DQN

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

## 6. Bellman Correction

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

## 7. Staged Training Results

`staged_training_002` is authoritative: fresh online/target/Adam/replay/exploration/RNG/counters, seed42. Neither staged_training_001 nor historical pre-reformulation Episode25 was loaded. Stages1/2/3 completed Episodes1,2–10,11–25. Episode1→2 restored replay37,111, updates128, epsilon0.997568; Episode10→11 restored replay100,000, updates1280, epsilon0.97568. Network, target, Adam, chronological replay order, learner/action RNG, replay RNG, counters and persisted scheduler were verified. The full deque serializes oldest-to-newest order; no separate circular cursor is required. Episode25 finished with3200 updates and epsilon0.9392. All stage technical gates PASS; no protected-date access or development learner mutation.

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

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

## 8. Fixed March16 Development Results

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982 | 54330.574517 | 19.616313 | 0.450669 | 0.549331 | 3.107260 | 33.486538 |
| 10 | 2838 | 2792 | 0.983791 | 56855.790887 | 20.328218 | 0.450669 | 0.549331 | 58.999302 | 104.065437 |
| 25 | 2838 | 2786 | 0.981677 | 56419.267854 | 20.220285 | 0.450669 | 0.549331 | 147.337677 | 199.559387 |

The fixed March16 fixture has2,838 requests, environment/sensitivity seed424242, 00:00–02:00, greedy actions and unchanged learner fingerprints. Episode10→25 revenue fell **$56,855.79→$56,419.27** (approximately−0.77%); assignments2792→2786 and assignment rate decreased approximately0.21 percentage points. Episode25 is not an improvement over Episode10. Training episodes have different source dates/conditions: their assignment rates are not a controlled comparison.

No development replay writes, optimizer/target mutation, epsilon decay or training-RNG mutation occurred. This is a reused development fixture, not final held-out evaluation. March17–31 remains untouched.

A **forced request** has K=1 feasible arm; a **choice request** has K≥2. Episode25 development has1,559 forced and1,279 choice requests (choice rate0.450669486). Choice counts for factors0.85/0.90/0.95/1.00/1.05/1.10/1.15 are **78/75/36/17/62/991/20**. Factor1.10 dominates the current greedy choice policy: approximately92.60% for K=7 and90% for K=6; K=5 selects1.05 in78.125%; K=4 is mixed. Concentration is not inherently optimal. Policy interpretation uses greedy choice results, not exploratory training counts or forced actions. Entropy and feasible-count summaries remain in the saved artifacts.

## 9. Action-Dominance Diagnostic

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.267854 | 20.220285 | 20.250993 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.006192 | 20.724974 | 20.764855 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.042788 | 18.143989 | 18.143989 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441 | 19.515901 | 19.538425 | 91 | 0 |

## 10. Current Interpretation

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

The evidence supports technical completion and finite learning, not an empirically identified optimum. The development fixture is comparable across checkpoints but remains a single reused scenario. Changing training episode dates prevents simple causal attribution of training-revenue fluctuations. Immediate incentives favor higher feasible offers; operational feedback and different drivers prevent assuming the same long-term state. Additional evidence must address incremental value against the simple baseline rather than relying on Q growth alone.

## 11. Questions for Academic Review

1. Is positive absolute sensitivity with empirical truncation/resampling an acceptable behavioural proxy, given the absence of observed rejected-offer response labels?
2. Is `max(platform minimum, P_raw_c)` an acceptable effective passenger acceptance threshold, including its guaranteed minimum feasible arm?
3. Is the fixed0.85–1.15 factor set acceptable with moderate dataset justification and limited fare coverage?
4. Is gamma0.99 per request the preferred interpretation after moving the decision boundary to individual requests, given its request-intensity-dependent elapsed horizon?
5. With highest-feasible outperforming Episode25 DQN on March16, should longer training proceed first, should reward/environment structure be reconsidered, or should highest-feasible become a formal benchmark?
6. What evidence—across controlled fixtures, uncertainty and operational tradeoffs—should be required before claiming nontrivial DQN dynamic value?

These are questions for academic review, not decisions or authorization for another run.

[V1 hub](README.md) · [Methodology](METHODOLOGY.md) · [Academic review summary](ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](review_feedback_reconciliation/README.md) · [Bellman correction](bellman_discount_correction/README.md) · [Authoritative staged training](staged_training_002/README.md) · [Action dominance](staged_training_002/action_dominance_diagnostic/README.md)
