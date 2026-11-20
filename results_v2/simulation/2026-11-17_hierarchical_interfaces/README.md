# Hierarchical research interfaces — bounded validation

## Architecture and information boundaries

`DriverHierarchy` (`DRIVER_LOCAL_NEXT_SLOT_FEDAVG_V1`) is an opt-in interface on the existing OD runtime. UTILITY mode preserves deterministic private-utility routing. FRESH_UNTRAINED_GLOBAL creates the existing 169–64–32–9 model from an explicit seed; after local updates its global network supplies masked routing probabilities. Physical decisions remain private utility/charging decisions, as specified by master sections 7–8. No invalid historical routing checkpoint is activated.

Driver preferences, utility labels and bounded memories stay in driver-side simulated storage. The platform aggregation receives only existing exported model parameters and counts; the public lifecycle release contains round, participant count, availability and nonprivate status. Gymnasium info exposes aggregate acceptance/reward only. Python object privacy is an interface convention in a trusted simulator, not process isolation or a cryptographic guarantee. Runtime checkpoints contain private simulation state and must not be treated as public model releases.

## Slot lifecycle and federation

The current global policy supplies slot-start OD feedback. Idle-driver utility decisions produce local labels at slot close. After operational statistics close, eligible clients start from the shared global weights, use the existing masked cross-entropy local learner, and aggregate with existing FedAvg. Weights are proportional to the actual local batch count used in that round, not cumulative counts. The resulting global is available at the next boundary; earlier timestamp access is rejected. Historical stored pricing states are not rewritten.

Existing settings: batch size 32, memory capacity 1000, one local epoch, Adam learning rate 0.001. Local Adam optimizer state persists across rounds. Updates are disabled by default. Only tiny synthetic fixture updates were executed; no historical-data model training, CNN/DQN training or long simulations occurred.

## Privacy status

NONPRIVATE. Existing DP utilities were preserved and inspected, but are not silently attached to this lifecycle. A deployment threat model/release boundary, client clipping norm, noise mechanism/multiplier, sampling semantics, accountant configuration and budget report remain necessary before any DP claim. FedAvg alone is not differential privacy.

## Mixed fleets

`MIXED_EV_FLEET_V1` selects exactly 500/1000/1500 of 5000 drivers for 10%/20%/30% EV scenarios using an independent seeded draw. All legacy vehicles without an explicit flag retain EV behavior. Non-EVs have no battery consumption, bypass station reserve screening, and use ordinary utility/cost repositioning without charging navigation. EV utility, reserve checks, charging queues, timed arrivals and preferences remain unchanged. Fleet composition is checkpointed and validated. No full EV experiment was run.

## Gymnasium

`src.simulation.od_gymnasium.ODPricingEnv(runtime_factory, pairs, horizon=16)` wraps the existing runtime. The factory accepts `seed` and constructs fresh explicit configuration. Ordered feasible OD pairs define a fixed `MultiDiscrete([7]*N)` action vector; no support expansion occurs. Observations are `(N,13)` float32 pricing states. The scalar environment reward is successful-dispatch system revenue, with supported and fallback components in info; OD learner rewards are unchanged. Slot16 terminates; an explicitly shorter horizon truncates. Reset is required after either. The official checker passes against the real runtime with small synthetic request/fleet fixtures. Its two warnings about unbounded observation Boxes are intentional: no unsupported feature bounds or clipping are introduced.

## Checkpointing

The OD checkpoint stores hierarchy version/mode/settings, global/local weights, local Adam slots and counters, private memories, federation round, EV identity/composition, existing fleet/charging/RNG/OD state. Compatibility checks require the caller's hierarchy and composition contracts. A mismatched federation boundary or EV count fails closed. Deterministic private-local optimizer continuation and mixed-runtime checkpoint/resume are fixture tested.

## Activation limits

Learned routing is structurally integrated and fixture validated, but the prospective non-learned manifest cannot authorize learned online updates. That combination explicitly rejects startup. A separate online-learning provenance contract is still needed before activating this learned lifecycle in a prospective experiment. Historical learned checkpoint lineage remains incompatible. Weather availability remains assumption-based, and existing development-tuned methodology limitations remain.

## Validation

See tests.txt, final_tests.txt, checkpoint_tests.txt and validation.json. Tests cover exact EV composition, non-EV dispatch/energy, EV reserve/charging safety, normalized feedback, private releases, end-of-slot update timing, deterministic restore, official Gymnasium compliance, cutoff rejection and existing OD/replay/UTC behavior. Historical results and checkpoints are preserved. No new real-data episode was run.

Next task: define and validate the prospective online-routing information/provenance contract, including local experience cutoffs and next-slot policy availability, before authorizing any learned-routing experiment.

Final result: **54 distinct tests passed** across overlapping bounded batches (52, 12, 2, 1). The intermediate checkpoint JSON representation failure is retained as superseded evidence; both affected tests passed after correction. A separate actual-runtime fresh-global feedback fixture also passed. No remaining test failure. Historical preservation checks found no changes among 2,279 recorded files.
