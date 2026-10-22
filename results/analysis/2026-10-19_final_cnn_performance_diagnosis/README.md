# Focused final CNN performance diagnosis

## Decision

**D. CNN_VALID_BUT_HISTORICAL_BASELINE_SUPERIOR.** The initial run was **TRAINING_TRUNCATED**, so the single authorized continuation was performed from the saved epoch-100 checkpoint, including its Adam optimizer state. No architecture, preprocessing, data, split, learning rate, batch size, seed methodology or loss changed. The continuation improved performance but the TRAIN-only historical baseline still wins. Stop; no further run or hyperparameter search is justified by this task.

The CNN module can be closed for the approved implementation and bounded diagnostic experiment. This is **not a claim of mathematical convergence**: best validation epoch is again at the cap, epoch **200**, after **100 additional epochs**. Retain the CNN as the roadmap model and historical average as a strong evaluation baseline. No claim that CNN is empirically best is supported.

## Fairness and leakage gate

Both original CNN and historical-average errors were reconstructed on exactly **768 TEST timestamps × 142 valid grids = 109,056 observations**, with the same observed targets, masks and pooled MAE/RMSE/R² definitions. Metrics reproduce the persisted original comparison. No missing or duplicate grid/timestamp pairs occur.

Independent regrouping from the source January–February rows reproduces the historical lookup, both fallback tables, seasonal baseline and scalers. Replacing **all held-out demand, temperature, wind and weather-code values** with a sentinel leaves the fitted lookup/fallbacks/scalers unchanged. Every saved TRAIN/VALIDATION/TEST X/Y tensor and timestamp array reproduces exactly. No validation or test target enters fitting. The existing weather source required no imputation. No preprocessing, leakage or alignment defect was found.

The known retrospective-weather qualification remains: forecast-time weather is observed historical weather, not an archived ex-ante forecast. This does not leak TEST targets into the historical baseline or fitted transformations, but live forecasting needs weather available at issuance. Training examples use a lookup fitted on the entire TRAIN partition, as specified; this is not an online expanding-window evaluation within TRAIN.

## Training history

| epoch | train_masked_MSE | validation_masked_MSE |
|---|---|---|
| 1 | 17379.019531 | 9251.830560 |
| 10 | 1767.337158 | 1477.185050 |
| 25 | 690.122864 | 696.351196 |
| 50 | 544.075195 | 583.834331 |
| 75 | 476.917725 | 557.996898 |
| 90 | 437.847015 | 546.271466 |
| 100 | 395.747620 | 531.823444 |

Lowest original validation MSE: **epoch 100**, at the configured maximum. It improved at every epoch during the final 20-epoch interval. Change definitions use epoch 90→100 (ten optimizer epochs) and 80→100 (twenty optimizer epochs):

- Last 10: **546.271466 → 531.823444**, change **−14.448022 / −2.644843%**.
- Last 20: **554.133737 → 531.823444**, change **−22.310293 / −4.026157%**.

Training MSE also fell. This is evidence of an unfinished optimization run rather than an overfit validation reversal. Continuous improvement and the roughly 4% final-20 validation reduction were considered materially improving; the recorded >1% diagnostic gate was stated before continuation and is not a tuned model hyperparameter.

## TRAIN numerical ranges — valid cells only

| variable | min | max | mean | std |
|---|---|---|---|---|
| DayOfWeek | 0.000000 | 1.000000 | 0.508475 | 0.328243 |
| Hour | 0.000000 | 1.000000 | 0.500000 | 0.300965 |
| PeriodWithinHour | 0.000000 | 1.000000 | 0.500000 | 0.500000 |
| WeatherType | 0.037037 | 0.777778 | 0.123064 | 0.125612 |
| Temperature | -2.945047 | 2.657154 | 0.000000 | 1.000000 |
| WindSpeed | -1.477375 | 3.744137 | 0.000000 | 1.000000 |
| HistoricalAverageDemandDistribution | 0.000000 | 16.327017 | 0.200419 | 1.000000 |
| target | 0.000000 | 1742.000000 | 17.599723 | 89.757364 |
| historical_lookup_unscaled | 0.000000 | 1433.750000 | 17.599723 | 87.814572 |

The historical plane has unit population SD after division by **87.814568**, retains a maximum of **16.327017**, and is not flattened. Its unscaled mean matches the TRAIN target mean. Weather/time planes do not dominate numerically. The target remains raw request counts (SD **89.757364**); features are normalized by design. Learning the output amplitude is required but this is not an accidental target-unit mismatch or excessive historical-feature normalization.

## Historical plane and mask integrity

The seventh plane exactly matches the saved lookup after its specified float32 scaling for all samples, with explicit first/middle/last checks per partition in `channel_integrity.csv`. Grid/raster placement, weekday and half-hour-of-day are correct; no temporal or spatial shift exists. Forced missing-key fixtures verify fallback to same-grid/same-half-hour TRAIN mean, then same-grid overall TRAIN mean, then zero without history. The actual dense TRAIN data cover the primary keys.

For batch size B the loss is:

`(1/B) * sum_b [sum_(r,c) mask[r,c] * (prediction-target)^2 / 142]`.

The mask broadcasts as `[1,1,16,16]`; all **142 valid** and **114 invalid** positions are accounted for. Setting invalid-cell errors to 99,999 does not change a unit valid-cell loss. The invalid-cell gradient is exactly zero; the two-example unit-error fixture gives valid gradients `1/142`, consistent with batch reduction. Validation and test metrics select the same 142 cells rather than averaging padded zeros.

## Actual checkpoint and ReLU behavior

The loaded checkpoint is exactly **7→14→7→1**, three **3×3**, stride-1, same-padded ReLU convolutions with external `[B,7,16,16]→[B,1,16,16]`; the output mask matches the saved mask. The original Adam checkpoint restored **4,500 optimizer steps**, learning rate0.001. Continued checkpoint optimizer steps are **9000**. No optimizer reset or random-weight restart occurred.

The original CNN predicts exactly zero on **81.508583%** of valid TEST cells, including **79.286705%** of positive-target cells. Actual zero-demand cells constitute **53.721024%** of TEST observations. This excessive zero-floor behavior is a substantive optimization symptom, not a mask error. Inspection of final-convolution preactivations on first/middle/last TRAIN samples confirms negative/nonpositive activations clipped by the required final ReLU. Positive-target zero-activation shares on those samples: original **79.646%**, continued **37.611%**. Full TEST positive-target zero share after continuation is **43.967%**.

ReLU has zero derivative in negative preactivation regions, so it can suppress these predictions, but the model is not globally dead and continuation substantially reduces zero output. The required architecture is implemented correctly. No alternative activation or residual architecture was tested, so do not claim ReLU alone causally explains the performance gap.

## Prediction behavior and spatial errors

Original CNN mean/total: **14.856740 / 1,620,216.636** versus observed **18.157497 / 1,980,184**; ratio **0.818215**, correlation **0.976415**. Historical mean/total: **17.191064 / 1,874,788.653**; ratio **0.946775**, correlation **0.986279**.

After continuation CNN mean/total: **17.016261 / 1,855,725.400**; ratio **0.937148**, correlation **0.981014**. Separate CSVs contain all original/continued summaries.

`original_demand_quantile_errors.csv` and its continued counterpart separate zero demand, then tied empirical positive-demand quantiles at 0/25/50/75/90/95/99/100%. Band edges are explicitly reported; they are descriptive TEST groupings, not fitting decisions.

- At observed zero demand, original CNN mean prediction/MAE is **0.590780**, versus historical **0.238301**: some zero cells are overpredicted.
- Positive low/middle demand is generally **underpredicted**, not overpredicted. For observed counts 17–53, observed mean **28.179487**, CNN **7.490204**, historical **25.488487**.
- The top positive-demand percentile has observed mean **1001.401980**, CNN **901.408599**, historical **894.273159**. CNN still has worse error there, but its mean underprediction is not worse than the baseline's in this band.
- Mean spatial maximum: observed **700.092468**, original CNN **637.106812**, historical **638.604309**; continued CNN **644.406982**. Peaks are attenuated, but the similar historical peak attenuation means **excessive peak smoothing alone does not explain the CNN gap**.

The evidence principally supports incomplete fitting and broad low/mid-demand suppression, with positive-target zero-floor behavior. MSE emphasis on large errors and the lack of a direct historical-baseline identity path are plausible contributing mechanisms, not isolated causal findings. No bug in the historical channel was found.

### Ten largest improvements: original CNN minus historical MAE

| Grid_ID | CNN_MAE | baseline_MAE | difference |
|---|---|---|---|
| 42 | 0.300781 | 0.457303 | -0.156521 |
| 33 | 0.210938 | 0.332628 | -0.121691 |
| 32 | 0.473958 | 0.577980 | -0.104022 |
| 25 | 0.121094 | 0.218515 | -0.097421 |
| 126 | 0.183609 | 0.279966 | -0.096357 |
| 41 | 0.522135 | 0.611889 | -0.089753 |
| 26 | 0.187500 | 0.274541 | -0.087041 |
| 18 | 0.201259 | 0.276313 | -0.075054 |
| 69 | 0.598777 | 0.645833 | -0.047057 |
| 127 | 0.232812 | 0.275463 | -0.042651 |

### Ten largest degradations

| Grid_ID | CNN_MAE | baseline_MAE | difference |
|---|---|---|---|
| 59 | 39.604599 | 9.167228 | 30.437371 |
| 20 | 22.094900 | 4.641819 | 17.453082 |
| 46 | 67.667061 | 51.808323 | 15.858738 |
| 30 | 23.138712 | 7.980234 | 15.158478 |
| 45 | 21.423073 | 6.689381 | 14.733692 |
| 40 | 21.982611 | 8.019170 | 13.963441 |
| 58 | 20.624237 | 7.554235 | 13.070002 |
| 31 | 20.661850 | 7.647768 | 13.014081 |
| 74 | 15.320096 | 4.308901 | 11.011195 |
| 47 | 17.003695 | 6.390299 | 10.613395 |

Original CNN improves **16 grids**, degrades **125**, with **one tie**. Six of the ten largest degradations intersect Manhattan taxi-zone polygons. Manhattan-intersecting cells contribute **47.717165%** of summed positive per-grid MAE excess; the highest quartile of grids by TEST mean demand contributes **81.405566%**. Thus degradation is broad, with magnitudes concentrated in higher-demand cells, **not confined to Manhattan**. Geographic identification uses positive polygon overlap with the unchanged taxi-zone boundary; cross-borough cells are not relabeled as exclusively Manhattan. `grid_error_comparison.csv` contains all142 grid results and overlap fractions.

## Authorized continuation and final comparison

Same chronological batches, masked MSE, Adam0.001, batch64, seed42, patience10, maximum100 additional epochs. Checkpoints were chosen only by validation loss. The selected continued checkpoint was evaluated on TEST **once** after selection; original predictions were reused. Continued best validation RMSE: **21.221130**, epoch **200**.

| model | MAE | RMSE | R2 |
|---|---|---|---|
| CNN | 6.072322 | 20.485018 | 0.951101 |
| HistoricalAverage | 3.314528 | 16.271804 | 0.969147 |
| Seasonal | 28.088483 | 92.155248 | 0.010377 |
| CNN_continued | 5.242741 | 18.292800 | 0.961007 |

Historical average still wins on both MAE and RMSE; accept this result and stop. No further continuation, restart, alternate architecture or hyperparameter search was performed. Epoch200 being best does not authorize an additional run.

The separate continued model is `models/cnn/jan_mar_2026_3km_30min_continued/best.keras`, with continuation metadata and its saved TEST predictions beside it. Original checkpoint, original forecasts, CNN configuration, source data and historical results are unchanged. The existing canonical configuration still points to the original checkpoint; this focused task preserves it and records the continued model separately, as requested.

## Files and validation

`precontinuation_checks.json`, `channel_integrity.csv`, `training_history_checkpoints.csv`, `train_numerical_ranges.csv`, original/continued prediction summaries and demand-band errors, grid-error tables, `relu_diagnostics.json`, `continuation_history.csv`, `baseline_comparison.csv`, `summary.json`, original fingerprints and the reproducible `run_diagnosis.py` provide the compact evidence. No new charts or large tensor copies were generated.

All continuation gates were checked before optimizer updates. Original artifact checksums and inherited passenger-sensitivity/old-model protections pass for **215 files**. No grid, demand, passenger-sensitivity, routing, FedAvg, DQN or privacy code/artifact was modified. Validated methodology remains unchanged. Closure is appropriate for this bounded CNN task, while the already documented live-weather and downstream operational contracts remain outside its scope.
