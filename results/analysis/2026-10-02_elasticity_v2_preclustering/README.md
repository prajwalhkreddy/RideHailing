# Preliminary elasticity V2 — before 3-class clustering

Input: validated Jan–Mar 2026 parquet, unchanged; its hash and exact window are in `global_bases.json`.
One global fare mean and distance mean are calculated from all 10,620,887 rows. Relative distance change is divided by relative price change. Only exact zero price-change denominators are excluded. Signed dimensionless epsilon is retained without caps, clipping, trimming, or near-zero thresholds.

`summary.json` records denominator, sign, nonfinite, tail and overall diagnostics. Shares use valid epsilon N. SD is population SD (ddof=0); variance is its square. `extreme_epsilon_top20.csv` preserves the 20 largest absolute epsilon observations for inspection; none are removed.

The preliminary table contains observed code/hour groups only. The 14×24 matrix explicitly retains NaN in missing positions. Median is diagnostic only. Charts use full linear axes and show original codes, not final classes. Missing-hour handling must be decided before clustering; no imputation or K-means is performed.

Canonical bases and both tables are in `data/processed/elasticity_v2/`; copies here are identical. Reproduce with `MPLCONFIGDIR=/tmp/m10_mpl_cache python scripts/build_elasticity_v2_preclustering.py`. No runtime or simulation changes.
