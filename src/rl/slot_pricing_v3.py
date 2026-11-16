"""Fresh V3 15D/7-action learner and destination-slot replay; no legacy weights."""
from collections import deque
from pathlib import Path
import json
import numpy as np
import tensorflow as tf
from src.pricing.slot_v3 import VERSION,CONTRACT,sha,load_contract,validate_state
from src.rl.pricing_dqn import DQNConfig,action_index,soft_update,bellman_targets
class SlotDQN:
 def __init__(self,seed=42):
  self.contract=load_contract();self.contract_hash=sha(CONTRACT);self.config=DQNConfig(seed=seed);self.rng=np.random.default_rng(seed);self.replay=deque(maxlen=100000);self.training_steps=0;self.decisions=0
  tf.keras.utils.set_random_seed(seed)
  def build():return tf.keras.Sequential([tf.keras.Input((15,)),tf.keras.layers.Dense(64,activation='relu'),tf.keras.layers.Dense(64,activation='relu'),tf.keras.layers.Dense(7)])
  self.online=build();self.target=build();self.target.set_weights(self.online.get_weights());self.online.compile(optimizer=tf.keras.optimizers.Adam(.001),loss=tf.keras.losses.Huber());self.online.optimizer.build(self.online.trainable_variables)
 @property
 def epsilon(self):
  return max(.05,1-.95*self.training_steps/50000)
 def select_action(self,state,explore=True):
  s=validate_state(state);epsilon=self.epsilon
  q=self.online(s[None],training=False).numpy()[0]
  if not np.isfinite(q).all():raise ValueError('Invalid Q')
  a=int(self.rng.integers(7)) if explore and self.rng.random()<epsilon else int(q.argmax());self.decisions+=1;return a
 def store(self,s,a,r,n,done):
  s=validate_state(s);n=validate_state(n);a=action_index(a)
  if not isinstance(done,(bool,np.bool_)) or not np.isfinite(r) or r<0:raise ValueError('Invalid slot transition')
  self.replay.append((s.copy(),a,float(r),n.copy(),bool(done)))
 def train_step(self):
  if len(self.replay)<1000:return None
  ix=self.rng.choice(len(self.replay),64,replace=False);r=[self.replay[i] for i in ix];s,a,re,n,d=zip(*r);s=np.stack(s);n=np.stack(n);y=bellman_targets(re,np.array(d,bool),self.target(n,training=False).numpy(),.99)
  with tf.GradientTape() as tape:
   q=tf.gather(self.online(s,training=True),a,axis=1,batch_dims=1);diff=y-q;loss=tf.reduce_mean(tf.where(tf.abs(diff)<=1,.5*diff**2,tf.abs(diff)-.5))
  grad=tape.gradient(loss,self.online.trainable_variables)
  if not np.isfinite(float(loss)) or any(g is None or not np.isfinite(g.numpy()).all() for g in grad):raise ValueError('Nonfinite update')
  self.online.optimizer.apply_gradients(zip(grad,self.online.trainable_variables));soft_update(self.online,self.target,.005);self.training_steps+=1;return float(loss)
 def save(self,path):
  p=Path(path);p.mkdir(parents=True,exist_ok=False);self.online.save(p/'online.keras');self.target.save(p/'target.keras')
  rows=list(self.replay);np.savez_compressed(p/'replay.npz',s=np.array([x[0] for x in rows]).reshape(-1,15),a=np.array([x[1] for x in rows]),r=np.array([x[2] for x in rows]),n=np.array([x[3] for x in rows]).reshape(-1,15),d=np.array([x[4] for x in rows],bool))
  (p/'checkpoint.json').write_text(json.dumps(dict(version=VERSION,versions=self.contract['versions'],contract_hash=self.contract_hash,seed=self.config.seed,training_steps=self.training_steps,decisions=self.decisions,rng=self.rng.bit_generator.state)))
 @classmethod
 def load(cls,path):
  p=Path(path);m=json.loads((p/'checkpoint.json').read_text())
  if m.get('version')!=VERSION or m.get('contract_hash')!=sha(CONTRACT) or m.get('versions')!=load_contract()['versions']:raise ValueError('Legacy/incompatible checkpoint rejected')
  obj=cls(m['seed']);obj.online=tf.keras.models.load_model(p/'online.keras');obj.target=tf.keras.models.load_model(p/'target.keras',compile=False)
  for net in [obj.online,obj.target]:
   if net.input_shape!=(None,15) or net.output_shape!=(None,7) or [l.units for l in net.layers]!=[64,64,7]:raise ValueError('Invalid V3 network')
  with np.load(p/'replay.npz',allow_pickle=False) as z:
   if len({len(z[k]) for k in ['s','a','r','n','d']})!=1 or len(z['s'])>100000:raise ValueError('Invalid replay')
   for row in zip(z['s'],z['a'],z['r'],z['n'],z['d']):obj.store(*row)
  obj.training_steps=m['training_steps'];obj.decisions=m['decisions'];obj.rng.bit_generator.state=m['rng']
  if int(obj.online.optimizer.iterations)!=obj.training_steps:raise ValueError('Optimizer count mismatch')
  return obj
