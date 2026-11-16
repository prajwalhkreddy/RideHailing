"""Detached, fail-closed Episode10→25 handoff. Never signal the active stage."""
from pathlib import Path
import sys,os,json,time,subprocess,fcntl,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.train_v3_stage3 import OUT,MODEL,RESUME,atomic,run
BASE=OUT.parent
HANDOFF=BASE/'overnight_ep25_handoff.json'
STAGE2=BASE/'stage_ep02_ep10'
KEYS=('TECHNICAL_INVARIANTS','NUMERICAL_STABILITY','PASSENGER_ACCEPTANCE_INVARIANT','REWARD_RECONCILIATION','REPLAY_HEALTH','CHECKPOINT_VALID','ROUTING_FROZEN','FLEET_INVARIANTS')
def validate_gate(status,gate,manifest,checkpoint_status):
    expected=dict(status='COMPLETED',pid=33413,episode=10,stage_slots_completed=144,stage_target_slots=144,latest_completed_episode=10,failure=None,timestamp='2026-03-04 08:00:00')
    if not set(expected).issubset(status) or any(status.get(k)!=v for k,v in expected.items()):raise ValueError('Episode10 completion fields mismatch')
    if Path(status.get('latest_safe_checkpoint','')).resolve()!=RESUME.resolve():raise ValueError('Not the final Episode10 checkpoint')
    if any(gate.get(k)!='PASS' for k in KEYS) or gate.get('MARCH17_31')!='UNTOUCHED':raise ValueError('Absent/incomplete/failed Episode10 technical gate')
    if any('CONTINUE' in k and v=='NOT_RECOMMENDED' for k,v in gate.items()):raise ValueError('Continuation NOT_RECOMMENDED')
    expected=dict(checkpoint_schema_version='V3_FULL_RUNTIME_1',checkpoint_status='COMPLETE',episode=10,slot=16,terminal=True,absolute_timestamp='2026-03-04 08:00:00',optimizer_updates=1224,replay_size=22720,exploration_epsilon=1-.95*1224/50000)
    if any(manifest.get(k)!=v for k,v in expected.items()):raise ValueError('Episode10 checkpoint metadata mismatch')
    if checkpoint_status.get('checkpoint_status')!='COMPLETE':raise ValueError('Checkpoint not COMPLETE')
def worker(fd):
    state=dict(status='WAITING_FOR_EP10',handoff_pid=os.getpid(),current_stage2_pid=33413,stage3_pid=None,stage2_status_file=str(STAGE2/'training_status.json'),stage3_status_file=str(OUT/'training_status.json'),latest_event='Waiting for natural Episode10 completion',failure=None,current_episode=None)
    atomic(HANDOFF,state)
    def publish(status,event,**extra):
        state.update(status=status,latest_event=event,**extra);atomic(HANDOFF,state)
    try:
        while True:
            s=json.loads((STAGE2/'training_status.json').read_text())
            state['current_episode']=s.get('episode')
            if s.get('pid')!=33413:raise ValueError('Stage2 PID identity changed')
            if s.get('status')=='FAILED' or s.get('failure') is not None:
                publish('BLOCKED','BLOCKED_STAGE2_FAILED',failure=s.get('failure') or 'Stage2 FAILED');return 1
            if s.get('status')=='COMPLETED':break
            if s.get('status') not in ('STARTING','RUNNING'):raise ValueError('Unexpected Stage2 status')
            # Read-only process listing; no signal, debugger, or active-file mutation.
            proc=subprocess.run(['ps','-p','33413','-o','stat='],capture_output=True,text=True)
            if proc.returncode!=0 or not proc.stdout.strip() or proc.stdout.strip().startswith('Z'):
                publish('BLOCKED','BLOCKED_STAGE2_EXITED_WITHOUT_COMPLETION',failure='Stage2 process absent/zombie before completion');return 1
            publish('WAITING_FOR_EP10','Stage2 still active; next local check in 60 seconds')
            time.sleep(60)
        publish('VALIDATING_EP10','Checking saved Episode10 technical gate and checkpoint')
        try:
            gate=json.loads((STAGE2/'health_gate.json').read_text())
            manifest=json.loads((RESUME/'manifest.json').read_text())
            checkpoint_status=json.loads((RESUME/'status.json').read_text())
            validate_gate(s,gate,manifest,checkpoint_status)
            from src.simulation.v3_stage2_checkpoint import load_v3_checkpoint
            runtime=load_v3_checkpoint(RESUME)  # checks all immutable/component hashes, restores all RNGs
            if runtime.episode!=10 or runtime.slots!=16 or runtime.engine.slot_index!=160:raise ValueError('Restored cursor mismatch')
            if str(runtime.engine.timestamp)!='2026-03-04 08:00:00':raise ValueError('Restored timestamp mismatch')
            atomic(OUT/'handoff_checkpoint_validation.json',dict(status='PASS',resume_checkpoint=str(RESUME),schema='V3_FULL_RUNTIME_1',all_hashes_validated=True,episode=10,slot=16,environment_reset=False))
        except Exception as e:
            publish('BLOCKED','BLOCKED_EPISODE10_GATE',failure=f'{type(e).__name__}: {e}');traceback.print_exc();return 1
        publish('STARTING_EP11','Episode10 gate passed; full-state continuation',stage3_pid=os.getpid())
        publish('RUNNING_EP11_EP25','Same PID executing Stage3; stops after Episode25')
        run(fd,resumed_runtime=runtime)
        publish('COMPLETED','Episode25 complete; Episode26 NOT_STARTED')
        return 0
    except BaseException as e:
        publish('FAILED','Handoff/Stage3 failed; no restart',failure=f'{type(e).__name__}: {e}');traceback.print_exc();return 1

def main():
    if '--lock-fd' in sys.argv:return worker(int(sys.argv[sys.argv.index('--lock-fd')+1]))
    if sys.argv[1:]!=['--background']:raise ValueError('Explicit --background required')
    OUT.mkdir(parents=True,exist_ok=True);MODEL.mkdir(parents=True,exist_ok=True)
    lock=(MODEL/'writer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if HANDOFF.exists() or (OUT/'training_status.json').exists() or (MODEL/'LATEST.json').exists():raise ValueError('Handoff/Stage3 namespace already used')
    with (OUT/'stage_ep11_ep25.log').open('x') as log:
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno())],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(lock.fileno(),))
    lock.close();print(json.dumps(dict(handoff_pid=child.pid,handoff_status_file=str(HANDOFF),stage3_log=str(OUT/'stage_ep11_ep25.log'))))
    return 0
if __name__=='__main__':sys.exit(main())
