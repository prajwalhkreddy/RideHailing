"""Thin fixed-feasible-OD action adapter; no private driver data in info."""
import gymnasium as gym
import numpy as np
class ODPricingEnv(gym.Env):
    metadata={'render_modes':[]}
    def __init__(self,runtime_factory,pairs,*,horizon=16):
        super().__init__()
        self.factory=runtime_factory;self.pairs=tuple(pairs);self.horizon=horizon;self.runtime=None
        if not self.pairs or len(set(self.pairs))!=len(self.pairs) or not 1<=horizon<=16:raise ValueError('Invalid OD environment contract')
        self.action_space=gym.spaces.MultiDiscrete(np.full(len(self.pairs),7,dtype=np.int64))
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(len(self.pairs),13),dtype=np.float32)
    def _observation(self):
        x=np.stack([self.runtime.states[p] for p in self.pairs]).astype(np.float32)
        if not np.isfinite(x).all():raise ValueError('Nonfinite OD state')
        return x
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        if options:raise ValueError('No runtime mutation via reset options')
        self.runtime=self.factory(seed=seed)
        if tuple(self.runtime.pairs)!=self.pairs:raise ValueError('Feasible OD identity mismatch')
        self.steps=0
        return self._observation(),{'od_pairs':self.pairs}
    def step(self,action):
        if self.runtime is None or self.steps>=self.horizon:raise RuntimeError('Reset required')
        if not self.action_space.contains(action):raise ValueError('Invalid OD action vector')
        actions=dict(zip(self.pairs,map(int,action)))
        rows=self.runtime.run_slot(policy=lambda pair,state:actions[pair]);self.steps+=1
        reward=float(self.runtime.system_revenue)
        return self._observation(),reward,self.runtime.slots>=16,self.steps>=self.horizon and self.runtime.slots<16,{'accepted':sum(r['accepted'] for r in rows),'assigned':sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in rows),'supported_reward':float(self.runtime.environment_reward),'fallback_reward':reward-float(self.runtime.environment_reward)}
