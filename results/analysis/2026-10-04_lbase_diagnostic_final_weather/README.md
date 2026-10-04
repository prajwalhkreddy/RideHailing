# L_base diagnostic — actual Clear, Rain and Snowfall

Status: LBASE_DIAGNOSTIC_READY_FOR_REVIEW. Diagnostic only; no canonical methodology or results changed and no winner selected.

## Authority and scope

The requested `notebooks/plan/Passenger_Price_Sensitivity_Lbase_Diagnostic.pdf` was not present under `notebooks/plan` when checked. This package follows the explicit diagnostic instructions in the user request; it does not claim verification against that unavailable document. The existing clean-reference final package remains authoritative for canonical results.

No data preparation, clustering, production changes or charts were run. The complete existing cleaned Jan–Mar 2026 population contains 10,620,409 trips with 0 < trip_distance <= 100 miles. The 100-mile rule remains the existing project source-cleaning decision. All weather codes contribute to overall statistics and the fixed global P_base; only codes 1 (Clear), 8 (Rain), 15 (Snowfall) enter weather-hour comparisons.

## Reused inputs and verification

- `data/processed/elasticity_v2/elasticity_input_2026_01_03_cleaned.parquet`: unchanged trip-level input.
- `results/analysis/2026-10-02_elasticity_v2_lbase_reference/lbase_window_comparison.csv`: reused conditioned bases/support. Each support count and distance mean was verified from the cleaned rows inside its inclusive fare window.
- Same folder, `elasticity_window_comparison.csv`: reused conditioned overall distribution summaries; mean and population SD independently checked against current formulas. Maximum absolute epsilon is max(abs(minimum), abs(maximum)).
- `results/analysis/2026-10-03_elasticity_clean_reference_final/summary.json`: canonical global bases; both verified against complete cleaned source means.
- `data/processed/elasticity_v2/elasticity_actual_weather_clean_reference_final.csv`: all 64 baseline hourly means, SDs and counts reproduced within floating-point tolerance.

## Definitions and calculation

P_base = 21.34586956773507 USD is fixed for every scenario. L_base units are miles. A is the complete cleaned-population mean distance. B–E are mean distances among cleaned trips satisfying abs(fare - P_base) <= the stated window. Support N describes reference estimation, not the elasticity population: every definition evaluates all 10,620,409 cleaned trips.

```text
delta_P = (fare - P_base) / P_base
delta_L = (trip_distance - L_base) / L_base
epsilon = delta_L / delta_P
```

Only exact delta_P == 0 is excluded (0 rows). Signed epsilon is retained. There is no denominator cutoff, clipping, trimming, normalization, imputation or clustering. SD uses ddof=0; quantiles use linear interpolation. P95 and P99 are signed epsilon quantiles; max_abs_epsilon is the largest absolute observation, not a transformation of the input distribution.

## Overall comparison

| definition | L_base_definition | L_base | L_base_support_N | mean_epsilon | median_epsilon | population_SD | P95 | P99 | max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | global | 3.469070 | 10620409 | 1.426752 | 1.225762 | 28.115013 | 4.053349 | 16.506131 | 30585.381366 |
| B | +/-$0.25 | 3.048671 | 155857 | 1.307600 | 1.161406 | 30.148398 | 4.298821 | 15.876997 | 35515.619226 |
| C | +/-$0.50 | 2.991079 | 196325 | 1.288669 | 1.151855 | 30.595108 | 4.365102 | 15.925928 | 36298.966978 |
| D | +/-$1.00 | 3.017999 | 479000 | 1.297608 | 1.156745 | 30.380327 | 4.330111 | 15.903852 | 35929.087990 |
| E | +/-$2.00 | 3.033396 | 937897 | 1.302649 | 1.159000 | 30.262224 | 4.313342 | 15.957732 | 35720.483129 |

## Weather-hour comparison

Each definition has 64 actual observed weather/hour groups (320 comparison rows total), using the same 3,409,670 observations: Clear 3,085,571 across 24 hours; Rain 217,536 across 20; Snowfall 106,563 across 20. Rain lacks hours 5, 10, 11, 12; Snowfall lacks 0, 4, 20, 22. Clear has no missing hours. No absent groups are materialized or filled.

Across-hour summaries below weight each observed hour equally. They are summaries of hourly statistics, not pooled weather-wide statistics. CSV comparison columns contain absolute change and 100 * (candidate - baseline) / abs(baseline); positive dispersion changes mean increases.

| definition | weather_name | median_hourly_mean_epsilon | min_hourly_mean_epsilon | max_hourly_mean_epsilon | median_hourly_SD | maximum_hourly_SD | median_hourly_P99 | maximum_hourly_max_abs_epsilon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Clear | 1.408119 | 0.920406 | 1.895927 | 25.084142 | 43.986403 | 17.670487 | 10599.509450 |
| A | Rain | 1.351553 | 0.802874 | 1.682793 | 18.903687 | 39.574819 | 15.036116 | 3603.742249 |
| A | Snowfall | 1.406319 | -1.962060 | 4.671881 | 10.599189 | 108.411948 | 17.701986 | 3276.003374 |
| B | Clear | 1.303102 | 0.653283 | 1.854325 | 24.682180 | 49.080371 | 17.969472 | 12562.624653 |
| B | Rain | 1.214641 | 0.701125 | 1.659534 | 18.862858 | 36.510002 | 14.497526 | 3388.044343 |
| B | Snowfall | 1.207719 | -1.805506 | 5.800276 | 10.844620 | 104.632906 | 16.679768 | 3015.111620 |
| C | Clear | 1.298114 | 0.610840 | 1.847715 | 24.695314 | 50.035994 | 18.505823 | 12874.536963 |
| C | Rain | 1.206539 | 0.684958 | 1.655838 | 18.922147 | 36.746847 | 14.618334 | 3353.772879 |
| C | Snowfall | 1.190067 | -1.780632 | 5.979563 | 11.028066 | 108.478684 | 17.204412 | 2973.659468 |
| D | Clear | 1.302145 | 0.630881 | 1.850836 | 24.685507 | 49.580383 | 18.175496 | 12727.259066 |
| D | Rain | 1.210760 | 0.692592 | 1.657583 | 18.886676 | 36.510645 | 14.511900 | 3369.955084 |
| D | Snowfall | 1.198402 | -1.792377 | 5.894908 | 10.939116 | 106.662678 | 16.896843 | 2993.232231 |
| E | Clear | 1.302628 | 0.642183 | 1.852596 | 24.682820 | 49.326872 | 18.066216 | 12644.197075 |
| E | Rain | 1.212718 | 0.696897 | 1.658567 | 18.872568 | 36.392388 | 14.586822 | 3379.081547 |
| E | Snowfall | 1.203102 | -1.799001 | 5.847164 | 10.890780 | 105.638576 | 16.637833 | 3004.270905 |

## Interpretation

**A_SD**: No broad reduction. Overall population SD increases 7.23–8.82%. Clear median hourly SD changes little, but its maximum rises; Rain maximum SD falls modestly; Snowfall maximum SD is similar while median SD rises.

**B_extremes**: No consistent extreme-tail improvement. Overall signed P99 falls about 3.3–3.8%, but maximum absolute epsilon increases 16.1–18.7%. Clear hourly tails worsen, while Rain/Snowfall maxima improve modestly. Signed P99 does not capture the negative tail; maximum absolute epsilon captures either tail.

**C_stability**: The +/-$0.50, +/-$1 and +/-$2 candidates are reasonably close descriptively: L_base span 1.415% of smallest; overall SD span 1.100%. This is descriptive, not a formal stability test. Weather-hour summaries are close but not identical.

**D_pattern**: Broad pattern persists: Clear/Rain hourly means stay positive; Snowfall includes negative and large positive hourly means and the largest peak SD. Fine rankings change: global median hourly mean ranks Clear > Snowfall > Rain; conditioned candidates rank Clear > Rain > Snowfall. Do not infer causal weather effects or statistical significance.

**decision**: Diagnostic only; no winner selected and current canonical global L_base remains unchanged.

Changing L_base changes the relative-distance numerator for every trip while retaining the same denominator. It does not remove near-zero price differences, so large ratio tails remain possible. These are descriptive reference-point sensitivities, not causal or inferential comparisons. No formal “materiality” threshold has been introduced.

## Files and validation

- `overall_lbase_comparison.csv`: five definitions, bases/support and complete-population diagnostics.
- `actual_weather_hour_lbase_comparison.csv`: 320 observed rows with N, mean, median, population SD, P95, P99 and maximum absolute epsilon.
- `weather_summary_by_lbase.csv`: 15 weather/definition summaries and changes versus global.
- `summary.json`: exact results, provenance, interpretation, missing hours, tests and protected SHA-256 hashes.
- `README.md`: this record.

Focused checks passed: population count/date/distance constraints; global references; all candidate supports and means; reused conditioned mean/SD; baseline equality to canonical hourly CSV; selected support counts; finite outputs; exact missing groups; independent relative-formula, sign, near-zero and exact-zero spot checks. Before/after SHA-256 hashes confirm the cleaned source, reused diagnostics, entire existing clean-reference final package and canonical final CSV were unchanged. No canonical files were written.
