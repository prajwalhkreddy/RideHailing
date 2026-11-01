# Final Behavioral Routing-Experience Generation

**FINAL_BEHAVIORAL_ROUTING_GENERATION_LAUNCHED = YES**

This is generation only. Startup health was verified and monitoring stopped. This report does not claim720-slot completion. The unattended process writes subsequent status and completion statistics.

## Frozen configuration

Exactly720 half-hour slots: March1 00:00 through March15 23:30, completion boundary March16 00:00. Seed42; fixed neutral pricing1.00; zero pricing replay and optimizer updates. No routing training or FedAvg. All-EV5000 fleet,142 valid3km grids and16×16 raster remain unchanged. States169D, masks9D, actions STAY,N,NE,E,SE,S,SW,W,NW; labels REPOSITION and EV_CHARGING_NEXT_HOP are finite and mask-valid.

Passenger epsilon=abs(Delta_D/Delta_P), sampled empirically with replacement from resolved historical pools; no Normal, smoothing or artificial floor. Invalid/zero values are excluded from sampling pools. P_max=P_base*(1+Delta_D/epsilon); passenger accepts iff P_dispatch<=P_max. The independent driver gate requires P_dispatch>=price_preference, equality eligible; FCFS skips ineligible candidates. Timed movement, energy, U1/U2/U3, H_i_max10minutes and post-movement station reachability are unchanged.

## Isolated namespace and launch

Data: `data/processed/routing_experiences_mar01_mar15_2026_final_behavioral/`

PID: **20665**, persisted in that namespace's `generation.pid`. Log: `data/processed/routing_experiences_mar01_mar15_2026_final_behavioral/generation.log`. Detached worker uses a new process session and disconnected stdin/stdout/stderr. Only the lock-owning worker writes its PID. A live duplicate background launch was rejected and preserved the original PID file.

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/generate_final_behavioral_routing.py --background
```

Initial log verifies March1 00:00, zero committed slots and zero experiences; empirical sampler and driver gate active. The worker progressed during the process-access permission check, so clean-start evidence is the initial log entry, not a later progress snapshot. No second generation was started.

## Persistence and resume

Existing atomic checkpoint/partition persistence is reused. Checkpoint every8slots, at day boundaries, completion and safe SIGINT/SIGTERM after the active slot finishes. Checkpoint is authoritative; on resume summaries reconcile from its reports. Tentative partitions beyond the checkpoint must reproduce exactly, otherwise resume fails. Experience IDs are contiguous and committed partitions checked for duplication. The checkpoint binds passenger artifacts, profile data and upstream implementation fingerprints; mismatches fail closed.

Resume requires the explicit `--resume` flag on the same launcher. A clean launch refuses an existing checkpoint/partition namespace. Never use either older namespace. Signal tests confirm safe checkpointing; no signal was sent to the full run. Request and passenger RNG states are persisted; passenger RNG is not reset each slot.

## Prelaunch evidence

Separate namespace: `data/processed/routing_experiences_mar01_mar15_2026_final_behavioral_validation/`. Exactly2clean slots generated **9182** experiences from **6797** requests: **1009** accepted, **841** assigned and **168** accepted-unmatched. No invalid-price assignments. Fleet5000 conserved; zero pricing replay/updates. State/mask/label, accounting and contiguous-ID checks passed. Existing timed-arrival, fleet and energy validation remained active; no EV behavior was changed.

Checkpoint reload reproduced the next32passenger draws exactly, without executing any additional simulator slots. **32focused tests passed,0failed**, covering generator persistence/cadence, signal checkpointing, temporal boundary cap, no implicit resume, contract mismatch, writer/PID protection, empirical sampling and driver eligibility. The validation dataset is never reused in the full run.

Prelaunch sampled epsilon minimum: **0.005730948687963**; slot medians: [1.247981865908674, 1.2510778149896622]. Price-ineligible candidate evaluations: **58178** across **991** requests; **168** accepted requests remained unmatched with otherwise feasible candidates blocked by price. These are driver outcomes, not passenger rejection.

## Compact diagnostics

Committed slot summaries contain epsilon minimum/P0.1/P1/P5/median, P_max min/max and counts above2×/5×P_base, accepted/rejected/assigned/unmatched and all three driver-price counters. Daily summaries aggregate counts and extrema; slot quantiles are not incorrectly averaged into daily quantiles.

`grid_slot_supply.csv` stores142rows per committed slot: request count, **idle vehicles at slot start in that grid**, assignments and accepted-unserved requests. This is an exact boundary snapshot, not request-time available neighbor supply. Grid assignment counts use request origin. These diagnostics use existing state, with no simulation redesign or value clipping.

## Provenance and next step

The3,077,890-experience pre-reachability dataset remains SUPERSEDED_PRE_REACHABILITY_RESERVE_GENERATION / PROVENANCE_ONLY. The3,257,840-experience reachability dataset remains PRE_CORRECTION_PROVENANCE. Neither was resumed, deleted or mixed into this run. Their checkpoint hashes were verified unchanged.

No March16+ training experiences are allowed; the terminal slot avoids advancing input access into March16. March17–31 remains protected. No model training, privacy implementation or frozen methodology changes occurred.

After completion, a separate task must validate the final dataset, freeze March1–12/March13–15 splits, train central routing and plain FedAvg, and evaluate probabilities against the empirical-prior baseline. None of those steps was executed here.

## Evidence files

- generation_config.json: frozen run configuration.
- upstream_contract_identity.json: active upstream fingerprints.
- prelaunch_validation.json: two-slot checks and reload evidence.
- execution_validation.json: PID, lock, clean-start and duplicate-launch evidence.
- prelaunch/: separate prelaunch diagnostics.
- generation_status.json and generation_checkpoint_manifest.json: worker-maintained progress.
- experience_generation_summary.csv, daily_generation_summary.csv and grid_slot_supply.csv: checkpoint-committed diagnostics.
