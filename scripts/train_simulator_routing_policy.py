"""One fixed five-round driver-client FedAvg run on real simulator experiences."""
from pathlib import Path
import sys,os,json,hashlib
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,pyarrow.parquet as pq,tensorflow as tf
from src.routing.learning import LocalRoutingLearner,RoutingLearningParameters,LocalObservationBuffer,LocalPolicyObservation,build_routing_policy_model,load_final_policy
from src.routing.federated import aggregate_policy_updates
from src.simulation.temporal_protocol import assert_training_update_allowed

OUT=ROOT/'results/analysis/2026-10-21_simulator_derived_routing_policy'
DATA=ROOT/'data/processed/routing_experiences_mar01_mar15_2026'
MODELS=ROOT/'models/routing_policy/mar01_mar15_2026_3km_simulator_169x64x32x9_seed42'

def save(name,value): (OUT/name).write_text(json.dumps(value,indent=2,default=str)+'\n')

def evaluate(model,x,m,y):
    cm=np.zeros((9,9),np.int64);loss_sum=0.;n=len(y)
    for start in range(0,n,4096):
        xb=x[start:start+4096];mb=m[start:start+4096];yb=y[start:start+4096]
        logits=model(xb,training=False).numpy().astype(float)
        assert logits.shape==(len(yb),9) and np.isfinite(logits).all()
        logits=np.where(mb,logits,-np.inf);mx=logits.max(1);ex=np.exp(logits-mx[:,None]);probs=ex/ex.sum(1)[:,None]
        assert np.isfinite(probs).all() and np.allclose(probs.sum(1),1.) and (probs[~mb]==0).all()
        pred=probs.argmax(1);assert mb[np.arange(len(yb)),pred].all()
        loss_sum+=float(np.sum(mx+np.log(ex.sum(1))-logits[np.arange(len(yb)),yb]))
        np.add.at(cm,(yb,pred),1)
    support=cm.sum(1);prediction=cm.sum(0);p=prediction[prediction>0]/n
    precision=np.divide(np.diag(cm),prediction,out=np.zeros(9),where=prediction>0)
    recall=np.divide(np.diag(cm),support,out=np.zeros(9),where=support>0)
    f1=np.divide(2*precision*recall,precision+recall,out=np.zeros(9),where=precision+recall>0)
    accuracy=float(np.trace(cm)/n);majority=float(support.max()/n)
    return dict(N=n,accuracy=accuracy,cross_entropy=loss_sum/n,majority_label_accuracy=majority,valid_action_prediction_rate=1.,invalid_action_count=0,action_support=support.tolist(),predicted_counts=prediction.tolist(),precision=precision.tolist(),recall=recall.tolist(),F1=f1.tolist(),STAY_prediction_share=float(prediction[0]/n),prediction_entropy=float(-(p*np.log(p)).sum()),zero_prediction_actions=np.where(prediction==0)[0].tolist(),ROUTING_EFFECTIVENESS_CONCERN=bool(accuracy<=majority or ((prediction==0)&(support/n>=.01)).any() or (prediction.max()/n>.9 and support[prediction.argmax()]/n<.9))),cm

def main():
    assert json.loads((OUT/'generation_status.json').read_text())['status']=='COMPLETE'
    paths=[DATA/f'slot_{slot:04d}.parquet' for slot in range(720)]
    assert all(p.is_file() for p in paths)
    # Load only required arrays; source order remains slot/experience order.
    arrays=[[],[],[],[],[]];counts=np.zeros(5000,np.int64);support=np.zeros(9,np.int64);types={};previous=-1;train_n=0;valid_n=0
    for slot,path in enumerate(paths):
        f=pq.read_table(path).to_pandas();timestamp=pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*slot)
        assert_training_update_allowed(timestamp)
        assert (f.timestamp==timestamp).all() and f.experience_id.is_monotonic_increasing
        if len(f):assert f.experience_id.iloc[0]==previous+1;previous=int(f.experience_id.iloc[-1])
        x=np.stack(f.state_169).astype(np.float32) if len(f) else np.empty((0,169),np.float32)
        m=np.stack(f.action_mask_9).astype(bool) if len(f) else np.empty((0,9),bool)
        y=f.label_action_0_to_8.to_numpy(np.int64);ids=f.driver_id.to_numpy(np.int64)
        assert x.shape==(len(f),169) and m.shape==(len(f),9) and np.isfinite(x).all()
        assert ((y>=0)&(y<9)).all() and m[np.arange(len(y)),y].all() and ((ids>=0)&(ids<5000)).all()
        assert (x[:,:27].reshape(-1,9,3)[~m]==0).all()
        arrays[0].append(x);arrays[1].append(m);arrays[2].append(y);arrays[3].append(ids);arrays[4].append(np.full(len(f),slot,np.int16))
        counts+=np.bincount(ids,minlength=5000);support+=np.bincount(y,minlength=9)
        for k,v in f.decision_type.value_counts().items():types[k]=types.get(k,0)+int(v)
        if slot<576:train_n+=len(f)
        else:valid_n+=len(f)
    X,M,Y,IDS,SLOTS=[np.concatenate(a) for a in arrays];del arrays
    split=dict(train_start='2026-03-01 00:00',train_end='2026-03-12 23:30',validation_start='2026-03-13 00:00',validation_end='2026-03-15 23:30',train_experiences=train_n,validation_experiences=valid_n,total_experiences=len(Y),participant_semantics='one driver_id is one client',participants_with_experience=int((counts>0).sum()),zero_experience_participants=int((counts==0).sum()),active_participant_counts=dict(min=int(counts[counts>0].min()),median=float(np.median(counts[counts>0])),mean=float(counts[counts>0].mean()),max=int(counts.max())),decision_type_counts=types)
    save('routing_split.json',split)
    params=RoutingLearningParameters();config=dict(optimizer='Adam',learning_rate=params.learning_rate,batch_size=params.batch_size,local_epochs=params.local_epochs,rounds=5,seed=42,early_stopping=False,loss='masked sparse categorical cross entropy from logits',selection='lowest March 13–15 validation cross entropy across five fixed rounds',client='driver_id; no synthetic grid partition',local_order='chronological',optimizer_reset='fresh Adam per client per round, matching existing controlled baseline trainer',central_pretraining='not applicable; one plain FedAvg training procedure from seed42 global initialization',rebalance=False)
    save('routing_training_config.json',config);MODELS.mkdir(parents=True,exist_ok=True)
    tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
    model=build_routing_policy_model(params,seed=42);history=[];best=float('inf');best_round=None
    progress=MODELS/'training_progress.json'
    if progress.exists():
        pr=json.loads(progress.read_text());history=pr['history'];best=pr['best_loss'];best_round=pr['best_round'];model=load_final_policy(MODELS/'last.keras')
    initial,_=evaluate(model,X[train_n:],M[train_n:],Y[train_n:]) if not history else (json.loads((OUT/'routing_validation_metrics.json').read_text())['initial_untrained'],None)
    # A reusable local workspace preserves identical fresh optimizer semantics, not a new client partition.
    learner=LocalRoutingLearner(0,params,seed=42);learner.optimizer.build(learner.policy_model.trainable_variables)
    initial_optimizer=[v.numpy().copy() for v in learner.optimizer.variables]
    indices=[np.flatnonzero(IDS[:train_n]==i) for i in range(5000)]
    final_metadata=None
    for round_id in range(len(history),5):
        updates=[];losses=[];global_weights=model.get_weights()
        for client,positions in enumerate(indices):
            learner.vehicle_id=client;learner.local_sample_count=0;learner._trained_slots.clear();learner.reset_from_global_weights(global_weights)
            for variable,value in zip(learner.optimizer.variables,initial_optimizer):variable.assign(value)
            for step,start in enumerate(range(0,len(positions),32)):
                idx=positions[start:start+32]
                for slot in np.unique(SLOTS[idx]):assert_training_update_allowed(pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*int(slot)))
                learner.observations=LocalObservationBuffer(params.local_observation_capacity)
                for j in idx:learner.observations.add(LocalPolicyObservation(X[j],int(Y[j]),M[j],slot_id=int(SLOTS[j])))
                loss=learner.train_for_slot(step);assert np.isfinite(loss);losses.append(loss)
            updates.append(learner.export_local_update())
            if (client+1)%500==0:print(f'round {round_id+1}: {client+1}/5000 clients',flush=True)
        aggregate=aggregate_policy_updates(updates,round_index=round_id)
        assert aggregate.updated and aggregate.metadata.total_sample_count==train_n
        # Independent weighted first tensor check, with exact contributing counts.
        expected=sum(u['weights'][0].astype(np.float64)*u['sample_count'] for u in updates if u['sample_count'])/train_n
        np.testing.assert_allclose(aggregate.weights[0],expected,rtol=1e-6,atol=1e-7)
        assert set(aggregate.metadata.skipped_zero_sample_vehicle_ids)==set(i for i,v in enumerate(indices) if len(v)==0)
        model.set_weights(aggregate.weights);del updates
        metrics,cm=evaluate(model,X[train_n:],M[train_n:],Y[train_n:]);history.append(dict(round=round_id+1,training_loss=float(np.mean(losses)),accuracy=metrics['accuracy'],cross_entropy=metrics['cross_entropy']))
        model.save(MODELS/'last.keras')
        if metrics['cross_entropy']<best:best=metrics['cross_entropy'];best_round=round_id+1;model.save(MODELS/'best.keras')
        pd.DataFrame(history).to_csv(OUT/'routing_training_history.csv',index=False)
        final_metadata=dict(rounds=round_id+1,active_train_participants=aggregate.metadata.participating_updates,zero_sample_excluded=list(aggregate.metadata.skipped_zero_sample_vehicle_ids),total_sample_count=train_n,sample_weighting='PASS',shapes='169->64->32->9',last_round_metrics=metrics)
        save('fedavg_validation.json',final_metadata);save('routing_validation_metrics.json',dict(initial_untrained=initial,last_fedavg=metrics))
        progress.write_text(json.dumps(dict(history=history,best_loss=best,best_round=best_round),indent=2)+'\n')
        print('ROUND COMPLETE '+json.dumps(history[-1]),flush=True)
    selected=load_final_policy(MODELS/'best.keras');metrics,cm=evaluate(selected,X[train_n:],M[train_n:],Y[train_n:])
    save('routing_validation_metrics.json',dict(initial_untrained=initial,selected_fedavg=metrics,best_round=best_round,last_fedavg=json.loads((OUT/'fedavg_validation.json').read_text())['last_round_metrics'],old_synthetic=dict(accuracy=.2923,majority=.3363,evaluation_basis='different controlled-synthetic validation; not a like-for-like improvement claim')))
    pd.DataFrame(cm,index=range(9),columns=range(9)).rename_axis('true_action').to_csv(OUT/'routing_confusion_matrix.csv')
    pd.DataFrame(dict(action=range(9),total_support=support,train_support=np.bincount(Y[:train_n],minlength=9),validation_support=metrics['action_support'],prediction_count=metrics['predicted_counts'])).to_csv(OUT/'routing_action_support.csv',index=False)
    status=dict(SIMULATOR_ROUTING_POLICY_READY='YES',ROUTING_EFFECTIVENESS_CONCERN='YES' if metrics['ROUTING_EFFECTIVENESS_CONCERN'] else 'NO',status='SIMULATOR_DERIVED_ROUTING_BASELINE',checkpoint=str((MODELS/'best.keras').relative_to(ROOT)),old_checkpoint='PRESERVED; supersession for downstream training conditional on effectiveness review' if metrics['ROUTING_EFFECTIVENESS_CONCERN'] else 'SUPERSEDED_BY_SIMULATOR_DERIVED_ROUTING_MODEL',new_model_reloaded=True,invalid_actions=0)
    save('routing_checkpoint_status.json',status)
    print(json.dumps(status),flush=True)

if __name__=='__main__':main()
