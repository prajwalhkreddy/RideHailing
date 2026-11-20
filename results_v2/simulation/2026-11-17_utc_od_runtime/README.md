# UTC elapsed-time OD runtime

## Contract and scope

`OD_AWARE_UTC_ELAPSED_V1` is an opt-in research interface selected by supplying
`utc_inputs` to `ODPricingRuntime`. It automatically enables the master EWMA and
squared Bellman contracts. All runtime event instants, ledger boundaries,
commitments, replay identities and checkpoint cursors are aware UTC. Historical
V3 and the default historical OD interface retain their original conventions.
No training was performed. Tests use two-vehicle deterministic fixtures, fixed
pricing actions and synthetic fractional forecasts, not a production episode.

## Boundaries and reused mechanics

At initialization, a naive caller start is interpreted strictly as New York civil
time and converted to UTC. Persisted naive TLC pickup/dropoff labels are localized
once when a request batch is loaded; ambiguous/nonexistent times reject rather
than silently dropping rows. Source Parquet filters use NY civil labels because
that is the source storage convention. UTC event arithmetic never uses those naive
labels. Source identity, ordering and eligible counts are retained; elapsed trip
duration is calculated from UTC pickup/dropoff instants. For example, 01:01 EST to
03:31 EDT is90 minutes, not150 minutes. This corrects civil-clock subtraction.

The original production engine's event loop, dispatch, fleet, routing and timed
charging implementations are reused. Optional initialization/state-source hooks
supply UTC ledger and snapshot adapters. Legacy initialization follows the original
branch. No complete engine was duplicated. Priors and the unused historical customer
resource are initialized through their existing local-time source boundaries once;
they do not set the simulation clock. Operational state immediately uses UTC.

Slots are30 elapsed minutes, mini-slots120 seconds. Requests are ordered by pickup
instant then stable source identity; dispatch occurs at the actual within-slot
offset. Dispatch diagnostic timestamps include the offset rather than rounding down
to mini-slot start. Immediate contention still implies zero passenger queue wait;
this migration does not introduce a new pending-passenger queue or waiting policy.
Driver idle waits, travel countdowns, charging waits and energy increments retain
elapsed-minute units. The existing16-slot horizon remains unchanged; terminal
transitions do not bootstrap, and subsequent slot calls reject before mutation.

## Forecast and weather interface

`utc_inputs` contains:

- `forecasts`: UTC target-keyed DataFrames with142 Grid_ID values, fractional
  nonnegative `predicted_demand`, aware issuance/target/cutoff timestamps and weather
  observation/assumed-availability timestamps.
- `weather_contract` and `checkpoint_metadata`: the exact versioned120-minute
  persistence contract and its fingerprint; oracle identities reject.
- `channels`: the existing ordered seven CNN channels; `grid_ids`:0 through141.
- `popularity` and aware `popularity_available_at`: explicit causal ordinal values.
- `realized_weather`: UTC slot-keyed actual weather codes for sensitivity experiments.

Issuance/cutoff are target−30 elapsed minutes; target end is target+30 minutes.
Observation+120 minutes must not exceed issuance. Forecast timestamp fields must
be timezone-aware. The new UTC snapshot path removes the old naive-clock DST
bridge restriction, while retaining all timing/grid/value checks. The historical
forecast loader is not consulted in UTC mode. No real CNN predictions are generated
or relabeled by this task.

NY local time is derived once per pricing slot for T1–T4 selection; all arrivals
inside that slot share the calendar group. Realized sensitivity weather remains
distinct from the forecast persistence input. Weighted calibration is unchanged.
The bundle is explicit and preserved in checkpoints; callers must supply verified
provenance for real research predictions. Synthetic fixtures are not evidence of
forecast accuracy or historical publication availability.

**Operational mode remains blocked:** publication/vintage provenance is unverified.
The120-minute assumption is research-only, not an archived forecast. This is now a
weather-information limitation, not a UTC engine limitation.

## Checkpoints

Schema `FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_5` identifies UTC versus historical
clock mode, mathematical mode and research forecast provenance. Loads require
`master_math=True, utc_mode=True` for this new mode; old/differently timed contracts
reject. Pending commitments, event cursors, charging queues, movement countdowns,
fleet state, RNG, pricing networks, optimizer and replay are serialized by the
existing codec through a narrowly scoped OD adapter. The historical codec is
unchanged. File/component hashes protect the saved forecast bundle and runtime;
source hashes include all three UTC adapters. No existing checkpoint is overwritten.

## Validation

42 focused/bounded regression tests passed in41.779 seconds. Evidence includes:

- Historical request loading, exact source counts and stable mini-slot order.
- Dispatch and assignment-fare reward reconciliation with UTC commitments.
- A checkpoint at01:30 EST restored before crossing to03:00 EDT; subsequent
  fleet state, pending-trip completion, OD states and replay identities match.
- Charging state checkpointed before DST and resumed across it with identical
  fleet and charging infrastructure; energy stays within capacity.
- Thirty elapsed charging/idle-wait minutes across DST yield the expected energy
  increment and30-minute wait, not90 minutes.
- Repositioning across01:59→03:00 retains hop duration, arrival grid and exact
  distance-based energy deduction.
- Ordinary16-slot termination and rejection of a seventeenth slot.
- Oracle/forecast-timing rejection, master mathematics, historical OD behavior,
  operational-state and CNN/persistence timing regressions.

A strengthened future-arrival assertion was subsequently added: both pending trips
appear in the03:30–04:00 EDT bucket. All7 UTC integration tests passed again
(24.439 seconds; `arrival_check_tests.txt`).

The saved preservation manifest reports2,279 historical artifacts unchanged.
No historical results or model checkpoints were edited. Shared production code
changed only via opt-in hooks; historical branches are exercised by regression
fixtures. Tests are not a full production replay or a performance benchmark, so no
claim of measured throughput equivalence is made. Timezone conversion is batched
at request ingestion and performed once per slot for sensitivity classification.

Reproduce with the project Python environment:

```
python -B -m unittest tests.test_utc_od_runtime tests.test_od_pricing tests.test_master_od_math tests.test_operational_grid_state tests.test_persistence_weather tests.test_cnn_causal_timing
```

## Remaining limitations and next task

UTC integration passes bounded tests. Real operational forecasting remains blocked
by missing publication/vintage evidence. Continuous-weather sensitivity alignment
and other previously documented methodological decisions remain open. Nonexistent
or ambiguous source civil timestamps fail closed and require source review; no
silent corrections are made. The protected post-development period is not replayed.

Next single task: perform a bounded, no-training OD research acceptance run with an
explicitly validated forecast artifact and weighted sensitivity contract, reporting
its research-only weather assumption. Do not launch model training from this result.
