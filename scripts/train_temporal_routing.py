"""Chronological, client-local buffered routing learning; offline contract test."""
from pathlib import Path
import os,json,pickle,hashlib,random
os.environ.setdefault('TF_DETERMINISTIC_OPS','1')
import numpy as np,pandas as pd,tensorflow as tf
from src.routing.learning import build_routing_policy_model,RoutingLearningParameters
from scripts.experiment_fedavg_protocols import evaluate
R=Path(__file__).resolve().parents[1];OLD=R/'models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42';MD=R/'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42';O=R/'results/analysis/2026-10-31_temporal_federated_routing';DIAG=R/'results/analysis/2026-10-30_routing_effectiveness_diagnosis'
SHAPES=((169,64),(64,),(64,32),(32,),(32,9),(9,));CUT=np.r_[0,np.cumsum([np.prod(s) for s in SHAPES])];P=int(CUT[-1])
def flatten(w):return np.concatenate([a.ravel() for a in w])
def unpack(w):return [w[CUT[k]:CUT[k+1]].reshape(s) for k,s in enumerate(SHAPES)]
def save(p,v):
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(p)
@tf.function(reduce_retracing=True)
def local_step(global_flat,x,mask,y,valid,m,v,iterations):
 """Independent client Adam steps batched for execution only; no cross-client loss."""
 c=tf.shape(x)[0];w=tf.broadcast_to(global_flat[None,:],[c,P])
 with tf.GradientTape() as tape:
  tape.watch(w);ws=[tf.reshape(w[:,CUT[k]:CUT[k+1]],[-1,*s]) for k,s in enumerate(SHAPES)]
  h=tf.nn.relu(tf.einsum('cbi,cij->cbj',x,ws[0])+ws[1][:,None,:]);h=tf.nn.relu(tf.einsum('cbi,cij->cbj',h,ws[2])+ws[3][:,None,:]);z=tf.einsum('cbi,cij->cbj',h,ws[4])+ws[5][:,None,:];z=tf.where(mask,z,tf.constant(-1e9,tf.float32));loss=tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y,logits=z);per=tf.reduce_sum(loss*valid,axis=1)/tf.reduce_sum(valid,axis=1);total=tf.reduce_sum(per)
 g=tape.gradient(total,w);m=m+(g-m)*tf.constant(.1,tf.float32);v=v+(tf.square(g)-v)*tf.constant(.001,tf.float32);t=tf.cast(iterations+1,tf.float32)[:,None];alpha=.001*tf.sqrt(1-tf.pow(.999,t))/(1-tf.pow(.9,t));new=w-(m*alpha)/(tf.sqrt(v)+1e-7)
 return new,m,v,per

def update_slot(slot,weights,mom,vel,it,history,ids,slots,X,M,Y,batch_clients=64):
 left,right=np.searchsorted(slots,[slot,slot+1]);positions=np.arange(left,right);clients=np.unique(ids[positions]);assert len(clients)>0
 for pos in positions:
  i=int(ids[pos]);history[i].append(int(pos));history[i]=history[i][-1000:]
 sums=np.zeros(P,np.float64);loss_sum=0.;examples=0;maxsource=-1
 for start in range(0,len(clients),batch_clients):
  group=clients[start:start+batch_clients];selected=[history[int(i)][-32:] for i in group];length=np.array([len(a) for a in selected]);idx=np.zeros((len(group),32),np.int64);valid=np.zeros((len(group),32),np.float32)
  for j,ind in enumerate(selected):idx[j,:len(ind)]=ind;idx[j,len(ind):]=ind[-1];valid[j,:len(ind)]=1
  assert (slots[idx]<=slot).all() and (ids[idx]==group[:,None]).all();maxsource=max(maxsource,int(slots[idx].max()))
  new,m,v,loss=local_step(tf.constant(weights),tf.constant(X[idx]),tf.constant(M[idx]),tf.constant(Y[idx]),tf.constant(valid),tf.constant(mom[group]),tf.constant(vel[group]),tf.constant(it[group]));new=new.numpy();assert np.isfinite(new).all();sums+=new.astype(np.float64).sum(0);mom[group]=m.numpy();vel[group]=v.numpy();it[group]+=1;loss_sum+=float(np.sum(loss.numpy()*length));examples+=int(length.sum())
 new=(sums/len(clients)).astype(np.float32)
 return new,dict(slot=slot,participants=len(clients),current_slot_experiences=len(positions),local_examples=examples,clients_without_current_experience=5000-len(clients),clients_with_zero_usable_experience=0,aggregation_weight_total=len(clients),max_source_slot=maxsource,model_available_slot=slot+1,global_update_norm=float(np.linalg.norm(new.astype(float)-weights)),training_CE=loss_sum/examples)

def main():
 O.mkdir(parents=True,exist_ok=True);MD.mkdir(parents=True,exist_ok=True);tf.keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
 X,M,Y,I=[np.load(OLD/'validated_cache'/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']];slots=np.load(DIAG/'metadata.npz')['slot'];assert len(Y)==3303289 and (slots[:2656632]<576).all() and (slots[2656632:]>=576).all()
 model=build_routing_policy_model(RoutingLearningParameters(),seed=42);initial=model.get_weights();weights=flatten(initial);sha=hashlib.sha256(weights.tobytes()).hexdigest();expected=json.loads((R/'results/analysis/2026-10-30_fedavg_protocol_correction/protocol_variants.json').read_text())['initialization_weights_sha256'];assert sha==expected
 model.save(MD/'initial.keras');sem=dict(interpretation='TEMPORAL_ACCUMULATED_LOCAL_HISTORY',buffer_capacity=1000,batch='latest32 from bounded localhistory includingcurrent slot',participation='only clients contributing current-slot observations',weighting='equal eligible client; payload sample_count=1 per main_slot.py and roadmapparagraph204',optimizer='persistent client-local Adam moments and iteration acrossslots; modelweights reset fromglobal eachslot',learning_rate=.001,batch_size=32,local_epochs=1,initialization_hash=sha,source=['src/routing/learning.py:LocalObservationBuffer.latest/train_for_slot/reset_from_global_weights','src/simulation/main_slot.py:235–259','Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx paragraphs187–215'],privacy_boundary='Single-process offline emulation of private clientstores; aggregator receives onlyweights/unitcounts. No distributedprivacy guarantee; no privatefeatures added.',execution='Independent client models computed in batched tensoroperations; focused numerical equivalence test against KerasAdam required.')
 save(O/'temporal_learning_semantics.json',sem);save(O/'methodology_contract.json',dict(PUBLIC_ROUTING_STATE_CONTRACT_VALIDATED='YES',state_dimension=169,mask_dimension=9,global_target='mean routingresponse frompublicgridstatistics',private_utility_decision_unchanged=True,document='notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx',paragraphs={'187':'meanresponse without centrally collectingpreferences','188':'public candidate triples andglobal H_hat','199':'actual decisions utility-governed','201':'localexperiences and parameteruploads','204':'equaleligibleclient aggregation'},old_offline_experiment='diagnostic baseline; not sequential temporalcontract',train_slots=576,validation_slots=144))
 progress=MD/'resume.pkl';start=0;rows=[];days=[];history=[[] for _ in range(5000)];mom=np.zeros((5000,P),np.float32);vel=np.zeros_like(mom);it=np.zeros(5000,np.int64)
 if progress.exists():
  state=pickle.loads(progress.read_bytes());assert state['initialization_hash']==sha;weights=state['weights'];mom=state['mom'];vel=state['vel'];it=state['iterations'];history=state['history'];start=state['next_slot'];rows=state['rows'];days=state['days'];random.setstate(state['python_rng']);np.random.set_state(state['numpy_rng'])
 resume_verified=False
 # Fixed development slice is first512 March1 00:00 rows, available before firstdayevaluation.
 dev=np.flatnonzero(slots==0)[:512]
 for slot in range(start,576):
  weights,row=update_slot(slot,weights,mom,vel,it,history,I,slots,X,M,Y);row['timestamp']=str(pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*slot));rows.append(row)
  if (slot+1)%48==0:
   model.set_weights(unpack(weights));metric=evaluate(model,X[dev],M[dev],Y[dev],initial,'TEMPORAL',slot+1);days.append(metric);pd.DataFrame(days).to_csv(O/'development_metrics.csv',index=False)
  if (slot+1)%16==0 or slot==575:
   model.set_weights(unpack(weights));model.save(MD/f'global_after_slot_{slot+1:03d}.keras');state=dict(initialization_hash=sha,next_slot=slot+1,weights=weights,mom=mom,vel=vel,iterations=it,history=history,rows=rows,days=days,python_rng=random.getstate(),numpy_rng=np.random.get_state(),tensorflow_rng='No stochastic training operations; deterministic dense/ReLU/Adam; seed42 initialization persisted')
   temp=progress.with_suffix('.tmp');temp.write_bytes(pickle.dumps(state,protocol=5));temp.replace(progress)
   pd.DataFrame(rows).to_csv(O/'training_progress.csv',index=False);pd.DataFrame(rows)[['slot','timestamp','participants','current_slot_experiences','local_examples','clients_without_current_experience','clients_with_zero_usable_experience','aggregation_weight_total']].to_csv(O/'slot_participation_summary.csv',index=False)
   print('CHECKPOINT',slot+1,'CE',row['training_CE'],flush=True)
   if not resume_verified and slot==15:
    # Replay nextslot from independently loaded savedstate; discard both probes, no effect ontraining.
    loaded=pickle.loads(progress.read_bytes());a=update_slot(slot+1,weights,mom.copy(),vel.copy(),it.copy(),[h.copy() for h in history],I,slots,X,M,Y)[0];b=update_slot(slot+1,loaded['weights'],loaded['mom'],loaded['vel'],loaded['iterations'],loaded['history'],I,slots,X,M,Y)[0];np.testing.assert_array_equal(a,b);save(O/'checkpoint_validation.json',dict(status='PASS',checkpoint_slot=16,replayed_update_slot=16,next_model_slot=17,global_weights_bit_exact=True,optimizer_and_buffers_restored=True,validation_updates=0,checkpoint_policy='globalmodel every16slots/day; full resumable state latestcheckpoint only; no stochastic operations afterseededinit'));resume_verified=True
 model.set_weights(unpack(weights));final=MD/'final_march12.keras';model.save(final);metric=evaluate(model,X[2656632:],M[2656632:],Y[2656632:],initial,'TEMPORAL',576);save(O/'final_validation.json',metric);print('COMPLETE',json.dumps(metric),flush=True)
if __name__=='__main__':main()
