"""Measured active geometry/data contracts and nine-action structural fixtures."""
import unittest
import json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from src.spatial.metric_grid import validate_metric_grid, build_metric_neighbors, topology_summary
from src.routing.baseline import ACTION_ORDER, RoutingAction, movement_distance_m, RoutingParameters, execute_reposition, RoutingState, GridRoutingFeatures
from src.routing.learning import STATE_DIMENSION, RoutingLearningParameters, build_routing_policy_model
from src.charging.energy import EnergyParameters
from src.fleet.state import VehicleState, VehicleStatus
from src.data.config import load_config
P=Path('data/processed');D=P/'spatial_3km_jan_mar_2026'
class ActiveFoundationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.grid=gpd.read_parquet(P/'grid_lookup.parquet')
  cls.links=pd.read_parquet(P/'neighbour_map.parquet')
  cls.demand=pd.read_parquet(D/'demand_master_jan_mar_2026.parquet')
 def test_measured_geometry_and_reversible_raster(self):
  validate_metric_grid(self.grid)
  np.testing.assert_allclose(self.grid.geometry.area,9e6,rtol=0,atol=1e-6)
  self.assertEqual(len(self.grid),142)
  r=pd.read_parquet(D/'grid_raster_mapping.parquet')
  self.assertEqual((len(r),int(r.ValidMask.sum())),(256,142))
  self.assertFalse(r[['Row','Column']].duplicated().any())
  pd.testing.assert_frame_equal(r.loc[r.ValidMask,['GridID','Row','Column']].astype('int64').reset_index(drop=True),self.grid[['GridID','Row','Column']].astype('int64'))
 def test_neighbors_and_boundary_masks(self):
  expected=build_metric_neighbors(self.grid,'8way')
  self.assertEqual(len(self.links),958)
  np.testing.assert_allclose(self.links.DistanceMeters,expected.DistanceMeters,atol=1e-6,rtol=0)
  self.assertEqual(self.links.NeighbourGridID.tolist(),expected.NeighbourGridID.tolist())
  self.assertEqual(topology_summary(self.grid,expected,'8way')['connected_component_sizes'],[142])
  a=pd.read_parquet(D/'action_masks.parquet')
  self.assertEqual(len(a),142*9)
  self.assertEqual(int(a.ValidAction.sum()),958+142)
  self.assertTrue(a.loc[~a.ValidAction,'DestinationGridID'].isna().all())
  self.assertEqual(a.ExternalRelativeIndex.tolist(),(a.ActionIndex+1).tolist())
 def test_movement_and_nine_output_structure(self):
  self.assertEqual([x.value for x in ACTION_ORDER],['STAY','NORTH','NORTHEAST','EAST','SOUTHEAST','SOUTH','SOUTHWEST','WEST','NORTHWEST'])
  self.assertEqual(movement_distance_m('STAY'),0)
  self.assertEqual(movement_distance_m('EAST'),3000)
  self.assertAlmostEqual(movement_distance_m('NORTHEAST'),3000*np.sqrt(2))
  self.assertAlmostEqual(RoutingParameters(15,3,30).duration_minutes(RoutingAction.NORTHEAST),12*np.sqrt(2))
  model=build_routing_policy_model(RoutingLearningParameters(),seed=42)
  self.assertEqual((STATE_DIMENSION,model.input_shape,model.output_shape),(155,(None,155),(None,9)))
 def test_diagonal_energy_and_arrival_time(self):
  f=GridRoutingFeatures(1,1,1,1,0,0,10,1,10,1,1,1,1,1,False,0)
  state=RoutingState(0,0,40,f,{RoutingAction.NORTHEAST:f})
  vehicle=VehicleState(0,0,VehicleStatus.IDLE,None,0,'idle',40)
  energy=EnergyParameters(75,60,7.5,.15,30,.9,75,.5,.05,.5,.7,.2)
  tr=execute_reposition(vehicle,state,RoutingAction.NORTHEAST,RoutingParameters(15,3,30),energy)
  self.assertAlmostEqual(tr.distance_km,3*np.sqrt(2))
  self.assertAlmostEqual(40-vehicle.energy_level,.15*3*np.sqrt(2))
  self.assertAlmostEqual(vehicle.remaining_travel_time,12*np.sqrt(2))
 def test_complete_demand_and_reconciliation(self):
  d=self.demand;slots=pd.date_range('2026-01-01','2026-04-01',freq='30min',inclusive='left')
  self.assertEqual(len(d),4320*142)
  self.assertTrue(pd.DatetimeIndex(d.TimeSlot.drop_duplicates()).equals(slots))
  self.assertFalse(d[['TimeSlot','GridID']].duplicated().any())
  self.assertFalse(d.isna().any().any())
  self.assertEqual(set(d.GridID),set(range(142)))
  self.assertGreater(int((d.Demand==0).sum()),0)
  r=pd.read_csv('results/analysis/2026-10-19_true_3km_grid_activation/data_reconciliation.csv')
  for _,row in r.iloc[:3].iterrows():
   self.assertEqual(int(d.loc[d.TimeSlot.dt.month==int(row.month[-2:]),'Demand'].sum()),row.source_rows)
   self.assertEqual(row.source_rows,row.mapped_dropoffs)
 def test_no_future_historical_feature_and_explicit_config(self):
  self.assertNotIn('HistoricalDemand',self.demand)
  self.assertEqual(set(self.demand.PeriodWithinHour),{0,1})
  c=load_config();self.assertEqual(c['cnn']['forecast_minutes'],30)
  self.assertEqual(c['grid']['grid_construction_crs'],'EPSG:32118')
  self.assertNotIn('size_meters',c['grid'])
 def test_stations_preserved(self):
  new=pd.read_parquet(D/'charging_stations.parquet');old=pd.read_parquet(P/'charging_stations_2026_01.parquet')
  self.assertEqual(new.station_id.tolist(),old.station_id.tolist())
  self.assertEqual(len(new),15)
  self.assertTrue(new.grid_id.between(0,141).all())
  for col in ['pickup_count','dropoff_count','popularity']:self.assertEqual(new[col].tolist(),old[col].tolist())
 def test_lagged_popularity_no_future(self):
  from src.popularity.destination import trailing_dropoff_average
  pop=pd.read_parquet(D/'destination_popularity_source.parquet')
  pd.testing.assert_frame_equal(pop,trailing_dropoff_average(pop[['TimeSlot','GridID','dropoff_count']]))
  self.assertTrue(pop.loc[pop.TimeSlot==pop.TimeSlot.min(),'dropoff_ma_3h'].isna().all())
  self.assertEqual(pop.dropoff_count.sum(),11005364)

 def test_popularity_encoding_is_reference_only_and_normalized_ordinal(self):
  from src.popularity.destination import fit_popularity_thresholds, apply_popularity_levels
  source=pd.read_parquet(D/'destination_popularity_source.parquet')
  actual=pd.read_parquet(D/'destination_popularity.parquet')
  cutoff=pd.Timestamp('2026-01-25 18:30')
  reference=source.loc[source.TimeSlot<cutoff,'dropoff_ma_3h']
  thresholds=fit_popularity_thresholds(reference,reference_start='2026-01-01',reference_end_exclusive=cutoff)
  expected=apply_popularity_levels(source,thresholds)
  pd.testing.assert_frame_equal(actual.loc[actual.TimeSlot>=cutoff].reset_index(drop=True),expected.loc[expected.TimeSlot>=cutoff].reset_index(drop=True))
  self.assertTrue(actual.loc[actual.TimeSlot<cutoff,'popularity_value'].isna().all())
  self.assertTrue(set(actual.popularity_value.dropna()).issubset({0,.25,.5,.75,1}))
 def test_migrated_station_schema_and_supply_static(self):
  from src.charging.stations import validate_station_definition, stations_from_definition
  stations=pd.read_parquet(D/'charging_stations.parquet')
  validate_station_definition(stations,range(142),15)
  objects=stations_from_definition(stations,3000,30)
  self.assertEqual(len(objects),15)
  self.assertTrue(all(x.max_power_kw==3000 for x in objects))
  supply=pd.read_parquet(D/'initial_supply_seed42.parquet')
  self.assertEqual(supply.initial_idle_supply.sum(),5000)
  self.assertEqual(supply.initial_incoming_supply.sum(),0)
 def test_legacy_production_is_blocked_on_new_grid(self):
  from src.simulation.production import LegacyProductionExperiment
  with self.assertRaisesRegex(RuntimeError,'superseded'):
   LegacyProductionExperiment(Path.cwd(),seed=42)
