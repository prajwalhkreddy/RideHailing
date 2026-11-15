"""Wait for baseline completion evidence, finalize, then exit. Never trains."""
from pathlib import Path
import json,time,subprocess,sys,os
O=Path(__file__).resolve().parent
A=Path('results/analysis/2026-11-14_pricing_v2_time_specific_weather')
def write(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def fail(reason):
 result=dict(verdict='V2_TRAINING_BLOCKED_WEATHER_CONDITIONING_BASELINE_VALIDATION_FAILED',reason=reason,training_started=False,March17_31_untouched=True)
 for path in [O/'prelaunch_verification.json',A/'prelaunch_verification.json',O/'completion_status.json']:write(path,result)
 note='## Current conditional baseline status\n\n**'+result['verdict']+'**. Training has not started. Completion checks stopped; see `results/training/pricing_v2_staged_training_001/weather_conditioned/prelaunch_verification.json` for the exact failure. No readiness is asserted.\n\n'
 for path in [O/'README.md',A/'README.md',Path('README.md'),Path('results/analysis/2026-11-01_current_state_review/README.md')]:
  h,b=path.read_text().split('\n',1);path.write_text(h+'\n\n'+note+b.lstrip('\n'))
write(O/'completion_status.json',dict(status='WAITING_FOR_COMPLETE_BASELINE_COMMAND',pid=os.getpid(),baseline_session_id=78450,training_started=False))
while True:
 if (O/'baseline_failure.json').exists():
  fail(json.loads((O/'baseline_failure.json').read_text()).get('reason','Baseline command failed'));break
 if (O/'baseline_manifest.json').exists():
  with (O/'finalization.log').open('w') as log:result=subprocess.run([sys.executable,'-B',str(O/'finalize.py')],stdout=log,stderr=subprocess.STDOUT)
  if result.returncode:
   fail('Finalization failed; inspect finalization.log and harness_verification.txt')
  else:write(O/'completion_status.json',dict(status='COMPLETE',verdict='READY_TO_LAUNCH_V2_STAGE25',training_started=False))
  break
 time.sleep(30)
