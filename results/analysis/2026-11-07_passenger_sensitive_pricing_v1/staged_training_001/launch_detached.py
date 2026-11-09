"""Detached handoff only: wait for superseded writer lock, preserve it, exec Stage1."""
from pathlib import Path
import os,json,fcntl,shutil,sys
from datetime import datetime,timezone
R=Path(__file__).parent;M=Path('models/pricing_dqn/passenger_sensitive_v1_seed42/staged_training_001')
def write(p,x):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
now=datetime.now(timezone.utc).isoformat()
(R/'stage1.pid').write_text(str(os.getpid())+'\n')
write(R/'detached_startup.json',dict(pid=os.getpid(),stage=1,status='INITIALIZING',phase='WAITING_FOR_SUPERSEDED_WORKER_SAFE_STOP',started_at=now,prior_pid=60838,checkpoint=str(M/'episode_001'),completion_marker=str(R/'stage_ep01_complete.json'),old_historical_checkpoint_loaded=False))
# Worker-side coordination, never a Codex polling loop.
lock=(M/'writer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
A=R/'superseded_attached_attempt';B=M/'superseded_attached_attempt';A.mkdir(exist_ok=True);B.mkdir(exist_ok=True)
for p in list(R.iterdir()):
 if p.is_file() and p.suffix in ['.csv','.json','.npz','.png','.log'] and p.name not in ['detached_startup.json','detached_launch.json','detached_bootstrap.log']:
  if (A/p.name).exists():raise RuntimeError('Prior attempt archive collision; refusing overwrite')
  shutil.move(str(p),str(A/p.name))
for p in list(M.iterdir()):
 if p.name not in ['writer.lock','superseded_attached_attempt']:
  if (B/p.name).exists():raise RuntimeError('Model archive collision; refusing overwrite')
  shutil.move(str(p),str(B/p.name))
write(R/'training_status.json',dict(status='INITIALIZING',stage='STAGE1',pid=os.getpid(),started_at=now,last_updated=now,episode=1,slot=0,completion_marker=str(R/'stage_ep01_complete.json'),protected_period_untouched=True,prior_partial_attempt='Preserved separately; not resumed; fresh Stage1 required by new protocol'))
fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
fd=os.open(R/'training.log',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o644);os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
os.execv(sys.executable,[sys.executable,'-B',str(R/'run_staged.py'),'--stage','1'])
