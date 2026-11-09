"""V1 request-level replay, masked actions/targets and per-request discount."""
from collections import deque
from dataclasses import asdict
from pathlib import Path
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from src.rl.pricing_dqn import (PricingDQN, DQNConfig, PricingAction, ACTIONS,
    validate_state, action_index, soft_update)
from src.pricing.passenger_sensitive_v1 import guard_date

def validate_mask(mask):
    mask = np.asarray(mask)
    if mask.shape != (7,) or mask.dtype != bool:
        raise ValueError('Boolean seven-action mask required.')
    return mask.copy()

def masked_targets(rewards, dones, next_q, masks, delta_t, gamma=.99):
    r = np.asarray(rewards, dtype=np.float64)
    d = np.asarray(dones)
    q = np.asarray(next_q, dtype=np.float64)
    m = np.asarray(masks)
    # Elapsed time is validated diagnostic metadata, never a discount or replay weight.
    dt = np.asarray(delta_t, dtype=np.float64)
    if (r.ndim != 1 or d.shape != r.shape or d.dtype != bool or q.shape != (len(r),7)
        or m.shape != q.shape or m.dtype != bool or dt.shape != r.shape
        or not np.isfinite(r).all() or not np.isfinite(q).all() or not np.isfinite(dt).all()
        or (dt < 0).any() or not np.isfinite(gamma) or not 0 < gamma <= 1):
        raise ValueError('Invalid V1 Bellman batch.')
    if ((~d) & (~m.any(axis=1))).any():
        raise ValueError('Nonterminal next request must be actionable.')
    result = r.copy()
    live = ~d
    result[live] += gamma * np.where(m[live],q[live],-np.inf).max(axis=1)
    if not np.isfinite(result).all() or (np.abs(result)>np.finfo(np.float32).max).any():
        raise ValueError('Invalid float32 Bellman target.')
    return result.astype(np.float32)

class RequestReplay:
    def __init__(self, capacity=100000, seed=43):
        self.items = deque(maxlen=capacity)
        self.rng = np.random.default_rng(seed)
    def __len__(self):return len(self.items)
    def add(self, state, action, reward, next_state, done, next_action_mask, delta_t_minutes):
        s,n = validate_state(state),validate_state(next_state)
        a = action_index(action);r=float(reward);dt=float(delta_t_minutes);m=validate_mask(next_action_mask)
        if not isinstance(done,(bool,np.bool_)) or not np.isfinite([r,dt]).all() or dt<0 or r<0 or r>np.finfo(np.float32).max:
            raise ValueError('Invalid V1 transition.')
        if not done and not m.any():raise ValueError('Nonterminal empty next mask.')
        self.items.append((s,a,r,n,bool(done),m,dt))
    def sample(self,n):
        if n<1 or n>len(self):raise ValueError('Invalid batch size.')
        rows=[self.items[i] for i in self.rng.choice(len(self),n,replace=False)]
        return (np.stack([r[0] for r in rows]),np.array([r[1] for r in rows],np.int32),
                np.array([r[2] for r in rows]),np.stack([r[3] for r in rows]),
                np.array([r[4] for r in rows],bool),np.stack([r[5] for r in rows]),np.array([r[6] for r in rows]))

class PassengerSensitiveDQN(PricingDQN):
    def __init__(self,config=DQNConfig()):
        super().__init__(config)
        self.replay=RequestReplay(config.replay_capacity,config.seed+1)
    def select_action(self,state,mask,*,explore=True):
        s=validate_state(state);m=validate_mask(mask);indices=np.flatnonzero(m)
        if not len(indices):return None
        explored=bool(explore and self.rng.random()<self.epsilon)
        if explored:a=int(self.rng.choice(indices))
        else:
            q=self.online(s[None,:],training=False).numpy()[0]
            if not np.isfinite(q).all():raise ValueError('Nonfinite Q values.')
            a=int(indices[np.argmax(q[indices])])
        return PricingAction(a,ACTIONS[a],self.epsilon,explored)
    def store(self,*args):self.replay.add(*args)
    def train_step(self):
        if len(self.replay)<self.config.minimum_replay_size:return None
        s,a,r,n,d,m,dt=self.replay.sample(self.config.batch_size)
        y=masked_targets(r,d,self.target(n,training=False).numpy(),m,dt,self.config.gamma)
        with tf.GradientTape() as tape:
            q=tf.gather(self.online(s,training=True),a,axis=1,batch_dims=1)
            diff=tf.convert_to_tensor(y)-q;absolute=tf.abs(diff)
            loss=tf.reduce_mean(tf.where(absolute<=1,.5*diff**2,absolute-.5))
        grads=tape.gradient(loss,self.online.trainable_variables)
        if not np.isfinite(float(loss)) or any(g is None or not np.isfinite(g.numpy()).all() for g in grads):raise ValueError('Nonfinite gradient/loss.')
        self.online.optimizer.apply_gradients(zip(grads,self.online.trainable_variables))
        soft_update(self.online,self.target,self.config.soft_target_tau);self.training_steps+=1
        return dict(loss=float(loss),epsilon=self.epsilon,replay_size=len(self.replay))
    def complete_slot(self,timestamp):
        guard_date(timestamp,calibration=True)
        if pd.Timestamp(timestamp)<pd.Timestamp('2026-03-01'):raise ValueError('Pricing training slots start March1.')
        return [self.train_step() for _ in range(8)] if len(self.replay)>=self.config.minimum_replay_size else []
    def enable_compiled_updates(self):raise ValueError('Legacy compiled updater is not valid for V1 replay.')
    def compiled_train_step(self):raise ValueError('Legacy compiled updater is not valid for V1 replay.')
    def save(self,path):
        path=Path(path)
        if path.exists() and any(path.iterdir()):raise FileExistsError('Use a fresh V1 checkpoint directory.')
        path.mkdir(parents=True,exist_ok=True)
        self.online.save(path/'online.keras');self.target.save(path/'target.keras')
        rows=list(self.replay.items)
        np.savez_compressed(path/'replay.npz',states=np.array([x[0] for x in rows],np.float32).reshape(-1,13),actions=np.array([x[1] for x in rows],np.int32),rewards=np.array([x[2] for x in rows]),next_states=np.array([x[3] for x in rows],np.float32).reshape(-1,13),dones=np.array([x[4] for x in rows],bool),next_action_masks=np.array([x[5] for x in rows],bool).reshape(-1,7),delta_t_minutes=np.array([x[6] for x in rows]))
        (path/'checkpoint.json').write_text(json.dumps(dict(schema='passenger_sensitive_request_v1',discount_semantics='PER_REQUEST_TRANSITION',config=asdict(self.config),training_steps=self.training_steps,rng_state=self.rng.bit_generator.state,replay_rng_state=self.replay.rng.bit_generator.state),indent=2)+'\n')
    @classmethod
    def load(cls,path):
        path=Path(path);m=json.loads((path/'checkpoint.json').read_text())
        if m.get('schema')!='passenger_sensitive_request_v1' or m.get('discount_semantics')!='PER_REQUEST_TRANSITION':raise ValueError('Legacy or time-aware pricing checkpoint prohibited for corrected V1.')
        obj=cls(DQNConfig(**m['config']))
        obj.online=tf.keras.models.load_model(path/'online.keras');obj.target=tf.keras.models.load_model(path/'target.keras',compile=False)
        for model in [obj.online,obj.target]:
            if model.input_shape!=(None,13) or model.output_shape!=(None,7) or [l.units for l in model.layers]!=[64,64,7]:raise ValueError('Invalid V1 architecture.')
        if not isinstance(obj.online.optimizer,tf.keras.optimizers.Adam) or int(obj.online.optimizer.iterations)!=m['training_steps']:raise ValueError('Invalid optimizer state.')
        with np.load(path/'replay.npz',allow_pickle=False) as z:
            names=['states','actions','rewards','next_states','dones','next_action_masks','delta_t_minutes']
            if len({len(z[k]) for k in names})!=1 or len(z['states'])>obj.config.replay_capacity:raise ValueError('Invalid replay sizes.')
            for row in zip(*(z[k] for k in names)):obj.store(*row)
        obj.training_steps=m['training_steps'];obj.rng.bit_generator.state=m['rng_state'];obj.replay.rng.bit_generator.state=m['replay_rng_state']
        return obj

class ActionableRequestLinker:
    """Keep one pending real action until its next actionable context is known."""
    def __init__(self,learner):self.learner=learner;self.pending=None;self.audit=[];self.last_time=None
    def observe(self,request_id,state,action,reward,timestamp,mask):
        t=guard_date(timestamp);m=validate_mask(mask);s=validate_state(state)
        if self.last_time is not None and t<self.last_time:raise ValueError('Request chronology reversed.')
        self.last_time=t
        if action is None:
            if m.any() or reward!=0:raise ValueError('No-action request must have empty mask and zero reward.')
            return
        a=action_index(action)
        if not m[a] or not np.isfinite(reward) or reward<0:raise ValueError('Infeasible action or invalid reward.')
        if self.pending is not None:self._finish(s,m,t,False,request_id)
        self.pending=(request_id,s,a,float(reward),t)
    def _finish(self,next_state,mask,t,done,next_id):
        rid,s,a,r,previous=self.pending;dt=(t-previous).total_seconds()/60
        if dt<0:raise ValueError('Negative elapsed time.')
        self.learner.store(s,a,r,next_state,done,mask,dt)
        self.audit.append(dict(Request_ID=rid,next_actionable_request_id=next_id,delta_t_minutes=dt,gamma_eff=self.learner.config.gamma,done=done,reward=r,action=a,next_action_mask=mask.tolist()))
        self.pending=None
    def finish_episode(self,end):
        t=pd.Timestamp(end)
        if self.last_time is not None and t<self.last_time:raise ValueError('Terminal time before last request.')
        if self.pending is not None:self._finish(self.pending[1],np.zeros(7,bool),t,True,None)
