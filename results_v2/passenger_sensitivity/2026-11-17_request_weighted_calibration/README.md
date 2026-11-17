# Request-count-weighted binned sensitivity calibration

## Decision and scope

`REQUEST_COUNT_WEIGHTED_BINNED_SENSITIVITY_V1` implements the approved primary
empirical sampling assumption: probability proportional to historical request
count within each positive, finite distance bin in the applicable pool. This
represents the observed historical trip-distance mixture, not identified
individual passenger heterogeneity. It is explicitly selectable; historical V3
remains the runtime default when no new contract is supplied. Uniform-bin and
trip-level evidence is preserved.

Reuse the 6,967,155 eligible January 1–March 15 observations, 1.5≤distance<75 km,
and their saved 0.5-km bin aggregates. No raw preparation or calibration-period
expansion occurred. Common references remain provisional:
Pbase=22.354198442390455 USD; Lbase=4.616983790655043 km.

For each bin, the unchanged estimator is
`((bin_lower_km-Lbase)/Lbase) / ((mean_fare-Pbase)/Pbase)`.
For eligible positive finite bin estimates, `probability_i = count_i / sum(count)`.
The contract validates shapes, finite nonnegative counts/probabilities, integer
counts, positive total mass, normalization and source-population reconciliation.
Negative/undefined bin estimates remain in existing diagnostic artifacts; their
counts are separately disclosed as excluded from positive sampling, not deleted
historical observations. Conditional fitting pools overlap; their counts must not
be added as independent populations.

## Numerical reconciliation

The GLOBAL pool contains 147 positive bins representing all **6,967,155** requests:

- Mean: **1.7152994769891912**
- Population SD: **0.41601488931379027**
- Median (inverse weighted empirical CDF): **1.5039106516645928**
- Support: **[1.3563048375726, 2.856160057081828]**

Every pool's mean/SD agrees with the preceding decision evidence to absolute
1e-12 tolerance. `distribution_statistics.csv` contains positive-bin counts,
represented/excluded request counts, bounds and quantiles for all eight pools.
For example, T3_POOLED represents 2,885,063 of 3,014,550 requests in positive bins;
129,487 belong to its nonpositive bin. This changes positive sampling mass, not
historical row retention. GLOBAL has no such exclusion.

## Support and temporal limitation

Use the exact positive finite empirical values from the saved Jan1–Mar15
calibration. No extra epsilon floor, parametric tail, validation-driven widening,
clipping or individual-trip bin lookup is introduced. Draws use replacement,
normalized counts and caller-controlled RNG. The sampler receives weather and
time, not the requesting passenger's distance. Distance enters acceptance only.

The prior chronological diagnostic compared Jan–Feb support with March1–15 bins:
0.71–6.16% of positive validation **bin estimates**, not passengers, exceeded the
training range. `support_exceedance_review.csv` retains these results without
changing those training boundaries. This implemented contract uses the explicitly
authorized full Jan1–Mar15 calibration population; it is not presented as a
Jan–Feb-only held-out evaluation model. Empirical limits remain modeling support,
not natural bounds. Unseen tail behavior and support adequacy remain provisional.

## Weather and references

Keep existing weather-code/T1–T4 mappings and fallback ordering: mapped group,
T1 raw-code pool, time pool, GLOBAL, using existing ≥5,000 historical trip-candidate
support counts. This criterion is inherited and does not imply 5,000 independent
bin estimates. RAW pools span times; time pools span weather codes. Unknown integer
codes use the existing pooled fallback; missing/nonfinite weather fails closed.

No continuous weather bins or new distributions are introduced. Adding temperature
and wind worsened chronological diagnostic RMSE from 0.258529 to 0.295726, and
also worsened it after distance-composition adjustment. That extension is not
promoted. Complete CNN/sensitivity weather-feature alignment remains unresolved.
Processed weather is retrospective observed weather, including existing filling;
decision-time forecast availability is unverified.

Reference construction remains provisional because existing mean-fare/crossing
provenance is not identical to the master's selected-observation procedure.
No parametric family is selected. These limitations do not reopen the approved
request-count-weighting decision.

## Explicit runtime and checkpoint integration

Select this file via the existing constructor:

```python
ODPricingRuntime(
    sensitivity_contract="results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration/sampling_contract.json",
    **existing_engine_arguments,
)
```

`load_sensitivity` dispatches by contract version; the uniform version still uses
its original unweighted RNG call. No contract argument preserves historical V3.
Acceptance remains exactly
`offer <= Pbase + (Pbase/epsilon)*((distance_km-Lbase)/Lbase)`.
Nonpositive/nonfinite sensitivities and overflow reject without silent repair.

`SUCCESSFUL_DISPATCH_REWARD_V1`, `FEASIBLE_OD_PRICING_V1` and
`HISTORICAL_REQUEST_REPLAY_V1` remain intact. OD runtime checkpoints preserve
sampler type, exact contract hash and RNG along with full runtime state. Mixed
uniform/weighted snapshot versions, modified contracts and incompatible code
fingerprints reject. Existing older checkpoints remain untouched; strict source
fingerprinting can reject snapshots made with earlier implementation code rather
than silently migrating them. Historical V3 checkpoint handling is unchanged.

No CNN/DQN architecture, dispatch, charging, federated mechanism or historical
V3 implementation changed. Bounded fixtures exercise runtime integration; there
is no model training or full episode execution.

## Files and validation

- `sampling_contract.json`: version, counts/probabilities, bounds, groups and provenance hashes.
- `distribution_statistics.csv`: exact weighted summaries and population reconciliation.
- `support_exceedance_review.csv`: unchanged temporal exceedance evidence with interpretation.
- `test_results.txt`, `validation.json`: focused/bounded tests, fingerprints and preservation.
- `scripts/build_weighted_binned_calibration.py`: builder using saved bins only.
- `src/pricing/weighted_binned_sampler.py`: weighted mode and version dispatch.
- `tests/test_weighted_binned_sampler.py`: moments, conditional counts, RNG, acceptance and checkpoint/replay checks.

Next single task: resolve the remaining common-reference selection procedure in
an explicit methodological decision. Preserve weighted sampling and defer training;
continuous-weather alignment and empirical-tail adequacy remain separately open.
