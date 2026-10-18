# Hierarchical RL implementation audit — 14 October 2026

## Executive finding and evidence boundaries

The repository contains an integrated **non-private LinUCB baseline**, with CNN demand predictions, passenger response, dispatch, EV movement, utility-based repositioning, supervised policy learning and FedAvg. It does **not** contain the requested pricing DQN. Existing integrated runs must not be described as successful episodes of the final DQN hierarchy.

Approximate stage: baseline integration/validation complete enough for research runs; final hierarchical pricing and privacy remain. An explicitly coarse feature-readiness estimate is **about 55–65% of the non-private foundation**, not a measured percentage of research completion or remaining effort. Five of fourteen phases below are COMPLETE at the implemented component level; five PARTIAL, three MISSING, one METHODOLOGY BLOCKED. Privacy and attacks can be substantial work beyond these counts.

No file named “Complete Hierarchical RL Implementation Roadmap” was found in the inspected inventory, nor that title in the available plan DOCX text. The phase list and requirements supplied in the audit request are therefore the comparison contract. The exact manuscript equation and any unstated roadmap action bounds cannot be independently certified from that title. Do not treat older plan documents as automatically overriding the latest request. This limitation is a decision item, not permission to invent the missing specification.

Inspected source, tests, scripts, configuration, README, notebook inventory, selected saved summaries and processed metadata; no raw tables loaded. Only this report is created. No simulation, training, adapter, refactor or deletion performed. Quick unit tests used `-B`/PYTHONDONTWRITEBYTECODE to avoid source-tree bytecode changes. Saved metrics are reported as persisted evidence, not reproduced training results.

## Architecture inventory

- 62 Python files under `src`, 41 under `tests`, 37 under `scripts`; five `.ipynb` legacy notebooks plus extensionless NB2 and plan/reference documents.
- `src/data`, `spatial`, `demand`, `popularity`: taxi/weather cleaning, zone/grid mapping, demand tensors/CNN/inference and destination popularity.
- `src/pricing`: two acceptance branches, historical parameter lookup, LinUCB, reward/context scaling and opt-in time factor. No pricing DQN; `models/pricing` contains only `.gitkeep`.
- `src/dispatch`, `fleet`, `charging`: empirical requests, eligibility/contention, state transitions and station queues/energy.
- `src/routing`: deterministic utility decisions, supervised local policy, synchronous FedAvg and production initialization. `src/federated/__init__.py` is not a separate privacy implementation.
- `src/simulation`: pricing/dispatch slot, main-slot and multi-slot orchestration, production assembly and small validation harness.
- `src/analysis/passenger_sensitivity_m10.py`, `src/elasticity_v2`: older analyses; Record-029/030 are completed descriptive artifacts, not the runtime sampler.
- `results/validation/phase7d_48slot_final_integrated_seed42`: saved 5,000-vehicle, 48-slot baseline run, Jan 25 19:00–Jan 26 19:00, runtime 3377.13 seconds. Earlier 4/8/48-slot and request-8D/scaled-reward runs also exist. Root README still lists the 298-slot evaluation as pending.

## Final status matrix / roadmap phases 1–14

COMPLETE means the named component exists with tests/output evidence, not blanket certification of an unavailable full roadmap. Priorities P0/P1 precede DQN integration, P2 follows the first non-private episode.

| Phase | Module / evidence (src paths unless stated) | Status | What works / main gap | Blocks next phase? | Priority |
|---|---|---|---|---|---|
| 1 Data preparation / sensitivity | data/taxi.py, data/weather.py; Record-029/030 results and processed methodology | COMPLETE | Cleaned data and descriptive analysis available; do not equate these with behavioural calibration | No for baseline; acceptance decision separate | P0 |
| 2 Grid / slots | spatial/grid.py, mapping.py; fleet/fleet.py; grid_metadata.json | COMPLETE | 1,213 valid square cells, directional neighbours, 30/2-minute clocks; any different roadmap topology needs agreement | No for existing topology | P0 |
| 3 CNN demand | demand/model.py, tensors.py, inference.py; models/demand | COMPLETE | Trained CNN and held-out predictions consumed by runtime; does not establish cross-month generalization | No | P1 |
| 4 Passenger acceptance | pricing/customer.py, customer_sensitivity.py; production.py | METHODOLOGY BLOCKED | Two executable branches exist; descriptive e is not behaviour E; approve final convention | Yes for final architecture, not existing baseline | P0 |
| 5 Fleet / dispatch / revenue | fleet/state.py, fleet.py; dispatch/dispatch.py, contention.py, generation.py | PARTIAL | Working assignments, transitions and gross revenue; completed-trip ledger, passenger waiting constraints and net earnings contracts incomplete | Yes for final reward/evaluation definition | P1 |
| 6 Grid statistics | simulation/statistics.py:OperationalStatistics | PARTIAL | Fare/wait mean and SD EWMAs; requested F_hat and H_hat semantics not implemented as specified | Yes for final state/utility contract | P0 |
| 7 Driver repositioning / EV | routing/baseline.py; charging/energy.py, stations.py | COMPLETE | Utilities, argmax, masked actions, energy and queues integrated; provisional utility/charging assumptions still documented | No for baseline | P1 |
| 8 Global policy | routing/learning.py, simulation/grid_policy.py | COMPLETE | 87→64→32→5 logits, masked softmax, supervised labels and runtime global reuse | No; not itself Q-learning | P1 |
| 9 Plain FL | routing/federated.py; simulation/main_slot.py | COMPLETE | Sample-weighted FedAvg, participating local observations, broadcast; synchronous in-process only | No for non-private pilot | P1 |
| 10 Pricing DQN | pricing/linucb.py is alternative; models/pricing empty | MISSING | No requested state builder, Q/target nets, replay, TD loss, epsilon-greedy, soft update, DQN checkpoints/training | Yes | P0 |
| 11 Hierarchical integration | simulation/main_slot.py, production.py, multi_slot.py | PARTIAL | Baseline loop already connected; DQN decision and delayed next-state/replay transition missing | Yes | P0 |
| 12 Privacy / secure aggregation | routing/federated.py exports weights only | MISSING | No DP-SGD, accountant or cryptographic aggregation; schema hygiene is not privacy | Not before non-private episode | P2 |
| 13 Attacks / robustness | no attack implementation found | MISSING | No poisoning/Sybil/inference/inversion harness; numerical validation is not Byzantine defense | Not before non-private episode | P2 |
| 14 Evaluation / baselines / ablations | reporting modules; validation outputs; experiment scripts | PARTIAL | Saved baseline runs and metrics; final DQN, multi-seed baselines/ablations and uncertainty missing | Blocks final claims, not first episode | P2 |

### Phase evidence: tests and outputs

1. `test_artifacts`, `test_historical_sensitivity`, `test_elasticity_v2_population`, `test_passenger_sensitivity_m10`; cleaned metadata, Record-029 authoritative/empirical Parquets and Record-030 tables. Tests of earlier definitions are not tests approving Record-029 as behaviour.
2. `test_grid`, `test_spatial_mapping`, `test_config`, `test_fleet_state`; grid lookup, mask and neighbour artifacts.
3. `test_demand_aggregation`, `test_cnn_tensors`, `test_cnn_model`, `test_demand_artifacts`; CNN model/normalization/predictions/metrics.
4. `test_customer_sensitivity`, `test_pricing`, `test_pricing_dispatch`; compatibility audit documents distinct formulas; no approved descriptive-to-behaviour bridge.
5. `test_dispatch`, `test_driver_contention`, `test_driver_waiting`, `test_empirical_arrivals`, `test_passenger_trip`, `test_pricing_supply`; per-slot dispatch/revenue/fleet output.
6. `test_statistics`, `test_driver_waiting`; nb9_fare_representative.csv and nb9_wait.csv.
7. `test_routing_baseline`, `test_energy`, `test_charging_stations`; saved fleet/routing diagnostics.
8. `test_routing_learning`, `test_grid_policy`, `test_routing_production`; common initialization NPZ and saved routing-grid probabilities.
9. `test_routing_federated`, `test_main_slot`, `test_multi_slot`; routing_rounds.csv. There is no privacy test evidence.
10. LinUCB tests/checkpoint records exist, but no DQN tests or checkpoint.
11. `test_main_slot`, `test_multi_slot`, `test_production_simulation`, `test_validation_24h`; 48-slot integrated baseline evidence, not final pricing RL replay.
12–13. No implementation-specific privacy/attack outputs or tests found.
14. `test_reporting`, pricing/reporting tests; prior validation/analysis summaries. Experiment completion must be checked from CSV rows rather than folder names.

## Passenger sensitivity and acceptance: four separate concepts

A. Record-029: **e_price_distance = [(P−P_b)/P_b] / [(L−L_b)/L_b]**, dimensionless, signed, empirical; P_b=21.34586956773507, L_b=3.01799878914405, price window ±$1; frozen support [−12.890744316473482,15.442447741158892]. Algebra gives P=P_b(1+e_price_distance*r_L). This is a historical relation, not identified causal willingness-to-pay.

B. Runtime `customer_sensitivity.py:sample_positive_truncated_normal`, `maximum_price`, `evaluate_resolved`: E~Normal(mu,sigma²) conditioned on E>0; artifact mu/sigma are passed as underlying Normal parameters. P_max=P_b(1+r_L/E), P_dispatch=P_b*alpha; accept iff offered<=P_max. Location/distance bases are resolved by weather and half-hour with optional hierarchy, not necessarily the global Record-029 references. Production explicitly loads January historical parameter Parquets and hierarchical fallback. E is a positive inverse distance coefficient in this behavioural threshold, not Record-029 e.

C. `customer.py:customer_acceptance_probability`: p=1/[1+exp(0.67*alpha*S/D−1.67)], S>=0,D>0; `draw_customer_acceptance` accepts U<p. **No sampled epsilon occurs in this Eq. (31) branch.** Default YAML selects eq31; production overrides to historical_sensitivity. Branch defaults and actual production must not be conflated.

D. The reciprocal-elasticity threshold referred to by the request has the runtime-shaped expression P_b[1+r_L/E]. Its exact manuscript definition/reference bases require the missing roadmap document; a symbolic resemblance does not prove equivalence. If the manuscript intends E=e_price_distance, it conflicts with Record-029 algebra. Setting E=1/e only aligns forms for nonzero e, matching bases and the same price interpretation; it violates positivity for negative e and adds a singularity at e=0. No arbitrary transformation is recommended.

For E→0+, runtime P_max tends to +infinity for L>L_b and −infinity for L<L_b; E=0 is rejected. For fixed distance, Record-029 implied price instead tends to P_b as e→0. `test_customer_sensitivity` explicitly encodes opposite monotonicities above/below reference distance and equality acceptance. Direct substitution is **NOT_DIRECTLY_COMPATIBLE**. Phase 4 remains blocked for a final convention, while Option A can retain existing runtime behaviour as a separately labelled baseline.

## Grid and time implementation

`grid_metadata.json`: 3,000-m square grid, EPSG:2263, 51×52 bounding raster (2,652 generated cells), 1,213 valid cells; 4,544 directed neighbour links. `assign_grid_ids_by_zone_legacy` samples pickup/dropoff GridIDs from intersecting taxi zones with seeded RNG, since source LocationIDs have no point coordinates. The generic point-assignment helper exists but is not evidence that these trips have coordinate-derived assignments.

`build_neighbor_map` persists GridID, NeighbourGridID, Direction; relative row/column deltas N=(-1,0), E=(0,1), S=(1,0), W=(0,-1) exist. Local policy action indices are STAY,NORTH,EAST,SOUTH,WEST, with boundary masks. No separate learned/roadmap-specific arbitrary neighbour-index embedding is established. Thirty-minute main slots and fifteen two-minute mini-slots exist; empirical arrival offsets and travel-duration fields are handled by request/fleet code. Compatibility is confirmed for this square topology, not an unspecified hex/H3 or coordinate-accurate alternative.

## Demand model audit

**The CNN is implemented and used.** `build_model` has same-padded 3×3 Conv2D 32/64/32 ReLU and 1×1 linear output. Inputs: HistoricalDemand, Temperature, WindSpeed, WeatherCode, DayOfWeek, Hour, Period; current Demand excluded. Output: next-slot grid demand. Normalization is fitted on training features; linear predictions can be negative and runtime separately uses nonnegative demand where required.

Saved time metadata: 1,189 training input slots Jan 1 00:00–Jan 25 18:00; 298 held-out input slots Jan 25 18:30–Jan 31 23:00. Targets are +30 minutes. Training uses an internal 20% validation split, shuffle=True, Adam 0.001, up to 50 epochs, early stopping. This internal validation is distinct from the chronological outer holdout; the training array is not all fitted optimizer samples after validation splitting.

`models/demand/cnn_metrics.csv`: RMSE 2.59156919, MAE 0.63377517, MAPE 83.48948359%, R² 0.89855289. These are stored aggregate metrics; MAPE requires care with sparse demand. Saved cnn_model.keras, normalization.pkl, cnn_history.pkl, cnn_predictions.npy and cnn_provenance.json exist. Production consumes aligned precomputed predictions rather than retraining on each slot. Five legacy notebooks include NB4 dataset/NB5 CNN.

No AE or LSTM-AE implementation was found in the inspected src/scripts/tests/config/notebook inventory. Do not claim those models replace the CNN or invent a relationship. If held externally, they need separate evidence.

## Simulator, utility and statistics audit

`generate_requests` samples empirical trip/OD rows from predicted demand with persistent RNG and within-slot arrivals; this is stochastic generation, not exact replay of every raw request. Fleet tracks IDLE/BUSY/CHARGING and passenger/reposition movement, advances timers and completes movement/energy transitions. Dispatch searches local/one-hop eligible idle vehicles; both legacy FCFS/lowest-ID and production driver-contention utility modes exist. Requests are ordered by mini-slot/request ID. Energy/charging eligibility is enforced. Driver waiting episodes are recorded; this is not a fully calibrated passenger patience/cancellation or maximum-pickup-wait model. Pickup-distance preference in contention is not itself a hard passenger wait cap.

Accepted requests may remain unserved. Gross served-fare revenue is recorded on assignment; `served` must not be relabelled completed trips. A complete passenger journey revenue/earnings ledger and cancellation accounting are not exposed. Driver earnings/net commission metrics are not established. Seeds are explicit; identical seeds do not ensure identical trajectories after policy divergence.

`OperationalStatistics.update_slot`: successful fare mean/SD and completed driver-wait mean/SD, ddof=0. EWMAs use alpha=.30, first-observation initialization, once per completed main slot; missing observations carry the previous value, not fabricated zeros. mu/sigma exist. `fare_count` is an observation count, **not an implemented EWMA dispatch frequency F_hat**. `charging_wait` comes directly from station observations, **not an H_hat EWMA state**. Exact requested F_hat/H_hat definitions and update timing need implementation/agreement.

Driver control is utility-based, not DQN: `price_utility` (U1) and decreasing `wait_utility` (U2) normalize preferences around mean±sigma; `charging_utility` (U3) combines charge-time utility and normalized degradation penalty. `candidate_utility` averages the three equally; `select_action` takes masked argmax with fixed tie order. `execute_reposition` applies fixed-distance/time and energy cost. Production degradation uses normalized DOD component; temperature degradation is not fully represented. EV trigger <=20% SOC, capacity 75 kWh; full-charge release is a documented provisional rule. Stations implement capacity/queue/power constraints.

No routing DQN was found. Under the requested utility-repositioning roadmap, any externally retained old routing DQN should be classified **BASELINE / ABLATION or LEGACY, not FINAL ARCHITECTURE**; no nonexistent file is recommended for deletion. Utility control is active final-direction machinery, although assumptions need explicit approval.

## Policy network and federated learning

`LocalPolicyObservation`: state, chosen_action_index, action_mask, optional utility_vector and slot_id. This is supervised imitation of actual utility choices, not (s,a,r,s_next,done) RL replay. `build_routing_policy_model` is 87→64→32→5 logits with masked softmax. Local buffers/train_for_slot and global policy redistribution exist. `aggregate_policy_updates` validates shapes, architecture, finite tensors and sample counts, then sample-count-weighted FedAvg; zero-new-sample clients are excluded. main_slot trains, aggregates, broadcasts, builds next grid routing probabilities. Raw observations are forbidden in update payloads, but weights can still leak information. In-process synchronization is not a distributed failure-tolerant or privacy-preserving protocol.

## Pricing and first missing integration edge

Existing: configurable fixed arms, grid-level and request-level DisjointLinUCB, reward scaling, seven factors 0.85–1.15, plus optional daypart adjustment. The request 8D context is [scaled predicted demand, corrected supply, relevant OD routing probability, destination popularity, scaled trip distance, scaled P_base, scaled time, weather severity]. This is **not** roadmap [J_hat,J_disp_previous,incoming_dropoffs,routing_probability,destination_popularity]. An analysis-only `public_aggregate_state` in M10 exposes similar field names but is not a runtime DQN builder.

All pricing DQN items are missing: agreed action representation, runtime state, replay/terminal transition, primary Q network, target network, epsilon-greedy exploration, TD update, soft target update, DQN checkpoints and training loop. Existing LinUCB checkpoints do not satisfy them. Revenue rewards and supply estimates are reusable foundations, not proof that the target reward/state semantics are settled.

The current baseline chain connects demand→LinUCB→acceptance→dispatch/movement→statistics→utility/charging→local policy→FedAvg→next LinUCB context/reward. For the requested final hierarchy, the **first missing edge is predicted demand/previous operational aggregates → roadmap DQN state and pricing decision**. At the later end, (s,a,r,s_next,done) replay is also missing. Do not rebuild the functioning fleet/FedAvg loop to address this gap.

## Privacy / security / robustness

DP-SGD: MISSING; per-example privacy clipping: MISSING; calibrated noise: MISSING; accountant: MISSING; secure aggregation/cryptographic masks: MISSING; robust Byzantine aggregation: MISSING; poisoning/Sybil/membership inference/attribute inference/gradient or update inversion: MISSING. Ordinary numeric clipping, masks, payload rejection, reward scaling and weights-only sharing are implemented controls but not these methods. No attack stubs were mistaken for finished work.

## Tests and quality

Static AST count: **292 test functions/methods in 41 Python test files** (not a discovered runtime count; parameterized/subtests may differ). Quick current execution: **67 tests passed, zero failed**, covering time policy, pricing, pricing dispatch, production fixtures, statistics and historical sensitivity, in 0.912 s after imports. Full suite not run; no claim all 292 pass. No expensive training or simulator execution.

Before DQN training add tests for exact state order/units and lag timestamps; incoming-dropoff vs supply distinctions; action-to-price mapping; reward assignment vs completion semantics; terminal transitions/no bootstrap at done; replay sampling and seed determinism; Bellman targets; online/target isolation and soft update; exploration schedule; checkpoint+RNG restoration; one-episode conservation and next-state temporal leakage; explicit acceptance branch contract. Existing routing tests exercise a supervised model, not these Q-learning requirements.

## Legacy, duplication and partial experiments

| Item | Recommendation | Reason |
|---|---|---|
| Record-029/030 descriptive records | KEEP ACTIVE | Current descriptive evidence, not acceptance model |
| Runtime positive E and Eq31 branches | KEEP AS BASELINE | Executable but final behavioural convention unresolved |
| LinUCB and daypart policy | KEEP AS BASELINE | Alternatives for later final DQN comparisons |
| Utility routing / policy / FedAvg | KEEP ACTIVE | Integrated reusable foundation |
| M10 / elasticity_v2 global and fare-conditioned analyses | ARCHIVE LATER | Opposite ratios and earlier reference choices; retain provenance/tests until dependencies reviewed |
| NB1–NB5 legacy notebooks, extensionless NB2 | KEEP AS BASELINE / provenance | Traceability to active grid/CNN contracts; age alone does not make them obsolete |
| Old routing DQN / AE / LSTM-AE | Not located | No implementation classification can be assigned to nonexistent local evidence |

Record-030 time-pricing CSV currently contains **control, A and B only**, seed42, four slots each; C/D absent. README may still describe the earlier blocked state. This is an interrupted experiment, not a completed five-policy result. Existing baseline artifacts remain valid; presentation-ready Record-030 descriptive results are a separate folder/task.

## METHODOLOGY / DOCUMENT CONFLICTS REQUIRING DECISION

1. Signed descriptive e versus positive behavioural E versus Eq31: choose final behavioural contract; do not insert 1/e, abs(e) or a Gaussian conversion without justification.
2. Obtain the exact latest roadmap/manuscript document; verify its reciprocal equation, references and state/action specification. Root README describes a LinUCB milestone, not final pricing DQN completion.
3. Utility repositioning versus any routing-DQN proposal: current utility decisions plus supervised global policy are not reinforcement learning for drivers; preserve that distinction.
4. CNN is present. AE/LSTM-AE are not located; no basis to replace CNN on an assumption about their existence.
5. Current seven arms span 0.85–1.15; experiment factors multiply them and can exceed that interval. Unspecified roadmap examples cannot silently become final action limits.
6. Required F_hat/H_hat versus current wait/fare EWMAs and raw charging waits; define each denominator, timing and missing-value convention.
7. Source populations differ: January runtime grid mapping/behaviour artifacts versus Jan–Mar Record-029 cleaning. Shared terminology does not make these interchangeable.
8. Assigned revenue/driver wait versus completed-trip/platform-net-revenue/passenger-wait claims; finalize metric contracts before reward tuning.

## Next five implementation tasks, in exact order

1. **Decision/specification gate:** obtain latest roadmap and freeze the final acceptance branch, reference interpretation, action bounds and reward timing. Keep Record-029 descriptive unless explicit behavioural evidence/approval says otherwise. Option A baseline can proceed separately.
2. **Complete the DQN state contract:** implement and test lagged J_disp_previous, incoming dropoffs, routing probability/popularity and required F_hat/H_hat updates on the existing slot boundary; prevent future leakage.
3. **Implement standalone pricing DQN:** primary/target networks, replay, epsilon-greedy, TD loss, soft updates, deterministic seeds and checkpoint restore. Keep LinUCB default and reusable as baseline until parity tests pass.
4. **Wire an opt-in DQN episode into existing orchestration:** retain dispatch/EV/utility/FedAvg, add next-state/terminal/reward transitions; run tiny deterministic fixtures and resolve assignment/completion accounting.
5. **Run and persist the first non-private hierarchical episode:** start short, verify counts, reward/replay timing and restore reproducibility, then compare against a matched-seed LinUCB control. Expand horizon/seeds only after this works; privacy and attacks follow.

HIERARCHICAL_RL_IMPLEMENTATION_AUDIT_READY
