# Passenger Pricing V2 — pre-implementation decision closure

Primary artifact: [V2_METHODOLOGY_DECISION_SHEET.md](V2_METHODOLOGY_DECISION_SHEET.md). Machine-readable register: [V2_DECISION_STATUS.csv](V2_DECISION_STATUS.csv).

## Original scope contract (read from existing CSV)

- **EVIDENCE_READY_FOR_FREEZE**: EPSILON_ORIENTATION, UPPER_DISTANCE_CUTOFF, P_BASE_PRECISION.
- **MORE_ANALYSIS_REQUIRED**: EPSILON_DISTRIBUTION, NYC_LOWER_BOUND, NYC_UPPER_BOUND.
- **ACADEMIC_INTERPRETATION_REQUIRED**: EPSILON_POPULATION, EPSILON_SIGN, EPSILON_ZERO_RULE, LOWER_DISTANCE_CUTOFF, MIN_BIN_COUNT, SPARSE_BIN_SEMANTICS, L_BASE, ACTION_FACTORS, ACTION_COUNT, ACCEPTANCE_SEQUENCE, REJECTION_REWARD, REQUEST_GENERATOR.
- **BLOCKED_BY_MISSING_FORMULA**: PRICE_GENERATION_FORMULA.

## Bounded work and result
Only the three MORE_ANALYSIS_REQUIRED items were advanced, all to ACADEMIC_INTERPRETATION_REQUIRED. Completed fit/support evidence cannot justify a universal family; completed quantile coverage cannot choose normative lower/upper fare caps. No analysis was rerun. No other status changed. Final counts:19 total,3 evidence-ready,15 academic,0 more-analysis,1 missing-formula blocker. Eight grouped approval questions replace the longer list.

Read sources: prior decision table/summary, context-audit preconditions, saved fit rankings, fare quantile coverage, source-contract table and supplied PDF pp3/6–9. Equations checked directly using pypdf text extraction. Source direction is explicit; complete generated-price/action/response composition is not. PDF bin-first generation is explicit, but replacement of the existing joint generator is unresolved; the sheet labels this UNCLEAR rather than claiming no directive exists.

Validation:19 unique IDs and original decisions preserved; only3 allowed status transitions; requested CSV columns present; counts3/15/0/1 verified; primary sheet contains eight approval questions and all19 decision entries; consulted inputs below unchanged by SHA256. This is a document/content check, not a runtime test. Approximately4–6 printed pages is a target, not a rendered-page assertion. Only these three new files were written; no production, V1, historical data, checkpoint, root README or existing reports changed. No analytical rows, March16 request rows or March17–31 rows were opened during this task. No training or simulation.

## Source fingerprints

- `results/analysis/2026-11-13_pricing_recalibration_decision_analysis/decision_support/ACADEMIC_DECISION_TABLE.csv`: `351f715522ae6b3f6d69d5d01c8c3cbef53cc4fff2f51da0831dde42223de142`
- `results/analysis/2026-11-13_pricing_recalibration_decision_analysis/decision_support/ACADEMIC_RECALIBRATION_DECISION_SUMMARY.md`: `e1d31855fcfe30c80401088aa0388869d55dc0bdf4b85ed92640ea8eaeba8773`
- `results/analysis/2026-11-13_pricing_recalibration_decision_analysis/fare_bounds/quantile_clipping_effects.csv`: `eb8d1d3986dff01a8ef455ff82307145eaad923ef75e640e78d033ee2403131c`
- `results/analysis/2026-11-13_pricing_recalibration_decision_analysis/distribution_fits/best_within_scenario.csv`: `5548b153c84730ea48aadb427eb3d278c9d7e5492d028501c7c1e1168d460af3`
- `notebooks/plan/Passenger Price Sensitivity and NYC Fare Calibration.pdf`: `6bff09ca3e92acfead77117723b793cc594861d5b08274b15533d4e5aa2f7540`
