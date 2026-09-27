# Ride-Hailing Platform Simulation

## 1. Project overview

This repository is a modular research implementation for studying NYC ride-hailing demand prediction, fleet operations, EV charging, vehicle repositioning, federated routing-policy aggregation, and contextual pricing/customer acceptance. It uses January 2026 NYC Yellow Taxi data and a shared spatial representation to keep demand, vehicle, and operational state contracts consistent.

The work has two distinct layers:

- **Demand prediction (offline):** prepare taxi, spatial, and weather data; construct a grid-time demand table; build CNN tensors; train and validate a demand predictor.
- **Operations and learning (online components):** represent a fleet, generate empirical OD requests, price requests, draw customer acceptance, dispatch accepted requests, track operating statistics, manage EV energy/charging, execute utility-based repositioning, and learn/federate routing policies.

Demand prediction estimates future grid demand. NB11 utility selects actual vehicle movement, while NB12/NB13 policy probabilities provide a learned signal to pricing rather than movement commands. The production assembler executes the complete request-level pricing, historical customer, contention dispatch, EV, routing, and federated-learning pipeline continuously over aligned held-out CNN targets. Phase 7D validated one 48-slot/24-hour trajectory with 5,000 vehicles; the authoritative 298-slot held-out experiment is the next proposed run.

The legacy NB1-NB5 notebooks remain reference material and are not modified. The modular implementation currently extends through NB13.

## 2. Current implementation status

| Component | Status | Current scope |
| --- | --- | --- |
| Spatial/data preparation (NB1-NB2) | COMPLETE | January taxi cleaning, zone/grid artifacts, deterministic legacy-compatible mapping |
| Weather preparation | COMPLETE | Legacy-compatible January Meteostat artifact |
| Demand master (NB3) | COMPLETE | Half-hour grid-level pickup-demand master table |
| CNN tensors (NB4) | COMPLETE | Seven-channel, one-step-ahead tensor dataset |
| CNN training/inference (NB5) | COMPLETE | Legacy CNN, persisted model, normalization, predictions, and metrics |
| Fleet baseline | COMPLETE | Vehicle state, seeded placement, supply aggregation |
| Request/empirical-trip generation | COMPLETE | Intact empirical trip-row sampling and empirical within-slot arrivals |
| Baseline dispatch | COMPLETE | FCFS same-grid/direct-neighbour dispatch with empirical duration and passenger energy |
| Operational statistics (NB9) | COMPLETE | Grid/slot fare, wait, EWMA, and charging context |
| EV energy (NB10A) | COMPLETE | SOC initialization, energy consumption, trigger, charge/release transitions |
| Charging infrastructure (NB10B) | COMPLETE | Popularity-based stations, power-limited charging, FCFS queue |
| Utility-based routing/repositioning (NB11) | CORRECTED / COMPLETE | Equal-weight component utilities, action mask, maximum-utility selection, EV transition |
| Local routing policy learning (NB12) | CORRECTED / COMPLETE | Per-vehicle supervised policy learning from NB11 utility-selected actions |
| Federated routing aggregation (NB13) | COMPLETE | Compatibility-validated, sample-count-weighted FedAvg of local policy networks |
| Pricing state + contextual LinUCB | COMPLETE / PRODUCTION | Request-level 8D context, seven factor arms, disjoint LinUCB, served-revenue feedback |
| Customer acceptance + pricing payoff | COMPLETE / PRODUCTION | Historical sensitivity, hierarchical fallback, positive truncated-Normal draw, `P_max` decision |
| Pricing/customer/dispatch integration | COMPLETE | One request-level decision, pre-dispatch historical acceptance, contention, served-revenue feedback |
| One-main-slot orchestration | COMPLETE | Pricing through FedAvg and next-slot pricing-input boundary; production federates every slot |
| Short multi-slot temporal orchestration | COMPLETE | Four consecutive 30-minute slots with persistent state and explicit federation schedule |
| Production assembler | COMPLETE | Authoritative loading, persistent state/RNG, aligned CNN targets, one NB13 round per slot |
| Integrated production validation | COMPLETE | Phase 7D: 48 slots, seed 42, 5,000 vehicles; `READY_FOR_PHASE_8A` |
| Final held-out experiment | NEXT | Proposed 298-slot run over the frozen held-out target window |

## 3. High-level architecture

```text
NYC Yellow Taxi records + Taxi Zones + Meteostat weather
                         |
                         v
              Spatial and data preparation (NB1-NB2)
                         |
                         v
                 Demand master table (NB3)
                         |
                         v
                   CNN tensors (NB4)
                         |
                         v
                CNN demand predictor (NB5)
                         |
                         v
                 Predicted grid demand
                         |
       +-----------------+------------------+
       |                                    |
       v                                    v
Fleet state <---- requests / empirical OD --> Dispatch
       |                                    |
       +-------------> operational statistics
                              |
                    +---------+---------+
                    |                   |
                    v                   v
                 EV energy        Charging system
                    \                   /
                     \                 /
                      v               v
                         Routing state
                              |
                              v
               NB11 utility-based repositioning
                              |
                              v
               NB12 local supervised policy network
                              |
                              v
                 Local weights and sample count only
                              |
                              v
            NB13 policy-network FedAvg
                              |
                              v
                    Common routing policy
                              |
                              v
          Contextual LinUCB pricing + acceptance
                              |
                              v
                 Integrated production simulation
```

NB11 and NB12 intentionally have different responsibilities:

- **NB11** constructs state, calculates price/wait/charging utilities per valid candidate, combines them with fixed equal weights, and selects the maximum-utility action before applying the EV transition. NB11 is not DQN or Q-learning.
- **NB12** learns a masked local policy `P(action | state)` from NB11's `(state, chosen_action)` observations. It does not select the actual routing action in this milestone.
- **NB13** validates explicitly supplied local policy updates and applies sample-count-weighted FedAvg to produce new common policy weights.

## 4. Repository layout

```text
config/                 Runtime configuration
data/raw/               Externally supplied taxi and taxi-zone inputs
data/interim/           Reserved intermediate data area
data/processed/         Versioned stage artifacts (grid, weather, demand, CNN, stations)
models/demand/          Persisted NB5 model and associated artifacts
models/routing/         Frozen NB12/NB13 common initialization and metadata
models/pricing/         Reserved for future pricing artifacts
outputs/figures/        NB5 figures
outputs/metrics/        Reserved metrics outputs
outputs/logs/           Reserved execution logs
results/validation/     Engineering/production validation and dated reporting packages
src/                    Importable implementation packages
scripts/                Stage build, validation, and deterministic demonstration scripts
tests/                  Unit tests using small synthetic/deterministic fixtures
notebooks/legacy/       Unmodified legacy notebooks, when supplied
notebooks/plan/         Implementation and charging planning documents/reference paper
```

Important source packages:

| Package | Responsibility |
| --- | --- |
| `src/data/` | YAML configuration, taxi loading/filtering, legacy-compatible weather handling |
| `src/spatial/` | Grid construction, zone/grid mapping, neighbours, persisted spatial artifacts |
| `src/demand/` | Demand aggregation/contracts, NB4 tensors, NB5 model, inference |
| `src/fleet/` | Vehicle state, fleet transitions, and grid supply |
| `src/dispatch/` | Request state, empirical OD generation, deterministic dispatch |
| `src/simulation/` | Grid/main-slot operational statistics and EWMA state |
| `src/charging/` | EV energy operations and charging station infrastructure |
| `src/routing/` | NB11 utility routing, NB12 local policy learning, and NB13 policy FedAvg |
| `src/pricing/` | Standalone pricing context, LinUCB, customer acceptance, and revenue payoff |

## 5. Data and external inputs

The configured study period is **January 2026**. Place these raw inputs at the configured relative paths before building the first stages:

| Input | Configured path | Notes |
| --- | --- | --- |
| NYC Yellow Taxi parquet | `data/raw/yellow_taxi/yellow_tripdata_2026-01.parquet` | January 2026 trip records |
| NYC Taxi Zone shapefile | `data/raw/taxi_zones/taxi_zones.shp` | Include companion `.shx`, `.dbf`, `.prj`, and other shapefile sidecars |
| Weather | fetched by `scripts/build_weather.py` | Meteostat network access is required only when fetching/rebuilding weather |

The persisted spatial metadata records 3,724,889 raw taxi records and 3,699,638 retained records after valid-zone filtering. The raw January file has `PULocationID` and `DOLocationID`, but not pickup/dropoff coordinates. Therefore the implementation deliberately preserves NB2's seeded within-zone `LocationID -> GridID` sampling rather than claiming point-level trip locations.

Spatial contract:

- CRS: **EPSG:2263**.
- Square grid cell size: **3,000 m**.
- Layout: **51 rows x 52 columns**.
- Valid cells: **1,213**, with deterministic GridIDs **0-1212** ordered north-to-south then west-to-east.
- Zone/Grid assignment: seeded candidate-grid sampling per taxi zone; pickup and dropoff assignments use the same deterministic RNG stream.
- Neighbours: side-adjacent north/east/south/west valid grid cells only; this is an engineering convention because NB1/NB2 did not define a neighbour method.

## 6. Stage-by-stage implementation

### 6.1 Spatial preparation (NB1-NB2)

| Item | Current contract |
| --- | --- |
| Purpose | Build canonical grid, map zone-based trips to GridIDs, and persist downstream spatial artifacts |
| Modules | `src/data/taxi.py`, `src/spatial/grid.py`, `src/spatial/mapping.py`, `src/spatial/artifacts.py` |
| Script | `python scripts/build_grid.py [--validate] [--force]` |
| Inputs | Raw Yellow Taxi parquet and Taxi Zone shapefile |
| Outputs | `cleaned_trips.parquet`, `grid_lookup.parquet`, `grid_mask.npy`, `zone_grid_mapping.parquet`, `zone_to_grids.pkl`, `neighbour_map.parquet`, `grid_metadata.json` |
| Validation | Spatial schemas, mask dimensions, canonical IDs, mappings, and neighbour links |

`cleaned_trips.parquet` contains cleaned taxi fields plus `PUGridID` and `DOGridID`. The random generator is seeded with `random_seed + month_number` (42 + 1 for January) to reproduce the legacy zone-to-candidate-grid allocation. This mapping is an approximation introduced by the coordinate limitation, not an observed trip coordinate assignment.

### 6.2 Weather preparation

| Item | Current contract |
| --- | --- |
| Purpose | Reproduce the legacy hourly weather utility input for NB3 |
| Modules | `src/data/weather.py` |
| Script | `python scripts/build_weather.py [--validate] [--force]` |
| Provider | Meteostat **1.7.6** using `Hourly(Point(...), start, end).fetch()` |
| Location | 40.7128, -74.0060, altitude 10 m |
| Period | 2026-01-01 00:00:00 through 2026-01-31 23:59:59 |
| Outputs | `data/processed/weather/nyc_weather_processed_2026_01.parquet`, `weather_metadata_2026_01.json` |

The processed table has 744 hourly rows and exactly `Datetime`, `Temperature`, `WindSpeed`, and `WeatherCode`. It retains Meteostat `temp`, `wspd`, and `coco`, renames them, sorts timestamps, forward-fills missing values, and backward-fills any remaining leading values. It adds no interpolation, normalization, lags, or derived weather variables.

Both taxi and weather timestamps are intentionally timezone-naive to reproduce the legacy behaviour. Their temporal alignment remains a research assumption requiring an explicit future decision.

### 6.3 NB3 demand master

| Item | Current contract |
| --- | --- |
| Purpose | Create complete half-hourly grid-level pickup-demand records with weather and calendar features |
| Modules | `src/demand/aggregation.py`, `src/demand/contracts.py` |
| Script | `python scripts/build_demand_master.py [--validate] [--force]` |
| Inputs | Cleaned trips, canonical grid artifacts, processed weather |
| Outputs | `demand_master_2026_01.parquet`, `demand_master_2026_01_metadata.json` |

The authoritative NB3 table has 1,488 half-hour slots x 1,213 GridIDs = **1,804,944 rows** and these 14 columns:

```text
TimeSlot, GridID, Demand, Row, Column, Temperature, WindSpeed, WeatherCode,
DayOfWeek, Hour, Minute, Period, TimeIndex, HistoricalDemand
```

Demand is the pickup count by `(TimeSlot, PUGridID)`; dropoff GridID is not used for the target. The January-filtered pickup total is **3,699,633**. This is five fewer than the cleaned-trip total because five trips fall outside the January pickup-time boundary. `HistoricalDemand` is a strictly earlier expanding mean by `GridID`, `DayOfWeek`, and `Period`; it does not use current or future demand. NB3 applies no normalization.

### 6.4 NB4 CNN dataset

| Item | Current contract |
| --- | --- |
| Purpose | Convert the frozen NB3 table into legacy-compatible spatial tensors |
| Module | `src/demand/tensors.py` |
| Script | `python scripts/build_cnn_dataset.py [--validate] [--force]` |
| Input | `data/processed/demand_master_2026_01.parquet` plus canonical grid artifacts |
| Output directory | `data/processed/cnn/` |

Feature-channel order is fixed:

```text
0 HistoricalDemand   1 Temperature   2 WindSpeed   3 WeatherCode
4 DayOfWeek          5 Hour          6 Period
```

For each ordered time `t`, the feature map is at `t` and the raw pickup-demand target is at `t+1`. The full unsplit shapes are `X = (1487, 7, 51, 52)` and `y = (1487, 1, 51, 52)`, stored as `float32`. Invalid grid positions are zero padded. The split is chronological and unshuffled: 1,189 training samples and 298 test samples.

Persisted artifacts are `X_train.npy`, `y_train.npy`, `X_test.npy`, `y_test.npy`, `time_train.npy`, `time_test.npy`, and `metadata.pkl`.

### 6.5 NB5 CNN demand model

| Item | Current contract |
| --- | --- |
| Purpose | Train/validate the legacy CNN demand baseline and expose inference helpers |
| Modules | `src/demand/model.py`, `src/demand/inference.py` |
| Script | `python scripts/train_cnn.py [--validate] [--force]` |
| Input | Persisted NB4 dataset |
| Model artifacts | `models/demand/` |
| Figures | `outputs/figures/` |

The network is `Conv2D(32, 3x3, ReLU) -> Conv2D(64, 3x3, ReLU) -> Conv2D(32, 3x3, ReLU) -> Conv2D(1, 1x1, linear)`, all with same padding. It has 39,041 parameters. Channel-wise normalization is fitted on `X_train` only; targets are not normalized. Training requests up to 50 epochs, batch size 32, shuffled 20% validation split, and early stopping on validation loss (patience 5, restore best weights).

Persisted artifacts are `normalization.pkl`, `cnn_model.keras`, `cnn_metrics.csv`, `cnn_predictions.npy`, `cnn_history.pkl`, and `cnn_provenance.json`. The current saved metrics are RMSE 2.5915691905, MAE 0.6337751746, MAPE 83.4894835949%, and R² 0.8985528946. The legacy baseline intentionally includes padded positions in normalization, loss, and metrics.

### 6.6 Fleet baseline

| Item | Current contract |
| --- | --- |
| Purpose | Represent seed-reproducible vehicle and grid supply state |
| Modules | `src/fleet/state.py`, `src/fleet/fleet.py`, `src/fleet/supply.py` |
| Demonstration | `python scripts/test_fleet_state.py` |

The configured fleet contains 5,000 vehicles, initially sampled uniformly over valid GridIDs. This is a provisional engineering baseline. Each `VehicleState` carries `vehicle_id`, `current_grid`, `trip_status`, `destination`, `remaining_travel_time`, `current_action`, and `energy_level`. The implemented statuses are `IDLE`, `BUSY`, and `CHARGING`. A busy vehicle has a valid destination and positive remaining duration; completing travel returns it to `IDLE` at its destination.

### 6.7 Requests, OD generation, and dispatch

| Item | Current contract |
| --- | --- |
| Modules | `src/dispatch/request.py`, `src/dispatch/generation.py`, `src/dispatch/dispatch.py` |
| Demonstration | `python scripts/test_dispatch.py` |
| Source | Frozen January trip rows containing OD, timestamps, distance, and fare |

The frozen processed table contains 3,699,638 source trips. Runtime empirical sampling preserves one source row's `PUGridID`, `DOGridID`, pickup/drop-off timestamps, duration, distance, and base fare together rather than independently resampling its fields. The source NB2 policy did not filter duration or fare; runtime validation therefore excludes non-positive duration, negative/non-finite distance, and negative/non-finite fare candidates without clipping or rebuilding the parquet. In the current artifact, 44,612 rows have non-positive duration, 38,793 have negative fare, and distance has no negative or non-finite rows; accounting for overlap, 83,405 rows are excluded from runtime sampling.

One request is generated per integer grid-demand unit. The empirical pickup timestamp's absolute historical date and time are not replayed. Instead, its offset from the start of its original 30-minute bucket determines the corresponding simulated two-minute mini-slot: `floor(within_slot_offset_seconds / 120)`. For example, `08:17:43` is 17 minutes 43 seconds into the `08:00` bucket, maps to mini-slot 8, and arrives at minute 16 of whichever simulated main slot is active. Requests are then processed FCFS by `(request_time, request_id)`. The mini-slot controls simulated arrival discretization only; it is not passenger-trip duration.

Empirical-row selection remains seeded. Arrival placement consumes no random draw, and customer acceptance retains its separate explicit RNG stream.

Production uses `driver_contention`: accepted requests are announced to eligible `IDLE` drivers in the origin and direct canonical neighbours, excluding charging/threshold, insufficient-energy, and in-transit vehicles. Its request utility reuses NB11's equal-weight price/wait/charging structure. A driver contends when request utility is at least its best valid outside-option utility. The platform ranks contenders by shortest pickup distance, then descending request utility with utility-tie handling, and finally vehicle ID; assignment is immediate. Requests remain FCFS by `(request_time, request_id)`, and zero contenders means unserved. The earlier lowest-ID origin/neighbor policy remains legacy-only. Served empirical requests use their paired pickup/dropoff duration, and completion moves the vehicle to the paired destination. The configured default duration remains only a compatibility fallback for synthetic/manual requests lacking empirical fields.

**Waiting-time semantics:** NB9/NB11 waiting means driver/vehicle idle time in a grid before receiving a dispatch, not passenger waiting time. An available IDLE vehicle begins an episode at zero in its current grid and gains two minutes after each completed mini-slot that it remains IDLE. Dispatch closes the episode and records its completed duration against the vehicle's waiting grid, including when a neighboring vehicle serves the request. Main-slot boundaries and NB11 STAY do not reset it. BUSY trip time, charging time, and reposition travel are not idle waiting. Passenger-trip and charging completion start a new zero-minute episode at the available grid. A MOVE abandons the origin episode without fabricating a completed observation; the vehicle remains unavailable during its 12-minute reposition, and its destination idle clock begins only on arrival.

NYC TLC `trip_distance` is retained as `trip_distance_miles` for source audit. Kilometres are the simulation's canonical operational distance unit, converted exactly once as `trip_distance_km = trip_distance_miles * 1.609344`. At successful assignment, before the vehicle transitions from `IDLE` to `BUSY`, passenger energy is deducted exactly once with the existing consumption rate: `trip_distance_km * 0.15 kWh/km`. The request records before, consumed, and after energy. Mini-slot advancement does not deduct it again. A completed low-energy vehicle enters the existing NB10 charging workflow; BUSY vehicles cannot charge or reposition.

### 6.8 NB9 operational statistics

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/statistics.py` |
| Demonstration | `python scripts/test_statistics.py` |

Fare state begins from a pre-cutoff `PUGridID` historical bootstrap, using grid-level population mean/SD and a global historical fallback where required. For every grid/main slot, NB9 then records served fares and completed driver-idle dispatch waits, with separate counts, means, and population standard deviations (`ddof=0`), plus `ewma_fare`, `ewma_std_fare`, `ewma_wait`, and `ewma_std_wait`. Current observations update the state with `alpha = 0.30`; no observation carries it forward. A vehicle that remains idle has not completed an episode and creates no fake observation. Candidate grids with no current or EWMA wait history receive `U_wait = 0.5` only at NB11 utility evaluation. Charging availability and queue-wait context are carried where supplied.

```text
EWMA_next = (1 - alpha) * EWMA_previous + alpha * current_observation
```

Alpha, initialization, population SD, and no-observation behaviour are provisional engineering decisions.

### 6.9 NB10A EV energy

| Item | Current contract |
| --- | --- |
| Module | `src/charging/energy.py` |
| Demonstration | `python scripts/test_energy.py` |

The code adopts selected Table I values from Ding et al.: 75 kWh battery capacity, 60 kWh reference initial energy, 7.5 kWh reference minimum, 0.15 kWh/km consumption, and 30 kW charging power. The operational fleet initialization is instead a seeded truncated-normal SOC distribution: mean 0.50, SD 0.05, bounds [0.50, 0.70]. The charging trigger is SOC <= 0.20 (energy <= 15 kWh), so it must not be confused with the 7.5 kWh literature reference. Charging efficiency is 0.90; release occurs at 75 kWh (full charge), which is provisional.

### 6.10 NB10B charging infrastructure

| Item | Current contract |
| --- | --- |
| Module | `src/charging/stations.py` |
| Script | `python scripts/build_charging_stations.py [--validate] [--force]` |
| Demonstration | `python scripts/test_charging_infrastructure.py` |
| Artifact | `data/processed/charging_stations_2026_01.parquet` |

Fifteen station grids are selected by descending pickup-plus-dropoff popularity (with lower GridID resolving a tie). A station has a 3,000 kW power limit and each active EV reserves 30 kW. It uses a power-only representation rather than a physical charger count. Nearest-station selection uses projected grid-centroid distance, charging queues are FCFS by arrival order with seeded random priority for simultaneous arrivals, and queued wait increments by mini-slot duration. Charging gain is `power * efficiency * hours` and is capped at battery capacity.

### 6.11 NB11 utility-based routing/repositioning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/baseline.py` |
| Demonstration | `python scripts/test_routing_baseline.py` |

Only eligible `IDLE` vehicles not requiring charging may reposition. The fixed action order is `[STAY, NORTH, EAST, SOUTH, WEST]`; absent boundary neighbours are invalid and masked. For each valid candidate, NB11 calculates normalized price, decreasing waiting-time, and charging utilities, then uses `U_total = (U_price + U_wait + U_charge) / 3`. The actual decision is `state -> component utilities -> equal-weight total utility -> maximum valid utility -> STAY or MOVE`, with fixed action order breaking ties. Explicit price/wait preferences and an explicitly normalized degradation penalty are required; production values are not fabricated. Production NB11 uses the normalized DOD-related battery degradation component derived from Chauhan & Jain, referenced to charging from the frozen 20% SOC threshold to 100%; its separate temperature-dependent component is not modeled. The utility vector is audit data, not Q-values or probabilities. NB11 is not DQN or Q-learning.

Production uses 5,000 seed-42 persistent driver profiles. Price preference is generated from the pre-cutoff fare distribution; preferred idle-wait duration is sampled from `Uniform(0,30 minutes)`. Both are fixed per vehicle. These are synthetic project assumptions, not measured individual NYC-driver traits, passenger waiting, or a cap on actual idle time. When a candidate grid has no causal wait history, NB11 assigns only that candidate's normalized wait component the neutral value `0.5`; this creates no NB9 observation and is replaced when current or EWMA wait statistics exist.

The baseline uses 15 km/h, a 3 km repositioning threshold, and <=30-minute feasibility. Thus a non-stay movement takes 12 minutes, consumes 0.45 kWh, remains unavailable to dispatch during movement, and begins destination idle waiting only after arrival. NB11 has no reward or learning logic.

The authoritative production assembler is `src/simulation/production.py`, invoked by `scripts/run_production_experiment.py`. It loads and hashes production-authoritative artifacts, initializes the historical fare prior once with empty causal wait history, uses uniform-valid routing probabilities only for the first slot, and then preserves fleet, persistent RNG streams, LinUCB, NB9, NB11 operational state, NB12/NB13, charging, repositioning, and learned routing probabilities across boundaries. Missing or incompatible authoritative inputs fail fast; no validation-fixture fallback exists. It writes compact slot, learning, wait, fleet, source-manifest, and reproducibility artifacts.

The frozen CNN is one-step-ahead: each saved prediction produced from `X_test[i]` is keyed in production by the target timestamp `time_test[i] + 30 minutes`. The 298 held-out targets therefore cover 2026-01-25 19:00 inclusive through 2026-02-01 00:00 exclusive; the stored `time_test` array retains its original X/input timestamp meaning.

### 6.12 NB12 local supervised routing-policy learning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/learning.py` |
| Demonstration | `python scripts/test_local_routing_learning.py` |

Each participating vehicle has a local supervised learner trained from the actual `(state, chosen_action)` observations produced by NB11. The fixed deterministic `float32` state vector has **87** elements:

```text
vehicle.current_grid, vehicle.energy_level,

for each action in [STAY, NORTH, EAST, SOUTH, WEST]:
  valid, grid_id, predicted_demand,
  supply_total, supply_idle, supply_busy, supply_charging,
  mean_fare, std_fare, ewma_fare, ewma_std_fare,
  mean_wait, std_wait, ewma_wait, ewma_std_wait,
  charging_available, charging_wait
```

An invalid candidate has an all-zero block, including `valid=0`; `valid` remains a separate action mask. A missing `charging_available` within an otherwise valid candidate is encoded as -1. The common architecture is:

```text
87 -> Dense(64, ReLU) -> Dense(32, ReLU) -> Dense(5, linear)
```

The shared architecture is:

```text
87 -> Dense(64, ReLU) -> Dense(32, ReLU) -> 5 action logits
```

Invalid logits are excluded before softmax, so invalid actions have probability zero and valid probabilities sum to one. The supervised target is NB11's chosen action, not its utility vector, and training minimizes sparse categorical cross-entropy/negative log likelihood. Local observations contain state, chosen action, and action mask; an optional utility vector and slot ID are audit-only. Training runs at most once at the end of each 30-minute main slot, and zero observations produce no update.

Each vehicle retains a bounded local observation buffer. Federation-ready export contains only copied policy weights, vehicle ID, sample count, state dimension, action order, and architecture version; raw local observations are never exported.

### 6.13 NB13 federated routing-policy aggregation

| Item | Current contract |
| --- | --- |
| Module | `src/routing/federated.py` |
| Demonstration | `python scripts/test_federated_routing.py` |

One synchronous federated round consumes corrected-NB12 export payloads, validates state dimension, action order, architecture version, tensor count/shapes, finite weights, and non-negative integer sample counts, then computes each global tensor as `sum(n_i * theta_i) / sum(n_i)`. Zero-sample clients are validated but excluded. If every submitted client has zero samples, the round returns an explicit no-update result with no fabricated weights.

The common and local policies share the same `87 -> 64 -> 32 -> 5 logits` architecture, so aggregated weights load directly into fresh NB12 learners. Production performs one round after each main slot using only clients with new observations, applies sample-count-weighted FedAvg, and redistributes the global model. The interface aggregates weights only; raw states, chosen actions, masks, utilities, trajectories, and rewards are neither required nor transmitted. This baseline does not claim differential privacy, secure aggregation, client-failure simulation, or production communication behavior.

### 6.14 Contextual pricing and historical customer acceptance

| Item | Current contract |
| --- | --- |
| Modules | `src/pricing/state.py`, `linucb.py`, `customer.py`, `reward.py` |
| Demonstration | `python scripts/test_pricing.py` |

Production pricing uses one request-level decision from a disjoint-arm contextual LinUCB learner with `alpha = 1.0`. The fixed 8D feature order is `[scaled predicted demand, scaled idle_plus_incoming supply, relevant OD routing probability, lagged destination popularity, scaled trip distance in kilometres, scaled historical P_base(W,T), Period/47, categorical weather severity]`. The fixed arms are `[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]`. Each arm maintains `A = I` and `b = 0`, is scored with `theta^T x + alpha * sqrt(x^T A^-1 x)`, and only the selected arm receives the request's finalized feedback. A deterministic global cold start assigns each arm until all have an actual reward observation; later numeric score ties use the seeded RNG. There is no epsilon-greedy exploration. The earlier grid-level eight-feature interface remains only as a clearly separated legacy compatibility mode.

**Pricing popularity semantics:** popularity is destination attractiveness from empirical drop-off activity, not pickup demand, predicted demand, supply, combined pickup/drop-off activity, or charging-station popularity. Trips are attributed by `DOGridID` and the 30-minute slot containing `tpep_dropoff_datetime`. For grid `g` and slot `t`, the feature uses a strictly lagged simple mean of observed drop-off counts in slots `t-6` through `t-1`—a three-hour window—with all available prior slots used during warm-up. Observed zero-drop-off grid-slots remain zeros; unavailable pre-period history remains unavailable rather than being fabricated.

Fixed global `Q20/Q40/Q60/Q80` thresholds are fitted only on the chronological reference/training period and then applied unchanged to test/runtime data. Inclusive upper boundaries produce `Very Low`, `Low`, `Medium`, `High`, and `Very High`, encoded respectively as `0`, `0.25`, `0.5`, `0.75`, and `1`. Duplicate thresholds are retained and the same deterministic inequalities still apply. The label remains in the popularity artifact for audit while the eighth LinUCB feature receives only its scalar encoding, preserving the eight-dimensional context.

#### Pricing context scaling

Only demand and supply are transformed. Raw frozen-CNN demand is clipped at zero, transformed as `log1p(max(0, demand)) / log1p(45.085255432128896)`, then clipped to `[0,1]`. The denominator is the P99 of non-negative frozen-CNN predictions produced by inference on the existing chronological training/reference tensors (2026-01-01 00:00 through 2026-01-25 18:00); held-out predictions were not used. Negative raw demand remains available in diagnostics alongside its non-negative and scaled values.

Supply retains the existing `supply_total` semantics and is transformed as `log1p(supply_total) / log1p(9)`, then clipped to `[0,1]`. The reference value `9` is the P99 reproduced from the configured seed-42 uniform initialization of 5,000 vehicles over 1,213 canonical grids. This initialization distribution does not capture later endogenous vehicle concentration caused by dispatch, repositioning, or charging. Values above the fixed reference are therefore clipped to one and clipping counts/rates are recorded; the scaler is never dynamically refitted.

Routing probabilities and the five-level popularity value are unchanged. The deterministic parameters, artifact hashes, fitting provenance, transforms, clipping policy, and methodology version are persisted in `config/pricing_context_scaler.json`. LinUCB `alpha = 1.0` remains provisional and has not been optimized for the scaled context; scaling behaviour must stabilize before alpha sensitivity analysis.

The January artifact uses the frozen cleaned-trip destination and drop-off timestamp fields. No pre-January drop-off observation exists locally, so all January 1 00:00 grid moving averages are unavailable; January 1 00:30 uses only the observed 00:00 counts, and the history expands until six slots are available. This is an explicit initialization limitation, not future filling. The static charging-station field named `popularity` remains the separate whole-month `pickup_count + dropoff_count` ranking and is never used as the pricing feature.

#### Offline historical customer sensitivity — Phase 1

**M10 methodology update (2026-09-27, professor review only):** The new
[`Final_Module_Wise_Algorithm_Input_Output_Document.pdf`](notebooks/plan/Final_Module_Wise_Algorithm_Input_Output_Document.pdf)
specifies condition-mean bases and `epsilon = ((L-L_base)/L_base)/(P-P_base)`,
retaining positive distance/price deviations and finite positive epsilon.
This has been implemented in the isolated `src/analysis/passenger_sensitivity_m10.py`
and analyzed by `scripts/analyze_passenger_sensitivity_m10.py` for both half-hour
and hourly conditions. The [professor-review package](results/analysis/2026-09-27_passenger_sensitivity_m10/README.md)
documents the empirical results. Time grouping, source-cleaning policy, outlier
treatment, any minimum price-deviation threshold, runtime sampling, and sparse-condition
fallback remain under review; the new runtime model is **not frozen or production-ready**.
The prior sensitivity implementation/artifacts described below remain unchanged
and are legacy relative to this new document. Production still uses that prior
behavior until a separately approved integration; no DQN replacement or M12
production change is included in this analysis.

`src/pricing/historical_sensitivity.py` and `scripts/build_customer_sensitivity.py` build the pre-cutoff sensitivity inputs later consumed by production. Training trips before the exclusive `2026-01-25 18:30` boundary are pooled by `(WeatherCode, Period)`. Source-valid rows require positive finite `fare_amount` and positive finite TLC `trip_distance` no greater than 100 miles. Within each group, `P_base` and `D_base` are the respective means. An observation enters the ratio only when `abs(trip_distance - D_base) >= 0.01` mile, matching source resolution; retained observations use `epsilon = abs(((P-P_base)/P_base) / ((D-D_base)/D_base))`. The group and hierarchical-fallback tables retain population/sample SD and diagnostic quantiles. These build-stage rules are not epsilon clipping or winsorization; runtime positive-truncated sampling and `P_max` evaluation occur separately.

Production resolves sensitivity hierarchically for `(WeatherCode, Period)` using `exact -> Period -> Weather -> Global`, samples epsilon from the stored mean/population SD with a positive lower-truncated Normal draw, and computes `P_dispatch = P_base * alpha` and `P_max = P_base + (((D-D_base)/D_base) * P_base / epsilon_customer)`. The request is accepted exactly when `P_dispatch <= P_max`. Resolution and sampling occur once per request and retain the complete sensitivity/price audit. The ordinary Eq.31 response remains a legacy comparison mode, not the production configuration.

Phase 4A adds a reusable unscaled pricing-supply feature: `Supply(g,t) = currently IDLE vehicles in g + BUSY vehicles with a known passenger destination g and expected completion in the upcoming 30-minute slot`. The incoming window follows existing mini-slot completion semantics, `(slot_start, slot_end]`; charging and charging-queue vehicles are excluded. Phase 4B exposes this value through the `idle_plus_incoming` supply selector and places it in the unchanged second position of the eight-feature LinUCB context. The existing log1p/P99 transform remains unchanged. Recalibration preserves the original deterministic initialization reference convention; because all 5,000 initialized vehicles are IDLE, the corrected and legacy P99 references are both 9 across 1,213 grid observations. Remaining context features are unchanged.

The offered fare is the empirical base fare multiplied by the selected factor. Production feedback is finalized after dispatch: a served request contributes its recorded dispatch fare, while rejected and accepted-but-unserved requests contribute zero. The learner receives `raw_served_revenue / (BASE_PRICE_REF_P99 * 1.15)` using the frozen training-reference scale without clipping; raw served revenue remains the economic diagnostic. Every priced request receives exactly one update and no pending reservation remains after a slot.

LinUCB state is copy-exportable/importable in memory. Scaling is applied once at the methodology-derived pricing-context boundary; the LinUCB equations and eight-dimensional state contract are unchanged.

### 6.15 One-slot pricing, acceptance, and dispatch

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/pricing_dispatch.py` |
| Demonstration | `python scripts/test_pricing_dispatch.py` |

In production, each generated request receives its own 8D context and one pricing selection when it arrives within the 30-minute slot. It retains the empirical base fare and records factor, offered fare, sensitivity resolution, acceptance decision, dispatch outcome, and finalized reward. Processing order is `request context -> pricing -> historical-sensitivity acceptance -> contention dispatch -> served-revenue feedback`; rejected requests never enter dispatch.

Raw served revenue includes only accepted requests successfully assigned by dispatch. Accepted-but-unserved and rejected requests yield zero learning reward. The production runner validates one selection and one finalized update per generated request and fails if any reservation remains pending.

### 6.16 One-main-slot orchestration and grid policy aggregation

| Item | Current contract |
| --- | --- |
| Modules | `src/simulation/main_slot.py`, `grid_policy.py` |
| Demonstration | `python scripts/test_main_slot.py` |

One main slot executes pricing/customer acceptance/contention dispatch across 15 mini-slots; NB10 charging advancement and NB9 end-slot statistics; NB11 maximum-utility routing and 12-minute movement; NB12 local supervised observation/training; NB13 FedAvg and redistribution; global-policy inference; and next-slot pricing-input construction. Production supplies aligned frozen-CNN demand and lagged popularity, and performs one federated round per main slot.

The grid routing probability supplied to pricing uses an explicit **project baseline aggregation rule**, not a professor- or paper-prescribed formula. The global NB12/NB13 policy first produces an individually masked `[STAY, NORTH, EAST, SOUTH, WEST]` probability vector for every eligible idle vehicle from its real 87-D routing state. These probability vectors are averaged arithmetically within each grid. One vehicle uses its vector unchanged. A grid with zero eligible vehicles carries its previous grid vector; first use without history requires explicit initialization. This aggregation is a learned policy tendency only and may be revisited in sensitivity analysis. **NB11 maximum utility remains the sole source of actual repositioning actions.**

### 6.17 Short temporal simulation

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/multi_slot.py` |
| Demonstration | `python scripts/test_multi_slot.py` |

The controlled temporal driver invokes the completed one-slot orchestrator exactly four times, advancing timestamps by 30 minutes. It reuses the same fleet and charging infrastructure, LinUCB learner, acceptance RNG stream, NB9 EWMA engine, local NB12 learners, and global policy learner. The latest grid probability becomes the next zero-vehicle carry-forward value. Federation slots are an explicit caller-supplied set rather than a claimed final cadence. Each slot receives only its explicitly supplied boundary forecast, popularity, requests, and utility inputs; no later realized outcome is inspected.

### 6.18 24-hour small-fleet validation

The temporal driver now supports an arbitrary positive slot count while retaining the four-slot compatibility wrapper. A deterministic **SMALL-FLEET VALIDATION** runs 48 consecutive 30-minute slots with 50 vehicles and four active grids. It is an integration-health milestone, not the final thesis experiment and not evidence that the 5,000-vehicle January simulation is complete.

The fixture uses controlled deterministic demand/popularity and retains an explicit federation schedule for engineering tests. Production instead uses authoritative held-out inputs and one federated round per slot. Two fixture runs produced identical aggregate trajectories. Run it with `python scripts/test_validation_24h.py`.

### Reproducible validation reporting

Run `python scripts/generate_validation_figures.py` to reproduce the compact pricing, customer-response, and dispatch reporting package from the deterministic 50-vehicle, four-grid, 48-slot, seed-42 engineering validation. The script consumes completed simulator results, validates reporting invariants, and writes one-row-per-pricing-context and one-row-per-slot datasets under `results/validation/validation_50v_4g_48slots_seed42/`, human-readable summaries under `results/tables/{pricing,customer_response,dispatch}/`, and 240-DPI figures under `results/figures/{pricing,customer_response,dispatch}/`. `summary.json` records the run configuration and reconciled totals; `figure_manifest.json` maps every figure to its compact source CSV.

These artifacts describe integration behaviour only. They are not results from the intended 5,000-vehicle January experiment, do not establish causal pricing effects, and do not identify an optimal pricing factor.

The completed Phase 7D production validation uses aligned frozen-CNN targets, authoritative popularity, a 5,000-vehicle fleet, and one NB13 round per slot. Its machine output is under `results/validation/phase7d_48slot_final_integrated_seed42/`; the dated professor-review package is under `results/validation/2026-09-08_48slot_run/`. The older Phase 7C-4 output used misaligned prediction timestamps and is invalid for scientific performance interpretation; Phase 7C-6 is the corrected aligned preflight.

Passenger-trip duration and energy now use the intact sampled empirical TLC row. Busy state is temporally persistent across mini-slot and main-slot boundaries, and passenger energy remains deducted once across those advances. No centroid distance, grid-hop estimate, assumed speed, or external route model is used.

### Production validation status

The latest integrated validation is Phase 7D: 48 consecutive aligned target slots from **2026-01-25 19:00 inclusive to 2026-01-26 19:00 exclusive**, seed 42, fleet 5,000. All accounting/numerical gates passed, a fresh two-slot replay matched exactly, and the latest full regression passes **258 tests**. Status is **`READY_FOR_PHASE_8A`**. Machine output is in `results/validation/phase7d_48slot_final_integrated_seed42/`; the dated chart/table package is in `results/validation/2026-09-08_48slot_run/`. The next proposed authoritative experiment is the complete 298-target held-out window ending 2026-02-01 00:00 exclusive.

## 7. Configuration reference

`config/config.yaml` is the active configuration source. The table summarizes research-relevant settings rather than repeating every path.

| Area | Settings | Status/provenance |
| --- | --- | --- |
| Data/time | Month `2026-01`; seed 42; 30-minute interval | Study configuration / reproducibility control |
| Spatial | EPSG:2263; 3,000 m square grid | Legacy NB1-aligned adopted setting |
| Fleet | 5,000 vehicles; uniform valid-grid initialization; 30/2 minute main/mini slots | Supervisor/project decision; uniform initialization provisional |
| Weather | Meteostat 1.7.6; NYC point; naive timestamps | Legacy utility compatibility; temporal alignment unresolved |
| Statistics | Pre-cutoff fare prior; population SD; EWMA alpha 0.30; causal driver waits; missing-history `U_wait=0.5` | Frozen production configuration |
| EV energy | 75 kWh, 0.15 kWh/km, 30 kW | Ding et al. Table I values adopted in code |
| EV operations | SOC mean 0.50, SD 0.05, [0.50,0.70]; <=20% trigger; 0.90 efficiency; full-charge release | Supervisor/project/provisional settings as identified above |
| Charging | 15 stations; 3,000 kW per station | Project baseline; power-only capacity model |
| Dispatch | FCFS accepted requests; origin/direct-neighbour idle eligibility; driver contention; pickup-distance/utility/ID tie ranking | Final production dispatch with legacy compatibility mode |
| Routing | Equal component weights; STAY/N/E/S/W; 12-minute/0.45-kWh MOVE; normalized DOD penalty | Frozen production NB11 baseline |
| Routing policy learning | [64,32], LR 0.001, local observation capacity 1000, batch 32, 1 local epoch | Provisional NB12 engineering hyperparameters |
| Pricing | Request-level 8D LinUCB; factors 0.85-1.15; alpha 1.0; historical sensitivity; served-revenue/training-reference reward | Frozen production configuration; later sensitivity analysis remains possible |

## 8. Fresh-machine installation

### Prerequisites

- Git (or an extracted repository archive)
- Conda/Miniconda/Anaconda
- Python 3.12-compatible platform and sufficient disk/RAM for the January taxi parquet and generated arrays
- Internet access only when building/rebuilding Meteostat weather

```bash
git clone <repository-url>
cd Implementation
```

The intended Conda environment is named `ridehailing-phd`. The repository's current `environment.yml` defines only Python 3.12, `requirements.txt` is intentionally empty, and `requirements-lock.txt` contains machine-local build paths. Consequently, none of these files is currently a one-command portable environment specification.

Create the environment and install the verified working dependency set:

```bash
conda create -n ridehailing-phd python=3.12 -y
conda activate ridehailing-phd

python -m pip install \
  numpy==1.26.4 scipy==1.14.1 pandas==3.0.5 pyarrow==25.0.0 \
  geopandas==1.1.4 shapely==2.1.2 pyproj==3.7.2 \
  PyYAML==6.0.3 scikit-learn==1.9.0 matplotlib==3.11.1 \
  mapclassify==2.8.1 meteostat==1.7.6 \
  tensorflow==2.16.2 keras==3.15.1
```

The explicit NumPy/SciPy/mapclassify/TensorFlow pins are important: newer incompatible combinations previously broke TensorFlow in the working environment. Current saved artifacts were built on macOS ARM, but the code makes no Apple-Silicon-specific installation claim; verify TensorFlow on the target machine.

```bash
python -m pip check
python -c "import tensorflow as tf; print(tf.__version__); print(tf.reduce_sum(tf.ones((2, 2))))"
python -c "import meteostat, numpy, scipy; print(meteostat.__version__, numpy.__version__, scipy.__version__)"
```

## 9. Required data placement

Before the spatial build, place the following files relative to the repository root:

```text
data/raw/yellow_taxi/yellow_tripdata_2026-01.parquet
data/raw/taxi_zones/taxi_zones.shp
data/raw/taxi_zones/taxi_zones.shx
data/raw/taxi_zones/taxi_zones.dbf
data/raw/taxi_zones/taxi_zones.prj
```

Additional shapefile sidecars supplied with the zone dataset should remain in `data/raw/taxi_zones/`. The weather build fetches and persists the Meteostat artifact; later stages consume the persisted parquet rather than downloading weather themselves.

## 10. Reproducible workflow

Run scripts from the repository root with the `ridehailing-phd` environment activated.

```bash
# 1. Spatial/grid artifacts and cleaned trips
python scripts/build_grid.py

# 2. Legacy-compatible weather artifact (requires network access if absent)
python scripts/build_weather.py

# 3. NB3 demand master
python scripts/build_demand_master.py

# 4. NB4 CNN dataset
python scripts/build_cnn_dataset.py

# 5. NB5 training (can take materially longer than validation)
python scripts/train_cnn.py

# 6. NB10 station placement
python scripts/build_charging_stations.py
python scripts/build_destination_popularity.py

# 7. Deterministic component demonstrations
python scripts/test_fleet_state.py
python scripts/test_dispatch.py
python scripts/test_statistics.py
python scripts/test_energy.py
python scripts/test_charging_infrastructure.py
python scripts/test_routing_baseline.py
python scripts/test_local_routing_learning.py

# 8. Unit suite
python -m unittest discover -s tests -q

# Rebuild the Phase 7D human-readable package from existing results (no simulation)
python scripts/generate_phase7d_report.py

# Production execution interface; choose slot count/output explicitly
python scripts/run_production_experiment.py --slots <N> --seed 42 --output <directory>
```

For build scripts, `--validate` reloads and validates existing artifacts without rebuilding. `--force` explicitly rebuilds/overwrites that stage's artifacts. `scripts/train_cnn.py --validate` validates saved NB5 artifacts without training; `--force` retrains and overwrites the saved NB5 outputs.

### Quick validation without retraining

If generated artifacts already exist, use:

```bash
python scripts/build_grid.py --validate
python scripts/build_weather.py --validate
python scripts/build_demand_master.py --validate
python scripts/build_cnn_dataset.py --validate
python scripts/train_cnn.py --validate
python scripts/build_charging_stations.py --validate
python scripts/build_destination_popularity.py --validate
python -m unittest discover -s tests -q
```

## 11. Generated artifacts

| Stage | Artifact | Purpose |
| --- | --- | --- |
| Spatial | `data/processed/cleaned_trips.parquet` | Filtered trips with seeded `PUGridID`/`DOGridID` |
| Spatial | `grid_lookup.parquet`, `grid_mask.npy`, `grid_metadata.json` | Canonical valid-grid geometry, mask, and provenance |
| Spatial | `zone_grid_mapping.parquet`, `zone_to_grids.pkl`, `neighbour_map.parquet` | Zone candidates and four-direction adjacency |
| Weather | `weather/nyc_weather_processed_2026_01.parquet`, metadata JSON | Legacy-compatible hourly weather/provenance |
| NB3 | `demand_master_2026_01.parquet`, metadata JSON | Authoritative complete grid-time demand table |
| NB4 | `cnn/*.npy`, `cnn/metadata.pkl` | Train/test CNN tensors and chronology |
| NB5 | `models/demand/normalization.pkl`, `cnn_model.keras` | Training-only normalization and trained CNN |
| NB5 | `cnn_metrics.csv`, `cnn_predictions.npy`, `cnn_history.pkl`, `cnn_provenance.json` | Evaluation, outputs, training history, provenance |
| NB5 | `outputs/figures/cnn_*.png` | Training, map, scatter, and error visualizations |
| NB10B | `charging_stations_2026_01.parquet` | Popularity-ranked station definitions |
| Pricing popularity | `destination_popularity_2026_01.parquet`, metadata JSON | Leakage-safe destination/drop-off trailing SMA, fixed global quintiles, labels, and scalar encodings |
| Validation | `results/tables/validation_24h_*.csv` | Aggregate 48-slot small-fleet diagnostics and pricing-factor frequencies |
| Validation | `results/figures/validation_24h_*.png` | Fleet, energy, request, and revenue health plots |
| Production | `models/routing/nb12_nb13_common_initialization_seed42.npz`, metadata JSON | Frozen common NB12/NB13 initialization |
| Production | `driver_preferences_seed42.parquet`, `nb9_fare_bootstrap_2026_01_25_1830.parquet` | Persistent profiles and pre-cutoff fare prior |
| Phase 7D | `results/validation/phase7d_48slot_final_integrated_seed42/` | Authoritative 48-slot machine output |
| Phase 7D reporting | `results/validation/2026-09-08_48slot_run/` | Dated charts, tables, manifest, and review index |

`models/pricing/`, `outputs/metrics/`, and `outputs/logs/` remain reserved persistence/output areas. Production state remains in memory during a trajectory; compact result artifacts and reproducibility fingerprints are persisted after execution.

## 12. Testing

The latest full regression contains **258 passing tests**:

```bash
python -m unittest discover -s tests -q
```

| Area | Test file(s) |
| --- | --- |
| Configuration/spatial grid/artifacts/mapping | `test_config.py`, `test_grid.py`, `test_artifacts.py`, `test_spatial_mapping.py` |
| Weather and demand | `test_weather_contract.py`, `test_demand_aggregation.py`, `test_demand_artifacts.py` |
| CNN tensors/model | `test_cnn_tensors.py`, `test_cnn_model.py` |
| Fleet/dispatch/statistics | `test_fleet_state.py`, `test_dispatch.py`, `test_statistics.py` |
| EV energy/charging | `test_energy.py`, `test_charging_stations.py` |
| Routing/local learning/federation | `test_routing_baseline.py`, `test_routing_learning.py`, `test_routing_federated.py` |
| Pricing and one-slot dispatch integration | `test_pricing.py`, `test_pricing_dispatch.py` |
| Grid policy aggregation and main-slot orchestration | `test_grid_policy.py`, `test_main_slot.py` |
| Four-slot temporal continuity | `test_multi_slot.py` |
| Empirical trip duration/distance/passenger energy | `test_passenger_trip.py` |
| Empirical within-slot arrival timing | `test_empirical_arrivals.py` |
| Generic temporal driver and 24-hour small-fleet validation | `test_validation_24h.py` |
| Driver/vehicle idle-wait lifecycle and grid attribution | `test_driver_waiting.py` |
| Destination/drop-off popularity aggregation, leakage, quintiles, and encoding | `test_destination_popularity.py` |
| Historical sensitivity, customer sampling, `P_max`, and hierarchical fallback | `test_historical_sensitivity.py`, `test_customer_sensitivity.py` |
| Driver contention and request-level pricing | `test_driver_contention.py`, `test_request_pricing_context.py`, `test_pricing_dispatch.py` |
| Production routing artifacts and aligned assembler | `test_routing_production.py`, `test_production_simulation.py` |

Tests primarily exercise deterministic and synthetic fixtures plus production loading/contracts. Passing validates module contracts. The separate completed Phase 7D trajectory validates 24-hour integrated production behavior; neither result substitutes for the proposed 298-slot experiment.

The final proposed request-level pricing context builder has a fixed order of scaled predicted demand, scaled corrected supply, routing probability mass toward the destination, lagged destination popularity, scaled trip distance in kilometres, scaled historical `P_base(W,T)`, `Period / 47`, and categorical weather severity. Distance and base price use clipped `log1p/P99` transforms with frozen training references.

Production uses `request_8d` for one LinUCB selection per request. Rewards are finalized only after dispatch: a served request receives its recorded dispatch price, while rejected and accepted-but-unserved requests receive zero. `legacy_grid` remains compatibility-only.

Production historical sensitivity uses the training-only hierarchical fallback `exact → Period → Weather → Global`, with resolve-once sampling and complete pending-decision accounting.

Production request-level LinUCB uses `training_reference` scaling: raw served `P_dispatch` remains the economic metric, while the learner receives `raw_served_revenue / (BASE_PRICE_REF_P99 × 1.15)` without clipping. Other selectors remain compatibility modes.

## 13. Reproducibility boundaries

The code centralizes seed 42 and uses deterministic ordering where possible: GridID ordering; zone-to-grid mapping; fleet placement; empirical trip-row sampling; empirical pickup-to-mini-slot mapping; initial SOC sampling; simultaneous charging priority; and NB12 state/action encoding. Customer acceptance uses its own explicit persistent RNG. NB4 uses a chronological split, and NB5 fits normalization on training features only.

The saved grid, weather, demand, tensor, station, and CNN provenance metadata provide artifact-level traceability. TensorFlow training is configured for best-effort deterministic behaviour, but identical training results should not be assumed bit-for-bit across operating systems, devices, TensorFlow builds, or CPU kernels.

## 14. Research assumptions and limitations

The following distinctions are material to interpreting results:

1. Taxi records lack trip coordinates; seeded within-zone GridID assignment is an approximation.
2. The 3 km square grid is an adopted legacy setting, not reselected by this implementation.
3. Taxi/weather timestamps are naive; their alignment is unresolved.
4. Weather is point-derived Meteostat data, and `WeatherCode` is retained without additional transformation.
5. Padded invalid grid cells remain in NB5 normalization/loss/metrics to reproduce the legacy baseline.
6. The four-direction neighbour map, uniform fleet placement, and origin/direct-neighbour contention region are current engineering baselines. Passenger origin, destination, timestamps, duration, distance, and fare are derived jointly from an empirical TLC row; arrival remains discretized to two-minute resolution. NB9 waiting is completed driver-idle waiting before dispatch, not passenger waiting. Repositioning takes 12 minutes and vehicles remain unavailable during movement.
7. Station placement is popularity-based; charging navigation uses projected centroid distance rather than road-network travel.
8. Charging capacity is power-only; the 0.90 efficiency and full-charge release rule are project/provisional choices.
9. NB11 movement uses 15 km/h and a 3 km threshold, not road-network routing.
10. NB12 learns a local masked policy from utility-selected actions; policy inference does not replace NB11's actual maximum-utility decision in the current implementation.
11. The production assembler connects aligned frozen-CNN demand, popularity, request-level pricing, historical sensitivity, driver contention, NB9-NB13, charging, and continuous 5,000-vehicle state. Phase 7D covers 48 slots; conclusions over the full held-out target period await the proposed 298-slot run.

## 15. Methodology provenance

Not all values in this repository have the same evidentiary status. Methodology authority is, in order: the corrected final implementation process; supervisor clarifications; cited mathematical sources for degradation, LinUCB pricing, and ordinary customer acceptance; and the broader execution plan where not superseded. NB1-NB5 compatibility decisions preserve the legacy notebooks. Unresolved modelling choices remain explicitly provisional.

For EV energy, the adopted Table I reference is: Zhaohao Ding et al., *Pricing Based Charging Navigation Scheme for Highway Transportation to Enhance Renewable Generation Integration*, IEEE Transactions on Industry Applications (2023). The code adopts its documented capacity, reference energy, consumption, and charging-power values; it does not claim that every operational SOC, queue, or release rule is literature-derived.

## 16. Pending work and roadmap

1. **Phase 8A:** run the proposed 298 aligned held-out target slots with the frozen production configuration.
2. **Final evaluation:** produce prespecified thesis tables, baselines, and ablations without tuning from headline profitability.
3. **Separate elasticity analysis:** use approximately three or six months of historical data for time-by-weather elasticity outputs; confirm the channelization definition first.

These remaining experiments are intentionally pending; implemented production components and completed Phase 7D validation should not be mistaken for the unrun 298-slot result.
