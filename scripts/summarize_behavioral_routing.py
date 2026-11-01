"""Saved-final-model probability gate; no optimization or simulator execution."""
import json,hashlib
import numpy as np,pandas as pd
from src.routing.learning import load_final_policy

def finalize(root,out,data,modeldir,cache):
 def save(n,v):(out/n).write_text(json.dumps(v,indent=2,default=str)+'\n')
 meta=json.loads((out/'dataset_validation.json').read_text());n=meta['train_n'];X,M,Y=[np.load(cache/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y']];model=load_final_policy(modeldir/'fedavg_round_5.keras')
 prior=np.bincount(Y[:n],minlength=9).astype(float);prior/=prior.sum();N=len(Y)-n
 totals={k:dict(ce=0.,brier=0.,mean=np.zeros(9),bins=np.zeros((10,3))) for k in ['fedavg','masked_training_prior']};diffs=[]
 # Block-level paired loss differences expose temporal dependence; no tuning.
 slot_sizes=[len(pd.read_parquet(data/f'slot_{i:04d}.parquet',columns=['experience_id'])) for i in range(576,720)]
 pos=n
 for size in slot_sizes:
  paired=np.zeros(2)
  for start in range(pos,pos+size,4096):
   end=min(start+4096,pos+size);mask=M[start:end];y=Y[start:end];logits=model(X[start:end],training=False).numpy().astype(float);logits=np.where(mask,logits,-np.inf);mx=logits.max(1);exp=np.exp(logits-mx[:,None]);p=exp/exp.sum(1)[:,None];b=np.where(mask,prior,0.);assert (b.sum(1)>0).all();b/=b.sum(1)[:,None]
   loss=[]
   for name,q in [('fedavg',p),('masked_training_prior',b)]:
    assert np.isfinite(q).all() and np.allclose(q.sum(1),1) and (q[~mask]==0).all()
    true=q[np.arange(len(y)),y]
    # Training supports all validation actions; no smoothing or loss clipping.
    assert (true>0).all()
    ce=-np.log(true);br=(q*q).sum(1)-2*true+1
    t=totals[name];t['ce']+=ce.sum();t['brier']+=br.sum();t['mean']+=q.sum(0)
    conf=q.max(1);correct=q.argmax(1)==y;bi=np.minimum((conf*10).astype(int),9)
    for j in range(10):
     z=bi==j;t['bins'][j]+=np.array([z.sum(),conf[z].sum(),correct[z].sum()])
    loss.append((ce,br))
   paired+=np.array([(loss[0][j]-loss[1][j]).sum() for j in range(2)])
  diffs.append(paired/size);pos+=size
 result={}
 for name,t in totals.items():
  bins=[dict(lower=i/10,upper=(i+1)/10,N=int(row[0]),mean_confidence=row[1]/row[0],accuracy=row[2]/row[0]) for i,row in enumerate(t['bins']) if row[0]]
  result[name]=dict(cross_entropy=t['ce']/N,Brier=t['brier']/N,mean_probability=(t['mean']/N).tolist(),calibration_bins=bins,top_label_ECE=sum(z['N']*abs(z['mean_confidence']-z['accuracy']) for z in bins)/N)
 delta=np.asarray(diffs);dmean=delta.mean(0);se=delta.std(0,ddof=1)/np.sqrt(len(delta));improvement=all(result['fedavg'][k]<result['masked_training_prior'][k] for k in ['cross_entropy','Brier'])
 worse=any(result['fedavg'][k]>result['masked_training_prior'][k] for k in ['cross_entropy','Brier'])
 verdict='YES' if improvement and (dmean+1.96*se<0).all() else 'NO' if worse and (dmean-1.96*se>0).any() else 'INCONCLUSIVE'
 result.update(ROUTING_PROBABILITIES_INFORMATIVE=verdict,train_N=n,validation_N=N,training_action_prior=prior.tolist(),true_distribution=(np.bincount(Y[n:],minlength=9)/N).tolist(),Brier_definition='mean sum_k(p_k-y_k)^2; no divide by class count',paired_slot_difference=dict(mean=dmean.tolist(),standard_error=se.tolist(),columns=['CE','Brier'],note='Descriptive144slot block check, assumes independent slots; serial dependence not formally corrected. Not a tuning criterion.'),previous_provenance=dict(fedavg_accuracy=.8536730607823922,fedavg_CE=.538559741855583,fedavg_Brier=.2458809862428875,prior_CE=.3520592919240443,prior_Brier=.11762113534739826,note='Different dataset; no causal or direct model-improvement claim.'))
 save('routing_probability_adequacy.json',result)
 metrics=json.loads((out/'routing_validation_metrics.json').read_text());support=pd.read_csv(out/'routing_action_support.csv');majority=int(support.train.to_numpy().argmax())
 for name,file in [('central','central_validation.json'),('final_fedavg','fedavg_validation.json')]:
  m=metrics[name];m['majority_action_from_training']=majority;m['majority_label_accuracy']=float((Y[n:]==majority).mean());m['catastrophic_collapse']=bool(m['largest_predicted_class_share']>.9 and m['action_support'][np.argmax(m['predicted_counts'])]/N<.9)
  m['supported_zero_prediction_actions']=[i for i in range(9) if m['action_support'][i]>0 and m['predicted_counts'][i]==0]
  m['ROUTING_EFFECTIVENESS_CONCERN']=bool(m['accuracy']<=m['majority_label_accuracy'] or m['catastrophic_collapse'] or m['supported_zero_prediction_actions'] or m['invalid_action_count'] or (name=='final_fedavg' and verdict!='YES'))
  if name=='central':save(file,m)
  else:
   original=json.loads((out/file).read_text());original['final_metrics']=m;save(file,original)
 save('routing_validation_metrics.json',metrics)
 cm=pd.read_csv(out/'routing_confusion_matrix.csv')
 for label,file in [('central','central_confusion_matrix.csv'),('fedavg_round5','fedavg_confusion_matrix.csv')]:cm[cm.model==label].drop(columns='model').to_csv(out/file,index=False)
 selection=dict(FINAL_BEHAVIORAL_ROUTING_MODEL_READY='YES',ROUTING_READY_FOR_PRICING='YES' if verdict=='YES' else 'NO',ROUTING_PROBABILITIES_INFORMATIVE=verdict,ROUTING_EFFECTIVENESS_CONCERN='YES' if metrics['final_fedavg']['ROUTING_EFFECTIVENESS_CONCERN'] else 'NO',checkpoint=str((modeldir/'fedavg_round_5.keras').relative_to(root)),checkpoint_sha256=hashlib.sha256((modeldir/'fedavg_round_5.keras').read_bytes()).hexdigest(),rationale='Final fifth-round global model required structurally; selection does not imply probability adequacy.',runtime_activation='Not changed; pricing training not authorized.',status='SIMULATOR_DERIVED_ROUTING_BASELINE')
 save('routing_model_selection.json',selection)
 gen=root/'results/analysis/2026-10-29_final_behavioral_routing_generation';slots=pd.read_csv(gen/'experience_generation_summary.csv');grid=pd.read_csv(gen/'grid_slot_supply.csv');grid['demand_minus_slot_start_idle']=grid.requests-grid.idle_at_slot_start
 keys=['requests','accepted','rejected','assignments','accepted_unmatched','price_ineligible_candidate_count','requests_with_any_price_ineligible_candidate','accepted_requests_unmatched_due_to_no_price_eligible_driver','P_max_above_2base','P_max_above_5base','driver_price_assignment_violations']
 summary={k:int(slots[k].sum()) for k in keys};summary.update(epsilon_min=float(slots.epsilon_min.min()),P_max_min=float(slots.P_max_min.min()),P_max_max=float(slots.P_max_max.max()),grid_slot_supply='AVAILABLE: exact slot-start idle in grid; not request-time neighbor availability',grid_slot_rows=len(grid),highest_deficits=grid.nlargest(10,'demand_minus_slot_start_idle').to_dict('records'),highest_excess=grid.nsmallest(10,'demand_minus_slot_start_idle').to_dict('records'),reserve_exclusions=json.loads((gen/'generation_status.json').read_text()),no_simulator_rerun=True)
 previous=root/'results/analysis/2026-10-25_final_simulator_routing_training/dataset_validation.json'
 if previous.exists():
  old=json.loads(previous.read_text());summary['previous_provenance_decision_types']=old.get('decision_types');summary['previous_provenance_total']=old.get('experiences');summary['comparison_note']='Different upstream contracts and generated population; descriptive only.'
 save('behavioral_generation_summary.json',summary)
 meta['majority_action']=int(support.total.to_numpy().argmax());meta['majority_percentage']=float(support.percentage.max());meta['zero_support_actions']=support.loc[support.total==0,'action'].tolist();meta['very_low_support_actions']=support.loc[(support.total>0)&(support.percentage<1),'action'].tolist();meta['very_low_support_definition']='positive support below1%, descriptive existing threshold; no rebalancing'
 save('dataset_validation.json',meta)
 print('PROBABILITY GATE '+json.dumps(selection),flush=True)
