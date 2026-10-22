"""Single seeded controlled routing-only baseline; no empirical simulator claims."""
import os
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
from pathlib import Path
import json,shutil
import numpy as np,pandas as pd,geopandas as gpd
import tensorflow as tf
from types import SimpleNamespace
from src.routing.configuration import configured_interfaces,CONTRACT
from src.routing.final_state import RoutingState
from src.routing.learning import LocalRoutingLearner,RoutingLearningParameters,build_routing_policy_model,masked_softmax,load_final_policy
from src.routing.baseline import ACTION_ORDER
from src.routing.federated import aggregate_policy_updates
from src.dispatch.request import RequestStatus

out=Path('results/analysis/2026-10-20_final_routing_policy');modeldir=Path('models/routing_policy/jan_mar_2026_3km_169x64x32x9')
if (out/'training_metrics.json').exists():raise SystemExit('Completed run exists; refusing implicit rerun.')
modeldir.mkdir(parents=True,exist_ok=True)
tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
rng=np.random.default_rng(42);base=Path('data/processed/spatial_3km_jan_mar_2026')
grid=gpd.read_parquet('data/processed/grid_lookup.parquet');neighbours=pd.read_parquet(base/'neighbour_map.parquet');stations=pd.read_parquet(base/'charging_stations.parquet')
producer,routing=configured_interfaces(grid,neighbours,stations,'2026-02-01')
params=RoutingLearningParameters(); samples=[];fixture=[]
# Twelve half-hour slots; two private profiles per grid, synthetic outcomes explicitly.
for slot in range(12):
    now=producer.timestamp
    for g in range(142):
        for profile in range(2):
            energy=60. if profile==0 else 30.
            decision=routing.decide(producer,now,grid=g,energy_kwh=energy,minimum_energy_kwh=30.,p_min=float(rng.uniform(10,35)),w_max_minutes=float(rng.uniform(5,30)),h_max_minutes=float(rng.uniform(5,30)),energy_per_km=.15)
            state=RoutingState.from_producer(routing,producer,now,g)
            label=routing.label(decision,g);assert state.mask[label]
            samples.append((slot,g%3,state,label))
            if g<2:fixture.append(dict(slot=slot,timestamp=str(now),Grid_ID=g,branch=decision.branch,label=label,next_grid=decision.next_grid,final_grid=decision.final_grid,mu=producer.state_for(now).iloc[g].mu,F_hat=producer.state_for(now).iloc[g].F_hat))
    requests=[]
    for g in range(142):
        for _ in range(int(rng.integers(0,8))):
            requests.append(SimpleNamespace(origin_grid=g,status=RequestStatus.ASSIGNED,assigned_vehicle_id=1,offered_fare=float(rng.uniform(5,55))))
    waits={int(g):float(rng.uniform(0,20)) for g in stations.grid_id.unique()}
    producer.complete_slot(slot_start=now,completed_at=now+pd.Timedelta(minutes=30),requests=requests,charging_waits=waits)
train=[s for s in samples if s[0]<8];valid=[s for s in samples if s[0]>=8]
X=np.stack([s[2].values for s in valid]);masks=np.stack([s[2].mask for s in valid]);y=np.array([s[3] for s in valid])
def evaluate(model):
    logits=model(X,training=False).numpy();probs=np.stack([masked_softmax(l,m) for l,m in zip(logits,masks)])
    pred=probs.argmax(1);assert np.isfinite(probs).all() and np.allclose(probs.sum(1),1)
    assert np.all(probs[~masks]==0)
    # Stable masked log-softmax for loss, avoiding probability-underflow clipping.
    masked=np.where(masks,logits.astype(float),-np.inf);mx=masked.max(1)
    loss=np.mean(mx+np.log(np.exp(masked-mx[:,None]).sum(1))-masked[np.arange(len(y)),y])
    return dict(accuracy=float(np.mean(pred==y)),cross_entropy=float(loss),invalid_action_count=int(np.sum(~masks[np.arange(len(y)),pred])),valid_action_prediction_rate=float(np.mean(masks[np.arange(len(y)),pred]))),pred
model=build_routing_policy_model(params,seed=42);history=[];best=float('inf');last=None
# One fixed five-round FedAvg run, unchanged Adam/.001/batch32/local_epochs1.
for round_id in range(5):
    updates=[];losses=[]
    for client in range(4):
        learner=LocalRoutingLearner(client,params,seed=42+client)
        learner.reset_from_global_weights(model.get_weights())
        local=[s for s in train if s[1]==client]
        for step,start in enumerate(range(0,len(local),32)):
            batch=local[start:start+32]
            from src.routing.learning import LocalObservationBuffer
            learner.observations=LocalObservationBuffer(params.local_observation_capacity)
            for _,_,state,label in batch:learner.record_observation(state,ACTION_ORDER[label])
            losses.append(learner.train_for_slot(step))
        updates.append(learner.export_local_update())
    last=aggregate_policy_updates(updates,round_index=round_id);model.set_weights(last.weights)
    metrics,_=evaluate(model);history.append(dict(round=round_id+1,training_loss=float(np.mean(losses)),**metrics))
    if metrics['cross_entropy']<best:
        best=metrics['cross_entropy'];model.save(modeldir/'best.keras')
    print('round',round_id+1,metrics,flush=True)
model.save(modeldir/'last.keras');loaded=load_final_policy(modeldir/'best.keras');metrics,pred=evaluate(loaded)
counts=np.bincount(y,minlength=9);predcounts=np.bincount(pred,minlength=9)
metrics.update(training_samples=len(train),validation_samples=len(valid),total_samples=len(samples),best_round=int(min(history,key=lambda r:r['cross_entropy'])['round']),seed=42,experience_source='controlled synthetic routing-only fixture, NOT empirical fleet outcomes',validation_design='chronologically later fixture slots; best checkpoint selected on this validation set, no independent test claim',severe_prediction_dominance=bool(predcounts.max()/len(y)>.9),majority_label_accuracy=float(counts.max()/len(y)),routing_policy_ready=True)
pd.DataFrame(history).to_csv(out/'training_history.csv',index=False)
pd.DataFrame(dict(action=range(9),name=[a.value for a in ACTION_ORDER],train_count=np.bincount([s[3] for s in train],minlength=9),validation_count=counts,predicted_count=predcounts)).to_csv(out/'action_support.csv',index=False)
cm=np.zeros((9,9),int);np.add.at(cm,(y,pred),1);pd.DataFrame(cm,index=range(9),columns=range(9)).rename_axis('true_action').to_csv(out/'confusion_matrix.csv')
pd.DataFrame(fixture).to_csv(out/'routing_fixture.csv',index=False)
(out/'training_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(out/'fedavg_validation.json').write_text(json.dumps(dict(rounds=5,participants=3,zero_sample_excluded=list(last.metadata.skipped_zero_sample_vehicle_ids),sample_count=last.metadata.total_sample_count,architecture=[169,64,32,9],aggregated_model_reloaded=True,probabilities_valid=True),indent=2)+'\n')
cfg=json.loads(CONTRACT.read_text());cfg['training']={'seed':42,'rounds':5,'optimizer':'Adam','learning_rate':.001,'batch_size':32,'local_epochs':1,'data_description':'12 synthetic slots, first8 train, last4 validation; 142 grids times2 private profiles','cost_normalizer_metres':float(3000*np.sqrt(2))}
(out/'routing_config.json').write_text(json.dumps(cfg,indent=2)+'\n')
for source,name in [(out/'routing_config.json','training_configuration.json'),(out/'training_history.csv','training_history.csv'),(CONTRACT.parent/'policy_state_spec.json','state_specification.json'),(Path('results/analysis/2026-10-20_driver_ev_routing_state/action_mapping.json'),'action_specification.json')]:shutil.copyfile(source,modeldir/name)
print(json.dumps(metrics),flush=True)
