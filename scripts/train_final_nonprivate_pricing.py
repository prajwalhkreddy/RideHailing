"""Launch/resume the fixed March 1–15 final non-private pricing run."""
from pathlib import Path
import sys,os,argparse,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--resume',action='store_true');p.add_argument('--stop-after-slot',type=int,default=720);p.add_argument('--checkpoint-every-slots',type=int,default=8)
    p.add_argument('--background',action='store_true');p.add_argument('--lock-fd',type=int,help=argparse.SUPPRESS)
    p.add_argument('--validation-only',action='store_true')
    p.add_argument('--log',type=Path,default=ROOT/'results/analysis/2026-10-25_final_nonprivate_pricing_training/training.log')
    args=p.parse_args()
    # Acquire writer ownership before spawning or touching the active PID/log.
    from src.simulation.final_pricing_training import MODEL,OUT,run,lock_writer
    namespace=MODEL if not args.validation_only else MODEL.with_name(MODEL.name+'_prelaunch')
    output=OUT if not args.validation_only else OUT/'prelaunch'
    if args.validation_only and args.stop_after_slot>4:p.error('Validation is limited to four slots.')
    if not 1<=args.stop_after_slot<=720 or not 1<=args.checkpoint_every_slots<=8:p.error('Invalid target/cadence.')
    if args.background:
        lock=lock_writer(namespace)
        if args.resume!=(namespace/'CURRENT.json').exists():lock.close();raise ValueError('Fresh/resume namespace mismatch.')
        args.log.parent.mkdir(parents=True,exist_ok=True)
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno()),'--stop-after-slot',str(args.stop_after_slot),'--checkpoint-every-slots',str(args.checkpoint_every_slots)]
        if args.resume:command.append('--resume')
        if args.validation_only:command.append('--validation-only')
        with args.log.open('a') as log:
            child=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(lock.fileno(),))
        # The child alone owns PID publication after inheriting the lock.
        lock.close();print(f'Launched PID {child.pid}; log {args.log}',flush=True)
    else:run(namespace=namespace,output=output,resume=args.resume,stop_after_slot=args.stop_after_slot,cadence=args.checkpoint_every_slots,lock_fd=args.lock_fd)
if __name__=='__main__':main()
