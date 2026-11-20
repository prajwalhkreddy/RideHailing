import unittest,json,tempfile,hashlib,copy
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np,pandas as pd
from src.fleet.state import VehicleStatus
from src.simulation.research_utility_routing import probabilities,validate,VERSION
from src.simulation.information_cutoff import validate_manifest
class UtilityTests(unittest.TestCase):
 def test_deterministic_frequency_private_inputs_and_empty_grid(self):
  class Routing:
   calls=0
   def decide(self,producer,timestamp,**k):
    self.calls+=1
    assert k['h_max_minutes']==10 and k['p_min']==20
    return S(action_index=1 if k['energy_kwh']>10 else 0)
   def label(self,d,g):return d.action_index
  vehicles=[S(vehicle_id=i,current_grid=0,trip_status=VehicleStatus.IDLE,energy_level=e) for i,e in enumerate([20,5])]
  engine=S(routing=Routing(),fleet=S(vehicles=vehicles),charging=S(vehicle_station={}),profiles=pd.DataFrame(dict(price_preference=[20,20],wait_preference=[5,5],charging_wait_preference_minutes=[10,10])),energy=S(battery_capacity_kwh=50,charging_trigger_soc=.2,consumption_rate_kwh_per_km=.2),timestamp=pd.Timestamp('2026-03-12',tz='UTC'),operational=object())
  masks={g:np.array([True,True]+[False]*7) for g in [0,1]}
  a=probabilities(engine,masks);b=probabilities(engine,masks)
  np.testing.assert_array_equal(a[0],[.5,.5,0,0,0,0,0,0,0]);self.assertEqual(a[1][0],1)
  for g in a:np.testing.assert_array_equal(a[g],b[g])
  self.assertEqual(engine.routing.calls,0)
  masks[0][1]=False
  with self.assertRaises(ValueError):probabilities(engine,masks)
 def test_nonlearned_contract_cannot_hide_weights(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'routing.json';c=dict(version=VERSION,learned=False,probabilities='idle-fleet deterministic-action frequencies; empty-grid STAY',utility='existing operational_interface.decide');p.write_text(json.dumps(c));validate(p)
   a=dict(kind='NONLEARNED',path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),methodology_version=VERSION,fitted_observations=0)
   m=dict(version='PROSPECTIVE_INFORMATION_CUTOFF_V1',artifacts={'routing':a},permitted_cutoffs={'routing':'2026-03-12T00:00:00-04:00'});validate_manifest(m)
   a['fitted_observations']=1
   with self.assertRaises(ValueError):validate_manifest(m)
   c['learned']=True;p.write_text(json.dumps(c))
   with self.assertRaises(ValueError):validate(p)
