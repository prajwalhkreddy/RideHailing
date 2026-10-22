"""Activate the validated candidate and build Jan–Mar sources; never train models.

Run once; completed builds are validated without regeneration on subsequent runs.
Legacy artifacts are copied and hashed before active files are replaced.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hashlib
import json
import pickle
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from src.spatial.metric_grid import validate_metric_grid, build_metric_neighbors, topology_summary
from src.spatial.mapping import build_zone_to_grids, assign_grid_ids_by_zone_legacy
from src.data.taxi import load_taxi_data, prepare_legacy_trips
from src.popularity.destination import aggregate_dropoffs, trailing_dropoff_average

P = ROOT / 'data/processed'
C = P / 'grid_3km_candidate'
D = P / 'spatial_3km_jan_mar_2026'
L = P / 'legacy_914m_provenance'
R = ROOT / 'results/analysis/2026-10-19_true_3km_grid_activation'
VERSION = 'true_3km_v1'
START, END = pd.Timestamp('2026-01-01'), pd.Timestamp('2026-04-01')
SCRIPT = 'scripts/activate_true_3km_foundation.py'
BASE = dict(grid_version=VERSION, valid_grid_count=142, raster_rows=16, raster_columns=16,
            creation_script=SCRIPT, dataset_start=str(START), dataset_end_exclusive=str(END))

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def dump(p,obj):p.write_text(json.dumps(obj,indent=2,default=str)+'\n')

def save(df,name,notes='',sources=None):
    path=D/name
    df.to_parquet(path,index=False)
    dump(path.with_suffix('.metadata.json'),{**BASE,'rows':len(df),'notes':notes,'sources':sources or [],'sha256':sha(path)})
    return path

def validate():
    grid=gpd.read_parquet(P/'grid_lookup.parquet');validate_metric_grid(grid)
    assert len(grid)==142 and grid.GridID.tolist()==list(range(142))
    assert np.load(P/'grid_mask.npy').shape==(16,16)
    assert np.load(P/'grid_mask.npy').sum()==142
    raster=pd.read_parquet(D/'grid_raster_mapping.parquet')
    assert len(raster)==256 and raster.ValidMask.sum()==142 and not raster[['Row','Column']].duplicated().any()
    pd.testing.assert_frame_equal(raster.loc[raster.ValidMask,['GridID','Row','Column']].astype('int64').reset_index(drop=True),grid[['GridID','Row','Column']].astype('int64'))
    links=pd.read_parquet(P/'neighbour_map.parquet')
    assert len(links)==958
    expected=build_metric_neighbors(grid,'8way')
    np.testing.assert_allclose(links.DistanceMeters,expected.DistanceMeters,rtol=0,atol=1e-6)
    assert links.NeighbourGridID.tolist()==expected.NeighbourGridID.tolist()
    demand=pd.read_parquet(D/'demand_master_jan_mar_2026.parquet')
    slots=pd.date_range(START,END,freq='30min',inclusive='left')
    assert len(slots)==4320 and len(demand)==4320*142
    assert pd.DatetimeIndex(demand.TimeSlot.drop_duplicates()).equals(slots)
    assert not demand.isna().any().any() and 'HistoricalDemand' not in demand
    assert set(demand.GridID)==set(range(142)) and not demand[['TimeSlot','GridID']].duplicated().any()
    assert set(demand.PeriodWithinHour)=={0,1}
    rec=pd.read_csv(R/'data_reconciliation.csv')
    assert (rec.source_rows==rec.mapped_pickups).all() and (rec.source_rows==rec.aggregated_demand).all()
    assert int(demand.Demand.sum())==int(rec.iloc[-1].source_rows)
    for batch in pq.ParquetFile(D/'trips_jan_mar_2026.parquet').iter_batches(columns=['PUGridID','DOGridID']):
        for name in batch.schema.names:
            a=batch.column(name).to_numpy();assert (a>=0).all() and (a<142).all()
    pop=pd.read_parquet(D/'destination_popularity_source.parquet')
    pd.testing.assert_frame_equal(pop,trailing_dropoff_average(pop[['TimeSlot','GridID','dropoff_count']]))
    assert int(pop.dropoff_count.sum())==int(rec.iloc[-1].dropoffs_in_window)
    for path,expected_hash in json.loads((R/'protected_fingerprints.json').read_text()).items():assert sha(ROOT/path)==expected_hash,path
    for path,expected_hash in json.loads((R/'legacy_fingerprints.json').read_text()).items():assert sha(ROOT/path)==expected_hash,path
    if (R/'artifact_index.json').exists():
        for path,expected_hash in json.loads((R/'artifact_index.json').read_text()).items():assert sha(ROOT/path)==expected_hash,path
    print('FOUNDATION VALIDATION PASS',len(demand),'grid/time rows',flush=True)


def complete_source_contracts():
    from pathlib import Path
    import sys,json
    sys.path.insert(0,str(Path.cwd()))
    import pandas as pd
    import yaml
    from src.popularity.destination import fit_popularity_thresholds,apply_popularity_levels
    # Retain existing reference interval; do not silently choose the future CNN split.
    old=json.loads((P/'destination_popularity_2026_01_metadata.json').read_text())
    pop=pd.read_parquet(D/'destination_popularity_source.parquet')
    start=pd.Timestamp(old['reference_start']);end=pd.Timestamp(old['reference_end_exclusive'])
    ref=pop.loc[pop.TimeSlot.ge(start)&pop.TimeSlot.lt(end),'dropoff_ma_3h']
    th=fit_popularity_thresholds(ref,reference_start=start,reference_end_exclusive=end)
    encoded=apply_popularity_levels(pop,th)
    # Training-fitted thresholds are unavailable for runtime before reference closes.
    encoded.loc[encoded.TimeSlot<end,['popularity_level','popularity_value']]=[pd.NA,float('nan')]
    save(encoded,'destination_popularity.parquet','Existing six-slot lagged averages + fixed global reference quintiles. Retains existing Jan1–Jan25 18:30 fit period; encoded values unavailable before reference closes. Encoding 0,.25,.5,.75,1 is ordinal, NOT sum-to-one probability. Refit after final chronological training split is frozen.')
    dump(D/'destination_popularity_thresholds.json',{**BASE,**th.to_metadata(),'runtime_available_from':str(end),'status':'EXISTING_REFERENCE_PERIOD_NOT_FINAL_CNN_SPLIT'})
    weather=pd.concat([pd.read_parquet(P/f'weather/nyc_weather_processed_2026_{m:02d}.parquet') for m in (1,2,3)],ignore_index=True)
    save(weather,'weather_jan_mar_2026.parquet','Existing hourly weather concatenation; raw Meteostat code unchanged, naive timestamp convention unchanged.',[str(P/f'weather/nyc_weather_processed_2026_{m:02d}.parquet') for m in (1,2,3)])
    cpath=Path('config/config.yaml');cfg=yaml.safe_load(cpath.read_text());cfg['data']['weather_path']=str(D.relative_to(Path.cwd())/'weather_jan_mar_2026.parquet');cfg['data']['destination_popularity_path']=str(D.relative_to(Path.cwd())/'destination_popularity.parquet');cpath.write_text('# Active true-metre grid; legacy config preserved in legacy_914m_provenance.\n'+yaml.safe_dump(cfg,sort_keys=False))
    for path in [D/'grid_metadata.json',P/'grid_metadata.json']:
     meta=json.loads(path.read_text());meta['popularity_status']='REGENERATED_EXISTING_REFERENCE_CUTOFF_RUNTIME_AVAILABLE_FROM_2026_01_25_1830';dump(path,meta)
    # Complete per-artifact metadata, including small geometry/mask/pickle files.
    for path in D.iterdir():
     if path.suffix in ('.parquet','.npy','.pkl') and not path.with_suffix('.metadata.json').exists():
      dump(path.with_suffix('.metadata.json'),{**BASE,'source_candidate':'data/processed/grid_3km_candidate','sha256':sha(path)})
    manifest=pd.read_csv(R/'artifact_migration_manifest.csv').fillna('')
    for path in [D/'destination_popularity.parquet',D/'weather_jan_mar_2026.parquet']:
     if str(path.relative_to(Path.cwd())) not in set(manifest.new_path):
      manifest.loc[len(manifest)]={'artifact':path.name,'old_path':'','old_grid_version':'','new_path':str(path.relative_to(Path.cwd())),'new_grid_version':'true_3km_v1','status':'ACTIVE_NEW','regenerated':True,'requires_retraining':False,'superseded':False,'notes':'See metadata; popularity uses existing reference cutoff, not future CNN split.'}
    manifest.to_csv(R/'artifact_migration_manifest.csv',index=False)
    print('Quintiles',th.q20,th.q40,th.q60,th.q80,'stations',pd.read_parquet(D/'charging_stations.parquet').grid_id.nunique(),'unique grids')

def complete_static_contracts():
    from pathlib import Path
    import sys,json
    sys.path.insert(0,str(Path.cwd()))
    import pandas as pd,numpy as np
    from src.fleet.fleet import initialize_fleet
    fleet=initialize_fleet(5000,range(142),42)
    supply=pd.Series([v.current_grid for v in fleet]).value_counts().reindex(range(142),fill_value=0)
    save(pd.DataFrame({'GridID':range(142),'initial_idle_supply':supply.to_numpy(),'initial_incoming_supply':0}),'initial_supply_seed42.parquet','Existing uniform valid-grid initialization, 5000 vehicles, seed42. Static supply only; no simulation.')
    dump(D/'supply_reference.json',{**BASE,'fleet_size':5000,'seed':42,'supply_ref_p99':float(np.quantile(supply,.99)),'status':'STATIC_INITIALIZATION_REFERENCE_ONLY','demand_scaler':'Await new CNN training; do not use old pricing_context_scaler.json as migrated calibration.'})
    fare=pd.read_parquet(D/'fare_bootstrap_legacy_cutoff.parquet')
    save(fare.nlargest(5,'historical_fare_count'),'priority_grids_legacy_cutoff.parquet','Existing production top-five fare-count convention, retained old cutoff; review after final split, not final DQN statistic.')
    links=pd.read_parquet(D/'neighbour_map.parquet')
    links['TravelMinutesAt15Kmph']=links.DistanceMeters/1000/15*60
    links['EnergyKwhAt015PerKm']=links.DistanceMeters/1000*.15
    save(links,'neighbour_travel.parquet','Geometric travel distance, existing15km/h and .15kWh/km unchanged; no road-network or diagonal feasibility claim.')
    grid=pd.read_parquet(D/'grid_lookup.parquet')
    st=pd.read_parquet(D/'charging_stations.parquet')
    rows=[]
    for g in grid.itertuples():
     for station in st.itertuples():
      dist=float(np.hypot(g.CentroidX-station.location_x_m,g.CentroidY-station.location_y_m))
      rows.append((g.GridID,station.station_id,station.grid_id,dist,dist/1000/15*60,dist/1000*.15))
    save(pd.DataFrame(rows,columns=['GridID','station_id','station_grid_id','DistanceMeters','TravelMinutesAt15Kmph','EnergyKwhAt015PerKm']),'charging_navigation_distances.parquet','Metric geometric navigation inputs to preserved provisional station locations; runtime charging transition remains deferred to task D.')
    manifest=pd.read_csv(R/'artifact_migration_manifest.csv').fillna('')
    for path in sorted(D.glob('*.parquet')):
     if str(path.relative_to(Path.cwd())) not in set(manifest.new_path):
      manifest.loc[len(manifest)]={'artifact':path.name,'old_path':'','old_grid_version':'','new_path':str(path.relative_to(Path.cwd())),'new_grid_version':'true_3km_v1','status':'ACTIVE_NEW','regenerated':True,'requires_retraining':False,'superseded':False,'notes':'See companion metadata for source and runtime limitations.'}
    for path,note in [('config/pricing_context_scaler.json','Old CNN demand and1213-grid supply references; new demand calibration requires CNN training.'),('config/pricing_reward.json','Existing historical simulation reference; revalidate after final reward decision.')]:
     if path not in set(manifest.old_path):manifest.loc[len(manifest)]={'artifact':Path(path).name,'old_path':path,'old_grid_version':'legacy_3000_us_survey_feet','new_path':'','new_grid_version':'','status':'SUPERSEDED','regenerated':False,'requires_retraining':False,'superseded':True,'notes':note+' KEEP_PROVENANCE.'}
    manifest.to_csv(R/'artifact_migration_manifest.csv',index=False)
    print('Supply P99',np.quantile(supply,.99))

def finalize_provenance():
    from pathlib import Path
    import sys,json
    sys.path.insert(0,str(Path.cwd()))
    import yaml
    sources={
     'grid_lookup.parquet':['data/processed/grid_3km_candidate/grid_lookup_3km.parquet'],
     'grid_mask.npy':['data/processed/grid_3km_candidate/grid_raster_mapping_3km.parquet'],
     'zone_to_grids.pkl':['data/processed/grid_3km_candidate/zone_grid_mapping_3km.parquet'],
     'grid_raster_mapping.parquet':['data/processed/grid_3km_candidate/grid_raster_mapping_3km.parquet'],
     'zone_grid_mapping.parquet':['data/processed/grid_3km_candidate/zone_grid_mapping_3km.parquet'],
     'neighbour_map.parquet':['data/processed/grid_3km_candidate/neighbors_8way_3km.parquet'],
     'charging_stations.parquet':['data/processed/charging_stations_2026_01.parquet','data/processed/legacy_914m_provenance/grid_lookup.parquet'],
     'initial_supply_seed42.parquet':['src/fleet/fleet.py','data/processed/grid_lookup.parquet'],
    }
    for path in sorted(D.iterdir()):
     if path.suffix not in ('.parquet','.npy','.pkl'):continue
     meta_path=path.with_suffix('.metadata.json');meta=json.loads(meta_path.read_text())
     if not meta.get('sources'):
      meta['sources']=sources.get(path.name,[str((D/'trips_jan_mar_2026.parquet').relative_to(Path.cwd())),str((D/'grid_lookup.parquet').relative_to(Path.cwd()))])
     meta['source_version']='Existing local 2026 Jan–Mar sources; source hashes in source_reconciliation.json and artifact_index.json'
     dump(meta_path,meta)
    index={str(p.relative_to(Path.cwd())):sha(p) for p in D.iterdir() if p.is_file()}
    dump(R/'artifact_index.json',index)
    meta=json.loads((R/'activation_complete.json').read_text());meta.update(legacy_source_git_commit='0cca91368bda5f81a5eb6ad1692ed8b2748fbf96',popularity='Existing reference cutoff retained; pre-cutoff runtime encoding masked',new_policy_dimensions=[155,64,32,9]);dump(R/'activation_complete.json',meta)
    cpath=Path('config/config.yaml');cfg=yaml.safe_load(cpath.read_text())
    for key,name in [('fare_bootstrap_path','fare_bootstrap_legacy_cutoff.parquet'),('priority_grids_path','priority_grids_legacy_cutoff.parquet'),('initial_supply_path','initial_supply_seed42.parquet'),('movement_distance_path','neighbour_travel.parquet'),('charging_navigation_distances_path','charging_navigation_distances.parquet')]:cfg['data'][key]=str((D/name).relative_to(Path.cwd()))
    cpath.write_text('# Active true-metre grid; legacy config preserved in legacy_914m_provenance.\n'+yaml.safe_dump(cfg,sort_keys=False))

def main():
    if (R/'activation_complete.json').exists():
        validate();return
    for p in (D,L,R):p.mkdir(parents=True,exist_ok=True)
    protected_file=R/'protected_fingerprints.json'
    if not protected_file.exists():
        protected={}
        roots=[P/'price_distance_sensitivity_record029',P/'elasticity_v2', ROOT/'models',P/'cnn',
               ROOT/'results/analysis/2026-10-09_price_distance_sensitivity_record029_full_jan_mar',
               ROOT/'results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios']
        for root in roots:
            for p in root.rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:protected[str(p.relative_to(ROOT))]=sha(p)
        dump(protected_file,protected)
    originals=['grid_lookup.parquet','grid_mask.npy','grid_metadata.json','zone_grid_mapping.parquet','zone_to_grids.pkl','neighbour_map.parquet','cleaned_trips.parquet']
    for name in originals:
        if not (L/name).exists():shutil.copy2(P/name,L/name)
    if not (L/'config.yaml').exists():shutil.copy2(ROOT/'config/config.yaml',L/'config.yaml')
    dump(R/'legacy_fingerprints.json',{str(p.relative_to(ROOT)):sha(p) for p in L.iterdir() if p.is_file()})
    grid=gpd.read_parquet(C/'grid_lookup_3km.parquet');validate_metric_grid(grid)
    assert len(grid)==142
    raster=pd.read_parquet(C/'grid_raster_mapping_3km.parquet')
    zones=pd.read_parquet(C/'zone_grid_mapping_3km.parquet')
    assert zones.LocationID.nunique()==263
    lookup=build_zone_to_grids(zones)
    links=pd.read_parquet(C/'neighbors_8way_3km.parquet')
    pd.testing.assert_frame_equal(links,build_metric_neighbors(grid,'8way'))
    assert len(links)==958
    names=['north','northeast','east','southeast','south','southwest','west','northwest']
    links['Direction']=links.ActionIndex.map(dict(enumerate(names,1)))
    grid.to_parquet(D/'grid_lookup.parquet',index=False)
    save(raster,'grid_raster_mapping.parquet',sources=[str(C.relative_to(ROOT))])
    save(zones,'zone_grid_mapping.parquet','Polygon-intersection inclusion; no centroid or majority-area substitution.')
    save(links,'neighbour_map.parquet','Eight-way geometry; no road/water feasibility claim.')
    actions=[]
    by_key=links.set_index(['GridID','ActionIndex'])
    for g in range(142):
        for a,name in enumerate(['stay']+names):
            if a==0:dst,dist,valid=g,0.,True
            elif (g,a) in by_key.index:
                row=by_key.loc[(g,a)];dst,dist,valid=int(row.NeighbourGridID),float(row.DistanceMeters),True
            else:dst,dist,valid=None,None,False
            actions.append((g,a,a+1,name,dst,valid,dist))
    save(pd.DataFrame(actions,columns=['GridID','ActionIndex','ExternalRelativeIndex','Direction','DestinationGridID','ValidAction','DistanceMeters']),'action_masks.parquet')
    mask=np.zeros((16,16),dtype=np.uint8);mask[grid.Row,grid.Column]=1
    np.save(D/'grid_mask.npy',mask)
    with (D/'zone_to_grids.pkl').open('wb') as f:pickle.dump(lookup,f)
    print('Candidate validated; legacy preserved',flush=True)
    staged = ['trips_jan_mar_2026.parquet','demand_master_jan_mar_2026.parquet','destination_popularity_source.parquet','od_counts.parquet','centroid_distances.parquet','charging_stations.parquet','fare_bootstrap_legacy_cutoff.parquet']
    if all((D/name).exists() for name in staged) and (R/'source_reconciliation.json').exists():
        # Reuse only complete, hash-verified staged products.
        for name in staged:
            meta=json.loads((D/name).with_suffix('.metadata.json').read_text())
            assert sha(D/name)==meta['sha256'],name
        sources=json.loads((R/'source_reconciliation.json').read_text())['source_files']
        for source in sources:assert sha(ROOT/source['path'])==source['sha256']
        reconciliation=pd.read_csv(R/'data_reconciliation.csv').to_dict('records')
        print('Reusing hash-verified completed staged data',flush=True)
    else:
        frames=[];reconciliation=[];sources=[];filtering={}
        for m in (1,2,3):
            if m==1:
                source=L/'cleaned_trips.parquet';trips=pd.read_parquet(source).drop(columns=['PUGridID','DOGridID'])
                prep={'records_loaded':len(trips),'already_cleaned':True}
            else:
                source=ROOT/f'data/raw/yellow_taxi/yellow_tripdata_2026-{m:02d}.parquet'
                trips,prep=prepare_legacy_trips(load_taxi_data(source),set(lookup))
            # Restrict only to the declared overall date window, not source-file month.
            in_period=trips.tpep_pickup_datetime.ge(START)&trips.tpep_pickup_datetime.lt(END)
            prep['outside_jan_mar_pickup_window']=int((~in_period).sum())
            trips=trips.loc[in_period].reset_index(drop=True)
            trips['source_file_month']=m;trips['source_prepared_row']=np.flatnonzero(in_period)
            rng=np.random.default_rng(42+m)
            for zone,out in [('PULocationID','PUGridID'),('DOLocationID','DOGridID')]:
                trips=assign_grid_ids_by_zone_legacy(trips,zone,out,lookup,rng)
            trips['pickup_grid_id']=trips.PUGridID;trips['dropoff_grid_id']=trips.DOGridID
            assert trips.PUGridID.between(0,141).all() and trips.DOGridID.between(0,141).all()
            frames.append(trips);filtering[str(m)]=prep;sources.append({'path':str(source.relative_to(ROOT)),'sha256':sha(source)})
            print('Mapped source month',m,len(trips),flush=True)
        trips=pd.concat(frames,ignore_index=True);del frames
        save(trips,'trips_jan_mar_2026.parquet','Existing NB2 valid-zone population; not the passenger-sensitivity population. Seeded intersecting-zone assignment, seed=42+source month; pickup then dropoff.',sources)
        slots=pd.date_range(START,END,freq='30min',inclusive='left')
        dense=pd.MultiIndex.from_product([slots,range(142)],names=['TimeSlot','GridID']).to_frame(index=False)
        counts=trips.groupby([trips.tpep_pickup_datetime.dt.floor('30min'),'PUGridID']).size()
        counts.index.names=['TimeSlot','GridID']
        demand=dense.merge(counts.rename('Demand'),on=['TimeSlot','GridID'],how='left')
        demand.Demand=demand.Demand.fillna(0).astype('int32')
        demand=demand.merge(grid[['GridID','Row','Column']],on='GridID',how='left',validate='many_to_one')
        weather=pd.concat([pd.read_parquet(P/f'weather/nyc_weather_processed_2026_{m:02d}.parquet') for m in (1,2,3)],ignore_index=True)
        assert not weather.Datetime.duplicated().any()
        demand['Datetime']=demand.TimeSlot.dt.floor('h')
        demand=demand.merge(weather,on='Datetime',how='left',validate='many_to_one').drop(columns='Datetime')
        assert demand[['Temperature','WindSpeed','WeatherCode']].notna().all().all()
        demand['DayOfWeek']=demand.TimeSlot.dt.dayofweek;demand['Hour']=demand.TimeSlot.dt.hour
        demand['PeriodWithinHour']=(demand.TimeSlot.dt.minute//30).astype('int8')
        demand['TimeIndex']=np.repeat(np.arange(len(slots)),142)
        save(demand,'demand_master_jan_mar_2026.parquet','Requests/grid/30min, zero-filled full domain. Raw weather codes retained. No historical-average plane or scalers fitted.',sources)
        pop=trailing_dropoff_average(aggregate_dropoffs(trips,range(142),slots))
        save(pop,'destination_popularity_source.parquet','Existing strictly lagged six-slot mean. Not a probability distribution; no sum-to-one normalization. Quintile encoding deferred until training split frozen; no future-fitted thresholds.',sources)
        for m in (1,2,3):
            t=trips.loc[trips.tpep_pickup_datetime.dt.month==m]
            d=demand.loc[demand.TimeSlot.dt.month==m]
            reconciliation.append(dict(month=f'2026-{m:02d}',source_rows=len(t),mapped_pickups=len(t),mapped_dropoffs=len(t),aggregated_demand=int(d.Demand.sum()),unmapped_pickups=0,unmapped_dropoffs=0,valid_grids=142,time_slots=d.TimeSlot.nunique(),dropoffs_in_window=int(pop.loc[pop.TimeSlot.dt.month==m,'dropoff_count'].sum())))
        total={k:sum(x[k] for x in reconciliation) for k in reconciliation[0] if k not in ('month','valid_grids')};total.update(month='Jan–Mar total',valid_grids=142)
        reconciliation.append(total);pd.DataFrame(reconciliation).to_csv(R/'data_reconciliation.csv',index=False)
        dump(R/'source_reconciliation.json',{'source_files':sources,'source_file_filtering':filtering,'dropoffs_outside_window':int((~trips.tpep_dropoff_datetime.between(START,END,inclusive='left')).sum()),'population':'Existing NB2 location-ID cleaning, no new fare/distance/duration filters.'})
        od=trips.groupby(['PUGridID','DOGridID']).size().rename('trip_count').reset_index()
        save(od,'od_counts.parquet','Descriptive full-period OD counts; not a runtime feature fitted on future trips.')
        xy=np.c_[grid.CentroidX,grid.CentroidY];dist=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=-1)
        save(pd.DataFrame({'GridID':np.repeat(np.arange(142),142),'DestinationGridID':np.tile(np.arange(142),142),'DistanceMeters':dist.ravel()}),'centroid_distances.parquet','Straight-line projected distance, not road distance.')
        # Preserve each provisional station at its old cell centroid; never select new top grids.
        oldgrid=gpd.read_parquet(L/'grid_lookup.parquet').set_index('GridID')
        stations=pd.read_parquet(P/'charging_stations_2026_01.parquet')
        points=gpd.GeoDataFrame(stations.copy(),geometry=[oldgrid.loc[g].geometry.centroid for g in stations.grid_id],crs=oldgrid.crs).to_crs(grid.crs)
        joined=gpd.sjoin(points,grid[['GridID','geometry']],how='left',predicate='within').sort_index()
        assert len(joined)==15 and joined.GridID.notna().all()
        stations['legacy_grid_id']=stations.grid_id;stations['grid_id']=joined.GridID.astype(int).to_numpy()
        stations['location_x_m']=points.geometry.x;stations['location_y_m']=points.geometry.y
        save(stations,'charging_stations.parquet','Provisional synthetic stations remapped from preserved old-cell centroids. 15 station identities retained, co-location allowed; power/capacity config unchanged. Historical popularity counts retained, not reranked.')
        # Existing pre-cutoff fare bootstrap is static; retain its cutoff, not a new CNN split.
        from src.routing.production import build_fare_bootstrap
        fare,faremeta=build_fare_bootstrap(trips,range(142))
        save(fare,'fare_bootstrap_legacy_cutoff.parquet','Legacy pre-Jan25 18:30 reference only. Requires split review for final runtime; no final operational-statistics redesign.')
        dump(D/'fare_bootstrap_legacy_cutoff.details.json',faremeta)
    metadata={**BASE,'status':'ACTIVE_NEW','metric_crs':'EPSG:32118','grid_construction_crs':'EPSG:32118','grid_cell_size_m':3000,'grid_size_meters':3000,'valid_cells':142,'grid_rows':16,'grid_columns':16,'generated_cells':256,'unused_cells':114,'neighbor_links':958,'neighbour_topology':'eight_way','geometry_tolerance_m':1e-6,'source_candidate':str(C.relative_to(ROOT)),'sources':sources,'action_order':['STAY']+[n.upper() for n in names],'topology':topology_summary(grid,build_metric_neighbors(grid,'8way'),'8way'),'cnn_status':'PREPROCESSING_AND_RETRAINING_REQUIRED','historical_demand':'Deferred: fit with training data only','popularity_status':'LAGGED_SOURCE_READY_QUINTILES_AWAIT_TRAINING_SPLIT'}
    dump(D/'grid_metadata.json',metadata)
    # Only after the full staged foundation is built, promote coherent spatial artifacts.
    for name in originals[:-1]:shutil.copy2(D/name,P/name)
    cfg=yaml.safe_load((L/'config.yaml').read_text())
    cfg['grid']={'geometry':'square','grid_cell_size_m':3000,'grid_construction_crs':'EPSG:32118','neighbour_topology':'eight_way','valid_grid_count':142,'raster_rows':16,'raster_columns':16,'grid_version':VERSION}
    cfg['data'].update(spatial_foundation_dir=str(D.relative_to(ROOT)),trips_path=str((D/'trips_jan_mar_2026.parquet').relative_to(ROOT)),demand_master_path=str((D/'demand_master_jan_mar_2026.parquet').relative_to(ROOT)),destination_popularity_path=str((D/'destination_popularity_source.parquet').relative_to(ROOT)),charging_stations_path=str((D/'charging_stations.parquet').relative_to(ROOT)),cnn_dataset_dir='data/processed/cnn_3km_jan_mar_2026')
    cfg['cnn']={'forecast_minutes':30,'forecast_status':'DOCUMENTED_ADAPTATION','dataset_start':str(START),'dataset_end_exclusive':str(END),'raster_rows':16,'raster_columns':16,'valid_grid_count':142,'preprocessing_status':'NOT_BUILT','historical_average_fit':'TRAINING_ONLY','scaler_fit':'TRAINING_ONLY','split':'CHRONOLOGICAL_TO_BE_FROZEN'}
    (ROOT/'config/config.yaml').write_text('# Active true-metre grid; legacy configuration is preserved in legacy_914m_provenance.\n'+yaml.safe_dump(cfg,sort_keys=False))
    rows=[]
    def entry(artifact,old,new,status,regen=False,retrain=False,note=''):
        rows.append(dict(artifact=artifact,old_path=old,old_grid_version='legacy_3000_us_survey_feet' if old else '',new_path=new,new_grid_version=VERSION if new else '',status=status,regenerated=regen,requires_retraining=retrain,superseded=bool(old and status in ('SUPERSEDED','RETRAIN_REQUIRED')),notes=note))
    for name in originals[:-1]:entry(name,str((L/name).relative_to(ROOT)),str((P/name).relative_to(ROOT)),'ACTIVE_NEW',True,note='Legacy bytes retained and hashed.')
    for p in sorted(D.iterdir()):
        if p.suffix in ('.parquet','.npy','.pkl'):entry(p.name,'',str(p.relative_to(ROOT)),'ACTIVE_NEW',True,note='Source foundation; metadata describes deferred threshold fitting where applicable.')
    for root in (P/'cnn',ROOT/'models'):
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:entry(p.name,str(p.relative_to(ROOT)),'','RETRAIN_REQUIRED',retrain=True,note='KEEP_PROVENANCE; SUPERSEDED_FOR_FINAL_JAN_MAR_3KM_CNN or SUPERSEDED_BY_3KM_9ACTION_MIGRATION; no overwrite.')
    for name in ['cleaned_trips.parquet','demand_master_2026_01.parquet','destination_popularity_2026_01.parquet','charging_stations_2026_01.parquet','nb9_fare_bootstrap_2026_01_25_1830.parquet']:
        entry(name,str((P/name).relative_to(ROOT)),'','SUPERSEDED',note='Retained historical old-grid artifact; active config uses versioned replacement.')
    for name in ['driver_preferences_seed42.parquet','customer_price_sensitivity_2026_01.parquet','customer_price_sensitivity_fallback_2026_01.parquet']:
        entry(name,str((P/name).relative_to(ROOT)),'','KEEP_PROVENANCE',note='Preserved; runtime reference-period/methodology review deferred; not regenerated.')
    entry('Record-029',str((P/'price_distance_sensitivity_record029').relative_to(ROOT)),'','UNCHANGED',note='Fingerprint protected; no recomputation.')
    for root in (ROOT/'results',ROOT/'outputs'):
        for p in root.iterdir():
            if p.is_dir() and p.name!='analysis':entry(p.name,str(p.relative_to(ROOT)),'','KEEP_PROVENANCE',note='Historical environment; not directly comparable to migrated grid.')
    pd.DataFrame(rows).to_csv(R/'artifact_migration_manifest.csv',index=False)
    complete_source_contracts()
    complete_static_contracts()
    validate()
    dump(R/'activation_complete.json',{**BASE,'validation':'PASS','no_training':True,'passenger_sensitivity_unchanged':True})
    finalize_provenance()
    print(pd.DataFrame(reconciliation).to_string(index=False),flush=True)

if __name__=='__main__':main()
