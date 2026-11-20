"""Bounded development evidence; no model training or protected target reads."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.demand.persistence_weather import contract,build_persistence
out=ROOT/'results_v2/cnn_demand/2026-11-17_observation_persistence'
meta=contract(120)
d=pd.read_parquet(ROOT/'data/processed/spatial_3km_jan_mar_2026/demand_master_jan_mar_2026.parquet',filters=[('TimeSlot','>=',pd.Timestamp('2026-01-01')),('TimeSlot','<',pd.Timestamp('2026-03-17'))])
w=pd.read_parquet(ROOT/'data/processed/spatial_3km_jan_mar_2026/weather_jan_mar_2026.parquet',filters=[('Datetime','<',pd.Timestamp('2026-03-17'))])
g=pd.read_parquet(ROOT/'data/processed/grid_lookup.parquet',columns=['GridID','Row','Column'])
x,y,s,bad=build_persistence(d,g,w,meta)
s.to_csv(out/'sample_timing.csv',index=False)
assert (s.assumed_available_at<=s.issued_at).all()
assert np.array_equal(y,np.load(ROOT/'results_v2/cnn_demand/2026-11-17_causal_timing/Y_development.npy',mmap_mode='r'))
assert float(y.sum(dtype=float))==float(d.Demand.sum())
mask=np.zeros((16,16),bool);mask[g.Row,g.Column]=True
assert not x[:,:,~mask].any()
summary=dict(shape=list(x.shape),samples=len(s),eligible=int(s.eligible.sum()),split_counts=s.groupby('split').eligible.agg(['size','sum']).to_dict('index'),source_rows=len(d),nonexistent_civil_rows=len(bad),request_demand_retained=float(y.sum(dtype=float)),target_labels_unchanged=True,age_min_minutes=float(s.observation_age_minutes.min()),age_max_minutes=float(s.observation_age_minutes.max()),availability_violations=int((s.assumed_available_at>s.issued_at).sum()),weather_missing_cells=int(w[['WeatherCode','Temperature','WindSpeed']].isna().sum().sum()),development_only=True,training_performed=False,operational_ready=False,source_timezone_evidence='Meteostat1.7.6 utilities/mutations.py localize treats native time as UTC; fetch omitted timezone',publication_time_recorded=False,archived_forecasts_in_inspected_lineage=False,model_data_allowed=True,source_flags_retained=False,local_fill_changed_values=False,assumption='120-minute lag covers hourly support plus assumed one-hour delay; NOT measured release latency or historical-vintage proof',interval_semantics='Hourly labels; exact observation/aggregation interval not persisted; conservative one-hour support allowance is assumed',od_dst_bridge='Legacy naive runtime bridge fails closed at spring transition; no new civil slots',sensitivity='Weighted sampler unchanged; realized legacy WeatherCode clock differs from new UTC-converted persistence weather',checks='Finite tensors; exact unchanged targets; mask; availability ordering')
paths=['src/demand/persistence_weather.py','src/demand/causal_timing.py','src/demand/final_cnn.py','src/data/weather.py','src/simulation/od_pricing_runtime.py','src/pricing/weighted_binned_sampler.py']
summary['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
summary['selected_weather_hash']=hashlib.sha256(pd.util.hash_pandas_object(w,index=False).values.tobytes()).hexdigest()
(out/'weather_availability_contract.json').write_text(json.dumps(meta,indent=2)+'\n')
(out/'validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
