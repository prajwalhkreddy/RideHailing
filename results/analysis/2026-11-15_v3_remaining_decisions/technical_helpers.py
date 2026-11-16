"""Offline V3 decision-validation helpers; not wired into production."""
import numpy as np
import pandas as pd
FEATURES=('predicted_demand','idle_supply','incoming_supply','previous_dispatch','p_STAY','p_N','p_NE','p_E','p_SE','p_S','p_SW','p_W','p_NW','dropoff_probability','destination_popularity')
def permitted(t):
 t=pd.Timestamp(t)
 if not pd.Timestamp('2026-01-01')<=t<pd.Timestamp('2026-03-16'):raise ValueError('Protected or non-calibration date')
 return t
class DropoffAdapter:
 def __init__(self,initial=None,initial_available=None):
  self.initial=None if initial is None else self.validate(initial)
  self.initial_available=None if initial_available is None else pd.Timestamp(initial_available)
  self.previous=None;self.last_time=None
 @staticmethod
 def validate(v):
  v=np.array(v,dtype=float,copy=True)
  if v.shape!=(142,) or not np.isfinite(v).all() or (v<0).any() or not np.isclose(v.sum(),1,atol=1e-12,rtol=0):raise ValueError('Invalid probability vector')
  return v
 def build(self,lag,t,observed_through):
  t=permitted(t)
  if pd.Timestamp(observed_through)>=t or (self.last_time is not None and t<=self.last_time):raise ValueError('Noncausal or unordered slot')
  a=np.asarray(lag,float)
  if a.shape!=(142,) or not np.isfinite(a).all() or (a<0).any():raise ValueError('Invalid lagged measure')
  if a.sum()>0:v=a/a.sum();level='NORMALIZED'
  elif self.previous is not None:v=self.previous.copy();level='CARRY_FORWARD'
  elif self.initial is not None and self.initial_available is not None and self.initial_available<t:v=self.initial.copy();level='HISTORICAL_INITIALIZATION'
  else:raise ValueError('DROP_OFF_PROBABILITY_INITIALIZATION_UNAVAILABLE')
  self.previous=self.validate(v);self.last_time=t
  return self.previous.copy(),level
def state(values):
 if set(values)!=set(FEATURES):raise ValueError('Wrong state fields')
 a=np.array([values[k] for k in FEATURES],float)
 if not np.isfinite(a).all():raise ValueError('Nonfinite state')
 return a

def dominated(a):
 a=np.asarray(a,float)
 return np.array([any(np.all(b<=x) and np.any(b<x) for b in a) for x in a])
def factors(low,high,base):
 if not 0<low<high or not base>0:raise ValueError('Invalid bounds')
 return np.linspace(low/base,high/base,7)
