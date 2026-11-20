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

## Prospective utility-baseline acceptance — 17 November 2026

The opt-in non-learned private-utility routing baseline completed March12’s four-slot
engineering acceptance with 5,000 vehicles and January–February sensitivity.
All 4,137 eligible requests reconciled; 996 assignments produced $21,934.5083968848.
Deterministic repeat/resume and 48 focused tests passed; no training occurred.
The earlier learned-routing lineage remains blocked and unchanged. This research
baseline does not establish policy effectiveness or verified weather availability.
[Evidence](../../results_v2/simulation/2026-11-17_prospective_utility_acceptance/README.md).

# Historical observed-request replay

`HISTORICAL_REQUEST_REPLAY_V1` is the primary demand protocol of the opt-in
`ODPricingRuntime`. It retains `FEASIBLE_OD_PRICING_V1` and
`SUCCESSFUL_DISPATCH_REWARD_V1`. Historical `SlotPricingV3` and
`ProductionExperiment.requests_for_slot()` retain their previous behavior.

## Forecast and realized demand

At decision time t, the OD state receives the existing CNN snapshot's predicted
origin count for `[t,t+30min)`. It remains nonnegative and potentially fractional.
The existing snapshot exposes `available_at` and `observed_through`; the current
adapter records the latter as t−30min. This change preserves those availability
checks and does not independently certify the CNN training/feature pipeline.

All supported OD actions are selected **before** historical requests are loaded.
No realized count, source fare, destination list or future pickup is supplied to
the pricing learner. The source is then filtered by actual pickup timestamp to
`[t,t+30min)`, independently of forecasts. Requests enter dispatch at their exact
within-slot offsets, inside the existing fifteen two-minute mini-slots.

Observed eligible pickups determine `realized_requests` in `demand_audit`.
Passenger acceptance is subsequently simulated; successful assignment is a
separate outcome. Request audits retain both. OD slot audits distinguish
`generated`, `accepted`, `rejected`, `assigned`, `accepted_unmatched`, descriptive
accepted revenue and learning/assignment revenue. The current state and replay
retain the separate CNN input. Neither acceptance nor assignment changes the
historical request count or reconstructs the CNN forecast.

## Source, identity and eligibility

Read the existing `data/processed/spatial_3km_jan_mar_2026/trips_jan_mar_2026.parquet`
using an exact slot filter. Preserve observed PU/DO grid IDs, pickup/dropoff
timestamps, distance, fare and duration. Valid source timestamps have microsecond
resolution. Order by pickup timestamp, then `source_file_month`, then
`source_prepared_row`. Encode the stable identifier as month × 10^12 + prepared
row, with enforced integer/range/uniqueness checks. Request audits also retain
both original identifiers and observed fare, distinct from the offered fare.
No timestamps, destinations or missing trip attributes are fabricated.

Eligibility reuses the generator's finite, nonnegative fare/distance and finite,
positive-duration rule. Invalid trip attributes are counted explicitly. Spatial
mapping, temporal mismatch, missing fields or invalid source identity fail closed.
An eligible OD outside the January feasibility mask aborts the slot explicitly;
it is never silently removed or used to extend training support. The unfinished
runtime cannot continue or checkpoint. Restore the last committed snapshot.
Broader unsupported-OD handling needs a research decision.

TLC observed pickups are a **proxy for request arrivals**: they do not identify
latent requests that never became recorded trips. Observed durations/distances
are replay attributes for counterfactual simulation, not a new travel-time model.
Source fare is provenance; the OD policy still offers common P_base × action.

## Chronology

The existing research split remains: January–February CNN training; March1–15
hierarchical RL training/development; March16 development only; March17–31
protected final evaluation. Replay currently rejects protected dates before
reading data. No final evaluation is authorized by this implementation. January
alone constructs OD support. Replay does not fit sensitivity or choose parameters.
Existing timestamps remain project-local, timezone-naive; no new DST repair.

## Historical alternative

The unchanged historical generator rounds nonnegative CNN origin forecasts,
zeros origins without empirical support, then samples intact January trips with
replacement. It exactly conserves the resulting supported integer input counts,
**not** historical pickup totals or fractional forecast totals. It preserves
January-supported OD pairs and sampled within-half-hour offsets, not exact
historical calendar demand. January-only sampling isolates its source from
protected evaluation; this alone does not resolve independent CNN provenance gaps.

## Persistence and scalability

`FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_2` persists the demand identity/source,
next-slot cursor, completed-slot count, request count/cursor, last ordering hash,
mode and existing environment/OD/learner/RNG state. Replay itself uses no RNG.
Checkpoints are permitted only at complete slot boundaries, so no partially
consumed request queue is required. Incompatible demand protocols and earlier
OD/runtime schemas are rejected rather than silently reinterpreted.
Explicit request injection is retained for tests and labeled
`EXPLICIT_REQUEST_FIXTURE`, never reported as observed-source replay.

Inference uses batches of at most 1,024 contexts while preserving per-context
exploration RNG order. Requests are grouped once for OD reporting. The unchanged
9,572-pair January mask avoids a full 20,164-pair Cartesian expansion. Each
historically supported pair remains a proactive decision/replay context, including
zero-request slots: absence of future demand is unknown at decision time. Changing
this policy requires a justified causal relevance rule. At 16 slots there are
153,152 transitions; the unchanged 100,000 FIFO capacity evicts the oldest with
synchronized identity metadata. Memory timings report array/frame payloads only,
not full process or checkpoint size.

## Bounded reproduction

```sh
TF_CPP_MIN_LOG_LEVEL=3 PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/reward_validation_mpl python -B scripts/validate_historical_request_replay.py --output results_v2/simulation/a_new_validation_run
```

Use the established TensorFlow environment and a new output directory. This runs
fixtures and one source-slot count reconciliation, plus a full-support inference
measurement. It does not train or run a multi-episode experiment. Source/config
hashes, Git state, seed, reconciliation, timing and test outcomes are saved.

## Versioned CNN timing boundary

The [new CNN timing evidence](../../results_v2/cnn_demand/2026-11-17_causal_timing/README.md) preserves target-start alignment but does not replace runtime forecasts. Oracle weather is rejected operationally; the legacy naive OD clock also cannot silently represent a spring-forward issuance crossing. Resolve these contracts before forecast promotion.

### Assumption-based CNN weather boundary

The new `src.demand.persistence_weather.validate_persistence_forecast` adapter
validates research forecast metadata without changing historical OD consumption.
It preserves fractional demand, rejects oracle/checkpoint mismatches and fails
closed on the legacy DST bridge. Actual publication availability and consistency
with realized passenger weather remain unresolved.
[Evidence](../../results_v2/cnn_demand/2026-11-17_observation_persistence/README.md).

## Earlier OD mathematical correction status (temporal limitation superseded)

Opt-in `master_math=True` implements previous-mean absolute-deviation EWMA and
half squared Bellman loss. UTC boundary helpers are tested, but the inherited
engine/ledger clock migration remains incomplete. Operational startup fails closed;
no training started. Historical V3 is unchanged.
[Contract, validation and exact remaining work](../../results_v2/simulation/2026-11-17_master_math_temporal/README.md).

## UTC OD research runtime

`OD_AWARE_UTC_ELAPSED_V1` now integrates UTC request/event flow, master mathematics
and checkpoint restoration through the inherited engine. DST trip, charging and
repositioning checks pass; 42 bounded tests passed. Historical V3 is unchanged.
Operational forecasts remain blocked by unverified weather availability; no training
was performed. [Evidence and input contract](../../results_v2/simulation/2026-11-17_utc_od_runtime/README.md).


## Real-data OD acceptance gate — 17 November 2026

March12 00:00–02:00 NY bounded research acceptance completed all four slots and
4,137 eligible requests. Explicit `VALID_UNSEEN_OD_REFERENCE_PRICE_V1` served two
January-unseen pairs at factor 1.0, without expanding support or adding fallback
DQN transitions. Total revenue $22,254.5750635514 includes $44.7083968848 fallback
revenue. Repeat/resume passed; no training occurred. January historical-average
forecasts are a labeled baseline, not trained CNN output. Frozen sensitivity remains
retrospectively calibrated through March15; prospective information timing remains
unresolved. [Preflight evidence](../../results_v2/simulation/2026-11-17_end_to_end_acceptance/FALLBACK_ACCEPTANCE.md).

## Prospective OD information cutoff — 17 November 2026

The versioned January–February request-weighted sensitivity calibration contains
5,457,435 observations (weighted mean 1.725916, population SD 0.426314).
Prospective startup is **blocked**: the routing snapshot’s direct updates end
before March12, but its generated training requests inherit CNN model selection
using March1–15 validation. The new information guard rejects this lineage.
No prospective replay or training ran; earlier retrospective acceptance evidence
remains unchanged. Grouping/reference choices remain development-tuned.
[Cutoff evidence and next step](../../results_v2/simulation/2026-11-17_prospective_acceptance_v1/README.md).
