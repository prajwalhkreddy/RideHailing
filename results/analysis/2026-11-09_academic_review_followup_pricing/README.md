# Academic Review Follow-up — Passenger-Sensitive Pricing V1

**Analysis only. NO_METHODOLOGY_CHANGE_YET. FURTHER_TRAINING_REMAINS_PAUSED.**

Read the [academic review report](academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md), then the [chart index](academic_review_summary/CHART_INDEX.md) and [master numerical summary](academic_review_summary/master_results.csv).

## Scope and findings

- Cleaned Jan1–Mar15 fare-distance N=8,692,819; TLC fare_amount in USD; source miles converted to km before all analysis.
- VALID finite nonzero signed epsilon N=8,685,488; frozen supported positive N=8,598,805; support exactly reconciled.
- No minimum-fare flat-distance region established: $0.01 observations cover widely varying distances. Quantile candidates are descriptive, not L_flat selections.
- Existing action range covers 14.379972710808772% of observed fares; weak coverage of broad fare-distance levels, distinct from earlier moderate bounded-experiment justification.
- March16 counterfactuals use the existing 2,838-row export only, producing 19,866 request/action rows. These are threshold-rule outcomes, not observed causal demand or dispatch simulations.

## Artifacts and conventions

`fare_distance/`: full descriptive statistics, populated 0.5/1-km bins, distance bands, minimum-fare bands and charts.

`sensitivity_distribution/`: signed, absolute and T0 statistics; sign/near-zero/range counts, intervals, shape metrics, bounded actual extremes and charts.

`acceptable_price/`: empirical-quantile formula illustrations, same-distance examples and paired historical raw-preference categories. Illustration rows are not actual passengers.

`counterfactual_acceptance/`: saved March16 requests crossed with seven offers; global and grouped acceptance curves. No simulation.

`action_space_validation/`: historical factors, inclusive-range coverage and distance-conditioned coverage with figures.

`reference_value_review/`: frozen-versus-restricted comparisons and descriptive windows around L_base; no reference change.

`academic_review_summary/`: full review narrative, current-decision/evidence matrix, chart index and headline metrics.

Bins are lower-inclusive/upper-exclusive; observed groups only. Quantile windows/support are inclusive, using linear interpolation. SD uses ddof=0 except explicitly labelled sample SD. Shape moments use bias=True empirical moment estimates. Full-range histograms retain tails; the signed central figure alone displays P1–P99. Raw protection counts overlap category rows and must not be summed with them. Low-fare bands overlap each other. No fare components beyond fare_amount are available to explain unusual records.

The authoritative Parquet is read with a Jan1–Mar15 predicate, as in existing V1 calibration, and the selected rows are checkpointed in `jan01_mar15_analysis_cache.parquet`. Protected-date rows are not selected into the analysis. `progress.json` records completed work; `analysis_results.json` preserves numerical summaries. No checkpoint/model is opened, no source evidence is written, and no production module is imported.

## Review classifications

`EMPIRICAL_FLAT_FARE_REGION = NOT_SUPPORTED`  
`SIGNED_EPSILON_ANALYSIS_COMPLETE = YES`  
`CURRENT_T0_SUPPORT_CONSISTENT_WITH_NEW_ANALYSIS = YES`  
`COUNTERFACTUAL_ACCEPTANCE_ANALYSIS_COMPLETE = YES`  
`FIXED_GLOBAL_ACTION_SPACE_EMPIRICAL_COVERAGE = WEAK`  
`P_BASE_EMPIRICAL_SUPPORT = MODERATE`  
`L_BASE_EMPIRICAL_SUPPORT = MODERATE`  
`L_BASE_EQUALS_L_FLAT = NOT_ESTABLISHED`  
`METHODOLOGY_CHANGE_RECOMMENDED_BEFORE_REVIEW = NO`  
`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`  

These qualitative classifications are not new automatic methodology gates. Support consistency means numerical reconciliation, not behavioural validation. Reference support reflects provenance and descriptive alignment, not universal tariff validity.

## Validation

See [validation.json](validation.json) for population, support, coverage, mask and subgroup reconciliation checks. No training, methodology change or March17–31 evaluation occurred.
