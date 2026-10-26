"""Resume deterministic real March 1–15 collection; no model training."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop-after-slot',type=int,default=720)
    parser.add_argument('--validation-only',action='store_true')
    parser.add_argument('--resume',action='store_true',help='Require an existing checkpoint')
    parser.add_argument('--checkpoint-every-slots',type=int,default=8)
    parser.add_argument('--background',action='store_true',help='Detach into a new local process session')
    parser.add_argument('--log',type=Path,default=ROOT/'results/analysis/2026-10-24_routing_generation_execution_optimization/routing_generation.log')
    args=parser.parse_args()
    if args.background:
        import subprocess,os
        args.log.parent.mkdir(parents=True,exist_ok=True)
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--stop-after-slot',str(args.stop_after_slot),'--checkpoint-every-slots',str(args.checkpoint_every_slots)]
        if args.resume:command.append('--resume')
        if args.validation_only:command.append('--validation-only')
        with args.log.open('a') as log:
            process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        args.log.with_suffix('.pid').write_text(str(process.pid)+'\n')
        print(f'Detached PID {process.pid}; log {args.log}',flush=True)
        raise SystemExit(0)
    from src.simulation.routing_experience_generation import generate
    generate(ROOT,stop_after_slot=args.stop_after_slot,checkpoint_every_slots=args.checkpoint_every_slots,resume=args.resume,validation_only=args.validation_only)
