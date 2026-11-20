import copy,json,hashlib,tempfile,unittest
from pathlib import Path
from src.simulation.information_cutoff import validate_artifact,validate_manifest,validate_event,VERSION
from src.pricing.prospective_binned_sampler import ProspectiveBinnedSensitivity
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.od_pricing_checkpoint import load_od_checkpoint
from src.simulation.master_od_contract import utc
CAL=Path('results_v2/simulation/2026-11-17_prospective_acceptance_v1/sampling_contract.json')
class CutoffTests(unittest.TestCase):
 def test_boundary_future_hash_selection(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'a';p.write_text('fixed')
   a=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_start='2026-01-01T00:00:00-05:00',source_end_exclusive='2026-03-01T00:00:00-05:00',latest_observation='2026-02-28T23:59:59-05:00',fitting_cutoff='2026-03-01T00:00:00-05:00',methodology_version='TEST')
   cutoff=a['fitting_cutoff'];validate_artifact(a,cutoff)
   for key in ['latest_observation','source_end_exclusive','fitting_cutoff']:
    bad=dict(a,**{key:'2026-03-02T00:00:00-05:00'})
    with self.assertRaises(ValueError):validate_artifact(bad,cutoff)
   with self.assertRaisesRegex(ValueError,'selection'):validate_artifact(dict(a,selection_end_exclusive='2026-03-16T00:00:00-04:00'),cutoff)
   m=dict(version=VERSION,artifacts={'sensitivity':a},permitted_cutoffs={'sensitivity':cutoff});validate_manifest(m)
   m['permitted_cutoffs']['sensitivity']='2026-03-16T00:00:00-04:00'
   with self.assertRaises(ValueError):validate_manifest(m)
   p.write_text('changed')
   with self.assertRaises(ValueError):validate_artifact(a,cutoff)
 def test_realized_events_not_fitted(self):
  validate_event(utc('2026-03-12 00:15'),utc('2026-03-12'),utc('2026-03-12 00:30'))
  with self.assertRaises(ValueError):validate_event(utc('2026-03-12 00:30'),utc('2026-03-12'),utc('2026-03-12 00:30'))
 def test_calibration_sampling_and_resume(self):
  a=ProspectiveBinnedSensitivity(CAL,42);b=ProspectiveBinnedSensitivity(CAL,42)
  for code in [1,8,15,99]:
   for t in ['2026-03-12','2026-03-12 05:00','2026-03-12 10:00','2026-03-12 17:00']:
    x=a.draw(code,t);self.assertEqual(x,b.draw(code,t));self.assertGreater(x['epsilon'],0)
    self.assertGreaterEqual(a.counts[x['sensitivity_condition']],5000)
  restored=type(a).restore(a.snapshot());self.assertEqual(a.draw(1,'2026-03-12'),restored.draw(1,'2026-03-12'))
  self.assertEqual(a.calibration['source_N'],5457435)
 def test_requires_provenance_before_engine(self):
  with self.assertRaisesRegex(ValueError,'requires information'):
   ODPricingRuntime(start='2026-03-12',routing_checkpoint='unused',sensitivity_contract=CAL)
 def test_checkpoint_manifest_mismatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'manifest.json').write_text(json.dumps({'schema':'FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_5','information_contract':{'version':'OLD'}}))
   with self.assertRaisesRegex(ValueError,'Incompatible'):load_od_checkpoint(p)

 def test_saved_calibration_future_and_fallback_tampering(self):
  c=json.loads(CAL.read_text())
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'calibration.json'
   bad=copy.deepcopy(c);bad['calibration_period']='2026-01-01 <= pickup_timestamp < 2026-03-16';p.write_text(json.dumps(bad))
   with self.assertRaises(ValueError):ProspectiveBinnedSensitivity(p)
   bad=copy.deepcopy(c);bad['support_counts']['GLOBAL']+=1;p.write_text(json.dumps(bad))
   with self.assertRaises(ValueError):ProspectiveBinnedSensitivity(p)
   bad=copy.deepcopy(c);bad['population_provenance']['latest_observation']='2026-03-01T00:00:00-05:00';p.write_text(json.dumps(bad))
   with self.assertRaises(ValueError):ProspectiveBinnedSensitivity(p)
 def test_actual_routing_lineage_stops_before_engine(self):
  from unittest.mock import patch
  m=json.loads(CAL.with_name('information_contract.json').read_text())
  with patch('src.simulation.od_pricing_runtime.ProductionExperiment') as engine:
   with self.assertRaisesRegex(ValueError,'selection'):
    ODPricingRuntime(start='2026-03-12',routing_checkpoint='unused',sensitivity_contract=CAL,information_contract=m)
   engine.assert_not_called()
