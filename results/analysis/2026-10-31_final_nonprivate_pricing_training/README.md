# Final Non-Private Multi-Episode Pricing Training

FINAL_NONPRIVATE_PRICING_TRAINING_LAUNCHED = YES

The frozen protocol in `../2026-10-31_final_pricing_training_protocol/` is unchanged. This run starts fresh, not from a legacy or fixture checkpoint. Budget: 500 episodes, 16 slots each, 8,000 slots total. Eight updates per completed slot after 1,000-transition warmup; epsilon 1.0 to 0.05 over 50,000 optimizer updates. The persisted episode sequence is used directly.

## Launch

PID: 36160. Detached command: `/Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/run_multiepisode_pricing.py --launch` with `PYTHONPATH=.`.

Log: `training.log`. Initial health evidence: `launch_health.json`. Live status: `status.json`. Checkpoint namespace: `models/pricing_dqn/final_nonprivate_multiepisode_seed42/`. Writer metadata: namespace `process.json`; exclusive lock: `writer.lock`. Episode checkpoints contain online/target/Adam/replay/RNG and simulator state. `protocol_cursor.json` records completed episode sequence position. Future explicit resume uses the same command with `--resume`.

Initial health verified: episode 1 initialized, replay 0, optimizer updates 0, epsilon 1.0, target identical to deterministic seed-42 online initialization, exclusive writer lock held. Routing hash verified: `db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a`. Routing remains inference-only at `models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras`.

## Launch safeguards and validation

The entrypoint received execution-only PID/status reporting, episode diagnostic fields, and deferred SIGINT/SIGTERM handling. A signal completes the current atomic simulator slot then checkpoints and stops; a development interruption resumes from the preceding completed training checkpoint and repeats the fixed development fixture. No learning parameters, reward, acceptance or reset semantics changed. Second writers are rejected before PID metadata is written. Fourteen focused tests passed; a mocked SIGTERM test verified safe-slot checkpoint and lock release. No additional simulator fixture was run.

Per-episode metrics and periodic development summaries are persisted in the checkpoint namespace. Price-ineligible candidate counts are eligibility rejections, not successful-assignment violations. Existing assignment and reward invariants remain active.

March16 is greedy development only, with no replay insertion or training. March17–31 is untouched. Old pricing, protocol fixture and routing artifacts are preserved. Monitoring stopped after initial launch health verification; this report does not claim training completion or convergence.

Next action after episode500: FINAL_NONPRIVATE_PRICING_TRAINING_EVALUATION. No evaluation or automatic extension is performed by this launch task.

## Episode 1 reporting repair and exact resume

Episode 1 completed all 16 slots and committed `episode_0001/checkpoint_0016_1944f2bd` before summary generation failed. `OperationalRouting.decide` lazily creates `reserve_reposition_rejections` only on its first rejected reposition candidate (`src/routing/operational_interface.py:129–130`). Absence is therefore legitimately zero, not missing mandatory telemetry. The reporting helper now reads this optional counter with an explicit explanatory comment; nonzero counts are preserved. No routing or training behavior changed.

Checkpoint payload hashes, online/target weights, Adam state, replay contents, both learner RNGs and required simulator RNG fields passed verification. Two focused tests cover optional-counter access and the actual completed checkpoint through the resume boundary. A simulator-slot call in the completed-episode test is forbidden: no episode 1 slot or optimizer update is repeated. Learner weights, target, optimizer variables, replay and RNG signatures are identical at episode 2 initialization. Episode 1 metrics were recovered once with 7,662 replay insertions and exactly the persisted reward total.

Resume command: `PYTHONPATH=. /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B scripts/run_multiepisode_pricing.py --launch --resume`.

New PID: **36651**, process existence verified, exclusive writer lock held, `resume=true`. Initial episode 2 state: **7,662 replay entries, 120 optimizer updates, epsilon 0.99772**. Frozen routing SHA256 verified unchanged. Existing namespace and `training.log` are reused. Original failure evidence remains preserved; `resume_health.json` and `reporting_repair_tests.log` record recovery evidence. No state was lost or repeated. March17–31 remains untouched. Monitoring stopped after initial resume health verification.

**FINAL_PRICING_TRAINING_RESUMED**

## Authoritative continuation with observational monitoring

Resumed from episode5/slot2 checkpoint `episode_0005/checkpoint_0002_c73ba1cf`: replay30,039, updates520, epsilon0.99012. PID42615; existing training.log and status.json remain the launch/status paths. Exact weights, target, Adam variables, replay arrays/RNG, simulator cursor and unique completed metrics passed validation. Three focused tests passed. No accelerated checkpoint initializes this run; trusted eight-update cadence remains unchanged.

Monitoring reports at episodes10/25/50/100 contain consistent seed42 replay probes, terminal calibration, horizon-reference ratios, bootstrap fraction, current loss and the fixed mutation-free March16 greedy fixture. Existing every25-episode development evaluations are preserved, with episode10 added as explicitly requested. Full learner/replay fingerprints verify observational purity. Flags compare observed ratios to the preserved and accelerated references; they request review and neither define convergence nor stop merely because Q increases. No new learning parameters are selected.

The prior accelerated review and stability diagnosis are complete. Cadence attribution supports conditional monitored continuation, not established convergence. The500×16×8 protocol and protected March17–31 boundary remain unchanged. Initial health evidence is in monitored_resume_health.json; no monitoring beyond initial continuation is part of this launch task.

## Current-state review — 2026-11-01

PRICING_REVIEW_CUTOFF = EPISODE_25. Authoritative8-update training is paused for review; later partial episode26 is preserved and excluded. Episode10 versus25: mean|Q|141.653641→328.287354; Qmax586.097656→1122.203857; meanloss29.076785→41.908789; terminalreward26.500238→26.030598; terminalQ147.014526→338.098694; bootstrap80.662549%→89.363635%; replay67413→100000; updates1272→3192; epsilon0.975832→0.939352. Fixed development revenue23981.007204→20595.954943 and assignments1272→887. Policy has not converged. March17–31 untouched. Full consolidated review: `../2026-11-01_current_state_review/README.md`. Historical launch/failure/resume entries above remain provenance.
