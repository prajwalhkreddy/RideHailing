# Singleton tail check — codes 15 and 16 only

Uses cleaned trip-level rows for these two codes and frozen P_base=21.34586956773507, L_base=3.01799878914405. Signed epsilon uses the approved relative changes and exact-zero denominator exclusion only (zero exclusions observed). No canonical data, official means or clustering artifacts changed; input/package hash checks passed. K-means was not rerun.

The distribution table covers all 35 actually observed code/hour groups. Driving-hour diagnostics cover (15,03), (15,05), (16,00), (16,23), including tail counts/shares and the existing Class-1 centroid. Population SD uses ddof=0. Quantiles use pandas linear interpolation.

Trimmed means are diagnostic only: sort each group's epsilon and remove floor(N*p) observations from each tail, with p=0.01 or 0.05. No values are deleted from official statistics. These percentages are per tail.

All four driving hours are descriptively TAIL_DRIVEN: medians lie near the Class-1 centroid, and trimmed means greatly reduce the unusual official mean excursions. Code 15 at 03:00 remains sensitive to trimming level (0.624 versus 1.637); code 16 at 23:00 retains some elevation at 1% trimming (1.628) but approaches the centroid with 5% (1.065 versus 1.014). Thus this does not establish identical distributions or absence of broader differences. Classifications use actual values without a formal threshold.

Verdict: CLUSTER_ASSIGNMENT_TAIL_SENSITIVE. No alternative estimator, trimming rule, or new assignment is adopted.
