# Passenger-Sensitive Pricing V1 — Authoritative Staged Training Through Episode25

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

## Initialization and exact stage continuation

`staged_training_002` is authoritative: fresh online/target/Adam/replay/exploration/RNG/counters, seed42. Neither staged_training_001 nor historical pre-reformulation Episode25 was loaded. Stages1/2/3 completed Episodes1,2–10,11–25. Episode1→2 restored replay37,111, updates128, epsilon0.997568; Episode10→11 restored replay100,000, updates1280, epsilon0.97568. Network, target, Adam, chronological replay order, learner/action RNG, replay RNG, counters and persisted scheduler were verified. The full deque serializes oldest-to-newest order; no separate circular cursor is required. Episode25 finished with3200 updates and epsilon0.9392. All stage technical gates PASS; no protected-date access or development learner mutation.

## Frozen active method

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

## Episode1 / Episode10 / Episode25

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

## Q / TD / loss / realized return calibration

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

## Fixed March16 development

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982 | 54330.574517 | 19.616313 | 0.450669 | 0.549331 | 3.107260 | 33.486538 |
| 10 | 2838 | 2792 | 0.983791 | 56855.790887 | 20.328218 | 0.450669 | 0.549331 | 58.999302 | 104.065437 |
| 25 | 2838 | 2786 | 0.981677 | 56419.267854 | 20.220285 | 0.450669 | 0.549331 | 147.337677 | 199.559387 |

The fixed March16 fixture has2,838 requests, environment/sensitivity seed424242, 00:00–02:00, greedy actions and unchanged learner fingerprints. Episode10→25 revenue fell **$56,855.79→$56,419.27** (approximately−0.77%); assignments2792→2786 and assignment rate decreased approximately0.21 percentage points. Episode25 is not an improvement over Episode10. Training episodes have different source dates/conditions: their assignment rates are not a controlled comparison.

No development replay writes, optimizer/target mutation, epsilon decay or training-RNG mutation occurred. This is a reused development fixture, not final held-out evaluation. March17–31 remains untouched.

## Choice requests and policy movement

A **forced request** has K=1 feasible arm; a **choice request** has K≥2. Episode25 development has1,559 forced and1,279 choice requests (choice rate0.450669486). Choice counts for factors0.85/0.90/0.95/1.00/1.05/1.10/1.15 are **78/75/36/17/62/991/20**. Factor1.10 dominates the current greedy choice policy: approximately92.60% for K=7 and90% for K=6; K=5 selects1.05 in78.125%; K=4 is mixed. Concentration is not inherently optimal. Policy interpretation uses greedy choice results, not exploratory training counts or forced actions. Entropy and feasible-count summaries remain in the saved artifacts.

Exact Episode10→25 request-level movement is unavailable: Episode10 saved aggregate frequencies only. policy_movement_ep10_ep25.json explicitly records this. Distribution concentration and performance movement are descriptive; no reconstructed pairs or significance claim.

## Current scientific interpretation

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

## Action-dominance diagnostic

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.267854 | 20.220285 | 20.250993 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.006192 | 20.724974 | 20.764855 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.042788 | 18.143989 | 18.143989 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441 | 19.515901 | 19.538425 | 91 | 0 |

[Full action-dominance report](action_dominance_diagnostic/README.md)

## Artifacts and stop point

Authoritative stage_summary.csv, development_evaluation.csv, mc_return_calibration.csv, q_diagnostics.csv, td_diagnostics.csv, loss_by_update.csv and episode_summary.csv provide metrics. Completion markers stage_ep01_complete.json, stage_ep10_complete.json, stage_ep25_complete.json are PASS. continuation_state_verification.json and stage3_continuation_state_verification.json document exact restore. Checkpoint: models/pricing_dqn/passenger_sensitive_v1_seed42/staged_training_002/episode_025. Final3200 updates and epsilon0.9392 reconcile. The TD final-status serialization fix is documented in stage2_preflight.json.

Stage1/2 reviews PASS; Episode25 is the current academic-review stop point. No further training or Episode100 authorization.

[V1 hub](../README.md) · [Methodology](../METHODOLOGY.md) · [Academic review summary](../ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../review_feedback_reconciliation/README.md) · [Bellman correction](../bellman_discount_correction/README.md) · [Authoritative staged training](README.md) · [Action dominance](action_dominance_diagnostic/README.md)
