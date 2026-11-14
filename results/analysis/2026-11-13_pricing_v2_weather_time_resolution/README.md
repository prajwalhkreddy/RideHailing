# Passenger Pricing V2 — weather/time resolution evidence

**Outcome: three-cluster stability is WEAK; final weather freeze is not justified by these results. Recommend historical T1–T4 for the next conditional analysis.**

New-e analysis covers 6,967,155 Jan1–Mar15 observations with 1.5≤distance<75 km and the specified candidate references. Primary standardized mean/SD clustering isolates codes 13 and 14; median/IQR and 1%-trimmed mean/SD instead isolate 16 and 17. Their agreement with the primary has ARI −0.158182. The latter code has only 596 observations from one date. No historical mapping was arbitrarily restored and no final selection was inferred from semantic names.

The prespecified primary candidate is WEATHER_GROUP_1={1,2,3,5,7,8,9,12,15,16,17,21}, WEATHER_GROUP_2={13}, WEATHER_GROUP_3={14}. This is a diagnostic candidate, **not a frozen or approved final mapping**. Combined with T1–T4 it has 12 possible/10 observed scenarios; 8 pass the proposed 5,000-positive gate and directly cover 99.941698% of trips. The 2 observed sparse scenarios fall back to weather-only. The robust alternative and 144-scenario comparison are documented separately.

## Files and schema

- `FINAL_WEATHER_MAPPING.csv`: all 14 raw codes, verified descriptions, primary and two robustness memberships, counts, event-date support, neutral labels, and explicit not-approved status.
- `WEATHER_CLUSTER_COMPARISON.csv`: filter `record_type=raw_weather_new_e_statistics` for the full requested raw-code count/mean/SD/quantile table. Other record types contain partition comparisons, feature scaling/silhouettes and pooled cluster statistics. **The earlier requested raw_weather_new_e_statistics.csv is consolidated here to honor the final five-file-only output instruction.**
- `TIME_GROUP_COMPARISON.csv`: record types distinguish full signed time statistics, primary weather/time statistics, pairwise time similarity, within-T half-hour resolution, and support/fallback summaries for all three clustering variants. Blank columns mean not applicable to that record type, not zero. JSON-valued cells contain only small label/count metadata, never trip arrays.
- `WEATHER_TIME_FREEZE_RECOMMENDATION.md`: authority, reproducible numerical procedure, exact mappings, historical agreement, caveats, time evidence, fallback evaluation and remaining decisions.
- `README.md`: this entry point.

CSV statistics retain numeric precision; Markdown displays are rounded for readability. Positive/negative/undefined percentages use total group N. Primary clustering uses all finite signed e; positive counts only assess prospective positive-support distribution fitting. `dates` counts distinct observed pickup dates, not independent experimental units.

## Status

THREE_CLUSTER_STABILITY=WEAK. T1_T4_SUPPORTED_UNDER_NEW_E=YES (descriptive operational candidate, not optimality proof). FINAL_WEATHER_MAPPING_APPROVED=NO. WEATHER_TIME_TAXONOMY_FREEZE_READY=NO. GROUPED_DISTRIBUTION_REFIT_REQUIRED=YES. P_BASE_POPULATION_ALIGNMENT=PROFESSOR_CONFIRMATION_REQUIRED.

No production implementation, training or simulation. March16 and March17–31 analytical rows excluded. No change to frozen historical methodology. Research decision needed on tail-sensitive versus robust weather similarity before a final exactly-three taxonomy can be recommended as stable; the 5,000 threshold and P_base remain unchanged.
