> Checkpoint status: **STRUCTURALLY_VALID / INTEGRATION_BASELINE / NOT_FINAL_EXPERIMENTAL_POLICY**. Controlled-synthetic accuracy 29.23% is below the 33.63% majority baseline. Retain for fixtures; final simulator-generated experiences require later retraining/evaluation.

# Final 169-input nine-action routing baseline

**ROUTING_POLICY_READY = YES for the specified structural/training integration gate.** Predictive quality is limited: this controlled baseline does not establish effective fleet routing or real-world generalization. No CNN, passenger-sensitivity, pricing-DQN, privacy or attack module was changed.

## Frozen project baseline

α=β=δ=κ=0.3; ζ is not applicable. σ floor is 10⁻⁶ USD and Ĥ floor is 10⁻⁶ minutes. F̂₀=Ĥ₀=0 for every grid: no previous simulated dispatches and initially empty queues. These are explicit project decisions, not manuscript-reported values.

μ and σ retain successful-assignment mean-price and population-SD EWMAs. F̂=0.3×previous-slot dispatch count/30+0.7×prior F̂, in dispatches/minute. Ĥ=0.3×observed wait+0.7×prior Ĥ, in minutes. Missing charging observations carry prior Ĥ; observed co-located station queues retain queue-count-weighted pooling.

Verified historical μ/σ priors are available only after January 25, 2026 at 18:30; earlier starts fail closed. The fixture starts February 1. No validation/test outcomes initialize estimates.

C_rep=0.25×distance_metres/(3000√2). Thus STAY=0, cardinal≈0.1767767, diagonal=0.25. Full charging-path cost uses the same normalizer and may exceed 0.25. Physical travel time and energy still use actual metres/km. The economic coefficient is a project hyperparameter recorded for later sensitivity analysis; no ablation was run.

The canonical source remains `../2026-10-20_final_routing_configuration/routing_configuration.json`; this package's `routing_config.json` records the exact training snapshot. The factory converts the normalized coefficient to the existing utility-cost/km interface without changing its meaning.

## State, labels and controlled experience generation

Architecture: **169→64→32→9**, hidden layers unchanged. Candidate order STAY/N/NE/E/SE/S/SW/W/NW contributes μ/σ/F̂ triples (27); Ĥ for grids 0–141 contributes 142. Invalid triples are zero placeholders with separate masks. Utilities read only the published previous-completed-slot state.

A deterministic routing-only generator produced **3,408 controlled synthetic experiences** over 12 half-hour slots, 142 grids and two private profiles per grid. First eight slots: **2,272 training samples**; final four: **1,136 validation samples**. These are newly generated experiences, not historical fleet observations or old training files.

One profile has energy 60 kWh; another 30 kWh with charging threshold 30. Private preferences are seeded uniform draws: P_min $10–35, W_max/H_max 5–30 minutes. Synthetic slot outcomes use 0–7 assigned dispatches/grid, fares $5–55 and station-grid waits 0–20 minutes. These fixture-generation ranges are not new production preference calibrations. Actual μ/σ priors, topology, station mapping, recurrences and utility decisions come from the final interfaces. No pricing or passenger-acceptance simulation is claimed.

Above-threshold labels maximize U1+U2−C_rep; charging labels are the valid next hop toward the chosen U3−C_rep destination. All labels are verified in 0–8 and under the origin mask. Clients are partitioned by grid modulo three. Local experiences stay in local learner buffers; FedAvg receives weights/counts only. This is single-process conceptual locality, not a distributed privacy implementation.

## One reproducible training configuration

Seed 42 with TensorFlow deterministic operations. Adam, learning rate .001, batch size 32, one local epoch, original hidden layers and masked cross-entropy are retained. Five fixed FedAvg rounds, three data-bearing clients plus one zero-sample client. Each local mini-batch is trained once per round; client weights start from the common global weights each round. No hyperparameter search or repeated baseline run.

Best validation cross-entropy selects the checkpoint. This same validation set is used for selection and reporting; there is no independent test-set claim. `train_baseline.py` records generation/training and refuses implicit rerun when completed metrics exist. `routing_fixture.csv` provides selected grid/slot decisions and state values. Reproducibility is configured by seed/deterministic operations, not independently demonstrated by a second full run.

## Results and limitations

Best round: **5**. Validation accuracy **29.2254%**; masked cross-entropy **1.829169**. Majority-label baseline accuracy is **33.6268%**. The trained model is below that baseline.

Training action counts (0–8): **702, 399, 168, 150, 59, 188, 159, 314, 133**. All nine actions have training and validation support. Predicted STAY share is **61.44%**, compared with **33.63%** of validation labels; SE receives **zero predictions**. These indicate substantial action imbalance/partial collapse despite finite masked probabilities. No quality improvement is claimed. Private preferences influence labels but are absent from the public policy state, which is a possible limitation rather than a tested explanation.

Invalid predicted actions: **0**; valid-action prediction rate: **100%**. Every evaluated probability is finite, masked probabilities are zero and valid probabilities sum to one. The action support table and confusion matrix disclose all outcomes. The readiness gate passes the requested structural/training conditions, not an empirical-performance criterion.

## FedAvg, artifacts and protection

All five rounds completed with sample-count weighting. Each round represents 2,272 local samples; client 3 has zero samples and is excluded. Best and last aggregated models reload with 169 inputs and nine outputs. Focused fixtures separately verify unequal sample weighting and loadability.

Models: `models/routing_policy/jan_mar_2026_3km_169x64x32x9/best.keras` and `last.keras`. The directory also contains training configuration/history and state/action specifications. Existing 155-input, five-action and old FL artifacts remain untouched and are classified **SUPERSEDED_FOR_FINAL_169_INPUT_9_ACTION_POLICY**; no old experience files were reused.

**35 focused tests passed, 0 failed** across frozen baseline configuration, final state/checkpoints, utilities/navigation, operational statistics, config and FedAvg. No long simulator was run. The training pipeline itself verifies masks, label validity, aggregate loading and probability normalization.

Next task, not executed: freeze passenger acceptance and pricing-reward contracts, then assemble [J_hat, previous J_disp, I, p, destination popularity] for final pricing-DQN implementation.
