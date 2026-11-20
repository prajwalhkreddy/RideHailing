## Routing-to-pricing coupling validation — 2026-11-18

Bounded validation confirms that next-slot global routing probabilities enter the nine routing dimensions of the 13D OD pricing state and change unchanged-network Q outputs. Private utility still chooses physical driver actions. The prior fully exploratory, zero-pricing-update control therefore need not differ in assignments or revenue. Fifteen focused tests passed; no training was initiated. Evidence: `results_v2/federated_learning/2026-11-18_hierarchical_coupling_validation/README.md`. A frozen, separately authorized joint-learning protocol remains the next step.

## Online-routing reproducibility and control — 18 November 2026

The RNG discrepancy was the separately unseeded TensorFlow global Generator.
Research-run initialization now seeds it once; resume restores it. Historical
runtime behavior and scientific settings are unchanged. All 50 focused tests
passed. The four-slot learned run, independent repeat and checkpoint/resume
matched exactly, including RNG state. The matched no-update control completed:
routing probabilities changed, but dispatch/revenue/movement aggregates did not.
There were 19,342 genuine local updates and four NONPRIVATE FedAvg rounds;
pricing optimization remained disabled. No policy-improvement claim is made.
[Evidence and limitations](../../results_v2/federated_learning/2026-11-17_online_routing_rng_retry_002/README.md).

## Online-routing retry 001 — 17 November 2026

The mixed-fleet arrival reserve guard now exempts explicit non-EVs while retaining
historical EV safety. All 46 focused tests passed. The four-slot real-data run
completed with 19,342 genuine local updates and four equal-client NONPRIVATE
FedAvg rounds; checkpoint/resume matched exactly. The independent fresh repeat
stopped at slot1 because only the global RNG fingerprint differed. All other
compared state fingerprints matched. The no-update control was not run.
Pricing optimization remains disabled. Next: resolve RNG-state reproducibility
before continuing the bounded validation; no extended training is authorized.
[Retry evidence](../../results_v2/federated_learning/2026-11-17_online_routing_retry_001/README.md).

## Bounded online-routing attempt — 17 November 2026

The first real-data mixed-fleet attempt passed provenance/startup checks but
stopped before completing slot 1 at the post-arrival station-reserve guard.
An isolated regression confirms that this guard incorrectly applies EV battery
requirements to non-EVs. No routing or pricing optimizer update occurred.
Control/repeat/resume were not run after the safety stop. Forty existing tests
passed; the new non-EV arrival regression fails while the EV rejection passes.
Production code and historical artifacts are unchanged. Next: correct arrival
reserve applicability, preserve EV safety, and retry the bounded protocol.
[Attempt evidence](../../results_v2/federated_learning/2026-11-17_online_routing_experiment/README.md).

## Prospective online routing — 17 November 2026

A fresh-only routing initialization and online-experience provenance contract now
supports the versioned equal-client next-slot FedAvg interface. Historical learned
lineage remains rejected; prior sample-weighted and utility modes are preserved.
Updates remain off by default. Validation uses synthetic parameter updates and
small fixtures, with no gradient training or experiment launch. FedAvg is nonprivate;
weather availability and development-tuning limitations remain.
[Contract and evidence](../../results_v2/federated_learning/2026-11-17_prospective_online_routing/README.md).

## Hierarchical research interfaces — 17 November 2026

Opt-in driver-local routing/FedAvg lifecycle, deterministic mixed-EV composition
and a thin Gymnasium OD adapter are implemented and fixture-tested. Updates are
disabled by default; FedAvg is explicitly nonprivate. Historical V3 and the
non-learned research baseline remain available. Learned prospective activation
still requires an online-policy provenance contract. No training experiment ran.
[Architecture and bounded evidence](../../results_v2/simulation/2026-11-17_hierarchical_interfaces/README.md).

