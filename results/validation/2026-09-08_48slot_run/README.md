# Phase 7D 48-Slot Integrated Production Validation

## Run identity

| Item | Value |
| --- | --- |
| Window | 2026-01-25 19:00 inclusive to 2026-01-26 19:00 exclusive |
| Slots | 48 consecutive half-hours |
| Seed | 42 |
| Fleet | 5,000 vehicles |
| Source | `results/validation/phase7d_48slot_final_integrated_seed42/` |
| CNN mapping | target timestamp = saved X/input timestamp + 30 minutes |
| Regression | 258 tests passing |
| Determinism | Fresh two-slot replay exactly matched the first two run rows |
| Status | `READY_FOR_PHASE_8A` |

This folder is a human-readable reporting package. The source Phase 7D directory remains the authoritative machine-generated run. Reproduce this package without rerunning the simulator using `python scripts/generate_phase7d_report.py`.

## Result summary

| Measure | Value |
| --- | ---: |
| Generated | 106,729 |
| Accepted | 61,863 |
| Rejected | 44,866 |
| Served | 27,967 |
| Accepted but unserved | 33,896 |
| Acceptance rate | 57.96% |
| Served/generated | 26.20% |
| Served/accepted | 45.21% |
| Raw served revenue | 513,292.3994 |
| Scaled learning reward | 17,217.7956 |

All accounting checks passed, the fleet reconciled to 5,000 at every boundary, and all LinUCB selections had exactly one update. All 48 NB13 rounds had participating clients and nonzero finite parameter changes.

## Chart index

PNG and PDF versions are stored in `charts/`.

1. `01_request_funnel`; 2. `02_request_outcomes`; 3. `03_linucb_arm_distribution`; 4. `04_linucb_arm_evolution`; 5. `05_revenue_reward_over_time`; 6. `05b_cumulative_revenue`; 7. `06_nb11_action_distribution`; 8. `07_routing_p5_evolution`; 9. `08_nb13_parameter_change`; 10. `09_nb12_participation`; 11. `10_driver_wait_statistics`; 12. `11_wait_history_coverage`; 13. `12_contention_service`; 14. `13_repositioning`; 15. `14_fleet_state_evolution`; 16. `15_charging_activity`; 17. `16_energy_health`; 18. `17_time_of_day_performance`.

The wait figure uses aggregate statistics, not a histogram, because raw waits were not persisted. `chart_manifest.json` identifies every chart's source, columns, aggregation, output files, and SHA-256 hashes.

## Table index

`tables/` contains core, LinUCB-arm, routing-action, full routing-P5, federated-round, wait, contention, fleet-state, per-Period, representative-fare, and representative-routing tables. `summary.csv` supplies a single-row headline summary.

## Key observations

- Factor 0.85 received 61.52% of LinUCB selections; this is not an optimality claim.
- NB11 selected STAY for 90.74% of actions. Global probabilities still changed over all rounds and remained valid.
- Causal wait-history coverage grew from 572 to 808 grids; neutral fallback fell from 57.92% to 33.25%.
- Driver idle wait was heavy-tailed: median 0, mean 32.32, P95 204, P99 540.68, maximum 1,364 minutes.
- 45.21% of accepted requests were served. Accepted-but-unserved demand is a service-level result, not an accounting error.

## Cautions and professor-review questions

This 24-hour trajectory validates integration and numerical health. It does not identify a causal optimum, justify tuning, or replace the proposed 298-slot experiment.

1. Should factor 0.85's preference be evaluated using a prespecified arm-sensitivity or baseline comparison?
2. Should NB11's STAY prevalence receive a prespecified routing ablation?
3. Which robust summaries should accompany the long driver idle-wait tail?
4. Which service-level metric should be primary for accepted-but-unserved requests?

## Elasticity-vs-Time/Weather Deliverables

These were deliberately not generated from Phase 7D. Mean elasticity versus time/weather, elasticity channelization, and the aggregated time-by-weather table require a separate historical analysis using approximately three or six months of NYC observations and repeated weather categories. The primary recommended interval is hourly with about three meaningful weather categories. Graph 2's “channelization” definition must be confirmed before implementation. This is a separate thesis-analysis track, not a missing simulation output.
