"""Explicitly versioned time-specific V2 empirical sampling, separate from pooled V2."""
from pathlib import Path
import copy,json
import numpy as np
from src.pricing.passenger_sensitive_v2 import V2EmpiricalSensitivityProvider,sha256
from src.pricing.passenger_sensitive_v1 import EpsilonDraw,guard_date
VERSION='WEATHER_TIME_CONDITIONED_V2'
DEFAULT_GROUPING='results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json'
class ConditionedV2SensitivityProvider(V2EmpiricalSensitivityProvider):
 version=VERSION
 def __init__(self,*,rng,root=None,grouping_path=DEFAULT_GROUPING,expected_grouping_hash=None,**kwargs):
  super().__init__(rng=rng,root=root,**kwargs)
  import pandas as pd
  path=self.root/grouping_path;self.grouping_hash=sha256(path)
  if expected_grouping_hash is None or self.grouping_hash!=expected_grouping_hash:raise ValueError('Pinned grouping contract hash required')
  c=json.loads(path.read_text());self.grouping=c
  if c['methodology_version']!='WEATHER_TIME_CONDITIONED_V2_2026_11_14' or c['T_group_definitions']!={'T1':[0,4],'T2':[4,6],'T3':[6,16],'T4':[16,24]}:raise ValueError('Invalid conditional contract')
  for p,h in c['source_hashes'].items():
   if sha256(self.root/p)!=h:raise ValueError('Conditional provenance mismatch')
  directory=path.parent
  for file,key in [('weather_time_group_mapping.csv','mapping_hash'),('conditional_support_manifest.csv','conditional_support_manifest_hash')]:
   if sha256(directory/file)!=c[key]:raise ValueError('Mapping/support manifest mismatch')
  self.mapping={(r['raw_weather_code'],r['T_group']):r for r in c['mapping']}
  if len(self.mapping)!=len(c['mapping']):raise ValueError('Duplicate weather/time mapping')
  csv=pd.read_csv(directory/'weather_time_group_mapping.csv').fillna('')
  for r in csv.to_dict('records'):
   m=self.mapping.get((r['raw_weather_code'],r['T_group']))
   if m is None or m['time_specific_weather_group']!=r['time_specific_weather_group'] or m['assignment_type']!=r['assignment_type']:raise ValueError('Mapping table/contract disagreement')
  if c['fallback_policy']['version']!='TIME_SPECIFIC_RAW_WEATHER_FALLBACK_1' or c['fallback_policy']['minimum_N']!=5000:raise ValueError('Unknown fallback policy')
  self.supports={};self.support_metadata={}
  for r in pd.read_csv(directory/'conditional_support_manifest.csv').to_dict('records'):
   p=self.root/r['path']
   if sha256(p)!=r['support_hash']:raise ValueError('Conditional support hash mismatch')
   a=np.load(p,mmap_mode='r',allow_pickle=False)
   if a.ndim!=1 or len(a)!=r['N'] or not np.isfinite(a).all() or (a<=0).any():raise ValueError('Invalid conditional empirical support')
   self.supports[r['support_id']]=a;self.support_metadata[r['support_id']]=r
  if len(self.supports['GLOBAL'])!=len(self.values) or not np.array_equal(self.supports['GLOBAL'],self.values):raise ValueError('Global fallback differs from canonical pool')
  self.fallback_counts={str(i):0 for i in range(4)}
 def time_group(self,h):
  if not isinstance(h,(int,np.integer)) or not 0<=h<24:raise ValueError('Invalid hour')
  return 'T1' if h<4 else 'T2' if h<6 else 'T3' if h<16 else 'T4'
 def select_support(self,raw_weather_code,hour):
  if not np.isfinite(raw_weather_code) or int(raw_weather_code)!=raw_weather_code:raise ValueError('Finite integer weather code required')
  code=int(raw_weather_code);t=self.time_group(hour);row=self.mapping.get((code,t));group=row['time_specific_weather_group'] if row else '';pooled_t=self.grouping['selected_K_per_T'][t] is None
  options=[]
  if group:options.append((group,0))
  if not pooled_t:options.append(('RAW_'+str(code),1))
  options.extend([(t+'_POOLED',2),('GLOBAL',3)])
  for sid,level in options:
   if sid in self.supports and len(self.supports[sid])>=5000:
    return dict(raw_weather_code=code,T_group=t,time_specific_weather_group=group or ('T_GROUP_POOLED_FALLBACK' if pooled_t else 'CELL_FALLBACK'),support_id=sid,support_hash=self.support_metadata[sid]['support_hash'],fallback_level=level)
  raise ValueError('No sufficient conditional/fallback support')
 def sample_request(self,raw_weather_code,timestamp):
  t=guard_date(timestamp);meta=self.select_support(raw_weather_code,t.hour);a=self.supports[meta['support_id']];v=float(a[self.rng.integers(len(a))]);self.fallback_counts[str(meta['fallback_level'])]+=1;meta['sampled_epsilon']=v
  return EpsilonDraw(v,v,0.),meta
 def sample(self):raise ValueError('Conditional sampling requires weather and timestamp')
 def sample_many(self,n):raise ValueError('Conditional sampling requires request contexts')
 def state_dict(self):
  state=super().state_dict();state.update(sensitivity_version=VERSION,passenger_sensitivity_version=VERSION,weather_time_grouping_version=self.grouping['methodology_version'],mapping_hash=self.grouping['mapping_hash'],conditional_support_manifest_hash=self.grouping['conditional_support_manifest_hash'],fallback_policy_version=self.grouping['fallback_policy']['version'],grouping_contract_hash=self.grouping_hash,fallback_counts=copy.deepcopy(self.fallback_counts));return state
 def load_state_dict(self,state):
  expected=self.state_dict()
  for key in ['sensitivity_version','passenger_sensitivity_version','weather_time_grouping_version','mapping_hash','conditional_support_manifest_hash','fallback_policy_version','grouping_contract_hash','contract_sha256','empirical_support_sha256']:
   if state.get(key)!=expected[key]:raise ValueError('Pooled/conditional checkpoint or contract mismatch: '+key)
  self.rng.bit_generator.state=copy.deepcopy(state['rng_state']);self.fallback_counts=copy.deepcopy(state['fallback_counts'])
 def require_training_ready(self):
  super().require_training_ready()
  gate=self.root/'results/training/pricing_v2_staged_training_001/weather_conditioned/prelaunch_verification.json'
  if not gate.exists():raise ValueError('Conditional launch gate absent')
  g=json.loads(gate.read_text())
  if g.get('verdict')!='READY_TO_LAUNCH_V2_STAGE25' or g.get('grouping_contract_hash')!=self.grouping_hash:raise ValueError('Conditional launch gate not ready')
