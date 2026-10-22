"""Document a completed CNN run without training or inference."""
from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pandas as pd
import yaml
R=ROOT/'results/analysis/2026-10-19_final_jan_mar_3km_cnn'
D=ROOT/'data/processed/cnn_jan_mar_2026_3km_30min'
M=ROOT/'models/cnn/jan_mar_2026_3km_30min'
m=json.loads((R/'metrics.json').read_text())
comparison=pd.DataFrame([
 {'property':'Dataset period','Old CNN':'January2026','Final CNN':'January–March2026'},
 {'property':'Grid cell side','Old CNN':'3000USsurveyfeet =914.401829m','Final CNN':'3000metres EPSG:32118'},
 {'property':'Valid grid count','Old CNN':'1213','Final CNN':'142'},
 {'property':'Raster','Old CNN':'51x52','Final CNN':'16x16'},
 {'property':'Forecast horizon','Old CNN':'next30minutes','Final CNN':'next30minutes, explicit forecast_timestamp'},
 {'property':'Input channels','Old CNN':'HistoricalDemand,Temperature,WindSpeed,WeatherCode,DayOfWeek,Hour,Period','Final CNN':'DayOfWeek,Hour,PeriodWithinHour,WeatherType,Temperature,WindSpeed,HistoricalAverageDemandDistribution'},
 {'property':'Architecture','Old CNN':'7->32->64->32->1, linear output','Final CNN':'7->14->7->1, allReLU, valid-cell mask'},
 {'property':'Split','Old CNN':'January outer chronological split plus internal validation','Final CNN':'TrainJan–Feb;validationMar1–15;testMar16–31'},
 {'property':'Preprocessing','Old CNN':'Expanding historical averages; scaling includes internal validation interval','Final CNN':'Frozen TRAIN-only lookup/scalers; no imputation needed'},
 {'property':'Status','Old CNN':'KEEP_PROVENANCE / SUPERSEDED_FOR_FINAL_JAN_MAR_3KM_CNN','Final CNN':'Selected best validation checkpoint; test evaluated once'}])
comparison.to_csv(R/'old_vs_final_cnn.csv',index=False)
metrics_table=pd.read_csv(R/'baseline_comparison.csv').to_string(index=False,float_format=lambda x:f'{x:.6f}')
verdict='outperformed both baselines on MAE and RMSE' if m['cnn_beats_both_on_mae_and_rmse'] else 'did not outperform both baselines on both MAE and RMSE'
readme=f'''# Final Jan–Mar 2026 true-3-km CNN demand predictor

## Purpose and source contract

Produce J_hat(g,t), requests for valid Grid_ID g during `[forecast_timestamp, forecast_timestamp+30 minutes)`. It is the prediction for the next main slot, issued at its preceding boundary; there is **no one-slot target shift**. Forecast-time calendar/weather features are explicit. The30-minute horizon is a **DOCUMENTED_ADAPTATION**, not the reference paper's10-minute horizon. Simulator mini-slots remain2minutes and are unrelated to CNN targets.

The validated migration source is `data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet`. It contains4320 half-hour slots and613440 grid/time rows, including zeros. Requests: January3,699,644;February3,377,979;March3,928,571;total11,006,194. Active grid EPSG:32118:3000m squares,142 valid grids,16×16 raster,114 masked cells. Source and geometry hashes are persisted; no old grid/tensor enters training.

## Chronological partitions and tensor alignment

|Partition|Inclusive start|Exclusive end|Slots|X|Y|
|---|---|---|---:|---|---|
|TRAIN|2026-01-01|2026-03-01|2832|[2832,7,16,16]|[2832,1,16,16]|
|VALIDATION|2026-03-01|2026-03-16|720|[720,7,16,16]|[720,1,16,16]|
|TEST|2026-03-16|2026-04-01|768|[768,7,16,16]|[768,1,16,16]|

Features and targets share the forecast timestamp. Target totals reconcile with the source at every timestamp; eight representative boundary/interior samples passed before full tensor generation. No slot is discarded to implement a misleading shift. Batch order is chronological; timestamps are never shuffled between partitions.

## Seven input planes and leakage protection

1. **DayOfWeek:** forecast weekday, Monday0–Sunday6, divided by6.
2. **Hour:** forecast hour0–23, divided by23.
3. **PeriodWithinHour:** minute00=0;minute30=1.
4. **WeatherType:** original Meteostat `coco` → project `WeatherCode`, divided by27, one scalar plane. Retains the legacy numeric code representation with fixed project normalization; not passenger CLEAR/RAIN. Numeric encoding does not claim weather categories form a physical ordered scale.
5. **Temperature:** forecast-time source temperature, z-scored using TRAIN hourly mean/population SD.
6. **WindSpeed:** forecast-time source wind, same TRAIN-only z-score procedure.
7. **HistoricalAverageDemandDistribution:** TRAIN mean by GridID,weekday,half-hour-of-day, divided by the TRAIN historical-plane population SD. It is not previous-slot, current-slot or future observed demand.

Fallback: same GridID+half-hour TRAIN mean → same GridID overall TRAIN mean → zero only without TRAIN history. The complete dense TRAIN domain provides all336 temporal combinations per grid; fallback is retained for inference robustness. The lookup is fitted once on January–February, including their targets as training data, then frozen for held-out inference. Training examples use this fitted TRAIN lookup; they are not online expanding-window backtests.

All learned statistics use TRAIN only. Validation selects the checkpoint; TEST never fits preprocessing or selects epochs. Invalid raster cells are zero **after** transformation and excluded from both loss and metrics. Existing weather metadata confirms zero missing values before filling for all three months; this pipeline adds no imputation. Fixed calendar/code divisors are implementation constants, not learned held-out statistics.

## Model and one training run

External layout `[B,7,16,16] → [B,1,16,16]`; TensorFlow internally permutes to channels-last for convolution. Three Conv2D layers:7→14→7→1, allReLU including output,3×3 kernel,stride1,same padding. These unspecified kernel/training choices are **PROJECT IMPLEMENTATION**, not claimed source-paper parameters. A fixed output mask zeroes unused cells. Masked MSE sums valid-cell squared error and divides by142.

TensorFlow/Keras (existing project environment), Adam learning rate0.001,batch64,max100epochs,early-stopping patience10,seed42. Python,NumPy,TensorFlow seeds and deterministic operations enabled; CPU thread limits recorded in the training script. No PyTorch dependency was installed. No hyperparameter search or second training configuration. The initial implementation/parser corrections occurred before any optimizer update. Best checkpoint is the lowest validation MSE.

Epochs run: **{m['epochs_run']}**. Best epoch: **{m['best_epoch']}**.
Validation MAE **{m['validation']['MAE']:.6f}**,RMSE **{m['validation']['RMSE']:.6f}**.
The selected saved checkpoint was reloaded before one TEST inference/evaluation.

## Test evaluation and baselines

All metrics use exactly768×142 valid cells. R² is pooled across those observations. MAPE is omitted because zero-demand cells make it unsuitable as a primary metric.

```text
{metrics_table}
```

The CNN **{verdict}**. No performance claim is inferred from architecture alone. HistoricalAverage is the frozen grid-specific weekday/half-hour TRAIN predictor. Seasonal is the frozen weekday/half-hour TRAIN mean **across grids**, broadcast spatially; it deliberately omits grid-specific baselines. Neither uses TEST outcomes.

Test prediction range: {m['test_prediction_range']}. Observed range: {m['test_observed_range']}. Predictions are finite/nonnegative, without post-hoc positive clipping. ReLU enforces nonnegativity. Spatial and temporal tails can still be underestimated; inspect diagnostic maps rather than interpreting aggregate metrics as uniform performance.

## Saved model and downstream interface

- Dataset: `data/processed/cnn_jan_mar_2026_3km_30min/`:X/Y tensors,forecast timestamps,mask,lookup/fallbacks,seasonal baseline,source/split/feature/preprocessing/grid metadata.
- Selected checkpoint: `models/cnn/jan_mar_2026_3km_30min/best.keras`; training config,history,best epoch and preprocessing provenance alongside it.
- Canonical forecast: `results/analysis/2026-10-19_final_jan_mar_3km_cnn/dqn_ready_forecasts.parquet`.
- Identical explicit test artifact:`test_predictions.parquet`.

Forecast columns:`forecast_timestamp,Grid_ID,predicted_demand,observed_demand,split`. There are **{m['forecast_rows']:,} rows**, **768 timestamps**,142 IDs per timestamp,continuous30-minute cadence,no duplicates or missing grid/timestamp combinations. The artifact covers TEST only; it does not claim forecasts outside March16–31. `predicted_demand` is J_hat(g,t). `observed_demand` is evaluation-only and must not enter runtime state.

`src/demand/final_cnn.py:FinalDemandPredictor` reloads the model and frozen preprocessing for caller-supplied forecast-time weather/calendar rows. No refit occurs. Configuration points explicitly to the versioned dataset/checkpoint/forecast; legacy runtime remains blocked pending other required migrations.

## Figures

`charts/test_maps_first.png`, `test_maps_middle.png`, `test_maps_highest_demand.png` each contain observed,predicted,absolute-error maps with invalid cells masked. `charts/test_total_demand.png` compares total TEST demand over time. The highest-demand diagnostic is selected only after model selection; it does not affect training.

## Provenance, limitations and next dependency

`old_vs_final_cnn.csv` compares methodology and provenance. Old January/~914m/1213-grid/51×52 artifacts remain **KEEP_PROVENANCE** and **SUPERSEDED_FOR_FINAL_JAN_MAR_3KM_CNN**. Old/new raw metrics are not like-for-like. Protected-artifact hashes verify Record-029,epsilon/support,final weather scenarios and old models remain unchanged. No passenger acceptance,routing,FedAvg,pricing,charging,DQN,privacy or robustness behavior is changed.

This is a retrospective conditional-weather evaluation: weather aligned to the forecast interval is observed historical weather, **not an archived ex-ante weather forecast**. Live use needs weather available at issuance time; future observed weather must not be claimed available operationally. The inherited timezone-naive alignment is unchanged. Taxi-zone-based stochastic spatial assignment and three months of history limit generalization. The fixed numerical weather plane is simple but categorical distances are not physically meaningful. TEST was evaluated once; reporting and tests reuse saved predictions.

Run implementation:`PYTHONDONTWRITEBYTECODE=1 python -B scripts/train_final_cnn.py`. Completed evaluation prevents unnecessary retraining. A training-start marker prevents silent reruns after interruption. Focused validation: **22 run, 22 passed, zero failed** (`test_results.json`). Run `PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/final_cnn_matplotlib python -B scripts/test_final_cnn.py`. No training-bearing legacy tests are required.

Next stages, **not executed here**:correct μ,σ,F_hat,H_hat;driver U1/U2 andEV U3;charging navigation and nine-action global routing state;retrain routing/plainFedAvg;resolve passenger-acceptance/reward contracts;assemble `[J_hat,J_disp,I,p,destination_popularity]`;implement pricingDQN;then run a short non-private hierarchical episode. There is no missing CNN artifact blocking operational-statistics implementation. Live weather availability and downstream contracts remain explicit deployment limitations.
'''
(R/'README.md').write_text(readme)
cpath=ROOT/'config/config.yaml';c=yaml.safe_load(cpath.read_text())
c['data']['cnn_dataset_dir']=str(D.relative_to(ROOT))
c['cnn'].update(preprocessing_status='TRAINED_VALIDATED',split='TRAIN_JAN_FEB_VALIDATION_MAR01_15_TEST_MAR16_31',
 model_path=str((M/'best.keras').relative_to(ROOT)),forecast_path=str((R/'dqn_ready_forecasts.parquet').relative_to(ROOT)),
 feature_channels=['DayOfWeek','Hour','PeriodWithinHour','WeatherType','Temperature','WindSpeed','HistoricalAverageDemandDistribution'],
 training_start='2026-01-01 00:00:00',training_end_exclusive='2026-03-01 00:00:00',validation_end_exclusive='2026-03-16 00:00:00')
cpath.write_text('# Active true-metre spatial foundation and final Jan–Mar CNN.\n'+yaml.safe_dump(c,sort_keys=False))
print('Final CNN report and CNN-specific config updated')
