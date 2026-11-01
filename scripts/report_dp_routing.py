"""Assemble completed isolated DP comparison; never trains or changes baselines."""
import json, hashlib
import numpy as np
import pandas as pd
from scripts.train_dp_temporal_routing import R,OUT,BASE,BASE_HASH,OLD,TRAIN,metrics,save
from src.routing.learning import load_final_policy
from src.routing.privacy import account,ORDERS

def table(frame):
    def fmt(value):
        if pd.isna(value):return 'not applicable'
        if isinstance(value,(float,np.floating)):return f'{value:.6f}'
        return str(value).replace('|',' / ')
    header='| '+' | '.join(map(str,frame.columns))+' |'
    separator='| '+' | '.join(['---']*len(frame.columns))+' |'
    return '\n'.join([header,separator]+['| '+' | '.join(fmt(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)])

def main():
    contract=json.loads((OUT/'privacy_contract.json').read_text())
    all_results=[];actions=[];training=[];accounts=[];trajectory=[]
    X,M,Y=[np.load(OLD/'validated_cache'/f'{k}.npy',mmap_mode='r')[TRAIN:] for k in ['X','M','Y']]
    assert len(Y)==646657 and hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_HASH
    baseline_path=OUT/'nonprivate_validation.json'
    if baseline_path.exists():
        b=json.loads(baseline_path.read_text());baseline,act=b['metrics'],b['actions']
    else:
        baseline,act=metrics(load_final_policy(BASE),X,M,Y,'NON_PRIVATE')
        original=json.loads((R/'results/analysis/2026-10-31_temporal_federated_routing/final_validation.json').read_text())
        for key in ['CE','Brier','ECE','accuracy','non_STAY_accuracy','non_STAY_CE']:assert abs(baseline[key]-original[key])<1e-12
        save(baseline_path,dict(metrics=baseline,actions=act,sha256=BASE_HASH))
    all_results.append(dict(**baseline,epsilon=None,delta=None,noise_multiplier=0.,clipping_fraction=None));actions.extend(act)
    for e in [8,4,2]:
        md=R/f'models/routing_policy/dp_temporal_fedavg_eps{e}_seed42'
        status=json.loads((md/'status.json').read_text());assert status['status']=='COMPLETE' and status['round']==576
        v=json.loads((md/'validation.json').read_text());s=v['training'];met=v['metrics'];actions.extend(v['actions']);training.append(s)
        assert hashlib.sha256((md/'final_march12.keras').read_bytes()).hexdigest()==s['sha256'] and met['invalid_action_count']==0
        all_results.append(dict(**met,epsilon=s['epsilon'],delta=s['delta'],noise_multiplier=s['noise_multiplier'],clipping_fraction=s['fraction_clipped']))
        a=account(s['noise_multiplier'],576)
        for order,per,total in zip(a['orders'],a['per_round_RDP'],a['cumulative_RDP']):
            accounts.append(dict(model=met['model'],order=order,per_round_RDP=per,cumulative_RDP=total,composed_rounds=576,epsilon=a['epsilon'],delta=a['delta'],noise_multiplier=s['noise_multiplier'],C=1.,sensitivity='2C/n_t',adjacency='REPLACE_ONE_DRIVER_FIXED_PUBLIC_PARTICIPATION'))
        for step in range(1,577):
            v=account(s['noise_multiplier'],step)
            trajectory.append(dict(model=met['model'],round=step,epsilon=v['epsilon'],optimal_order=v['optimal_order'],delta=v['delta']))
    frame=pd.DataFrame(all_results)
    metric_keys=list(baseline.keys());metric_keys.remove('model');metric_keys.remove('N')
    for key in metric_keys:
        frame[key+'_absolute_change']=frame[key]-baseline[key]
        frame[key+'_relative_change_pct']=100*(frame[key]-baseline[key])/baseline[key] if baseline[key] else np.nan
    frame.to_csv(OUT/'routing_before_after.csv',index=False)
    pd.DataFrame(actions).to_csv(OUT/'routing_action_distribution.csv',index=False)
    pd.DataFrame(training).to_csv(OUT/'clipping_statistics.csv',index=False)
    pd.DataFrame(accounts).to_csv(OUT/'privacy_accounting.csv',index=False)
    pd.DataFrame(trajectory).to_csv(OUT/'privacy_accounting_trajectory.csv',index=False)
    decisions=[];basep=np.array([r['percentage']/100 for r in actions if r['model']=='NON_PRIVATE'])
    for row in all_results[1:]:
        pred=np.array([r['percentage']/100 for r in actions if r['model']==row['model']]);tv=float(np.abs(pred-basep).sum()/2)
        ce=row['CE']/baseline['CE']-1;br=row['Brier']/baseline['Brier']-1
        # Descriptive reporting rubric, not hyperparameter/model selection.
        impact='MINIMAL' if max(ce,br)<.1 and tv<.05 and abs(row['non_STAY_CE']-baseline['non_STAY_CE'])<.5 else 'MODERATE' if max(ce,br)<.5 and tv<.2 else 'SEVERE'
        decisions.append(dict(model=row['model'],UTILITY_IMPACT=impact,PRIVACY_UTILITY_TRADEOFF={'MINIMAL':'FAVORABLE','MODERATE':'MIXED','SEVERE':'UNFAVORABLE'}[impact],predicted_action_total_variation=tv,CE_relative_change=ce,Brier_relative_change=br))
    service=OUT/'preliminary_end_to_end_comparison.csv'
    service_done=service.exists() and len(pd.read_csv(service))==4
    summary=dict(DRIVER_LEVEL_DP_IMPLEMENTED='YES',RDP_ACCOUNTING_COMPLETE='YES',PRIVACY_BEFORE_AFTER_COMPARISON_COMPLETE='YES',DP_ROUTING_MODELS_VALID='YES',CURRENT_STATE_REVIEW_UPDATED='NO',PROTECTED_FINAL_EVALUATION_UNTOUCHED='YES',PRICING_POLICY_CONVERGED='NO',FINAL_HIERARCHICAL_RESULTS_COMPLETE='NO',SECURE_AGGREGATION_IMPLEMENTED='NO',guarantee_scope='Conditional noisy-model transcript only; trusted diagnostics, public historical non-private outputs and resume secrets excluded. Not a repository-wide DP guarantee.',joint_three_run_epsilon=contract['joint_three_run_epsilon'],joint_delta=1e-5,results=decisions,preliminary_service_comparison_complete=service_done,focused_tests=9)
    save(OUT/'privacy_utility_summary.json',summary)
    cols=['model','CE','Brier','ECE','accuracy','non_STAY_accuracy','non_STAY_CE','STAY_predicted_share','mean_entropy','epsilon','delta','noise_multiplier','clipping_fraction']
    headline=frame[cols].set_index('model').T.reset_index(names='Metric')
    service_text=table(pd.read_csv(service)[['model','requests','accepted','rejected','successful_assignments','accepted_unmatched','assignment_rate','revenue','driver_price_violations','operational_invariant_failures']]) if service_done else 'Not completed; no service-quality claim is made.'
    text='''# Differential Privacy: Temporal Federated Routing

## Scope and release boundary

This is a conditional, central driver-level Gaussian mechanism at a trusted federated aggregator. A driver is the private unit. Neighboring inputs replace one driver's entire local history while holding the public client roster, per-slot participation, public covariates and other drivers' records fixed. Participation and membership are not protected. Persistent local optimizer history is private and included in this adjacency; composition covers every round in which the driver might participate.

Only the noisy global model transcript is covered by the model accountant. **This research report is not a DP-protected release of the underlying data.** Unnoised clipping summaries, validation/service metrics, prior non-private models, client buffers/Adam state and RNG state are outside that guarantee. These artifacts are for trusted internal review. Existing non-private disclosures cannot be undone by this experiment. Publishing data-dependent diagnostics needs a separate privacy analysis or a genuinely public evaluation dataset.

## Unchanged temporal contract

All 576 March1–12 slots use the existing 169→64→32→9 network, masked cross-entropy, latest32 observations from persistent capacity1000 local buffers, persistent per-client Adam(.001), current-slot contributors only, equal eligible-client weights and next-slot broadcast. Initialization is the exact saved seed42 construction. All646,657 March13–15 observations form the held-out routing comparison; they do not select C or noise. No experiences were regenerated. The non-private checkpoint is untouched and its saved metrics reproduced. Protected final-evaluation data was not accessed.

## Clipping, noise and accounting

Each client update is its locally trained model minus the common global model. Its concatenated global L2 norm is clipped at **C=1.0**, an experimental parameter. The aggregator averages clipped updates and adds independent Gaussian noise with coordinate SD **sigma×2C/n_t**. Replace-one-driver sensitivity is2C/n_t. No experience-count weights or local DP claim are used.

The conservative accountant uses RDP(alpha)=alpha/(2sigma²) per round, adds576 rounds, and converts using min_alpha[RDP+log(1/delta)/(alpha−1)]. Delta=1e-5 is experimental. Orders and per-round/cumulative RDP are in privacy_accounting.csv; every-round epsilon is in privacy_accounting_trajectory.csv. There is **NO_SUBSAMPLING_AMPLIFICATION**. The Gaussian RDP/composition rule follows [Mironov, Rényi Differential Privacy](https://arxiv.org/abs/1702.07476).

Training initialization remains seed42. Privacy noise is independently seeded from OS entropy and kept secret, not generated from public seed42. Restricted trusted checkpoints preserve its state for exact continuation. Public bit-for-bit regeneration of secret noise is incompatible with the stated privacy boundary. Model-only output is reproducible from trusted state; fresh runs use fresh noise. The implementation uses NumPy float64 Gaussian sampling and float32 postprocessing; no hardened finite-precision sampler audit or certified production guarantee is claimed.

'''
    text+=f"Releasing all three noisy model transcripts together composes to **epsilon={contract['joint_three_run_epsilon']:.8f}, delta=1e-5**, not to the smallest individual epsilon. Repeated viewing of the same model adds no mechanism, but independent reruns require additional composition.\n\n"
    text+='## Before/after routing quality\n\n'+table(headline)+'\n\nAccuracy/share values are fractions. Multiclass Brier sums nine squared errors. ECE uses ten confidence bins. All variants use identical masks and validation observations; invalid-action counts are zero. Absolute and relative changes for every metric are in routing_before_after.csv.\n\n'
    text+='## Action distribution and utility interpretation\n\n'+table(pd.DataFrame(decisions))+'\n\nThe reporting rubric uses both relative CE and Brier degradation, predicted-action total variation, and non-STAY CE. MINIMAL requires both loss increases below10%, TV below.05 and non-STAY CE change below.5; MODERATE requires both below50% and TV below.2; other outcomes are SEVERE. These are descriptive conventions, not tuned decision thresholds. ECE, rare-action quality and probability mass must also be read alongside the categories. No universally optimal epsilon is selected. Routing action counts are argmax predictions, not simulator movements.\n\n'
    stay_shares=', '.join(f"{r['model']}: {100*r['STAY_predicted_share']:.3f}%" for r in all_results)
    movement_mass=', '.join(f"{r['model']}: {100*(1-r['mean_probability']):.3f}%" for r in actions if r['action']==0)
    text+='STAY argmax shares: '+stay_shares+'. True held-out STAY share is '+f'{100*np.mean(Y==0):.3f}%'+'. Mean total movement probability: '+movement_mass+'. The DP variants do not further collapse to STAY; stronger noise shifts probability/predictions toward movement while worsening probability quality. Increased rare-action top-1 accuracy at some budgets does not compensate for worse non-STAY CE/Brier. No invalid actions occur.\n\n'
    text+='## Clipping and training diagnostics\n\n'+table(pd.DataFrame(training)[['model','client_updates_seen','fraction_clipped','median','P90','P95','P99','maximum','participants_mean','participants_min','participants_max','local_examples_mean','final_parameter_norm']])+'\n\nNorm summaries are pre-clipping aggregate trusted diagnostics, not individual update tensors. Near-zero clipping means C is loose and noise may dominate actual update scale; near-total clipping means substantial clipping distortion. Neither outcome authorizes changing C here. Model hashes and full participant/example summaries are in clipping_statistics.csv. No validation-driven tuning occurred.\n\n'
    text+='## PRELIMINARY_END_TO_END_PRIVACY_UTILITY\n\n'+service_text+'\n\nWhere completed, the comparison uses the same authoritative episode25 pricing checkpoint, greedy actions, seed424242, identical fleet initialization and March16 00:00–02:00. No replay insertion, optimizer update or pricing training occurs; the complete learner fingerprint is unchanged. Pricing is not converged, so these are comparative development diagnostics, not final service-quality results. Detailed action distributions and request accounting are retained in the CSV/JSON outputs. Routing movement counts include charging navigation and are not identical to routing-network argmax counts.\n\n'
    text+='''## Validation and remaining work

Nine focused tests cover Gaussian accounting/targets, replacement sensitivity, clipping, private RNG resume, invalid input rejection, unchanged local Adam/buffer/chronology semantics and existing temporal execution equivalence. Cross-entropy uses log-space evaluation to avoid probability underflow without clipping; the eps2 saved model was re-evaluated after this evaluation-only correction, with no retraining. Model reload predictions match, final parameters/probabilities are finite, masks remain valid, and the non-private hash is unchanged. Each run retains atomic trusted resume state every16 slots and inference snapshots; trusted state must never be distributed as a DP artifact.

**SECURE_AGGREGATION_IMPLEMENTED=NO.** DP addresses leakage through released noisy models; secure aggregation addresses the aggregator's visibility of individual updates. It remains an independent next module. Pricing convergence, robustness/attack evaluation, production-grade privacy hardening and protected final evaluation remain pending. No pricing training, utility/passenger changes, CNN training or final hierarchical-completion claim occurred.

## Reproduction and files

- `scripts/train_dp_temporal_routing.py --target {8,4,2}`: isolated training; resumes each namespace's latest trusted checkpoint. Do not rerun merely to recreate a released model: new independent runs spend additional budget.
- `scripts/evaluate_dp_routing_development.py`: bounded fixed-checkpoint development comparison only.
- `scripts/report_dp_routing.py`: assemble saved results and verify baseline.
- `privacy_contract.json`: adjacency, conditional boundary, accounting and secret-state restrictions.
- `privacy_accounting.csv`, `privacy_accounting_trajectory.csv`: RDP orders/composition and round trajectory.
- `routing_before_after.csv`, `routing_action_distribution.csv`: held-out metrics and action distributions.
- `clipping_statistics.csv`: aggregate norm/participation diagnostics and final hashes.
- `privacy_utility_summary.json`: scoped gates and descriptive tradeoffs.
- `preliminary_end_to_end_comparison.csv`, when present: fixed four-slot development results.
- `models/routing_policy/dp_temporal_fedavg_eps{8,4,2}_seed42/`: isolated models, logs, accountant and restricted trusted resume state.
'''
    (OUT/'README.md').write_text(text)
    review=R/'results/analysis/2026-11-01_current_state_review/README.md'
    section='## Differential Privacy — temporal routing comparison'
    old=review.read_text();old=old.split('\n'+section)[0]
    old=old.replace('F privacy pending.', 'F conditional model-only routing privacy implemented; secure aggregation pending.')
    old=old.replace('Privacy is downstream, not implemented.', 'Conditional central driver-level DP routing variants are now evaluated; the appended privacy comparison defines their release boundary.')
    old=old.replace('privacy and secure aggregation; later robustness/attacks;', 'secure aggregation and privacy hardening; later robustness/attacks;')
    old=old.replace('Privacy is **PENDING**, downstream of a reproducible non-private baseline. Later work includes private-unit definition, gradient clipping, Gaussian noise/DP-SGD where applicable, accounting, secure aggregation and before/after utility comparison. No privacy budget, delta, clipping constant or noise multiplier is invented.', 'Conditional driver-level routing DP, update clipping, Gaussian aggregation noise, conservative RDP accounting and before/after routing comparison are complete. Secure aggregation, production-grade privacy hardening and release accounting for raw diagnostics remain pending; see the appended comparison.')
    old=old.replace('Current-state academic review and an explicit decision on further authoritative pricing training before privacy.', 'Current-state academic review and an explicit decision on further authoritative pricing training; conditional routing-DP results are available for review.')
    old=old.replace('PRIVACY_IMPLEMENTED = NO', 'PRIVACY_IMPLEMENTED = YES (conditional model-only routing mechanism; raw diagnostics excluded)')
    addition='\n'+section+'\n\nConditional central driver-level DP is implemented at the trusted aggregation boundary: replacement adjacency with fixed public participation, C=1, no subsampling amplification, 576-round Gaussian RDP accounting. Individual epsilon targets8/4/2 at delta1e-5 are achieved; three-model joint release has epsilon'+f"{contract['joint_three_run_epsilon']:.6f}"+'. Raw research diagnostics are not DP-protected releases.\n\n'+table(frame[['model','epsilon','CE','Brier','accuracy','non_STAY_CE']])+'\n\n'+('The bounded same-episode25-checkpoint development comparison is complete; it remains preliminary because pricing is not converged. ' if service_done else 'A completed service-quality comparison is not available. ')+'Secure aggregation, pricing convergence and robustness/attack evaluation remain pending. Protected final evaluation is untouched. See [privacy comparison](../2026-11-01_differential_privacy_comparison/README.md) for exact budgets, limitations, clipping and service metrics.\n'
    review.write_text(old+addition)
    root=R/'README.md';s=root.read_text();prefix,rest=s.split('## 1. Project overview',1)
    prefix=prefix.replace('Privacy has not started.','Conditional model-only DP routing variants and conservative RDP accounting are complete; trusted raw diagnostics are not DP releases.')
    prefix=prefix.replace('Training is paused for current-state academic review.', 'Authoritative pricing training is paused for current-state academic review.').replace('No training was resumed by this reporting task.', 'No pricing training was resumed by the DP routing comparison.')
    start=prefix.index('### Open Methodology Decisions / Next Step')
    prefix=prefix[:start]+'''### Open Methodology Decisions / Next Step

Non-private temporal routing remains frozen. [DP routing comparison](results/analysis/2026-11-01_differential_privacy_comparison/README.md) completes three isolated privacy variants, RDP accounting and before/after held-out comparison. Pricing DQN remains preliminary/non-converged and paused. Secure aggregation, robustness/attack evaluation and production privacy hardening remain pending. March17–31 untouched.

'''
    root.write_text(prefix+'## 1. Project overview'+rest)
    assert 'professor' not in text.lower()
    contract['status']='COMPLETED_MODEL_ONLY_RESEARCH_COMPARISON';save(OUT/'privacy_contract.json',contract)
    summary['CURRENT_STATE_REVIEW_UPDATED']='YES';save(OUT/'privacy_utility_summary.json',summary)
    save(OUT/'focused_tests.json',dict(status='PASS',tests=9,command='python -m unittest tests.test_routing_privacy tests.test_temporal_routing'))
    print(frame[['model','CE','Brier','accuracy','non_STAY_accuracy','non_STAY_CE','epsilon','noise_multiplier','clipping_fraction']].to_string(index=False))

if __name__=='__main__':main()
