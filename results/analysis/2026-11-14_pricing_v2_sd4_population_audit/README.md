# Read-only V2 population reconciliation against strict SD<4

## Verdict

**Stop before clustering. All48 observed Weather×T scenarios have population SD>=4, in both POSITIVE_VALID and SIGNED_VALID.** The governing PDF page2 explicitly requires combined SD strictly below4 and rejects exactly4. Previous SD<=1 interpretations are superseded for this audit and were not tested. No membership, clipping, support or production rule was changed.

### 1. Methodology consistency

The current calculation is consistent with the documented current V2 formula and scenario-statistics implementation. **Exact equivalence to the population intended by the professor's numerical criterion is not established.** The PDF specifies scenario analysis and strict combined SD<4 but does not specify epsilon orientation, P_base/L_base, sign restriction, dates, distance limits or support treatment. It cannot independently approve those choices. Do not claim a proven formula bug merely because the threshold fails.

Read `methodology_reconciliation.csv` for twelve explicit comparisons. October17's supported Record029 analysis used reciprocal orientation and historical signed support; its lower SD cannot be transferred to current unrestricted positive new-e. No raw historical full-period rows were read for this comparison.

### 2. Exact current contract and sources

Formula printed before calculation:

`e = ((L - 4.616983790655043)/4.616983790655043) / ((P - 22.354198442390455)/22.354198442390455)`.

P is fare USD; L is source trip_distance miles ×1.609344 km. References, range and population decision come from `results/analysis/2026-11-14_pricing_v2_weather_clustering_resolved/WEATHER_CLUSTER_VALIDATION.md`; underlying candidate calibration provenance is in the earlier V2 freeze-design package. These reference values remain **candidates pending approval**, despite being fixed inputs for current diagnostics.

Use Jan1≤pickup<Mar16,1.5≤L<75 km, `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet`. Asserted date bounds. Weather from monthly processed weather files was read with Jan1≤Datetime<Mar16 predicates and joined many-to-one by hour. No unmatched weather or added rows. T1[00,04),T2[04,06),T3[06,16),T4[16,24). All14 raw codes remain separate.

Exact price denominator zero undefined; nonfinite excluded. Positive primary is e>0; signed companion retains all finite defined signs. No abs, clipping, trimming or old T0/Record029 support. Near-zero flag |r_P|<0.001 is reused diagnostically and removes nothing. Zero numerator/nonzero denominator yields zero. Current sample has no undefined or exact-zero e.

### 3. Dispersion reproduction

| population | observations | observed scenarios | SD<4 | SD>=4 | minimum SD | median SD | maximum SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| POSITIVE_VALID primary | 5,975,653 |48|0 (0%)|48|5.101840|20.731691|190.961702|
| SIGNED_VALID companion | 6,967,155 |48|0 (0%)|48|8.601133|30.262207|175.564703|

Eight unsupported code×T combinations are absent, not fabricated. Positive-population excluded share reports nonpositive source observations (991,502 negatives overall), separately from undefined share=0. Fractions for included populations and source signs are named separately in the CSV. The 96 rows are48 scenarios×2 populations, not96 different scenarios. Population SD uses ddof=0; NumPy linear empirical quantiles. P01/P05/P25/P75/P95/P99, min/max, dates and included hours are persisted.

### 4. What causes excessive dispersion?

Representatives selected deterministically by primary scenario SD: lowest; lower middle rank of48 (rank24); highest. No observations removed. The top1% calculation is only an accounting of squared deviations, not a trimmed analysis.

| scenario | positive N | SD | median | existing near-zero flag N | share of squared deviations from flagged rows | top1% squared-deviation share |
|---|---:|---:|---:|---:|---:|---:|
| W9_T2 (lowest_SD) | 992 | 5.101840 | 2.104376 | 0 | 0.0000% | 78.5611% |
| W5_T3 (median_rank_SD) | 217390 | 20.549068 | 1.177080 | 21 | 81.4217% | 98.7590% |
| W7_T1 (highest_SD) | 731 | 190.961702 | 2.350277 | 1 | 98.8986% | 99.7844% |

- **W7_T1 (Light Rain)**: one fare$22.36, distance10.7826048km trip has r_P=0.0002595287693 and r_L=1.3354218444, yielding e=5145.563816. That one near-zero row contributes98.89865% of squared deviations. Large relative fare is not its cause: the fare is exceptionally close to P_base. Distance deviation amplifies the ratio but is not an impossible-distance record.
- **W5_T3 (Fog)**:21 flagged observations (0.0096601% of the positive group) contribute81.42172%. Highest rows include fare$22.35/$22.36 with modest-to-material distance deviations and e in the thousands. Top1% accounts for98.75897%. This is pronounced denominator-sensitive tail concentration.
- **W9_T2 (Heavy Rain)**: no observations satisfy the existing |r_P|<0.001 flag, yet SD=5.10184. The largest e=95.4486 has fare$22.20, r_P=−0.00689796 and distance1.57715712km (r_L=−0.658401). Both deviations negative give positive e. Thus the flag does not explain every failing group; finite small denominators and a heavy tail remain relevant outside it. Top1% contributes78.56105%.

Detailed representative fare/distance ranges, deviation extremes and five largest squared-deviation records are stored in verification.json. Some whole-group fares are unusual (for example$0.01 in Fog T3), but they do not dominate the displayed extreme-e rows. No raw-source forensic validation was performed, so neither source errors nor validity of every observation is established. Records pass current filters; plausible fare-distance pairs can generate extreme ratios without a unit error or impossible distance. Do not label them invalid from this analysis.

Sign changes affect signed distributions but **cannot be the sole explanation**, since positive-only scenarios all still fail. Consistent miles→km conversion of observation and reference introduces no relative-distance unit mismatch. No existing tail-support restriction is applied to new e; historical signed bounds cannot be transplanted without a new decision. These findings diagnose arithmetic/tail concentration, not an authorized remediation.

### 5. Clustering gate and combinations

Per the instruction to stop when most/all individual scenarios exceed4, **no pairwise matrix, linkage, candidate merge or final grouping was calculated**. Those four CSV outputs are header-only with explicit NOT_COMPUTED_STOP_GATE status in verification.json. Empty rejected_groups.csv means no merges tested, not that all merges passed. Individual failures are in scenario_statistics.csv.

For any intact-scenario merge, pooled variance=sum[n_i*(SD_i²+(mu_i−mu_pool)²)]/sum[n_i]. All current individual variances exceed16, so any such merge also exceeds16. This is a feasibility implication, not an enumerated clustering result. No scientifically acceptable exhaustive grouping can emerge from these unchanged scenario observations under strict<4; ordinary clustering would not repair the dispersion. Reconcile the calibration-population/criterion contract first.

### 6. Weather-level interpretation

No accepted groupings or natural final group count were established; count is NOT_ASSESSED, not zero clusters. No stable weather-only mapping across T1–T4 can be inferred. Categories A (consistently together) and B (time-dependent group membership) are unassessed because merges stopped. Category C has reliability evidence: codes17 and21 have only one represented date; codes13 and16 have four dates. Counts/date coverage are in weather_time_stability.csv. Repeated trips within one event do not establish independent weather generalization.

### 7. Remaining decisions

Confirm the exact elasticity population to which strict<4 is intended to apply under the current ratio and references; clarify reference-population alignment and whether any explicitly justified support/denominator handling is intended. Current inputs are reproduced faithfully, but the PDF supplies no alternative numerical rule. No cutoff, clipping, absolute transformation or criterion workaround is recommended or applied here. Runtime positive-sensitivity admissibility and distribution-family approvals remain separate unresolved issues.

### 8. Files and verification

Nine requested outputs only. scenario_statistics.csv and methodology_reconciliation.csv contain numerical/evidence results; weather_time_stability.csv contains reliability observations only; verification.json contains exact summaries, causes, examples, PDF hash and stop status. pairwise_scenario_distances.csv, candidate_combination_tests.csv, accepted_groups.csv and rejected_groups.csv intentionally have headers only.

The PDF text was extracted using pypdf; the decisive strict-boundary table is explicitly present on page2. No PDF layout was modified. Verified counts, date limits, joins, absent combinations and strict threshold boundary (4.0 rejected). No production, freeze-registry, V1, checkpoint or replay edits; no model training/simulation or March17–31 analytical access. This is isolated analysis, not a new frozen methodology.
