# Final non-private pricing-DQN training — launch record

**FINAL_NONPRIVATE_PRICING_TRAINING_LAUNCHED = YES.** Initial health verified for detached PID **6380**, at March 1 00:00 with zero slots completed. This is a launch record, not a claim of 720-slot completion. Monitoring stopped immediately after startup health passed. Use local status files for subsequent progress; the launch PID is not a permanent liveness guarantee.

## Frozen routing model and limitation

Selected inference-only routing checkpoint:
`models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras`.

Status: **SIMULATOR_DERIVED_ROUTING_BASELINE**. Architecture 169→64→32→9. SHA-256: `e82601fd5bfdf29ba85b54d2dfc3fa2b00a70779bda00a765575f0f89f482e0a`. Routing weights are checked unchanged after each slot; routing updates are rejected and the frozen execution path does not invoke FedAvg. No new routing dataset is written.

**ROUTING_EFFECTIVENESS_CONCERN = YES:** validation accuracy 85.3673% is below the 93.8993% majority baseline. This limitation remains unresolved. The central and synthetic checkpoints are not substituted.

## Pricing initialization and fixed configuration

Final training starts independently from deterministic **seed 42**, with target weights exactly copied from online weights, fresh Adam state, empty replay, zero optimizer steps and epsilon 1.0. The initial committed checkpoint is `/Users/prajwalhk/Keerthi/Implementation/models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0000_caa5a618`. Its online/target weight hash matches the independently verified seed-42 initialization. Neither the standalone implementation fixture, March-16 integration checkpoint nor prelaunch checkpoint initializes final training.

Network 13→64 ReLU→64 ReLU→7 raw Q-values; standard DQN, Adam 0.001, Huber loss, gamma 0.99, batch 64, replay capacity 100,000, warm-up 1,000, soft target tau 0.005. Epsilon decreases linearly from 1.0 to 0.05 over 50,000 **optimizer updates**, not requests or slots. Exactly one optimizer check occurs after each main slot; no extra updates are introduced.

Identity-normalized pricing features remain J_hat, previous-slot J_disp, incoming commitments, nine selected-policy routing probabilities and destination popularity. Actions remain [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15], applied to the existing weather/half-hour fare baseline. Acceptance remains `behavioural_E_threshold`; Record-029 epsilon is not used at runtime. Reward is gross accepted, successfully assigned fare at assignment time, with no cost subtraction.

One replay transition represents **one observed origin/destination pair within a 30-minute slot**. Its action is reused for that OD within the slot and its reward sums successful assignment fares. Zero-assignment OD rewards remain zero. No request-level or alternative aggregation was introduced. Transition counters count insertions even after replay reaches capacity.

## Temporal and simulator contract

Chronological training starts March 1 00:00 and ends with March 15 23:30, 720 slots. Completion boundary March 16 00:00 is not a training observation. Optimizer execution at March 16 or later is rejected before slot execution. Final replay uses `done=True` and an ignored copy of the current state as the terminal next-state; no March-16 forecast/state is loaded. March 17–31 remains untouched protected final evaluation.

The existing true-3-km / 142-grid / 16×16 environment, 5,000-driver fleet, operational formulas, H_i_max=10, EV reachability, FCFS matching, timed passenger/reposition movement and timed charging are unchanged. Requests use the existing forecast-count/intact empirical-trip simulator flow. Final model selection is the final chronological checkpoint, with no later-period performance selection.

## Bounded real validation

Four March-1 slots ran only in `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42_prelaunch/`. Execution paused after two slots and resumed from the committed two-slot state to complete slots three and four, without repeating completed slots.

| Metric | Value |
|---|---:|
| Requests | 12,298 |
| Accepted / rejected | 2,431 / 9,867 |
| Assigned / accepted unmatched | 2,274 / 157 |
| Revenue, USD | 47170.55439367 |
| Replay transitions / replay size | 1,731 / 1,731 |
| Optimizer updates | 2 |
| Epsilon start / end | 1.0 / 0.999962 |
| Pricing action counts, 0–6 | [247, 259, 257, 242, 212, 264, 250] |
| Fleet | 5,000 |
| Charging events | 0 |
| Reserve assignment / reposition exclusions | 0 / 0 |

Rewards reconcile with assignment rewards and replay rewards. All observed states and next-states validate as finite 13D vectors with nine valid routing probabilities. Fleet identity/count and nonnegative finite energy passed; existing movement and reachability invariants remained active. Timed charging was enabled but no charging event occurred in these four slots; this is not evidence of new charging-event coverage. Routing weights remained unchanged. Warm-up was crossed in slot three and the existing update cadence produced two updates.

**19 focused tests passed; zero failed.** Tests cover selected routing identity/shape/masking, clean deterministic initialization, replay/action validation, epsilon schedule, standard Bellman targets, target updates, optimizer continuation, complete checkpoint resume, nonblocking writer lock, failed duplicate background launch preserving the active PID, frozen routing-update rejection and the terminal/cutoff boundary. No broad simulator/CNN/DQN discovery suite was run.

## Launch, status and resume

Executed from the project root:

```sh
MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/train_final_nonprivate_pricing.py --background
```

Default target is 720 slots; default checkpoint cadence is eight. Fresh launch refuses an already committed namespace. Do not launch a second writer.

- PID file: `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/process.json` (launch PID 6380).
- Writer lock: `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/writer.lock`.
- Log: `results/analysis/2026-10-25_final_nonprivate_pricing_training/training.log`.
- Compact live status: `results/analysis/2026-10-25_final_nonprivate_pricing_training/training_status.json`.
- Checkpoint commit pointer: `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/CURRENT.json`.
- Slot metrics: `results/analysis/2026-10-25_final_nonprivate_pricing_training/slot_metrics.csv` (written at commits).

After a safe stop or process failure, resume with:

```sh
MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/train_final_nonprivate_pricing.py --background --resume
```

`--stop-after-slot N` is an absolute slot target, not additional slots. `--checkpoint-every-slots` accepts 1–8; final launch uses eight. `--log PATH` changes redirected stdout/stderr. `--validation-only` selects the isolated fixture namespace and permits at most four slots.

Safe pause: send SIGINT or SIGTERM to the current PID from `process.json`; it completes the current slot, commits and exits. SIGKILL/power interruption may lose work since the last committed checkpoint. Never start a resume while another process owns the lock.

## Checkpoint and exactly-once semantics

An immutable checkpoint directory contains online and target models, Adam state, replay, schedule counters, simulator state, fleet, operational history, passenger commitments, charging state/events, request counter, cumulative reports and RNG states. A `CURRENT.json` pointer is atomically advanced only after payload files are saved and fsynced. Routing identity and every payload hash are checked on resume. Static empirical request support is reloaded lazily, with its existing RNG state restored.

The committed slot counter is authoritative. Resume does not repeat committed slots, duplicate replay or repeat committed optimizer updates, and does not reset epsilon. A failed/uncommitted partial slot is discarded and may be recomputed from the last valid checkpoint. Output summaries are derived from committed cumulative reports, not appended blindly.

Checkpoints occur every eight slots, at day boundaries, completion and safe pause. Errors retain the last committed checkpoint rather than saving partially mutated simulator state. Background launch acquires the lock before spawning; the child inherits it in a separate OS session and alone publishes the PID. A rejected second launch cannot overwrite the active PID.

## Initial health and review artifacts

The one-time health check confirmed the process exists in its own session, writer lock is held, selected routing identity is loaded, fresh pricing initialization matches, timestamp is March 1 00:00, log exists and initial checkpoint is committed. No further training monitoring was performed in this task.

Review `training_config.json`, `routing_checkpoint_identity.json`, `prelaunch_validation.json`, `checkpoint_contract.json` and `execution_validation.json`. Implementation: `scripts/train_final_nonprivate_pricing.py` and `src/simulation/final_pricing_training.py`; minimal integration edits are in `src/simulation/final_production.py`.

After independent completion, a separate task must validate/freeze final checkpoints and learning behavior before protected March 17–31 evaluation. No final evaluation, routing retraining, FedAvg, privacy/security experiments or hyperparameter search was performed here.
