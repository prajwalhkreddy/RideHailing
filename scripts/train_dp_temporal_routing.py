"""Isolated trusted research runner; only March 1–15 cached routing records.

Public seed42 controls model initialization, NOT privacy noise. Resume state and
raw aggregate diagnostics are trusted-only and excluded from the DP release.
"""
from pathlib import Path
import os, json, pickle, hashlib, secrets, argparse, fcntl
os.environ.setdefault('TF_DETERMINISTIC_OPS', '1')
import numpy as np
import pandas as pd
import tensorflow as tf
from scripts.train_temporal_routing import local_step, flatten, unpack, P, OLD, DIAG, R
from src.routing.learning import build_routing_policy_model, RoutingLearningParameters, load_final_policy
from src.routing.privacy import account, solve_multiplier, clip_updates, noisy_mean

OUT = R/'results/analysis/2026-11-01_differential_privacy_comparison'
BASE = R/'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'
BASE_HASH = 'db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a'
INIT_HASH = '9e7bc3688a3d9c17eba7abf86a64f78606d6be9694b19d906e367ec108f5b4b0'
TRAIN = 2656632

def save(path, data):
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)

def update(slot, w, mom, vel, it, history, ids, slots, X, M, Y, sigma, rng):
    left, right = np.searchsorted(slots, [slot, slot+1])
    positions = np.arange(left, right)
    clients = np.unique(ids[positions])
    if not len(clients) or not 0 <= slot < 576:
        raise ValueError('Empty or protected training slot')
    for pos in positions:
        i = int(ids[pos]); history[i].append(int(pos)); history[i] = history[i][-1000:]
    total = np.zeros(P, np.float64); norms = []; examples = 0
    for start in range(0, len(clients), 64):
        group = clients[start:start+64]
        selected = [history[int(i)][-32:] for i in group]
        idx = np.zeros((len(group),32),np.int64); valid = np.zeros(idx.shape,np.float32)
        for j, ind in enumerate(selected):
            idx[j,:len(ind)] = ind; idx[j,len(ind):] = ind[-1]; valid[j,:len(ind)] = 1
        assert (slots[idx] <= slot).all() and (ids[idx] == group[:,None]).all()
        new, m, v, loss = local_step(tf.constant(w),tf.constant(X[idx]),tf.constant(M[idx]),tf.constant(Y[idx]),tf.constant(valid),tf.constant(mom[group]),tf.constant(vel[group]),tf.constant(it[group]))
        new = new.numpy(); m=m.numpy(); v=v.numpy()
        if not all(np.isfinite(a).all() for a in (new,m,v,loss.numpy())):
            raise ValueError('Non-finite local training')
        clipped, ns = clip_updates(new.astype(float)-w.astype(float), 1.)
        assert (np.linalg.norm(clipped,axis=1) <= 1.+1e-12).all()
        total += clipped.sum(0); norms.extend(ns.tolist())
        mom[group]=m; vel[group]=v; it[group]+=1; examples+=int(valid.sum())
    after = (w.astype(float)+noisy_mean(total,len(clients),sigma,rng)).astype(np.float32)
    if not np.isfinite(after).all(): raise ValueError('Non-finite global model')
    return after, dict(round=slot+1,participants=int(len(clients)),fresh_examples=int(len(positions)),local_examples=examples,
        fraction_clipped=float(np.mean(np.array(norms)>1.)),noise_SD=float(2*sigma/len(clients)),
        max_source_slot=slot,model_available_slot=slot+1), np.array(norms)

def metrics(model, X, M, Y, name):
    ps=[]; log_true=[]
    for start in range(0,len(Y),8192):
        mask=M[start:start+8192]; z=model(X[start:start+8192],training=False).numpy().astype(float)
        if not np.isfinite(z).all():raise ValueError('Non-finite held-out logits')
        z=np.where(mask,z,-np.inf); z-=z.max(1)[:,None]; p=np.exp(z); denominator=p.sum(1)
        y=Y[start:start+8192]; log_true.append(z[np.arange(len(y)),y]-np.log(denominator))
        p/=denominator[:,None]
        assert np.isfinite(p).all() and np.allclose(p.sum(1),1) and (p[~mask]==0).all()
        ps.append(p)
    p=np.concatenate(ps); pred=p.argmax(1); true=p[np.arange(len(Y)),Y]
    assert M[np.arange(len(Y)),Y].all()
    ce=-np.concatenate(log_true); assert np.isfinite(ce).all()
    br=(p*p).sum(1)-2*true+1; move=Y!=0; conf=p.max(1)
    bins=np.minimum((conf*10).astype(int),9)
    ece=sum(abs(conf[bins==k].sum()-(pred[bins==k]==Y[bins==k]).sum()) for k in range(10))/len(Y)
    result=dict(model=name,N=len(Y),accuracy=float(np.mean(pred==Y)),CE=float(ce.mean()),Brier=float(br.mean()),ECE=float(ece),
        STAY_accuracy=float(np.mean(pred[~move]==0)),non_STAY_accuracy=float(np.mean(pred[move]==Y[move])),non_STAY_CE=float(ce[move].mean()),
        non_STAY_Brier=float(br[move].mean()),mean_true_action_probability=float(true.mean()),mean_entropy=float(-(p*np.log(np.maximum(p,1e-300))).sum(1).mean()),
        STAY_predicted_share=float(np.mean(pred==0)),invalid_action_count=int((~M[np.arange(len(Y)),pred]).sum()))
    counts=np.bincount(pred,minlength=9)
    actions=[dict(model=name,action=k,name=label,count=int(counts[k]),percentage=float(100*counts[k]/len(Y)),mean_probability=float(p[:,k].mean())) for k,label in enumerate(['STAY','N','NE','E','SE','S','SW','W','NW'])]
    return result,actions

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--target',type=int,choices=[8,4,2],required=True); args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    md=R/f'models/routing_policy/dp_temporal_fedavg_eps{args.target}_seed42'
    md.mkdir(mode=0o700,parents=True,exist_ok=True); os.chmod(md,0o700)
    lock=(md/'writer.lock').open('w'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_HASH
    X,M,Y,ids=[np.load(OLD/'validated_cache'/f'{k}.npy',mmap_mode='r') for k in ['X','M','Y','IDS']]
    slots=np.load(DIAG/'metadata.npz')['slot']
    assert len(Y)==3303289 and len(slots)==len(Y) and (np.diff(slots)>=0).all()
    assert np.array_equal(np.unique(slots[:TRAIN]),np.arange(576)) and np.array_equal(np.unique(slots[TRAIN:]),np.arange(576,720))
    assert X.shape==(3303289,169) and M.shape==(3303289,9) and ids.min()>=0 and ids.max()<5000
    tf.keras.utils.set_random_seed(42); tf.config.experimental.enable_op_determinism()
    model=build_routing_policy_model(RoutingLearningParameters(),seed=42); w=flatten(model.get_weights())
    assert hashlib.sha256(w.tobytes()).hexdigest()==INIT_HASH
    sigma=solve_multiplier(args.target)
    progress=md/'trusted_resume.pkl'
    if progress.exists():
        s=pickle.loads(progress.read_bytes()); assert s['target']==args.target and s['initialization_hash']==INIT_HASH and s['sigma']==sigma
        w=s['weights'];mom=s['mom'];vel=s['vel'];it=s['iterations'];history=s['history'];rows=s['rows'];norms=s['norms'];start=s['next_slot']
        rng=np.random.default_rng();rng.bit_generator.state=s['noise_rng']
    else:
        # This state is secret. Publishing seed42 noise would invalidate the privacy claim.
        rng=np.random.default_rng(secrets.randbits(256)); start=0; rows=[];norms=[]
        mom=np.zeros((5000,P),np.float32);vel=np.zeros_like(mom);it=np.zeros(5000,np.int64);history=[[] for _ in range(5000)]
    save(md/'accountant.json',dict(target=args.target,noise_multiplier=sigma,**account(sigma,576)))
    for slot in range(start,576):
        w,row,ns=update(slot,w,mom,vel,it,history,ids,slots,X,M,Y,sigma,rng); rows.append(row);norms.append(ns)
        # Latest trusted state every16 rounds, matching the existing temporal runner.
        s=dict(target=args.target,sigma=sigma,initialization_hash=INIT_HASH,weights=w,mom=mom,vel=vel,iterations=it,history=history,rows=rows,norms=norms,next_slot=slot+1,noise_rng=rng.bit_generator.state)
        if (slot+1)%16==0:
            tmp=progress.with_suffix('.tmp')
            with tmp.open('wb') as f: pickle.dump(s,f,protocol=5)
            os.chmod(tmp,0o600);tmp.replace(progress)
        save(md/'status.json',dict(status='TRAINING',round=slot+1,epsilon=account(sigma,slot+1)['epsilon']))
        if (slot+1)%16==0:
            model.set_weights(unpack(w)); model.save(md/f'global_after_slot_{slot+1:03d}.keras')
            print(args.target,slot+1,flush=True)
    model.set_weights(unpack(w));final=md/'final_march12.keras'
    if not final.exists():model.save(final)
    reloaded=load_final_policy(final)
    np.testing.assert_array_equal(flatten(reloaded.get_weights()),w)
    np.testing.assert_array_equal(model(X[TRAIN:TRAIN+32],training=False).numpy(),reloaded(X[TRAIN:TRAIN+32],training=False).numpy())
    result,actions=metrics(reloaded,X[TRAIN:],M[TRAIN:],Y[TRAIN:],f'DP_EPS{args.target}')
    ns=np.concatenate(norms);frame=pd.DataFrame(rows)
    stats=dict(model=f'DP_EPS{args.target}',client_updates_seen=len(ns),fraction_clipped=float(np.mean(ns>1)),median=float(np.median(ns)),P90=float(np.quantile(ns,.9)),P95=float(np.quantile(ns,.95)),P99=float(np.quantile(ns,.99)),maximum=float(ns.max()),rounds=576,noise_multiplier=sigma,epsilon=account(sigma,576)['epsilon'],delta=1e-5,final_parameter_norm=float(np.linalg.norm(w.astype(float))),sha256=hashlib.sha256(final.read_bytes()).hexdigest())
    for col in ['participants','local_examples','fresh_examples']:
        stats.update({col+'_'+stat:float(getattr(frame[col],stat)()) for stat in ['mean','min','max']})
    save(md/'validation.json',dict(metrics=result,actions=actions,training=stats,privacy_scope='Model transcript only; raw diagnostics/trusted state excluded'))
    frame.to_csv(md/'training_log.csv',index=False)
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_HASH
    save(md/'status.json',dict(status='COMPLETE',round=576,epsilon=stats['epsilon']))
    print('COMPLETE',json.dumps(result),flush=True)

if __name__=='__main__': main()
