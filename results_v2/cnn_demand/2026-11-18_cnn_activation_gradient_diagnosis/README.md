# Final-output activation and gradient diagnosis

**Classification A: confirmed activation/gradient blocking.** At the saved checkpoint, negative final pre-activations produce exact zeros through the final ReLU. Positive-demand cells on this branch have useful output-loss gradients but no gradient through the activation. This directly establishes the zero-output mechanism in the bounded batch; it does not reconstruct how optimization reached these weights or establish that this is the sole cause of all performance loss.

## Scope and reconstruction

Eight deterministic eligible January 7 training samples at local hours 00,03,06,09,12,15,18,21 represent a daily cycle (not a statistically representative sample of all months). The existing builder processes only January1–7 history to reproduce its causal moments and persistence features. Only eight tensors enter model inference/autodiff. No full prediction pipeline, March data, training, optimizer update or alternative model was run.

The original compiled checkpoint was loaded. A lightweight submodel exposes the input to `conv_3`; TensorFlow conv2d and bias addition using the unchanged trained kernel/bias expose its pre-activation. Reapplying ReLU, permutation and the original mask yields **bitwise-identical predictions** to the loaded model on all cells. Saved checkpoint SHA256, in-memory weights and optimizer iteration count remain unchanged. Source and batch fingerprints are in `validation.json`; exact timestamps are in `batch_timing.csv`.

## Architecture and zero provenance

`src/demand/final_cnn.py:build_model` specifies three 3×3 convolutions, all ReLU. The trained model confirms final `conv_3` activation is ReLU and bias is **−0.08551890403032303**. Its subsequent operations are axis permutation and multiplication by the valid-grid mask. There is no downstream clipping in the prediction exporter. The mask is one for all 142 evaluated cells, so it cannot explain valid-grid zeros.

Among 1,136 valid grid-time cells:

- Exact-zero output: **94.5423%**.
- Negative / exactly-zero / positive final pre-activation: **94.5423% / 0% / 5.4577%**.
- Pre-activation min / median / max: **−527.118652 / −17.459850 / 1020.343872**.
- Output zero is exactly equivalent to pre-activation ≤0 in the batch.

There are 530 positive-demand cells: 470 predicted zero and 60 predicted positive. Thus **88.6792%** of positive-demand cells are blocked at the output activation. The bias alone is not claimed to cause the negative pre-activations; they include the learned kernel response.

## Automatic differentiation evidence

The actual checkpoint's compiled masked MSE is used, with denominator batch size ×142. Restricted loss contributions retain this denominator; no loss reweighting or optimizer operation occurs.

| Diagnostic | Positive target, zero output (470) | Positive target, positive output (60) |
|---|---:|---:|
| Mean absolute dLoss/dOutput | 0.013803565 | 0.142176941 |
| Maximum absolute dLoss/dOutput | 0.167253524 | 0.575078309 |
| Mean absolute dLoss/dPreactivation | **0** | 0.142176941 |
| Maximum absolute dLoss/dPreactivation | **0** | 0.575078309 |
| Isolated final-kernel gradient L2 | **0** | 1219.709961 |
| Isolated final-bias gradient magnitude | **0** | 1.669734 |

All blocked cells have strictly negative pre-activation (largest −1.189654). Their dLoss/dOutput values are negative, correctly requesting increased predictions; the final ReLU removes that signal. Full-loss final-kernel/bias gradient magnitudes are 1219.659790 / 1.663408, confirming other cells still drive updates. This is not a globally dead network. Shared parameter changes from other cells could later move blocked cells across zero, but blocked cells cannot directly supply their own corrective signal at this checkpoint.

## Loss, sparsity and masking

The training objective is original-count MSE averaged over 142 valid cells, with no class weights or normalization of targets. Autodiff loss **818.289978** matches the independent masked calculation within floating-point tolerance. All 912 invalid raster cells have zero output-loss and pre-activation gradients.

Targets are zero in **53.3451%** of valid cells, but zero-target cells contribute only **9.638703 / 929,577.377642 squared error (about 0.00104%)**. Positive-demand/zero-output cells contribute 88,199 squared error, or loss 77.639969 (about 9.49% of total). Positive-demand/positive-output cells contribute loss 740.641479 (about 90.51%).

Thus target sparsity alone does not establish a majority-zero objective advantage. MSE penalizes underprediction of positive counts, and errors on high-count active cells dominate this batch. The demonstrated failure is that the final activation blocks a nonzero corrective signal from many other positive-demand cells. No new loss function is justified by this measurement alone.

## Recommended single correction — not implemented

For a separately authorized, versioned correction, **replace only the final convolution's ReLU with Softplus**, preserving the hidden architecture, loss, masking and data contract. This removes the hard zero-gradient region mathematically while retaining nonnegative predictions. Do not replace this checkpoint in place.

Softplus is a minimal candidate, not a demonstrated performance remedy: at very negative pre-activations its derivative is tiny and can underflow numerically. Applying it to the existing −527-scale pre-activations is not guaranteed to revive them. Any subsequent single training experiment must explicitly check gradients, positive-demand zero rates and baseline-relative errors; no such experiment or activation comparison occurred here. Initialization/scale changes are not authorized or inferred.

## Reproducibility and limitations

`diagnose.py` includes focused assertions for exact original-forward equivalence, valid mask, manual loss agreement, nonzero output gradients, blocked pre-activation/parameter contributions, invalid-cell gradient exclusion, and unchanged weights/checkpoint/optimizer state. All passed. No production test expectations were weakened. `model_structure.json`, `activation_gradient_statistics.csv`, `validation.json`, `batch_timing.csv` and the execution log preserve the evidence.

This is a one-day training-batch diagnosis of the selected checkpoint. It does not prove the same gradient fractions across validation, explain the entire RMSE gap, or identify the original optimization trajectory. Hidden-layer gradient distributions were not separately characterized because the final activation already supplies a direct blocking mechanism. Historical results, CNN checkpoint, OD pricing, routing and sensitivity remain unchanged.
