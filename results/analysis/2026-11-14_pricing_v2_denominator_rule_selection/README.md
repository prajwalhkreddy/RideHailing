# Denominator rule selection: methodology audit

## Scope and source precedence

This is an offline diagnostic comparison, not a runtime implementation or automatic freeze. Latest input: `notebooks/plan/answers1.pdf`, pages 1–3, questions Q1–Q7. The source was read using PDF text extraction; mathematical notation is normalized below because PDF text ordering separates some equation fragments. No visual-layout claims are made. The latest answers govern the questions they address; their references to earlier recordings have not been independently reverified here.

Q7 supersedes the earlier explanatory PDF's hard SD<4 acceptance wording and the resulting all-scenarios-fail interpretation. SD<4 is now only an internal diagnostic, with N>=50/100 reported separately. Q1–Q4 supersede treating every finite small-denominator ratio as a usable behavioural observation. Q5 rules out replacing passenger heterogeneity with a single regression estimate. Q6 resolves simulation sign support as epsilon>=0 without taking absolute values. Q7 prioritizes the pooled main experiment over conditional weather/hour experiments. Earlier artifacts remain intact as historical evidence.

## Unchanged calculation contract and approval limitation

P_base=P_norm=22.354198442390455 USD; L_base=4.616983790655043 km. These are the exact existing calculation references, not newly estimated values. Existing contract and hourly-audit records describe reference approval as pending/provisional; this audit does not silently promote them to fully approved constants. Results are conditional on these unchanged values.

Source: `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet`. Fields: pickup_timestamp, fare (processed TLC fare_amount, USD), trip_distance (miles). Convert miles to km with 1.609344. Existing positive fare and 0<distance<=100-mile source rules are preserved; the current analytical filter is 1.5<=distance_km<75. Calibration is Jan1 inclusive to Mar16 exclusive, 2026. The resulting source N is 6,967,155. Weather is an hourly many-to-one join from processed monthly files with the same date predicate. No raw preparation, additional source cleansing, or protected-date observations are used.

Notation is unambiguous:

- delta_P_abs_usd = fare - P_base. Despite the name, this is a **signed dollar deviation**; abs(delta_P_abs_usd) is its magnitude.
- r_P = (fare-P_base)/P_base; r_L = (distance_km-L_base)/L_base.
- epsilon = r_L/r_P; r_P==0 is undefined. Zero r_L with nonzero r_P yields zero.

No source row is deleted or relabelled as an invalid taxi trip. Each candidate first marks denominator failures unresolved, then audits resolved negative ratios, then constructs epsilon>=0. No absolute-value transformation of epsilon, winsorization, support cap, fitting, clustering, or simulation occurs. All moments use population SD; quantiles use linear interpolation; skewness is the population standardized third central moment. No zero or undefined ratios occur in this particular source population. Baseline is the unfiltered positive-valid comparison, not a proposed production rule.

## Price precision versus economic resolution

Stored fares are cent-aligned; minimum observed adjacent unique-fare spacing is $0.01. Previously measured gap counts: $0.01:11,262; $0.02:574; $0.03:243; $0.04:139; $0.05:100. These count adjacent levels in sorted unique fares, not trip frequencies or consecutive meter ticks. They cannot establish an economic identification threshold.

Q3 describes approximate $0.50–$0.70 meter/economic increments and one-to-two effective increments around $0.50–$1.00. Those guidance amounts are not inferred from the cent precision. Their differences from $0.01 are $0.49/$0.69/$0.99. Literal two $0.70 ticks would be $1.40; the guidance's approximate $0.50–$1.00 range is not an exact equivalence to every possible meter increment. No extra $1.40 candidate is introduced. This audit does not independently certify a current legal tariff or claim every observed fare contains a separately identifiable surcharge. The reconciliation CSV records dollar differences for each concept and the empirical gap frequencies.

## Candidate construction and population accounting

A retains abs(delta_P_abs_usd)>=0.50; B retains >=1.00; C retains abs(r_P)>=0.05. The two dual rules intersect C with the $0.50 and $1.00 conditions respectively. Algebraically their effective dollar floor is max(meter_floor,0.05*P_base). Here 0.05*P_base=1.1177099221195228, exceeding $0.50 by $0.6177099221195228 and $1.00 by $0.1177099221195228. Both dual masks are exactly identical to C in the data. The inverse relative denominator is capped at 20 by C; epsilon itself is **not** capped at 20 because r_L varies.

All boundaries are inclusive. Denominator-excluded and final-retained percentages use the original 6,967,155. Negative counts are disjoint from denominator-unresolved counts; the CSV gives percentages of both source and denominator-resolved populations. Each partition reconciles to source N. Negative ratios within unresolved rows are not double counted.

| rule_id | denominator_excluded_N | denominator_excluded_pct | negative_excluded_N | final_nonnegative_N | final_retained_pct |
| --- | --- | --- | --- | --- | --- |
| BASELINE | 0 | 0.000000 | 991502 | 5975653 | 85.768911 |
| A | 206403 | 2.962515 | 894435 | 5866317 | 84.199605 |
| B | 341715 | 4.904656 | 839507 | 5785933 | 83.045849 |
| C | 353234 | 5.069989 | 834708 | 5779213 | 82.949396 |
| DUAL_050 | 353234 | 5.069989 | 834708 | 5779213 | 82.949396 |
| DUAL_100 | 353234 | 5.069989 | 834708 | 5779213 | 82.949396 |

## Pooled distribution stability

| rule_id | mean | median | SD | P95 | P99 | maximum | skewness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | 2.746274 | 1.184555 | 22.483278 | 6.225279 | 26.347464 | 16628.981005 | 176.647721 |
| A | 1.946258 | 1.169291 | 2.599478 | 5.164117 | 11.531349 | 533.492211 | 16.532989 |
| B | 1.815636 | 1.155919 | 2.023622 | 4.733401 | 9.027503 | 286.512406 | 18.973472 |
| C | 1.807321 | 1.154356 | 1.990089 | 4.705542 | 8.872682 | 286.512406 | 19.527461 |
| DUAL_050 | 1.807321 | 1.154356 | 1.990089 | 4.705542 | 8.872682 | 286.512406 | 19.527461 |
| DUAL_100 | 1.807321 | 1.154356 | 1.990089 | 4.705542 | 8.872682 | 286.512406 | 19.527461 |

Full P01/P05/P25/P50/P75/P95/P99/P99.5/P99.9 and all baseline changes are in global_distribution_comparison.csv. A retains 98.1703% of the baseline positive population; B 96.8251%; C/dual 96.7127%. The corresponding source-retention percentages are lower because negative ratios are also excluded. Thus the source is not described as almost entirely retained without qualifying which stage/population is meant.

A reduces SD by 88.44% but mean by 29.13%; B by 91.00% and 33.89%; C by 91.15% and 34.19%, respectively. Medians change by only -1.29%, -2.42%, -2.55%. Median stability does not mean the full distribution is unchanged. Large right tails remain: B/C maximum286.5124 and skewness about19, despite SD near2. These are unresolved heterogeneity/source-interpretation questions, not automatic invalidity labels or justification for an upper cap.

B to C removes another 6,720 nonnegative observations (0.1161% of B), with mean change -0.458%, median -0.135%, SD -1.657%, and P99 -1.715%. This is local stability between two nearby thresholds, not proof of a universal plateau.

## Ratio-bias sanity benchmark

Use an origin-constrained least-squares relationship in normalized deviations: beta=sum(r_P*r_L)/sum(r_P^2). The raw distance/fare version has km/USD units and must be multiplied by P_base/L_base before comparison with dimensionless epsilon. Both are recorded. This follows the reference-centered slope in Q5; it is not an intercept-fitted causal demand regression or a replacement sensitivity distribution.

The benchmark is computed separately on the same denominator-resolved signed population and on the same nonnegative population as each set of individual ratios. Representative cells are selected by fixed names rather than optimizing agreement: Clear12, Light Rain01, Fog12, Heavy Rain05. Rain12 has no source observations and is omitted, never imputed. The CSV explicitly labels population and group.

| rule_id | mean_epsilon | median_epsilon | normalized_origin_slope | mean_minus_slope |
| --- | --- | --- | --- | --- |
| BASELINE | 2.746274 | 1.184555 | 1.821174 | 0.925100 |
| A | 1.946258 | 1.169291 | 1.821074 | 0.125184 |
| B | 1.815636 | 1.155919 | 1.820810 | -0.005175 |
| C | 1.807321 | 1.154356 | 1.820784 | -0.013463 |
| DUAL_050 | 1.807321 | 1.154356 | 1.820784 | -0.013463 |
| DUAL_100 | 1.807321 | 1.154356 | 1.820784 | -0.013463 |

The positive mean–slope gap falls from0.9251 to0.1252 then approximately-0.0052/-0.0135. This is consistent with reducing near-denominator upward tail influence; it is not a statistical proof that the cleaned mean is unbiased. The slope is a denominator-squared-weighted mean of individual ratios and weights trips differently. Sign conditioning is itself selection. In the signed population the mean is already below the slope and moves farther below it as filtering strengthens, so a claim of universally corrected upward bias would be false. Median-to-slope differences remain material. Representative cells can also behave differently; their full values remain visible.

## Secondary Weather x Hour diagnostics

| rule_id | supported_cells | cells_N_ge50 | cells_N_ge100 | median_cell_SD | P90_cell_SD | maximum_cell_SD | cells_SD_lt4 | cells_SD_ge4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASELINE | 211.000000 | 211.000000 | 210.000000 | 17.458141 | 40.411140 | 376.971680 | 4.000000 | 207.000000 |
| A | 211.000000 | 211.000000 | 210.000000 | 2.636840 | 3.926153 | 5.245465 | 194.000000 | 17.000000 |
| B | 211.000000 | 211.000000 | 210.000000 | 2.000567 | 2.761314 | 3.785245 | 211.000000 | 0.000000 |
| C | 211.000000 | 211.000000 | 210.000000 | 1.977162 | 2.720387 | 3.582856 | 211.000000 | 0.000000 |
| DUAL_050 | 211.000000 | 211.000000 | 210.000000 | 1.977162 | 2.720387 | 3.582856 | 211.000000 | 0.000000 |
| DUAL_100 | 211.000000 | 211.000000 | 210.000000 | 1.977162 | 2.720387 | 3.582856 | 211.000000 | 0.000000 |

All211 observed cells remain. No missing combinations are fabricated. Under C the only cell below100 is Heavy Snowfall hour03, N=80. Every cell meets50. A has17 SD>=4 cells, B/C have none; this is descriptive and not the selection objective. A future conditional model could use pooled fallback for an insufficient-N or high-SD cell; no fallback or minimum-N policy is installed here.

## Negative-epsilon audit and limits

Before denominator screening, 991,502 ratios (14.2311% of source) are negative. Of these,413,113 (41.6654%) have fare above P_base and distance below L_base;578,389 (58.3346%) have the opposite crossing. Under C,834,708 remain negative (11.9806% of original source;12.6205% of resolved rows):343,987 (41.2105%) short/high-fare crossings and490,721 (58.7895%) long/low-fare crossings. No negatives are converted to magnitudes.

At baseline negative median fare=$21.46, median distance=4.828032km, median abs(delta_P_abs_usd)=$3.324198. Under C those medians are $20.50,4.828032km,$4.094198; median abs(r_L)=0.208745. Negativity therefore persists well beyond the immediate price dead zone and is not confined to arbitrarily close L_base crossings. Fare/distance ranges and denominator proximity by weather and hour appear in the audit CSV.

Under C, negative rates within resolved weather populations range from 21 Snow Shower: 11.866% to 16 Heavy Snowfall: 25.189%; hourly rates range from hour16: 8.285% to hour3: 19.732%. These conditional rates, alongside shares of all negatives, avoid confusing large weather populations with exceptional negative propensity.

The cache has no surcharge components, trip duration or traffic exposure. Their causal contribution is **not identifiable** from fare, distance, time and weather alone. Fare is fare_amount, not total_amount; attributing all high short-trip fares to itemized surcharges would be unsupported. Short/high-fare cases are compatible with time-meter or other fare heterogeneity, but this is not confirmation. The source guidance's suggestion to confirm traffic/surcharge anomalies cannot be fulfilled with these columns. Negative observations remain valid historical records; their exclusion is from the candidate simulation sign support only. Representative examples retain raw timestamp, fare, source miles, converted km and normalized deviations, selected deterministically as most-negative, nearest-price and median-ratio-nearest for each rule.

## Methodology already resolved

- Numerically unresolved ratios are distinct from valid source trips.
- A meaningful denominator screen precedes any secondary tail treatment.
- Heterogeneous individual epsilon values remain the simulation population; regression is validation only.
- Simulation candidates use epsilon>=0 after auditing negatives.
- The initial/main experiment is pooled; weather/hour modelling is secondary.
- SD<4 is an internal stability diagnostic, not a hard methodology gate.

## Still to be selected

**THRESHOLD DECISION STILL REQUIRES REVIEW.** The strongest distinct candidates are B ($1.00) and C/dual (5%, $1.1177099221195228). C/dual most directly implements the latest combined economic-plus-relative guidance. B preserves slightly more data and is marginally closer to the global positive slope. Both have similar central statistics and secondary stability; three distinct thresholds do not independently establish the economically correct identification boundary. The cent grid cannot settle this choice. A improves tail behaviour but leaves a larger positive mean–slope gap and more residual dispersion.

No candidate is selected solely from SD<4 counts or minimum SD, and no final threshold is frozen. The review must balance economic resolution, retention, mean/median/SD change, residual tail influence, slope comparison and conditional robustness. Approval status of the existing numerical references also remains as recorded. No fitting, upper-support selection or runtime follow-on is executed.

## Files and validation

- notation_contract.json: exact unchanged references, fields, units, dates, formula and approval limitation.
- fare_resolution_reconciliation.csv: stored precision, empirical spacings, guidance increments and dollar differences.
- candidate_population_comparison.csv: all five candidates plus labelled baseline, with disjoint population accounting and final comparison metrics.
- global_distribution_comparison.csv: full quantiles/moments and baseline changes.
- ratio_bias_validation.csv: global and representative-group normalized/raw slopes, signed and nonnegative populations.
- weather_hour_secondary_diagnostics.csv: observed-cell statistics and per-rule summaries; quality flags only.
- negative_epsilon_audit.csv: overall, weather, hourly and crossing distributions with explicit percentage denominators.
- representative_negative_observations.csv: deterministic raw examples, not invalidity labels.
- verification.json: source hashes, date bounds, partition checks, dual-rule equivalence and scope verification.

All source hashes are unchanged. Every denominator/sign partition reconciles to6,967,155; both dual masks exactly match C. Source dates are Jan1–Mar15 only; weather reads use the same predicate. No production, V1, runtime, checkpoint, replay or registry writes; no clustering, model fitting or training. Outputs are confined to this new analysis folder. Historical analysis and signed records remain intact.
