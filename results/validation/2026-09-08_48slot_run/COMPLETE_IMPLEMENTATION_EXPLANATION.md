# Complete Implementation Explanation — PhD Ride-Hailing Simulation

**Documentation audit date:** 2026-09-08. **Scope:** current implementation and existing Phase 7D outputs only. No simulation, configuration change, artifact regeneration, or new methodology is part of this document.

**How to read:** §§1–33 explain implementation and corrections; §§34–47 interpret the 48-slot outputs, all 18 charts, and all 11 tables; §§48–54 distinguish evidence, questions, status, and limitations; §55 is the meeting summary. Equations describe current code, not proposed replacements. Counts are exact unless rounded explicitly; percentages use the denominators stated beside them.

**Authority:** [audited root README](../../../README.md), current code/config, authoritative artifact metadata, [raw Phase 7D results](../phase7d_48slot_final_integrated_seed42/summary.json), then the [dated reporting package](README.md). Earlier documents are chronology only. References such as `production.py:function` mean the named current function; repository-relative paths identify the source precisely. Where README prose conflicts internally with the executable production path, the contradiction is reported and current validated behavior is explained.

**Important audit outcome:** Phase 7D's numerical results reconcile. The documented READY_FOR_PHASE_8A milestone requires qualification because current terminal next-context lookup cannot finish the last frozen target (§31). Current grid units and request-contention wait-proxy semantics also need explicit review. These findings are documented, not fixed.

**Source map:** `src/demand/` for CNN; `src/spatial/` and `src/data/` for spatial/data preparation; `src/fleet/`, `src/dispatch/`, `src/charging/` for operational transitions; `src/pricing/` for contexts, sensitivity, supply and LinUCB; `src/routing/` for utility/local/federated learning; `src/simulation/` for statistics/orchestration. `config/config.yaml`, `config/pricing_context_scaler.json`, and legacy `config/pricing_reward.json` were compared with effective production arguments. Chart content was visually inspected and traced through `scripts/generate_phase7d_report.py` and `chart_manifest.json`. The appendix-style source/contradiction register is included within §54 to preserve exactly 55 numbered sections.

## 1. RESEARCH OBJECTIVE

The research implements an interacting ride-hailing platform in which predicted passenger demand, prices, customer willingness to pay, driver willingness to serve, vehicle availability, and EV energy evolve together. It combines **demand prediction + dynamic pricing + customer price response + vehicle dispatch + driver behavior + EV charging + repositioning + local routing learning + federated learning**. The purpose is to study the behavior and eventual comparative performance of this integrated proposed model.

These components cannot be interpreted independently. A lower offered fare may attract more customers, but it creates revenue only when an eligible driver contends and receives the assignment. A served trip removes local availability, consumes energy, and eventually adds a vehicle at its destination. Repositioning changes future availability but temporarily removes the moving vehicle from dispatch. Charging restores energy while tying up availability. These changes alter the next pricing context and the driver utilities used for subsequent movement.

| Decision layer | Current responsibility | What is learned or changed |
| --- | --- | --- |
| Platform | Forecast demand; choose one price factor per request; announce and rank driver contenders; operate charging and aggregate routing models | LinUCB learns expected scaled served revenue conditional on request context |
| Customer | Compare offered fare with a sampled willingness-to-pay limit | No customer learning model; a fixed historical statistical model supplies heterogeneous draws |
| Driver | Contend if the request utility meets the best alternative; select the highest-utility valid NB11 movement | Persistent preferences affect behavior; NB12 learns to imitate NB11 |
| Vehicle | Maintain location, travel time, energy, availability, idle timer, and charging membership | Physical/accounting state evolves, independently of neural-network training |
| Federated routing system | Combine local model weights and redistribute a common model | Learns global tendencies in NB11 labels; supplies probabilities to pricing |

There is no single jointly trained neural controller optimizing every subsystem. The CNN minimizes prediction error, LinUCB learns served-revenue feedback, NB11 maximizes a specified utility, and NB12 minimizes supervised classification loss. NB13 averages compatible local parameters. Revenue is gross recorded dispatch fare, not net platform profit after energy, wages, or depreciation. [Sources: root README §§1–3, 6; `src/simulation/production.py`, `src/simulation/main_slot.py`.]

## 2. END-TO-END SYSTEM ARCHITECTURE

```text
OFFLINE, frozen artifacts
January NYC taxi zones + trips + hourly weather
  -> canonical grid / zone assignment / N-E-S-W neighbours
  -> half-hour pickup demand and historical-demand channel
  -> seven-channel tensors X[t], pickup targets y[t+1]
  -> trained CNN + normalization + target-aligned predictions
  -> empirical trip pool, lagged destination popularity,
     customer sensitivity hierarchy, fare priors, driver profiles,
     charging-station definitions, common routing weights

ONCE AT RUN START
5000 vehicles + SOC + empty causal wait history + historical fare prior
  + persistent RNG streams + fresh LinUCB + common local/global weights
  + uniform probability over each grid's valid actions

EACH 30-MINUTE SLOT
aligned forecast -> rounded request counts -> empirical row sampling
  -> fleet snapshot: Idle + Incoming
  -> request-specific 8D contexts -> batched LinUCB selections
  -> historical P_base and sampled epsilon -> customer acceptance
  -> 15 mini-slots:
       accepted arrivals -> eligible drivers -> utility contention
       -> dispatch -> passenger BUSY / trip energy deduction
       -> advance travel and idle clocks -> present/advance charging
  -> finalize one served-revenue learning update per generated request
  -> NB9 served-fare and completed-driver-wait statistics
  -> NB11 candidate utility / maximum valid action
  -> STAY or timed BUSY repositioning
  -> NB12 local supervised training -> NB13 FedAvg
  -> masked vehicle probabilities -> grid averages / carry-forward
  -> next-slot routing probability and pricing context
```

The arrows are dependencies, not a claim that all work executes at passenger arrival. Current code selects **all request prices before the mini-slot dispatch loop**, using the slot-level supply and routing snapshot; feedback is applied after that loop. Thus there are individual request contexts and decisions, but no within-slot LinUCB learning between successive arrivals. NB11 movement starts at the end of the slot, after operational statistics have been updated. Its travel completes in following mini-slots.

Offline training and artifact creation are separate from runtime. Files are loaded and validated once, then mutable fleet, random-generator, pricing, statistics, charging, and local/global learning state persist in memory. Every 30 minutes the simulation collects results and performs one federation round. Every two minutes dispatch availability, travel completion, idle waiting, queue waiting, and charging energy can change. [Sources: `production.py:run_slot`, `pricing_dispatch.py:_run_request_pricing_dispatch_slot`, `main_slot.py:run_main_slot`.]

## 3. DATASET AND CLEANING

The source is NYC Yellow Taxi **January 2026**. Spatial metadata and the README report **3,724,889 raw trips**, **3,699,638 retained after valid-zone filtering**, and **3,699,633 January pickup events** in NB3. The last count is five lower because five cleaned records have pickup times outside the January aggregation window. These are different populations, not competing estimates of one count.

Retained information includes `tpep_pickup_datetime`, `tpep_dropoff_datetime`, `PUGridID`, `DOGridID`, `fare_amount`, and TLC `trip_distance`. Runtime derives duration from the paired timestamps and stores distance both in original miles and converted kilometres. Duration need not be a separately persisted parquet column: it is retained through the timestamp pair. The original fare is retained for audit even though production offered prices use the historical weather/period base price described in §15.

An empirical request preserves one trip row's origin, destination, distance, duration, fare, and within-slot arrival offset together. This preserves observed dependence: independently inventing a long distance, short duration, and unrelated fare could produce an implausible trip. Empirical sampling still has limitations: origins and destinations are approximate grid assignments, and month-wide sampling does not preserve the exact current half-hour's OD distribution.

NB2's zone cleaning did not remove every unusable runtime fare or duration. Runtime sampling excludes non-positive duration, negative/non-finite distance, and negative/non-finite fare. The README reports 44,612 non-positive-duration rows, 38,793 negative-fare rows, and **83,405 excluded rows after overlap**; distance has no negative/non-finite rows. Historical sensitivity uses its own stricter positive fare/distance rules (§14). No source parquet is repaired during a production run. [Sources: README §§5, 6.1, 6.3, 6.7; `src/data/taxi.py`; `src/dispatch/generation.py`; Phase 7D source manifest.]

## 4. SPATIAL GRID

The canonical spatial representation has **1,213 valid GridIDs, 0–1212**, placed in a **51 × 52** rectangular CNN layout. A GridID is the common integer identifier joining demand, vehicle locations, statistics, stations, popularity, and policy outputs. IDs are ordered north-to-south and then west-to-east. The rectangular layout contains padded positions outside the valid-grid mask; these are not additional operating grids.

A canonical neighbour is a valid cell immediately north, east, south, or west. Diagonal cells and cells beyond a direct neighbour are excluded. The neighbour artifact has 4,544 directional rows. The CNN uses surrounding tensor positions through convolution; dispatch searches the origin and its direct neighbours; repositioning considers one action per direction; routing masks absent neighbours; and supply is counted against the same GridIDs. A change to this representation would therefore affect the entire system.

The raw records contain taxi-zone IDs, not pickup/dropoff coordinates. The preserved mapping samples candidate intersecting grids within each zone using the deterministic legacy stream, seeded by 42 + January month number = 43. It is an approximation, not observed point-level trip location.

**Current unit contradiction:** README/config describe 3,000 metres, but `src/spatial/grid.py:build_grid` applies the numeric `size_meters=3000` directly to **EPSG:2263 coordinate values, which are US survey feet**. The current grid artifact's centroid spacing is 3,000 coordinate units. Thus its physical spacing is approximately 914.4 m, not a verified 3 km. Dispatch correctly labels centroid distances as EPSG:2263 feet. NB11 separately charges a fixed **3 km operational movement** (§27). This documentation preserves the artifacts and reports the discrepancy; it does not redefine the grid. Exact physical 3 km grid cells are **NOT VERIFIED FROM CURRENT AUTHORITATIVE SOURCE**. The established 1,213-grid/51×52 contract remains verified.

## 5. TEMPORAL STRUCTURE

One main slot lasts **30 minutes** and contains **15 × 2-minute mini-slots**. The daily calendar variable `Period` is `2 × hour + floor(minute/30)`, ranging from 0 at midnight to 47 at 23:30. Here `hour` is the timestamp's 0–23 clock hour, and `minute` is its minute component. This formula creates a stable time-of-day index shared by historical sensitivity, weather context, and pricing.

The 48-slot run starts at Period 38 (19:00), passes through midnight, and ends after Period 37 (18:30). CSV `slot_index` is zero-based elapsed run order; chart “Slot” is one-based; Period is clock time. These three labels must not be interchanged.

A main-slot forecast and context give a manageable half-hour decision horizon. Two-minute updates allow trips to finish and vehicles to become available within that horizon. Empirical passenger durations can span several mini-slots or main slots. A 12-minute reposition requires six mini-slots. Mini-slot quantization affects completion availability and driver waiting; it does not replace empirical trip duration with a two-minute ride. [Sources: config `time`, `simulation`; `src/fleet/fleet.py`; `generation.py`.]

## 6. CNN DEMAND PREDICTION

NB3 creates **1,488 January half-hour slots × 1,213 grids = 1,804,944 rows**. Demand is the count of pickups by `(TimeSlot, PUGridID)`. `HistoricalDemand` is a strictly earlier expanding mean for the same GridID, weekday, and Period. It is not current demand.

The one-step learning relation is:

\[
X[t]\longrightarrow y[t+1].
\]

`X[t]` is the seven-channel spatial feature map at slot `t`; `y[t+1]` is the map of pickup counts one half-hour later. One predicted value is an estimated number of pickups in one grid in that next slot, not a probability or destination choice. A forecast ahead of operations can inform availability and price before the target slot is processed.

| Channel | Meaning and construction | Why it is included |
| --- | --- | --- |
| HistoricalDemand | Earlier mean pickups in matching grid/weekday/Period | Repeated spatial and calendar demand pattern |
| Temperature | Hourly Meteostat temperature, repeated across the grid | Weather condition associated with travel demand |
| WindSpeed | Hourly Meteostat wind speed | Additional weather information |
| WeatherCode | Meteostat condition code | Discrete weather category; numeric coding follows legacy CNN |
| DayOfWeek | Calendar weekday index | Weekly variation |
| Hour | Clock hour | Daily variation |
| Period | Half-hour index 0–47 | Finer daily variation |

There are **1,487 one-step pairs**: the last January feature map has no next-January target. The chronological split is **1,189 training pairs + 298 held-out test targets**. NB4 saves channel-first `float32` arrays: X shape `(1487,7,51,52)`, y shape `(1487,1,51,52)` before splitting. Invalid cells are zero padded. NB5 converts layouts as required by Conv2D and fits channel-wise normalization on X_train only; target counts stay unnormalized.

The CNN is `Conv2D(32,3×3,ReLU) → Conv2D(64,3×3,ReLU) → Conv2D(32,3×3,ReLU) → Conv2D(1,1×1,linear)`, using same padding and **39,041 trainable parameters**. A convolution applies shared local spatial filters; ReLU retains positive activations and sets negative ones to zero. The final linear layer can output negative forecasts, which runtime clips to zero before request-count construction.

Training requested up to 50 epochs, batch size 32, a shuffled 20% validation split, and early stopping after five validation-loss epochs without improvement, restoring best weights. Held-out test targets are separate from this training validation split.

Saved outputs in `models/demand/` are `cnn_model.keras` (weights/architecture), `normalization.pkl` (training feature transform), `cnn_predictions.npy` (held-out maps), `cnn_metrics.csv`, `cnn_history.pkl` (epoch history), and `cnn_provenance.json` (traceability). NB4 `time_train.npy` and `time_test.npy` retain input timestamps. Grid and tensor metadata document shape, ordering, and provenance; they let downstream consumers reject incompatible artifacts.

For residual `e_i = predicted_i − observed_i` over `n` evaluated positions:

\[
MAE=\frac1n\sum_i|e_i|,\quad RMSE=\sqrt{\frac1n\sum_i e_i^2},\quad
R^2=1-\frac{\sum_i e_i^2}{\sum_i(observed_i-\overline{observed})^2}.
\]

`i` indexes evaluated grid/time positions and the overbar is the mean observed count. MAE measures typical absolute count error; RMSE gives large mistakes more weight; R² compares squared error with predicting the overall mean. Lower MAE/RMSE and higher R² usually indicate better predictions on the same evaluation population. Current saved values are **RMSE 2.5915691905, MAE 0.6337751746, MAPE 83.4894835949%, R² 0.8985528946**. MAPE is the mean absolute error relative to nonzero actual demand, multiplied by 100; low actual counts can make percentage error large. These are forecasting metrics, not dispatch or revenue scores. Legacy padding remains in normalization/loss and the general metric population; MAPE separately masks zero actual targets. Thus do not present these as exclusively occupied-cell accuracy. [Sources: README §§6.3–6.5; `src/demand/model.py`, `tensors.py`, `inference.py`; saved metrics.]

## 7. CNN TIMESTAMP BUG AND CORRECTION

The original consumer used `prediction[i] → time_test[i]`, treating an **input timestamp** as a **target timestamp**. Since the model was trained one step ahead, the correct mapping is:

\[
target\_time_i=input\_time_i+30\text{ minutes}.
\]

`i` is the prediction-array row. The addition aligns a predicted map with the half-hour whose pickups it predicts. Without it, operations consumed every prediction 30 minutes early. Correcting the consumer changes the association between values and time, not the values or trained weights; retraining was unnecessary.

The frozen input timestamps run from **2026-01-25 18:30** to **2026-01-31 23:00**. Their 298 targets run from **2026-01-25 19:00 inclusive** to **2026-02-01 00:00 exclusive**, with the final target at January 31 23:30. There are 149 hours × two slots/hour = **298 slots**, not 299. Counting both the old 18:30 input boundary and all corrected targets incorrectly adds a slot.

The old 18:30-start preflight is useful only as engineering chronology. It cannot support correctly timed scientific comparisons. `phase7c6_aligned_production_preflight_seed42` and Phase 7D use the corrected mapping. **Separate boundary finding:** the current assembler unconditionally requests the next forecast even at the last target; §31 explains why this limits execution readiness for the full 298 slots. [Sources: `production.py:_load_sources_once`, `_demand`, `run_slot`; direct inspection of `time_test.npy`; README §6.11.]

## 8. FLEET INITIALIZATION

Production creates **5,000 vehicles**, initially placed uniformly over valid GridIDs with seed 42. Each is modeled with a **75 kWh** battery. State of charge (SOC) is energy divided by capacity. Initial SOC is drawn from a Normal with underlying mean 0.50 and SD 0.05, truncated to **[0.50,0.70]**. Truncation changes the realized mean; this is not a symmetric distribution with actual mean exactly 50%. The stored 60 kWh reference is not the operational initialization.

Energy consumption is **0.15 kWh/km**. A vehicle stores its ID, current grid, destination, remaining travel time, current action, energy, and idle-wait episode. The status enum has `IDLE`, `BUSY`, and `CHARGING`; reporting separates passenger BUSY from repositioning BUSY using movement state/action. Queue membership is tracked by charging infrastructure; “REPOSITIONING” is an operational/reporting category rather than a fourth enum status.

The same objects continue across slot boundaries. A busy trip does not end because a half-hour ends, a driver idle clock does not reset, and charging/queue membership persists. Final-state counts are snapshots, while starts/completions are flows during the slot. [Sources: config `simulation`, `energy`; `src/fleet/state.py`, `fleet.py`; `src/charging/energy.py`; `production.py`.]

## 9. EMPIRICAL REQUEST GENERATION

**Current code differs from the request's premise of current-slot empirical trip replay.** `ProductionExperiment._request_counts` rounds each nonnegative current-target CNN prediction to an integer using NumPy `rint`; a grid without an empirical origin pool gets zero. `generate_requests` then samples that many intact empirical rows by origin from the **month-wide valid cleaned-trip pool**, with replacement. The current slot determines forecast volume and pricing context; it does not restrict sampling to trips observed in that calendar half-hour.

For a sampled pickup timestamp, subtract the start of its original half-hour bucket. Let this offset be `s` seconds. The arrival mini-slot is:

\[
m=\lfloor s/120\rfloor,\qquad request\_minute=2m.
\]

`m` ranges from 0 to 14. A pickup at 08:17:43 has offset 1,063 seconds, maps to mini-slot 8, and arrives at simulated minute 16. The old historical date is not replayed. Arrival placement consumes no random draw.

A persistent request random-number generator (RNG) is created once, then passed into successive sampling calls. An RNG is a reproducible sequence of pseudo-random draws; resetting it to seed 42 every slot would repeatedly restart that sequence and create unintended repeated sampling patterns. IDs also continue across slots. Customer sampling has its own persistent stream.

Each request retains source OD, source pickup/dropoff timestamps, duration, original distance in miles, kilometre distance, original fare, simulated arrival, offered fare, sensitivity fields, customer outcome, dispatch outcome, assigned vehicle, and reward audit. These let the assembler link pricing to the eventual service outcome. The generated count is **forecast-driven simulated opportunity volume**, not the observed 48-slot TLC count. This distinction limits scientific claims about real-world unmet demand. [Sources: `production.py:_request_counts`, `run_slot`; `generation.py:sample_trip`, `generate_requests`; `src/dispatch/request.py`.]

## 10. REQUEST-LEVEL PRICING

A grid-level price decision cannot distinguish two passengers in the same origin with different destinations, distances, destination attractiveness, and historical base-price context. Production therefore constructs one eight-dimensional (8D) vector and one LinUCB selection per request:

```text
[predicted demand, corrected supply, relevant routing probability,
 destination popularity, trip distance, base price, time, weather]
```

| Position / feature | Source | Scaling | Interpretation and reason |
| --- | --- | --- | --- |
| 1. Predicted demand | Target-aligned frozen CNN at origin | Clipped log transform; reference 45.085255432128896 | High means more predicted local requests; gives market-pressure context |
| 2. Corrected supply | Slot snapshot Idle + Incoming at origin | Same transform; reference 9 | High means more current/near-term local availability; separates demand from feasible supply |
| 3. Relevant routing probability | Origin grid's previous learned five-action distribution | Already [0,1] | Sum probability in directions reducing row/column distance to destination; same-grid OD uses P(STAY); indicates directional compatibility |
| 4. Destination popularity | Current timestamp's destination-grid lagged dropoff category | 0, .25, .50, .75, 1 | High means greater recent destination activity; differentiates destination attractiveness |
| 5. Trip distance | Empirical miles × 1.609344 | Clipped log transform; reference 31.02815232 km | High means a longer trip with different service/energy burden |
| 6. Base price | Resolved historical P_base(weather,Period) | Clipped log transform; reference 25.923249887235002 | Fare scale relevant to offered price and acceptance; not the sampled row's fare |
| 7. Time | Current slot Period | Period / 47 | Position in daily cycle; midnight discontinuity remains |
| 8. Weather | Current hour's WeatherCode | Fixed severity lookup | Categorical weather-condition context; unknown codes fail |

For nonnegative raw value `z` and frozen positive P99 reference `r`, the transform is:

\[
f(z;r)=clip\left(\frac{\log(1+z)}{\log(1+r)},0,1\right).
\]

`clip` limits values to the stated interval; P99 is a reference distribution's 99th percentile. Negative demand is first replaced by zero. The logarithm compresses large differences so one large-unit feature does not dominate the regression. Values above the reference saturate at one, losing some magnitude detail; clipping diagnostics are therefore useful. References are frozen from training/reference data or seeded initial supply, never fitted to Phase 7D results.

For routing, a destination northeast of the origin uses P(NORTH)+P(EAST), not a learned probability of the full passenger route. Weather severity uses codes `{1,2,3}:0`, `{5,7,14}:.25`, `{8,15,21}:.50`, `{9,12}:.75`, `{13,16}:1`. This is the exact pricing lookup, separate from the CNN's raw code channel and from any future elasticity plotting categories.

**README correction:** the older scaler subsection says “only demand and supply” and retains all-status supply wording; its popularity paragraph also calls popularity the eighth feature. Current request code/scaler use four log-scaled fields, corrected supply, popularity fourth, and weather eighth. [Sources: `src/pricing/request_context.py`, `scaler.py`; `config/pricing_context_scaler.json`; README final testing notes.]

## 11. CORRECTED SUPPLY

\[
Supply(g,t)=Idle(g,t)+Incoming(g,t).
\]

`g` denotes an origin GridID and `t` the main-slot start. `Idle` is vehicles currently IDLE in that grid. `Incoming` is passenger-BUSY vehicles with that known destination and an expected completion within **(slot_start, slot_end]**, following existing mini-slot completion semantics. Charging, charging queue, and repositioning are excluded from incoming passenger supply. This is an availability feature, not the exact vehicle-by-vehicle dispatch eligibility test.

The previous all-status count credited busy/charging vehicles at their current grid even when they could not serve there. Corrected supply represents present idle availability plus causally known passenger arrivals, without counting future events that are not yet scheduled. It improves temporal and spatial interpretation but does not guarantee a vehicle will still be idle when a particular passenger arrives. Price contexts use a slot snapshot; dispatch independently checks live state and energy. High supply can moderate scarcity signals, but LinUCB learns its coefficient rather than enforcing a hard-coded negative price relationship. [Sources: `src/pricing/supply.py`; `pricing_dispatch.py`; README §6.14.]

## 12. DESTINATION POPULARITY

Popularity uses **dropoffs grouped by DOGridID and dropoff time**, not pickup demand, forecast demand, or charging-station popularity. At grid `g` and current slot `t`, it averages dropoff counts in the six previous slots:

\[
PopularitySMA(g,t)=\frac{1}{6}\sum_{k=1}^{6}Dropoffs(g,t-k).
\]

`k` is the lag in half-hours; `Dropoffs` is the observed count in that earlier slot. During January warm-up, the denominator is the number of available previous slots instead of six. The current slot is excluded, so its as-yet unrealized activity is not leaked into its own feature. Observed zero counts stay zero; unavailable pre-January history is not invented.

Training/reference global Q20/Q40/Q60/Q80 cutoffs map this moving average to **Very Low, Low, Medium, High, Very High**, encoded **0, .25, .50, .75, 1**. Inclusive upper boundaries and duplicate thresholds are preserved. High categories indicate greater recent destination activity; they do not necessarily indicate profitable service. The category enters pricing directly and can influence future fleet distribution indirectly through which requests are served. It is not a separate direct term in NB11's three-component utility. Static station placement uses whole-month pickup-plus-dropoff ranking and must not be confused with this feature. [Sources: `src/popularity/destination.py`; README §6.14; popularity metadata.]

## 13. LINUCB

LinUCB is a contextual bandit: it chooses one action, observes feedback for that action, and uses the request's features to generalize to later decisions. Here an **arm** is one price multiplier: **0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15**. Respectively these offer 15%, 10%, or 5% below base; the base price; or 5%, 10%, or 15% above base.

\[
P_{dispatch}=aP_{base},\qquad
\theta_a=A_a^{-1}b_a,\qquad
score_a(x)=\theta_a^Tx+\alpha\sqrt{x^TA_a^{-1}x}.
\]

`a` is the fare multiplier; `P_base` is the resolved historical base fare; `x` is the eight-feature request context. Each arm has its own matrix `A_a`, vector `b_a`, and fitted coefficient vector `theta_a`. The first score term is exploitation: predicted scaled served reward. The second is exploration: an uncertainty bonus. **LinUCB alpha = 1.0** scales exploration and is distinct from the price factor, even though some customer APIs call the factor `alpha`.

Initialize each arm with `A_a=I` (identity matrix) and `b_a=0`. For the chosen arm only, a finalized learning reward `r` updates:

\[
A_a\leftarrow A_a+xx^T,\qquad b_a\leftarrow b_a+rx.
\]

`xx^T` records the observed context geometry and `rx` links it to reward. Rejected/unserved requests still provide a zero-reward observation. Cold-start reservations distribute selections across arms until actual feedback exists; subsequent numeric score ties use the seeded RNG. This is not epsilon-greedy random exploration. All selections for a slot precede feedback, explaining near-balanced first-slot arm counts. LinUCB is learning conditional served revenue, not an independently observed causal price-demand curve. [Sources: `src/pricing/linucb.py`; `pricing_dispatch.py`.]

## 14. CUSTOMER PRICE SENSITIVITY

Historical sensitivity is computed offline using pickups **2026-01-01 00:00 inclusive to 2026-01-25 18:30 exclusive**. This frozen pre-cutoff reference is not shifted forward merely because CNN target consumption was corrected to start at 19:00. Trips are grouped by WeatherCode and Period. Valid source rows require finite positive fare, finite positive distance no greater than 100 miles, and valid context.

For each group:

\[
P_{base}=mean(P_i),\quad D_{base}=mean(D_i),\quad
\Delta P_i=\frac{P_i-P_{base}}{P_{base}},\quad
\Delta D_i=\frac{D_i-D_{base}}{D_{base}},\quad
\epsilon_i=\left|\frac{\Delta P_i}{\Delta D_i}\right|.
\]

`P_i` is a trip's historical fare; `D_i` is its distance in miles. `P_base` and `D_base` are that group's means. Delta P and Delta D are relative deviations, not unnormalized currency/mile differences. Epsilon is an absolute ratio of those relative deviations. Observations require absolute distance difference at least **0.01 mile** to avoid division by a near-zero difference at source precision. The procedure retains group means, population/sample SD, counts, and quantiles.

A high epsilon says the row's relative price deviation is large compared with its relative distance deviation. This is the project's historical sensitivity proxy; it should not be called a causal estimate of conventional quantity-demand elasticity from randomized prices. These historical trips do not directly observe passengers' rejected offers.

Runtime draws one epsilon from a Normal parameterized by the selected group's mean and population SD, **lower-truncated strictly above zero, with no upper cap**. A normal distribution describes spread around a mean; truncation removes invalid nonpositive sensitivity while preserving heterogeneous positive values. It is not sampling and then clipping all negatives to a common constant. Zero SD uses the valid positive mean. No upper clipping/winsorization has been added. Epsilon controls the magnitude of the signed Pmax adjustment (§15). [Sources: `historical_sensitivity.py`; `customer_sensitivity.py:sample_positive_truncated_normal`; training cutoff constants.]

## 15. CUSTOMER P_MAX AND ACCEPTANCE

The exact implemented formula is:

\[
P_{max}=P_{base}+\left(\frac{D-D_{base}}{D_{base}}\right)\frac{P_{base}}{\epsilon_{customer}}.
\]

`P_base` and `D_base` come from the same resolved historical parameter row; `D` is the sampled request's distance **in miles**, matching D_base; `epsilon_customer` is its single positive runtime draw. Pmax is this model's maximum acceptable fare in the historical fare's monetary unit. The relative distance difference remains **signed**. Longer-than-base trips add to Pmax; shorter trips subtract; equal distance gives Pmax=P_base. Large epsilon makes either adjustment smaller. It is therefore inaccurate to describe higher epsilon as universally decreasing Pmax: for shorter trips it raises Pmax back toward base.

If a short trip has a sufficiently small epsilon, its negative adjustment can exceed P_base and yield **Pmax ≤ 0**. The code accepts finite nonpositive Pmax as a model result; it does not silently floor it. Since offered fares are positive, those customers reject.

Acceptance is exactly **P_dispatch ≤ Pmax**, including equality. It is a deterministic comparison conditional on the random epsilon draw; there is no additional Bernoulli probability in this production path. Acceptance only authorizes a dispatch attempt; a customer can accept yet have no eligible/contending driver.

**Base-fare contradiction resolved:** production historical acceptance returns `P_dispatch = factor × historical P_base(W,T)` and the dispatcher stores that value as `offered_fare`. The sampled trip's `base_fare` is preserved for audit, but it is not multiplied in this production mode. README's sentence “empirical base fare multiplied by the selected factor” describes the other/legacy branch, not current Phase 7D behavior. [Sources: `customer_sensitivity.py:maximum_price`, `evaluate_resolved`; `pricing_dispatch.py:_run_request_pricing_dispatch_slot`.]

## 16. SENSITIVITY HIERARCHICAL FALLBACK

The exact production lookup order is **exact WeatherCode × Period → Period pooled across weather → WeatherCode pooled across periods → Global**. The model stops at the first usable parameter record, then reuses that record for context, epsilon sampling, and offered/Pmax prices. This resolve-once approach prevents inconsistent bases within one request.

The exact artifact has 243 rows; the fallback artifact has 62. Missing combinations are expected with limited January weather coverage. A fail-on-missing-pair mode would interrupt an otherwise valid runtime slot. The hierarchy allows operation without using held-out customer observations to fit missing parameters.

Pooled rows are **recomputed from pooled valid historical trips**: pooled P_base/D_base change the deviations, the valid distance-difference population, and the epsilon ratios. An average of group epsilon means or SDs would not recreate those quantities; averaging SDs also loses between-group variation. High reliance on pooled levels indicates weaker context specificity, not necessarily a computational failure. The per-request lookup level is audit information; compact Phase 7D tables do not preserve every individual lookup for later causal analysis. [Sources: `customer_sensitivity.py:resolve_parameters`; `historical_sensitivity.py`; fallback build script.]

## 17. REWARD MODEL

For request `i`, the raw economic feedback is:

\[
r_i^{raw}=\begin{cases}P_{dispatch,i}&\text{accepted and assigned/served}\\0&\text{rejected or accepted-unserved.}\end{cases}
\]

`P_dispatch,i` is its recorded offered fare, and “served” means assigned in the simulator, not necessarily that passenger travel has completed by the final boundary. Raw revenue is the sum of these rewards. LinUCB instead receives:

\[
r_i^{learn}=r_i^{raw}/REWARD\_REF,\quad
REWARD\_REF=25.923249887235002\times1.15=\mathbf{29.81173737032025}.
\]

The first factor is the frozen training-reference P99 historical base price; 1.15 is the maximum arm. Scaling places predicted rewards on a more comparable scale to the uncertainty bonus. There is **no clipping** of this learning reward, so a reward above one is possible. Raw revenue remains unchanged as an accounting unit for the same realized assignments.

Phase 6A showed a scale imbalance: at its final checkpoint the median absolute exploitation/exploration ratio was about **23.29**, P95 **572.62**, and maximum **834.23**. Phase 6B introduced the reference scale; its corresponding diagnostics were about **1.45**, **17.11**, and **22.57**. These earlier runs also show different served outcomes because changed learning can change chosen arms. They demonstrate the numerical reason for scaling, not a valid final performance comparison: both used the old 18:30 window and earlier integration.

Phase 7D has **106,729 selections and 106,729 updates**, raw revenue **513,292.39943358075**, and total learning reward **17,217.795563454834**. The selected arm gets exactly one finalized update per generated request. `config/pricing_reward.json` still describes legacy normalized accepted revenue including unserved acceptances; production explicitly selects served revenue and training-reference scaling instead. Do not use that legacy JSON to interpret Phase 7D. [Sources: `pricing_dispatch.py`; `src/pricing/reward.py`; Phase 6A/6B summaries; Phase 7D summary.]

## 18. DRIVER CONTENTION DISPATCH

Accepted requests are processed first-come-first-served (**FCFS**) by `(request_time, request_id)` within the mini-slot chronology. For each request, enumerate drivers in the origin and direct canonical neighbour grids. Eligible drivers must be IDLE, not in a charging/queue action, not at/below the charging trigger, and have enough energy for the empirical passenger trip. BUSY passenger and repositioning vehicles cannot participate.

Each eligible driver is evaluated against a best outside option:

\[
U_{request}\ge U_{best\ alternative},\qquad
U_{best\ alternative}=\max_{a\in valid\ actions}U_a.
\]

`U_request` is the request-specific adapter utility (§19); `U_a` is that driver's utility for STAY or a valid directional NB11 option. The maximum is what the driver could achieve by declining this request under the current modeled alternatives. Equality is enough to contend. “Contend” means expressing willingness to take the offer, not being assigned.

The platform chooses contenders by **shortest pickup centroid distance → highest request utility → lowest vehicle ID**, using the tuple ordering in current `dispatch.py`. Same-grid pickup distance is zero, so a same-grid contender outranks a farther one. The remaining tie keys make assignments deterministic. Assignment is immediate; the vehicle becomes BUSY and later requests cannot reuse it.

There are two terminal unsuccessful cases: **A, zero eligible drivers**, and **B, eligible drivers exist but zero contend**. A represents feasibility/local availability failure; B represents modeled driver refusal despite feasibility. They require different interpretation. No passenger queue, repeated search in later mini-slots, or wider-radius retry is implemented. Phase 7D assigned **9,299 same-grid** and **18,668 neighbour** requests. Pickup geometry affects ranking/utility, but empirical passenger duration and distance determine travel/energy; a separate physical pickup leg is not added by this dispatcher. [Sources: `dispatch.py:eligible_local_vehicles`, `dispatch_requests`; `contention.py`.]

## 19. PASSENGER REQUEST UTILITY ADAPTER

Contention reuses NB11's utility functions through a distinct request-specific input adapter. It must not be confused with production driver profiles or the NB11 DOD penalty.

| Input | Exact request adapter | Meaning and downstream role |
| --- | --- | --- |
| Price preference argument | Offered request fare P_dispatch | Evaluated against origin-grid fare mean/SD using the increasing price utility; higher offered fare generally increases this component until saturation |
| Wait preference argument | `1 − clip(pickup_distance / pickup_reference,0,1)` | Geometry-derived number in [0,1]; pickup_reference is maximum canonical neighbour centroid distance; passed into the existing wait utility |
| Degradation argument | `clip((trip_distance_km × .15)/75,0,1)` | Passenger energy requirement divided by full battery capacity; larger energy burden reduces charging utility |

In these expressions, `pickup_distance` and its reference have the same EPSG:2263 coordinate unit; `trip_distance_km` is the empirical converted distance; .15 is kWh/km; and 75 is battery capacity in kWh. Clipping prevents a normalized burden outside [0,1]. Each resulting utility contributes one-third to U_request, which is compared with the driver's best alternative.

**Interpretation caveat from current code:** the pickup adapter gives 1 for same-grid pickup and a lower number for farther pickup, yet passes it as `wait_preference` into a *decreasing* function calibrated against driver wait statistics in minutes. It does not convert pickup distance to minutes. Consequently, do not claim the implemented wait component always penalizes farther pickups; ranking still explicitly favors shorter pickup distance. This dimension/monotonicity question deserves methodological review (§50), not a silent change here.

The trip-energy ratio is neither measured battery wear nor the production NB11 normalized recharge-depth penalty. NB11 alternatives use persistent synthetic price/wait traits and projected remaining battery energy; the passenger request uses offered fare, pickup proxy, and passenger energy burden. [Sources: `src/dispatch/contention.py:evaluate_request_contention`, `pickup_wait_preference`, `normalized_trip_energy_burden`; `baseline.py:wait_utility`.]

## 20. NB9 OPERATIONAL STATISTICS

NB9 turns realized operations into grid-level context for NB11 and the local learner. It maintains two distinct streams:

**A. Fare statistics:** served dispatch fares attributed to pickup grids. Counts show observed activity, means indicate fare scale, and population standard deviations describe within-slot variability. Historical EWMA fare fields supply context where current observations are absent.

**B. Driver idle-wait statistics:** completed IDLE episodes recorded when a driver receives an assignment, attributed to the driver's waiting grid. Counts indicate how much observed evidence exists; means and SDs summarize wait duration. Current or smoothed history informs routing utility, and no-history candidates get only a neutral utility fallback.

For observed values `v_1,...,v_n`, population mean is their sum divided by `n`, and population SD is the square root of the mean squared deviation from that mean (denominator `n`, not `n−1`). High SD means more dispersion, not necessarily more observations. Empty samples have absent mean/SD; they are not zero-minute or zero-fare observations. NB9 also carries charging availability and queue-wait context where supplied. These fields enter the 87D state, although the explicit NB11 charging component is based on energy/charging time and degradation rather than a direct station-queue term. [Sources: `src/simulation/statistics.py`; `baseline.py:build_grid_routing_features`, `candidate_utility`.]

## 21. NB9 FARE BOOTSTRAP

`nb9_fare_bootstrap_2026_01_25_1830.parquet` covers **1,213 grids: 1,028 grid-specific historical priors + 185 global fallbacks**. It uses finite positive pre-cutoff fares by PUGridID, with the same exclusive January 25 18:30 boundary. Each grid gets a historical mean and **population SD**; grids with no usable local history get the pooled historical values.

The prior initializes only fare EWMA fields. It does not increment runtime fare_count, create a served passenger, or populate driver wait history. Historical count remains separately auditable. Once a slot has served fares, each fare summary is smoothed using:

\[
EWMA_{new}=0.70\,EWMA_{old}+0.30\,statistic_{current}.
\]

EWMA means exponentially weighted moving average. `statistic_current` is the observed slot mean or slot SD, and the two have separate smoothed fields. Alpha **0.30** gives recent observations 30% weight while carrying 70% of the previous state. This is smoothing of means/SDs, not recomputation of an exact pooled lifetime variance. A slot without an observation carries its previous EWMA forward. Higher fare means alter NB11's reference range; they do not necessarily monotonically raise a fixed driver's price utility, since the formula compares the trait with that range. [Sources: `routing/production.py:build_fare_bootstrap`, `initialize_nb9_fare_prior`; `statistics.py`; bootstrap metadata.]

## 22. DRIVER IDLE-WAIT TRACKING

The lifecycle is **vehicle becomes IDLE → new timer zero → add two minutes for each completed mini-slot still IDLE → dispatch records completed wait**. A driver dispatched immediately can legitimately record zero minutes. A driver receiving a neighbour-grid request records its wait against the grid where it was actually waiting, not automatically the passenger origin.

The timer continues across main-slot boundaries and NB11 STAY decisions. Passenger BUSY time, charging, queue time, and repositioning travel are not driver idle waiting. These transitions stop/abandon the active idle episode; they do not accrue those durations and then resume one continuous old episode. Passenger or charging completion starts a new zero-minute episode. A reposition abandons its origin episode without reporting it as completed; arrival starts the destination episode.

The earlier instantaneous-reposition defect moved the driver to its destination immediately and allowed the destination idle clock to start too early. Current movement occupies **12 minutes** in BUSY repositioning state. That restores dispatch unavailability and starts destination waiting only on arrival. Completed waits now reflect a real simulated available interval.

These are **driver waits, not passenger waits**. They are also a selected sample: only waits ending in dispatch are recorded. Drivers still idle at the final boundary, or episodes abandoned for repositioning/charging, do not appear as completed waits. The long-tail summary therefore does not measure the full fleet's censored/uncompleted waiting exposure. [Sources: `fleet.py`, `state.py`; `dispatch.py:DriverWaitObservation`; `baseline.py:execute_reposition`; README §6.7.]

## 23. EMPTY WAIT-HISTORY FALLBACK

NB11 uses **U_wait = 0.5** only when a candidate has neither a usable current mean/SD pair nor a usable EWMA mean/SD pair. It is neutral because it is the midpoint of the normalized [0,1] utility range, avoiding automatic best/worst treatment of an unseen grid.

This is a decision-time fallback, not an observation of 0.5 minutes or a fabricated distribution. It never updates NB9 counts, means, SD, or EWMA. As real completed waits arrive, the candidate uses the applicable current/history utility instead. High fallback share means more routing evaluations lack observed wait evidence; a declining share shows growing usable coverage, with the candidate population itself also changing. [Sources: `baseline.py:candidate_utility`; `production.py:_build_report`.]

## 24. DRIVER PROFILES

There are **5,000 persistent seed-42 profiles**, one per vehicle. Let `mu_f` and `sigma_f` be the mean and population SD of valid positive pre-cutoff historical fares. Price preference is drawn **Uniform(max(0,mu_f−sigma_f), mu_f+sigma_f)**; wait preference is drawn **Uniform(0,30 minutes)**. Uniform means all values within the interval are equally likely, not that all drivers have the same trait.

Price traits are therefore informed by a historical fare distribution but are not sampled directly from identifiable drivers' past choices. Both traits are **synthetic project assumptions**. Fixing them across slots represents persistent heterogeneity; resampling them every slot would confound behavior changes with changing personalities.

The 30-minute upper bound limits the preferred-wait trait, not the idle timer. Actual idle waiting can exceed 30 minutes indefinitely until another state transition, explaining why the completed-wait tail can reach hundreds of minutes. The profile artifact's vehicle IDs must exactly cover the runtime fleet. [Sources: `routing/production.py:generate_driver_profiles`, `valid_training_fares`; profile artifact/metadata; README §6.11.]

## 25. NB11 UTILITY ROUTING

NB11 chooses actual end-of-slot behavior for IDLE vehicles that do not require charging. Actions have fixed order **STAY, NORTH, EAST, SOUTH, WEST**. A valid-action mask is a set of booleans excluding absent canonical neighbours; it prevents impossible actions. Each valid candidate supplies fare/wait reference statistics and operational state.

For nonzero SD, the component equations are:

\[
U_{price}=clip\left(\frac{p-(\mu_p-\sigma_p)}{2\sigma_p},0,1\right),\quad
U_{wait}=clip\left(\frac{\mu_w+\sigma_w-w}{2\sigma_w},0,1\right),
\]
\[
T(E)=60\frac{75-E}{30\times0.90},\quad
U_{charge}=clip\left(clip(1-T(E)/T(15),0,1)-d_a,0,1\right),
\]
\[
U_{total}(a)=\frac{U_{price}(a)+U_{wait}(a)+U_{charge}(a)}{3}.
\]

`p` and `w` are the driver's fixed price and wait traits; `mu_p,sigma_p` and `mu_w,sigma_w` are candidate-grid current mean/SD, falling back to EWMA. `E` is current battery energy in kWh, `T(E)` is minutes to full at effective 27 kW, `T(15)` is the threshold-to-full reference duration, and `d_a` is the normalized action-dependent degradation penalty (§26). Action `a` identifies STAY or one valid move. Current energy enters charging-time utility; action-projected energy enters degradation. These are distinct inputs.

Price utility increases with its preference argument within the candidate range; wait utility decreases with its preference argument; charging utility rewards shorter recharge time and penalizes degradation. High total means a more attractive modeled option. Equal weights avoid giving one component a larger explicitly chosen coefficient, but saturation and differing input distributions still affect influence. With zero fare SD, price utility is 0 below the mean and 1 otherwise; zero wait SD gives 1 at/below the mean and 0 above. No usable wait history invokes §23.

NB11 chooses the largest valid total; fixed action order resolves exact ties, favoring STAY when tied. Its output is an action and audit component values, not a neural prediction, Q-value, or reinforcement-learning reward. Predicted demand and supply are present in the state, but the direct utility equation contains only the three components shown. Do not invent an additional demand-seeking term. [Sources: `src/routing/baseline.py:price_utility`, `wait_utility`, `candidate_utility`, `select_action`.]

## 26. NB11 BATTERY DEGRADATION

The code attributes its DOD-related source formulation to the supervisor-cited Chauhan & Jain V2G/G2V paper, *Scheduling of Electric Vehicles Power in V2G and G2V Modes Using an Improved Charge/Discharge Opportunity-Based Approach*. DOD means depth of discharge. The source-form implementation in `battery_degradation_cost` is:

\[
C_{level}=\frac{C_{investment}}{2LQ\Delta DOD},\qquad
C_{DOD}=C_{level}(t_cP_c+t_dP_d).
\]

`C_investment` is battery investment cost; `L` is battery life cycles; `Q` is capacity; `Delta DOD` is the specified depth increment; `t_c,t_d` are charging/discharging durations; `P_c,P_d` are their powers. Duration/power units must be compatible so their products represent energy. `C_level` converts energy throughput to the source DOD-related cost. This documents the cited equation as implemented; it does not imply that complete physical aging parameters are estimated in this production run.

Production keeps the recharge-energy proportional component and normalizes it by the recharge span from 20% SOC to full. The proportional cost coefficient cancels:

\[
d_a=clip\left(\frac{75-E_{projected,a}}{75(1-.20)},0,1\right)
=clip\left(\frac{75-E_{projected,a}}{60},0,1\right).
\]

`E_projected,a` is energy after candidate movement; 75 kWh is capacity, 20% is the 15 kWh charging trigger, and 60 kWh is the maximum reference recharge span. STAY uses current energy; MOVE uses current energy minus **3 km × .15 kWh/km = .45 kWh**. Before clipping, MOVE's penalty is .45/60 = **.0075** larger. High values penalize low remaining energy in NB11 charging utility; zero corresponds to full projected energy, and one to projected energy at/below the trigger.

This is a bounded preference proxy, **not measured state-of-health loss, dollars of realized battery damage, or a lifetime prediction**. The generic source helper includes a separate temperature-dependent term; production `normalized_dod_degradation_penalty` does not use it. Weather in pricing/CNN must not be described as weather-dependent battery aging. [Sources: `baseline.py:battery_degradation_cost`; `routing/production.py:normalized_dod_degradation_penalty`, `RuntimeProductionUtilityInputs`; README §6.11.]

## 27. REPOSITIONING

Each valid MOVE uses the frozen operational assumption **3 km at 15 km/h**:

\[
t_{move}=60(3/15)=12\text{ minutes},\qquad E_{move}=3\times.15=.45\text{ kWh}.
\]

The factor 60 converts hours to minutes; .15 is energy consumption per kilometre. The fixed 12 minutes is within the 30-minute feasibility limit. These are assumed operational distances, not measured road-network paths or verified grid-centroid kilometres (§4).

At movement start energy is deducted once and the vehicle becomes BUSY with a reposition destination and remaining travel time. Its current-grid location changes on completion, not immediately at decision time. It cannot dispatch, charge, or reposition again while moving. Destination idle waiting begins only at arrival; origin waiting is abandoned without a fake completion. STAY neither spends this movement energy nor resets an existing idle clock.

Starts count decisions initiating moves; completions count actual arrivals; the in-transit count is a boundary snapshot. These outputs diagnose availability costs and state continuity, and movement changes where supply appears in subsequent slots. [Sources: `baseline.py:execute_reposition`; `fleet.py`; `config/config.yaml:routing`.]

## 28. NB12 LOCAL LEARNING

NB12 is a local supervised learner for each vehicle. Its **87D** state has two vehicle values (current GridID and energy), plus **five action blocks × 17 values**:

```text
valid, grid_id, predicted_demand,
supply_total, supply_idle, supply_busy, supply_charging,
mean_fare, std_fare, ewma_fare, ewma_std_fare,
mean_wait, std_wait, ewma_wait, ewma_std_wait,
charging_available, charging_wait
```

Invalid actions have zero blocks and a separate false mask. Missing charging availability on a valid candidate is encoded as −1. This fixed order gives local models compatible parameter meanings; the 87D representation is distinct from the scaled 8D pricing vector.

The network is **87 → 64 ReLU → 32 ReLU → 5 logits**. A logit is an unnormalized score. Masked softmax converts valid scores `z_a` to probabilities:

\[
P(a\mid s)=\frac{\exp(z_a)}{\sum_{b\in valid(s)}\exp(z_b)},\quad
Loss=-\log P(a_{NB11}\mid s).
\]

`s` is an encoded routing state; `a,b` are action indices; `a_NB11` is the chosen NB11 label. Invalid actions receive zero probability. The loss is large when the model gives the actual NB11 action little probability, so training makes it better imitate utility-selected behavior. It is supervised classification, **not reinforcement learning** with delayed rewards or Bellman targets.

Training uses **Adam, learning rate .001, buffer capacity 1,000, batch 32, one local epoch**, at most once per main slot. An epoch is one pass over the usable local buffer; Adam is an adaptive gradient optimizer. Eligible NB11 actors create one new state/action observation per slot. Clients without new observations skip training for that slot. Buffers persist when common weights are redistributed, allowing historical local observations to influence updates. Production models start from identical frozen common weights; independently randomized networks would make direct parameter averaging poorly aligned. [Sources: `src/routing/learning.py`; `main_slot.py`; config `routing_learning`.]

## 29. NB13 FEDERATED LEARNING

FedAvg forms one common model from locally trained models. For tensor/parameter position `j`:

\[
\theta^{global}_j=\frac{\sum_{i\in participants}n_i\theta_{i,j}}{\sum_i n_i}.
\]

`i` is a participating vehicle, `theta_i,j` its local parameter, and `n_i` its declared new-observation sample count. Higher weight gives a client proportionally more influence. NB13 validates state dimension, action order, architecture version, tensor shapes, finite weights, and nonnegative integer counts before averaging. Zero-sample exports are excluded; no participants means no fabricated update.

**Production-specific weighting detail:** `main_slot.py` includes only vehicles with a new NB11 observation and explicitly sets each export's `sample_count=1`. There is one new action per participating vehicle per slot. Thus the general algorithm is sample-count weighted, but current per-round production averaging is **equal across the new-observation participants**, not proportional to cumulative buffer length. Local training can still use each retained buffer.

One synchronous round occurs per 30-minute slot, and updated global weights are redistributed to every local model. Only weights, IDs, sample counts, and compatibility metadata form export payloads; raw local states/actions remain in local buffers. This is a simulated locality boundary inside one process, not a demonstrated deployed privacy protocol, secure aggregation system, or distributed communication experiment.

The behavioral chain is **NB11 generates actions → NB12 learns those labels locally → NB13 aggregates global tendencies → masked policy probabilities inform pricing**. The common network does not replace NB11's actual movement decision. [Sources: `src/routing/federated.py`; `main_slot.py:exports`; `learning.py:export_local_update`.]

## 30. FIRST-SLOT ROUTING INITIALIZATION

Before any local observation exists, pricing receives **uniform probability over each grid's valid actions**. With all five actions valid, each has .20; with only STAY plus two neighbours, each valid action has 1/3 and absent directions have zero. This avoids treating arbitrary untrained network logits as meaningful routing knowledge.

After slot 1 trains and federates, slot 2 pricing consumes the resulting grid distributions. For grids with eligible policy states, the assembler averages masked vehicle probabilities; a grid without eligible states carries forward its previous vector, or the initial vector if no previous one exists. Therefore “global routing probability” is a grid-context aggregation, including fallback, not one universal five-number vector emitted independent of state.

The saved slot-1 P5 checkpoint is **after the first federation and next-grid-policy construction**, not the initial uniform distribution used to price slot 1. This resolves the apparent conflict between uniform initialization and saved slot-1 P(STAY) about .5604. [Sources: `production.py:_uniform_valid_grid_probabilities`, `_build_report`; `src/simulation/grid_policy.py`; `main_slot.py`.]

## 31. PRODUCTION ASSEMBLER

`src/simulation/production.py` is the authoritative assembler and `scripts/run_production_experiment.py` is its command-line entry point. The entry point accepts slot count, seed, and output directory, invokes the continuous experiment, and writes compact results. It does not rebuild artifacts or retrain the CNN.

The assembler loads canonical grid/neighbours, cleaned trips, weather, frozen predictions/times/model, lagged popularity, sensitivity and fallback, pricing scaler, profiles, fare bootstrap, common routing initialization, and stations. Frozen hashes for explicitly pinned artifacts are checked; all required paths must exist, and a source manifest records hashes and schema coverage. A SHA-256 hash is a content fingerprint used to detect changed files; it is not evidence that a model is scientifically correct.

Validation checks include 1,213 grid coverage, prediction/target alignment, finite demand, compatible policy weights, complete runtime contexts, and request/fleet/learning reconciliation. It preserves separate RNG streams, fleet/energy, LinUCB matrices, NB9 histories, charging, timed repositioning, local buffers, common weights, and next-slot probabilities. Missing or incompatible authoritative inputs fail immediately; synthetic test fixtures are not silently substituted.

**Configuration distinction:** YAML retains legacy default dispatch/pricing/arrival selectors. Production passes explicit overrides: historical sensitivity, hierarchical fallback, request_8d, idle_plus_incoming, served_dispatch_revenue, training_reference, and driver_contention. Empirical generation directly uses its persistent sampler. Reading only YAML would therefore misidentify Phase 7D behavior.

**New read-only boundary finding:** `run_slot` calls `_demand(next_timestamp)` and `_popularity(next_timestamp)` unconditionally before processing the current slot. At the 298th target, current time is January 31 23:30 and next time is February 1 00:00. The saved forecast targets end at January 31 23:30, and popularity has January coverage only. `_demand` raises on a missing target; no terminal branch supplies this next-slot context. Thus the advertised full 298-slot entry-point run is **not executable as currently written** through that final slot. This is a static code/artifact conclusion, not a simulation rerun. It does not invalidate Phase 7D's 48 completed slots. Terminal-boundary handling must be addressed in separately authorized engineering work; this explanation does not invent a forecast or change the evaluation window.

## 32. VALIDATION HISTORY

| Stage | Purpose and interpretation |
| --- | --- |
| Unit tests | Check isolated contracts: grid IDs, temporal mapping, vehicle transitions, pricing accounting, utility, masks, and compatible model aggregation. Small deterministic fixtures make failures localizable. |
| Two-slot smoke | Check initialization followed by a real next-slot boundary; persistent state and RNG cannot be established from an isolated slot alone. |
| Eight-slot integration | Exercise repeated trips, statistics, routing, and learning; reveal integration errors missed by small fixtures. |
| Phase 6A 48-slot request-pricing diagnostics | Check per-request context, sampling, update counts, and raw-reward score imbalance; older timestamp alignment means engineering evidence only. |
| Phase 6B 48-slot reward scaling | Check frozen training-reference reward scale and exploration/exploitation balance; not a final proposed-model comparison. |
| Phase 7B driver contention, eight slots | Check eligible/contender distinctions and integrate request utility against outside options; compare diagnostic dispatch paths. |
| Phase 7C production work / old 7C4 preflight | Connect authoritative artifacts, initialization, timed movement, fare/wait state, and learning. Old 18:30 start is superseded. |
| CNN timestamp audit / corrected 7C6 preflight | Verify prediction i corresponds to input timestamp +30 minutes and establish the 19:00 start. |
| Phase 7D, 48 slots | Validate one continuous 24-hour, 5,000-vehicle trajectory and publish compact outputs plus reporting package. |

Larger windows reveal consequences that need time: long driver waits, charging after accumulated energy use, model aggregation drift, and delayed arrivals. Passing a smoke test cannot prove these behaviors remain coherent for a day. Likewise a day cannot exercise the very last January forecast boundary (§31).

The README and dated package report **258/258 passing tests**. This documentation task did not run tests or simulations; the number is a recorded regression result, not a new execution claim. Exact historical test logs for every smoke milestone were not reconstructed: **NOT VERIFIED FROM CURRENT AUTHORITATIVE SOURCE** where no persisted stage-specific transcript exists. Current Phase 6A/6B/7B/7C6/7D summaries and code supply the described engineering chronology.

## 33. MAJOR PROBLEMS DISCOVERED AND CORRECTED

| Problem | Why it mattered | How it was discovered / evidenced | Correction in current implementation | Scientific consequence |
| --- | --- | --- | --- | --- |
| All-status pricing supply | Counted unavailable vehicles at wrong operational locations | Supply contract audit and tests; README Phase 4 account | Idle + passenger Incoming | More interpretable availability context |
| Grid-level pricing context | Ignored OD/distance variation within origin | Request-context integration diagnostics | Fixed request-specific 8D vector and one selection/update | Unit of price feedback is a request |
| Sensitivity/fallback gaps | Missing weather/Period pairs halted evaluation or tempted ad hoc values | Phase 6A missing-pair diagnostics; fallback tests | Training-only exact→Period→Weather→Global, resolve once | Contexts operate without fitting held-out customers |
| Reward scale imbalance | Raw currency exploitation dwarfed uncertainty | Phase 6A score diagnostics, Phase 6B comparison | Divide raw served fare by frozen 29.81173737032025 | Learning scale changes without relabeling gross revenue |
| Driver contention missing | Feasible drivers were assigned without willingness comparison | Phase 7B contention validation; dispatch tests | Utility threshold and deterministic contender ranking | Unserved demand splits into feasibility and behavioral cases |
| NB9 wait semantics | Passenger or boundary-reset timing misrepresented driver idle history | Driver-wait lifecycle tests and corrected README | Persistent driver IDLE episodes, correct waiting-grid attribution | Wait metrics now describe completed driver availability spells |
| Instantaneous repositioning | Destination availability/wait began too early | Timed movement and wait tests | BUSY movement for 12 minutes | Movement has an explicit availability cost |
| Driver preference initialization | Fabricated/changing traits obscured behavioral interpretation | Production profile contract and artifact metadata | Fixed pre-cutoff-based synthetic price and Uniform(0,30) wait traits | Reproducible heterogeneity, still not measured driver preferences |
| Fare-stat initialization | Empty/fabricated fare statistics distorted utilities | Bootstrap coverage audit | 1,028 grid priors +185 pooled priors; no runtime count increment | First-slot fare context has documented provenance |
| NB12 common initialization | Unaligned random local parameters undermine weight averaging | Production initialization compatibility tests/artifact | Identical frozen common weights | FedAvg starts from a common parameter representation |
| First-slot routing signal | Random untrained logits were treated as learned evidence | Initialization policy audit | Uniform over valid actions for first-slot pricing | Neutral initial signal with explicit post-round timing |
| Degradation normalization | Raw costs are incompatible with normalized utility | Utility range and DOD contract tests | Threshold-to-full normalized projected recharge depth | Bounded comparable penalty, not physical lifetime proof |
| Production assembler gap | Disconnected demonstrations did not prove an integrated trajectory | Production-loading/integration validation | Authoritative loader and persistent orchestration with fail-fast checks | Phase 7D is traceable to frozen inputs |
| RNG reset across slots | Repeated draw sequences could create artificial patterns | Persistent-stream checks and reproducibility state | Carry request/customer RNG state across boundaries | Deterministic trajectory without per-slot reseeding |
| CNN off-by-one timestamp | Forecasts consumed 30 minutes early | Input-target audit against saved arrays | Target=input+30 min, aligned 19:00 start | Old preflight excluded from final scientific comparison |

This table describes verified current corrections, not an invented chronology of particular failing test executions. Remaining current contradictions are **not marked solved**: grid physical units (§4), request adapter wait semantics (§19), and final-target lookahead (§31). Stale README/config prose is distinguished from runtime behavior rather than edited in this task.

## 34. PHASE 7D — 48-SLOT RUN

Phase 7D ran **2026-01-25 19:00 inclusive to 2026-01-26 19:00 exclusive**, using **48 half-hour slots, 5,000 vehicles, seed 42**. It covers every Period value once, across portions of two calendar dates. January dates are the simulated timeline; September 8 is the reporting-package date.

The purpose was to prove engineering continuity across pricing, customer response, contention dispatch, driver waiting, energy/charging, timed repositioning, utility labeling, local learning, and federation with authoritative artifacts. It was not designed as a controlled proposed-versus-baseline experiment.

The machine output is `results/validation/phase7d_48slot_final_integrated_seed42/`; the human-readable package is `results/validation/2026-09-08_48slot_run/`. Recorded runtime is **3,377.1279648329946 seconds**, about **56.29 minutes**, with **31.603481156592167 requests/second** (generated requests divided by elapsed runtime). Throughput is an engineering performance diagnostic tied to this environment, not a scientific fleet-performance metric. [Sources: Phase 7D `summary.json`, `analysis.json`, `per_slot.csv`; dated `summary.json`.]

## 35. REQUEST/REVENUE OUTPUTS

| Output | Value | Definition / calculation | Interpretation and downstream meaning |
| --- | ---: | --- | --- |
| Generated G | 106,729 | Sum of forecast-driven sampled requests | All offered opportunities; denominator for acceptance/service coverage and LinUCB accounting |
| Accepted A | 61,863 | Offers satisfying P_dispatch≤Pmax | Customer willingness under the assumed model; dispatch input, not guaranteed rides |
| Rejected R | 44,866 | G−A | Customer refusal; zero reward and no dispatch attempt |
| Served S | 27,967 | Accepted requests assigned a driver | Produces fare reward, passenger BUSY state, energy use, and a completed driver wait |
| Accepted-unserved U | 33,896 | A−S | Willing customers without assignment; zero economic/learning reward |
| Raw revenue | 513,292.3994 | Sum of recorded P_dispatch over S assignments; full precision 513,292.39943358075 | Gross simulated fare revenue; not net profit or completed-trip cash realization |

The exact funnel reconciles **G=A+R** and **A=S+U**. Here G,A,R,S,U are the counts defined above; neither funnel stage has an implicit different population.

| Rate | Numerator / denominator | Result | Why it matters |
| --- | --- | ---: | --- |
| Acceptance | 61,863 / 106,729 | **57.96%** | Willingness to accept among all generated offers |
| Served/generated | 27,967 / 106,729 | **26.20%** | Overall opportunity coverage after both customer and dispatch filters |
| Served/accepted | 27,967 / 61,863 | **45.21%** | Dispatch realization among customers who agreed |

Each percentage is the stated ratio ×100. A higher service rate means more coverage on the same denominator; a higher acceptance rate alone can coexist with lower revenue or worse dispatch realization. Counts also respond to opportunity volume and the forecast generator. Revenue feeds LinUCB after scaling and served fares update NB9; headline aggregates themselves are reports, not extra feedback updates. [Sources: raw summary, analysis totals, summed per_slot.csv, dated core_summary.csv and summary.csv.]

## 36. WHY UNSUCCESSFUL DISPATCH IS HIGH

| Accepted outcome | Requests | Share of all 61,863 accepted | Share of 33,896 unsuccessful |
| --- | ---: | ---: | ---: |
| Served | 27,967 | 45.21% | Not applicable |
| Zero eligible | 23,445 | **37.90%** | **69.17%** |
| Eligible but zero contenders | 10,451 | **16.89%** | **30.83%** |
| All accepted-unserved | 33,896 | **54.79%** | 100% |

Each accepted share divides its row count by 61,863; each failure share divides by 33,896. The two failure counts sum exactly to accepted-unserved. These are **observed facts from the counters**.

Reasonable mechanisms for zero eligibility include the local origin-plus-neighbour radius, passenger BUSY vehicles, repositioning unavailability, charging/energy exclusions, and spatial mismatch between vehicles and requests. A globally large IDLE count does not establish local feasible availability. High NB11 STAY may sustain a spatial distribution rather than actively rebalance it. For eligible-but-zero-contender requests, the direct observed mechanism is failure to meet the modeled outside-option threshold.

These outputs do **not** apportion the 23,445 zero-eligible cases among radius, energy, charging, BUSY time, and mismatch, or prove how much STAY caused any failure. Nor does the second category validate real drivers' refusal behavior. A causal attribution would require more specific counters or controlled comparisons; none are invented here. [Sources: `analysis.json:contention`; `per_slot.csv`; `dispatch.py`.]

## 37. LINUCB OUTPUTS

| Factor | Selection count | Share of 106,729 selections |
| --- | ---: | ---: |
| .85 | 65,661 | 61.52% |
| .90 | 4,610 | 4.32% |
| .95 | 22,526 | 21.11% |
| 1.00 | 3,808 | 3.57% |
| 1.05 | 2,025 | 1.90% |
| 1.10 | 3,128 | 2.93% |
| 1.15 | 4,971 | 4.66% |

Each share is arm count divided by all selections; rounding makes displayed percentages sum to slightly more than 100%. The two discount arms .85 and .95 dominate this trajectory. This suggests LinUCB found their conditional served-reward predictions attractive given its accumulated evidence and uncertainty bonuses. Lower prices can improve customer acceptance, but can also reduce driver willingness; the learner sees only the eventual reward.

Frequent .85 selection is not automatically a bug: the lowest fare can yield larger expected served revenue than higher offers under a willingness model. Conversely, its frequency does not prove .85 is universally optimal. Early exploration, batched feedback, weather/time composition, scaling/saturation, and the available fleet all influence the sequence.

The first-eight-slot .85 share is **48.54%**, the analysis middle-eight share **77.58%**, and last-eight share **71.38%**. Investigate persistence across the final target window, per-arm rewards and service/acceptance rates, uncertainty versus exploitation, context coverage, clipping, and controlled baseline/ablation results. Do not tune alpha or change arms just to make a more balanced histogram. [Sources: analysis arm_windows; tables/linucb_arm_summary.csv; raw linucb_factors.csv.]

## 38. NB9 WAIT OUTPUT

All statistics describe **27,967 completed driver idle episodes**, one per served assignment:

| Statistic | Minutes | Interpretation |
| --- | ---: | --- |
| Minimum | 0 | At least one driver dispatched without accumulating a completed idle mini-slot |
| P25 | 0 | Lower quartile is zero |
| Median / P50 | 0 | At least half the completed observations are at zero |
| Mean | 32.32 | Total recorded completed wait divided by 27,967; full value 32.31959094647263 |
| P75 | 10 | Three-quarters of the ordered sample lie at/below roughly ten minutes |
| P90 | 74 | Upper tenth extends beyond roughly 74 minutes |
| P95 | 204 | Upper five percent extends beyond roughly 3.4 hours |
| P99 | 540.68 | Upper one percent extends beyond roughly nine hours; interpolated percentile need not be an observed even-minute wait |
| Maximum | 1,364 | Longest recorded completed episode: 22 h 44 min |

A percentile is a threshold in an ordered sample, not the percentage of drivers with exactly that value. Mean much greater than median demonstrates strong **right skew**: many zero/small waits coexist with a small group of very long waits. “Heavy tail” is descriptive here; no particular statistical tail distribution has been fitted.

The maximum is possible inside a 1,440-minute run because a driver can stay IDLE across many main slots before eventually receiving dispatch. Uniform(0,30) is a preference distribution, not an operational timer cap. High wait values reveal modeled utilization imbalance but exclude unfinished/abandoned episodes (§22). The supervisor question is whether uncapped continuous idle waiting until dispatch matches the intended behavior and reporting target. [Sources: `summary.json:driver_wait_minutes`; wait_summary.csv.]

## 39. WAIT HISTORY COVERAGE

Real-history grids increase from **572 after slot 1 to 808 after slot 48**. This counts grids with usable causal wait history; it is not the number of observations or the number of drivers. Initial fare priors do not supply wait evidence.

The fallback evaluation share is:

\[
FallbackShare_t=\frac{NeutralCandidates_t}{RealCandidates_t+NeutralCandidates_t}.
\]

`t` is an elapsed slot; numerator and denominator count NB11 candidate evaluations, including repeated grids across different vehicles. It is **57.92% at slot 1**, **37.41% at slot 8**, **29.56% at slot 24**, and **33.25% at slot 48**. The initial drop toward 30% is consistent with accumulating real completed waits replacing neutral fallback.

Coverage can grow while fallback share rises: later drivers may evaluate different grids more often. Unvisited or rarely served grids may never acquire completed wait history; therefore fallback need not reach zero. The evidence supports causal-statistics accumulation, not statistical consistency of every grid's estimated wait distribution. [Sources: `nb9_wait.csv`; analysis wait_checkpoints; production candidate counting.]

## 40. NB11 ROUTING OUTPUT

| Action | Count | Share of 218,002 NB11 observations |
| --- | ---: | ---: |
| STAY | 197,812 | **90.74%** |
| NORTH | 7,645 | **3.51%** |
| EAST | 5,261 | **2.41%** |
| SOUTH | 3,981 | **1.83%** |
| WEST | 3,303 | **1.52%** |

These are selected actions among eligible end-of-slot drivers, not percentages of all 5,000 vehicles at every mini-slot or learned probabilities. A vehicle can contribute an action in many slots. The four MOVE counts sum to 20,190 starts.

STAY can be attractive because it avoids .45 kWh movement, candidate utilities may saturate/tie, boundary masks restrict choices, and fixed action order favors STAY in exact ties. Fare/wait profiles also shape utility comparisons. These are plausible mechanisms, not measured shares of the cause of STAY. Direct forecast demand does not appear as a separate NB11 utility term (§25).

High STAY can preserve spatial mismatch and thus affect local service availability, but the observed distribution is not proof of faulty routing or a causal explanation of all unserved demand. Its acceptability depends on the intended driver objective and later controlled comparisons. [Sources: analysis routing counts/shares; routing_action_summary.csv; baseline select_action.]

## 41. ROUTING P5 OUTPUT

P5 means the five-element distribution in **[STAY,NORTH,EAST,SOUTH,WEST]** order, not the fifth percentile. These are **post-slot next-context grid means**, averaged equally across the 1,213 grid vectors, which themselves use eligible-vehicle averaging or carry-forward/initialization.

| Completed slot | P(STAY) | P(NORTH) | P(EAST) | P(SOUTH) | P(WEST) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | .560392 | .198827 | .080833 | .080420 | .079527 |
| 2 | .525697 | .277737 | .065912 | .065911 | .064743 |
| 8 | .597900 | .276463 | .042001 | .042196 | .041441 |
| 24 | .675135 | .217673 | .038023 | .034501 | .034668 |
| 48 | .750966 | .147560 | .034581 | .032853 | .034040 |

Higher P(STAY) means more predicted STAY probability mass in this aggregate; it is not the fraction of actual repositioning decisions. NB11 **90.7% actual STAY** and final global-grid **75.1% P(STAY)** coexist because they use different populations, time aggregation, soft probabilities versus argmax labels, and zero-vehicle fallback. A supervised model also need not perfectly match training-label frequencies.

The probability health report finds finite values, zero out-of-bounds probabilities, and maximum sum-to-one error **2.220446049250313e−16**, floating-point precision scale. This validates probability representation, not calibration, optimality, or service improvement. The values enter next-slot pricing through relevant OD probability mass. [Sources: analysis selected_mean_p5 and probability_health; per_slot.csv; routing_rounds.csv; grid_policy.py.]

## 42. FEDERATED LEARNING OUTPUT

Phase 7D completes **48/48 federation rounds**, with **218,002 NB11/local observations** and **3,928–4,927 participants per round**. Observations sum over driver-slot pairs, not unique drivers. Zero-observation clients are the complement of participants within the 5,000-vehicle fleet; the same vehicle may be inactive in one round and active in the next.

The reported global parameter-change norm is:

\[
\|\Delta\theta_t\|_2=\sqrt{\sum_j(\theta_{t,j}-\theta_{t-1,j})^2}.
\]

`theta_t,j` is scalar parameter `j` after round `t`, and `theta_t−1,j` is its previous value. All weight/bias arrays are included. The norm measures how far the global model moved in parameter space; it is not loss, accuracy, reward, communication cost, or an action probability.

Values are **first .0105862439292027**, **median .011928269048993901**, **mean .011507766290834031**, **P95 .01369105569776472**, **maximum .0137551890349106**, and **last .0074585446259795**. Updates rise early then generally decline; zero-participant rounds and zero-change-with-participants cases are both zero.

Declining late update size may suggest stabilization, but it does not prove convergence: learning rate, changing participant/data composition, saturation, and imitation of a stable label majority can also make updates smaller. Held-out policy loss/accuracy and longer-run behavior would be needed to assess learning quality. Current compact artifacts primarily report participation, labels, parameter movement, and probabilities; they do not establish a complete FL generalization result. [Sources: routing_rounds.csv; analysis learning; production parameter-norm calculation.]

## 43. DEGRADATION OUTPUT

There are **1,028,006 valid NB11 candidate evaluations**, more than the number of actions because each eligible driver evaluates STAY and multiple valid neighbours.

| Statistic | Normalized penalty |
| --- | ---: |
| Minimum | 0 |
| Median | .6403540524498172 |
| Mean | .6607777332558145 |
| P95 | .8302345798337193 |
| P99 | .9347536705141327 |
| Maximum | 1 |

Mean is the arithmetic average over candidates; median/P95/P99 are ordered-sample thresholds. Higher values correspond to lower projected battery energy and a larger subtraction from charging utility. These describe candidate evaluation exposure, including repeated drivers and actions, not independent batteries or actual damage events.

The observed **[0,1]** range supports normalization health for this trajectory; it does not prove the physical degradation model, correct units elsewhere, or total economic wear. These penalties affect NB11 labels and thereby local/global policy training. They are separate from the passenger request adapter's energy ratio. [Sources: raw summary nb11_degradation_penalty; production.py; routing/production.py.]

## 44. REPOSITIONING OUTPUT

The run has **20,190 starts** and **20,080 completions**, leaving **110 vehicles repositioning at the final boundary**. A move begun at the end of slot 48 has not yet had its six mini-slots to arrive.

The conservation rule is:

\[
InTransit_{end}=InTransit_{start}+Starts-Completions.
\]

`InTransit` is a snapshot count, while `Starts` and `Completions` are event totals over the same interval. Here the initial count is zero, so **0+20,190−20,080=110**. For this implementation, end-of-slot starts are in transit at that same boundary; each 12-minute move completes during the following 30-minute slot unless outside the observation window.

`analysis.json` also sums boundary snapshots to 20,190. That is the sum of per-slot exposures, **not the final in-transit fleet**. Starts need not equal completions at an arbitrary stop time. This distinction avoids incorrectly diagnosing the valid residual 110 as lost vehicles. [Sources: analysis reposition; per_slot.csv; final fleet_states.csv.]

## 45. CHARGING AND ENERGY OUTPUT

Charging records **322 presentations/entries**, **246 completions**, **158 maximum active vehicles at a recorded boundary**, and **0 maximum queued vehicles at a recorded boundary**. Entries/completions are flows; active/queued values are snapshots. Zero boundary queue is not proof that no transient intra-mini-slot queue could ever occur, and this day does not stress every possible station bottleneck.

There are 15 popularity-ranked stations, each with a 3,000 kW power budget and 30 kW per active EV: 100 simultaneous full-power reservations per station. The model uses power capacity rather than a separate charger-count constraint. Queue order is FCFS, with seeded simultaneous-arrival ordering. Station choice uses nearest projected centroid; the presentation routine changes to station location without modeling a timed charging-navigation road trip. That simplification is distinct from the corrected timed NB11 repositioning.

Energy gain in one two-minute charge step is:

\[
\Delta E=30\times.90\times(2/60)=.9\text{ kWh},
\]

where 30 is kW, .90 efficiency, and 2/60 elapsed hours. Charging caps at 75 kWh and releases at full charge. Across recorded fleet boundaries, minimum energy is **10.30819619827143 kWh** and maximum **75 kWh**.

**Why below 15 kWh is permitted:** dispatch requires current energy above the charging trigger and enough energy for the entire passenger trip, but does not reserve 15 kWh after that trip. It deducts the trip's energy immediately at assignment and sets the vehicle BUSY. `_present_low_energy_vehicles` explicitly excludes BUSY vehicles. The mini-slot loop advances travel, then presents newly available low-energy vehicles and advances charging. Therefore a passenger still BUSY can appear below the trigger at a boundary. Repositioning can also cross the trigger and remains BUSY until arrival. The 15 kWh value triggers charging presentation when available; it is not a hard energy floor during travel. This is verified transition logic, **not proof of the precise trip/state responsible for the aggregate minimum**, which compact outputs do not identify.

Final reconciliation is **4,493 IDLE +321 passenger BUSY +110 repositioning BUSY +76 CHARGING =5,000**. Charging independently reconciles **0+322−246=76 active/queued members** at the end (76 active, zero queue). Every recorded fleet row reconciles to 5,000. Positive minimum and bounded maximum support state-accounting health; they do not establish range feasibility on a real road network. [Sources: dispatch.py energy eligibility/deduction; main_slot.py charging callback; charging/stations.py; fleet_states.csv; analysis fleet.]

## 46. CHART-BY-CHART EXPLANATION

All **18 charts** were visually inspected as existing PNGs and cross-checked against the generator and manifest. Each chart has a PNG and PDF with identical plotted content; these are **18 chart concepts / 36 files**, not 36 independent results. Links below open PNGs; the same stem with `.pdf` is the export version. Source names refer to the authoritative Phase 7D directory. No chart was regenerated.

### 46.1. `01_request_funnel.png` / `.pdf`

**Title:** Request funnel. [View chart](charts/01_request_funnel.png).

**Source:** summary.json + per_slot.csv; fields `generated, accepted, served`; aggregation: 48-slot sums.

**Axes and encoding:** X = Categories Generated, Accepted, Served. Y = Requests. Blue Generated; orange Accepted; green Served.

**Visible pattern:** 106,729 narrows to 61,863 then 27,967. These are nested stages, so the bars must not be added.

**Safe conclusion:** The observed modeled service funnel loses opportunities at acceptance and dispatch. **Not safe:** The plot cannot establish why a specific customer rejected or prove superiority.

**Thesis/supervisor use:** Introduces the thesis operational funnel.

### 46.2. `02_request_outcomes.png` / `.pdf`

**Title:** Final request outcomes. [View chart](charts/02_request_outcomes.png).

**Source:** summary.json + per_slot.csv; fields `rejected, served, accepted_unserved`; aggregation: 48-slot sums.

**Axes and encoding:** X = Rejected, Served, Accepted–unserved. Y = Requests. Blue Rejected; orange Served; green Accepted-unserved.

**Visible pattern:** Rejected 44,866 is largest; accepted-unserved 33,896 exceeds served 27,967. These three exclusive outcomes sum to generated.

**Safe conclusion:** Most generated requests do not produce an assignment. **Not safe:** It does not attribute failures to a specific fleet constraint.

**Thesis/supervisor use:** Separates customer refusal from dispatch failure.

### 46.3. `03_linucb_arm_distribution.png` / `.pdf`

**Title:** LinUCB pricing-factor selections. [View chart](charts/03_linucb_arm_distribution.png).

**Source:** per_slot.csv; fields `arm_085, arm_090, arm_095, arm_100, arm_105, arm_110, arm_115`; aggregation: 48-slot sums.

**Axes and encoding:** X = Seven pricing factors .85–1.15. Y = Selections. In increasing factor order: blue, orange, green, red, purple, teal, brown.

**Visible pattern:** The .85 and .95 bars dominate; .85 has 65,661 selections.

**Safe conclusion:** Discount offers dominate this trajectory. **Not safe:** Selection frequency is not a counterfactual per-arm revenue comparison or proof of optimality.

**Thesis/supervisor use:** Summarizes the pricing policy actually exercised.

### 46.4. `04_linucb_arm_evolution.png` / `.pdf`

**Title:** LinUCB pricing-factor share by slot. [View chart](charts/04_linucb_arm_evolution.png).

**Source:** per_slot.csv; fields `arm_085, arm_090, arm_095, arm_100, arm_105, arm_110, arm_115`; aggregation: 48 rows; within-slot shares.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Selection share, 0–1. Stacked areas for .85,.90,.95,1.00,1.05,1.10,1.15 using blue, orange, green, red, purple, teal, brown.

**Visible pattern:** Early shares fluctuate across arms; after about slot 20, blue .85 and green .95 dominate. Each slot is normalized by its own selection total.

**Safe conclusion:** The selected-arm mixture changes during learning and changing contexts. **Not safe:** Time variation cannot isolate learning from time-of-day/weather/fleet changes; area is not request-weighted total volume.

**Thesis/supervisor use:** Shows behavior hidden by an all-day histogram.

### 46.5. `05_revenue_reward_over_time.png` / `.pdf`

**Title:** Served revenue by slot / LinUCB learning reward by slot. [View chart](charts/05_revenue_reward_over_time.png).

**Source:** per_slot.csv; fields `raw_served_revenue, scaled_learning_reward`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Upper: Revenue; lower: Scaled reward. Blue upper line is raw served revenue; orange lower line is scaled learning reward.

**Visible pattern:** Revenue is high early, low near slots 17–22, rises near 28, and declines later. Both panels have the same shape because scaling is constant.

**Safe conclusion:** Raw economic reward and numerical learning reward remain proportional. **Not safe:** The panels are not two independent outcomes or a net-profit analysis.

**Thesis/supervisor use:** Explains reward units while retaining the economic timeline.

### 46.6. `05b_cumulative_revenue.png` / `.pdf`

**Title:** Cumulative served revenue. [View chart](charts/05b_cumulative_revenue.png).

**Source:** per_slot.csv; fields `raw_served_revenue`; aggregation: 48-row cumulative sum.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Cumulative revenue. Single blue cumulative-sum line.

**Visible pattern:** The curve rises throughout, flattens during low-revenue slots, and ends at 513,292.3994.

**Safe conclusion:** Cumulative accounting agrees with the raw total. **Not safe:** An increasing cumulative curve alone cannot show convergence or improvement; nonnegative revenue makes it monotone.

**Thesis/supervisor use:** Provides a readable total-revenue accumulation view.

### 46.7. `06_nb11_action_distribution.png` / `.pdf`

**Title:** NB11 routing-action distribution. [View chart](charts/06_nb11_action_distribution.png).

**Source:** per_slot.csv; fields `action_stay, action_north, action_east, action_south, action_west`; aggregation: 48-slot sums.

**Axes and encoding:** X = STAY, NORTH, EAST, SOUTH, WEST. Y = Actions. Blue STAY; orange NORTH; green EAST; red SOUTH; purple WEST.

**Visible pattern:** STAY 197,812 greatly exceeds the directional counts.

**Safe conclusion:** 90.74% of NB11 decisions select STAY. **Not safe:** These bars are not global-policy probabilities or fractions of every fleet state.

**Thesis/supervisor use:** Frames the driver-behavior review question.

### 46.8. `07_routing_p5_evolution.png` / `.pdf`

**Title:** Mean global routing probability over time. [View chart](charts/07_routing_p5_evolution.png).

**Source:** routing_rounds.csv (manifest); generator actually plots the identical P5 columns from per_slot.csv. Both tables were compared. This is a provenance-label discrepancy, not a numeric difference.; fields `mean_p_stay, mean_p_north, mean_p_east, mean_p_south, mean_p_west`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48, post-round checkpoints. Y = Mean probability, 0–1. Blue STAY; orange NORTH; green EAST; red SOUTH; purple WEST.

**Visible pattern:** STAY first dips, then rises toward .751; NORTH rises early then ends near .148; other directions remain low.

**Safe conclusion:** Post-round aggregated probabilities evolve while remaining normalized. **Not safe:** The curve is not actual movement share, and slot 1 is not the uniform pre-run input.

**Thesis/supervisor use:** Connects local/federated learning outputs to the next pricing context.

### 46.9. `08_nb13_parameter_change.png` / `.pdf`

**Title:** Global parameter-update magnitude over federated rounds. [View chart](charts/08_nb13_parameter_change.png).

**Source:** routing_rounds.csv; fields `global_parameter_change_norm`; aggregation: 48 rows.

**Axes and encoding:** X = Federated round 1–48. Y = L2 change norm. Single blue line, norm of all global parameter differences.

**Visible pattern:** The norm peaks around .01376 in the earlier-middle rounds and falls to .00746.

**Safe conclusion:** All rounds update, with smaller late parameter movements. **Not safe:** Declining weight movement alone does not prove convergence or accuracy.

**Thesis/supervisor use:** Provides a quantitative FL update diagnostic.

### 46.10. `09_nb12_participation.png` / `.pdf`

**Title:** NB12 participation by federated round. [View chart](charts/09_nb12_participation.png).

**Source:** routing_rounds.csv; fields `nb12_participants, zero_observation_clients`; aggregation: 48 rows.

**Axes and encoding:** X = Round 1–48. Y = Vehicles. Blue participating clients; orange zero-observation clients; grey horizontal line is fleet size 5,000.

**Visible pattern:** Participation remains 3,928–4,927; the complementary inactive line is much smaller.

**Safe conclusion:** Every round has substantial new-observation participation. **Not safe:** High participation does not prove good labels, low loss, privacy, or communication scalability.

**Thesis/supervisor use:** Explains which local models contribute to each federation.

### 46.11. `10_driver_wait_statistics.png` / `.pdf`

**Title:** Completed driver idle-wait statistics. [View chart](charts/10_driver_wait_statistics.png).

**Source:** summary.json; fields `min, p25, median, mean, p75, p90, p95, p99, max`; aggregation: 27,967 waits; aggregate statistics (not a histogram).

**Axes and encoding:** X = Statistic labels MIN,P25,MEDIAN,MEAN,P75,P90,P95,P99,MAX. Y = Minutes. All blue bars; labels show duration values.

**Visible pattern:** Zero lower quantiles contrast with P99 about 540.7 and maximum 1,364. Mean precedes P75 in the label order, so bars need not increase monotonically.

**Safe conclusion:** Completed driver waits are strongly right-skewed. **Not safe:** This is not a histogram, passenger wait distribution, or full censored-fleet wait analysis.

**Thesis/supervisor use:** Highlights driver utilization and the uncapped-wait question.

### 46.12. `11_wait_history_coverage.png` / `.pdf`

**Title:** Causal wait-history grid coverage / Neutral wait-utility fallback. [View chart](charts/11_wait_history_coverage.png).

**Source:** nb9_wait.csv; fields `real_wait_history_grids, wait_real_candidates, wait_neutral_candidates`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Upper: Grids; lower: Candidate share (%). Blue upper line is real-history grids; orange lower line is neutral/(real+neutral) candidate evaluations ×100.

**Visible pattern:** Coverage rises 572→808; fallback falls from 57.92% toward 30%, then ends at 33.25%.

**Safe conclusion:** Real completed waits gradually replace some neutral evaluation inputs. **Not safe:** Fallback percentage is not the percentage of all grids without history; growth does not prove statistical estimator consistency.

**Thesis/supervisor use:** Shows the difference between initialized priors and accumulating causal runtime evidence.

### 46.13. `12_contention_service.png` / `.pdf`

**Title:** Driver contention and service. [View chart](charts/12_contention_service.png).

**Source:** per_slot.csv; fields `eligible_evaluations, contenders, zero_eligible_requests, eligible_zero_contender_requests, served`; aggregation: 48-slot sums.

**Axes and encoding:** X = Eligible evals, Contenders, Zero eligible, Eligible/no contender, Served. Y = Count. Blue eligible evaluations; orange contender evaluations; green zero-eligible requests; red eligible/no-contender requests; purple served requests.

**Visible pattern:** 418,607 eligible driver–request evaluations yield 235,709 contender evaluations; failure request counts are 23,445 and 10,451.

**Safe conclusion:** The dispatch audit records both opportunity-level driver evaluation and request outcomes. **Not safe:** The five bars do not share one denominator: evaluations count repeated driver–request pairs, not unique requests or drivers. Do not read it as a five-stage funnel.

**Thesis/supervisor use:** Makes the availability-versus-willingness decomposition explainable.

### 46.14. `13_repositioning.png` / `.pdf`

**Title:** Repositioning state over time. [View chart](charts/13_repositioning.png).

**Source:** per_slot.csv; fields `reposition_starts, reposition_completions, repositioning_at_boundary`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Vehicles; event counts and boundary snapshots. Blue starts; orange completions; green repositioning at boundary.

**Visible pattern:** Starts/boundary overlap; completions lag because moves started after a slot arrive during the next slot. Large early activity declines.

**Safe conclusion:** Timed movement and the final in-transit residual reconcile. **Not safe:** Summing boundary snapshots is not the final fleet in transit, and fewer moves does not prove better routing.

**Thesis/supervisor use:** Demonstrates the cost and continuity of repositioning.

### 46.15. `14_fleet_state_evolution.png` / `.pdf`

**Title:** 5,000-vehicle fleet composition. [View chart](charts/14_fleet_state_evolution.png).

**Source:** fleet_states.csv; fields `fleet_idle, busy_passenger, busy_repositioning, fleet_charging`; aggregation: 48 rows; each row sums to 5,000.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Vehicles, stacked to 5,000. Blue IDLE; orange PASSENGER_BUSY; green REPOSITIONING; red CHARGING.

**Visible pattern:** Early repositioning is substantial; IDLE becomes dominant; charging becomes visible later. All bands total 5,000.

**Safe conclusion:** Recorded state counts conserve the fleet. **Not safe:** Many globally idle vehicles do not guarantee eligible supply at a request origin or imply each driver is frequently used.

**Thesis/supervisor use:** Checks continuous fleet reconciliation and availability composition.

### 46.16. `15_charging_activity.png` / `.pdf`

**Title:** Charging activity. [View chart](charts/15_charging_activity.png).

**Source:** fleet_states.csv; fields `charging_active, charging_entered, charging_completed, charging_queued`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Vehicles. Blue active; orange entered; green completed; red queued.

**Visible pattern:** Charging grows mainly later, active reaches 158 then declines; queue stays at zero in snapshots.

**Safe conclusion:** Charging entries, restoration, and releases occur in the integrated trajectory. **Not safe:** Zero snapshot queue does not validate capacity under other EV shares or rule out all transient congestion.

**Thesis/supervisor use:** Shows energy constraints eventually activate rather than staying a dormant module.

### 46.17. `16_energy_health.png` / `.pdf`

**Title:** Fleet energy health. [View chart](charts/16_energy_health.png).

**Source:** fleet_states.csv; fields `energy_min, energy_median, energy_mean, energy_p95, energy_max`; aggregation: 48 rows.

**Axes and encoding:** X = Elapsed Slot 1–48. Y = Energy (kWh), 0–75. Blue MIN; orange MEDIAN; green MEAN; red P95; purple MAX.

**Visible pattern:** Minimum drops toward 10–11 kWh; mean/median decline then recover; maximum reaches the 75 kWh cap; upper tail rises with charging.

**Safe conclusion:** Recorded energy remains nonnegative and capacity-bounded while charging replenishes part of the fleet. **Not safe:** Each point is a fleet cross-section, not one vehicle path; low boundary energy does not identify its vehicle or prove realistic road energy.

**Thesis/supervisor use:** Connects travel consumption, trigger timing, and charge recovery.

### 46.18. `17_time_of_day_performance.png` / `.pdf`

**Title:** Time-of-day request volume / Time-of-day served/accepted rate. [View chart](charts/17_time_of_day_performance.png).

**Source:** per_period.csv; fields `period, generated, accepted, served`; aggregation: 48 Period rows.

**Axes and encoding:** X = Half-hour Period 0–47, sorted by clock time. Y = Upper: Requests; lower: Rate (%). Upper blue Generated and orange Served; lower green Served/Accepted ×100.

**Visible pattern:** Generated volume is low overnight and grows through daytime; served/accepted is low in later afternoon and high near the early evening periods. The wrap around 19:00 combines different calendar dates.

**Safe conclusion:** This single trajectory has strong time-of-day differences in generated volume and service realization. **Not safe:** It is not a many-day average or a causal time/weather effect; ordering by Period is not elapsed learning order.

**Thesis/supervisor use:** Supports discussion of demand–service mismatch across the modeled day.

## 47. TABLE-BY-TABLE EXPLANATION

The `tables/` directory contains **11 CSV tables**. The reporting generator copies or aggregates authoritative artifacts and writes floats with 12 significant digits; small last-digit differences from raw CSV/JSON are formatting, not alternate runs. High/low interpretations follow §§35–45. These reporting tables are downstream diagnostics and are not read back as additional online learning observations.

### 47.1. [core_summary.csv](tables/core_summary.csv)

**Rows:** One complete 48-slot trajectory.

**Columns:** generated, accepted, rejected, served, accepted_unserved are the funnel counts; acceptance_rate=A/G, served_generated_rate=S/G, served_accepted_rate=S/A are fractions, not percentages; raw_served_revenue is summed assignment fare; scaled_learning_reward is its training-reference-scaled sum; slots=48 and fleet=5000 define exposure.

**Analysis / thesis question:** Answers how much demand becomes realized service and revenue; supports headline thesis accounting.

### 47.2. [linucb_arm_summary.csv](tables/linucb_arm_summary.csv)

**Rows:** One row per pricing factor, seven rows.

**Columns:** pricing_factor is the multiplier; count is selections for that arm; share=count/106729.

**Analysis / thesis question:** Answers which prices were chosen; compare concentration and later experiment distributions, not causal arm effects.

### 47.3. [routing_action_summary.csv](tables/routing_action_summary.csv)

**Rows:** One row per NB11 action, five rows.

**Columns:** action is STAY/NORTH/EAST/SOUTH/WEST; count is selected labels across slots; share=count/218002.

**Analysis / thesis question:** Answers what drivers actually chose under NB11; supplies routing-behavior discussion.

### 47.4. [routing_p5_by_slot.csv](tables/routing_p5_by_slot.csv)

**Rows:** One completed slot, 48 rows.

**Columns:** slot_index is zero-based elapsed order; timestamp is that slot start; mean_p_stay/north/east/south/west are post-round next-context probability means across all grid vectors.

**Analysis / thesis question:** Answers how the routing signal supplied to future pricing evolved; distinguishes probabilities from actions.

### 47.5. [federated_learning_rounds.csv](tables/federated_learning_rounds.csv)

**Rows:** One slot/round, 48 rows.

**Columns:** slot_index and timestamp identify time; nb11_observations counts new labels; nb12_participants counts contributors; zero_observation_clients counts remaining fleet clients; nb13_rounds is completed rounds in the slot; global_parameter_change_norm is the all-parameter L2 change; action_stay/north/east/south/west count labels; mean_p_* are post-round grid-mean probabilities.

**Analysis / thesis question:** Answers whether local observations and federation continue and whether weight changes stabilize; does not contain a held-out loss/accuracy curve.

### 47.6. [wait_summary.csv](tables/wait_summary.csv)

**Rows:** One aggregate completed-wait distribution.

**Columns:** count=27967; min/max are extremes; mean is total completed minutes/count; median is P50; p25,p75,p90,p95,p99 are percentile thresholds in minutes.

**Analysis / thesis question:** Answers how long dispatched drivers had waited and how unequal completed waiting is; excludes unfinished episodes.

### 47.7. [contention_summary.csv](tables/contention_summary.csv)

**Rows:** One whole-run contention aggregate.

**Columns:** eligible_evaluations and contenders count driver–request pairs; zero_eligible_accepted and eligible_zero_contender count accepted requests by failure category; served counts assignments; contender_rate=contenders/eligible_evaluations; served_accepted_rate=served/accepted.

**Analysis / thesis question:** Answers whether failed dispatch was no feasible local vehicle or no willing eligible driver; preserves distinct denominators.

### 47.8. [fleet_state_by_slot.csv](tables/fleet_state_by_slot.csv)

**Rows:** One post-slot fleet boundary, 48 rows.

**Columns:** slot_index/timestamp identify the completed slot; fleet_idle, busy_passenger, busy_repositioning, fleet_charging are mutually exclusive counts; charging_active/queued split infrastructure members; charging_entered/completed are within-slot flows; energy_min/median/mean/p5/p95/max are fleet cross-sectional kWh summaries.

**Analysis / thesis question:** Answers whether fleet/charging reconcile and energy stays bounded; distinguishes flows, stocks, and distributions.

### 47.9. [per_period_summary.csv](tables/per_period_summary.csv)

**Rows:** One daily Period, 48 rows, encountered in run order in the CSV.

**Columns:** period is clock index 0–47; generated/accepted/served are request counts; raw_served_revenue is summed assignment fare; wait_mean is mean completed-driver wait for that period; action_* and arm_* are label/selection counts. Only one slot contributes per Period in this day.

**Analysis / thesis question:** Answers when service/price/routing behavior differs by time of day; sorting Period creates clock order rather than learning chronology.

### 47.10. [representative_fare_history.csv](tables/representative_fare_history.csv)

**Rows:** Five selected grids ×48 slots =240 rows.

**Columns:** slot_index/timestamp/grid_id identify observation location/time; historical_count/mean/std are fixed pre-cutoff bootstrap fields; observed_count/mean/std are current served-fare sample fields; ewma_mean/std are carried or updated fare summaries. Empty current means/SDs are absent, not zero.

**Analysis / thesis question:** Answers whether historical initialization becomes causally updated; grids 293,292,321,320,379 illustrate behavior and are not a statistically representative random fleet/grid sample.

### 47.11. [representative_routing_probabilities.csv](tables/representative_routing_probabilities.csv)

**Rows:** The same five selected grids ×48 slots =240 rows.

**Columns:** slot_index/timestamp/grid_id identify checkpoint; p_stay,p_north,p_east,p_south,p_west are that grid’s next-context masked/fallback probabilities, summing to one.

**Analysis / thesis question:** Answers how individual grid vectors differ from the all-grid mean; zero direction can reflect masking, and strong local probability does not imply a universal global preference.

### Supporting package and raw outputs

The package root also has `summary.json` (run identity, funnel, rates, verdict), `summary.csv` (one-row numeric version), `README.md` (review index), and `chart_manifest.json` (source/figure hashes and plotting fields). Raw `per_slot.csv` is the broad joined slot report; `per_period.csv` reorganizes key outputs by clock Period; `linucb_factors.csv` records factor counts; `nb9_wait.csv` holds slot wait/coverage counters; `routing_rounds.csv` holds learning summaries; `fleet_states.csv` holds reconciled snapshots; representative raw CSVs supply the corresponding reporting tables. Raw `summary.json` stores totals/distribution summaries/source manifest, `analysis.json` stores derived diagnostics/checkpoints, and `reproducibility.json` stores seeds, RNG fingerprints, update count, and trajectory fingerprint. The nested `reproducibility_check_2slot/` is an existing repeat-prefix artifact, not a second full-day replication.

**Analysis flag caveat:** `analysis.json:fare.finite=false` comes from testing representative current fare means/SDs including legitimately absent values when observed_count is zero. Read missing current statistics together with observed_count and finite EWMA fields; the flag alone is not proof of invalid initialized fare history. This was checked against the representative fare table. There is no saved per-vehicle completed-wait histogram or request-level full-day microdata file in this compact output directory; do not promise analyses requiring those raw records from these summaries alone.

## 48. WHAT THE 48-SLOT RUN PROVES

Within the tested trajectory, the available evidence supports these engineering conclusions:

| Conclusion | Evidence and practical limit |
| --- | --- |
| Integrated simulator operates continuously | 48 consecutive aligned rows; all Periods covered once |
| State persistence works | Delayed passenger/reposition arrivals, extended driver waits, later charging, and accumulated learner state |
| CNN alignment works for this window | First target 19:00, matching input+30-minute mapping; this is not proof of terminal lookahead handling |
| Pricing decision/update accounting works | 106,729 generated=selections=updates, with served-revenue feedback |
| NB9 develops causal statistics | Real wait-history coverage 572→808; fare current counts separate from bootstrap |
| NB11 produces valid actions | 218,002 labels and timed MOVE accounting |
| NB12 training is connected | New-observation clients train using NB11 labels; this does not establish predictive generalization |
| NB13 federates | 48 rounds with participants and nonzero global parameter changes |
| Routing probabilities evolve | Post-round P5 changes and remains finite/normalized |
| Vehicle states reconcile | Every recorded boundary sums to 5,000; final composition verified |
| Charging works in the tested regime | 322 entries, 246 releases, energy restoration to capacity |
| Degradation stays bounded | All recorded candidate-summary extrema lie in [0,1] |
| Reproducibility mechanisms work | Frozen source fingerprints and RNG/trajectory records; existing two-slot repeat matches the first two trajectory rows |

“Proves” here means operational evidence under these inputs and checks, not a universal theorem. In particular, the existing reproducibility repeat covers **two slots**, not two independently rerun 48-slot trajectories or cross-hardware bitwise reproducibility. TensorFlow behavior across platforms remains subject to the README's reproducibility boundary. No simulation was rerun for this explanation.

## 49. WHAT THE 48-SLOT RUN DOES NOT PROVE

It does **not** establish proposed-model superiority, statistical significance, final convergence, best LinUCB alpha, best fleet size, best service rate, or best routing behavior. There is no controlled baseline here, no repeated-seed confidence interval, and no prespecified optimum search result.

It also does not isolate the contribution of **weather, destination popularity, routing, or corrected supply**, and does not establish robustness to EV penetration. Changing several coupled components at once cannot attribute an effect to a particular feature. A learned coefficient or large arm share is not a controlled ablation.

It does not validate synthetic customer/driver assumptions against actual acceptance decisions, establish the physical correctness of the spatial unit labels, model complete road-network pickup/charging navigation, or quantify realized battery aging. The 48-slot engineering result and saved CNN metrics are necessary evidence for continuing research, not substitutes for final experiments or resolution of the current documented contradictions.

## 50. SUPERVISOR QUESTIONS

1. **Pricing:** LinUCB selects .85 for 61.52% of opportunities. Is this acceptable under the intended objective of expected served gross fare, or does the intended scientific objective include other economic/service terms? This is an objective question, not a request to force balanced arms.
2. **Routing:** NB11 selects STAY 90.74% of the time. Is this the intended consequence of equal-weight price/wait/charging utility and STAY tie priority?
3. **Driver waiting:** Should available idle waiting remain uncapped until dispatch, with unfinished/abandoned episodes excluded from the completed-wait summary? Maximum completed wait is 22 h 44 min.
4. **Dispatch reach and behavior:** Only 45.21% of accepted demand is assigned. Is origin+direct-neighbour search with immediate failure and current outside-option contention the intended model, or should that methodology be revisited?
5. **Spatial semantics:** Current geometry is 3,000 EPSG:2263 feet while documentation says metres and MOVE assumes 3 km. Which intended physical interpretation should govern a separately planned correction and any resulting artifact/evaluation impact?
6. **Contention adapter semantics:** Is passing a dimensionless, decreasing-with-distance pickup proxy into the existing decreasing minutes-based wait function intended? Clarify the mapping before interpreting pickup burden as a behavioral explanation.
7. **Experiment interpretation:** Is forecast-driven volume with month-wide empirical OD sampling, and zero-time/energy charging-station presentation, the intended evaluation environment? These are current modeling choices, not new proposed methods.
8. **Separate historical study:** Confirm the elasticity channelization definition and weather groupings before generating the requested multi-month plots.

Do not turn solved timestamp alignment, persistent RNG, common initialization, or completed-wait accounting into open methodology questions. The terminal-lookahead failure (§31) is an engineering issue to address before execution, not a question of whether the supervisor prefers correct indexing. No implementation change is made by listing these questions.

## 51. CURRENT PROJECT STATUS

**Recorded regression status: 258/258 tests passing. Phase 7D: COMPLETE. Recorded project milestone: READY FOR PHASE 8A. Next intended scientific run: the authoritative 298-slot proposed-model evaluation.** These statements match the audited README and the dated reporting verdict, and the test count is reported evidence rather than a new test run.

**Current audit qualification:** the recorded readiness label predates or does not cover the terminal next-context issue found by this documentation audit. Current code requests an unavailable February 1 00:00 forecast while trying to execute the last January 31 23:30 target. Therefore distinguish **recorded milestone readiness** from **verified ability to finish all 298 slots**. The latter is blocked by the documented boundary handling until separately corrected. Phase 7D's completed 48-slot evidence remains intact.

No configuration, source behavior, model weights, or existing result artifacts have been modified. This document is the only project addition. The scientific-methodology caveats in §§4,19,45 also need explicit treatment when interpreting or extending the proposed evaluation.

## 52. WORK REMAINING

The requested research sequence remains:

1. **Phase 8A 298-slot proposed model:** first resolve the identified terminal lookahead in separately authorized engineering work and decide how current methodological contradictions affect the frozen evaluation; then execute the aligned January 25 19:00–February 1 00:00 window. No extra target is invented here.
2. **Review proposed output:** reconcile counts, temporal boundaries, waits, energy, contention, learning, and gross revenue before interpreting performance.
3. **Baseline experiment:** execute the agreed comparator on an explicitly comparable environment/window.
4. **Proposed versus baseline:** compare the defined system metrics with consistent denominators and experimental controls.
5. **Ablations:** no weather, no popularity, no routing, and the planned supply-related ablation. The exact supply-ablation setting is **NOT VERIFIED FROM CURRENT AUTHORITATIVE SOURCE**; this document does not substitute a newly invented variant.
6. **EV penetration study:** evaluate approved EV shares; older planning discusses 25%, 50%, and 75%, but the final experiment protocol must govern the comparison. Current production initializes the entire fleet through the EV model.
7. **LinUCB convergence/result plots:** investigate arm evolution, served reward, uncertainty, and context coverage without equating stable arm share with convergence.
8. **NB12/NB13 FL learning plots:** supplement participation/update norms with the approved learning-quality outputs; do not relabel weight norms as loss.
9. **Final system-performance tables:** report service, customer refusal, failure decomposition, gross revenue, fleet/energy, routing, and learning with defined populations.
10. **Separate historical elasticity versus time/weather analysis:** use an adequately long historical dataset and confirmed channelization definition (§53).
11. **Thesis-ready figures/tables:** assemble evidence, limitations, provenance, and consistent captions from the completed comparisons.

This is a roadmap, not a claim that these experiments or all their detailed protocols already exist. No baseline, ablation, full-window simulation, or historical multi-month analysis was run for this documentation task.

## 53. ELASTICITY VS TIME/WEATHER WORK

The supplied task describes a separate supervisor guide requiring:

- **Graph 1: Mean Elasticity vs Time under Different Weather Conditions.** Time intervals on the horizontal axis; a mean historical sensitivity/elasticity measure on the vertical axis; one explicitly defined weather group per series, with counts and uncertainty where the approved protocol requires them.
- **Graph 2: Elasticity Channelization vs Time under Different Weather Conditions.** The meaning of “channelization” is not fixed in current authoritative implementation. It must not be silently interpreted as clustering, quantile bins, a histogram, or a new network channel.
- **An aggregated table** aligned with the same time/weather groups, retaining observation support and defined summary measures.

One simulated 48-slot day cannot scientifically provide the requested historical weather/time coverage: it contains one occurrence of each Period, a narrow realized weather sequence, and simulated acceptance draws rather than a multi-month empirical elasticity panel. January alone also does not provide the approximately **three or six months** requested for the separate study. Additional historical coverage is needed to observe repeated time intervals under different weather conditions rather than confounding one day with weather.

An **hourly starting interval** is the requested recommendation for the historical study, separate from the simulator's half-hour operation. Weather categories should group documented WeatherCode conditions consistently; precise final category names, boundaries, and pooling rules must be confirmed. The production severity lookup in §10 is available, but is not automatically the approved grouping for this separate analysis.

**Verification boundary:** the three/six-month duration, the two exact graph titles, hourly recommendation, and request for an aggregated table are explicit in the supplied user task; README independently confirms multi-month work and the need to confirm channelization. The exact separately named historical-elasticity guide and its detailed category/channelization protocol were **NOT VERIFIED FROM CURRENT AUTHORITATIVE SOURCE** in the inspected local supervisor documents. They are reported as the task's requested future work, not falsely attributed to an unseen guide. The historical epsilon proxy (§14) must also be distinguished from causal demand elasticity when naming thesis results.

## 54. ASSUMPTIONS / LIMITATIONS

The labels below distinguish data evidence from adopted mathematical forms and engineering/synthetic choices. “PROFESSOR-DEFINED” denotes an adopted supervisor-directed baseline/formulation, not a claim that every numeric constant was empirically estimated.

| Item | Type | Current assumption | Why needed | Possible limitation |
| --- | --- | --- | --- | --- |
| Taxi OD, fare, distance, duration | EMPIRICAL | Preserve valid fields jointly from one January row | Retain observed trip characteristics | No coordinates; month-wide origin-conditioned sampling does not retain current-slot OD seasonality |
| Zone-to-grid assignment | SYNTHETIC ASSUMPTION | Seeded candidate-grid draws within each observed taxi zone | Obtain GridIDs without coordinates | Individual location is imputed; spatial findings inherit allocation uncertainty |
| Grid spacing/unit label | PROJECT ENGINEERING ASSUMPTION | Existing 1,213-grid artifact uses 3,000 projected coordinate units | Preserve canonical shared representation | EPSG:2263 feet conflicts with metre label and 3 km movement interpretation |
| Weather/time alignment | PROJECT ENGINEERING ASSUMPTION | Taxi and weather times remain timezone-naive; hourly weather is filled forward then backward | Preserve legacy pipeline | True timezone/DST alignment is unresolved; backward filling is not causal real-time sensing |
| Weather values | EMPIRICAL | One NYC Meteostat point, temperature/wind/code | Provide observed environmental context | A single station/point cannot capture full spatial weather variation |
| CNN layout/metrics | PROJECT ENGINEERING ASSUMPTION | Seven-channel legacy model with padded invalid positions | Reproduce established predictor | Padded-cell metrics differ from exclusively valid-grid evaluation |
| Request volume | PROJECT ENGINEERING ASSUMPTION | Round nonnegative CNN forecasts; zero without an origin pool | Convert forecast into integer opportunities | System service results depend on prediction error and rounding, not just operations |
| Driver price/wait traits | SYNTHETIC ASSUMPTION | Fixed Uniform price range based on fare mean/SD and Uniform wait | Reproducible persistent heterogeneity | Not observed individual choices; price mapping semantics need careful interpretation |
| Wait preference range | SYNTHETIC ASSUMPTION | 0–30 minutes, fixed | Bound preference trait | Does not cap realized waiting or validate the long tail |
| Customer sensitivity/WTP | PROFESSOR-DEFINED | Historical absolute ratio, positive truncated Normal, signed Pmax | Operational acceptance model | Proxy is not causal demand elasticity; no upper epsilon cap and possible nonpositive Pmax |
| Dispatch radius | PROJECT ENGINEERING ASSUMPTION | Origin + direct canonical neighbours; no retry queue | Deterministic local feasibility | Local mismatch can coexist with a globally idle fleet |
| Contention adapter | PROJECT ENGINEERING ASSUMPTION | Offered fare, normalized pickup proxy, normalized passenger energy | Connect request willingness to existing utility | Dimensionless proxy is passed to minutes-based decreasing wait utility |
| Reposition distance/speed | PROJECT ENGINEERING ASSUMPTION | 3 km /15 km/h /12 minutes /.45 kWh | Explicit unavailable travel interval | No road paths and physical grid-spacing mismatch |
| Battery model | PROFESSOR-DEFINED | Adopted 75 kWh, .15 kWh/km, 30 kW baseline; 20% trigger | Track EV feasibility and charge need | No temperature/traffic-specific energy, no post-trip 15 kWh reserve |
| Initial SOC | SYNTHETIC ASSUMPTION | Truncated Normal underlying .50±.05 bounded [.50,.70] | Heterogeneous initial energy | Artificial cold-start distribution; realized mean differs from underlying mean |
| Degradation | PROFESSOR-DEFINED | Supervisor-cited DOD source with project threshold normalization | Comparable penalty in utility | Engineering normalization, not measured SOH; temperature component omitted |
| Charging operation | PROJECT ENGINEERING ASSUMPTION | 15 stations; 3,000 kW each; .90 efficiency; full-charge release; zero-time/energy station presentation | Operational power/queue state | Simplified navigation and capacity; whole-month station placement is static and not training-only |
| Fleet size/placement | PROJECT ENGINEERING ASSUMPTION | Working 5,000 baseline, uniform valid-grid initialization, all initialized as EVs | Establish reproducible integrated scenario | Not an optimized size, real deployment distribution, or EV-share robustness result |
| First-slot routing | PROJECT ENGINEERING ASSUMPTION | Uniform over valid actions | Avoid arbitrary untrained pricing signal | Neutrality convention and startup effects remain |
| Fare bootstrap | PROJECT ENGINEERING ASSUMPTION | Pre-cutoff local/global means and population SD; .30 EWMA | Usable fare reference from the first slot | Pooled fallback suppresses local differences; EWMA of SD is not pooled lifetime SD |
| Wait fallback | PROJECT ENGINEERING ASSUMPTION | U_wait=.5 only when no usable history | Allow evaluation without fabricated observations | Unobserved grids can retain neutral treatment indefinitely |
| NB12/NB13 | PROJECT ENGINEERING ASSUMPTION | Supervised utility imitation; common initialization; one-observation-per-client FedAvg | Learn reusable routing tendency for pricing | No demonstrated RL optimality, real network privacy, or held-out FL convergence |
| Pricing/update schedule | PROJECT ENGINEERING ASSUMPTION | Per-request decisions batched before mini-slot dispatch; feedback after slot | Preserve implemented causal update boundary | No immediate within-slot learning; slot supply snapshot can become stale |
| Evaluation end | PROJECT ENGINEERING ASSUMPTION | 298 targets frozen; next-context lookup currently unconditional | Next-slot orchestration | Last target requests unavailable February context; unresolved terminal boundary |

### Documentation verification performed

Read-only checks reconciled all core totals against raw summary, analysis, per-slot rows, and the dated package; verified all 48 fleet rows and final charging/repositioning balances; confirmed the 1,028/185 bootstrap split and saved CNN metrics; compared all P5 columns across per-slot and round tables; confirmed the existing two-slot repeat equals the first two production rows; and verified SHA-256 hashes for all 36 existing chart files and all source files listed by the chart manifest. The document contains exactly 55 numbered main sections, 18 chart explanations, and 11 table explanations. `git diff --check` passed; an additional no-index whitespace check covers this newly created, initially untracked Markdown file. No tests or simulation were executed. All existing artifacts remain unchanged.

### Current contradiction and verification register

| Finding | Resolution in this explanation |
| --- | --- |
| README “3 km grid” vs 3,000 EPSG:2263 feet in code/artifact | Preserve existing artifact; disclose unit contradiction (§4) |
| Task current-slot empirical trips vs month-wide pool | Explain actual origin-conditioned month-wide sampling and forecast counts (§9) |
| README empirical offered base fare vs historical P_base | Follow production historical customer branch (§15) |
| README request pricing “when it arrives” vs pre-dispatch batch selections | Explain exact selection/dispatch/update schedule (§2) |
| Older README scaler/supply/popularity positions vs request_8d | Use four log transforms, corrected supply, popularity fourth, weather eighth (§10) |
| Legacy YAML/reward JSON vs explicit production selectors | Explain effective overrides; do not treat retained compatibility config as Phase 7D behavior (§31) |
| Generic sample-count FedAvg vs equal new-count exports | Explain sample_count=1 per new participating client (§29) |
| Uniform first pricing signal vs nonuniform saved first P5 | Separate pre-slot input from post-round output (§30) |
| Chart 07 manifest vs generator source table | P5 fields are equal; source filename labeling differs (§46) |
| Analysis fare finite=false | Legitimate missing no-observation current values, with finite EWMA; not automatically corrupted priors (§47) |
| Recorded READY_FOR_PHASE_8A vs terminal lookahead | Keep recorded milestone and flag current full-run execution gap (§51) |
| Requested elasticity guide details/supply ablation protocol | Exact missing specifics explicitly NOT VERIFIED; no substitute methodology added (§§52–53) |

Other explicit limits: the vehicle/state causing the 10.308 kWh minimum is not identified by compact outputs; no new 48-slot replication or regression suite was executed; physical battery-aging validity and final policy convergence are unproven. These are limits of evidence, not missing reported numerical summaries.

## 55. FINAL ONE-PAGE EXECUTIVE SUMMARY

**Objective.** Study a ride-hailing platform coupling forecast demand, contextual pricing, customer willingness to pay, driver contention, dispatch, EV charging, repositioning, and local/federated routing learning. Gross served fare is the pricing feedback; net profit is not modeled by that reward.

**Architecture.** January 2026 TLC data and weather become a shared 1,213-grid CNN representation. A frozen seven-channel CNN predicts one half-hour ahead. Rounded forecasts generate opportunities; origin-conditioned empirical trip rows supply OD/distance/duration. Each request receives an 8D LinUCB price context and historical-sensitivity acceptance test. Fifteen two-minute steps handle accepted arrivals, driver contention, travel and charging. NB9 updates fares/completed driver waits; NB11 selects utility-maximizing STAY/MOVE; NB12 imitates those labels; NB13 federates and returns routing probabilities to pricing.

**Completed components and corrections.** NB1–NB13 and authoritative production integration are implemented. Major corrections include Idle+Incoming supply, request-level pricing, historical sensitivity fallback, served-revenue scaling, contention, persistent driver waiting/RNG, timed 12-minute repositioning, historical fare priors, persistent driver traits, common local-model initialization, uniform first-slot routing, bounded degradation, and the CNN target timestamp +30-minute correction. NB11 drives actual behavior; the learned model supplies pricing signals.

**Phase 7D evidence.** Seed 42, 5,000 vehicles, January 25 19:00–January 26 19:00 exclusive; 48 continuous slots. Generated **106,729**; accepted **61,863**; rejected **44,866**; served **27,967**; accepted-unserved **33,896**. Acceptance **57.96%**; served/generated **26.20%**; served/accepted **45.21%**. Gross recorded revenue **513,292.3994**. All 106,729 price decisions receive feedback. There are **48 federation rounds**, **218,002 observations**, and reconciled fleet/charging/repositioning counts.

**Four observations for the meeting.** (1) .85 is selected **61.52%** of the time: assess against the intended objective, not a preferred histogram. (2) NB11 selects STAY **90.74%**: consider intended driver behavior and spatial availability. (3) Completed driver wait has median **0**, mean **32.32**, maximum **1,364 minutes**: discuss uncapped waits and omitted unfinished episodes. (4) Only **45.21%** of accepted demand is assigned: **23,445** failures have no eligible vehicle and **10,451** have eligible drivers but no contenders; the detailed causes of local scarcity are not identified by these aggregates.

**Status and limits.** Recorded status is **258/258 tests passing; Phase 7D COMPLETE; READY FOR PHASE 8A**. This audit finds a terminal lookahead that requests an unavailable February 1 forecast on the last of 298 targets; address it before execution. Also resolve interpretation of the feet/metres grid discrepancy and the contention wait adapter. Phase 7D does not prove superiority, statistical significance, convergence, or EV-share robustness. No code/configuration/artifacts were changed and no simulation was rerun for this explanation.

**Next steps.** Resolve the documented execution boundary and methodological interpretations; run the authoritative 298-target proposed evaluation; review outputs; run baseline/comparisons, planned ablations and EV-share studies; assemble pricing/FL/system figures. Separately obtain multi-month history and confirm elasticity channelization/weather categories before producing its two requested graphs and table.
