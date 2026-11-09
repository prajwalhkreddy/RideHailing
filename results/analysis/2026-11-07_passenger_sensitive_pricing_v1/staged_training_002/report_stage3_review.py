"""Saved-metric completion review only; no training, evaluation or parameter changes."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
R=Path(__file__).parent
st=pd.read_csv(R/'stage_summary.csv');dev=pd.read_csv(R/'development_evaluation.csv');mc=pd.read_csv(R/'mc_return_calibration.csv');q=pd.read_csv(R/'q_diagnostics.csv');td=pd.read_csv(R/'td_diagnostics.csv');ep=pd.read_csv(R/'episode_summary.csv')
inv=json.loads((R/'invariant_summary.json').read_text());last=ep[ep.episode==25].iloc[0]
assert last.optimizer_updates_cumulative==3200 and np.isclose(last.exploration_epsilon,.9392,rtol=0,atol=1e-15)
assert dev[dev.episode==25].learner_unchanged.all() and not any(inv.values())
comparison=dev[dev.episode.isin([1,10,25])].copy();comparison.to_csv(R/'development_ep01_ep10_ep25_comparison.csv',index=False)
qtrain=q[q.kind=='training'].set_index('episode');mtrain=mc[mc.kind=='training'].set_index('episode');ttrain=td[td.kind=='training'].set_index('episode')
ratio_before=abs(mtrain.loc[10,'median_selected_Q']/mtrain.loc[10,'median_G']);ratio_after=abs(mtrain.loc[25,'median_selected_Q']/mtrain.loc[25,'median_G'])
finite=np.isfinite(qtrain.select_dtypes('number')).all().all() and np.isfinite(mtrain.select_dtypes('number')).all().all() and np.isfinite(ttrain.select_dtypes('number')).all().all()
improving=(abs(1-ratio_after)<abs(1-ratio_before) and mtrain.loc[25,'MAE_Q_G']<mtrain.loc[10,'MAE_Q_G'] and ttrain.loc[25,'mean_abs_TD']<ttrain.loc[10,'mean_abs_TD'] and ttrain.loc[25,'mean_loss']<ttrain.loc[10,'mean_loss'])
movement={'available':False,'reason':'Episode10 per-request greedy actions/IDs were not persisted. Aggregate frequencies cannot identify request-level changes; no rerun performed.','same_action_pct':None,'changed_action_pct':None,'mean_absolute_factor_change':None,'upward_factor_changes_pct':None,'downward_factor_changes_pct':None}
a=R/'development_request_actions_ep10.csv';b=R/'development_request_actions_ep25.csv'
if a.exists() and b.exists():
 x=pd.read_csv(a);y=pd.read_csv(b);assert x.Request_ID.is_unique and y.Request_ID.is_unique
 z=x.merge(y,on='Request_ID',suffixes=('_10','_25'),validate='one_to_one');diff=z.selected_factor_25-z.selected_factor_10
 if len(z)==len(x)==len(y):movement=dict(available=True,N=len(z),same_action_pct=float(100*(diff==0).mean()),changed_action_pct=float(100*(diff!=0).mean()),mean_absolute_factor_change=float(abs(diff).mean()),upward_factor_changes_pct=float(100*(diff>0).mean()),downward_factor_changes_pct=float(100*(diff<0).mean()),interpretation='Change is not by itself improvement.')
(R/'policy_movement_ep10_ep25.json').write_text(json.dumps(movement,indent=2)+'\n')
freq=pd.read_csv(R/'action_frequency_by_feasible_count.csv');freq[(freq.episode==25)&(freq.kind=='development')].to_csv(R/'ep25_development_action_by_feasible_count.csv',index=False)
pol=pd.read_csv(R/'feasible_arm_policy_summary.csv');pol[(pol.episode==25)&(pol.kind=='development')].to_csv(R/'ep25_development_choice_policy.csv',index=False)
review=dict(Q_SCALE_TREND='APPROACHING_RETURN_SCALE' if improving else 'UNCLEAR',NUMERICALLY_STABLE='YES' if finite else 'NO',POLICY_STABLE='UNCLEAR',LEARNING_SIGNAL='YES' if improving else 'UNCLEAR',CONVERGED='NO',optimizer_updates=int(last.optimizer_updates_cumulative),exploration_epsilon=float(last.exploration_epsilon),protected_period_untouched=True,policy_movement_available=movement['available'],review_basis='Descriptive Episode10→25 changes in Q/MC relative gap, MAE, TD and loss jointly; no convergence or causal performance claim.',later_training_authorized=False)
(R/'episode25_review.json').write_text(json.dumps(review,indent=2)+'\n')
cols=['episode','revenue','assignments','assignment_rate','mean_offer','choice_request_rate','forced_request_rate','mean_abs_Q','max_abs_Q']
f=comparison[cols];table='| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in f.itertuples(index=False,name=None))
text='\n## Corrected V1 Episode25 completed review\n\n'+table+'\n\n```json\n'+json.dumps(review,indent=2)+'\n```\n\nFull choice/all-action and feasible-count distributions are in development_ep01_ep10_ep25_comparison.csv, ep25_development_action_by_feasible_count.csv and ep25_development_choice_policy.csv under the staged_training_002 report. MC calibration is retained per episode, including 15, 20, 25 and Episode25 development. No equality of Q and MC is required. Exact Episode10→25 per-request policy movement is '+('available.' if movement['available'] else 'unavailable because Episode10 did not retain those request records; aggregate policy movement is descriptive only.')+' No Episodes26+ launched; March17–31 untouched.\n'
for p in [R/'README.md',R.parent/'README.md',Path('README.md'),Path('results/analysis/2026-11-01_current_state_review/README.md'),Path('results/analysis/2026-11-04_academic_review_validation/README.md')]:
 with p.open('a') as out:out.write(text)
print('EP25_COMPLETION_REVIEW_SAVED')
