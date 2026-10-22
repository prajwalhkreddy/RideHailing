"""Focused final CNN and directly affected quick regressions; no training."""
from pathlib import Path
import sys,os,json,unittest
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
suite=unittest.defaultTestLoader.loadTestsFromNames(['test_final_cnn','test_config','test_demand_aggregation'])
r=unittest.TextTestRunner(verbosity=2).run(suite)
out={'run':r.testsRun,'passed':r.testsRun-len(r.failures)-len(r.errors),'failed':len(r.failures)+len(r.errors),'errors':[(t.id(),s) for t,s in r.errors],'failures':[(t.id(),s) for t,s in r.failures],'training_performed':False,'test_metrics_recomputed_from_saved_predictions_only':True}
Path('results/analysis/2026-10-19_final_jan_mar_3km_cnn/test_results.json').write_text(json.dumps(out,indent=2)+'\n')
sys.exit(not r.wasSuccessful())
