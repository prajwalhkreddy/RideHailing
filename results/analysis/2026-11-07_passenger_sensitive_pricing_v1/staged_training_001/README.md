# SUPERSEDED_TIME_AWARE_DISCOUNT_DIAGNOSTIC

This technically valid time-aware run is historical evidence, not the active V1 model. Its original text, checkpoint and metrics are preserved below. The per-request discount correction supersedes its gamma semantics; it was never resumed into staged_training_002.

[V1 hub](../README.md) · [Methodology](../METHODOLOGY.md) · [Academic review summary](../ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../review_feedback_reconciliation/README.md) · [Bellman correction](../bellman_discount_correction/README.md) · [Authoritative staged training](../staged_training_002/README.md) · [Action dominance](../staged_training_002/action_dominance_diagnostic/README.md)

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`. No additional training is authorized.

---

# Passenger-Sensitive Pricing V1 — Staged Fresh Training

## 1. Purpose

Fresh Passenger-Sensitive Pricing V1 staged training: **COMPLETED**. Completed episodes=1; current episode=1, slot=16. One fresh seed42 learner; no old checkpoint resumed. Stop ceiling25 episodes; stage gates1/10/25. Choice and forced requests are reported separately. Convergence=NO; numerical/policy stability remain UNCLEAR until stage evidence is reviewed. March17–31 untouched. Training beyond25 not started. See [staged report](README.md).

## 2. Frozen Methodology

Positive truncated empirical support[0.017809913104763053,27.324599740032788], no extra floor; global references unchanged; raw preference P_base-scaled equation; P_accept=max(0.85*P_base,P_raw). Seven factors0.85–1.15.13D state and all frozen model/dispatch interfaces unchanged.

## 3. Fresh Initialization

Fresh online/target/Adam/replay/RNG/counters seed42. Initialization hashes and exact source in run_config.json and model initialization.json; no prior pricing checkpoint loaded.

## 4. Training Data Boundary

Authoritative saved March1–15 episode schedule, first25 only; exact start/end per episode in run_config.json/episode_summary.csv. March16 fixed development only.

## 5. Training Protocol

16×30min slots;8 updates/warm slot after1000 finalized transitions; no request-count decay or updates. Same learner persists. Three monitoring-adapter preflight tests passed.

## 6. Detached Execution Model

Three separate detached workers. Stage1 only episode1; Stage2 restores episode1 only after a separate PASS review; Stage3 similarly restores episode10. Each worker evaluates March16, checkpoints, writes its completion marker and terminates. No automatic next-stage launch; no active Codex polling.

## 7. Request-Level Replay

Next chronological actionable request; masks stored; gamma=.99**(elapsed minutes/30); terminal reward only.

## 8. Time-Aware Discount

gamma_eff=0.99**(elapsed simulated minutes/30); equal timestamps give1. Terminal target is reward only.

## 9. Feasible-Arm Distribution

See feasible_arm_policy_summary.csv and action_frequency_by_feasible_count.csv; K1..7 separate.

## 10. Choice vs Forced Requests

Forced K1; choice K>=2. Entropy/normalized entropy/greedy concentration restricted to K>=2. Current completed-episode choice rate: 0.3415968311282369

## 11. Episode 1 Smoke Test

| stage | episode | requests | choice_rate | forced_rate | assignments | assignment_rate | revenue | mean_offer | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE | dev_revenue | dev_assignments | dev_assignment_rate | stage_status | technical_gate | review_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP1 | 1 | 37111 | 0.3415968 | 0.6584032 | 33528 | 0.9034518 | 642373 | 19.08917 | 37111 | 128 | 0.997568 | 4.106485 | 39.09884 | 21.19454 | 24.61663 | 315478.6 | 322895.2 | 315481.3 | 54360.46 | 2767 | 0.9749824 | TECHNICAL_PASS_REVIEW_PENDING | PASS | NOT_REVIEWED |


## 12. Episode 10 Diagnostic

Not reached.


## 13. Episode 25 Review

Not reached.


## 14. Q / TD / Loss Diagnostics

Fixed deterministic evenly spaced sample up to512 replay entries per episode. Does not consume training RNG. Finite checks on model weights, Q, targets, losses. See q_diagnostics.csv/td_diagnostics.csv and loss_by_update.csv.

## 15. Monte-Carlo Return Calibration

| episode | kind | N | mean_G | median_G | P95_G | mean_selected_Q | median_selected_Q | MAE_Q_G | median_absolute_error | relative_median_calibration_ratio | correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | training | 512 | 315478.6 | 322895.2 | 567575.2 | -2.655957 | -2.856463 | 315481.3 | 322900.6 | -8.846408e-06 | 0.3291672 |
| 1 | development | 512 | 27092.11 | 27305.76 | 50703.67 | 2.511346 | 1.098285 | 27089.59 | 27307.3 | 4.022174e-05 | 0.3371694 |


## 16. Replay Utilization

Sampled examples=64×optimizer updates; cumulative reuse ratio divides by cumulative transitions added, not current capped replay size.

## 17. March16 Development Evaluation

Fixed March16 00:00–02:00,4 slots, environment/provider seed424242, full request flow, greedy. EvaluationView store is a no-op: no replay writes. Full weights/Adam/replay/RNG/counter fingerprint must match before/after each slot. Local trajectory audit is not replay.

## 18. Stage-Gate Decisions

| stage | episode | requests | choice_rate | forced_rate | assignments | assignment_rate | revenue | mean_offer | replay_size | optimizer_updates | exploration_epsilon | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE | dev_revenue | dev_assignments | dev_assignment_rate | stage_status | technical_gate | review_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EP1 | 1 | 37111 | 0.3415968 | 0.6584032 | 33528 | 0.9034518 | 642373 | 19.08917 | 37111 | 128 | 0.997568 | 4.106485 | 39.09884 | 21.19454 | 24.61663 | 315478.6 | 322895.2 | 315481.3 | 54360.46 | 2767 | 0.9749824 | TECHNICAL_PASS_REVIEW_PENDING | PASS | NOT_REVIEWED |


## 19. Numerical Stability

UNCLEAR pending completed stage diagnostics. Hard failure stops immediately; each stage terminates; a separate invocation reviews it before the next detached launch. No automatic parameter changes.

## 20. Policy Stability

UNCLEAR until separate saved-artifact stage review. Choice requests only are used to assess policy diversity.

## 21. Convergence Status

CONVERGED=NO by protocol;25 episodes cannot establish convergence.

## 22. Protected Final Evaluation

March17–31 excluded. March16 not used for training; fixed diagnostics only.

## 23. Artifact Index

run_config.json, training_status.json, invariant_summary.json, training.log; episode/slot/stage metrics; Q/TD/MC metrics; policy-by-feasible-count metrics; development_evaluation.csv; applicable plots; fresh per-episode checkpoints. Missing later-stage rows/plots mean NOT_REACHED, never inferred results.

## Bellman Return Scale Diagnostic Complete

Saved-artifact review: **METHODOLOGY_REVIEW_REQUIRED; STAGE1_REVIEW=REVIEW_REQUIRED**. MC arithmetic reconciles, but horizon aliasing and total-request-revenue scale require methodology review. Stage2 not launched. [Diagnostic report](bellman_return_scale_diagnostic/README.md).
