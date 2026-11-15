"""Launch-gate regressions; synthetic fixtures, no training episode."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from src.pricing.passenger_sensitive_v1 import guard_date
from src.simulation.temporal_protocol import assert_training_update_allowed
from src.rl.passenger_sensitive_dqn import PassengerSensitiveDQN

class PreflightContracts(unittest.TestCase):
 def test_date_boundaries(self):
  guard_date('2026-03-15 23:30',calibration=True)
  assert_training_update_allowed('2026-03-15 23:30')
  guard_date('2026-03-16 23:30')
  for t in ['2026-03-16','2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):guard_date(t,calibration=True)
  for t in ['2026-03-17','2026-03-31']:
   with self.assertRaises(ValueError):guard_date(t)
 def test_v1_roundtrip_and_missing_schema(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);d=PassengerSensitiveDQN();d.save(p)
   e=PassengerSensitiveDQN.load(p)
   for a,b in zip(d.online.get_weights(),e.online.get_weights()):np.testing.assert_array_equal(a,b)
   m=json.loads((p/'checkpoint.json').read_text());m.pop('schema');(p/'checkpoint.json').write_text(json.dumps(m))
   with self.assertRaisesRegex(ValueError,'schema'):PassengerSensitiveDQN.load(p)
 def test_profile_migration_provenance_and_mutation(self):
  from tests.test_production_simulation import ProductionSimulationTests
  # Exercise the actual migrated artifact assertion, then a simulated corrupted digest.
  test=ProductionSimulationTests('test_frozen_artifacts_and_first_eight_predictions_exist')
  test.test_frozen_artifacts_and_first_eight_predictions_exist()
  from src.routing.production import sha256_file
  def changed(path):
   return '0'*64 if Path(path).name=='driver_preferences_seed42.parquet' else sha256_file(path)
  with patch('tests.test_production_simulation.sha256_file',side_effect=changed):
   with self.assertRaises(AssertionError):test.test_frozen_artifacts_and_first_eight_predictions_exist()
