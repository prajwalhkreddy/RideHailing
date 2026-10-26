# Final simulator-derived routing training and plain FedAvg

## Status and scope

**FINAL_SIMULATOR_ROUTING_MODEL_READY = YES.** The final clean dataset, chronological split, central supervised pass and five plain FedAvg rounds are complete. **ROUTING_EFFECTIVENESS_CONCERN = YES.** Structural readiness does not establish useful predictive performance.

Only `data/processed/routing_experiences_mar01_mar15_2026_reachability/` was used. No experiences were regenerated or rebalanced. The simulator, reachability constraint, passenger behavior, operational state, pricing policy and frozen interfaces were not changed. No pricing training or privacy/security mechanism was run.

## Dataset validation and provenance

All **3,257,840** experiences in **720** consecutive half-hour partitions span March 1 00:00–March 15 23:30, 2026. The March 16 00:00 timestamp is the generation completion boundary, not a training observation. Every identifier is unique and consecutive; all states are finite 169D, masks Boolean 9D, labels integral 0–8 and permitted by their mask, and current grid IDs belong to 0–141. Driver IDs belong to 0–4999. Invalid candidate features are zero. No legacy dimensions or grid set were used.

The generation checkpoint hash agrees with its completed manifest and carries the `EV_POST_MOVEMENT_STATION_REACHABILITY` contract. Every saved slot report retains a fleet of 5,000, zero pricing replay, no pricing optimizer training and zero federated updates during generation. Generation recorded **1,705,916 requests**, **301,920 assignments**, 57 reserve candidate rejections involving 3 distinct requests, and no reserve reposition rejections. The partition SHA-256 inventory is in `dataset_validation.json`.

The older non-reachability dataset remains `SUPERSEDED_PRE_REACHABILITY_RESERVE_GENERATION / PROVENANCE_ONLY / DO_NOT_USE_FOR_FINAL_ROUTING_TRAINING`; it was not consumed.

## Action and decision support

| action | name | total | percentage | train | validation |
|---|---|---|---|---|---|
| 0 | STAY | 3054927 | 93.771548 | 2454153 | 600774 |
| 1 | N | 31230 | 0.958611 | 27926 | 3304 |
| 2 | NE | 13026 | 0.399835 | 7462 | 5564 |
| 3 | E | 28194 | 0.86542 | 24803 | 3391 |
| 4 | SE | 14312 | 0.439309 | 12621 | 1691 |
| 5 | S | 43912 | 1.347887 | 31766 | 12146 |
| 6 | SW | 18506 | 0.568045 | 15035 | 3471 |
| 7 | W | 32842 | 1.008091 | 28112 | 4730 |
| 8 | NW | 20891 | 0.641253 | 16155 | 4736 |

STAY is the majority label (93.771548% overall). There are no zero-support actions. For descriptive reporting only, low support means <1%: N, NE, E, SE, SW and NW. No reweighting or rebalancing was applied.

REPOSITION: **3,234,802** experiences from **5,000** drivers. EV_CHARGING_NEXT_HOP: **23,038** experiences from **4,165** drivers (0.707156% of all experiences), so charging support is low.

All **5,000** profiles contribute; **0** have zero experiences. Active-driver counts: minimum **208**, median **688**, mean **651.568**, maximum **720**. Detailed counts are recorded in `participant_distribution.json`.

## Frozen chronological split and training configuration

- Training: March 1 00:00–March 12 23:30, **576 slots / 2,618,033 experiences**.
- Validation only: March 13 00:00–March 15 23:30, **144 slots / 639,807 experiences**.
- No random split, March 16 observations or March 17–31 evaluation data.
- Network: **169 → 64 ReLU → 32 ReLU → 9 logits**; action order STAY, N, NE, E, SE, S, SW, W, NW. Invalid actions are masked in training and evaluation.
- Adam, learning rate **0.001**, batch size **32**, seed **42**; unchanged inputs, no normalization, no architecture/hyperparameter/class-balancing search.
- Central: one chronological supervised epoch, reusing the existing one-epoch default. Final epoch checkpoint is selected; no validation-driven epoch search.
- FedAvg: independent seed-42 initialization, **5 rounds**, all **5,000 driver clients**, one local epoch per round. Each client's observations preserve chronological order; fresh Adam state per client/round matches the prepared trainer. Every round represents **2,618,033** training examples.

The existing `aggregate_policy_updates` implements sample-count weighting and zero-sample exclusion. All six tensors were independently checked against weighted means every round. No actual client had zero training samples; zero-client exclusion is additionally exercised in focused tests. Validation labels never enter central or client training.

## Validation and collapse assessment

March 13–15 majority-label baseline: **93.899254%**, all STAY. Validation STAY true share is the same value.

| Model | Accuracy | Cross_entropy | STAY_predicted | Zero_prediction_actions | Effectiveness_concern |
|---|---|---|---|---|---|
| Central supervised | 92.1855% | 0.407089 | 96.9872% | [2, 3, 4] | True |
| Final FedAvg round 5 | 85.3673% | 0.538560 | 91.4394% | [1, 2, 3, 4, 6, 8] | True |

Both models have **100% valid-action predictions / zero invalid-action violations**, finite logits/probabilities and finite cross-entropy. Confusion matrices, class support, prediction counts, precision, recall and F1 are persisted. Both accuracies are below the majority baseline, which independently triggers the effectiveness concern. Strong STAY concentration and unpredicted directional classes are reported rather than hidden by aggregate accuracy.

For this diagnostic, materially supported means ≥1% validation support. Catastrophic collapse is flagged if a class receives >90% predictions while its true share is <90%; this explicit rule avoids confusing natural label imbalance with that specific collapse condition. The concern also independently triggers on accuracy ≤ majority baseline or a materially supported class with no predictions. No automatic retraining/tuning followed these findings.

### FedAvg rounds

| round | active_participants | training_examples | training_loss | accuracy | cross_entropy |
|---|---|---|---|---|---|
| 1 | 5000 | 2618033 | 1.175051 | 0.853671 | 0.823909 |
| 2 | 5000 | 2618033 | 0.501652 | 0.853659 | 0.791394 |
| 3 | 5000 | 2618033 | 0.440842 | 0.853671 | 0.682807 |
| 4 | 5000 | 2618033 | 0.404559 | 0.853671 | 0.606544 |
| 5 | 5000 | 2618033 | 0.386374 | 0.853673 | 0.53856 |

Each aggregate was saved and reloaded, with exact matching logits on the reload check. The final aggregate was evaluated on the full held-out validation population.

## Selected checkpoint and historical comparison

Selected: `models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras`.

Status: **SIMULATOR_DERIVED_ROUTING_BASELINE**. The final fifth-round global FedAvg aggregate is selected to preserve the hierarchical/federated design, even if the independent central model has higher validation accuracy. `central.keras` is retained as the separately evaluated supervised baseline. This task records the selection; it does not change runtime loading or launch pricing training.

The old synthetic checkpoint is **SUPERSEDED_FOR_FINAL_NON_PRIVATE_TRAINING / PROVENANCE_ONLY**, retained without deletion. Its historical accuracy 29.23%, cross-entropy 1.82917, majority baseline 33.63%, STAY prediction share 61.44% and zero SE predictions arose from a different synthetic validation dataset. They do not support a direct statistical superiority claim.

## Reproducibility, resumption and focused checks

Entry point: `scripts/train_final_reachability_routing.py`. It streams one source partition at a time into disk-mapped validated arrays, retains source hashes and a source fingerprint, checkpoints central optimizer progress and each completed FedAvg client/round, and resumes without repeating completed training. Per-client progress files contain model updates, not participant datasets. The compiled masked-gradient step was checked against the existing eager learner implementation.

Focused tests: **11 passed, 0 failed** across `tests/test_final_reachability_routing_training.py` and `tests/test_routing_federated.py`. Checks cover full cached loading, source boundary timestamps, chronological split, final-evaluation guard, shapes, finite states, valid labels, corrected action totals, masked predictions, compiled/eager update equivalence, sample weighting, zero-client exclusion, metadata rejection, checkpoint reload, Adam resume state, five-round completion and final selection. The runtime assertions additionally validate every partition and every round. Tests ran with standard-library `unittest`; pytest is not installed in this environment. No unrelated suites were run.

The action-support CSV's split-index reporting error was corrected using the validated label cache before delivery. It did not affect source rows, the split, training or evaluation.

## Review files

- `dataset_validation.json`, `routing_action_support.csv`, `participant_distribution.json`, `routing_split.json`: data provenance and support.
- `routing_training_config.json`, `routing_training_history.csv`, `fedavg_round_metrics.csv`: fixed configuration and histories.
- `routing_validation_metrics.json`, `central_validation.json`, `routing_confusion_matrix.csv`, `fedavg_validation.json`: held-out results and structural checks.
- `routing_model_selection.json`, `focused_test_results.json`: selected model, readiness, test record and hashes.
- Versioned model directory: `models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/`.

## Next step — not executed

Reset pricing DQN from its reproducible seed-42 initialization; do not continue the March-16 integration checkpoint. Subsequent March 1–15 pricing training must explicitly load the selected simulator-derived global routing checkpoint. Predictive effectiveness remains a reported limitation; no new tuning decision is made here.
