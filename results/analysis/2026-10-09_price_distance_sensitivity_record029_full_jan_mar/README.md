# Record-029 Price–Distance Sensitivity — Full January–March 2026 Analysis

## Scope and source population

This analysis implements the price–distance sensitivity formulation in `notebooks/plan/Price_Distance_Sensitivity_Implementation_Guide.docx`. The quantity describes paired historical price and distance; it is not a direct estimate of classical price-demand elasticity. All main calculations use the complete validated January–March 2026 population, not an inspection sample.

The source is `data/processed/elasticity_v2/elasticity_input_2026_01_03_cleaned.parquet`. All 10,620,409 rows pass the additional checks: finite positive fare and distance, distance no greater than 100 miles, valid timestamp within 2026-01-01 inclusive to 2026-04-01 exclusive, hour consistent with timestamp and within 0–23, and integer Meteostat condition codes within 1–27. No additional rows were removed. Reason counts and observed weather codes are in cleaning_summary.json. The existing 100-mile rule is retained as a project source-cleaning decision.

Fare is in USD, distance in miles. Pickup timestamp, hour, weather code and original paired values are retained. `source_row_index` is the zero-based row position in the unchanged input, not a new claim of unique trip identity. Row order is preserved.

## Global price reference and price-conditioned distance references

P_base is the arithmetic mean fare over all 10,620,409 rows: **21.34586956773507 USD**. Weather/hour subsets are not used to estimate it.

The working specification defines distance reference through proximity to the global fare reference:

\[
L_{base}(\tau_P)=\operatorname{mean}\{L_i: |P_i-P_{base}|\leq\tau_P\}.
\]

The reference subset establishes L_base only; it does not limit the population used for sensitivity estimation. No candidate window is designated supervisor-approved or final. Distance SD in this table is population SD (ddof=0).

| tau_P | support_N | support_percentage | L_base | distance_median | distance_SD | distance_P05 | distance_P95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 155857 | 1.46752352 | 3.04867083 | 3 | 1.42580086 | 1.19 | 4.89 |
| 0.5 | 196325 | 1.84856346 | 2.99107867 | 2.9 | 1.48284323 | 1.11 | 5 |
| 1 | 479000 | 4.51018412 | 3.01799879 | 2.95 | 1.42984655 | 1.17 | 4.93 |
| 2 | 937897 | 8.83108174 | 3.03339603 | 2.97 | 1.43856042 | 1.15 | 5.04 |

## Formulation and denominator handling

\[
\mathrm{price\_diff}_i=P_i-P_{base},\qquad
\mathrm{distance\_diff}_i=L_i-L_{base},
\]
\[
r_{P,i}=\frac{P_i-P_{base}}{P_{base}},\qquad
r_{L,i}=\frac{L_i-L_{base}}{L_{base}},\qquad
\epsilon_i=\frac{r_{P,i}}{r_{L,i}}.
\]

This is relative price divided by relative distance, the reverse of the previous elasticity_v2 formulation. No earlier epsilon values are reused. Each candidate is calculated independently for every cleaned observation. Signed values are retained; exact r_L=0 is the only exclusion from epsilon calculation, represented by an explicit Boolean flag and null epsilon. All four candidates have zero such cases. No nonzero near-zero denominator is discarded.

The full epsilon Parquet stores price_diff and relative_price_deviation, plus distance_diff, relative_distance_deviation, epsilon and exact-zero flags for each suffix `tau_025`, `tau_050`, `tau_100`, `tau_200`. No denominator threshold, sensitivity clipping, trimming, winsorization, extra normalization, minimum raw distance, distribution fitting or simulation change is applied.

## Full-population sensitivity distributions

| tau_P | N_valid_epsilon | N_exact_zero_denominator | mean | median | population_SD | P01 | P99 | max_abs_epsilon | negative_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 10620409 | 0 | 0.787444031 | 0.764565894 | 28.9046105 | -7.0710261 | 7.73582409 | 24569.4902 | 11.5449885 |
| 0.5 | 10620409 | 0 | 0.445894558 | 0.768680082 | 34.1020157 | -7.4124447 | 7.80306334 | 11516.5959 | 11.6732322 |
| 1 | 10620409 | 0 | 0.739608303 | 0.767133106 | 19.27705 | -7.09494554 | 7.9953435 | 7676.41774 | 11.5828778 |
| 2 | 10620409 | 0 | 0.613266391 | 0.766456795 | 13.5891643 | -7.00257395 | 7.8887834 | 11660.2734 | 11.5573138 |

Medians are close across candidates, whereas means and SDs are appreciably reference-sensitive. No candidate is selected because its SD is smallest. The complete summary CSV also reports variance, extrema, P05/P25/P75/P95, sign counts and percentages. Population SD uses ddof=0; quantiles use linear interpolation. Sign shares use valid epsilon N.

For each candidate, the full-range histogram uses 40 equal-width bins spanning observed extrema, with a symmetric-log count axis so rare tail bins remain visible. Supplementary P01–P99 histograms use 40 bins on that central view, with linear counts. Bin intervals include the left edge and exclude the right, except the last includes both. Full-view counts reconcile to valid N. Central-view restrictions affect visualization only. The bin CSV provides percentages relative both to all valid rows and to displayed rows.

`extreme_sensitivity_examples_by_lbase.csv` preserves 20 largest-absolute-epsilon examples per candidate with original source positions, fare, distance, time/weather and both relative deviations. These observations are retained; their appearance is not an invalidity determination.

## Near-zero relative-distance deviations

| tau_P | band | N | percentage | max_abs_epsilon |
| --- | --- | --- | --- | --- |
| 0.25 | 0 <= abs(relative_distance_deviation) < 1e-05 | 0 | 0 | nan |
| 0.25 | 1e-05 <= abs(relative_distance_deviation) < 0.0001 | 0 | 0 | nan |
| 0.25 | 0.0001 <= abs(relative_distance_deviation) < 0.001 | 8826 | 0.0831041441 | 24569.4902 |
| 0.25 | 0.001 <= abs(relative_distance_deviation) < 0.01 | 44649 | 0.420407538 | 2131.5645 |
| 0.25 | 0.01 <= abs(relative_distance_deviation) < inf | 10566934 | 99.4964883 | 495.329365 |
| 0.5 | 0 <= abs(relative_distance_deviation) < 1e-05 | 0 | 0 | nan |
| 0.5 | 1e-05 <= abs(relative_distance_deviation) < 0.0001 | 0 | 0 | nan |
| 0.5 | 0.0001 <= abs(relative_distance_deviation) < 0.001 | 9427 | 0.0887630599 | 11516.5959 |
| 0.5 | 0.001 <= abs(relative_distance_deviation) < 0.01 | 66398 | 0.625192495 | 1362.93354 |
| 0.5 | 0.01 <= abs(relative_distance_deviation) < inf | 10544584 | 99.2860444 | 1003.20989 |
| 1 | 0 <= abs(relative_distance_deviation) < 1e-05 | 0 | 0 | nan |
| 1 | 1e-05 <= abs(relative_distance_deviation) < 0.0001 | 0 | 0 | nan |
| 1 | 0.0001 <= abs(relative_distance_deviation) < 0.001 | 9017 | 0.0849025683 | 7676.41774 |
| 1 | 0.001 <= abs(relative_distance_deviation) < 0.01 | 66358 | 0.624815862 | 3282.8091 |
| 1 | 0.01 <= abs(relative_distance_deviation) < inf | 10545034 | 99.2902816 | 1010.22439 |
| 2 | 0 <= abs(relative_distance_deviation) < 1e-05 | 0 | 0 | nan |
| 2 | 1e-05 <= abs(relative_distance_deviation) < 0.0001 | 0 | 0 | nan |
| 2 | 0.0001 <= abs(relative_distance_deviation) < 0.001 | 0 | 0 | nan |
| 2 | 0.001 <= abs(relative_distance_deviation) < 0.01 | 53725 | 0.50586564 | 11660.2734 |
| 2 | 0.01 <= abs(relative_distance_deviation) < inf | 10566684 | 99.4941344 | 369.241614 |

The denominator is small when distance is close to the candidate L_base, approximately three miles, not when raw distance itself approaches zero. No candidate has abs(relative_distance_deviation)<0.0001. The 0.0001–0.001 band contains 8,826, 9,427 and 9,017 observations for the first three windows, respectively; it is empty for ±$2. These differences illustrate sensitivity to where the continuous reference lies among recorded distance values. Counts and percentiles are evidence for numerical inspection, not a filtering policy. Band N includes exact-zero denominators if present; epsilon summaries use defined values only, and the file separately reports both counts.

## Very short raw distances

| percentile | distance_miles |
| --- | --- |
| P0 | 0.01 |
| P0.1 | 0.01 |
| P0.5 | 0.01 |
| P1 | 0.15 |
| P5 | 0.5 |
| P10 | 0.68 |
| P50 | 1.89 |
| P90 | 8.68 |
| P95 | 12.62 |
| P99 | 19.56 |
| P100 | 99.93 |

Overall mean distance is 3.46907003958134 miles. The minimum 0.01-mile value occurs 54,993 times (0.517805%). Empirical quantile boundaries, after merging repeated values, define descriptive bands in `distance_distribution_diagnostic.csv`; bands partition the entire cleaned population. No L_min is adopted.

The 100 shortest observations, ordered by distance then original row position, appear in `short_distance_examples.csv`. Their fares range from $3.00 to $125.00. This is an inspection set, not a basis for population statistics or an automatic invalidity label. A raw distance near zero gives relative_distance_deviation near −1 for these references; it is different from a distance near L_base, which gives a near-zero denominator.

## Price–distance relationship

Full-population Pearson correlation is 0.852985; this is descriptive association, not a causal or fitted demand model. The full-range density chart bins every observation deterministically in a 180×180 grid. The supplementary density view restricts both axes to their marginal P99 values only for display, with displayed N labelled; all statistics use full data.

`price_distance_summary.csv` contains overall means/ranges and full-support summaries for the 20 most frequent exact fares and 20 most frequent exact distances. Conditional P05–P95 spreads show different distances at identical fares (flat-price patterns) and different fares at identical distances. The conditional-spread figure presents these medians/ranges without fitting a functional form. Repeated fares do not alone identify a tariff or prove a source error; the charts do not establish a unique piecewise model.

## Clear/Rain hourly analysis

Detailed reporting covers actual Clear (1) and Rain (8) observations only, while global references and main summaries use all weather codes. There are 44 populated groups per candidate: 24 Clear and 20 Rain, or 176 rows across four candidates. They contain 3,303,107 actual observations per candidate. Rain hours 5, 10, 11 and 12 remain absent. No weather clustering or missing-cell imputation is used. The hourly CSV reports N, mean, median, population SD, extrema, P95 and P99.

## Research decisions remaining open

The final price window tau_P, corresponding final L_base, any minimum meaningful raw distance L_min, any treatment of near-zero relative-distance deviations, epsilon outlier bounds, final sensitivity distribution and truncated-normal parameters remain unresolved. No bounded distribution, synthetic population or downstream simulation integration is selected here. The observed reference sensitivity and tails should inform subsequent methodological decisions rather than automatically determine them.

## Files and reproducibility

Processed namespace: `data/processed/price_distance_sensitivity_record029/`

- `cleaned_price_distance_jan_mar_2026.parquet`: all validated rows and source positions.
- `cleaning_summary.json`: input/output counts and validity checks.
- `full_jan_mar_sensitivity_by_lbase.parquet`: all rows, four candidate epsilon calculations and supporting formula columns.

Analysis files:

- `cleaning_summary.json`: identical copy of processed cleaning report.
- `lbase_price_window_comparison.csv`: four reference windows and support/distribution statistics.
- `near_zero_distance_deviation_diagnostic.csv`: denominator-band counts and absolute-epsilon summaries.
- `distance_distribution_diagnostic.csv`: raw-distance quantiles, mean and empirical bands.
- `short_distance_examples.csv`: 100 shortest traceable observations.
- `full_jan_mar_sensitivity_summary_by_lbase.csv`: complete-population candidate summaries.
- `full_jan_mar_epsilon_bins_by_lbase.csv`: full and central-view bin counts.
- `price_distance_summary.csv`: full-data overall and exact-value conditional summaries.
- `clear_rain_hour_sensitivity_by_lbase.csv`: actual weather/hour summaries.
- `extreme_sensitivity_examples_by_lbase.csv`: traceable full-population extreme examples.
- `summary.json`: authority hash, references, results, unresolved decisions and preservation checks.

Charts: `epsilon_tau_025_full.png`, `epsilon_tau_025_p01_p99.png`, and corresponding `050`, `100`, `200` figures; `price_distance_full_density.png`, `price_distance_central_density.png`, `price_distance_conditional_spreads.png`.

No optional 1,000-row sample was created. All main calculations use the full January–March population. Focused validation checks cover basic validity, row preservation, all persisted formula columns for every row and candidate, exact-zero flags, 44-group support/gaps, histogram and denominator-band totals, and unchanged hashes for prior passenger-sensitivity artifacts. The analysis is isolated from previous results and production code.
