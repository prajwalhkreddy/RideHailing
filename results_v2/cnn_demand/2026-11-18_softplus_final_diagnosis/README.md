# Final bounded Softplus CNN diagnosis

## Decision

**B — confirmed optimization/gradient saturation at the saved checkpoint.** No additional preprocessing, masking or implementation defect is demonstrated. This identifies the near-zero mechanism, not the historical cause of the learned negative preactivations. It does not establish that removing saturation would resolve the dominant high-demand errors.

**Recommended single action: freeze this CNN experiment and proceed to OD-DQN training preparation with the historical-average comparison retained.** No further CNN correction/retraining is justified by this bounded evidence alone. This recommendation authorizes neither training nor automatic replacement of the downstream forecast. The current checkpoint must not be represented as superior to the baseline or as February-cutoff prospective input.

## Population and prediction evidence

Saved validation predictions cover 718 intervals × 142 valid grids (101,956 cells); March16 development covers 48 × 142 (6,816). March16 is not an independent final test. Zero-demand frequency is 53.77%/53.45%, whereas 86.18%/89.16% of positive-demand cells are predicted below 0.01. Thus sparsity alone does not explain the collapse. Positive-target medians are 5 requests in both populations; P90 is 56/43.8 and P99 is 760.68/655.96. Mean actual/predicted demand is 19.1101/13.8626 and 16.7773/7.8594.

Reconciled CNN MAE/RMSE: validation 7.013677/26.027186; development 8.956793/39.232116. Baseline: 3.518426/18.226779 and 5.085002/29.771590. All metrics use the same saved rows and original request-count units. No protected-period data were read.

## Activation, gradients and learning

The deterministic diagnostic uses eight January7 training timestamps (00,03,06,09,12,15,18,21 local), reconstructing only the January1–7 prefix needed for causal preprocessing. It has 1,136 valid cells, including 530 positive targets. The reconstructed Softplus forward pass matches the checkpoint exactly. No optimizer step occurred; iterations remained 1,890 and checkpoint/weights were unchanged.

For the 458 positive targets predicted below 0.01, median final preactivation is −23.30265, minimum −537.11127. Median sigmoid derivative is 7.59e−11; 18.12% of these outputs are numerically exact zero. Mean absolute loss gradient is 0.0134425 at output but only 4.25e−7 at preactivation. Their final-kernel gradient norm is 0.004973, versus 1,141.007 for the other positive cells. Softplus therefore permits gradients mathematically but is strongly saturated numerically. It does not provide the hard ReLU barrier previously diagnosed.

Final bias is −0.109166; kernel L2 norm is 3.39420 (range −0.922836 to 0.815375). Bias alone cannot explain preactivations as low as −537. Neither hidden layer has an entirely inactive channel in this batch. Their zero fractions are 51.21% and 59.28%; there is no evidence of total hidden-layer collapse.

Masked MSE is 831.500854 versus independent calculation 831.500896 (floating-point reduction difference). Invalid-grid gradients are exactly zero. Zero-demand cells contribute only 0.000247% of batch squared error; near-zero positive cells 8.5994%; other positive cells 91.4004%. The objective is not numerically dominated by zero targets. Best validation epoch is 42; early stopping ended at 52. This endpoint diagnostic cannot reconstruct earlier optimization trajectories.

## Historical demand and preprocessing

The established seven-channel order remains day-of-week, hour, half-hour period, weather code, temperature, wind speed, historical-average demand. Targets and outputs are unscaled counts; there is no inverse-output transformation or downstream clipping. Historical demand is divided by causal prior-training demand SD, while weather is standardized from eligible history; no new inconsistency was found. Existing missing-data and causal weather-persistence handling is unchanged. The 120-minute availability lag is an assumption, not verified operational availability.

Batch demand SD is 70.3811–73.3332; normalized history median/P99/max is 0.007005/5.52410/12.40543. Reconstructed count-scale history median/P99/max is 0.5/392.525/893.333. Setting only history channel to zero reduces mean prediction from 13.16277 to 0.004442 and raises RMSE from 28.83576 to 89.68287. Scaling it by 0.9/1.1 changes mean prediction to 11.67630/14.64731. The CNN uses this feature strongly; it does not simply ignore it. Positive near-zero prevalence remains 86.42% under both ±10% perturbations. These are diagnostic perturbations, not proposed preprocessing changes or performance estimates.

## Error concentration

Positive-demand cells contribute 99.51%/99.999% of validation/development SSE. Cells above 100 actual requests contribute 82.47%/93.44%; the five grids ranked highest by training demand contribute 81.60%/92.96%. Peak slots (upper quartile of observed city demand, descriptive only) contribute 53.33%/63.33%. Low-demand cells (1–10) contribute 15.10%/11.68% of absolute error but only 0.90%/0.37% of SSE. Large-demand errors dominate RMSE even though saturated modest-demand cells dominate the near-zero phenomenon. Complete disjoint demand bands and overlapping grid/time summaries are in `error_concentration.csv`.

## Reproducibility and scope

`diagnose.py` records model structure, exact forward equivalence, gradient statistics, input/source/checkpoint fingerprints, no-update checks and history perturbations. `saved_statistics.py` produces float64 saved-output summaries and error shares without inference. `validation.json`, `model_structure.json`, `batch_timing.csv`, `activation_gradient_statistics.csv`, `history_channel_perturbation.csv`, `saved_prediction_summary.json` and `error_concentration.csv` contain the numerical evidence.

All diagnostic assertions passed. No new production correctness defect was established, so no production patch or new regression test was introduced. Only this new diagnostic directory was written. Historical models/results, OD pricing, routing and sensitivity remain unchanged. No training, simulation, architecture search or storage cleanup was performed. Small-batch conclusions do not establish population-wide gradient behavior or a uniquely effective corrective intervention.
