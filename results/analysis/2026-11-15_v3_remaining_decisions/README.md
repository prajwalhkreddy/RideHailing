> Current status (reporting update): V3 implementation and Episodes1–10 are complete; scientific review is paused at Episode10. This folder retains the earlier decision evidence, not a current implementation blocker. See [Episodes1–10 review](../2026-11-15_source_aligned_slot_pricing_v3/review_ep01_ep10/README.md). Frozen numerical content below is unchanged.

# V3 technical resolution and fare decision

Frozen: seven action count; proactive destination pricing; accepted-unmatched accepted-revenue contribution; accumulated context/slot reward; one transition per active destination per30minutes;16slot horizon; gamma0.99 applied once per slot, terminal reward only. This is explicit project carry-forward, not tuning. Weather mapping and fallback unchanged. No production runtime implementation or training.

## Drop-off probability and state

Offline pricing adapter technical_helpers.py consumes frozen dropoff_ma_3h (shift1 trailing6completed slots), normalizes over142 grids, and persists fallback classification. Zero-total uses previous valid probability; lacking that uses explicitly configured Jan–Feb historical dropoff-count proportions available beforeMar1; otherwise fails closed. No uniform fallback. Probability and ordinal popularity remain separate. Validation covers720 March1–15 slots,142grids each; all finite/nonnegative/sum1, zero zero-total slots. Synthetic tests exercise carry/init/failure/leakage. Upstream artifact remains untouched. PreMarch data supplies initialization; no future count enters March state. This is an offline adapter, not a wired runtime.

Final15D ordered vector and normalization are in final_destination_state.csv. Actual demand,idle,incoming,prior dispatch,nine local directional routing probabilities,dropoff probability,popularity. All indexed at context grid d; not a passenger origin or passenger-derived feature. No weather/time added.

## Extended conditional comparison

All six parametric families now use the identical persisted seed42 Bernoulli80/20 FIT/VALIDATION split from canonical Jan1–Mar15 data. Earlier full-data fits retained as history; refitting was necessary for comparable held-out metrics. Gamma/lognormal/Weibull, positive-truncated normal, Fisk, generalized gamma only; no unbounded family search. Empirical FIT distribution is a held-out reference only. Full fit rows are used, duplicate weights exact; no sampling approximation. Truncated normal uses lower0 upperinfinity and normalization Phi(mu/sigma); all families have positive support, no abs-generated samples or finite upper cap. Generalized gamma uses positive shape/exponent, explicitly excluding negative-exponent inverse variants from this bounded search. Numeric optimizer boundary results are ineligible. Fit likelihood/AIC/BIC use training rows; KS/quantiles/tail error use validation rows.

Pareto dimensions: held-out KS and absolute median/P95/P99 errors, all minimized. Failed convergence/invalid support excluded. No arbitrary weighted score or p-value cutoff. Multiple fronts remain human review where central/tail tradeoff is real; empirical is never automatically selected. Per-condition tables preserve exact parameters, support, metrics and statuses. This process does not claim the lowest KS is sufficient.

## Fare decision only

P_base22.354198442390455USD remains frozen. Existing fare candidate scope Jan1–Mar15,1.5<=km<75, positive-fare/source cleaning:6,967,155rows. This differs from earlier P_base reference scope1<=km<75. Positive-fare cleaning still admits0.01 anomalies; observed extrema are diagnostic, not validated tariff bounds. No new anomaly rule or percentile introduced. The6.60–94.70 proposal is empirical P0.5–P99.5 of this population. Exact retained/excluded counts and percentages are in fare_bound_decision_packet.csv; exclusion counts recovered from persisted percentages. No candidate has prior approval. Seven equally spaced factors for existing empirical candidates are in fare_bound_factor_sets.csv.

Human action: APPROVE CANDIDATE <named empirical interval> as project fare support, or DO NOT APPROVE — FURTHER EXTERNAL EVIDENCE REQUIRED. No recommendation is promoted to approval. Raw extrema and unavailable tariff bounds are not usable alternatives.

## Validation and preservation

See test_results.txt and verification.json. Focused adapter/fit/state/Pareto/factor/date tests plus established destination-popularity and pricing-DQN-contract suites run. No full V3 runtime is claimed. Historical V1/V2, frozen upstream modules and March17–31 remain untouched. No March16 selection, simulation or training. The remaining human choices are fare endpoints and the named conditional Pareto tradeoffs only.
