# Chronological hierarchical OD orchestration

**Status: two-episode pilot and exact cross-episode recovery PASSED.** The 35-episode budget is frozen, but the remaining33 episodes were not launched. `validation.json` is the final consolidated result; `pilot_validation.json` records the earlier pre-recovery execution status.

The approved future timeline is March1 00:00 EST through March12 17:00 EDT (35 consecutive eight-hour episodes). The pilot is capped at the first two episodes: March1 00:00–08:00 and 08:00–16:00 EST. March13–15 development evaluation and March16 confirmation are not run in this pilot. March17–31 is protected.

## Contracts

`CHRONOLOGICAL_OD_V1` preserves historical single-episode behavior and adds an explicit physical reset with persistent pricing online/target weights, Adam, replay, counters, sensitivity RNG, global RNG, routing weights, local Adam and private memories. Reset fleet IDs, EV identity and persisted driver attributes must match exactly. Private memories remain associated with the same driver ID. Global federation IDs increase monotonically; episode-local simulation/demand counters restart. Terminal transitions retain zero-bootstrap semantics. Outstanding passenger commitments, charging occupants and navigation missions are counted as censored at reset, not completed.

`MASTER_UPDATE_STAIRCASE_V1`: epsilon = max(0.1, 1 − 0.005 floor(completed pricing updates / 10)). Neither attempted warm-up updates nor action selection advances this clock. Historical linear exploration remains the default legacy contract. Checkpoint loading rejects an incompatible exploration or orchestration contract.

Fresh routing uses `FRESH_CHRONOLOGICAL_ONLINE_ROUTING_V2`, with an explicit March1 initialization and chronological experience window. `CHRONOLOGICAL_INFORMATION_CUTOFF_V2` retains January OD and baseline demand, January–February sensitivity, verified historical driver priors and assumed 120-minute weather persistence. No historical learned weights are relabeled. Existing project hyperparameters were exposed to development evidence; this is not an independent model-selection experiment.

All scientific settings except the approved exploration schedule are retained: 5,000 vehicles/500 EVs; 120-second mini-slots; 13→64→64→7 pricing; eight updates per warm slot; half-squared Bellman objective; successful-dispatch learning rewards with fallback revenue separately reconciled; one local routing update per participating driver on the latest at most 32 observations; equal-client NONPRIVATE FedAvg.

## Evaluation interface

`isolated_evaluation` creates independent physical state and pricing networks, copies frozen learned weights, uses a frozen routing-response model, and restores the training process RNG on exit (including failure). Its supplied step uses epsilon-zero greedy selection. Pricing optimizer calls are rejected, routing updates are disabled, and any evaluation replay belongs only to the disposable environment. Private driver actions and EV safety continue normally. The training replay, memories, counters and optimizer state are not used by reference.

The approved evaluation milestones are episodes7/14/21/28/35; fixed seed42. The three fixed March13–15 windows and March16 confirmation remain as specified in the decision packet. No evaluation is performed during the two-episode pilot. Frozen snapshots must precede the evaluated timestamps. Matched policies must use identical request populations and documented sensitivity/fleet random streams.

## Checkpoint controls

Checkpoints are under `models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42/`. Existing atomic serialization includes source fingerprints, provenance, optimizer/target/replay/private-memory state and RNG. Role pointers are `latest`, `best`, `milestone`; at most three retained generations plus one in-progress generation. Every four slots the latest pointer advances only after a complete atomic write; the previous generation is then retired. An interrupted staging generation blocks further writes pending inspection, preserving the last-known-good pointer.

A conservative projected-write guard requires at least70 GiB free (50 GiB reserve +20 GiB maximum generation), ≤80 GiB before a write and ≤20 GiB per generation. Pilot RSS is capped at16 GiB. Historical checkpoint directories are never retired. Strict source-fingerprint validation remains: old checkpoints are not silently relabeled or migrated to changed source files.

Run commands from the repository root using the established `ridehailing-phd` environment:

```sh
python -B scripts/run_multi_episode_od_pilot.py primary
python -B scripts/run_multi_episode_od_pilot.py resume
python -B scripts/run_multi_episode_od_pilot.py recover
```

`primary` refuses existing run evidence. `resume` restores the latest verified checkpoint and runs only through episode2; metrics ahead of the checkpoint are preserved in a separate interrupted-evidence file before reconstruction. `recover` restores the episode1 milestone, performs the physical reset, and repeats only episode2's first slot for exact comparison. It does not extend the timeline.

## Evidence and limitations

`frozen_configuration.json`, `temporal_boundaries.json` and provenance manifests identify the approved scientific contracts and source versions. `slot_metrics.json` records actual optimizer updates, epsilon, losses/gradient norms, routing updates, reward and replay diagnostics. Per-episode request reconciliation and reset checks are saved separately. No prioritized replay, synthetic demand, client subsampling or architecture change is introduced.

Twenty focused tests passed before pilot execution; subsequent RNG, federation, evaluation-schedule and continuation-gate checks bring the total to **27 distinct passing tests, zero failures**. The evaluation-isolation test was additionally rerun after adding explicit optimizer rejection. Existing no-dispatch, Bellman, mixed-fleet and checkpoint tests were retained. Real-data recovery passed exactly. This experiment uses historical-average demand, not the later-selected Softplus CNN. Charging exposure and independent protected evaluation remain separate scientific requirements.


## Completed pilot results

| Metric | Episode1 | Episode2 |
|---|---:|---:|
| Eligible requests | 30,359 | 38,486 |
| Accepted | 8,354 | 9,864 |
| Successful assignments | 5,958 | 8,876 |
| Assignment revenue, USD | 133,576.496310 | 193,410.700636 |
| Supported OD learning reward, USD | 133,241.183333 | 192,963.616667 |
| Pricing optimizer updates | 128 | 128 |
| Ending epsilon | 0.940 | 0.875 |
| Routing optimizer updates | 76,148 | 72,948 |
| Ending cumulative federation round | 16 | 32 |
| Recorded charging events | 3 | 4 |

Source reconciliation: **70,106 rows =1,261 unchanged invalid-row exclusions +68,845 eligible requests**. Of the eligible population,36 used the approved unseen-OD fallback. Total assignment revenue **326,987.19694548374 USD** reconciles to **326,204.8 USD supported learning reward +782.39694548374 USD fallback revenue** (floating-point summation tolerance applies). Accepted-unmatched requests are2,396 and988 respectively; rejected requests are22,005 and28,622. No rejected or accepted-unmatched request contributes learning reward.

There were **149,096 genuine routing optimizer updates**,2,351,026 local sample presentations,32 equal-client NONPRIVATE federation rounds and256 pricing updates. The final epsilon is0.875, reflecting floor(256/10)=25 decrements. Historical linear-schedule configuration fields remain serialized for backward compatibility; the explicit `MASTER_UPDATE_STAIRCASE_V1` contract determines active exploration, including its0.1 floor.

Replay generated **306,304 transitions**, retained100,000 and evicted206,304 through unchanged FIFO semantics. All9,572 OD identities remain represented. Final retained replay is **97.319% zero-reward /2.681% positive-reward**. There were146,287 and145,291 zero-request OD-slot contexts in the respective episodes. Final age quantiles(minimum/median/P90/maximum) are1/6/10/11 half-hour slots, measured from each transition's slot-start identity, not its insertion time. These diagnostics do not imply learning convergence or justify replay pruning.

## Reset correction and deterministic recovery

An environment-RNG preservation gap was identified before the first physical reset. The attempt was interrupted after the slot8 checkpoint; uncommitted partial work was rolled back. Its log and initial configuration are preserved. `multi_episode_rng.py` wraps the physical reset and preserves `engine.request_rng`, `charging.rng` and `customer.rng`, in addition to the learning/global RNG handling. An advanced charging-RNG fixture verifies preservation rather than merely comparing unused seeds. No historical checkpoint was relabeled, and the existing slot8 checkpoint's source files remained unchanged by this wrapper addition.

Execution resumed at the saved boundary and completed the same two chronological episodes. At the physical reset, driver IDs/EV identities and profiles matched, the active pricing learner and routing hierarchy were retained, and231 passenger commitments plus one charging occupant were explicitly censored. They were not reported as completed. Logged charging-event counts are event records, not a claim of seven completed charging sessions.

A separate recovery process then loaded the episode1 terminal milestone, reproduced the physical reset, and repeated **only episode2 slot1**. Restored state, reset state, resulting runtime/replay/fleet/charging state, local/global routing weights and optimizers, pricing online/target weights and optimizer, RNG domains, pricing losses and gradient norms matched exactly. The recovered branch did not replace the authoritative episode2 terminal checkpoint. See `recovery_validation.json`.

## Resources and readiness

Committed slot execution, including updates and boundary checks, totaled **57.59 minutes**. This excludes checkpoint serialization, setup/recovery and the interrupted uncommitted work. The resumed process separately recorded47.71 minutes after loading its checkpoint; that is not the total task wall time. Peak RSS for the completed pilot process was **4.86 GB**. The two retained resumable checkpoints total **3.10 GB**; approximately222.76 GB disk space remained at final consolidation.

The continuation entry point is `scripts/continue_multi_episode_od.py`. It requires `--authorize-remaining-33`, an explicit checkpoint, and separate new output/model directories; it refuses to overwrite the pilot. It implements the episode7/14/21/28/35 development-evaluation calls, best-score selection, milestone retention and the approved plateau/budget stop rules. **It was not launched.** Its authorization gates were tested; later real-data evaluation milestones and long-horizon checkpoint/resource growth are not established by this two-episode experiment.

For an interrupted pilot, the exact recovery command remains `python -B scripts/run_multi_episode_od_pilot.py resume`, which stops at episode2. The independent validation command is `python -B scripts/run_multi_episode_od_pilot.py recover`. Do not rerun either merely to reproduce this report. The authoritative continuation state is `models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42/latest`, resolving to the episode2 slot16 generation; `milestone` resolves to episode1 slot16.

**Readiness:** the bounded orchestration gate passed. Continuation requires a separate explicit launch instruction and continued resource/invariant enforcement. This is not evidence of policy convergence, CNN superiority, operational weather availability, privacy, or continuous-horizon charging performance. No March13–16 real-data evaluation or March17–31 evaluation was executed. Historical results/models and the previous exploration contract were preserved. `implementation_sources.json` lists changed/new implementation files and fingerprints; `frozen_configuration.json` identifies the executed scientific settings.
