# Prospective online-routing RNG correction and bounded validation

Started 17 November; completed 18 November 2026. **PASS: four-slot learned run, independent repeat, checkpoint/resume and matched no-update control.** This is development integration evidence, not final training or evidence of policy improvement.

## Root cause and first divergence

Two independent small processes were observed before changes (`diagnosis_a.json`, `diagnosis_b.json`, reproducible with `diagnose_rng.py`). Process-start Python, NumPy and TensorFlow states naturally differed. After the existing seed 42 call, Python and NumPy matched; only the TensorFlow global Generator differed. Model weights matched exactly. That Generator state remained unchanged through model construction, fleet initialization and repeated capture.

`src/simulation/v3_checkpoint.py:rng_bundle` calls `tf.random.get_global_generator()`. This separate generator was lazily initialized without an explicit seed. The existing `tf.keras.utils.set_random_seed(42)` did not initialize it in this environment. This is **differing RNG initialization (B)**, exposed by state capture, rather than defective serialization or demonstrated stochastic trajectory divergence. Capture hashes were stable within a process. The corrected primary reproduced the prior retry's runtime, hierarchy/local-optimizer, charging and pricing fingerprints exactly; only the formerly unseeded global RNG state changed.

## Minimal correction

Only the research experiment runner adds `initialize_experiment_rng(42)`: existing Keras seeding plus `tf.random.set_global_generator(tf.random.Generator.from_seed(42, alg='philox'))`, once at fresh-run entry. Resume does not initialize again; it restores the checkpoint RNG bundle. No per-slot reseeding, ignored fingerprints, changed sampling rules or production/historical checkpoint changes were introduced.

The runner now records fingerprints by RNG domain at process initialization, run initialization, routing-model initialization, fleet initialization, before slots and after each completed slot. The independent repeat matches from run initialization onward. Unseeded process-start differences are retained as evidence. The entire prior global RNG fingerprint assertion remains active.

## RNG inventory

| Domain/component | Ownership and use |
|---|---|
| Python `random` and NumPy global | Existing Keras model construction seeds these; captured/restored by checkpoint. Local model construction uses seed 42 + driver ID + 1. |
| Keras/TensorFlow initialization | Existing seeded Dense initializers; exact initial and learned weights validated. No dropout or stochastic optimizer minibatch selection. |
| TensorFlow global Generator | Previously unseeded lazy generator; now explicit Philox seed 42 at fresh research entry. No state advancement observed in these four slots. |
| Pricing RNG | Learner-owned NumPy Generator seed 42; epsilon-greedy actions. No replay sampling or optimizer updates. |
| Passenger sensitivity | Provider-owned NumPy Generator seed 43, request-weighted conditional empirical sampling. |
| Fleet locations / initial SOC / EV composition | Existing separate seed 42 NumPy generators; unchanged initialization and exact 500/4,500 composition. |
| Local routing minibatch | Deterministic latest available observations; no random shuffling or sampling. Persistent local Adam. |
| Dispatch and physical routing | Existing deterministic eligibility/FCFS and private utility decisions, not global NumPy draws. |
| Charging queue | Infrastructure-owned seed 42 Generator for tie priority; preserved in charging state. Zero charging events here. |
| Legacy request/customer objects | Existing owned generators retained; historical replay bypasses synthetic request generation. |

The correction does not mutate independent NumPy Generator instances. In the control, Python/NumPy global states differ after the learned arm constructs local models and the control does not. This expected difference between **different protocols** is documented, not suppressed. Active pricing/sensitivity streams remain independently owned. No difference in dispatch/revenue/movement aggregates occurred. The full runtime hashes differ because routing probabilities, pricing states and replay next states differ.

## Frozen configuration and information boundary

March 12 00:00–02:00 America/New_York / 04:00–06:00 UTC; four 30-minute slots, 120-second mini-slots; 5,000 vehicles, 500 EVs/4,500 non-EVs; seed 42. January OD support, January–February sensitivity, existing reference-price OD fallback, causal research historical-average forecast and 120-minute assumed weather persistence are unchanged.

Fresh 169→64→32→9 routing, Adam 0.001, batch capacity 32, one epoch, memory 1000 and equal-participating-client NONPRIVATE FedAvg are unchanged. Global updates become available at the next slot boundary. Pricing optimizer updates remain zero. Historical routing weights were not loaded; March 17–31 was not accessed. Inherited development-tuning and decision-time weather availability limitations remain explicit in the reused provenance contract.

## Learned execution and reproducibility

All four slots passed finite gradient/weight/loss, equal-client aggregation, masked-probability, fleet/EV, UTC and reward checks. The run performed **19,342 genuine local optimizer updates**, **47,670 sample presentations** and **four FedAvg updates**, producing **38,288 replay transitions**. Every global update changed parameters. No synthetic updates were used in these real-data runs.

The independent fresh repeat matched every completed-slot fingerprint, including Python, NumPy and TensorFlow RNG. Slot 2 checkpoint restoration and resumed slots 3–4 matched exactly: local/global weights, optimizer states, private memories, fleet/charging, RNG and pricing state. The TensorFlow global Generator remained at its explicitly initialized state throughout, confirming it was not driving observed trajectory randomness.

## Matched control

| Metric | Learned routing | No-update control |
|---|---:|---:|
| Eligible requests | 4,137 | 4,137 |
| Accepted / rejected | 1,192 / 2,945 | 1,192 / 2,945 |
| Assigned / accepted-unmatched | 996 / 196 | 996 / 196 |
| Successful-dispatch revenue | $21,934.508396884783 | $21,934.508396884783 |
| Routing updates | 19,342 | 0 |
| Charging events | 0 | 0 |

Source accounting remains 4,215 rows = 78 unchanged-invalid exclusions + 4,137 eligible; 4,135 supported + 2 fallback. Fleet composition is conserved; energy and non-EV bypass checks pass. Repositioning action counts, boundary repositioning-vehicle counts and EV energy totals match by slot; charging-state hashes match exactly.

Mean absolute differences between learned/control routing-response probabilities at the four boundaries were **0.007878,0.018982,0.031760,0.048715**. Thus next-state routing feedback changes, while outcomes remain equal. Pricing epsilon stays 1.0 because pricing optimizer updates are disabled; physical routing retains private utility decisions. This experiment validates integration and determinism, not improved policy performance. Zero charging activity limits real-data charging conclusions; focused safety tests remain the supporting evidence.

## Tests and performance

**50 focused tests passed in 66.922 seconds**, including independent subprocess initialization, owned-stream preservation, stable capture, RNG restore, identical model weights, slot-boundary RNG, arrival/EV safety, historical defaults, provenance, checkpoint, UTC, replay and OD fallback. Small provenance fixtures are not presented as genuine gradient evidence; the real runs supply that evidence.

Primary measured slot time: **593.08s**; repeat 590.86s; control 163.25s. Peak primary RSS: **3,859,267,584 bytes** on macOS. These timings exclude startup, checkpoint serialization and post-slot fingerprinting. The previous primary took 579.49s, so this primary was 2.35% slower; this uncontrolled wall-clock difference does not isolate RNG overhead. The correction executes once at startup and adds no per-update or per-slot reseeding. No optimization study was performed.

## Evidence, changes and preservation

- `configuration.json`, `preflight.json`, `validation.json`: configuration, Git/source hashes, provenance and completion checks.
- `diagnosis_a.json`, `diagnosis_b.json`, `diagnose_rng.py`: pre-correction first-divergence evidence.
- `rng_domain_fingerprints.csv`, `*_rng_stages.json`: compact per-domain observations.
- `*_slot_metrics.csv`, `*_request_reconciliation.csv`, `*_probabilities.npz`: bounded execution evidence.
- `control_comparison.csv`: outcome/action/probability/state comparison.
- `*_checks.json`, `*_complete.json`, restricted run logs and `slot2_checkpoint/`: repeat/resume and private checkpoint evidence. Private checkpoint data must not be treated as platform-facing reports.
- `tests.txt`: focused results.

Implementation changed only `scripts/validate_online_routing_experiment.py`; added `tests/test_online_experiment_rng.py`. Relevant root/routing/simulation READMEs were updated. Historical implementation, failed/partial experiments and model checkpoints were preserved; 2,279 historical paths match the existing size/mtime preservation manifest. No extended training occurred.

## Recommended next single task

Freeze the next bounded hierarchical evaluation protocol, explicitly defining pricing exploration and routing-feedback outcome measurements before further experiments. This successful engineering validation does not finalize learned-routing quality, privacy, weather availability or policy performance.
