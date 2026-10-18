# Supported weather/time scenario analysis — clarified decision population

## 1. Supported-population analysis definition
The strict combined population SD < 4 decision rule applies AFTER the already-frozen empirical support restriction. PRIMARY decision population is 10,505,278 supported VALID observations; unrestricted VALID N=10,611,392 is retained ONLY as diagnostic evidence of tail sensitivity. Support was frozen before this weather clustering decision and was not introduced merely to make SD < 4 pass. No epsilon, support, reference or behavioural method changed.

## 2. Populations and unchanged scenario definitions
Inclusive support: [−12.890744316473482,15.442447741158892]; epsilon_status=VALID. All 14 original labels remain unchanged. There are 48 observed weather × six-hour scenarios: T1 00–05, T2 06–11, T3 12–17, T4 18–23. These remain presentation periods and do not replace frozen simulation T groups. Missing scenarios are not fabricated. Existing supported scenario CSVs were independently verified and reused byte-for-byte.

## 3. Supported weather results
All 14 individual weather scenarios satisfy strict SD<4.

| weather_code | weather_name | N | mean_epsilon | median_epsilon | population_SD |
| --- | --- | --- | --- | --- | --- |
| 1 | Clear | 3050121 | 0.621737 | 0.734565 | 1.478379 |
| 2 | Fair | 769018 | 0.654904 | 0.763951 | 1.432828 |
| 3 | Cloudy | 5177886 | 0.666440 | 0.781962 | 1.423801 |
| 5 | Fog | 616431 | 0.672629 | 0.792883 | 1.401925 |
| 7 | Light Rain | 92492 | 0.657293 | 0.780269 | 1.403982 |
| 8 | Rain | 215014 | 0.654704 | 0.779043 | 1.512583 |
| 9 | Heavy Rain | 212103 | 0.634154 | 0.751408 | 1.439045 |
| 12 | Sleet | 144849 | 0.661823 | 0.800243 | 1.479018 |
| 13 | Heavy Sleet | 21709 | 0.625641 | 0.786209 | 1.683882 |
| 14 | Light Snowfall | 74930 | 0.668144 | 0.786467 | 1.479545 |
| 15 | Snowfall | 105496 | 0.664929 | 0.783713 | 1.422310 |
| 16 | Heavy Snowfall | 16123 | 0.486535 | 0.525007 | 2.172872 |
| 17 | Rain Shower | 4969 | 0.751416 | 0.820560 | 1.428979 |
| 21 | Snow Shower | 4137 | 0.763375 | 0.860949 | 1.475881 |

## 4. Similarity and clustering implementation
Unscaled Euclidean distance=sqrt((mean_A−mean_B)^2+(SD_A−SD_B)^2); average-linkage agglomerative clustering, equal scenario weights in feature geometry, population weighting only for combined statistics. Weather names do not enter assignments. Same K ranges as before: weather 2–8; weather/time 2–12. Closest supported pairs:

| Scenario_A | Scenario_B | Euclidean_Distance |
| --- | --- | --- |
| W03 | W15 | 0.002124 |
| W12 | W14 | 0.006343 |
| W02 | W15 | 0.014530 |
| W02 | W03 | 0.014648 |
| W05 | W07 | 0.015473 |

These are descriptive statistical similarities, not tested equivalence of full distributions.

## 5. Candidate K comparison and recommendation
All clusters at every evaluated K pass the strict pooled SD rule. That rule alone does not determine a useful K. For weather, K2 silhouette=0.798705 with minimum N=16,123; K3=0.608023 separates Heavy Sleet; K4=0.462833 additionally separates shower scenarios. K3/K4 increase fragmentation without improving silhouette. K5–8 also score below K2 and add groups. K2 is recommended because simplicity, separation and support agree, not because a numeric maximum is automatically selected. Its minority group is only about 0.15% of the population, so transportability still needs review.

| K | silhouette_score | number_of_clusters | minimum_cluster_N | maximum_cluster_N |
| --- | --- | --- | --- | --- |
| 2 | 0.798705 | 2 | 16123 | 10489155 |
| 3 | 0.608023 | 3 | 16123 | 10467446 |
| 4 | 0.462833 | 4 | 9106 | 10458340 |
| 5 | 0.484973 | 5 | 9106 | 6973426 |
| 6 | 0.407350 | 6 | 4137 | 6973426 |
| 7 | 0.339388 | 7 | 4137 | 6973426 |
| 8 | 0.244515 | 8 | 4137 | 6761323 |

All-weather pooled supported SD is 1.444588, also below 4. K1 has no silhouette and was outside the prescribed evaluation range; the SD condition alone cannot establish that two distributions are necessary. K2 is a candidate scenario representation, not a uniquely identified natural partition or a frozen downstream model.

## 6. Recommended weather-only candidate
Cluster 1: codes 1,2,3,5,7,8,9,12,13,14,15,17,21. Cluster 2: code16 Heavy Snowfall. Original labels/codes remain in the recommended mapping.

| Cluster_ID | Member_Weather_Codes | Total_N | Combined_Mean | Combined_Median | Combined_Population_SD | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1;2;3;5;7;8;9;12;13;14;15;17;21 | 10489155 | 0.651912 | 0.767296 | 1.443171 | ACCEPT |
| 2 | 16 | 16123 | 0.486535 | 0.525007 | 2.172872 | ACCEPT |

## 7. True combined SD and acceptance
Pooled mean=sum(n_i*mu_i)/N. Pooled variance=sum(n_i*(SD_i²+(mu_i−mu_pool)²))/N; population SD is its square root. Between-scenario mean differences are included. Medians are calculated from underlying supported observations. Each unique pooled mean/SD was verified against direct observations. ACCEPT strictly means SD<4 on supported data, with no rounding for decisions. No supported candidate clusters were EXCLUDE. Acceptance under this criterion does not approve a grouping methodology or justify a simulation change.

## 8. Weather × time candidate and whether time helps
All 48 individual scenarios pass; maximum SD=2.347770. K2 silhouette=0.653741, below weather-only 0.798705; cross-analysis scores concern different scenario units and are descriptive rather than a formal improvement test. K3=0.500042 and K4=0.459027 add subdivisions; K8–12 introduce a 619-observation cluster below the existing N≥1,000 candidate-support preference. No observations are excluded for sparseness.

| K | silhouette_score | number_of_clusters | minimum_cluster_N | maximum_cluster_N |
| --- | --- | --- | --- | --- |
| 2 | 0.653741 | 2 | 9746 | 10495532 |
| 3 | 0.500042 | 3 | 9746 | 9579263 |
| 4 | 0.459027 | 4 | 3140 | 9579263 |
| 5 | 0.427685 | 5 | 3140 | 7498067 |
| 6 | 0.418469 | 6 | 3140 | 7498067 |
| 7 | 0.458097 | 7 | 3140 | 4531620 |
| 8 | 0.438369 | 8 | 619 | 4531620 |
| 9 | 0.461774 | 9 | 619 | 4531620 |
| 10 | 0.453811 | 10 | 619 | 4531620 |
| 11 | 0.452010 | 11 | 619 | 4531620 |
| 12 | 0.457836 | 12 | 619 | 4531620 |

Recommended time diagnostic K2 isolates W16_T4 (Heavy Snowfall 18–23), N=9,746, SD=2.347770; all remaining scenarios pool to N=10,495,532, SD=1.443476. Thus Heavy Snowfall 00–17 joins the broad cluster, whereas weather-only isolates the whole code. Time reveals variation but does not improve global separation or justify extra grouping complexity on this evidence. Weather-only K2 is the simpler candidate to take for sign-off.

| Cluster_ID | Total_N | Combined_Mean | Combined_Median | Combined_Population_SD | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | 10495532 | 0.651824 | 0.767172 | 1.443476 | ACCEPT |
| 2 | 9746 | 0.473593 | 0.502160 | 2.347770 | ACCEPT |

## 9. Manual three-bucket reference
Reference only, not automatically selected. All three pass SD<4, but semantic labels did not drive the data-derived clusters. Closest pairs cross semantic families (Cloudy–Snowfall; Sleet–Light Snowfall).

| group | N | mean_epsilon | median_epsilon | population_SD | Decision |
| --- | --- | --- | --- | --- | --- |
| NON-PRECIPITATION | 9613456 | 0.651731 | 0.766558 | 1.440831 | ACCEPT |
| RAIN | 524578 | 0.647767 | 0.767860 | 1.463619 | ACCEPT |
| SNOW/FROZEN | 367244 | 0.655315 | 0.786209 | 1.513771 | ACCEPT |

## 10. Diagnostic findings and methodology review
A: all 14 weather scenarios have SD<4. B: closest is Cloudy–Snowfall, followed by Sleet–Light Snowfall. C: recommend weather-only K2 as a candidate. D/E: pooled SDs 1.443171 and 2.172872, both strictly passing. F: manual three buckets pass, but that alone does not validate semantic grouping. G: time changes some membership but lowers silhouette and does not materially improve the case for a richer representation. H: consider weather-only K2 in methodology review, alongside the passing manual reference and the caveat that K1 also meets the SD threshold. Final group count, average linkage, support adequacy and downstream distribution representation remained subject to methodology review in this earlier analysis.

## 11. Diagnostic provenance and file guide
Current decision outputs are the 11 requested CSVs ending `_supported.csv`. The original weather/time supported statistics are unchanged; new supported pairwise, K evaluations, pooled-cluster summaries, recommended mappings and manual reference are added. Recommended mappings preserve original_weather_code, original_weather_name and original_time_period.

Earlier unsuffixed clustering CSVs, `*_valid.csv`, `scenario_sample_size_audit.csv`, and the four existing charts describe the unrestricted diagnostic population ONLY. Their no-acceptable-clustering conclusion is superseded for current decision-making, not deleted or numerically altered. The full earlier report is preserved as README_unrestricted_diagnostic.md. Existing charts are not supported-population decision figures. Do not run legacy reproduce_analysis.py/finalize_presentation.py to produce a current decision report: use update_supported_analysis.py, which implements this clarification.

## 12. Validation and scope
Verified VALID N=10,611,392 and supported N=10,505,278; weather and weather/time supported counts reconcile. Each row maps to one original weather code and one presentation period. Existing scenario values were checked against source observations. Direct-vs-pooled means/SDs agree. Protected-file hashes and all earlier CSV hashes were unchanged after analysis. No epsilon values, support bounds, Record-029/030 files, simulator, acceptance or pricing were changed. No predictive or joint model training performed: records were pooled only for descriptive summaries. Clustering is exploratory analysis; DQN/RL is outside scope.
