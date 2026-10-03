# Final actual-weather passenger elasticity

Status: ACTUAL_WEATHER_ELASTICITY_FINAL. Latest analysis direction: notebooks/plan/price elasticity2.docx. This comparison selects actual observed conditions, not fitted weather classes.

WeatherCode 1 = Clear, 8 = Rain, 15 = Snowfall. The existing project weather pipeline preserves Meteostat coco codes; provider definitions: https://dev.meteostat.net/formats.html#weather-condition-codes . The user explicitly approved authoritative “Snowfall” in place of the document's shorthand “Snow”.

Jan–Mar 2026 cleaned population, 0 < distance <=100 miles. Global P_base=21.34586956773507 USD and L_base=3.01799878914405 miles, independently reproduced from the full cleaned population (L_base from 479,000 fares within inclusive ±$1). References are not recomputed for selected weather subsets. Signed dimensionless epsilon uses relative distance change / relative price change; exact-zero denominator exclusion only. No trimming, threshold, clipping, normalization, clustering, or imputation. Population SD uses ddof=0; variance=SD².

Clear has 24 observed hours, Rain 20, Snowfall 20: 64 table rows. Rain lacks hours 5,10,11,12; Snowfall lacks 0,4,20,22. Missing groups remain absent in tables and gaps in plots. Weather-hour counts refer to persisted monthly weather; trip counts use actual cleaned epsilon observations. Existing timezone-naive timestamp alignment is retained.

Previous weather-class/K-means outputs: **SUPERSEDED_FOR_FINAL_WEATHER_COMPARISON**. Those folders remain unchanged as diagnostic history; no production/runtime integration is performed.

The canonical data/processed/elasticity_v2/elasticity_3_actual_weather_conditions_final.csv is byte-identical to the result table. summary.json records support, ranges, source hashes and focused checks. Both final charts use full linear axes and all actual untrimmed group statistics.
