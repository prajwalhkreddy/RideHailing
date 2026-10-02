# Professor-guided L_base reference comparison

Source cleaning retains 0 < trip_distance <=100 miles as a PROJECT_IMPLEMENTATION_DECISION, not a professor-specified cutoff. Exactly 478 rows were removed into a separate cleaned canonical input; the original is unchanged. Provenance and hashes are in `data/processed/elasticity_v2/source_cleaning_manifest.json`.

P_base is one mean fare over the cleaned population. Four candidate L_base values are mean distances among trips within inclusive ±$0.25, ±$0.50, ±$1 and ±$2 fare windows. Each candidate is then evaluated across the entire cleaned population, not only its fare window. Only exact-zero relative-price denominators are excluded; signed epsilon is retained without clipping, normalization or a denominator threshold. All SDs use ddof=0.

Adjacent L_base percentage changes divide the absolute change by the previous (narrower-window) value. No window is selected or frozen. Full numerical comparisons are in the three CSVs and summary.json. Weather-hour summaries use observed groups only. No charts, clustering, or production changes.

Focused checks passed: 478 exclusions, unchanged original hash, exact cleaned parquet roundtrip, source-distance rule, recomputed global price, independent fare-window membership, ratio algebra, exact-zero-only denominator exclusion and signed epsilon retention (including synthetic near-zero checks).
