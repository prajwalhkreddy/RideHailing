# Bellman Discount Correction — SUPPORTED / FROZEN

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

## Persisted offline comparison

| formulation | N | mean_reward | median_reward | mean_G | median_G | P95_G | median_G_over_median_reward | corr_remaining_requests | corr_remaining_time | quartile_1_mean_G | quartile_2_mean_G | quartile_3_mean_G | quartile_4_mean_G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OLD_TIME_AWARE | 37111 | 17.309504 | 18.143989 | 315510.192211 | 322877.321850 | 567554.654932 | 17795.277515 | 0.998324 | 0.998274 | 536190.187270 | 402760.507215 | 242513.749872 | 80551.000150 |
| NEW_REQUEST_STEP_099 | 37111 | 17.309504 | 18.143989 | 1725.825875 | 1799.281877 | 1922.039298 | 99.166829 | -0.478167 | -0.466432 | 1470.881311 | 1826.598761 | 1844.198037 | 1761.629249 |

Both rows reuse the same saved Stage1 trajectory; no rerun was performed for this documentation update. These full-trajectory means differ legitimately from512-position MC probes in fresh staged training. Gamma is applied per actionable request, with terminal reward only.

## Implementation and current status

37 focused checks passed at correction (30 learner/fixture and7 adapter checks), including zero/one-second/30-minute elapsed gaps, masking, terminal handling, cadence and legacy-checkpoint rejection. The former checkpoint was not resumed. Corrected staged_training_002 subsequently completed Episode25. The correction addresses return scaling and exposure; it does not prove policy optimality or resolve action-dominance concerns.

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

[V1 hub](../README.md) · [Methodology](../METHODOLOGY.md) · [Academic review summary](../ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../review_feedback_reconciliation/README.md) · [Bellman correction](README.md) · [Authoritative staged training](../staged_training_002/README.md) · [Action dominance](../staged_training_002/action_dominance_diagnostic/README.md)
