"""Explicitly gated continuation of the approved run; never invoked by the pilot."""
import argparse,hashlib,json,time
from pathlib import Path

def arguments(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--authorize-remaining-33',action='store_true',required=True)
 p.add_argument('--checkpoint',required=True)
 p.add_argument('--output',required=True)
 p.add_argument('--models',required=True)
 return p.parse_args(argv)

def main(argv=None):
 args=arguments(argv) # Reject before importing runtime or accessing data.
 import scripts.run_multi_episode_od_pilot as pilot
 from src.simulation.multi_episode_od import retain_checkpoint
 from src.simulation.multi_episode_rng import advance_with_environment_rng
 from src.simulation.od_development_evaluation import due,evaluate_due
 from src.routing.learning import LocalRoutingLearner
 out=Path(args.output);models=Path(args.models)
 pilot_root=Path('results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration')
 if out.resolve()==pilot_root.resolve() or models.resolve()==pilot.MODELS.resolve():raise ValueError('Continuation must preserve pilot outputs/checkpoints')
 m=json.loads((pilot_root/'information_contract.json').read_text())
 config=json.loads((pilot_root/'frozen_configuration.json').read_text())
 for path,h in config['source_sha256'].items():
  if pilot.sha(path)!=h:raise ValueError('Changed approved source: '+path)
 launcher_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 runtime=pilot.load(args.checkpoint,m)
 if not 32<=getattr(runtime,'episode_offset',0)+runtime.slots<=560:raise ValueError('Only validated episode2-or-later continuation is permitted')
 progress=getattr(runtime,'continuation_progress',None)
 if progress is None:
  if getattr(runtime,'episode_offset',0)+runtime.slots!=32:raise ValueError('Missing continuation progress')
  if out.exists() or models.exists():raise FileExistsError('New continuation locations required')
  progress=dict(launcher_sha256=launcher_hash,output=str(out.resolve()),models=str(models.resolve()),development_scores=[],best_score=None,completed_slots=32,wall_seconds=0.,status='RUNNING')
 else:
  if progress['launcher_sha256']!=launcher_hash or progress['output']!=str(out.resolve()) or progress['models']!=str(models.resolve()):raise ValueError('Continuation checkpoint/configuration mismatch')
 runtime.continuation_progress=progress
 out.mkdir(parents=True,exist_ok=True)
 def write(name,value):
  tmp=out/('.'+name+'.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(out/name)
 write('configuration.json',dict(approved=config,launcher_sha256=launcher_hash,start_checkpoint=str(Path(args.checkpoint).resolve()),episode_limit=35,evaluation='frozen epsilon0, no pricing/routing updates',protected_access=False))
 LocalRoutingLearner.train_for_slot=pilot.previous.observed_train
 factory=pilot.factory(m);started=time.monotonic();wall_initial=progress['wall_seconds']
 while True:
  if wall_initial+time.monotonic()-started>=96*3600:
   progress['status']='WALL_BUDGET_STOP';break
  completed=getattr(runtime,'episode_offset',0)+runtime.slots
  if runtime.slots==16:
   episode=completed//16
   # Re-entering a checkpoint does not repeat an already committed evaluation.
   if due(runtime) and episode not in [r['episode'] for r in progress['development_scores']]:
    reports=evaluate_due(runtime,factory)
    score=sum(r['revenue'] for r in reports)/len(reports)
    progress['development_scores'].append(dict(episode=episode,score=score))
    write(f'evaluation_episode{episode:02d}.json',reports)
    if progress['best_score'] is None or score>progress['best_score']:
     progress['best_score']=score
     retain_checkpoint(runtime,models,'best')
    retain_checkpoint(runtime,models,'milestone')
    scores=[r['score'] for r in progress['development_scores']]
    if episode>=21 and len(scores)>=3:
     reference=max(scores[:-3],default=scores[0])
     if max(scores[-3:])<reference+.01*max(abs(reference),1.):
      progress['status']='DEVELOPMENT_PLATEAU';break
   if episode==35:progress['status']='BUDGET_COMPLETE';break
   runtime=advance_with_environment_rng(runtime,factory);runtime.continuation_progress=progress
  if wall_initial+time.monotonic()-started>=96*3600:
   progress['status']='WALL_BUDGET_STOP';break
  metric=pilot.step(runtime)
  progress['completed_slots']=getattr(runtime,'episode_offset',0)+runtime.slots
  progress['wall_seconds']=wall_initial+time.monotonic()-started
  write(f"slot_{progress['completed_slots']:04d}.json",metric)
  if runtime.slots%4==0:retain_checkpoint(runtime,models)
  write('progress.json',progress)
 # The last committed periodic checkpoint remains authoritative on resource stops.
 progress['wall_seconds']=wall_initial+time.monotonic()-started
 write('completion.json',progress)

if __name__=='__main__':main()
