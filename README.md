# Ride-Hailing Platform Simulation

## 1. Project overview

This repository is a modular research implementation for studying NYC ride-hailing demand prediction, fleet operations, EV charging, vehicle repositioning, and future federated routing and pricing. It uses January 2026 NYC Yellow Taxi data and a shared spatial representation to keep demand, vehicle, and operational state contracts consistent.

The work has two distinct layers:

- **Demand prediction (offline):** prepare taxi, spatial, and weather data; construct a grid-time demand table; build CNN tensors; train and validate a demand predictor.
- **Operations and learning (online components):** represent a fleet, generate empirical OD requests, dispatch vehicles, track operating statistics, manage EV energy/charging, execute deterministic repositioning, and train local routing Q-networks.

Demand prediction estimates future grid demand. Routing selects a vehicle movement action. Pricing, customer response, federated aggregation, and a complete slot-level simulator are separate future components; they are not implemented by the current codebase.

The legacy NB1-NB5 notebooks remain reference material and are not modified. The modular implementation currently extends through NB12.

## 2. Current implementation status

| Component | Status | Current scope |
| --- | --- | --- |
| Spatial/data preparation (NB1-NB2) | COMPLETE | January taxi cleaning, zone/grid artifacts, deterministic legacy-compatible mapping |
| Weather preparation | COMPLETE | Legacy-compatible January Meteostat artifact |
| Demand master (NB3) | COMPLETE | Half-hour grid-level pickup-demand master table |
| CNN tensors (NB4) | COMPLETE | Seven-channel, one-step-ahead tensor dataset |
| CNN training/inference (NB5) | COMPLETE | Legacy CNN, persisted model, normalization, predictions, and metrics |
| Fleet baseline | COMPLETE | Vehicle state, seeded placement, supply aggregation |
| Request/OD generation | COMPLETE | Empirical conditional OD sampling and seeded mini-slot arrivals |
| Baseline dispatch | COMPLETE | FCFS same-grid/direct-neighbour dispatch baseline |
| Operational statistics (NB9) | COMPLETE | Grid/slot fare, wait, EWMA, and charging context |
| EV energy (NB10A) | COMPLETE | SOC initialization, energy consumption, trigger, charge/release transitions |
| Charging infrastructure (NB10B) | COMPLETE | Popularity-based stations, power-limited charging, FCFS queue |
| Routing/repositioning baseline (NB11) | COMPLETE | Fixed actions, action mask, deterministic selection, EV transition |
| Local routing learning (NB12) | COMPLETE | Per-vehicle local DQN-style learner and federation-ready export payload |
| Federated aggregation (NB13) | PENDING | No participant selection, aggregation, or global model exists |
| Pricing integration | PENDING | No pricing state, learner, offered fare, or customer-response model exists |
| Integrated simulator / experiments | PENDING | No end-to-end multi-slot controller or experiment suite exists |

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
               NB11 deterministic repositioning
                              |
                              v
                  NB12 local routing Q-learning
                              |
                              v
                 Local weights and sample count only
                              |
                              v
            NB13 federated aggregation [PENDING]
                              |
                              v
                    Global routing model [PENDING]
                              |
                              v
                 Pricing / integrated simulation [PENDING]
```

NB11 and NB12 intentionally have different responsibilities:

- **NB11** defines state construction, the fixed action set, invalid-action masking, deterministic score selection, and EV repositioning mechanics.
- **NB12** learns local Q-values from completed outcomes using the NB11 state and mask.
- **NB13** will aggregate local model updates into a common model. It is not implemented.

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
| `src/routing/` | NB11 baseline routing and NB12 local learning |
| `src/federated/`, `src/pricing/` | Package placeholders; research logic is pending |

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
| Source | Frozen `PUGridID -> DOGridID` pairs from cleaned January trips |

The empirical OD distribution has 3,699,638 source trips and 191,762 observed OD pairs. One request is generated per integer grid-demand unit; an origin's destination is sampled from its seeded empirical conditional distribution. Requests are assigned uniformly and reproducibly across the 15 two-minute mini-slots inside a 30-minute main slot, then processed FCFS by `(request_time, request_id)`.

The current dispatch policy is an engineering baseline: find the lowest-ID eligible `IDLE` vehicle in the origin grid, then direct canonical neighbours; exclude BUSY/CHARGING and low-energy vehicles; mark a failure `UNSERVED`. The configured two-minute trip duration is a placeholder, not an empirical travel-time model.

### 6.8 NB9 operational statistics

| Item | Current contract |
| --- | --- |
| Module | `src/simulation/statistics.py` |
| Demonstration | `python scripts/test_statistics.py` |

For every grid/main slot, the module records fare and wait counts, means, and population standard deviations (`ddof=0`), along with `ewma_fare`, `ewma_std_fare`, `ewma_wait`, and `ewma_std_wait`. It also carries charging availability and wait context where supplied. The configured `alpha = 0.30` uses first observation initialization and no-observation carry-forward:

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

### 6.11 NB11 deterministic routing/repositioning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/baseline.py` |
| Demonstration | `python scripts/test_routing_baseline.py` |

Only eligible `IDLE` vehicles not requiring charging may reposition. The fixed action order is `[STAY, NORTH, EAST, SOUTH, WEST]`; absent boundary neighbours are invalid and masked. The state combines the current grid and valid candidate-grid features: predicted demand, supply totals/statuses, current and EWMA fare/wait statistics, charging availability/wait, plus vehicle energy. The selector chooses the highest valid externally supplied score and breaks ties by fixed action order.

The baseline uses 15 km/h, a 3 km repositioning threshold, and <=30-minute feasibility. Thus a non-stay movement takes 12 minutes and consumes 0.45 kWh under the current energy model. NB11 has no reward or learning logic.

### 6.12 NB12 local routing learning

| Item | Current contract |
| --- | --- |
| Module | `src/routing/learning.py` |
| Demonstration | `python scripts/test_local_routing_learning.py` |

NB12 uses one local learner per participating vehicle. It has a fixed finite `float32` state vector of **87** elements, exactly:

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

The five outputs are Q-values, not probabilities, in `[STAY, NORTH, EAST, SOUTH, WEST]` order. Greedy selection is the NB11 masked deterministic argmax. During training, seeded epsilon-greedy exploration samples only valid actions.

An experience is recorded only when the dispatch result from the **next 30-minute main slot** is known:

```text
(state_t, action_t, reward_t, state_t+1, next_action_mask, terminal)
reward_t = 1.0 if dispatched in the next slot, else 0.0
```

`STAY` may receive reward 1. Raw replay stays local in a bounded per-vehicle buffer; incomplete outcomes create no experience. The learner has online and target networks, trains at most one minibatch per main slot, uses the masked target-network maximum for nonterminal DQN bootstrap, and synchronizes target weights every configured interval. Its federation-ready export contains only copied online weights, vehicle ID, local sample count, state dimension, and action order. No aggregation or shared/global model is implemented.

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
| Dispatch | Seeded uniform mini-slot arrival; same-grid then direct-neighbour FCFS | Current engineering baseline; 2-minute duration placeholder |
| Routing | Action order; 15 km/h; 3 km; <=30 minutes | Current NB11 baseline |
| Routing learning | [64,32], LR 0.001, gamma 0.95, replay 1000, batch 32, epsilon 0.10->0.01 x0.995, target sync 5 slots | Provisional NB12 learning hyperparameters |

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

`models/routing/`, `models/pricing/`, `outputs/metrics/`, and `outputs/logs/` are currently reserved areas rather than evidence of completed global routing, pricing, or integrated experiments.

## 12. Testing

The suite contains **83** defined test methods across 16 files:

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
| Routing/local learning | `test_routing_baseline.py`, `test_routing_learning.py` |

Tests primarily exercise small deterministic and synthetic fixtures. Passing them validates module contracts; it does not constitute a completed full-month integrated simulation or a completed research experiment.

## 13. Reproducibility boundaries

The code centralizes seed 42 and uses deterministic ordering where possible: GridID ordering; zone-to-grid mapping; fleet placement; OD destination sampling; mini-slot request arrival; initial SOC sampling; simultaneous charging priority; and NB12 exploration/replay sampling. NB4 uses a chronological split, and NB5 fits normalization on training features only.

The saved grid, weather, demand, tensor, station, and CNN provenance metadata provide artifact-level traceability. TensorFlow training is configured for best-effort deterministic behaviour, but identical training results should not be assumed bit-for-bit across operating systems, devices, TensorFlow builds, or CPU kernels.

## 14. Research assumptions and limitations

The following distinctions are material to interpreting results:

1. Taxi records lack trip coordinates; seeded within-zone GridID assignment is an approximation.
2. The 3 km square grid is an adopted legacy setting, not reselected by this implementation.
3. Taxi/weather timestamps are naive; their alignment is unresolved.
4. Weather is point-derived Meteostat data, and `WeatherCode` is retained without additional transformation.
5. Padded invalid grid cells remain in NB5 normalization/loss/metrics to reproduce the legacy baseline.
6. The four-direction neighbour map, uniform fleet placement, request mini-slot timing, dispatch search, and two-minute trip duration are current engineering baselines, not final empirical methodology.
7. Station placement is popularity-based; charging navigation uses projected centroid distance rather than road-network travel.
8. Charging capacity is power-only; the 0.90 efficiency and full-charge release rule are project/provisional choices.
9. NB11 movement uses 15 km/h and a 3 km threshold, not road-network routing.
10. NB12 uses a binary next-slot dispatch reward. Its architecture and hyperparameters are provisional and should not be represented as a final research reward/utility formulation.
11. No federated aggregation, global routing model, pricing mechanism, customer acceptance model, or full integrated simulator exists yet.

## 15. Methodology provenance

Not all values in this repository have the same evidentiary status. NB1/NB2/NB3/NB4/NB5 compatibility decisions preserve the legacy notebooks. Operational baselines are documented in code/configuration as project or supervisor decisions where applicable. Unresolved modelling choices remain explicitly provisional.

For EV energy, the adopted Table I reference is: Zhaohao Ding et al., *Pricing Based Charging Navigation Scheme for Highway Transportation to Enhance Renewable Generation Integration*, IEEE Transactions on Industry Applications (2023). The code adopts its documented capacity, reference energy, consumption, and charging-power values; it does not claim that every operational SOC, queue, or release rule is literature-derived.

## 16. Pending work and roadmap

1. **NB13 federated learning:** define eligibility, participant sampling, aggregation algorithm/weights, global-model persistence, and redistribution.
2. **Pricing:** freeze pricing state/action/reward, customer response, offered-fare logic, and learning method.
3. **Integrated simulation:** connect predicted demand, fleet, requests, dispatch, statistics, EV charging, routing, local learning, federation, and pricing on the 30-minute/2-minute timeline.
4. **Research experiments:** multi-slot/month runs, EV-penetration scenarios, sensitivity analysis, baselines/ablations, research metrics, thesis figures/tables, and final reproducibility validation.

These items are intentionally pending. They must not be inferred from package names, reserved directories, or the presence of local NB12 exports.
