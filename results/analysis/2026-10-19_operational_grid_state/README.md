# Operational grid state

The canonical producer interface is implemented and fixture-validated. Production configuration remains **CONFIG_DECISION_REQUIRED**. No utility equations, passenger acceptance, grid topology, or training were changed. The legacy main-slot loop is deliberately not switched to an incompletely specified methodology.

## Final CNN J_hat — closed

`config/config.yaml` now selects `models/cnn/jan_mar_2026_3km_30min_continued/best.keras` (best epoch 200) and this folder's `dqn_ready_forecasts.parquet`. The latter republishes verified saved epoch-200 test predictions: 109,056 unique timestamp/Grid_ID pairs, 768 consecutive half-hour timestamps, all 142 grids per timestamp, finite nonnegative forecasts. Saved predictions reproduce RMSE 18.2928002064. No inference or training was repeated. Original epoch-100 artifacts remain historical and unchanged.

Epoch-200 test MAE/RMSE/R²: 5.242741 / 18.292800 / 0.961007. Historical-average baseline remains stronger: 3.314528 / 16.271804 / 0.969147. Forecast timestamps label the next 30-minute target slot; existing forecast-weather availability limitations remain. Exact checkpoint and forecast fingerprints are in the contract JSON.

## Population, equations and units

`src/dispatch/dispatch.py` sets `RequestStatus.ASSIGNED` after `fleet.assign_busy`. This is successful vehicle assignment, not proof of eventual trip completion. The producer accepts only that status with a vehicle ID and finite nonnegative offered fare. Pending, passenger-rejected, and unmatched/UNSERVED requests do not enter price estimates or dispatch counts. The existing `src/simulation/main_slot.py` also constructs fare observations from ASSIGNED requests.

For observations from completed slot t−1:

- μ(t) = α × observed mean assigned fare + (1−α) × μ(t−1), USD.
- σ(t) = β × observed population fare SD + (1−β) × σ(t−1), USD.
- F̂(t) = δ × [successful dispatch count / 30] + (1−δ) × F̂(t−1), successful dispatches/minute.
- Ĥ(t) = κ × observed charging wait + (1−κ) × Ĥ(t−1), minutes.

The price equations preserve the mathematically consistent provisional EWMAs in `src/simulation/statistics.py`. They are **not confirmed manuscript recurrences**. The roadmap `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx` refers to manuscript price equations but does not supply them or parameter values. Its F̂/Ĥ equations are implemented directly.

`charging_grid_observations` pools elapsed waits of currently queued vehicles across every station sharing a grid, weighted by queue counts. This explicit engineering aggregation preserves the existing queue-snapshot meaning; it is not completed charging-wait duration. Empty observed station grids report zero; absent/nonstation grids supply no observation. This avoids the legacy dictionary's overwrite of co-located stations. Infrastructure and capacities are unchanged. Confirmation of this aggregation as final methodology remains outstanding.

## Parameters, initialization and missing observations

`config/config.yaml: operational_state` exposes all decisions. α=0.3 comes from the existing `statistics.ewma_alpha`; β=0.3 retains its shared price-SD coefficient provisionally. δ, κ, ζ, sigma floor and F̂/Ĥ initial priors remain null. ζ is mentioned in the roadmap but is not silently incorporated into another equation. `smoothing_parameters.json` records sources and explicit fixture-only values.

The constructor requires 142 finite nonnegative μ/σ/F̂/Ĥ priors and a cutoff strictly earlier than the first decision. Existing `data/processed/spatial_3km_jan_mar_2026/fare_bootstrap_legacy_cutoff.parquet` may supply μ/σ only for simulations starting after its 2026-01-25 18:30 cutoff; it cannot initialize early January. No test outcomes are used. F̂/Ĥ priors require a decision. Fixtures use synthetic priors, not production defaults.

With no dispatches, μ/σ carry forward and F̂ decays with zero count. With no charging observation, Ĥ carries forward. Observed columns are null when absent, deliberately distinguishable from zero; the four estimated state columns remain finite. A separately exposed `sigma_for_denominator=max(sigma, configured floor)` guards division without changing estimated σ or any utility equation. The floor has no arbitrary production default.

## Timing and consumer interface

`src/simulation/operational_state.py: OperationalGridState` is the canonical producer. `state_for(timestamp)` publishes a copy of the current decision-boundary state. `complete_slot(slot_start, completed_at, requests, charging_waits)` requires precisely the current 30-minute interval, then publishes the next boundary. Duplicate, skipped, early-completion and future-state requests are rejected. Caller must supply only that completed slot's event batch; mutable RequestState objects do not independently certify event timestamps.

Sequence: initialize slot 0 → decisions 0 → complete observations 0 → publish slot 1 → decisions 1. Outcomes from slot 1 cannot be requested as state 1 after update. Callers must not report a future completion before it occurs.

The interface returns timestamp, Grid_ID, μ, σ, F̂, Ĥ, successful dispatch count, observed mean/SD price, observed charging wait, and the separate sigma safeguard. It validates the actual EPSG:32118 3,000-metre geometry and exact IDs 0–141; legacy 1,213-grid domains are rejected. Dense output has 142 rows per timestamp. U1/U2/U3 consumers can use named estimates directly; fare_count is never treated as F̂ and raw charging wait is never treated as Ĥ. Existing routing features retain legacy names/semantics and are not represented as this new interface.

## Validation and readiness

Run `python -B -m unittest tests.test_operational_grid_state -v` in the project environment. Eight tests pass: equations and event selection; no-event carry/decay; timing; bad-grid rejection and atomicity; co-located stations; required configuration; sigma safeguard; future-prior and legacy-domain rejection.

`hand_calculated_fixture.csv` gives independent expected grid-0 values for three slots. `fixture_state_output.csv` contains all 426 rows, including unobserved grids. Fixture δ=0.5, κ=0.25, floor=0.01 and initial values are numerical examples only.

Before production/U1–U3 activation: confirm manuscript μ/σ recurrences, select δ/κ and clarify ζ, approve initialization and sigma floor, confirm charging observation aggregation, and wire the completed-slot boundary into consumers. The interface is ready for integration work; the final operational methodology is not yet fully configured. No full simulation or unrelated model training was run.

Focused regression run: 36 tests passed across operational state, config, legacy statistics, dispatch and charging. The persisted three-slot hand fixture matches output values; unresolved project configuration fails closed through `SmoothingParameters.from_config`.
