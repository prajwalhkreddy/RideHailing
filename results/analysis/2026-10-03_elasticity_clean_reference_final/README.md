# Final actual-weather elasticity — clean reference

Status: CLEAN_REFERENCE_ELASTICITY_FINAL. Authority: notebooks/plan/Passenger_Price_Sensitivity_Implementation_Steps_Clean.pdf, interpreted under the user's explicit instruction that three weather classes mean actual observed Clear (1), Rain (8), Snowfall (15). No K-means or weather reduction is performed.

Both global references are arithmetic means over ALL 10,620,409 cleaned Jan–Mar 2026 trips: P_base=21.34586956773507 USD; L_base=3.46907003958134 miles. The existing project source rule 0 < trip_distance <=100 miles is unchanged. Bases do not vary by weather, hour, month or OD and are calculated before selecting the three conditions.

Signed dimensionless epsilon = ((trip_distance-L_base)/L_base)/((fare-P_base)/P_base). Only exactly zero price-change denominators are excluded (none observed). No absolute-value conversion, denominator threshold, clipping, normalization, trimming or imputation. Population SD uses ddof=0; variance=SD². Existing timezone-naive taxi/weather alignment is retained.

Clear has 24 observed hours; Rain 20 (missing 5,10,11,12); Snowfall 20 (missing 0,4,20,22). Tables contain 64 observed groups only. Charts use full linear axes with gaps and no trimmed/clipped values. Weather labels follow the project's preserved Meteostat coco definitions and the explicit approved Snowfall display label.

SUPERSEDED FOR THIS FINAL ANALYSIS: the previous ±$1 fare-window L_base (3.01799878914405 miles) and K-means/weather-class analysis. All earlier files are preserved, unchanged, as diagnostic history. Final “classes” here refer only to actual Clear/Rain/Snowfall conditions.

Canonical output: data/processed/elasticity_v2/elasticity_actual_weather_clean_reference_final.csv, byte-identical to the result table. summary.json records source provenance, full support, ranges and focused verification. No production/runtime changes.
