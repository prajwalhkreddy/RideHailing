# Record-029 Passenger Price–Distance Sensitivity — Technical Record

Full-population estimation, numerical-stability diagnostics and source-quality investigation for January–March 2026.

## Analysis Objective and Scope

The analysis characterizes historical price–distance sensitivity, assesses its dependence on price-conditioned reference distance, and identifies numerical and source-data issues that must be resolved before a passenger-sensitivity model is used in simulation. It describes paired fare/distance observations, not a directly identified causal price-demand elasticity.

All primary estimates use 10,620,409 cleaned January–March trips, across all observed weather conditions. Detailed hourly comparisons cover actual Clear (WeatherCode 1) and Rain (8). The 1,000-observation inspection concept does not limit the estimation population.

## Established Results

### Population, validation and price provenance

The existing source-cleaning rule is 0 < trip_distance ≤ 100 miles, with valid timestamps and finite positive fares. The training window is 2026-01-01 inclusive to 2026-04-01 exclusive. Additional Record-029 validation removed zero rows. All 10,620,409 observations remain retained.

The source price is TLC `fare_amount`, renamed `fare` in the processed data; it is measured in USD. It is not a derived total fare, per-mile price or synthetic model-generated price. Distance is measured in miles. Pickup timestamps, source row positions, hour and weather code retain source traceability.

### Global price reference and candidate distance references

The single global P_base is **21.34586956773507 USD**, calculated from all cleaned observations. No weather-specific or hourly base is used. L_base is price-conditioned:

\[
L_{base}(\tau_P)=\operatorname{mean}\{L_i:|P_i-P_{base}|\leq\tau_P\}.
\]

The conditioning subset estimates the distance reference only; epsilon statistics use the complete historical population for every candidate.

| tau_P (USD) | Exact L_base (miles) | Reference support N |
| --- | --- | ---: |
| ±$0.25 | 3.0486708328788574 | 155,857 |
| ±$0.50 | 2.9910786705717562 | 196,325 |
| ±$1.00 | 3.01799878914405 | 479,000 |
| ±$2.00 | 3.0333960338928465 | 937,897 |

### Record-029 formulation

\[
\mathrm{price\_diff}_i=P_i-P_{base},\quad
\mathrm{distance\_diff}_i=L_i-L_{base},
\]
\[
r_{P,i}=\frac{P_i-P_{base}}{P_{base}},\quad
r_{L,i}=\frac{L_i-L_{base}}{L_{base}},\quad
\epsilon_i=\frac{r_{P,i}}{r_{L,i}}
=\frac{(P_i-P_{base})/P_{base}}{(L_i-L_{base})/L_{base}}.
\]

The numerator is relative price deviation and the denominator is relative distance deviation. Epsilon is signed and dimensionless. Exact-zero denominators would yield undefined epsilon, explicitly flagged while preserving the source row. The observed exact-zero count is **zero for all four candidates**. The historical candidate diagnostics retained all nonzero near-zero denominators and large epsilon values; the current authoritative denominator rule is specified below. No clipping, winsorization, trimming, extra normalization or fitted sensitivity distribution is applied.

### Full-population candidate comparison

| tau_P | mean_epsilon | median_epsilon | SD_epsilon | P95 | P99 | max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- |
| 0.250000 | 0.787444 | 0.764566 | 28.904610 | 1.903402 | 7.735824 | 24569.490215 |
| 0.500000 | 0.445895 | 0.768680 | 34.102016 | 1.957584 | 7.803063 | 11516.595900 |
| 1.000000 | 0.739608 | 0.767133 | 19.277050 | 1.943506 | 7.995343 | 7676.417735 |
| 2.000000 | 0.613266 | 0.766457 | 13.589164 | 1.917327 | 7.888783 | 11660.273365 |

Each historical candidate calculation has 10,620,409 defined epsilon observations before the newly frozen resolution rule; these tables remain diagnostic history. Population SD uses ddof=0; empirical quantiles use linear interpolation. Medians are comparatively stable, while means, SDs and extreme magnitudes vary appreciably. Signed epsilon is retained, including negative values; sign is not an automatic source-validity classification.

### Clear/Rain hourly results

There are 44 observed groups per candidate: 24 Clear and 20 Rain, or 176 candidate/group records. Their support is 3,303,107 observations per candidate. Rain hours 5, 10, 11 and 12 remain absent. No weather clustering or imputation is used. The existing hourly tables are complete candidate comparisons, but are not final frozen-method group models.

### Consolidated historical analysis population

The authoritative consolidated population is `data/processed/price_distance_sensitivity_record029/record029_analysis_population_jan_mar_2026.parquet`. It contains all 10,620,409 rows in source order, reference-dependent epsilon/deviation columns, integer pickup month, and explicit review flags. Exact reference values and status definitions are embedded in `record029_population_metadata` in the Parquet schema.

Short-distance flags describe exact 0.01 mile and cumulative bounds of 0.05, 0.10, 0.25 and 0.50 miles. Candidate suffixes 025/050/100/200 identify the fare windows; denominator-flag suffixes 0001/001/005/01 mean absolute relative-distance deviations below 0.0001/0.001/0.005/0.01. These are diagnostic flags, **not exclusions**.

Source review in this consolidated file uses the investigated exact 0.01-mile cohort. Numerical review uses abs(relative_distance_deviation)<0.001 for any candidate. Combined review means both; VALID_STANDARD means neither selected trigger, not certification of every source record. Other short-distance flags remain independent. Duration and raw source-quality fields exist in the separate 0.01-mile source diagnostic, not in the consolidated full-population file; they were not inferred or joined into it.

| metric | N |
| --- | --- |
| is_distance_001 | 54993 |
| is_distance_le_005 | 81302 |
| is_distance_le_010 | 97124 |
| is_distance_le_025 | 146460 |
| is_distance_le_050 | 553301 |
| SOURCE_QUALITY_REVIEW | 54993 |
| NUMERICAL_STABILITY_REVIEW | 27270 |
| SOURCE_AND_NUMERICAL_REVIEW | 0 |
| VALID_STANDARD | 10538146 |

All rows remain retained. No universal L_min or review-based filtering rule is adopted.

## Diagnostic Findings

### Distance precision and denominator instability

The observed distances comprise 5,712 unique values on an approximately 0.01-mile grid. All rows align to this grid within the reported floating-point tolerance; strict equality of 100×distance to an integer holds for 88.304801%. Binary representation error is distinct from actual finer measurement precision.

| tau_P | L_base | nearest_distance_below | nearest_distance_above | absolute_gap_below | absolute_gap_above | relative_deviation_below | relative_deviation_above | count_at_nearest_below | count_at_nearest_above |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.250000 | 3.048671 | 3.040000 | 3.050000 | 0.008671 | 0.001329 | -0.002844 | 0.000436 | 8981 | 8826 |
| 0.500000 | 2.991079 | 2.990000 | 3.000000 | 0.001079 | 0.008921 | -0.000361 | 0.002983 | 9427 | 29874 |
| 1.000000 | 3.017999 | 3.010000 | 3.020000 | 0.007999 | 0.002001 | -0.002650 | 0.000663 | 9076 | 9017 |
| 2.000000 | 3.033396 | 3.030000 | 3.040000 | 0.003396 | 0.006604 | -0.001120 | 0.002177 | 9000 | 8981 |

| tau_P | near_zero_denominator_N | near_zero_denominator_pct | near_zero_variance_pct |
| --- | --- | --- | --- |
| 0.250000 | 8826 | 0.083104 | 94.407415 |
| 0.500000 | 9427 | 0.088763 | 95.193236 |
| 1.000000 | 9017 | 0.084903 | 86.682230 |
| 2.000000 | 0 | 0.000000 | 0.000000 |

Here the near-zero region is abs(relative_distance_deviation)<0.001, a descriptive comparison rather than an adopted filtering rule. No candidate has observations below 0.0001. Squared-deviation contributions are measured about the full-candidate mean, not a recentered subset mean.

The first three references lie sufficiently close to populated grid values to create near-zero denominators. The ±$2 reference has no observations inside the 0.001 region. Its lower SD is consistent with greater numerical separation from the discrete grid, but is not sufficient evidence to select it. Reference placement, corresponding fare deviations and the remaining observations jointly determine dispersion. Choosing a reference solely for low SD could favor a numerical coincidence rather than a substantively justified reference.

### Distribution and price–distance evidence

The full and P01–P99 histograms describe empirical candidate distributions. Full plots retain all observations; central plots restrict visualization only. Full-range count axes are symmetric-log to expose rare tails. Histogram bin totals, sign counts and extrema are preserved in the supporting CSVs. Extreme exports trace large ratios to paired fares/distances rather than labelling them invalid automatically.

Full-data price–distance density and conditional summaries reveal different distances at identical fares and different fares at identical distances. The median/IQR curve over 0–10 miles uses all observations within fixed distance bins for its calculations. No complex price model is fitted; plotted patterns alone do not establish a tariff mechanism or causality.

### Very short distances and raw-source validation

Exactly 0.01 mile occurs in **54,993 trips (0.517805%)**. It is distinct from distance close to L_base: raw distance near zero generally yields a relative-distance deviation near −1, whereas distance near L_base makes the ratio denominator small.

| month | N | valid_monthly_N | percentage |
| --- | --- | --- | --- |
| 2026-01 | 18440 | 3560712 | 0.517874 |
| 2026-02 | 19590 | 3249875 | 0.602792 |
| 2026-03 | 16963 | 3809822 | 0.445244 |

The pattern occurs across all three months. Duration median is 14.716667 minutes, P05 0.150000, P95 36.000000, and maximum 1755.100000. There are 68 zero-duration records, retained and flagged; no missing durations were reported for this cohort.

Only 13.765388% have identical recorded pickup/dropoff zones; 86.234612% differ. This does not directly measure geographic distance, but it argues against a uniformly stationary/local interpretation.

Fare median is $25.19, mean $29.370123, P05 $3.70, P95 $70.00, and maximum $623.70. Median total_amount is $30.75. Missing RatecodeID and payment_type 0 coincide in 48,814 records. These raw code values are not assigned unverified semantic meanings.

| distance | N | median_fare | median_duration_minutes | same_zone_percentage | missing_location_N |
| --- | --- | --- | --- | --- | --- |
| 0.010000 | 54993 | 25.190000 | 14.716667 | 13.765388 | 0 |
| 0.020000 | 14337 | 24.200000 | 10.750000 | 29.964428 | 0 |
| 0.030000 | 4656 | 20.435000 | 0.533333 | 67.160653 | 0 |
| 0.040000 | 3888 | 24.000000 | 0.400000 | 70.344650 | 0 |
| 0.050000 | 3428 | 25.980000 | 0.450000 | 65.985998 | 0 |
| 0.100000 | 6294 | 5.100000 | 1.866667 | 59.850651 | 0 |
| 0.250000 | 4460 | 5.100000 | 2.700000 | 46.457399 | 0 |
| 0.500000 | 70158 | 5.800000 | 4.491667 | 24.074232 | 0 |
| 1.000000 | 107638 | 9.010000 | 7.983333 | 3.260930 | 0 |

The 0.01-mile and 0.02-mile cohorts have substantially elevated fares/durations relative to several adjacent short-distance values. Source evidence is mixed: zero/extreme durations, missing metadata and substantial fares with tiny recorded distances warrant review, but do not prove all short trips invalid. Zone boundaries, waiting time and different fare arrangements cannot be resolved conclusively from these fields. A universal L_min is **not justified**.

The raw source diagnostic preserves 54,993 matched rows and available fare components, timestamps and zone/rate/payment fields. Matching uses pickup timestamp, fare, distance and occurrence order for duplicate keys. Multiplicities reconcile, but identity within otherwise indistinguishable duplicate keys is not independently provable. The 500-row manual review is a deterministic inspection set, not the population used for statistics.

## Current Frozen Methodology

References, denominator-resolution handling, no L_min and inclusive P0.5–P99.5 support remain unchanged. The final project model uses four contiguous time groups, shared Clear/Rain parameters, and empirical resampling as specified below. Earlier discussion of unresolved grouping/family is historical evidence superseded by this final decision. No production simulator is modified.

## Key Files for Review

Paths below are relative to this analysis folder unless a processed-data path is stated. The current artifacts form a complete evidence package; `summary.json` records the original full-data run and is not a consolidated summary of every subsequent extension.

- [cleaning_summary.json](cleaning_summary.json): Input/output counts and original basic-validity checks.
- [summary.json](summary.json): Original full-data references, candidate summaries, authority and preservation metadata.
- [lbase_price_window_comparison.csv](lbase_price_window_comparison.csv): Exact references, support and within-window distance statistics.
- [full_jan_mar_sensitivity_summary_by_lbase.csv](full_jan_mar_sensitivity_summary_by_lbase.csv): Complete-population candidate mean, median, SD, variance, quantiles, sign counts and extrema.
- [clear_rain_hour_sensitivity_by_lbase.csv](clear_rain_hour_sensitivity_by_lbase.csv): 176 observed candidate/weather/hour records.
- [full_jan_mar_epsilon_bins_by_lbase.csv](full_jan_mar_epsilon_bins_by_lbase.csv): Full and central-view bin counts and percentages.
- [near_zero_distance_deviation_diagnostic.csv](near_zero_distance_deviation_diagnostic.csv): Five relative-distance-deviation bands for each candidate.
- [distance_distribution_diagnostic.csv](distance_distribution_diagnostic.csv): Full raw-distance distribution and descriptive bands.
- [short_distance_examples.csv](short_distance_examples.csv): 100 shortest observations for inspection.
- [price_distance_summary.csv](price_distance_summary.csv): Full-data overall and repeated-price/distance conditional summaries.
- [extreme_sensitivity_examples_by_lbase.csv](extreme_sensitivity_examples_by_lbase.csv): Initial top-20 extreme inspection per candidate.
- [distance_precision_summary.csv](distance_precision_summary.csv): Grid-alignment metrics, increments, frequent values and counts around 2.90–3.10 miles.
- [lbase_nearest_distance_grid.csv](lbase_nearest_distance_grid.csv): Observed distances immediately below/above each reference.
- [variance_contribution_by_distance_denominator_band.csv](variance_contribution_by_distance_denominator_band.csv): Five-band contributions to full-candidate squared deviations.
- [extreme_epsilon_by_lbase.csv](extreme_epsilon_by_lbase.csv): Expanded top-100 inspection per candidate (400 rows).
- [short_distance_cohort_summary.csv](short_distance_cohort_summary.csv): Overlapping short-distance cohorts with fare/distance/weather/hour summaries.
- [distance_001_examples.csv](distance_001_examples.csv): Stable 100-row exact 0.01-mile inspection.
- [lbase_candidate_decision_table.csv](lbase_candidate_decision_table.csv): Reference, sensitivity and near-zero variance comparison.
- [price_distance_binned_curve.csv](price_distance_binned_curve.csv): Full-data distance-bin fare medians and quartiles.
- [short_distance_disjoint_cohorts.csv](short_distance_disjoint_cohorts.csv): Non-overlapping distance cohort support and fare statistics.
- [distance_001_full_source_diagnostic.parquet](distance_001_full_source_diagnostic.parquet): All 54,993 source-linked 0.01-mile records and duration/source-quality fields.
- [distance_001_duration_bands.csv](distance_001_duration_bands.csv): Selected cohort duration support, including nonpositive duration.
- [distance_001_fare_bands.csv](distance_001_fare_bands.csv): Fare-band support for exact 0.01-mile trips.
- [distance_001_top_location_pairs.csv](distance_001_top_location_pairs.csv): Twenty most frequent raw zone pairs.
- [distance_001_monthly_stability.csv](distance_001_monthly_stability.csv): Monthly cohort counts and percentages of valid monthly trips.
- [short_distance_exact_value_comparison.csv](short_distance_exact_value_comparison.csv): Exact-distance fare/duration and same-zone comparisons.
- [distance_001_manual_review.csv](distance_001_manual_review.csv): 500 distinct representative raw-linked rows with selection labels.
- [short_distance_source_validation_summary.json](short_distance_source_validation_summary.json): Raw-source checksums, traceability caveat and source-validation statistics.
- [record029_analysis_population_summary.csv](record029_analysis_population_summary.csv): Consolidated population flags/status counts overall and monthly.

### Processed full-population files

- [cleaned_price_distance_jan_mar_2026.parquet](../../../data/processed/price_distance_sensitivity_record029/cleaned_price_distance_jan_mar_2026.parquet): Validated full-population source fields and original row position.
- [cleaning_summary.json](../../../data/processed/price_distance_sensitivity_record029/cleaning_summary.json): Processed copy of the validity report.
- [full_jan_mar_sensitivity_by_lbase.parquet](../../../data/processed/price_distance_sensitivity_record029/full_jan_mar_sensitivity_by_lbase.parquet): Completed four-candidate formula columns and epsilon for all rows.
- [record029_analysis_population_jan_mar_2026.parquet](../../../data/processed/price_distance_sensitivity_record029/record029_analysis_population_jan_mar_2026.parquet): Consolidated historical population with diagnostic flags, review statuses and embedded definitions.

### Figures

- [epsilon_tau_025_full.png](charts/epsilon_tau_025_full.png): Candidate distribution: full observed range, all tails retained.
- [epsilon_tau_025_p01_p99.png](charts/epsilon_tau_025_p01_p99.png): Candidate distribution: central P01–P99 visualization only.
- [epsilon_tau_050_full.png](charts/epsilon_tau_050_full.png): Candidate distribution: full observed range, all tails retained.
- [epsilon_tau_050_p01_p99.png](charts/epsilon_tau_050_p01_p99.png): Candidate distribution: central P01–P99 visualization only.
- [epsilon_tau_100_full.png](charts/epsilon_tau_100_full.png): Candidate distribution: full observed range, all tails retained.
- [epsilon_tau_100_p01_p99.png](charts/epsilon_tau_100_p01_p99.png): Candidate distribution: central P01–P99 visualization only.
- [epsilon_tau_200_full.png](charts/epsilon_tau_200_full.png): Candidate distribution: full observed range, all tails retained.
- [epsilon_tau_200_p01_p99.png](charts/epsilon_tau_200_p01_p99.png): Candidate distribution: central P01–P99 visualization only.
- [price_distance_binned_median_and_short_trips.png](charts/price_distance_binned_median_and_short_trips.png): 0–10-mile median/IQR curve and disjoint short-distance fare comparison.
- [price_distance_central_density.png](charts/price_distance_central_density.png): Marginal-P99 density view; full-data statistics unchanged.
- [price_distance_conditional_spreads.png](charts/price_distance_conditional_spreads.png): Median/P05–P95 spreads at repeated exact fares and distances.
- [price_distance_full_density.png](charts/price_distance_full_density.png): Full-range aggregated price–distance density.

## Evidence Boundaries

The completed work establishes full-population candidate calculations, numerical reference sensitivity, source-validation findings and a traceable population with review flags. The ±$1 reference window is now frozen by project decision; a universal distance cutoff, epsilon deletion policy and simulation-ready distribution are not established. Review labels and diagnostic bounds preserve observations rather than adjudicating validity. Methodological agreement and subsequent frozen-method implementation remain distinct stages.

## Frozen Reference Definition

P_base = 21.34586956773507 USD; tau_P = ±$1.00; L_base = 3.01799878914405 miles. The inclusive criterion abs(fare − P_base) ≤ $1.00 has support 479,000 observations (4.510184% of the full population). The reference values and support were verified from existing processed observations. `frozen_reference_values.json` in the processed Record-029 namespace records the decision.

This is a PROJECT METHODOLOGY DECISION balancing interpretable price closeness, substantial reference support and stability of candidate distance references. It is not based on minimizing epsilon SD. The ±$2 alternative is not inferior solely because of dispersion; its lower SD was influenced by numerical separation from the discrete distance grid. Historical candidate comparisons remain unchanged as supporting evidence.

## Near-Zero Relative-Distance Diagnostic

The frozen-reference analysis uses all 10,620,409 observations and the denominator (trip_distance − L_base)/L_base. The six bands below partition the complete population; epsilon is relative price divided by relative distance. Squared deviations are taken about the full epsilon mean. Empty bands have undefined medians/quantiles (blank CSV fields), not zero-valued distribution statistics.

| band | N | percentage | distance_min | distance_median | distance_max | relative_price_deviation_median | epsilon_median | P95_abs_epsilon | P99_abs_epsilon | max_abs_epsilon | sum_squared_deviation_from_full_epsilon_mean | percentage_total_squared_deviations | valid_epsilon_N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 <= abs(relative_distance_deviation) < 0.0001 | 0 | 0 | — | — | — | — | — | — | — | — | 0 | 0 | 0 |
| 0.0001 <= abs(relative_distance_deviation) < 0.001 | 9017 | 0.084902568 | 3.02 | 3.02 | 3.02 | -0.03962685 | -59.760712 | 1201.4837 | 2527.8673 | 7676.4177 | 3.4209952e+09 | 86.68223 | 9017 |
| 0.001 <= abs(relative_distance_deviation) < 0.005 | 18076 | 0.1702006 | 3.01 | 3.01 | 3.03 | -0.03962685 | -0.42652654 | 250.371 | 521.26714 | 3282.8091 | 3.0600833e+08 | 7.7537332 | 18076 |
| 0.005 <= abs(relative_distance_deviation) < 0.01 | 48282 | 0.45461526 | 2.99 | 3 | 3.04 | -0.072420079 | 7.8061844 | 90.757738 | 195.036 | 717.06919 | 1.2422562e+08 | 3.1476671 | 48282 |
| 0.01 <= abs(relative_distance_deviation) < 0.05 | 260155 | 2.4495761 | 2.87 | 2.98 | 3.16 | -0.04759092 | 0.7680896 | 30.320704 | 70.203588 | 1010.2244 | 75877417 | 1.9226054 | 260155 |
| 0.05 <= abs(relative_distance_deviation) < inf | 10284879 | 96.840705 | 0.01 | 1.81 | 99.93 | -0.2851076 | 0.76655846 | 2.1066968 | 5.0908047 | 173.67842 | 19486876 | 0.49376446 | 10284879 |

There are 9,017 observations with abs(relative_distance_deviation)<0.001, all at recorded distance 3.02 miles. Their relative-distance deviation is 0.000663092001. Their fares range from $0.01 to $130.00, median $20.50; this includes varied price deviations despite identical recorded distance. The near-zero denominator is therefore mechanically explained by proximity to L_base on the 0.01-mile distance grid. Some large fare/ratio observations merit contextual review, but these fields alone do not establish source invalidity. The cohort contains ordinary grid-aligned distances and potentially unusual fares; a source-error explanation for the entire cohort is not supported.

`near_zero_relative_distance_records.parquet` preserves all 9,017 records with source identifiers and paired fare/distance, weather/hour and calculated deviations/epsilon. No record is removed from the historical analysis population. Exact-zero distance denominators number zero.

## Short-Distance Status

No L_min is adopted. All currently valid trips and existing short-distance flags remain intact, including 54,993 exact 0.01-mile trips (0.517805%). Existing source validation found mixed/unusual cases but did not justify universal removal. That investigation was not repeated here.

Phase 1–3 additions: `data/processed/price_distance_sensitivity_record029/frozen_reference_values.json`, `near_zero_relative_distance_diagnostic_frozen.csv`, and `near_zero_relative_distance_records.parquet`. Validation covers full N, reproduced references/support, correct formula direction, complete band totals and unchanged prior artifact hashes; only this README was updated.

## Frozen Authoritative Methodology

The authoritative dataset is `data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet`, with current methodology in `authoritative_epsilon_methodology.json` in the same namespace. Earlier four-candidate and consolidated-population Parquets are preserved as historical diagnostic inputs; their unmasked epsilon values are not the authoritative distribution after this decision. Existing `analysis_status` columns are retained as historical review labels; `epsilon_status` alone determines inclusion in the present distribution.

The formula is relative_price_deviation=(fare−P_base)/P_base, relative_distance_deviation=(trip_distance−L_base)/L_base, and epsilon=relative_price_deviation/relative_distance_deviation. Signed values remain retained; no clipping, trimming or range bounds are applied.

## Measurement-Resolution Denominator Treatment

Verified distance increment is 0.01 mile. Rows satisfying the strict absolute-distance rule abs(trip_distance−3.01799878914405)<0.005 miles are marked UNRESOLVED_DISTANCE_DENOMINATOR with null epsilon. The boundary is half the measurement increment; it is not a relative-deviation cutoff. These are neither invalid-trip nor outlier labels. No other denominator cutoff is adopted. All 9,017 affected observations have recorded distance 3.02 miles, as verified from the processed population.

## Authoritative Epsilon Population

All 10,620,409 historical rows are preserved in source order. VALID epsilon N is 10,611,392; unresolved denominator N is 9,017. The 54,993 exact 0.01-mile observations and other short trips remain retained; no L_min is adopted. Source identifiers, pickup timestamp, month, weather/hour and available source-quality flags are preserved. Prior candidate-specific columns are omitted from the authoritative output to avoid multiple competing epsilon fields.

## Near-Zero Relative-Price Analysis

This is numerator analysis within VALID rows, not filtering.

| band | N | percentage | epsilon_median | epsilon_P05 | epsilon_P95 | epsilon_P99 | min | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 <= abs(relative_price_deviation) < 0.0001 | 0 | 0 | — | — | — | — | — | — |
| 0.0001 <= abs(relative_price_deviation) < 0.001 | 2002 | 0.018866516 | 0.00026405552 | -0.0059590908 | 0.0063475652 | 0.025497266 | -0.24976778 | 0.28050852 |
| 0.001 <= abs(relative_price_deviation) < 0.005 | 11393 | 0.10736574 | 0.0027341826 | -0.070904716 | 0.062177306 | 0.28239415 | -1.8405967 | 1.8713374 |
| 0.005 <= abs(relative_price_deviation) < 0.01 | 137296 | 1.2938548 | -0.010099629 | -0.18467838 | 0.1627983 | 0.78709525 | -3.2546668 | 3.6389251 |
| 0.01 <= abs(relative_price_deviation) < 0.05 | 334866 | 3.1557217 | 0.038087596 | -0.65710434 | 0.63614125 | 3.3526169 | -18.809438 | 18.840179 |
| 0.05 <= abs(relative_price_deviation) < inf | 10125835 | 95.424191 | 0.79098121 | -1.0383648 | 1.9727881 | 8.0588994 | -1574.6401 | 3282.8091 |

There are 2,002 valid observations with abs(relative_price_deviation)<0.001 (0.018867%); their median epsilon is approximately 0.000264, with P05/P95 approximately −0.005959/+0.006348. Small relative-price numerators produce a local concentration near zero, although the denominator still affects individual ratios and the observed range is wider. This small cohort does not establish a dominant population-wide zero mass; there are no exactly zero epsilon values. No numerator-based observation is removed.

## Empirical Epsilon Distribution

| N | mean | median | population_SD | variance | min | max | negative_percentage | zero_percentage | positive_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10611392 | 0.64718083 | 0.76717248 | 7.0372555 | 49.522965 | -1574.6401 | 3282.8091 | 11.54382 | 0 | 88.45618 |

| quantile | epsilon |
| --- | --- |
| P0.01 | -216.13169 |
| P0.1 | -51.198452 |
| P0.5 | -12.890744 |
| P1 | -6.7176683 |
| P2.5 | -2.5676659 |
| P5 | -0.99383858 |
| P25 | 0.38461259 |
| P50 | 0.76717248 |
| P75 | 0.94784251 |
| P95 | 1.9322194 |
| P97.5 | 3.3784927 |
| P99 | 7.7234115 |
| P99.5 | 15.442448 |
| P99.9 | 52.070827 |
| P99.99 | 161.27176 |

All statistics use all VALID rows. SD is population SD (ddof=0) and quantiles use linear interpolation. Full and central-view histograms do not alter the calculation population. The ECDF uses full-data sorted ranks, with deterministic rank subsampling only for drawing and a symmetric-log epsilon axis. This is an empirical distribution, not a fitted Normal model.

## Empirical Range Evidence

| candidate | lower_bound | upper_bound | retained_N | retained_percentage | excluded_low_N | excluded_low_percentage | excluded_high_N | excluded_high_percentage | mean_after | median_after | SD_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0.01–P99.99 | -216.13169 | 161.27176 | 10609273 | 99.980031 | 1057 | 0.0099609929 | 1062 | 0.010008112 | 0.65654501 | 0.76717248 | 4.8206722 |
| P0.1–P99.9 | -51.198452 | 52.070827 | 10590825 | 99.80618 | 10143 | 0.095585951 | 10424 | 0.098234049 | 0.66265919 | 0.76717248 | 2.9073996 |
| P0.5–P99.5 | -12.890744 | 15.442448 | 10505278 | 98.999999 | 53057 | 0.50000038 | 53057 | 0.50000038 | 0.65165848 | 0.76717248 | 1.4445879 |
| P1–P99 | -6.7176683 | 7.7234115 | 10399673 | 98.004795 | 105808 | 0.99711706 | 105911 | 0.99808772 | 0.65051475 | 0.76717248 | 1.0331157 |
| P2.5–P97.5 | -2.5676659 | 3.3784927 | 10080824 | 95.000015 | 265285 | 2.5000019 | 265283 | 2.499983 | 0.65701808 | 0.76717248 | 0.64907905 |
| P5–P95 | -0.99383858 | 1.9322194 | 9550674 | 90.003969 | 530562 | 4.9999284 | 530156 | 4.9961023 | 0.66968845 | 0.76717248 | 0.44506637 |

Candidate endpoints come from the observed empirical quantiles, not predetermined sensitivity values. Inclusive bounds preserve ties, so retained percentages can differ slightly from nominal quantile coverage. These are counterfactual subset summaries, not changes to the authoritative data. The P1–P99 candidate retains approximately 98.005% and has SD 1.0331, compared with full VALID SD 7.0373, while its median remains approximately 0.76717. This quantifies tail influence without selecting epsilon_min or epsilon_max.

## Authoritative Evidence Files and Remaining Decisions

- Processed `authoritative_epsilon_jan_mar_2026.parquet`: one authoritative epsilon field/status for every historical row.
- Processed `authoritative_epsilon_methodology.json`: exact frozen references, resolution rule, counts and unresolved decisions.
- `relative_price_deviation_diagnostic.csv`: numerator-band signed-epsilon summaries.
- `authoritative_epsilon_summary.csv`: full valid-population statistics and quantiles.
- `authoritative_epsilon_bins.csv`: quantile-based intervals plus zero, counts, percentages and cumulative percentages; left-inclusive/right-exclusive except the last right-inclusive bin.
- `epsilon_empirical_range_candidates.csv`: inclusive empirical-bound comparisons; none selected.
- `clear_rain_authoritative_epsilon_diagnostic.csv`: 44 observed valid-epsilon weather/hour groups; descriptive preparation, not fitted/final group distributions.
- `charts/authoritative_epsilon_histogram_full.png`: all VALID observations, symmetric-log counts.
- `charts/authoritative_epsilon_histogram_p01_p99.png`: central P01–P99 display only.
- `charts/authoritative_epsilon_ecdf.png`: empirical cumulative probabilities from full-data ranks.

The remaining decisions are epsilon bounds, final weather-group distribution parameters and simulation distribution. Historical/diagnostic outputs remain unchanged except the authorized README update. Validation confirms all row identifiers/order, persisted null/status masks, finite valid values, reconciled population totals and historical artifact hashes.

## Empirical Sensitivity Range — Phase 5

### Authoritative distribution and scope

This review uses only the 10,611,392 VALID observations in the authoritative epsilon dataset. Frozen references, the strict half-resolution denominator treatment, retained short trips and signed formula are unchanged. All six previously calculated empirical ranges are reused and their counts/mean/median/SD verified. New work adds quantiles, side-specific tail review and within-group consistency. No candidate restriction is applied to the authoritative dataset.

### Tail structure

| quantile_pct | side | bound | beyond_bound_N | beyond_bound_pct |
| --- | --- | --- | --- | --- |
| 0.010000 | lower | -216.131688 | 1057 | 0.009961 |
| 0.050000 | lower | -78.699047 | 5306 | 0.050003 |
| 0.100000 | lower | -51.198452 | 10143 | 0.095586 |
| 0.250000 | lower | -24.258856 | 26529 | 0.250005 |
| 0.500000 | lower | -12.890744 | 53057 | 0.500000 |
| 1.000000 | lower | -6.717668 | 105808 | 0.997117 |
| 2.500000 | lower | -2.567666 | 265285 | 2.500002 |
| 5.000000 | lower | -0.993839 | 530562 | 4.999928 |
| 95.000000 | upper | 1.932219 | 530156 | 4.996102 |
| 97.500000 | upper | 3.378493 | 265283 | 2.499983 |
| 99.000000 | upper | 7.723411 | 105911 | 0.998088 |
| 99.500000 | upper | 15.442448 | 53057 | 0.500000 |
| 99.750000 | upper | 29.059711 | 26524 | 0.249958 |
| 99.900000 | upper | 52.070827 | 10424 | 0.098234 |
| 99.950000 | upper | 76.817054 | 5169 | 0.048712 |
| 99.990000 | upper | 161.271763 | 1062 | 0.010008 |

Tails are materially asymmetric rather than mirror images: the outermost negative quantile has a larger magnitude than its positive counterpart, while several less-extreme positive quantiles exceed corresponding negative magnitudes. Positive and negative probabilities and endpoint magnitudes should therefore be assessed separately rather than imposing symmetric bounds. Quantile spacing expands progressively into both tails; these summaries do not establish a unique structural break or a natural cutoff.

### Six empirical range candidates

| candidate | lower_bound | upper_bound | retained_N | retained_pct | excluded_negative_N | excluded_negative_pct | excluded_positive_N | excluded_positive_pct | mean | median | population_SD | P05 | P95 | P99 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0.01–P99.99 | -216.131688 | 161.271763 | 10609273 | 99.980031 | 1057 | 0.009961 | 1062 | 0.010008 | 0.656545 | 0.767172 | 4.820672 | -0.991178 | 1.932219 | 7.723411 |
| P0.1–P99.9 | -51.198452 | 52.070827 | 10590825 | 99.806180 | 10143 | 0.095586 | 10424 | 0.098234 | 0.662659 | 0.767172 | 2.907400 | -0.964480 | 1.910577 | 7.102821 |
| P0.5–P99.5 | -12.890744 | 15.442448 | 10505278 | 98.999999 | 53057 | 0.500000 | 53057 | 0.500000 | 0.651658 | 0.767172 | 1.444588 | -0.853697 | 1.817335 | 5.360343 |
| P1–P99 | -6.717668 | 7.723411 | 10399673 | 98.004795 | 105808 | 0.997117 | 105911 | 0.998088 | 0.650515 | 0.767172 | 1.033116 | -0.735817 | 1.718378 | 4.169350 |
| P2.5–P97.5 | -2.567666 | 3.378493 | 10080824 | 95.000015 | 265285 | 2.500002 | 265283 | 2.499983 | 0.657018 | 0.767172 | 0.649079 | -0.462706 | 1.506620 | 2.566246 |
| P5–P95 | -0.993839 | 1.932219 | 9550674 | 90.003969 | 530562 | 4.999928 | 530156 | 4.996102 | 0.669688 | 0.767172 | 0.445066 | -0.172823 | 1.302674 | 1.719077 |

Retained percentages use inclusive endpoints; empirical ties explain departures from nominal coverage. The global median is highly stable across candidates, while means shift modestly and SD declines strongly as more tail probability is excluded. Lower SD alone is not evidence of a superior model. P05/P95/P99 of each retained population are recorded in the comparison file.

### Tail observation review

All six candidates were reviewed on both sides using all observations outside their intervals. The compact tail CSV reports full-tail fare/distance ranges and quantiles, relative-price/deviation summaries, and shares in the previously used absolute relative-distance bands (<0.005, <0.01). A numerator diagnostic abs(relative_price_deviation)>=1 means the fare deviation is at least P_base, not an invalid-price threshold. The minimum absolute distance gap reports proximity to the frozen 0.005-mile boundary directly.

| candidate | tail | N | fare_median | distance_median | abs_relative_distance_median | pct_abs_relative_distance_lt_01 | pct_abs_relative_price_ge1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0.01–P99.99 | negative | 1057 | 44.300000 | 3.010000 | 0.002650 | 98.107852 | 53.736991 |
| P0.01–P99.99 | positive | 1062 | 47.740000 | 3.030000 | 0.003977 | 87.476460 | 61.487759 |
| P0.1–P99.9 | negative | 10143 | 33.420000 | 3.000000 | 0.005964 | 76.880607 | 27.437642 |
| P0.1–P99.9 | positive | 10424 | 30.300000 | 3.030000 | 0.005964 | 72.524942 | 24.721796 |
| P0.5–P99.5 | negative | 53057 | 29.210000 | 2.990000 | 0.012591 | 39.949488 | 21.586219 |
| P0.5–P99.5 | positive | 53057 | 24.000000 | 3.030000 | 0.009277 | 52.362553 | 17.475545 |
| P1–P99 | negative | 105808 | 28.200000 | 2.980000 | 0.027171 | 23.054022 | 19.993762 |
| P1–P99 | positive | 105911 | 25.870000 | 3.040000 | 0.020544 | 30.687086 | 17.258831 |
| P2.5–P97.5 | negative | 265285 | 28.180000 | 2.900000 | 0.060305 | 9.976063 | 20.025256 |
| P2.5–P97.5 | positive | 265283 | 24.130000 | 3.040000 | 0.049039 | 13.308429 | 15.974261 |
| P5–P95 | negative | 530562 | 27.020000 | 2.800000 | 0.111994 | 5.366951 | 14.900803 |
| P5–P95 | positive | 530156 | 19.130000 | 3.000000 | 0.096753 | 6.767253 | 14.236753 |

Tail observations combine proximity to the denominator boundary and differing fare deviations; contributions differ by tail and candidate width. Wider exclusions encompass less extreme, potentially ordinary observations as well as large ratios. No plausible trip is labelled invalid, and this evidence does not establish that the omitted records are source errors. Short raw distance and small deviation from L_base remain distinct mechanisms.

### Clear/Rain consistency

| candidate | median_retained_pct | minimum_retained_pct | maximum_retained_pct | median_mean_change | median_median_change | median_SD_change |
| --- | --- | --- | --- | --- | --- | --- |
| P0.01–P99.99 | 99.977741 | 99.825073 | 100.000000 | 0.009462 | 0.000000 | -1.954810 |
| P0.1–P99.9 | 99.791980 | 99.494655 | 99.920234 | 0.021309 | 0.000000 | -3.969760 |
| P0.5–P99.5 | 98.921751 | 97.951958 | 99.387151 | 0.005921 | 0.000000 | -5.447372 |
| P1–P99 | 97.801701 | 96.112731 | 98.774303 | 0.005593 | 0.000000 | -5.882115 |
| P2.5–P97.5 | 94.524109 | 90.165209 | 96.844181 | 0.016737 | 0.000137 | -6.269796 |
| P5–P95 | 88.783337 | 80.174927 | 93.941955 | 0.034333 | 0.000905 | -6.477800 |

There are 44 observed groups for each of the six candidates, with no imputation. Across-group summaries weight each group equally; changes are signed retained-minus-original statistics. Minimum/maximum retention identifies uneven exclusion across weather/hour groups and does not assume global quantile coverage applies equally to each group. The complete 264-row table records each group's response.

### Recommendation status and remaining choice

The evidence does not uniquely justify one empirical cutoff. **PROJECT METHODOLOGY RECOMMENDATION FOR REVIEW:** prioritize P0.1–P99.9 and P1–P99 as the two clearest contrasting candidates: the former preserves approximately 99.8% and limits truncation of observed behavior; the latter retains approximately 98% and provides a substantially more concentrated central range while preserving the global median. This shortlist balances retained probability, central-location stability and interpretability; it is not a claim that either boundary marks invalid data or a verified structural break. The intermediate P0.5–P99.5 remains a valid compromise and is not statistically ruled out.

No range is frozen or supervisor-approved. Selection requires an explicit judgement about acceptable tail probability and group-specific retention, followed by model validation; no distribution fitting or simulation work is performed here.

### Phase 5 evidence files

- `epsilon_tail_quantiles.csv`: separate lower/upper quantiles and strict beyond-bound counts.
- `epsilon_range_comparison_final.csv`: six expanded comparison summaries; “final” denotes this comparison table, not approval of any range.
- `epsilon_tail_observation_review.csv`: twelve full-tail review summaries.
- `epsilon_range_weather_hour_consistency.csv`: 264 group/candidate comparisons.
- `charts/epsilon_empirical_range_comparison.png`: population/group retention, central location and SD comparisons.

Authoritative Parquet/methodology and all earlier analysis artifacts remain byte-identical; only this README is appended.

Group-specific exclusion is appreciably uneven for narrower ranges. Rain 02:00 has the lowest retention for P0.1–P99.9 (99.494655%), P1–P99 (96.112731%), P2.5–P97.5 (90.165209%) and P5–P95 (80.174927%); Rain 00:00 is lowest for P0.5–P99.5 (97.951958%). Thus nominal 90% global retention can retain only about 80% in an observed hourly group. This weighs against selecting the narrowest intervals merely for low SD and favors retaining both probability preservation and hourly distortion as explicit decision criteria.

## Frozen Empirical Epsilon Support

The frozen PROJECT METHODOLOGY DECISION is epsilon_min = **−12.890744316473482** and epsilon_max = **15.442447741158892**, the exact persisted empirical P0.5/P99.5 endpoints. Both endpoints are inclusive. `data/processed/price_distance_sensitivity_record029/frozen_epsilon_support.json` records the values, rule, counts and rationale.

Of 10,611,392 authoritative VALID observations, **10,505,278 (98.99999924609325%)** are in simulation support. There are **53,057 (0.5000003769533724%)** below and the same number above. The 9,017 unresolved denominator rows are a separate historical status and are not included in this VALID denominator. No historical row is deleted, relabelled invalid or clipped. Existing short-trip handling remains unchanged.

The support is empirical and asymmetric, retains approximately 99% of valid observations, preserves central mean/median behavior and materially limits rare denominator-sensitive tails. No natural structural break was established. The rule balances these considerations rather than selecting the minimum-SD interval. Earlier Phase-5 alternatives remain evidence, not competing current support definitions.

## Final Clear/Rain Hourly Distribution Analysis

The empirical table uses authoritative VALID epsilon within the inclusive frozen support. “Final” denotes descriptive statistics under these frozen rules, not final simulation-distribution parameters. Original-group retention uses each weather/hour group's authoritative VALID count before applying the support. All 44 observed groups are present; Rain hours 5, 10, 11 and 12 remain absent.

### Overall weather comparison

| weather | N | mean | median | population_SD | variance | P05 | P25 | P50 | P75 | P95 | P99 | min | max | IQR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clear | 3050121 | 0.621737 | 0.734565 | 1.478379 | 2.185603 | -0.967745 | 0.370593 | 0.734565 | 0.931763 | 1.807494 | 5.489121 | -12.889572 | 15.442447 | 0.561170 |
| Rain | 215014 | 0.654704 | 0.779043 | 1.512583 | 2.287906 | -0.999502 | 0.391768 | 0.779043 | 0.950631 | 1.932219 | 5.735770 | -12.890725 | 15.384341 | 0.558863 |

Pooled Rain minus Clear mean is 0.032966, median difference 0.044478, and SD ratio 1.023136. IQRs are 0.561170 (Clear) and 0.558863 (Rain). Their one-dimensional Wasserstein distance is 0.040511 epsilon units. These pooled summaries support considering shared weather behavior, but do not prove equivalence; unequal weather/hour composition can conceal conditional differences.

### Hour and same-hour comparisons

| weather_name | hour | N | percentage_original_group_retained | mean | median | population_SD | P25 | P75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clear | 0 | 94466 | 98.659008 | 0.598433 | 0.690659 | 1.662968 | 0.267569 | 0.985598 |
| Clear | 1 | 56391 | 98.780808 | 0.610907 | 0.723838 | 1.627537 | 0.237241 | 0.991832 |
| Clear | 2 | 35516 | 98.856014 | 0.610722 | 0.755789 | 1.685729 | 0.227774 | 1.008568 |
| Clear | 3 | 23313 | 98.650135 | 0.641472 | 0.727070 | 1.707514 | 0.236149 | 1.038486 |
| Clear | 4 | 19257 | 98.597102 | 0.581193 | 0.517107 | 1.798144 | 0.215674 | 0.992247 |
| Clear | 5 | 31605 | 98.630009 | 0.586601 | 0.495891 | 1.605424 | 0.282660 | 0.983572 |
| Clear | 6 | 64055 | 98.672151 | 0.665385 | 0.682187 | 1.649757 | 0.314518 | 1.013545 |
| Clear | 7 | 117426 | 98.497697 | 0.673339 | 0.788984 | 1.748030 | 0.345309 | 1.010286 |
| Clear | 8 | 163042 | 98.436293 | 0.613795 | 0.748238 | 1.722581 | 0.353409 | 0.944488 |
| Clear | 9 | 163703 | 98.881339 | 0.614405 | 0.714805 | 1.480421 | 0.364617 | 0.914543 |
| Clear | 10 | 153317 | 99.151518 | 0.598405 | 0.695204 | 1.324122 | 0.369794 | 0.896573 |
| Clear | 11 | 142417 | 99.088550 | 0.585498 | 0.684531 | 1.329943 | 0.371141 | 0.883358 |
| Clear | 12 | 167979 | 99.141259 | 0.598279 | 0.698548 | 1.327537 | 0.377867 | 0.891691 |
| Clear | 13 | 152341 | 99.059738 | 0.616177 | 0.707458 | 1.345136 | 0.394380 | 0.897320 |
| Clear | 14 | 191474 | 99.077907 | 0.611426 | 0.710427 | 1.365181 | 0.415258 | 0.890486 |
| Clear | 15 | 207217 | 99.038848 | 0.566080 | 0.692543 | 1.436744 | 0.389381 | 0.880293 |
| Clear | 16 | 188333 | 99.334895 | 0.651257 | 0.750301 | 1.220852 | 0.446051 | 0.905519 |
| Clear | 17 | 185684 | 99.226215 | 0.638471 | 0.773489 | 1.304978 | 0.437261 | 0.920291 |
| Clear | 18 | 169155 | 99.145434 | 0.652930 | 0.787117 | 1.345523 | 0.435592 | 0.931110 |
| Clear | 19 | 147729 | 99.196911 | 0.650332 | 0.802969 | 1.341818 | 0.410908 | 0.950322 |
| Clear | 20 | 167377 | 98.764973 | 0.657487 | 0.804114 | 1.573715 | 0.388107 | 0.985598 |
| Clear | 21 | 154879 | 98.499727 | 0.626672 | 0.785350 | 1.687090 | 0.358286 | 0.991092 |
| Clear | 22 | 141078 | 98.632493 | 0.621032 | 0.733181 | 1.645622 | 0.329005 | 0.985598 |
| Clear | 23 | 112367 | 98.855439 | 0.626123 | 0.695534 | 1.582831 | 0.308216 | 0.986024 |
| Rain | 0 | 14109 | 97.951958 | 0.560212 | 0.756110 | 1.932934 | 0.162575 | 1.048943 |
| Rain | 1 | 970 | 99.182004 | 0.451969 | 0.429326 | 1.300291 | 0.282649 | 0.847556 |
| Rain | 2 | 5060 | 98.347911 | 0.567694 | 0.766403 | 2.071300 | 0.136844 | 1.056748 |
| Rain | 3 | 6262 | 98.567606 | 0.658782 | 0.790546 | 2.002698 | 0.180238 | 1.080731 |
| Rain | 4 | 2429 | 98.619570 | 0.651903 | 0.576685 | 1.762306 | 0.243800 | 1.014967 |
| Rain | 6 | 2296 | 98.922878 | 0.659448 | 0.665850 | 1.472266 | 0.328067 | 0.991436 |
| Rain | 7 | 24795 | 98.666932 | 0.729558 | 0.818512 | 1.675792 | 0.376143 | 1.010286 |
| Rain | 8 | 12153 | 98.981919 | 0.664990 | 0.792671 | 1.485717 | 0.409757 | 0.948215 |
| Rain | 9 | 10587 | 99.371128 | 0.680866 | 0.782295 | 1.244688 | 0.430528 | 0.931860 |
| Rain | 13 | 18293 | 99.310532 | 0.675923 | 0.751154 | 1.162215 | 0.472325 | 0.891130 |
| Rain | 14 | 14109 | 99.387151 | 0.657236 | 0.729820 | 1.137559 | 0.459226 | 0.878517 |
| Rain | 15 | 16887 | 99.189427 | 0.611158 | 0.731578 | 1.248621 | 0.461211 | 0.877540 |
| Rain | 16 | 3593 | 99.144592 | 0.791384 | 0.905519 | 1.368879 | 0.523058 | 1.040136 |
| Rain | 17 | 11200 | 99.264380 | 0.731870 | 0.838207 | 1.251829 | 0.503846 | 0.955990 |
| Rain | 18 | 18393 | 99.287449 | 0.638941 | 0.802875 | 1.285710 | 0.446486 | 0.928607 |
| Rain | 19 | 19030 | 99.057831 | 0.637902 | 0.752199 | 1.489476 | 0.385927 | 0.929868 |
| Rain | 20 | 9786 | 98.223427 | 0.573390 | 0.834319 | 1.789913 | 0.375705 | 0.991245 |
| Rain | 21 | 12305 | 99.018267 | 0.708130 | 0.827928 | 1.530478 | 0.390045 | 1.003670 |
| Rain | 22 | 5957 | 98.920624 | 0.672901 | 0.807932 | 1.554557 | 0.344133 | 1.021051 |
| Rain | 23 | 6800 | 98.550725 | 0.548560 | 0.680247 | 1.874208 | 0.262076 | 0.963972 |

The comparison CSV includes pooled weather, all 20 same-hour Clear/Rain pairs, and every within-weather hour pair (276 Clear and 190 Rain pairs). Signed differences are B minus A; SD ratio is B/A. Wasserstein distance compares entire empirical distributions without fitting a family. No significance tests or formal materiality cutoffs are imposed.

Hourly median ranges are 0.495891–0.804114 for Clear and 0.429326–0.905519 for Rain; SD ranges are 1.220852–1.798144 and 1.137559–2.071300. Within-weather hourly Wasserstein distances have median 0.194272 and maximum 0.620803, exceeding the pooled weather distance in typical comparisons. Same-hour weather distance has median 0.113856 and maximum 0.301670, so weather differences cannot be dismissed uniformly. Rain support varies substantially (for example, 970 supported observations at 01:00), which limits strong claims from individual hourly contrasts.

### Simplest supported grouping recommendation

A single pooled Clear/Rain distribution is a plausible coarse baseline because aggregate centers, IQR and SD are close. It is not sufficient to preserve the observed time-of-day variation. Merely separating Clear from Rain does not address that variation. Conversely, the evidence does not justify automatically fitting 44 independent Weather × Hour distributions.

**PROJECT RECOMMENDATION, not a fitted or approved grouping:** evaluate a small number of shared time-of-day groups across Clear/Rain as the simplest supported next modelling structure. Hour is the clearer conditioning dimension in the present descriptive evidence. Exact group number and boundaries are not identified by these pairwise comparisons and should be validated before adoption; same-hour weather discrepancies should be checked within proposed shared groups. No data-driven clustering, boundary optimization or final distribution selection has been performed.

### Files and validation

- `final_clear_rain_hourly_epsilon_statistics.csv`: N, original-group retention, mean/median, population SD/variance, P05/P25/P50/P75/P95/P99 and extrema.
- `clear_rain_hourly_distribution_comparison.csv`: pooled, same-hour and within-weather pairwise differences, IQRs, quantile differences and Wasserstein distances (487 comparisons).
- `charts/final_clear_vs_rain_epsilon_distribution.png`: normalized empirical densities on common support, not fitted curves.
- `charts/final_hourly_epsilon_median.png`: supported hourly medians with gaps for unobserved hours.
- `charts/final_hourly_epsilon_sd.png`: supported hourly population SDs with the same gaps.

Frozen endpoints were read with round-trip precision from Phase 5. Full support counts reproduce the existing range comparison, 44 groups are retained, and every historical authoritative/diagnostic artifact remains unchanged apart from this authorized README update. No simulation distribution is fitted; family, grouping and parameters remain open.

## Final Time Grouping

The frozen project grouping is T1=00–03, T2=04–05, T3=06–15 and T4=16–23 (inclusive integer hours). Exact pooled hourly quantiles were calculated from supported Clear/Rain observations because subgroup medians cannot be averaged into a pooled median. Existing hourly N/mean/variance were reused and verified. No raw preparation or epsilon reconstruction was performed.

Contiguous partitions for K=1–4 were evaluated exhaustively on trip-count-weighted squared deviation of hourly medians from each segment's weighted center. Optimal boundaries and objective values: K1 [0,24], 8347.2990; K2 [0,16,24], 5325.6172; K3 [0,16,22,24], 4356.5065; K4 [0,4,6,16,24], 3056.7070. The comparison CSV records exact pooled profiles, adjacent-hour differences, group statistics and minimum Rain support.

K3 leaves the pronounced 04–05 median trough unrepresented; K4 captures it and reduces the objective by 29.8% beyond K3 (63.4% relative to K1). Improvement is not monotonic in K, so the smaller K2→K3 gain is not a reliable elbow by itself. K4 is the smallest tested representation capturing the trough and later-day transition. K5 was not evaluated because remaining fluctuations do not clearly establish a need for another group; its lack of benefit is not mathematically proved. These linear day partitions are interpretable project choices, not naturally identified clusters or formal equivalence tests.

## Final Weather Decision

TIME-ONLY GROUPING is frozen: Clear and Rain share each time group's empirical source.

| time_group | N_Clear | N_Rain | mean_Clear | mean_Rain | mean_difference_Rain_minus_Clear | median_Clear | median_Rain | median_difference_Rain_minus_Clear | SD_Clear | SD_Rain | SD_difference_Rain_minus_Clear | P05_Clear | P05_Rain | P05_difference_Rain_minus_Clear | P25_Clear | P25_Rain | P25_difference_Rain_minus_Clear | P75_Clear | P75_Rain | P75_difference_Rain_minus_Clear | P95_Clear | P95_Rain | P95_difference_Rain_minus_Clear | SD_ratio_Rain_over_Clear |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 209686 | 26401 | 0.608654 | 0.581048 | -0.027606 | 0.713870 | 0.743591 | 0.029721 | 1.662492 | 1.958241 | 0.295748 | -1.318984 | -1.970521 | -0.651537 | 0.249193 | 0.171978 | -0.077215 | 0.992007 | 1.050547 | 0.058541 | 2.238010 | 2.818563 | 0.580553 | 1.177895 |
| T2 | 50862 | 2429 | 0.584553 | 0.651903 | 0.067350 | 0.502291 | 0.576685 | 0.074395 | 1.680994 | 1.762306 | 0.081312 | -1.210721 | -1.157913 | 0.052808 | 0.262944 | 0.243800 | -0.019143 | 0.990966 | 1.014967 | 0.024000 | 2.287381 | 2.505523 | 0.218142 | 1.048372 |
| T3 | 1522971 | 99120 | 0.608163 | 0.674452 | 0.066289 | 0.710041 | 0.761015 | 0.050974 | 1.461696 | 1.374563 | -0.087133 | -0.925731 | -0.657104 | 0.268627 | 0.373305 | 0.433131 | 0.059827 | 0.909001 | 0.923205 | 0.014204 | 1.729784 | 1.738630 | 0.008846 | 0.940389 |
| T4 | 1266602 | 87064 | 0.641719 | 0.654635 | 0.012916 | 0.773415 | 0.807929 | 0.034514 | 1.456858 | 1.499205 | 0.042347 | -0.942080 | -1.026744 | -0.084664 | 0.393433 | 0.404438 | 0.011006 | 0.946740 | 0.962475 | 0.015735 | 1.794976 | 1.868147 | 0.073171 | 1.029067 |

Weather effects vary across groups and quantiles rather than consistently separating the distributions. Given modest overall separation, unequal weather support and a preference for parsimonious modelling, separate weather-specific samplers are not adopted. This decision does not assert exact weather invariance or causal equivalence. It is a project modelling decision; independent temporal validation remains useful for assessing transportability.

## Final Simulation Distribution

Only empirical sampling and truncated Normal were compared. Truncated-Normal mu/sigma were estimated by constrained maximum likelihood on the full supported group, with fixed support endpoints; parameters are latent Normal parameters, not simply assumed to equal empirical moments. KS is reported descriptively, without a fitted-parameter null p-value.

| group_name | KS | absolute_error_median | absolute_error_P25 | absolute_error_P75 | absolute_error_P05 | absolute_error_P95 |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 0.214419 | 0.110759 | 0.782062 | 0.752225 | 0.798201 | 1.097299 |
| T2 | 0.221748 | 0.082891 | 0.810636 | 0.733067 | 0.974266 | 1.069105 |
| T3 | 0.253730 | 0.100896 | 0.746927 | 0.685680 | 0.875147 | 1.278336 |
| T4 | 0.242263 | 0.132973 | 0.736026 | 0.679207 | 0.813089 | 1.242479 |

Systematic central and tail quantile errors remain despite moment agreement. EMPIRICAL is therefore frozen. The fitted comparison is retained as evidence, not selected simulation parameters. Uniform resampling of historical rows preserves the empirical distribution, including repeated values and negative sensitivity within frozen support.

## Final Record-029 Methodology

P_base=21.34586956773507 USD; tau_P=±$1; L_base=3.01799878914405 miles; epsilon=relative price deviation / relative distance deviation; resolution 0.01 mile; unresolved denominator when abs(distance−L_base)<0.005 mile; no L_min; inclusive support [−12.890744316473482,15.442447741158892]. The final population is 3,265,135 supported Clear/Rain observations, assigned exclusively to the four time groups.

Historical data retain all source-valid trips. Unresolved-denominator rows remain historical with undefined epsilon. VALID epsilon outside support remains valid history and is omitted only from simulation support. Only the supported Clear/Rain population supplies this final sampler. No historical record or production code is changed.

## Simulation Input Specification

| group_name | start_hour | end_hour | weather_scope | N | epsilon_min | epsilon_max | sampling_method |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | 0 | 3 | Clear (1) and Rain (8), shared | 236087 | -12.890744 | 15.442448 | EMPIRICAL_RESAMPLE |
| T2 | 4 | 5 | Clear (1) and Rain (8), shared | 53291 | -12.890744 | 15.442448 | EMPIRICAL_RESAMPLE |
| T3 | 6 | 15 | Clear (1) and Rain (8), shared | 1622091 | -12.890744 | 15.442448 | EMPIRICAL_RESAMPLE |
| T4 | 16 | 23 | Clear (1) and Rain (8), shared | 1353666 | -12.890744 | 15.442448 | EMPIRICAL_RESAMPLE |

Use `data/processed/price_distance_sensitivity_record029/final_passenger_sensitivity_empirical.parquet` (only time_group and epsilon). Given hour 0–23 and Clear/Rain weather, map the hour to one group and draw uniformly from that group's rows WITH replacement. Preserve repeated values as empirical mass; use a caller-controlled random seed. Do not sample groups uniformly, interpolate quantiles, clip, or refit. Unsupported weather requires a separately approved fallback; this model supplies none. Production integration is not performed here.

`final_passenger_sensitivity_methodology.json` records frozen decisions and sampling semantics; `final_passenger_sensitivity_parameters.csv` lists group supports and EMPIRICAL_RESAMPLE. Other additions are the grouping/weather/fit comparison CSVs and exactly two charts: `final_time_grouping.png` and `final_distribution_fit.png`.

Historical data → P_base → ±$1 price conditioning → L_base → relative price/distance deviations → measurement-resolution denominator handling → authoritative epsilon → P0.5–P99.5 simulation support → four time groups → shared Clear/Rain → empirical distribution → uniform within-group empirical resampling.
