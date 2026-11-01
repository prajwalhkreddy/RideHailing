import time,json,pickle,hashlib,fcntl
from pathlib import Path
import numpy as np,pandas as pd
import src.simulation.multiepisode_pricing as m
O=m.ROOT/'results/analysis/2026-10-31_pricing_execution_performance';O.mkdir(exist_ok=True)
def write(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
for _ in range(90):
 st=json.loads((m.RUN_OUT/'status.json').read_text())
 if st['status']=='STOPPED_SAFE':break
 time.sleep(1)
else:raise RuntimeError('Safe stop not confirmed')
with (m.FINAL/'writer.lock').open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cp=Path(st['checkpoint']);meta=json.loads((cp/'manifest.json').read_text())
for f,h in meta['files'].items():assert m.sha(cp/f)==h
write('safe_stop.json',st)
# Identical small update fixture from stopped checkpoint.
a=m.PricingDQN.load(cp/'dqn');b=m.PricingDQN.load(cp/'dqn');b.enable_compiled_updates()
for _ in range(8):a.train_step();b.compiled_train_step()
err=max(float(np.max(np.abs(x-y))) for x,y in zip(a.online.get_weights(),b.online.get_weights()))
passed=all(np.allclose(x,y,rtol=1e-5,atol=1e-5) for x,y in zip(a.online.get_weights(),b.online.get_weights()))
write('small_equivalence.json',dict(passed=passed,max_absolute_parameter_difference=err,tolerance='rtol=1e-5, atol=1e-5',same_replay_rng=a.replay.rng.bit_generator.state==b.replay.rng.bit_generator.state))
if not passed:raise RuntimeError('Compiled candidate rejected: small equivalence failed')
results={};states={}
for mode in ['old','optimized']:
 start=time.perf_counter();learner=m.PricingDQN.load(cp/'dqn');spec=json.loads((m.OUT/'episode_protocol.json').read_text())['starts'][st['episode']]
 x=m.reset(spec,learner);timing={'initialization':time.perf_counter()-start}
 if mode=='optimized':learner.enable_compiled_updates();learner.train_step=learner.compiled_train_step
 def timed(obj,name,key):
  original=getattr(obj,name)
  def call(*args,**kwargs):
   t=time.perf_counter()
   try:return original(*args,**kwargs)
   finally:timing[key]=timing.get(key,0)+time.perf_counter()-t
  setattr(obj,name,call)
 timed(x.policy,'call','routing_inference');timed(learner,'select_action','pricing_action_inference');timed(learner,'store','replay_insertion');timed(learner,'train_step','optimizer_updates')
 for j in range(16):
  t=time.perf_counter();m.slot(x,terminal=j==15);timing['slots_total']=timing.get('slots_total',0)+time.perf_counter()-t
  if (j+1)%8==0:
   t=time.perf_counter();m.checkpoint(x,O/'benchmark_checkpoints'/mode,m.RID);timing['checkpoint_serialization']=timing.get('checkpoint_serialization',0)+time.perf_counter()-t
  print(mode,j+1,flush=True)
 t=time.perf_counter();pd.DataFrame(x.reports).to_csv(O/(mode+'_slots.csv'),index=False);timing['reporting_csv']=time.perf_counter()-t
 timing['seconds_episode']=time.perf_counter()-start
 timing['simulator_request_dispatch_other']=timing['slots_total']-sum(timing.get(k,0) for k in ['routing_inference','pricing_action_inference','replay_insertion','optimizer_updates'])
 results[mode]=timing;write('profile.json',results)
 states[mode]=dict(online=learner.online.get_weights(),target=learner.target.get_weights(),reports=x.reports,replay=list(learner.replay.items),rng=learner.rng.bit_generator.state,replay_rng=learner.replay.rng.bit_generator.state,steps=learner.training_steps,epsilon=learner.epsilon,fleet=[(v.vehicle_id,v.current_grid,v.trip_status,v.energy_level) for v in x.fleet.vehicles])
a,b=states['old'],states['optimized'];keys=['requests','accepted','rejected','assigned','unmatched','reward','transitions','pricing_action_counts','routing_actions','fleet_size']
checks=dict(same_reports=all(all(x[k]==y[k] for k in keys) for x,y in zip(a['reports'],b['reports'])),same_fleet=a['fleet']==b['fleet'],same_action_rng=a['rng']==b['rng'],same_replay_rng=a['replay_rng']==b['replay_rng'],same_updates=a['steps']==b['steps'],same_epsilon=a['epsilon']==b['epsilon'],online_close=all(np.allclose(x,y,rtol=1e-5,atol=1e-5) for x,y in zip(a['online'],b['online'])),target_close=all(np.allclose(x,y,rtol=1e-5,atol=1e-5) for x,y in zip(a['target'],b['target'])))
checks['pass']=all(checks.values());write('equivalence_validation.json',checks)
old,new=results['old']['seconds_episode'],results['optimized']['seconds_episode'];write('benchmark.json',dict(old_seconds=old,optimized_seconds=new,speedup=old/new,estimated_100_hours=new*100/3600,estimated_500_hours=new*500/3600,ready=checks['pass'] and new<old))
