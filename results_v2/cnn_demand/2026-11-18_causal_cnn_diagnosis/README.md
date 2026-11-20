# Causal CNN underperformance: bounded saved-artifact diagnosis

**Classification B — MODEL GENERALIZATION / BIAS.** The primary demonstrated failure mode is widespread zero-valued predictions and systematic underprediction, including suppressed high-demand peaks. No specific correctness defect is established in the inspected preprocessing, masking, units or metric calculation. This does not establish the causal reason for the learned zero-heavy mapping. No retraining, inference, tensor regeneration, simulation or protected-period access was performed.

## Metric reconciliation and population

Saved `forecasts.parquet` contains the CNN, baseline and actual count on the same row. Unique UTC target/Grid_ID pairs, exactly 142 grids per target, finite nonnegative values, integer actual counts, issuance/target boundaries and assumed weather availability all pass. Recomputed float64 MAE/RMSE match recorded results within 1e-10.

| Population | N | CNN MAE / RMSE | Baseline MAE / RMSE |
|---|---:|---:|---:|
| March1–15 validation | 101,956 | 7.107571 / 26.145924 | 3.518426 / 18.226779 |
| March16 development | 6,816 | 9.167995 / 39.863315 | 5.085002 / 29.771590 |

Units are requests/grid/30 elapsed minutes. March16 is development-only, not an independent final test. UTC timestamps falling on March17 correspond only to late March16 New York targets. No March17–31 local targets were read. The exact saved forecast hash, checkpoint hash and preprocessing source hashes match the training manifest.

## Bias and zero predictions

| Measure | Validation | March16 development |
|---|---:|---:|
| Mean actual | 19.110077 | 16.777289 |
| Mean CNN | 13.671755 | 7.621289 |
| Mean baseline | 17.337395 | 13.078950 |
| CNN aggregate count bias | −554,469.503 | −62,407.292 |
| CNN count bias % | −28.4579% | −54.5738% |
| Baseline count bias % | −9.2762% | −22.0437% |
| CNN under / over predictions, all cells | 44.3201% / 3.8222% | 46.4495% / 0.2201% |
| CNN zero predictions, all cells | 92.7302% | 95.8480% |
| Positive-demand observations predicted zero | 41,672 / 47,133 | 2,898 / 3,173 |
| Underprediction among positive-demand observations | 95.8713% | 99.7794% |

All-cell underprediction percentages are diluted by correctly zero/zero cells. City demand is underpredicted in 98.3287% of validation slots and every development slot. City MAE/RMSE are 780.993/954.333 validation and 1300.152/1505.501 development, versus baseline 333.551/475.435 and 574.164/812.125.

Positive-demand quantiles are calculated separately from zeros to avoid tied-zero percentile bins. The top 1% positive-demand band contributes approximately 51.6% of validation CNN squared error and 56.9% of development squared error. Its mean errors are −202.209 and −401.093 requests/grid/slot. Exact bounds, denominators and all bands are in `error_breakdown.csv`.

Peak slots are a descriptive, outcome-defined top quartile of actual city demand within each split, not a fitted predictor or tuning rule. Peak CNN/baseline RMSE: 38.128/28.015 validation, 63.046/51.900 development. Off-peak: 20.639/13.445 and 28.175/16.850. The deficit occurs in both regimes.

## Spatial peaks and baseline degradation

Training-selected high-demand grids (27,37,28,46,36) have validation CNN/baseline RMSE 125.325/94.841; development 204.711/156.528. Low-demand grids (57,120,132,140,141) have validation RMSE 0.226748/0.029282. The low group has essentially no development demand, so aggregate relative errors there are not meaningful.

At each slot's five actual highest-demand locations, validation totals are 1,456,784 actual, 1,256,057.588 CNN and 1,306,264.262 baseline. Development totals are 84,554, 49,376.952 and 63,331.000. Mean spatial maxima are 733.481 actual versus 607.763 CNN in validation, and 628.021 versus 367.080 in development.

These demonstrate peak suppression, but **do not prove spatial over-smoothing**: the CNN also erases many positive-demand cells rather than simply spreading peaks over neighbours. The saved predictions do not distinguish convolutional smoothing, ReLU inactivity, optimization behavior or feature-scale sensitivity.

The historical feature reproduces the baseline **by construction**: the trainer multiplies channel 7 by its corresponding historical demand SD. The trained CNN degrades an already informative supplied feature on both MAE and RMSE. There is no residual/identity constraint requiring the CNN to preserve that feature; this is a modeling choice, not an implementation defect.

## Feature, target and numerical checks

Source references:

- `src/demand/causal_timing.py:build_oracle`: fixed channel order, expanding history and scaling, target raster placement.
- `src/demand/persistence_weather.py:select_weather/build_persistence`: prior eligible complete observations replace oracle weather before tensor construction.
- `src/demand/final_cnn.py:build_model/MaskedMSE`: convolution/output ReLU, 142-cell loss mask.
- `scripts/train_causal_research_cnn.py:main`: masks, split eligibility, inverse-scaled baseline, model selection and export.

Seven channels in order: weekday/6; hour/23; half-hour indicator; Meteostat category/27; standardized temperature (Celsius source); standardized wind (km/h source); historical demand divided by expanding demand SD. Weather z-scores use previously available Jan–Feb weather moments. The same builder serves every split, with held-out labels excluded from moment/history updates.

History only incorporates Jan–Feb intervals ending at or before issuance, with grid/weekday/half-hour → grid/half-hour → grid fallback. Baseline eligibility is therefore causal under the assumed immediate demand availability. Its inverse scale uses the exact recorded number of eligible training slots. Source inspection confirms no held-out labels enter baseline fitting. This is a code/provenance check, not a newly regenerated independent baseline.

Demand targets are **unscaled original counts**. CNN outputs require no inverse transform. Only the historical feature is inverse-scaled for baseline comparison; missing CNN inverse normalization is not the explanation. Input scale changes over early training and freezes after eligible Jan–Feb history is exhausted. This may complicate learning, but no train/validation branch mismatch is evident and its contribution is not quantified.

All layers including the output use ReLU, so exact zeros are permitted; valid-cell zeros are not padding. The loss averages squared error over the 142-cell mask; invalid cells remain zero and are absent from saved evaluation rows. Weather selects the latest complete finite observation; it does not backfill future observations. No-history training samples are explicitly excluded. Forecasts target the original interval, not a shifted label. March8 nonexistent civil slots were quarantined with zero demand in the existing preflight.

The causal input tensors and per-sample scaling arrays were not persisted. Their distributions, activation pre-values and gradient histories cannot be inspected from this output package without additional reconstruction/instrumentation. No such experiment was performed.

## Training and checkpoint consistency

Epoch 50 is the recorded validation minimum: MSE 683.609344, equal to the reproduced validation RMSE squared. Its streaming training MSE is 630.361206. At epoch 60 training MSE improves to 594.513550 while validation MSE is 686.107763; ten non-improving epochs trigger stopping. This supports a limited generalization plateau, not a claim that severe overfitting explains the full gap. Even the selected-checkpoint training metrics favor the baseline (CNN RMSE 26.210067 versus 24.911639).

Checkpoint bytes match the saved selected-model hash. Existing exact reload evidence is retained. Predictions were not regenerated from weights because the inputs were not saved; checkpoint-to-export consistency rests on matching hashes, recorded selection and the inspected trainer flow.

## Recommendation and preservation

No numerical code correction is justified by this evidence. **Next single action:** a separately authorized, bounded activation/gradient diagnostic of the selected checkpoint on a small, deterministically reconstructed permitted sample, with exact preprocessing provenance. Inspect pre-output activations and gradients at positive-demand/zero-prediction cells before selecting any change to output activation, initialization or scaling. Do not presume dead ReLUs or change architecture merely because the baseline wins.

No tests were added because no correctness gap requiring a regression test was identified. The diagnostic's assertions reconcile metrics, population, timestamps, values and hashes. Existing training results, model checkpoints and production sources remain unchanged. Only this separate diagnostic directory was created.

Evidence: `diagnose.py`, `metric_bias_reconciliation.csv`, `error_breakdown.csv`, `spatial_peak_diagnostics.csv`, `validation.json`. Reproduce with the project Python environment: `python -B results_v2/cnn_demand/2026-11-18_causal_cnn_diagnosis/diagnose.py`.
