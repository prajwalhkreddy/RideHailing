"""Small OD fixtures; no model fitting or experiment training."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from src.pricing.od_contract import support_from_trips, pairs_from_support, od_states
from src.simulation.od_pricing_runtime import ODPricingRuntime
from src.simulation.dispatch_reward_runtime import DispatchRewardRuntime
from src.simulation.od_pricing_checkpoint import save_od_checkpoint, load_od_checkpoint
from src.simulation.v3_checkpoint import save_v3_checkpoint, load_v3_checkpoint
from src.simulation.v3_checkpoint_codec import encode
from src.rl.slot_pricing_v3 import SlotDQN
from src.rl.od_pricing_dqn import ODPricingDQN
from src.rl.pricing_dqn import bellman_targets
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState, VehicleStatus
from src.dispatch.request import RequestState

ROUTING = 'models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'


def evidence():
    return pd.DataFrame(dict(PUGridID=[0,1,0], DOGridID=[1,1,2],
        tpep_pickup_datetime=pd.to_datetime(['2026-01-02']*3),
        tpep_dropoff_datetime=pd.to_datetime(['2026-01-02 00:30']*3),
        trip_distance=[3.]*3, fare_amount=[20.]*3))


def runtime(kind=ODPricingRuntime):
    fleet = Fleet([VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(2)], frozenset(range(142)),2)
    profiles = pd.DataFrame(dict(vehicle_id=range(2),price_preference=[0.]*2,wait_preference=[10.]*2,charging_wait_preference_minutes=[10.]*2))
    kwargs = dict(start='2026-03-12',seed=42,fleet=fleet,driver_profiles=profiles,routing_checkpoint=ROUTING)
    if kind is ODPricingRuntime: kwargs['od_support'] = support_from_trips(evidence())
    return kind(**kwargs)


def requests(t, origin=0):
    return [RequestState(i,0,origin,1,base_fare=20.,source_trip_id=i,
        empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=150)).to_pydatetime(),
        trip_duration_minutes=150.,trip_distance_miles=d/1.609344,trip_distance_km=d)
        for i,d in enumerate([30.,30.,30.,.01])]


class ODContractTests(unittest.TestCase):
    def test_support_deterministic_and_sparse(self):
        a=support_from_trips(evidence());b=support_from_trips(evidence().iloc[::-1])
        self.assertEqual(a,b);self.assertEqual(pairs_from_support(a),((0,1),(0,2),(1,1)))
    def test_support_date_and_grid_rejected(self):
        for column,value in [('tpep_pickup_datetime',pd.Timestamp('2026-03-17')),('PUGridID',142)]:
            frame=evidence();frame.loc[0,column]=value
            with self.assertRaises(ValueError):support_from_trips(frame)
    def test_corrupt_support_rejected(self):
        support=support_from_trips(evidence());support['pair_counts'][0][2]=0
        with self.assertRaises(ValueError):pairs_from_support(support)


class ODIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new=runtime();cls.old=runtime(DispatchRewardRuntime)
        cls.initial=copy.deepcopy(cls.new.states)
        cls.new.run_slot(requests(cls.new.engine.timestamp),policy=lambda od,s:0,weather_code=1)
        cls.old.run_slot(requests(cls.old.engine.timestamp),policy=lambda d,s:0,weather_code=1)

    def test_origin_demand_destination_popularity_and_ewma(self):
        r=self.new;e=r.engine;t=e.timestamp
        for (o,d),s in r.states.items():
            self.assertEqual(s[0],np.float32(e.current_states.forecast.get(o,t)))
            self.assertEqual(s[12],e.current_states.popularity.get(d,t))
            self.assertAlmostEqual(float(s[1]),float(e.operational.state_for(t).set_index('Grid_ID').loc[o,'F_hat'])*30,places=6)
        self.assertFalse(np.array_equal(self.initial[(0,1)],self.initial[(1,1)]))
        self.assertEqual(self.initial[(0,1)][12],self.initial[(1,1)][12])

    def test_od_actions_and_invalid_request(self):
        r=runtime();rows=r.run_slot(requests(r.engine.timestamp,1),policy=lambda od,s: 1 if od[0]==1 else 0,weather_code=1)
        self.assertTrue(all(x['factor']==r.provider.contract['actions'][1] for x in rows))
        self.assertEqual([s['action'] for s in r.slot_audit],[0,0,1])
        r=runtime();bad=requests(r.engine.timestamp,2)
        with self.assertRaises(ValueError):r.run_slot(bad,weather_code=1)
        self.assertEqual(len(r.learner.replay),0)

    def test_dispatch_and_rng_preserved_for_same_offers(self):
        fields=['request_id','P_offer','epsilon','P_max','accepted','dispatch_outcome','reward_contribution']
        self.assertEqual([[x[k] for k in fields] for x in self.new.audit],[[x[k] for k in fields] for x in self.old.audit])
        for name in ['fleet','passengers','missions','request_rng','operational','ledger']:
            self.assertEqual(encode(getattr(self.new.engine,name)),encode(getattr(self.old.engine,name)))
        self.assertEqual(encode(self.new.provider.rng),encode(self.old.provider.rng))

    def test_reward_replay_next_states_and_targets(self):
        r=self.new
        self.assertEqual({x['dispatch_outcome'] for x in r.audit},{'PASSENGER_REJECTED','ACCEPTED_BUT_UNMATCHED','ACCEPTED_AND_ASSIGNED'})
        assigned=sum(x['P_offer'] for x in r.audit if x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED')
        self.assertAlmostEqual(assigned,r.environment_reward)
        self.assertAlmostEqual(assigned,sum(x[2] for x in r.learner.replay))
        for identity,transition,slot in zip(r.learner.identities,r.learner.replay,r.slot_audit):
            pair=identity[1:];np.testing.assert_array_equal(transition[0],self.initial[pair]);np.testing.assert_array_equal(transition[3],r.states[pair])
            self.assertEqual(transition[2],slot['assignment_revenue'])
        self.assertEqual(r.learner.target.input_shape,(None,13))
        rewards=np.array([x[2] for x in r.learner.replay]);nextq=r.learner.target(np.stack([x[3] for x in r.learner.replay]),training=False).numpy()
        np.testing.assert_allclose(bellman_targets(rewards,np.zeros(3,bool),nextq,.99),rewards+.99*nextq.max(axis=1),rtol=1e-6)
        self.assertTrue(all(x['reward_contribution']==0 for x in r.audit if x['dispatch_outcome']!='ACCEPTED_AND_ASSIGNED'))
        self.assertEqual(r.learner.training_steps,0)

    def test_two_origins_reward_attribution(self):
        r=runtime();vehicle=r.engine.fleet.vehicle(1);vehicle.current_grid=1;vehicle.start_idle_wait()
        a=requests(r.engine.timestamp,0)[0];b=requests(r.engine.timestamp,1)[0];b.request_id=99
        rows=r.run_slot([a,b],policy=lambda od,s:0,weather_code=1)
        self.assertTrue(all(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in rows))
        rewards={identity[1:]:transition[2] for identity,transition in zip(r.learner.identities,r.learner.replay)}
        self.assertEqual(rewards[(0,1)],rows[0]['P_offer']);self.assertEqual(rewards[(1,1)],rows[1]['P_offer'])
        self.assertEqual(rewards[(0,2)],0.)

    def test_full_resume_equivalence_and_historical_rejection(self):
        r=runtime();r.run_slot(requests(r.engine.timestamp),weather_code=1)
        # Nonzero optimizer-state sentinel tests persistence without training.
        r.learner.training_steps=1
        r.learner.online.optimizer.iterations.assign(1)
        for variable in r.learner.online.optimizer.variables[2:]:
            variable.assign(np.full(variable.shape, .125))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'od';save_od_checkpoint(r,p);loaded=load_od_checkpoint(p)
            with self.assertRaises(ValueError):load_v3_checkpoint(p)
            historical=Path(tmp)/'historical_runtime';historical.mkdir()
            (historical/'manifest.json').write_text(json.dumps({'checkpoint_schema_version':'V3_FULL_RUNTIME_1'}))
            with self.assertRaises(ValueError):load_od_checkpoint(historical)
            with self.assertRaises(ValueError):save_v3_checkpoint(r,Path(tmp)/'old_api')
            with self.assertRaises(ValueError):SlotDQN.load(p/'learner')
            old=Path(tmp)/'old_learner';self.old.learner.save(old)
            with self.assertRaises(ValueError):ODPricingDQN.load(old)
            for obj in (r,loaded):obj.run_slot(requests(obj.engine.timestamp),weather_code=1)
            self.assertEqual(encode(r.audit),encode(loaded.audit));self.assertEqual(encode(r.slot_audit),encode(loaded.slot_audit))
            self.assertEqual(encode(r.states),encode(loaded.states))
            self.assertEqual(encode(list(r.learner.replay)),encode(list(loaded.learner.replay)))
            self.assertEqual(list(r.learner.identities),list(loaded.learner.identities))
            for name in ['fleet','passengers','missions','request_rng','operational','ledger','charging']:
                self.assertEqual(encode(getattr(r.engine,name)),encode(getattr(loaded.engine,name)))
            self.assertEqual(encode(r.provider.rng),encode(loaded.provider.rng))
            self.assertEqual(encode(r.learner.rng),encode(loaded.learner.rng))
            for a,b in zip(r.learner.online.optimizer.variables,loaded.learner.online.optimizer.variables):np.testing.assert_array_equal(a.numpy(),b.numpy())
            for left,right in [(r.learner.online,loaded.learner.online),(r.learner.target,loaded.learner.target)]:
                for a,b in zip(left.get_weights(),right.get_weights()):np.testing.assert_array_equal(a,b)
            m=json.loads((p/'manifest.json').read_text());m['reward_contract']='OLD';(p/'manifest.json').write_text(json.dumps(m))
            with self.assertRaises(ValueError):load_od_checkpoint(p)


if __name__=='__main__':unittest.main()
