# V2 methodology and results review

**Reporting-only package, 15 November 2026.** No training, model execution, clustering, distribution fitting, baseline replay or counterfactual simulation. Episode26 not started. March17–31 data not accessed.

**Coverage is not complete:** the original T1 linkage matrix, per-training-episode action frequencies, and disaggregated vehicle utility/earnings were not persisted. The optional Q/MC scatter is unavailable. These are disclosed, not fabricated or silently marked complete.

[One-page summary](review_summary.pdf) · [Summary image](charts/SUMMARY.png) · [Visual index](visual_index.csv) · [Coverage audit](requested_visual_coverage.csv) · [Source hashes](source_manifest.json)

## Current methodology

P_base=22.354198442390455 USD; L_base=4.616983790655043 km. Calibration Jan1–Mar15; current distance scope1.5≤L<75km. Epsilon=r_L/r_P, inclusive abs(r_P)≥0.05. Runtime population5,779,213 finite nonnegative observations; no negative-to-absolute transformation or tail truncation. Uniform empirical row resampling with replacement preserves duplicate frequencies. WEATHER_TIME_CONDITIONED_V2 is current.

T1=[00,04), T2=[04,06), T3=[06,16), T4=[16,24). T1 groups and fallback eligibility are detailed in D; T2–T4 explicitly pool across weather.

## Current V2 results

Episode25 completed; 3,200 optimizer updates; replay100,000; exploration0.9392. Training16 half-hour slots per episode; development48 slots. Numerical stability and learning signal do not establish convergence. Highest Feasible remains ahead on fixed development revenue.

## Open research question

Do below-highest actions produce beneficial future value under this environment? Immediate state changes are meaningful, but bounded realized evidence is weak. Q calibration remains poor.

## What changed since earlier review

V1 and pooled-only runtime are historical. Global weather K=3 is not current. Time-specific T1 grouping and T2–T4 pooling are final runtime handling. The full-day audit supersedes earlier bounded-review NONE/CONDITIONAL with WEAK/NO for dynamic evidence and longer-training recommendation. Earlier source READMEs may contain pending statuses; completed run verification governs current execution state.

## Next decision

Do not simply extend training. Review the weak realized-value evidence and value-calibration gap before authorizing a separate scoped investigation. No new methodology or training is authorized by this report.

## A — Distance, demand and fare calibration

**Question:** How do fares and support vary across distance?

Counts, means and quantile bands use saved half-kilometre bins. The current [1.5,75) km population is distinct from the [1,75) reference-price origin. No reference is recomputed.

- [A1: Empirical distance probability by 0.5-km bin](charts/A1.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | N=6,967,155; retained [1.5,75) km | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv)
- [A2: Trip count by 0.5-km distance bin](charts/A2.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | N=6,967,155; retained [1.5,75) km | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv)
- [A3: Distance and mean fare: frozen reference crossing](charts/A3.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | P_base originates from [1,75) km, applied unchanged | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv); [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json)
- [A4: Fare quantile bands by distance](charts/A4.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Sparse bins retained; not a trip-level boxplot | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/array_a/array_a_verified.csv)
- [A5: Frozen fare and distance references](charts/A5.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json); [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/population_reconciliation.csv`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/population_reconciliation.csv)
- [A6: Historical distance–fare scatter evidence](appendix/A6.png) — HISTORICAL_SUPERSEDED. Jan1–Mar15 historical calibration diagnostic; not a V2 runtime population | 
  Sources: [`results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_vs_distance_hexbin.png`](../../../results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_vs_distance_hexbin.png)

## B — Denominator and population resolution

**Question:** What changes when near-reference fares are unresolved?

The frozen inclusive 5% relative-price screen excludes 353,234 from runtime consideration; 834,708 resolved negative observations are also excluded. Historical rows remain retained. Before/after nonnegative views have different N; no absolute-value sign conversion occurs.

- [B1: Historical raw ratio: central view and full magnitude tails](appendix/B1.png) — HISTORICAL_SUPERSEDED. Jan 1–Mar 15 | Historical [1,75) km array; no denominator screen | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/new_e_B_INTERPOLATED.npy`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/new_e_B_INTERPOLATED.npy)
- [B2: Near-reference fare observations and ratio sensitivity](charts/B2.png) — DIAGNOSTIC_ONLY. Jan 1–Mar 15 | Historical [1,75) km; cumulative |r_P| bands | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/zero_denominator/price_gap_bands.csv`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/zero_denominator/price_gap_bands.csv)
- [B3: Denominator candidates: nonnegative epsilon dispersion](charts/B3.png) — DIAGNOSTIC_ONLY. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Candidate diagnostics; C is frozen | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_denominator_rule_selection/global_distribution_comparison.csv`](../../../results/analysis/2026-11-14_pricing_v2_denominator_rule_selection/global_distribution_comparison.csv)
- [B4: Population reconciliation](charts/B4.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/population_reconciliation.csv`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/population_reconciliation.csv)
- [B5: Before/after denominator screening: location, spread and tail](charts/B5.png) — DIAGNOSTIC_ONLY. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Nonnegative subset in each scenario; no sign transformation | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_denominator_rule_selection/global_distribution_comparison.csv`](../../../results/analysis/2026-11-14_pricing_v2_denominator_rule_selection/global_distribution_comparison.csv)
- [B6: Current-scope nonnegative epsilon before and after screening](charts/B6.png) — DIAGNOSTIC_ONLY. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Before N=5,975,653; after N=5,779,213; full tails on right | 
  Sources: [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/new_e_B_INTERPOLATED.npy`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/new_e_B_INTERPOLATED.npy); [`results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/distance_array_range.npy`](../../../results/analysis/2026-11-13_pricing_recalibration_decision_analysis/intermediate/distance_array_range.npy); [`data/interim/pricing_v2_sensitivity/time_specific_weather_2026_11_14/GLOBAL.npy`](../../../data/interim/pricing_v2_sensitivity/time_specific_weather_2026_11_14/GLOBAL.npy)

## C — Sensitivity distribution selection

**Question:** Which representation preserves held-out empirical shape?

Empirical resampling is best supported. Saved fits compare Gamma, Weibull, Lognormal and Exponential on a common internal random-row split. These pooled-marginal diagnostics remain valid, but pooled-only runtime has been superseded by conditional lookup.

- [C1: Nonnegative sensitivity density comparison](charts/C1.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Pooled marginal of unchanged current population; conditional runtime selection differs
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/density_comparison.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/density_comparison.png)
- [C2: Empirical distribution and CDF diagnostics](charts/C2.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Pooled marginal of unchanged current population; conditional runtime selection differs
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/pooled_distribution_diagnostics.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/pooled_distribution_diagnostics.png)
- [C3: Held-out CDF comparison](charts/C3.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Pooled marginal of unchanged current population; conditional runtime selection differs
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/cdf_comparison.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/cdf_comparison.png)
- [C4: Candidate Q–Q comparisons](charts/C4.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Pooled marginal of unchanged current population; conditional runtime selection differs
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/qq_comparison.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/qq_comparison.png)
- [C6: Candidate quantile comparison](charts/C6.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Pooled marginal of unchanged current population; conditional runtime selection differs
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/central_quantile_comparison.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/central_quantile_comparison.png)
- [C5: Empirical resampling best supported by held-out CDF fidelity](charts/C5.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | FIT 4,623,641; validation 1,155,572; random-row split | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/distribution_fit_comparison.csv`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/distribution_fit_comparison.csv)
- [C7: Upper-tail probability comparison](charts/C7.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD; Held-out tail fidelity; no tail cutoff selected
  Sources: [`results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/upper_tail_comparison.png`](../../../results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/charts/upper_tail_comparison.png)

## D — Weather/time conditioning

**Question:** How does each actual weather/time cell select support?

T1 has G1={1,2,3,5,7,8,9,12,14,16}, G2={13,15}. Codes17/21 have fallback handling. T2–T4 use T-pooled support. T1_G2 N=1,669 is below runtime N≥5,000; eligible raw-code fallback is used. SD<4 is not a hard grouping gate. Missing observations are not imputed. The original linkage matrix was not saved; D5 remains missing.

- [D1: Raw-weather epsilon mean by time group](charts/D1.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Observed cells only; SD ddof=0 | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv)
- [D2: Raw-weather epsilon SD by time group](charts/D2.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Observed cells only; SD ddof=0 | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv)
- [D3: Observed support and support tiers](charts/D3.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv)
- [D4: Frozen T1 grouping in mean–SD feature space](charts/D4.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | G2 does not meet runtime N≥5,000 | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_code_time_statistics.csv); [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_group_mapping.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_group_mapping.csv)
- D5: Actual frozen T1 hierarchical dendrogram — source unavailable — DIAGNOSTIC_ONLY. Linkage was computed but not persisted. No clustering rerun permitted; membership plot D4 is not a substitute dendrogram.
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/build.py`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/build.py); [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json)
- [D6: T1 cluster selection: K=2 frozen](charts/D6.png) — DIAGNOSTIC_ONLY. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | Stability and support gates; SD<4 is not a hard criterion | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_cluster_candidates.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_cluster_candidates.csv)
- [D7: Actual runtime support lookup by weather and time](charts/D7.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | T1_G2 uses raw-code fallback; T2–T4 pooled | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/runtime_cell_support_selection.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/runtime_cell_support_selection.csv)
- [D8: Weather/time sampling decision flow](charts/D8.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json); [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/runtime_cell_support_selection.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/runtime_cell_support_selection.csv)
- [D9: Conditional empirical support comparison](charts/D9.png) — CURRENT_AUTHORITATIVE. Jan 1–Mar 15, 2026 | V2 calibration | distance km, fare USD | G2 diagnostic only (N=1,669); runtime uses fallback | 
  Sources: [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_statistics.csv`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_statistics.csv)

## E — Passenger ceiling and feasible actions

**Question:** Which offers are model-feasible, and which are served?

P_raw=P_base+(P_base/epsilon)r_L; P_accept=max(0.85 P_base,P_raw). Seven actions enforce the 1.15 P_base maximum offer. No raw-preference upper clipping occurs. Feasibility is not assignment. Request plots use the frozen highest-feasible export, with identical sensitivity fixture but policy-dependent fleet state.

- [E1: Raw preference and effective acceptance ceiling](charts/E1.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Full range; symlog handles negative raw preference | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet)
- [E2: Request-level feasible-action count](charts/E2.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet)
- [E3: Model feasibility across the seven pricing factors](charts/E3.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Feasible does not mean dispatched or served | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet)
- [E4: Episode25 greedy action coverage](charts/E4.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv)
- [E5: Acceptance floor and action-space maximum](charts/E5.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet)
- [E6: Request offers versus acceptance ceilings](charts/E6.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Highest-feasible baseline; not EP25 offers | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/HIGHEST_FEASIBLE_requests.parquet)

## F — End-to-end implementation

**Question:** Where do pricing, routing and learning interact?

The diagram separates training replay/Bellman updates from March16 greedy inference. CNN/routing are frozen during pricing; this is request-level masked DQN, not the historical MAB formulation.

- [F1: Current hierarchical pricing workflow](charts/F1.png) — CURRENT_AUTHORITATIVE. V2 | Frozen routing; train 16 slots/episode; March16 development 48 slots | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/training_harness_config.json`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/training_harness_config.json); [`results/training/pricing_v2_staged_training_001/weather_conditioned/verification.json`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/verification.json); [`results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json`](../../../results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json)

## G — Training and development traces

**Question:** Is there evidence of learning or convergence?

Training revenue/assignment trends mix source conditions and cannot establish policy improvement. Loss is per training episode; saved Q/TD/action trajectories are checkpoint development diagnostics, explicitly labelled. Per-training action counts were not persisted. No convergence claim is supported.

- [G1: Training revenue](charts/G1.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G2: Training assignment rate](charts/G2.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G3: Training loss](charts/G3.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G4: Development TD error](charts/G4.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv)
- [G5: Development Q magnitude](charts/G5.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv)
- [G6: Exploration schedule](charts/G6.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G7: Replay occupancy](charts/G7.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G9: Training charging events](charts/G9.png) — CURRENT_AUTHORITATIVE. Episodes 1–25 | 16 slots/episode | Changing source conditions, not controlled comparisons | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/episode_metrics.csv)
- [G8: Fixed-development action-frequency evolution](charts/G8.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Training per-episode action counts not persisted in episode table | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv)
- [G10: Fixed-development mean offered price](charts/G10.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Acceptance and assignment are different outcomes | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv)
- [G11: Fixed-development model acceptance](charts/G11.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Acceptance and assignment are different outcomes | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv)

## H — Controlled development comparisons

**Question:** How does Episode25 compare on the fixed day?

All policies use the same 73,754-request March16 fixture. Episode25 earns $1,237,868.21 on59,632 assignments; Highest Feasible earns $1,261,843.09 on59,768. The gap is −$23,974.88 (−1.90%) and−136 assignments. Development results are not final holdout performance.

- [H1: Fixed-development checkpoint revenue](charts/H1.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv); [`results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv)
- [H2: Fixed-development checkpoint assignments](charts/H2.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv); [`results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv)
- [H3: Episode25 and fixed policy baselines](charts/H3.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_evaluations.csv); [`results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/weather_conditioned_baseline_comparison.csv)

## I — Action position and stability

**Question:** How often does the learned policy choose below the feasible maximum?

Of27,719 choice requests, 43.00% select highest,40.86% one below and16.14% two or more below. EP20→25 choice-action agreement is41.0801255%. Fixed-development checkpoint agreement is incomplete; top-line rewards alone do not establish stability.

- [I3: Episode25 greedy action coverage](charts/I3.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv)
- [I1: Position relative to highest feasible action](charts/I1.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Choice-only N=27,719 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/development_actions_ep25.csv)
- [I2: Checkpoint action agreement](charts/I2.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/postrun_analysis/policy_stability.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/postrun_analysis/policy_stability.csv)

## J — Q calibration

**Question:** Do network values match realized return?

Episode25 mean selected Q is about160.05 versus mean Monte-Carlo return1,675.51. Request-level Q/MC pairs were not persisted, so the optional scatter is unavailable. Dynamic-case Q ranking is incorrect19 times with1 undiscounted tie; all20 discounted comparisons are unfavorable.

- J1: Selected-Q versus state-matched Monte-Carlo return scatter — source unavailable — DIAGNOSTIC_ONLY. Only aggregate Q/MC moments persisted; request-level pairs unavailable. Generating pairs would require an evaluation rerun, prohibited here.
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv); [`results/training/pricing_v2_staged_training_001/weather_conditioned/postrun_analysis/analyze.py`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/postrun_analysis/analyze.py)
- [J2: Q and Monte-Carlo return means](charts/J2.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv)
- [J3: Q versus Monte-Carlo error](charts/J3.png) — CURRENT_AUTHORITATIVE. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/value_calibration.csv)
- [J4: Q ranking versus realized counterfactual value](charts/J4.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 20 bounded cases; all discounted comparisons unfavorable | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json)

## K — Dynamic opportunity and realized value

**Question:** Can lower prices change future state, and is that beneficial?

The full-day screen finds meaningful immediate divergence. Twenty genuine divergent cases persist across routing boundaries, with one partial recovery, one full recovery and zero net-positive cases. Chronological bounded sampling omits peak-demand quartile and is not a prevalence estimate or proof of universal Highest Feasible dominance.

- [K1: Full-day immediate dynamic-opportunity screen](charts/K1.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Screened=15,800; branches are not an additive/nested funnel | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json)
- [K2: Bounded state-matched dynamic outcomes](charts/K2.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 20 genuine cases; outcomes overlap, not additive | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json)
- [K3: Q advantage versus realized net value](charts/K3.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 20 cases; descriptive correlation, not causation | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/q_value_realized_value.csv`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/q_value_realized_value.csv)
- [K4: Immediate sacrifice and downstream recovery](charts/K4.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | Chronological bounded selection, not prevalence estimation | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/q_value_realized_value.csv`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/q_value_realized_value.csv)
- [K5: Dynamic opportunity is not established profitable value](charts/K5.png) — DIAGNOSTIC_ONLY. March 16, 2026 | 73,754 frozen requests | WEATHER_TIME_CONDITIONED_V2 | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json)

## L — Correctness and provenance

**Question:** What has been validated?

Saved overlapping suites have zero failures/errors; do not sum counts. Resume accounting, fixture identity and paired controls are documented. This reporting run performs no simulation or model execution.

- [L1: Persisted correctness evidence and protected boundaries](charts/L1.png) — CURRENT_AUTHORITATIVE. Evidence through November 15, 2026 | 
  Sources: [`results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json`](../../../results/analysis/2026-11-15_pricing_v2_dynamic_opportunity_audit/verification.json); [`results/training/pricing_v2_staged_training_001/weather_conditioned/resume_validation.json`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/resume_validation.json); [`results/training/pricing_v2_staged_training_001/weather_conditioned/verification.json`](../../../results/training/pricing_v2_staged_training_001/weather_conditioned/verification.json)

## R — Routing learning context

**Question:** What evidence supports the frozen routing model?

The existing temporal routing update norm and CE traces are reused. R2 is a512-observation bounded development diagnostic, not the full frozen-validation result. The final frozen-validation CE/Brier/ECE are0.291657966/0.093053954/0.015838035, as recorded in `results/analysis/2026-10-31_final_routing_freeze_validation/final_routing_readiness.json`. Regression MSE requests are inapplicable to the current classification loss. Routing remains frozen during the V2 pricing experiment.

- [R1: Frozen temporal federated routing learning trace](charts/R1.png) — CURRENT_AUTHORITATIVE. March1–12, 2026 | Routing frozen during V2 pricing; CE, not regression MSE | 
  Sources: [`results/analysis/2026-10-31_temporal_federated_routing/training_progress.csv`](../../../results/analysis/2026-10-31_temporal_federated_routing/training_progress.csv)
- [R2: Routing bounded-development diagnostic (512 observations)](charts/R2.png) — CURRENT_AUTHORITATIVE. March13–15 routing validation | Not simultaneous V2 routing retraining | 
  Sources: [`results/analysis/2026-10-31_temporal_federated_routing/development_metrics.csv`](../../../results/analysis/2026-10-31_temporal_federated_routing/development_metrics.csv)

## Coverage and limitations

The coverage CSV includes the explicit A–L checklist and extracted requests from six review/calibration documents. Source filenames are retained literally for provenance. Current diagrams do not adopt obsolete Normal/truncated-Normal, MAB or global-K3 requests. Historical A6 and B1 are segregated in the appendix.

Missing: D5 actual saved linkage dendrogram; training action-frequency history; mean vehicle utility/driver earnings. No raw linkage is fabricated, no training curve is reconstructed from checkpoint frequencies, and platform gross fares are not relabelled as driver earnings.

Conditional/unavailable: J1 optional request Q/MC scatter. Inapplicable: raw-price upper clipping, regression MSE for classification routing, and CNN protected-date evaluation within this restricted reporting task.

Read-only aggregate metadata disclosed that an existing CNN evaluation spans March16–31; its prediction rows and plots were not opened. No protected-period observations were read.

## Reproduction and validation

`build_review.py`, `complete_review.py` and `audit_guidance.py` read explicit persisted files. Run the guidance extractor, then `complete_review.py`; no production imports are used. `test_reporting.py` checks sources, counts, masks, figures and coverage truthfulness. See `validation.json` and `test_results.txt`.

Reused distribution images retain their original plot styling; their scope and pooled-marginal interpretation are provided in the index and this guide. Source manifests record SHA256 for every opened numerical input. No large dataset was copied.
