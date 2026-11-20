# Corrected causal-research CNN: single bounded training experiment

**Completed one experiment. CNN underperforms the historical-average baseline; it is not promoted over that baseline.** Best checkpoint: epoch 50; early stopping: epoch 60. No DQN/routing training or behavior changes occurred.

## Data and information contract

The inherited split is January 1–February 28 training (2,830 eligible half-hour samples), March 1–15 validation (718), and March 16 **development-only** evaluation (48). Two January no-history samples are excluded explicitly. March 17–31 New York evaluation targets were not loaded, trained on, tuned on or evaluated. A final test requires separate explicit release of that protected period under a frozen evaluation protocol. March 16 is not an independent final test and has prior development usage.

Inputs are `(N,7,16,16)`, outputs `(N,1,16,16)`, with 142 valid cells. Channels: DayOfWeek, Hour, PeriodWithinHour, WeatherType, Temperature, WindSpeed, HistoricalAverageDemandDistribution. Targets remain requests in `[target_start,target_end)`, 30 elapsed minutes. Issuance and feature cutoff are 30 elapsed minutes before target start. Expanding history uses only completed Jan–Feb intervals ending at or before issuance; held-out labels never update history or scaling. Feature warm-up and scaling remain exactly as implemented in the corrected builder.

Weather uses `CNN_OBSERVATION_PERSISTENCE_ASSUMED_AVAILABILITY_V1`: latest complete UTC-labeled observation with assumed availability (observation +120 minutes) no later than issuance. Temperature is Celsius, wind km/h. This is an **unverified publication-lag/persistence assumption**, not an archived weather forecast or verified operational availability. Provider revisions/model filling remain unresolved. Demand availability at interval close is also assumed.

March 8 nonexistent 02:00/02:30 New York labels are excluded: 284 grid rows and zero demand. No civil slots are synthesized. The full permitted prefix retains 9,140,364 target requests. UTC exports preserve elapsed-time boundaries; late March 16 local targets naturally have March 17 UTC timestamps and do not access March 17 local evaluation labels.

`configuration.json` records hashes of selected permitted demand/weather rows, grid mapping, generated tensors and preprocessing source. Full protected-period datasets were not read for content hashing. `sample_timing.csv` records all eligibility, issuance, source weather and target times. Tensors were constructed in memory rather than duplicated on disk.

## Model and training

Reused `src/demand/final_cnn.py:build_model`: 7→14→7→1 convolutional channels, three 3×3 same-padding ReLU layers and valid-grid output mask. Adam 0.001; batch size 64; chronological batches without shuffle; valid-cell MSE; maximum 100 epochs; validation patience 10; seed 42; deterministic TensorFlow operations; four intra-op/two inter-op threads. No architecture search, hyperparameter search or second training attempt.

Best validation MSE: **683.609344**. At epoch 50, streaming training MSE was **630.361206**; epoch 60 streaming training MSE was **594.513550**. Streaming loss accumulates across updates and differs from evaluation of a fixed selected checkpoint. Selected-checkpoint training MAE/RMSE: **6.911756 / 26.210067**. Every epoch was checked for finite losses and weights. The checkpoint selection finished before March 16 evaluation.

## Identical-population evaluation

Units below are requests/grid/30 minutes. All 142 valid grids are included; invalid raster cells are excluded.

| Population | Grid-time N | CNN MAE | CNN RMSE | Historical-average MAE | Historical-average RMSE |
|---|---:|---:|---:|---:|---:|
| Validation March1–15 | 101,956 | 7.107571 | 26.145924 | 3.518426 | 18.226779 |
| Development March16 | 6,816 | 9.167995 | 39.863315 | 5.085002 | 29.771590 |

Baseline uses the identical causal grid/weekday/half-hour mean, then grid/half-hour and grid fallbacks. It is reconstructed in count units from the historical channel and its expanding training-only SD; its precision reflects the float32 feature representation. It does not fit held-out targets.

City-total validation MAE/RMSE: CNN **780.993 / 954.333**, baseline **333.551 / 475.435**. Development: CNN **1300.152 / 1505.501**, baseline **574.164 / 812.125**. CNN mean city bias is negative: −772.242 validation and −1300.152 development requests/slot.

High/low groups are the five highest/lowest grids by Jan–Feb mean demand, fixed without using validation rankings. High grids: 27,37,28,46,36; low grids: 57,120,132,140,141. In validation, high-grid CNN/baseline RMSE is 125.325/94.841; low-grid RMSE 0.226748/0.029282. Grid-level diagnostics and development results are persisted. Comparisons show no CNN superiority.

## Forecast export and downstream compatibility

`forecasts.parquet` contains 108,772 rows across 766 validation/development intervals, with nonnegative fractional predictions, actual/baseline values, Grid_ID, UTC issuance, target start/end, feature cutoff, source observation and assumed availability. `forecast_contract.json` binds the forecast file to checkpoint, preprocessing sources, channel order, weather protocol, mask and exact grid mapping hashes.

All 766 intervals passed the existing `src.simulation.utc_od_inputs.forecast` checks, including the March 8 DST transition. The accompanying metadata must be carried with the forecasts; this does not authorize automatic replacement of the current runtime forecast or an operational-readiness claim. Existing historical checkpoints and oracle tensors were not relabeled.

The checkpoint uses March1–15 validation selection and **is not cutoff-valid for the separate February28-cutoff March12 prospective experiment**. Interface compatibility does not erase fitted/model-selection lineage. This is retrospective chronological research evaluation: causal feature timestamps do not establish that the selected checkpoint existed at each historical issuance. In particular, March validation predictions from the ultimately selected model are not prospective out-of-sample operational forecasts.

## Validation, reproduction and preservation

29 focused tests passed, zero failed (26.213 seconds): persistence weather, causal timing, CNN model/tensors and UTC OD runtime. They cover deterministic preprocessing, future/self/held-out exclusion, weather availability, DST, shape/mask and interface rejection. The selected trained checkpoint was loaded twice and produced exactly identical predictions on the reload fixture. No second training run was used to claim empirical cross-run training equivalence.

An existing untrained-model test emitted an optimizer-variable loading warning; the trained checkpoint loaded without that warning. Historical preservation checked 2,279 paths by size/mtime and existing pipeline source hashes; no changes were found. These are metadata preservation checks, not a fresh full historical content audit.

Commands (training refuses to overwrite an existing attempt):

```
python -B scripts/train_causal_research_cnn.py
python -B scripts/report_causal_research_cnn.py
python -B -m unittest tests.test_persistence_weather tests.test_cnn_causal_timing tests.test_cnn_model tests.test_cnn_tensors tests.test_utc_od_runtime -q
```

## Files and next task

- `configuration.json`, `preflight.json`, `sample_timing.csv`: protocol, provenance and eligibility.
- `training_history.csv`, `training.log`, `metrics.csv`, `validation.json`: single-run training/evaluation evidence.
- `grid_diagnostics.csv`, `high_low_diagnostics.csv`, `city_metrics.csv`: spatial and aggregate errors.
- `forecasts.parquet`, `forecast_contract.json`: explicit research forecast export.
- `charts/`: actual/predicted/baseline development comparisons and learning curves.
- `tests.log`: bounded test result.
- `models/cnn/causal_persistence_120min_2026_seed42_v1/best.keras`: new selected checkpoint; adjacent metadata records configuration and lineage.

Recommended next single task: a bounded **no-training residual/underprediction diagnosis** of this checkpoint versus the causal historical baseline, using existing validation evidence. Do not promote this model, change architecture, release protected test labels or initiate DQN training from this result alone.
