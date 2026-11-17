# Passenger-sensitivity methodological decision evidence

## Scope and decision status

This offline analysis reuses the provisional binned calibration, its 32 family
evaluations and existing January 1–March 15 intermediate data. No active simulation,
pricing, sampler, references or model artifacts were changed. No training or full
simulation was performed. March 16 is not used for calibration; March 17–31 is not
read. Recommendations below are not silent freezes or claims of final compliance.

## Bin weighting and target population

The opt-in sampler currently samples occupied positive distance-bin estimates
uniformly, preserving duplicate values. A passenger's own distance does not select
its epsilon. Each bin's original count is in `bin_request_counts.csv`.

| Pooled empirical weighting | Mean | Population SD | Median | P05 | P95 | Effective bin count |
|---|---:|---:|---:|---:|---:|---:|
| Uniform 147 bins | 2.257965 | 0.339971 | 2.330456 | 1.631466 | 2.713919 | 147.00 |
| Historical request counts | 1.715299 | 0.416015 | 1.503911 | 1.356305 | 2.532622 | 14.67 |

Both supports are [1.3563048375726, 2.856160057081828]. Quantiles use the inverse
weighted empirical CDF, not interpolated quantiles from earlier reports. The
1.5–2.0 km bin alone represents 993,072 requests. Count weighting concentrates
mass in common distances; it does not recover within-bin passenger heterogeneity.
Uniform weights represent equally weighted occupied distance intervals, not the
historical trip-distance distribution.

Master §3.1 says to form a distribution of the resulting interval estimates and
does not explicitly instruct count weighting. **Recommendation: retain uniform
bin sampling provisionally as the most literal master implementation.** If the
intended target is explicitly the historical passenger-distance mix, count
weighting is the corresponding alternative, but requires an explicit estimand
choice. Neither estimator alone identifies individual passenger preferences.
Do not choose weighting by whichever produces preferred acceptance or lower SD.

Conditional fits use equal bin weights. They do not preserve passenger proportions
within each pool. Across conditions, runtime weather/time selects the pool; pools
are not sampled uniformly. `assigned_population_proportions.csv` contains disjoint
counts summing to 6,967,155 and fractions summing to one. Fitting pools overlap and
must not have their percentages summed. Conditional nonpositive-bin exclusion
also changes represented request mass, disclosed per pool in the weighting table.

## References

Existing common references remain **Pbase = 22.354198442390455 USD** and
**Lbase = 4.616983790655043 km**. Pbase is a count-weighted fare mean from the earlier
[1,75) km scope; Lbase is an interpolated fare-distance crossing. Master §3.1 instead
specifies an observed fare nearest the selected base fare and an average of chosen
representative distances near the selected base distance. These constructions are
not mathematically equivalent.

Conditional on treating the existing Pbase as the selected target, the nearest
observed eligible fare is **$22.35**, with 408 observations. Holding Lbase unchanged,
this changes pooled bin epsilon by at most **0.01718516**, with mean signed change
**−0.00055276**. This is a one-component sensitivity check, not a faithful complete
reference pair. The selected targets and representative-distance/nearness rule
are unspecified, so a complete alternative Lbase cannot be computed without
inventing a decision. Retain both references provisionally; do not replace them
from this diagnostic alone.

## Weather evidence and information boundary

Existing processed temperature (°C) and wind (km/h) cover all eligible calibration
trips. The earlier alignment audit verified 3,552 half-hour weather slots, including
existing filling. This is not raw measurement completeness. Current weather-hour
outcomes cover **1,775 hours**, not 6.97 million independent weather observations.
No eligible outcome exists at March 8 02:00; none is fabricated. Hours are serially
correlated, so even 1,775 is not an effective-independent-sample estimate.

`conditional_weather_support.csv` reports variation, dates, support and Spearman
associations within each assigned condition. T1_G1 and T2–T4 have broad within-group
temperature/wind variation. Assigned RAW_13 has only two hours on one date, entirely
in validation; RAW_15 has four hours on three dates, entirely in training. Their
correlations cannot support a conditional extension. These assignment supports
are distinct from the larger all-time RAW fitting pools.

Existing assigned groups explain only **4.88%** of hourly temperature variance and
**2.17%** of wind variance. Raw weather codes alone explain **7.10%** and **4.68%**;
T groups alone **4.87%** and **2.17%**. These are descriptive variance decompositions,
not independent causal effects. Temperature–wind correlation is −0.0827. Existing
categories are not a proxy for all continuous-weather variation.

A bounded association probe predicts the median positive elasticity of occupied
hourly distance bins. It is not a passenger distribution or implemented conditional
sampler. Train January–February; validate March 1–15. One observation per hour:
1,416 train and 357 comparable validation hours. The two unseen RAW_13 validation
hours are reported and excluded from this regression comparison, not fabricated
or silently assigned new intercepts. No temperature/wind bins or thresholds are used.

| Descriptive hourly predictor | Validation MAE | RMSE |
|---|---:|---:|
| Existing group intercepts | 0.196503 | 0.258529 |
| Group intercepts + temperature/wind | 0.231991 | 0.295726 |
| Group intercepts + mean distance control | 0.177438 | 0.235559 |
| Same distance control + temperature/wind | 0.217520 | 0.277893 |

This does not support promoting the tested parsimonious linear extension. It does
not establish absence of weather dependence: the outcome is noisy, positive-only,
composition-dependent, and the validation period has seasonal shift. Additional
stratification is not justified by these results and would invent cut points.
Approach A remains the provisional baseline; B has no evidence-backed extra bins;
C was evaluated only as an offline association probe and is not selected.

The master nevertheless requires accounting for CNN temperature/wind. Therefore
categorical-only calibration cannot be declared fully compliant. **Continuous
weather conditioning remains an open methodological decision.** Data are observed
retrospective weather, with existing forward/backward filling. Forecast availability
at pricing time has not been verified; operational causality is not established.

## Distribution selection and finite support

Reuse all 32 prior comparisons: same positive bin observations and equal weights
within each pool. They are not comparisons against count-weighted passenger
populations. The generalized gamma has the smallest in-sample KS for six pools;
the normal-then-truncated approximation has the smallest KS for T1_G1 and T2_POOLED.
That ranking is descriptive, not held-out model selection. Ordinary fits were
normalized to finite empirical support; the normal fit was not truncated-likelihood
MLE. Neither KS significance nor final family choice is justified.

Full-period fits contain validation dates. They cannot honestly be relabelled
held-out fits. A separate train/validation reaggregation checks distribution
stability without repeating a family search. Training positive-bin counts range
89–147; validation counts 89–147. Pooled mean is 2.259681 in training versus
2.275667 in validation; KS distance is 0.136054. RAW_13 mean shifts 2.269411→3.284714,
RAW_15 2.241984→2.770458. T1 pooled KS is 0.240887. Small or sparse bins and shared
references further limit effective information.

Across pools, **0.71–6.16% of positive validation bin estimates lie outside training
empirical min/max** (pooled 3.40%). Empirical truncation is an explicit finite
simulation-support rule, not a proven natural bound; temporal stability is not
guaranteed. Undefined “ZIF” remains undefined. **Recommendation: retain transparent
finite empirical resampling provisionally; do not freeze a parametric family.**
After references and weighting are resolved, a single pre-specified chronological
family validation would be needed before final fitted-family selection.

## Offline acceptance impact

`acceptance_impact.csv` compares eight pools at five fixed distances and the seven
existing factors, using the unchanged master inequality. Historical trip empirical
probabilities are exact; historical fitted probabilities use deterministic 4,096
midpoint inverse-CDF points. That quadrature is bounded numerical approximation,
not simulated request outcomes. No realized fleet or revenue claim is made.

Pooled examples (percent accepting):

| Distance / offered fare | Historical trip | Historical fitted | Uniform bins | Count-weighted bins |
|---|---:|---:|---:|---:|
| 1.5 km / $6.60 | 67.57 | 58.91 | 100.00 | 100.00 |
| 10 km / $35.97 | 68.71 | 65.28 | 16.33 | 72.70 |
| 30 km / $94.70 | 65.45 | 60.89 | 6.12 | 65.26 |

The $35.97 display is rounded; calculations use the exact persisted action/fare.
At distance=Lbase, all positive sensitivities accept exactly offers≤Pbase. These
large differences make weighting/reference decisions consequential, not cosmetic.
They do not establish real-world willingness-to-pay or select a model by revenue.

## Decisions and next single task

Evidence supports retaining common references across groups, the implemented bin
lower-limit formula, explicit population accounting, deterministic positive finite
sampling, temporal separation and preservation of historical artifacts. These
technical conventions can be reaffirmed without inventing scientific choices.
No new numerical calibration or distribution selection is frozen here.

Genuine remaining decisions are: the intended bin-versus-passenger weighting
estimand; selected reference targets and representative-distance rule; how to
account for continuous weather with decision-time availability; and final support/
family validation. The tested linear weather extension should not be promoted.

**Next single task:** obtain an explicit calibration decision specifying weighting
and the reference-selection rule, then implement only that approved reference/
weighting contract with the existing acceptance regression checks. Continuous
weather must remain explicitly unresolved unless a justified rule is also approved.
Do not start training or a new model search.

## Evidence, tests and preservation

- `configuration.json`: population, boundaries, references and exact quantile convention.
- `bin_request_counts.csv`, `weighting_comparison.csv`, `assigned_population_proportions.csv`: counts and weighting.
- `reference_comparison.json`: provenance and conditional alternative.
- `weather_evidence.json`, `conditional_weather_support.csv`, `hourly_weather_evidence.csv`, `temporal_weather_association.csv`: weather evidence and temporal probe.
- `distribution_fit_summary.csv`, `temporal_distribution_stability.csv`: reused fit rankings and temporal support.
- `acceptance_impact.csv`: all fixed-distance/fare comparisons.
- `validation.json`, `test_results.txt`: fingerprints, focused tests and preservation.

Reproduce with `python -B scripts/sensitivity_decision_analysis.py`.
Focused/bounded tests: `python -B -m unittest tests.test_sensitivity_decision_analysis tests.test_binned_sensitivity tests.test_binned_sampler.SamplerTests.test_determinism_support_and_groups tests.test_binned_sampler.SamplerTests.test_acceptance_formula`.
