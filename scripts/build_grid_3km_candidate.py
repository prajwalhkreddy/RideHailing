#!/usr/bin/env python3
"""Build only the isolated true-3km candidate; never activate or rebuild consumers."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import geopandas as gpd
import pandas as pd
import numpy as np
from src.spatial.metric_grid import (build_metric_grid,validate_metric_grid,build_metric_neighbors,
                                     topology_summary,GRID_CELL_SIZE_METERS,CONSTRUCTION_CRS)

CANDIDATE=ROOT/'data/processed/grid_3km_candidate'
REPORT=ROOT/'results/analysis/2026-10-19_true_3km_grid_migration'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def protected():
    return sorted(p for d in ['data/processed','models','results','config'] for p in (ROOT/d).rglob('*')
                  if p.is_file() and not p.is_relative_to(CANDIDATE) and not p.is_relative_to(REPORT)
                  and '__pycache__' not in p.parts)

def main():
    before={str(p.relative_to(ROOT)):sha(p) for p in protected()}
    source=ROOT/'data/raw/taxi_zones/taxi_zones.shp'
    zones=gpd.read_file(source)
    result=build_metric_grid(zones)
    candidate=result.grid
    CANDIDATE.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    candidate.to_parquet(CANDIDATE/'grid_lookup_3km.parquet',index=False)
    result.raster.to_parquet(CANDIDATE/'grid_raster_mapping_3km.parquet',index=False)
    result.zone_mapping.to_parquet(CANDIDATE/'zone_grid_mapping_3km.parquet',index=False)
    # Validate deserialized geometry and raster, not just objects before saving.
    candidate=gpd.read_parquet(CANDIDATE/'grid_lookup_3km.parquet')
    geometry=validate_metric_grid(candidate)
    raster=pd.read_parquet(CANDIDATE/'grid_raster_mapping_3km.parquet')
    assert len(raster)==result.rows*result.columns
    valid=raster[raster.ValidMask]
    assert len(valid)==len(candidate) and valid.GridID.is_unique
    assert not raster[['Row','Column']].duplicated().any()
    pd.testing.assert_frame_equal(valid[['GridID','Row','Column']].astype('int64').reset_index(drop=True),
        candidate[['GridID','Row','Column']].astype('int64').reset_index(drop=True))
    assert set(result.zone_mapping.LocationID)==set(zones.LocationID)
    topologies={}
    for topology in ['cardinal','8way']:
        links=build_metric_neighbors(candidate,topology)
        links.to_parquet(CANDIDATE/f'neighbors_{topology}_3km.parquet',index=False)
        loaded=pd.read_parquet(CANDIDATE/f'neighbors_{topology}_3km.parquet')
        pd.testing.assert_frame_equal(links,loaded)
        topologies[topology]=topology_summary(candidate,loaded,topology)
    old=gpd.read_parquet(ROOT/'data/processed/grid_lookup.parquet')
    oldmeta=json.loads((ROOT/'data/processed/grid_metadata.json').read_text())
    factor=old.crs.axis_info[0].unit_conversion_factor
    bounds=old.geometry.bounds
    oldwidth=float((bounds.maxx-bounds.minx).median()*factor)
    oldheight=float((bounds.maxy-bounds.miny).median()*factor)
    oldarea=float(old.area.median()*factor**2/1e6)
    comparison=[('cell_width_metres',oldwidth,geometry['width_min_m']),
        ('cell_height_metres',oldheight,geometry['height_min_m']),('cell_area_km2',oldarea,9.),
        ('generated_grid_count',oldmeta['generated_cells'],result.generated_cells),
        ('valid_grid_count',len(old),len(candidate)),('raster_rows',oldmeta['grid_rows'],result.rows),
        ('raster_columns',oldmeta['grid_columns'],result.columns),
        ('unused_raster_cells',oldmeta['grid_rows']*oldmeta['grid_columns']-len(old),len(raster)-len(candidate)),
        ('cardinal_neighbor_links',oldmeta['neighbor_links'],topologies['cardinal']['directed_links']),
        ('cell_area_relative_to_old',1.,9./oldarea)]
    pd.DataFrame(comparison,columns=['metric','old_active_grid','new_3km_candidate']).to_csv(REPORT/'grid_old_vs_3km_comparison.csv',index=False)
    impacts=[
      ('zone to GridID','data/processed/zone_grid_mapping.parquet; zone_to_grids.pkl','MUST_REGENERATE','New IDs/zone intersections; candidate mapping is isolated, not activated.'),
      ('mapped trips','data/processed/cleaned_trips.parquet','MUST_REGENERATE','Reassign PUGridID/DOGridID from existing zone IDs; no raw preparation required.'),
      ('active grid/mask/neighbors','data/processed/grid_lookup.parquet;grid_mask.npy;neighbour_map.parquet','MUST_REGENERATE','Activate versioned candidate only after topology and migration sign-off.'),
      ('demand aggregation','data/processed/demand_master_2026_01.parquet','MUST_REGENERATE','Recount pickups and historical means on new IDs; retain30-minute horizon.'),
      ('destination popularity','data/processed/destination_popularity_2026_01.parquet','MUST_REGENERATE','New destination grid counts, trailing means and training thresholds.'),
      ('CNN tensors','data/processed/cnn/','MUST_REGENERATE','New raster, masks, feature/target arrays and time-aligned metadata.'),
      ('CNN model','models/demand/cnn_model.keras;normalization.pkl','RETRAIN_REQUIRED','New spatial support; fit preprocessing on training data and version new weights.'),
      ('CNN predictions','models/demand/cnn_predictions.npy;cnn_metrics.csv','MUST_REGENERATE','New model/raster predictions, held-out evaluation and provenance.'),
      ('request generation','src/dispatch/generation.py','CODE_REUSABLE','Origin-conditioned sampler reusable; rebuild OD tables from new mapped rows.'),
      ('fleet initialization','src/fleet/fleet.py;src/charging/energy.py','CODE_REUSABLE','Initialize fresh state using new valid IDs; old vehicle placement not portable.'),
      ('neighbor masks','src/routing/baseline.py;src/simulation/grid_policy.py','MUST_REGENERATE','Rebuild masks; cardinal code reusable,8way requires explicit9-class adaptation.'),
      ('driver utility','src/routing/baseline.py','CODE_REUSABLE','Core computations reusable; new candidates and geometry-derived travel cost;8way distance sqrt(2)*3km.'),
      ('charging navigation','src/charging/stations.py','CODE_REUSABLE','Rebuild station/centroid inputs; existing zero-time navigation remains a separate roadmap gap.'),
      ('charging stations','data/processed/charging_stations_2026_01.parquet','MUST_REGENERATE','Re-rank new-grid activity; station count/capacity need feasibility review.'),
      ('fare priors','data/processed/nb9_fare_bootstrap_2026_01_25_1830.parquet','MUST_REGENERATE','Training fares per new grid; no passenger sensitivity re-estimation.'),
      ('driver preference values','data/processed/driver_preferences_seed42.parquet','CODE_REUSABLE','Not inherently spatial; retain numerical preferences if source population unchanged.'),
      ('pricing normalization','config/pricing_context_scaler.json','MUST_REGENERATE','Grid-demand/supply references and geometry pickup reference must be recalibrated.'),
      ('routing-policy training data','src/routing/learning.py local observations','MUST_REGENERATE','Old grid IDs/neighborhood states cannot be mixed with new observations.'),
      ('routing-policy model','models/routing/nb12_nb13_common_initialization_seed42.npz','RETRAIN_REQUIRED','Relearn routing on new states;8way also changes architecture,labels and masks.'),
      ('FedAvg implementation','src/routing/federated.py','CODE_REUSABLE','Averaging reusable;8way requires shape/version guards updated before use.'),
      ('FedAvg outputs','results/validation/*/routing_rounds.csv','RESULTS_SUPERSEDED','Historical baseline only; new-grid rounds must be regenerated later.'),
      ('LinUCB validation','results/validation/phase6*;phase7*','RESULTS_SUPERSEDED','Grid context/action economics change; retain old results as history.'),
      ('integrated simulation','results/validation/phase7d_48slot_final_integrated_seed42/','RESULTS_SUPERSEDED','Reinitialize/run new-grid baseline after dependencies and sign-off.'),
      ('production assembler','src/simulation/production.py','CODE_REUSABLE','Update1213-grid guards,paths,hashes and topology assumptions in later migration only.'),
      ('spatial consumers','scripts/build_demand_master.py;scripts/build_cnn_dataset.py;src/demand/contracts.py','CODE_REUSABLE','Versioned artifact paths/CRS checks must be adapted; do not feed candidate to EPSG2263 legacy validator.'),
      ('Record029/030/weather analysis','data/processed/price_distance_sensitivity_record029/;results/analysis/','CODE_REUSABLE','Nonspatial sensitivity results stay frozen; no regeneration due solely to grid migration.')]
    pd.DataFrame(impacts,columns=['component','artifact_or_module','classification','migration_requirement']).to_csv(REPORT/'grid_3km_downstream_impact.csv',index=False)
    after={str(p.relative_to(ROOT)):sha(p) for p in protected()}
    assert before==after,'Protected artifact changed during candidate generation'
    metadata={'status':'VALIDATED_CANDIDATE_NOT_ACTIVE','grid_cell_size_meters':GRID_CELL_SIZE_METERS,
       'source_boundary':str(source.relative_to(ROOT)),'source_crs':zones.crs.to_string(),
       'construction_crs':CONSTRUCTION_CRS,'output_crs':candidate.crs.to_string(),
       'crs_linear_unit':candidate.crs.axis_info[0].unit_name,
       'source_bbox_native':zones.total_bounds.tolist(),'boundary_bbox_metres':result.boundary_bounds,
       'grid_bbox_metres':candidate.total_bounds.tolist(),'boundary_zone_count':len(zones),
       'boundary_source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in source.parent.glob('taxi_zones.*') if p.is_file()},
       'valid_cell_rule':'Same polygon-intersection overlay rule as legacy; retain full squares; no overlap-percentage threshold.',
       'id_order':'North-to-south then west-to-east; full bounding-lattice Row/Column; new IDs independent of old IDs.',
       'generated_cells':result.generated_cells,'valid_cells':len(candidate),'raster_rows':result.rows,'raster_columns':result.columns,
       'unused_raster_positions':len(raster)-len(candidate),'geometry_validation':geometry,
       'topologies':topologies,'final_topology':None,'recommended_topology':'8way',
       'diagonal_rule':'Valid endpoints only; diagonal crossing/road feasibility not certified.',
       'area_ratio_new_to_old':9./oldarea,'protected_file_count':len(before),
       'protected_sha256_before':before,'protected_sha256_after_match':True}
    (CANDIDATE/'grid_metadata_3km.json').write_text(json.dumps(metadata,indent=2)+'\n')
    table='\n'.join(f'| {metric} | {a:.9g} | {b:.9g} |' for metric,a,b in comparison)
    topology_rows='\n'.join(f"| {k} | {v['directed_links']} | {v['mean_neighbors']:.6f} | {v['min_neighbors']}–{v['max_neighbors']} | {v['boundary_grids']} | {v['isolated_grids']} | {v['connected_component_sizes']} |" for k,v in topologies.items())
    text=f'''# True 3 km Grid Migration — Validated Candidate

## Methodology and implementation

Grid cell side length is 3,000 metres. The active grid has3,000-US-survey-foot sides ({oldwidth:.9f}m), caused by passing3000 directly to EPSG:2263 geometry coordinates. The candidate uses EPSG:32118 (NAD83/New York Long Island,metres): the same regional projection family, with explicit reprojection of the unchanged source boundary. No boundary zones are added or removed. EPSG2263 construction is rejected by the new API rather than silently interpreting its units.

`src/spatial/metric_grid.py` is the new unit-safe path; `scripts/build_grid_3km_candidate.py` is its isolated entry point. The legacy `build_grid` and current config remain unchanged solely to reproduce the active baseline. Do not use the legacy path for new methodology. No candidate is activated by this script.

## Boundary and inclusion

Source: `{source.relative_to(ROOT)}`; {len(zones)} zones. Source CRS:{zones.crs.to_string()}; construction/output:{CONSTRUCTION_CRS}. Source bounds(native units):{zones.total_bounds.tolist()}. Reprojected boundary bounds(m):{result.boundary_bounds}. Candidate full-cell bounds(m):{candidate.total_bounds.tolist()}.

Same inclusion rule: polygon intersection with any taxi zone, no percentage threshold; retain whole squares. Polygon-only overlay preserves the existing treatment of zero-area contacts. Grid envelope may extend beyond boundary because squares are not clipped; this is not a change to study-region selection. There is no random grid construction.

## Old versus candidate geometry

| Metric | Old active | Candidate |
|---|---:|---:|
{table}

New cells have9km² area, {9./oldarea:.9f}times the old area. Fewer cells follow from coarser spacing over the same study boundary; boundary intersection effects mean counts need not scale exactly inversely with area.

## Direct geometry and raster validation

Persisted polygons were reloaded and checked: width/height3000m, area9km²; absolute linear tolerance1e-6m,relative tolerance0. Full-square shape and stored centroids also verified. All cardinal links, including interior links, measure3000m; diagonals measure3000√2m≈4242.640687m. Raster indices are full-lattice positions, not compressed across missing rows/columns.

Raster:{result.rows}×{result.columns}; valid{len(candidate)}; unused{len(raster)-len(candidate)}. `grid_raster_mapping_3km.parquet` includes every raster position, nullableGridID andValidMask; GridID↔(Row,Column) is one-to-one/reversible for valid cells. IDs follow north-to-south/west-to-east. New IDs are not compatible with old0–1212 IDs.

## Topology comparison

| Topology | Directed links | Mean neighbours | Min–max | Boundary grids | Isolated IDs | Connected-component sizes |
|---|---:|---:|---|---:|---|---|
{topology_rows}

Boundary means fewer than4(cardinal) or8(eight-way) valid neighbours; includes coastline/holes, not just raster edges. STAY is implicit action0 and omitted from link counts. Cardinal action indices1–4=N,E,S,W; eight-way1–8=N,NE,E,SE,S,SW,W,NW. Boundary masking permits STAY plus only listed neighbour actions. Connectivity is geometric, not road-network feasibility; diagonal valid endpoints do not certify water/corner crossings.

## Downstream migration requirements

`grid_3km_downstream_impact.csv` inventories each dependent component. Reassign zone-based trip grids, aggregate demand/popularity/priors/stations, rebuild CNN tensors/preprocessing, retrain CNN, regenerate predictions and routing observations/models, then rerun LinUCB/FL/integrated evaluations. Preserve30-minute forecast timing and frozen passenger sensitivity. New spatial artifacts cannot be mixed with old GridIDs. Existing source is often reusable but production guards,paths,hashes,CRS validation and potentially action shapes need an explicit migration change.

`RESULTS_SUPERSEDED` in the inventory means unsuitable as evidence for the future true3km deployment; it does not invalidate or delete historical runs under their original configuration. Policy retraining is required on new states; cardinal architecture can be reused, while eight-way requires9outputs. Diagonal travel must use√2distance and corresponding time/energy, not3km for every move.

## Outputs and reproduction

Candidate folder:`data/processed/grid_3km_candidate/`: grid lookup,metadata,complete raster mapping,zone mapping,and cardinal/eight-way neighbour tables. Report folder contains this README,geometry comparison CSV and downstream impact CSV.

Reproduce only the candidate: `PYTHONDONTWRITEBYTECODE=1 python -B scripts/build_grid_3km_candidate.py` using the project environment. The script reads the existing boundary and active-grid geometry for comparison, not raw taxi records. It hashes all existing protected processed-data/model/result/config files before/after; {len(before)}files matched. Candidate outputs are the only processed spatial artifacts written.

## Protection and focused tests

Active geometry/neighbours,existing demand/CNN/model predictions,simulator,Record029,Record030,weather analysis and validation runs remain unchanged. No training,downstream regeneration or simulator changes occurred. Focused tests in `tests/test_metric_grid.py` cover dimensions,area,determinism,raster holes/reversibility,cardinal/diagonal links,boundary masks,invalid geometry,feet-input conversion and rejection of feet-based construction. Validation on 19 October 2026: 16 focused tests passed, 0 failed (10 new metric-grid tests plus 6 existing grid/mapping/artifact tests). Command: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p test_metric_grid.py`; legacy grid, spatial-mapping and artifact suites were also run. Full NYC candidate rebuilt in memory in reversed zone order matched saved polygons and raster exactly; boundary coverage and reciprocal neighbour links passed.

## Decisions required before downstream regeneration

1. Candidate valid-grid count:{len(candidate)}.
2. Raster dimensions:{result.rows}×{result.columns},unused{len(raster)-len(candidate)}.
3. Cardinal:{topologies['cardinal']}.
4. Eight-way:{topologies['8way']}.
5. Neither representation has duplicate IDs or geometrically invalid links. Component counts/isolated IDs above identify actual connectivity limitations; roads/water barriers require separate operational feasibility treatment. Legacy consumers enforceEPSG2263/fiveactions and must not load candidate artifacts unchanged.
6. Recommend **eight-neighbour topology**, not activated: it aligns with the roadmap's current-plus-eight concept and a square raster. Cardinal is simpler and reuses the five-action architecture, but excludes adjacent diagonal options. Eight-way requires nine-action masks/labels/policy outputs,FL shape/version guards and geometry-aware travel costs. This is an explicit implementation cost, not a reason to misrepresent cardinal as the full roadmap. Confirm topology and diagonal feasibility/cost convention before regenerating dependent artifacts. Candidate geometry remains isolated pending migration sign-off.
'''
    (REPORT/'README.md').write_text(text)
    print(json.dumps({k:v for k,v in metadata.items() if k not in ['protected_sha256_before','boundary_source_hashes']},indent=2))

if __name__=='__main__':main()
