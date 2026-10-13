# Record-030 Passenger Price–Distance Sensitivity Results

## 1. Professor Request
Reporting follow-up using frozen Record-029 results: cleaning flow, hourly Clear/Rain summaries, six-hour presentation and the 8 AM–8 PM variability observation. No epsilon reconstruction, refitting or production modification.

## 2. Frozen Record-029 Method Used
The frozen references are P_base=21.34586956773507 USD, tau_P=±1.00 USD and L_base=3.01799878914405 miles. Price is TLC fare_amount. Sensitivity is epsilon=[(fare−P_base)/P_base]/[(trip_distance−L_base)/L_base]. The strict half-resolution rule abs(trip_distance−L_base)<0.005 mile leaves epsilon unresolved; distance resolution is 0.01 mile. No L_min is adopted. Simulation support is inclusive [−12.890744316473482,15.442447741158892]. These are project methodology decisions, not identified causal price elasticity.

The simulation groups remain T1 00–03, T2 04–05, T3 06–15 and T4 16–23, shared across Clear/Rain. The six-hour G groups below are presentation only.

## 3. Dataset and Cleaning Counts
The three January–March 2026 input files contain 11,077,206 trips. Ten lie outside the pickup window [2026-01-01,2026-04-01), leaving 11,077,196. Combined finite-positive fare/distance and timestamp validity leaves 10,620,887 (456,309 excluded). The existing ≤100-mile source rule removes 478, yielding 10,620,409 cleaned trips. Record-029 revalidation removes zero additional rows. The denominator rule marks 9,017 historical rows unresolved, leaving 10,611,392 VALID epsilon observations. Inclusive simulation support retains 10,505,278; 53,057 valid observations below and 53,057 above remain historical data. Supported Clear/Rain scope contains 3,265,135 observations: Clear 3,050,121 and Rain 215,014.

See `record030_dataset_cleaning_flow.csv`. It separates source cleaning, denominator resolution and simulation-support restrictions. The latter two do not delete historical observations. Mean/median/SD columns also preserve the all-weather VALID and supported-weather overall summaries for tracing the draft.

## 4. Hourly Clear/Rain Results
The hourly CSV reuses all 44 observed groups (24 Clear, 20 Rain). Missing Rain hours remain absent from the table and gaps in plots. Overall supported summaries:

| weather_name | N | mean | median | population_SD |
| --- | --- | --- | --- | --- |
| Clear | 3050121 | 0.621737 | 0.734565 | 1.478379 |
| Rain | 215014 | 0.654704 | 0.779043 | 1.512583 |

Hourly means vary less than hourly dispersion; lower SD is not synonymous with lower mean sensitivity. The separate hourly mean and SD figure titles identify the frozen P0.5–P99.5 support. The six-hour figure presents only mean and population SD; medians remain in the CSV.

## 5. Grouped 6-Hour Results
G1=00–05, G2=06–11, G3=12–17 and G4=18–23. Quantiles and population SD are pooled from actual stored epsilon, not averaged hourly quantiles. Both conditions have minimum SD in G3 and maximum SD in G1; mean ordering differs.

| weather_name | period | hours | N | mean | median | population_SD |
| --- | --- | --- | --- | --- | --- | --- |
| Clear | G1 | 00–05 | 260548 | 0.603949 | 0.673279 | 1.666147 |
| Clear | G2 | 06–11 | 803960 | 0.618779 | 0.718184 | 1.536148 |
| Clear | G3 | 12–17 | 1093028 | 0.612928 | 0.723239 | 1.337078 |
| Clear | G4 | 18–23 | 892585 | 0.640382 | 0.779759 | 1.530691 |
| Rain | G1 | 00–05 | 28830 | 0.587018 | 0.726728 | 1.942595 |
| Rain | G2 | 06–11 | 49831 | 0.700236 | 0.797232 | 1.538050 |
| Rain | G3 | 12–17 | 64082 | 0.670993 | 0.765048 | 1.209440 |
| Rain | G4 | 18–23 | 72271 | 0.635867 | 0.792883 | 1.539304 |

## 6. 8 AM–8 PM Variability Check
Descriptive evidence of lower daytime dispersion: daytime (08–19) has lower dispersion than OTHER (20–23 and 00–07) in both weather conditions. Clear pooled SD is 1.383509 versus 1.651547 (difference −0.268038; ratio 0.837705), and Rain is 1.298893 versus 1.763551 (difference −0.464658; ratio 0.736521). Weighted mean hourly SD and median hourly SD show the same direction. This does not establish a continuous trend, a causal weather effect, or lower average sensitivity.

| weather_name | period | N | mean | median | population_SD | weighted_mean_hourly_SD | median_hourly_SD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clear | DAYTIME | 2032391 | 0.616147 | 0.730760 | 1.383509 | 1.378041 | 1.343477 |
| Clear | OTHER | 1017730 | 0.632901 | 0.748238 | 1.651547 | 1.650313 | 1.656363 |
| Rain | DAYTIME | 124245 | 0.661434 | 0.773256 | 1.298893 | 1.292292 | 1.251829 |
| Rain | OTHER | 90769 | 0.645492 | 0.796592 | 1.763551 | 1.753029 | 1.762306 |

## 7. Gaussian ±4 Sigma Clarification
Gaussian ±4 sigma was discussed as a possible simulation representation; it is not the selected model. Record-029 compared truncated Normal with empirical distributions and found material quartile/tail mismatch despite moment agreement. EMPIRICAL_RESAMPLE remains selected. No Gaussian was fitted here; sigma=2.18 is not adopted as a current parameter.

## 8. Results-Section Conclusions
The evidence describes passenger price-distance sensitivity and its dispersion, not causal willingness-to-pay. Daytime dispersion is lower in both conditions, but hourly curves are nonmonotonic and weather differences vary by period. Reporting periods do not replace the frozen simulation grouping.

## 9. Files for Professor Review
- [record030_dataset_cleaning_flow.csv](record030_dataset_cleaning_flow.csv)
- [record030_hourly_clear_rain_statistics.csv](record030_hourly_clear_rain_statistics.csv)
- [record030_six_hour_group_statistics.csv](record030_six_hour_group_statistics.csv)
- [record030_8am_8pm_variability_check.csv](record030_8am_8pm_variability_check.csv)
- [charts/record030_hourly_mean_clear_rain.png](charts/record030_hourly_mean_clear_rain.png)
- [charts/record030_hourly_sd_clear_rain.png](charts/record030_hourly_sd_clear_rain.png)
- [charts/record030_six_hour_clear_rain_comparison.png](charts/record030_six_hour_clear_rain_comparison.png)
- [Passenger_Price_Sensitivity_Results_Draft.md](Passenger_Price_Sensitivity_Results_Draft.md)

## 10. Remaining Issues, if any
Upstream per-rule failure counts overlap. Their individual sequential removal counts are not separately persisted and are not inferred. Percentages in the flow CSV identify their denominator explicitly. Initial counts come from the existing population manifest, so raw tables were not loaded. The frozen support JSON contains historical unresolved-decision notes; the final methodology JSON governs current grouping and family. Rain has no observations at hours 05, 10, 11 and 12. Sparse and unequal weather/hour coverage limits generalization.

Validation: original Record-029 file hashes checked unchanged; frozen references/support retained; hourly, six-hour and daytime counts reconcile; missing Rain hours preserved. Figures are plotted directly from the same data frames serialized to their CSVs. No production code changed.
