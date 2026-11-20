# Master-alignment reward validation

New research output belongs under `results_v2/<research_domain>/<ISO-date>_<descriptive_run_id>/`.
Only `pricing_dqn` is created for this batch. Historical `results/`, data and model artifacts remain in place.
Implementations live in `src/`, commands in `scripts/`, configuration in `config/`, and tests in `tests/`.
Use snake_case files/functions/directories, PascalCase classes and UPPER_SNAKE_CASE constants.
Keep existing import and historical artifact names stable.

The opt-in `DispatchRewardRuntime` reuses historical destination-context dispatch mechanics.
Its `SUCCESSFUL_DISPATCH_REWARD_V1` contract implements master Eq.(3)'s successful-dispatch accounting:
rejected and accepted-unmatched requests contribute zero; each assigned request contributes its offered fare once.
The adapter buffers historical transition proposals without storing their rewards, reconciles assignments,
then commits corrected replay. It makes no additional random draws or dispatch calls.

This is **not full master compliance**: decisions remain destination-only; demand, sensitivity,
CNN features, routing, federation, loss and training settings are unchanged. Do not launch training from this validation.

## Validation and output contract

From the repository root, in the established Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/reward_validation_mpl python -B scripts/validate_dispatch_reward.py --output results_v2/pricing_dqn/2026-11-17_dispatch_reward_validation
```

Use a new dated run identifier on subsequent runs. Existing directories are rejected, not overwritten.
The bounded fixture uses two vehicles and four constructed requests on March12, with no optimizer updates.
It compares both modes using identical initialization, requests and actions. No experiment episode is launched.

Each run contains `validation.json` (run ID, commit/dirty state, exact configuration, references,
input/source hashes, seed, metric definitions and pass/fail counts) and `test_results.txt`.
Large datasets/checkpoints belong in `data/` and `models/`, not here.

`accepted_revenue` remains a descriptive acceptance total; `assignment_revenue` and `learning_reward`
are the corrected objective. Per-request `reward_contribution` also follows the new contract.

## Checkpoint boundary

Versioned learner-only checkpoints use `DispatchRewardDQN.save/load` and a reward-contract envelope.
Historical top-level learner checkpoints are rejected by the new loader and vice versa.
The nested `learner/` payload is an implementation detail, not a standalone migration path.
Historical full-runtime checkpoint saving rejects the new runtime before writing.
New full-runtime resume is intentionally unsupported until separately validated; no historical weights are relabelled.
Historical V3 source/checkpoints retain their original semantics and hash identities.

## Feasible OD correction

`FEASIBLE_OD_PRICING_V1` now provides shared 13D OD pricing and versioned full-runtime
resume. The earlier reward-only adapter remains distinct. See
[OD validation](2026-11-17_feasible_od_validation/README.md) and
[implementation contract](../../../src/pricing/README.md). Historical results and
models are unchanged; no new training was performed.


## First bounded joint-learning pilot

[2026-11-18 joint pilot](2026-11-18_joint_learning_pilot/README.md): four March12 slots passed with 32 pricing updates, 19,344 routing updates, four FedAvg rounds, exact repeat and checkpoint continuation. Cutoff-safe historical-average forecasts were used. This is engineering integration evidence, not policy efficacy; no extended training has started.


## Single full-episode development validation

[2026-11-20 full episode](2026-11-20_full_episode_development/README.md) completed 16 March12 slots with 128 pricing updates and 16 NONPRIVATE FedAvg rounds. One-slot recovery matched exactly. The historical-average forecast preserves the fitted-information boundary; no CNN or protected evaluation data were used. This is development integration evidence, not policy efficacy. Only rolling recovery and final checkpoints are retained in the versioned models hierarchy. Further training requires a separately frozen development/evaluation protocol.

## Proposed multi-episode protocol — approval pending

[2026-11-20 decision packet](2026-11-20_training_protocol_decision/README.md) proposes one chronological 35-episode pass, master-described exploration, frozen development evaluation and bounded retention. It uses historical-average forecasts, not the later-selected CNN. Multi-episode resets and evaluation isolation require implementation validation after approval. No additional training or protected evaluation has been launched.

## Approved multi-episode orchestration — bounded pilot complete

[2026-11-20 orchestration](2026-11-20_multi_episode_orchestration/README.md) freezes the approved35-episode protocol and validates only the first two chronological March1 episodes. All32 slots completed with256 pricing updates,149,096 routing updates and32 NONPRIVATE FedAvg rounds. Epsilon continued from1.0 to0.875. Exact cross-episode checkpoint recovery and27 focused tests passed. The environment-RNG reset correction and interrupted-attempt evidence are documented. The continuation entry point is explicitly gated; the remaining33 episodes and real-data development evaluation were not launched. Long-horizon resource growth and later evaluation milestones remain unexecuted.
