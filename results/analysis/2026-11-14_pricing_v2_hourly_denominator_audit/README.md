# Weather × Hour dispersion and fare-resolution diagnostic

## Exact unchanged calculation contract

The hourly granularity in the latest instruction governs this audit. This does not silently rewrite the runtime/freeze registry. References fixed for computation are **P_base/P_norm=22.354198442390455 USD**, **L_base=4.616983790655043 km**. Existing artifacts still classify numerical reference approval as pending; they must not be described as fully frozen methodology.

`delta_P=(fare-P_base)/P_base`; `delta_L=(L_km-L_base)/L_base`; `epsilon=delta_L/delta_P`. Source: `results/analysis/2026-11-14_pricing_v2_weather_clustering_resolved/WEATHER_CLUSTER_VALIDATION.md`, with prior calibration provenance in the V2 freeze-design package. These constants and rules were reported before calculation.

Source cache: `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet`, columns pickup_timestamp, fare, trip_distance. fare is the processed TLC fare_amount measure (USD), not total_amount. trip_distance is source miles; multiply by1.609344 to obtain L_km. Use existing cleaned Jan1≤pickup<Mar16 population, upstream positive-distance≤100-mile source rule, and current analytical1.5≤L_km<75 filter. No raw preparation or additional source cleaning. Weather joined by pickup hour from processed monthly weather files with Jan1≤Datetime<Mar16 read filters. Date bounds and many-to-one join asserted; N=6,967,155.

Signed epsilon retained. Exact zero denominator undefined, nonfinite excluded. Zero numerator/nonzero denominator gives zero. No abs transformation, clipping, empirical support restriction or automatic denominator threshold. There are no undefined or exact-zero epsilon values in this current population. SIGNED_VALID statistics cover6,967,155; POSITIVE_VALID companion covers5,975,653 for continuity with previous primary positive-fit diagnostics. This distinction avoids conflating hourly granularity with a sign-population change. Both are explicitly labelled in every output.

## A. Hourly scenario findings and T-group comparison

211 observed raw Weather×Hour combinations for each population; no missing combinations fabricated. The authoritative diagnostic uses hours0–23, not merged semantic weather. Previously observed T-groups numbered48; current hourly rows are not the same statistical units, so a difference in median scenario SD alone is not a causal aggregation effect.

| Population | SD<4 | SD>=4 | Minimum SD | Median SD | P90 SD | Maximum SD | Prior T-group median SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIGNED_VALID |0/211 (0%)|211|5.398019|23.698368|54.549975|349.045914|30.262207|
| POSITIVE_VALID |4/211 (1.895735%)|207|3.716809|17.458141|40.411140|376.971680|20.731691|

Positive scenarios below4: Heavy Rain hour15 (N5128,SD3.893019), Heavy Rain hour17 (N6095,SD3.836638), Snowfall hour1 (N258,SD3.890356), Snowfall hour16 (N5732,SD3.716809). These are individual descriptive passes, not approved clusters or validated stable distributions.

`t_vs_hour_comparison.csv` decomposes each original Weather×T variance exactly into weighted within-hour variance plus weighted squared hourly-mean differences. Positive median between-hour contribution **0.018260%**, maximum **0.453327%**; signed median **0.007947%**, maximum **0.485207%**. Thus T aggregation did **not materially inflate dispersion through differing hourly means** in these observations. Smaller hourly groups expose concentrated extreme observations: maximum SD increases. The hourly medians are lower, but within-hour tails remain the main issue. All decompositions checked against the original T variance; population rather than sample variance used.

## B. Concentration of squared deviations

For each scenario deviations are from that same population's full hourly mean. Contributions rank **squared deviations**, not the numerical maximum signed epsilon. Top fractions use ceil(fraction*N); fixed top5/10/50/100 are capped at N. This matters for small groups. No top-tail values were removed for calculating original statistics.

In **all211 positive and all211 signed scenarios**, the largest1% by squared deviation contributes over50% of variance. The existing |delta_P|<0.001 flag contributes over50% in **111/211 positive** and **136/211 signed** scenarios. Therefore tail concentration is universal here, whereas the particular near-zero flag is not a universal explanation. Small denominators outside that flag can still have substantial effects. `extreme_contribution_analysis.csv` retains every requested top-count/fraction contribution and actual selected counts.

`extreme_observations.csv` records top10 squared-deviation rows for low/median-rank/high-SD scenarios separately by sign population, with timestamp, raw weather/hour, fare, converted distance, references, deltas and epsilon. Median representative is the lower middle ordered scenario; it is not necessarily equal to the interpolated median SD. The same file also preserves **all408 rows** at the smallest nonzero absolute denominator under a separate reason label. Duplicate appearance across diagnostic roles is intentional, not additional observations.

## C. Fare and denominator resolution

All current fares align with a cent grid within1e-7 cent floating-point tolerance. The minimum observed meaningful positive adjacent unique-fare increment is **$0.01**. Unique sorted-price spacings—not changes between arbitrary successive trips—are enumerated in fare_resolution_analysis.csv, including each spacing frequency. Most common: $0.01 (11262 adjacent-level gaps), $0.02 (574), $0.03 (243), $0.04 (139), $0.05 (100). Twelve-decimal rounding is used only to coalesce floating-point representations of diagnostic gap sizes; no source fare or epsilon is rounded for computation.

P_base is a non-cent-aligned mean. The nearest observed fare is **$22.35**, difference approximately−$0.004198442390455, giving **abs(delta_P)=0.00018781449047585653** in408 source rows. $22.36 gives delta_P≈0.00025952876926. Ordinary discrete fares can therefore generate very large ratios when delta_L is nonzero. This is denominator/measurement sensitivity in the ratio, not evidence of a floating-point divide bug or independently verified source corruption.

The resolution CSV provides all unique fares within±$0.10, cumulative counts in explicitly diagnostic absolute-dollar windows, and empirical distributions of abs(P−P_base) and abs(delta_P). No diagnostic window is a validity cutoff. The nearest-row export contains actual source observations, not synthetic examples.

## D. Denominator sensitivity — no recommended threshold

Exact-zero denominators would remain excluded even in threshold0. The same fixed eight diagnostic thresholds are evaluated independently within each population. Excluded percentages use the corresponding no-threshold sign population as denominator. No extra thresholds were introduced.

| population | diagnostic_min_abs_delta_P | excluded_pct | SD_lt4 | median_SD | global_mean | global_median | mean_change | median_change |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SIGNED_VALID | 0.000000 | 0.000000 | 0 | 23.698368 | 1.439360 | 1.058745 | 0.000000 | 0.000000 |
| SIGNED_VALID | 0.000100 | 0.000000 | 0 | 23.698368 | 1.439360 | 1.058745 | 0.000000 | 0.000000 |
| SIGNED_VALID | 0.000250 | 0.005856 | 0 | 18.607502 | 1.442421 | 1.058745 | 0.003061 | 0.000000 |
| SIGNED_VALID | 0.000500 | 0.011784 | 1 | 13.707768 | 1.433840 | 1.058745 | -0.005520 | 0.000000 |
| SIGNED_VALID | 0.001000 | 0.023510 | 1 | 11.480402 | 1.441404 | 1.058745 | 0.002044 | 0.000000 |
| SIGNED_VALID | 0.002500 | 0.073358 | 2 | 9.449578 | 1.442207 | 1.058745 | 0.002847 | 0.000000 |
| SIGNED_VALID | 0.005000 | 0.158357 | 2 | 8.463815 | 1.425198 | 1.058745 | -0.014161 | 0.000000 |
| SIGNED_VALID | 0.010000 | 0.720208 | 4 | 5.607639 | 1.423940 | 1.058745 | -0.015420 | 0.000000 |
| POSITIVE_VALID | 0.000000 | 0.000000 | 4 | 17.458141 | 2.746274 | 1.184555 | 0.000000 | 0.000000 |
| POSITIVE_VALID | 0.000100 | 0.000000 | 4 | 17.458141 | 2.746274 | 1.184555 | 0.000000 | 0.000000 |
| POSITIVE_VALID | 0.000250 | 0.003899 | 4 | 12.961538 | 2.677186 | 1.184555 | -0.069088 | 0.000000 |
| POSITIVE_VALID | 0.000500 | 0.006978 | 5 | 9.799604 | 2.619000 | 1.184555 | -0.127275 | 0.000000 |
| POSITIVE_VALID | 0.001000 | 0.013421 | 5 | 8.580872 | 2.582724 | 1.184555 | -0.163550 | 0.000000 |
| POSITIVE_VALID | 0.002500 | 0.043644 | 6 | 7.340780 | 2.516790 | 1.184555 | -0.229484 | 0.000000 |
| POSITIVE_VALID | 0.005000 | 0.099069 | 8 | 6.479092 | 2.456562 | 1.183834 | -0.289712 | -0.000721 |
| POSITIVE_VALID | 0.010000 | 0.481839 | 56 | 4.711971 | 2.272167 | 1.180244 | -0.474107 | -0.004311 |

The CSV also reports retained/excluded N, retained%, scenario counts and missing counts, percentage SD<4, min/P90/max SD and sign shares. Threshold0.0001 has no effect because the smallest actual nonzero denominator is larger. Across the tested grid there is **no demonstrated SD plateau**: median SD continues falling through0.01, and most scenarios still fail4. Medians are stable, but the positive mean drops from2.746274 to2.272167 (about17.3%) by0.01, despite only0.481839% positive observations being excluded. Signed mean shifts much less and its median is unchanged, partly reflecting offsetting signed tails; that does not establish that the positive simulation distribution is unchanged.

Consequently this audit identifies a sensitivity region, not a defensible winning cutoff or proof of central-distribution invariance. No automatic exclusion, threshold or sampler rule is approved.

## E. Heavy Rain T2 follow-up

Heavy Rain T2 contains **only hour05** in these data; hour04 is absent and not fabricated. Its between-hour variance is zero (signed numerical residue approximately1e-34%). The previous failure cannot be attributed to mixing different hourly means.

Positive hour05: N992, mean2.897879, median2.104376, SD5.101840, P99=24.624022, max95.448605. There are zero existing near-zero flags, but min abs(delta_P)=0.006451. Largest observation contributes33.1737% of squared deviations; top10 contribute78.5611%. IQR=3.496620−0.899654≈2.596966: the spread is not solely a broad shift of the center. The earlier saved audit identifies the largest positive row at fare$22.20, distance1.57715712km, delta_P≈−0.00689796, epsilon95.448605. This is a small but non-flagged denominator.

Signed hour05: N1181, SD47.557135, minimum−1608.59009; two existing near-zero flagged observations; the largest squared-deviation observation contributes96.9049%. Positive filtering hides that negative extreme but does not make the positive group pass4. Modest sample size makes its few extreme rows influential; it does not prove sampling error or source invalidity. No row is relabelled invalid.

## F. Methodological verdict

1. Hourly resolution changes descriptive SD summaries but does not remove the issue; between-hour mean mixing contributes less than0.5% in every T scenario.
2. Unmodified hourly passes: signed0/211; positive4/211.
3. Small numbers of observations dominate variance. Near-zero denominators under the existing flag explain most variance in about53% of positive and64% of signed scenarios, not all; outside-flag ratios also matter.
4. Cent-discrete fares near a non-discrete reference mean provide direct evidence of strong ratio sensitivity. No numerical rounding error or new invalidity rule is inferred.
5. Every diagnostic exclusion fraction is reported above and in the response CSV; no fraction is approved.
6. No clear stabilizing plateau preserving both mean and median is demonstrated. Positive mean changes materially as tail contributions are removed.
7. Heavy Rain remains problematic at hourly resolution; T2 is already a single observed hour.
8. The next decision concerns **denominator/data-resolution and calibration-population methodology**, not clustering. This is not a blanket claim that the professor's requirement is impossible under every valid methodology; it diagnoses the unchanged current contract.

Clustering NOT approved. No clustering, sampler integration, fitting, DQN training, production/V1/runtime change or protected March17–31 analytical access. March16 is also excluded. Registry and previous reports are unchanged.

## File definitions and checks

Nine requested outputs only. Counts N describe the named sign population; positive/negative counts reconcile to N. Undefined counts are zero here, verified before statistics; omitted nonpositive rows in the positive companion remain in signed data. Dates refer to actual represented dates for each sign population. All SDs use ddof=0, quantiles use linear interpolation. Verification records summaries, denominator resolution and concentration counts.
