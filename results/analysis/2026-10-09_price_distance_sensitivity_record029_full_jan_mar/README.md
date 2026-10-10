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

The numerator is relative price deviation and the denominator is relative distance deviation. Epsilon is signed and dimensionless. Exact-zero denominators would yield undefined epsilon, explicitly flagged while preserving the source row. The observed exact-zero count is **zero for all four candidates**. No nonzero near-zero denominator or large epsilon is excluded. No clipping, winsorization, trimming, extra normalization or fitted sensitivity distribution is applied.

### Full-population candidate comparison

| tau_P | mean_epsilon | median_epsilon | SD_epsilon | P95 | P99 | max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- |
| 0.250000 | 0.787444 | 0.764566 | 28.904610 | 1.903402 | 7.735824 | 24569.490215 |
| 0.500000 | 0.445895 | 0.768680 | 34.102016 | 1.957584 | 7.803063 | 11516.595900 |
| 1.000000 | 0.739608 | 0.767133 | 19.277050 | 1.943506 | 7.995343 | 7676.417735 |
| 2.000000 | 0.613266 | 0.766457 | 13.589164 | 1.917327 | 7.888783 | 11660.273365 |

Each candidate has 10,620,409 valid epsilon observations. Population SD uses ddof=0; empirical quantiles use linear interpolation. Medians are comparatively stable, while means, SDs and extreme magnitudes vary appreciably. Signed epsilon is retained, including negative values; sign is not an automatic source-validity classification.

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

## Current Methodological Status

The following remain unresolved methodology decisions; none is finalized:

- tau_P.
- The resulting final L_base.
- L_min.
- Near-zero relative-distance-deviation treatment.
- epsilon_min and epsilon_max.
- Final sensitivity distribution.
- Truncated-normal parameters.

Existing candidate estimates and review flags are evidence for those decisions, not approved parameter choices. All full-data observations remain retained. The available results neither authorize automatic deletion of extremes nor establish a truncated Normal distribution as the appropriate model.

## Required Next Steps

1. **Supervisor/research agreement:** decide tau_P and final L_base using substantive reference rationale and the documented numerical sensitivity.
2. **Supervisor/methodology agreement:** decide principled handling of observations where abs((L−L_base)/L_base) approaches zero; review numerical and source-quality implications separately.
3. **Implementation after steps 1–2:** recalculate the authoritative epsilon distribution using those frozen decisions and document support and exclusions, if any.
4. **Empirical assessment and methodology agreement:** determine empirically justified epsilon_min and epsilon_max; do not infer them solely from the current tails or candidate SD ranking.
5. **Implementation after the relevant decisions:** rerun/finalize Clear/Rain weather-hour statistics using the frozen method.
6. **Comparative analysis and research decision:** compare group distributions and determine whether separate sensitivity models are necessary.
7. **Model selection, agreement and validation:** select and validate the bounded/truncated empirical distribution; estimate parameters only for the agreed model and population.
8. **Implementation after model validation:** only then define the passenger-sensitivity sampler for simulation. Simulation integration is not established by the present diagnostic results.

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

The completed work establishes full-population candidate calculations, numerical reference sensitivity, source-validation findings and a traceable population with review flags. It does not establish the final reference window, a universal distance cutoff, an epsilon deletion policy or a simulation-ready distribution. Review labels and diagnostic bounds preserve observations rather than adjudicating validity. Methodological agreement and subsequent frozen-method implementation remain distinct stages.
