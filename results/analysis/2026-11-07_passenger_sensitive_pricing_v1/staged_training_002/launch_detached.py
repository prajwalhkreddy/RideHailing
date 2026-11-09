"""Fresh corrected Stage1 bootstrap; no archive, checkpoint load, or stage chaining."""
from pathlib import Path
import os,sys,json,runpy,traceback
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
M=Path('models/pricing_dqn/passenger_sensitive_v1_seed42/staged_training_002')
def write(name,x):
 p=R/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
now=datetime.now(timezone.utc).isoformat()
try:
 if (M/'initialization.json').exists():raise RuntimeError('Refusing to resume existing corrected initialization')
 (R/'stage1.pid').write_text(str(os.getpid())+'\n')
 write('detached_startup.json',dict(pid=os.getpid(),status='INITIALIZING',started_at=now,INITIALIZATION_SOURCE='FRESH',STAGED_TRAINING_001_CHECKPOINT_LOADED='NO',OLD_PRE_REFORMULATION_EP25_LOADED='NO',discount_semantics='PER_REQUEST_TRANSITION',gamma=.99,stage=1,stage_end=1))
 write('training_status.json',dict(pid=os.getpid(),status='INITIALIZING',stage='STAGE1',episode=1,slot=0,started_at=now,protected_period_untouched=True))
 sys.argv=[str(R/'run_staged.py'),'--stage','1']
 runpy.run_path(sys.argv[0],run_name='__main__')
except BaseException as exc:
 write('bootstrap_failure.json',dict(error=repr(exc),traceback=traceback.format_exc()))
 raise
