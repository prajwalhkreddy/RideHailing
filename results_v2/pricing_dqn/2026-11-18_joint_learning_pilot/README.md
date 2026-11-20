# Bounded joint OD pricing and routing pilot

Status: **PASSED — primary, independent repeat and checkpoint continuation.** This is a four-slot March12 development pilot of a future 16-slot design, not extended training or an efficacy claim.

## Frozen protocol

Seed42; 5,000 vehicles, 500 EVs; 30-minute UTC slots and 120-second mini-slots. Shared 13→64→64→7 OD DQN, Adam0.001, gamma0.99, replay100000, batch64, warm-up1000, epsilon1→0.05 over50000 optimizer steps, target tau0.005. Eight updates after a completed warm slot reuse the documented cadence in `src/simulation/v3_episode1_protocol.py`; the new learner uses half mean squared Bellman error and maximum target-network Q bootstrap. Four-slot stopping is truncation, not the16-slot terminal. Pricing factors and sensitivity contracts are inherited unchanged.

January OD support/popularity/historical-average demand, January–February weighted sensitivity and fresh prospective NONPRIVATE equal-client FedAvg routing are retained. Routing uses169→64→32→9, Adam0.001, batch32, one local epoch, memory1000. No selected CNN or historical routing weights enter this pilot. Weather availability remains assumption-based120-minute persistence. Inherited development-selected hyperparameters do not establish independent model-selection provenance. March17–31 remains protected.

## Preflight and bounds

31focused tests passed:30existing math, coupling, provenance, arrival and OD tests plus one documented-warm-up/real-step/epsilon/target test. Source hashes and parameters are in `frozen_protocol.json`. Estimated four-slot work:38,288transitions and approximately19,342routing updates; approximately4GiB peak memory;30–45minutes including independent repeat, resume and serialization. Prior recovery checkpoint measured1.1GiB; retain at most one recovery and one final checkpoint. Available space at preflight approximately221GiB.

Initial preflight correctly rejected the original pre-arrival-fix provenance. `initial_preflight_blocker.json` and `source_mismatch.json` preserve it. The corrected manifest in the prior retry directory exactly equals the successful RNG-retry experiment's recorded routing and information contracts; it is reused without editing fingerprints or weakening checks.

## Validation plan

Successful primary is followed only by an independent deterministic repeat and slot2 checkpoint continuation. Existing guards check finite local gradients, equal-client means, routing masks/probabilities, fleet/EV invariants, UTC boundaries, acceptance and successful-dispatch reward. Additional assertions check pricing losses, optimizer count, finite parameters, parameter changes, replay reward and nonterminal truncation. No matched control or extension is authorized here.


## Completed results

Four slots completed: 4,137 eligible requests, 1,144 accepted, 2,993 rejected, 975 assigned and 169 accepted-unmatched. Successful-dispatch revenue was $21,605.02506355145. Reward/replay assertions passed. Source reconciliation retains 4,215 rows = 78 unchanged-invalid exclusions + 4,137 eligible; 4,135 supported and two fallback requests.

There were 38,288 OD transitions and 32 pricing updates (eight per slot), without lowering warm-up or fabricating transitions. Epsilon ended at 0.999392. Pricing loss ranged from 0.36721277 to 452.76174927. Finite-gradient guards passed and parameters changed. Gradient tensors are not persisted; guards, optimizer iterations, losses and fingerprints provide compact update evidence. The final boundary is nonterminal truncation.

Routing performed 19,344 optimizer updates, 47,658 sample presentations and four equal-client FedAvg rounds. Aggregation and subsequent-state feedback passed. Fleet composition stayed at 500 EVs and 4,500 non-EVs. No charging events occurred; charging safety coverage relies additionally on focused fixtures.

Every independent-repeat slot fingerprint matched. Immediate slot2 restoration and resumed slots3–4 matched exactly, including pricing weights/optimizer, routing local/global state, fleet, replay and RNG. Per-update pricing losses, epsilon and rewards also match. Primary slot execution took 587.48 seconds, excluding startup, serialization and fingerprinting. Exact peak RSS and checkpoint sizes are in `validation.json`. Only recovery and final full checkpoints are retained.

## Changes, limitations and next task

New runner: `scripts/validate_joint_od_pilot.py`; new test: `tests/test_joint_od_pilot.py`. Production source, historical models/results and protected periods were unchanged. This directory contains protocol, provenance, compact metrics/checks, two checkpoints, logs and final validation. Preserved `primary_blocker.json` describes the initial outdated-manifest rejection, not current status; `validation.json` records completion.

No correctness blocker remains within the bounded pilot. This is not convergence or policy-efficacy evidence: exploration remains near-random, the window is two hours, weather availability is assumed, routing is NONPRIVATE and inherited hyperparameters retain development-selection caveats. The later-selected Softplus CNN was not used.

Recommended next single task: separately approve a bounded 16-slot joint-learning development protocol and evaluation plan. No extension was executed.
