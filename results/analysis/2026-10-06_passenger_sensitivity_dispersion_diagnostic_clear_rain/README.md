# Passenger-sensitivity dispersion diagnostic — Clear / Rain

## Scope and frozen methodology

The professor's concern is high population SD relative to mean elasticity. This is diagnostic only, restricted to actual Clear (WeatherCode 1) and Rain (8), hours 0–23. Snowfall is excluded only from this follow-up scope; canonical methodology remains unchanged.

The existing paired-observation Parquet is `data/processed/elasticity_v2/actual_weather_hour_price_distance_arrays_2026_01_03.parquet`. It preserves the cleaned Jan–Mar 2026 population's trip pairing and order. Original cleaned population N=10,620,409, with 0 < trip_distance <=100 miles; Clear/Rain support is 3,303,107. No raw-data preparation was run.

P_base=21.34586956773507 USD; L_base=3.46907003958134 miles. Neither was re-estimated.

```text
delta_P = (price-P_base)/P_base
delta_L = (distance-L_base)/L_base
epsilon = delta_L/delta_P
```

Signed epsilon is retained. Exact-zero delta_P exclusion only (0 exclusions). No denominator threshold, clipping, trimming, normalization, imputation, clustering or synthetic sensitivity. Population variance and SD use numpy.var/std with ddof=0. Quantiles use linear interpolation.

## OBSERVATION: independent verification and selection

All 44 observed Clear/Rain groups pass independent N, mean, variance and population-SD comparisons with the canonical CSV (rtol=1e-11, atol=1e-12 for floating-point arithmetic). Variance fields supplement the requested verification columns. Rank is descending recalculated population SD, with weather code/hour deterministic tie breaks. Clear 23:00 was automatically selected as rank 1, not manually chosen.

Top 10 groups:

| rank | weather_name | hour | n | recomputed_mean | recomputed_sd |
| --- | --- | --- | --- | --- | --- |
| 1 | Clear | 23 | 113775 | 1.122915 | 43.986403 |
| 2 | Clear | 5 | 32073 | 1.241690 | 41.114246 |
| 3 | Rain | 19 | 19235 | 1.496421 | 39.574819 |
| 4 | Clear | 3 | 23657 | 1.335006 | 35.833769 |
| 5 | Rain | 2 | 5155 | 0.802874 | 35.426164 |
| 6 | Clear | 8 | 165769 | 1.387338 | 33.452482 |
| 7 | Rain | 3 | 6361 | 1.547692 | 33.121260 |
| 8 | Clear | 1 | 57138 | 1.278495 | 32.558658 |
| 9 | Clear | 7 | 119329 | 1.118810 | 30.440942 |
| 10 | Clear | 4 | 19549 | 1.434058 | 30.391032 |

## OBSERVATION: complete selected distribution

All 113,775 observations are used. Mean=1.122914800; median=1.178884791; variance=1934.803641433; population SD=43.986402915. Min=-10599.509449943; max=3919.354668418; max absolute epsilon=10599.509449943.

- P01: -15.602574000
- P05: -2.034094983
- P25: 0.859166221
- P50: 1.178884791
- P75: 1.840228779
- P95: 4.324441698
- P99: 16.555641876

The full histogram and bin CSV use 15 equal-width bins spanning min to max: left-inclusive/right-exclusive, except the last includes its right edge. Counts sum to N; no tail observation is omitted. The supplementary P01–P99 histogram restricts display only, uses 15 bins over displayed observations, and does not affect any reported calculation. Strong full-range histogram concentration reflects the long tails, not omitted observations.

## OBSERVATION: first 1,000 paired observations

`selected_group_first_1000_price_distance_epsilon.csv` contains exactly the first 1,000 valid observations of Clear 23:00 in existing source order. `source_row_index` is the naturally available zero-based Parquet row position, not a claimed unique trip ID. Price, distance, relative deltas and signed epsilon remain paired. No random sampling, per-hour sampling or independent column sorting is used.

## OBSERVATION: top 20 extreme observations

The top-100 export is selected from the FULL group, ordered by descending abs(epsilon), breaking ties by source row position. The following per-record classifications are descriptive explanations, not automatic cleaning criteria. A denotes small-denominator amplification; C denotes that amplification together with a large distance deviation. B alone is not supported for these top 20. D (suspicious source data) cannot be established from epsilon alone. Rank 1 merits context review without an invalidity label.

| rank | price | distance | delta_P | delta_L | epsilon | descriptive_cause |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 21.340000 | 13.580000 | -0.000275 | 2.914594 | -10599.509450 | C: both small denominator and large relative-distance deviation |
| 2 | 21.350000 | 6.100000 | 0.000194 | 0.758396 | 3919.354668 | A: primarily small denominator |
| 3 | 21.350000 | 1.130000 | 0.000194 | -0.674264 | -3484.564476 | A: primarily small denominator |
| 4 | 21.350000 | 1.170000 | 0.000194 | -0.662734 | -3424.975590 | A: primarily small denominator |
| 5 | 21.350000 | 1.420000 | 0.000194 | -0.590668 | -3052.545049 | A: primarily small denominator |
| 6 | 21.340000 | 1.050000 | -0.000275 | -0.697325 | 2535.964134 | A: primarily small denominator |
| 7 | 21.340000 | 1.120000 | -0.000275 | -0.677147 | 2462.581600 | A: primarily small denominator |
| 8 | 21.350000 | 1.830000 | 0.000194 | -0.472481 | -2441.758963 | A: primarily small denominator |
| 9 | 21.350000 | 1.880000 | 0.000194 | -0.458068 | -2367.272855 | A: primarily small denominator |
| 10 | 21.340000 | 1.430000 | -0.000275 | -0.587786 | 2137.601807 | A: primarily small denominator |
| 11 | 21.340000 | 1.520000 | -0.000275 | -0.561842 | 2043.252835 | A: primarily small denominator |
| 12 | 21.340000 | 1.690000 | -0.000275 | -0.512838 | 1865.038109 | A: primarily small denominator |
| 13 | 21.350000 | 2.380000 | 0.000194 | -0.313937 | -1622.411774 | A: primarily small denominator |
| 14 | 21.340000 | 4.860000 | -0.000275 | 0.400952 | -1458.142359 | A: primarily small denominator |
| 15 | 21.350000 | 4.300000 | 0.000194 | 0.239525 | 1237.854777 | A: primarily small denominator |
| 16 | 21.360000 | 1.340000 | 0.000662 | -0.613729 | -927.118579 | A: primarily small denominator |
| 17 | 21.330000 | 5.630000 | -0.000743 | 0.622913 | -837.869491 | A: primarily small denominator |
| 18 | 21.350000 | 2.930000 | 0.000194 | -0.155393 | -803.064585 | A: primarily small denominator |
| 19 | 21.360000 | 1.700000 | 0.000662 | -0.509955 | -770.354037 | A: primarily small denominator |
| 20 | 21.330000 | 1.570000 | -0.000743 | -0.547429 | 736.337075 | A: primarily small denominator |

All top-20 prices lie between $21.33 and $21.36, close to P_base. Rank 1 has delta_L≈2.915 and a denominator≈−0.000275. Other top-20 absolute relative-distance deviations are below one, yet small denominators magnify them into very large signed ratios. No observation has been declared invalid or removed.

## OBSERVATION: denominator bands

The following bands are diagnostic summaries only, using the full selected group. Empty bands have undefined distribution statistics (blank CSV cells), not zero quantiles.

| band | N | percentage | median_abs_epsilon | P95_abs_epsilon | P99_abs_epsilon | max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- |
| <0.00001 | 0 | 0.000000 | nan | nan | nan | nan |
| 0.00001–0.0001 | 0 | 0.000000 | nan | nan | nan | nan |
| 0.0001–0.001 | 37 | 0.032520 | 770.354037 | 3571.522515 | 8194.653729 | 10599.509450 |
| 0.001–0.01 | 1650 | 1.450231 | 32.480807 | 144.313599 | 272.034235 | 563.307024 |
| >=0.01 | 112088 | 98.517249 | 1.248757 | 5.253293 | 15.225867 | 105.156016 |

Only 37 trips (0.032520%) have abs(delta_P)<0.001, yet they contribute 95.403489% of the sum of squared deviations from the full-group mean. The largest 20 absolute-epsilon observations contribute 93.967129%. These are additive contributions to the original variance numerator, not SDs after trimming. They strongly support denominator amplification and concentrated tails as the provisional explanation for high SD.

## OBSERVATION: negative epsilon

Negative: 14,989 (13.174247%); positive: 98,786 (86.825753%); zero: 0. Among negative observations, 9,512 have delta_P>0 and delta_L<0; 5,477 have delta_P<0 and delta_L>0. Opposite-signed relative deviations produce negative epsilon algebraically; these observations remain included.

## Professor decision cases

**CASE_A**: Not established. Large epsilon alone does not establish invalid price/distance data. The leading $21.34 / 13.58-mile pair merits source-context review, but cannot be declared invalid from these fields.

**CASE_B**: Strongly supported: 37 observations (0.032520%) with abs(delta_P)<0.001 contribute 95.403489% of squared deviations about the full-group mean. All top 20 fall in that band.

**CASE_C**: Not supported as the principal cause of this group SD. The top 20 (0.017578% of the group) contribute 93.967129% of squared deviations. This does not imply zero dispersion among the remaining observations.

**CASE_D**: Calculation is verified. Suitability for downstream use requires a professor/project decision; the high SD and tail concentration warrant review but do not by themselves establish unusability.

## METHODOLOGY DECISION

None implemented. The diagnostic establishes numerical consistency and identifies sensitivity to very small price deviations. It does not choose a denominator threshold, reject source records, trim tails, modify references or change production. Any downstream method decision remains for professor/project review.

## Files and validation

The folder contains the requested verification and ranking CSVs; selected full-group distribution JSON; 15-bin CSV; exactly 1,000 paired observations; full-group top-100 CSV; denominator-band CSV; summary.json; this README; and three charts in `charts/` (full histogram, P01–P99 visualization, Clear/Rain SD versus hour). Missing Rain hours 5, 10, 11, 12 remain gaps.

Before/after SHA-256 checks preserve the source Parquet, canonical CSV, current methodology JSON and all canonical final-package files including README. No canonical or production files were written. Focused checks verify 44 groups, canonical support/statistics, histogram totals, pairing, sample order, full-group top-100 selection and sign partitions. No full analysis pipeline was rerun.

## Near-Zero Denominator Follow-up

### Price provenance and precision

`price` is a direct renamed TLC `fare_amount`, in USD, not a constructed total or price-per-mile. `scripts/prepare_elasticity_v2_population.py` reads `tpep_pickup_datetime`, `fare_amount`, and `trip_distance` from `data/raw/yellow_taxi/yellow_tripdata_2026-01.parquet`, `2026-02.parquet`, and `2026-03.parquet` (each has prefix `yellow_tripdata_`). `src/elasticity_v2/population.py:14` applies numeric coercion to `fare_amount`, and line 27 writes float64 `fare`. The cleaned Parquet retains `fare`; the paired-observation export renames it `price`. No arithmetic price transformation or rounding is applied in these steps. Exact ordered price/distance equality with the cleaned source was verified for all 113,775 selected rows.

In this group, all price values are consistent with a cent grid within 1e-8 cents of floating-point representation (0 off-grid values). This is observed monetary precision, not evidence of a new rounding operation or a claim about every TLC record. The global arithmetic mean P_base is not cent-aligned; nearby discrete prices therefore produce very small, nonzero relative differences. All distinct stored prices in the inclusive P_base ±$0.10 window are listed below (no rounding/coalescing before grouping).

| price | count | price_minus_P_base | delta_P | abs(delta_P) |
| --- | --- | --- | --- | --- |
| 21.25 | 12 | -0.0958695677 | -0.00449124677 | 0.00449124677 |
| 21.26 | 12 | -0.0858695677 | -0.00402277206 | 0.00402277206 |
| 21.27 | 4 | -0.0758695677 | -0.00355429735 | 0.00355429735 |
| 21.28 | 8 | -0.0658695677 | -0.00308582265 | 0.00308582265 |
| 21.29 | 7 | -0.0558695677 | -0.00261734794 | 0.00261734794 |
| 21.3 | 9 | -0.0458695677 | -0.00214887323 | 0.00214887323 |
| 21.31 | 9 | -0.0358695677 | -0.00168039852 | 0.00168039852 |
| 21.32 | 5 | -0.0258695677 | -0.00121192382 | 0.00121192382 |
| 21.33 | 7 | -0.0158695677 | -0.00074344911 | 0.00074344911 |
| 21.34 | 12 | -0.00586956774 | -0.000274974403 | 0.000274974403 |
| 21.35 | 11 | 0.00413043226 | 0.000193500305 | 0.000193500305 |
| 21.36 | 7 | 0.0141304323 | 0.000661975012 | 0.000661975012 |
| 21.37 | 3 | 0.0241304323 | 0.00113044972 | 0.00113044972 |
| 21.38 | 10 | 0.0341304323 | 0.00159892443 | 0.00159892443 |
| 21.39 | 7 | 0.0441304323 | 0.00206739913 | 0.00206739913 |
| 21.4 | 5 | 0.0541304323 | 0.00253587384 | 0.00253587384 |
| 21.41 | 8 | 0.0641304323 | 0.00300434855 | 0.00300434855 |
| 21.42 | 13 | 0.0741304323 | 0.00347282326 | 0.00347282326 |
| 21.43 | 11 | 0.0841304323 | 0.00394129796 | 0.00394129796 |
| 21.44 | 22 | 0.0941304323 | 0.00440977267 | 0.00440977267 |

### Diagnostic threshold scenarios

Same Clear × 23 group; fixed P_base=21.34586956773507, L_base=3.46907003958134, relative delta formulas and signed epsilon. Scenario A retains all observations after the existing exact-zero rule (zero such exclusions). Thresholds in B–E are diagnostic subsets only. Population SD uses ddof=0; quantiles use linear interpolation. Excluded percentages use the original N=113,775.

| scenario | minimum_abs_delta_P | retained_N | excluded_N | excluded_percentage | mean_epsilon | median_epsilon | population_SD | P95 | P99 | min | max | max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 | 113775 | 0 | 0 | 1.1229148 | 1.17888479 | 43.9864029 | 4.3244417 | 16.5556419 | -10599.5094 | 3919.35467 | 10599.5094 |
| B | 0.0001 | 113775 | 0 | 0 | 1.1229148 | 1.17888479 | 43.9864029 | 4.3244417 | 16.5556419 | -10599.5094 | 3919.35467 | 10599.5094 |
| C | 0.001 | 113738 | 37 | 0.0325203252 | 1.2566601 | 1.17888479 | 9.43103987 | 4.32140068 | 16.2797151 | -563.307024 | 465.030387 | 563.307024 |
| D | 0.005 | 113561 | 214 | 0.18809053 | 1.23014838 | 1.17888479 | 6.88729558 | 4.28531756 | 15.2212974 | -201.67333 | 215.165891 | 215.165891 |
| E | 0.01 | 112088 | 1687 | 1.48275104 | 1.29284356 | 1.18025276 | 3.63193241 | 4.07990725 | 11.702989 | -105.156016 | 104.623068 | 105.156016 |

### Contribution to original variance

Squared deviations use the FULL-group mean for every band. Their sums add to the original variance numerator, not to separate within-band variances.

| band | N | percentage | sum_squared_deviation_from_full_mean | percentage_of_total_squared_deviation |
| --- | --- | --- | --- | --- |
| 0 <= abs(delta_P) < 0.001 | 37 | 0.0325203252 | 210013879 | 95.4034886 |
| 0.001 <= abs(delta_P) < 0.005 | 177 | 0.155570204 | 4730351.8 | 2.14886781 |
| 0.005 <= abs(delta_P) < 0.01 | 1473 | 1.29466051 | 3906271.82 | 1.7745111 |
| 0.01 <= abs(delta_P) < inf | 112088 | 98.517249 | 1481781.93 | 0.673132491 |

### Observation and interpretation

The collapse is concentrated at the smallest denominators: 0.0001 excludes no rows and leaves SD unchanged; 0.001 excludes just 37 (0.032520%) and removes approximately 95.40% of the original squared-deviation mass. The scenario table reports the resulting SD and further changes at 0.005 and 0.01 without endorsing any cutoff. Mean and median remain near one but are not invariant; signed P99 also changes as the diagnostic exclusions broaden. This is consistent with epsilon=delta_L/delta_P: moderate distance deviations can produce large signed ratios when fares fall close to a non-cent-aligned global reference.

Case B is further strengthened. Neither cent-valued fares nor a large ratio establish invalid source data. No threshold is declared correct or recommended; the canonical population and all existing methodological decisions remain unchanged.

New files: `selected_group_prices_near_pbase.csv`, `denominator_threshold_sensitivity.csv`, `variance_contribution_by_delta_p_band.csv`, and the two requested charts under `charts/`. The retained-population chart overlays population SD on a separately labelled right axis to show exclusion/dispersion trade-offs; the retained-percentage axis is deliberately zoomed and labelled. Full diagnostic calculations retain their own stated populations; no canonical calculation was changed. Existing diagnostic files except this README were preserved byte-for-byte, as were canonical metadata/results.

## Cross-Group Near-Zero Denominator Validation

Diagnostic only: all 44 observed Clear/Rain groups (24 Clear, 20 Rain), using the same 3,303,107 actual observations and frozen P_base=21.34586956773507, L_base=3.46907003958134. Signed epsilon and exact-zero denominator exclusion are unchanged. The abs(delta_P)>=0.001 subsets are comparisons, not an adopted or recommended threshold. No additional 1,000-row samples were extracted.

Variance contribution is the near-zero subset's sum of squared deviations about the **full-group mean**, divided by the full group's sum. SD after exclusion uses the retained group's own mean and ddof=0. Cross-group medians below give each observed group equal weight.

- groups: 44
- groups_gt50: 34
- groups_gt75: 26
- groups_gt90: 3
- median_contribution_pct: 81.213538548
- max_contribution_pct: 95.403488597
- median_nearzero_observation_pct: 0.019123736
- max_nearzero_observation_pct: 0.062883194
- median_SD_before: 23.466830408
- median_SD_after: 10.530683119
- median_pct_SD_reduction: 56.655534707
- median_abs_median_change: 0.000000000
- max_abs_median_change: 0.000572626
- top10_gt50: 10

Top 10 groups ranked by original population SD:

| weather_name | hour | N | population_SD | count_abs_delta_P_lt_0_001 | pct_abs_delta_P_lt_0_001 | pct_total_squared_deviations_abs_delta_P_lt_0_001 | SD_after |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clear | 23 | 113775 | 43.986403 | 37 | 0.032520 | 95.403489 | 9.431040 |
| Clear | 5 | 32073 | 41.114246 | 14 | 0.043650 | 80.673389 | 18.078396 |
| Rain | 19 | 19235 | 39.574819 | 6 | 0.031193 | 92.133119 | 11.100783 |
| Clear | 3 | 23657 | 35.833769 | 9 | 0.038044 | 87.614745 | 12.611939 |
| Rain | 2 | 5155 | 35.426164 | 3 | 0.058196 | 79.191942 | 16.161531 |
| Clear | 8 | 165769 | 33.452482 | 63 | 0.038005 | 68.679217 | 18.725231 |
| Rain | 3 | 6361 | 33.121260 | 4 | 0.062883 | 86.539231 | 12.138805 |
| Clear | 1 | 57138 | 32.558658 | 21 | 0.036753 | 88.420704 | 11.078703 |
| Clear | 7 | 119329 | 30.440942 | 49 | 0.041063 | 83.529266 | 12.356699 |
| Clear | 4 | 19549 | 30.391032 | 9 | 0.046038 | 85.377242 | 11.623225 |

**Observation:** Case B generalizes beyond Clear 23:00: 34 of 44 groups attribute more than half of squared deviations to abs(delta_P)<0.001, including 10 of the top 10 original-SD groups. A median 0.019124% of observations contributes a median 81.213539% of squared deviations. The effect is widespread, though strength varies by group. Median epsilon remains comparatively stable: median absolute before/after change 0.000000000, maximum 0.000572626.

**Methodology decision:** None. This supports small-denominator amplification, not a finding that those source observations are invalid or that 0.001 is correct. Canonical methodology and results remain unchanged.

New files: `all_groups_near_zero_denominator_diagnostic.csv` and `charts/original_vs_diagnostic_sd_by_weather_hour.png`. Rain hours 5, 10, 11, 12 remain absent in the table and gaps in the graph. Validation passed: all 44 original group counts/means/SDs reproduce canonical results; retained/excluded counts reconcile; Clear 23:00 matches the prior sensitivity scenario; protected source, canonical and existing diagnostic files are byte-identical. Only this README was appended.
