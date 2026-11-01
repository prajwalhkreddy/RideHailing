"""Launch isolated corrected-behavior March1–15 routing generation only."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
if __name__=='__main__':
 import argparse,subprocess,os
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--background',action='store_true');p.add_argument('--validation-only',action='store_true')
 p.add_argument('--resume',action='store_true');p.add_argument('--stop-after-slot',type=int,default=720)
 a=p.parse_args()
 suffix='_validation' if a.validation_only else ''
 data=ROOT/f'data/processed/routing_experiences_mar01_mar15_2026_final_behavioral{suffix}'
 data.mkdir(parents=True,exist_ok=True)
 if a.background:
  import fcntl
  with (data/'generation.lock').open('a') as lock:
   try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise SystemExit('Another generation process holds the lock; no launch or PID modification.')
   fcntl.flock(lock,fcntl.LOCK_UN)
  cmd=[sys.executable,'-B',str(Path(__file__).resolve()),'--stop-after-slot',str(a.stop_after_slot)]
  if a.resume:cmd.append('--resume')
  if a.validation_only:cmd.append('--validation-only')
  with (data/'generation.log').open('a') as log:
   proc=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
  # The locked worker owns PID persistence; this launcher never writes it.
  print(f'Spawned worker PID {proc.pid}; log {data/"generation.log"}',flush=True)
 else:
  from src.simulation.routing_experience_generation import generate
  generate(ROOT,stop_after_slot=a.stop_after_slot,checkpoint_every_slots=8,resume=a.resume,validation_only=a.validation_only,final_behavioral=True)
