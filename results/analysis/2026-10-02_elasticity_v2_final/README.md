# Elasticity V2 — frozen offline methodology

Status: **ELASTICITY_V2_OFFLINE_FROZEN**. This package freezes existing approved outputs; no estimation or clustering was rerun.

Training: 2026-01-01 inclusive to 2026-04-01 exclusive. The project distance rule 0 < trip_distance <=100 miles removes 478 rows, retaining 10,620,409. The numerical cutoff is a project implementation decision, not a professor-specified cutoff.

P_base = 21.34586956773507 USD. L_base = 3.01799878914405 miles, the mean distance of 479,000 cleaned trips with fares within inclusive ±$1 of P_base. The ±$1 window is a project implementation decision implementing the professor's reference-point instruction.

Signed, dimensionless epsilon = ((L-L_base)/L_base) / ((P-P_base)/P_base). Exclude only exactly zero price-change denominators. No denominator threshold, epsilon clipping or normalization.

Clustering alone uses 1% per-tail trimmed WeatherCode/hour means, with missing positions completed from same-hour pooled 1%-trimmed trip epsilon. This is a project robustness decision. K-means uses K=3, seed=42, n_init=50, Lloyd, no scaling or trip weighting. The 225 observed and 111 filled features are not used as final observations.

Official mapping: Class 1 = 1,2,3,9,12,13,14,17,21; Class 2 = 5,8,15; Class 3 = 7,16. Final class/hour statistics use ALL actual untrimmed trip epsilon, population SD (ddof=0), and variance=SD². There are 68 observed groups. Class 3 hours 5,7,13,17 remain missing. Charts are unchanged copies of approved untrimmed-statistic charts.

**Limitations retained:** 5% trimming changes codes 5 and 15; seeds 1,10,100 differ from the official partition among six tested seeds. Weather classes are frozen operational groupings, not claimed uniquely identified natural clusters. See sensitivity_summary.json and its hashed source references. Freezing does not reverse those diagnostic findings.

Canonical files are in data/processed/elasticity_v2/: final_elasticity_methodology.json, weather_code_class_mapping_final.csv and elasticity_3_weather_classes_final.csv. Tables and methodology here are exact copies; methodology records source/output hashes and focused verification. Previous diagnostic history remains preserved. No production/runtime code was modified.
