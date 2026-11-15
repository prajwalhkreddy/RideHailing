# V2 sensitivity contract and distribution selection

## Decision and scope

The operative denominator rule for this current V2 experiment is frozen as **abs(r_P)>=0.05**, inclusive, by the explicit project decision accompanying this task. The selected sampling representation is **EMPIRICAL_RESAMPLING_BEST_SUPPORTED**, status **REVIEWED_NOT_INTEGRATED**. This package freezes an offline sensitivity-population contract and evaluates sampling representations; it does not change production or assert that the wider V2 pricing architecture is ready.

Fare/meter resolution motivates a meaningful dead zone, while the selected rule is the scale-aware 5% relative band. The $0.50 and $1.00 alternatives are weaker at the current P_base and add no restriction. No separate dollar filter alters the selected population. The prior denominator audit's threshold-pending status is superseded for this experiment; historical records are not rewritten.

## References, units and source provenance

P_base=P_norm=22.354198442390455 USD; L_base=4.616983790655043 km. Values are **loaded**, not recomputed, from the preceding notation_contract.json; the original V2 numerical-reference provenance document is also hashed and linked in the contract. That provenance distinguishes the P_base derivation over [1,75)km from the current [1.5,75)km analytical population. This task retains those existing values; it does not quietly substitute the narrower-population fare mean or revise historical approval metadata. P_norm is not an operational fare floor.

Fare field is `fare`, derived from TLC `fare_amount` in USD, not total_amount. `trip_distance` is source miles; `distance_km=trip_distance*1.609344`. Calibration uses Jan1 inclusive through Mar16 exclusive, 2026. The existing Jan1–Mar15 source cache contains8,692,819 already-cleaned observations. Its positive-fare, positive-distance<=100-mile rules are asserted; current [1.5,75)km scope retains6,967,155. The1,725,664 outside that analytical scope are not newly classified as invalid. Source-invalid N=0 refers only to this already-cleaned analytical source, not to the unknown raw-data exclusion history.

The contract contains source paths and SHA256 hashes for both reference values, the source cache, preceding count evidence and regression benchmark. Weather is joined many-to-one by pickup hour using date-filtered monthly reads. Protected-date rows are never read. The source cache remains unchanged.

## Formula and population materialization

P_deviation_abs=abs(fare-P_base); r_P=(fare-P_base)/P_base; r_L=(distance_km-L_base)/L_base; epsilon=r_L/r_P. When abs(r_P)<0.05 the persisted epsilon is NaN, status DENOMINATOR_UNRESOLVED. It is never replaced with zero. Resolved epsilon<0 has status NEGATIVE_AUDITED_EXCLUDED; exact zero has NONNEGATIVE_VALID; positive epsilon has POSITIVE_VALID. Runtime candidates satisfy epsilon>=0. No negative-to-absolute transformation, clipping, winsorization, upper truncation or imposed epsilon_max occurs.

Effective dollar threshold: **1.1177099221195228 USD**. Both previous dual rules reproduce this same population. The denominator bound limits inverse-relative-price amplification to20; it does not limit epsilon to20 because r_L varies.

Canonical analysis materialization: `data/interim/pricing_v2_sensitivity/pricing_v2_sensitivity_population_jan01_mar15_2026.parquet`. The project's existing ignored large-data convention is used, without changing .gitignore or adding a binary to Git. The entire6,967,155-row scoped source is retained in order, including unresolved and negative statuses; select `is_runtime_candidate==True` to reconstruct the final5,779,213-row population exactly. This avoids losing historical provenance.

`source_observation_id` is the zero-based source-cache row position, defined jointly with that cache's SHA256, not an invented TLC identifier. The artifact preserves timestamp, fare, source miles, converted km, weather code, hour, P_deviation_abs, r_P, r_L, epsilon, source-valid and denominator-resolved flags, candidate flag, status and persisted fit/validation assignment. Metadata and binary hash are in the JSON contract and verification. Storage location does not imply runtime activation.

## Exact population reconciliation

| Stage | N | Percentage of scoped source |
|---|---:|---:|
| Scoped source / source-valid |6,967,155|100|
| Source-invalid within this already-cleaned scope |0|0|
| Denominator unresolved |353,234|5.069989|
| Denominator resolved |6,613,921|94.930011|
| Resolved negative |834,708|11.980615|
| Resolved zero |0|0|
| Resolved positive / final nonnegative |5,779,213|82.949396|

Resolved negatives are12.620471% of the denominator-resolved population. Unresolved+negative+nonnegative equals source N exactly. These counts and the nonnegative mean/SD match candidate C in the completed denominator-rule-selection audit. Nothing is silently discarded from the materialized historical table.

## Pooled empirical distribution

| N | mean | median | SD | minimum | maximum | skewness | excess_kurtosis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5779213.000000 | 1.807321 | 1.154356 | 1.990089 | 0.000082 | 286.512406 | 19.527461 | 1578.750738 |

| P001 | P01 | P05 | P10 | P25 | P50 | P75 | P90 | P95 | P99 | P995 | P999 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.011404 | 0.084324 | 0.346035 | 0.567107 | 0.881235 | 1.154356 | 2.341131 | 3.589487 | 4.705542 | 8.872682 | 11.064993 | 18.038551 |

Quantile names: P001=0.1%, P01=1%, P995=99.5%, P999=99.9%. Quantiles use linear interpolation; SD is ddof=0, skewness is the standardized third central moment and excess kurtosis subtracts3. The finite empirical maximum is an observed value, not a selected support cutoff. Pooled empirical resampling preserves that value and its frequency.

The denominator screen removes the local ratio singularity sufficiently to make finite distribution fitting well-defined on this population: SD falls from22.483278 before denominator screening to1.990089. It does **not** prove behavioural validity of every tail observation, remove all outliers or produce a light-tailed distribution. Skewness19.53 and excess kurtosis1578.75 make tail fidelity consequential. No additional tail treatment is introduced.

## Fit and held-out validation protocol

Within the final candidate rows in source order, NumPy default_rng(seed=42) generates one uniform draw per row: draw<0.8 is FIT, otherwise VALIDATION. Assignment is persisted and source IDs are disjoint. Fit N=4,623,641; validation N=1,155,572. This is a reproducible internal random-row distribution check, **not** a temporal generalization test or independent-day experiment. Repeated observed values are preserved in both sets; no deduplication or frequency flattening occurs. Only FIT rows determine fitted distributions. March16 is not used; March17–31 is excluded entirely.

Required candidates: empirical row resampling with replacement, Gamma, Weibull, Lognormal and Exponential. Parametric families use maximum likelihood with location fixed at0, with no upper support boundary. Gamma uses fixed-location MLE, Weibull uses its shape likelihood score root and corresponding scale, Lognormal uses sample mean/SD of log epsilon, and Exponential uses sample mean. No epsilon offset is added. Observed zero mass is0; a future non-negligible zero mass would require an explicit point mass/hurdle for strictly-positive families, not silent dropping or jitter. No hurdle fit is needed here.

All fits converged to finite parameters; fixed-location Gamma and Weibull score residuals are checked. Train log likelihood/AIC/BIC and held-out continuous log likelihood are recorded for parametric models. Empirical sampling is a discrete atomic distribution, so its continuous likelihood/AIC/BIC are **not comparable** and are left missing, not assigned artificial values. No significance p-value is used for selection.

Empirical candidate evaluation uses the **fit-set** empirical distribution analytically, rather than adding Monte Carlo sampling error. Uniform row sampling preserves duplicate frequencies. After selection, the reviewed deployment candidate is the full cleaned pool; held-out metrics always refer to the fit-only version. No production sampler is installed.

## Held-out fidelity

| candidate | mean_error_pct | SD_error_pct | KS_descriptive | Wasserstein |
| --- | --- | --- | --- | --- |
| Empirical_resampling | 0.042295 | -1.691093 | 0.001089 | 0.003810 |
| Gamma | 0.042295 | -30.275609 | 0.118157 | 0.248305 |
| Weibull | 0.890734 | -24.979164 | 0.108392 | 0.289251 |
| Lognormal | 3.160451 | -4.560042 | 0.093743 | 0.153402 |
| Exponential | 0.042295 | -10.402959 | 0.176996 | 0.308242 |

| candidate | quantile | validation_value | model_value | error_pct |
| --- | --- | --- | --- | --- |
| Empirical_resampling | P50 | 1.153495 | 1.155167 | 0.144922 |
| Empirical_resampling | P95 | 4.703620 | 4.705729 | 0.044847 |
| Empirical_resampling | P99 | 8.839465 | 8.881659 | 0.477333 |
| Empirical_resampling | P995 | 11.035871 | 11.083464 | 0.431259 |
| Gamma | P50 | 1.153495 | 1.458569 | 26.447806 |
| Gamma | P95 | 4.703620 | 4.560632 | -3.039951 |
| Gamma | P99 | 8.839465 | 6.537861 | -26.037814 |
| Gamma | P995 | 11.035871 | 7.370838 | -33.210181 |
| Weibull | P50 | 1.153495 | 1.434446 | 24.356467 |
| Weibull | P95 | 4.703620 | 4.808642 | 2.232796 |
| Weibull | P99 | 8.839465 | 6.860422 | -22.388719 |
| Weibull | P995 | 11.035871 | 7.703243 | -30.198141 |
| Lognormal | P50 | 1.153495 | 1.296339 | 12.383563 |
| Lognormal | P95 | 4.703620 | 5.265645 | 11.948781 |
| Lognormal | P99 | 8.839465 | 9.411553 | 6.471974 |
| Lognormal | P995 | 11.035871 | 11.640998 | 5.483279 |
| Exponential | P50 | 1.153495 | 1.252845 | 8.612973 |
| Exponential | P95 | 4.703620 | 5.414707 | 15.117871 |
| Exponential | P99 | 8.839465 | 8.323723 | -5.834536 |
| Exponential | P995 | 11.035871 | 9.576568 | -13.223264 |

CDF/KS statistics are descriptive: exact two-sample empirical CDF discrepancy for resampling, and maximum one-sample CDF discrepancy against the fitted continuous CDF for parametric candidates. Empirical Wasserstein is exact in one dimension; parametric Wasserstein is an approximate quantile integral on20,000 equal-probability midpoints and underweights the extreme endpoints. This approximation is labelled and is not the sole selection metric. Tail-probability errors at held-out P95/P99/P99.5/P99.9 thresholds appear in upper_tail_probability_comparison.csv, using strict exceedance consistently. Validation thresholds are evaluation locations, not fit inputs.

Lognormal has the strongest parametric likelihood and the smallest parametric CDF distance, but still shifts the median by12.38%, P95 by11.95%, and P99 by6.47%. Gamma/Weibull underestimate P99 by26.04%/22.39% and SD by30.28%/24.98%. Exponential's median error8.61% and CDF gap0.177 show that matching the fitted mean alone does not establish fidelity. No parametric family is preferred merely for analytic convenience or best AIC.

Empirical fit/validation CDF discrepancy is0.001089, median error0.145%, P95 error0.045%, P99 error0.477% and P99.5 error0.431%. Its SD differs by-1.69%, consistent with rare-tail allocation between the two large samples; it does not perfectly reproduce held-out tails. It nevertheless materially outperforms every required parametric alternative across the practical central/CDF/tail criteria. A single deterministic split is not proof of all-seed or temporal stability.

## Sampling recommendation

**EMPIRICAL_RESAMPLING_BEST_SUPPORTED.** It retains individual heterogeneity, zeros if later present, observed skew and duplicate frequencies without choosing an inaccurate smooth family. Runtime implementation would draw a uniform row index with replacement using a caller-controlled random generator. An epsilon-only float64 array of5,779,213 values is46,233,704 bytes (about44.1MiB), with constant-time indexing; this is a practical memory trade-off, not a measured runtime benchmark. It cannot invent unobserved extreme values or claim extrapolative tail coverage. Parametric alternatives offer compact parameters but no demonstrated advantage sufficient to offset their observed distortions here.

No mean/regression constant replaces sampled heterogeneity. Candidate status is REVIEWED_NOT_INTEGRATED. The sensitivity contract is ready for a separately authorized integration/validation step; this does **not** approve unresolved operational price, response, mask, zero-response or DQN-interface decisions elsewhere in V2. Production readiness is not asserted.

## Regression sanity benchmark

| population | N | mean_epsilon | median_epsilon | normalized_origin_slope | mean_minus_slope |
| --- | --- | --- | --- | --- | --- |
| RESOLVED_SIGNED | 6613921 | 1.332454 | 1.055828 | 1.732863 | -0.400410 |
| SIMULATION_NONNEGATIVE | 5779213 | 1.807321 | 1.154356 | 1.820784 | -0.013463 |

The prior candidate-C global and fixed representative Weather×Hour benchmarks are retained because the population is exactly reproduced. Normalized reference-centered slope=sum(r_P*r_L)/sum(r_P^2); raw km/USD slope is multiplied by P_base/L_base for comparison. It is a denominator-squared-weighted relationship, not an unbiasedness proof or a causal demand estimate. For nonnegative rows the mean1.807321 is near slope1.820784, while median1.154356 differs materially. Signed resolved rows are separately labelled and not confused with the simulation pool.

## Secondary weather/hour diagnostics

211 observed Weather×Hour cells;211 meet N>=50,210 meet N>=100;211 have SD<4 and0 have SD>=4. Every cell is calculated from the same final pool, with N, mean, median, population SD, P95 and P99. Missing cells remain absent. SD<4 is INTERNAL_STABILITY_DIAGNOSTIC only, not a gate for the pooled distribution or a fitted-family objective. No clustering, new weather classes or conditional runtime laws are created.

## Figures and reproducibility

- pooled_distribution_diagnostics.png: full cleaned population histogram/density, empirical CDF and log tail.
- density_comparison.png and cdf_comparison.png: held-out empirical versus fit candidates.
- qq_comparison.png: candidate quantiles versus held-out quantiles throughP99.99.
- upper_tail_comparison.png: log survival across the full observed range.
- central_quantile_comparison.png: central quantile fidelity.

Central views explicitly stop at validation/pooledP99.5 for readability; histograms retain full-population normalization rather than renormalizing the zoomed interval. All underlying observations enter fits and statistics. The log-tail plot's visible probability range does not truncate data or fits; probabilities below its display minimum are outside view. Empirical distributions are shown as histograms/steps, not mislabelled continuous PDFs.

reproduce_audit.py records the exact offline computation. CSV/JSON artifacts record parameters, moments, population reconciliation, fidelity, regression and secondary statistics. verification.json records hashes and focused checks. One JSON serialization issue after fits was corrected; completed data/fits were reused and independently read back rather than retrained. No model/DQN training occurred.

## Validation and final answers

1. The5% rule is reproduced exactly, including unresolved NaNs and disjoint sign statuses.
2. The final nonnegative pool contains5,779,213 observations.
3. Mean1.807321, median1.154356, population SD1.990089.
4. The denominator singularity is controlled for finite modelling, but residual heavy tails remain.
5. Empirical row resampling best preserves the cleaned population.
6. Required parametric families materially distort central and/or tail features, quantified above.
7. Empirical resampling is preferred, REVIEWED_NOT_INTEGRATED.
8. Secondary cells are well supported overall; the SD diagnostic is not a methodological acceptance criterion.
9. The offline sensitivity contract is complete and ready for integration review, not an authorization to activate runtime V2.

Source hashes unchanged; counts/moments match the previous audit; status partition, readback, source order, date bounds and fit/validation membership checked. Production/runtime, V1, checkpoints, replay and registry remain unchanged. No protected-period access, clustering, upper-tail trimming, sign conversion or DQN training.

## Conditional-runtime follow-up — 14 November 2026

The pooled denominator/sign/population contract above is unchanged. The current task requires WEATHER_TIME_CONDITIONED_V2 for authoritative training; pooled support becomes control/fallback rather than the sole runtime source. The time-preserving grouping analysis is complete but mapping freeze is blocked by temporal instability. See `../2026-11-14_pricing_v2_weather_time_conditioning/README.md`. No conditional runtime is claimed and no historical population or fit result was rewritten.

## Time-specific conditional runtime — current

The subsequent independent-T analysis freezes T1 K2 and explicitly uses T-pooled fallback for T2–T4. The global population and all historical distribution-selection results above remain unchanged. Conditional empirical sampling is version-isolated; full-day conditioned baseline validation is pending. See `../2026-11-14_pricing_v2_time_specific_weather/README.md`. Training has not started.
