# Academic recalibration decision summary

## 1. Why recalibration is needed

The supplied *Passenger Price Sensitivity and NYC Fare Calibration* document asks for a population-based sensitivity model, empirical distance demand, a base-fare mechanism and supported NYC fare bounds. These changes go beyond replacing a numerical constant. The current V1 uses a different historical ratio orientation, a positive absolute-value pool, a platform-protected acceptance threshold and seven pre-masked offers. The new document supplies several mathematical components but does not fully connect long-distance reference fare, sensitivity, maximum price and selected offer.

This analysis supplies evidence for academic decisions. It does not freeze V2, modify V1, load a learner, train, or alter simulation. All recalibration observations come from the already restricted Jan 1–Mar 15 cache. March 16 appears only as a labelled saved request-stream illustration. No March 17–31 analytical rows or full-period trip files were opened. Historical reference values and documents are reused as provenance, not recalculated from protected periods.

Two comparison scopes are reported. ARRAY_RANGE contains 7,946,921 observations with 1<=distance_km<75, enabling a like-for-like comparison with 148 bin proxies. ALL_SAFE retains all 8,692,819 cleaned Jan 1–Mar 15 trips and exposes effects hidden by the array range. Neither scope inherits historical Record-029 VALID status or T0 bounds. Original physical fields remain unchanged.

## 2. Formula orientation

For this analysis only, r_P=(P-P_base)/P_base, r_L=(L-L_base)/L_base, and new e = r_L/r_P. The historical ratio is r_P/r_L. On the same observation with the same references and both deviations finite/nonzero, their product equals 1. The maximum numerical error across the tested reference scenarios is 2.220446049250313e-16, with zero mismatches above 1e-12. This validates algebra, not a behavioural interpretation.

The current historical references differ from the new candidates, so taking a reciprocal of the old supported pool is not equivalent to recomputing new e. Absolute values would also discard sign. No absolute transformation is applied here. The saved historical epsilon is included only for source comparison in bounded extreme examples; a separately named same-reference reciprocal prevents confusing these quantities.

The new denominator is price, not distance. Historical exclusion of distances near L_base therefore cannot be inherited. New validity requires finite paired inputs and a nonzero price deviation. Exact-zero denominators are recorded separately rather than replaced by arbitrary constants. Near-zero denominators remain in all descriptive statistics and fits.

## 3. Array-a provenance

The existing half-kilometre fare CSV matches its checksum in the completed context audit. Its 148 lower-edge labels run 1.0–74.5; the represented interval is[1,75), not 148 exact trip distances. Counts sum 7,946,921 and weighted fare sum 177,647,049.04 USD. P_base_candidate is exactly 22.354198442390455 USD in the persisted calculation;22.3542 is the rounded document value. Raw preparation and fare aggregation were not rerun.

Actual within-bin mean distance was calculated from the permitted cache while checking count alignment. This is the only new bin-distance aggregation. Lower edge, midpoint and observed mean are distinct representations. The lower edge reproduces the document example; neither it nor the midpoint is automatically a true passenger distance. Bin mean fare is a conditional average, not a statutory tariff or individual price.

The price-near reference candidate uses the explicitly diagnostic ±1 USD window around the new price, restricted to the array range:346,880 observations give L_base=5.300620449409596 km and mean fare≈22.483206 USD. Windows±0.25/0.50/1/2 and the full safe population are separately reported. The ±1 choice borrows a historical diagnostic width; it is not a newly approved V2 definition. Full-safe ±1 mean distance is≈5.207588 km. No taxi-meter threshold is established.

## 4. Population weighting comparison

At P_base=22.354198442390455 and L_base 4.5, the primary results are:

| population | scope | finite_mass | mean | population_SD | median | negative_mass | zero_mass | undefined_mass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BIN_UNWEIGHTED | ARRAY_RANGE | 148.000000 | 2.313937 | 0.407451 | 2.398156 | 0.000000 | 1.000000 | 0.000000 |
| BIN_COUNT_WEIGHTED | ARRAY_RANGE | 7,946,921.000000 | 1.628232 | 0.579044 | 1.373563 | 0.000000 | 310,535.000000 | 0.000000 |
| TRIP_LEVEL_NEW_E | ARRAY_RANGE | 7,946,921.000000 | 1.427109 | 29.316258 | 1.065359 | 1,044,072.000000 | 0.000000 | 0.000000 |
| TRIP_LEVEL_NEW_E | ALL_SAFE | 8,692,819.000000 | 1.414919 | 29.609236 | 1.087483 | 1,105,611.000000 | 0.000000 | 0.000000 |


Unweighted bins allocate one vote to every distance interval, regardless of passenger volume. Count weighting instead assigns the bin proxy to its observed number of trips, but still suppresses within-bin variation. Trip-level ratios restore that variation and price-denominator instability. The ratio evaluated at mean fare/distance is not the mean of individual ratios.

| lower_km | upper_km | bin_N | trip_N | unweighted_bin_pct | count_weighted_pct |
| --- | --- | --- | --- | --- | --- |
| 1 | 5 | 8 | 5286079 | 5.405405 | 66.517322 |
| 5 | 10 | 10 | 1355140 | 6.756757 | 17.052390 |
| 10 | 20 | 20 | 872279 | 13.513514 | 10.976314 |
| 20 | 40 | 40 | 410413 | 27.027027 | 5.164428 |
| 40 | 60 | 40 | 21004 | 27.027027 | 0.264304 |
| 60 | 75 | 30 | 2006 | 20.270270 | 0.025242 |


Thus 1–5 km receives 5.405405% of equal-bin probability but 66.517322% of count-weighted probability. Conversely 60–75 km receives 20.270270% versus 0.025242%. These are radically different implied populations. If the modelling unit is passengers, frequency weighting has a clearer population interpretation than equal bins, but it does not establish that a bin-average ratio is a valid individual sensitivity. That remains an academic choice.

Statistics use population SD. Epsilon quantiles use the left inverse empirical CDF consistently with weights; fare quantiles use linear interpolation. For bin weighting, Kish effective N describes the concentration of 148 bin weights; it is not evidence of millions of independent epsilon measurements. Trip counts and distinct support points are separately retained in fit tables.

## 5. Zero and extreme handling

At the exact candidate price, no observed trip has r_P=0. There are consequently no observed nonzero/0 or 0/0 cases in the evaluated trip populations. At L_base 4.5 the lower-edge bin at 4.5 has e=0, representing 310,535 weighted observations; no actual physical trip equals that exact kilometre reference. This zero is a representation effect. Using a midpoint or observed mean instead creates a negative value in that bin. An interpolated synthetic point(P_base,L_base) would be 0/0 and requires a convention; none was inserted into the sample.

For ALL_SAFE observations, price gaps within$0.01/$0.05/$0.10/$0.25/$0.50/$1 contain 858/4,457/10,414/116,921/212,606/353,811 rows. These cumulative counts overlap and must not be added. Relative bounds equal each dollar tolerance divided by 22.354198442390455. The smallest price gap is approximately$0.00419844239. Resolution evidence, not arbitrary epsilon thresholds, motivates these diagnostics; no rows were excluded by them.

The matched trip-level distribution ranges approximately−15,450.17 to 17,161.44. A saved example at fare 22.36 USD and distance 24.542496 km has e 17,161.442304 because r_P≈0.00025953. Such cases can be numerically extreme while satisfying existing source cleaning. They are not declared invalid. The bounded example file preserves source-row IDs, timestamps, both deviations and historical values. It does not establish complete raw-record integrity or causal sensitivity.

The rule “if e=0, price=P_base” is a piecewise simulation convention. It cannot define 0/0 or justify a near-zero exclusion. New denominator treatment, signs and any zero mass must be agreed before a final sampler is built.

## 6. Distribution fits

All fits use the full observation masses through exact weighted sufficient statistics or numerical likelihood solutions; no large-population random subsample was fitted. Positive families use fixed location 0. Normal is the unrestricted baseline. Fits are made separately for each L_base and distance representation; historical T0 support is never used.

There are two explicitly different fit targets. SIGNED_COMPLETE retains all finite values. POSITIVE_COMPONENT_DIAGNOSTIC conditions on e>0, reports the excluded negative/zero mass, and does not claim to model the full population. No absolute transformation, shift or silent deletion is used. Gamma/lognormal/Weibull fitting is not attempted on incompatible negative support; zero-boundary cases require a separate modelling decision. Exponential can evaluate zero with finite density, but does not supply a structural point mass.

| population | sign_treatment | family | KS | AIC |
| --- | --- | --- | --- | --- |
| BIN_UNWEIGHTED | POSITIVE_COMPONENT_DIAGNOSTIC | weibull | 0.120167 | 103.410073 |
| BIN_UNWEIGHTED | SIGNED_COMPLETE | normal | 0.112529 | 158.246429 |
| BIN_COUNT_WEIGHTED | POSITIVE_COMPONENT_DIAGNOSTIC | lognormal | 0.385185 | 8,781,924.607886 |
| BIN_COUNT_WEIGHTED | SIGNED_COMPLETE | normal | 0.327434 | 13,868,353.757171 |
| TRIP_LEVEL_NEW_E | POSITIVE_COMPONENT_DIAGNOSTIC | lognormal | 0.109105 | 22,926,243.362714 |
| TRIP_LEVEL_NEW_E_ALL_SAFE | POSITIVE_COMPONENT_DIAGNOSTIC | lognormal | 0.125208 | 24,586,281.621426 |
| TRIP_LEVEL_NEW_E | SIGNED_COMPLETE | normal | 0.402070 | 76,244,048.142157 |
| TRIP_LEVEL_NEW_E_ALL_SAFE | SIGNED_COMPLETE | normal | 0.403947 | 83,573,198.131588 |


For the 4.5-km lower-edge case, the lowest positive-component AIC is Weibull for equally weighted bins and lognormal for count-weighted bins and trip-level observations. These are within-scenario comparisons, not a universal family recommendation. The full signed trip population leaves normal as the only compatible tested parametric baseline, with a large KS discrepancy around 0.40. That is not evidence that normal is a good model; it is a limitation of the candidate support set. Empirical resampling reproduces the in-sample distribution exactly, so its zero in-sample KS is tautological and not an out-of-sample success.

AIC/BIC and likelihoods must only be compared for the same population/component. Frequency-weighted bin scores are descriptive pseudo-likelihood scores; repeated bin proxies do not create independent observations. Effective-N versions are supplied to expose this limitation. KS statistics measure fitted-CDF discrepancy. No unadjusted p-value is reported: parameters were estimated from these data, bins are not IID random samples, and trips may be dependent. No formal goodness-of-fit rejection or acceptance is claimed without an appropriate resampling/held-out procedure.

Histogram, CDF and Q–Q panels are saved for the reference scenarios. P1–P99 plotting windows are labelled display restrictions; full tails remain in likelihoods and statistics. Every representation has numerical Q–Q diagnostics. No single family clearly dominates across unresolved populations, representations and support conventions.

## 7. Distance and bin-count cutoffs

| scenario | retained_trips | bins_retained | largest_usable_endpoint_km | P_base | mean | population_SD |
| --- | --- | --- | --- | --- | --- | --- |
| LOWER_1_UPPER_75 | 7946921 | 148 | 75.000000 | 22.354198 | 1.427109 | 29.316258 |
| LOWER_1.5_UPPER_75 | 6967155 | 147 | 75.000000 | 24.203710 | -0.470870 | 156.295579 |
| LOWER_2_UPPER_75 | 5974083 | 146 | 75.000000 | 26.360795 | 0.674070 | 183.272163 |
| LOWER_1_EXISTING_100_MILES | 7948380 | 304 | 161.000000 | 22.396290 | 1.554960 | 33.223909 |
| MIN_50_INDIVIDUAL | 7946674 | 142 | 74.000000 | 22.349247 | 1.451247 | 111.604860 |
| MIN_50_CONTIGUOUS | 7946238 | 134 | 68.000000 | 22.340146 | 0.758230 | 599.163550 |
| MIN_100_INDIVIDUAL | 7945256 | 121 | 62.000000 | 22.321677 | 1.339097 | 53.321943 |
| MIN_100_CONTIGUOUS | 7945146 | 120 | 61.000000 | 22.319579 | 1.483615 | 198.156940 |


Lower bounds 1/1.5/2 km retain 7,946,921/6,967,155/5,974,083 trips, respectively. The existing allowed 100-mile range is used solely as a sensitivity reference, not a proposed 100-km rule. Adding distances>=75 km brings only 1,459 safe records; their small mass does not imply they are invalid. A final half-kilometre label can end at 161 km, while the actual physical cap remains 160.9344 km and observed maximum 160.82174592 km.

Individual 50-count filtering removes 6 bins/247 trips; contiguous filtering stops before 68 km and removes 14 bins/683 trips. Individual 100-count filtering removes 27 bins/1,665 trips; contiguous filtering stops before 61 km and removes 28 bins/1,775 trips. The 61.5 bin has 110 trips, so dropping sparse bins cannot be equated with a single upper cutoff.

The table above recomputes P_base within each scenario, showing the combined population/reference effect. Small price changes can move the denominator close to a common fare. To isolate filtering, a second table keeps exact P_base and L_base 4.5 fixed: SDs change much less (about 29.25–32.39 across most filters). For example, contiguous 50 filtering has SD 599.16 with its recomputed price but 29.28 with fixed references. This is not evidence that the cutoff itself creates anomalous trips or that minimum-SD reference selection is justified.

## 8. Reference-value comparison

| candidate | representation | mean | population_SD | negative_units | zero_units |
| --- | --- | --- | --- | --- | --- |
| A_LOWER_EDGE | LOWER_EDGE | 2.313937 | 0.407451 | 0 | 1 |
| A_LOWER_EDGE | CENTRE | 2.321836 | 0.620608 | 1 | 0 |
| A_LOWER_EDGE | ACTUAL_MEAN | 2.323085 | 0.609254 | 1 | 0 |
| B_INTERPOLATED | LOWER_EDGE | 2.251705 | 0.347216 | 0 | 0 |
| B_INTERPOLATED | CENTRE | 2.259404 | 0.496618 | 1 | 0 |
| B_INTERPOLATED | ACTUAL_MEAN | 2.260621 | 0.486735 | 1 | 0 |
| C_PRICE_NEAR_PM 1 | LOWER_EDGE | 1.942960 | 0.713889 | 1 | 0 |
| C_PRICE_NEAR_PM 1 | CENTRE | 1.949665 | 0.491188 | 1 | 0 |
| C_PRICE_NEAR_PM 1 | ACTUAL_MEAN | 1.950725 | 0.499614 | 1 | 0 |


The 4.5 candidate is the nearest lower-edge bin, with observed mean fare≈21.983204 USD, not exactlyP_base. The 4.616983790655043 candidate interpolates that curve toP_base. It does not identify a taxi-meter base distance. The 5.300620449409596 candidate is a conditional physical-distance mean, subject to a diagnostic price-window choice. Midpoint and actual-mean representations alter signs as well as dispersion, so lower-edge epsilon moments are not representation invariant.

| comparison | mean_abs_e_difference | max_abs_e_difference | median_abs_e_difference | sign_changes |
| --- | --- | --- | --- | --- |
| DOCUMENT_ROUNDED | 0.000082 | 5.728764 | 0.000000 | 0 |
| HISTORICAL | 2.796085 | 39,358.243918 | 0.080872 | 154011 |


Rounded 22.3542 differs from exact P_base by only≈1.56e-6 USD, yet the largest full-safe e difference is≈5.73 because of small denominators; median differences are tiny. Using historical 21.34586956773507 changes the denominator more substantially and flips 154,011 signs at fixedL_base. Exact arithmetic with separately rounded display values is a reproducible interpretation, not a newly frozen decision.

## 9. Fare-bound candidates

| scenario | N | P0.1 | P0.5 | P1 | P 2.5 | P5 | P95 | P97.5 | P99 | P99.5 | P99.9 | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALL_SAFE | 8692819 | 3.000000 | 4.400000 | 4.400000 | 5.100000 | 5.800000 | 58.190000 | 70.000000 | 78.600000 | 91.230000 | 135.300000 | 2,555.200000 |
| LOWER_1_UPPER_75 | 7946921 | 3.000000 | 5.800000 | 5.800000 | 6.500000 | 7.200000 | 59.700000 | 70.000000 | 78.600000 | 91.710000 | 131.800000 | 2,084.100000 |


| q_lower | q_upper | lower | upper | pct_clipped_low | pct_clipped_high | pct_unaffected |
| --- | --- | --- | --- | --- | --- | --- |
| 0.001000 | 0.999000 | 3.000000 | 135.300000 | 0.013540 | 0.099887 | 99.886573 |
| 0.005000 | 0.995000 | 4.400000 | 91.230000 | 0.497054 | 0.499987 | 99.002959 |
| 0.010000 | 0.990000 | 4.400000 | 78.600000 | 0.497054 | 0.997340 | 98.505606 |
| 0.025000 | 0.975000 | 5.100000 | 70.000000 | 1.279619 | 1.463599 | 97.256782 |
| 0.050000 | 0.950000 | 5.800000 | 58.190000 | 2.863329 | 4.997171 | 92.139500 |


These bounds are empirical diagnostics on recorded TLC fare_amount. Ties make actual excluded percentages differ from nominal quantile tails. The$0.01 minimum,$7.52 illustrative value,$207 bin-mean scale and$2,555.20 maximum are not automatically operational fare limits. Trip-level quantiles and bin-mean ranges are separate artifacts, with all candidate distance/count filters evaluated.

Clipping the seven example global offers under all 135 combinations of candidate empirical bounds and old/exact/rounded base price leaves 7 distinct offers: zero collapsed action pairs. This finding concerns these global arithmetic candidates only. It says nothing about collapse under the missing distance-dependent price equation. Such clipping cannot be simulated or validated by inventing that equation.

## 10. Pricing-contract gap

The PDF explicitly states e=r_L/r_P; L_effective=max(L_observed,L_base); a base-price branch for short trips; e=0 implies price P_base; P_action=P_base×alpha; and NYC lower/upper clipping. It does not fully specify how a long-distance fare and epsilon-derived preference combine with P_max and P_action. Source operations and page references are classified in `pricing_contract/source_document_contract.csv`.

**PRICE_GENERATION_FORMULA_READY_FOR_IMPLEMENTATION=NO.** The missing composition is material: multiplying a distance-dependent reference differs from multiplying global P_base, and clipping may change both effective actions and response. No equation is supplied by this analysis. The current seven factors remain examples for comparison, not final V2 actions. Old global offers span$18.143989–$24.547750; the new exact price gives$19.001069–$25.707328. Distance-band coverage tables quantify the limited envelope without asserting a replacement.

## 11. Acceptance and state implication

For ordered prices c_j=a_jP_base, the current mask m_j=1[c_j<=P_accept] reveals a threshold interval through the number of feasible arms. The Q-network does not directly observe epsilon or distance, but the policy and Bellman maximization use this passenger-specific mask. A minimum-protected threshold guarantees at least the lowest arm is feasible.

Removing the mask while retaining the 13D state leaves two passengers with identical public context but different independent sensitivities indistinguishable to the pricing policy. Classification: **UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. Aggregate contextual prediction may still be possible; individual threshold observability is not. This does not authorize state expansion.

A post-action rejection design needs explicit outcome, reward, dispatch-bypass, chronological replay and next-request semantics. Existing zero reward for accepted-unmatched is not an approved rejection penalty. Rejected offers must not silently enter successful-dispatch fare statistics or commitments. No reward value or new replay schema is chosen here.

## 12. Request-generator implication

The baseline already preserves empirical distance by resampling intact January trips conditional on forecast-driven origin counts. Independent draws from the pooled array marginal could break OD-distance-duration consistency and change energy, routing and fleet dynamics. It is therefore not an automatic requirement.

The saved March 16 illustration contains 2,838 requests;2,511 lie in[1,75),327 are below 1 km and none are>=75 km. Conditional on the common range, half-kilometre total variation is 0.131465, binned KS is 0.120322, and Jensen–Shannon distance is 0.128700. Its 1–5 km share is 55.396256%, versus 66.517322% in array a. Thus this fixture is not an exact match, although both are empirically grounded. A short nighttime development fixture cannot certify the full generator distribution or select a new calibration rule.

**ARRAY_A_DISTANCE_PROBABILITIES_NEEDED_FOR_RUNTIME=ACADEMIC_DECISION_REQUIRED.** The smallest defensible baseline is to preserve existing joint observations until the target marginal and coupling requirements are agreed. No generator, physical distance, duration, demand forecast or geometry is changed.

## 13. Decision table

| decision | readiness | academic_approval_required |
| --- | --- | --- |
| EPSILON_ORIENTATION | EVIDENCE_READY_FOR_FREEZE | YES |
| EPSILON_POPULATION | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| EPSILON_SIGN | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| EPSILON_ZERO_RULE | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| EPSILON_DISTRIBUTION | MORE_ANALYSIS_REQUIRED | YES |
| LOWER_DISTANCE_CUTOFF | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| UPPER_DISTANCE_CUTOFF | EVIDENCE_READY_FOR_FREEZE | YES |
| MIN_BIN_COUNT | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| SPARSE_BIN_SEMANTICS | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| P_BASE_PRECISION | EVIDENCE_READY_FOR_FREEZE | YES |
| L_BASE | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| NYC_LOWER_BOUND | MORE_ANALYSIS_REQUIRED | YES |
| NYC_UPPER_BOUND | MORE_ANALYSIS_REQUIRED | YES |
| PRICE_GENERATION_FORMULA | BLOCKED_BY_MISSING_FORMULA | YES |
| ACTION_FACTORS | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| ACTION_COUNT | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| ACCEPTANCE_SEQUENCE | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| REJECTION_REWARD | ACADEMIC_INTERPRETATION_REQUIRED | YES |
| REQUEST_GENERATOR | ACADEMIC_INTERPRETATION_REQUIRED | YES |


Readiness counts: {'EVIDENCE_READY_FOR_FREEZE': 3, 'ACADEMIC_INTERPRETATION_REQUIRED': 12, 'MORE_ANALYSIS_REQUIRED': 3, 'BLOCKED_BY_MISSING_FORMULA': 1}. “Evidence ready” does not mean approved. “More analysis” identifies remaining validation/source needs after defining the target. One missing-formula decision blocks implementation directly; academic interpretation gates remain equally binding. The full CSV records options, numerical evidence, tradeoffs, architecture/training consequences and non-final interpretations for every decision.

## 14. Exact questions requiring academic freeze

1. Confirm the new distance/price ratio as the replacement analytical orientation; how should negative values be interpreted?
2. Is the passenger population represented by equally weighted bins, count-weighted bin proxies, or individual trips?
3. Is bin distance a lower edge, centre or observed mean when constructing epsilon?
4. What conventions govern exact/near-zero price denominators and 0/0, and is a structural zero mass retained?
5. Which sign/support population should be used for distribution fitting, and what validation is required before selecting a family?
6. Which lower and upper physical ranges apply, and are they calibration-only or runtime filters?
7. Does a minimum count remove individual bins or define a contiguous range, and is the threshold 50 or 100?
8. Is exact P_base retained with rounded presentation, and which L_base definition is intended?
9. Is taxi-meter L_flat distinct from reference L_base, and what evidence defines it?
10. What fare-component and empirical evidence justify NYC lower and upper limits?
11. What is the complete piecewise reference-fare/P_max/action/generation equation, including zero and short-distance cases?
12. Which factors/count and post-clipping action identities follow from that equation?
13. Does passenger response remain a preselection constraint or become an explicit post-action event, and what information must the policy observe?
14. If rejection occurs, what reward, replay, dispatch and operational-statistics treatment applies?
15. Should the existing joint request generator remain, or must it target a new distance marginal while preserving physical consistency?

No answer is silently selected. Any V2 implementation, checkpoint initialization or training requires a subsequent explicit decision and authorization. Historical Record-029, current V1, replay, CNN, routing and protected evaluation remain unchanged.
