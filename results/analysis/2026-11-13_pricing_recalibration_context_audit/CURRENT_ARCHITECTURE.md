# Current architecture and exact active code context

Paths are repository-relative. Source symbols, not historical status prose, determine the active path. Historical root-README sections contain older behavioural-E/FedAvg defaults; `staged_training_002/run_staged.py` explicitly supplies the current V1 provider, learner and frozen temporal routing checkpoint.

## End-to-end hierarchy

NYC TLC processed zone/grid trips + Meteostat → true 3-km grid/half-hour demand → frozen CNN forecasts J_hat → forecast-driven empirical requests → positive V1 sensitivity → preference/feasibility mask → request DQN offer → passenger accepted by mask → driver price/energy eligibility → FCFS dispatch → passenger commitments/vehicle movement/timed charging → completed-slot operational estimates → utility-selected routing movement and frozen global routing probabilities → next13D pricing state → request reward/replay/updates → March16 development → later protected hierarchical evaluation.

The pricing module must integrate with this actual simulator, routing response, driver/EV behaviour and dispatch; an isolated synthetic price generator is not a substitute. Global routing probabilities are **features**, not the direct movement selector. Utility routing chooses movement; the frozen network estimates routing labels.

| Component | Active path/symbol | Frozen boundary / dependency |
| --- | --- | --- |
|Spatial | `src/simulation/final_production.py::validate_final_contract`, `ProductionExperiment.__init__` | `data/processed/grid_lookup.parquet`, `grid_metadata.json`, spatial_3km_jan_mar_2026/neighbour_map.parquet;142 valid grids,16x16,EPSG32118 metres;3km cardinal. No spatial rebuild implied. |
|Demand | `src/pricing/dqn_contract.py::artifact_snapshots` | `config/final_temporal_protocol.json::rl_forecast_path` points to epoch200142-grid March1–15 forecasts. March16 uses saved dqn_ready_forecasts. CNN checkpoint/prior preprocessing frozen; no inference/retraining here. |
|Request counts | `ProductionExperiment.requests_for_slot` | Rounded nonnegative forecast count per origin; origins without January support omitted with explicit unsupported_demand record. |
|Joint empirical trips | `src/dispatch/generation.py::build_empirical_od_distribution`, `EmpiricalODDistribution.sample_trip`, `generate_requests` | January subset of spatial_3km_jan_mar_2026/trips_jan_mar_2026.parquet. Intact row sampling with replacement within origin. |
|Reference/preference | `src/pricing/passenger_sensitive_v1.py::P_BASE_USD`, `L_BASE_KM`, `maximum_price` | Global constants and scaled inverse-epsilon price equation. Pricing-specific. |
|Epsilon provider | `PositiveEpsilonProvider.__init__/sample/require_training_ready`; `run_staged.py::provider` | positive_epsilon_calibration.npy + restricted_calibration_support.json; seeded global empirical replacement sampling. |
|Offer/mask/acceptance | `effective_threshold`, `feasible_mask`; `src/simulation/passenger_sensitive_v1.py::PassengerSensitiveExperiment.run_slot` | Candidates=aP_base; mask first; accepted=True after selected feasible action; no active customer response call afterward. |
|Driver eligibility/dispatch | `src/dispatch/dispatch.py::find_eligible_vehicle`, `dispatch_requests` | Idle, not charging-required, enough trip energy and destination station reserve; offer >= persisted driver price_preference; same-grid then neighbours, lowest vehicle ID; FCFS request order. |
|Reward/dispatch count | `src/pricing/dqn_contract.py::DispatchLedger.complete_slot`, `completed_request_outcomes`; `run_slot` | Assignment-time gross fare, zero unmatched; ledger checks accepted assignments; previous-slot successful counts J_disp. |
|Movement/commitments | `passenger_commitment`; `ProductionExperiment.advance_until`; `src/fleet/fleet.py::Fleet.advance_time` called by orchestrator | Actual empirical duration, actual distance for EV consumption; absolute arrival events and future incoming commitments. Fleet implementation not redesigned or executed. |
|EV/charging | `src/charging/energy.py` functions called by dispatch; `src/charging/timed.py::TimedChargingInfrastructure` called by orchestrator; `_continue_charging` | Existing timed admission, multihop navigation, reserve/energy checks; H_i_max10 min from profiles. No teleportation/fare-distance substitution. |
|Operational state | `src/simulation/operational_state.py::OperationalGridState.complete_slot` | Successful fares update mu/sigma; assignments update F_hat; charging waits update H_hat; prior carried where appropriate. |
|Routing movement | `src/routing/operational_interface.py::OperationalRouting.decide/start_next_hop`, `u1/u2/u3`; `ProductionExperiment.route_idle` | Noncharging U1+U2-cost; charging U3-cost; reachability; persisted driver preferences. |
|Global routing | `ProductionExperiment._state_sources`; `src/routing/final_state.py::RoutingState.from_producer`; `src/routing/learning.py::load_final_policy/masked_softmax` called by orchestrator | Frozen169→64→32→9; no local/FedAvg updates in V1 (`frozen_routing=True`). |
|Pricing state | `src/pricing/dqn_contract.py::PricingStateBuilder.build`, `FEATURES` |13D: J_hat,J_disp_previous,incoming,9routing probabilities,destination popularity. |
|Pricing DQN | `src/rl/passenger_sensitive_dqn.py::PassengerSensitiveDQN.select_action/train_step`; inherited `src/rl/pricing_dqn.py::build_q_network` |13→64→64→7; request feasibility mask; historical epsilon/distance do not enter network features. |
|Replay/target | `RequestReplay.add/sample`, `ActionableRequestLinker.observe/_finish/finish_episode`, `masked_targets` | Next chronological actionable request; gamma.99 once/request; terminal no bootstrap. |
|Training | `V1/staged_training_002/run_staged.py::main`, `PassengerSensitiveDQN.complete_slot` | Protocol-defined March1–15 episodes;8 updates/warm slot; paused atEP25. |
|Development | `run_staged.py::EvaluationView`, development branch of `main` | March16 four-slot fixture; seed424242; greedy, no learner writes. |
|Date protection | `src/pricing/passenger_sensitive_v1.py::guard_date`, `complete_slot`; `src/simulation/temporal_protocol.py` | Calibration<Mar16; V1 runtime<Mar17; training additionally>=Mar1. FinalMarch17–31 requires separately authorized evaluation integration, not bypassing current guard. |

`V1` in this table means results/analysis/2026-11-07_passenger_sensitive_pricing_v1. The frozen routing checkpoint passed by run_staged is `models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras`, not the older default reachability checkpoint in base ProductionExperiment.

Base startup still initializes a legacy behavioural customer through `behavioural_model`; V1's override of run_slot does not invoke that customer's acceptance. Do not confuse construction dependencies with the active V1 decision formula.

## Request generation: HYBRID (C)

| Field | Source and handling |
| --- | --- |
|Simulation timestamp |Current March slot + sampled January pickup's within-half-hour offset. Original January pickup/dropoff retained separately. Not actual chronological MarchTLC requests. |
|Origin grid |Forecast demand determines number per origin; existing grid mapping retained. |
|Destination |Sampled intact January row conditional on origin; not independently sampled marginal. |
|Trip distance |Same row's TLC trip_distance miles ×1.609344; source miles retained. Not resampled independently from OD/duration. |
|Trip duration |Same row's dropoff−pickup; must bepositive; used for passenger movement. |
|Fare/reference |Same row's fare_amount initially RequestState.base_fare; V1 overwrites base_fare with global P_base and offered_fare with factor×global P_base before dispatch. Historical fare is not the DQN offer. |
|Sensitivity |Independent draw from supported positive Jan1–Mar15 pool, not the sampled source trip's own epsilon. |
|Ordering |15 two-minute mini-slots; within each, empirical offset then requestID; absolute clock advances chronologically. Source ID is positional in loaded January frame, not a universally unique rawTLC identifier. |

PDF pp6,9 says sample distance marginal then spatial positions. Replacing the intact-row sampler with independently sampled distances and grids risks invalid OD-distance-duration coupling, altered travel/energy and a changed CNN-demand contract. Using Ni/sumN only to summarize/calibrate fare/sensitivity is safe conceptually; making it the runtime marginal needs an explicit conditional/joint generation design. It cannot be silently bolted onto current requests. Sampling exact distance uniformly within a bin is not explicitly authorized; the document only says sample within it.

## Reference storage and assumption inventory (active dependency closure)

| Location | Role | If references change |
| --- | --- | --- |
|`src/pricing/passenger_sensitive_v1.py` |P/L constants; import-time candidate prices/min/max; maximum_price |Version constants/contract and derived values together. |
|`src/simulation/passenger_sensitive_v1.py` |Imports constants; writes request base fare,offers and audit reference fields |New audit/version schema; dispatch/reward changes downstream. |
|`V1/pricing_v1_spec.json`, `METHODOLOGY.md`, `README.md` |Serialized explicit frozen P/L/equations/action dollars |New versioned spec; preserve historical record. |
|`data/processed/price_distance_sensitivity_record029/frozen_reference_values.json`, `authoritative_epsilon_methodology.json`, historical summary |Original mile-based reference provenance |Do NOT rewrite; construct separate recalibration artifacts. |
|`V1/restricted_calibration_support.json`, `positive_epsilon_calibration.npy`, `calibration_distance_km.npy` |Values/support derived under old references; current provider loads them |Cannot reuse as new e calibration; retain history. |
|`V1/review_feedback_reconciliation/analyze_review.py` |Hard-coded P/L and formula diagnostics |New approved analysis namespace; do not overwrite old figures. |
|`V1/calibrate_positive_epsilon.py` |Hard-coded P/L but exits immediately as superseded generator |Historical, not an executable current calibration entry point. |
|`Follow-up/analyze.py` |Old references in saved diagnostic calculations |Provenance only for new method; do not edit old results. |
|`staged_training_002/run_staged.py` |ImportsACTIONS; serializes support/actions; loadsprovider and checkpoint |Version runconfig/sampling/checkpoint contract after decisions. |
|`episode_025/checkpoint.json` and replay |Schema/dimensions/discount/config, but no full P/L/sampler semantic fingerprint |Shape/schema load success cannot establish scientific compatibility; old reward/masks retained. |
|Saved request export and diagnostic CSVs |P_base,L_base,price thresholds/offer columns, old masks |Historical evidence; never relabel as new method. |

No claim is made about every historical literal elsewhere in the repository: no whole-repository search was performed. This inventory covers the traced active execution and directly referenced provenance paths.

## Seven-action assumptions in the active path

- `src/pricing/passenger_sensitive_v1.py`: ACTIONS, CANDIDATE_PRICES, first/last extrema.
- `src/rl/pricing_dqn.py`: duplicate ACTIONS; action_index0..6; build_q_network Dense7; saved/load architecture checks.
- `src/rl/passenger_sensitive_dqn.py`: validate_mask shape(7,), targets(N,7), replay serialization reshape(-1,7), load output7/layers64,64,7; terminal zero mask 7.
- `src/simulation/final_production.py::validate_final_contract`: frozen seven-action tuple check.
- `src/simulation/passenger_sensitive_v1.py::run_slot`: seven hard-coded audit labels085…115 and imported candidate prices.
- `staged_training_002/run_staged.py`: frequency reporting, run_config actions, checkpoints, replay and diagnosticCSV contracts.

Changing only factor values can preserve tensor shape but changes action meaning. Changing count changes output layer, masks, replay, reports and checkpoint architecture. Neither is exact EP25 continuation.

## Causal feedback and frozen-model implications

J_hat comes from frozen demand forecasts and is not directly repriced in current code. Fares change driver eligibility and assignments; J_disp_previous and incoming commitments then change. Actual assignments change movement/energy/charging and future supply. Assigned prices also directly update operational mu/sigma; counts updateF_hat; these enter169D routing state and U1, while charging waits affectH_hat/U3. Frozen routing probabilities change as input state changes. Pricing's13D state therefore shifts even with fixed weights.

CNN/grid dimensions and physical movement interfaces remain compatible if requests, timing and geometry remain unchanged. A new generator could alter demand/OD/duration relationships and requires separate validation. Routing weights remain mechanically compatible with169D inputs, but fare/assignment changes introduce distribution shift: validate routing probability quality/utility responses before deciding whether retraining is necessary. Do not automatically retrain or claim compatibility from dimensions alone.

The current13D state omits distance and epsilon. If masks are removed, passenger information previously conveyed by the mask no longer constrains the action. This information-loss/partial-observability issue needs an explicit architecture review; this audit does not add features. The new PDF does not independently authorize a state expansion.
