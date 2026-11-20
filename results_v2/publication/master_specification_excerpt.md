# Master specification — read-only text extraction

Source: `notebooks/plan/masterdocument/MASTER DOCUMENT1.docx`. SHA256: `17ca4a5f8ad8181bb59eec418fb696e9aabd78fd3dcf32247c0627641a0b07dd`. This verbatim paragraph-text extract aids navigation; the original Word document remains authoritative. Word tables are serialized in document order; layout is not reproduced.

```text
FINAL MASTER IMPLEMENTATION ROADMAP
Privacy-Aware Pricing and Repositioning for Ride-Hailing Systems:A Hierarchical Reinforcement Learning Approach
Consolidated from the research manuscript and three supervisor-meeting transcriptsPrepared: 16 November 2026

Document purpose and source coverage
Contents
1. Research objective and architecture
2. System entities, data and notation
3. Passenger price sensitivity and acceptance
4. CNN demand prediction module
5. Top-level destination-based pricing DQN
6. Grid statistics and EWMA updates
7. Bottom-level driver repositioning and EV charging
8. Federated learning and privacy
9. Gymnasium simulation environment and slot sequence
10. Replay buffer and DQN training algorithm
11. Demand, destination and episode generation
12. Experimental configuration and evaluation
13. End-to-end implementation checklist
14. Decisions and parameters requiring finalization
15. Source traceability
1. Research objective and architecture
The proposed framework jointly handles dynamic dispatch pricing, passenger acceptance, dispatch assignment, driver repositioning, and EV charging navigation while protecting individual driver preferences. The platform operator (PO) controls the top-level pricing decision. Individual idle vehicles make private bottom-level repositioning or charging-navigation decisions.
The objective is to maximize the total expected discounted revenue from successful ride dispatches across all origin–destination (OD) grid pairs. The coupling is two-way: destination-based prices affect passenger acceptance and driver dispatch contention; the expected dispatch opportunities and charging conditions influence drivers’ private repositioning choices; the aggregate mean routing response is fed back to the PO.
Layer
Agent / module
Decision or output
Information boundary
Top level
Platform operator; DQN
One pricing factor for each feasible origin–destination pair (g,g′) and slot
Uses grid-level aggregates; does not observe individual passenger elasticity or driver preferences
Bottom level
Each idle driver; shared/global policy network
Stay or move to a one-hop neighbouring grid; EV charging navigation when required
Individual preferences and decisions remain local/private
Coordination
Federated learning
Aggregated global routing-policy parameters and mean routing probabilities
Local experiences/individual actions are not disclosed as raw individual records
Demand input
CNN predictor
Grid-wise predicted request volume for the upcoming slot
Prediction is a grid-aligned output; observed requests remain the realized simulator demand

2. System entities, data and notation
2.1 Spatial and temporal model
The operating region is divided into fixed-size grids G. The paper uses one-hop neighbourhoods Ng, including the current grid itself.
The manuscript gives a 30-minute time slot as an example. Each slot is subdivided into mini-slots, with 2 minutes given as an example, for request arrivals and dispatch matching.
The meeting discussion confirms a proposed 3 km × 3 km grid size. The number of grid indices and feasible neighbouring/destination grids must be calculated from the selected study-area boundary.
Relative neighbourhood indexing for the routing network: current grid is index 1; its neighbours are indexed 2–9 clockwise starting from the left. Boundary grids may have fewer than eight neighbours.
Symbol
Meaning
G, T
Set of geographic grids and time slots
g, g′
Origin grid and destination grid
Ng
One-hop neighbourhood of grid g, including g
Jg,t
Passenger requests originating in grid g and awaiting dispatch in slot t
Oj, Dj
Origin and destination of passenger request j
Tj
Request time; Tj (maximum wait duration) as denoted in the paper
εj,t
Passenger price elasticity / sensitivity parameter; private to the PO
I
Set of vehicles in the operating region
Oi,t
Current grid of vehicle i
Bi,t
Busy indicator: 0 idle, 1 busy
Pimin, Wimax
Driver i’s minimum acceptable dispatch price and maximum dispatch-wait tolerance
Vi
EV indicator: 1 for EV
Ei,t, Eimax, Eimin
EV stored energy, battery capacity and energy threshold
Himax
EV driver’s charging-wait tolerance
Lgg′
Distance from origin grid g to destination grid g′
Pbase, Lbase
Base fare and corresponding base distance
α, β, δ, κ, ζ, τ
Smoothing factors; τ is specifically the target-DQN soft-update factor
γ
Discount factor for future rewards

2.2 Passenger and vehicle attributes
A passenger request contains origin, destination, price sensitivity εj,t, request time and maximum wait duration. The manuscript states that the PO does not observe individual εj,t or Tj. The PO estimates population-level elasticity statistics from historical ride-hailing data.
Each vehicle has a current grid, busy/idle state, minimum acceptable dispatch price and maximum tolerated dispatch wait. EVs additionally have stored energy, battery capacity, an energy threshold and charging-wait tolerance. These individual attributes are private to the vehicle.
3. Passenger price sensitivity and acceptance
3.1 Empirical elasticity calculation
The manuscript defines passenger price elasticity as the ratio of percentage change in distance to percentage change in price. The supervisor meeting describes calculating it from distance-binned historical trip/fare statistics.
ε = (ΔL / Lbase) ÷ (ΔP / Pbase)
The calculation workflow discussed in the meetings is:
Aggregate historical trips by distance intervals. The current analysis used 500-metre distance breakups; changing to 100-metre or 1-kilometre bins changes the resulting empirical estimates.
For each distance interval, calculate the relevant mean fare/price and request count. Use the distance-bin lower limit in the elasticity calculation as described by the supervisor.
Choose a common Lbase from the representative distance observations that are close to the selected base distance; the meeting describes Lbase as an average of the selected values.
Choose a common Pbase as the observed fare closest to the selected base fare, using the request counts/distribution in the empirical analysis.
Calculate ε values across the distance intervals using the common Lbase and Pbase, then form the empirical distribution of the resulting elasticity values.
Important: distance bins are used to estimate the population elasticity distribution. The supervisor explicitly says not to assign a different elasticity to each customer solely according to that customer’s distance bin. Once estimated, draw an elasticity from the appropriate population distribution and use it for each simulated passenger.
3.2 Weather and time-conditioned distributions
Repeat the elasticity estimation after filtering the historical data by weather condition and time interval. The goal is to obtain a distribution for each supported weather/time pattern rather than one pooled distribution only.
Use the same aggregate Lbase and Pbase across weather/time subsets; the meeting says these common base values were selected from the aggregate data. Subset-specific empirical lower/upper bounds and elasticity distributions may differ.
The weather representation must be consistent between the CNN demand predictor and the passenger-sensitivity model. If the predictor uses categorical weather classes (for example, normal/rain/snow encoded as categories), the elasticity model must use the same classification. If temperature, wind speed or other continuous weather variables are included in the predictor, the sensitivity model must account for those same variables rather than using an inconsistent definition of “weather”.
Time need not automatically be modelled hour by hour. The supervisor suggests testing coarser time intervals (for example, 2-hour or 4-hour groups) and merging intervals only when the empirical elasticity patterns are sufficiently similar.
For each weather/time pattern, report the mean and standard deviation and the fitted distribution’s lower and upper truncation limits. Also report the population percentage/counts so that the proportions across all patterns sum to 1 (or 100%).
3.3 Distribution fitting and sampling
The pooled empirical elasticity distribution discussed in the meeting was described as having a long lower tail and a shorter upper tail. A rough aggregate mean of about 2.31 and standard deviation around 0.4 were mentioned, with observed values discussed as ranging from 0 to approximately 2.813. These were conversational/illustrative figures from an earlier analysis, not a final validated parameter table.
Candidate distribution families explicitly mentioned: exponential or “ZIF” .
A truncated normal distribution was also discussed as a possible approximation, with a stated need to report its mean, standard deviation and lower/upper truncation bounds. The supervisor cautioned that a normal distribution may not represent the skewed empirical shape well; it was presented as a possible approximation to test, not an unquestioned final choice.
For a weather/time pair, fit candidate distributions to that pair’s empirical elasticity observations, compare goodness of fit, select the best-supported family and parameters, then sample and truncate to the empirically justified support.
All elasticity values in the discussed empirical results were positive; the supervisor says to use a positive magnitude within the observed range. Do not invent a universal upper cap: estimate/report the empirical support for each pattern.
Sparse weather/time combinations may have too few observations or no requests. Do not claim a reliable distribution for an empty group. Consider combining adjacent time intervals only when the empirical patterns support it, or document the group as unsupported.
3.4 Passenger acceptance condition
The DQN selects a pricing factor for an OD pair before requests are realized. The dispatch price is the pricing factor multiplied by the common base fare:
(1)   Pdisp(g,g′,t) = a(g,g′,t) × Pbase
A passenger accepts the offered dispatch price when the following condition from the manuscript is satisfied:

(2)   P_disp(g,g′,t) ≤ P_base + (P_base / ε_j,t) × ((L_g,g′ − L_base) / L_base)
Here P_disp is the DQN-selected offered dispatch price; L_g,g′ is the OD distance; L_base and P_base are the aggregate reference values; ε_j,t is the passenger's sampled elasticity for the current weather/time pattern. Apply the inequality per request to decide accept/reject. The equation and corrected P_base term are the manuscript/supervisor version.
Implementation checks: protect against ε=0 in numerical code (the empirical support may include zero); define a documented positive sampling floor or a zero-handling rule before evaluating the division.
4. CNN demand prediction module
Experimental Configuration

Parameter
Proposed configuration
Study area
New York City
Dataset period
1 January–31 March 2026
Dataset source
NYC Taxi and Limousine Commission (TLC) trip records
Primary dataset choice
Select one consistent taxi dataset (Yellow Taxi or Green Taxi) for the primary experiment
Prediction model
2D convolutional neural network (CNN)
Input feature channels
Seven channels, following the feature design described in the reference paper
Daily time resolution
48 half-hour slots per normal local day
Forecast horizon
Next 30 minutes (one slot ahead)
Spatial environment
 grid environment, subject to verification of grid mapping and geometry
Input tensor
N × 7 × H × W
Output tensor
N × 1 × H × W
Evaluation
MAE, RMSE, actual-versus-predicted tables, plots, heatmaps and error analysis
Dataset selection note: Yellow Taxi, Green Taxi and High Volume FHV represent different service populations and data collection processes. Choose one for the primary experiment and keep it consistent. 
Overall Implementation Workflow
Module 1: Collect January, February and March 2026 NYC TLC data.
Module 2: Clean records and document every exclusion rule.
Module 3: Map pickup locations to the existing grid environment.
Module 4: Convert pickup timestamps into 30-minute slots.
Module 5: Generate actual demand counts for every grid and slot.
Module 6: Construct the seven CNN input feature maps.
Module 7: Create input tensors and next-slot ground-truth labels.
Module 8: Implement, train and validate the CNN.
Module 9: Generate next-30-minute demand forecasts.
Module 10: Calculate MAE and RMSE on held-out test data.
Module 11: Verify actual versus predicted demand at grid and city levels.
Module 12: Export forecasts for downstream pricing, supply, dispatch and repositioning modules.

Module 1 – Dataset Collection
Download the monthly Parquet files for January, February and March 2026 from the official NYC TLC Trip Record Data portal. For the primary experiment, use one consistent dataset type. The core fields required for demand counting are pickup datetime and pickup location ID.
Required fields: pickup datetime, pickup location ID, drop-off datetime, drop-off location ID, trip distance and fare amount. Pickup datetime and pickup location ID are the essential fields for constructing the demand target.
import pandas as pd jan = pd.read_parquet("2026-01.parquet") feb = pd.read_parquet("2026-02.parquet") mar = pd.read_parquet("2026-03.parquet") df = pd.concat([jan, feb, mar], ignore_index=True) print(df.shape) print(df.head()) print(df.info())import pandas as pd jan = pd.read_parquet("2026-01.parquet") feb = pd.read_parquet("2026-02.parquet") mar = pd.read_parquet("2026-03.parquet") df = pd.concat([jan, feb, mar], ignore_index=True) print(df.shape) print(df.head()) print(df.info())Example loading code:
import pandas as pd jan = pd.read_parquet("2026-01.parquet") feb = pd.read_parquet("2026-02.parquet") mar = pd.read_parquet("2026-03.parquet") df = pd.concat([jan, feb, mar], ignore_index=True) print(df.shape) print(df.head()) print(df.info())
import pandas as pd jan = pd.read_parquet("2026-01.parquet") feb = pd.read_parquet("2026-02.parquet") mar = pd.read_parquet("2026-03.parquet") df = pd.concat([jan, feb, mar], ignore_index=True) print(df.shape) print(df.head()) print(df.info())
Check the actual filenames and Parquet schema before running the code; TLC column names can differ by dataset type and year.
Module 2 – Data Cleaning
Remove records with missing pickup timestamps.
Remove records with missing or invalid pickup location IDs.
Check duplicate records using an appropriate record-identification rule.
Restrict records to the January–March 2026 study period.
Check timestamp validity and logical pickup/drop-off ordering.
Investigate zero or extreme trip distances (less than or equal to 75 km) rather than automatically deleting all such records.
Record the number of rows removed by each cleaning rule.

Output: cleaned_nyc_2026.parquet and a cleaning report containing original records, missing timestamps, invalid locations, duplicates, removed records and final valid records.

Module 3 – Map Pickup Locations
The  environment contains xx grids. The taxi pickup location IDs must be connected to those same grid IDs through a verified spatial mapping. TLC taxi records generally provide taxi-zone IDs rather than individual GPS pickup coordinates.
If taxi-zone polygons and custom grid polygons are available, use a documented spatial assignment method. One possible approximation is to assign each taxi zone through its centroid. Document the method and assess its limitations.
Mapping relationship: Grid_i = Map(PULocationID_i).
Output: a mapping table with pickup datetime, pickup location ID and assigned grid ID. Do not assume a taxi-zone ID is itself one of the custom grid IDs.

Module 4 – Generate 48 Daily Time Slots
For a normal New York local day, divide 24 hours into 48 half-hour intervals.

Slot
Local time interval
0
00:00–00:30
1
00:30–01:00
2
01:00–01:30
3
01:30–02:00

Slot
Local time interval
…
…
45
22:30–23:00
46
23:00–23:30
47
23:30–00:00
df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"]) # Convert/localize timestamps to America/New_York as appropriate. df["slot"] = ( df["pickup_datetime"].dt.hour * 2 + df["pickup_datetime"].dt.minute // 30 ) df["date"] = df["pickup_datetime"].dt.date df["day_of_week"] = df["pickup_datetime"].dt.dayofweek df["hour"] = df["pickup_datetime"].dt.hourdf["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"]) # Convert/localize timestamps to America/New_York as appropriate. df["slot"] = ( df["pickup_datetime"].dt.hour * 2 + df["pickup_datetime"].dt.minute // 30 ) df["date"] = df["pickup_datetime"].dt.date df["day_of_week"] = df["pickup_datetime"].dt.dayofweek df["hour"] = df["pickup_datetime"].dt.hour
df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"]) # Convert/localize timestamps to America/New_York as appropriate. df["slot"] = ( df["pickup_datetime"].dt.hour * 2 + df["pickup_datetime"].dt.minute // 30 ) df["date"] = df["pickup_datetime"].dt.date df["day_of_week"] = df["pickup_datetime"].dt.dayofweek df["hour"] = df["pickup_datetime"].dt.hour
df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"]) # Convert/localize timestamps to America/New_York as appropriate. df["slot"] = ( df["pickup_datetime"].dt.hour * 2 + df["pickup_datetime"].dt.minute // 30 ) df["date"] = df["pickup_datetime"].dt.date df["day_of_week"] = df["pickup_datetime"].dt.dayofweek df["hour"] = df["pickup_datetime"].dt.hour




Ensure that timezone conversion is correct for the source timestamps before deriving local dates and slots.
Module 5 – Generate Actual Passenger Demand
Count valid pickup records for every grid and 30-minute slot. This observed pickup count is the ground-truth demand proxy, consistent with the reference paper's use of request counts when request-to-order conversion data are unavailable.
demand_df = ( df.groupby(["date", "slot", "grid_id"]) .size() .reset_index(name="actual_demand") )demand_df = ( df.groupby(["date", "slot", "grid_id"]) .size() .reset_index(name="actual_demand") )D(g,t) = sum over records i of 1[Grid_i = g and Slot_i = t].
demand_df = ( df.groupby(["date", "slot", "grid_id"]) .size() .reset_index(name="actual_demand") )
demand_df = ( df.groupby(["date", "slot", "grid_id"]) .size() .reset_index(name="actual_demand") )
Create a complete date × slot × valid-grid index. Fill unobserved valid grid-slot combinations with zero only when the absence of records truly means zero observed pickups. Preserve a spatial validity mask for inactive or out-of-area cells.
Output: actual_demand_30min.parquet, with date, slot, grid_id and actual_demand.

Module 6 – Generate the Seven CNN Input Features

Channel
Feature
How it is represented
1
Day of week
Day category/value for the forecast target time, mapped across the spatial grid
2
Hour of day
Hour value (0–23) for the forecast target time
3
Period of hour
For half-hour slots: first half or second half of the hour
4
Weather type
Weather category at forecast time, encoded consistently
5
Temperature
Temperature at forecast time, in a consistent unit
6
Wind speed
Wind speed at forecast time, in a consistent unit
7
Historical average demand
Grid-specific average demand for comparable historical weekday/time periods
Historical average demand
For each grid, calculate the average demand over comparable historical periods, such as previous occurrences of the same weekday and half-hour slot. Use only information available before the forecast is made.
H(g,t) = average of D(g, comparable historical periods).
For example, if Grid 101 had demand values 25, 30, 28, 33 and 24 across five previous comparable Mondays at 09:00, the historical average is 28.
Weather data: use weather information that would have been available at prediction time, such as an archived forecast. Do not use future observed weather in a historical back test unless it is explicitly treated as an oracle-information experiment.
Module 7 – Prepare Training Inputs and Labels
Use one-step-ahead supervised forecasting: X_t  Y_(t+1). X_t contains the seven feature matrices available at the forecast origin. Y_(t+1) is the actual pickup-count matrix during the following 30-minute interval.

Forecast origin
Target interval
CNN label
09:00
09:30–10:00
Actual demand in that interval
09:30
10:00–10:30
Actual demand in that interval
10:00
10:30–11:00
Actual demand in that interval
10:30
11:00–11:30
Actual demand in that interval

Tensor shapes: X = (number_of_samples, 7, H, W); Y = (number_of_samples, 1, H, W).

Chronological data split

Partition
Dates
Purpose
Training
1 January–20 February 2026
Learn CNN parameters
Validation
21–28 February 2026
Tune hyperparameters and early stopping
Testing
1–31 March 2026
Final evaluation on unseen dates
These are proposed date ranges. Use chronological splits, not random row splits. Historical features must be generated without using future observations. Ideally obtain December 2025 data for historical warm-up only; if restricted to January–March, exclude early samples that lack sufficient historical context.

Module 8 – CNN Architecture

Layer
Configuration
Output shape
Input
7 channels
7 × H × W
Conv2D + ReLU
32 filters, 3 × 3, stride 1, padding 1
32 × H × W
Conv2D + ReLU
64 filters, 3 × 3, stride 1, padding 1
64 × H × W
Conv2D + ReLU
128 filters, 3 × 3, stride 1, padding 1
128 × H × W
Conv2D + ReLU
64 filters, 3 × 3, stride 1, padding 1
64 × H × W
Output Conv2D
1 filter, 1 × 1
1 × H × W
Softplus
Nonnegative regression output
1 × H × W
import torch import torch.nn as nn class CNNDemandPredictor(nn.Module): def  init (self):super(). init () self.network = nn.Sequential( nn.Conv2d(7, 32, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 1, kernel_size=1), nn.Softplus() ) def forward(self, x): return self.network(x) model = CNNDemandPredictor() criterion = nn.MSELoss() optimizer = torch.optim.Adam(model.parameters(), lr=0.001)import torch import torch.nn as nn class CNNDemandPredictor(nn.Module): def  init (self):super(). init () self.network = nn.Sequential( nn.Conv2d(7, 32, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 1, kernel_size=1), nn.Softplus() ) def forward(self, x): return self.network(x) model = CNNDemandPredictor() criterion = nn.MSELoss() optimizer = torch.optim.Adam(model.parameters(), lr=0.001)This is a proposed baseline fully convolutional network, not a claim that these exact layer counts or hyperparameters are specified by the reference paper.
import torch import torch.nn as nn class CNNDemandPredictor(nn.Module): def  init (self):
super(). init () self.network = nn.Sequential( nn.Conv2d(7, 32, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 1, kernel_size=1), nn.Softplus() ) def forward(self, x): return self.network(x) model = CNNDemandPredictor() criterion = nn.MSELoss() optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
import torch import torch.nn as nn class CNNDemandPredictor(nn.Module): def  init (self):
super(). init () self.network = nn.Sequential( nn.Conv2d(7, 32, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(32, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(128, 64, kernel_size=3, padding=1), nn.ReLU(), nn.Conv2d(64, 1, kernel_size=1), nn.Softplus() ) def forward(self, x): return self.network(x) model = CNNDemandPredictor() criterion = nn.MSELoss() optimizer = torch.optim.Adam(model.parameters(), lr=0.001)





Training setting
Initial value
Optimizer
Adam
Learning rate
0.001
Batch size
32

Training setting
Initial value
Maximum epochs
100
Loss
Mean Squared Error
Early stopping
Use validation loss
Checkpoint
Save best validation model

Tune these settings using validation data. Include training and validation loss histories, early stopping and reproducibility controls in the final implementation.

Module 9 – Generate Next-30-Minute Predictions
At forecast origin 09:00, construct X_09:00 from the seven feature maps available at that time. The CNN returns a demand matrix for 09:00–09:30, depending on the agreed target-interval convention. Make the
forecast-origin/target-interval convention explicit and use it consistently.
The model output is a nonnegative, potentially fractional expected count for every grid. Retain decimal values during evaluation; do not round predictions before calculating errors.
Output file: cnn_predicted_demand_30min.parquet.

Column
Meaning
prediction_datetime
Time at which the forecast is generated
target_datetime
Start or label of the target interval, consistently defined
grid_id
Geographical grid identifier
actual_demand
Observed pickup count in the target interval
predicted_demand
CNN forecast for the target interval
absolute_error
Absolute difference
squared_error
Squared difference

Module 10 – Calculate MAE and RMSE
Mean Absolute Error (MAE)
MAE = (1/N) ×  |Y_i  ■_i|. It measures the average absolute difference between actual and predicted passenger demand.
Root Mean Squared Error (RMSE)
RMSE = sqrt[(1/N) ×  (Y_i  ■_i)²]. It penalizes large prediction errors more strongly than MAE.
import numpy as np from sklearn.metrics import mean_absolute_error, mean_squared_error actual = Y_test.flatten() predicted = predictions.flatten() mae = mean_absolute_error(actual, predicted) rmse = np.sqrt(mean_squared_error(actual, predicted)) print("MAE:", mae) print("RMSE:", rmse)import numpy as np from sklearn.metrics import mean_absolute_error, mean_squared_error actual = Y_test.flatten() predicted = predictions.flatten() mae = mean_absolute_error(actual, predicted) rmse = np.sqrt(mean_squared_error(actual, predicted)) print("MAE:", mae) print("RMSE:", rmse)Illustrative example only: actual values [25, 10, 40, 5] and predictions [28, 12, 38, 8] produce absolute errors [3, 2, 2, 3], MAE = 2.5 and RMSE = sqrt(6.5)  2.55. These are not results from the NYC dataset.
import numpy as np from sklearn.metrics import mean_absolute_error, mean_squared_error actual = Y_test.flatten() predicted = predictions.flatten() mae = mean_absolute_error(actual, predicted) rmse = np.sqrt(mean_squared_error(actual, predicted)) print("MAE:", mae) print("RMSE:", rmse)
import numpy as np from sklearn.metrics import mean_absolute_error, mean_squared_error actual = Y_test.flatten() predicted = predictions.flatten() mae = mean_absolute_error(actual, predicted) rmse = np.sqrt(mean_squared_error(actual, predicted)) print("MAE:", mae) print("RMSE:", rmse)



Calculate metrics on the original passenger-count scale after reversing any target normalization. Report the test date range, number of grid-slot observations and the aggregation method. Consider reporting both all-grid metrics and metrics for active/valid grid cells.

Module 11 – Actual-versus-Predicted Verification
Grid-slot comparison table

Date
Target interval
Grid
Actual
Predicted
Abs. error
Example
09:30–10:00
101
25
27.5
2.5
Example
09:30–10:00
102
15
13.8
1.2
Example
10:00–10:30
101
30
28.6
1.4
Example
10:00–10:30
102
20
19.2
0.8

The final table must be generated from actual March test predictions, not manually entered illustrative values.

Time-series plots
Plot actual and predicted demand over time for selected high-demand grids.
Plot actual and predicted demand for selected low-demand grids.
Plot city-wide aggregate actual and predicted demand by target interval.
Use the same target intervals and date ranges for both series.

Spatial heatmaps
For the same target interval, plot an actual-demand heatmap and a predicted-demand heatmap using identical grid geometry and colour scales. Inspect whether the CNN identifies high-demand and low-demand regions and spatial concentration.
Error analysis
Signed error = Actual  Predicted. Positive values indicate underprediction; negative values indicate overprediction. Generate an error heatmap and identify grids or time periods with systematic errors.

Report MAE and RMSE for each model. This helps establish whether CNN improves over simple historical forecasting.

Expected Deliverables

File name
Contents
01_cleaned_nyc_data.parquet
Cleaned January–March 2026 records
02_grid_mapping.csv
Taxi-zone to custom-grid mapping
03_actual_demand_30min.parquet
Observed demand by grid and slot
04_cnn_input_features.npy
Seven-channel CNN input tensors
05_cnn_training_labels.npy
Next-30-minute actual demand labels
06_cnn_best_model.pth
Best trained CNN checkpoint
07_cnn_predictions_march.csv
March actual-versus-predicted results
08_cnn_evaluation.csv
MAE and RMSE metrics
09_actual_vs_predicted.png
Comparison plots

File name
Contents
10_demand_heatmaps.png
Actual and predicted spatial heatmaps
11_error_analysis.png
Prediction error visualizations

Boundary: CNN predicts passenger demand. It does not directly predict driver supply, passenger price sensitivity, waiting time or the optimal pricing factor.


Notebook Execution Sequence

Notebook
Main task
Main output
CNN_NB1_Data_Collection
Download and inspect TLC data
Monthly source files
CNN_NB2_Cleaning
Clean and document exclusions
Cleaned dataset
CNN_NB3_Grid_Mapping
Map taxi zones to custom grids
Grid-mapped trips
CNN_NB4_Demand_Matrix
Build 30-minute demand counts
Actual demand matrices
CNN_NB5_Feature_Engineering
Generate seven feature planes
CNN input tensors
CNN_NB6_Training
Train and validate CNN
Best model checkpoint
CNN_NB7_Evaluation
Forecast, evaluate and verify
MAE, RMSE, plots and tables

Final expected research outcome: A trained CNN that forecasts next-30-minute pickup demand across the verified NYC grid environment, with reproducible March 2026 test results, MAE and RMSE,actual-versus-predicted comparisons, spatial heatmaps, error analysis.Final expected research outcome: A trained CNN that forecasts next-30-minute pickup demand across the verified NYC grid environment, with reproducible March 2026 test results, MAE and RMSE,actual-versus-predicted comparisons, spatial heatmaps, error analysis.
Final expected research outcome: A trained CNN that forecasts next-30-minute pickup demand across the verified NYC grid environment, with reproducible March 2026 test results, MAE and RMSE,
actual-versus-predicted comparisons, spatial heatmaps, error analysis.
Final expected research outcome: A trained CNN that forecasts next-30-minute pickup demand across the verified NYC grid environment, with reproducible March 2026 test results, MAE and RMSE,
actual-versus-predicted comparisons, spatial heatmaps, error analysis.

4.1 Role in the hierarchy
The CNN demand predictor supplies the grid-wise predicted passenger demand J-hat(g,t) for the upcoming slot. It is one input to the top-level DQN state. It is not itself the pricing agent: CNN prediction is implemented as a separate module and its output is passed into the hierarchical simulation.
4.2 Inputs, output and tensor alignment
The predictor may use 2D convolution: provide spatial/grid matrices as inputs and produce a grid-shaped output matrix. If 1D convolution is used instead, reshape each grid matrix to a vector (the supervisor’s example is a 10 × 10 matrix reshaped to 100 × 1). The target matrix/vector must have the same shape as the model output.
The output is a grid-wise predicted request count. It can be fractional because it represents an expected/mean demand value. It must not be negative: if a model output is negative, clamp/round it to zero as discussed.
For grids with no predicted demand, store 0. For grids with predicted demand, retain the nonnegative predicted value.
The actual observed request count and predicted count are distinct. The prediction is used as a state feature/forecast. Actual requests from the dataset are used to realize the slot’s requests and calculate rewards.

5. Top-level destination-based pricing DQN
5.1 State definition
At the beginning of each slot, for every feasible origin–destination pair (g,g′), the PO constructs the state vector:
Sᵘ(g,g′,t) = [ Ĵ(g,t), Ĵdisp(g,t−1), I(g,t), p(g,t), π(g′,t) ]
State component
Meaning / source
J-hat(g,t)
CNN-predicted number of passenger requests in origin grid g during slot t
J-hat-disp(g,t−1)
EWMA estimate of successful dispatches in grid g from the previous slot
I(g,t)
Estimated number of vehicles arriving into grid g to drop off passengers during slot t
p(g,t)
Mean routing-response probability vector for the current grid and its one-hop neighbours; output of the global policy network
π(g′,t)
Popularity of destination grid g′ derived from historical ride demand; may be adapted using a moving average

The state is built separately for every feasible OD pair. The DQN’s input dimension equals the state-vector dimension. The primary and target DQNs have the same input and output dimensions.
5.2 Pricing action space
The DQN output neurons represent a discrete set A of candidate pricing factors. The supervisor’s proposed construction is data-driven:
Find the lower and upper price limits from the NYC dataset. The discussion suggests dividing the lowest observed fare and highest observed fare by Pbase to obtain lower/upper pricing-factor bounds.
Divide this interval into discrete increments, with 0.01, 0.05, 0.1 or 0.15 mentioned as candidate resolutions. These are alternatives to test, not a single final selected step.
Each output neuron corresponds to one pricing-factor action. For a selected action, multiply its factor by Pbase to obtain Pdisp for the OD pair.
The meeting references observed trips/prices extending to approximately 75 km when discussing an upper bound; verify the dataset support and avoid treating 75 km as a universal study-area limit.
Only feasible OD pairs should be considered. If an OD pair has no meaningful historical/demand support, do not create a pointless pricing decision or DQN experience for it.
5.3 Exploration and action selection
Use ε-greedy exploration to populate experiences: with probability ε, select a random action/output neuron; with probability 1−ε, select the action with the maximum Q-value.
The paper gives initial ε = 1 and gradual reduction (example decrement 0.005) until ε = 0.1.
The meeting additionally suggests starting at 1 or 0.99, reducing by 0.005 or 0.01 every 10 iterations, then holding at 0.1. Select and document one schedule in the final experiment configuration.
The meeting clarifies that ε-greedy is for action selection/experience collection. During the DQN update target calculation, select the maximum-Q action from the target network, not a random ε-greedy action.
5.4 Reward and objective
Let xj,t = 1 if passenger j is successfully dispatched, otherwise 0. The OD-pair reward is the sum of successful dispatch prices for requests from g to g′:
(3)   R(g,g′,t) = Σ[j∈Jg,t] Pdisp(g,g′,t) · 1(Dj=g′) · xj,t
The PO maximizes expected discounted revenue across grids, destinations and time:
(4)   max E[ Σt Σg∈G Σg′∈G γᵗ R(g,g′,t) ]
The reward is computed at the end of the slot from successful dispatches only. Rejected requests and unsuccessful dispatches do not contribute revenue under this reward definition.
6. Grid statistics and EWMA updates
The PO periodically broadcasts aggregate grid statistics to vehicles. The paper specifies estimates of dispatch-price mean and deviation, dispatch frequency, and waiting time for charging. The meeting gives practical guidance for the smoothing coefficients.
(5)   μ(g,t) = α · [Σg′ Σj∈Jg,t−1 Pdisp(g,g′,t−1) · 1(Dj=g′) · xj,t−1] / [Σj∈Jg,t−1 xj,t−1] + (1−α) μ(g,t−1)
(6)   σ(g,t) = β · [Σj∈Jg,t−1 Σg′ |Pdisp(g,g′,t−1)−μ(g,t−1)| · 1(Dj=g′) · xj,t−1] / [Σj∈Jg,t−1 xj,t−1] + (1−β) σ(g,t−1)
(7)   F-hat(g,t) = δ · [Σj∈Jg,t−1 xj,t−1 / Δt] + (1−δ) F-hat(g,t−1)
(8)   H-hat(g,t) = κ · H(g,t−1) + (1−κ) H-hat(g,t−1)
μ and σ estimate the mean and deviation of dispatch prices. The manuscript assumes dispatch prices are normally distributed for this driver-utility calculation. F-hat is estimated successful dispatch frequency (dispatches per slot/time unit). H-hat is the estimated EV charging wait in slots, based on observed waiting times in the previous slot.
Implementation note: When no successful dispatch occurs in a grid during a slot, the denominators in (5)–(6) are zero. The sources do not prescribe the exact numerical safeguard. Implement an explicit no-observation rule (for example, retain the previous estimates) and document it; do not divide by zero.

7. Bottom-level driver repositioning and EV charging
7.1 Dispatch and waiting utility
An idle driver evaluates its current grid and one-hop neighbours using private minimum acceptable price Pimin and maximum tolerated dispatch wait Wimax.
(9)   U¹(i,g′′,t) = 1 − Φ( (Pimin − μ(g′′,t)) / σ(g′′,t) )
(10)  U²(i,g′′,t) = 1 − exp(−F-hat(g′′,t) · Wimax)
U¹ is the probability of encountering a dispatch price at least as large as the driver’s minimum acceptable price. U² is the probability of being dispatched within the driver’s tolerated waiting time, under the assumed exponential waiting-time model.
7.2 Repositioning decision
(11)  y(i,t) = arg max[g′′∈Ng] { U¹(i,g′′,t) + U²(i,g′′,t) − C-rep(i,g′′,t) }
The repositioning cost C-rep is the product of the unit travel cost and the distance from the current grid to candidate grid g′′. The selected action is the relative index of the current or neighbouring grid.
7.3 EV charging navigation
An idle EV is eligible to reposition only if its stored energy is above the energy threshold Eimin. If Ei,t ≤ Eimin, it performs charging navigation instead.
(12)  U³(i,g′,t) = 1 − exp(−Himax / H-hat(g′,t))
(13)  D′(i,t) = arg max[g′ with charging availability] { U³(i,g′,t) − C-rep(i,g′,t) }
The vehicle stores the next grid along the path toward the selected charging destination as zi,t. It may recompute the next navigation step until it reaches the charging destination because charging-wait estimates may change during travel.
7.4 Private preferences and privacy
The PO does not receive individual driver preferences (Pimin, Wimax, EV energy and charging tolerance) or individual repositioning/charging decisions.
The PO broadcasts aggregate grid statistics; the driver locally computes utility and makes its own decision.
The paper allows multiple repositioning decisions during a slot. The meeting transcript offers a practical implementation interpretation: define a repositioning interval T′, with at most one repositioning choice per vehicle at a decision opportunity; after moving, the vehicle may get another decision opportunity in the same slot. Finalize this simulator timing rule explicitly.
Only vehicles that remain in their current grid/are available after the repositioning stage contend for dispatch in the described meeting sequence.
8. Federated learning and privacy
The PO maintains a global policy network that maps each grid’s local statistics to a distribution over relative next-grid actions. The global policy produces mean routing probabilities used as the top-level DQN state feature.
Sᶫ(g,t) = [ { μ(g′′,t), σ(g′′,t), F-hat(g′′,t) } for g′′∈Ng ; { H-hat(g′,t) } for charging grids g′∈G ]
p(g,t) = softmax( π(Sᶫ(g,t) | ϕ) )
The output dimension K is |Ng|, i.e. the number of possible relative neighbourhood actions. The local/global policy network is trained using driver-local experiences.
(19)  C(ϕᶫᵢ) = −(1/Nᵢ) Σn=1..Nᵢ Σk=1..K 1(yⁿᵢ=k or zⁿᵢ=k) · log(π(sⁿᵢ | ϕᶫᵢ)k)
(20)  ϕᶫᵢ ← ϕᶫᵢ − ηᶫ ∇ϕᶫᵢ C(ϕᶫᵢ)
(21)  ϕ = (1 / |Iᵗ_idle|) Σ[i∈Iᵗ_idle] ϕᶫᵢ
At the end of each slot, idle vehicles sample Ni local experiences (grid-statistics plus their private repositioning/charging decisions), update their local policy network by minimizing cross-entropy, and upload the updated model parameters. The PO averages the received local parameters to form the global model for the next slot. The meeting mentions using a Rényi-accountant/privacy aggregation equation, but the precise privacy accountant equation/parameters are not reproduced in the uploaded manuscript excerpt/transcripts; implement the exact privacy mechanism specified in the complete project design and report its parameters.
9. Gymnasium simulation environment and slot sequence
The meeting recommends implementing the simulator using a Gymnasium environment so that the environment, observation, action, transition, reward and termination behaviour are reproducible and can be shared through a code repository/GitHub link with the paper.
9.1 Environment state and stored records
Environment object
Required contents
Grid map
Grid IDs, valid neighbours, OD feasibility, distance matrix and charging availability
Time
Episode index, slot index, mini-slot index and simulation clock
Demand
CNN forecast per grid, actual requests per slot, request OD, weather/time class and request arrival time
Vehicle
Vehicle ID internally, current grid, busy status, availability time, dispatch price preference, wait tolerance, EV flag, battery/energy state and charging tolerance
Pricing
DQN state per feasible OD pair, discrete pricing-factor action, selected factor and dispatch price
Grid statistics
EWMA mean/deviation of dispatch price, dispatch frequency, charging wait, arrivals and destination popularity
Learning
DQN replay buffer, primary/target networks, global/local policy network parameters and local private memories

9.2 Required sequence within each slot
Start slot t and obtain the CNN-predicted demand map J-hat(g,t).
Update/assemble PO grid statistics from the preceding slot: estimated dispatches, vehicle arrivals, routing probabilities and destination popularity.
For every feasible OD pair (g,g′), build the state vector and run the pricing DQN. Select a pricing factor using ε-greedy during training; calculate Pdisp = factor × Pbase.
Broadcast updated aggregate grid statistics to vehicles.
Each idle vehicle independently decides whether to stay/reposition or, if it is an EV below its energy threshold, navigate toward a charging station. Preserve private driver attributes and actions.
Generate/realize the actual passenger requests for slot t. The realized request count may differ from the CNN forecast.
For each request, determine its destination (actual dataset destination or the selected destination-sampling procedure), sample passenger elasticity for its weather/time class, and test the acceptance condition (2).
For accepted requests, identify eligible idle vehicles whose minimum acceptable dispatch price is no greater than the offered price. Conduct contention and assign the selected vehicle.
Process requests sequentially within the slot, as advised in the meeting, because the set of available vehicles changes after each dispatch.
Update successful-dispatch indicators, revenue, dispatch counters, vehicle busy status, trip/arrival times and charging events.
At slot end, calculate reward for each OD pair, update EWMA grid statistics and prepare the next state.
Store DQN experiences; train the DQN after the slot when the replay buffer is sufficiently populated.
Vehicles train local routing policies from private memories; aggregate uploaded model parameters at the PO and produce next-slot routing probabilities.
Advance to the next slot. End the episode after T slots or the defined horizon.
9.3 Dispatch contention and travel/arrival accounting
The paper defines a vehicle as eligible to contend for a request when the offered price is at least its Pimin. The PO acknowledges the winner on a first-come-first-served basis.
The meeting suggests assigning among eligible contending vehicles using a random number (for example, uniform in [0,1] or a chosen integer range) and selecting the vehicle with the minimum random value. This is a proposed simulator tie-breaking/selection implementation; document it consistently.
If no vehicle is dispatched within the request’s maximum wait duration Tj, set xj,t = 0.
For a successful dispatch, determine trip travel time and arrival time; map the arrival to its corresponding future slot and increment I(g,t) for the destination grid in that arrival slot.
Increment the successful-dispatch counter Xj,t / grid dispatch count for every successful assignment; this counter feeds the next-slot dispatch-frequency/mean-dispatch estimates.
10. Replay buffer and DQN training algorithm
10.1 Experience tuple
eₘ = (sₘ, aₘ, rₘ, s′ₘ)
Each experience contains the OD-pair state, selected pricing action, slot-end OD reward, and next state. The next state cannot be finalized until slot-end statistics and the updated routing response are available.
10.2 Replay buffer warm-up
The supervisor suggests starting DQN training only after the replay buffer contains approximately 1.5 times the mini-batch size.
Example only: batch size 50 means begin training after at least 75 experiences are stored.
After each slot, if the warm-up condition is met, randomly sample a mini-batch from the buffer and train before proceeding to the next slot.
10.3 Bellman target, loss and updates
For each sampled experience, feed sₘ to the primary DQN and select the action with maximum primary-network Q-value for the current-state prediction. Feed s′ₘ to the target DQN and select its maximum-Q action for the bootstrap target.
a′ₘ = arg maxₐ Qtarget(s′ₘ,a)
eₘ = rₘ + γ Qtarget(s′ₘ,a′ₘ) − Qprimary(sₘ,aₘ)
L(θ,θ̂) = (1 / 2|M|) Σ[m∈M] eₘ²
θ ← θ − ηᵘ ∇θ Qprimary(sₘ,aₘ | θ)
θ̂ ← (1−τ) θ̂ + τ θ
The paper provides the Bellman error, mean-squared loss, gradient update and exponentially weighted target-network update. The meeting clarifies that ε-greedy is used for collecting/exploring actions; the target calculation uses the maximum action value.
10.4 Hyperparameter guidance from the meetings
Parameter
Source guidance
Implementation status
EWMA α, β, δ, κ and other moving-average factors
Use a common value if desired; approximately 0.1–0.2, with 0.125 suggested and 0.2 as an upper suggestion
Choose and record a single value or justify separate values
Target-network τ
Much smaller than EWMA factors; 0.005 or 0.01 discussed; 0.001, 0.005 or 0.01 listed in the later meeting
Select by stability testing; do not set equal to EWMA by default
DQN ε start
1 or 0.99
Choose one
DQN ε decrement
0.005 or 0.01, suggested every 10 iterations
Choose schedule
DQN ε floor
0.1
Use as meeting recommendation
Replay batch size
50 used only as an example
Tune and document
Replay warm-up
1.5 × batch size; example 75 for batch 50
Implement as a configurable threshold
Discount factor γ
Defined in manuscript; no numerical value specified in these four files
Select experimentally and document
Learning rate ηᵘ / ηˡ
Defined symbolically; no numerical value specified
Select experimentally and document

11. Demand, destination and episode generation
11.1 Demand forecast versus realized demand
The CNN provides forecast demand for the PO state. The actual dataset supplies the realized passenger requests used for acceptance, dispatch and reward.
A grid with zero predicted demand should have J-hat = 0. Negative predictions should be clipped to zero. Nonzero predictions may be decimal expected counts.
The meeting states that the CNN predictor is trained using actual observed request counts. For a subsequent simulation round, use the predictor output for the forecast state; the actual request count remains the realized demand. One transcript says the predictor output is discarded for the next round after the CNN prediction/training update; operationally, preserve the distinction between forecast input and actual observed target rather than replacing observed demand with a prediction.
11.2 Destination assignment
Two approaches are explicitly discussed; choose one and state it in the experiment protocol.
Approach
Procedure
When appropriate / caveat
Observed destination from NYC data
Each historical request retains its actual recorded drop-off grid.
Most directly preserves observed OD pairings; the supervisor explicitly says the dataset already contains pickup and drop-off for each trip.
Sampled destination using popularity
Estimate global historical destination popularity; restrict to destinations feasible from the given origin grid; normalize the probabilities over that feasible subset so they sum to one; sample a destination.
Useful when synthesizing requests beyond directly replaying historical OD records. Do not sample from all global destinations without origin-specific feasibility filtering.

If destination popularity π is updated by a moving average, renormalize the destination probabilities after the update so that the probabilities sum to 1.
Different origin grids can have different numbers of feasible destinations (the meeting gives examples of 4, 5 or 10). A destination that never occurs from an origin need not receive a pricing action.
Only create DQN experiences for OD pairs with meaningful destination probability/support or when an actual request occurs.
11.3 OD significance threshold
The supervisor proposes a threshold on the number of drop-offs to a destination: if the count is above a threshold, treat the destination as sufficiently relevant for taxi assignment; below the threshold, the request may be excluded from the taxi-service assignment model or interpreted as served by another transport option. No numerical threshold is supplied. The threshold must be selected from empirical support/validation and documented.
11.4 Episodes and horizon
The supervisor discusses a three-month dataset (approximately 90 days). A direct one-day-per-episode replay would provide at most 90 daily episodes.
More than 90 training episodes may be generated by sampling/rearranging demand according to the empirical demand distribution, provided the aggregate request total is preserved and the distribution across slots/episodes remains consistent with the data.
The total number of requests across the generated episodes should match the underlying dataset total when using a full-data replay/sampling design; their allocation across slots may vary according to the chosen demand-generation procedure.
An episode contains T slots. Slot duration is an example of 30 minutes; a day at this resolution contains 48 slots. The exact episode length/horizon should match the experiment design.
12. Experimental configuration and evaluation
12.1 Values discussed for the first simulation setup
Configuration item
Value / instruction from sources
Study area
NYC taxi dataset / NYC operating region
Grid definition
3 km × 3 km grid proposed in the meeting
Grid indices
Derive from geographic boundary; compute valid neighbours and feasible OD pairs
Time resolution
30-minute slot example in the manuscript
Mini-slot
2-minute example in the manuscript
Fleet size
5,000 vehicles proposed in the meeting
EV penetration
Test 10%, 20%, 30%: 500, 1,000 and 1,500 EVs respectively for a 5,000-vehicle fleet
Weather
Use the same weather classes/features for CNN demand prediction and passenger elasticity
Vehicle speed / travel time
Use travel time to determine movement, trip arrival and repositioning cost; the four files do not give a numeric speed value
Charging
Model charging availability, charging wait and EV energy threshold; numeric battery/charger parameters are not specified
Episodes
Three-month data discussed; daily replay gives 90 episodes, but demand-distribution sampling may create more

The transcript recommends three EV-penetration levels to show a trend; it explicitly says it is not necessary to run 100% EV penetration for the initial results.
12.2 Evaluation measures
Mean total revenue from successful dispatches.
Mean percentage of successful dispatches / dispatch success rate.
Mean repositioning costs.
Passenger price-elasticity distributions and their dependence on weather/time patterns.
Driver preference/routing response and mean routing probabilities.
CNN demand-prediction error, including matrix norm error and aggregate percentage request-count error.
Performance comparison against benchmark frameworks as described in the paper.
12.3 Reproducibility and repository
The supervisor recommends providing a GitHub repository link in the paper with the implementation code and additional analyses. The Gymnasium environment is recommended to make the simulation procedure clear to readers/reviewers. Include the calculations of ε, Lbase and Pbase, weather-conditioned distributions, configuration files, training procedure and analysis scripts.
13. End-to-end implementation checklist
☐ Clean and prepare NYC trip records; retain pickup/drop-off grid, timestamps, fare, distance and weather/time features required by the design.
☐ Fix the study boundary, construct the 3 km × 3 km grid map, enumerate valid grid IDs, neighbours, OD feasibility and distances.
☐ Compute historical OD counts and global destination popularity; derive origin-specific feasible destination subsets.
☐ Compute Lbase and Pbase from aggregate distance/fare statistics and freeze them for all weather/time elasticity subsets.
☐ Calculate empirical passenger elasticity using distance bins; inspect positive support, skewness, counts and population percentages.
☐ Create weather/time-conditioned elasticity groups; choose time aggregation based on empirical similarity and sparse-data support.
☐ Fit and compare candidate elasticity distributions (including the transcript’s exponential and “ZIF” candidate; evaluate truncated normal as a possible approximation); document parameters and truncation bounds.
☐ Implement passenger elasticity sampling and acceptance condition (2), using consistent weather/time feature definitions.
☐ Train/validate the CNN predictor using actual grid-wise request counts; confirm all seven input planes and output tensor shape in the separate CNN specification.
☐ Clamp negative CNN demand predictions to zero; preserve fractional expected counts and write zero for grids with no predicted demand.
☐ Define the DQN OD state vector and discrete pricing-factor action set using observed fare bounds divided by Pbase.
☐ Implement the Gymnasium environment, vehicle state transitions, mini-slot request arrivals, trip travel/arrival time and charging events.
☐ Implement EWMA grid statistics and safe handling of no-dispatch/no-observation cases.
☐ Implement private driver utility, repositioning and EV charging navigation; ensure individual preferences/actions are not exposed to the PO.
☐ Implement the global routing policy, local driver updates, aggregation and the required privacy/accounting mechanism.
☐ Implement OD reward calculation, DQN replay buffer, warm-up, ε-greedy action collection, Bellman loss and target-network soft update.
☐ Run the three EV penetration experiments (10%, 20%, 30%) with the 5,000-vehicle fleet.
☐ Evaluate CNN error, passenger elasticity, dispatch success, revenue, repositioning cost and routing response; compare benchmarks.
☐ Save random seeds, environment configuration, model hyperparameters, training logs and plots; prepare the GitHub repository.
14. Decisions and parameters requiring finalization
The following points are not numerically or structurally fixed by the four uploaded sources. They should be finalized before claiming the implementation is fully specified.
Open item
What the sources say
Required action
Seven CNN planes
Seven planes are mentioned; weather, wind and temperature are examples.
Attach the definitive CNN input-channel specification and tensor shape.
CNN architecture/training
CNN predictor is separate; matrix/vector alignment and norm-based error are discussed.
Document layers, kernels, channels, optimizer, loss, split, epochs and final metrics from the actual implementation.
Elasticity distribution family
Exponential or “ZIF” is suggested; truncated normal is discussed as a possible approximation but may fit poorly.
Confirm what “ZIF” means; compare fits per weather/time group and select empirically.
Elasticity support and sparse groups
Positive values and truncation are required; groups may have few/no observations.
Report group-specific sample counts, mean, SD, support and truncation limits; define handling of unsupported groups.
Lbase and Pbase
Common values selected from aggregate data; exact numeric values are not present in these four files.
Insert the final empirical values and reproducible derivation.
Pricing action bounds/resolution
Bounds from observed fares divided by Pbase; increments 0.01/0.05/0.1/0.15 are candidates.
Choose lower/upper factor and step size; ensure prices remain within the intended dataset-supported range.
Feasible OD threshold
Only significant destination probabilities/drop-off counts should generate experiences; no threshold number supplied.
Set and justify the minimum OD count/probability threshold.
Destination generation
Use observed NYC drop-offs or sample from origin-feasible normalized popularity.
Select one primary method and document any sensitivity/ablation comparison.
Demand episode sampling
90-day replay or additional episodes from empirical demand distributions are discussed.
Specify episode construction, request conservation, randomization and train/test temporal split.
EWMA factors
0.125 suggested; range 0.1–0.2 / maximum 0.2 discussed.
Choose α, β, δ, κ and any other smoothing coefficients.
DQN tau
0.001, 0.005 or 0.01 suggested; much smaller than EWMA factors.
Select τ based on training stability.
DQN schedule and batch
ε starts 1/0.99, decays 0.005/0.01 every 10 iterations to 0.1; batch 50 is only an example.
Fix batch size, buffer capacity, warm-up threshold, ε decay cadence and update frequency.
γ and learning rates
Symbols defined in manuscript; no numerical values in uploaded sources.
Tune and report discount factor and primary/local learning rates.
Dispatch contention tie-break
First-come-first-served in paper; random-number minimum described in meeting implementation.
Clarify whether FCFS request ordering plus random eligible-vehicle selection is the final implementation.
Repositioning cadence T′
A periodic repositioning interval is suggested in meeting; paper allows multiple decisions per slot.
Specify exact decision timing and whether a vehicle can move more than once per slot.
Vehicle speed and costs
Travel distance and unit travel cost define repositioning cost; travel time determines arrival slot.
Specify speed model, travel-time computation, unit cost and EV energy consumption.
EV/charging parameters
EV shares 10/20/30%; energy threshold and charging wait appear symbolically.
Set battery capacity, initial SOC distribution, energy threshold, charger locations, charging rates and charging cost.
Privacy accounting
Federated averaging is in paper; meeting mentions a Rényi accountant.
Specify privacy mechanism, clipping/noise/accountant parameters and report privacy guarantees.
No-data numerical safeguards
Equations may have zero denominators or unavailable destinations.
Define safe fallback for zero successful dispatches, zero σ, empty destination support and missing weather groups.

Final implementation order
Recommended build order: (i) spatial/data preparation; (ii) aggregate base fare/base distance and elasticity estimation; (iii) CNN demand prediction; (iv) destination popularity and feasible OD construction; (v) Gymnasium environment and vehicle dynamics; (vi) EWMA grid statistics; (vii) driver repositioning/EV charging and global routing policy; (viii) DQN pricing and replay training; (ix) federated aggregation/privacy; (x) full experiments and evaluation. Validate each module independently before coupling it into the complete slot loop.
```
