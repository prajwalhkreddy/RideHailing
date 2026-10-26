# Pricing-DQN training adequacy diagnosis

## Decision

**TRAINING_SCHEDULE_MISMATCH**. **PROJECT_CONFIG_DECISION_REQUIRED = YES.** A single 720-slot training horizon yields only 718 optimizer updates, completing 1.436% of a 50,000-update epsilon schedule. The scheduled exploration-to-exploitation transition cannot meaningfully occur in that horizon. This is a compatibility finding, not proof that the learned greedy Q-network is useless.

Before protected final evaluation, agree whether to change the optimizer cadence, define epsilon decay relative to the available training horizon, or explicitly permit multiple chronological training episodes. No option is selected here. No retraining or optimizer update was performed; all simulator methodology, DQN settings, selected routing model and source checkpoints remain unchanged. March 17–31 was neither read nor simulated.

## Verified final checkpoint and cadence

Checkpoint: `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4`.

All payload hashes match the committed manifest. Completion is **720 slots / March 16 00:00**, with **288,181** inserted transitions, final replay **100,000**, optimizer iterations **718**, and epsilon **0.986358**. Online/target weights and optimizer tensors are finite. Independent reloads reproduce model/optimizer/RNG hashes and exact Q predictions.

`ProductionExperiment.run_slot` invokes `PricingDQN.train_step` once after insertion of the completed slot's OD transitions. `train_step` returns without an update when replay contains fewer than 1,000 entries. The first two slots contain 473 and 921 cumulative transitions; slot 3 reaches 1,329. Slots 3–720 each execute exactly one update: **720 − 2 = 718**. The number of transitions inserted within a slot does not multiply optimizer updates. Sampling remains batch size 64 from the existing replay buffer. No cadence change was made.

## Epsilon mathematics and horizon

The implemented schedule is `epsilon(u) = 1 − 0.95 × min(u / 50000, 1)`, where `u` is optimizer updates. Therefore `epsilon(718) = 1 − 0.95 × 718 / 50000 = 0.986358`.

| Target epsilon | Continuous update crossing | First integer update |
|---|---:|---:|
| 0.90 | 5,263.157895 | 5,264 |
| 0.50 | 26,315.789474 | 26,316 |
| 0.10 | 47,368.421053 | 47,369 |
| 0.05 | 50,000 | 50,000 |

At 718 updates per pass, 50,000 updates require 69.637883 pass-equivalents. If replay carries over and only the first pass incurs two warm-up slots, the equivalent is `(50000+2)/720 = 69.447222` passes. Either interpretation requires reaching a **70th whole pass**. These are arithmetic diagnostics, not permission to repeat the training period or reset/reuse replay differently.

Training action selection remained approximately 98.64–100% exploratory over the run. The final diagnostic instead uses greedy `argmax Q`, with exploration disabled only for inference. The persisted epsilon schedule remains 0.986358.

## Final Q-network

Sample: 10,000 evenly spaced current states from the final 100,000-entry replay; duplicates retain their empirical frequency. The retained replay begins within the slot **2026-03-11 14:00:00** and extends through March 15. This is a compact late-training sample, not a uniform sample of the entire March 1–15 population.

- Finite Q values: **YES**.
- Q magnitude minimum / mean / maximum: **3.869085 / 81.000320 / 566.696594**. All sampled Q values are positive, so raw and absolute summaries coincide.
- Mean action-Q range, `max(Q) − min(Q)`: **17.711189**.
- Mean top-1 minus top-2 gap: **2.419454**.
- Greedy action counts 0–6: **[4295, 5705, 0, 0, 0, 0, 0]**.
- Greedy percentages: **[42.95, 57.05, 0.0, 0.0, 0.0, 0.0, 0.0]**.
- Five actions are never selected in this sample. The largest action share is **57.05%**, selecting factor 0.90; the remaining 42.95% select factor 0.85.
- Near-tie fraction: **19.52%**, defined descriptively as top-1 minus top-2 ≤ 1% of `max(1, |top1|, |top2|)`. This is not a method change or an inference tolerance.

The network differentiates action values and produces a state-dependent discount policy. Q spread alone does not establish calibrated values, convergence, optimality or out-of-sample effectiveness.

## March 16 development-only comparison

Both modes used **March 16 00:00–02:00, four 30-minute slots**, fresh identical seed-42 fleet/operational initialization, the same final trained DQN and frozen selected FedAvg routing model. The final training fleet was not continued. The existing forecast/intact-trip request flow was used. Request signatures matched for every slot. This is an early-night development diagnostic, not full-day or protected final evaluation. A 48-slot pair was not inexpensive at the observed runner cost, so the existing bounded short-run interface was used.

Greedy selection calls the existing policy with `explore=False`; reported inference epsilon is zero without modifying the agent's schedule. Fixed-1.00 selects the existing action index 3. These are diagnostic-local action adapters, not production changes. Replay insertion and optimizer methods were guarded to raise if invoked. Every source snapshot was guarded to March 16 only.

| Metric | Greedy final Q-network | Fixed factor 1.00 |
|---|---:|---:|
| Requests | 2,838 | 2,838 |
| Accepted | 1,801 | 953 |
| Rejected | 1,037 | 1,885 |
| Assigned | 1,801 | 953 |
| Accepted unmatched | 0 | 0 |
| Gross assignment revenue, USD | 33721.10975948 | 19996.37637951 |
| Mean assigned-request pricing factor | 0.889672 | 1.000000 |
| Fleet count | 5,000 | 5,000 |
| Charging events | 0 | 0 |
| Reserve assignment exclusions | 0 | 0 |
| Distinct reserve-rejected requests | 0 | 0 |
| Reserve reposition exclusions | 0 | 0 |

Greedy action counts 0–6: **[196, 908, 0, 0, 0, 0, 0]**. Fixed action counts: **[0, 0, 0, 1104, 0, 0, 0]**. Counts represent one selected action per observed OD/main-slot, not individual requests. Dispatched-factor means are weighted by successful assignments.

Greedy revenue differs from fixed-1.00 by **$13,724.73 (+68.64%)** in this matched two-hour development window. The comparison shows policy-response differences under the simulator; it does not establish a uniquely effective or converged policy, causal real-world price elasticity, whole-day superiority or protected-period performance. Do not infer that high training epsilon alone makes the final greedy network useless.

## Integrity checks and scope

Both inference runs retain exactly **718 optimizer updates**, **100,000 replay entries**, unchanged online/target/optimizer/RNG hashes, unchanged routing weights, 5,000 unique vehicles and finite nonnegative energy. Existing reward reconciliation and movement/reachability invariants remained active. Charging-event counts above describe observed coverage, not new proof about unobserved events. All source checkpoint hashes were rechecked after inference. There was no training call, replay insertion, hyperparameter search or protected-period access.

## Review files

- `training_cadence.json`: completion, warm-up, update count, reload and hash validation.
- `epsilon_schedule_diagnosis.json`: arithmetic, horizon compatibility and required decision.
- `q_value_diagnostics.json`: compact saved-state Q analysis and explicit sampling/tie definitions.
- `march16_greedy_diagnostic.json`: greedy development metrics and integrity checks.
- `march16_fixed100_comparator.json`: matched fixed-price development comparator.
- `diagnose.py`: scoped reproducible diagnostic implementation; refuses to overwrite completed inference results.

**PRICING_DQN_TRAINING_ADEQUACY_DIAGNOSED**
