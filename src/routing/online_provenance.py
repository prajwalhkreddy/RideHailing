"""Fresh-only online lineage; never certifies historical learned weights."""
import copy,hashlib,json
from pathlib import Path
import pandas as pd
import numpy as np
from src.routing.research_hierarchy import DriverHierarchy
from src.routing.learning import RoutingLearningParameters
VERSION='FRESH_PROSPECTIVE_ONLINE_ROUTING_V1'
MULTI_VERSION='FRESH_CHRONOLOGICAL_ONLINE_ROUTING_V2'
AGGREGATION='EQUAL_PARTICIPATING_CLIENT_V1'
SOURCES=['src/simulation/od_pricing_runtime.py','src/simulation/od_pricing_checkpoint.py','src/simulation/final_production.py','src/routing/online_provenance.py','src/routing/research_hierarchy.py','src/routing/learning.py','src/routing/federated.py','src/routing/configuration.py']
def utc(x):
 t=pd.Timestamp(x)
 if pd.isna(t) or t.tz is None:raise ValueError('Aware routing timestamp required')
 return t.tz_convert('UTC')
def digest(c):return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def weight_hash(weights):
 h=hashlib.sha256()
 for w in weights:h.update(str(w.shape).encode());h.update(w.tobytes())
 return h.hexdigest()
def validate(c):
 if c['version'] not in {VERSION,MULTI_VERSION} or c['initialization']!='FRESH_SEEDED_EXISTING_KERAS_INITIALIZERS' or c['offline_fitting_period'] is not None or c['validation_selection_period'] is not None or c['historical_checkpoint'] is not None:raise ValueError('Historical/fitted routing lineage rejected')
 if c['architecture']!=[169,64,32,9] or c['aggregation']!=AGGREGATION or c['privacy']!='NONPRIVATE':raise ValueError('Routing methodology mismatch')
 expected_start='2026-03-01T05:00Z' if c['version']==MULTI_VERSION else '2026-03-12T04:00Z'
 if c['version']==MULTI_VERSION and utc(c['experience_end_exclusive'])!=pd.Timestamp('2026-03-12T21:00Z'):raise ValueError('Invalid multi-episode cutoff')
 if utc(c['experiment_start'])!=pd.Timestamp(expected_start) or utc(c['experience_end_exclusive'])<=utc(c['experiment_start']):raise ValueError('Invalid experiment experience window')
 if c['initial_federation_round']!=0 or c['initial_global_version']!=0:raise ValueError('Fresh initialization required')
 if set(c['source_sha256'])!=set(SOURCES):raise ValueError('Incomplete initialization sources')
 for p,h in c['source_sha256'].items():
  if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h:raise ValueError('Routing source fingerprint mismatch')
 if hashlib.sha256(Path('config/config.yaml').read_bytes()).hexdigest()!=c['configuration_sha256']:raise ValueError('Routing configuration mismatch')
 if c['seed']!=42 or c['local_seed_rule']!='global_seed + driver_id + 1':raise ValueError('Unapproved initialization seed contract')
 RoutingLearningParameters(**c['parameters']).validate()

class OnlineHierarchy(DriverHierarchy):
 def __init__(self,provenance,*,updates_enabled=False):
  validate(provenance);self.provenance=copy.deepcopy(provenance)
  super().__init__(mode='FRESH_UNTRAINED_GLOBAL',seed=provenance['seed'],parameters=RoutingLearningParameters(**provenance['parameters']),updates_enabled=updates_enabled,aggregation=AGGREGATION)
  if weight_hash(self._global.get_weights())!=provenance['initial_weights_sha256']:raise ValueError('Fresh initialization identity mismatch')
  self.available_at=utc(provenance['experiment_start']);self.experience_cutoff=self.available_at;self.global_version=0;self._event_times={}
 def record(self,driver,observation,*,event_time=None):
  t=utc(event_time);start=utc(self.provenance['experiment_start'])+pd.Timedelta(minutes=30*self.round);end=start+pd.Timedelta(minutes=30)
  if not start<=t<=end or t>utc(self.provenance['experience_end_exclusive']):raise ValueError('Future/out-of-window local experience')
  super().record(driver,observation)
  self._event_times.setdefault(int(driver),[]).append(t);self._event_times[int(driver)]=self._event_times[int(driver)][-self.parameters.local_observation_capacity:]
 def finish_slot(self,start,end):
  start=utc(start);end=utc(end);expected=utc(self.provenance['experiment_start'])+pd.Timedelta(minutes=30*self.round)
  if start!=expected or end>utc(self.provenance['experience_end_exclusive']):raise ValueError('Online update outside approved experiment')
  for driver,memory in self._memory.items():
   times=self._event_times.get(driver,[])
   if len(times)!=len(memory) or any(not utc(self.provenance['experiment_start'])<=t<=end for t in times):raise ValueError('Ineligible local memory')
  result=super().finish_slot(start,end);self.experience_cutoff=end
  if result['participants']:self.global_version+=1
  return dict(result,global_version=self.global_version,initialization_identity=digest(self.provenance),aggregation=AGGREGATION)
 def contract(self):return dict(super().contract(),online_provenance_sha256=digest(self.provenance))
 def snapshot(self):return dict(super().snapshot(),online_provenance=copy.deepcopy(self.provenance),event_times=copy.deepcopy(self._event_times),experience_cutoff=self.experience_cutoff,global_version=self.global_version)
 @classmethod
 def restore(cls,s):
  validate(s['online_provenance']);x=DriverHierarchy.restore(s);x.__class__=cls;x.provenance=copy.deepcopy(s['online_provenance']);x._event_times=copy.deepcopy(s['event_times']);x.experience_cutoff=s['experience_cutoff'];x.global_version=s['global_version']
  if x.aggregation!=AGGREGATION or x.round<0 or not 0<=x.global_version<=x.round:raise ValueError('Online checkpoint version mismatch')
  expected=utc(x.provenance['experiment_start'])+pd.Timedelta(minutes=30*x.round)
  if expected>utc(x.provenance['experience_end_exclusive']) or x.available_at!=expected or x.experience_cutoff!=expected:raise ValueError('Online checkpoint cutoff mismatch')
  for d,memory in x._memory.items():
   times=x._event_times.get(d,[])
   if len(times)!=len(memory) or any(not utc(x.provenance['experiment_start'])<=utc(t)<=expected for t in times):raise ValueError('Future checkpoint memory')
   for o,t in zip(memory,times):
    from src.routing.learning import _validate_observation
    _validate_observation(o)
    if not 0<=o.slot_id<x.round:raise ValueError('Future checkpoint observation slot')
    lo=utc(x.provenance['experiment_start'])+pd.Timedelta(minutes=30*o.slot_id)
    if not lo<=utc(t)<=lo+pd.Timedelta(minutes=30):raise ValueError('Observation timestamp/slot mismatch')
  return x
