"""Approved persisted baseline and startup only; never advance an episode."""
import unittest,json
from pathlib import Path
import pandas as pd
from src.simulation.final_production import ProductionExperiment,validate_driver_profiles
from src.routing.operational_interface import u3
ROOT=Path(__file__).resolve().parents[1]

class HimaxBaselineTests(unittest.TestCase):
    def test_persisted_baseline(self):
        f=pd.read_parquet(ROOT/'data/processed/driver_preferences_seed42.parquet')
        self.assertEqual(len(f),5000)
        self.assertTrue((f.H_i_max_minutes==10.).all())
        self.assertTrue((f.charging_wait_preference_minutes==f.H_i_max_minutes).all())
        validate_driver_profiles(f,f.vehicle_id)
        meta=json.loads((ROOT/'data/processed/driver_preferences_seed42_metadata.json').read_text())
        self.assertEqual(meta['H_i_max_calibration']['status'],'PROJECT_CALIBRATION')
    def test_baseline_u3(self):
        self.assertAlmostEqual(u3(10.,10.,wait_floor_minutes=1e-6),.6321205588285577,places=12)
    def test_production_startup_only(self):
        x=ProductionExperiment()
        self.assertEqual(len(x.grid),142)
        self.assertEqual(x.policy.input_shape[-1],169);self.assertEqual(x.policy.output_shape[-1],9)
        self.assertEqual(x.dqn.online.input_shape[-1],13);self.assertEqual(x.dqn.online.output_shape[-1],7)
        self.assertTrue(x.charging.timed_navigation);self.assertIsNotNone(x.operational)
        self.assertTrue((x.profiles.charging_wait_preference_minutes==10.).all())
        self.assertEqual(len(x.profiles),5000);self.assertEqual(len(x.reports),0);self.assertEqual(x.slot_index,0)
        for g in range(142):self.assertEqual(x.current_states.build(g,0,x.timestamp).shape,(13,))
        meta=json.loads((ROOT/'data/processed/grid_metadata.json').read_text())
        self.assertEqual([meta['raster_rows'],meta['raster_columns']],[16,16])
        self.assertEqual(x.dqn.training_steps,0)

if __name__=='__main__':unittest.main()
