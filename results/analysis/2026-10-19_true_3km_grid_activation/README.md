# True 3 km, eight-way Jan–Mar spatial migration

## Active decision and measured geometry

The intended square-cell methodology was 3 km × 3 km. The historical builder added 3,000 directly to EPSG:2263 coordinates, whose units are US survey feet. Its saved cells consequently measured 914.401828803657 m per side. This was a native-unit implementation defect.

The existing validated candidate was promoted without rebuilding or changing its boundary. Active geometry is `data/processed/grid_lookup.parquet`; construction/output CRS is EPSG:32118, NAD83 / New York Long Island in **metres**. The unchanged 263-zone boundary is reprojected before grid construction. There are 256 lattice positions, **142 valid full squares**, **114 explicitly masked unused positions**, and a **16×16** raster. GridIDs are contiguous 0–141 in north-to-south, west-to-east order. They do not retain old 0–1212 semantics.

Persisted widths and heights are 3,000 m to absolute tolerance **1e-6 m**, with areas 9,000,000 m² to absolute tolerance **1e-6 m²**. Raster/ID mappings are unique and reversible. Legacy files and configuration were copied byte-for-byte to `data/processed/legacy_914m_provenance/` before activation; their hashes are in `legacy_fingerprints.json`. Historical builder source remains in version control and `src/spatial/grid.py`; the active builder entrypoint cannot regenerate the old geometry.

## Topology, actions and movement

Eight-way topology has **958 directed non-STAY links**, one connected component of 142 cells and no isolated cells. Action indices are:

| Internal index | Action | External relative index | Distance m |
|---:|---|---:|---:|
|0|STAY|1|0|
|1|NORTH|2|3000|
|2|NORTHEAST|3|4242.640687119286|
|3|EAST|4|3000|
|4|SOUTHEAST|5|4242.640687119286|
|5|SOUTH|6|3000|
|6|SOUTHWEST|7|4242.640687119286|
|7|WEST|8|3000|
|8|NORTHWEST|9|4242.640687119286|

Boundary actions are explicitly masked, with nullable destination/distance for invalid moves; STAY is always valid. Cardinal/diagonal adjacency is checked against raster offsets and measured centroid spacing. Geometry does not certify road connectivity, bridge access, or diagonal feasibility across water.

At the unchanged 15 km/h, cardinal travel takes 12 minutes and diagonal travel 16.97056274847714 minutes. At unchanged 0.15 kWh/km these consume 0.45 and 0.636396103067893 kWh respectively. Reposition transitions and action-dependent degradation inputs use actual action distance; arrival timers retain continuous minutes and existing mini-slot update semantics. Main slots remain 30 minutes, mini-slots 2 minutes, 15 per main slot.

## Jan–Mar source population and mapping

The demand population uses the **existing NB2 location-ID cleaning**, not Record-029 fare/distance cleaning. January reuses `legacy_914m_provenance/cleaned_trips.parquet`. No processed February/March table retained the required pickup/dropoff zone IDs; their local taxi Parquets were read with the existing seven-column loader and existing valid-zone preparation routine. No passenger-sensitivity data preparation or epsilon computation was repeated.

The 263-zone mapping retains polygon intersections, not centroid assignment or majority-area selection. Taxi trips have LocationIDs rather than coordinates. Existing NB2 deterministic seeded sampling selects among intersecting cells by zone, seed `42 + source-file month`, pickup then dropoff. This is a zone-based spatial representation, not a recovered exact trip coordinate. Source-file month and prepared-row index remain available. All assigned pickup/dropoff IDs are valid; no row was dropped because of the changed grid.

| Pickup calendar month | Source requests | Mapped pickups | Mapped dropoffs | Aggregated demand | Half-hour slots |
|---|---:|---:|---:|---:|---:|
|January|3,699,644|3,699,644|3,699,644|3,699,644|1,488|
|February|3,377,979|3,377,979|3,377,979|3,377,979|1,344|
|March|3,928,571|3,928,571|3,928,571|3,928,571|1,488|
|Total|11,006,194|11,006,194|11,006,194|11,006,194|4,320|

Counts are by actual pickup calendar month, not filename. Source-file retained counts are January 3,699,634; February 3,377,978; March 3,928,582. Cross-month timestamps explain the difference. Existing valid-zone preparation excludes 21,888 February and 23,865 March source rows. Four January and four March prepared rows lie outside `[2026-01-01, 2026-04-01)` and are excluded solely by the declared date window. `source_reconciliation.json` documents every count; source files remain intact. The demand table has **613,440 rows**, one per grid/slot, including zero demand. No stochastic request generation or simulation was run.

## Weather, calendar and destination popularity

Existing monthly hourly weather files cover all required timestamps. They are concatenated with original Meteostat WeatherCode, temperature and wind speed. The existing naive timestamp join convention is unchanged; no new timezone interpretation is introduced. Passenger CLEAR/RAIN scenario labels are not used as CNN encoding. DayOfWeek, Hour and PeriodWithinHour (0/1 for the two half-hours) are aligned to each slot.

No final HistoricalAverageDemandDistribution plane, scaler, tensor split or CNN model was computed. The old expanding historical-average pipeline continues updating using prior held-out observations and the old scaler includes its internal validation interval; neither satisfies the forthcoming **training-only** contract. Legacy preprocessing/training entrypoints now fail explicitly against the migrated active config.

Destination popularity preserves the existing definition: actual dropoffs in 30-minute slots; a strictly lagged rolling mean over up to six earlier slots; fixed reference-period quintiles encoded Very Low=0, Low=.25, Medium=.5, High=.75, Very High=1. This is an ordinal feature, **not a sum-to-one destination probability**. No new normalization methodology is introduced.

The regenerated lagged source spans all 4,320 slots. Dropoffs inside the period total **11,005,364**: January 3,697,367; February 3,377,927; March 3,930,070. **830** retained pickup trips have dropoff timestamps outside the period. Trip rows are retained; only in-window dropoffs contribute to the dropoff table. Pickup and dropoff calendar-month counts need not match.

The existing reference interval `[Jan 1, Jan 25 18:30)` is retained for a compatible encoded artifact, with regenerated quintiles **0, 1/3, 11/6, 6**. Encoded popularity is unavailable before the reference closes, so runtime features never use future-fitted thresholds. This retained cutoff is **not a decision on the final CNN split**. Once that split is frozen, fit thresholds on its training reference only. The lagged source is already available for that work.

## Regenerated static foundation

Active versioned data live in `data/processed/spatial_3km_jan_mar_2026/`; active paths are explicit in `config/config.yaml`.

- Grid lookup, full raster mapping/mask, zone intersection table and lookup pickle, eight-way neighbours, nine-action masks.
- `trips_jan_mar_2026.parquet`: all 11,006,194 mapped source requests, original trip fields and pickup/dropoff aliases.
- `demand_master_jan_mar_2026.parquet`: dense requests per grid per 30-minute slot, weather/calendar source fields.
- `weather_jan_mar_2026.parquet`: original hourly weather representation.
- `destination_popularity_source.parquet`, `destination_popularity.parquet`, thresholds JSON: lagged source and existing-cutoff compatible encoding.
- `od_counts.parquet`: full-period descriptive pickup/destination counts; not an operational feature fitted using future trips.
- `centroid_distances.parquet`, `neighbour_travel.parquet`: projected straight-line metric distances and unchanged speed/energy assumptions.
- `charging_stations.parquet`, `charging_navigation_distances.parquet`: identity-preserving provisional station mapping and metric navigation inputs.
- `fare_bootstrap_legacy_cutoff.parquet`, `priority_grids_legacy_cutoff.parquet`: existing pre-Jan25 18:30 fare-prior/top-five convention on new grids; final operational-statistics and split review still required.
- `initial_supply_seed42.parquet`, `supply_reference.json`: existing uniform 5,000-vehicle initialization over 142 grids, seed42, all idle, incoming0; supply P99 **50.59**. No simulation run. The complete pricing scaler still awaits new CNN demand predictions and is not silently reused.

Every generated artifact is covered by grid metadata and a companion metadata file where applicable, specifying grid version, dimensions, creator and source/provenance. Machine-readable manifest statuses separate source readiness from artifacts requiring retraining or final split review.

### Charging locations

The 15 existing stations are provisional locations defined by legacy grid centroids. Those centroids are reprojected and assigned to their containing new cell. All 15 station identities remain; they occupy **four** new cells. No deduplication, activity reranking, new stations or power/capacity change occurred. Historical activity counts are retained as provenance, not represented as newly calculated activity. The validator supports this explicit migrated schema. Metric navigation distances are prepared, but replacing the existing instantaneous charging transition and validating road travel remain task D; this migration does not claim that charging navigation is complete.

## Structural routing compatibility and preserved history

Routing now represents nine action classes. The existing 17-feature-per-candidate structural encoding expands from 87 to **155** inputs; policy output expands from5 to **9**, retaining64/32 hidden units. This is a dimensional migration, not the final roadmap state redesign. Masks, label validation, action order, movement time/energy and FedAvg tensor validation follow the new dimensions. Tiny array-based FedAvg fixtures verify weighted aggregation without training or operational federated rounds.

Old CNN tensors/checkpoints/predictions are `KEEP_PROVENANCE` and `SUPERSEDED_FOR_FINAL_JAN_MAR_3KM_CNN`. Old five-action routing/FedAvg artifacts are `SUPERSEDED_BY_3KM_9ACTION_MIGRATION`. Old LinUCB/simulation results and January static outputs remain available; they describe a different environment and must not be compared directly as equivalent-grid outcomes. The legacy production runner fails closed with a retraining message when it encounters the new grid. Its historical eight-dimensional pricing adapters are not silently reinterpreted as a new pricing methodology.

`artifact_index.json` fingerprints every new data-foundation artifact. Legacy source code is reproducible from git commit `0cca91368bda5f81a5eb6ad1692ed8b2748fbf96`. `artifact_migration_manifest.csv` lists active replacements, provenance, retraining dependencies and unchanged artifacts. Models, Record-029, elasticity artifacts and final analytical weather scenarios are SHA-256 protected in `protected_fingerprints.json`. **Record-029 supported N=10,505,278, its epsilon methodology and final CLEAR/RAIN scenarios remain unchanged.** No CNN training, routing training, long simulation, DQN implementation or privacy experiment was performed.

## Validation and execution

Build/validate command (completed builds validate without recomputing):

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mpl_audit python -B scripts/activate_true_3km_foundation.py
```

Measured geometry, raster reversibility, valid GridIDs, connectivity/adjacency, masks, action distances, weather coverage, continuous dates, demand reconciliation, lagged popularity and protected/legacy hashes pass. The focused quick suite covers active artifacts, metric/legacy geometry fixtures, config, destination popularity, energy/fleet, routing, policy shape and array-only FedAvg. The final run passed **91 tests, zero failures/errors**. Run `PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/mpl_audit python -B scripts/test_spatial_migration.py`. Four training-bearing tests are excluded explicitly; the machine-readable `test_results.json` records execution results and omissions. No model checkpoint is created by shape-only initialization fixtures.

## Final CNN contract and remaining dependency chain

**Locked:** Jan 1–Mar 31 2026 inclusive; true3km squares;142 valid grids;16×16 raster; forecast **next30-minute main slot**; target **requests/grid/30-minute interval**. The 30-minute horizon is a **DOCUMENTED_ADAPTATION**; the paper's10-minute horizon does not introduce a10-minute handoff. The2-minute mini-slot is simulator dynamics only.

Seven intended feature concepts are DayOfWeek, Hour, PeriodWithinHour, WeatherType, Temperature, WindSpeed, HistoricalAverageDemandDistribution. Historical averages and scalers must be fitted on **training data only**. Use a chronological train/validation/test split; exact dates remain for the next task. Preserve original weather representation until its final CNN encoding is specified.

The source foundation has no missing month or weather timestamp blocking preprocessing. Final tensor/model work must implement the corrected pipeline and freeze split dates; old entrypoints intentionally refuse to train. Destination thresholds and runtime calibration must respect that split. The required sequence is:

1. **A:** Build corrected Jan–Mar CNN preprocessing/tensors on the16×16 raster.
2. **B:** Retrain/validate final CNN with chronological split, seven concepts, training-only historical averages/scalers and next30-minute target.
3. **C:** Correct operational statistics μ, σ, F_hat, H_hat.
4. **D:** Correct driver U1/U2, EV U3, charging navigation and global routing-policy state; retrain nine-action routing/plain FedAvg artifacts.
5. **E:** Resolve/freeze passenger-acceptance and reward methodology where still blocked.
6. **F:** Build final DQN state `[J_hat(g,t), J_disp(g,t−1), I(g,t), p(g,t), destination_popularity(g′,t)]`.
7. **G:** Implement deterministic standalone pricing DQN.
8. **H:** Run the first short non-private hierarchical DQN episode.

None of A–H is executed in this migration.
