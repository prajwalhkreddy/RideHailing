# Frozen chronological hierarchical experimental protocol

**TEMPORAL_PROTOCOL_READY = YES**

The canonical configuration is `config/final_temporal_protocol.json`. All boundaries below are inclusive half-hour slot starts, using the existing timezone-naive project timestamp convention without conversion.

| Role | Start | Last slot start | Slots |
|---|---|---|---:|
| CNN training | 2026-01-01 00:00 | 2026-02-28 23:30 | 2,832 |
| Hierarchical RL development/training | 2026-03-01 00:00 | 2026-03-15 23:30 | 720 |
| Integration/development exclusion | 2026-03-16 00:00 | 2026-03-16 23:30 | 48 |
| Final hierarchical evaluation | 2026-03-17 00:00 | 2026-03-31 23:30 | 720 |

The four intervals are contiguous, disjoint and contain exactly 4,320 slots. March 1–15 was originally CNN validation; it is intentionally reused for hierarchical RL development/training, not final hierarchical evaluation. March 16 is excluded because integration/debugging and one DQN update already occurred there.

March 17–31 is reserved prospectively for final hierarchical inference/logging. It must not influence scaling, priors, labels, replay training, weights, checkpoint selection, thresholds, hyperparameters, features or methodology decisions. This designation is for the hierarchical experiment; it does not claim those dates were never examined in prior CNN evaluation reports. No such reports were re-evaluated here.

## Epoch-200 March 1–15 forecasts

Published separate artifact:

`data/processed/cnn_jan_mar_2026_3km_30min/j_hat_epoch200_3km_142grids_mar01_15_2026_horizon30min.parquet`

Fields: `forecast_timestamp`, `Grid_ID`, `predicted_demand` (J_hat). Exactly **102,240 rows / 720 timestamps / 142 grids**. All combinations exist once; timestamps match the full required half-hour sequence. Predictions are finite/nonnegative without clipping or post-processing. The saved CNN grid mapping matches the active mapping exactly.

Inference used `models/cnn/jan_mar_2026_3km_30min_continued/best.keras`, whose continuation metadata identifies best epoch 200, and the unchanged saved `X_validation.npy` / `forecast_timestamp_validation.npy`. Existing preprocessing, seven channels and 30-minute target convention were reused without fitting. The checkpoint hash remained unchanged. No observed demand target was written into the runtime forecast artifact.

`forecast_validation.json` records checkpoint/output hashes and validation. Existing March 16–31 forecast artifacts were not overwritten. The runtime snapshot adapter selects this new artifact only for the configured March 1–15 interval and retains the existing artifact outside it, with the same fail-closed timestamp/grid checks.

## Downstream availability

All ten categories are AVAILABLE; exact paths and checked coverage are in `training_input_availability.json`:

- Requests: existing intact January empirical-trip source mapped to the final domain, sampled using forecast counts. Existing unsupported-origin reporting is retained; availability does not assert every origin has empirical support.
- J_hat: the complete new artifact above.
- P_base: frozen TLC-fare weather/half-hour lookup and existing hierarchical fallback resolve every weather/period pair present during March 1–15.
- Destination popularity: complete 102,240-row coverage, available after its existing pre-March cutoff.
- Weather/calendar: complete required runtime weather coverage; calendar from timestamps. The inherited retrospective observed-weather contract remains unchanged and is not represented as an archived ex-ante weather forecast.
- Supply: final 142-grid seed42 initialization reference; runtime uses the existing EV fleet initializer.
- Operational priors: verified 142-grid fare priors with January 25 18:30 cutoff, before March starts; F_hat_0/H_hat_0 remain zero.
- Profiles: 5,000 explicit 10-minute H_i_max values and matching persisted runtime fields.
- Stations: 15 existing stations with valid final grid mapping.
- Topology: existing masks/distance/travel artifacts; 1,278 long-format mask rows represent nine actions for each of 142 grids.

## Minimal temporal enforcement

`src/simulation/temporal_protocol.py` provides aligned-time validation, `training_update_allowed`, final-evaluation identification, a raising update guard and checkpoint quarantine validation. Training permission ends inclusively at March 15 23:30; March 16 and later are rejected. Final-evaluation mode rejects updates regardless of timestamp.

The final runner invokes the shared guard **before any slot mutation** whenever pricing training or routing/FedAvg updates are requested. It does not record training replay transitions from excluded/evaluation slots. Inference-only slots can retain their logging/state progression without weight updates. No training loop, optimizer, architecture or frozen coefficient was redesigned. Future training entry points must use the same guard for their data timestamps; final-evaluation observations must never be used for tuning or development.

## March-16 checkpoint quarantine

`models/pricing_dqn/first_short_hierarchical_20260316_0000_0200_seed42/` is classified externally in the canonical config and `integration_checkpoint_status.json` as:

- SHORT_HIERARCHICAL_INTEGRATION_CHECKPOINT
- NOT_FINAL_TRAINING_CHECKPOINT
- DO_NOT_CONTINUE_FOR_FINAL_EXPERIMENTS

The existing checkpoint files were neither overwritten nor deleted; their hashes are recorded and tested. Final-runner initialization rejects this checkpoint as a final-experiment starting point. Final pricing training must restart from reproducible seed42 initialization or a later explicitly approved initialization contract. Ordinary low-level checkpoint inspection remains possible; the final runner enforces the quarantine.

## Validation and next step

Seven focused tests pass: exact boundaries/counts/no overlap, training/evaluation guards, pre-mutation runner rejection, full forecast coverage and runtime selection, checkpoint quarantine/integrity and forecast provenance/input availability. No simulation episode, CNN/routing/DQN training, hyperparameter search or broad test suite ran.

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B -m unittest tests.test_final_temporal_protocol
```

The next separately authorized task is generation of simulator-derived routing experiences on March 1–15, followed by routing/FedAvg work. It was not executed here.
