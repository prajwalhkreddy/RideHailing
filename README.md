# Ride-Hailing Platform Simulation

## 1. Project overview

This repository is a modular research implementation for studying NYC ride-hailing demand prediction, fleet operations, EV charging, vehicle repositioning, federated routing-policy aggregation, and contextual pricing/customer acceptance. It uses January 2026 NYC Yellow Taxi data and a shared spatial representation to keep demand, vehicle, and operational state contracts consistent.

The work has two distinct layers:

- **Demand prediction (offline):** prepare taxi, spatial, and weather data; construct a grid-time demand table; build CNN tensors; train and validate a demand predictor.
- **Operations and learning (online components):** represent a fleet, generate empirical OD requests, price requests, draw customer acceptance, dispatch accepted requests, track operating statistics, manage EV energy/charging, execute utility-based repositioning, and learn/federate routing policies.

Demand prediction estimates future grid demand. NB11 utility selects actual vehicle movement, while NB12/NB13 policy probabilities provide a learned signal to pricing rather than movement commands. One complete controlled 30-minute slot and a short four-slot/two-hour temporal driver are implemented; full-scale and January simulation remain future work.

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
| Pricing state + contextual LinUCB | COMPLETE (standalone) | Eight-feature context, seven factor arms, disjoint LinUCB |
| Customer acceptance + pricing payoff | COMPLETE (standalone) | Ordinary ride-hailing Eq. (31), seeded draw, accumulated accepted offered revenue |
| Pricing/customer/dispatch one-slot integration | COMPLETE | One frozen factor per context, pre-dispatch acceptance, separate accepted/served revenue |
| One-main-slot orchestration | COMPLETE | Pricing through optional FedAvg and next-slot pricing-input boundary |
| Short multi-slot temporal orchestration | COMPLETE | Four consecutive 30-minute slots with persistent state and explicit federation schedule |
| Full-scale simulator / experiments | PENDING | No production-scale or January experiment suite exists |

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
                 Integrated simulation [PENDING]
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
models/routing/         Reserved for future global routing artifacts
models/pricing/         Reserved for future pricing artifacts
outputs/figures/        NB5 figures
outputs/metrics/        Reserved metrics outputs
outputs/logs/           Reserved execution logs
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

The default legacy dispatch policy finds the lowest-ID eligible `IDLE` vehicle in the origin grid, then direct canonical neighbours; it excludes BUSY/CHARGING, charging-threshold vehicles, and vehicles lacking energy for the sampled passenger distance. The selectable final `driver_contention` mode instead offers each accepted request to all eligible same-grid/direct-neighbour vehicles. Its request utility reuses NB11's equal-weight price/wait/charging utility: centroid pickup distance maps to a bounded pickup-burden preference, and passenger-trip energy divided by full battery capacity supplies the normalized energy-burden penalty (neither is a measured passenger wait or battery-health percentage). A driver contends when request utility is at least its best valid non-passenger NB11 alternative; the platform ranks contenders by pickup distance, descending request utility, then vehicle ID. Both modes remain FCFS by request time/request ID, assign immediately, and do not queue failures. Served empirical requests use `tpep_dropoff_datetime - tpep_pickup_datetime` as their positive trip duration. Remaining travel time is decremented by each two-minute mini-slot and may cross 30-minute boundaries; completion moves the vehicle to the sampled empirical destination. The configured default duration remains only a compatibility fallback for synthetic/manual requests that lack empirical fields.

**Waiting-time semantics:** NB9/NB11 waiting means driver/vehicle idle time in a grid before receiving a dispatch, not passenger waiting time. An available IDLE vehicle begins an episode at zero in its current grid and gains two minutes after each completed mini-slot that it remains IDLE. Dispatch closes the episode and records its completed duration against the vehicle's waiting grid, including when a neighboring vehicle serves the request. Main-slot boundaries and NB11 STAY do not reset it. BUSY trip time, charging time, and reposition travel are not idle waiting. Passenger-trip completion and charging completion start a new zero-minute episode at the vehicle's available grid. Under the current instantaneous reposition transition, a MOVE abandons the origin episode without recording it and immediately starts a new zero-minute episode at the destination; no abandoned-wait statistic is fabricated.

NYC TLC `trip_distance` is retained as `trip_distance_miles` for source audit. Kilometres are the simulation's canonical operational distance unit, converted exactly once as `trip_distance_km = trip_distance_miles * 1.609344`. At successful assignment, before the vehicle transitions from `IDLE` to `BUSY`, passenger energy is deducted exactly once with the existing consumption rate: `trip_distance_km * 0.15 kWh/km`. The request records before, consumed, and after energy. Mini-slot advancement does not deduct it again. A completed low-energy vehicle enters the existing NB10 charging workflow; BUSY vehicles cannot charge or reposition.

### 6.8 NB9 operational statistics

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/statistics.py` |
| Demonstration | `python scripts/test_statistics.py` |

For every grid/main slot, the module records successful-trip fares and completed driver-idle dispatch waits, with separate counts, means, and population standard deviations (`ddof=0`), along with `ewma_fare`, `ewma_std_fare`, `ewma_wait`, and `ewma_std_wait`. A vehicle that remains idle has not completed an episode and creates no observation; a grid with no completed wait retains the existing missing/current and EWMA carry-forward behavior. It also carries charging availability and charging-queue wait context where supplied. The configured `alpha = 0.30` uses first observation initialization and no-observation carry-forward:

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

Production driver profiles use one seed-reproducible, persistent price preference and one persistent synthetic preferred idle-wait duration per vehicle. The wait preference is sampled uniformly from 0–30 minutes as a project modelling assumption; it is not measured NYC behavior, passenger waiting, or a cap on actual driver idle time. When a candidate grid has no causal driver-wait history, NB11 assigns only that candidate's normalized wait component the neutral value `0.5`; this creates no NB9 observation and is replaced immediately when current or carried EWMA wait statistics exist.

The baseline uses 15 km/h, a 3 km repositioning threshold, and <=30-minute feasibility. Thus a non-stay movement takes 12 minutes and consumes 0.45 kWh under the current energy model. NB11 has no reward or learning logic.

The authoritative production runner is `scripts/run_production_experiment.py`. It explicitly validates production artifacts, initializes the historical pre-cutoff fare prior once with empty causal wait history, uses uniform-valid routing probabilities only for the first slot, and then preserves fleet, RNG, LinUCB, NB9, NB12/NB13, charging, and learned routing state across slot boundaries. Production execution fails rather than substituting validation fixtures or demo inputs.

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

The common and local policies share the same `87 -> 64 -> 32 -> 5 logits` architecture, so aggregated weights load directly into fresh NB12 learners. The interface aggregates model weights only; raw states, chosen actions, masks, utilities, trajectories, and rewards are neither required nor transmitted. This baseline does not claim differential privacy, secure aggregation, client-failure simulation, or production communication behavior. Federation cadence remains a later simulator-integration decision.

### 6.14 Standalone contextual pricing and customer acceptance

| Item | Current contract |
| --- | --- |
| Modules | `src/pricing/state.py`, `linucb.py`, `customer.py`, `reward.py` |
| Demonstration | `python scripts/test_pricing.py` |

Pricing uses a disjoint-arm contextual LinUCB learner. Its bounded eight-feature context is `[scaled predicted demand, scaled current supply, P(STAY), P(NORTH), P(EAST), P(SOUTH), P(WEST), popularity]`; the complete routing-policy vector is required. The fixed arms are `[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]`. Each arm maintains `A = I` and `b = 0`, is scored with `theta^T x + alpha * sqrt(x^T A^-1 x)` using linear solves, and only the selected arm receives the context-specific payoff update. Before ordinary score selection begins, a deterministic global cold-start assigns each arm in that order until every arm has one actual reward observation. Assignments awaiting end-of-slot feedback are tracked as pending so simultaneous grid decisions use different unassigned arms. After cold start, numerically tied maximum scores are resolved with a seeded reproducible RNG rather than fixed lowest-index selection. There is no epsilon-greedy exploration.

**Pricing popularity semantics:** popularity is destination attractiveness from empirical drop-off activity, not pickup demand, predicted demand, supply, combined pickup/drop-off activity, or charging-station popularity. Trips are attributed by `DOGridID` and the 30-minute slot containing `tpep_dropoff_datetime`. For grid `g` and slot `t`, the feature uses a strictly lagged simple mean of observed drop-off counts in slots `t-6` through `t-1`—a three-hour window—with all available prior slots used during warm-up. Observed zero-drop-off grid-slots remain zeros; unavailable pre-period history remains unavailable rather than being fabricated.

Fixed global `Q20/Q40/Q60/Q80` thresholds are fitted only on the chronological reference/training period and then applied unchanged to test/runtime data. Inclusive upper boundaries produce `Very Low`, `Low`, `Medium`, `High`, and `Very High`, encoded respectively as `0`, `0.25`, `0.5`, `0.75`, and `1`. Duplicate thresholds are retained and the same deterministic inequalities still apply. The label remains in the popularity artifact for audit while the eighth LinUCB feature receives only its scalar encoding, preserving the eight-dimensional context.

#### Pricing context scaling

Only demand and supply are transformed. Raw frozen-CNN demand is clipped at zero, transformed as `log1p(max(0, demand)) / log1p(45.085255432128896)`, then clipped to `[0,1]`. The denominator is the P99 of non-negative frozen-CNN predictions produced by inference on the existing chronological training/reference tensors (2026-01-01 00:00 through 2026-01-25 18:00); held-out predictions were not used. Negative raw demand remains available in diagnostics alongside its non-negative and scaled values.

Supply retains the existing `supply_total` semantics and is transformed as `log1p(supply_total) / log1p(9)`, then clipped to `[0,1]`. The reference value `9` is the P99 reproduced from the configured seed-42 uniform initialization of 5,000 vehicles over 1,213 canonical grids. This initialization distribution does not capture later endogenous vehicle concentration caused by dispatch, repositioning, or charging. Values above the fixed reference are therefore clipped to one and clipping counts/rates are recorded; the scaler is never dynamically refitted.

Routing probabilities and the five-level popularity value are unchanged. The deterministic parameters, artifact hashes, fitting provenance, transforms, clipping policy, and methodology version are persisted in `config/pricing_context_scaler.json`. LinUCB `alpha = 1.0` remains provisional and has not been optimized for the scaled context; scaling behaviour must stabilize before alpha sensitivity analysis.

The January artifact uses the frozen cleaned-trip destination and drop-off timestamp fields. No pre-January drop-off observation exists locally, so all January 1 00:00 grid moving averages are unavailable; January 1 00:30 uses only the observed 00:00 counts, and the history expands until six slots are available. This is an explicit initialization limitation, not future filling. The static charging-station field named `popularity` remains the separate whole-month `pickup_count + dropoff_count` ranking and is never used as the pricing feature.

#### Offline historical customer sensitivity — Phase 1

`src/pricing/historical_sensitivity.py` and `scripts/build_customer_sensitivity.py` implement diagnostic preprocessing only. Training trips before the exclusive `2026-01-25 18:30` boundary are pooled by the existing `(WeatherCode, Period)` convention. Source-valid rows require positive finite `fare_amount` and positive finite TLC `trip_distance` no greater than 100 miles. Within each group, `P_base` and `D_base` are the respective means over all source-valid rows. An observation enters the ratio only when `abs(trip_distance - D_base) >= 0.01` mile, matching source resolution; retained observations use the unchanged `epsilon = abs(((P-P_base)/P_base) / ((D-D_base)/D_base))`. The derived group table and reproducibility metadata are saved as `data/processed/customer_price_sensitivity_2026_01.parquet` and `data/processed/customer_price_sensitivity_2026_01_metadata.json`. These validity and denominator-eligibility rules are not epsilon clipping or winsorization. Both population and sample SDs and unmodified diagnostic quantiles are retained; no distribution fitting, customer sampling, `P_max`, acceptance, reward, or LinUCB integration is part of Phase 1.1.

Standalone Phase 2 is implemented separately in `src/pricing/customer_sensitivity.py`; the published Eq.31 baseline remains unchanged. For a requested `(WeatherCode, Period)`, customer sensitivity is sampled from a Normal distribution with the stored `epsilon_mean` and `epsilon_std_population`, lower-truncated at zero with no upper bound. It then computes `P_dispatch = P_base * alpha` and `P_max = P_base + (((D-D_base)/D_base) * P_base / epsilon_customer)` and accepts exactly when `P_dispatch <= P_max`. Phase 3A exposes this proposed model through the runtime selector `pricing.customer_response_model`; `eq31` remains the default. Proposed-mode rejection gates the existing dispatch path and logs the complete W,T/sensitivity/price audit. Phase 3B adds the explicit `served_dispatch_revenue` reward mode: after dispatch, each context supplies LinUCB the sum of recorded offers for successfully served requests, while rejected and accepted-but-unserved requests contribute zero. Customer feedback remains separately reported. The default `legacy_normalized_accepted_revenue` mode preserves the earlier accepted-revenue-per-opportunity normalization; final context/supply redesign remains pending.

Phase 4A adds a reusable unscaled pricing-supply feature: `Supply(g,t) = currently IDLE vehicles in g + BUSY vehicles with a known passenger destination g and expected completion in the upcoming 30-minute slot`. The incoming window follows existing mini-slot completion semantics, `(slot_start, slot_end]`; charging and charging-queue vehicles are excluded. Phase 4B exposes this value through the `idle_plus_incoming` supply selector and places it in the unchanged second position of the eight-feature LinUCB context. The existing log1p/P99 transform remains unchanged. Recalibration preserves the original deterministic initialization reference convention; because all 5,000 initialized vehicles are IDLE, the corrected and legacy P99 references are both 9 across 1,213 grid observations. Remaining context features are unchanged.

The offered fare is the provided base fare multiplied by the selected factor. Ordinary ride-hailing acceptance uses Eq. (31) from the cited MARL pricing paper: `1 / (1 + exp(0.67 * factor * supply / potential_demand - 1.67))`. This project maps its selected factor to the paper's ordinary-order factor `lambda^1`; the paper does not supply this project's exact seven-arm set. A seeded RNG draws acceptance before dispatch. Accepted requests contribute their full offered fare whether or not a later vehicle assignment succeeds; rejected requests contribute zero revenue while remaining denominator opportunities.

The LinUCB reward measures realized accepted revenue per incoming pricing opportunity: `raw_revenue_per_opportunity = accepted_revenue / generated_requests`, followed by `normalized_reward = clip(raw_revenue_per_opportunity / 73, 0, 1)`. The denominator contains every generated request offered the selected price, not only accepted or served requests, so the reward preserves both offered-fare magnitude and acceptance/rejection effects without allowing raw grid request volume to dominate. The fixed fare reference `73` is the P99 of 2,898,376 finite positive empirical base fares in the chronological training/reference period `[2026-01-01 00:00, 2026-01-25 18:30)`; provenance is persisted in `config/pricing_reward.json`. Contexts with no generated request produce no learning observation or zero-reward update. LinUCB receives only the normalized value, while raw opportunity revenue remains available diagnostically.

LinUCB state is copy-exportable/importable in memory. Scaling is applied once at the methodology-derived pricing-context boundary; the LinUCB equations and eight-dimensional state contract are unchanged.

### 6.15 One-slot pricing, acceptance, and dispatch

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/pricing_dispatch.py` |
| Demonstration | `python scripts/test_pricing_dispatch.py` |

For each explicitly supplied grid context, pricing is selected once at the start of a 30-minute slot and remains frozen across all 15 two-minute mini-slots. The runtime interface receives predicted demand, the complete current global routing-policy probability vector, and existing popularity explicitly; current supply is snapshotted with the canonical fleet supply aggregator. Each generated request retains its base fare and records factor, offered fare, acceptance probability, and its single seeded customer decision. Processing order is `pricing -> customer acceptance -> dispatch`; rejected requests never enter dispatch.

The pricing revenue is the sum of offered fares for all customer-accepted requests, including accepted requests that dispatch cannot serve. The learning reward is that accepted revenue divided by all generated requests in the context and then normalized by the fixed training-fare P99. **Served revenue** remains a separate operational diagnostic and includes only accepted requests assigned by dispatch. An active context with generated requests receives one end-of-slot update, including a legitimate zero reward when requests were offered but none accepted. An active context with no generated request receives no learning update; if no context is active, no decision or synthetic update is created.

### 6.16 One-main-slot orchestration and grid policy aggregation

| Item | Current contract |
| --- | --- |
| Modules | `src/simulation/main_slot.py`, `grid_policy.py` |
| Demonstration | `python scripts/test_main_slot.py` |

One controlled main slot executes the completed modules in this order: pricing/customer acceptance/dispatch across 15 mini-slots; NB10 charging advancement and NB9 end-slot statistics; NB11 maximum-utility routing and existing movement/energy transition; NB12 local supervised observation and at-most-once slot training; optional NB13 FedAvg and global-weight redistribution; global-policy inference; and construction of the next pricing inputs. It stops before selecting the next pricing factors. Predicted demand and popularity remain explicit inputs, and production federation cadence remains unresolved rather than being hardcoded to every slot.

The grid routing probability supplied to pricing uses an explicit **project baseline aggregation rule**, not a professor- or paper-prescribed formula. The global NB12/NB13 policy first produces an individually masked `[STAY, NORTH, EAST, SOUTH, WEST]` probability vector for every eligible idle vehicle from its real 87-D routing state. These probability vectors are averaged arithmetically within each grid. One vehicle uses its vector unchanged. A grid with zero eligible vehicles carries its previous grid vector; first use without history requires explicit initialization. This aggregation is a learned policy tendency only and may be revisited in sensitivity analysis. **NB11 maximum utility remains the sole source of actual repositioning actions.**

### 6.17 Short temporal simulation

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/multi_slot.py` |
| Demonstration | `python scripts/test_multi_slot.py` |

The controlled temporal driver invokes the completed one-slot orchestrator exactly four times, advancing timestamps by 30 minutes. It reuses the same fleet and charging infrastructure, LinUCB learner, acceptance RNG stream, NB9 EWMA engine, local NB12 learners, and global policy learner. The latest grid probability becomes the next zero-vehicle carry-forward value. Federation slots are an explicit caller-supplied set rather than a claimed final cadence. Each slot receives only its explicitly supplied boundary forecast, popularity, requests, and utility inputs; no later realized outcome is inspected.

### 6.18 24-hour small-fleet validation

The temporal driver now supports an arbitrary positive slot count while retaining the four-slot compatibility wrapper. A deterministic **SMALL-FLEET VALIDATION** runs 48 consecutive 30-minute slots with 50 vehicles and four active grids. It is an integration-health milestone, not the final thesis experiment and not evidence that the 5,000-vehicle January simulation is complete.

The fixture uses a controlled deterministic demand series (`controlled_validation_fixture`) and an explicit deterministic popularity series (`explicit_deterministic_validation_fixture`). Its every-fourth-slot federation schedule is validation-only; the production cadence remains unresolved. Two seed-42 runs produced identical aggregate trajectories. The validation checks request, fleet-state, energy, charging, pricing, routing, NB9, NB12, federation, and grid-policy invariants, and writes aggregate CSV tables and diagnostic charts under `results/tables/` and `results/figures/`. Run it with `python scripts/test_validation_24h.py`.

### Reproducible validation reporting

Run `python scripts/generate_validation_figures.py` to reproduce the compact pricing, customer-response, and dispatch reporting package from the deterministic 50-vehicle, four-grid, 48-slot, seed-42 engineering validation. The script consumes completed simulator results, validates reporting invariants, and writes one-row-per-pricing-context and one-row-per-slot datasets under `results/validation/validation_50v_4g_48slots_seed42/`, human-readable summaries under `results/tables/{pricing,customer_response,dispatch}/`, and 240-DPI figures under `results/figures/{pricing,customer_response,dispatch}/`. `summary.json` records the run configuration and reconciled totals; `figure_manifest.json` maps every figure to its compact source CSV.

These artifacts describe integration behaviour only. They are not results from the intended 5,000-vehicle January experiment, do not establish causal pricing effects, and do not identify an optimal pricing factor.

Pending before the final experiment are frozen-CNN demand and popularity runtime wiring, final federation cadence, 5,000-vehicle scaling, January execution, and research tuning/evaluation.

Passenger-trip duration and energy now use the intact sampled empirical TLC row. Busy state is temporally persistent across mini-slot and main-slot boundaries, and passenger energy remains deducted once across those advances. No centroid distance, grid-hop estimate, assumed speed, or external route model is used.

## 7. Configuration reference

`config/config.yaml` is the active configuration source. The table summarizes research-relevant settings rather than repeating every path.

| Area | Settings | Status/provenance |
| --- | --- | --- |
| Data/time | Month `2026-01`; seed 42; 30-minute interval | Study configuration / reproducibility control |
| Spatial | EPSG:2263; 3,000 m square grid | Legacy NB1-aligned adopted setting |
| Fleet | 5,000 vehicles; uniform valid-grid initialization; 30/2 minute main/mini slots | Supervisor/project decision; uniform initialization provisional |
| Weather | Meteostat 1.7.6; NYC point; naive timestamps | Legacy utility compatibility; temporal alignment unresolved |
| Statistics | EWMA alpha 0.30; first observation | Provisional engineering settings |
| EV energy | 75 kWh, 0.15 kWh/km, 30 kW | Ding et al. Table I values adopted in code |
| EV operations | SOC mean 0.50, SD 0.05, [0.50,0.70]; <=20% trigger; 0.90 efficiency; full-charge release | Supervisor/project/provisional settings as identified above |
| Charging | 15 stations; 3,000 kW per station | Project baseline; power-only capacity model |
| Dispatch | Empirical within-slot arrival and duration; same-grid then direct-neighbour FCFS | Empirical timing with synthetic-request fallback |
| Routing | Equal component weights; one-sigma ranges; action order; 15 km/h; 3 km; <=30 minutes | Corrected NB11 baseline |
| Routing policy learning | [64,32], LR 0.001, local observation capacity 1000, batch 32, 1 local epoch | Provisional NB12 engineering hyperparameters |
| Pricing | LinUCB; factors 0.85-1.15; alpha 1.0; acceptance seed 42 | Approved method/arms; alpha is provisional because the paper's formula depends on unspecified confidence parameter delta |

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

`models/routing/`, `models/pricing/`, `outputs/metrics/`, and `outputs/logs/` remain reserved persistence/output areas; NB13 and pricing currently expose copy-safe in-memory state and do not implement production persistence or integrated experiments.

## 12. Testing

The suite contains **165** defined test methods across 27 files:

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

Tests primarily exercise small deterministic and synthetic fixtures. Passing them validates module contracts; it does not constitute a completed full-month integrated simulation or a completed research experiment.

The final proposed request-level pricing context builder has a fixed order of scaled predicted demand, scaled corrected supply, routing probability mass toward the destination, lagged destination popularity, scaled trip distance in kilometres, scaled historical `P_base(W,T)`, `Period / 47`, and categorical weather severity. Distance and base price use clipped `log1p/P99` transforms with frozen training references.

The optional `request_8d` pricing mode now uses that context for one LinUCB selection per request. Rewards are finalized only after dispatch: a served request receives its recorded dispatch price, while rejected and accepted-but-unserved requests receive zero. The default `legacy_grid` mode preserves grid-slot selection and its existing reward behavior.

Historical sensitivity can optionally use the training-only hierarchical fallback `exact → Period → Weather → Global`; fail-fast exact lookup remains the default. A short four-slot held-out proposed-mode run validates resolve-once fallback, request-level selection, delayed served rewards, and complete pending-decision accounting.

Request-level LinUCB learning can optionally use `training_reference` reward scaling: raw served `P_dispatch` remains the economic metric, while the learner receives `raw_served_revenue / (BASE_PRICE_REF_P99 × 1.15)` without clipping. The default `none` preserves the original raw-reward path and all legacy grid pricing behavior.

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
6. The four-direction neighbour map, uniform fleet placement, and dispatch search are current engineering baselines. Passenger arrival position, duration, distance, and fare are derived jointly from an empirical TLC row; arrival remains discretized to two-minute resolution. NB9 waiting is completed driver-idle waiting before dispatch, not passenger waiting; reposition is still instantaneous in the current transition model.
7. Station placement is popularity-based; charging navigation uses projected centroid distance rather than road-network travel.
8. Charging capacity is power-only; the 0.90 efficiency and full-charge release rule are project/provisional choices.
9. NB11 movement uses 15 km/h and a 3 km threshold, not road-network routing.
10. NB12 learns a local masked policy from utility-selected actions; policy inference does not replace NB11's actual maximum-utility decision in the current implementation.
11. One controlled slot and a four-slot temporal driver connect pricing through NB13 and next pricing inputs. Empirical passenger duration/distance/energy are integrated; final federation cadence, automatic frozen-CNN/popularity wiring, full-scale persistence, and the January simulator remain pending.

## 15. Methodology provenance

Not all values in this repository have the same evidentiary status. Methodology authority is, in order: the corrected final implementation process; supervisor clarifications; cited mathematical sources for degradation, LinUCB pricing, and ordinary customer acceptance; and the broader execution plan where not superseded. NB1-NB5 compatibility decisions preserve the legacy notebooks. Unresolved modelling choices remain explicitly provisional.

For EV energy, the adopted Table I reference is: Zhaohao Ding et al., *Pricing Based Charging Navigation Scheme for Highway Transportation to Enhance Renewable Generation Integration*, IEEE Transactions on Industry Applications (2023). The code adopts its documented capacity, reference energy, consumption, and charging-power values; it does not claim that every operational SOC, queue, or release rule is literature-derived.

## 16. Pending work and roadmap

1. **Runtime methodology completion:** connect frozen CNN predictions/popularity and finalize federation cadence.
2. **Full simulation and evaluation:** scale the fleet, run January/full-scale experiments, and produce evaluation/reporting outputs.
3. **Research experiments and tuning:** evaluate grid-policy aggregation sensitivity, context feature scaling, LinUCB alpha, other sensitivity analysis, and baselines/ablations.

These items are intentionally pending. They must not be inferred from package names, reserved directories, or the presence of local NB12 exports.
