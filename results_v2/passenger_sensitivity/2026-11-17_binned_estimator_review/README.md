# Provisional binned passenger-sensitivity calibration

## Status and authority

The master §3 distance-binned estimator is implemented and a versioned empirical
sampler is available **only by explicit opt-in**. This is not final numerical
calibration or full master compliance. The user authorized provisional completion
while continuous-weather conditioning remains an **OPEN METHODOLOGICAL DECISION**.
No pricing, CNN or routing training was performed. Historical V3 remains unchanged.

Use `final_validation/` for corrected estimator, comparison and OD evidence, and
`provisional_sampling/` for current sampling, family comparison, weather availability
and tests. Earlier files directly in this directory are preliminary: their RAW
pools used assigned requests instead of complete historical fallback pools. They
are superseded by `final_validation/`. The estimator-only blocked status recorded
in `final_validation/calibration_contract.json` and its validation snapshot is
superseded, for bounded opt-in sampling only, by
`provisional_sampling/sampling_contract.json`; scientific limitations remain open.

## Population and common references

Reuse `data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet`:
6,967,155 observations, January 1–March 15 inclusive, 1.5 ≤ distance < 75 km.
This is the existing fare/distance-eligible population, not a new raw preparation.
The previous trip estimator additionally applied its recorded denominator/sign
eligibility, leaving 5,779,213 positive runtime candidates. Both comparisons start
from the same 6,967,155 rows; their statistical observation units differ.

Common references are retained provisionally: **Pbase = 22.354198442390455 USD**;
**Lbase = 4.616983790655043 km**. Existing provenance is a count-weighted fare mean
on the earlier [1,75) km population and an interpolated fare-distance crossing.
These are not the master's observed-fare/representative-distance selection rule.
No reference is silently recomputed or asserted finally master-aligned. Evidence:
existing V2 numerical freeze and denominator-rule notation contracts, fingerprinted
in `final_validation/validation.json`.

## Estimator and comparison

Use left-closed, right-open 0.5-km bins with origin zero. For every occupied bin,
retain request count and ordinary mean fare. Calculate

`epsilon = ((bin_lower_km - Lbase)/Lbase) / ((mean_fare - Pbase)/Pbase)`.

Exact zero price deviation is undefined (NaN with explicit status); there is no
near-zero threshold, clipping or absolute-value transformation. Negative and zero
bin estimates remain in diagnostic tables. All 147 pooled bins are positive;
several conditional pools have one negative estimate. No trip is deleted.

| Empirical observations | N | Mean | Population SD | Median | Minimum–maximum |
|---|---:|---:|---:|---:|---:|
| Historical eligible positive trip estimates | 5,779,213 | 1.807321 | 1.990089 | 1.154356 | 0.000081633–286.512406 |
| Pooled bin estimates | 147 | 2.257965 | 0.339971 | 2.330456 | 1.356305–2.856160 |

Aggregation changes the estimand; lower SD is not evidence of a superior model.
The request-count-weighted bin mean is 1.715299, reported only as a diagnostic.
The provisional empirical sampler treats each bin estimate as one observation,
with replacement and duplicate frequencies retained. This literal bin-distribution
interpretation is explicit, not a newly fitted request-weighting scheme; final
weighting/distribution approval remains open.

`fixed_offer_acceptance_diagnostic.csv` evaluates the same fixed prices/distances
for both empirical distributions, without simulation. At 1.5 km and $6.60,
acceptance is 67.5721% for eligible trip estimates versus 100% for positive pooled
bin estimates. These are calibration diagnostics, not causal or training outcomes.

## Conditioning, support and fallback

Preserve the existing T1 00–03, T2 04–05, T3 06–15 and T4 16–23 representation and
weather-code mappings. Eight overlapping fitting pools are retained: GLOBAL,
RAW_13, RAW_15, T1_G1 and T1–T4_POOLED. RAW pools span all times; time pools span
all weather codes. Pool counts reproduce historical support exactly. Disjoint
assigned population shares and overlapping fitting shares are reported separately.

Each provisional pool samples only positive finite estimates, bounded inclusively
by its actual empirical minimum/maximum (101–147 positive bins per pool). Negative,
zero and undefined estimates remain reported; no absolute-value repair or invented
positive floor is used. Near-zero positive values, if present, are not silently
removed. Nonfinite acceptance arithmetic fails closed. The default V3 provider and
its fitted distributions remain intact.

Fallback ordering and the existing ≥5,000 **trip-candidate** support criterion are
unchanged: mapped group, T1 raw-code pool, time pool, GLOBAL. This is inherited
routing logic, not proof of sufficient independent bin estimates. Unknown integer
weather codes follow the existing pooled fallback; missing/nonfinite/fractional
codes reject. Empty, nonpositive or malformed empirical pools reject at load;
no synthetic distribution is substituted.

## Bounded family evidence

`bounded_family_comparison.csv` contains 32 evaluations: lognormal, generalized
gamma, normal truncated to empirical bounds, and exponential for each pool.
Each receives one ordinary fit, then finite empirical-support normalization.
The normal candidate uses ordinary normal fitted moments before truncation; this
is not a truncated-likelihood maximum-likelihood fit. The other candidates also
use ordinary, not truncation-aware, fitting. Parameters, conditional log likelihood
and KS distance are descriptive **in-sample** diagnostics without fitted-parameter
KS significance claims or held-out selection. Sparse/dependent bin estimates and
shared references limit inference. No exhaustive search or historical parameter
reuse on the new estimator occurs. Undefined “ZIF” is not assigned an invented
meaning. Empirical bin resampling is the transparent provisional implementation;
no final fitted family is selected.

## Continuous-weather availability and limitation

The CNN uses categorical WeatherType plus z-scored Temperature and WindSpeed.
The processed demand master has consistent weather values within each of 3,552
half-hour slots in January 1–March 15. All 6,967,155 calibration timestamps align
to finite temperature/wind values; categorical weather mismatch count is zero.
Temperature ranges −15.2 to 25.0 °C; wind speed 0 to 37 km/h. Units follow the
unchanged Meteostat `temp`/`wspd` rename in `src/data/weather.py`; installed
Meteostat `units.py` defines Celsius and km/h source conversions. There is no
unit conversion in that preparation path. These are processed values with existing
forward/backward filling, not a claim of complete raw measurement coverage.

No temperature/wind bins, weights, thresholds or conditional distributions were
invented. Conditional regression or validated stratification are possible future
approaches, not adopted rules. The needed scientific decision is how to condition
sensitivity on these continuous features and establish adequate conditional support.
Full weather-feature alignment and final master compliance are **not established**.

## Runtime, checkpoints and validation

Pass `sensitivity_contract=.../provisional_sampling/sampling_contract.json` to
`ODPricingRuntime` to opt in. Without it, historical V3 sampling remains selected.
Sampling uses caller-controlled NumPy RNG; it does not choose epsilon by the
request's distance bin. Acceptance remains
`offer <= Pbase + (Pbase/epsilon)*((distance_km-Lbase)/Lbase)`.
OD actions, observed request replay, successful-dispatch rewards, fleet, charging
and operational logic are unchanged.

OD checkpoint schema `FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_3` records the sensitivity
version, exact calibration hash, sampler RNG and audit state. Incompatible schemas,
changed calibration files and mixed versions reject. Historical checkpoint codecs
are untouched. Focused and bounded regression results are saved in
`provisional_sampling/test_results.txt`; tests cover formula/bin edges, signs,
common references, bounds, RNG, groups/fallbacks, acceptance, checkpoint/resume,
rewards and historical behavior. Temporary runtime fixtures are not training runs.

## OD coverage and next decision

March 1–16 existing spatial records contain 2,024,014 eligible requests; 914
(0.045158%) reference 690 valid pairs absent from January support. March 16:
49/112,080 (0.043719%). There are no invalid grid IDs in this already spatially
processed eligible population; this does not quantify upstream raw exclusions.
Feasibility remains fail-closed. No March 17–31 observations were inspected.

Next single task: resolve and document continuous-weather conditioning and its
support-validation protocol. Final reference construction and distribution/weighting
approval also remain necessary before promotion; unseen-valid OD handling is a
separate outstanding decision. No automatic retraining or feasibility expansion.

## Reproduction and file guide

- `src/pricing/binned_sensitivity.py`: exact estimator and historical pool selection.
- `src/pricing/binned_sampler.py`: provisional empirical sampler and explicit state.
- `scripts/audit_binned_sensitivity.py`: saved population/bin/comparison/OD evidence.
- `scripts/complete_binned_sensitivity.py`: bounded family and weather completion.
- `final_validation/*distance_bins.csv`: full bin evidence, signs and counts.
- `final_validation/conditional_*`: pool summaries and disjoint assigned shares.
- `final_validation/estimator_comparison.csv`: estimator summaries/quantiles.
- `final_validation/*od*.csv`: development-only OD counts and unseen valid pairs.
- `provisional_sampling/sampling_contract.json`: current versioned opt-in contract.
- `provisional_sampling/bounded_family_comparison.csv`: candidate parameters/diagnostics.
- `provisional_sampling/continuous_weather_availability.json`: aligned coverage.
- `provisional_sampling/validation.json`: final tests, preservation and fingerprints.

Bounded verification: `python -B -m unittest tests.test_binned_sensitivity tests.test_binned_sampler tests.test_dispatch_reward tests.test_slot_pricing_v3 tests.test_od_pricing tests.test_historical_request_replay`.
