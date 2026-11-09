# Academic Review Follow-up: Passenger-Sensitive Pricing V1

## 1. Objective

This report supplies the additional descriptive evidence requested after review of Passenger-Sensitive Pricing V1. It examines observed fare–distance structure, the signed historical sensitivity distribution and its positive transformation, acceptable-price behaviour under the unchanged formula, counterfactual passenger acceptance, and empirical coverage of the existing action prices. It does not train or evaluate a new policy. Neither action redesign nor a different acceptance mechanism is implemented. Existing Episode25 performance remains a separate result, not a result of this analysis.

The distinction between measured data, deterministic formula illustrations, and simulator-derived development observations is central. Fare and distance summaries are descriptive properties of recorded completed trips. Historical epsilon is a derived variable under Record-029, not a measured individual willingness to pay. Same-distance price examples are controlled formula evaluations using empirical quantiles. Counterfactual acceptance applies the existing deterministic rule to saved development requests; it is not an estimate of real passenger response to interventions.

## 2. Data and protected split

The calibration population contains **8,692,819 cleaned Jan1–Mar15 trips**. The Parquet read used the predicate `2026-01-01 <= pickup_timestamp < 2026-03-16`; no full-period DataFrame was loaded. The selected fields come from the authoritative Record-029 table, which retains the cleaned source rows including rows with unresolved epsilon. Fare-distance analyses retain all these rows; signed sensitivity additionally requires VALID, finite, nonzero epsilon. The source price is **TLC fare_amount**, in USD, not an assumed all-in passenger payment. Source trip_distance is miles and is multiplied by exactly 1.609344 before all km bins and plots.

March16 contributes only the saved Episode25 00:00–02:00 export, containing 2,838 requests. No simulator replay or checkpoint loading was necessary for this task. March17–31 was excluded from all analysis selections. Frozen P_base and L_base retain their previously approved full-cleaned-Jan–Mar provenance; this is an existing reference exception, not a new recalibration with protected dates. The restricted population is used to compare those references, not replace them.

The source filenames, date predicate and numerical checkpoints are recorded in `analysis_results.json`, `progress.json`, and `validation.json`. A restricted analysis cache makes the calculations resumable. Population counts reconcile with the previous V1 factor and sensitivity studies. Meeting example values were not treated as empirical measurements.

## 3. NYC fare-distance findings

Recorded fare ranges from **$0.01 to $2,555.20**, with median **$15.60**, mean **$21.352107**, and population SD **$17.480453**. Distance ranges from **0.01609344 to 160.82174592 km**, with median **3.02556672 km**, mean **5.548668 km**, and population SD **6.798634 km**. Full quantiles are in `fare_distance/population_statistics.csv`; no trimming was applied to these statistics.

The 0.5-km and 1-km tables preserve observed counts and fare quantiles in each populated bin. Intervals are lower-inclusive and upper-exclusive. Sparse long-distance bins remain visible; their quantiles should not be read as stable conditional fare estimates. The first 0–0.5-km bin has a median fare of $8.20, compared with $6.50 in 0.5–1 km and $7.90 in 1–1.5 km. Thus even the short-distance medians are not a single simple monotonic tariff description. No causal regression or tariff reconstruction is fitted.

The broad conditional medians increase substantially across the distance bands used for action review:

| lower_km | upper_km | N | median_fare | P5_fare | P95_fare |
| --- | --- | --- | --- | --- | --- |
| 0 | 5 | 6030518 | 12.100000 | 5.800000 | 27.200000 |
| 5 | 10 | 1355140 | 25.400000 | 17.200000 | 44.890000 |
| 10 | 15 | 555976 | 35.200000 | 25.500000 | 57.300000 |
| 15 | 20 | 316303 | 44.190000 | 33.250000 | 64.600000 |
| 20 | 30 | 311622 | 70.000000 | 42.500000 | 85.600000 |
| 30 | inf | 123260 | 70.000000 | 52.500000 | 147.900000 |

Fare per kilometre is reported as a descriptive ratio for positive distances. Very short distances can make that ratio large; it is not identified as a per-kilometre tariff. The cleaned population deliberately retains short trips and unusual positive fares under its existing rule. This report does not declare them invalid or introduce new exclusions.

## 4. Minimum-fare / L_flat evidence

**EMPIRICAL_FLAT_FARE_REGION = NOT_SUPPORTED** by these observations. The observed minimum, $0.01, appears in 283 trips, with median distance 7.58001024 km and maximum 40.3945344 km. It therefore does not identify a short-distance flat-price regime. Widening the fare band to $0.51 or $1.01 still selects very sparse, broadly distributed distances. This is a statement about the evidence, not a claim that no tariff or minimum-charge rule can exist elsewhere.

The requested candidate distance percentiles are shown below. They are descriptive quantiles of low-fare-like records, **not proposed cutoffs**:

| candidate | fare_upper | N | distance_median | L_flat_P90 | L_flat_P95 | L_flat_P99 | distance_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| exact_minimum | 0.010000 | 283 | 7.580010 | 18.095464 | 21.846845 | 28.630230 | 40.394534 |
| minimum_plus_0p50 | 0.510000 | 310 | 6.823619 | 17.960279 | 21.383354 | 28.355032 | 40.394534 |
| minimum_plus_1p00 | 1.010000 | 345 | 6.018947 | 17.725315 | 21.005158 | 27.848089 | 40.394534 |
| fare_P1 | 4.400000 | 109248 | 0.531084 | 2.816352 | 13.019593 | 25.403978 | 87.419566 |
| fare_P5 | 5.800000 | 450709 | 0.804672 | 1.174821 | 1.319662 | 15.111740 | 87.419566 |

The P5-fare band has P90/P95 distances around 1.17/1.32 km, but its P99 is approximately 15.11 km. The exact-minimum band's P95 is approximately 21.85 km. These changes show strong sensitivity to the definition of a low fare. A maximum observation would be particularly unsuitable as an automatic L_flat. The P1/P5 fare bands also contain more than nominal 1%/5% shares because inclusive boundaries include ties.

The retained source has fare_amount, not an itemized fare-component breakdown. Consequently this analysis cannot attribute unusual low fares to surcharges, negotiated fares, adjustments, recording errors, or specific payment components. Repeated fare levels and ties are visible, but rounding alone does not demonstrate a flat-distance mechanism. No statutory NYC minimum is asserted. **L_base == L_flat remains NOT_ESTABLISHED**; no d_min or L_flat is implemented.

## 5. Signed epsilon distribution

The VALID finite nonzero signed population is **8,685,488**. Mean is **0.640621**, population SD **7.106335**, median **0.762120**, and negative share **11.734355%**. The signed distribution is therefore not equivalent to a positive response parameter before transformation. Negative values are retained in the descriptive evidence and are not labelled erroneous.

The statistics file reports population and sample SD, sign counts, quantiles and counts with absolute epsilon below 0.001, 0.005 and 0.01. The analysis population excludes exact zero by the specified rule; reported zero counts describe that selected population. Full-support histograms use 0.05 and 0.10 bin widths and symlog count axes. A separate P1–P99 central view explicitly excludes tails only from that display; it does not alter any calculated population. The ECDF is displayed at 2,001 quantile positions and is not a fitted distribution.

| distribution | skewness | excess_kurtosis | P95_minus_median_over_median_minus_P5 | P99_over_P50 |
| --- | --- | --- | --- | --- |
| signed | -7.452200 | 9,263.308218 | 0.656636 | 10.193560 |
| absolute_pre_support | 57.658499 | 9,826.185201 | 3.365985 | 17.395589 |
| positive_supported_T0 | 7.486824 | 71.665103 | 3.086147 | 11.970947 |

Extreme moment values show why a mean and SD alone are insufficient. They do not prove that extreme records are invalid or that a specific parametric family should be adopted. The bounded example table contains actual source rows for the 20 largest positive, 20 most negative and 20 smallest absolute nonzero epsilon observations. Fare, distance and persisted relative deviations are included to expose the ratio structure. A source row can appear in more than one selection if definitions overlap; the selections are diagnostic sets, not population counts.


The leading saved examples make the ratio mechanism concrete:

| Selection | Fare USD | Distance miles | Relative price deviation | Relative distance deviation | Signed epsilon |
| --- | --- | --- | --- | --- | --- |
| largest_positive | 300.0 | 3.03 | 13.054241222079757 | 0.0039765459479701 | 3282.8090993751007 |
| most_negative | 110.43 | 3.01 | 4.173366193847559 | -0.0026503619460758 | -1574.64009775221 |
| smallest_absolute_nonzero | 21.35 | 24.0 | 0.0001935003046761 | 6.95228947285521 | 2.7832601825861228e-05 |

These examples are consistent with a ratio becoming large when its denominator is small or its numerator large, and becoming near zero when the numerator is small relative to the denominator. This algebraic description does not identify a source error.

## 6. Current V1 epsilon support

The absolute distribution before support has mean **1.414638**, population SD **6.993510**, and median **0.820126**. V1 first takes absolute values within the restricted VALID population, then applies inclusive positive P0.5–P99.5 bounds **[0.017809913104763053, 27.324599740032788]**. These bounds reproduce the saved V1 support exactly within the documented numerical check.

The supported population contains **8,598,805** observations, mean **1.095299**, population SD **1.817300**, and median **0.820123**. It remains right-skewed and heavy-tailed descriptively. **CURRENT_T0_SUPPORT_CONSISTENT_WITH_NEW_ANALYSIS = YES** means the construction and population reconcile; it does not independently establish causal or behavioural validity. The active sampling method remains TRUNCATED_EMPIRICAL_RESAMPLING, with replacement and duplicate frequencies preserved. No extra epsilon floor or fitted family is adopted.

Central interval coverage is explicitly measured in `central_interval_analysis.csv`. Mean ± SD bands are empirical intervals, not Gaussian probability assertions. For signed epsilon, literal membership in the positive T0 bounds is reported separately from membership by absolute magnitude. This avoids conflating positive support with a symmetric signed interval. T0 is symmetric in nominal tail probability, not in numerical distance from zero. Inclusive ties explain why the retained share is not exactly 99%.

## 7. Passenger acceptable-price behaviour

The unchanged expression is `P_raw_c = P_base + (P_base/epsilon_c)*((L-L_base)/L_base)`, followed by `P_accept_c = max(0.85*P_base, P_raw_c)`. P_raw_c, P_accept_c and P_offer are distinct quantities. The first is a raw formula output, the second is an effective acceptance threshold, and the third is an offered action price. An effective threshold can exceed the platform's largest selectable fare without changing the action set.

The distance/epsilon table uses distance P10/P25/P50/P75/P90 and interpretable 2, 5, 10 and 20 km values within observed support. Epsilon values are quantiles of the supported empirical positive population. These are formula illustrations, not invented observed passenger records. At a fixed distance below L_base, decreasing positive epsilon makes the negative adjustment larger in magnitude. Above L_base, it enlarges the positive adjustment. At L_base, the raw expression equals P_base regardless of epsilon. This follows directly from the displayed equation and explains the crossing in the curves.

The raw-preference table uses each supported historical trip's own epsilon and distance, matching the earlier calibration diagnostic. It is not independent runtime resampling. Mutually exclusive categories and the separate protection count are:

| category | N | percentage |
| --- | --- | --- |
| RAW_NONPOSITIVE | 1229215 | 14.295184 |
| RAW_POSITIVE_BELOW_PLATFORM_MIN | 4080228 | 47.451105 |
| RAW_WITHIN_PLATFORM_RANGE | 958180 | 11.143176 |
| RAW_ABOVE_PLATFORM_MAX | 2331182 | 27.110535 |
| EFFECTIVE_MIN_PROTECTION_APPLIED | 5309443 | 61.746289 |

The protection-applied row overlaps the first two categories and must not be added to their total. Applying a platform minimum does not erase negative raw outputs from the evidence. It also guarantees feasibility of the minimum arm for valid inputs, which must be considered when interpreting the absence of observed rejection.

## 8. Counterfactual acceptance curves

Every saved March16 request is paired with all seven current factors, yielding **19,866 request-action rows**. Only the offered price and the existing deterministic acceptance comparison are evaluated. No dispatch, vehicle response, policy retraining, or stochastic demand simulation occurs. For each request the same sampled epsilon and effective threshold from the authoritative export are retained.

| factor | offer_price | accepted_N | rejected_N | acceptance_pct |
| --- | --- | --- | --- | --- |
| 0.850000 | 18.143989 | 2838 | 0 | 100.000000 |
| 0.900000 | 19.211283 | 1279 | 1559 | 45.066949 |
| 0.950000 | 20.278576 | 1220 | 1618 | 42.988020 |
| 1.000000 | 21.345870 | 1149 | 1689 | 40.486258 |
| 1.050000 | 22.413163 | 1103 | 1735 | 38.865398 |
| 1.100000 | 23.480457 | 1071 | 1767 | 37.737844 |
| 1.150000 | 24.547750 | 1041 | 1797 | 36.680761 |

The minimum factor accepts every request by construction. At 0.90, 1,279 requests accept and 1,559 reject; those 1,559 correspond to the forced requests whose only feasible factor is 0.85. The 1.15 factor accepts 1,041 requests. These results reconcile with the saved feasible masks. Higher prices cannot increase acceptance under the frozen threshold comparison, so the monotone curve is partly a logical consequence of the model.

This curve is a **model counterfactual acceptance curve**, not a causal demand estimate. Runtime selected offers had zero rejection because infeasible arms were masked before selection. The current analysis exposes what that mask removes. Separate tables stratify by distance, epsilon magnitude and raw-preference category; absent groups are not fabricated. No claim about counterfactual assignments or revenue is made, because changing offers could change driver matching and future fleet state.

## 9. Existing DQN action-space coverage

The seven global offers range from approximately $18.14 to $24.55. Exactly **1,250,025 / 8,692,819 = 14.379972710808772%** of historical fares lie within the inclusive 0.85–1.15 factor range. The result matches the previous factor study. Below-range fares account for 57.302274%; above-range fares account for 28.317753%. The denominator is the full cleaned restricted fare population, not only the positive-supported epsilon population and not March16 requests.

| lower_km | upper_km | N | median_historical_factor | below_pct | inside_pct | above_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 5 | 6030518 | 0.566854 | 80.791783 | 12.121778 | 7.086439 |
| 5 | 10 | 1355140 | 1.189926 | 7.390676 | 36.892720 | 55.716605 |
| 10 | 15 | 555976 | 1.649031 | 0.575025 | 3.129452 | 96.295524 |
| 15 | 20 | 316303 | 2.070190 | 0.727151 | 0.200125 | 99.072725 |
| 20 | 30 | 311622 | 3.279323 | 0.816695 | 0.124831 | 99.058475 |
| 30 | inf | 123260 | 3.279323 | 0.668506 | 0.527341 | 98.804154 |

**FIXED_GLOBAL_ACTION_SPACE_EMPIRICAL_COVERAGE = WEAK** is a descriptive judgement about representing the broad observed fare-distance population, not a new statistical gate or a replacement of the earlier MODERATE justification for a bounded experiment. Coverage is highest in 5–10 km at approximately 36.89%, falls to 3.13% in 10–15 km and below 1% in each longer band. One global price interval therefore does not adequately represent the full range of recorded fare levels across materially different distances.

That does not prove a different action space would improve the simulator or the real system. Recorded fares include heterogeneous trip conditions and are not direct policy-action labels. Whether the intended model needs broad fare-level representation or only adjustments around a global reference is an academic design question. No endpoints, spacing, state features or masks are changed here.

## 10. P_base / L_base review

P_base remains **21.34586956773507 USD**, originally the global mean of the full cleaned Jan–Mar fare population. The restricted mean is **21.352107453289896 USD**; their difference is approximately $0.00624, computed as restricted mean minus frozen reference. The restricted median is $15.60, with P25/P75 $10.00/$26.66. The mean alignment supports its provenance as a global reference, not its suitability as a conditional fare for all distances.

Around L_base, diagnostic windows of ±0.25, ±0.50 and ±1.00 km produce the following observed fare summaries; these windows do not redefine the reference:

| window_halfwidth_km | N | mean_fare | median_fare | P25_fare | P75_fare |
| --- | --- | --- | --- | --- | --- |
| 0.250000 | 280174 | 22.427749 | 20.500000 | 17.700000 | 24.700000 |
| 0.500000 | 563369 | 22.376043 | 20.440000 | 17.700000 | 24.700000 |
| 1.000000 | 1186243 | 21.903147 | 19.800000 | 17.000000 | 24.110000 |

L_base remains **4.856998243316242 km**, converted from the frozen price-conditioned mean of 3.01799878914405 source miles. Its historical construction uses fares within ±$1 of P_base; it is not the overall mean distance. The restricted overall mean/median distances are 5.548668/3.025567 km, with P25/P75 1.738092/6.115507 km. These contextual comparisons do not demonstrate that L_base is a minimum-fare threshold.

**P_BASE_EMPIRICAL_SUPPORT = MODERATE** and **L_BASE_EMPIRICAL_SUPPORT = MODERATE** are qualitative review classifications. Both have documented empirical construction; neither is validated as a universal behavioural or tariff parameter. No equivalence between L_base and L_flat is established. The existing constants remain unchanged while their modelling interpretation is reviewed.

## 11. What remains valid from V1

The numerical positive-support construction, existing reference values, and saved development mask counts reconcile. The accepted/unmatched distinction remains essential: this analysis does not reinterpret the 52 unmatched requests as passenger rejection. Current empirical sampling continues to preserve the supported distribution without introducing a Gaussian assumption. No new evidence here concerns Bellman discounting, reward definition or state dimensionality; those remain unchanged.

| current_V1_decision | new_empirical_evidence | consistent | potential_implication | academic_decision_required |
| --- | --- | --- | --- | --- |
| positive epsilon magnitude | 11.734355% signed negatives; abs construction preserved | Numerically yes; behavioural meaning unresolved | Transformation is a proxy, not a causal elasticity | YES |
| T0 truncation | 8,598,805 supported; exact bounds reproduced | YES | No alternative support adopted | YES: scientific suitability |
| empirical resampling | Supported empirical skew/tails preserved; no distribution fitted | YES | No response-data validation claimed | YES |
| P_accept lower protection | Minimum arm accepts every request; pre-mask higher offers may fail | YES | Zero selected-offer rejection is structural | YES |
| global P_base | Restricted mean 21.352107 versus frozen 21.345870; distance medians differ | Numerically compatible as global reference | Not a universal conditional fare level | YES |
| global L_base | Price-conditioned reference; no flat-region equivalence | Provenance consistent | Do not equate reference with L_flat | YES |
| seven action factors | 14.379973% full fare coverage; weak long-distance coverage | Narrow range, not broad empirical coverage | Review whether relative global adjustments suffice | YES |
| hard pre-selection mask | Observed acceptance 100%; offline highest factor 36.680761% | YES | Mask and demand-curve evidence must be separated | YES |
| gamma=.99/request | No new discount evidence in this analysis | UNCHANGED | No gamma recommendation from this task | NO new decision from this evidence |

Numerical consistency is narrower than scientific validation. The follow-up does not prove passenger willingness-to-pay identification, DQN superiority, convergence, a natural fare floor, or protected-period generalization. The new evidence strengthens the need to distinguish global-reference arithmetic from observed fare heterogeneity and masked feasibility from empirical demand response.

## 12. What needs academic decision

**A. Does the fare data support an empirical minimum-fare region?** The observed minimum is sparse and spread across distances; no stable region is established.

**B. Should an empirical minimum replace the project platform minimum or remain separate?** The observed $0.01 minimum and the $18.143989 platform floor have different meanings; no substitution is justified automatically.

**C. Should an L_flat mechanism be introduced?** Low-fare distance percentiles vary strongly with band definition; no cutoff has been identified.

**D. Is absolute positive epsilon magnitude acceptable after signed-distribution review?** Negative historical values exist and transformation changes interpretation; positive proxy acceptability requires review.

**E. Is T0 empirical resampling still defensible?** Its numerical construction reproduces exactly, but completed-trip proxies do not identify response probabilities.

**F. Does the seven-arm global set adequately cover observed fare-distance levels?** Only 14.379973% overall coverage; materially different conditional coverage.

**G. Should actions become distance-relative?** This is a possible modelling decision, not an implemented recommendation or validated alternative.

**H. Should acceptance remain a pre-selection mask or become an outcome after selection?** Zero observed rejection is structural; the offline seven-action curve is not observed demand.

**I. Should training continue before these questions are resolved?** Further training remains paused; this report supplies evidence, not authorization.

## 13. Recommended decision sequence

First agree on what the passenger-preference equation is intended to represent and how completed-trip sensitivity proxies should be interpreted. Second decide whether observed low-fare evidence supports any additional fare/distance mechanism; the current evidence does not supply a defensible automatic L_flat. Third clarify whether the action space should represent broad distance-conditioned fare levels or a deliberately narrow global adjustment experiment. Fourth decide whether acceptance remains a feasibility constraint or becomes a modelled outcome after an action. These are methodology decisions, not implementation fixes inferred from the current tables.

Only after those decisions should implementation changes, if any, be specified and tested, followed by an explicit decision on further DQN training. Any new acceptance model would require its own data justification and validation. The existing gamma, reward, 13D state and checkpoints remain untouched. This sequence proposes a review order, not a preferred replacement method, distribution family or approved training run.

**NO_METHODOLOGY_CHANGE_YET. FURTHER_TRAINING_REMAINS_PAUSED.**
