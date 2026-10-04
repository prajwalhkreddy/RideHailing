# Passenger Price Sensitivity — Final Clean Reference Analysis

**Status: `CLEAN_REFERENCE_ELASTICITY_FINAL`.** This is the FINAL offline passenger price-sensitivity analysis for January through March 2026.

The final comparison uses three **actual observed weather conditions**: WeatherCode 1 = **Clear**, WeatherCode 8 = **Rain**, and WeatherCode 15 = **Snowfall**. “Three weather conditions/classes” means these selected conditions, not K-means clusters. Previous clustering experiments are superseded for the final analysis and retained only as diagnostic history.

The authoritative mathematical reference is [Passenger_Price_Sensitivity_Implementation_Steps_Clean.pdf](../../../notebooks/plan/Passenger_Price_Sensitivity_Implementation_Steps_Clean.pdf). Its reference-value and relative-change sequence is implemented with the agreed project choices described below. The document's general three-class step is interpreted under the explicit final instruction to compare actual Clear/Rain/Snowfall conditions without clustering. Both references are full-population arithmetic means. The 100-mile source cutoff is a project implementation decision, not a numerical cutoff prescribed by the professor.

All paths below are relative to the project root unless shown as clickable package-local links. This README documents existing results; updating it did not rerun the analysis or modify data, code, tables, JSON or charts.

## 1. Objective

Estimate the historical passenger price-sensitivity / elasticity measure for each **Hour of Day × Weather Condition**, and describe:

- Its arithmetic mean: average sensitivity within a condition.
- Its population standard deviation: variability among individual trip sensitivity values within that condition.

The final comparison is **Clear vs Rain vs Snowfall across hours 0–23**. This is descriptive historical analysis. It does not, by itself, establish that weather causally changes passenger behaviour or isolate a causal price response.

## 2. Raw data

The inputs are three NYC Yellow Taxi parquet files:

| Source file | Raw rows |
|---|---:|
| `data/raw/yellow_taxi/yellow_tripdata_2026-01.parquet` | 3,724,889 |
| `data/raw/yellow_taxi/yellow_tripdata_2026-02.parquet` | 3,399,866 |
| `data/raw/yellow_taxi/yellow_tripdata_2026-03.parquet` | 3,952,451 |

The exact training window is:

```text
2026-01-01 00:00:00 inclusive <= pickup_timestamp < 2026-04-01 00:00:00 exclusive
```

These raw counts are counts by source file, not counts assigned by pickup calendar month. File labels do not override the timestamp boundary: stray source records outside the training window are excluded. The population manifest distinguishes source-file counts from valid counts by pickup calendar month.

Only fields needed for sensitivity estimation are retained. Source `tpep_pickup_datetime` becomes `pickup_timestamp`, `fare_amount` becomes `fare` (USD), and `trip_distance` remains in miles. The prepared input also contains `hour` and joined `WeatherCode`.

**Origin and destination are not grouping variables or required estimation fields.** No OD-specific bases or grid mapping are used to estimate passenger elasticity. Raw rows are drawn across the full regional population rather than selecting particular OD pairs.

Provenance: `data/processed/elasticity_v2/population_manifest.json` records source filenames, SHA-256 hashes, raw/valid counts, boundary handling and the weather join.

## 3. Weather data

Weather uses the existing `src/data/weather.py` preparation utility and Meteostat hourly data. The established pipeline retains Meteostat's `temp`, `wspd` and `coco` fields as `Temperature`, `WindSpeed` and `WeatherCode`, alongside `Datetime`. Its preparation semantics sort timestamps and allow forward/backward filling of missing weather feature values; this is not imputation of elasticity groups. The final elasticity analysis consumes the persisted weather artifacts rather than downloading or changing weather.

| Processed weather file | Actual / expected hourly records |
|---|---:|
| `data/processed/weather/nyc_weather_processed_2026_01.parquet` | 744 / 744 |
| `data/processed/weather/nyc_weather_processed_2026_02.parquet` | 672 / 672 |
| `data/processed/weather/nyc_weather_processed_2026_03.parquet` | 744 / 744 |
| **Total** | **2,160 / 2,160** |

The processed set has no missing or duplicate hourly timestamps and no missing WeatherCode values. Corresponding `weather_metadata_2026_01.json`, `weather_metadata_2026_02.json` and `weather_metadata_2026_03.json` files preserve monthly provenance.

Each taxi pickup timestamp is floored to its hour and matched to weather `Datetime`, using the existing many-to-one hourly join. The existing timezone-naive alignment is retained; no timezone conversion is introduced. Successful timestamp matching verifies mechanical coverage, not an independent resolution of physical timezone alignment.

Validated join results **before the final >100-mile source-distance exclusion**:

| Join measure | Result |
|---|---:|
| Valid taxi rows before join | 10,620,887 |
| Matched rows | 10,620,887 |
| Unmatched rows | 0 |
| Match percentage | 100% |

## 4. Basic taxi validation

Before elasticity estimation, source records require:

- A valid pickup timestamp inside the training window.
- Finite fare and `fare > 0`.
- Finite trip distance and `trip_distance > 0`.

The retained records are joined to hourly weather. These are source-field and temporal validity checks; **epsilon is not used to decide source validity**. The pre-distance-cutoff validated population is stored in `data/processed/elasticity_v2/elasticity_input_2026_01_03.parquet` with only `pickup_timestamp`, `hour`, `fare`, `trip_distance` and `WeatherCode`.

## 5. Source-distance cleaning

The final **PROJECT IMPLEMENTATION DECISION** is:

```text
Retain:  0 < trip_distance <= 100 miles
Exclude: trip_distance > 100 miles
```

| Population stage | Rows |
|---|---:|
| Valid weather-matched population before distance rule | 10,620,887 |
| Source records removed by >100-mile rule | 478 |
| Final cleaned population | 10,620,409 |

Inspection found conspicuous source anomalies, including recorded distances in the hundreds of thousands of miles with ordinary taxi fares. This motivated a project data-quality rule. **The professor did not explicitly prescribe the 100-mile numerical threshold.** Nor does the rule establish that every excluded trip was independently proven invalid.

Source records are filtered **before calculating the final global reference values**. This is not epsilon clipping, trimming or winsorization. The original input remains preserved; the separate cleaned artifact is `data/processed/elasticity_v2/elasticity_input_2026_01_03_cleaned.parquet`.

The exact decision, counts and original/cleaned hashes are recorded in `data/processed/elasticity_v2/source_cleaning_manifest.json`.

## 6. Global reference values

Both references are calculated **once from the complete cleaned Jan–Mar population**, before selecting weather/hour groups. Let $P_i$ denote fare in USD and $L_i$ trip distance in miles. For the full cleaned population of size $N$:

$$
P_{\mathrm{base}} = \frac{1}{N}\sum_{i=1}^{N} P_i
$$

$$
L_{\mathrm{base}} = \frac{1}{N}\sum_{i=1}^{N} L_i
$$

| Reference | Final value |
|---|---:|
| $N$ | 10,620,409 |
| $P_{\mathrm{base}}$ | 21.34586956773507 USD |
| $L_{\mathrm{base}}$ | 3.46907003958134 miles |

There is one global price reference and one global distance reference, shared across all observations. Neither is calculated separately by weather, hour, month or OD pair. All observed weather types contribute to these global means; the references are not fitted only on Clear/Rain/Snowfall trips.

The earlier experimental **±$1 fare-window $L_{\mathrm{base}}$**, approximately 3.018 miles, is **SUPERSEDED** and is not used in this final clean-reference analysis. For final numerical references, use this package's `summary.json`, not older reference JSON files describing that experiment.

## 7. Relative price change — delta P

For each historical trip:

$$
\Delta P_i = \frac{P_i-P_{\mathrm{base}}}{P_{\mathrm{base}}}
$$

This is the relative deviation of the individual trip fare from the single global reference fare. It is a fraction, not the raw difference in dollars.

**EXAMPLE ONLY — not a measured project observation:** if the reference were $21.35 and a trip fare were $25:

$$
\Delta P_i = \frac{25-21.35}{21.35} \approx 0.171
$$

The fare would be approximately 17.1% above that illustrative reference. Actual calculations use the full-precision project value recorded in Section 6, not the rounded example.

## 8. Relative distance change — delta L

For each historical trip:

$$
\Delta L_i = \frac{L_i-L_{\mathrm{base}}}{L_{\mathrm{base}}}
$$

This measures the trip distance's relative deviation from the global reference distance. A positive value means the trip is longer than the reference; a negative value means it is shorter. Like relative price change, it is dimensionless. It is not a raw distance difference in miles.

## 9. Individual passenger sensitivity

The project defines the observation-level price-sensitivity / elasticity measure as:

$$
\epsilon_i = \frac{\Delta L_i}{\Delta P_i}
= \frac{(L_i-L_{\mathrm{base}})/L_{\mathrm{base}}}
       {(P_i-P_{\mathrm{base}})/P_{\mathrm{base}}}
$$

Both numerator and denominator are relative changes, so epsilon is **dimensionless**. The final rules are:

- Retain signed epsilon; do not take its absolute value.
- Do not clip, normalize or trim epsilon.
- Do not require positive price or distance deviations.
- Do not introduce a denominator threshold such as $|\Delta P|\geq0.001$.
- Exclude only an exactly zero $\Delta P_i$, where the ratio is undefined.

The final cleaned population had **zero exact-zero denominator exclusions**. The recorded final validation also confirmed finite retained epsilon values.

For nonzero deviations, positive epsilon means price and distance deviations have the same sign; negative epsilon means they have opposite signs. Zero epsilon can occur when distance equals its reference while the price deviation is nonzero. These are algebraic descriptions of the project measure, not causal economic response estimates.

When $\Delta P_i$ is very close to zero while $\Delta L_i$ is not, the ratio can become very large in magnitude. This mechanism contributes to heavy tails in the historical epsilon distribution and can produce large standard deviations. Large ratios are retained under the final method.

## 10. Time grouping

Pickup timestamps determine 24 hourly slots:

| Hour | Time-of-day interval |
|---|---|
| 0 | 00:00–00:59 |
| 1 | 01:00–01:59 |
| … | … |
| 23 | 23:00–23:59 |

Each slot includes its entire hour, up to but not including the next hour. Trips from all dates in the training period with the same hour-of-day value are pooled. **No 30-minute grouping is used in the final analysis.**

## 11. Final weather conditions

The project retains Meteostat's original weather codes. The verified labels are:

| WeatherCode | Authoritative label | Valid trips in final comparison | Represented hours of day | Weather records across training period |
|---|---|---:|---:|---:|
| 1 | Clear | 3,085,571 | 24/24 | 605 |
| 8 | Rain | 217,536 | 20/24 | 39 |
| 15 | Snowfall | 106,563 | 20/24 | 39 |

Label authority: [Meteostat weather-condition definitions](https://dev.meteostat.net/formats.html#weather-condition-codes). “Snowfall” is the final display label. Each code is used exactly as observed; related rain or snowfall codes are not silently pooled into these selections.

These are actual weather conditions, not fitted weather classes. No K-means, clustering, weather-class imputation or trimmed-mean clustering is used. The selected comparison comprises **3,409,670 trips**, whereas the global references use the complete **10,620,409-trip** cleaned population.

Weather-record counts measure calendar hours carrying a condition. Represented hours-of-day count distinct clock positions and are a different support measure.

## 12. Time × weather sensitivity arrays

For every observed weather condition $W$ and hour $T$, collect all qualifying historical trips with that weather code and pickup hour. Calculate each trip's epsilon using the same global references. For example, 08:00 × Clear yields an array:

$$
\boldsymbol{\epsilon}_{W,T} = (\epsilon_1,\epsilon_2,\ldots,\epsilon_{N_{W,T}})
$$

Each element belongs to one actual historical trip. The array spans all matching dates within Jan–Mar; it is not an array of daily averages or weather-code centroids. These arrays are the conceptual grouping used for computation; the final CSV stores their aggregate statistics, not separate arrays.

Groups may have different $N_{W,T}$. No equal-sample-size balancing, subsampling or group weighting is introduced. No missing groups are fabricated.

## 13. Group statistics

For each observed $(W,T)$ group, define $N_{W,T}$ as its number of individual epsilon observations. Its arithmetic mean is:

$$
\bar{\epsilon}_{W,T} = \frac{1}{N_{W,T}}
\sum_{i=1}^{N_{W,T}}\epsilon_i
$$

Its population standard deviation is:

$$
\sigma_{W,T} = \sqrt{\frac{1}{N_{W,T}}
\sum_{i=1}^{N_{W,T}}(\epsilon_i-\bar{\epsilon}_{W,T})^2}
$$

Population SD uses **`ddof = 0`**, dividing by $N_{W,T}$ rather than $N_{W,T}-1$. Variance is:

$$
\operatorname{Var}(\epsilon)_{W,T} = \sigma_{W,T}^2
$$

The mean describes average sensitivity under the project formulation. SD describes dispersion of the individual trip measures around that mean. High SD indicates greater dispersion and may reflect strong influence from extreme ratios; low SD indicates a more concentrated set of values.

The distributions are heavy-tailed. SD is therefore a dispersion measure, not evidence of a Normal-shaped population. No Normal distribution is fitted or assumed to produce these descriptive outputs.

## 14. Final output table

Canonical result:

```text
data/processed/elasticity_v2/elasticity_actual_weather_clean_reference_final.csv
```

Its package-local copy is [actual_weather_hour_elasticity.csv](actual_weather_hour_elasticity.csv). The files are byte-identical.

| Exact column name | Meaning |
|---|---|
| `weather_code` | Actual Meteostat code: 1, 8 or 15 |
| `weather_name` | Clear, Rain or Snowfall |
| `hour` | Pickup hour of day, 0–23 |
| `n_valid` | Number of actual epsilon observations in that group |
| `mean_elasticity` | Arithmetic mean of individual epsilon values |
| `std_elasticity` | Population SD, `ddof=0` |
| `variance_elasticity` | Square of population SD |

The final table contains **64 observed rows**, not 72. There is one row per supported actual-weather/hour pair. Statistics are calculated from untrimmed trip observations, not from imputed values or clustering features.

## 15. Missing weather × hour groups

| Condition | Missing hour-of-day values |
|---|---|
| Clear | None |
| Rain | 5, 10, 11, 12 |
| Snowfall | 0, 4, 20, 22 |

Missing means there is no observed support for that pair in the final population. **It does not mean elasticity equals zero.** No interpolation or imputation is performed. Those groups are absent from the CSV, and chart lines show gaps rather than connecting across missing hours. Observed isolated points remain visible as markers.

## 16. Final results

Ranges below are minima and maxima across each condition's **observed hourly aggregate values**, rounded to six decimals. They are not ranges of individual trip epsilon or confidence intervals.

| Condition | Hourly mean minimum | Hourly mean maximum | Population SD minimum | Population SD maximum |
|---|---:|---:|---:|---:|
| Clear | 0.920406 | 1.895927 | 12.194799 | 43.986403 |
| Rain | 0.802874 | 1.682793 | 5.271878 | 39.574819 |
| Snowfall | -1.962060 | 4.671881 | 3.670163 | 108.411948 |

Clear and Rain have broadly overlapping hourly mean ranges. Snowfall exhibits greater observed variation across some hours and substantially larger within-hour SD in some periods. It has some hours with unusually high dispersion, not uniformly greater sensitivity across the day.

These descriptions do not establish a causal weather effect or statistical significance. Differences in support and influence from extreme individual ratios must be considered when interpreting the curves.

## 17. Graph 1 — mean elasticity

File: [mean_elasticity_actual_weather_clean_reference.png](charts/mean_elasticity_actual_weather_clean_reference.png).

Title: **Mean Passenger Elasticity vs Time of Day by Weather Condition**.

- X-axis: Hour of Day (0–23).
- Y-axis: Mean Passenger Elasticity.
- Lines: Clear, Rain and Snowfall.

Each point is the arithmetic mean of all individual epsilon observations for that weather/hour pair. Lines connect adjacent observed hours; they are a visual guide, not an interpolation model. Missing pairs appear as gaps.

The graph addresses: **“How does average historical passenger sensitivity vary by hour under the three selected weather conditions?”** It uses ordinary linear axes and includes all calculated values without presentation trimming or clipping.

## 18. Graph 2 — elasticity variability

File: [std_elasticity_actual_weather_clean_reference.png](charts/std_elasticity_actual_weather_clean_reference.png).

Title: **Passenger Elasticity Variability vs Time of Day by Weather Condition**.

- X-axis: Hour of Day (0–23).
- Y-axis: Population SD of Elasticity.
- Lines: Clear, Rain and Snowfall.

Each point represents the spread of individual epsilon values within one weather/hour group. It is not the mean, a standard error or a confidence interval.

**An SD of 100 does not mean mean elasticity is 100.** It means the individual observations are highly dispersed around their group mean. A few extreme ratios arising when relative price deviation is close to zero can contribute strongly to a large SD.

The graph uses ordinary linear axes, retains all calculated SD values, and shows gaps for missing groups.

## 19. Interpretation and limitations

1. This is observational historical analysis, with no causal weather-effect identification or statistical-significance claim.
2. Sample sizes differ substantially across weather conditions and hours; no balancing was performed.
3. Rain and Snowfall each lack four hour-of-day positions, so their full-day curves are incomplete.
4. Epsilon is a ratio sensitive to near-zero relative price deviations, even when source fare and distance pass validity checks.
5. Resulting distributions are heavy-tailed; Normality is not assumed.
6. Means and SDs can be strongly influenced by extreme observations that remain in the final population.
7. The 100-mile source-distance rule is a project implementation/data-quality decision, not a professor-specified cutoff.
8. Only three selected actual weather codes are compared; conclusions do not extend automatically to every Meteostat weather type.
9. The inherited timezone-naive hourly taxi/weather alignment remains a provenance assumption; complete matching alone does not validate physical timezone alignment.

## 20. What was not used in the final method

### Superseded development and diagnostic analyses

The following were explored during development but are **not part of this final clean-reference methodology**:

- 30-minute elasticity grouping.
- Condition-specific price or distance bases.
- A raw price-difference denominator instead of relative price change.
- Positive-only epsilon filtering.
- Minimum absolute relative-price-deviation threshold experiments.
- The ±$1 fare-window distance reference.
- K-means weather clustering.
- 1% / 5% trimmed-mean weather clustering.
- Weather-class imputation.

They remain preserved in historical diagnostic folders for reproducibility. They are superseded analyses, not descriptions of the current final result. In particular, previous weather-class outputs are **SUPERSEDED_FOR_FINAL_WEATHER_COMPARISON**; their class assignments are not used here.

## 21. Final pipeline summary

```text
Jan–Mar Yellow Taxi data, within the exact training window
→ basic timestamp/fare/distance validity
→ hourly Meteostat weather join
→ remove source trips >100 miles
→ final cleaned N = 10,620,409
→ one global P_base + one global L_base from the full cleaned population
→ select actual Weather × Hour
→ calculate relative ΔP
→ calculate relative ΔL
→ epsilon = ΔL / ΔP, excluding exact ΔP = 0 only
→ actual trip-level sensitivity array
→ N + mean epsilon + population SD + variance
→ repeat for Clear / Rain / Snowfall × Hour 0–23 where observed
→ final 64-row table + two graphs
```

Calculating epsilon before grouping or within each group gives the same measure because the bases remain fixed. Grouping does not refit the references.

## 22. Reproducibility / final files

### Authoritative final results

| Artifact | Path or link |
|---|---|
| Clean reference document | `notebooks/plan/Passenger_Price_Sensitivity_Implementation_Steps_Clean.pdf` |
| Canonical result | `data/processed/elasticity_v2/elasticity_actual_weather_clean_reference_final.csv` |
| Human-review package | `results/analysis/2026-10-03_elasticity_clean_reference_final/` |
| Result-table copy | [actual_weather_hour_elasticity.csv](actual_weather_hour_elasticity.csv) |
| Support table | [actual_weather_support.csv](actual_weather_support.csv) |
| References, provenance, checks and ranges | [summary.json](summary.json) |
| Mean graph | [mean_elasticity_actual_weather_clean_reference.png](charts/mean_elasticity_actual_weather_clean_reference.png) |
| SD graph | [std_elasticity_actual_weather_clean_reference.png](charts/std_elasticity_actual_weather_clean_reference.png) |

### Input and provenance artifacts

- `data/processed/elasticity_v2/population_manifest.json`: raw files and hashes, per-source counts, training window, weather coverage, join checks and pre-distance-cutoff population.
- `data/processed/elasticity_v2/source_cleaning_manifest.json`: project distance rule, removed/retained counts and original/cleaned input hashes.
- `data/processed/elasticity_v2/elasticity_input_2026_01_03.parquet`: validated weather-matched population before the 100-mile rule.
- `data/processed/elasticity_v2/elasticity_input_2026_01_03_cleaned.parquet`: complete cleaned population used to calculate both global means.
- The three monthly weather parquet files and corresponding metadata listed in Section 3.

To reproduce the mathematical result, use the cleaned input, calculate both full-population means, apply the relative-change formulas, select codes 1/8/15, and aggregate actual trip epsilon by code/hour with population SD. Preserve missing groups. The explicit formulas, field names and boundary rules above define the final procedure without requiring any development-history output.

The existing `summary.json` records checks from the analysis run: full-population references, source/date rules, signed relative-change ratios, exact-zero-only exclusion, independent group mean/SD verification, variance identity, support gaps, exact CSV roundtrip and unchanged protected input/history hashes. It also records source/output hashes. This documentation update verified counts, schema, support, ranges and byte identity against the existing final artifacts without rerunning trip-level calculations.

Older result directories and older reference/methodology JSONs remain diagnostic history. They must not be used as final runtime inputs. This is an offline analysis package; creating or documenting it does not modify production/runtime behaviour or authorize runtime integration.

## Historical Price–Distance Arrays

The long-format file [`actual_weather_hour_price_distance_arrays_2026_01_03.parquet`](../../../data/processed/elasticity_v2/actual_weather_hour_price_distance_arrays_2026_01_03.parquet) contains **3,409,670 paired trip-level observations** from the unchanged cleaned Jan–Mar 2026 input (0 < trip_distance <= 100 miles), restricted to Clear (1), Rain (8) and Snowfall (15). Columns are `weather_code`, `weather_name`, `hour`, `price` (USD) and `distance` (miles). Each row keeps P_i and L_i from the same historical trip; price and distance columns were selected together without aggregation, independent sorting or deduplication. No stable trip identifier is present in the source schema, so no artificial `observation_id` was added.

The earlier `professor_price_distance_arrays_2026_01_03.parquet` contains 10,620,887 rows with columns `pickup_timestamp`, `fare`, `trip_distance`, `hour`, `WeatherCode`. It supports direct weather/hour extraction, but includes 478 distances over 100 miles and all weather codes, so it does not exactly match this final cleaned three-condition requirement. It remains unchanged.

Filter the new file by weather code and hour, then extract its `price` and `distance` columns together to obtain aligned arrays. The existing global P_base = 21.34586956773507 USD and L_base = 3.46907003958134 miles reconstruct delta_P = (P_i - P_base)/P_base, delta_L = (L_i - L_base)/L_base, and epsilon = delta_L/delta_P, excluding exact-zero delta_P only. This addition does not recompute elasticity or change the references.

[`price_distance_array_index.csv`](price_distance_array_index.csv) records `weather_code`, `weather_name`, `hour`, `n_observations` for the 64 observed groups. Clear has 3,085,571 observations across 24 hours; Rain 217,536 across 20; Snowfall 106,563 across 20. Missing hours remain absent: Rain 5, 10, 11, 12; Snowfall 0, 4, 20, 22; none for Clear. Every group's count(price) equals count(distance) and the canonical final n_valid. No array-valued CSV cells or fabricated groups are used.

Validation passed: full Parquet round-trip and row-wise source pairing; date/distance constraints; nonmissing finite pairs; all 64 canonical group counts; totals and missing-hour sets. Canonical elasticity CSV, existing source Parquets and other final-package artifacts remain unchanged, verified by before/after SHA-256 checks. Only this README, the new index and the new paired-observation Parquet were written.
