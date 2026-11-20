# Prospective information-cutoff contract — development validation V1

**BLOCKED_UPSTREAM_ROUTING_SELECTION. No prospective simulation or training was executed.**

## Completed calibration and guard

`JAN_FEB_REQUEST_WEIGHTED_BINNED_SENSITIVITY_V1` reconstructs the approved 0.5-km binned estimator using only raw pickup time, fare, distance, weather code and hour fields for **January1–February28**. Parquet predicate filtering excludes March before aggregation. Neither the persisted trip epsilon nor its `is_runtime_candidate` flag is read. The fixed 1.5 ≤ distance < 75 km population scope is retained.

- Source/pooled represented population: **5,457,435** requests.
- Latest source observation: **2026-02-28 23:59:59 America/New_York**.
- Exclusive source and fitting cutoff: **2026-03-01 00:00 EST**.
- P_base: **22.354198442390455 USD**; L_base: **4.616983790655043 km**, preserved project assumptions, not re-estimated.
- Pooled request-weighted mean: **1.7259156936729738**.
- Population SD: **0.4263137770107406**.
- Positive empirical support: **[1.3623823900961856, 2.860009965945212]**.

Conditional bins, empirical values, request weights and support counts are recomputed separately from January–February. Existing weather/T1–T4 definitions and fallback order remain fixed; the ≥5,000 support rule now counts requests represented by positive finite bins in the new population. Nonpositive/undefined bin estimates remain in diagnostics but not the sampler. There is no extra clipping, tail extrapolation, parametric fit or deterministic assignment from a passenger's own distance bin.

This is a retrospective reconstruction with a historical information boundary, not a claim that these files physically existed on March1. Weather grouping, reference values, price factors and statistical design retain development tuning, including March evidence. Independent out-of-sample design selection is not claimed.

`PROSPECTIVE_INFORMATION_CUTOFF_V1` validates aware source start/end, latest observation, fitting cutoff, artifact identity/hash and methodology identity. Upstream model-selection information is included in the check. Permitted role cutoffs cannot be moved forward by the caller. Realized request events have a separate scheduled-slot check and are not incorrectly treated as calibration data.

The new calibration is opt-in; runtime initialization requires an information contract, complete active-role provenance and matching active sensitivity/routing/support/forecast artifacts. Checkpoints store the contract and require an identical requested contract, with source fingerprints. Historical modes remain explicit and unchanged.

## Essential upstream blocker

The proposed frozen routing snapshot is `global_after_slot_528.keras`. Its **direct** training evidence is verified from `training_progress.csv`: slot527 = March11 23:30, maximum source slot527, model availability slot528 = March12 00:00. This does not establish the cutoff of its upstream fitted inputs.

The generation path is:

1. `scripts/generate_final_behavioral_routing.py` → `RoutingExperienceExperiment` in `src/simulation/routing_experience_generation.py`.
2. Inherited `ProductionExperiment.requests_for_slot` → `src/pricing/dqn_contract.py:artifact_snapshots`.
3. `config/final_temporal_protocol.json` selects the epoch200 March1–15 forecast artifact and explicitly records that March1–15 was CNN validation.
4. `src/demand/final_cnn.py:SPLITS` sets CNN training before March1 and validation before March16. `scripts/train_final_cnn.py` selects `best.keras` by lowest validation error. The continued model metadata retains the best-validation metric and the original best-model lineage.

Thus routing experiences inherit a CNN selected using validation observations through **March15**, even though routing updates themselves stop on March11. A replacement January demand baseline for the current replay cannot remove this dependency from already learned routing weights. The manifest deliberately records `selection_end_exclusive = March16 00:00 EDT` and rejects it against March12 startup with **“Upstream model selection exceeds cutoff.”**

No routing weights were relabeled, retrained or substituted with an unapproved untrained policy. The task's stop rule applies. The provided evidence does not certify an alternative routing checkpoint free of this dependency; no broad checkpoint search was performed.

## Other input audit

`fitted_input_audit.csv` records paths, hashes, periods and limitations:

- January OD support remains unchanged.
- January-only demand averages and January popularity from the previous acceptance are reusable before forecast issuance. They are not CNN predictions.
- The direct OD state uses no learned scaler. Inherited CNN normalizers fit January–February, but model selection remains the blocker above.
- Fare priors and driver-price profiles have a guarded January25 18:30 cutoff. Their saved metadata do not separately record the exact last observation; those fields were not invented.
- Weather availability retains the explicit 120-minute persistence assumption, not verified historical publication/vintage information.
- The proposed pricing learner remains untrained and would support integration checks only.

The information manifest is explicitly **incomplete and blocked**, not a runnable certificate. Completion of inherited exact-latest-observation fields and remaining active-role bindings is deferred after the essential routing rejection.

## Validation and execution status

No March12 requests were replayed in this task: slots **0**, optimizer updates **0**. Acceptance/reward differences, four-slot repeat and full runtime resume are **not available**, rather than zero outcomes or inherited passes from the retrospective experiment.

Focused tests cover cutoff boundaries, future observations and selection, changed fingerprints, preserved calibration counts, deterministic sampling/sampler restoration, fallback-count tampering, scheduled future replay events, checkpoint rejection, and rejection before engine construction. Existing fallback, historical replay/resume and forecast-guard regressions remain in the bounded suite. See `tests_final.txt` and `validation.json` for the final test result.

## Files and next task

- `sampling_contract.json`, `population_manifest.json`: versioned calibration and selected-population fingerprint.
- `conditional_distance_bins.csv`, `distribution_statistics.csv`: rebuilt empirical pools and statistics.
- `information_contract.json`, `fitted_input_audit.csv`, `preflight.json`: proposed cutoffs and exact blocker.
- `tests_final.txt`, `validation.json`: checks, fingerprints and preservation evidence.

Reproduce the calibration with `scripts/build_prospective_sensitivity.py`; no model training is involved. Prior `results/`, models and retrospective acceptance evidence are preserved.

**Next single task:** establish a cutoff-valid routing-experience/model lineage, or obtain an explicit decision permitting an alternate research routing baseline. Existing weights cannot be certified by changing metadata. Any necessary regeneration/retraining requires separate authorization; neither was performed here.
