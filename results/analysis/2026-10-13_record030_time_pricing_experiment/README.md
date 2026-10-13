# Record-030 time-of-day pricing experiment

Status: **BLOCKED — policy interface implemented; zero simulation runs.**

## Baseline documented before implementation

`config/config.yaml` selects LinUCB with seven arms 0.85–1.15, legacy grid decisions and Eq. (31) customer response. Offered fare is request base fare times the selected arm. Eq. (31) acceptance probability is 1/(1+exp(0.67 × factor × supply/demand − 1.67)), drawn with an explicit RNG. The default reward uses normalized accepted revenue. These defaults are unchanged.

The production runner explicitly uses the separate `historical_sensitivity` mode. Its `HistoricalCustomerSensitivityModel` loads weather/half-hour Normal parameters and draws strictly positive truncated-Normal epsilon. `maximum_price` computes P_base + relative_distance × P_base / epsilon. Neither that parameter lookup nor that response equation implements the frozen signed Record-029 model. The existing arm validator also restricts Eq. (31) to seven approved factors; arbitrary multiplied arms cannot silently be passed into it.

## Opt-in interface

`src/pricing/time_policy.py` defines `TimePricingPolicy.from_config(mapping)` and `apply(existing_factor, hour)`. BASELINE and EXPERIMENT_A use unit adjustments. TIME_OF_DAY multiplies the existing selected factor by daytime_factor for hours 08–19 inclusive and other_factor otherwise. This is a multiplicative adjustment to the existing policy, not a conversion of observed SD into price.

`run_pricing_dispatch_slot` accepts optional `time_pricing_policy`; omission preserves its existing execution path. Experimental modes currently raise a precise error before touching simulation state, including EXPERIMENT_A. This prevents running the experimental control with the wrong sensitivity model. The pure factor interface is implemented, but experimental fare/acceptance execution is intentionally gated.

The separate `config/record030_time_pricing_experiment.json` specifies a planned five-run comparison with seed 42: control (1,1), daytime (0.95,1), (1.05,1), (1.10,1), and other-hours (1,1.05). It does not overwrite or automatically load into baseline configuration. A future experiment runner must construct policies from its entries and pass them explicitly. Matching request-level randomness should be coupled across runs; a common seed alone may not guarantee identical draws if execution paths diverge.

## Exact blocker and scope boundary

There is no runtime adapter for the frozen Record-029 T1–T4 signed empirical row sampler and passenger-response decision. Wiring the old positive-only model to the Parquet would change the model and misinterpret epsilon. An explicit compatible response adapter, approved signed-epsilon acceptance semantics, and supported-weather handling are required before experiments can run. This task stops at the configurable interface as instructed; it does not substitute a Gaussian, refit epsilon, alter frozen references, or invent a willingness-to-pay model.

Frozen source remains `data/processed/price_distance_sensitivity_record029/final_passenger_sensitivity_empirical.parquet`, with uniform within-time-group row sampling with replacement, preserved duplicates and caller-controlled RNG. Groups remain T1 00–03, T2 04–05, T3 06–15, T4 16–23; support remains [-12.890744316473482, 15.442447741158892]. No Record-029 artifact was modified.

## Outputs and interpretation

Both requested CSVs contain headers only, meaning no completed runs—not zero-valued outcomes. No charts or pricing-outcome claims are produced. Completed-trip versus assigned-trip metrics and platform net revenue versus gross served fare must be distinguished when a runner is integrated; unavailable earnings/wait metrics must remain unavailable rather than invented.

Focused tests cover policy boundaries, identity factors, invalid configuration, the pre-mutation blocker, and existing pricing/dispatch regression behavior. Production runner and baseline configuration were not modified.
