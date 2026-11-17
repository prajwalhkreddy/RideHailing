"""Development-only tensor/timing diagnostic; never trains or exports predictions."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.demand.causal_timing import build_oracle,VERSION,ZONE
OUT=ROOT/'results_v2/cnn_demand/2026-11-17_causal_timing'
source=ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet'
d=pd.read_parquet(source,filters=[('TimeSlot','<',pd.Timestamp('2026-03-17')),('TimeSlot','>=',pd.Timestamp('2026-01-01'))])
grid=pd.read_parquet(ROOT/'data/processed/grid_lookup.parquet',columns=['GridID','Row','Column'])
x,y,t,bad=build_oracle(d,grid);OUT.mkdir(exist_ok=True)
np.save(OUT/'X_oracle_development.npy',x);np.save(OUT/'Y_development.npy',y);t.to_csv(OUT/'sample_timing.csv',index=False);bad.to_csv(OUT/'nonexistent_civil_slots.csv',index=False)
mask=np.zeros((16,16),np.uint8);mask[grid.Row,grid.Column]=1;np.save(OUT/'valid_mask.npy',mask)
assert np.array_equal(mask,np.load(ROOT/'data/processed/cnn_jan_mar_2026_3km_30min/valid_mask.npy'))
counts=t.groupby('split').agg(samples=('eligible','size'),eligible=('eligible','sum')).to_dict('index')
meta=dict(version=VERSION,timezone=ZONE,source_timestamp_assumption='TLC naive pickup slots interpreted as New York civil time; Meteostat naive clock relationship not established',source=str(source.relative_to(ROOT)),selected_population_hash=hashlib.sha256(pd.util.hash_pandas_object(d,index=False).values.tobytes()).hexdigest(),period='Jan1-Mar16 inclusive only',issuance='target_start minus 30 elapsed minutes',target='[target_start,target_start+30 elapsed minutes)',feature_cutoff='issuance; completed demand interval end <= issuance',historical_updates='Only earlier Jan-Feb intervals; frozen history and scalers for validation/development test',weather_mode='ORACLE_OBSERVED_TARGET_WEATHER',operational_available=False,weather_provenance='Meteostat 1.7.6 Hourly(Point).fetch; no archived issuance metadata in inspected lineage; naive time preserved; forward/backward fill',normalization='Calendar/code scaling retained; weather prior-training running mean/std; history scaled by prior-training demand population SD; zero SD uses scale1',warmup='No earlier complete training demand -> ineligible; zero placeholder never a training sample',shape=list(x.shape),split_counts=counts,source_rows=len(d),nonexistent_rows=len(bad),nonexistent_slots=int(bad.TimeSlot.nunique()),nonexistent_slot_demand=float(bad.Demand.sum()),retained_demand=float(y.sum(dtype=np.float64)),original_selected_demand=float(d.Demand.sum()),historical_training_self_inclusion_rows=2832*142,historical_future_training_lookup='Full Jan-Feb means included future training dates for early origins',label_semantics='Existing Y(t) is demand at t, confirmed on development prefix; do not shift labels',retraining_required=True,training_performed=False,remaining_blockers=['Archived ex-ante weather and timezone alignment','Legacy naive OD clock DST boundary integration before operational promotion','New-model training approval after protocol validation'])
# Validate old label semantics without reading protected target arrays beyond development prefix.
for name in ['train','validation','test']:
 p=ROOT/'data/processed/cnn_jan_mar_2026_3km_30min';times=np.load(p/f'forecast_timestamp_{name}.npy',mmap_mode='r');old=np.load(p/f'Y_{name}.npy',mmap_mode='r');keep=np.flatnonzero(times<np.datetime64('2026-03-17'))
 actual=d.groupby('TimeSlot').Demand.sum().reindex(pd.to_datetime(times[keep])).to_numpy()
 assert np.array_equal(old[keep].sum(axis=(1,2,3),dtype=np.float64),actual)
meta['legacy_label_alignment_verified']=True
(OUT/'temporal_protocol.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
