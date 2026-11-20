import unittest,tempfile,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from src.simulation.multi_episode_od import episode_bounds,retain_checkpoint,validate_start
from src.rl.od_pricing_dqn import ODPricingDQN
from src.routing.online_provenance import MULTI_VERSION
class MultiEpisodeTests(unittest.TestCase):
 def test_schedule_updates_and_legacy(self):
  a=ODPricingDQN(42,master_math=True,utc_mode=True,exploration_contract='MASTER_UPDATE_STAIRCASE_V1')
  for n,e in [(0,1),(9,1),(10,.995),(128,.94),(256,.875),(1800,.1),(50000,.1)]:a.training_steps=n;self.assertAlmostEqual(a.epsilon,e)
  a.training_steps=0;self.assertIsNone(a.train_step());self.assertEqual(a.epsilon,1)
  s=np.zeros(13,np.float32);s[3]=1
  for i in range(1000):a.store(s,0,1,s,False,identity=('2026-03-01T05:00Z',i//142,i%142))
  for _ in range(10):self.assertTrue(np.isfinite(a.train_step()))
  self.assertEqual(a.training_steps,10);self.assertAlmostEqual(a.epsilon,.995)
  with tempfile.TemporaryDirectory() as d:
   a.save(Path(d)/'model')
   with self.assertRaises(ValueError):ODPricingDQN.load(Path(d)/'model',master_math=True,utc_mode=True)
   b=ODPricingDQN.load(Path(d)/'model',master_math=True,utc_mode=True,exploration_contract='MASTER_UPDATE_STAIRCASE_V1');self.assertEqual(a.epsilon,b.epsilon);self.assertEqual(a.rng.bit_generator.state,b.rng.bit_generator.state)
  old=ODPricingDQN();old.training_steps=128;self.assertAlmostEqual(old.epsilon,.997568)
 def test_dates_dst(self):
  import pandas as pd
  a,b=episode_bounds(34);self.assertEqual(str(b.tz_convert('America/New_York')),'2026-03-12 17:00:00-04:00')
  values=pd.date_range(episode_bounds(0)[0],b,inclusive='left',freq='30min').tz_convert('America/New_York')
  march8=[x for x in values if str(x.date())=='2026-03-08'];self.assertEqual(len(march8),46);self.assertFalse(any(x.hour==2 for x in march8))
  with self.assertRaises(ValueError):episode_bounds(35)
 def test_provenance_boundary(self):
  h=SimpleNamespace(provenance={'version':MULTI_VERSION},round=16)
  validate_start(episode_bounds(1)[0],h)
  with self.assertRaises(ValueError):validate_start(episode_bounds(0)[0],h)
 def test_atomic_failed_write_preserves_good(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);old=root/'latest_episode01_slot04';old.mkdir();(root/'latest').symlink_to(old.name)
   r=SimpleNamespace(slots=8,episode_offset=0)
   def fail(*args):raise OSError('interrupted')
   with patch('shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)):
    with self.assertRaises(OSError):retain_checkpoint(r,root,writer=fail)
   self.assertEqual((root/'latest').resolve(),old.resolve());self.assertTrue(old.exists())
 def test_retention(self):
  with tempfile.TemporaryDirectory() as d,patch('shutil.disk_usage',return_value=SimpleNamespace(free=100*1024**3)):
   def writer(r,p):p.mkdir();(p/'manifest.json').write_text('{}')
   for n in [4,8,12,16]:retain_checkpoint(SimpleNamespace(slots=n,episode_offset=0),d,writer=writer)
   self.assertEqual(len([p for p in Path(d).iterdir() if not p.is_symlink()]),1)
   with self.assertRaises(ValueError):retain_checkpoint(SimpleNamespace(slots=16),d,'unknown',writer)
 def test_reset_persistence_and_rng(self):
  import pandas as pd
  from src.simulation.multi_episode_od import advance_episode
  from src.simulation.v3_checkpoint import rng_bundle
  from scripts.run_full_od_development import hash_value
  h=SimpleNamespace(round=16,_memory={0:[]});profiles=pd.DataFrame({'a':[1]})
  def engine():return SimpleNamespace(driver_hierarchy=h,fleet=SimpleNamespace(vehicles=[SimpleNamespace(vehicle_id=0,is_ev=True)]),profiles=profiles,passengers={},missions={},charging=SimpleNamespace(vehicle_station={}))
  e=engine();e.timestamp=episode_bounds(1)[0]
  r=SimpleNamespace(multi_episode=True,evaluation_mode=False,slots=16,engine=e,learner=object(),provider=object(),slot_audit=[{'x':1}])
  before=hash_value(rng_bundle())
  def factory(start,h):
   np.random.random();return SimpleNamespace(engine=engine(),pairs=[])
  with patch('src.pricing.od_contract.od_states',return_value={}):n=advance_episode(r,factory)
  self.assertIs(n.learner,r.learner);self.assertIs(n.provider,r.provider);self.assertEqual(n.prior_slot_audit,r.slot_audit)
  self.assertEqual(n.engine.routing_slot_offset,16);self.assertEqual(hash_value(rng_bundle()),before)
 def test_evaluation_isolation(self):
  import pandas as pd
  from src.routing.research_hierarchy import DriverHierarchy
  from src.simulation.multi_episode_od import isolated_evaluation
  from src.simulation.v3_checkpoint import rng_bundle
  from scripts.run_full_od_development import hash_value
  h=DriverHierarchy(mode='FRESH_UNTRAINED_GLOBAL',updates_enabled=True)
  h.provenance={'version':MULTI_VERSION};h.experience_cutoff=episode_bounds(1)[0];h.available_at=h.experience_cutoff;h.global_version=16
  learner=ODPricingDQN(master_math=True,utc_mode=True,exploration_contract='MASTER_UPDATE_STAIRCASE_V1')
  t=SimpleNamespace(engine=SimpleNamespace(driver_hierarchy=h),learner=learner)
  state=np.zeros(13,np.float32);state[3]=1
  def factory(start,frozen,evaluation_mode):
   a=SimpleNamespace(engine=SimpleNamespace(driver_hierarchy=frozen),learner=ODPricingDQN(master_math=True,utc_mode=True),pairs=[],slots=0)
   a.run_slot=lambda policy,**kw:policy((0,0),state)
   return a
  before=hash_value(rng_bundle());weights=hash_value(learner.online.get_weights())
  with patch('src.pricing.od_contract.od_states',return_value={}):
   with isolated_evaluation(t,pd.Timestamp('2026-03-13T04:00Z'),factory) as (e,step):
    self.assertFalse(e.engine.driver_hierarchy.updates_enabled)
    with self.assertRaises(ValueError):e.learner.train_step()
    step();self.assertEqual(learner.decisions,0);self.assertEqual(len(learner.replay),0)
  self.assertEqual(hash_value(rng_bundle()),before);self.assertEqual(hash_value(learner.online.get_weights()),weights)
if __name__=='__main__':unittest.main()
