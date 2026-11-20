# Prospective online routing provenance

## Scope and initialization

`FRESH_PROSPECTIVE_ONLINE_ROUTING_V1` enables fresh online routing as a structurally eligible research option. No training experiment is launched. Historical checkpoints cannot be renamed or imported through this initialization contract. The existing utility baseline and sample-weighted hierarchy remain separate and unchanged in their default behavior.

The manifest records architecture 169–64–32–9; seed42; the existing seeded Keras initializers and exact initial-weight hash; local seed = global seed + driver ID + 1; source/configuration hashes; initial global version0 and federation round0. Existing settings are Adam0.001, batch32, one local epoch, memory1000 and persistent local optimizer state. These are inherited project settings exposed to prior March development work, not independently selected out-of-sample hyperparameters. No tuning is performed here.

The initial proposed window is March12 00:00–02:00 New York (04:00–06:00 UTC), matching the bounded acceptance scope. Offline routing fitting and validation-selection periods are null: there are no inherited learned weights. The end bound governs slot starts/closure; the final slot's closing utility observation at 06:00 is permitted, but no subsequent slot update is permitted. Any longer experiment requires a new explicit frozen contract.

## Information cuts

The complete manifest reuses January OD support, January–February sensitivity and the earlier cutoff-verified historical demand/popularity/driver-prior inputs. Forecasts remain under the existing 120-minute assumed-availability protocol. It does not certify operational weather vintage. References/grouping and other development-tuned design assumptions remain limitations.

Only local utility labels collected in the active experiment slot can enter memory. Actual runtime collection stamps the engine UTC clock. Stored observations must have the current federation slot ID. Future/out-of-window timestamps fail; retained memories are checked before each update and during restore. Old experiment observations may be reused within the bounded memory; no pre-experiment/offline experiences are imported. Local updates occur at slot close and new global weights are available only at the next decision boundary. Requests remain scheduled realized events, not fitted artifacts.

## Equal-client federation

This task explicitly specifies equal-client aggregation. The new version uses an arithmetic mean over participating clients with a current-slot observation and positive local work. It reuses the existing validated FedAvg tensor aggregator with unit aggregation weights; its internal `sample_count=1` represents an equal-client weight, not a claim that the client trained on one observation. Actual learner sample/optimizer counters remain private and checkpointed. The previous sample-count-weighted mode remains the default for historical hierarchy contracts.

Global version advances only when a nonempty update is published. Federation round advances at every completed slot; no-participant slots retain weights. Private memories/preferences never appear in the public lifecycle release. This is NONPRIVATE FedAvg, not DP. Python-local storage is not process isolation; model updates can disclose information. No clipping/noise/accountant/budget is attached or claimed.

## Checkpoint and mixed-fleet integration

Checkpoints bind initialization identity, source/configuration hashes, aggregation mode, global version, federation round, availability/experience cutoffs, global/local weights, local optimizer states and private memories. The existing OD checkpoint continues to preserve fleet EV identities/composition, charging state, OD replay and RNGs. Mismatched lineage/configuration/cutoffs fail closed. Historical frozen routing weights remain rejected.

Mixed 10%,20%,30% EV composition uses the existing deterministic initializer. EV energy/charging overrides and non-EV battery bypass behavior are unchanged. Full EV experiments are not run.

## Validation interpretation

Synthetic deterministic parameter-update payloads exercise equal-client averaging, participation, version advancement and uninterrupted/resumed updates. `train_for_slot` is mocked in those tests: no gradients are computed. The real local Adam/cross-entropy implementation is reused without change; its prior fixture-validation evidence remains in the hierarchical-interface report. This task does not newly validate learned convergence or a training run.

Small runtime fixtures exercise full information-manifest admission and OD checkpoint/resume. Other bounded regressions cover historical lineage rejection, UTC events, station reserve safety, fallback/replay, utility probabilities and mixed-fleet initialization. The initial snapshot-aliasing failure is preserved as superseded test evidence; the fix copies event timestamp lists across snapshot/restore.

## Readiness and next task

Fresh online routing is structurally eligible for a separately authorized bounded research experiment. Full learned-routing training is not yet validated; updates remain disabled by default. Final research evaluation requires a frozen experiment protocol, including duration, seeds, aggregation/optimizer settings, weather assumptions, evaluation split and stopping rules. The next single task is to freeze that bounded protocol and authorize its execution; no execution is initiated here.

See routing_initialization.json, information_contract.json, validation.json and test logs. No historical results or model checkpoints were modified.

Final validation: **54 distinct tests passed**, no remaining failures, across overlapping bounded batches. Full-runtime synthetic-update checkpoint continuation passed with two successive global versions. The first batch’s timestamp-list aliasing failure is retained as superseded evidence. No gradients, historical-data fitting or real-data episode was executed. Preservation checks found no changes among 2,279 historical files.
