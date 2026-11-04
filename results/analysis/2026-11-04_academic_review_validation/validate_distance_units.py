from pathlib import Path
import json
import numpy as np,pandas as pd,pyarrow.parquet as pq,geopandas as gpd
R=Path('results/analysis/2026-11-04_academic_review_validation')
p=Path('data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet')
f=next(pq.ParquetFile(p).iter_batches(batch_size=10000,columns=['trip_distance','fare','epsilon','epsilon_status'])).to_pandas();f=f[f.epsilon_status=='VALID']
b=3.01799878914405;pricebase=21.34586956773507
r=(f.trip_distance-b)/b;rk=(f.trip_distance*1.609344-b*1.609344)/(b*1.609344);p=(f.fare-pricebase)/pricebase;e=p/r;ek=p/rk
np.testing.assert_array_equal(e,f.epsilon);np.testing.assert_allclose(e,ek,rtol=1e-12,atol=1e-12)
g=gpd.read_parquet('data/processed/grid_lookup.parquet');bounds=g.geometry.bounds
assert g.crs.to_epsg()==32118 and len(g)==142
np.testing.assert_allclose(bounds.maxx-bounds.minx,3000,atol=1e-8);np.testing.assert_allclose(bounds.maxy-bounds.miny,3000,atol=1e-8)
result={'classification':'NO_ISSUE_UNIT_INVARIANT','historical_sample_N':len(f),'relative_deviation_max_abs_difference':float(abs(r-rk).max()),'relative_deviation_mean_abs_difference':float(abs(r-rk).mean()),'relative_deviation_mismatch_count_gt_1e_12':int((abs(r-rk)>1e-12).sum()),'epsilon_max_abs_difference':float(abs(e-ek).max()),'epsilon_mean_abs_difference':float(abs(e-ek).mean()),'epsilon_absolute_mismatch_count_gt_1e_12':int((abs(e-ek)>1e-12).sum()),'epsilon_allclose_mismatch_count_atol_rtol_1e_12':int((~np.isclose(e,ek,rtol=1e-12,atol=1e-12)).sum()),'historical_formula_matches_stored_epsilon':True,'source_resolution_miles_RAW':.01,'resolution_km':.01*1.609344,'half_resolution_km':.005*1.609344,'grid_crs':'EPSG:32118','grid_native_units':'metres','valid_grids':142,'cell_width_km':float((bounds.maxx-bounds.minx).median()/1000),'cell_height_km':float((bounds.maxy-bounds.miny).median()/1000),'cardinal_movement_km':3.,'diagonal_movement_km':3*2**.5,'stay_movement_km':0.}
(R/'distance_unit_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(result)
