"""Preserve environment random streams around the physical-only episode reset."""
import copy,random
import numpy as np
from src.simulation.multi_episode_od import advance_episode

def advance_with_environment_rng(runtime,factory):
    # Fleet/SOC initialization is deliberately seed42; stochastic runtime streams
    # are distinct and must retain their state (notably charging queue tie breaks).
    owners={'engine':runtime.engine,'charging':runtime.engine.charging,'customer':getattr(runtime.engine,'customer',None)}
    streams={}
    for label,owner in owners.items():
        if owner is not None:
            for name,value in vars(owner).items():
                if isinstance(value,(np.random.Generator,np.random.RandomState,random.Random)):
                    streams[(label,name)]=copy.deepcopy(value)
    new=advance_episode(runtime,factory)
    targets={'engine':new.engine,'charging':new.engine.charging,'customer':getattr(new.engine,'customer',None)}
    for (label,name),value in streams.items():
        if targets[label] is None or not hasattr(targets[label],name):raise ValueError('Reset lost a stochastic owner')
        setattr(targets[label],name,value)
    new.reset_evidence['environment_rng_streams_preserved']=[label+'.'+name for label,name in streams]
    return new
