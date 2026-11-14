# V2 semantic weather/time calibration

Semantic verification PASS. **Weather mapping and T1–T4 frozen by explicit user decision; distribution families remain unapproved.** Elasticity clustering no longer selects meteorological membership.

NON_PRECIPITATION={1,2,3,5}; RAIN={7,8,9,17}; SNOW_FROZEN={12,13,14,15,16,21}. Twelve scenarios observed; ten meet 5,000 positive observations, covering 99.8492498% of trips by direct-fit eligibility. Rain T2 and Snow/Frozen T2 use weather-only fallback pools. All 12 scenarios require academic family confirmation because the compared families have substantial tail mismatch or inverse-moment/convergence problems. No fallback distribution is silently activated.

Files:
- `V2_WEATHER_MAPPING.csv`: code descriptions, semantic rationale and provenance.
- `V2_WEATHER_TIME_COUNTS.csv`: all counts, shares, flags, support classification, fallback pool and family status.
- `V2_GROUP_DISTRIBUTION_FITS.csv`: 36 fit comparisons, including two weather-only fallback pools. AIC leaders are not approved selections.
- `V2_WEATHER_TIME_FREEZE.md`: method, fit diagnostics, weather statistics, decisions and limitations.

P_base population alignment remains unresolved. Overall V2 freeze readiness NO. No production implementation, training, clustering rerun or protected analytical-row access. Historical artifacts unchanged. Only these five files and the three authorized final-freeze report files are updated.
