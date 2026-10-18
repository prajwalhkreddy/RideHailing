# Final professor-approved two-scenario passenger sensitivity analysis

## Final Two Weather Scenarios

The original dataset contains 14 Meteostat weather codes. For the final passenger-sensitivity analysis these are consolidated into two analytical scenarios:

- **CLEAR (display: Clear)** = non-precipitation conditions: 1 Clear, 2 Fair, 3 Cloudy, 5 Fog.
- **RAIN (display: Rain)** = precipitation conditions, including liquid, frozen and mixed precipitation: 7 Light Rain, 8 Rain, 9 Heavy Rain, 12 Sleet, 13 Heavy Sleet, 14 Light Snowfall, 15 Snowfall, 16 Heavy Snowfall, 17 Rain Shower, 21 Snow Shower.

“Clear” does not imply literally clear skies for every observation. “Rain” is an analytical precipitation label and includes snow/sleet. Original Meteostat code/name remain retained for traceability. This is the professor-approved analytical mapping, not the earlier data-driven K=2 split.

## Population and unchanged method

Use existing authoritative epsilon with epsilon_status=VALID and inclusive frozen support [−12.890744316473482,15.442447741158892]: **10,505,278 observations**. Epsilon is not recomputed. Record-029 references, denominator treatment and simulation methodology remain unchanged. No runtime weather classification or passenger acceptance is modified by this analysis.

## Final pooled results and strict SD rule

| final_weather_scenario | N | percentage | mean_epsilon | median_epsilon | population_SD | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| CLEAR | 9613456 | 91.510724 | 0.651731 | 0.766558 | 1.440831 | ACCEPT |
| RAIN | 891822 | 8.489276 | 0.650875 | 0.775522 | 1.484481 | ACCEPT |

Population SD is computed directly from all constituent supported observations (ddof=0), not averaged over weather-code SDs. Independent pooled-hour variance checks include between-hour mean differences. ACCEPT iff SD<4, EXCLUDE iff SD≥4; decisions use unrounded values. Both scenarios pass independently.

## Hourly and six-hour presentation

Each final scenario has observations in all 24 hours: 48 hourly rows total. There are eight six-hour rows, using 00–05, 06–11, 12–17 and 18–23. These are presentation periods only, not the frozen simulation time groups. The new plots use these final pooled observations, never the old literal code-1/code-8 curves.

## Old versus final scope

The old literal comparison selected only codes 1 and 8: 3,050,121+215,014=3,265,135 observations. The final mapping covers every supported code and adds **7,240,143** observations to the reporting scope, without changing support or source rows. Increases are 6,563,335 in Clear and 676,808 in Rain.

| definition | final_weather_scenario | N | mean_epsilon | median_epsilon | population_SD |
| --- | --- | --- | --- | --- | --- |
| OLD_LITERAL | CLEAR | 3050121 | 0.621737 | 0.734565 | 1.478379 |
| OLD_LITERAL | RAIN | 215014 | 0.654704 | 0.779043 | 1.512583 |
| FINAL_ANALYTICAL | CLEAR | 9613456 | 0.651731 | 0.766558 | 1.440831 |
| FINAL_ANALYTICAL | RAIN | 891822 | 0.650875 | 0.775522 | 1.484481 |

## Traceability and files

Every new CSV retains weather_code, original_weather_name and final_weather_scenario. In pooled aggregate rows, weather_code and original_weather_name are aligned semicolon-separated constituent lists, because a pooled statistic has multiple original codes; no single original code is fabricated. The mapping CSV has one row per original code. The original authoritative Parquet remains unchanged; added labels exist only in the analytical working frame and outputs.

- final_weather_2scenario_mapping.csv: exhaustive one-to-one original-code mapping, counts and percentages.
- final_clear_rain_statistics.csv: final pooled summaries and strict decisions.
- final_clear_rain_hourly_statistics.csv: 48 observed scenario/hour summaries.
- final_clear_rain_six_hour_statistics.csv: eight presentation summaries.
- old_vs_final_clear_rain_comparison.csv: literal versus analytical scopes on the same support.
- charts/final_clear_rain_hourly_mean.png and charts/final_clear_rain_hourly_sd.png: final hourly plots.
- charts/final_clear_rain_six_hour_comparison.png: mean and population SD panels.
- finalize_two_scenarios.py: reproduction entry point for this final representation.

## Diagnostic provenance

The previous Heavy Snowfall versus all-other-weather K=2 mapping, manual three-bucket references, unrestricted analysis and their figures/CSVs are retained as diagnostic history only. They are NOT the final weather representation. Prior supported-clustering README is preserved as README_supported_clustering_diagnostic.md; unrestricted report remains README_unrestricted_diagnostic.md. Earlier reproduction scripts reproduce historical diagnostics and must not be mistaken for the current final mapping.

## Validation and interpretation

CLEAR+RAIN counts, original-code counts, hourly counts and six-hour counts each reconcile to 10,505,278. All 14 codes map exactly once; source_row_index is unique and final labels are exhaustive, so no supported observation is dropped or duplicated. Protected source/Record-029/Record-030/runtime/config hashes were checked unchanged. Figure values match their CSV statistics. All calculations are descriptive; no predictive/RL training or causal willingness-to-pay inference is performed.
