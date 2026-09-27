# M9/M10 passenger sensitivity: professor review

**Status: READY_FOR_PROFESSOR_REVIEW, not frozen and not production-integrated.**

## 1. Authoritative document and findings

Source: [Final_Module_Wise_Algorithm_Input_Output_Document.pdf](../../../notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf). All 24 pages were text-inspected; M9/M10/M12 equations were also visually checked. Key sections: overall flow p.1; master table pp.2-4; M3 p.7; M9 p.13; M10 p.14; M11/privacy p.15; M12 p.16; exact slot algorithm and coding order p.23; integration checklist p.24. The document puts M9/M10 before pricing/integration. Future DQN and routing changes are outside this task.

M3 fixes **operational** slots at 30 minutes, but M9 says Time-of-Day groups without defining their width. Neither weather regrouping, a numeric outlier rule, a sampling family, nor sparse-condition fallback is specified. Thus 30-minute Period and Hour are compared, not selected. Population SD (`ddof=0`) follows the explicit task. “Document and apply the chosen outlier rule” remains pending; untrimmed results are the audit reference, not a frozen choice of no trimming.

## 2. Exact M9/M10 definitions and units

For condition c, **L_base,c = mean(L_i)** and **P_base,c = mean(P_i)** over positive finite historical distance/fare rows with a valid condition. Each trip has raw deviations `delta_L = L_i - L_base,c` and `delta_P = P_i - P_base,c`. Then:

```text
relative_delta_L = delta_L / L_base,c
epsilon_i = relative_delta_L / delta_P
retain iff delta_L > 0 and delta_P > 0 and epsilon finite and epsilon > 0
```

L_i is source TLC trip distance in miles, P_i is `fare_amount` in USD, and c identifies time bucket plus WeatherCode. The ratio of distances is dimensionless; **epsilon has units 1/USD**, unlike the old dimensionless ratio. Changing distance units consistently for L_i and its base cancels; changing fare currency rescales epsilon. No absolute value is used. Means are computed BEFORE the positive-deviation filters, not from only above-base trips.

Current production remains legacy: absolute relative-price/relative-distance ratio, previous input/deviation rules, positive-truncated Normal and exact→Period→Weather→Global fallback, with an extra P_base factor in its willingness-to-pay adjustment. [Full 15-row difference table](current_vs_new_m10.csv). Old code and artifacts were not overwritten.

## 3. Historical data, source validity and weather join

Use existing `data/processed/cleaned_trips.parquet`. Frozen pickup window: **2026-01-01 00:00 inclusive to 2026-01-25 18:30 exclusive**. Future trip rows and weather timestamps are removed before fitting or diagnostics. Invalid/unparseable pickup timestamps cannot enter that window. No hold-out values determine bases, percentiles, fit parameters, outlier diagnostics or acceptance scenarios.

Weather uses the existing processed NYC point-derived Meteostat hourly WeatherCode joined by pickup timestamp floored to the hour. Timestamps retain the project's documented naive-time assumption; no new timezone conversion, interpolation, or WeatherCode merging is introduced. The source weather file already contains legacy forward/backward fill; this analysis does not claim a new causal weather-feed validation. Condition IDs are unambiguous strings `30min:Txx:Wcode` or `hourly:Txx:Wcode`; “Time × Weather” is a Cartesian pairing, not numerical multiplication.

Input eligibility is finite strictly positive distance and fare. **The old sensitivity-specific 100-mile cap and .01-mile absolute distance-deviation threshold are not carried into new M10.** They are absent from the new M9/M10 formula and requested funnel. The old cap excludes 93 otherwise positive-finite historical rows; the summary separately records extreme source counts for review. No new “impossible trip” threshold is invented. This is a documented analysis input policy requiring source-quality interpretation before freezing, not an assertion that all positive historical outliers are plausible. A future approved input cleaning change would require recomputing both bases and epsilon.

`trip_id` is retained if present; otherwise stable zero-based source-row position is used, tied to the input hash. Full row-level diagnostic parquet files, including invalid rows and `valid_m10` flags, are local/ignored under `data/processed/passenger_sensitivity_m10_review/`. They contain PRIVATE epsilon and are never passed to a pricing or routing model.


Historical input audit:

| source_rows | invalid_pickup_timestamps | historical_rows | outside_history | historical_positive_finite | historical_positive_finite_above_100_miles | historical_max_positive_distance_miles |
| --- | --- | --- | --- | --- | --- | --- |
| 3699638 | 0 | 2931451 | 768187 | 2812329 | 93 | 236217 |

## 4. Exact filter funnels

Percent_previous is conditional on the previous stage; percent_raw always divides by historical rows. The final row repeats the positive-finite stage to identify the output population. No trims are applied. Missing condition/base exclusions are separate from invalid fare/distance.


### 30min

| stage | count | percent_previous | percent_raw |
| --- | --- | --- | --- |
| raw_historical_rows | 2931451 | 100 | 100 |
| valid_positive_distance_fare | 2812329 | 95.9364 | 95.9364 |
| valid_condition_bases | 2812329 | 100 | 95.9364 |
| delta_L_positive | 558137 | 19.8461 | 19.0396 |
| delta_P_positive | 526892 | 94.4019 | 17.9738 |
| finite_epsilon | 526892 | 100 | 17.9738 |
| positive_epsilon | 526892 | 100 | 17.9738 |
| final_valid_m10 | 526892 | 100 | 17.9738 |

### hourly

| stage | count | percent_previous | percent_raw |
| --- | --- | --- | --- |
| raw_historical_rows | 2931451 | 100 | 100 |
| valid_positive_distance_fare | 2812329 | 95.9364 | 95.9364 |
| valid_condition_bases | 2812329 | 100 | 95.9364 |
| delta_L_positive | 510224 | 18.1424 | 17.4052 |
| delta_P_positive | 487710 | 95.5874 | 16.6372 |
| finite_epsilon | 487710 | 100 | 16.6372 |
| positive_epsilon | 487710 | 100 | 16.6372 |
| final_valid_m10 | 487710 | 100 | 16.6372 |

## 5. Time grouping support

Possible conditions = 48 or 24 buckets × distinct codes present in **historical weather only**. It is not a claim of all possible meteorological codes. Observed conditions have N>0; missing means no support in that Cartesian product. N quantiles are over observed conditions; both observed-only and all-possible sparse counts are in the CSV. Base N and retained-epsilon N are separate populations. Sparse flags N<30, <100 and <500 are descriptive, overlapping thresholds, not pooling decisions.

| variant | population | possible_conditions | observed_conditions | missing_conditions | observed_n_min | observed_n_p25 | observed_n_median | observed_n_p75 | observed_n_max | observed_groups_n_lt_30 | observed_groups_n_lt_100 | observed_groups_n_lt_500 | observed_groups_n_ge_500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30min | base | 624 | 243 | 381 | 158 | 2682.5 | 4559 | 16189.5 | 58619 | 0 | 0 | 14 | 229 |
| 30min | epsilon | 624 | 238 | 386 | 1 | 612.5 | 1039.5 | 2447.5 | 14578 | 4 | 16 | 54 | 184 |
| hourly | base | 312 | 122 | 190 | 328 | 5405.5 | 8909.5 | 32762.2 | 115425 | 0 | 0 | 3 | 119 |
| hourly | epsilon | 312 | 117 | 195 | 30 | 1269 | 2013 | 5051 | 28113 | 0 | 3 | 14 | 103 |

## 6. Raw epsilon distribution

| variant | transform | count | mean | std_population | min | p01 | p05 | p10 | p25 | median | p75 | p90 | p95 | p99 | p995 | p999 | max | skewness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30min | raw | 526892 | 0.380185 | 67.0908 | 2.04331e-07 | 0.00112177 | 0.00590044 | 0.0113818 | 0.0313489 | 0.0669869 | 0.0922013 | 0.128649 | 0.179184 | 0.576244 | 1.09156 | 6.47844 | 36880.7 | 432.045 |
| 30min | log1p | 526892 | 0.0774809 | 0.147427 | 2.04331e-07 | 0.00112114 | 0.0058831 | 0.0113176 | 0.0308675 | 0.0648387 | 0.0881952 | 0.121021 | 0.164823 | 0.455045 | 0.737912 | 2.01202 | 10.5155 | 21.4618 |
| hourly | raw | 487710 | 0.588876 | 154.575 | 3.72208e-07 | 0.000969262 | 0.00456223 | 0.00910838 | 0.0224052 | 0.0537005 | 0.0847999 | 0.116764 | 0.158403 | 0.493789 | 0.923522 | 4.26416 | 97164 | 541.713 |
| hourly | log1p | 487710 | 0.0671306 | 0.138945 | 3.72207e-07 | 0.000968793 | 0.00455185 | 0.00906715 | 0.0221579 | 0.0523082 | 0.0813956 | 0.110435 | 0.147042 | 0.401316 | 0.654158 | 1.66092 | 11.4842 | 25.6094 |

Percentiles use NumPy linear interpolation; std is population ddof=0; skewness is SciPy bias-corrected sample skewness. `log1p(epsilon)` is visualization only: no values are transformed for M10/M12 or any frozen sampling configuration. Overall summaries are row-weighted, not averages of condition means.

## 7. Small positive delta_P

| variant | bin | count | mean | median | p90 | p95 | p99 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30min | 0 <= delta_P < 0.01 (positive) | 161 | 215.347 | 30.1527 | 113.628 | 147.489 | 784.966 | 24929.9 |
| 30min | 0.01 <= delta_P < 0.05 (positive) | 444 | 10.1411 | 6.63754 | 23.9151 | 30.1684 | 62.1432 | 83.7668 |
| 30min | 0.05 <= delta_P < 0.1 (positive) | 631 | 3.27344 | 1.7465 | 6.76653 | 9.21618 | 15.3761 | 108.042 |
| 30min | 0.1 <= delta_P < 0.25 (positive) | 1527 | 25.5701 | 0.883616 | 3.25224 | 4.34281 | 7.00058 | 36880.7 |
| 30min | 0.25 <= delta_P < 0.5 (positive) | 3223 | 0.684429 | 0.410861 | 1.50347 | 2.11579 | 3.45958 | 82.0987 |
| 30min | 0.5 <= delta_P < inf (positive) | 520906 | 0.226194 | 0.0664108 | 0.124393 | 0.16424 | 0.363805 | 10778.3 |
| hourly | 0 <= delta_P < 0.01 (positive) | 94 | 67.0471 | 48.5332 | 137.751 | 189.47 | 516.169 | 605.678 |
| hourly | 0.01 <= delta_P < 0.05 (positive) | 219 | 18.3477 | 7.64861 | 35.4488 | 53.3216 | 95.0918 | 971.293 |
| hourly | 0.05 <= delta_P < 0.1 (positive) | 1011 | 2.50429 | 1.38406 | 4.57097 | 6.71348 | 11.1158 | 365.508 |
| hourly | 0.1 <= delta_P < 0.25 (positive) | 1171 | 113.888 | 0.846787 | 3.30214 | 4.3886 | 7.43933 | 97164 |
| hourly | 0.25 <= delta_P < 0.5 (positive) | 2338 | 0.618367 | 0.400547 | 1.37689 | 1.91802 | 2.84919 | 29.0343 |
| hourly | 0.5 <= delta_P < inf (positive) | 482877 | 0.288974 | 0.0530871 | 0.113387 | 0.147148 | 0.318967 | 22843.7 |

Bins are disjoint and exhaustive. The formula mechanically amplifies relative-distance deviations when price deviations approach zero. Large epsilon at small delta_P is therefore a denominator effect, not independent evidence of a passenger behavioral law. Values below one cent are deviations from a group mean: source cent-denominated fares do not imply delta_P is cent-quantized. No minimum delta_P, epsilon cap or winsorization has been added.

**Observed stability finding:** the very smallest positive delta_P bin is unstable, but it does not contain the overall maximum in either grouping. Both maxima lie in the [.10,.25) USD bin. Source-distance extremes also drive the tail: the historical input includes a maximum positive distance of 236,216.69 miles. Treat such source values as data-quality issues for review, not plausible NYC trip lengths. A denominator floor alone would not address them.

30min: 54 retained rows above the legacy 100-mile reference contribute 58.05% of the sum of epsilon. This is an attribution diagnostic, not an applied exclusion; removing input rows would also change condition bases.

hourly: 56 retained rows above the legacy 100-mile reference contribute 84.11% of the sum of epsilon. This is an attribution diagnostic, not an applied exclusion; removing input rows would also change condition bases.

## 8. Time × Weather findings

| variant | WeatherCode | count | mean | median | p99 | max |
| --- | --- | --- | --- | --- | --- | --- |
| 30min | 1 | 135009 | 0.328798 | 0.0671152 | 0.533831 | 10778.3 |
| 30min | 2 | 40689 | 0.133488 | 0.0768043 | 0.588315 | 283.379 |
| 30min | 3 | 276424 | 0.414647 | 0.0613634 | 0.5274 | 36880.7 |
| 30min | 5 | 16496 | 0.143618 | 0.0774699 | 0.489203 | 461.23 |
| 30min | 7 | 3037 | 0.0902613 | 0.0767188 | 0.406186 | 4.29089 |
| 30min | 8 | 6051 | 0.134711 | 0.0802863 | 1.14498 | 23.9243 |
| 30min | 9 | 14081 | 0.130735 | 0.0837891 | 1.05719 | 55.3886 |
| 30min | 12 | 16436 | 0.128543 | 0.076689 | 0.745775 | 116.791 |
| 30min | 13 | 2045 | 0.119498 | 0.0857558 | 0.900005 | 6.88382 |
| 30min | 14 | 6079 | 4.25435 | 0.0795293 | 0.914933 | 24929.9 |
| 30min | 15 | 9184 | 0.220891 | 0.0875228 | 1.27674 | 464.597 |
| 30min | 16 | 761 | 0.361495 | 0.0560085 | 2.84434 | 112.943 |
| 30min | 21 | 600 | 0.0894944 | 0.0786495 | 0.472995 | 1.19237 |
| hourly | 1 | 127078 | 0.403054 | 0.058303 | 0.48347 | 22843.7 |
| hourly | 2 | 35902 | 0.172244 | 0.0716497 | 0.581041 | 509.432 |
| hourly | 3 | 254000 | 0.860267 | 0.0430239 | 0.402328 | 97164 |
| hourly | 5 | 15365 | 0.157606 | 0.0774488 | 0.448056 | 665.771 |
| hourly | 7 | 3028 | 0.0909437 | 0.0767749 | 0.482916 | 4.78767 |
| hourly | 8 | 6018 | 0.130515 | 0.0808143 | 0.760591 | 48.1578 |
| hourly | 9 | 14085 | 0.134882 | 0.0839004 | 0.888274 | 55.5096 |
| hourly | 12 | 16129 | 0.167415 | 0.0743501 | 0.703158 | 605.678 |
| hourly | 13 | 2047 | 0.173121 | 0.087295 | 1.14672 | 50.31 |
| hourly | 14 | 5827 | 0.128433 | 0.0698017 | 1.54333 | 12.7059 |
| hourly | 15 | 7491 | 0.269294 | 0.0735186 | 0.777129 | 768.983 |
| hourly | 16 | 740 | 0.117694 | 0.0565059 | 1.37268 | 5.09528 |
| hourly | 21 | 0 | nan | nan | nan | nan |

These are descriptive associations with historical fare-distance deviations, not causal weather or price-demand elasticity estimates. Hourly groups recompute both means and epsilon from their own members; they do not average half-hour epsilon statistics. Changing grouping can change retention, denominator closeness and tail magnitude, not merely reduce noise. The support heatmap retains missing cells; codes are never merged. Hourly WeatherCode 21 has zero retained M10 observations despite historical weather/base support; it is explicitly shown as N=0 rather than silently dropped.


Largest condition means (30min; inspect N before interpretation):

| condition_id | base_sample_count | sample_count | mean_epsilon | std_epsilon | median | p99 | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 30min:T07:W3 | 10515 | 105 | 351.247 | 3582.01 | 0.00205196 | 0.016483 | 36880.7 |
| 30min:T15:W1 | 16379 | 7 | 160.728 | 201.076 | 0.00704976 | 485.569 | 489.548 |
| 30min:T17:W5 | 3154 | 2 | 80.3857 | 80.3461 | 80.3857 | 159.125 | 160.732 |
| 30min:T19:W14 | 2702 | 754 | 33.1668 | 907.288 | 0.0879242 | 0.607343 | 24929.9 |
| 30min:T14:W3 | 21719 | 245 | 22.166 | 248.465 | 0.00146094 | 0.0883324 | 3216.76 |

Largest condition means (hourly; inspect N before interpretation):

| condition_id | base_sample_count | sample_count | mean_epsilon | std_epsilon | median | p99 | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hourly:T03:W3 | 22541 | 1390 | 69.9132 | 2605.2 | 0.0101411 | 0.0364679 | 97164 |
| hourly:T07:W1 | 28288 | 88 | 21.8643 | 111.979 | 0.00202899 | 669.075 | 760.412 |
| hourly:T10:W3 | 65984 | 1889 | 21.456 | 801.858 | 0.00326933 | 0.0300046 | 34605.4 |
| hourly:T08:W5 | 6066 | 30 | 9.52925 | 51.1739 | 0.00352925 | 202.603 | 285.108 |
| hourly:T22:W1 | 27173 | 3706 | 6.18745 | 375.194 | 0.0205758 | 0.0634693 | 22843.7 |

## 9. Outlier-rule comparison - PROFESSOR DECISION REQUIRED

| variant | rule | upper_inclusive | count | percent_retained | mean | std_population | median | p90 | p95 | p99 | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30min | none | inf | 526892 | 100 | 0.380185 | 67.0908 | 0.0669869 | 0.128649 | 0.179184 | 0.576244 | 36880.7 |
| 30min | upper_P99 | 0.576244 | 521623 | 99 | 0.0713367 | 0.0603737 | 0.0664008 | 0.124303 | 0.163457 | 0.330639 | 0.57624 |
| 30min | upper_P99.5 | 1.09156 | 524257 | 99.4999 | 0.074814 | 0.078242 | 0.0666977 | 0.126396 | 0.170783 | 0.411518 | 1.09128 |
| 30min | upper_P99.9 | 6.47844 | 526366 | 99.9002 | 0.083791 | 0.180139 | 0.0669271 | 0.12821 | 0.177536 | 0.533931 | 6.47844 |
| 30min | IQR_Q3_plus_1.5IQR | 0.18348 | 501627 | 95.2049 | 0.0628186 | 0.0390171 | 0.064072 | 0.111935 | 0.131087 | 0.166582 | 0.183473 |
| 30min | log1p_IQR_diagnostic | 0.190278 | 503246 | 95.5122 | 0.0632174 | 0.0395819 | 0.0642641 | 0.112747 | 0.132745 | 0.171291 | 0.190271 |
| hourly | none | inf | 487710 | 100 | 0.588876 | 154.575 | 0.0537005 | 0.116764 | 0.158403 | 0.493789 | 97164 |
| hourly | upper_P99 | 0.493789 | 482832 | 98.9998 | 0.0610905 | 0.0539041 | 0.0530223 | 0.11293 | 0.14548 | 0.28117 | 0.493756 |
| hourly | upper_P99.5 | 0.923522 | 485271 | 99.4999 | 0.0640928 | 0.0689082 | 0.053375 | 0.114805 | 0.151381 | 0.354952 | 0.923427 |
| hourly | upper_P99.9 | 4.26416 | 487222 | 99.8999 | 0.0710626 | 0.139823 | 0.0536374 | 0.116323 | 0.15706 | 0.454572 | 4.26379 |
| hourly | IQR_Q3_plus_1.5IQR | 0.178392 | 468338 | 96.028 | 0.0547282 | 0.0380388 | 0.0509826 | 0.104115 | 0.122888 | 0.15937 | 0.178386 |
| hourly | log1p_IQR_diagnostic | 0.185604 | 469583 | 96.2832 | 0.0550654 | 0.0385471 | 0.0511578 | 0.104756 | 0.124325 | 0.163705 | 0.185603 |

Every candidate starts from the same valid raw epsilon population. Upper trimming retains epsilon <= its pooled percentile. IQR = P75−P25; its upper fence is P75+1.5 IQR. The optional log-space diagnostic applies that fence to log1p(epsilon) and maps the bound back with expm1. Rules are global pooled **diagnostic comparisons**, not selected condition-specific production rules. Bases are held fixed during these epsilon-trimming comparisons; source-row cleaning would be a separate decision. No winner is selected and no runtime config is written.

## 10. Candidate distributions - PROFESSOR DECISION REQUIRED

| variant | candidate | mean | std_population | median | p90 | p95 | p99 | probability_nonpositive | descriptive_cdf_max_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 30min | empirical | 0.380185 | 67.0908 | 0.0669869 | 0.128649 | 0.179184 | 0.576244 | 0 | 0 |
| 30min | Normal | 0.380185 | 67.0908 | 0.380185 | 86.3605 | 110.735 | 156.457 | 0.497739 | 0.497739 |
| 30min | positive_truncated_Normal | 53.6691 | 40.5118 | 45.3939 | 110.588 | 131.746 | 173.09 | 0 | 0.983886 |
| 30min | lognormal | 0.0955581 | 0.157179 | 0.049641 | 0.215191 | 0.326137 | 0.711428 | 0 | 0.131712 |
| hourly | empirical | 0.588876 | 154.575 | 0.0537005 | 0.116764 | 0.158403 | 0.493789 | 0 | 0 |
| hourly | Normal | 0.588876 | 154.575 | 0.588876 | 198.685 | 254.842 | 360.184 | 0.49848 | 0.49848 |
| hourly | positive_truncated_Normal | 123.547 | 93.286 | 104.479 | 254.615 | 303.35 | 398.586 | 0 | 0.990299 |
| hourly | lognormal | 0.0824052 | 0.145292 | 0.040654 | 0.186518 | 0.287263 | 0.645819 | 0 | 0.098082 |

Empirical sampling describes the observed valid values with equal row probability. The Normal diagnostic uses empirical mean/population SD and can allocate invalid nonpositive probability. Positive-truncated Normal uses those same **underlying Normal parameters** and truncates at zero; its realized mean/SD differ and may be severely inflated by a heavy empirical tail. Lognormal uses the mean and population SD of log(epsilon), location fixed at zero, and ensures positive support. These pooled families are visual/descriptive candidates, not condition-level frozen sampling distributions.

The CDF gap is the maximum distance between candidate CDF and both sides of the exact empirical CDF steps. Parameters are estimated on the same descriptive sample; this is not a formal calibrated goodness-of-fit test or cross-validated ranking. No p-values, new dependencies or selected family are introduced. Inspect quantiles, central mass, tails and conditional variation together.

30min: untruncated Normal assigns 49.77% nonpositive mass. Truncation using those tail-inflated parameters moves the mean to 53.67, versus empirical median 0.066987. Lognormal has a smaller descriptive CDF gap (0.1317) in this pooled comparison but does not reproduce the extreme tail or resolve conditional/source-quality problems. This observation does not select a family.

hourly: untruncated Normal assigns 49.85% nonpositive mass. Truncation using those tail-inflated parameters moves the mean to 123.5, versus empirical median 0.0537. Lognormal has a smaller descriptive CDF gap (0.09808) in this pooled comparison but does not reproduce the extreme tail or resolve conditional/source-quality problems. This observation does not select a family.

## 11. M12 acceptance sanity - ILLUSTRATIVE, NOT PRODUCTION INTEGRATION

PDF p.16 states `P_max = P_base + relative_distance / epsilon` and accepts when `factor * P_base <= P_max`. The extra P_base multiplier in current production is absent. `P_max−P_base` is in USD because epsilon is 1/USD. Historical inversion gives exactly delta_P for a retained trip with its own epsilon; this algebraic identity does not empirically validate willingness to pay.

Scenarios use pooled P10/P25/P50/P75/P90/P95 epsilon, distance deviations +5%, +10%, +25%, +50%, +100%, and all seven existing factors .85–1.15. A representative base is the median historical condition P_base across retained rows in each variant; the CSV states it explicitly. The tolerance itself is independent of that representative base; comparison with multiplier premiums is not.


30min tolerance above base, USD:

| epsilon_percentile | 0.05 | 0.1 | 0.25 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- |
| P10 | 4.39296 | 8.78592 | 21.9648 | 43.9296 | 87.8592 |
| P25 | 1.59495 | 3.18991 | 7.97477 | 15.9495 | 31.8991 |
| P50 | 0.746415 | 1.49283 | 3.73207 | 7.46415 | 14.9283 |
| P75 | 0.542292 | 1.08458 | 2.71146 | 5.42292 | 10.8458 |
| P90 | 0.388655 | 0.77731 | 1.94328 | 3.88655 | 7.7731 |
| P95 | 0.279042 | 0.558085 | 1.39521 | 2.79042 | 5.58085 |

hourly tolerance above base, USD:

| epsilon_percentile | 0.05 | 0.1 | 0.25 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- | --- |
| P10 | 5.48945 | 10.9789 | 27.4473 | 54.8945 | 109.789 |
| P25 | 2.23162 | 4.46325 | 11.1581 | 22.3162 | 44.6325 |
| P50 | 0.93109 | 1.86218 | 4.65545 | 9.3109 | 18.6218 |
| P75 | 0.589623 | 1.17925 | 2.94812 | 5.89623 | 11.7925 |
| P90 | 0.428216 | 0.856431 | 2.14108 | 4.28216 | 8.56431 |
| P95 | 0.315651 | 0.631302 | 1.57826 | 3.15651 | 6.31302 |

For these positive-distance cases, factors <=1 always pass; larger epsilon lowers the permissible premium, while smaller epsilon can yield a very large premium. Zero relative distance gives P_max=P_base. Negative deviations (not part of the requested positive scenario grid) lower P_max and can make it nonpositive at small epsilon. The retained historical M10 sample contains only positive distance/price deviations; it cannot by itself validate acceptance for shorter trips. No Bernoulli draw, runtime distribution selection, dispatch, or simulation is performed.

## 12. Privacy and API separation

`src/analysis/passenger_sensitivity_m10.py` is never imported by production. Full private diagnostics remain in ignored local parquet; CSVs expose condition/population aggregates and illustrative quantiles, not identifiable per-trip epsilon. `illustrative_private_pmax` is the only new consumer using an individual sensitivity as an acceptance input. `public_aggregate_state` takes only explicit public fields J_hat, J_disp_prev, I, p, pi and rejects an epsilon keyword; it is an analysis schema, **not** a new DQN. Tests inspect existing pricing and routing state definitions for epsilon exposure. Existing request/customer audit epsilon is private research data, not a public state input. This is interface separation, not encryption, differential privacy, or a proof about a future unimplemented DQN.

## 13. Production unchanged and reproduction

No production pricing, sampler, dispatch, routing, configuration or legacy sensitivity artifact was changed. No 2/8/48/298-slot production run was invoked. Unit tests include their existing small fixture-based orchestration checks; those are not production experiments.

Run the standalone analysis with:

```bash
python scripts/analyze_passenger_sensitivity_m10.py
python -m unittest discover -s tests -p test_passenger_sensitivity_m10.py -v
python -m unittest discover -s tests -q
```

The script reads only historical rows for computations; it hashes full source files solely for identity. Metadata contains input/source hashes, Python library versions, deterministic output hashes, population semantics and open decisions. Chart PDFs have volatile creation/modification timestamps removed. Small-fixture byte reproducibility is tested; full tables/figures are checked with a second standalone analysis pass. This does not rerun a simulator.


## 14. Output guide

- `current_vs_new_m10.csv`: 15 compatibility decisions.
- `filter_funnel_*.csv`: exact sequential filters.
- `base_conditions_*.csv`: M9 means/counts and sparse flags.
- `sensitivity_conditions_*.csv`: retained epsilon statistics, including zero-output base conditions.
- `overall_sensitivity_summary.csv`: raw and log1p summaries.
- `time_grouping_comparison.csv`: base and epsilon support, possible/observed/missing cells.
- `small_delta_p_diagnostic.csv`: disjoint denominator bins.
- `outlier_rule_comparison.csv`: alternative trims, no selected rule.
- `sampling_distribution_diagnostic.csv`: pooled descriptive candidates, no selected sampler.
- `weather_sensitivity_summary.csv`: observed WeatherCode summaries.
- `m12_acceptance_sanity.csv`: illustrative private-acceptance scenarios.
- `summary.json`, `artifact_manifest.json`: assumptions, source identity, totals and output hashes.
- `verification.json`: execution results and preservation checks from this task.
- `charts/`: 15 requested chart topics plus additional condition mean/SD heatmaps; PNG and PDF per chart.

Plots use log axes where needed, with units and tail-display omissions labeled. Scatter-density hexagons use all valid observations, not an undisclosed sample. Missing condition cells stay grey/gapped. Charts summarize historical association, not final runtime model behavior.


## PROFESSOR-REQUESTED ELASTICITY VS TIME/WEATHER PLOTS

Graph 1 plots the existing `mean_epsilon` for each time-of-day × WeatherCode condition as a separate weather line. Its logarithmic y-axis shows every observed mean without clipping, trimming, or changing values.

Graph 2 plots the existing median ε with the empirical P25–P75 shaded band. Thin vertical IQR marks also show isolated supported points. The term distribution channel in Graph 2 refers only to the empirical interquartile band (P25–P75). It is not a newly defined channelization metric.

Hourly versions (`17_mean_elasticity_vs_time_weather` and `18_elasticity_distribution_channel_vs_time_weather`) are the primary presentation versions. The 30-minute versions (`17b_mean_elasticity_vs_halfhour_weather` and `18b_elasticity_distribution_channel_vs_halfhour_weather`) are supplementary because final Time-of-Day grouping remains subject to professor confirmation. Each is available as PNG and PDF in `charts/`.

The project has no authoritative descriptive weather-name mapping for these tables, so labels are Weather 1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 15, 16, and 21. No categories are merged. Hourly charts represent 487,710 valid observations across 117 of 312 combinations and 12 observed weather codes; Weather 21 remains in the legend with no data. The 195 missing hourly combinations remain gaps. The supplementary charts represent 526,892 observations across 238 of 624 combinations and all 13 weather codes; 386 missing combinations remain gaps.

No values are interpolated, zero-filled, or forward-filled. Means require N ≥ 1. Distribution plots omit empty and singleton groups (N < 2), the minimum display rule needed to avoid a single-observation distribution; this does not define a new methodological sample-size threshold. Hourly data have no singleton groups. The 30-minute distribution omits Period 7 / 03:30 / Weather 1 (N=1) and Period 28 / 14:00 / Weather 2 (N=1); their means remain on Graph 1. All condition sample sizes, including zero support, are recorded in `elasticity_time_weather_chart_manifest.json`.

Graph 2 uses a **view-only** y-axis range from zero to pooled raw ε P99: 0.493789 for hourly and 0.576244 for 30-minute data (exact limits in the chart manifest). This keeps the central distribution readable; portions of IQRs/medians above this display limit are clipped only in the rendering. Statistics use the full untrimmed valid M10 population. The manifest lists each affected condition and its unchanged quantiles. No maxima, filtering changes, or new outlier rule are introduced.

Reproduce this reporting-only addition with `MPLCONFIGDIR=/tmp/m10_mpl_cache python scripts/plot_m10_time_weather.py`. It reads only the existing condition tables and pooled summary. Exact source-to-plot equality and preservation of all original package files except this README and chart manifests are checked during generation. The original `summary.json` and `verification.json` describe the original analysis run; the supplementary chart manifest records these additions, and `artifact_manifest.json` includes their hashes.

## QUESTIONS FOR PROFESSOR

1. M9 does not define Time-of-Day width: should 30-minute Period or Hour be frozen, given the support and distribution differences?
2. Which outlier rule, if any, should be selected, and should its scope be pooled or condition-specific? The M10 formula itself is explicit and has been implemented without reinterpretation.
3. Should a positive minimum delta_P be imposed after reviewing the denominator-tail diagnostics? If so, specify the currency threshold and its scientific rationale.
4. Which conditional runtime sampling family should be approved: empirical, positive-truncated Normal, lognormal, or another specified family? If truncation is selected, how should its parameters be estimated?
5. What fallback, if any, should apply to sparse or absent Time × Weather conditions, and what support threshold defines sparse for that purpose?
6. Does the numerical willingness-to-pay behavior from the fixed M12 equation match the intended passenger model, especially very small epsilon and negative distance deviations?
7. Should the legacy 100-mile source-validity cap be retained as a documented M1 cleaning rule for this new analysis, or should positive finite inputs remain the review population? No replacement threshold has been invented.

The formula, positive-deviation filters, condition means, individual-epsilon privacy, and M12 equation are already specified in the PDF and are not posed as unresolved choices. Time grouping, source cleaning, outliers, denominator floor, sampling and fallback remain **PROFESSOR DECISION REQUIRED**. No runtime sampling configuration is frozen by this package.
