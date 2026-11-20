"""Opt-in driver-local storage and nonprivate next-slot FedAvg lifecycle."""
from dataclasses import asdict
import copy
import numpy as np
import pandas as pd
from src.routing.learning import LocalRoutingLearner,RoutingLearningParameters,LocalPolicyObservation,build_routing_policy_model,masked_softmax
from src.routing.federated import aggregate_policy_updates
VERSION='DRIVER_LOCAL_NEXT_SLOT_FEDAVG_V1'

class DriverHierarchy:
    def __init__(self, *, mode='UTILITY', seed=42, updates_enabled=False, parameters=None, aggregation="SAMPLE_WEIGHTED_ACTUAL_LOCAL_BATCH_V1"):
        if mode not in {'UTILITY','FRESH_UNTRAINED_GLOBAL'}:raise ValueError('Only utility or explicit fresh research initialization permitted; historical lineage rejected')
        if updates_enabled and mode!='FRESH_UNTRAINED_GLOBAL':raise ValueError('Utility baseline cannot train')
        if aggregation not in {"SAMPLE_WEIGHTED_ACTUAL_LOCAL_BATCH_V1","EQUAL_PARTICIPATING_CLIENT_V1"}:raise ValueError("Unknown aggregation contract")
        self.aggregation=aggregation
        self.mode=mode;self.seed=seed;self.updates_enabled=updates_enabled
        self.parameters=parameters or RoutingLearningParameters();self.parameters.validate()
        self._global=build_routing_policy_model(self.parameters,seed=seed) if mode!='UTILITY' else None
        self._locals={};self._memory={};self.round=0;self.available_at=None;self.last_end=None
    def record(self,driver,observation):
        if observation.slot_id!=self.round:raise ValueError('Local observation outside active federation slot')
        from src.routing.learning import _validate_observation
        _validate_observation(observation)
        self._memory.setdefault(int(driver),[]).append(copy.deepcopy(observation))
        self._memory[int(driver)]=self._memory[int(driver)][-self.parameters.local_observation_capacity:]
    def finish_slot(self,start,end):
        start=pd.Timestamp(start);end=pd.Timestamp(end)
        if start.tz is None or end.tz is None or end-start!=pd.Timedelta(minutes=30) or (self.last_end is not None and start!=self.last_end):raise ValueError('Invalid federation UTC boundary')
        uploads=[]
        if self.updates_enabled:
            weights=self._global.get_weights()
            for driver,memory in sorted(self._memory.items()):
                if not memory or memory[-1].slot_id!=self.round:continue
                if driver not in self._locals:self._locals[driver]=LocalRoutingLearner(driver,self.parameters,seed=self.seed+driver+1)
                learner=self._locals[driver]
                learner.reset_from_global_weights(weights)
                # Persistent local Adam state; only current retained local memory is used.
                learner.observations._items.clear()
                for o in memory:learner.observations.add(o)
                before=learner.local_sample_count;learner.train_for_slot(self.round)
                upload=learner.export_local_update();upload['sample_count']=learner.local_sample_count-before
                if self.aggregation=='EQUAL_PARTICIPATING_CLIENT_V1' and upload['sample_count']>0:upload['sample_count']=1
                uploads.append(upload)
            result=aggregate_policy_updates(uploads,round_index=self.round)
            if result.updated:self._global.set_weights(result.weights)
        self.round+=1;self.last_end=end;self.available_at=end
        return {'version':VERSION,'round':self.round,'participants':len(uploads),'privacy':'NONPRIVATE','available_at':str(end)}
    def mean_probabilities(self,vectors,masks,timestamp):
        t=pd.Timestamp(timestamp)
        if t.tz is None or (self.available_at is not None and t<self.available_at):raise ValueError('Future global routing policy')
        if self._global is None:raise ValueError('Utility probabilities are produced by the private driver utility baseline')
        logits=self._global(np.stack(vectors),training=False).numpy()
        return {g:masked_softmax(logits[g],masks[g]) for g in masks}
    def contract(self):
        return dict(version=VERSION,mode=self.mode,updates_enabled=self.updates_enabled,seed=self.seed,parameters={**asdict(self.parameters),'hidden_units':list(self.parameters.hidden_units)},aggregation=self.aggregation,optimizer='PERSISTENT_LOCAL_ADAM',privacy='NONPRIVATE')
    def snapshot(self):
        def obs(o):return dict(state=o.state.copy(),chosen_action_index=o.chosen_action_index,action_mask=o.action_mask.copy(),utility_vector=o.utility_vector,slot_id=o.slot_id)
        return dict(version=VERSION,aggregation=self.aggregation,mode=self.mode,seed=self.seed,updates_enabled=self.updates_enabled,parameters=asdict(self.parameters),round=self.round,available_at=self.available_at,last_end=self.last_end,
            weights=None if self._global is None else self._global.get_weights(),memory={d:[obs(o) for o in m] for d,m in self._memory.items()},
            locals={d:dict(weights=l.policy_model.get_weights(),optimizer=[v.numpy() for v in l.optimizer.variables],gradient_updates=l.gradient_updates,sample_count=l.local_sample_count,trained_slots=sorted(l._trained_slots)) for d,l in self._locals.items()})
    @classmethod
    def restore(cls,s):
        if s['version']!=VERSION:raise ValueError('Hierarchy checkpoint mismatch')
        x=cls(mode=s['mode'],seed=s['seed'],updates_enabled=s['updates_enabled'],parameters=RoutingLearningParameters(**s['parameters']),aggregation=s.get('aggregation','SAMPLE_WEIGHTED_ACTUAL_LOCAL_BATCH_V1'))
        if x._global is not None:x._global.set_weights(s['weights'])
        x.round=s['round'];x.available_at=s['available_at'];x.last_end=s['last_end']
        x._memory={d:[LocalPolicyObservation(**o) for o in m] for d,m in s['memory'].items()}
        for d,v in s['locals'].items():
            l=LocalRoutingLearner(d,x.parameters,seed=x.seed+d+1);l.policy_model.set_weights(v['weights']);l.optimizer.build(l.policy_model.trainable_variables)
            if len(l.optimizer.variables)!=len(v['optimizer']):raise ValueError('Local optimizer contract mismatch')
            for target,value in zip(l.optimizer.variables,v['optimizer']):target.assign(value)
            l.gradient_updates=v['gradient_updates'];l.local_sample_count=v['sample_count'];l._trained_slots=set(v['trained_slots']);x._locals[d]=l
        return x
