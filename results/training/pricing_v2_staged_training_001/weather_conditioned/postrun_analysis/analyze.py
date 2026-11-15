"""Persisted-artifact analysis only; never runs a simulator or training step."""
import sys,json,hashlib,zipfile
from pathlib import Path
import numpy as np,pandas as pd
O=Path(__file__).resolve().parent;P=O.parent;sys.path.insert(0,str(P))
import training_harness as h
cfg,fixture,m=h.verify();p=h.provider()
status=json.loads((P/'training_status.json').read_text());assert status['status']=='COMPLETED' and status['completed_episode']==25 and status['optimizer_updates']==3200
tr=pd.read_csv(P/'episode_metrics.csv');ev=pd.read_csv(P/'development_evaluations.csv');v=pd.read_csv(P/'value_calibration.csv');b=pd.read_csv(P/'weather_conditioned_baseline_comparison.csv');hf=b.set_index('policy').loc['HIGHEST_FEASIBLE']
assert tr.episode.tolist()==list(range(1,26));assert ev.episode.tolist()==list(h.CHECKPOINTS);assert v.episode.tolist()==list(h.CHECKPOINTS)
assert (tr.optimizer_updates==128).all() and (tr.cumulative_optimizer_updates==tr.episode*128).all()
assert np.array_equal(tr.requests,tr.assignments+tr.unmatched)
assert np.array_equal(tr.replay_size,np.minimum(tr.requests.cumsum(),100000))
assert np.allclose(tr.exploration_epsilon,1-.95*tr.cumulative_optimizer_updates/50000)
checks=[]
for ep in h.CHECKPOINTS:
 cp=P/'checkpoints'/f'episode_{ep:03d}';meta=json.loads((cp/'continuation.json').read_text());h.validate_continuation(meta,h.sha256(P/'training_harness_config.json'),h.sha256(P/'march16_v2_full_day_fixture_manifest.json'),p.support_hash)
 d=h.PassengerSensitiveDQN.load(cp,sensitivity_provider=p)
 assert d.training_steps==ep*128 and len(d.replay)==int(tr.set_index('episode').loc[ep,'replay_size'])
 for model in [d.online,d.target]:assert all(np.isfinite(x.numpy()).all() for x in model.weights)
 assert all(np.isfinite(x.numpy()).all() for x in d.online.optimizer.variables)
 saved=json.loads((cp/'checkpoint.json').read_text());assert d.rng.bit_generator.state==saved['rng_state'];assert d.replay.rng.bit_generator.state==saved['replay_rng_state'];assert p.state_dict()==saved['sensitivity_state']
 checks.append(dict(episode=ep,updates=d.training_steps,replay_size=len(d.replay),epsilon=d.epsilon,hashes={f.name:h.sha256(f) for f in cp.iterdir() if f.is_file()}))
 del d
assert ev.requests.eq(73754).all() and ev.conditioning_sha256.eq(m['conditioning_sha256']).all()
assert ev.fleet_conserved.all() and ev.invalid_masks.eq(0).all() and ev.passenger_threshold_violations.eq(0).all()
base=pd.read_parquet(P/'HIGHEST_FEASIBLE_requests.parquet');maskcols=['mask_'+x for x in ['085','090','095','100','105','110','115']];masks=base[maskcols].to_numpy(bool);hi=masks.sum(axis=1)-1;choice=hi>0;factors=np.array([.85,.90,.95,1,1.05,1.10,1.15]);price=p.P_BASE_USD if hasattr(p,'P_BASE_USD') else 22.354198442390455
assert np.array_equal(masks,np.arange(7)[None,:]<=hi[:,None]);actions={};rows=[]
for ep in h.CHECKPOINTS:
 a=pd.read_csv(P/f'development_actions_ep{ep:02d}.csv');assert np.array_equal(a.Request_ID,base.Request_ID);ix=a.selected_action_index.to_numpy(int);assert masks[np.arange(len(ix)),ix].all();assert np.array_equal(a.feasible_action_count,base.feasible_action_count)
 summary=ev.set_index('episode').loc[ep];assert np.isclose(a.reward.sum(),summary.revenue);assert (a.reward>0).sum()==summary.assignments
 assert np.allclose(a.reward[a.reward>0],price*factors[ix[a.reward>0]])
 actions[ep]=ix;row=summary.to_dict();row.update(episode=ep,mean_offer=float((price*factors[ix]).mean()),revenue_gap_pct=100*(summary.revenue/hf.revenue-1),unmatched_difference=int(summary.unmatched-hf.unmatched));rows.append(row)
pd.DataFrame(rows).to_csv(O/'checkpoint_comparison.csv',index=False)
st=[]
for x,y in [(1,5),(5,10),(10,15),(15,20),(20,25),(10,25),(15,25)]:
 same=actions[x]==actions[y];ex=ev.set_index('episode').loc[x];ey=ev.set_index('episode').loc[y]
 st.append(dict(from_episode=x,to_episode=y,all_agreement_pct=100*same.mean(),choice_agreement_pct=100*same[choice].mean(),changed_pct=100*(~same).mean(),action_distribution_total_variation=.5*np.abs(np.bincount(actions[x],minlength=7)-np.bincount(actions[y],minlength=7)).sum()/len(same),revenue_change=ey.revenue-ex.revenue,assignment_change=int(ey.assignments-ex.assignments)))
pd.DataFrame(st).to_csv(O/'policy_stability.csv',index=False)
diff=hi[choice]-actions[25][choice];dominance=dict(highest_pct=100*float((diff==0).mean()),one_below_pct=100*float((diff==1).mean()),two_or_more_below_pct=100*float((diff>=2).mean()),mean_rank_below=float(diff.mean()),median_rank_below=float(np.median(diff)),choice_factor_counts=np.bincount(actions[25][choice],minlength=7).tolist())
selected=np.flatnonzero(choice & (actions[25]<hi))[:20];a25=pd.read_csv(P/'development_actions_ep25.csv');review=pd.DataFrame(dict(Request_ID=base.Request_ID.iloc[selected].to_numpy(),dqn_action=actions[25][selected],highest_action=hi[selected],dqn_reward=a25.reward.iloc[selected].to_numpy(),highest_policy_reward=base.reward.iloc[selected].to_numpy()));review['interpretation']='Policy-trajectory association only; no paired state-matched counterfactual';review.to_csv(O/'bounded_policy_difference_cases.csv',index=False)
ctx=pd.DataFrame(fixture['conditioning']);assert h.digest(fixture['conditioning'])==m['conditioning_sha256'];np.testing.assert_array_equal(base.epsilon_c,fixture['epsilon'])
manifest=pd.read_csv(Path(h.DEFAULT_GROUPING).parent/'conditional_support_manifest.csv').set_index('support_id')
for sid,g in ctx.groupby('support_id'):
 vals=np.load(manifest.loc[sid,'path'],mmap_mode='r');assert np.isin(np.asarray(fixture['epsilon'])[g.index],vals).all()
ctx.groupby(['T_group','raw_weather_code','time_specific_weather_group','support_id','fallback_level'],dropna=False).size().rename('requests').reset_index().to_csv(O/'weather_support_usage.csv',index=False)
primary=pd.concat([ev[ev.episode==25].assign(policy='EP25_DQN'),b],ignore_index=True);primary['revenue_per_request']=primary.revenue/primary.requests;primary.to_csv(O/'episode25_comparison.csv',index=False)
tr['assignment_rate']=tr.assignments/tr.requests;tr.to_csv(O/'training_trends.csv',index=False)
v.merge(tr[['episode','mean_loss']],on='episode').to_csv(O/'value_calibration_review.csv',index=False)
summary=dict(verdict='V2_STAGE25_REVIEW_REQUIRED',numerical_stability='YES',learning_signal='YES',q_calibration='POOR',policy_stability='PARTIAL',dynamic_value_evidence='NONE',charging_coverage='EXERCISED',converged='NO',ready_for_longer_training='REVIEW_REQUIRED',resume_continuity_validated='YES',resume_evidence_limit='Validated checkpoint contract, restored identities and cumulative accounting; no persisted per-slot IDs or full transition history beyond replay capacity.',episodes=25,inferred_completed_slots=400,requests=int(tr.requests.sum()),assignments=int(tr.assignments.sum()),revenue=float(tr.revenue.sum()),updates=3200,replay_size=100000,epsilon=.9392,training_charging_events=int(tr.charging_events.sum()),episodes_with_charging=int(tr.charging_events.gt(0).sum()),ep25=rows[-1],highest_feasible=hf.to_dict(),dominance=dominance,policy_stability_comparisons=st,checkpoints=checks,missing_diagnostics=['Training per-episode forced/choice/action distributions','Training per-episode selected-Q and absolute-TD distributions/max Q','Independent persisted slot-level and complete transition-ID audit','Paired state-matched driver/trajectory/supply/commitment counterfactuals','Per-training-episode charging entry/exit vehicles','Original checkpoint payload digests: current digests are post-run fingerprints, not independent creation-time authentication'],protected_period_access=False)
(O/'analysis_summary.json').write_text(json.dumps(summary,indent=2,default=str)+'\n')
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,2,figsize=(10,7));ax[0,0].plot(tr.episode,tr.mean_loss);ax[0,0].set_title('Training mean loss');ax[0,1].plot(tr.episode,tr.exploration_epsilon);ax[0,1].set_title('Training exploration epsilon');ax[1,0].plot(ev.episode,ev.revenue-hf.revenue,marker='o');ax[1,0].axhline(0,color='gray');ax[1,0].set_title('Fixed-fixture revenue gap vs Highest Feasible');ax[1,1].plot(v.episode,v.Q_mean,label='Selected Q');ax[1,1].plot(v.episode,v.MC_mean,label='MC return');ax[1,1].legend();ax[1,1].set_title('Value scale');fig.tight_layout();fig.savefig(O/'training_and_development_trends.png',dpi=160);plt.close(fig)
print(json.dumps({k:summary[k] for k in ['requests','assignments','updates','training_charging_events','episodes_with_charging','dominance','policy_stability_comparisons']},default=str))
