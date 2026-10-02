# Weather-cluster robustness diagnostic

Only existing final-preclustering and clustering CSV artifacts were read. No input, mapping, methodology or production files changed. Euclidean centroid distances use the unchanged completed matrix. Margins are second-best minus assigned distance. Contribution columns are squared distances; shares are fractions, not percentages.

Codes 15 and 16 are singleton clusters: their assigned centroid residuals are zero up to floating-point error, so assigned imputed shares are undefined. The separately named Class-1 comparison decomposes their separation from the main cluster into observed and filled positions; it does not claim a causal ablation result.

Hourly comparisons include observed hours only. Median, P95, P99, min and max are unavailable in the permitted final-method artifacts and remain blank, with an explicit status column. Means and SD cannot establish tail dominance. Completing that portion requires authorization to read cleaned trip-level data and recompute these diagnostics with frozen references; older-method quantiles are not interchangeable.

K=3 reruns use seeds 0,1,2,10,42,100, n_init=50, Lloyd, no scaling or weighting. Labels are aligned by the permutation maximizing agreement with the canonical mapping. This tests initialization only, not robustness to samples, tails or imputation. Verdict: CLUSTER_ASSIGNMENT_REQUIRES_REVIEW.
