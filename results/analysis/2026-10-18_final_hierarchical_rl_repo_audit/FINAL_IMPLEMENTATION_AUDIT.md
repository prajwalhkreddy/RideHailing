# Final Hierarchical RL Repository Implementation Audit

Audit date: 18 October 2026. Repository: `/Users/prajwalhk/Keerthi/Implementation`.

## Executive baseline

The repository has a tested, integrated **LinUCB research baseline**, not a completed hierarchical pricing DQN. The updated CNN roadmap is now present. Its architecture/feature requirements materially differ from the current CNN, operational statistics, driver utilities, charging navigation and policy-state representation. The project’s next-30-minute CNN horizon is explicitly frozen and is a DOCUMENTED_ADAPTATION, not a mismatch. Existing baseline tests and historical runs do not certify those newer equations.

**First missing edge:** available forecasts/operational events → the specified lagged, origin–destination DQN state and pricing action. **First methodology-blocked edge:** sampled passenger sensitivity → a dimensionally consistent, approved acceptance threshold. A separate earlier dependency is the spatial-unit/topology decision before rebuilding spatial artifacts or retraining.

Most important findings:

1. The stored square-grid step is **3,000 US survey feet (~914.402 m)**, not 3,000 metres: `EPSG:2263` uses feet and construction adds `size_meters` directly to projected coordinates. Metadata calls it metres, while repositioning assumes 3 km. This is a verified unit discrepancy, not a choice between square and hexagonal grids.
2. CNN currently predicts +30 minutes using an expanding prior-weekday/period mean, four convolution layers (7→32→64→32→1), and linear output. The project’s +30-minute horizon is correct and must remain unchanged. Training-only historical-average construction and three ReLU convolution stages (7→14→7→1) remain substantive requirements; those architecture/preprocessing changes justify retraining and versioned feature/forecast regeneration, not a horizon change.
3. Roadmap acceptance adds `(1/epsilon)*relative_distance` to a USD fare. This requires epsilon in USD⁻¹; frozen Record-029 epsilon is dimensionless and signed. Current runtime uses a different positive behavioural parameter and an extra `P_base` multiplier. No direct substitution is certified.
4. Linear driver utilities, raw charging waits, absent dispatch-frequency EWMA, nearest-station teleportation and an 87-feature private-vehicle-conditioned policy are not the roadmap equations/state.
5. Plain FL works as infrastructure. The generic aggregator is sample-weighted, but **active main-slot orchestration sets each participating update's sample_count to 1**, so operational aggregation is equal-client averaging. It must not be reported as unequal-sample weighting in production.
6. New two-scenario analytical weather results cover all supported records. The frozen empirical sampler still covers literal weather codes 1/8 only; production uses January-only behavioural artifacts instead. None is silently interchangeable.
7. Pricing DQN, replay/target updates, formal privacy, secure aggregation and attacks are missing. A terminal-window issue also exists: production unconditionally asks for a forecast after the last available target.

This report is a durable baseline. Re-audit only changed contracts and their dependants; use the evidence inventory and acceptance criteria below rather than repeating a repository-wide audit.

## 0. Authority and source gaps

Precedence used: the explicit project decisions in the current audit request govern the named adaptations; otherwise updated roadmap → identifiable original manuscript for equations explicitly deferred to it → frozen project methodology → current implementation → historical plans/audits. In particular, the paper’s 10-minute horizon does not override the frozen project 30-minute horizon.

| Authority | Exact repository path | Finding |
|---|---|---|
| Latest roadmap | `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx` | Found and text-inspected in full, including author-specific CNN supplement. Authoritative for this audit. |
| CNN source manuscript | `notebooks/plan/papers/Joint_Optimization_of_Pricing_Dispatching_and_Repositioning_in_Ride-Hailing_With_Multiple_Models_Interplayed_Reinforcement_Learning.pdf` | Found; Zhang et al. 2024, Fig.4(b), Section IV-B, p.8598. Text confirms seven planes, historical means and 10-minute prediction. CNN architecture authority also explicitly transcribed in updated roadmap. |
| Eq31 baseline paper | `notebooks/plan/papers/MARL-Based_Pricing_Strategy_via_Mutual_Attention_for_MoD_Systems_with_Ridesharing_and_Repositioning.pdf` | Found; Eq31 matches logistic baseline. Not the reciprocal-acceptance source. |
| Earlier implementation guide | `notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf` | Found; M10 defines an older USD⁻¹ sensitivity and M12 reproduces additive reciprocal acceptance. Historical guidance, not permission to reverse frozen Record-029. |
| Other previous guidance | `notebooks/plan/Corrected_Final_Implementation_Process_NYC_RideHailing_PhD.docx`; `notebooks/plan/PhD_Implementation_Clear_Picture_and_Execution_Plan.docx`; `notebooks/plan/supervisor/Record-019.pdf` | Earlier implementations/clarifications; explain linear-utility lineage, not overrides of latest roadmap. |
| Record-029 | `data/processed/price_distance_sensitivity_record029/` and `results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar/` | Frozen numerical methodology/artifacts found; detailed distinctions in §4. |
| Final weather | `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/` | Final mapping, pooled/hourly/six-hour tables, figures, reproduction scripts and diagnostic history found. |
| Previous audit | `results/analysis/2026-10-14_hierarchical_rl_implementation_audit/IMPLEMENTATION_AUDIT.md` | Historical only. Its missing-roadmap and CNN/utility-complete judgments are superseded by this comparison. |

**SOURCE_GAP:** the roadmap refers to “two supplied documents” and a hierarchical manuscript for exact mean-price/deviation smoothing equations (α, β, dispatch smoothing ζ), but does not identify that manuscript bibliographically. No verified original hierarchical manuscript containing that full equation set was identified among the local papers/guides. The Zhang CNN source instead uses a conversion-rate formulation; it must not be assumed to supply the hierarchical reciprocal equation. Therefore original μ/σ/ζ recurrences, exact manuscript neighbourhood clockwise ordering, and original epsilon dimensional convention cannot be certified beyond the explicit roadmap/older-guide text. Obtain the identified manuscript/equation pages, or approve a fully specified project adaptation. Do not invent the missing recurrences.

PDF text extraction used pypdf; no rendering utility was available. Formula conclusions use explicit roadmap text and extracted Eq31/older-guide definitions; no unverified visual reconstruction of manuscript symbols is claimed. No internet lookup was needed: supplied local authority was inspected directly.

## 1. Frozen project methodology decisions

The latest request explicitly freezes the following project adaptations and methodological facts. These are not open horizon/population choices:

- **CNN:** predict the next30-minute main-slot demand; units requests/grid/30min. **DOCUMENTED_ADAPTATION**, not MISMATCH. Fifteen2-minute mini-slots implement within-slot dynamics; they do not change the forecast horizon. No10-minute handoff is required or recommended.
- **Passenger sensitivity:** Record-029 formula/reference/denominator/support decisions remain unchanged. Supported N=10,505,278; analytical CLEAR(non-precipitation)=codes1,2,3,5,N9,613,456; analytical RAIN(precipitation)=codes7,8,9,12,13,14,15,16,17,21,N891,822. Original Meteostat codes/names remain traceable.
- **Distinct weather contracts:** analytical passenger CLEAR/RAIN does not automatically replace CNN original WeatherCode encoding or authorize an acceptance-parameter conversion.

Current source confirms the30-minute horizon. Remaining CNN architecture,training-only historical feature and validation-isolation findings are independent of that approved adaptation. The report and implementation plan below supersede the earlier audit version’s10-minute conversion recommendation.

## 2. Current-state inventory and entry points

The appendix inventories all files in requested source/config/test/model/notebook/validation trees. `docs/` is absent. `src/federated/__init__.py` is an empty namespace, not a privacy implementation.

| Active area | Paths / role |
|---|---|
| Data and geometry | `src/data/{taxi,weather,config}.py`, `src/spatial/{grid,mapping,artifacts}.py`; legacy January demand/grid pipeline |
| Forecasting | `src/demand/{aggregation,tensors,model,inference,contracts}.py`; `scripts/{build_demand_master,build_cnn_dataset,train_cnn}.py` |
| Passenger/pricing | `src/pricing/{customer,customer_sensitivity,historical_sensitivity,linucb,state,request_context,scaler,reward,supply,time_policy}.py` |
| Operations | `src/dispatch/{generation,request,dispatch,contention}.py`, `src/fleet/{fleet,state,supply}.py`, `src/charging/{energy,stations}.py` |
| Routing and FL | `src/routing/{baseline,learning,federated,production}.py`, `src/simulation/grid_policy.py` |
| Orchestration | `scripts/run_production_experiment.py` → `src/simulation/production.py:ProductionExperiment` → `main_slot.py` → `pricing_dispatch.py`; generic `multi_slot.py`; small `validation_24h.py` harness |
| Reporting / baseline analyses | `src/reporting/*`; `src/analysis/passenger_sensitivity_m10.py`; `src/elasticity_v2/*` are historical analytical definitions |
| Configs | `config/config.yaml`, `pricing_context_scaler.json`, `pricing_reward.json`, opt-in `record030_time_pricing_experiment.json` |
| Demand model | `models/demand/cnn_model.keras`, `normalization.pkl`, `cnn_history.pkl`, `cnn_metrics.csv`, `cnn_predictions.npy`, `cnn_provenance.json` |
| Routing model | `models/routing/nb12_nb13_common_initialization_seed42.npz` and `_metadata.json`: common initialization, not a final learned DQN |
| Pricing model | `models/pricing/.gitkeep` only: no DQN checkpoint |

Production overrides YAML: request-level LinUCB, historical sensitivity with hierarchical fallback, corrected supply, served-revenue reward with training-reference scale, driver-contention dispatch and FedAvg every main slot. YAML defaults instead name Eq31, legacy-grid pricing, legacy dispatch/supply/reward; report the actual entry point, not defaults alone.

Persisted `results/validation/phase7d_48slot_final_integrated_seed42/` and `2026-09-08_48slot_run/` establish historical baseline runs, not DQN episodes. 298 target slots are available in production; the historical 48-slot output does not establish a successful complete 298-slot execution. `2026-10-13_record030_time_pricing_experiment/pricing_experiment_summary.csv` contains only control/A/B (four slots, seed42); C/D are absent.

## 3. Complete module status matrix

“COMPLETE” is scoped to the stated component, not overall scientific validity. “Blocks” means FIRST_NON_PRIVATE_DQN_EPISODE under the roadmap with the frozen project adaptations; a synthetic DQN fixture can precede most artifact work. Test names below are files under `tests/`; saved validation references are under `results/validation/`.

| # / component | Exists / roadmap match | Status | Code; tests; saved evidence | Exact gap / blocks? | Required work |
|---|---|---|---|---|---|
| 1 Data / passenger sensitivity | Yes / descriptive result yes, runtime bridge no | COMPLETE (descriptive scope) | `src/data`, Record-029 JSON/Parquets, final weather tables; `test_historical_sensitivity`, `test_elasticity_v2_population` | Runtime Jan-only data and acceptance are separate; bridge blocks | METHODOLOGY_DECISION, DATA_REGENERATION for approved downstream adapter |
| 2 Grid / timing | Yes / 30/2 yes; geometry units and topology no | PARTIAL | `src/spatial`, `fleet/fleet.py`; `test_grid`, `test_spatial_mapping`, grid metadata/mask/neighbours | Feet/metres discrepancy; 5 vs9 actions; yes | CONFIG_DECISION, CODE_CHANGE, possibly DATA_REGENERATION |
| 3 CNN | Yes / horizon adaptation; architecture/features partial | PARTIAL | `src/demand`; `test_cnn_*`, `test_demand_*`; six demand model files | Architecture, historical-average fit and validation isolation/evaluation; horizon correct; yes for compliant real-data episode | CODE_CHANGE, DATA_REGENERATION, MODEL_RETRAINING |
| 4 Acceptance | Three concepts implemented/documented / no final contract | METHODOLOGY_BLOCKED | `pricing/customer*.py`; `test_customer_sensitivity`, `test_pricing`; compatibility report | Dimension/convention conflict; yes | METHODOLOGY_DECISION then CODE_CHANGE |
| 5 Fleet / dispatch / revenue | Yes / partial | PARTIAL | `fleet`, `dispatch`; fleet/dispatch/contention/trip tests; per_slot/fleet_states outputs | Hard driver fare floor, passenger wait/pickup travel, reward/termination; yes | CONFIG_DECISION, CODE_CHANGE |
| 6 Statistics / EWMA | Yes / partial | PARTIAL | `simulation/statistics.py`; `test_statistics`, `test_driver_waiting`; nb9 CSVs | F_hat and H_hat missing, μ/σ source gap; yes | METHODOLOGY_DECISION, CODE_CHANGE |
| 7 Repositioning | Yes / no | PARTIAL | `routing/baseline.py`; `test_routing_baseline`; routing rounds | Linear U1/U2, no roadmap C_rep objective; yes | CODE_CHANGE, CONFIG_DECISION |
| 8 Charging | Yes / no navigation match | PARTIAL | `charging/*`; `test_energy`, `test_charging_stations`; fleet output | Nearest-station teleport, no U3 routing; yes for EV-compliant episode | CODE_CHANGE, CONFIG_DECISION |
| 9 Global policy | Yes / no state/output match | PARTIAL | `routing/learning.py`, `simulation/grid_policy.py`; routing-learning/grid-policy tests; initialization NPZ | 87 vehicle-dependent features,5 outputs vs public μ/σ/F/H state; yes | CODE_CHANGE, MODEL_RETRAINING (new initialization/local training) |
| 10 Plain FL | Yes / equal averaging at runtime | PARTIAL | `routing/federated.py`, `main_slot.py`; `test_routing_federated`; routing_rounds.csv | New schema, charging labels and participant semantics; yes after policy change | CODE_CHANGE, CONFIG_DECISION |
| 11 Pricing DQN | No | MISSING | `pricing/linucb.py` is baseline only; no DQN tests/artifact | Full DQN/state/transition implementation; yes | CODE_CHANGE, CONFIG_DECISION |
| 12 End-to-end hierarchy | Baseline yes / DQN no | PARTIAL | `simulation/*`; main/multi/production tests; historical48slot | DQN/state/reward/replay and terminal edge; yes | CODE_CHANGE |
| 13 DP | No | MISSING | No DP source/test/output | Per-example clipping/noise/accountant; no before non-private | CODE_CHANGE, CONFIG_DECISION |
| 14 Secure aggregation | No | MISSING | No crypto protocol/test/output | Masks/shares/dropout handling; no before non-private | CODE_CHANGE, METHODOLOGY_DECISION |
| 15 Robust aggregation / attacks | No | MISSING | Plain FedAvg only | Byzantine defenses/poisoning/Sybil; no before non-private | CODE_CHANGE, CONFIG_DECISION |
| 16 Privacy / attack evaluation | No | MISSING | No attack metrics/results | Concrete attack procedures, formal budgets; no before non-private | CODE_CHANGE, METHODOLOGY_DECISION |
| 17 Final evaluation | Baseline evidence yes / final no | PARTIAL | `reporting`, scripts, validation tables; `test_reporting` | DQN, comparative multi-seed CIs/ablations, privacy results; not first fixture | CODE_CHANGE, CONFIG_DECISION |

No full updated utility/EV/CNN module is certified COMPLETE merely because its older tests pass. The CNN forecast horizon and raster dimensions are separately certified DOCUMENTED_ADAPTATION items, not blockers.

## 4. Frozen passenger sensitivity and downstream artifact audit

Read-only streaming verification of **only weather_code, epsilon_status, epsilon** from the authoritative Parquet confirmed VALID N=10,611,392 and inclusive supported N=10,505,278. No epsilon was recalculated. Counts reconcile exactly with all 14 rows in `final_weather_2scenario_mapping.csv`:

- **CLEAR = 1,2,3,5**, non-precipitation analytical scenario: **9,613,456**.
- **RAIN = 7,8,9,12,13,14,15,16,17,21**, precipitation including liquid/frozen/mixed: **891,822**.
- Original labels/codes remain in authoritative source code fields and the final mapping's `original_weather_name`. Pooled CSVs retain aligned constituent code/name lists; the source Parquet does not itself store a weather-name field. Neither label means every observation is literally clear skies/rain.

Exact Record-029 files in `data/processed/price_distance_sensitivity_record029/`:

| File | Role / current limitation |
|---|---|
| `frozen_reference_values.json` | P_base=21.34586956773507 USD; tau_P=1 USD; L_base=3.01799878914405 miles; support479,000 |
| `authoritative_epsilon_methodology.json` | Signed epsilon=r_P/r_L; strict `abs(L-L_base)<0.005 miles` unresolved; all10,620,409 rows retained,9,017 null-epsilon records |
| `authoritative_epsilon_jan_mar_2026.parquet` | Full historical analytical source; valid/support filtering does not delete historical tails |
| `frozen_epsilon_support.json` | Exact inclusive [−12.890744316473482,15.442447741158892];10,505,278 support |
| `final_passenger_sensitivity_methodology.json` | EMPIRICAL_RESAMPLE, T1=00–03/T2=04–05/T3=06–15/T4=16–23, but **scope remains literal Clear1/Rain8** |
| `final_passenger_sensitivity_empirical.parquet` | Verified metadata:3,265,135 rows, only `time_group, epsilon`; duplicate frequencies preserved; **not** a10.5M two-scenario sampler |

The final analytical weather package has aggregate distributions/statistics, not an approved replacement behavioural sampler. Existing Record-029 JSON fields listing previously unresolved bounds/family are stage provenance; later support/final methodology decisions supersede those fields. Do not revise frozen values during integration.

Actual production dependency: `customer_price_sensitivity_2026_01.parquet` plus `_fallback_2026_01.parquet`, grouped by original WeatherCode×half-hour Period, cutoff Jan25 18:30 exclusive, condition-specific bases, absolute historical relative ratio and0.01-mile denominator eligibility, positive Normal sampling. It consumes neither the final analytical scenarios nor Record-029 empirical resampling. This is a **stale dependency relative to intended downstream Record-029 use**, but a deliberately preserved baseline contract, not permission to overwrite artifacts.

## 5. Passenger acceptance: four contracts and dimensional audit

Let r_P=(P−P_b)/P_b and r_L=(L−L_b)/L_b.

| Contract | Formula / units | Authority and source | Current usage / parameter source |
|---|---|---|---|
| A Record-029 descriptive epsilon | e=r_P/r_L, dimensionless, signed. Rearrangement is P=P_b(1+e r_L), a historical relation, not proven willingness-to-pay | Frozen JSON/authoritative Parquet | Offline evidence; literal1/8 empirical sampler exists; no runtime import found |
| B Positive behavioural E | E~Normal(mu,sigma²) conditioned E>0; P_max=P_b[1+r_L/E]; accept P_offer≤P_max | `pricing/customer_sensitivity.py:sample_positive_truncated_normal,maximum_price,evaluate_resolved` | Production historical branch; January condition-specific mean/SD and bases, hierarchical fallback. Normal parameters are not empirical-resampling frequencies |
| C Eq31 | probability=1/(1+exp(0.67*a*S/D−1.67)); U<probability | `pricing/customer.py`; MARL-based pricing paper Eq31 | YAML default/fixtures; no individual epsilon. a,S/D dimensionless; fare=empirical base fare×arm |
| D Updated roadmap reciprocal | P_offer=aP_b; P_max=P_b+(1/e)*r_L | Roadmap Module4/§24; earlier module guide M12 | Final contract not implemented. Dimensional consistency requires e in USD⁻¹ or an explicitly different normalized-price convention |

Earlier guide M10 used `r_L/(P−P_b)` (USD⁻¹), making its additive reciprocal expression dimensionally coherent. This is **not** the frozen Record-029 definition. With dimensionless Record-029 e, D adds a dimensionless term to USD. Runtime B restores currency through P_b but still uses the reciprocal, a positive-only parameter and different reference bases. This is not resolved by a matching variable name.

**METHODOLOGY_BLOCKED:** before any data-driven DQN training, the methodology owner must identify the governing behavioural acceptance equation, specify price/epsilon units and reference basis, define how (or whether) signed Record-029 observations enter it, authorize the applicable weather/time population and fallback, and validate hand calculations across positive/negative/zero deviations. No abs, reciprocal conversion, Gaussian replacement, clipping or invented transformation is recommended. A mathematical DQN fixture may use a declared mock environment; it cannot be represented as calibrated passenger behaviour.

## 6. Grid, geometry and neighbours

Study footprint is the union/intersection coverage of **all263 NYC TLC taxi-zone polygons**, including source-zone coverage beyond a Manhattan-only study. Source boundary: `data/raw/taxi_zones/taxi_zones.shp`. Trips have zone IDs; `assign_grid_ids_by_zone_legacy` samples among intersecting grid IDs using seeded RNG, not actual pickup/drop-off coordinate geocoding.

Verified source bounds in EPSG:2263 feet: [913175.109008804,120121.88125434518,1067382.508405164,272844.2940054685]. Full retained-square bounds extend to [913175.109008804,120121.88125434518,1069175.109008804,273121.8812543452]. Cells are full squares intersecting the zones, not clipped-only operating polygons; any intersection is retained.

| Property | Verified value |
|---|---|
| Generated / valid / production environment |2,652 /1,213 /1,213; older1,156 claim is unsupported by current artifacts |
| Raster |51 rows×52 columns=2,652;1,439 unused cells |
| GridID |Sequential0..1212, north-to-south then west-to-east; `OriginalGridID` retains pre-sort identity |
| Mapping |`grid_lookup.parquet` Row/Column unique for every GridID; `grid_mask.npy` sum1,213; production gathers predictions using those positions |
| Grid step |3,000 EPSG:2263 units =3,000 US survey feet≈914.401829 m; **metadata's grid_size_meters=3000 is incorrect for physical geometry** |
| Neighbour links |4,544 directed /2,272 undirected: N/S1,137 each, E/W1,135 each |
| Diagonals |None; verified row/column deltas only (−1,0),(1,0),(0,−1),(0,1) |
| Action indices |0 STAY,1 NORTH,2 EAST,3 SOUTH,4 WEST; side-adjacent one hop |
| Roadmap |1 current,2–9 clockwise surrounding neighbours; exact clockwise start deferred to missing manuscript |

Classification: side-adjacent topology is a **DOCUMENTED_ADAPTATION** in saved grid metadata, but adoption for the latest roadmap is **DECISION_REQUIRED**. It is not a literal nine-class MATCH. The feet/metres issue is **ACCIDENTAL_DIVERGENCE**. Do not automatically force H3,47×48,or eight neighbours. Decide whether to retain the physical raster with corrected units or regenerate true3-km cells; separately approve cardinal adaptation or implement the required eight-neighbour convention.

Affected if geometry/topology changes: spatial builder/lookup/mask/neighbours/zone assignments; demand master/tensors/model/forecasts and scalers; OD/popularity/station/fare-prior grids; production hash/count guards; dispatch search/centroid pickup; utility actions/masks/transition distances; 87D encoder and5-output policy; federated shape guards and initialization NPZ; grid-policy aggregation; pricing state/request-direction probability; related tests/config/saved baseline manifests. **Topology-only** change need not regenerate CNN geometry; **physical grid** change does. Record-029 price-distance estimates do not depend on GridID and remain frozen.

## 7. Time model and causal slot timeline

| Time / stage | Actual behaviour | Contract issue |
|---|---|---|
| Offline |January30-min demand; CNN X(t) predicts demand(t+30min); held-out arrays persisted |30-minute project adaptation matches; issue-time availability still needs certification |
| Start of30-min slot t |Load current and next target forecast, next popularity; sample exact rounded current-demand number of empirical requests; use prior routing probabilities |Predictions need issue/availability times; production next target loaded even at final boundary |
| Within15×2-min mini-slots |Requests ordered by arrival mini-slot/request ID; request-level LinUCB action and passenger test, dispatch; movement timers and charging advance |Roadmap OD action at slot start differs from per-request updates |
| Arrival timing |Empirical source pickup offset/120s floored to0..14 |Not current-weather/time-conditioned replay |
| Trip movement |Duration from sampled historical row; completion on timer reaching0 at mini-slot boundary |Pickup approach travel/wait not integrated |
| End main slot |Assigned fares and completed driver idle waits→statistics; idle eligible vehicles choose utility move |Fare outcomes are assignments, not trip completions |
| Reposition |Once end-slot, fixed3km/15kmh=12min; BUSY across mini-slots |Physical grid is~0.914km; duration consistency unresolved |
| Local train / FedAvg |At end-slot, latest up-to32 observations, one local epoch; production aggregates every slot and broadcasts |Updated policy must feed subsequent states only |
| Next probabilities/state |Mean eligible vehicle policy vectors by current grid; empty grid carries previous/uniform initial vector |Not prescribed public-grid state; no DQN next-state builder |
| Reward |Current request/grid LinUCB updates within pricing stage, based on accepted or assigned outcomes depending branch |No OD-slot DQN transition/reward boundary |
| Replay / terminal |Missing |No terminal no-bootstrap rule; final production next forecast unavailable |

Leakage findings: expanding HistoricalDemand excludes the current observation but incorporates earlier validation/test observations; this is walk-forward history, **not training-only frozen historical means**. Normalizer fits all outer X_train, including later internal-validation rows. Weather ffill/bfill can use future values at initial gaps; timezone remains naive/unresolved. Production uses full-month empirical OD/station placement, including evaluation-period records: legitimate simulation calibration only if declared, not leakage-free predictive holdout. Lagged popularity is genuinely past-looking (six prior slots; training-fitted quintiles). Next forecasts and popularity are loaded early but used at the end-slot; explicit issue-time tests are needed before asserting online availability. Current p(t) is not retroactively replaced by post-slot FedAvg p(t+1).

## 8. CNN input planes

All stored planes are [samples,7,51,52], converted to channels-last for Keras. Valid-cell values fill GridID positions; unused cells initially zero. All channels undergo channelwise z-score using X_train mean/SD over samples and **all raster positions**, including padding; zero std replaced by1. Thus padding becomes nonzero after normalization and is not masked in loss/evaluation.

| Current order/name | Source and encoding / spatial form | Roadmap comparison / leakage |
|---|---|---|
|1 HistoricalDemand |`aggregation.add_historical_demand`: strictly earlier expanding mean by GridID,DayOfWeek,Period; first occurrence0; spatially varying |Historical average, **not recent raw lag**; not frozen training-only lookup; validation/test earlier rows enter subsequent means |
|2 Temperature |Meteostat temp, hourly same value on all valid cells |Measured weather at input time; missing-data/forecast-availability decision |
|3 WindSpeed |Meteostat wspd, hourly broadcast |Same; provider units retained, no weather forecast model |
|4 WeatherCode |Meteostat coco numeric scalar, broadcast; standardized as ordinal number |Original code, not analytical CLEAR/RAIN; encoding is project adaptation |
|5 DayOfWeek |0..6, input timestamp, broadcast |Feature exists; roadmap forecast-interval alignment differs at day boundaries |
|6 Hour |0..23 input timestamp, broadcast |Feature exists; not cyclic; input vs target-time alignment requires correction |
|7 Period |`Hour*2+Minute//30`,0..47, broadcast |Half-hour-of-day, **not period within hour**; project30-minute within-hour positions are0/1; settle feature semantics without changing horizon |

All encodings are deterministic, no learned categorical encoder. Historical-average construction before chronological split means “training-only normalization” does not establish training-only historical feature fit. Need separate train/validation/test split first, fit historical lookup and scalers only on optimizer-training period, and declare forecast-weather availability/fallback without future backfill. Do not replace the original CNN weather code with sensitivity scenario labels absent an authoritative requirement.

## 9. CNN architecture and hyperparameters

| Item | Current (`demand/model.py`, provenance) | Updated contract / classification |
|---|---|---|
| Channels/stages |7→32→64→32→1, four convolutions |7→14→7→1, three stages: MISMATCH_REQUIRES_CHANGE |
| Kernels |3×3 for three hidden convolutions;1×1 output |Paper not fully prescribing kernels: DOCUMENTED_ADAPTATION, choose for updated3 stages |
| Padding/stride |same / default1, no pooling |Spatial preservation MATCH; kernel/stride implementation choice |
| Activations |Hidden ReLU; linear output |Output must ReLU: MISMATCH_REQUIRES_CHANGE |
| Loss/optimizer/LR |MSE / Adam /0.001 |DOCUMENTED_ADAPTATION; not author-reported values |
| Batch/epochs |32 /50 requested |DOCUMENTED_ADAPTATION; saved history is actual epoch record |
| Early stop |val_loss,patience5,restore_best_weights=True |DOCUMENTED_ADAPTATION |
| Validation/shuffle |Keras last20% of outer training data, remaining training shuffled |Temporal validation order exists; scaler contamination and historical lookup require correction |
| Padding evaluation |Unmasked all-cell loss/metrics |DOCUMENTED legacy adaptation, not proof valid-grid evaluation is adequate |

A model passing current `test_cnn_model.py` enforces the legacy architecture, not the new one. Those tests must be versioned/updated when implementation is authorized. No model was trained in this audit.

## 10. Raster contract

51×52 is a technically lossless representation of the stored square grid, unlike forcing47×48. Verified unique GridID and Row/Column, mask sum, neighbour deltas, and production gather logic. The dimension difference is a **DOCUMENTED_ADAPTATION**; it does not itself require changing dimensions. Padding is safe for identity/extraction but **not excluded from normalization/loss/metrics**. Add valid-mask-aware evaluation and explicitly choose loss masking. A physical-grid correction may change dimensions and requires re-verification; a topology-only change does not. Save a raster version/hash in forecast outputs.

## 11. Frozen 30-minute forecast validation

**PROJECT DECISION: next30-minute main-slot forecast = DOCUMENTED_ADAPTATION.** The paper’s10-minute reference does not require a project10-minute model, three-forecast aggregation or10→2-minute allocator. No such layer exists and none is required.

| Contract | Evidence | Conclusion |
|---|---|---|
| Observed demand interval |`aggregation.aggregate_pickup_demand` floors pickup timestamp to30min and counts `(TimeSlot,PUGridID)` |Count covers half-open[t,t+30min), units requests/grid/30min |
| Supervised next target |`tensors.build_cnn_tensors`: X=features[:-1],y=Demand[1:], complete consecutive30min snapshots |Input anchor t predicts interval[t+30min,t+60min); target timestamp=t+30min |
| Runtime alignment |Production `cnn_target_timestamps=input_timestamps+30min`; exact Row/Column gather |Simulation slot start t consumes prediction for[t,t+30min), not a10-minute rate |
| Spatial identity |Unique GridID↔Row/Column plus mask; only valid positions gathered |No lost or duplicated valid grid |
| Integer conversion |`_request_counts`: `rint(max(0,value))` for origins with empirical rows,else0 |Explicit deterministic conversion; missing-origin suppression must be reported, not concealed |
| Mini-slot conservation |`generate_requests` creates exactly one request per integer count, asserts total, assigns empirical offset to0..14 |Sum of15 mini-slot requests equals intended integer30min total; not necessarily sum of fractional/raw predictions |
| Information availability |Features/weather anchored to input interval; existing arrays have target keys but no forecast issue-time metadata |No blanket no-leakage certificate; see §§7/12 for historical-average,validation and weather availability risks |

The30-minute target itself is correctly constructed. Future prediction packaging should expose `GridID, issue_time, interval_start, interval_end, predicted_request_count, model_version, grid_version, feature_cutoff`, with **30-minute intervals unchanged**. This is provenance/availability validation, not a new forecasting layer. At simulation slot t, consumed features must be available at t; current input-timestamp naming alone does not prove this. The forecast for the following slot, loaded early by production but used in end-slot routing, needs a cutoff/issue-time guard. The final-window lookahead defect remains independent of horizon choice.

Read-only saved-target spot checks (first, middle and last held-out samples; all1,213 grids in each) independently matched `y_test.npy` exactly to `demand_master_2026_01.parquet` at the next30-minute timestamp:

| Input anchor | Target interval start | Target interval end (exclusive) | Observed request total |
|---|---|---|---|
| 2026-01-25 18:30:00 | 2026-01-25 19:00:00 | 2026-01-25 19:30:00 | 763 |
| 2026-01-28 21:00:00 | 2026-01-28 21:30:00 | 2026-01-28 22:00:00 | 4,345 |
| 2026-01-31 23:00:00 | 2026-01-31 23:30:00 | 2026-02-01 00:00:00 | 4,276 |

These checks verify persisted sample alignment; they do not certify every source weather observation as available online. The full construction contract and quick tensor/arrival tests provide complementary coverage.

## 12. CNN training, leakage and evaluation

Persisted `time_train.npy`:1,189 input snapshots Jan1 00:00–Jan25 18:00; targets+30min. `time_test.npy`:298 inputs Jan25 18:30–Jan31 23:00; targets Jan25 19:00–Jan31 23:30. Outer split is chronological80/20. Internal Keras split yields951 optimizer-training inputs through Jan20 19:00,238 validation inputs Jan20 19:30–Jan25 18:00. Target endpoints are30min later. Shuffle applies to the optimizer-training partition, not random train/test assignment.

Scaler fits all1,189 outer-training inputs, so internal-validation distribution influences normalization; it does not use outer test. Historical average is an expanding past-mean across the month rather than a train-frozen table. No separate Jan–Mar CNN model exists in the inspected model directory. January mapped data includes3,699,638 mapped rows,3,699,633 in-month pickups used for demand, a different population from Record-029.

| Deliverable | Evidence / status |
|---|---|
| MAE/RMSE/R²/MAPE |`cnn_metrics.csv`:0.6337751746 /2.5915691905 /0.8985528946 /83.4894835949%; COMPLETE for legacy saved evaluation only |
| MAPE definition |Actual>0 mask, unmasked raster flattening otherwise; sparse targets require interpretation |
| Model / history / scaler / predictions |Persisted six demand files; COMPLETE legacy artifacts |
| Historical-average / seasonal baseline scores |MISSING from current saved model/evaluation package |
| Observed-versus-predicted grid maps |No standalone current model-evaluation artifact identified; legacy notebook visualizations are not a versioned updated evaluation deliverable: MISSING |
| Grid/time-keyed30-minute forecast table |MISSING standalone table; runtime correctly reconstructs30-minute keys from arrays and grid lookup: PARTIAL artifact packaging, not horizon mismatch |
| Leakage-safe updated split/preprocessing |PARTIAL: chronological outer split yes, training-only feature fit/validation isolation no |

**CNN retraining is required for the specified architecture and training/validation preprocessing corrections**, after physical-grid and feature contracts are finalized. It is **not required because of the horizon**: retain next30-minute targets. Target construction and raster identity pass the inspected contract; changes to those are not justified merely by the source paper. Keep old weights and metrics as baseline history. Do not compare new valid-grid metrics with old padded-grid metrics without identifying the metric population.

## 13. CNN weather versus passenger weather

CNN uses original Meteostat numeric WeatherCode. Passenger descriptive analysis consolidates14codes into analytical CLEAR/RAIN. Request pricing uses an additional hand-coded weather-severity mapping in `request_context.py`, not either of those feature contracts. There is no explicit latest-roadmap requirement to apply passenger two-scenario grouping to the CNN. Keep them separate, version the mappings, and test original-code coverage. The request severity mapping omits code17, another potential coverage issue if Jan–Mar runtime is broadened; do not guess a severity.

## 14. Request generation

`ProductionExperiment._request_counts`: per-grid `int(rint(max(0,prediction)))`; grids lacking empirical-origin rows produce0 requests. Therefore generated total can differ from the raw real-valued forecast sum. `dispatch/generation.py` samples intact January rows uniformly with replacement conditional **only on pickup grid**; row frequencies preserve empirical OD and joint distance/duration/fare. It is not exact replay, not Poisson demand and not weather/hour-conditional resampling.

Source fields: PUGridID,DOGridID,pickup/dropoff timestamp,trip_distance,fare_amount. Runtime filters nonfinite fields, duration≤0, negative distance/fare; it does not enforce the Record-029 complete cleaning contract. Source row IDs retain sampled-row provenance. Miles convert to km by1.609344. Source pickup offset inside its own historical half-hour determines mini-slot0..14; sampled arrival date/weather are not preserved as current simulation conditions. Current simulation weather/period separately select acceptance parameters. Persistent request RNG is spawned from explicit seed42 alongside customer/acceptance RNGs; policy divergence can change draw consumption.

Main-slot integer totals equal generated request counts; summing the15 mini-slot counts conserves those requests. No10-minute handoff exists or is required. Fractional forecasts are rounded and negative values floored before sampling; conservation is against those intended integer counts, not exact raw forecast sums. Full-January empirical calibration includes the evaluated January dates; freeze a calibration split or explicitly describe conditional historical simulation rather than independent generalization.

## 15. Fleet and dispatch

Current production creates5,000 IDLE vehicles, uniform-with-replacement over1,213 grids, seeded42; all are initialized by `initialize_ev_fleet` (effectively100% EV). There is no operative non-EV type/mixture contract. States IDLE/BUSY/CHARGING; action strings distinguish transport/reposition/charging queue. BUSY timers advance2 minutes, retain origin until completion, then move to destination and become IDLE. Energy is debited for passenger/reposition travel. Requests remain ASSIGNED rather than acquiring a persisted completed-trip status/ledger.

Local/side-neighbour search and energy eligibility exist. Legacy dispatch chooses FCFS lowest eligible ID; production computes driver contention by comparing request utility with best routing alternative, selects lowest pickup-centroid distance, then greatest request utility, then vehicle ID. It does **not** implement the explicit hard constraint `offered_fare >= P_i_min`. Current price preference is an input to a utility score, not a certified minimum-fare threshold. Driver preference profiles are fixed Uniform(3.9340498543,36.5337637351 USD); wait preference Uniform(0,30 minutes), both documented baseline assumptions.

Passenger allowed wait/max pickup time is absent; `request.wait_time=0` on assignment, unserved otherwise, no calibrated retry/cancellation process. Pickup centroid distance is a ranking feature, not charged travel time/energy. Passenger trip duration comes from the sampled row, default2min only if absent. Reposition uses12min; charging entry teleports. FCFS ordering is present, but roadmap dispatch suitability/wait semantics remain incomplete.

## 16. Revenue and reward contract

| Quantity | Existing meaning / availability |
|---|---|
| Offered fare |Eq31: empirical source fare×arm; historical branch: resolved condition P_base×arm (×optional daypart factor) |
| Accepted fare |Passenger threshold/probability passed; can still be unserved |
| Assigned fare |Accepted plus vehicle assignment; active production gross revenue sums these fares |
| Completed fare |No distinct per-trip settled fare ledger; must not label assignment revenue completed revenue |
| Gross revenue |Available, assigned dispatch fares in production |
| Driver earnings / platform net |MISSING commission/share/cost allocation; gross is not net platform income |
| Reposition cost |Energy/time tracked; no roadmap monetary/normalized C_rep deduction in utility/revenue |
| Charging cost |Energy/power tracked; no approved tariff/net-cost ledger |
| Legacy LinUCB reward |Accepted revenue per generated opportunity /training fare reference, clipped[0,1] |
| Production LinUCB reward |Served request fare or0 /fixed training reference; linear scaling, no clipping of economic revenue |

Roadmap requires OD-slot sum `Σ offered_fare * 1(destination=g') * successful_dispatch`. Its x denotes dispatch within allowed passenger wait, not necessarily trip completion. The closest existing quantity is assignment revenue, but missing pickup/wait rules and an OD ledger prevent exact certification. Freeze event timing, refunds/cancellations/episode-boundary outstanding trips, units (gross USD), cost treatment and discount time unit before implementing the final DQN reward. Do not silently substitute net profit or completion revenue. Current LinUCB updates do not constitute delayed DQN reward/replay.

## 17. Grid statistics / EWMA

`OperationalStatistics.update_slot` accepts successful `FareObservation`s; production supplies ASSIGNED offered fares. Driver waits are completed idle episodes ending in dispatch, **not passenger waits or charging waits**. Means and SDs use ddof0. All four existing EWMAs apply `alpha*current+(1-alpha)*previous`, alpha0.30, first observation initialization, missing observations carry forward. Production seeds fare mean/SD from training-only grid priors/global fallback; driver-wait history begins missing. Update occurs once after a main slot.

| Required quantity | Current data / gap |
|---|---|
| μ |ewma_fare exists,USD; uses same0.30 coefficient, previous carried state. Exact manuscript μ recurrence cannot be certified (SOURCE_GAP) |
| σ |ewma_std_fare exists,USD; smoothing slot populationSD directly is not necessarily manuscript deviation estimator; β not independently implemented |
| F_hat |MISSING. `fare_count` is raw successful-assignment count, not smoothed count/time. Need previous-slot N_dispatch/Δt and δ, units1/minute or explicit alternative consistent with W_max |
| H_hat |MISSING. `charging_wait` is mean **current queue elapsed wait**,0 for empty, missing non-station; not κ-smoothed completed/expected waiting time |
| ζ J_disp |No dedicated lagged smoothed successful-dispatch statistic; count/events are reusable inputs |

Required: obtain μ/σ/ζ equations; define rates/time units, empty-slot treatment (zero arrivals versus missing measure), initialization and lag; implement separate F/H fields and feed utilities/policy. `fare_count != F_hat`; `raw charging_wait != H_hat`; `ewma_wait` is not either substitute.

## 18. Driver utility comparison

| Item | Current | Roadmap / classification |
|---|---|---|
| U1 |clip((preference−(μ−σ))/(2σ),0,1), increasing with preference; zeroσ step |1−Φ((P_min−μ)/σ), decreasing with P_min: MISMATCH |
| U2 |clip(((mean_wait+sd_wait)−wait_preference)/(2sd_wait),0,1); unseen waits→0.5 |1−exp(−F_hat*W_max): MISMATCH |
| C_rep |Absent from maximizing objective; fixed distance/time/energy applied after selection |Subtract approved movement cost: MISSING |
| Combined score |(price+wait+charging)/3 |U1+U2−C_rep for ordinary repositioning: MISMATCH |
| Candidates |STAY plus4cardinals with mask |Up-to8neighbours: DOCUMENTED_ADAPTATION / DECISION_REQUIRED |
| Tie handling |Fixed STAY,N,E,S,W order |Deterministic implementation choice; document for approved topology |
| Zeroσ guard |Linear step branch exists |Numerical protection exists but not correct limiting Gaussian-tail utility; replace/test under chosen convention |

Linear utilities have historical guidance lineage; label them baseline, not accidental undocumented invention. They still do not match the latest authority. No independent per-driver DQN is required; utility control remains the requested architecture.

## 19. EV charging

Current75kWh battery; initial SOC rejection-sampled Normal(mean.50,sd.05) within[.50,.70]; initial_energy_kwh60 and minimum_energy_kwh7.5 remain reference config fields, while operative trigger isSOC≤.20 (15kWh). Consumption0.15kWh/km; per-EV30kW×.90efficiency=27kW effective; full75kWh release (provisional). From15 to75kWh nominal effective duration133.33min, before queue/discrete advancement. No new calibration implied.

15 stations ranked by full-January pickups+dropoffs, deterministic ties. Each station max3,000kW supports100 simultaneous30kW reservations; physical charger-count limit absent. Unbounded queue, FCFS arrival-order then seeded random tie then vehicle ID. Current queue mean elapsed wait exposed; promotion follows release. No physical road routing/congestion model.

Roadmap U3=`1−exp(−H_max/H_hat)` minus C_rep over charging destinations, followed by feasible next hop: **MISSING**. Current `present_vehicle` chooses nearest projected-centroid station, immediately relocates vehicle with zero time/energy. Existing `charging_utility` is clipped charge-to-full utility minus normalized degradation, not U3. Degradation functions contain temperature/DOD formulas, but active production uses normalized DOD component and omits separate temperature term. Threshold, fleet mix, power/capacity/release/queue assumptions require configuration sign-off; charging navigation needs code, not merely renamed variables.

## 20. Global policy network

`routing/learning.py` fixed feature order: vehicle.current_grid,vehicle.energy_level, then17 fields for each STAY/N/E/S/W: valid,grid_id,predicted_demand,supply_total,supply_idle,supply_busy,supply_charging,mean_fare,std_fare,ewma_fare,ewma_std_fare,mean_wait,std_wait,ewma_wait,ewma_std_wait,charging_available,charging_wait. Total2+5×17=87, missing numeric values encoded by helper conventions; invalid actions masked.

Architecture87→64ReLU→32ReLU→5linear logits; masked softmax, cross-entropy chosen utility-action labels; Adam.001,latest32 samples,one epoch,capacity1,000. Labels collected from ordinary reposition decisions only; charging-navigation labels absent. Softmax is valid and tested. Global inference is per eligible vehicle and then averaged by grid; empty grids carry old probabilities or uniform-valid initialization.

Roadmap state contains neighbouring μ/σ/F_hat and global charging H_hat; current state includes private per-vehicle energy and many other features but lacks F/H, so **PARTIAL/MISMATCH**. Need agreed aggregate/public feature contract, ordering/scale, masks and charging labels. Topology change alters state width, output labels/masks, hard-coded federated tensor shapes, initialization/checkpoints, grid-policy and OD routing-probability code. Cannot load old5-class weights into a new9-class head unchanged. Aggregation pattern is reusable after schemas are parameterized.

## 21. Federated learning

Local bounded buffers store encoded state/chosen action/mask/optional utility vector/slot ID, no RL transition. Eligible participants are drivers with a recorded utility decision in the current slot, even if that decision then initiates movement; charging vehicles do not contribute navigation labels. Each local learner trains at most once per slot on latest min(32,buffer) records, one epoch. Local Adam state persists across `set_weights` broadcasts; optimizer-reset convention is a documented implementation choice to settle.

Payload: vehicle_id,weights,sample_count,state_dimension,action_order,architecture_version; raw observations/replay rejected. Generic `aggregate_policy_updates` uses sample counts and skips zero-count updates; all-zero returns no update. **`main_slot.py` overrides sample_count=1 for each current participant**, giving the roadmap's plain equal average among submitted participants. Population is not literally every idle driver if no observation/eligible statistics; document that eligibility adaptation. Production federates every slot, generic harness supports selected slots. Broadcast occurs after local training, then next-grid probabilities are computed; prior probabilities feed current pricing. Common initialization and explicit seeds exist; no full resumable distributed protocol/checkpoint/RNG state established.

Plain FL is functional baseline machinery, not privacy/security. Schema checks and weights-only payloads do not stop update leakage or malicious clients. Reuse aggregation arithmetic/orchestration after policy shapes/labels change; replace fixed `_EXPECTED_WEIGHT_SHAPES` and architecture guards consistently.

## 22. Final pricing-state readiness

The five “components” need not mean five scalar input neurons: p is a vector and dimensionality depends on topology.

| Component | Availability | Source/shape/unit/time | Missing contract / leakage risk |
|---|---|---|---|
| J_hat(g,t) |PARTIAL |Forecast[GridID], request count/30min, target timestamp; production array gather |Horizon/units match frozen project decision; no explicit issue-time ledger or final DQN wiring; architecture/preprocessing issues remain |
| J_disp(g,t−1) |PARTIAL events, MISSING final feature |Prior assigned request events/fare_count per grid; count vs ζ-smoothed statistic unspecified |Dedicated carried lagged feature absent; must not use same-slot outcomes for its own action |
| I(g,t) |PARTIAL |`pricing/supply.py:build_raw_pricing_supply` already counts BUSY vehicles by destination completing in (slot_start,slot_start+30min], returning `incoming_supply` alongside idle/total supply |Reusable estimator exists, but all BUSY actions include repositioning, not passenger drop-offs only; not separately wired as final DQN I. Approve passenger-arrival scope, public aggregation/privacy and timestamps |
| p(g,t) |PARTIAL |Grid→5probabilities dimensionless from previous global update |Wrong policy input contract; topology decision; preserve prior-slot lag |
| destination popularity(g',t) |AVAILABLE baseline |Per-grid current timestamp; trailing6prior30min dropoff means, training global quintiles encoded0,.25,.5,.75,1 |Historical exogenous observations vs simulated updates must be declared; no future/current dropoff used in trailing mean |

No OD-keyed final state builder. Current legacy8D context `[scaled_demand,scaled_supply,p5,popularity]`; production request8D context `[scaled_demand,scaled_corrected_supply,relevant_OD_p,destination_popularity,scaled_distance,scaled_P_base,scaled_time,weather_severity]`. Neither includes the requested J_disp_previous/I contract as separate final state elements. Corrected supply already contains an incoming component; expose and validate it rather than rebuilding an arrival estimator from scratch. Exclude or separately account for reposition arrivals if I is specifically passenger drop-offs. The analysis-only M10 public-state helper is not wired into runtime. FIRST missing state edge: lagged operational aggregates/expected arrivals plus aligned forecasts → runtime DQN state.

## 23. Pricing actions

`pricing/linucb.py:PRICING_FACTORS`, YAML and customer validation use{.85,.90,.95,1,1.05,1.10,1.15}. LinUCB keeps separate arm parameters; Eq31 validates exact membership. Historical dispatch price accepts positive factors, and opt-in daypart policy can multiply outside seven-arm bounds. `config/record030_time_pricing_experiment.json` defines control and A/B/C/D factors; these are baseline experiments, not a final action-set approval.

Status: **FROZEN for historical baseline; DECISION_REQUIRED for DQN**. Roadmap.8..2 step.1 is illustrative, not a mandatory replacement. Confirm OD-slot versus request cadence, factor limits, base-fare components, training/evaluation exploration and daypart interactions. If changed, update action mapping/fare validation/reward reference/tests together; do not allow old static maximum-factor normalization to silently describe a new action set.

## 24. Pricing DQN implementation checklist

| Element | Current status |
|---|---|
| Final OD state builder / action mapper |MISSING (baseline contexts/arms reusable after decision) |
| Online Q / target Q networks |MISSING |
| Shared replay of(s,a,r,s_next,done) |MISSING; local routing buffers are supervised labels |
| Epsilon-greedy / schedule |MISSING; epsilon sensitivity is a different concept |
| Bellman target / terminal masking |MISSING |
| TD loss / optimizer / batch / gamma |MISSING, not settled configuration |
| Soft target update τ |MISSING |
| DQN checkpoint / optimizer / RNG restoration |MISSING |
| Training/evaluation episode driver |MISSING |

Required roadmap targets: y=r+γmaxQ_target(s',a'), terminal→y=r; loss(1/(2batch))Σ(y−Q_online)²; target←(1−τ)target+τonline. No implementation exists to verify. LinUCB is contextual bandit immediate-payoff learning, not a target-network RL implementation. Routing softmax learning is not DQN either.

## 25. End-to-end edge audit

| Edge | Status | Evidence/gap |
|---|---|---|
| CNN→baseline pricing |CONNECTED (30-minute horizon adaptation) |Grid/time mapping and interval match; model/preprocessing compliance assessed separately |
| CNN+operational aggregates→DQN state/action |MISSING |First missing edge |
| Price+sensitivity→final acceptance |METHODOLOGY_BLOCKED |First methodology-blocked edge, §5 |
| Baseline acceptance→dispatch |CONNECTED baseline / PARTIAL roadmap |No hard fare floor/passenger wait contract |
| Dispatch→fleet movement |CONNECTED baseline |Sampled duration/energy; pickup approach absent |
| Fleet/events→statistics |PARTIAL |Fare and driver wait only, no F/H estimator |
| Statistics→driver utility/charging |PARTIAL |Wrong equations; teleport charging |
| Decisions→local observations |PARTIAL |Reposition only, no charging label path |
| Local model→FedAvg |CONNECTED baseline |Equal operational client weight; fixed schema |
| FedAvg→next routing probability |CONNECTED baseline |Masked probabilities; carry-forward |
| Routing+arrivals→next DQN state |MISSING |No final state/issue-time contract |
| Dispatch outcomes→DQN reward |PARTIAL inputs / MISSING wiring |Gross assigned ledger reusable; final OD timing unsettled |
| Next state/reward→replay/TD training |MISSING |No DQN transition |

Terminal defect: `ProductionExperiment.run_slot` always calls `_demand(timestamp+30min)` and `_popularity` before running; at Jan31 23:30 it requests Feb1 00:00, absent from298 target keys. A short historical run avoids this. Implement explicit terminal transition or approved extra forecast coverage, not fabricated next demand.

## 26. Environment configuration freeze matrix

“Baseline” means implemented/persisted, not newly approved as final. Blocks distinguishes real-data episode from synthetic algorithm fixture.

| Setting | Current value and evidence | Frozen? / decision needed | Blocks real DQN? |
|---|---|---|---|
| Study area/boundary |All263 TLC zones; spatial builder and source shapefile; bounds§6 |Baseline / approve retained domain |Yes |
| Grid type/step |Square,3000feet mislabeled metres; config/grid metadata |No correct physical contract / retain~914m or regenerate3km |Yes |
| Raster / valid count |51×52/1213,grid_lookup/mask; production constant |Baseline / contingent on geometry |Yes |
| Neighbour topology |Cardinal4+stay; neighbour artifact |Documented adaptation / approve vs8+stay |Yes |
| Slot / mini-slot |30min /2min,YAML,production |Roadmap-aligned |No |
| CNN horizon |Next+30min,requests/grid/30min; tensors and production |FROZEN PROJECT DECISION / DOCUMENTED_ADAPTATION; no horizon decision needed |No |
| CNN model/checkpoint |Legacy7→32→64→32→1,models/demand/cnn_model.keras |Architecture/preprocessing corrections required; retain horizon |Yes for compliant real-data episode |
| Request generation |Rounded forecast counts,origin-conditioned empirical January rows |Baseline / calibration split and conditioning |Yes |
| Traffic |No dynamic traffic field/model |Explicit constant/empirical-duration assumption requires sign-off |For calibrated episode |
| Vehicle speed |15km/h,routing config |Baseline / calibrated movement consistency |Yes |
| Travel-time model |Empirical passenger duration;12min fixed reposition;zero pickup/station travel |Incomplete / correct units and charging routing |Yes |
| Fleet size |5000,YAML and production profile guard |Baseline / final scale decision |For real experiment |
| Initial fleet |Seeded uniform valid grids |Provisional / sign-off |For real experiment |
| Types / EV fraction |All initialized EV;100%,no type split |Baseline / sign-off mixture |For real experiment |
| Battery |75kWh,energy config |Reference-backed baseline / calibration |For real experiment |
| Initial SOC |TruncatedNormal .50,.05 within[.50,.70] |Project baseline;60kWh config reference not active sampled rule |For real experiment |
| SOC trigger |≤.20 (15kWh) |Project baseline;7.5kWh reference field not active trigger |For real experiment |
| Consumption |.15kWh/km |Reference baseline / distance consistency |Yes |
| Stations |15 top January activity grids |Baseline / exogenous calibration sign-off |For real experiment |
| Charging rate |30kW,.90efficiency |Project baseline |For real experiment |
| Station capacity |3000kW=>100 concurrent;no physical-port bound |Baseline / physical calibration |For real experiment |
| Queue/release |FCFS seeded ties,unbounded;full75kWh release |Full release provisional |For real experiment |
| Driver prefs |Uniform fare profile and wait0..30min,metadata§15 |Baseline / convert to true minimum/wait domains if approved |Yes |
| Base fare |Condition P_base production;source fare Eq31;Record029global21.34586956773507 |Different contracts / acceptance sign-off |Yes |
| Pricing actions |Seven.85..1.15;roadmap.8..2 illustrative |Baseline frozen / final decision |Yes |
| Sensitivity artifact |January W×Period parameter/fallback Parquets |Baseline / cannot silently swap Record029 |Yes |
| Weather mapping |Original codes runtime;analytical CLEAR/RAIN final report |Analysis frozen / downstream scope unresolved |Yes if using final empirical |
| Acceptance |PositiveE production;Eq31 YAML |Final methodology blocked |Yes |
| Reward |Scaled assigned-gross production;accepted-normalized legacy |Final OD success/wait/terminal semantics unsettled |Yes |
| Episode horizon |Available298slots Jan25 19:00–Feb1 exclusive;historical48;short flags |Final terminal/horizon decision |Yes |
| Episode count |No DQN count configured |Missing |Yes |
| Random seeds |42;SeedSequence request/customer/acceptance streams;common policy init |Baseline reproducible / multi-seed list not frozen |For evaluation |
| DQN hyperparameters |No replay/batch/gamma/tau/exploration/network values |Implementation decisions required |Yes |
| EWMA |.30 generic;F/H/ζ absent |Exact equations/source/coefficients needed |Yes |
| FL cadence |Every main slot production |Implemented adaptation / participant and schema agreement |Yes after changes |

## 27. Privacy and secure aggregation existence

DP-SGD, per-example norm clipping, calibrated gradient noise, RDP/moments accountant, per-driver epsilon/delta history: **MISSING**, not implemented stubs. Secure aggregation, pairwise masks, secret sharing, dropout recovery and collusion assumptions: **MISSING**. Parameter-name rejection/finite checks are implemented but are not privacy. `src/federated/__init__.py` does not supply these functions. Introduce privacy only after a reproducible non-private DQN baseline; define repeated driver participation and sampling assumptions before claiming a budget.

## 28. Robustness and attacks existence

Poisoning, Sybil, strategic misreporting, coordinate median, trimmed mean, Krum, Multi-Krum, Bulyan, membership inference, attribute inference, gradient/update inversion: **MISSING** in executable source/test/evaluation pipeline. Earlier weather-curve trimming is unrelated to robust FL aggregation. No attack outcome can be inferred from numerical-shape validation. Secure-sum compatibility of any robust aggregator requires explicit protocol design; not every defense can inspect hidden client updates.

## 29. Final evaluation readiness

| Metric / baseline | Current evidence | Readiness |
|---|---|---|
| Successful dispatch %,gross revenue |per_slot/reporting and48slot saved baseline |PARTIAL: assignment not completed-trip/net revenue |
| Reposition movement/cost |Action counts,energy/time tracked |PARTIAL: no final C_rep monetary/normalized ledger |
| Charging wait/energy violations |Queue and energy checks,validation tables |PARTIAL: current elapsed queue wait/teleport caveat |
| Privacy / attack metrics |None |MISSING |
| Rule-based / LinUCB |LinUCB active;fixed/control factors available;no matched final rule-surge study |Baseline available / final comparison missing |
| Plain FL |Integrated with LinUCB |Available baseline,not final hierarchy |
| DQN / centralized / DP / DP+robust |No final experiment artifacts |MISSING |
| Multi-seed |Seed parameters and deterministic checks |PARTIAL:no completed multi-seed final table/CIs |
| Ablations |Branch flags,cadence/config choices |PARTIAL:no final predeclared factorial evaluation |
| Logging/checkpointing |CSV/JSON source hashes,policy initialization,LinUCB diagnostic checkpoints |PARTIAL:no complete DQN/optimizer/replay/RNG resumability |

Need matched demand/calibration/seed protocol, uncertainty intervals across independent runs, prediction-on/off and cadence/heterogeneity ablations after stable non-private operation. Historical test success is not evidence of real-world optimality or causal passenger elasticity.

## 30. Test audit

292 tests discovered across41 test files. **270 executed and passed;0 failed,0 errors,0 framework-skipped;22 deliberately not run.** Repeated broad run258 in30.259s; supplemental12 non-training routing/FedAvg tests passed. Commands used `PYTHONDONTWRITEBYTECODE=1` and `python -B`; Matplotlib caches/test temporary files were outside repository. No optimizer training tests, long simulations or source/model regeneration were run. Small model construction/serialization/inference tests wrote only temporary fixtures, not production models.

Not run: main-slot6,multi-slot6,validation24h5 (fixtures execute local training/longer orchestration); routing-learning3 and federated1 training tests; full10M saved-population scan1 (higher-cost older-elasticity verification). The current authoritative support was independently verified via a narrow3-column stream, not that legacy test. Supplemental tests cover non-training shape/mask/aggregation validation; they do not prove updated roadmap equations.

| P0 missing test contract | Required acceptance test |
|---|---|
| Geometry units/topology |CRS unit conversion and measured edge length; unique raster mapping; approved diagonal index/mask/distance tests |
| Acceptance |Hand-calculated currency/dimension/sign/reference cases; approved artifact scope; zero-domain/fallback validation |
| CNN feature/time |Training-only historical/scaler fit; forecast timestamp/30min target count; future-sentinel mutation; positive output/raster mask |
| F/H/μ/σ/ζ |Hand-calculated recurrence,rate units,zero-vs-missing,initialization,strict previous-slot updates |
| U1/U2/U3/C_rep |Gaussian/exponential values,monotonicity,limits,tie rules,feasible charging next hop;no teleport |
| Dispatch/reward |Minimum fare,passenger wait/cancellation,pickup energy/time;OD successful dispatch conservation;assigned-vs-completed ledger |
| Public policy/FL |Approved state ordering,private-field exclusion,labels for charging/reposition,output mask;equal-client runtime regression |
| DQN state |J_disp lag,incoming arrivals horizon,OD indexing,forecast issue-time and no future events |
| DQN algorithm |Known Bellman target,terminal mask,soft-update arithmetic,replay sampling/exploration determinism,gradient/target isolation |
| Episode / resume |Boundary forecast absence,done handling,no bootstrap at terminal,checkpoint+optimizer+RNG restoration,tiny end-to-end conservation |

## 31. Legacy and superseded classification

| Component | Disposition | Reason |
|---|---|---|
| Record-029 source/references/support |KEEP ACTIVE |Frozen historical sensitivity method; runtime bridge unresolved |
| Final analytical weather package |KEEP ACTIVE |Exhaustive two-scenario descriptive representation |
| Literal Clear1/Rain8 Record029 sampler/Record030 results |KEEP PROVENANCE (sampler baseline only) |Earlier limited population; not exhaustive analytical weather sampler |
| Old elasticity_v2/M10 ratios/scripts |ARCHIVE LATER |Opposite/older conventions and tests; no deletion before dependency migration |
| Weather clustering diagnostics |KEEP PROVENANCE |Retained in final weather folder; not current final classification |
| LinUCB |KEEP BASELINE |Useful comparator,not DQN |
| Daypart policy / interrupted Record030 experiment |KEEP BASELINE / KEEP PROVENANCE |Opt-in control;only control/A/B completed |
| Legacy notebooks |KEEP PROVENANCE |Origins of grid/CNN conventions;not latest authority |
| Old demand weights/predictions |KEEP BASELINE |Frozen30min model;updated CNN must use versioned artifacts |
| PositiveE and Eq31 acceptance |KEEP BASELINE |Explicitly distinct executable responses;not approved final Record029 bridge |
| Old audits/plans |KEEP PROVENANCE |Historical context;do not propagate outdated completion/source-gap claims |

No component was deleted, archived or modified during this audit.

## 32. Source-to-code traceability

| Requirement | Code | Status | Existing test / artifact | Gap |
|---|---|---|---|---|
| Roadmap4 reciprocal acceptance |`customer_sensitivity.maximum_price` |METHODOLOGY_BLOCKED |`test_customer_sensitivity`;Jan sensitivity metadata |ExtraP_base,dimension/sign/reference mismatch |
| Eq31 alternative |`customer.customer_acceptance_probability` |MATCH baseline |`test_pricing`;MARL Eq31 PDF |Not requested final reciprocal model |
| F_hat recurrence |`OperationalStatistics.fare_count` only |MISSING |`test_statistics`;nb9CSV |No smoothed successful rate |
| H_hat recurrence |`stations.charging_observations` only |MISSING |`test_charging_stations` |No expected-wait EWMA |
| U1 Gaussian survival |`routing.baseline.price_utility` |MISMATCH |`test_routing_baseline` |Linear score/different direction |
| U2 exponential waiting |`routing.baseline.wait_utility` |MISMATCH |Same |NoF_hat |
| U3 charging navigation |`stations.nearest_station`,`charging_utility` |MISMATCH |Energy/station tests |Different utility and teleport |
| Policy softmax |`learning.masked_softmax` |MATCH primitive / state mismatch |Routing-learning/grid-policy tests;NPZ |Public F/H schema/labels missing |
| Plain FedAvg |`aggregate_policy_updates`+main_slot override |MATCH operational averaging / partial participants |Non-training FedAvg tests;routing_rounds |State schema/charging clients |
| DQN five components |`pricing/state`,`request_context` alternatives |MISSING final |Request-context tests |J_disp/I/OD lag contract |
| DQN Bellman / soft target |None |MISSING |No test/artifact |Implement algorithm |
| CNN seven planes |`aggregation`,`tensors` |PARTIAL |CNN tensor tests;metadata |Historical fit and within-hour/target timestamp |
| CNN7→14→7→1ReLU |`model.build_model` |MISMATCH |CNN model tests;legacy.keras |Fourlayers/outputlinear |
| CNN30-minute adaptation |`tensors` target next snapshot;production+30min |DOCUMENTED_ADAPTATION; timing/units MATCH |Time alignment and empirical-arrival tests;time_test.npy |No10-minute layer needed; explicit issue-time provenance and rounding/missing-origin accounting remain |

## 33. Ranked blocker register

P0 means needed before the corresponding compliant non-private milestone, not that every item prevents a mock Bellman test. P1 means full baseline/evaluation readiness; P2 means later privacy/security scope.

| Category | P0 | P1 | P2 |
|---|---|---|---|
| A Methodology |Acceptance dimension/sign/source and downstream scope;identify μ/σ/ζ manuscript;reward successful-event/cost/timing;approve utility/public policy contract |Calibration vs predictive holdout;sample/model generalization claims |Threat model,privacy adjacency/sampling,attack goals |
| B Configuration |Physical grid units/topology;actions;forecast availability and integer-count accounting (30/2 cadence frozen);F/H coefficients;driver/EV travel/wait/terminal rules |Fleet scale/mix,station calibration,episode/seed schedule,comparison design |Privacy budgets,adversary rates,protocol threat settings |
| C Code |CNN architecture/train-only feature corrections (retain30min);F/H and utilities/charging;public policy schema;DQN state/core/replay/terminal integration;dispatch floor/wait |Evaluation logger,resume/ablation/CI harness |DP,secure aggregation,robust defenses/attacks |
| D Retraining |Updated CNN;new policy initialization/output schema (local learning follows) |Multi-seed final pricing training |Private/robust training variants |
| E Regeneration |CNN tensors/scalers/forecasts;grid-dependent artifacts if geometry changes;approved weather-scoped downstream sampler only after decision |Versioned evaluation maps/baselines/manifests |Attack/privacy outputs |
| F Documentation |Single signed interface/config decision record;correct unit declarations;source gap closure |Root completion labels and stale stage metadata scope |Threat assumptions and limitation statements |

## 34. Dependency-aware one-time implementation plan

This is a plan, not authorization to change files in this read-only task. Preserve frozen Record-029 epsilon/reference/support throughout.

| Task / milestone | Dependency | Modules/files to change later | Tests / retraining | Artifact and done criterion |
|---|---|---|---|---|
| A1 Freeze minimum contracts |Source-gap resolution and methodology decisions |New specification/config record;acceptance/state/reward owners |Hand calculations;no retraining |Approved units,actions,reward/terminal and state schema,or explicitly mock-only fixture scope |
| A2 Deterministic standalone DQN |A1 algorithm hyperparameters;can use synthetic environment while real contracts pending |New `src/pricing/dqn.py`,replay/transition module;new focused tests |Bellman/terminal/target/RNG/replay tests;no data-model retraining |Online/target/replay checkpoint produces identical fixture actions/targets after restore |
| A3 Deterministic integration fixture |A2;approved mock event/state interfaces |Opt-in simulation adapter;LinUCB unchanged |Tiny fixed requests/fleet,public state,reward conservation;no real-data training |**Milestone A:** one deterministic non-private DQN transition cycle withdone,no future data;clearly synthetic |
| B1 Freeze spatial/physical config |Geometry/topology decision;30/2 cadence already frozen |spatial/config,time contracts |Feet/metres and neighbourhood tests;CNN training deferred until fixed |Versioned grid/config manifest;no ambiguous “3000m” |
| B2 Updated CNN artifacts |B1 and training split/weather availability |aggregation,tensors,model,inference,build/train scripts |Retain30-minute targets;correct train-only fit/architecture;mask/time tests;**retraining for these changes only** |New model/scalers/grid-keyed forecasts,held-out metrics and baselines/maps |
| B3 Operational contracts |A1+B1,μ/σ manuscript |statistics,dispatch,fleet,routing/baseline,charging |Exact recurrences/utilities,passenger wait/driverfloor,station travel tests |Correct F/H,public events,feasible vehicle/charging transitions |
| B4 Routing/FL schema |B3+topology decision |learning,federated,grid_policy,production init |Shape/masks/privacy-schema/label/equal-client tests;new weights/local learning |Public-grid policy and charging/reposition labels versioned |
| B5 Real-state/acceptance/reward adapter |A1+B2+B3+B4 |pricing state/acceptance adapters,main_slot,production |LaggedJ_disp/I,issue_time,reward ledger,terminal boundary,resume |**Milestone B:** short non-private DQN episode,all invariants,baseline unchanged;save full manifest |
| C Full non-private baseline |B success |Runner,reporting,checkpoint/experiment configs |Multi-seed runs,matchedLinUCB/rule/centralized comparisons;DQN training |**Milestone C:** prespecified horizons,seeds,CIs,restorable checkpoints,calibrated metrics |
| D Privacy/security |C;threat and participation model |Local trainer/privacy accountant,secure protocol modules |Per-sample clipping/noise/accounting,dropout/mask tests;private variants train |**Milestone D:** non-private parity plus formal per-driver budgets and secure-aggregate guarantees |
| E Robustness/attacks |D or plain baseline for attack controls;protocol compatibility |Robust aggregators,attacker harness |Controlled poison/Sybil/misreport/inference/inversion tests |**Milestone E:** measured attacks and compatible defenses,not labels alone |
| F Final experiments/ablations |C–E stable |Evaluation configs/reporting |SeedCIs,privacy/predictor/cadence/heterogeneity/robustness ablations |**Milestone F:** reproducible final tables/plots,limits and thesis traceability |

Do not start privacy because the FL function exists. Do not regenerate spatial artifacts before deciding physical extent/topology. CNN retraining is not needed to unit-test Bellman arithmetic, but is needed before claiming a roadmap-compliant real-data episode.

## 35. Exact next five tasks

1. **Freeze the acceptance/reward/public-state decision record and close manuscript gaps.** WHY NOW: signed dimensionless e cannot be inserted into reciprocal currency equation; μ/σ/ζ and successful-dispatch timing are not certified. WHAT: obtain equation pages; approve units,scope,behaviour/fallback,success/reward/terminal semantics and public/private fields. FILES: future specification/config only, plus planned customer/state/reward interfaces. TESTS: hand-calculation acceptance cases and schema/event examples. DONE WHEN: each equation has source,units and signed decisions,or is explicitly blocked. MUST NOT CHANGE: Record-029 formula/support/data or silently transform e.
2. **Resolve the geometry/time/action configuration contract.** WHY NOW: feet/metres error and topology affect almost every dependent artifact; avoid duplicate retraining. WHAT: choose retained physical raster versus true3km regeneration; cardinal adaptation versus8neighbours;preserve30-minute forecasts/2-minute dynamics,declare forecast availability and integer-count accounting,actionset,fleet/EV/wait assumptions. FILES: future `config/config.yaml`,spatial/time/action manifests; no mass regeneration before sign-off. TESTS: CRSedge-length,raster bijection,neighbour mask,count conservation. DONE WHEN: explicit versioned settings and dependency list approved. MUST NOT CHANGE: historical baseline artifacts or force47×48.
3. **Implement a standalone deterministic DQN and tiny mock integration fixture.** WHY NOW: validates RL mathematics independently while artifact regeneration is pending. WHAT: online/target/replay,epsilon-greedy,Bellman/terminal/softupdate,RNGcheckpoint with declared mock state/reward. FILES: new pricing DQN/replay/tests,opt-in tiny adapter. TESTS: known numeric targets,terminal no-bootstrap,restore parity,no private epsilon in state. DONE WHEN: MilestoneA passes without production data/model changes. MUST NOT CHANGE: default LinUCB or claim calibrated passenger behaviour.
4. **Correct operational equation/state producers and routing/FL schema.** WHY NOW: DQN must consume correct statistics,arrivals and public routing response. WHAT: agreed μ/σ/ζ,F/H,U1/U2/U3/C_rep,driverfloor/wait,charging hops,labels,topology,expected arrivals and final OD-state builder. FILES: `simulation/statistics.py`,dispatch/fleet/charging,routing learning/federated,pricing state. TESTS: hand recurrences/utilities,movement/event conservation,lag/no-leakage and equal aggregation. DONE WHEN: all P0 interface tests pass on tiny fixtures. MUST NOT CHANGE: frozen descriptive sensitivity or substitute counts/rawwait for F/H.
5. **Build the updated CNN and complete the opt-in short real-data episode.** WHY NOW: after settings are fixed, retrain once and connect the already-tested components. WHAT: training-only seven planes,unchanged30min targets,7→14→7→1ReLU,versioned forecasts,approved acceptance adapter,ODrewards/terminal/checkpoints. FILES: demand builders/model,inference,production/main-slot/newrunner; separate new artifacts. TESTS: held-out metrics/baselines/maps,forecast issue-time/grid alignment,short episode no-future/reward/replay/restore checks. DONE WHEN: MilestoneB succeeds with complete config/source hashes and current baseline preserved. MUST NOT CHANGE: Record-029 values,fit privacy/attack methods prematurely,or label an unresolved acceptance substitution final.

## 36. Overall readiness

Coarse engineering judgments, not task-count arithmetic or estimates of research effort:

- **Data/methodology foundation: roughly70–85%.** Strong frozen descriptive analysis,traceable inputs and geometry artifacts; acceptance applicability,physical units and forecast-contract revisions remain significant.
- **Non-private hierarchical system: roughly35–50%.** Fleet/LinUCB/plainFL infrastructure is reusable, but DQN,required equations/charging/publicstate/CNN revision are unfinished.
- **Full thesis implementation including privacy/robustness: roughly20–35%.** Non-private gaps plus missing formal mechanisms,attacks and comparative evaluation dominate remaining work.

Passing270 existing tests measures baseline implementation consistency, not these percentages or compliance with new requirements.

## Validation and audit boundaries

Only this existing report is updated in the repository for the clarified request. Source/config/data/models/figures remain unchanged; no analysis regeneration,raw taxi-table scan,training,long simulation,refactor or deletion. Inspected small spatial artifacts and the small taxi-zone boundary shapefile; streamed three columns of the existing authoritative processed epsilon dataset only to verify requested counts. The prior naming cleanup and earlier version of this audit are already in the repository baseline. Unchanged source findings were reused after verifying the recorded aggregate SHA-256 of every src Python file; quick tests were rerun.

The initial audit baseline had pre-existing changes `notebooks/plan/.DS_Store` and untracked `notebooks/plan/ImplementationPlan/`; these belong to the supplied source environment and are not audit edits. Test discovery/execution used temporary scripts/logs outside the repository. The clarified-request revision rechecked the recorded source and14 authority/config/model/artifact fingerprints and reran quick tests; all matched. It updated this existing report only. The evidence appendix records test exclusions,source hashes and tracked-state validation so subsequent work can be incremental.

**FINAL_HIERARCHICAL_RL_IMPLEMENTATION_AUDIT_READY**

## Appendix A. Evidence inventory and reproducibility baseline
Git HEAD at audit: `0cca91368bda5f81a5eb6ad1692ed8b2748fbf96`. Existing tracked/untracked status outside the new report directory matches the audit-start snapshot exactly. No changes were staged.

### src (62 files; bytecode/OS metadata excluded)
```text
src/__init__.py
src/analysis/__init__.py
src/analysis/passenger_sensitivity_m10.py
src/charging/__init__.py
src/charging/energy.py
src/charging/stations.py
src/data/__init__.py
src/data/config.py
src/data/taxi.py
src/data/weather.py
src/demand/__init__.py
src/demand/aggregation.py
src/demand/contracts.py
src/demand/inference.py
src/demand/model.py
src/demand/tensors.py
src/dispatch/__init__.py
src/dispatch/contention.py
src/dispatch/dispatch.py
src/dispatch/generation.py
src/dispatch/request.py
src/elasticity_v2/population.py
src/elasticity_v2/preclustering.py
src/federated/__init__.py
src/fleet/__init__.py
src/fleet/fleet.py
src/fleet/state.py
src/fleet/supply.py
src/popularity/__init__.py
src/popularity/destination.py
src/pricing/__init__.py
src/pricing/customer.py
src/pricing/customer_sensitivity.py
src/pricing/historical_sensitivity.py
src/pricing/linucb.py
src/pricing/request_context.py
src/pricing/reward.py
src/pricing/scaler.py
src/pricing/state.py
src/pricing/supply.py
src/pricing/time_policy.py
src/reporting/__init__.py
src/reporting/customer_response.py
src/reporting/dispatch.py
src/reporting/pricing.py
src/routing/__init__.py
src/routing/baseline.py
src/routing/federated.py
src/routing/learning.py
src/routing/production.py
src/simulation/__init__.py
src/simulation/grid_policy.py
src/simulation/main_slot.py
src/simulation/multi_slot.py
src/simulation/pricing_dispatch.py
src/simulation/production.py
src/simulation/statistics.py
src/simulation/validation_24h.py
src/spatial/__init__.py
src/spatial/artifacts.py
src/spatial/grid.py
src/spatial/mapping.py
```

### tests (42 files; bytecode/OS metadata excluded)
```text
tests/.gitkeep
tests/test_artifacts.py
tests/test_charging_stations.py
tests/test_cnn_model.py
tests/test_cnn_tensors.py
tests/test_config.py
tests/test_customer_sensitivity.py
tests/test_demand_aggregation.py
tests/test_demand_artifacts.py
tests/test_destination_popularity.py
tests/test_dispatch.py
tests/test_driver_contention.py
tests/test_driver_waiting.py
tests/test_elasticity_v2_population.py
tests/test_elasticity_v2_preclustering.py
tests/test_empirical_arrivals.py
tests/test_energy.py
tests/test_fleet_state.py
tests/test_grid.py
tests/test_grid_policy.py
tests/test_historical_sensitivity.py
tests/test_m10_time_weather_reporting.py
tests/test_main_slot.py
tests/test_multi_slot.py
tests/test_passenger_sensitivity_m10.py
tests/test_passenger_trip.py
tests/test_pricing.py
tests/test_pricing_dispatch.py
tests/test_pricing_scaler_reference.py
tests/test_pricing_supply.py
tests/test_production_simulation.py
tests/test_reporting.py
tests/test_request_pricing_context.py
tests/test_routing_baseline.py
tests/test_routing_federated.py
tests/test_routing_learning.py
tests/test_routing_production.py
tests/test_spatial_mapping.py
tests/test_statistics.py
tests/test_time_pricing_policy.py
tests/test_validation_24h.py
tests/test_weather_contract.py
```

### config (5 files; bytecode/OS metadata excluded)
```text
config/.gitkeep
config/config.yaml
config/pricing_context_scaler.json
config/pricing_reward.json
config/record030_time_pricing_experiment.json
```

### scripts (38 files; bytecode/OS metadata excluded)
```text
scripts/.gitkeep
scripts/analyze_passenger_sensitivity_m10.py
scripts/analyze_phase7d.py
scripts/build_charging_stations.py
scripts/build_cnn_dataset.py
scripts/build_customer_sensitivity.py
scripts/build_customer_sensitivity_fallback.py
scripts/build_demand_master.py
scripts/build_destination_popularity.py
scripts/build_driver_profiles.py
scripts/build_elasticity_v2_preclustering.py
scripts/build_grid.py
scripts/build_nb9_fare_bootstrap.py
scripts/build_routing_initialization.py
scripts/build_weather.py
scripts/generate_phase7d_report.py
scripts/generate_validation_figures.py
scripts/plot_m10_time_weather.py
scripts/prepare_elasticity_v2_population.py
scripts/run_production_experiment.py
scripts/run_record030_time_pricing_experiment.py
scripts/test_charging_infrastructure.py
scripts/test_dispatch.py
scripts/test_driver_waiting.py
scripts/test_empirical_arrivals.py
scripts/test_energy.py
scripts/test_federated_routing.py
scripts/test_fleet_state.py
scripts/test_local_routing_learning.py
scripts/test_main_slot.py
scripts/test_multi_slot.py
scripts/test_passenger_trip.py
scripts/test_pricing.py
scripts/test_pricing_dispatch.py
scripts/test_routing_baseline.py
scripts/test_statistics.py
scripts/test_validation_24h.py
scripts/train_cnn.py
```

### models (12 files; bytecode/OS metadata excluded)
```text
models/.gitkeep
models/demand/.gitkeep
models/demand/cnn_history.pkl
models/demand/cnn_metrics.csv
models/demand/cnn_model.keras
models/demand/cnn_predictions.npy
models/demand/cnn_provenance.json
models/demand/normalization.pkl
models/pricing/.gitkeep
models/routing/.gitkeep
models/routing/nb12_nb13_common_initialization_seed42.npz
models/routing/nb12_nb13_common_initialization_seed42_metadata.json
```

### notebooks (29 files; bytecode/OS metadata excluded)
```text
notebooks/.gitkeep
notebooks/legacy/.gitkeep
notebooks/legacy/NB1_Spatial_Info_Build.ipynb
notebooks/legacy/NB2_GridToTripAssignment
notebooks/legacy/NB3_DemandAggregation.ipynb
notebooks/legacy/NB4_CNNDatasetGeneration.ipynb
notebooks/legacy/NB5_CNNDemandPrediction.ipynb
notebooks/legacy/Utility_WeatherDownloader.ipynb
notebooks/plan/Charging_Implementation_Step_by_Step.docx
notebooks/plan/Corrected_Final_Implementation_Process_NYC_RideHailing_PhD.docx
notebooks/plan/Corrected_Updated_Weather_Elasticity_Implementation_3_Classes.docx
notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf
notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx
notebooks/plan/Passenger_Price_Sensitivity_Implementation_Steps_Clean.pdf
notebooks/plan/PhD_Implementation_Clear_Picture_and_Execution_Plan.docx
notebooks/plan/Price_Distance_Sensitivity_Implementation_Guide.docx
notebooks/plan/Professor_Guidance_Elasticity_2026-10-02.pdf
notebooks/plan/papers/A_Reinforcement_Learning_and_Prediction-Based_Lookahead_Policy_for_Vehicle_Repositioning_in_Online_Ride-Hailing_Systems (1).pdf
notebooks/plan/papers/Joint_Optimization_of_Pricing_Dispatching_and_Repositioning_in_Ride-Hailing_With_Multiple_Models_Interplayed_Reinforcement_Learning.pdf
notebooks/plan/papers/MARL-Based_Pricing_Strategy_via_Mutual_Attention_for_MoD_Systems_with_Ridesharing_and_Repositioning.pdf
notebooks/plan/papers/Pricing_Based_Charging_Navigation_Scheme_for_Highway_Transportation_to_Enhance_Renewable_Generation_Integration.pdf
notebooks/plan/papers/Scheduling_of_Electric_Vehicles_Power_in_V2G_and_G2V_Modes_Using_an_Improved_ChargeDischarge_Opportunity-Based_Approach.pdf
notebooks/plan/price elasticity1.docx
notebooks/plan/price elasticity2.docx
notebooks/plan/supervisor/Explain Pricing Dispatch Results.pdf
notebooks/plan/supervisor/Final_Next_Implementation_Process.docx
notebooks/plan/supervisor/Implementation Process Document.pdf
notebooks/plan/supervisor/Record-019.pdf
notebooks/plan/supervisor/customer sensitivity.pdf
```

### docs (0 files; bytecode/OS metadata excluded)
Not present.

### results/validation (94 files; bytecode/OS metadata excluded)
```text
results/validation/2026-09-08_48slot_run/COMPLETE_IMPLEMENTATION_EXPLANATION.md
results/validation/2026-09-08_48slot_run/README.md
results/validation/2026-09-08_48slot_run/chart_manifest.json
results/validation/2026-09-08_48slot_run/charts/01_request_funnel.pdf
results/validation/2026-09-08_48slot_run/charts/01_request_funnel.png
results/validation/2026-09-08_48slot_run/charts/02_request_outcomes.pdf
results/validation/2026-09-08_48slot_run/charts/02_request_outcomes.png
results/validation/2026-09-08_48slot_run/charts/03_linucb_arm_distribution.pdf
results/validation/2026-09-08_48slot_run/charts/03_linucb_arm_distribution.png
results/validation/2026-09-08_48slot_run/charts/04_linucb_arm_evolution.pdf
results/validation/2026-09-08_48slot_run/charts/04_linucb_arm_evolution.png
results/validation/2026-09-08_48slot_run/charts/05_revenue_reward_over_time.pdf
results/validation/2026-09-08_48slot_run/charts/05_revenue_reward_over_time.png
results/validation/2026-09-08_48slot_run/charts/05b_cumulative_revenue.pdf
results/validation/2026-09-08_48slot_run/charts/05b_cumulative_revenue.png
results/validation/2026-09-08_48slot_run/charts/06_nb11_action_distribution.pdf
results/validation/2026-09-08_48slot_run/charts/06_nb11_action_distribution.png
results/validation/2026-09-08_48slot_run/charts/07_routing_p5_evolution.pdf
results/validation/2026-09-08_48slot_run/charts/07_routing_p5_evolution.png
results/validation/2026-09-08_48slot_run/charts/08_nb13_parameter_change.pdf
results/validation/2026-09-08_48slot_run/charts/08_nb13_parameter_change.png
results/validation/2026-09-08_48slot_run/charts/09_nb12_participation.pdf
results/validation/2026-09-08_48slot_run/charts/09_nb12_participation.png
results/validation/2026-09-08_48slot_run/charts/10_driver_wait_statistics.pdf
results/validation/2026-09-08_48slot_run/charts/10_driver_wait_statistics.png
results/validation/2026-09-08_48slot_run/charts/11_wait_history_coverage.pdf
results/validation/2026-09-08_48slot_run/charts/11_wait_history_coverage.png
results/validation/2026-09-08_48slot_run/charts/12_contention_service.pdf
results/validation/2026-09-08_48slot_run/charts/12_contention_service.png
results/validation/2026-09-08_48slot_run/charts/13_repositioning.pdf
results/validation/2026-09-08_48slot_run/charts/13_repositioning.png
results/validation/2026-09-08_48slot_run/charts/14_fleet_state_evolution.pdf
results/validation/2026-09-08_48slot_run/charts/14_fleet_state_evolution.png
results/validation/2026-09-08_48slot_run/charts/15_charging_activity.pdf
results/validation/2026-09-08_48slot_run/charts/15_charging_activity.png
results/validation/2026-09-08_48slot_run/charts/16_energy_health.pdf
results/validation/2026-09-08_48slot_run/charts/16_energy_health.png
results/validation/2026-09-08_48slot_run/charts/17_time_of_day_performance.pdf
results/validation/2026-09-08_48slot_run/charts/17_time_of_day_performance.png
results/validation/2026-09-08_48slot_run/summary.csv
results/validation/2026-09-08_48slot_run/summary.json
results/validation/2026-09-08_48slot_run/tables/contention_summary.csv
results/validation/2026-09-08_48slot_run/tables/core_summary.csv
results/validation/2026-09-08_48slot_run/tables/federated_learning_rounds.csv
results/validation/2026-09-08_48slot_run/tables/fleet_state_by_slot.csv
results/validation/2026-09-08_48slot_run/tables/linucb_arm_summary.csv
results/validation/2026-09-08_48slot_run/tables/per_period_summary.csv
results/validation/2026-09-08_48slot_run/tables/representative_fare_history.csv
results/validation/2026-09-08_48slot_run/tables/representative_routing_probabilities.csv
results/validation/2026-09-08_48slot_run/tables/routing_action_summary.csv
results/validation/2026-09-08_48slot_run/tables/routing_p5_by_slot.csv
results/validation/2026-09-08_48slot_run/tables/wait_summary.csv
results/validation/phase6a_request_8d_48slots_seed42/arm_summary.csv
results/validation/phase6a_request_8d_48slots_seed42/checkpoints.csv
results/validation/phase6a_request_8d_48slots_seed42/per_slot.csv
results/validation/phase6a_request_8d_48slots_seed42/summary.json
results/validation/phase6b_request_8d_scaled_reward_48slots_seed42/arm_summary.csv
results/validation/phase6b_request_8d_scaled_reward_48slots_seed42/checkpoints.csv
results/validation/phase6b_request_8d_scaled_reward_48slots_seed42/per_slot.csv
results/validation/phase6b_request_8d_scaled_reward_48slots_seed42/summary.json
results/validation/phase7b_driver_contention_8slots_seed42/contention_per_slot.csv
results/validation/phase7b_driver_contention_8slots_seed42/legacy_per_slot.csv
results/validation/phase7b_driver_contention_8slots_seed42/summary.json
results/validation/phase7c4_production_preflight_seed42/per_slot.csv
results/validation/phase7c4_production_preflight_seed42/reproducibility.json
results/validation/phase7c4_production_preflight_seed42/summary.json
results/validation/phase7c6_aligned_production_preflight_seed42/per_slot.csv
results/validation/phase7c6_aligned_production_preflight_seed42/reproducibility.json
results/validation/phase7c6_aligned_production_preflight_seed42/summary.json
results/validation/phase7d_48slot_final_integrated_seed42/analysis.json
results/validation/phase7d_48slot_final_integrated_seed42/fleet_states.csv
results/validation/phase7d_48slot_final_integrated_seed42/linucb_factors.csv
results/validation/phase7d_48slot_final_integrated_seed42/nb9_fare_representative.csv
results/validation/phase7d_48slot_final_integrated_seed42/nb9_wait.csv
results/validation/phase7d_48slot_final_integrated_seed42/per_period.csv
results/validation/phase7d_48slot_final_integrated_seed42/per_slot.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility.json
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/fleet_states.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/linucb_factors.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/nb9_fare_representative.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/nb9_wait.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/per_slot.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/reproducibility.json
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/routing_grid_representative.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/routing_rounds.csv
results/validation/phase7d_48slot_final_integrated_seed42/reproducibility_check_2slot/summary.json
results/validation/phase7d_48slot_final_integrated_seed42/routing_grid_representative.csv
results/validation/phase7d_48slot_final_integrated_seed42/routing_rounds.csv
results/validation/phase7d_48slot_final_integrated_seed42/summary.json
results/validation/validation_50v_4g_48slots_seed42/customer_response.csv
results/validation/validation_50v_4g_48slots_seed42/dispatch_summary.csv
results/validation/validation_50v_4g_48slots_seed42/figure_manifest.json
results/validation/validation_50v_4g_48slots_seed42/pricing_decisions.csv
results/validation/validation_50v_4g_48slots_seed42/summary.json
```

### Relevant analysis packages
```text
results/analysis/2026-09-27_passenger_sensitivity_m10
results/analysis/2026-10-02_elasticity_v2_denominator_sensitivity
results/analysis/2026-10-02_elasticity_v2_source_extreme_audit
results/analysis/2026-10-02_professor_extreme_observation_review
results/analysis/2026-10-03_elasticity_clean_reference_final
results/analysis/2026-10-04_lbase_diagnostic_final_weather
results/analysis/2026-10-06_passenger_sensitivity_dispersion_diagnostic_clear_rain
results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar
results/analysis/2026-10-13_record030_passenger_response_compatibility
results/analysis/2026-10-13_record030_price_sensitivity_results_section
results/analysis/2026-10-13_record030_time_pricing_experiment
results/analysis/2026-10-14_hierarchical_rl_implementation_audit
results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios
results/analysis/2026-10-18_final_hierarchical_rl_repo_audit
```

### Exact non-executed tests
These22 were excluded, not reported as framework skips. Training-bearing fixtures were excluded even when their runtime might be short.

```text
test_elasticity_v2_population.PopulationTests.test_saved_population
test_main_slot.MainSlotOrchestrationTests.test_all_zero_federation_is_no_update_and_initializes_empty_grid_policy
test_main_slot.MainSlotOrchestrationTests.test_complete_order_pricing_nb9_nb11_nb12_nb13_and_next_state
test_main_slot.MainSlotOrchestrationTests.test_nb11_controls_actual_movement_and_charging_vehicle_is_excluded
test_main_slot.MainSlotOrchestrationTests.test_nb12_labels_are_nb11_actions_and_fedavg_exports_only_models
test_main_slot.MainSlotOrchestrationTests.test_nb9_uses_served_offered_fares_and_nb10_advances_once_per_mini_slot
test_main_slot.MainSlotOrchestrationTests.test_next_global_probabilities_are_masked_grid_means_with_audit_sources
test_multi_slot.MultiSlotTemporalTests.test_fleet_nb9_learning_and_charging_state_persist
test_multi_slot.MultiSlotTemporalTests.test_four_slots_exact_time_and_no_premature_pricing
test_multi_slot.MultiSlotTemporalTests.test_grid_policy_initialization_then_mean_then_latest_carry_forward
test_multi_slot.MultiSlotTemporalTests.test_nb11_authority_federation_schedule_and_global_persistence
test_multi_slot.MultiSlotTemporalTests.test_passenger_energy_limitation_and_busy_state_can_cross_boundaries
test_multi_slot.MultiSlotTemporalTests.test_rng_is_one_stream_and_full_replay_is_deterministic
test_routing_federated.RoutingFederatedTests.test_nb12_local_divergence_unequal_fedavg_and_global_reload
test_routing_learning.RoutingLearningTests.test_common_initialization_then_different_labels_diverge
test_routing_learning.RoutingLearningTests.test_federated_ready_export_excludes_raw_observations
test_routing_learning.RoutingLearningTests.test_supervised_training_increases_chosen_probability_and_zero_data_skips
test_validation_24h.Validation24hTests.test_energy_bounds_charging_integrity_and_no_nonfinite_values
test_validation_24h.Validation24hTests.test_generated_24h_summary_has_48_finite_consecutive_rows
test_validation_24h.Validation24hTests.test_generic_n_slot_driver_timestamps_state_and_accounting
test_validation_24h.Validation24hTests.test_pricing_routing_policy_learning_and_federation_stability
test_validation_24h.Validation24hTests.test_short_replay_is_deterministic_without_future_outcome_input
```

### Source/artifact identity fingerprints
SHA-256 identities at audit; hashes establish this baseline, not a fresh revalidation of the upstream derivation. Future work should compare only changed contracts/dependants.

| Path | SHA-256 |
|---|---|
| `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx` | `696555164a30851990a532b4292b39f088e1bb6229b9fba5f9cdddf046fbe7d0` |
| `notebooks/plan/papers/Joint_Optimization_of_Pricing_Dispatching_and_Repositioning_in_Ride-Hailing_With_Multiple_Models_Interplayed_Reinforcement_Learning.pdf` | `86fbd314c261334c205f416b47eebeba6cc987a489d2fba78bc5e23db504b3b5` |
| `notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf` | `d8b4effc503ba5192f6ac5b8777d7182b761406c047cc3c7202df394f80bf31a` |
| `config/config.yaml` | `8703c6d4b54b209264da2d4af47664a825a3341b0014350072f3f96aa2970319` |
| `data/processed/grid_metadata.json` | `b73d459072ced7f5bd2d740adbc575c8d55c01811cd53c5e2fd02e0778fbdb02` |
| `data/processed/grid_lookup.parquet` | `fec538a1c4049fd439f94c1cc6c86df3673ef1d328b64dfe2b4ceda0edc75217` |
| `data/processed/neighbour_map.parquet` | `4ac1726158a7a79ccd1e726058ce78c478f5d1bbde0f2c7b3b46998298f41a52` |
| `data/processed/price_distance_sensitivity_record029/final_passenger_sensitivity_methodology.json` | `4de811b719fd022d7eccf06234a3211108f08c358adb3a2b9fbe1cbb0991666a` |
| `data/processed/price_distance_sensitivity_record029/authoritative_epsilon_methodology.json` | `0d83b9a63f4a9b7ee75bb95133db183f9deb34fd9ee73addb15de08dfa55ddd7` |
| `data/processed/price_distance_sensitivity_record029/frozen_epsilon_support.json` | `cbff08702b6b13aaf92093e79890f7cbb9e9e7e6753265793d67da9aca2e18ef` |
| `models/demand/cnn_provenance.json` | `65eb9a81771ea41f57eab6022e30d9e0131a57589ffbef0b5ba7a152f9422a7e` |
| `models/demand/cnn_model.keras` | `f4e093906f7c8d65a570dd8d8f174bc9aa2cf3888867e3434ad3a139ed529b78` |
| `models/routing/nb12_nb13_common_initialization_seed42.npz` | `d6b74cf700dd0a85890b878e992f689bb7c29715ea9c5974a53ec3cd187d9c75` |
| `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/final_weather_2scenario_mapping.csv` | `a8542d39e121e22ade798b6efeb5f339698f91c48d1b59fed68bdfa2b6c13bee` |

Aggregate source identity: SHA-256 of newline-separated sorted `relative_path SHA256` entries for all src Python files: `680de1a6e7590789aed681ca911bff725bab6867114bc0e89faece3a652ee8da`.

### Code anchors for high-impact findings
Line numbers refer to this baseline and may move with later edits.

| Finding | Code anchor |
|---|---|
| `def build_grid` | `src/spatial/grid.py:41` |
| `x_coords =` | `src/spatial/grid.py:56` |
| `def add_historical_demand` | `src/demand/aggregation.py:103` |
| `def add_temporal_features` | `src/demand/aggregation.py:91` |
| `def build_model` | `src/demand/model.py:115` |
| `def train_model` | `src/demand/model.py:129` |
| `def compute_normalization` | `src/demand/model.py:75` |
| `def maximum_price` | `src/pricing/customer_sensitivity.py:93` |
| `class OperationalStatistics` | `src/simulation/statistics.py:72` |
| `def price_utility` | `src/routing/baseline.py:179` |
| `def wait_utility` | `src/routing/baseline.py:191` |
| `def candidate_utility` | `src/routing/baseline.py:257` |
| `def present_vehicle` | `src/charging/stations.py:133` |
| `def aggregate_policy_updates` | `src/routing/federated.py:98` |
| `STATE_FEATURE_ORDER =` | `src/routing/learning.py:27` |
| `def train_for_slot` | `src/routing/learning.py:251` |
| `payload["sample_count"] = 1` | `src/simulation/main_slot.py:253` |
| `def _paths` | `src/simulation/production.py:206` |
| `def run_slot` | `src/simulation/production.py:421` |
| `next_demand = self._demand` | `src/simulation/production.py:427` |
| `REQUEST_PRICING_CONTEXT_FEATURE_ORDER` | `src/pricing/request_context.py:17` |
