# Denominator stability diagnostic

The validated Jan–Mar population is restricted to trip_distance <=100 miles for this diagnostic. Both global reference means are then recomputed from the retained population, once, and held fixed across scenarios. Signed epsilon is relative distance change divided by relative price change; no absolute-value transformation or clipping is applied.

A excludes only exactly zero price-change denominators. B–E independently apply the stated inclusive absolute relative-price thresholds. Excluded counts and percentages refer to the distance-cleaned population, separately from source-distance exclusions. Weather-hour summaries use observed groups and population SD (ddof=0); no missing groups are fabricated.

The comparisons do not select or authorize a denominator threshold. No operational definition of material stabilization was prespecified; compare successive changes in overall and weather-hour summaries. Canonical input and all canonical artifacts remain unchanged. No charts, clustering, or production changes.

Validation: finite retained epsilon, group-count conservation, monotone scenario counts, and unchanged canonical hashes. Verdict: PROFESSOR_DENOMINATOR_DECISION_REQUIRED.
