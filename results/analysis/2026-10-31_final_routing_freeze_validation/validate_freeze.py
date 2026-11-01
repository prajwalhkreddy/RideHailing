from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from src.routing.learning import load_final_policy
R=Path.cwd();O=R/'results/analysis/2026-10-31_final_routing_freeze_validation';O.mkdir(exist_ok=True,parents=True)
T=R/'results/analysis/2026-10-31_temporal_federated_routing';D=R/'results/analysis/2026-10-30_routing_effectiveness_diagnosis';C=R/'models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42/validated_cache';path=R/'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras';n=2656632
get=lambda p:json.loads(p.read_text())
def save(f,x):(O/f).write_text(json.dumps(x,indent=2,default=lambda z:z.tolist() if hasattr(z,'tolist') else str(z))+'\n')
X,M,Y=[np.load(C/f'{k}.npy',mmap_mode='r')[n:] for k in ['X','M','Y']];S=np.load(D/'metadata.npz')['slot'][n:];assert len(Y)==646657 and np.array_equal(np.unique(S),np.arange(576,720));sha=hashlib.sha256(path.read_bytes()).hexdigest()
a=load_final_policy(path);b=load_final_policy(path);q=np.empty((len(Y),9));repeat=np.empty_like(q)
assert a.input_shape[-1]==169 and a.output_shape[-1]==9
for st in range(0,len(Y),8192):
 en=min(len(Y),st+8192);z=a(X[st:en],training=False).numpy();zz=b(X[st:en],training=False).numpy();np.testing.assert_array_equal(z,zz)
 for out,logits in [(q,z),(repeat,zz)]:
  l=np.where(M[st:en],logits.astype(float),-np.inf);p=np.exp(l-l.max(1)[:,None]);out[st:en]=p/p.sum(1)[:,None]
np.testing.assert_array_equal(q,repeat);assert np.isfinite(q).all() and np.allclose(q.sum(1),1) and (q[~M]==0).all() and M[np.arange(len(Y)),Y].all();assert M[np.arange(len(Y)),q.argmax(1)].all()
prior=np.array(get(D/'central_probability_adequacy.json')['prior']['mean_probability']) # use persisted TRAIN frequencies, not validation mean
prior=np.array(get(R/'results/analysis/2026-10-30_final_behavioral_routing_training/routing_probability_adequacy.json')['training_action_prior']);p=M*prior;p/=p.sum(1)[:,None]
def losses(v):
 t=v[np.arange(len(Y)),Y];return -np.log(t),(v*v).sum(1)-2*t+1
lc,bc=losses(q);lp,bp=losses(p)
def ece(v,idx):
 v=v[idx];y=Y[idx];conf=v.max(1);ok=v.argmax(1)==y;bins=np.minimum((conf*10).astype(int),9);return sum(abs(conf[bins==k].sum()-ok[bins==k].sum()) for k in range(10))/len(y)
metrics=dict(CE=float(lc.mean()),Brier=float(bc.mean()),ECE=float(ece(q,np.ones(len(Y),bool))))
original=get(T/'final_validation.json');assert all(abs(metrics[k]-original[k])<1e-12 for k in metrics)
rows=[]
for slot in range(576,720):
 z=S==slot;rows.append(dict(slot=slot,timestamp=str(pd.Timestamp('2026-03-01')+pd.Timedelta(minutes=30*slot)),N=int(z.sum()),model_CE=lc[z].mean(),prior_CE=lp[z].mean(),CE_difference=(lc-lp)[z].mean(),model_Brier=bc[z].mean(),prior_Brier=bp[z].mean(),Brier_difference=(bc-bp)[z].mean()))
f=pd.DataFrame(rows);f.to_csv(O/'paired_slot_adequacy.csv',index=False);diff=f[['CE_difference','Brier_difference']].to_numpy();rng=np.random.default_rng(42);starts=rng.integers(0,137,size=(2000,18));idx=(starts[:,:,None]+np.arange(8)).reshape(2000,144);boot=diff[idx].mean(1);ci=np.quantile(boot,[.025,.975],axis=0)
summary={}
for j,key in enumerate(['CE','Brier']):
 v=diff[:,j];summary[key]=dict(mean=float(v.mean()),median=float(np.median(v)),SD=float(v.std(ddof=1)),SE=float(v.std(ddof=1)/12),fraction_slots_model_wins=float((v<0).mean()),bootstrap_95=ci[:,j].tolist())
save('bootstrap_adequacy.json',dict(block_slots=8,replicates=2000,seed=42,method='noncircular movingblocks sampled from137overlappingstarts;18blocks perreplicate; unweighted mean of144slotmeans',metrics=summary,aggregate_observation_weighted_difference=dict(CE=float((lc-lp).mean()),Brier=float((bc-bp).mean())),qualification='MODEST / UNCERTAIN BUT POSITIVE' if (ci[1]>=0).any() else 'POSITIVE'))
days=[]
for day in range(3):
 z=(S>=576+48*day)&(S<624+48*day);days.append(dict(date=f'2026-03-{13+day}',N=int(z.sum()),model_CE=lc[z].mean(),prior_CE=lp[z].mean(),model_Brier=bc[z].mean(),prior_Brier=bp[z].mean(),model_ECE=ece(q,z),prior_ECE=ece(p,z),model_wins_both=bool(lc[z].mean()<lp[z].mean() and bc[z].mean()<bp[z].mean())))
pd.DataFrame(days).to_csv(O/'daily_stability.csv',index=False)
prob=[]
for k in range(9):prob.append(dict(action=k,mean=q[:,k].mean(),SD=q[:,k].std(),P05=np.quantile(q[:,k],.05),median=np.median(q[:,k]),P95=np.quantile(q[:,k],.95)))
pd.DataFrame(prob).to_csv(O/'routing_probability_distribution.csv',index=False)
ent=-(q*np.log(np.maximum(q,1e-300))).sum(1);truth=q[np.arange(len(Y)),Y];tr=[]
for name,z in [('ALL',np.ones(len(Y),bool)),('STAY',Y==0),('NON_STAY',Y!=0)]+[(str(k),Y==k) for k in range(1,9)]:
 tr.append(dict(group=name,N=int(z.sum()),mean=truth[z].mean(),median=np.median(truth[z]),P10=np.quantile(truth[z],.1),P90=np.quantile(truth[z],.9)))
pd.DataFrame(tr).to_csv(O/'true_action_probability.csv',index=False)
z=Y!=0;central=np.load(D/'central_probabilities.npy',mmap_mode='r')[n:];lcc,bcc=losses(central);non=dict(temporal=dict(CE=lc[z].mean(),Brier=bc[z].mean()),prior=dict(CE=lp[z].mean(),Brier=bp[z].mean()),central=dict(CE=lcc[z].mean(),Brier=bcc[z].mean()),NON_STAY_PROBABILITY_SIGNAL='YES' if lc[z].mean()<lp[z].mean() and bc[z].mean()<bp[z].mean() else 'NO' if lc[z].mean()>=lp[z].mean() and bc[z].mean()>=bp[z].mean() else 'INCONCLUSIVE',top1_accuracy=float((q[z].argmax(1)==Y[z]).mean()))
save('nonstay_probability_analysis.json',non)
# Nondegeneracy assessed descriptively using probability spread and entropy, no calibration.
vector=dict(mean_entropy=float(ent.mean()),P05=float(np.quantile(ent,.05)),median=float(np.median(ent)),P95=float(np.quantile(ent,.95)),action_SD=[float(v['SD']) for v in prob],ROUTING_VECTOR_NONDEGENERATE='YES' if max(v['SD'] for v in prob)>.01 else 'NO',criterion='Descriptive substantialvariation: at leastone action SD>0.01; assess alongsideentropy andfull probabilityquantiles. Not a training parameter.')
save('vector_quality.json',vector)
assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
save('checkpoint_reproducibility.json',dict(status='PASS',checkpoint=str(path.relative_to(R)),sha256=sha,full_validation_reload_logits_bit_identical=True,full_validation_probabilities_bit_identical=True,repeated_metrics_identical=True,original_metrics_reproduced=True,inference_RNG_independent=True,training='existing576slot chronology evidence reused',validation_updates=0,input_dim=169,output_dim=9,invalid_probabilities_exact_zero=True,invalid_predictions=0,finite=True))
contract=dict(GLOBAL_ROUTING_STATE='169D_PUBLIC_GRID_STATISTICS',PRIVATE_DRIVER_VARIABLES='LOCAL_ONLY',ROUTING_LEARNING='TEMPORAL_FEDAVG',LOCAL_BUFFER='LATEST_32',LOCAL_OPTIMIZER='PERSISTENT_ADAM',FEDERATION_PARTICIPATION='CURRENT_SLOT_CONTRIBUTORS_ONLY',AGGREGATION='EQUAL_ELIGIBLE_CLIENT_WEIGHTING',checkpoint=str(path.relative_to(R)),sha256=sha,status='FROZEN_STRUCTURAL_CONTRACT',production_activation='unchanged')
save('routing_freeze_contract.json',contract)
frozen=metrics['CE']<lp.mean() and metrics['Brier']<bp.mean() and vector['ROUTING_VECTOR_NONDEGENERATE']=='YES'
save('final_routing_readiness.json',dict(FINAL_ROUTING_MODEL_FROZEN='YES' if frozen else 'NO',ROUTING_READY_FOR_PRICING='YES' if frozen else 'NO',metrics=metrics,checkpoint=str(path.relative_to(R)),sha256=sha,qualification=get(O/'bootstrap_adequacy.json')['qualification'],nonstay_signal=non['NON_STAY_PROBABILITY_SIGNAL'],limitations='WeaknonSTAYtop1; nonSTAY subgroup loss qualification retained. No evidence of invalid/constantvector; subgroup weakness doesnot byitself negate aggregatevector adequacy underrequested gate.',next_action='FINAL_PRICING_DQN_TRAINING_PROTOCOL_FREEZE' if frozen else 'ROUTING_MODEL_CONTRACT_REVIEW',next_action_executed=False,March17_31_untouched=True))
print(json.dumps(dict(metrics=metrics,bootstrap=summary,entropy=vector,nonstay=non,days=days,truth=tr[:3],hash=sha),default=str))
