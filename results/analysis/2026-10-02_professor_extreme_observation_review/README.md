# Professor extreme-observation inspection

Current unfiltered Jan–Mar population: 10,620,887 rows. Global P_base=21.351866450514009 USD and L_base=6.4543849058934528 miles, recalculated over the whole population and verified against canonical bases. Signed epsilon uses relative distance change divided by relative price change. No exact-zero denominators or nonfinite epsilon occurred. No distance filtering, denominator threshold, clipping, normalization, clustering, or validity classification was applied.

The named `notebooks/plan/Professor_Guidance_Elasticity_2026-10-02.pdf` was absent at execution. This package follows the user's explicit instructions; the PDF has not been verified.

`long_distance_over_100_miles.csv` includes every >100-mile observation, descending distance. `epsilon_abs_ge_1000.csv` includes every observation meeting the inclusive absolute-epsilon threshold, descending absolute epsilon; its top-100 companion is an exact prefix. Both include fare per mile and global descending distance rank (minimum rank for ties). Overlap counts describe association, not proven causes or validity. Distance/fare correlations are descriptive only.

Both scatterplots retain all 478 long-distance records. The supplementary plot uses logarithmic x and y axes without altering source values. Full five-column arrays are saved at `data/processed/elasticity_v2/professor_price_distance_arrays_2026_01_03.parquet`. The companion `professor_price_distance_arrays_2026_01_03_sample10000.csv` here samples 10,000 rows without replacement using pandas random_state=42, then restores source order. No full-population CSV is created.

Validation passed: global bases matched, exported arrays matched all input rows/fields, subset counts and overlap partitions reconciled, and all pre-existing canonical file hashes remained unchanged. No production changes.
