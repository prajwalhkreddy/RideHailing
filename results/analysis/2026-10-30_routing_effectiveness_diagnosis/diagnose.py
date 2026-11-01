from pathlib import Path
import os,json,pickle
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import numpy as np,pandas as pd,pyarrow.parquet as pq
from scipy.special import rel_entr
from sklearn.metrics import roc_auc_score
from src.routing.learning import load_final_policy,build_routing_policy_model,RoutingLearningParameters
R=Path.cwd();O=R/'results/analysis/2026-10-30_routing_effectiveness_diagnosis';D=R/'data/processed/routing_experiences_mar01_mar15_2026_final_behavioral';MD=R/'models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42';T=R/'results/analysis/2026-10-30_final_behavioral_routing_training'
C=MD/'validated_cache';X,M,Y,I=[np.load(C/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']];n=2656632;N=len(Y);v=slice(n,None)
def save(name,obj):
 (O/name).write_text(json.dumps(obj,indent=2,default=lambda z:z.tolist() if hasattr(z,'tolist') else str(z))+'\n')
def stats(a):return dict(zip(['min','P10','median','mean','P90','P99','max'],[float(np.min(a)),float(np.quantile(a,.1)),float(np.median(a)),float(np.mean(a)),float(np.quantile(a,.9)),float(np.quantile(a,.99)),float(np.max(a))]))
def js(p,q):
 m=(p+q)/2;return (rel_entr(p,m).sum(-1)+rel_entr(q,m).sum(-1))/2
if not (O/'metadata.npz').exists():
 gs=[];ts=[];ss=[]
 for j in range(720):
  f=pq.read_table(D/f'slot_{j:04d}.parquet',columns=['current_grid','decision_type']).to_pandas();gs.append(f.current_grid.to_numpy());ts.append((f.decision_type=='EV_CHARGING_NEXT_HOP').to_numpy());ss.append(np.full(len(f),j,np.int16))
 np.savez(O/'metadata.npz',grid=np.concatenate(gs),kind=np.concatenate(ts),slot=np.concatenate(ss))
a=np.load(O/'metadata.npz');G=a['grid'];K=a['kind'];S=a['slot'];card=M.sum(1);pattern=(M*np.left_shift(1,np.arange(9))).sum(1).astype(int);prior=np.bincount(Y[:n],minlength=9)/n
# Saved inference only. Cache permits interruption recovery.
def predict(name,path,full=False):
 out=O/f'{name}_probabilities.npy';lo=0 if full else n
 if out.exists():return np.load(out,mmap_mode='r')
 model=load_final_policy(path);q=np.lib.format.open_memmap(out.with_suffix('.tmp.npy'),mode='w+',dtype='float64',shape=(N-lo,9))
 for b in range(lo,N,8192):
  e=min(N,b+8192);z=model(X[b:e],training=False).numpy().astype(float);z=np.where(M[b:e],z,-np.inf);z=np.exp(z-z.max(1)[:,None]);q[b-lo:e-lo]=z/z.sum(1)[:,None]
 q.flush();del q;out.with_suffix('.tmp.npy').replace(out);print('inference',name,flush=True);return np.load(out,mmap_mode='r')
pc=predict('central',MD/'central.keras',True);pf=predict('fedavg5',MD/'fedavg_round_5.keras',True)
pb=prior[None,:]*M;pb/=pb.sum(1)[:,None]
def losses(q,y):
 t=q[np.arange(len(y)),y]
 with np.errstate(divide='ignore'):ce=-np.log(t)
 return ce,(q*q).sum(1)-2*t+1
lc,bc=losses(pc,Y);lf,bf=losses(pf,Y);lb,bb=losses(pb,Y)
def metrics(q,y):
 ce,br=losses(q,y);conf=q.max(1);ok=q.argmax(1)==y;bins=[]
 for j in range(10):
  z=np.minimum((conf*10).astype(int),9)==j
  if z.any():bins.append(dict(lower=j/10,upper=(j+1)/10,N=int(z.sum()),confidence=float(conf[z].mean()),accuracy=float(ok[z].mean())))
 return dict(CE=float(ce.mean()),Brier=float(br.mean()),accuracy=float(ok.mean()),ECE=sum(b['N']*abs(b['confidence']-b['accuracy']) for b in bins)/len(y),mean_probability=q.mean(0),calibration=bins)
cm=metrics(pc[v],Y[v]);bm=metrics(pb[v],Y[v]);diff=np.array([[np.mean((lc-lb)[S==j]),np.mean((bc-bb)[S==j])] for j in range(576,720)]);dm=diff.mean(0);se=diff.std(0,ddof=1)/12
ver='YES' if cm['CE']<bm['CE'] and cm['Brier']<bm['Brier'] and (dm+1.96*se<0).all() else 'NO' if (dm-1.96*se>0).any() else 'INCONCLUSIVE'
save('central_probability_adequacy.json',dict(central=cm,prior=bm,CENTRAL_PROBABILITIES_INFORMATIVE=ver,paired_slot_mean=dm,paired_slot_SE=se,note='Same paired 144-slot descriptive uncertainty gate; independence assumption, no serial-dependence-adjusted inference.'))
mask={}
for name,z in [('train',np.arange(N)<n),('validation',np.arange(N)>=n)]:
 rows=[]
 for k in range(1,10):
  h=z&(card==k);rows.append(dict(cardinality=k,N=int(h.sum()),percentage=100*float(h.sum()/z.sum()),true_STAY_share=float((Y[h]==0).mean()) if h.any() else None,central_CE=float(lc[h].mean()) if h.any() else None,fedavg_CE=float(lf[h].mean()) if h.any() else None,prior_CE=float(lb[h].mean()) if h.any() else None))
 vals,cnt=np.unique(pattern[z],return_counts=True);order=np.argsort(-cnt)
 mask[name]=dict(cardinalities=rows,only_STAY=float((card[z]==1).mean()),STAY_one_move=float((card[z]==2).mean()),at_least_three=float((card[z]>=3).mean()),action_validity=M[z].mean(0),distinct_patterns=len(vals),top_patterns=[dict(bitmask=int(vals[j]),N=int(cnt[j])) for j in order[:15]])
mask['prior_mask_gain']=dict(unmasked_CE=float(-np.log(prior[Y[v]]).mean()),masked_CE=float(lb[v].mean()),unmasked_Brier=float(((prior**2).sum()-2*prior[Y[v]]+1).mean()),masked_Brier=float(bb[v].mean()))
save('mask_diagnostics.json',mask)
rows=[]
for k in range(9):
 z=Y[v]==k;rows.append(dict(action=k,train_N=int((Y[:n]==k).sum()),validation_N=int(z.sum()),train_share=float((Y[:n]==k).mean()),validation_share=float(z.mean()),central_true_probability=float(pc[v][z,k].mean()),fedavg_true_probability=float(pf[v][z,k].mean()),prior_true_probability=float(pb[v][z,k].mean())))
pd.DataFrame(rows).to_csv(O/'action_probability_diagnostics.csv',index=False)
extra={}
for name,q,loss in [('central',pc,lc),('fedavg',pf,lf),('prior',pb,lb)]:
 z=Y[v]!=0;move=1-q[v,0];extra[name]=dict(non_STAY_accuracy=float((q[v][z].argmax(1)==Y[v][z]).mean()),non_STAY_CE=float(loss[v][z].mean()),binary_AUROC=float(roc_auc_score(z,move)),binary_Brier=float(((move-z)**2).mean()),binary_accuracy=float(((move>=.5)==z).mean()))
save('non_stay_binary_diagnostics.json',extra)
counts=np.bincount(I[:n]*9+Y[:n],minlength=45000).reshape(5000,9);vc=np.bincount(I[v]*9+Y[v],minlength=45000).reshape(5000,9);tot=counts.sum(1);p=counts/tot[:,None];stay=p[:,0];non=tot-counts[:,0];ent=-np.where(p>0,p*np.log(np.maximum(p,1e-300)),0).sum(1);sup=(counts>0).sum(1);div=js(p,prior)
f=pd.DataFrame(dict(client_id=np.arange(5000),N=tot,STAY_share=stay,non_STAY_N=non,entropy=ent,supported_actions=sup,JS_global=div))
for k in range(9):f[f'action_{k}_N']=counts[:,k];f[f'action_{k}_share']=p[:,k]
f.to_csv(O/'client_distribution.csv',index=False)
heter=dict(STAY_share=stats(stay),non_STAY_N=stats(non),entropy=stats(ent),supported_actions=stats(sup),JS_global=stats(div),JS_units='nats')
for key,z in [('gt99_STAY',stay>.99),('gt95_STAY',stay>.95),('zero_non_STAY',non==0),('one_action',sup==1),('le5_non_STAY',non<=5),('le20_non_STAY',non<=20)]:heter[key]=dict(N=int(z.sum()),percentage=float(z.mean()*100))
save('client_heterogeneity.json',heter);both=(tot>0)&(vc.sum(1)>0);shift=js(p[both],vc[both]/vc[both].sum(1)[:,None]);save('client_temporal_shift.json',dict(clients=int(both.sum()),JS=stats(shift),units='nats'))
# 100 saved round-1 updates stratified jointly; no optimization.
f['count_bin']=pd.qcut(f.N,3,labels=False,duplicates='drop');f['stay_bin']=(f.STAY_share>=f.STAY_share.median()).astype(int);f['js_bin']=(f.JS_global>=f.JS_global.median()).astype(int)
chosen=[]
for _,grp in f.groupby(['count_bin','stay_bin','js_bin']):
 ids=grp.sort_values('client_id').client_id.to_numpy();chosen.extend(ids[np.linspace(0,len(ids)-1,min(8,len(ids)),dtype=int)].tolist())
chosen=sorted(set(chosen));rest=[j for j in range(5000) if j not in chosen];chosen+=list(np.asarray(rest)[np.linspace(0,len(rest)-1,100-len(chosen),dtype=int)]);chosen=sorted(chosen)
init=build_routing_policy_model(RoutingLearningParameters(),seed=42).get_weights();flat=lambda w:np.concatenate([x.ravel().astype(float) for x in w]);w0=flat(init);updates=[]
for j in chosen:
 u,_=pickle.loads((MD/'round_1_client_progress'/f'{j:04d}.pkl').read_bytes());updates.append(flat(u['weights'])-w0)
u=np.array(updates);norm=np.linalg.norm(u,axis=1);unit=u/norm[:,None];avg=u.mean(0);weighted=np.average(u,axis=0,weights=tot[chosen]);cos=unit@(avg/np.linalg.norm(avg));pair=(unit@unit.T)[np.triu_indices(len(u),1)]
save('fedavg_update_diagnostics.json',dict(round=1,clients=chosen,selection='deterministic joint count tertiles / median STAY / median JS strata, evenly spaced IDs; supplement evenly spaced remaining IDs to100',source='persisted client updates; zero optimization',update_norm=stats(norm),cosine_mean=stats(cos),pair_cosine=stats(pair),negative_pair_fraction=float((pair<0).mean()),cancellation_ratio=float(np.linalg.norm(avg)/norm.mean()),weighted_cancellation_ratio=float(np.linalg.norm(weighted)/np.average(norm,weights=tot[chosen])),correlation_count_norm=float(np.corrcoef(tot[chosen],norm)[0,1]),correlation_STAY_cosine=float(np.corrcoef(stay[chosen],cos)[0,1]),optimizer_steps=stats(np.ceil(tot/32))))
rounds=[];prev=w0
for j in range(1,6):
 model=load_final_policy(MD/f'fedavg_round_{j}.keras');w=flat(model.get_weights());q=pf[v] if j==5 else predict(f'round{j}',MD/f'fedavg_round_{j}.keras');ce,br=losses(q,Y[v]);rounds.append(dict(round=j,CE=ce.mean(),Brier=br.mean(),accuracy=float((q.argmax(1)==Y[v]).mean()),L2_initial=np.linalg.norm(w-w0),L2_previous=np.linalg.norm(w-prev)));prev=w
pd.DataFrame(rounds).to_csv(O/'fedavg_round_probability_metrics.csv',index=False)
# Identical-state testing includes mask; rounded precision is diagnostic only.
ambiguity={}
for precision in ['exact_float32','rounded_4_decimals']:
 hp=O/f'hash_{precision}.npy'
 if hp.exists():hashes=np.load(hp)
 else:
  chunks=[]
  for b in range(0,N,20000):
   x=np.array(X[b:b+20000]);x=np.round(x,4) if precision!='exact_float32' else x
   frame=pd.DataFrame(x);frame['mask']=pattern[b:b+len(x)];chunks.append(pd.util.hash_pandas_object(frame,index=False).to_numpy())
  hashes=np.concatenate(chunks);np.save(hp,hashes)
 result={}
 for name,z in [('all',np.ones(N,bool)),('REPOSITION',~K),('EV_CHARGING_NEXT_HOP',K)]:
  f0=pd.DataFrame(dict(h=hashes[z],y=Y[z],client=I[z]));group=f0.groupby('h');sizes=group.size();multi=sizes[sizes>=2];nlabels=group.y.nunique().loc[multi.index];clients=group.client.nunique().loc[multi.index];co=f0.groupby(['h','y']).size();prob=co/co.groupby(level=0).transform('sum');entropy=(-(prob*np.log(prob))).groupby(level=0).sum().loc[multi.index]
  result[name]=dict(repeated_groups=len(multi),observations=int(multi.sum()),conflicting_group_percentage=float((nlabels>1).mean()*100),conflicting_observation_percentage=float(multi[nlabels>1].sum()/multi.sum()*100),conditional_entropy_weighted=float((entropy*multi).sum()/multi.sum()),multiple_client_group_percentage=float((clients>1).mean()*100))
 ambiguity[precision]=result;print('ambiguity',precision,flush=True)
ambiguity['caveat']='64-bit hashes: negligible nonzero collision risk; exact test uses float32 cached representation plus mask. Rounded test uses absolute 0.0001 feature units and is not mathematical equivalence. No mask mixing.'
save('state_label_ambiguity.json',ambiguity)
dec={}
for name,z in [('REPOSITION',~K[v]),('EV_CHARGING_NEXT_HOP',K[v])]:
 dec[name]=dict(N=int(z.sum()),action_counts=np.bincount(Y[v][z],minlength=9),STAY_share=float((Y[v][z]==0).mean()),mask_cardinality_counts=np.bincount(card[v][z].astype(int),minlength=10)[1:],central_CE=float(lc[v][z].mean()),fedavg_CE=float(lf[v][z].mean()),prior_CE=float(lb[v][z].mean()))
save('decision_type_diagnostics.json',dec)
baselines={'global':bm}
for name,key in [('grid',G),('half_hour',S%48),('grid_x_6hour',G*4+(S%48)//12)]:
 maxkey=int(key.max())+1;ct=np.bincount(key[:n]*9+Y[:n],minlength=maxkey*9).reshape(maxkey,9);q=ct[key[v]].astype(float);unseen=q.sum(1)==0;q[unseen]=prior;q*=M[v];no_mask_mass=q.sum(1)==0;q[no_mask_mass]=pb[v][no_mask_mass];q/=q.sum(1)[:,None];b=metrics(q,Y[v]);b['unseen_fallback_N']=int(unseen.sum());b['no_mask_mass_fallback_N']=int(no_mask_mass.sum());b['zero_true_probability_N']=int((q[np.arange(N-n),Y[v]]==0).sum());baselines[name]=b
baselines['definition']='unsmoothed train-only empirical frequencies; fallback global for unseen group or zero remaining masked mass; zero true-class probabilities produce infinite CE, never silently clipped. Coarse time=00–05,06–11,12–17,18–23.'
save('conditional_prior_baselines.json',baselines)
print('ANALYTICAL PASS COMPLETE',ver,cm,flush=True)
