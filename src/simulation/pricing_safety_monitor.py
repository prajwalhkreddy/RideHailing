"""Read-only checkpoint observations; never select actions or update learners."""
import hashlib,pickle
import numpy as np
EPISODES={10,25,50,100}
def learner_fingerprint(d):
 h=hashlib.sha256()
 for v in d.online.weights+d.target.weights+list(d.online.optimizer.variables):h.update(v.numpy().tobytes())
 h.update(pickle.dumps((list(d.replay.items),d.replay.rng.bit_generator.state,d.rng.bit_generator.state,d.training_steps)))
 return h.hexdigest()
def observe(d,episode,mean_loss,development):
 rows=list(d.replay.items)
 if not rows:raise ValueError('Empty monitoring replay')
 ix=np.sort(np.random.default_rng(42).choice(len(rows),min(4096,len(rows)),replace=False));sample=[rows[i] for i in ix]
 s=np.stack([r[0] for r in sample]);n=np.stack([r[3] for r in sample]);reward=np.array([r[2] for r in sample],np.float32);done=np.array([r[4] for r in sample],bool)
 q=d.online(s,training=False).numpy();nq=d.target(n,training=False).numpy();boot=np.where(done,0,.99*nq.max(1));den=np.abs(reward)+np.abs(boot);frac=np.divide(np.abs(boot),den,out=np.zeros_like(den),where=den>0)
 term=[r for r in rows if r[4]]
 if term:
  tq=d.online(np.stack([r[0] for r in term]),training=False).numpy()[np.arange(len(term)),[r[1] for r in term]];tr=np.array([r[2] for r in term]);tmean=float(tq.mean());rmean=float(tr.mean());mae=float(np.abs(tq-tr).mean())
 else:tmean=rmean=mae=None
 all_rewards=np.array([r[2] for r in rows]);scale=float(all_rewards.mean()*sum(.99**i for i in range(16)))
 if not np.isfinite(q).all() or not np.isfinite(nq).all() or (mean_loss is not None and not np.isfinite(mean_loss)):raise ValueError('Nonfinite monitoring values')
 for v in d.online.weights+d.target.weights:
  if not np.isfinite(v.numpy()).all():raise ValueError('Nonfinite weights')
 ratio=None if not rmean else tmean/rmean;qr=float(np.abs(q).mean())/scale if scale else None;b=float(frac[den>0].mean())
 return dict(episode=episode,mean_abs_Q=float(np.abs(q).mean()),median_abs_Q=float(np.median(np.abs(q))),q_max=float(q.max()),mean_Q_spread=float(np.ptp(q,axis=1).mean()),mean_loss=mean_loss,terminal_N=len(term),terminal_mean_reward=rmean,terminal_selected_Q_mean=tmean,terminal_absolute_TD_error=mae,bootstrap_fraction=b,development_revenue=development['revenue'],development_assignments=development['assignments'],development_action_distribution=development['action_counts'],replay_size=len(rows),optimizer_updates=d.training_steps,epsilon=d.epsilon,mean_reward_16slot_reference=scale,flags=dict(TERMINAL_CALIBRATION_CONCERN=dict(status='NO_TERMINAL_EVIDENCE' if ratio is None else ('ABOVE_PRESERVED_REFERENCE_REVIEW' if ratio>93.63825988769531/26.50354172196378 else 'NOT_ABOVE_PRESERVED_REFERENCE'),Q_to_reward_ratio=ratio),Q_SCALE_CONCERN=dict(status='ABOVE_PRESERVED_REFERENCE_REVIEW' if qr is not None and qr>87.5663070678711/409.4048057278852 else 'NOT_ABOVE_PRESERVED_REFERENCE',Q_to_mean_reward_horizon_ratio=qr),BOOTSTRAP_DOMINANCE_CONCERN=dict(status='AT_OR_ABOVE_ACCELERATED_REFERENCE_REVIEW' if b>=.9546068808315554 else 'BELOW_ACCELERATED_REFERENCE',distance_to_accelerated_reference=.9546068808315554-b)),flag_policy='Reference comparisons only; an increase requests descriptive review, not dramatic-inflation proof, a convergence criterion or an automatic stop.')
