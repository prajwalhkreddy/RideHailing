# V2 scenario-statistics clustering — SD<=1 feasibility result

## Authoritative method now resolved

FINAL_CLUSTERING_REPRESENTATION=SCENARIO_MEAN_SD_FROM_INDIVIDUAL_OBSERVATIONS.
CLUSTERING_POPULATION_PRIMARY=POSITIVE_VALID.
V2_CLUSTERING_USES_NEW_E=YES.
OCTOBER17_SCENARIO_MEAN_SD_METHOD=METHODOLOGICAL_BASE.
OCTOBER2_HOURLY_VECTOR_CLUSTERING=HISTORICAL_DIAGNOSTIC.
SEMANTIC_WEATHER_GROUPING=SUPERSEDED.
FORCED_K3_WEATHER_CLUSTERING=SUPERSEDED.

The latest explicit user decision resolves the earlier representation conflict. Positive finite e is compatible with the current positive fitted-distribution calibration population; runtime edge-case approval remains separate. No old Record-029 r_P/r_L, V1 support, absolute transformation, trimming, winsorization or fitted parameters were used. SIGNED_VALID is diagnostic only.

Methodology authority: `notebooks/plan/Price_Elasticity_Weather_Scenario_Analysis_Explained.docx`, scenario means/SD and equivalent pooled variance; its labels are examples. Algorithm logic follows `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/reproduce_analysis.py::cluster`: unscaled Euclidean mean/SD, average linkage. Current implementation uses equivalent SciPy linkage/cut_tree, not K-means; no random seed is needed. Sample N is not a feature. Codes are sorted ascending; candidate IDs ordered by increasing cluster mean (member-code tie breaker). No historical assignments reused.

## Data and validity

Only the existing `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet` supplied trip rows. Jan1≤pickup<Mar16 asserted before use. Source miles ×1.609344 become km; retain 1.5≤L<75. Monthly processed weather files under `data/processed/weather/nyc_weather_processed_2026_01.parquet`, `_02.parquet`, `_03.parquet` were read with Jan1≤Datetime<Mar16 filters and joined many-to-one by pickup hour. All weather codes matched; N remained 6,967,155.

P_base=22.354198442390455 USD and L_base=4.616983790655043 km, as instructed candidates. e=((L−L_base)/L_base)/((fare−P_base)/P_base). Exact denominator zero undefined; finite zero numerator yields zero. Nonfinite e not valid. Near-zero |r_P|<0.001 remains flagged, not excluded. SIGNED_VALID N=6,967,155; POSITIVE_VALID N=5,975,653; negative N=991,502; zero/undefined N=0. Reference approval remains unchanged.

RAW_WEATHER_NEW_E_STATS.csv has two rows per raw code. N, mean, population/sample SD, median and quantiles refer to the named population. Negative/positive/undefined percentages refer to that population; source_* percentages refer to all original filtered observations of the code. near_zero_denominator_N and dates refer to source observations, while positive_dates records positive-population date coverage. Counts and raw descriptions retained; no semantic feature enters clustering.

## Individual-code prerequisite

Every code has INTRINSIC_SD_GT_1. Primary positive-e values:

| raw_code | description | N | population_SD | dates | positive_dates |
| --- | --- | --- | --- | --- | --- |
| 1 | Clear | 1798309 | 21.463332 | 56 | 56 |
| 2 | Fair | 425053 | 22.174863 | 50 | 50 |
| 3 | Cloudy | 2893822 | 20.462133 | 73 | 73 |
| 5 | Fog | 368567 | 19.330246 | 17 | 17 |
| 7 | Light Rain | 44996 | 29.899075 | 7 | 7 |
| 8 | Rain | 104368 | 18.515916 | 9 | 9 |
| 9 | Heavy Rain | 86813 | 18.022835 | 8 | 8 |
| 12 | Sleet | 101317 | 28.860434 | 10 | 10 |
| 13 | Heavy Sleet | 15394 | 13.507686 | 4 | 4 |
| 14 | Light Snowfall | 52369 | 81.113196 | 12 | 12 |
| 15 | Snowfall | 71647 | 33.907542 | 11 | 11 |
| 16 | Heavy Snowfall | 9444 | 39.469704 | 4 | 4 |
| 17 | Rain Shower | 510 | 26.470551 | 1 | 1 |
| 21 | Snow Shower | 3044 | 11.403883 | 1 | 1 |

## Exhaustive K search and impossibility proof

MAX_ALLOWED_CLUSTER_SD=1.0, inclusive, using **population** SD. Evaluated K=1,2,…,14 ascending; no K passed, so all were necessary to complete the requested search. WEATHER_K_SEARCH.csv records 105 candidate clusters, all FAIL, with positive N, mean, pooled SD, member mean range, between-member mean SD, dendrogram merge height and K-wide outcome. Singleton merge height is zero. No final neutral labels were installed; candidate labels are not runtime mappings.

For members i, N=sum n_i; mu=sum(n_i*mu_i)/N; pooled variance=sum[n_i*(SD_i²+(mu_i−mu)²)]/N. The second term is nonnegative. Here **every** component variance exceeds 1, so every nonempty weighted combination also exceeds 1. The smallest raw-code SD is 11.403883, already far above the threshold. This proves failure for any partition of these intact raw weather scenarios, not only average linkage. A single offending high-SD code alone would not prove all merges impossible because other low-variance scenarios could dilute it; the all-code finding is essential.

The weighted within-code SD lower bound across the full positive population is **22.482978939341123**. No rescaling, trimming, splitting within a weather code, or algorithm substitution was used to force compliance. MINIMUM_VALID_K=NONE; FINAL_WEATHER_CLUSTER_COUNT=UNRESOLVED_NO_FEASIBLE_PARTITION. This is a feasibility result, not an unresolved representation question.

## Pooled calculation verification

Every candidate's within/between pooled variance was checked independently against aggregated sums of actual positive e and e². Maximum absolute numerical variance difference: 3.484501576167531e-11; all relative-tolerance checks passed. A deterministic bounded sample (first up to 4096 positive observations per code, 52,706 total) was directly concatenated: direct and pooled SD both 12.596757707860764. This validation sample did not replace the full-population statistics or clustering inputs. Component SDs were never averaged.

## Signed diagnostic, standardization and rare codes

For every candidate membership, WEATHER_K_SEARCH.csv also gives signed-valid mean, pooled SD and negative share. Signed SD is never an acceptance gate. No final K exists, so the requested standardized-feature comparison **at final K** is NOT_APPLICABLE; agreement, ARI and CLUSTER_ASSIGNMENT_STABILITY are NOT_APPLICABLE, not zero or WEAK. Standardization cannot overcome the variance proof for unchanged populations. No replacement population/feature search was introduced.

Code17 has 596 source observations, 510 positives, one date, positive SD26.470551; code21 has 3515 source/3044 positive observations, one date. Codes13 and16 span four dates. Large within-date trip counts do not establish independent event replication. Generalization of rare-code statistics is therefore uncertain; no formal uncertainty intervals or independence-based significance claim were computed. Rare codes were included in all K candidates; they are not the sole obstacle because all codes violate the criterion.

## Downstream status

TIME_TAXONOMY=T1_T4 retained: [00,04),[04,06),[06,16),[16,24). No half-hour sensitivity reopening. Since no final weather partition exists, final K×4 scenario count, support>=5000 counts, direct coverage and fallback counts are NOT_APPLICABLE, not zero. The 5000-positive gate and cluster×time→cluster-only→time-only→global hierarchy remain; there is no valid membership on which to apply them.

GROUPED_DISTRIBUTION_REFIT_REQUIRED=YES, conditional on a future approved feasible taxonomy/population contract; no final distribution fitting performed. Semantic fits remain historical only. WEATHER_TAXONOMY_FROZEN=NO. All14 assigned in every candidate K=YES; all14 assigned to an accepted final mapping=NO. FINAL_WEATHER_MAPPING.csv is deliberately header-only, not an operational mapping.

## Next decision and scope

The specified untrimmed positive population, intact weather scenarios and SD<=1 cannot all produce an exhaustive accepted partition under these references. A separate explicit methodology decision is required before any changed criterion/population/reference analysis. This task does not recommend an automatic cutoff or lower SD through unauthorized filtering.

Five report files only, plus three weather-related freeze-registry updates. No production/checkpoint/replay change, training, simulation, raw preparation or March17–31 analytical-row access. March16 also excluded. Historical analyses unchanged. Representation conflict resolved; replacement blocker is proven SD-constraint infeasibility.
