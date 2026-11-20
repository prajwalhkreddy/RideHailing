# Versioned final-Softplus causal CNN experiment

One authorized fresh seed-42 run completed. **The activation correction modestly improves prediction errors over ReLU but does not recover baseline performance. No promotion or second variant is authorized by these results.**

## Minimal correction and provenance

`src/demand/softplus_cnn.py` reuses the unchanged historical builder, replacing only `conv_3.activation` with Softplus before training. Hidden convolutions, seven-channel order, 16×16 geometry, 142-grid mask, count targets, masked MSE and Adam 0.001 remain identical. A focused test confirms identical fresh seed-42 weight arrays between variants and unchanged hidden-layer configurations. The historical ReLU model is not loaded for initialization and remains unchanged.

`scripts/train_softplus_research_cnn.py` reuses the original causal trainer with separate output/model paths and variant metadata. Preflight requires exact agreement with the preceding experiment's selected demand/weather hashes, grid/mask and generated X/Y hashes. The original source files remain unchanged. No large training arrays are duplicated on disk.

## Protocol and gradient validation

Training: Jan1–Feb28, 2,830 eligible slots. Validation: March1–15, 718 slots. March16: 48 development-only slots, not a final test. March17–31 local targets are protected and never accessed. Causal expanding histories and the assumed 120-minute weather-persistence protocol are unchanged. UTC elapsed-time handling excludes nonexistent March8 civil slots without losing demand.

Adam 0.001; batch 64; chronological batches; seed42; deterministic operations; cap100 epochs; validation patience10. All epochs include finite-loss/weight checks. Minimum validation checkpoint is epoch **42**, with stopping at **52**. Selection precedes March16 diagnostics.

Tests establish finite nonnegative shape-compatible outputs; the actual final Softplus propagates negative-preactivation gradients for positive targets in a bounded fixture (z=−2), while invalid-cell gradients remain zero. The historical builder still uses ReLU. Saved/reloaded activation identity and predictions match. This proves removal of the mathematical hard-zero branch, not uniformly large derivatives: very negative Softplus arguments can still produce negligible gradients and numerical underflow. No loss change or hidden-layer redesign was made.

## Identical-population comparison

| Population/model | MAE | RMSE | Count bias % | Exact-zero % | Positive targets predicted <0.01 requests % |
|---|---:|---:|---:|---:|---:|
| Validation ReLU | 7.107571 | 26.145924 | −28.4579 | 92.7302 | 88.4136 |
| Validation Softplus | 7.013677 | 26.027186 | −27.4590 | 9.9906 | 86.1753 |
| Validation historical average | 3.518426 | 18.226779 | −9.2762 | 33.1339 | 1.9837 |
| March16 ReLU | 9.167995 | 39.863315 | −54.5738 | 95.8480 | 91.3331 |
| March16 Softplus | 8.956793 | 39.232116 | −53.1546 | 5.5458 | 89.1585 |
| March16 historical average | 5.085002 | 29.771590 | −22.0437 | 33.1866 | 2.0485 |

MAE/RMSE units: requests/grid/30 minutes. Validation N=101,956; development N=6,816. Saved target timestamps, grid identities, actual values and baseline predictions match the prior run exactly. Near-zero means <0.01 requests solely for this diagnostic; it is not a cleaning or exclusion rule. Remaining exact zeros are compatible with floating-point underflow and do not imply a ReLU was retained; per-cell pre-activation analysis was not repeated here.

`three_way_comparison.csv` also reports Jan–Feb-ranked high/low grids, actual-city-demand top-quartile peak/off-peak groups, city totals, absolute aggregate bias, zero rates and positive-target denominators for all three methods. These descriptive groups do not affect training or model selection. `metrics.csv` and `city_metrics.csv` contain original selected-model evaluation, including training. `charts/loss_comparison.png` shows both recorded loss histories.

## Export, tests and preservation

All 766 validation/development forecast intervals pass the existing UTC OD metadata validator. `forecasts.parquet` and `forecast_contract.json` bind nonnegative fractional predictions to timestamps, weather assumptions, grid/mask identity, preprocessing and model fingerprints. Selected-checkpoint reload predictions are exact. These forecasts are research outputs only: March1–15 model-selection lineage forbids promotion into the February28-cutoff March12 prospective experiment.

**32 focused tests passed, zero failed (24.487s).** Tests cover Softplus gradients, output masking, fresh initialization equivalence, ReLU compatibility, reload, causal history, tensors, weather, DST and UTC OD interfaces. An existing untrained-model test emits its known optimizer-variable warning; trained checkpoint reload succeeds. Historical register: 2,279 paths checked, zero changes. No pricing, routing, federation, sensitivity, historical results or checkpoints were altered.

## Reproduction and files

```
python -B -m unittest tests.test_softplus_cnn tests.test_persistence_weather tests.test_cnn_causal_timing tests.test_cnn_model tests.test_cnn_tensors tests.test_utc_od_runtime -q
python -B scripts/train_softplus_research_cnn.py
python -B scripts/report_softplus_research_cnn.py
```

The training entry point refuses to overwrite an existing attempt. Model: `models/cnn/causal_persistence_120min_2026_seed42_softplus_v1/best.keras`. Configuration, selected-row and source hashes, sample timing, history, metrics, comparison, forecasts, logs and validation JSON are in this directory. No repeated training is needed to inspect the results.

Storage maintenance is documented separately at `results_v2/repository_maintenance/2026-11-18_safe_cleanup/README.md`: only verified bytecode was deleted. The original ReLU checkpoint and all research evidence were retained.

## Limitations and next single task

Weather publication/vintage remains assumed, not verified operational availability. Validation-selected historical forecasts are not proof of prospective model availability. March16 is reused development data. Softplus reduces hard zeros but leaves severe near-zero behavior and substantial baseline-relative error; no superiority claim is justified.

Recommended next single task: a bounded, no-training diagnosis of the corrected checkpoint's remaining near-zero outputs and feature scales on a small provenance-matched batch. Do not change architecture, run a new training variant or initiate DQN training without a separate decision.
