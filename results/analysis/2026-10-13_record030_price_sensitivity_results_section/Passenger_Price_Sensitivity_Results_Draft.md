# Passenger Price–Distance Sensitivity Results

### A. Dataset and study period
The analysis uses the full cleaned January–March 2026 historical population. Detailed hourly weather comparisons in this subsection focus on observations classified as Clear or Rain. The source counts and population transitions are reported in [Table 1](record030_dataset_cleaning_flow.csv).

### B. Cleaning and retained observations
The three January–March 2026 input files contain 11,077,206 trips. Ten lie outside the pickup window [2026-01-01,2026-04-01), leaving 11,077,196. Combined finite-positive fare/distance and timestamp validity leaves 10,620,887 (456,309 excluded). The existing ≤100-mile source rule removes 478, yielding 10,620,409 cleaned trips. Record-029 revalidation removes zero additional rows. The denominator rule marks 9,017 historical rows unresolved, leaving 10,611,392 VALID epsilon observations. Inclusive simulation support retains 10,505,278; 53,057 valid observations below and 53,057 above remain historical data. Supported Clear/Rain scope contains 3,265,135 observations: Clear 3,050,121 and Rain 215,014.

Validity failure counts are overlapping audit counts, not additive sequential exclusions. The simulation-support restriction is distinct from data cleaning; excluded tails remain valid historical observations.

### C. Price-distance sensitivity calculation
The frozen references are P_base=21.34586956773507 USD, tau_P=±1.00 USD and L_base=3.01799878914405 miles. Price is TLC fare_amount. Sensitivity is epsilon=[(fare−P_base)/P_base]/[(trip_distance−L_base)/L_base]. The strict half-resolution rule abs(trip_distance−L_base)<0.005 mile leaves epsilon unresolved; distance resolution is 0.01 mile. No L_min is adopted. Simulation support is inclusive [−12.890744316473482,15.442447741158892]. These are project methodology decisions, not identified causal price elasticity.

### D. Undefined-denominator handling
The 9,017 resolution-sensitive observations remain in the historical population with unresolved epsilon. Neither these observations nor short trips are deleted. The denominator-resolution treatment precedes the separate empirical support restriction.

### E. Overall sensitivity statistics
Across all 10,611,392 VALID observations before simulation-support restriction, mean sensitivity is 0.647181, median 0.767172, and population SD 7.037255 (Table 1). These all-weather historical statistics must not be confused with supported Clear/Rain results. In the supported reporting population:

| weather_name | N | mean | median | population_SD |
| --- | --- | --- | --- | --- |
| Clear | 3050121 | 0.621737 | 0.734565 | 1.478379 |
| Rain | 215014 | 0.654704 | 0.779043 | 1.512583 |

The full authoritative VALID population contains 10,611,392 observations and has population SD 7.037255. The hourly Clear/Rain figures use the frozen P0.5–P99.5 supported population: empirical tails outside simulation support are excluded from those plots. Their lower plotted SDs reflect this population-definition difference, together with weather/hour grouping, rather than contradictory statistics.

### F. Hourly Clear/Rain results
[Table 2](record030_hourly_clear_rain_statistics.csv) reports N, mean, median, population SD and P05/P25/P75/P95 for each observed hour. Clear covers every hour; Rain lacks hours 05, 10, 11 and 12. [Figure 1](charts/record030_hourly_mean_clear_rain.png) presents means and [Figure 2](charts/record030_hourly_sd_clear_rain.png) presents SD separately, preserving gaps. Hourly fluctuations are descriptive, and the two curves need not rank weather conditions identically.

### G. Six-hour grouped presentation
[Table 3](record030_six_hour_group_statistics.csv) and [Figure 3](charts/record030_six_hour_clear_rain_comparison.png) use G1 00–05, G2 06–11, G3 12–17 and G4 18–23 for presentation only. Clear SD is 1.666147, 1.536148, 1.337078 and 1.530691, respectively; Rain SD is 1.942595, 1.538050, 1.209440 and 1.539304. Both have their lowest dispersion in G3 and highest in G1. These periods do not replace the simulation T groups.

### H. 8 AM–8 PM variability finding
Descriptive evidence of lower daytime dispersion: daytime (08–19) has lower dispersion than OTHER (20–23 and 00–07) in both weather conditions. Clear pooled SD is 1.383509 versus 1.651547 (difference −0.268038; ratio 0.837705), and Rain is 1.298893 versus 1.763551 (difference −0.464658; ratio 0.736521). Weighted mean hourly SD and median hourly SD show the same direction. This does not establish a continuous trend, a causal weather effect, or lower average sensitivity. [Table 4](record030_8am_8pm_variability_check.csv) reports pooled means, medians, SD and both hourly-SD summaries. Daytime is explicitly hours 08–19; OTHER is hours 20–23 and 00–07.

### I. Interpretation
Unequal weather/hour composition and absent Rain hours limit comparisons. Lower SD means lower dispersion, not necessarily lower mean sensitivity. Hourly and grouped results are descriptive; they do not establish causal price elasticity or causal willingness-to-pay.
