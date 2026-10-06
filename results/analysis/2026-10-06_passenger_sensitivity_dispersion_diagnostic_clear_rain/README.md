# Passenger Sensitivity Dispersion Analysis — Clear and Rain

Investigation of within-group variance and near-zero relative-price denominators in the January–March 2026 passenger-sensitivity estimates.

## 1. Analysis Objective

The existing passenger-sensitivity analysis produces moderate hourly mean elasticity estimates but relatively large population standard deviations in some Weather × Hour groups. This analysis investigates the source of that dispersion: broad variation across otherwise ordinary observations, a small number of extreme ratios, near-zero relative price deviations, unusually large relative distance deviations, or invalid underlying fare/distance records. Numerical verification and distributional evidence are considered separately from decisions about the sensitivity formulation.

## 2. Scope

Clear (WeatherCode 1) and Rain (WeatherCode 8) were selected for detailed dispersion analysis over hours 0–23. There are 24 observed Clear groups and 20 observed Rain groups, giving 44 groups and 3,303,107 trip observations. Rain hours 5, 10, 11 and 12 are absent; no observations or statistics are imputed.

The broader canonical analysis also contains Snowfall; this focused dispersion study evaluates Clear and Rain.

## 3. Underlying Data

The training period is January–March 2026, from 2026-01-01 inclusive to 2026-04-01 exclusive. The final cleaned historical population contains 10,620,409 trips satisfying 0 < trip_distance ≤ 100 miles. This existing source-cleaning rule remains fixed.

Price provenance is `fare_amount` in the raw TLC yellow-taxi data → `fare` in the processed elasticity input → `price` in the paired-observation export. Units are USD. `src/elasticity_v2/population.py` performs numeric coercion and stores `fare` as float64; it does not construct a total fare, per-mile fare or model-generated price. The export preserves the original paired fare and distance values.

The earlier precision check found that all selected Clear × 23:00 prices are effectively cent-valued within normal floating-point representation. No rounding operation is introduced here. The cleaned source is `data/processed/elasticity_v2/elasticity_input_2026_01_03_cleaned.parquet`; paired observations are available in `actual_weather_hour_price_distance_arrays_2026_01_03.parquet` in the same directory.

## 4. Fixed Reference Values

The two references are arithmetic means over the complete cleaned January–March population:

\[
P_{\mathrm{base}}=21.34586956773507\ \mathrm{USD},\qquad
L_{\mathrm{base}}=3.46907003958134\ \mathrm{miles}.
\]

They remain fixed throughout the analysis. No weather-specific or hour-specific references are used. The current definition is recorded in `data/processed/elasticity_v2/final_elasticity_clean_reference_methodology.json`.

## 5. Passenger Sensitivity Formulation

For paired price and distance observations from trip \(i\), relative deviations are

\[
\Delta P_i=\frac{P_i-P_{\mathrm{base}}}{P_{\mathrm{base}}},\qquad
\Delta L_i=\frac{L_i-L_{\mathrm{base}}}{L_{\mathrm{base}}}.
\]

Passenger sensitivity is

\[
\epsilon_i=\frac{\Delta L_i}{\Delta P_i}
=\frac{(L_i-L_{\mathrm{base}})/L_{\mathrm{base}}}
{(P_i-P_{\mathrm{base}})/P_{\mathrm{base}}}.
\]

Epsilon is dimensionless and signed. Negative values are not automatically invalid. Exact-zero price deviations are excluded; there were no such exclusions in the Clear/Rain population. No other denominator threshold, clipping, winsorization, trimming or normalization is used in the canonical calculation. The subset comparisons below do not amend that calculation.

## 6. Why Extreme Epsilon Is Possible

As abs(ΔP) approaches zero, a moderate nonzero ΔL can generate a very large ratio. An observed Clear × 23:00 trip illustrates this mechanism:

| Quantity | Observed value |
| --- | ---: |
| Price | $21.34 |
| Distance | 13.58 miles |
| ΔP | -0.000274974403 |
| ΔL | 2.914593780193 |
| Epsilon | -10,599.509450 |

The fare and distance have not, by themselves, been established as invalid. A substantial relative-distance numerator is divided by a relative-price deviation very close to zero. P_base lies between ordinary cent-valued fares such as $21.34 and $21.35, making near-zero relative-price deviations structurally possible. The exact stored prices and their frequencies within P_base ±$0.10 appear in `selected_group_prices_near_pbase.csv`.

## 7. Population Standard Deviation Verification

All 44 observed groups were independently evaluated using population variance and standard deviation:

\[
\bar\epsilon=\frac{1}{N}\sum_{i=1}^{N}\epsilon_i,\qquad
\sigma=\sqrt{\frac{1}{N}\sum_{i=1}^{N}(\epsilon_i-\bar\epsilon)^2}.
\]

The implementation check uses `numpy.std(epsilon, ddof=0)`. Counts, means, variances and SDs agree with the canonical table within floating-point tolerances (`rtol=1e-11`, `atol=1e-12`). Verification passes for all 44 groups. The large SDs are therefore reproduced by the population-SD calculation; the checks provide no evidence of an implementation error in variance or SD. This does not independently establish the validity of every source observation.

## 8. Weather × Hour SD Ranking

All 44 groups were ranked by population SD, highest first. Clear × 23:00 was identified automatically as the largest-SD group, with N=113,775.

| Mean | Median | Population SD | P95 | P99 | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- | --- |
| 1.122915 | 1.178885 | 43.986403 | 4.324442 | 16.555642 | -10599.509450 | 3919.354668 |

Mean and median are approximately 1.1–1.2, whereas SD is approximately 44. This contrast motivates an examination of tail influence rather than interpreting SD as a description of a typical observation.

The ten highest-SD groups are:

| rank | weather_name | hour | n | recomputed_sd |
| --- | --- | --- | --- | --- |
| 1 | Clear | 23 | 113775 | 43.986403 |
| 2 | Clear | 5 | 32073 | 41.114246 |
| 3 | Rain | 19 | 19235 | 39.574819 |
| 4 | Clear | 3 | 23657 | 35.833769 |
| 5 | Rain | 2 | 5155 | 35.426164 |
| 6 | Clear | 8 | 165769 | 33.452482 |
| 7 | Rain | 3 | 6361 | 33.121260 |
| 8 | Clear | 1 | 57138 | 32.558658 |
| 9 | Clear | 7 | 119329 | 30.440942 |
| 10 | Clear | 4 | 19549 | 30.391032 |

## 9. Distribution Interpretation

The selected distribution has mean 1.122915, median 1.178885, P95 4.324442 and P99 16.555642, but extends from -10,599.509450 to 3,919.354668. Its empirical tails are extremely long relative to the central distribution. The population variance is 1934.803641.

SD is highly sensitive to tail observations because deviations from the mean are squared. An SD of 43.99 does not mean that typical passengers have sensitivity around ±44, nor does it establish a Normal distribution. The P01–P99 figure displays the central distribution without allowing the most extreme values to compress its scale; full-group calculations retain all observations.

## 10. 1,000-Observation Inspection

`selected_group_first_1000_price_distance_epsilon.csv` contains exactly the first 1,000 paired observations from Clear × 23:00 in stable source order. Each row preserves price, distance, ΔP, ΔL and epsilon from the same historical trip, enabling direct manual tracing of the calculation.

`source_row_index` is the original zero-based Parquet row position, not a separate asserted trip identifier. The export is neither random nor a statistical subsample used for the group estimates: all original group statistics use the full 113,775 observations.

## 11. Extreme-Observation Analysis

`selected_group_top_100_abs_epsilon.csv` ranks observations from the full selected group by descending absolute epsilon. Only 37 observations fall in 0.0001 ≤ abs(ΔP) < 0.001, representing 0.032520% of the group, yet contributing 95.4035% of total squared deviations about the full-group mean. The top 20 absolute-epsilon observations contribute 93.97%.

A tiny fraction of observations therefore dominates the population variance. All top-20 prices are between $21.33 and $21.36. The largest ratio combines a small denominator with a substantial relative-distance deviation; the other top-20 absolute relative-distance deviations are below one. Large ratios alone do not establish invalid source records.

## 12. Denominator-Band Analysis

| band | N | percentage |
| --- | --- | --- |
| <0.00001 | 0 | 0.000000 |
| 0.00001–0.0001 | 0 | 0.000000 |
| 0.0001–0.001 | 37 | 0.032520 |
| 0.001–0.01 | 1650 | 1.450231 |
| >=0.01 | 112088 | 98.517249 |

The smallest non-empty denominator band has disproportionate influence on variance. Empty bands have undefined distribution statistics, represented by blank CSV cells rather than zero quantiles.

## 13. Diagnostic Threshold Sensitivity

These are analytical sensitivity scenarios. No denominator threshold has been adopted or recommended. Each scenario applies only to the selected group's comparative calculation.

| Minimum abs(ΔP) retained | Excluded N (%) | Mean | Median | SD | P99 |
| --- | --- | --- | --- | --- | --- |
| 0.000000 | 0 (0.000000%) | 1.122915 | 1.178885 | 43.986403 | 16.555642 |
| 0.000100 | 0 (0.000000%) | 1.122915 | 1.178885 | 43.986403 | 16.555642 |
| 0.001000 | 37 (0.032520%) | 1.256660 | 1.178885 | 9.431040 | 16.279715 |
| 0.005000 | 214 (0.188091%) | 1.230148 | 1.178885 | 6.887296 | 15.221297 |
| 0.010000 | 1,687 (1.482751%) | 1.292844 | 1.180253 | 3.631932 | 11.702989 |

SD is unchanged at 0.0001 because no observations occupy the smaller-denominator region. Excluding the first populated near-zero band removes only 37 observations and reduces SD from 43.99 to 9.43. Median remains unchanged at this comparison; mean changes more because it is tail-sensitive. P99 initially changes relatively little, from 16.56 to 16.28, but falls further under broader exclusions. These numerical responses do not establish an optimal or theoretically justified cutoff.

## 14. Variance Contribution by ΔP Band

| band | N | percentage_of_total_squared_deviation |
| --- | --- | --- |
| 0 <= abs(delta_P) < 0.001 | 37 | 95.403489 |
| 0.001 <= abs(delta_P) < 0.005 | 177 | 2.148868 |
| 0.005 <= abs(delta_P) < 0.01 | 1473 | 1.774511 |
| 0.01 <= abs(delta_P) < inf | 112088 | 0.673132 |

Every contribution uses deviations about the full-group mean:

\[
C_B=100\frac{\sum_{i\in B}(\epsilon_i-\bar\epsilon_{\mathrm{full}})^2}
{\sum_i(\epsilon_i-\bar\epsilon_{\mathrm{full}})^2}.
\]

The percentages sum to 100%. They partition the original variance numerator; they are not separately centered within-band variances. The smallest-denominator region accounts for the vast majority of squared deviation.

## 15. Cross-Group Validation

The Clear × 23:00 result was not assumed to generalize. The same comparison was evaluated independently for every observed Clear/Rain group, retaining abs(ΔP) ≥ 0.001 for the comparative statistics.

| Metric | Result |
| --- | --- |
| Groups with contribution >50% | 34 / 44 |
| Groups with contribution >75% | 26 / 44 |
| Groups with contribution >90% | 3 / 44 |
| Median near-zero observation percentage | 0.019124% |
| Maximum near-zero observation percentage | 0.062883% |
| Median variance contribution | 81.213539% |
| Maximum variance contribution | 95.403489% |
| Median original SD | 23.466830 |
| Median comparative SD | 10.530683 |
| Median percentage SD reduction | 56.655535% |

Cross-group medians weight each of the 44 groups equally. Median percentage SD reduction is the median of group-specific percentage reductions, not a percentage calculated from the two median SDs. Near-zero observations account for more than half of the variance in all ten highest-SD groups. The strength of the effect varies across the remaining groups; it is widespread, not universal.

## 16. Median Stability

The median absolute change in hourly median epsilon is 0; the maximum absolute change is 0.000573. Central location remains highly stable even when SD changes substantially. This supports the interpretation that extreme tails, rather than broad movement of the typical observation, dominate the original variance in the affected groups.

## 17. Negative Epsilon

Clear × 23:00 contains 14,989 negative observations (13.174247%) and 98,786 positive observations (86.825753%); there are no zero epsilon observations. Negative epsilon arises when the two relative deviations have opposite signs: 9,512 observations have ΔP > 0 and ΔL < 0, and 5,477 have ΔP < 0 and ΔL > 0.

Negative observations were retained and were not automatically treated as invalid. The sign follows from the relative-deviation ratio and does not alone establish a causal demand response.

## 18. Main Finding

The analysis indicates that the unusually large population standard deviations are primarily driven by near-zero relative price deviations rather than uniformly broad passenger-sensitivity distributions. Across Clear and Rain hourly groups, observations with abs(ΔP) < 0.001 represent a very small fraction of the data but account for a disproportionately large share of total squared deviations.

The effect is present across all ten highest-dispersion groups and is not limited to one weather/hour condition. The underlying fare and distance observations responsible for the largest ratios have not been established as invalid source records.

## 19. What Has Been Established

1. Population SD is calculated consistently with the canonical definition.
2. The extreme SD is reproducible from underlying observations.
3. Extreme epsilon values can be traced to paired historical fare/distance rows.
4. Near-zero ΔP dominates variance in most high-SD Clear/Rain groups, including all ten highest-SD groups.
5. A very small proportion of observations produces a large share of variance.
6. Median sensitivity remains highly stable under the comparative exclusion.
7. Invalid source records have not been established as the primary cause.

## 20. What Has Not Been Decided

The evidence does not establish that extreme epsilon values should be deleted, that observations with abs(ΔP) < 0.001 should be removed, or that 0.001 is an optimal or theoretically justified threshold. It also does not establish that the elasticity formula, P_base or L_base should change, or that empirical observations should be replaced by synthetic sensitivity data. These remain modelling and methodological decisions.

## 21. Methodological Implication

The evidence identifies a ratio-instability effect as relative price deviation approaches zero. The ensuing methodological question is how passenger sensitivity should be defined or handled when an observed price is extremely close to the reference price. Potential approaches require methodological agreement before evaluation or adoption. This report does not recommend one approach or alter the canonical method.

## 22. Figures

- [sd_vs_hour_clear_rain.png](charts/sd_vs_hour_clear_rain.png): Original population SD across hours for Clear and Rain, with the highest-SD group annotated. Missing Rain hours remain gaps.

- [selected_group_epsilon_histogram_full.png](charts/selected_group_epsilon_histogram_full.png): Full Clear × 23:00 epsilon distribution in 15 equal-width bins, including both extreme tails.

- [selected_group_epsilon_histogram_p01_p99.png](charts/selected_group_epsilon_histogram_p01_p99.png): Central P01–P99 visualization with 15 bins. Restriction is for display only; no full-group calculation excludes these tails.

- [sd_vs_denominator_threshold_clear_hour23.png](charts/sd_vs_denominator_threshold_clear_hour23.png): Population-SD response across the five denominator sensitivity scenarios.

- [retained_population_vs_denominator_threshold.png](charts/retained_population_vs_denominator_threshold.png): Retained population percentage and excluded-percentage annotations, with population SD on a separate right axis. The retained-percentage axis is zoomed.

- [original_vs_diagnostic_sd_by_weather_hour.png](charts/original_vs_diagnostic_sd_by_weather_hour.png): Original versus comparative SD after retaining abs(ΔP) ≥ 0.001, in separate Clear and Rain panels, with missing hours unfilled.

## 23. Data Files

- [weather_hour_sd_verification.csv](weather_hour_sd_verification.csv): Canonical and independently recomputed group counts, means, population SDs and variances; absolute SD differences and verification flags.

- [weather_hour_sd_ranking.csv](weather_hour_sd_ranking.csv): All 44 groups ranked by original population SD.

- [selected_group_distribution_summary.json](selected_group_distribution_summary.json): Full selected-group distribution, quantiles, sign counts and tail contribution measures.

- [selected_group_epsilon_bins.csv](selected_group_epsilon_bins.csv): Fifteen full-range histogram intervals, counts and percentages. Bins include their left edge; only the last also includes its right edge.

- [selected_group_first_1000_price_distance_epsilon.csv](selected_group_first_1000_price_distance_epsilon.csv): Exactly 1,000 paired source-order observations for manual tracing, with deltas and signed epsilon.

- [selected_group_top_100_abs_epsilon.csv](selected_group_top_100_abs_epsilon.csv): Top 100 full-group observations by absolute epsilon, with ranks and source positions.

- [selected_group_delta_p_bands.csv](selected_group_delta_p_bands.csv): Five absolute-denominator bands, counts, shares and absolute-epsilon distribution summaries.

- [selected_group_prices_near_pbase.csv](selected_group_prices_near_pbase.csv): All distinct observed selected-group prices within P_base ±$0.10, with frequencies and price deviations.

- [denominator_threshold_sensitivity.csv](denominator_threshold_sensitivity.csv): Five selected-group scenarios, retained/excluded counts, mean, median, population SD, P95, P99 and extrema.

- [variance_contribution_by_delta_p_band.csv](variance_contribution_by_delta_p_band.csv): Four denominator bands partitioning squared deviations about the full-group mean.

- [all_groups_near_zero_denominator_diagnostic.csv](all_groups_near_zero_denominator_diagnostic.csv): All 44 original and comparative group statistics, near-zero counts, variance contributions and percentage SD reductions.

- [summary.json](summary.json): Initial Clear/Rain analysis metadata, selected-group statistics, top-10 ranking, top-20 inspection and interpretation. Later denominator and cross-group extensions are recorded in their dedicated CSVs; this JSON is not a consolidated summary of those extensions.

The canonical comparison is `data/processed/elasticity_v2/elasticity_actual_weather_clean_reference_final.csv`. This report preserves the existing numerical artifacts; display rounding does not modify stored values.

## 24. Conclusion

The largest population standard deviations are not explained primarily by a generally broad central distribution. They are dominated by a very small number of observations whose relative price deviations from P_base are close to zero. Because epsilon is defined as ΔL/ΔP, these observations generate large-magnitude ratios and disproportionately influence variance.

The effect is reproducible across Clear and Rain hourly groups, including all ten highest-SD groups. The analysis therefore explains the observed dispersion mathematically and empirically while leaving the underlying methodology unchanged. Treatment of the near-zero denominator region remains a separate methodological decision.
