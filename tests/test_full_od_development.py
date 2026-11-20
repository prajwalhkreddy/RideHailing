import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import scripts.run_full_od_development as run
class FullDevelopmentTests(unittest.TestCase):
 def test_atomic_rotation_and_failed_write_preserves_recovery(self):
  with tempfile.TemporaryDirectory() as tmp:
   def save(r,p):p.mkdir();(p/'manifest.json').write_text('complete')
   with patch.object(run,'MODELS',Path(tmp)),patch.object(run,'save_od_checkpoint',save):
    run.rotate_checkpoint(SimpleNamespace(slots=4));run.rotate_checkpoint(SimpleNamespace(slots=8))
    self.assertEqual((Path(tmp)/'rolling').resolve().name,'recovery_slot08')
    self.assertFalse((Path(tmp)/'recovery_slot04').exists())
    with patch.object(run,'save_od_checkpoint',side_effect=RuntimeError('failed write')):
     with self.assertRaises(RuntimeError):run.rotate_checkpoint(SimpleNamespace(slots=12))
    self.assertTrue((Path(tmp)/'rolling/manifest.json').exists())
