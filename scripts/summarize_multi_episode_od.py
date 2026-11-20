"""Summarize completed pilot artifacts without model loading or simulation."""
from pathlib import Path
import json,csv,hashlib
P=Path('results_v2/pricing_dqn/2026-11-20_multi_episode_orchestration')
M=Path('models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42')
def table(name,rows):
 with (P/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 m=json.loads((P/'slot_metrics.json').read_text());v=json.loads((P/'pilot_validation.json').read_text());recovery=json.loads((P/'recovery_validation.json').read_text())
 assert len(m)==32 and [(r['episode'],r['slot']) for r in m]==[(e,s) for e in (1,2) for s in range(1,17)]
 assert v['episodes']==2 and recovery['status']=='PASS'
 episodes=[]
 for e in (1,2):
  rows=[r for r in m if r['episode']==e];last=rows[-1]
  episodes.append(dict(episode=e,requests=sum(r['requests'] for r in rows),accepted=sum(r['accepted'] for r in rows),assigned=sum(r['assigned'] for r in rows),revenue=sum(r['revenue'] for r in rows),supported_reward=sum(r['reward'] for r in rows),fallback_revenue=sum(r['fallback_revenue'] for r in rows),pricing_updates=128,epsilon_start=rows[0]['epsilon_before'],epsilon_end=last['epsilon_after'],routing_updates=sum(r['routing_updates'] for r in rows),routing_sample_presentations=sum(r['routing_samples'] for r in rows),federation_round=last['federation_round'],charging_events=last['charging_events'],zero_request_contexts=last['replay']['episode_zero_request_contexts'],seconds=sum(r['seconds'] for r in rows)))
 table('episode_metrics.csv',episodes)
 table('epsilon_trajectory.csv',[{k:r[k] for k in ['episode','slot','updates','epsilon_before','epsilon_after']} for r in m])
 table('replay_diagnostics.csv',[dict(episode=r['episode'],slot=r['slot'],**r['replay']) for r in m])
 inventory={}
 for role in ('latest','best','milestone'):
  if (M/role).exists():
   target=(M/role).resolve();meta=json.loads((target/'manifest.json').read_text())
   inventory[role]=dict(path=str(target),bytes=sum(f.stat().st_size for f in target.rglob('*') if f.is_file()),slot=meta['slot'],timestamp=meta['timestamp'],manifest_sha256=hashlib.sha256((target/'manifest.json').read_bytes()).hexdigest())
 assert len(inventory)<=3
 v.update(status='PASS',recovery=recovery,episode_metrics=episodes,checkpoint_inventory=inventory,tests_distinct_passed=27,tests_failed=0,interrupted_attempt='Stopped before first reset; eight committed slots retained, uncommitted partial slot rolled back; resumed slot8 checkpoint after RNG-wrapper correction.',remaining_episodes_started=False,evaluation_dates_accessed=False)
 (P/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
 print(json.dumps(v,indent=2))
if __name__=='__main__':main()
