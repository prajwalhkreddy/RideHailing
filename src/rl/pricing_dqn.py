"""Standard standalone DQN for frozen 13D pricing state; identity inputs."""
from dataclasses import dataclass,asdict
from collections import deque
from pathlib import Path
import json
import numpy as np
import tensorflow as tf
from src.pricing.dqn_contract import FEATURES

ACTIONS=(.85,.90,.95,1.,1.05,1.10,1.15)

@dataclass(frozen=True)
class DQNConfig:
    gamma:float=.99
    learning_rate:float=.001
    batch_size:int=64
    replay_capacity:int=100000
    minimum_replay_size:int=1000
    epsilon_start:float=1.
    epsilon_end:float=.05
    epsilon_decay_steps:int=50000
    soft_target_tau:float=.005
    seed:int=42
    def __post_init__(self):
        for name in ('gamma','learning_rate','epsilon_start','epsilon_end','soft_target_tau'):
            if not np.isfinite(getattr(self,name)):raise ValueError('Nonfinite config.')
        if not 0<=self.gamma<=1 or self.learning_rate<=0 or not 0<=self.epsilon_end<=self.epsilon_start<=1 or not 0<self.soft_target_tau<=1:raise ValueError('Invalid config range.')
        for name in ('batch_size','replay_capacity','minimum_replay_size','epsilon_decay_steps','seed'):
            x=getattr(self,name)
            if isinstance(x,bool) or not isinstance(x,int) or x<(0 if name=='seed' else 1):raise ValueError('Invalid integer config.')
        if not self.batch_size<=self.minimum_replay_size<=self.replay_capacity:raise ValueError('Require batch <= minimum <= capacity.')


def validate_state(state):
    x=np.asarray(state,dtype=np.float64)
    if x.shape!=(13,) or not np.isfinite(x).all() or (x<0).any():raise ValueError('Finite nonnegative 13D state required.')
    if not np.isclose(x[3:12].sum(),1.,rtol=1e-7,atol=1e-8) or not 0<=x[12]<=1:raise ValueError('Invalid routing probabilities/popularity.')
    if (x>np.finfo(np.float32).max).any():raise ValueError('State not representable by float32 network.')
    return x.astype(np.float32)


def action_index(action):
    if isinstance(action,(bool,np.bool_)) or not isinstance(action,(int,np.integer)) or not 0<=action<7:raise ValueError('Integer pricing action 0..6 required.')
    return int(action)

class ReplayBuffer:
    def __init__(self,capacity=100000,seed=42):
        if not isinstance(capacity,int) or capacity<=0:raise ValueError('Positive replay capacity required.')
        self.items=deque(maxlen=capacity);self.rng=np.random.default_rng(seed)
    def __len__(self):return len(self.items)
    def add(self,state,action,reward,next_state,done):
        s=validate_state(state);n=validate_state(next_state);a=action_index(action);r=float(reward)
        if not np.isfinite(r) or abs(r)>np.finfo(np.float32).max:raise ValueError('Finite float32 reward required.')
        if not isinstance(done,(bool,np.bool_)):raise ValueError('Boolean done required.')
        self.items.append((s,a,r,n,bool(done)))
    def sample(self,size):
        if not isinstance(size,int) or not 0<size<=len(self):raise ValueError('Invalid batch size.')
        indices=self.rng.choice(len(self),size=size,replace=False)
        rows=[self.items[int(i)] for i in indices]
        return (np.stack([r[0] for r in rows]),np.array([r[1] for r in rows],np.int32),np.array([r[2] for r in rows],np.float32),np.stack([r[3] for r in rows]),np.array([r[4] for r in rows],bool))


def build_q_network():
    return tf.keras.Sequential([tf.keras.Input((13,)),tf.keras.layers.Dense(64,activation='relu'),tf.keras.layers.Dense(64,activation='relu'),tf.keras.layers.Dense(7,activation='linear')],name='pricing_q')


def bellman_targets(rewards,dones,next_q,gamma):
    rewards=np.asarray(rewards,dtype=np.float32);dones=np.asarray(dones);q=np.asarray(next_q,dtype=np.float32)
    if rewards.ndim!=1 or dones.shape!=rewards.shape or dones.dtype!=bool or q.shape!=(len(rewards),7) or not np.isfinite(q).all() or not np.isfinite(rewards).all() or not 0<=gamma<=1:raise ValueError('Invalid Bellman batch.')
    result=rewards+np.where(dones,0.,gamma*q.max(axis=1))
    if not np.isfinite(result).all():raise ValueError('Nonfinite Bellman target.')
    return result.astype(np.float32)


def soft_update(online,target,tau):
    if not np.isfinite(tau) or not 0<tau<=1:raise ValueError('Invalid tau.')
    if len(online.weights)!=len(target.weights):raise ValueError('Mismatched networks.')
    for a,b in zip(online.weights,target.weights):
        if a.shape!=b.shape:raise ValueError('Mismatched network shape.')
        b.assign((1-tau)*b+tau*a)

@dataclass(frozen=True)
class PricingAction:
    action_index:int
    pricing_factor:float
    epsilon:float
    explored:bool

class PricingDQN:
    def __init__(self,config=DQNConfig()):
        self.config=config;tf.keras.utils.set_random_seed(config.seed)
        self.online=build_q_network();self.target=build_q_network();self.target.set_weights(self.online.get_weights())
        self.online.compile(optimizer=tf.keras.optimizers.Adam(config.learning_rate),loss=tf.keras.losses.Huber())
        self.online.optimizer.build(self.online.trainable_variables)
        self.replay=ReplayBuffer(config.replay_capacity,config.seed+1);self.rng=np.random.default_rng(config.seed);self.training_steps=0
    @property
    def epsilon(self):
        fraction=min(self.training_steps/self.config.epsilon_decay_steps,1.)
        return self.config.epsilon_start+(self.config.epsilon_end-self.config.epsilon_start)*fraction
    def select_action(self,state,*,explore=True):
        s=validate_state(state);random=bool(explore and self.rng.random()<self.epsilon)
        if random:a=int(self.rng.integers(7))
        else:
            q=self.online(s[None,:],training=False).numpy()[0]
            if not np.isfinite(q).all():raise ValueError('Nonfinite Q values.')
            a=int(np.argmax(q))
        return PricingAction(a,ACTIONS[a],self.epsilon,random)
    def store(self,state,action,reward,next_state,done):self.replay.add(state,action,reward,next_state,done)
    def train_step(self):
        if len(self.replay)<self.config.minimum_replay_size:return None
        states,actions,rewards,next_states,dones=self.replay.sample(self.config.batch_size)
        targets=bellman_targets(rewards,dones,self.target(next_states,training=False).numpy(),self.config.gamma)
        with tf.GradientTape() as tape:
            q=tf.gather(self.online(states,training=True),actions,axis=1,batch_dims=1)
            diff=tf.convert_to_tensor(targets)-q;absolute=tf.abs(diff)
            loss=tf.reduce_mean(tf.where(absolute<=1,.5*diff**2,absolute-.5))
        gradients=tape.gradient(loss,self.online.trainable_variables)
        if not np.isfinite(float(loss)) or any(g is None or not np.isfinite(g.numpy()).all() for g in gradients):raise ValueError('Nonfinite loss/gradient.')
        self.online.optimizer.apply_gradients(zip(gradients,self.online.trainable_variables))
        soft_update(self.online,self.target,self.config.soft_target_tau);self.training_steps+=1
        return dict(loss=float(loss),mean_q=float(tf.reduce_mean(q)),mean_target=float(np.mean(targets)),epsilon=self.epsilon,replay_size=len(self.replay))
    def save(self,path):
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        self.online.save(path/'online.keras');self.target.save(path/'target.keras')
        rows=list(self.replay.items)
        np.savez_compressed(path/'replay.npz',states=np.array([r[0] for r in rows],np.float32).reshape(-1,13),actions=np.array([r[1] for r in rows],np.int32),rewards=np.array([r[2] for r in rows],np.float64),next_states=np.array([r[3] for r in rows],np.float32).reshape(-1,13),dones=np.array([r[4] for r in rows],bool))
        metadata=dict(version=1,state_dim=13,action_dim=7,actions=ACTIONS,features=FEATURES,config=asdict(self.config),training_steps=self.training_steps,rng_state=self.rng.bit_generator.state,replay_rng_state=self.replay.rng.bit_generator.state)
        (path/'checkpoint.json').write_text(json.dumps(metadata,indent=2)+'\n')
    @classmethod
    def load(cls,path):
        path=Path(path);m=json.loads((path/'checkpoint.json').read_text())
        if m['version']!=1 or m['state_dim']!=13 or m['action_dim']!=7 or tuple(m['actions'])!=ACTIONS or tuple(m['features'])!=FEATURES:raise ValueError('Incompatible pricing checkpoint contract.')
        obj=cls(DQNConfig(**m['config']))
        obj.online=tf.keras.models.load_model(path/'online.keras');obj.target=tf.keras.models.load_model(path/'target.keras',compile=False)
        for model in (obj.online,obj.target):
            if model.input_shape!=(None,13) or model.output_shape!=(None,7) or [l.units for l in model.layers]!=[64,64,7] or [l.activation.__name__ for l in model.layers]!=['relu','relu','linear']:raise ValueError('Incompatible Q-network architecture.')
        if not isinstance(obj.online.optimizer,tf.keras.optimizers.Adam):raise ValueError('Checkpoint requires Adam optimizer.')
        steps=m['training_steps']
        if not isinstance(steps,int) or steps<0 or int(obj.online.optimizer.iterations)!=steps:raise ValueError('Inconsistent optimizer/training step.')
        with np.load(path/'replay.npz',allow_pickle=False) as data:
            sizes=[len(data[k]) for k in ('states','actions','rewards','next_states','dones')]
            if len(set(sizes))!=1 or sizes[0]>obj.config.replay_capacity:raise ValueError('Invalid persisted replay.')
            for row in zip(data['states'],data['actions'],data['rewards'],data['next_states'],data['dones']):obj.replay.add(*row)
        obj.training_steps=steps;obj.rng.bit_generator.state=m['rng_state'];obj.replay.rng.bit_generator.state=m['replay_rng_state']
        return obj
