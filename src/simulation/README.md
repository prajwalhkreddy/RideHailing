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
