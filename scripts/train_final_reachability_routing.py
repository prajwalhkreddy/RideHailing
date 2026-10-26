"""Frozen central one-epoch baseline plus five driver-client plain FedAvg rounds."""
from pathlib import Path
import os,sys,json,hashlib,pickle
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np,pandas as pd,pyarrow.parquet as pq,tensorflow as tf
from src.routing.learning import RoutingLearningParameters,LocalRoutingLearner,build_routing_policy_model,load_final_policy
from src.routing.federated import aggregate_policy_updates
from src.simulation.temporal_protocol import assert_training_update_allowed
from scripts.train_simulator_routing_policy import evaluate
OUT=ROOT/'results/analysis/2026-10-25_final_simulator_routing_training'
DATA=ROOT/'data/processed/routing_experiences_mar01_mar15_2026_reachability'
MODEL=ROOT/'models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42'
CACHE=MODEL/'validated_cache'

def save(name,obj):
 p=OUT/name;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(obj,indent=2,default=str)+'\n');t.replace(p)
def progress(p,obj):
 t=p.with_suffix('.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(p)
def validate():
 OUT.mkdir(parents=True,exist_ok=True);MODEL.mkdir(parents=True,exist_ok=True);CACHE.mkdir(exist_ok=True)
 report=ROOT/'results/analysis/2026-10-25_routing_generation_reachability'
 status=json.loads((report/'generation_status.json').read_text());assert status['status']=='COMPLETE' and status['completed_slots']==720 and status['experiences']==3257840
 paths=[DATA/f'slot_{i:04d}.parquet' for i in range(720)];assert all(p.exists() for p in paths)
 assert len(list(DATA.glob('slot_*.parquet')))==720
 signature=[(p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
 fingerprint=hashlib.sha256(json.dumps(signature).encode()).hexdigest()
 if (OUT/'dataset_validation.json').exists():
  meta=json.loads((OUT/'dataset_validation.json').read_text());assert meta['source_fingerprint']==fingerprint
  return meta
 n=3257840
 arrays={k:np.lib.format.open_memmap(CACHE/f'{k}.npy',mode='w+',dtype=dtype,shape=shape) for k,dtype,shape in [('X','float32',(n,169)),('M','bool',(n,9)),('Y','int32',(n,)),('IDS','int32',(n,))]}
 counts=np.zeros(5000,np.int64);support=np.zeros((2,9),np.int64);kinds={};drivers={};offset=0;train_n=0;hashes={}
 for i,p in enumerate(paths):
  t=pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*i);assert_training_update_allowed(t)
  f=pq.read_table(p).to_pandas();size=len(f)
  assert (f.timestamp==t).all() and t<pd.Timestamp('2026-03-16')
  assert np.array_equal(f.experience_id.to_numpy(),np.arange(offset,offset+size))
  x=np.stack(f.state_169);m=np.stack(f.action_mask_9);y=f.label_action_0_to_8.to_numpy();ids=f.driver_id.to_numpy()
  assert x.shape==(size,169) and m.shape==(size,9) and m.dtype==bool and np.isfinite(x).all() and m.any(1).all()
  assert np.issubdtype(y.dtype,np.integer) and ((y>=0)&(y<9)).all() and m[np.arange(size),y].all()
  assert ((ids>=0)&(ids<5000)).all() and np.issubdtype(ids.dtype,np.integer) and f.current_grid.between(0,141).all()
  assert (x[:,:27].reshape(-1,9,3)[~m]==0).all()
  assert set(f.decision_type)<= {'REPOSITION','EV_CHARGING_NEXT_HOP'}
  for k,v in [('X',x),('M',m),('Y',y),('IDS',ids)]:arrays[k][offset:offset+size]=v
  counts+=np.bincount(ids,minlength=5000);support[int(i>=576)]+=np.bincount(y,minlength=9)
  for kind,group in f.groupby('decision_type'):
   kinds[kind]=kinds.get(kind,0)+len(group);drivers.setdefault(kind,set()).update(group.driver_id)
  if i<576:train_n+=size
  offset+=size;hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 assert offset==n
 for a in arrays.values():a.flush()
 del arrays
 cp=DATA/'generation_checkpoint.pkl';manifest=json.loads((report/'generation_checkpoint_manifest.json').read_text());assert hashlib.sha256(cp.read_bytes()).hexdigest()==manifest['checkpoint_sha256']
 d=pickle.loads(cp.read_bytes());assert d['reachability_contract']=='EV_POST_MOVEMENT_STATION_REACHABILITY' and len(d['fleet'].vehicles)==5000
 assert len({v.vehicle_id for v in d['fleet'].vehicles})==5000
 assert all(r['fleet_size']==5000 and r['training'] is None and r['replay_size']==0 and r['federated_updates']==0 for r in d['reports'])
 meta=dict(status='PASS',source_fingerprint=fingerprint,experiences=n,slots=720,train_n=train_n,validation_n=n-train_n,duplicate_ids=0,invalid_labels=0,finite_states=True,state_dimension=169,mask_dimension=9,fleet=5000,decision_types=kinds,decision_type_drivers={k:len(v) for k,v in drivers.items()},real_requests=sum(r['requests'] for r in d['reports']),assignments=sum(r['assigned'] for r in d['reports']),partition_sha256=hashes)
 save('dataset_validation.json',meta)
 active=counts[counts>0];save('participant_distribution.json',dict(active=len(active),zero=int((counts==0).sum()),min=int(active.min()),median=float(np.median(active)),mean=float(active.mean()),max=int(active.max()),counts_by_driver=counts.tolist()))
 save('routing_split.json',dict(train_start='2026-03-01 00:00',train_end='2026-03-12 23:30',train_slots=576,train_experiences=train_n,validation_start='2026-03-13 00:00',validation_end='2026-03-15 23:30',validation_slots=144,validation_experiences=n-train_n,random_split=False))
 total=support.sum(0);pd.DataFrame(dict(action=range(9),name=['STAY','N','NE','E','SE','S','SW','W','NW'],total=total,percentage=100*total/n,train=support[0],validation=support[1])).to_csv(OUT/'routing_action_support.csv',index=False)
 print(json.dumps({k:v for k,v in meta.items() if k!='partition_sha256'}),flush=True);return meta

def compiled_step(model,optimizer):
 @tf.function(input_signature=[tf.TensorSpec([None,169],tf.float32),tf.TensorSpec([None,9],tf.bool),tf.TensorSpec([None],tf.int32)])
 def step(x,m,y):
  with tf.GradientTape() as tape:
   logits=tf.where(m,model(x,training=True),tf.constant(-1e9,tf.float32))
   loss=tf.reduce_mean(tf.keras.losses.sparse_categorical_crossentropy(y,logits,from_logits=True))
  optimizer.apply_gradients(zip(tape.gradient(loss,model.trainable_variables),model.trainable_variables))
  return loss
 return step

def main():
 meta=validate();n=meta['train_n'];X,M,Y,IDS=[np.load(CACHE/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']]
 params=RoutingLearningParameters();assert (params.learning_rate,params.batch_size,params.local_epochs,params.hidden_units)==(.001,32,1,(64,32))
 save('routing_training_config.json',dict(input_dimension=169,hidden_units=[64,32],output_dimension=9,action_order=['STAY','N','NE','E','SE','S','SW','W','NW'],optimizer='Adam',learning_rate=.001,batch_size=32,seed=42,central_epochs=1,central_epoch_rationale='existing one-epoch supervised default; one chronological pass, no search',local_epochs=1,fedavg_rounds=5,local_optimizer='fresh Adam state per driver each round',sample_weighted=True,client='driver_id',normalization='unchanged',rebalance=False,training_order='chronological; no shuffle',selection='final fifth global FedAvg aggregate; central model reported separately',material_support_threshold=.01,catastrophic_collapse_rule='largest prediction share>90% while corresponding true share<90%',cache='disk-mapped arrays; one source partition in memory during validation'))
 tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
 central_path=MODEL/'central.keras';central_progress=MODEL/'central_progress.json'
 if not central_path.exists():
  central=build_routing_policy_model(params,seed=42);opt=tf.keras.optimizers.Adam(.001);central.compile(optimizer=opt);opt.build(central.trainable_variables);start=0;loss_sum=0.
  if central_progress.exists():
   pr=json.loads(central_progress.read_text());central=tf.keras.models.load_model(MODEL/pr['checkpoint']);opt=central.optimizer;start=pr['next_row'];loss_sum=pr['loss_sum']
  step=compiled_step(central,opt)
  for j in range(start,n,32):
   stop=min(j+32,n);loss=float(step(X[j:stop],M[j:stop],Y[j:stop]).numpy());assert np.isfinite(loss);loss_sum+=loss*(stop-j)
   if (j//32+1)%10000==0 or stop==n:
    name=f'central_progress_{stop}.keras';central.save(MODEL/name);progress(central_progress,dict(next_row=stop,loss_sum=loss_sum,checkpoint=name));print('CENTRAL '+str(stop)+'/'+str(n),flush=True)
  central.save(central_path);pd.DataFrame([dict(epoch=1,examples=n,training_loss=loss_sum/n)]).to_csv(OUT/'routing_training_history.csv',index=False)
 central=load_final_policy(central_path);central_metrics,central_cm=evaluate(central,X[n:],M[n:],Y[n:]);save('central_validation.json',central_metrics)
 # Stable driver grouping preserves each driver's chronological row order.
 order=np.argsort(IDS[:n],kind='stable');client_counts=np.bincount(IDS[:n],minlength=5000);bounds=np.r_[0,np.cumsum(client_counts)]
 model=build_routing_policy_model(params,seed=42);learner=LocalRoutingLearner(0,params,seed=42);learner.optimizer.build(learner.policy_model.trainable_variables);initial_opt=[v.numpy().copy() for v in learner.optimizer.variables];step=compiled_step(learner.policy_model,learner.optimizer)
 history=[];pr_path=MODEL/'fedavg_progress.json'
 if pr_path.exists():
  pr=json.loads(pr_path.read_text());history=pr['history'];model=load_final_policy(MODEL/pr['checkpoint'])
 for round_i in range(len(history),5):
  weights=model.get_weights();updates=[];loss_sum=0.
  # Completed-client files make interrupted rounds resumable without replaying clients.
  round_dir=MODEL/f'round_{round_i+1}_client_progress';round_dir.mkdir(exist_ok=True)
  for client in range(5000):
   saved=round_dir/f'{client:04d}.pkl'
   if saved.exists():
    u,l=pickle.loads(saved.read_bytes());updates.append(u);loss_sum+=l;continue
   learner.vehicle_id=client;learner.local_sample_count=int(client_counts[client]);learner.reset_from_global_weights(weights)
   for variable,value in zip(learner.optimizer.variables,initial_opt):variable.assign(value)
   positions=order[bounds[client]:bounds[client+1]];local_loss=0.
   for j in range(0,len(positions),32):
    idx=positions[j:j+32];loss=float(step(X[idx],M[idx],Y[idx]).numpy());assert np.isfinite(loss);local_loss+=loss*len(idx)
   update=learner.export_local_update();updates.append(update);loss_sum+=local_loss
   temp=saved.with_suffix('.tmp');temp.write_bytes(pickle.dumps((update,local_loss),protocol=5));temp.replace(saved)
  aggregate=aggregate_policy_updates(updates,round_index=round_i);assert aggregate.updated and aggregate.metadata.total_sample_count==n
  assert set(aggregate.metadata.skipped_zero_sample_vehicle_ids)==set(np.where(client_counts==0)[0])
  for k,w in enumerate(aggregate.weights):
   expected=sum(u['weights'][k].astype(np.float64)*u['sample_count'] for u in updates if u['sample_count'])/n
   np.testing.assert_allclose(w,expected,rtol=1e-6,atol=1e-7)
  model.set_weights(aggregate.weights);del updates
  metrics,cm=evaluate(model,X[n:],M[n:],Y[n:]);name=f'fedavg_round_{round_i+1}.keras';model.save(MODEL/name)
  reloaded=load_final_policy(MODEL/name);np.testing.assert_allclose(reloaded(X[n:n+32],training=False).numpy(),model(X[n:n+32],training=False).numpy(),rtol=0,atol=0)
  row=dict(round=round_i+1,active_participants=aggregate.metadata.participating_updates,training_examples=n,training_loss=loss_sum/n,accuracy=metrics['accuracy'],cross_entropy=metrics['cross_entropy']);history.append(row)
  pd.DataFrame(history).to_csv(OUT/'fedavg_round_metrics.csv',index=False);progress(pr_path,dict(history=history,checkpoint=name));save('fedavg_validation.json',dict(rounds=round_i+1,sample_weighting='PASS all tensors',zero_sample_excluded=len(aggregate.metadata.skipped_zero_sample_vehicle_ids),checkpoint_reload='PASS',final_metrics=metrics));print('FEDAVG '+json.dumps(row),flush=True)
 final=load_final_policy(MODEL/'fedavg_round_5.keras');fm,fcm=evaluate(final,X[n:],M[n:],Y[n:])
 for metric in [central_metrics,fm]:
  metric['STAY_true_share']=metric['action_support'][0]/metric['N'];metric['largest_predicted_class_share']=max(metric['predicted_counts'])/metric['N'];metric['material_supported_zero_prediction_actions']=[i for i in range(9) if metric['action_support'][i]/metric['N']>=.01 and metric['predicted_counts'][i]==0]
 save('routing_validation_metrics.json',dict(central=central_metrics,final_fedavg=fm,synthetic_provenance=dict(accuracy=.2923,cross_entropy=1.82917,majority=.3363,STAY_prediction_share=.6144,comparison='different dataset; no direct superiority inference')))
 frames=[]
 for label,cm in [('central',central_cm),('fedavg_round5',fcm)]:
  frame=pd.DataFrame(cm,columns=[f'predicted_{i}' for i in range(9)]);frame.insert(0,'true_action',range(9));frame.insert(0,'model',label);frames.append(frame)
 pd.concat(frames).to_csv(OUT/'routing_confusion_matrix.csv',index=False)
 save('routing_model_selection.json',dict(FINAL_SIMULATOR_ROUTING_MODEL_READY='YES',status='SIMULATOR_DERIVED_ROUTING_BASELINE',checkpoint=str((MODEL/'fedavg_round_5.keras').relative_to(ROOT)),rationale='Final valid global fifth-round aggregate required by hierarchical/federated design; central accuracy does not override it.',ROUTING_EFFECTIVENESS_CONCERN='YES' if fm['ROUTING_EFFECTIVENESS_CONCERN'] else 'NO',old_synthetic_status=['SUPERSEDED_FOR_FINAL_NON_PRIVATE_TRAINING','PROVENANCE_ONLY'],runtime_activation='Selection recorded; pricing training not launched; legacy hard-coded runtime loading not changed in this training task.'))
 print('TRAINING COMPLETE',flush=True)
if __name__=='__main__':main()
