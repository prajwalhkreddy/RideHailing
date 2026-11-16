"""Opt-in V3 contracts, fitted sampling and causal destination state adapters."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from scipy import stats
from src.pricing.dqn_contract import ROOT
from src.pricing.supply import build_raw_pricing_supply
VERSION='SOURCE_ALIGNED_SLOT_PRICING_V3'
CONTRACT=ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/methodology_contract.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allowed(t):
 t=pd.Timestamp(t)
 if t.tz is not None or not pd.Timestamp('2026-03-01')<=t<pd.Timestamp('2026-03-17'):raise ValueError('V3 date outside allowed training/development')
 return t

def load_contract():
 c=json.loads(CONTRACT.read_text())
 if c['version']!=VERSION or c['gamma']!=.99 or c['episode_slots']!=16:raise ValueError('V3 contract mismatch')
 for p,h in c['source_hashes'].items():
  if sha(ROOT/p)!=h:raise ValueError('V3 source hash mismatch: '+p)
 a=np.array(c['actions']);expected=np.linspace(6.6/c['P_base'],94.7/c['P_base'],7)
 if not np.allclose(a,expected,rtol=0,atol=1e-15):raise ValueError('V3 action mismatch')
 return c

def validate_state(x):
 x=np.asarray(x,float)
 if x.shape!=(15,) or not np.isfinite(x).all() or (x<0).any() or (x>np.finfo(np.float32).max).any():raise ValueError('V3 finite nonnegative15D required')
 if not np.isclose(x[4:13].sum(),1) or not 0<=x[13]<=1 or x[14] not in [0,.25,.5,.75,1]:raise ValueError('Invalid probability/popularity')
 return x.astype(np.float32)

class FittedSensitivity:
 def __init__(self,seed=42):
  self.contract=load_contract();self.rng=np.random.default_rng(seed);self.audit=[]
  self.grouping=json.loads((ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/weather_time_grouping_contract.json').read_text())
  self.mapping={(r['raw_weather_code'],r['T_group']):r for r in self.grouping['mapping']}
  self.counts=pd.read_csv(ROOT/'results/analysis/2026-11-14_pricing_v2_time_specific_weather/conditional_support_manifest.csv').set_index('support_id').N.to_dict()
 def select(self,code,t):
  t=allowed(t)
  if not np.isfinite(code) or int(code)!=code:raise ValueError('Integer weather required')
  T='T1' if t.hour<4 else 'T2' if t.hour<6 else 'T3' if t.hour<16 else 'T4';row=self.mapping.get((int(code),T),{});g=row.get('time_specific_weather_group','');opts=[]
  if g:opts.append((g,0))
  if T=='T1':opts.append(('RAW_'+str(int(code)),1))
  opts += [(T+'_POOLED',2),('GLOBAL',3)]
  for sid,level in opts:
   if self.counts.get(sid,0)>=5000:
    if sid not in self.contract['conditions']:raise ValueError('Selected fitted condition absent')
    return sid,level,T
  raise ValueError('No valid fallback')
 def distribution(self,sid):
  c=self.contract['conditions'][sid];d={'Truncated_normal':stats.truncnorm,'Lognormal':stats.lognorm,'Generalized_gamma':stats.gengamma}[c['family']]
  return d(*c['parameters'])
 def draw(self,code,t):
  sid,level,T=self.select(code,t);e=float(self.distribution(sid).rvs(random_state=self.rng))
  if not np.isfinite(e) or e<=0:raise ValueError('Invalid fitted draw; no repair permitted')
  m=dict(sensitivity_condition=sid,fallback_level=level,T_group=T,family=self.contract['conditions'][sid]['family'],epsilon=e)
  self.audit.append(dict(timestamp=str(t),weather_code=int(code),**m));return m

def pmax(distance,epsilon,c):
 if not np.isfinite([distance,epsilon]).all() or distance<0 or epsilon<=0:raise ValueError('Invalid distance/sensitivity')
 p=c['P_base']+(c['P_base']/epsilon)*((distance-c['L_base'])/c['L_base'])
 if not np.isfinite(p):raise ValueError('Nonfinite ceiling')
 return float(p)

class DropoffProbability:
 def __init__(self):
  path=ROOT/'results/analysis/2026-11-15_v3_remaining_decisions/dropoff_probability_contract.json';c=json.loads(path.read_text());self.initial=np.array(c['initialization']);self.available=pd.Timestamp(c['initialization_available_before']);self.previous=None;self.last=None;self.audit=[]
 def build(self,t):
  t=allowed(t)
  if self.last is not None and t<=self.last:raise ValueError('Dropoff chronology')
  f=pd.read_parquet(ROOT/'data/processed/spatial_3km_jan_mar_2026/destination_popularity.parquet',columns=['TimeSlot','GridID','dropoff_ma_3h'],filters=[('TimeSlot','==',t)])
  if len(f)!=142 or f.GridID.nunique()!=142:raise ValueError('Missing dropoff grids')
  a=f.set_index('GridID').reindex(range(142)).dropoff_ma_3h.to_numpy()
  if not np.isfinite(a).all() or (a<0).any():raise ValueError('Invalid lagged dropoffs')
  if a.sum()>0:v=a/a.sum();level='NORMALIZED'
  elif self.previous is not None:v=self.previous.copy();level='CARRY_FORWARD'
  elif self.available<=t:v=self.initial.copy();level='HISTORICAL_INITIALIZATION'
  else:raise ValueError('DROP_OFF_PROBABILITY_INITIALIZATION_UNAVAILABLE')
  if not np.isfinite(v).all() or (v<0).any() or not np.isclose(v.sum(),1,atol=1e-12):raise ValueError('Invalid dropoff probabilities')
  self.previous=v.copy();self.last=t;self.audit.append(dict(timestamp=str(t),fallback=level));return v

def destination_states(engine,dropoff):
 t=allowed(engine.timestamp);b=engine.current_states;supply=build_raw_pricing_supply(engine.fleet.vehicles,range(142),t.to_pydatetime()).set_index('grid_id');p=dropoff.build(t)
 return {d:validate_state([b.forecast.get(d,t),supply.loc[d,'idle_supply'],supply.loc[d,'incoming_supply'],b.ledger.previous(t)[d],*b.routing.get(d,t),p[d],b.popularity.get(d,t)]) for d in range(142)}
