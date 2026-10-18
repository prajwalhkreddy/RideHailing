# Earlier weather/time scenario diagnostic analysis

## 1. Objective
Assess original scenarios using descriptive mean/SD geometry and true pooled SD. No semantic regrouping or model training is performed.

## 2. Population used
PRIMARY: all 10,611,392 VALID epsilon rows, before support restriction. SECONDARY: 10,505,278 VALID rows within inclusive [−12.890744316473482,15.442447741158892]. Existing epsilon is read, never recalculated. Primary statistics alone govern clustering and strict SD decisions.

## 3. Original weather scenarios
All 14 codes retain the original Meteostat labels.

| weather_code | weather_name | N | mean_epsilon | median_epsilon | population_SD |
| --- | --- | --- | --- | --- | --- |
| 1 | Clear | 3083027 | 0.597491 | 0.733827 | 7.509273 |
| 2 | Fair | 776464 | 0.652377 | 0.763951 | 5.999304 |
| 3 | Cloudy | 5228305 | 0.670138 | 0.781962 | 6.727232 |
| 5 | Fog | 622213 | 0.691247 | 0.792883 | 6.749869 |
| 7 | Light Rain | 93399 | 0.667342 | 0.780269 | 5.895823 |
| 8 | Rain | 217322 | 0.611535 | 0.778905 | 7.899671 |
| 9 | Heavy Rain | 214239 | 0.626514 | 0.751408 | 7.626100 |
| 12 | Sleet | 146488 | 0.681043 | 0.800350 | 7.357411 |
| 13 | Heavy Sleet | 22014 | 0.615499 | 0.786206 | 6.280061 |
| 14 | Light Snowfall | 75717 | 0.712874 | 0.786586 | 6.372740 |
| 15 | Snowfall | 106472 | 0.675837 | 0.784196 | 5.688358 |
| 16 | Heavy Snowfall | 16537 | 0.507261 | 0.522669 | 29.100775 |
| 17 | Rain Shower | 5015 | 0.884769 | 0.822918 | 4.238875 |
| 21 | Snow Shower | 4180 | 0.847779 | 0.861110 | 3.759910 |

## 4. Weather × time scenarios
48 observed scenarios. T1=00–05, T2=06–11, T3=12–17, T4=18–23 are PRESENTATION periods, not frozen simulation T groups. No absent scenarios fabricated. Sparse reporting flag is N<1,000; it is an implementation choice, not an exclusion. Sparse scenarios: 3.

## 5. Similarity definition
Euclidean distance in unscaled [mean, population SD], using signed A−B differences. Similarity is descriptive, not a statistical equivalence test or significance claim. Scenario sizes are reported; geometry is scenario-unweighted. Closest weather pairs:

| Scenario_A | Scenario_B | Euclidean_Distance |
| --- | --- | --- |
| W03 | W05 | 0.030951 |
| W02 | W07 | 0.104557 |
| W01 | W09 | 0.120378 |
| W13 | W14 | 0.134429 |
| W01 | W12 | 0.173329 |

## 6. Clustering method
Agglomerative average linkage, Euclidean metric, no scaling and no weather-name inputs. Linkage and sparse threshold are implementation choices, not frozen methodology decisions. Scenarios ordered by code/time; IDs canonicalized by first member. Weather K=2–8 and weather-time K=2–12. Silhouette uses scenario points, not replicated trips. Recommendation eligibility requires every cluster SD<4 and minimum cluster N≥1,000; among eligible choices highest silhouette wins, ties lower K. Interpretability still requires review; no automatic methodology selection.

## 7. Candidate clustering results
Weather recommendation: NO ACCEPTABLE CLUSTERING FOUND. Weather-time recommendation: NO ACCEPTABLE CLUSTERING FOUND.

| K | silhouette_score | number_of_clusters | minimum_cluster_N | maximum_cluster_N |
| --- | --- | --- | --- | --- |
| 2 | 0.870967 | 2 | 16537 | 10594855 |
| 3 | 0.623322 | 3 | 9195 | 10585660 |
| 4 | 0.627404 | 4 | 9195 | 6924584 |
| 5 | 0.595341 | 5 | 9195 | 5948249 |
| 6 | 0.489712 | 6 | 4180 | 5948249 |
| 7 | 0.524536 | 7 | 4180 | 5850518 |
| 8 | 0.447547 | 8 | 4180 | 5850518 |

| K | silhouette_score | number_of_clusters | minimum_cluster_N | maximum_cluster_N |
| --- | --- | --- | --- | --- |
| 2 | 0.890252 | 2 | 10027 | 10601365 |
| 3 | 0.720800 | 3 | 3216 | 10598149 |
| 4 | 0.501101 | 4 | 3216 | 10400254 |
| 5 | 0.503773 | 5 | 3216 | 7754546 |
| 6 | 0.437464 | 6 | 622 | 7754546 |
| 7 | 0.478742 | 7 | 622 | 5037458 |
| 8 | 0.498211 | 8 | 622 | 5037458 |
| 9 | 0.546616 | 9 | 622 | 5037458 |
| 10 | 0.532323 | 10 | 622 | 5037458 |
| 11 | 0.540715 | 11 | 622 | 4533801 |
| 12 | 0.527450 | 12 | 622 | 4533801 |

## 8. Combined-SD < 4 rule
For N=sum(n_i), pooled mean=sum(n_i*mu_i)/N; pooled variance=sum(n_i*(SD_i²+(mu_i−mu_pool)²))/N. This includes within- and between-scenario variation. Medians are computed from actual combined epsilon, never averaged. Pooled means/SDs are checked against direct observations for every unique cluster. ACCEPT iff SD<4; EXCLUDE iff SD≥4, with no rounded-value decisions. EXCLUDE labels a proposed grouping, not individual observations. Singleton clusters receive the same test.

The weighted within-scenario SD lower bound is 7.037166 (weather) and 7.037114 (weather-time). Since these exceed 4, no exhaustive partition of these indivisible scenarios can make every pooled cluster SD<4: its weighted cluster variance must be at least this within-scenario variance. This is stronger than failure of the tested K values; it does not preclude selected subsets passing.

## 9. Accepted combinations
All ACCEPT rows, including singletons and repeated memberships across K, are explicitly listed in the two cluster-combined CSVs. Counts by candidate occurrence: weather 3, weather-time 7. These do not constitute an acceptable exhaustive grouping.

## 10. Excluded combinations
Every EXCLUDE row lists exact member IDs and pooled SD in the same CSVs; no observations were removed. Candidate occurrence counts: weather 32, weather-time 70.

## 11. Manual 3-bucket reference comparison
Reference only, not approved and not used for clustering.

| group | N | mean_epsilon | median_epsilon | population_SD | Decision |
| --- | --- | --- | --- | --- | --- |
| NON-PRECIPITATION | 9710009 | 0.647004 | 0.766558 | 6.933297 | EXCLUDE |
| RAIN | 529975 | 0.630011 | 0.767860 | 7.442885 | EXCLUDE |
| SNOW/FROZEN | 371408 | 0.676294 | 0.786467 | 8.894414 | EXCLUDE |

## 12. Supported-population sensitivity check
Support restricts tails and changes dispersion; its results must not be substituted for the primary SD test. Weather-only primary versus supported SD:

| weather_code | population_SD_valid | population_SD_supported |
| --- | --- | --- |
| 1 | 7.509273 | 1.478379 |
| 2 | 5.999304 | 1.432828 |
| 3 | 6.727232 | 1.423801 |
| 5 | 6.749869 | 1.401925 |
| 7 | 5.895823 | 1.403982 |
| 8 | 7.899671 | 1.512583 |
| 9 | 7.626100 | 1.439045 |
| 12 | 7.357411 | 1.479018 |
| 13 | 6.280061 | 1.683882 |
| 14 | 6.372740 | 1.479545 |
| 15 | 5.688358 | 1.422310 |
| 16 | 29.100775 | 2.172872 |
| 17 | 4.238875 | 1.428979 |
| 21 | 3.759910 | 1.475881 |

## 13. Diagnostic conclusion
No acceptable exhaustive grouping is established on the primary population. Cloudy/Clear/Fair/Fog and rain/snow semantics are not assumed interchangeable; compare their distances and candidate memberships below. Adding time changes the points and memberships, but does not resolve the full-population SD constraint. A single final grouping for later representation is not supported by this analysis. No causal inference or willingness-to-pay interpretation is made.

## 14. Earlier unresolved methodology decisions
Average linkage, candidate-K selection and support adequacy criteria require review. If the strict rule remains necessary, methodology review must establish whether selected subsets or another explicitly defined population definition is intended. Do not silently switch to supported rows. Observations were NOT combined for joint model training; raw records are only pooled for correct descriptive statistics. Original labels remain preserved; grouping uses sensitivity statistics, not semantic names. DQN/RL, acceptance and pricing are out of scope.

## Validation and files
Counts reconcile for both weather and weather-time populations. Every retained observation has exactly one code and one presentation period. No epsilon values or protected files changed; hashes verified after generation. Four figures use primary statistics and explicitly show infeasibility when no recommendation exists. Recommended mapping CSVs retain original scenarios with blank candidate IDs and an explicit no-solution status when applicable. All required CSVs and figures are in this folder; reproduce_analysis.py is the self-contained reproduction entry point.

### Highest-silhouette weather partition (K=2), diagnostic ONLY
Not acceptable unless all pooled clusters pass.

| Scenario_ID | weather_name | diagnostic_cluster |
| --- | --- | --- |
| W01 | Clear | 1 |
| W02 | Fair | 1 |
| W03 | Cloudy | 1 |
| W05 | Fog | 1 |
| W07 | Light Rain | 1 |
| W08 | Rain | 1 |
| W09 | Heavy Rain | 1 |
| W12 | Sleet | 1 |
| W13 | Heavy Sleet | 1 |
| W14 | Light Snowfall | 1 |
| W15 | Snowfall | 1 |
| W16 | Heavy Snowfall | 2 |
| W17 | Rain Shower | 1 |
| W21 | Snow Shower | 1 |

### Highest-silhouette weather_time partition (K=2), diagnostic ONLY
Not acceptable unless all pooled clusters pass.

| Scenario_ID | weather_name | diagnostic_cluster |
| --- | --- | --- |
| W01_T1 | Clear | 1 |
| W01_T2 | Clear | 1 |
| W01_T3 | Clear | 1 |
| W01_T4 | Clear | 1 |
| W02_T1 | Fair | 1 |
| W02_T2 | Fair | 1 |
| W02_T3 | Fair | 1 |
| W02_T4 | Fair | 1 |
| W03_T1 | Cloudy | 1 |
| W03_T2 | Cloudy | 1 |
| W03_T3 | Cloudy | 1 |
| W03_T4 | Cloudy | 1 |
| W05_T1 | Fog | 1 |
| W05_T2 | Fog | 1 |
| W05_T3 | Fog | 1 |
| W05_T4 | Fog | 1 |
| W07_T1 | Light Rain | 1 |
| W07_T2 | Light Rain | 1 |
| W07_T3 | Light Rain | 1 |
| W07_T4 | Light Rain | 1 |
| W08_T1 | Rain | 1 |
| W08_T2 | Rain | 1 |
| W08_T3 | Rain | 1 |
| W08_T4 | Rain | 1 |
| W09_T1 | Heavy Rain | 1 |
| W09_T2 | Heavy Rain | 1 |
| W09_T3 | Heavy Rain | 1 |
| W09_T4 | Heavy Rain | 1 |
| W12_T1 | Sleet | 1 |
| W12_T3 | Sleet | 1 |
| W12_T4 | Sleet | 1 |
| W13_T1 | Heavy Sleet | 1 |
| W13_T4 | Heavy Sleet | 1 |
| W14_T1 | Light Snowfall | 1 |
| W14_T2 | Light Snowfall | 1 |
| W14_T3 | Light Snowfall | 1 |
| W14_T4 | Light Snowfall | 1 |
| W15_T1 | Snowfall | 1 |
| W15_T2 | Snowfall | 1 |
| W15_T3 | Snowfall | 1 |
| W15_T4 | Snowfall | 1 |
| W16_T1 | Heavy Snowfall | 1 |
| W16_T2 | Heavy Snowfall | 1 |
| W16_T3 | Heavy Snowfall | 1 |
| W16_T4 | Heavy Snowfall | 2 |
| W17_T1 | Rain Shower | 1 |
| W17_T2 | Rain Shower | 1 |
| W21_T2 | Snow Shower | 1 |

## Direct answers to the diagnostic scenario questions

A. Closest mean/SD pairs are Cloudy–Fog (distance 0.030951), Fair–Light Rain (0.104557), Clear–Heavy Rain (0.120378), and Heavy Sleet–Light Snowfall (0.134429). These are descriptive proximity statements, not statistical-equivalence findings.

B. Cloudy is much closer to Fog than to Fair (0.728145) or Clear (0.785407). It does not justify a uniform non-precipitation group under the SD criterion.

C. The rain family does not separate as one homogeneous group: Rain/Heavy Rain have SD around 7.90/7.63, Light Rain 5.90 and Rain Shower 4.24. Fair–Light Rain and Clear–Heavy Rain proximity crosses semantic families. A broad K=2 merge of almost everything is not evidence for a rain-specific cluster.

D. Snow/frozen types are heterogeneous: Heavy Sleet and Light Snowfall are close, but Heavy Snowfall SD is 29.10, Snowfall 5.69 and Snow Shower 3.76; Sleet SD is 7.36. No coherent approved frozen-weather group follows.

E. All manual buckets fail: pooled SD 6.933297, 7.442885 and 8.894414 for NON-PRECIPITATION, RAIN and SNOW/FROZEN respectively.

F. Time materially changes individual dispersions and diagnostic membership: Heavy Snowfall 18–23 has SD 35.940515 and becomes the isolated K=2 outlier. Nonetheless, both weather and weather-time exhaustive solutions remain infeasible under the strict primary-population rule.

G. At highest-silhouette K=2, weather clusters have SD 6.948267 and 29.100775; weather-time clusters have SD 6.953277 and 35.940515: all fail. Full membership and failure lists are in the combined-statistics CSVs for every K. The only accepted weather candidate membership is singleton Snow Shower (SD 3.759910), repeated at K=6–8. The only accepted weather-time candidate membership is singleton Heavy Sleet 00–05 (SD 2.445625), repeated at K=6–12. No multi-scenario merger generated by these candidate partitions passes.

H. No exhaustive grouping is defensible under all requested criteria. Do not relax the rule or substitute the supported population implicitly. Review the intended population and whether partial scenario representation is acceptable before choosing a subsequent representation.

Presentation reproducibility: after reproduce_analysis.py, run finalize_presentation.py to apply readable leader-line labels and this interpretation section. No CSV statistics are changed by the presentation pass.
