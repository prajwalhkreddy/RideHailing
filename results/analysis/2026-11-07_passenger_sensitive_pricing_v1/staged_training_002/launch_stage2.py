"""Detached exact-continuation Stage2 only; no auto-chain."""
from pathlib import Path
import os,sys,json,runpy,traceback
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
def write(name,x):
 p=R/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
try:
 assert not (R/'stage_ep10_complete.json').exists(),'Stage2 already completed'
 assert json.loads((R/'continuation_state_verification.json').read_text())['result']=='PASS'
 assert json.loads((R/'stage_ep01_review.json').read_text())['review_classification']=='PASS'
 (R/'stage2.pid').write_text(str(os.getpid())+'\n')
 write('stage2_bootstrap.json',dict(pid=os.getpid(),stage='STAGE2',status='INITIALIZING',started_at=datetime.now(timezone.utc).isoformat()))
 sys.argv=[str(R/'run_staged.py'),'--stage','2'];runpy.run_path(sys.argv[0],run_name='__main__')
except BaseException as exc:
 write('stage2_bootstrap_failure.json',dict(error=repr(exc),traceback=traceback.format_exc()))
 write('stage_ep10_complete.json',dict(stage=2,status='FAILED',technical_gate_result='FAIL',error=repr(exc)))
 raise
