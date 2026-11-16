"""V3 request boundary adapter; frozen dispatch lifecycle validation retained."""
from dataclasses import fields
import math
import numpy as np
from src.dispatch.request import RequestState
from src.pricing.slot_v3 import load_contract,pmax,VERSION
class V3Request(RequestState):
 def validate(self,valid_grid_ids,mini_slots_per_main_slot):
  if self.customer_model!=VERSION:return super().validate(valid_grid_ids,mini_slots_per_main_slot)
  c=load_contract()
  if self.pricing_factor not in c['actions'] or self.base_fare!=c['P_base'] or self.offered_fare!=self.pricing_factor*self.base_fare:raise ValueError('V3 offer mismatch')
  raw=pmax(self.trip_distance_km,self.epsilon_customer,c)
  if not math.isclose(raw,self.p_max,rel_tol=1e-12) or not isinstance(self.customer_accepted,bool) or self.customer_accepted!=(self.offered_fare<=raw) or self.acceptance_probability is not None:raise ValueError('V3 acceptance mismatch')
  # Validate all original geometry/time/assignment fields through immutable base,
  # with only the separately validated pricing audit omitted from a copy.
  values={f.name:getattr(self,f.name) for f in fields(RequestState)}
  for key in ['pricing_factor','offered_fare','customer_accepted','customer_model','weather_code','period','historical_p_base','historical_d_base','epsilon_customer','p_max']:values[key]=None
  RequestState(**values).validate(valid_grid_ids,mini_slots_per_main_slot)
 @classmethod
 def adapt(cls,r):
  if isinstance(r,cls):return r
  return cls(**{f.name:getattr(r,f.name) for f in fields(RequestState)})
