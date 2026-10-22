# First short non-private hierarchical DQN episode

**SHORT_HIERARCHICAL_EPISODE_READY = YES**

The successful run covers exactly March 16, 2026, 00:00–02:00: four consecutive 30-minute slots, seed 42, the active 142-grid/16×16 environment and 5,000 EV-capable drivers. No automatic extension, model search, CNN/routing retraining or privacy implementation occurred.

## Results

| Slot start | Requests | Accepted/assigned | Rejected | Revenue USD | Replay size |
|---|---:|---:|---:|---:|---:|
| 00:00 | 1,000 | 398 | 602 | 7,839.617415481530 | 331 |
| 00:30 | 792 | 283 | 509 | 5,444.697218404977 | 645 |
| 01:00 | 516 | 218 | 298 | 4,502.764247326871 | 858 |
| 01:30 | 530 | 222 | 308 | 4,745.037210361971 | 1,104 |

Totals: 2,838 generated requests, 1,121 accepted and successfully assigned, 1,717 rejected, zero accepted-unmatched; revenue USD 22,532.11609157535. Revenue is recognized at assignment, not completion. There were 913 passenger completions and 208 ongoing passenger commitments at the terminal boundary.

Real flow uses the existing rounded forecast-count generator and intact empirical January trip sampler, not supplied fixture requests or forced actions. The unchanged generator reported 49 forecast demand units with no empirical origin support (13/11/14/11 by slot); these are separate from generated/rejected requests.

## Pricing and learning

The frozen 13→64→64→7 DQN, identity inputs and real epsilon-greedy action selection were used. Decision counts for factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15] were [153,170,158,153,138,171,161]. Request counts using those actions were [371,347,412,518,361,467,362]. An OD decision is held within a slot, so decision counts differ from request counts.

Replay contains 1,104 transitions, including 246 terminal transitions. The first three training calls were below warm-up. The fourth produced one optimizer update (loss 30.841909408569336). Epsilon was 1.0 throughout the action selection in this run and became 0.999981 after its final update. This is an integration result, not a performance conclusion.

## Movement, charging and state

Routing used the unchanged provisional 169→64→32→9 checkpoint, nine masked probabilities and existing U1/U2/U3 decisions. The run recorded 14,946 STAY decisions and 4,005 non-STAY reposition decisions. No local routing updates were supplied; the existing empty-update FedAvg cadence was a no-op.

Timed charging was enabled with explicit persisted H_i_max = 10 minutes. No charging decision, arrival or queue event occurred; final minimum energy was 22.507839 kWh, above the 15-kWh trigger. This episode therefore does not newly exercise queue contention or charging travel; their prior focused migration validations remain the evidence for those paths.

Fleet size remained exactly 5,000 after every event check. At 02:00 there were 4,298 IDLE and 702 BUSY vehicles, zero charging; 208 of the busy vehicles had known passenger commitments. Active assignment conflicts are rejected by the runner. Requests use chronological within-slot offsets and existing FCFS matching.

Operational fields remained finite and valid, with the frozen coefficients, initial F_hat/H_hat and reposition cost unchanged. Each next pricing state passed the 13D validator, including full masked probabilities, completed prior dispatch counts and only known passenger incoming commitments. The existing timestamp contracts reject future-source leakage.

## Checks and reproducibility

Each completed slot passed state/action/fare/acceptance checks, exact sequential assignment-fare reward reconciliation, J_disp equality, fleet conservation, replay-count reconciliation, next-state validity and unchanged routing weights. Checkpoint reload passed; all saved replay states, rewards and online/target weights were finite. No unrelated test suite was rerun.

The first external audit used Python's built-in sum, which can accumulate floating-point numbers differently from the ledger's sequential addition. It stopped after one simulator slot at a bitwise equality assertion. That attempt is preserved under `audit_accumulator_attempt/` (its zero completed count means zero independently checked slots, not zero simulator execution). The audit was corrected to use the ledger's sequential accumulation order; no runner/configuration change was made. A fresh seed42 run then completed all four slots with exactly zero reconciliation difference per slot. These attempts were not combined into one episode.

Older blocked evidence remains byte-preserved under `blocked_attempt_before_himax_resolution/`. Root configuration/validation files describe the successful run.

## Artifacts

- `slot_metrics.csv`: four completed-slot reports, epsilon and training diagnostics.
- `pricing_action_distribution.csv`: decision and request counts separately.
- `reward_reconciliation.csv`: successful dispatch fare sums and exact zero differences.
- `fleet_metrics.csv`: fleet statuses, ongoing commitments and energy bounds.
- `operational_state_summary.csv`: published next-slot operational field ranges.
- `episode_config.json` and `episode_validation.json`: frozen run configuration and validation limits.
- New checkpoint: `models/pricing_dqn/first_short_hierarchical_20260316_0000_0200_seed42/` (online/target networks, replay and metadata). Created only after all four slots passed; existing checkpoints preserved.
