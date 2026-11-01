"""Frozen B/C/D local-work experiment; no production activation or data generation."""
from pathlib import Path
import os,json,pickle,hashlib
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
import numpy as np,pandas as pd,tensorflow as tf
from src.routing.learning import RoutingLearningParameters,build_routing_policy_model,load_final_policy
from scripts.train_final_behavioral_routing import compiled_step
R=Path(__file__).resolve().parents[1]
OLD=R/'models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42'
MD=R/'models/routing_policy/mar01_mar12_2026_final_behavioral_fedavg_protocols_seed42'
O=R/'results/analysis/2026-10-30_fedavg_protocol_correction'
DIAG=R/'results/analysis/2026-10-30_routing_effectiveness_diagnosis'
TRAIN=2656632;TOTAL=3303289

def save(path,value):
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def flat(weights):return np.concatenate([x.ravel().astype(np.float64) for x in weights])
def batch_positions(positions,client,round_index,cap):
 """Seeded unique per-round start, circular chronological window without duplicates."""
 count=len(positions)
 if not count:return []
 offsets=np.random.default_rng(np.random.SeedSequence([42,int(client)])).choice(count,min(5,count),replace=False)
 offset=int(offsets[(round_index-1)%len(offsets)])
 selected=positions[(offset+np.arange(min(count,32*cap)))%count]
 return [selected[i:i+32] for i in range(0,len(selected),32)]
def evaluate(model,X,M,Y,initial,variant,round_index):
 n=len(Y);ce=br=correct=move_correct=move_ce=0.;pred=np.zeros(9,np.int64);bins=np.zeros((10,3));invalid=0
 for b in range(0,n,8192):
  y=Y[b:b+8192];mask=M[b:b+8192];z=model(X[b:b+8192],training=False).numpy().astype(float);z=np.where(mask,z,-np.inf);p=np.exp(z-z.max(1)[:,None]);p/=p.sum(1)[:,None]
  assert np.isfinite(p).all() and np.allclose(p.sum(1),1) and (p[~mask]==0).all()
  chosen=p.argmax(1);t=p[np.arange(len(y)),y];loss=-np.log(t);ce+=loss.sum();br+=((p*p).sum(1)-2*t+1).sum();correct+=(chosen==y).sum();pred+=np.bincount(chosen,minlength=9);invalid+=int((~mask[np.arange(len(y)),chosen]).sum());move=y!=0;move_correct+=((chosen==y)&move).sum();move_ce+=loss[move].sum();conf=p.max(1);idx=np.minimum((conf*10).astype(int),9)
  for k in range(10):
   q=idx==k;bins[k]+=[q.sum(),conf[q].sum(),(chosen[q]==y[q]).sum()]
 nm=int((Y!=0).sum());ece=sum(abs(row[1]-row[2]) for row in bins)/n
 return dict(variant=variant,round=round_index,accuracy=float(correct/n),CE=float(ce/n),Brier=float(br/n),ECE=float(ece),STAY_predicted_share=float(pred[0]/n),non_STAY_accuracy=float(move_correct/nm),non_STAY_CE=float(move_ce/nm),true_counts=np.bincount(Y,minlength=9).tolist(),predicted_counts=pred.tolist(),invalid_action_violations=invalid,L2_from_initial=float(np.linalg.norm(flat(model.get_weights())-flat(initial))),validation_N=n)
def main():
 O.mkdir(parents=True,exist_ok=True);MD.mkdir(parents=True,exist_ok=True)
 X,M,Y,I=[np.load(OLD/'validated_cache'/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']]
 assert len(Y)==TOTAL and X.shape==(TOTAL,169) and M.shape==(TOTAL,9)
 meta=json.loads((R/'results/analysis/2026-10-30_final_behavioral_routing_training/dataset_validation.json').read_text());assert meta['train_n']==TRAIN and meta['validation_n']==646657
 params=RoutingLearningParameters();tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
 model=build_routing_policy_model(params,seed=42);initial=model.get_weights();initpath=MD/'initial.keras'
 if initpath.exists():
  saved=load_final_policy(initpath)
  for a,b in zip(initial,saved.get_weights()):np.testing.assert_array_equal(a,b)
 else:model.save(initpath)
 initsha=hashlib.sha256(b''.join(w.tobytes() for w in initial)).hexdigest()
 config=dict(seed=42,initialization_weights_sha256=initsha,initialization_checkpoint=str(initpath.relative_to(R)),initialization='Previous initialcheckpoint not persisted; reconstructed using same modelbuilder seed42; shared bit-identical B/C/D. Control A uses that documented original seed42 initialization.',train_N=TRAIN,validation_N=646657,architecture=[169,64,32,9],loss='unchanged masked mean multiclass crossentropy',lr=.001,batch_size=32,rounds=5,weighting='full client TRAIN count, not minibatch size',batch_rule='round-dependent seed42/client offsets sampled without replacement; rotate chronological client sequence; take first32 for B, up to160 for C/D; final partialbatch allowed; no duplicate within round; C and D identical batches',variants={'A':'existing Adam/full localepoch/fresh perclient; reuse','B':'Adam freshperclient, exactly1batch','C':'Adam freshperclient, at most5batches','D':'SGD momentum0, at most5batches'},production_changed=False)
 save(O/'protocol_variants.json',config)
 order=np.argsort(I[:TRAIN],kind='stable');counts=np.bincount(I[:TRAIN],minlength=5000);bounds=np.r_[0,np.cumsum(counts)];assert counts.sum()==TRAIN and (counts>0).all()
 for variant,cap in [('B',1),('C',5),('D',5)]:
  local=build_routing_policy_model(params,seed=42);opt=tf.keras.optimizers.SGD(.001,momentum=0.) if variant=='D' else tf.keras.optimizers.Adam(.001);opt.build(local.trainable_variables);fresh=[x.numpy().copy() for x in opt.variables];step=compiled_step(local,opt);weights=[x.copy() for x in initial]
  for round_index in range(1,6):
   checkpoint=MD/f'{variant}_round_{round_index}.keras';done=O/f'{variant}_round_{round_index}.json';progress=MD/f'{variant}_round_{round_index}_progress.pkl'
   if done.exists():weights=load_final_policy(checkpoint).get_weights();continue
   sums=[np.zeros_like(w,dtype=np.float64) for w in weights];unit_sum=np.zeros_like(flat(weights));norm_sum=0.;step_counts=[];sample_total=0;start=0
   if progress.exists():
    state=pickle.loads(progress.read_bytes());assert state['initialization_hash']==initsha
    start=state['next_client'];sums=state['sums'];unit_sum=state['unit_sum'];norm_sum=state['norm_sum'];step_counts=state['step_counts'];sample_total=state['sample_total']
   for client in range(start,5000):
    local.set_weights(weights)
    for variable,value in zip(opt.variables,fresh):variable.assign(value)
    positions=order[bounds[client]:bounds[client+1]];batches=batch_positions(positions,client,round_index,cap)
    assert len(batches)==min(cap,int(np.ceil(counts[client]/32)))
    for idx in batches:
     loss=float(step(X[idx],M[idx],Y[idx]).numpy());assert np.isfinite(loss)
    updated=local.get_weights();delta=flat(updated)-flat(weights);norm=float(np.linalg.norm(delta));norm_sum+=norm
    if norm:unit_sum+=(delta/norm)*counts[client]
    for k,w in enumerate(updated):sums[k]+=w.astype(np.float64)*counts[client]
    sample_total+=int(counts[client]);step_counts.append(len(batches))
    if (client+1)%250==0:
     state=dict(initialization_hash=initsha,next_client=client+1,sums=sums,unit_sum=unit_sum,norm_sum=norm_sum,step_counts=step_counts,sample_total=sample_total)
     temp=progress.with_suffix('.tmp');temp.write_bytes(pickle.dumps(state,protocol=5));temp.replace(progress)
    if (client+1)%1000==0:print(variant,round_index,'clients',client+1,flush=True)
   assert sample_total==TRAIN and len(step_counts)==5000
   new=[(w/sample_total).astype(np.float32) for w in sums];model.set_weights(new);model.save(checkpoint);reloaded=load_final_policy(checkpoint);np.testing.assert_array_equal(model(X[TRAIN:TRAIN+32],training=False).numpy(),reloaded(X[TRAIN:TRAIN+32],training=False).numpy())
   metrics=evaluate(model,X[TRAIN:],M[TRAIN:],Y[TRAIN:],initial,variant,round_index);globaldelta=flat(new)-flat(weights);gnorm=np.linalg.norm(globaldelta)
   localsteps=dict(variant=variant,round=round_index,clients=5000,total_weight=sample_total,mean=float(np.mean(step_counts)),P10=float(np.quantile(step_counts,.1)),median=float(np.median(step_counts)),P90=float(np.quantile(step_counts,.9)),total_optimizer_steps=int(sum(step_counts)))
   update=dict(variant=variant,round=round_index,mean_local_update_L2=norm_sum/5000,global_update_L2=float(gnorm),weighted_mean_client_global_cosine=float(np.dot(unit_sum/sample_total,globaldelta/gnorm)) if gnorm else None)
   save(done,dict(metrics=metrics,local_steps=localsteps,update=update,checkpoint=str(checkpoint.relative_to(R))));weights=new
   print('ROUND COMPLETE',json.dumps(metrics),flush=True)
   collect()
 # Reuse A checkpoints/predictions and savedclientweights; no optimization.
 weights=initial
 for r in range(1,6):
  path=O/f'A_round_{r}.json'
  if path.exists():weights=load_final_policy(OLD/f'fedavg_round_{r}.keras').get_weights();continue
  amodel=load_final_policy(OLD/f'fedavg_round_{r}.keras');met=evaluate(amodel,X[TRAIN:],M[TRAIN:],Y[TRAIN:],initial,'A',r);new=amodel.get_weights();g=flat(new)-flat(weights);gn=np.linalg.norm(g);ns=0.;unit=np.zeros_like(g)
  for client in range(5000):
   u,_=pickle.loads((OLD/f'round_{r}_client_progress'/f'{client:04d}.pkl').read_bytes());delta=flat(u['weights'])-flat(weights);l=np.linalg.norm(delta);ns+=l
   if l:unit+=(delta/l)*u['sample_count']
  steps=np.ceil(counts/32);save(path,dict(metrics=met,local_steps=dict(variant='A',round=r,clients=5000,total_weight=TRAIN,mean=float(steps.mean()),P10=float(np.quantile(steps,.1)),median=float(np.median(steps)),P90=float(np.quantile(steps,.9)),total_optimizer_steps=int(steps.sum())),update=dict(variant='A',round=r,mean_local_update_L2=ns/5000,global_update_L2=float(gn),weighted_mean_client_global_cosine=float(np.dot(unit/TRAIN,g/gn))),checkpoint=str((OLD/f'fedavg_round_{r}.keras').relative_to(R))));weights=new;print('CONTROL REUSED',r,flush=True)
 collect();print('EXPERIMENT COMPLETE',flush=True)
def collect():
 records=[json.loads(p.read_text()) for p in sorted(O.glob('[ABCD]_round_*.json'))]
 for key,filename in [('metrics','round_metrics.csv'),('local_steps','local_step_diagnostics.csv'),('update','update_diagnostics.csv')]:
  frame=pd.DataFrame([r[key] for r in records]);frame.to_csv(O/filename,index=False)
if __name__=='__main__':main()
