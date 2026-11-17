# Causal CNN history and temporal protocol

## Status

`CNN_CAUSAL_HISTORY_ORACLE_WEATHER_V1` corrects historical-feature information timing
and makes issuance, targets, weather exceptions and DST handling explicit. It is
an offline, versioned **oracle-weather dataset**, not an operationally leakage-safe
forecasting system. No CNN/DQN training or production forecast replacement occurred.
Historical models, metrics, V3, OD contracts and sensitivity calibration are preserved.

## Existing behavior and label verification

`src/demand/final_cnn.py` uses the full January–February training means for
GridID×weekday×half-hour, with grid×half-hour and grid fallbacks. Every training
row contributes to its own lookup: 2,832×142 = 402,144 grid/time rows. Early training
origins also use future training dates. Training-only global normalization likewise
uses later training values. Holding out March does not remove these within-training
information issues.

Existing `Y(t)` is the demand in [t,t+30 minutes), and `forecast_timestamp` means
that target's start. This was verified against all saved development-prefix labels
(Jan1–Mar16). A blanket target shift would be incorrect. The new protocol leaves
those labels attached to the same valid target interval and adds issuance metadata.
The existing pricing artifact adapter reads the exact target timestamp but supplies
availability/observed-through timestamps itself; this does not prove the source
CNN's weather was available at issuance.

## New timing and chronological feature construction

Interpret naive TLC pickup-slot labels as New York civil time. Internally use
`America/New_York` aware timestamps and elapsed-time arithmetic:

- Target start: t.
- Target end: t+30 elapsed minutes, exclusive.
- Issuance: t−30 elapsed minutes.
- Feature information cutoff: issuance.
- Eligible historical demand: intervals ending at or before issuance.

Demand is assumed available at interval close; actual ingestion latency is not
measured. This explicit zero-latency assumption must be reconsidered for deployment.
Calendar features describe the target and are known in advance. Oracle target-time
weather is the explicit exception described below, never represented as causal.

The historical channel uses only earlier completed January–February observations,
with the same comparison hierarchy: grid/weekday/half-hour → grid/half-hour → grid.
Running sums/counts replace full-training lookup tables. Validation and development
test targets never update these statistics. Weather normalization uses only those
earlier training slots; historical demand is scaled by earlier training-demand
population SD. Zero SD uses scale one. This is a versioned scaling change, not
claimed numerical compatibility with old model weights.

No-history samples have an explicit `eligible=false` flag; their zero placeholder
is not a fabricated warm-up training observation. A future trainer must apply this
mask. Two January samples are ineligible. The builder does not silently pretend
a complete prior week exists.

## Weather provenance and unresolved availability

The inspected lineage is Meteostat 1.7.6 `Hourly(Point(...)).fetch()` in
`src/data/weather.py`, followed by renaming `temp`, `wspd`, `coco`, sorting and
forward/backward filling. It supplies retrospective observations, not archived
forecasts with issuance times. No archived forecast evidence appears in this
verified lineage; this was not a repository-wide archive search.

The source preserves naive weather timestamps without timezone transformation.
Their correspondence to NYC civil time is not proven. Existing filled values may
also depend on later observations. Therefore this version preserves existing
aligned values solely as **ORACLE_OBSERVED_TARGET_WEATHER**. It does not fabricate
forecasts, silently lag weather, or certify weather alignment. Operational export
is rejected. Archived ex-ante weather with verified issue/valid times, timezone and
availability is still required for an operational claim.

## March 8 DST findings

The legacy naive calendar contains 48 half-hours on March 8. New York civil time
has 46: 02:00 and 02:30 do not exist. The source contains 284 corresponding grid
rows, all zero-demand. They are retained as evidence in
`nonexistent_civil_slots.csv` and excluded only from the new version. No original
artifact is rewritten and no nonexistent interval is filled.

01:30 EST→03:00 EDT is 30 elapsed minutes. A target beginning 03:00 EDT is issued
01:30 EST; its target end is 03:30 EDT. Ambiguous fall-back civil times fail closed
rather than being guessed, although they are outside this source period.

The diagnostic reads Jan1–Mar16 only: 511,200 source rows, 3,598 retained valid
slots. Both original and new selected targets sum to **9,140,364** requests.

| Partition | Valid slots | Eligible slots |
|---|---:|---:|
| Training Jan1–Feb28 | 2,832 | 2,830 |
| Validation Mar1–15 | 718 | 718 |
| Development-only Mar16 | 48 | 48 |

The metadata uses the legacy name `test` for March16; this is development evidence,
not a final evaluation. March17–31 targets were not inspected or evaluated. No
claim is made about a completed protected test dataset.

## Spatial and downstream contract

Arrays retain seven channels, a 16×16 raster, 142 valid grids, and the exact saved
mask/grid mapping. Invalid raster cells remain zero. Labels remain actual counts;
forecast validation permits fractional nonnegative outputs and rejects NaN/Inf.
No model predictions were generated.

`validate_forecast` is an explicit new-artifact boundary: it checks version,
timezone, all four timestamps, complete grid coverage and finite nonnegative
values. Target t must equal the OD decision target, with no silent offset.
Oracle data is rejected for operational use. Research-only validation is explicitly
opt-in. The legacy OD runtime has naive-clock interval arithmetic, so the DST
crossing is rejected even at that research boundary rather than concealed by
stripping timezone offsets. No existing OD loader was replaced; historical
execution behavior remains unchanged. Operational integration must wait for the
weather/timezone and DST clock contracts to be resolved.

## Evidence and reproduction

- `src/demand/causal_timing.py`: versioned chronological builder and metadata guard.
- `scripts/validate_cnn_timing.py`: bounded development-prefix build and old-label check.
- `temporal_protocol.json`: timing, normalization, population hash and limitations.
- `sample_timing.csv`: issue/target/cutoff, partition, history support and eligibility.
- `X_oracle_development.npy`, `Y_development.npy`, `valid_mask.npy`: versioned diagnostic tensors.
- `nonexistent_civil_slots.csv`: DST exclusions without source modification.
- `test_results.txt`, `validation.json`: tests, hashes and preservation evidence.

Focused tests cover future/self-inclusion, held-out target isolation, exact timing,
oracle rejection, DST, tensor shape/mask, determinism and fractional forecasts.
Bounded existing CNN tensor/model and OD tests are retained. They construct/reload
small models but never fit them.

## Retraining and next task

Corrected feature histories/scaling differ from those used to train the existing
CNN. A new model must eventually be trained and evaluated; old weights cannot be
claimed corrected by metadata changes. No retraining is authorized or run here.

Next single task: establish verified weather issuance/valid-time and timezone
provenance, or explicitly approve a separately specified causal weather strategy.
Do not infer an operational forecast from retrospective observations. Thereafter,
resolve the naive OD DST boundary before promoting new predictions, and obtain
separate approval for a versioned retraining run.
