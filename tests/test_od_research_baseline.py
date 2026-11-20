import tempfile,hashlib,unittest
from pathlib import Path
import pandas as pd
from tests.test_utc_od_runtime import inputs
from src.simulation.master_od_contract import utc
from src.simulation.utc_od_inputs import forecast,BASELINE

class BaselineTests(unittest.TestCase):
 def test_identity_and_values(self):
  b=inputs('2026-03-12');t=utc('2026-03-12')
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'baseline.csv';pd.DataFrame(dict(period=0,Grid_ID=range(142),predicted_demand=.25)).to_csv(p,index=False)
   b['forecast_protocol']=BASELINE;b['checkpoint_metadata']['version']=BASELINE
   b['baseline_provenance']=dict(method='January grid/local-half-hour arithmetic mean',training_start='2026-01-01',training_end_exclusive='2026-02-01',available_at=str(utc('2026-02-01')),artifact_path=str(p),artifact_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   forecast(b,t)
   b['forecasts'][str(t)].loc[0,'predicted_demand']=2
   with self.assertRaisesRegex(ValueError,'disagree'):forecast(b,t)
   b['forecasts'][str(t)].loc[0,'predicted_demand']=.25
   b['baseline_provenance']['available_at']=str(t)
   with self.assertRaisesRegex(ValueError,'Future'):forecast(b,t)
   b['baseline_provenance']['available_at']=str(utc('2026-02-01'));p.write_text('changed')
   with self.assertRaisesRegex(ValueError,'Changed'):forecast(b,t)
