# Unattended routing-generation execution

## Scope and preserved progress

Execution/persistence changes only. U1/U2/U3, neutral pricing factor1.00, empirical requests, labels, timing, fleet, operational equations, charging and model interfaces are unchanged. No training/FedAvg or time-parallel simulation is introduced.

The supervised process was interrupted before migration. The latest fully saved checkpoint was **March6 23:30,287 slots,1,301,888 experiences,5,000 vehicles**, not the earlier reported March2 checkpoint. `preserved_checkpoint.json` records the checkpoint hash and all287 existing partition hashes. Completed partitions are not regenerated.

## Persistence and commit semantics

Previously, each slot wrote one Parquet, rewrote small accumulated summary CSVs, and atomically replaced the mutable simulator checkpoint. It **did not rewrite accumulated experience rows**. The existing `slot_NNNN.parquet` format remains; no daily-format migration is needed.

Normal checkpoint/progress interval is now **8 half-hour slots =4 simulated hours**, plus calendar-day boundaries, requested stop/completion, and safe SIGINT/SIGTERM shutdown. Timing is measured since the last committed checkpoint; a day-boundary or safe-stop checkpoint resets that interval. Summary CSVs update at commit, not every slot. Checkpoints retain mutable fleet/charging/operational/passenger/mission state, counters, compact slot reports and persisted RNG states, not experience arrays.

Partitions are persisted atomically before the checkpoint. The atomic checkpoint is the commit authority; only its slot prefix is committed. The manifest records that prefix and checkpoint hash. Status/manifest/summary publication follows checkpoint replacement. If interruption occurs between these operations, resume reconciles them from the checkpoint, not a potentially stale CSV or manifest. They are separate atomic files, not a multi-file transaction.

Partitions beyond the checkpoint are tentative crash remnants. Resume deterministically regenerates only that uncommitted suffix and requires exact Arrow-table equality before reusing a remnant; a differing remnant fails closed rather than overwriting data. Committed partitions remain untouched. Worst-case crash recomputation is **up to8 slots**; never manually advance the checkpoint to match tentative files. A nonblocking file lock rejects a second writer.

The simulator's existing state/mask/label, temporal and fleet checks remain active. Runtime invariant failures stop generation and retain the last checkpoint; do not bypass them. SIGINT/SIGTERM requests completion of the current slot and a safe checkpoint, then exit. SIGKILL/power loss cannot checkpoint; recover from the preceding atomic commit.

## Local terminal commands

Run from the repository root with the existing `ridehailing-phd` environment and prepared inputs. This is the verified launcher; `--stop-after-slot` is an absolute target, not an additional-slot count.720 means the final March15 23:30 slot, ending at March16 00:00 without processing March16 requests.

```sh
conda activate ridehailing-phd
export PYTHONPATH=.
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=/tmp/final_cnn_matplotlib
python -B scripts/generate_simulator_routing_experiences.py --resume --checkpoint-every-slots 8 --stop-after-slot 720
```

Unattended/background (same activated environment; separate OS session):

```sh
python -B scripts/generate_simulator_routing_experiences.py --resume --checkpoint-every-slots 8 --stop-after-slot 720 --background --log results/analysis/2026-10-24_routing_generation_execution_optimization/routing_generation.log
```

`--background` redirects stdin to /dev/null and stdout/stderr to the log, persists a sibling `.pid` file, and uses `start_new_session=True`. It survives terminal logout but does not prevent host sleep/shutdown. Keep the local machine awake. Ordinary `nohup` attempts were terminated with their launching tool shells before generation began. The minimal explicit-session launcher is used and tested instead; no progress was lost. No Codex monitoring is needed for a local terminal launch. The full720-slot job is **not launched by this task**.

Manual progress check when wanted (not continuous polling):

```sh
tail -n 5 results/analysis/2026-10-24_routing_generation_execution_optimization/routing_generation.log
cat results/analysis/2026-10-21_simulator_derived_routing_policy/generation_checkpoint_manifest.json
```

Safe stop, after confirming the PID belongs to this generation process:

```sh
kill -TERM "$(cat results/analysis/2026-10-24_routing_generation_execution_optimization/routing_generation.pid)"
```

Wait for `PAUSED_ON_SIGNAL` and process exit; a busy slot may take time. Resume with the same command. Do not run two copies or delete the checkpoint/partitions. The lock is released by process exit; the lock file itself may remain. `--resume` rejects a missing checkpoint instead of silently starting from zero. A single RESUME log records startup, then logs occur at checkpoints, completion and failures, not per request/driver.

## Validation

Five focused execution tests cover eight-slot checkpoint cadence/final flush, calendar boundaries, required resume checkpoint, writer locking and fail-closed conflicting crash remnants. Real short validation is limited to eight additional slots:287→295. A test hook sends actual SIGTERM immediately after the slot288 day-boundary checkpoint; the process exits with PAUSED_ON_SIGNAL. The real CLI then resumes in a separate OS session with a hard stop at295. No frozen simulator calculation is patched by that hook.

Final persisted validation results and the latest resume point are recorded in `validation.json` after the bounded process exits. No full-dataset scan or repeated process monitoring is required for unattended operation.

Verified outcome: **UNATTENDED_ROUTING_GENERATION_READY = YES**. Eight real slots completed, with no duplicates and all287 earlier partitions unchanged. Final checkpoint: **2026-03-07 03:30:00,295/720 slots,1,338,429 experiences**. Fleet5,000; state/mask/label and finite operational-state checks passed. SIGTERM shutdown and detached resume both passed. Five isolated persistence tests passed. The bounded detached process exited at295; no full job remains running.
