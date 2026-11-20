import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np,pandas as pd
from src.routing.online_provenance import OnlineHierarchy,validate,weight_hash,AGGREGATION
from src.routing.learning import LocalRoutingLearner,LocalPolicyObservation
from src.simulation.v3_checkpoint_codec import encode
from src.simulation.information_cutoff import validate_manifest
from src.simulation.od_pricing_checkpoint import save_od_checkpoint,load_od_checkpoint
from src.simulation.od_pricing_runtime import ODPricingRuntime
from tests.test_research_hierarchy import fleet
from tests.test_utc_od_runtime import inputs
P=Path('results_v2/federated_learning/2026-11-17_online_routing_retry_001')
def contract():return json.loads((P/'routing_initialization.json').read_text())
def synthetic_update(self,slot):
 # Parameter payload fixture, NOT gradient training. Unequal counts expose weighting errors.
 if slot in self._trained_slots:raise ValueError('Duplicate fixture update')
 self._trained_slots.add(slot);self.optimizer.build(self.policy_model.trainable_variables)
 self.optimizer.iterations.assign_add(1)
 self.policy_model.set_weights([w+np.float32(self.vehicle_id+1) for w in self.policy_model.get_weights()])
 self.local_sample_count+=self.vehicle_id+1;self.gradient_updates+=1
 return 0.
def record(h,slot,drivers=(0,1)):
 for d in drivers:h.record(d,LocalPolicyObservation(np.ones(169,dtype=np.float32),d%9,np.ones(9,dtype=bool),slot_id=slot),event_time=pd.Timestamp(h.provenance['experiment_start'])+pd.Timedelta(minutes=30*(slot+1)))
class OnlineTests(unittest.TestCase):
 def test_fresh_identity_and_rejection(self):
  c=contract();a=OnlineHierarchy(c);b=OnlineHierarchy(c)
  self.assertEqual(weight_hash(a._global.get_weights()),weight_hash(b._global.get_weights()))
  for key,value in [('historical_checkpoint','old.keras'),('offline_fitting_period',['March1','March15']),('validation_selection_period',['March13','March15']),('seed',43)]:
   bad=copy.deepcopy(c);bad[key]=value
   with self.assertRaises(ValueError):OnlineHierarchy(bad)
  bad=copy.deepcopy(c);bad['source_sha256'][next(iter(bad['source_sha256']))]='changed'
  with self.assertRaises(ValueError):validate(bad)
 def test_equal_client_timing_private_release_and_resume(self):
  a=OnlineHierarchy(contract(),updates_enabled=True);start=pd.Timestamp(a.provenance['experiment_start']);before=[x.copy() for x in a._global.get_weights()]
  with patch.object(LocalRoutingLearner,'train_for_slot',synthetic_update):
   record(a,0);release=a.finish_slot(start,start+pd.Timedelta(minutes=30))
   for old,new in zip(before,a._global.get_weights()):np.testing.assert_allclose(new,old+1.5,atol=2e-7)
   self.assertEqual(release['participants'],2);self.assertEqual(release['global_version'],1);self.assertEqual(release['aggregation'],AGGREGATION)
   self.assertNotIn('memory',release);self.assertNotIn('preferences',release)
   with self.assertRaises(ValueError):a.mean_probabilities([np.ones(169)],{0:np.ones(9,dtype=bool)},start)
   b=OnlineHierarchy.restore(a.snapshot())
   for h in [a,b]:record(h,1,drivers=(0,));h.finish_slot(start+pd.Timedelta(minutes=30),start+pd.Timedelta(minutes=60))
   self.assertEqual(encode(a.snapshot()),encode(b.snapshot()))
   mask=np.array([True,False,True]+[False]*6);p=a.mean_probabilities([np.ones(169)],{0:mask},start+pd.Timedelta(minutes=60))[0]
   self.assertTrue(np.isfinite(p).all());self.assertAlmostEqual(p.sum(),1);self.assertEqual(p[~mask].sum(),0)
 def test_future_experiences_and_corrupt_resume(self):
  h=OnlineHierarchy(contract());start=pd.Timestamp(h.provenance['experiment_start']);o=LocalPolicyObservation(np.ones(169,dtype=np.float32),0,np.ones(9,dtype=bool),slot_id=0)
  with self.assertRaises(ValueError):h.record(0,o,event_time=start+pd.Timedelta(minutes=31))
  with self.assertRaises(ValueError):h.finish_slot(start+pd.Timedelta(minutes=30),start+pd.Timedelta(minutes=60))
  record(h,0);h.finish_slot(start,start+pd.Timedelta(minutes=30));s=h.snapshot();s['experience_cutoff']=start+pd.Timedelta(days=1)
  with self.assertRaises(ValueError):OnlineHierarchy.restore(s)
 @patch.object(LocalRoutingLearner,'train_for_slot',synthetic_update)
 def test_runtime_checkpoint_and_mixed_fleet(self):
  manifest=json.loads((P/'information_contract.json').read_text());validate_manifest(manifest)
  bundle=inputs('2026-03-12');a=manifest['artifacts'];table=pd.read_csv(a['forecast']['path'])
  from src.simulation.utc_od_inputs import BASELINE
  bundle['forecast_protocol']=BASELINE;bundle['checkpoint_metadata']['version']=BASELINE
  bundle['baseline_provenance']=dict(method='January grid/local-half-hour arithmetic mean',training_start='2026-01-01',training_end_exclusive='2026-02-01',available_at='2026-02-01T05:00Z',artifact_path=a['forecast']['path'],artifact_sha256=a['forecast']['sha256'])
  for t,f in bundle['forecasts'].items():
   local=pd.Timestamp(t).tz_convert('America/New_York');period=local.hour*2+local.minute//30
   f['predicted_demand']=table[table.period==period].set_index('Grid_ID').reindex(f.Grid_ID).predicted_demand.to_numpy()
  bundle['popularity']={int(k):v for k,v in json.loads(Path(a['popularity']['path']).read_text()).items()}
  r=ODPricingRuntime(start='2026-03-12T04:00Z',routing_checkpoint=a['routing']['path'],research_routing=True,information_contract=manifest,sensitivity_contract=a['sensitivity']['path'],od_support=json.loads(Path(a['od_support']['path']).read_text()),utc_inputs=bundle,driver_hierarchy=OnlineHierarchy(contract(),updates_enabled=True),fleet=fleet(10),ev_share=.2)
  r.run_slot([],policy=lambda d,s:0)
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'checkpoint';save_od_checkpoint(r,path)
   kw=dict(master_math=True,utc_mode=True,information_contract=manifest,hierarchy_contract=r.engine.driver_hierarchy.contract(),ev_composition=r.engine.ev_composition)
   bad=copy.deepcopy(kw);bad['hierarchy_contract']['online_provenance_sha256']='wrong'
   with self.assertRaises(ValueError):load_od_checkpoint(path,**bad)
   other=load_od_checkpoint(path,**kw)
   for x in [r,other]:x.run_slot([],policy=lambda d,s:0)
   self.assertEqual(r.engine.driver_hierarchy.global_version,2)
   self.assertEqual(encode(r.engine.driver_hierarchy.snapshot()),encode(other.engine.driver_hierarchy.snapshot()));self.assertEqual(encode(r.engine.fleet),encode(other.engine.fleet));self.assertEqual(encode(r.engine.charging),encode(other.engine.charging))
   for pair in r.states:np.testing.assert_array_equal(r.states[pair],other.states[pair])
