# Elasticity V2 — three weather classes

Frozen reference: Jan–Mar 2026, project distance rule 0 < distance <=100 miles, global P_base and L_base from the approved inclusive ±$1 fare window. Signed epsilon excludes only exact-zero price-change denominators. No clipping, denominator threshold, or normalization.

K-means uses each of 14 original weather codes once, with 24 hourly mean features; K=3, random_state=42, n_init=50, Lloyd algorithm, no sample weights or scaling. Classes are numbered by ascending smallest member code, without semantic weather names.

Exactly 111 missing clustering cells use the same-hour pooled mean of actual trip epsilon. All 225 observed cells stay unchanged. The mask records 1 for clustering-only fills, 0 for observations. This is a project clustering-completion decision. Sparse-code assignments can depend strongly on fills; silhouette is descriptive and does not choose K.

The final table maps actual trips to classes and aggregates their original epsilon, using population SD and variance=SD². No imputed matrix value enters final statistics. Absent groups would remain absent. Cluster centroids are unweighted averages of completed weather-code vectors and are not final trip-weighted class curves.

Charts use full linear axes without trimming. The diagnostic plot marks filled points with × and centroids with dashed black lines. summary.json records membership, trip/weather-hour shares, metrics, reference provenance and focused verification. No production changes.

Review status: CLUSTERING_RESULT_REQUIRES_REVIEW. Class 1 holds 12 codes and 98.8407% of trips; codes 15 and 16 form singleton classes. The actual-trip table contains 59 groups, with 13 unsupported groups left absent. This imbalance and the 111 clustering-only filled cells require interpretation before adoption.
