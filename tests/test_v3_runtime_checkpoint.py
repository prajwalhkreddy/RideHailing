"""Bounded validation only: no experiment training or protected dates."""
import gc,hashlib,json,random,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import tensorflow as tf
from src.simulation.slot_pricing_v3 import SlotPricingV3
from src.simulation.v3_checkpoint import save_v3_checkpoint,load_v3_checkpoint,encode,rng_bundle,digest
from src.fleet.fleet import Fleet
from src.fleet.state import VehicleState,VehicleStatus
from src.dispatch.request import RequestState


def stable(value):return hashlib.sha256(json.dumps(encode(value),sort_keys=True).encode()).hexdigest()


def snapshot(x):
    e=x.engine
    return dict(states=stable(x.states),replay=stable(list(x.learner.replay)),
        fleet=stable(e.fleet),charging=stable(e.charging),operational=stable(e.operational),
        routing=stable(e.current_states),dropoff=stable(x.dropoff),provider=stable(x.provider),
        ledger=stable(e.ledger),passengers=stable(e.passengers),missions=stable(e.missions),
        audit=stable(x.audit),slot_audit=stable(x.slot_audit),rng=stable(rng_bundle()),
        learner_rng=stable(x.learner.rng),request_rng=stable(e.request_rng),
        online=stable(x.learner.online.get_weights()),target=stable(x.learner.target.get_weights()),
        optimizer=stable([v.numpy() for v in x.learner.online.optimizer.variables]),
        timestamp=str(e.timestamp),slots=x.slots,replay_N=len(x.learner.replay),updates=x.learner.training_steps,
        decisions=x.learner.decisions)


def step(x):
    j=x.slots;t=x.engine.timestamp;rows=[]
    for i in range(4):
        d=30. if i<3 else .01
        rows.append(RequestState(j*10+i,0,0,1,base_fare=20.,source_trip_id=j*10+i,
            empirical_pickup_datetime=t.to_pydatetime(),empirical_dropoff_datetime=(t+pd.Timedelta(minutes=150)).to_pydatetime(),
            trip_duration_minutes=150.,trip_distance_miles=d/1.609344,trip_distance_km=d))
    x.run_slot(rows,weather_code=1)

class RuntimeCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='v3_resume_validation_');cls.path=Path(cls.temp.name)/'checkpoint'
        route='models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras'
        fleet=Fleet([VehicleState(i,0,VehicleStatus.IDLE,None,0,'idle',60.) for i in range(4)],frozenset(range(142)),2)
        profiles=pd.DataFrame(dict(vehicle_id=range(4),price_preference=[0.]*4,wait_preference=[10.]*4,charging_wait_preference_minutes=[10.]*4))
        x=SlotPricingV3(start='2026-03-12',routing_checkpoint=route,fleet=fleet,driver_profiles=profiles)
        from src.dispatch.generation import build_empirical_od_distribution
        trips=pd.DataFrame({'PUGridID':[0,0], 'DOGridID':[1,2],
            'tpep_pickup_datetime':pd.to_datetime(['2026-01-01 00:00','2026-01-01 01:00']),
            'tpep_dropoff_datetime':pd.to_datetime(['2026-01-01 00:30','2026-01-01 01:40']),
            'trip_distance':[2.,3.], 'fare_amount':[20.,30.]})
        x.engine.od=build_empirical_od_distribution(trips,range(142))
        station=next(iter(x.engine.charging.stations.values()))
        # Explicit controlled infrastructure fixture: one power-limited active place.
        station.max_power_kw=station.vehicle_charging_power_kw
        for i in [2,3]:
            v=x.engine.fleet.vehicle(i);v.current_grid=station.grid_id;v.energy_level=6.
            x.engine.charging.admit_arrived(v,station.station_id,x.engine.energy,i)
        step(x);step(x)
        cls.active_at_save=sum(len(s.active_vehicle_ids) for s in x.engine.charging.stations.values())
        cls.queued_at_save=sum(len(s.queue) for s in x.engine.charging.stations.values())
        # Dedicated synthetic replay fill, production warm-up unchanged.
        sample=x.learner.replay[0]
        while len(x.learner.replay)<1000:x.learner.store(*sample)
        x.learner.train_step()
        cls.before=snapshot(x);cls.performance=save_v3_checkpoint(x,cls.path)
        cls.manifest=json.loads((cls.path/'manifest.json').read_text())
        cls.next_loss_A=x.learner.train_step();step(x);step(x);cls.end_A=snapshot(x)
        cls.outcomes={r['dispatch_outcome'] for r in x.audit};del x;gc.collect()
        t=time.perf_counter();y=load_v3_checkpoint(cls.path);cls.load_seconds=time.perf_counter()-t
        cls.restored=snapshot(y)
        cls.next_loss_B=y.learner.train_step();step(y);step(y);cls.end_B=snapshot(y)
        cls.runtime=y
    @classmethod
    def tearDownClass(cls):
        output=Path('results/analysis/2026-11-15_source_aligned_slot_pricing_v3')
        pd.DataFrame([{'component':k,'identical':v==cls.end_B[k]} for k,v in cls.end_A.items()]).to_csv(output/'resume_equivalence_results.csv',index=False)
        pd.DataFrame([{'component':k,'identical':v==cls.restored[k]} for k,v in cls.before.items()]).to_csv(output/'checkpoint_roundtrip_results.csv',index=False)
        (output/'checkpoint_manifest_example.json').write_text(json.dumps(cls.manifest,indent=2)+'\n')
        (output/'checkpoint_performance.json').write_text(json.dumps(dict(bytes=cls.performance['bytes'],save_seconds=cls.performance['seconds'],load_seconds=cls.load_seconds,active_at_save=cls.active_at_save,queued_at_save=cls.queued_at_save,outcomes=sorted(cls.outcomes)),indent=2)+'\n')
        cls.temp.cleanup()
    def test_full_roundtrip(self):self.assertEqual(self.before,self.restored)
    def test_uninterrupted_resumed(self):self.assertEqual(self.end_A,self.end_B)
    def test_optimizer_next_update(self):self.assertEqual(self.next_loss_A,self.next_loss_B)
    def test_target_distinct(self):self.assertNotEqual(self.before['online'],self.before['target'])
    def test_no_duplicates(self):
        self.assertEqual(self.end_B['slots'],4);self.assertEqual(self.end_B['replay_N'],1284);self.assertEqual(self.end_B['updates'],2)
    def test_charging_exercised(self):
        self.assertGreater(self.active_at_save,0);self.assertGreater(self.queued_at_save,0)
    def test_outcomes(self):
        self.assertTrue({'ACCEPTED_AND_ASSIGNED','ACCEPTED_BUT_UNMATCHED','PASSENGER_REJECTED'}.issubset(self.outcomes))
    def test_unsafe_boundary(self):
        r=self.runtime;old=r.checkpoint_phase;r.checkpoint_phase='IN_SLOT'
        try:
            with self.assertRaisesRegex(ValueError,'UNSAFE_CHECKPOINT'):save_v3_checkpoint(r,Path(self.temp.name)/'bad')
        finally:r.checkpoint_phase=old
    def test_version_and_date_guards(self):
        p=self.path/'manifest.json';original=p.read_text()
        for field,value in [('methodology_version','V1'),('methodology_version','HISTORICAL_REQUEST_LEVEL_MASKED_V2'),('versions',{}),('ACTION_FACTORS',[.85,.9,.95,1,1.05,1.1,1.15]),('absolute_timestamp','2026-03-17')]:
            with self.subTest(field=field,value=value):
                m=json.loads(original);m[field]=value;p.write_text(json.dumps(m))
                try:
                    with self.assertRaises(ValueError):load_v3_checkpoint(self.path)
                finally:p.write_text(original)
    def test_corruption(self):
        p=self.path/'learner/replay.npz';data=p.read_bytes();p.write_bytes(data+b'corrupt')
        try:
            with self.assertRaisesRegex(ValueError,'Corrupt'):load_v3_checkpoint(self.path)
        finally:p.write_bytes(data)
    def test_missing_component(self):
        p=self.path/'runtime.json';q=p.with_suffix('.hidden');p.rename(q)
        try:
            with self.assertRaises(ValueError):load_v3_checkpoint(self.path)
        finally:q.rename(p)
    def test_atomic_failure(self):
        p=Path(self.temp.name)/'interrupted'
        with patch.object(self.runtime.learner,'save',side_effect=OSError('injected serialization interruption')):
            with self.assertRaises(OSError):save_v3_checkpoint(self.runtime,p)
        self.assertFalse(p.exists())
    def test_dropoff_carry_forward(self):
        from src.simulation.v3_checkpoint_codec import decode
        a=self.runtime.dropoff;b=decode(encode(a));before=a.previous.copy()
        frame=pd.DataFrame({'TimeSlot':[a.last+pd.Timedelta(minutes=30)]*142,'GridID':range(142),'dropoff_ma_3h':np.zeros(142)})
        with patch('src.pricing.slot_v3.pd.read_parquet',return_value=frame):
            np.testing.assert_array_equal(a.build(a.last+pd.Timedelta(minutes=30)),before)
            np.testing.assert_array_equal(b.build(b.last+pd.Timedelta(minutes=30)),before)
        self.assertEqual(a.audit[-1]['fallback'],'CARRY_FORWARD')

    def test_rng_next_values(self):
        from src.simulation.v3_checkpoint_codec import decode
        for rng in [self.runtime.learner.rng,self.runtime.provider.rng,self.runtime.engine.request_rng,self.runtime.engine.charging.rng]:
            a=decode(encode(rng));b=decode(encode(rng))
            np.testing.assert_array_equal(a.integers(100000,size=64),b.integers(100000,size=64))
    def test_replay_sampling_identity(self):
        from src.simulation.v3_checkpoint_codec import decode
        a=decode(encode(self.runtime.learner.rng));b=decode(encode(self.runtime.learner.rng))
        np.testing.assert_array_equal(a.choice(len(self.runtime.learner.replay),64,replace=False),b.choice(len(self.runtime.learner.replay),64,replace=False))
    def test_artifact_identity_rejected(self):
        p=self.path/'manifest.json';original=p.read_text();m=json.loads(original)
        m['artifact_hashes'][next(iter(m['artifact_hashes']))]='0'*64;p.write_text(json.dumps(m))
        try:
            with self.assertRaisesRegex(ValueError,'artifact'):load_v3_checkpoint(self.path)
        finally:p.write_text(original)
    def test_existing_checkpoint_cannot_overwrite(self):
        with self.assertRaises(FileExistsError):save_v3_checkpoint(self.runtime,self.path)

    def test_request_source_and_rng(self):
        from src.simulation.v3_checkpoint_codec import decode
        od=self.runtime.engine.od;restored=decode(encode(od))
        a=decode(encode(self.runtime.engine.request_rng));b=decode(encode(self.runtime.engine.request_rng))
        self.assertEqual([stable(od.sample_trip(0,a)) for _ in range(20)],
                         [stable(restored.sample_trip(0,b)) for _ in range(20)])
    def test_mixed_fleet_roundtrip_and_advance(self):
        from src.simulation.v3_checkpoint_codec import decode
        f=Fleet([VehicleState(0,0,VehicleStatus.IDLE,None,0,'idle',60.),
            VehicleState(1,0,VehicleStatus.BUSY,1,10,'repositioning',55.),
            VehicleState(2,0,VehicleStatus.BUSY,1,15,'passenger_trip',50.),
            VehicleState(3,0,VehicleStatus.CHARGING,None,0,'charging',6.),
            VehicleState(4,0,VehicleStatus.CHARGING,None,0,'charging_queue',6.)],frozenset(range(142)),2)
        g=decode(encode(f));self.assertEqual(stable(f),stable(g))
        f.advance_time(2);g.advance_time(2);self.assertEqual(stable(f),stable(g))
