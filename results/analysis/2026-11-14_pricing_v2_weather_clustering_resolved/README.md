# V2 weather clustering — SD<=1 resolved feasibility check

**No valid K exists under the specified positive-e population and intact weather scenarios.** The representation conflict is resolved. All14 individual positive-e SDs exceed1; average-linkage K1–14 yields105 failed clusters. The pooled-variance inequality also proves that no alternative partition of these intact scenarios can meet the rule.

Primary: POSITIVE_VALID; features unscaled mean/SD; Euclidean average linkage; no seed, trimming, semantics, hourly vectors or old epsilon values. N_positive=5,975,653. Diagnostic signed N=6,967,155. Candidate references unchanged. Threshold<=1 inclusive.

Files:
- RAW_WEATHER_NEW_E_STATS.csv: 28 rows, signed and positive statistics for14 codes; percentages/date coverage explicitly scoped in validation.
- WEATHER_K_SEARCH.csv: all105 candidates, merge distances, pooled moments, pass/fail and same-membership signed diagnostics.
- FINAL_WEATHER_MAPPING.csv: header only because no accepted partition exists; not a runtime mapping.
- WEATHER_CLUSTER_VALIDATION.md: method, proof, numerical checks, rare-code limitations and preserved decisions.

Final-K standardized agreement/ARI/stability NOT_APPLICABLE. No final weather×time counts or fallback counts can be asserted. T1–T4 and5000-positive gate retained. GROUPED_DISTRIBUTION_REFIT_REQUIRED=YES; WEATHER_TAXONOMY_FROZEN=NO.

{'EVIDENCE_READY': 5, 'ENGINEERING_READY': 4, 'PROFESSOR_CONFIRMATION_REQUIRED': 8, 'BLOCKER': 4}

No implementation/training/protected analytical-row access. No full distribution fitting. Historical artifacts unchanged.
