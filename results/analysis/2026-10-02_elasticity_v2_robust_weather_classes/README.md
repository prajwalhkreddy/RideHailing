# Robust weather clustering — offline review

The frozen elasticity formula and references are unchanged. As a PROJECT_ROBUSTNESS_DECISION, not a professor-specified rule, official clustering uses 1% trimmed means per observed WeatherCode/hour. Trimming removes floor(N*0.01) observations from each tail. Missing features use the pooled same-hour 1% trimmed mean across actual trips, not an average of weather-code means. Observed features remain intact; the mask is 1 for fills, 0 for observed cells.

K-means: K=3, seed=42, n_init=50, Lloyd, no scaling or trip weighting. Each weather code is one sample. Official classes are numbered by smallest member code. The 5% run is diagnostic only, aligned to official labels by maximum agreement. Six-seed reruns use the identical 1% matrix. Full features include ordinary and both trimmed means with support N.

Final class/hour N, mean, population SD (ddof=0) and variance use ALL actual untrimmed trip epsilon after exact-zero denominator exclusion. No trimmed or pooled feature enters final aggregation. Missing final groups remain absent. Charts use untrimmed final statistics on linear axes; the separate clustering diagnostic uses 1% features. No previous canonical artifact, historical clustering result, or production code is modified.

summary.json records partitions, agreement, shares, missing groups, ranges and focused validation. Agreement across these checks does not establish robustness to every sample or methodological choice. No 5% mapping is adopted.
