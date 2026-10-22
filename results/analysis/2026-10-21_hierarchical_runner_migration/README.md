# Final hierarchical runner migration

The public `src.simulation.production.ProductionExperiment` now imports the final implementation in `src/simulation/final_production.py`. The former runner and its guard remain explicitly named `LegacyProductionExperiment`; its legacy preflight and artifact writer also have explicit legacy names. No guard is bypassed.

**Final-interface fixture: PASS. Default production startup: BLOCKED pending an approved driver charging-wait allowance.** The persisted `driver_preferences_seed42.parquet` contains `vehicle_id`, `price_preference` and `wait_preference`, but no `charging_wait_preference_minutes` (H_i_max). Final U3 requires that private preference. The runner requires an explicit per-driver value and does not substitute dispatch-wait preference W_i_max. The fixture's 10-minute H_i_max is solely a controlled test input, not a project decision. Therefore `FINAL_HIERARCHICAL_RUNNER_READY = NO` for the unattended real episode.

## Final interfaces

- Active true-3-km geometry: 142 valid grids, 16 × 16 raster, nine masked movement actions. Existing configured operational/routing adapters validate the geometry and neighbour distances.
- Demand state: existing epoch-200 `dqn_ready_forecasts.parquet`; full timestamp/grid coverage is required, including the next pricing state before slot mutation.
- Operational state: existing causal producer, alpha/beta/delta/kappa = 0.3, initial F_hat/H_hat = 0. Fare-count and unsmoothed wait are not substituted.
- Routing: existing provisional 169 → 64 → 32 → 9 checkpoint. Invalid probabilities are zero; valid probabilities sum to one. U1/U2/U3 and normalized-distance reposition costs use the existing final routing implementation.
- Pricing: existing 13 → 64 → 64 → 7 DQN, identity normalization and unchanged multipliers. Fresh initialization is explicit; optional checkpoint loading uses the existing compatibility validation.
- Acceptance: existing positive behavioural E threshold model, never Record-029 signed epsilon.
- Requests retain the existing forecast-count/intact January empirical-trip sampling method using migrated grid assignments. Unsupported empirical origins are reported rather than concealed. The existing generator's duration/distance/fare validity checks are unchanged. No March future trip population is used to construct the request sampler. The large January sampler is loaded lazily only when real generated requests are requested; this fixture supplies controlled requests instead.
- Matching retains existing FCFS behavior. Its `legacy_fcfs_lowest_id` identifier describes matching order, not an old grid/state dependency.

## Event order and accounting

At each boundary, forecasts, operational state, masked routing probabilities, previous completed-slot assignments, known passenger arrivals and destination popularity form the 13D pricing state. A selected OD action is held within that slot. Actual within-slot request offsets determine when requests become eligible. Acceptance precedes dispatch; gross offered fare is rewarded only on successful assignment. Rejected and accepted-unmatched requests contribute zero.

The fleet clock splits each two-minute interval at travel arrivals and active charging release events. Passenger trips, repositioning and charging travel remain distinct. Only already-committed passenger arrivals in `(t, t+30 minutes]` enter incoming supply. The initial prior-slot assignment history is explicitly empty for a newly initialized simulation, not inferred historical dispatch data.

Completed-slot routing decisions use the previously published operational snapshot. EV navigation preserves its selected station through shortest-path hops. Location changes only when travel time elapses; admission requires IDLE status at that station. Queues use existing FCFS/power semantics. Arrival at an already occupied station queues rather than teleports or displaces another EV.

After completed observations, the operational producer publishes the next state. Routing observations retain per-vehicle association. The existing sample-weighted FedAvg function is called at the slot boundary for explicitly supplied local updates; empty updates are a no-op. No local routing training or checkpoint modification occurs in this migration fixture. Next-state construction precedes replay insertion. Optional DQN training invokes the existing warm-up check; the fixture remains below warm-up and performs zero optimizer updates.

## Controlled fixture and validation

The fixture runs two slots with three vehicles and four requests on a few active origins while retaining the full required 142-grid state domain. It is not the requested four-slot historical episode.

- Two assignments, two accepted-unmatched requests, two passenger completions.
- Assignment revenue: USD 42.550213666235734; unmatched revenue: zero.
- Four real runner replay transitions, two terminal transitions; zero DQN optimizer updates.
- EV at the threshold selects charging at 00:30, traverses 3,000 m over 12 minutes and is admitted at 00:42. Energy reaches 22.65 kWh at 01:00 after travel consumption and 18 minutes of charging.
- Additional focused tests exercise multihop travel, exact within-slot request offsets, no remote admission, one-car-power queue contention, waiting, release and promotion. The reduced station capacity is isolated to that test and does not change production station settings.
- Startup tests reject legacy grid/raster, 155-input/five-output routing, wrong pricing dimension/action map, missing operational state and zero-time charging adapters. Existing checkpoint tests cover incompatible checkpoint metadata.
- Protected geometry, forecast, routing checkpoint, behavioural-E calibration and configuration hashes match before/after fixture execution.

Focused test command (67 tests passed; three additional legacy-isolation/request-generation checks also passed, 70 total):

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/final_cnn_matplotlib /Users/prajwalhk/miniconda3/envs/ridehailing-phd/bin/python -B -m unittest tests.test_final_production_runner tests.test_pricing_dqn_contract tests.test_operational_routing tests.test_operational_grid_state tests.test_standalone_pricing_dqn tests.test_fleet_state tests.test_charging_stations
```

The standalone DQN tests exercise bounded synthetic optimizer/checkpoint behavior; they do not train a pricing policy for performance or overwrite a saved model.

## Files and next step

- `runner_contract.json`: final interfaces, temporal ordering and input semantics.
- `legacy_dependency_removal.json`: replaced paths, retained algorithm semantics and protected hashes.
- `runner_fixture_trace.csv`: actual two-slot runner reports.
- `timed_charging_validation.csv`: physical departure and station-admission timestamps.
- `startup_validation.json`: compatibility rejections, fixture result and explicit production blocker.
- `scripts/validate_final_hierarchical_runner.py`: reproducible controlled fixture/artifact writer; does not invoke real request generation.

An approved per-driver H_i_max source/value must be provided before the real episode can start. The CLI accepts `--driver-profiles` with the required explicit column. After that configuration decision, the next separately authorized run is March 16 00:00–02:00, four slots; it was **not run** in this task. CNN/routing training, passenger sensitivity, geometry, architecture/hyperparameters, FedAvg algorithm and historical result packages were not modified.
