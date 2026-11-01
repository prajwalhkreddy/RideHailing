# Temporal Federated Routing: Contract and Validation

**TEMPORAL_FEDAVG_PROBABILITIES_INFORMATIVE = YES**  
**PUBLIC_ROUTING_STATE_CONTRACT_VALIDATED = YES**  
**ROUTING_MODEL_CONTRACT_REVIEW_REQUIRED = NO**  
**Pricing remains blocked pending a separate decision.**

## Methodology evidence

The identified reference is `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx`. Its XML paragraphs 187–189 define a global network predicting mean routing response from public candidate-grid statistics and global charging-wait estimates, without collecting individual preferences centrally. Paragraph 199 retains utility-based actual routing. Paragraph 201 keeps experiences local; paragraph 204 specifies equal averaging over eligible clients.

The existing implementation resolves experience reuse:

- `src/routing/learning.py`, `LocalObservationBuffer`: a persistent bounded local buffer, capacity 1,000.
- `LocalRoutingLearner.train_for_slot`: one update per eligible slot using the latest 32 available observations and one local epoch.
- `reset_from_global_weights`: replaces model weights but retains the client's Adam moments and iteration.
- `src/simulation/main_slot.py:235–259`: current-slot routing contributors train and export; each exported aggregation count is explicitly 1; the resulting global weights are broadcast.

The supported interpretation is **TEMPORAL_ACCUMULATED_LOCAL_HISTORY**, using the latest 32 observations—not an epoch over the entire accumulated history. No competing interpretation was run because the code explicitly resolves this choice.

The aggregation rule is **equal eligible-client weighting**, implemented by the existing generic weighted aggregator with unit-count payloads. This is supported by both the temporal orchestrator and the roadmap. The earlier offline experiment instead used full-history sample counts; that diagnostic baseline is preserved rather than silently relabeled as the temporal contract.

## Frozen model and chronology

The 169 public features, nine actions, masks and labels remain unchanged. The network is 169→64→32→9, with the existing ReLU hidden layers and masked cross-entropy. Adam learning rate 0.001, batch size 32, one local epoch and seed 42 are unchanged.

Initialization tensor SHA256: `9e7bc3688a3d9c17eba7abf86a64f78606d6be9694b19d906e367ec108f5b4b0`. It matches the previous experiment's reconstructed seed-42 initialization.

All 576 training slots were processed in order, March 1 00:00 through March 12 23:30. At slot t, participating clients start from phi_t, train using their own eligible history through t, and aggregate into phi_(t+1). No future-slot observation enters an earlier update. Clients without a current routing observation do not export stale updates, even if they retain history.

The final March 12 model was frozen and evaluated on all 646,657 March 13–15 observations. Validation produced no optimizer update and did not select a checkpoint. The only development evaluation uses the fixed first 512 observations from March 1 00:00 at day boundaries; it is explicitly an in-sample diagnostic, not held-out model selection.

## Participation and exposure

| Quantity per slot | Mean | Minimum | Maximum |
|---|---:|---:|---:|
| Participating clients | 4607.574653 | 4175 | 4997 |
| Local batch observations used | 143141.979167 | 4591 | 159904 |

Fresh source observations total **2,656,632**. Local training exposures total **82,449,780**, including intended history reuse. Counts are not interchangeable. Every slot records fresh observations, participating clients, noncontributors, eligible clients with no usable data, aggregation weight, maximum source slot and next-model slot. Total aggregation weight equals the number of eligible participating clients.

## Execution boundary and checkpoints

Independent client networks and Adam updates are executed with a separate client dimension for efficiency. Each client has its own loss and optimizer state; gradients are not pooled before local optimization. Focused tests compare these updates with the existing Keras Adam implementation and compare batched clients with independent local updates.

This is a single-process replay of existing records, emulating client-local stores and a parameter-only aggregator. It is not a deployed distributed privacy system. The aggregate receives model weights and unit counts, not raw features or private preferences. No individual preference, battery, energy, utility score or charging branch was added to the public state.

Global model snapshots are saved every 16 slots and at day boundaries. The latest resumable checkpoint also contains local Adam moments, velocities and iterations, buffer row indexes, next-slot index and Python/NumPy RNG state. No stochastic training operation follows deterministic initialization. Older global snapshots are inference artifacts; full client state is retained for the latest checkpoint only.

At checkpoint 16, the next update was reproduced from independently reloaded state and matched the live-state update bit-for-bit. Both verification updates were discarded before normal training continued. Every batch checked client ownership and source-slot eligibility.

## Frozen validation results

| Model | CE | Multiclass Brier |
|---|---:|---:|
| Temporal final | 0.291657966 | 0.093053954 |
| Masked training-label prior | 0.293259219 | 0.095934945 |
| Central | 0.269109640 | 0.093789887 |
| Old offline FedAvg | 0.441746289 | 0.178063054 |

Temporal accuracy: **94.936265%**. ECE: **0.015838035**. Predicted STAY share: **99.788605%**. Non-STAY accuracy/CE: **0.619544% / 5.140560449**. Invalid-action violations: **0**.

True action counts (0–8): [614698, 3223, 3682, 2610, 1419, 9329, 3380, 4388, 3928].  
Predicted counts: [645290, 0, 0, 0, 0, 823, 0, 544, 0].

Brier is the mean sum of nine squared class-probability errors. ECE uses the same ten top-label confidence bins as previous experiments. No clipping, calibration, weighting or balancing was introduced.

The requested YES gate requires both prior losses to improve with zero invalid actions. For descriptive INCONCLUSIVE reporting, substantial improvement was defined before final validation as closing at least half of both old-offline-to-prior loss gaps without passing both. This reporting convention does not tune training. The full comparisons and criteria are persisted.

The CE improvement over the prior is small (approximately 0.001601); this is a pass of the requested point-estimate gate, not a claim of statistically established superiority. Non-STAY accuracy remains only 0.6195%, and the model predicts STAY for 99.7886% of validation observations. These limitations remain relevant to final freeze validation.

## Interpretation and next action

The public-state contract is supported by the methodology. Repeated public states with different private routing decisions are compatible with learning mean response probabilities; this observation alone does not justify exposing private preferences centrally. Previous conflicting-label diagnostics remain historical evidence, but their state-expansion implication is not adopted.

Recommended next category: **FINAL_ROUTING_FREEZE_VALIDATION**. It has not been executed. Any unresolved adequacy problem belongs to a separately authorized review of mean-response targets, local inference or decision-type architecture—not an automatic addition of private features.

The temporal and offline protocols differ in update count, timing, buffer reuse, optimizer persistence and aggregation semantics. Their comparison tests the complete supported contract; it does not identify the causal contribution of any single difference.

No pricing training, experience generation, utility change, state change, privacy implementation or March 17–31 access occurred. No runtime routing checkpoint was activated. Existing offline results and checkpoints remain unchanged.

## Review files and focused validation

- `methodology_contract.json` and `temporal_learning_semantics.json`: source evidence and exact semantics.
- `slot_participation_summary.csv` and `training_progress.csv`: all 576 causal updates.
- `development_metrics.csv`: fixed training-slice day-boundary diagnostics.
- `checkpoint_validation.json` and `focused_validation.json`: deterministic resume and focused checks.
- `final_validation.json`, `probability_adequacy.json`, `comparison_to_offline_fedavg.json`: frozen held-out results and gates.
- `next_action.json`: recommendation only.

Models are under `models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/`; the final model is `final_march12.keras`. Implementation: `scripts/train_temporal_routing.py`. Focused tests: `tests/test_temporal_routing.py`.

**TEMPORAL_FEDERATED_ROUTING_COMPLETE**
