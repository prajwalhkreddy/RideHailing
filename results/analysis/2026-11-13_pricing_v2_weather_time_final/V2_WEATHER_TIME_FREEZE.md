# V2 semantic weather/time freeze

Decision date: 2026-11-14. This package uses the requested 2026-11-13 output path.

## Frozen by explicit user decision

V2_WEATHER_TAXONOMY=SEMANTIC_THREE_GROUP. WEATHER_MAPPING_FROZEN=YES. WEATHER_GROUPS_DEFINED_SEMANTICALLY=YES. ELASTICITY_CLUSTERING_DETERMINES_WEATHER_GROUP=NO.

- NON_PRECIPITATION: 1 Clear, 2 Fair, 3 Cloudy, 5 Fog.
- RAIN: 7 Light Rain, 8 Rain, 9 Heavy Rain, 17 Rain Shower.
- SNOW_FROZEN: 12 Sleet, 13 Heavy Sleet, 14 Light Snowfall, 15 Snowfall, 16 Heavy Snowfall, 21 Snow Shower.

Verification PASS; zero conflicting codes. Labels verified against existing `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/recommended_weather_clustering_supported.csv`. Mapping provenance is `manual_3bucket_reference_check_supported.csv` in the same folder. That mapping was previously diagnostic; the current user decision supplies authority to freeze it. Fog is not a precipitation code; sleet is mixed/frozen precipitation and belongs to SNOW_FROZEN. No new semantic meanings or raw-code membership were inferred from elasticity.

V2_TIME_TAXONOMY=T1_T4, frozen by this decision: T1 [00:00,04:00), T2 [04:00,06:00), T3 [06:00,16:00), T4 [16:00,24:00). Exactly 12 scenarios, all observed. Thirty-minute simulation cadence is unchanged; 48 half-hour sensitivity groups are not used.

Prior elasticity clustering results remain diagnostic only. Their instability no longer blocks membership, since meteorological categories are independently defined. Scenario statistics and fits below do not reassign any raw code. The scenario-first and correct pooled-variance principles in `Price_Elasticity_Weather_Scenario_Analysis_Explained.docx` remain applicable; statistical clustering is superseded for category selection by explicit user instruction. The latest pricing clarification continues to require conditional distribution comparison, not a universal family.

## Population and computation

Use only `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet`, columns pickup_timestamp, fare, trip_distance. Assert Jan1 inclusive ≤ pickup < Mar16. Convert TLC miles ×1.609344 to km before filtering 1.5≤L<75. Join hourly WeatherCode many-to-one using monthly `data/processed/weather/nyc_weather_processed_2026_01.parquet`, `_02.parquet`, `_03.parquet`, with Jan1≤Datetime<Mar16 read filters. No missing codes or duplicate join expansion.

P_base=22.354198442390455 USD; L_base=4.616983790655043 km. e=((L−L_base)/L_base)/((fare−P_base)/P_base). No historical epsilon/support is imported. No absolute value, clipping, denominator threshold or historical signed-support truncation. Exact-zero price denominator is undefined; a zero numerator with finite nonzero denominator is zero. Nonfinite values are not valid. |relative_price_deviation|<0.001 is a diagnostic near-zero flag only, consistent with the immediately preceding taxonomy diagnostic; rows remain retained.

N=6,967,155; finite valid e=6,967,155; positive=5,975,653; negative=991,502; zero=0; undefined=0. Negative values are retained diagnostically; fitting uses individual positive observations with their original frequencies. Population SD uses ddof=0. Quantiles use linear interpolation. No synthetic balancing or resampling.

## Counts, support and fallback

| scenario | total_N | positive_N | negative_N | near_zero_denominator_N | support_status | fallback_scenario |
| --- | --- | --- | --- | --- | --- | --- |
| NON_PRECIPITATION_T1 | 519974 | 412901 | 107073 | 171 | DIRECT_FIT | NON_PRECIPITATION_T1 |
| NON_PRECIPITATION_T2 | 127678 | 103722 | 23956 | 40 | DIRECT_FIT | NON_PRECIPITATION_T2 |
| NON_PRECIPITATION_T3 | 2815547 | 2454515 | 361032 | 619 | DIRECT_FIT | NON_PRECIPITATION_T3 |
| NON_PRECIPITATION_T4 | 2928503 | 2514613 | 413890 | 626 | DIRECT_FIT | NON_PRECIPITATION_T4 |
| RAIN_T1 | 25221 | 19990 | 5231 | 11 | DIRECT_FIT | RAIN_T1 |
| RAIN_T2 | 4486 | 3702 | 784 | 4 | FALLBACK_REQUIRED | RAIN_ALL |
| RAIN_T3 | 89723 | 79377 | 10346 | 14 | DIRECT_FIT | RAIN_T3 |
| RAIN_T4 | 156335 | 133618 | 22717 | 41 | DIRECT_FIT | RAIN_T4 |
| SNOW_FROZEN_T1 | 22814 | 17832 | 4982 | 9 | DIRECT_FIT | SNOW_FROZEN_T1 |
| SNOW_FROZEN_T2 | 6017 | 4891 | 1126 | 2 | FALLBACK_REQUIRED | SNOW_FROZEN_ALL |
| SNOW_FROZEN_T3 | 109280 | 94669 | 14611 | 31 | DIRECT_FIT | SNOW_FROZEN_T3 |
| SNOW_FROZEN_T4 | 161577 | 135823 | 25754 | 70 | DIRECT_FIT | SNOW_FROZEN_T4 |

Ten of twelve scenarios pass the retained 5,000-positive gate. Direct scenario-specific **fit eligibility** covers 99.84924980138952% of all trips; this is not 99.849% coverage by approved distributions. RAIN_T2 has 3,702 positives/4,486 trips and uses RAIN_ALL (236,687 positives); SNOW_FROZEN_T2 has 4,891 positives/6,017 trips and uses SNOW_FROZEN_ALL (253,215 positives). No time-only or global fallback is needed. The two sparse scenarios contain 10,503 trips total. No absent group is fabricated.

Hierarchy remains weather×time → weather-only → time-only → global. The 5,000 threshold is practical here and unchanged. Fallback pools were also fitted; support eligibility does not guarantee that a fitted family is acceptable. No family-failure fallback is silently activated: both weather-only pools also need family confirmation.

## Distribution fits and selection

36 comparisons: 10 direct scenarios plus 2 required weather-only pools, three families each. Reused the mathematical fitting approach in the earlier freeze-analysis infrastructure, but recalculated all inputs for these semantic/T1–T4 groups. Existing infrastructure supports gamma, lognormal and positive-truncated normal; Weibull was not added, avoiding a new fitting implementation.

Frequency-weighted maximum likelihood on unique observed positive values is exactly equivalent to the individual-trip likelihood; duplicate frequencies are preserved. Gamma has loc=0 and fitted shape/scale. Lognormal has loc=0 and fitted log-mean/log-SD. Normal is truncated to (0,+infinity), not bounded by any previous empirical epsilon support. Its optimizer uses t=mu/sigma in [−30,30], log(sigma) in [−15,20], and three starting values; hitting a boundary is reported as **not converged**, not accepted as a fitted finite optimum. Two free parameters per family: AIC=4−2logL; BIC=2logN−2logL. KS compares both sides of each empirical CDF jump; no KS p-value or independence claim is made.

Each fit row includes parameters, convergence, AIC/BIC, KS, empirical/fitted median/P90/P95/P99 with signed percentage errors, lower-tail probabilities below 0.01 and 0.1, empirical minimum, empirical E[1/e], and model inverse-moment status. Continuous fitted support approaches zero; it does not impose a new empirical floor.

**No family approved in any of the 12 scenarios.** All are FAMILY_SELECTION=ACADEMIC_CONFIRMATION_REQUIRED. Lognormal is the AIC leader independently in all 10 direct scenarios and both fallback pools, but its P99 is 38.56–58.86% below empirical and median errors range from −7.79% to +35.47%; KS ranges 0.05352–0.11851. This is substantial tail mismatch, not a small improvement to accept solely by AIC. No invented formal acceptance tolerance was applied; this is an explicit conservative review judgment based on the reported errors.

Gamma KS=0.15342–0.19022 with central/tail mismatch; all fitted shapes are ≤1, hence E[1/e] diverges. All 12 truncated-normal optimizations are boundary-limited; their diagnostic scores are not valid interior-MLE endorsements. A positive-truncated normal with nonzero density at zero has divergent E[1/e]. Lognormal has finite inverse moment exp(−mu_log+sigma_log²/2), reported per row, but finite expectation alone does not establish safe request-level behavior. No new cutoff/floor or production sampler was introduced. Undefined model inverse moments are blank with inverse_moment_finite=False, not zero.

The acceptance expression's division by e makes the lower tail relevant; upper-tail mismatch is separately quantified. The next methodological decision is acceptable fit/tail behavior or an approved alternative—not automatic global lognormal selection. The two support fallback pools cannot supply approved distributions until this is resolved.

## Semantic-weather descriptive findings

All finite signed e, with no trimming; statistics cannot change code membership:

| weather | total_N | mean | SD | median | IQR | negative_share_pct | selected_family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NON_PRECIPITATION | 6391702 | 1.437245 | 28.568751 | 1.060048 | 1.569007 | 14.173862 | ACADEMIC_CONFIRMATION_REQUIRED (scenario-specific) |
| RAIN | 275765 | 1.397075 | 31.979906 | 1.055628 | 1.447861 | 14.170761 | ACADEMIC_CONFIRMATION_REQUIRED (scenario-specific) |
| SNOW_FROZEN | 299688 | 1.523375 | 49.490993 | 1.007758 | 1.579100 | 15.507127 | ACADEMIC_CONFIRMATION_REQUIRED (scenario-specific) |

Central medians are near 1.01–1.06; Snow/Frozen has markedly greater signed dispersion (49.49 vs 28.57 and 31.98). These are descriptive population contrasts, not causal weather effects or new category-selection evidence. There is no single selected weather-level distribution family; selection is conditional on time and remains pending.

## Reference and other proposals unchanged

P_base_[1,75)=22.354198442390455; P_base_[1.5,75)=24.20370974379068. P_BASE_POPULATION_ALIGNMENT=PROFESSOR_CONFIRMATION_REQUIRED. All fits here are conditional on the instructed current candidate, not a resolution of population alignment. Changed reference decisions would require recalibration.

Do not change proactive slot pricing, alpha×P_base offer, passenger response after offer, rejection zero, proposed unmatched zero, destination representation, slot reward, gamma, NYC bounds, action discretization, drop-off lambda, hybrid generation or fresh-learner requirements. Those prior approval rows remain unchanged.

## Validation and authorization

Validated 14 unique raw codes, complete semantic coverage, 12 observed scenario IDs, sign-count reconciliation to 6,967,155, positive count 5,975,653, 10 direct/2 fallback, and 36 finite-score diagnostic fit rows. Failed family adequacy is disclosed, not treated as a software-test failure. No clustering rerun, production implementation, model training, simulation or March17–31 analytical-row access. March16 also excluded from calibration.

Weather/time taxonomy is frozen by user decision. **Overall V2 methodology freeze remains NO** because reference alignment and distribution-family decisions (and unchanged architectural approvals) remain open. No implementation or training authorization is implied.
