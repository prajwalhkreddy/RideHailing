# Observation-persistence weather protocol

## Status

`CNN_OBSERVATION_PERSISTENCE_ASSUMED_AVAILABILITY_V1` is a separate,
assumption-based research baseline. It is **not an archived weather forecast,
not verified historical decision-time information, and not operationally ready**.
No model was trained. Historical CNN models, oracle tensors, OD runtime and
`REQUEST_COUNT_WEIGHTED_BINNED_SENSITIVITY_V1` remain unchanged.

## Provenance and limitation

The active concatenated weather artifact is
`data/processed/spatial_3km_jan_mar_2026/weather_jan_mar_2026.parquet`.
Its metadata points to three monthly processed Meteostat artifacts. The ingestion
function `src/data/weather.py:fetch_hourly_weather` invokes Meteostat 1.7.6
`Hourly(Point(...), start, end).fetch()` without a timezone argument. The installed
`meteostat/utilities/mutations.py:localize` explicitly localizes the native time
index as UTC before converting to a requested timezone. Thus the new adapter
interprets these naive source labels as UTC, then maps to America/New_York.
Historical joins preserved those labels without conversion; they are not rewritten.
The resulting weather alignment differs by five hours in winter and four after DST.

Fields are `Datetime`, `WeatherCode` (Meteostat category), `Temperature` (Celsius),
and `WindSpeed` (km/h). Labels have hourly cadence; exact measurement intervals
and aggregation conventions are not recorded in these artifacts. Ingestion applies
forward then backward filling, but all three monthly metadata files report zero
missing cells before and after filling. Therefore that local fill changed no values.
This does not prove the provider performed no interpolation or filling.

Meteostat's constructor defaults to `model=True, flags=False`. Model-filled values,
spatial processing and later revisions cannot be separated from observations here.
No publication timestamps, data vintages or archived forecast issuance records are
present in the inspected lineage. August/October build timestamps are extraction
provenance, not January/March availability times. Source availability is unverified.

## Explicit research assumption

The bounded validation uses a **120-minute assumed lag**, consisting of a
one-hour allowance for hourly observation support plus a one-hour assumed delivery
allowance. Neither allowance is a measured publication latency. This is a transparent
research assumption, not a new operational fact or guarantee against retrospective
provider revisions. The API requires an explicit lag of at least 60 minutes.

For a target `[t,t+30 elapsed minutes)`, issuance and feature cutoff equal
`t-30 elapsed minutes`. Select the latest complete observation satisfying
`source_UTC_label + assumed_lag <= issuance`; carry its category, temperature and
wind forward. Never use target-time weather. Missing/incomplete observations are
skipped in favor of the latest complete eligible observation. If none exists,
reject the batch as containing an ineligible sample. There is no backfill from the
future and no invented weather category. Stale observations remain explicitly aged;
no scientifically unsupported age threshold is introduced.

`weather_availability_contract.json` records the assumption and units.
`sample_timing.csv` records every selected source time, assumed availability, age,
issuance, target interval, eligibility and contract fingerprint. The script validates
features in memory; it does not overwrite or persist new training tensors.

## Timing, counts and OD boundary

The shared `causal_timing.timing` mapping is reused. March 8 03:00 EDT is issued at
01:30 EST, exactly 30 elapsed minutes earlier. Nonexistent 02:00/02:30 civil slots
are quarantined, never invented. The 284 source grid rows have zero demand.

Jan 1–Mar 16 development-prefix validation: 511,200 source rows, 3,598 valid
half-hour samples, 3,596 history-eligible samples; 2,832 training samples (2,830
eligible), 718 validation samples and 48 March 16 development samples. The inherited
`test` split label denotes March 16 development only in this package. Targets and
9,140,364 demand counts match the preceding timing package exactly. Seven channels,
16×16 raster and 142-cell mask are retained. Source weather was restricted to UTC
labels before March 17; late March 16 therefore carries older available weather.
Observed ages range from 120 to 240 minutes. Availability-order violations: zero.
March 17–31 target observations were not read.

`validate_persistence_forecast` provides an explicit opt-in OD export boundary:
exact 142 grid IDs, finite nonnegative fractional predictions, matching issuance,
target and cutoff, matching weather contract/checkpoint fingerprint, and observation
availability checks. Oracle/version-mismatched checkpoints are rejected. Research
use requires `research=True`; operational use always rejects this unverified source.
No existing checkpoint is relabeled. This adapter is not silently installed into the
historical OD loader. The legacy naive-clock OD spring-transition bridge remains
fail-closed; full timezone-aware OD execution requires a separate bounded change.
Historical replay request timestamps and counts remain unchanged.

## Passenger sensitivity

The weighted sampler still uses the existing weather-code and local T1–T4 pools
(T1 00–03, T2 04–05, T3 06–15, T4 16–23). Its realized/retrospective weather is not
the new issuance-time persistence input. Category vocabulary is shared; temporal
information availability and legacy timezone alignment are not. Temperature and
wind are CNN features only. No new passenger conditioning is introduced and full
cross-module weather-information alignment is not claimed.

## Validation and next task

31 focused/bounded tests passed across persistence, causal timing, CNN tensor/model
contracts and OD pricing. Checks cover lag/age, future-weather isolation, missing
weather, DST, deterministic shape/mask, fractional exports, checkpoint/version
rejection and historical behavior. The bounded empirical check also confirms exact
unchanged labels and demand counts. A saved preservation manifest verifies all
2,279 historical files unchanged by size/mtime. A Keras optimizer-load warning in
an existing synthetic save/reload test is unrelated to this weather protocol.

Reproduce with the project Python environment:

```
python -B scripts/validate_weather_persistence.py
python -B -m unittest tests.test_persistence_weather tests.test_cnn_causal_timing tests.test_cnn_model tests.test_cnn_tensors tests.test_od_pricing
```

Assumption-based research training can now be specified explicitly; **verified causal
operational training is not ready**. Next bounded task: decide/verify an acceptable
historical weather-availability and vintage contract (including model-filled data)
before approving a research training run. Separately, the OD DST bridge and realized
passenger-weather timing need resolution before operational promotion. No training
or simulation is authorized or started by this package.
