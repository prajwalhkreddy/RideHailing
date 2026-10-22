"""Split, availability and pre-update guard checks; no model execution."""
import unittest,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from src.simulation.temporal_protocol import (ROOT,protocol,training_update_allowed,is_final_evaluation,assert_training_update_allowed,assert_final_training_checkpoint)

class TemporalProtocolTests(unittest.TestCase):
    def test_counts_and_boundaries(self):
        p=protocol();allslots=[];previous=None
        for key,n in [('cnn_train',2832),('rl_train',720),('integration_exclusion',48),('final_eval',720)]:
            slots=pd.date_range(p[key+'_start'],p[key+'_end'],freq='30min');self.assertEqual(len(slots),n)
            if previous is not None:self.assertEqual(slots[0]-previous,pd.Timedelta(minutes=30))
            previous=slots[-1];allslots.extend(slots)
        self.assertEqual(len(set(allslots)),4320)
    def test_training_boundaries(self):
        self.assertTrue(training_update_allowed('2026-03-15 23:30'))
        for t in ['2026-03-16','2026-03-17','2026-03-31 23:30']:
            self.assertFalse(training_update_allowed(t))
            with self.assertRaises(ValueError):assert_training_update_allowed(t)
    def test_eval_mode_and_alignment(self):
        self.assertTrue(is_final_evaluation('2026-03-17'))
        self.assertTrue(is_final_evaluation('2026-03-31 23:30'))
        self.assertFalse(is_final_evaluation('2026-03-16 23:30'))
        with self.assertRaises(ValueError):assert_training_update_allowed('2026-03-01',evaluation_only=True)
        for t in ['2026-03-15 23:31','2026-03-15T23:30:00Z',pd.NaT]:
            with self.assertRaises(ValueError):training_update_allowed(t)
    def test_runner_guard_before_side_effects(self):
        from src.simulation.final_production import ProductionExperiment
        x=ProductionExperiment.__new__(ProductionExperiment)
        for t in ['2026-03-16','2026-03-17','2026-03-31 23:30']:
            x.timestamp=pd.Timestamp(t)
            with self.assertRaisesRegex(ValueError,'temporal protocol'):x.run_slot(train_dqn=True)
            with self.assertRaisesRegex(ValueError,'temporal protocol'):x.run_slot(routing_updates=[{}])
    def test_forecasts_and_runtime_selection(self):
        p=protocol();f=pd.read_parquet(ROOT/p['rl_forecast_path']);ts=pd.date_range(p['rl_train_start'],p['rl_train_end'],freq='30min')
        self.assertEqual(len(f),102240);self.assertFalse(f[['forecast_timestamp','Grid_ID']].duplicated().any())
        self.assertTrue(pd.DatetimeIndex(sorted(f.forecast_timestamp.unique())).equals(ts))
        self.assertEqual(set(f.Grid_ID),set(range(142)))
        self.assertTrue((f.groupby('forecast_timestamp').size()==142).all())
        self.assertTrue(np.isfinite(f.predicted_demand).all());self.assertTrue(f.predicted_demand.ge(0).all())
        from src.pricing.dqn_contract import artifact_snapshots
        for t in [ts[0],ts[-1]]:
            forecast,pop=artifact_snapshots(t);self.assertEqual(len(forecast.values),142);self.assertEqual(len(pop.values),142)
    def test_checkpoint_quarantine_and_integrity(self):
        p=protocol();cp=ROOT/p['quarantined_checkpoint']
        with self.assertRaisesRegex(ValueError,'DO_NOT_CONTINUE'):assert_final_training_checkpoint(cp)
        status=json.loads((ROOT/'results/analysis/2026-10-21_final_temporal_protocol/integration_checkpoint_status.json').read_text())
        self.assertIn('NOT_FINAL_TRAINING_CHECKPOINT',status['classification'])
        for f,sha in status['checkpoint_sha256'].items():self.assertEqual(hashlib.sha256((cp/f).read_bytes()).hexdigest(),sha)
    def test_forecast_provenance_and_availability(self):
        out=ROOT/'results/analysis/2026-10-21_final_temporal_protocol'
        v=json.loads((out/'forecast_validation.json').read_text())
        self.assertEqual(v['epoch'],200)
        self.assertEqual(hashlib.sha256((ROOT/v['checkpoint']).read_bytes()).hexdigest(),v['checkpoint_sha256'])
        self.assertEqual(hashlib.sha256((ROOT/v['forecast_path']).read_bytes()).hexdigest(),v['forecast_sha256'])
        a=json.loads((out/'training_input_availability.json').read_text());self.assertEqual(len(a['items']),10)
        self.assertTrue(all(i['status']=='AVAILABLE' for i in a['items'].values()))

if __name__=='__main__':unittest.main()
