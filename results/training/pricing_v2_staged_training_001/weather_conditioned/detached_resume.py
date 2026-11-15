"""Single-writer detached continuation; immutable original configuration retained."""
import os,sys,json,fcntl,hashlib,shutil,traceback,argparse
from pathlib import Path
from datetime import datetime,timezone
O=Path(__file__).resolve().parent

def write(path,data):
 temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)
def lock_run():
 f=(O/'training.writer.lock').open('a+')
 fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 return f

def validate():
 import numpy as np
 from dataclasses import asdict
 import resume_harness as h
 cfg,fixture,m=h.verify()
 candidates=sorted((O/'checkpoints').glob('episode_*'),reverse=True)
 rejected=[]
 for cp in candidates:
  try:
   for name in ['checkpoint.json','continuation.json','online.keras','target.keras','replay.npz']:
    if not (cp/name).is_file():raise ValueError('Missing '+name)
   meta=json.loads((cp/'continuation.json').read_text())
   h.validate_continuation(meta,h.sha256(O/'training_harness_config.json'),h.sha256(O/'march16_v2_full_day_fixture_manifest.json'),cfg['sensitivity_identity']['empirical_support_sha256'])
   p=h.provider();d=h.PassengerSensitiveDQN.load(cp,sensitivity_provider=p)
   assert asdict(d.config)==cfg['dqn_config'] and d.training_steps==meta['update']
   for model in [d.online,d.target]:
    assert all(np.isfinite(v.numpy()).all() for v in model.weights)
   assert all(np.isfinite(v.numpy()).all() for v in d.online.optimizer.variables)
   assert len(d.replay)>0 and d.replay.items[-1][4]
   saved=json.loads((cp/'checkpoint.json').read_text())
   assert d.rng.bit_generator.state==saved['rng_state'] and d.replay.rng.bit_generator.state==saved['replay_rng_state']
   assert p.state_dict()==saved['sensitivity_state']
   assert m['fixture_sha256']=='c23f815ab8dd573b958e83260b442ab428255325bffc8ac83fdbfcf77e1177a6'
   assert cfg['slots_per_episode']==16 and cfg['stop_after']==25 and cfg['updates_per_warm_slot']==8
   result=dict(status='VALIDATED',checkpoint=str(cp),completed_episode=meta['episode'],resume_slot=0,next_episode=meta['next_episode'],optimizer_updates=d.training_steps,replay_size=len(d.replay),exploration_epsilon=d.epsilon,checkpoint_hashes={f.name:h.sha256(f) for f in cp.iterdir() if f.is_file()},config_sha256=h.sha256(O/'training_harness_config.json'),environment_rng_contract=meta['continuation'],next_environment_seed=cfg['episodes'][meta['episode']]['environment_seed'],rejected_candidates=rejected)
   write(O/'resume_validation.json',result);return result
  except Exception as exc:rejected.append(dict(path=str(cp),reason=str(exc)))
 raise ValueError('No complete compatible checkpoint: '+str(rejected))

def run():
 lock=lock_run()
 r=json.loads((O/'resume_validation.json').read_text())
 for name,digest in r['checkpoint_hashes'].items():
  assert hashlib.sha256((Path(r['checkpoint'])/name).read_bytes()).hexdigest()==digest
 assert hashlib.sha256((O/'training_harness_config.json').read_bytes()).hexdigest()==r['config_sha256']
 lock.seek(0);lock.truncate();lock.write(str(os.getpid()));lock.flush()
 (O/'training.pid').write_text(str(os.getpid())+'\n')
 status=dict(status='RUNNING',pid=os.getpid(),training_started=True,resumed=True,resume_checkpoint=r['checkpoint'],completed_episode=r['completed_episode'],current_episode=r['next_episode'],current_slot=0,target_episode=25,slots_per_episode=16,minutes_per_slot=30,simulated_hours_per_episode=8,optimizer_updates=r['optimizer_updates'],replay_size=r['replay_size'],exploration_epsilon=r['exploration_epsilon'],latest_checkpoint=r['checkpoint'],last_update=datetime.now(timezone.utc).isoformat(),failure=None)
 write(O/'training_status.json',status)
 print('TRAINING_RESUMED '+json.dumps(status),flush=True)
 try:
  # Preserve all interrupted-attempt reports before retaining committed state only.
  archive=O/'interrupted_attempt_before_resume'
  archive.mkdir(exist_ok=False)
  for name in ['episode_metrics.csv','checkpoint_metrics.csv','development_evaluations.csv','value_calibration.csv']:
   f=O/name
   if f.exists():shutil.copy2(f,archive/name)
  import resume_harness as h
  for name in ['episode_metrics.csv','checkpoint_metrics.csv','development_evaluations.csv','value_calibration.csv']:
   f=O/name
   if f.exists():h.pd.DataFrame(h.committed_rows(name,r['completed_episode'])).to_csv(f,index=False)
  h.run_resume(r['checkpoint'])
  print('TRAINING_COMPLETED',flush=True)
 except BaseException as exc:
  traceback.print_exc();status=json.loads((O/'training_status.json').read_text());status.update(status='FAILED_RESUME_EXECUTION',failure=str(exc),last_update=datetime.now(timezone.utc).isoformat());write(O/'training_status.json',status);raise
 finally:lock.close()
if __name__=='__main__':
 if '--validate' in sys.argv:print(json.dumps(validate()))
 elif '--run' in sys.argv:run()
 else:raise SystemExit('Use --validate or --run')
