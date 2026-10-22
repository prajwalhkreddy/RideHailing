# True 3 km Grid Migration — Validated Candidate

## Methodology and implementation

Grid cell side length is 3,000 metres. The active grid has3,000-US-survey-foot sides (914.401828804m), caused by passing3000 directly to EPSG:2263 geometry coordinates. The candidate uses EPSG:32118 (NAD83/New York Long Island,metres): the same regional projection family, with explicit reprojection of the unchanged source boundary. No boundary zones are added or removed. EPSG2263 construction is rejected by the new API rather than silently interpreting its units.

`src/spatial/metric_grid.py` is the new unit-safe path; `scripts/build_grid_3km_candidate.py` is its isolated entry point. The legacy `build_grid` and current config remain unchanged solely to reproduce the active baseline. Do not use the legacy path for new methodology. No candidate is activated by this script.

## Boundary and inclusion

Source: `data/raw/taxi_zones/taxi_zones.shp`; 263 zones. Source CRS:EPSG:2263; construction/output:EPSG:32118. Source bounds(native units):[913175.109008804, 120121.88125434518, 1067382.508405164, 272844.2940054685]. Reprojected boundary bounds(m):[278336.32989854325, 36613.22263276968, 325338.8392395724, 83163.10713908107]. Candidate full-cell bounds(m):[278336.32989854325, 36613.22263276968, 326336.32989854325, 84613.22263276967].

Same inclusion rule: polygon intersection with any taxi zone, no percentage threshold; retain whole squares. Polygon-only overlay preserves the existing treatment of zero-area contacts. Grid envelope may extend beyond boundary because squares are not clipped; this is not a change to study-region selection. There is no random grid construction.

## Old versus candidate geometry

| Metric | Old active | Candidate |
|---|---:|---:|
| cell_width_metres | 914.401829 | 3000 |
| cell_height_metres | 914.401829 | 3000 |
| cell_area_km2 | 0.836130705 | 9 |
| generated_grid_count | 2652 | 256 |
| valid_grid_count | 1213 | 142 |
| raster_rows | 51 | 16 |
| raster_columns | 52 | 16 |
| unused_raster_cells | 1439 | 114 |
| cardinal_neighbor_links | 4544 | 496 |
| cell_area_relative_to_old | 1 | 10.7638674 |

New cells have9km² area, 10.763867361times the old area. Fewer cells follow from coarser spacing over the same study boundary; boundary intersection effects mean counts need not scale exactly inversely with area.

## Direct geometry and raster validation

Persisted polygons were reloaded and checked: width/height3000m, area9km²; absolute linear tolerance1e-6m,relative tolerance0. Full-square shape and stored centroids also verified. All cardinal links, including interior links, measure3000m; diagonals measure3000√2m≈4242.640687m. Raster indices are full-lattice positions, not compressed across missing rows/columns.

Raster:16×16; valid142; unused114. `grid_raster_mapping_3km.parquet` includes every raster position, nullableGridID andValidMask; GridID↔(Row,Column) is one-to-one/reversible for valid cells. IDs follow north-to-south/west-to-east. New IDs are not compatible with old0–1212 IDs.

## Topology comparison

| Topology | Directed links | Mean neighbours | Min–max | Boundary grids | Isolated IDs | Connected-component sizes |
|---|---:|---:|---|---:|---|---|
| cardinal | 496 | 3.492958 | 1–4 | 51 | [] | [142] |
| 8way | 958 | 6.746479 | 3–8 | 67 | [] | [142] |

Boundary means fewer than4(cardinal) or8(eight-way) valid neighbours; includes coastline/holes, not just raster edges. STAY is implicit action0 and omitted from link counts. Cardinal action indices1–4=N,E,S,W; eight-way1–8=N,NE,E,SE,S,SW,W,NW. Boundary masking permits STAY plus only listed neighbour actions. Connectivity is geometric, not road-network feasibility; diagonal valid endpoints do not certify water/corner crossings.

## Downstream migration requirements

`grid_3km_downstream_impact.csv` inventories each dependent component. Reassign zone-based trip grids, aggregate demand/popularity/priors/stations, rebuild CNN tensors/preprocessing, retrain CNN, regenerate predictions and routing observations/models, then rerun LinUCB/FL/integrated evaluations. Preserve30-minute forecast timing and frozen passenger sensitivity. New spatial artifacts cannot be mixed with old GridIDs. Existing source is often reusable but production guards,paths,hashes,CRS validation and potentially action shapes need an explicit migration change.

`RESULTS_SUPERSEDED` in the inventory means unsuitable as evidence for the future true3km deployment; it does not invalidate or delete historical runs under their original configuration. Policy retraining is required on new states; cardinal architecture can be reused, while eight-way requires9outputs. Diagonal travel must use√2distance and corresponding time/energy, not3km for every move.

## Outputs and reproduction

Candidate folder:`data/processed/grid_3km_candidate/`: grid lookup,metadata,complete raster mapping,zone mapping,and cardinal/eight-way neighbour tables. Report folder contains this README,geometry comparison CSV and downstream impact CSV.

Reproduce only the candidate: `PYTHONDONTWRITEBYTECODE=1 python -B scripts/build_grid_3km_candidate.py` using the project environment. The script reads the existing boundary and active-grid geometry for comparison, not raw taxi records. It hashes all existing protected processed-data/model/result/config files before/after; 462files matched. Candidate outputs are the only processed spatial artifacts written.

## Protection and focused tests

Active geometry/neighbours,existing demand/CNN/model predictions,simulator,Record029,Record030,weather analysis and validation runs remain unchanged. No training,downstream regeneration or simulator changes occurred. Focused tests in `tests/test_metric_grid.py` cover dimensions,area,determinism,raster holes/reversibility,cardinal/diagonal links,boundary masks,invalid geometry,feet-input conversion and rejection of feet-based construction. Validation on 19 October 2026: 16 focused tests passed, 0 failed (10 new metric-grid tests plus 6 existing grid/mapping/artifact tests). Command: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p test_metric_grid.py`; legacy grid, spatial-mapping and artifact suites were also run. Full NYC candidate rebuilt in memory in reversed zone order matched saved polygons and raster exactly; boundary coverage and reciprocal neighbour links passed.

## Decisions required before downstream regeneration

1. Candidate valid-grid count:142.
2. Raster dimensions:16×16,unused114.
3. Cardinal:{'directed_links': 496, 'mean_neighbors': 3.492957746478873, 'min_neighbors': 1, 'max_neighbors': 4, 'boundary_grids': 51, 'isolated_grids': [], 'connected_component_sizes': [142]}.
4. Eight-way:{'directed_links': 958, 'mean_neighbors': 6.746478873239437, 'min_neighbors': 3, 'max_neighbors': 8, 'boundary_grids': 67, 'isolated_grids': [], 'connected_component_sizes': [142]}.
5. Neither representation has duplicate IDs or geometrically invalid links. Component counts/isolated IDs above identify actual connectivity limitations; roads/water barriers require separate operational feasibility treatment. Legacy consumers enforceEPSG2263/fiveactions and must not load candidate artifacts unchanged.
6. Recommend **eight-neighbour topology**, not activated: it aligns with the roadmap's current-plus-eight concept and a square raster. Cardinal is simpler and reuses the five-action architecture, but excludes adjacent diagonal options. Eight-way requires nine-action masks/labels/policy outputs,FL shape/version guards and geometry-aware travel costs. This is an explicit implementation cost, not a reason to misrepresent cardinal as the full roadmap. Confirm topology and diagonal feasibility/cost convention before regenerating dependent artifacts. Candidate geometry remains isolated pending migration sign-off.
