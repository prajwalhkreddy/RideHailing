"""Fresh V3 Episode 1 only. Detached launch uses inherited exclusive writer lock."""
from pathlib import Path
import os,sys,json,subprocess,fcntl,traceback,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/training/episode_001'
MODEL=ROOT/'models/pricing_dqn/source_aligned_slot_pricing_v3/episode_001'
REPORT=OUT.parents[1]
def atomic(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def initial():
    return dict(status='STARTING',pid=os.getpid(),episode=1,timestamp='2026-03-01 00:00:00',slots_completed=0,target_slots=16,requests=0,accepted=0,rejected=0,assignments=0,accepted_unmatched=0,accepted_revenue=0.,replay_transitions=0,replay_size=0,optimizer_updates=0,epsilon=1.,mean_recent_loss=None,latest_safe_checkpoint=None,failure=None,episode2='NOT_STARTED',started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def run(fd):
    # Preserve inherited lock until process exit.
    lock=os.fdopen(fd,'a');status=initial();atomic(OUT/'training_status.json',status)
    try:
        import numpy as np,pandas as pd
        from src.pricing.slot_v3 import load_contract,sha,validate_state
        from src.simulation.slot_pricing_v3 import SlotPricingV3
        from src.simulation.v3_checkpoint import save_v3_checkpoint,load_v3_checkpoint
        from src.simulation.v3_episode1_protocol import TIMESTAMPS,assert_slot,update_after_slot
        from src.fleet.fleet import validate_fleet
        protocol=load_contract()['training_protocol'];atomic(OUT/'run_config.json',protocol)
        routing=ROOT/protocol['routing_checkpoint'];routing_hash=sha(routing)
        runtime=SlotPricingV3(start=protocol['episode1_start'],routing_checkpoint=routing,seed=42,fleet_size=5000)
        runtime.episode=1
        assert len(runtime.learner.replay)==runtime.learner.training_steps==runtime.learner.decisions==0
        assert all(np.array_equal(a,b) for a,b in zip(runtime.learner.online.get_weights(),runtime.learner.target.get_weights()))
        assert runtime.learner.epsilon==1.
        status['status']='RUNNING';atomic(OUT/'training_status.json',status)
        slots=[];learning=[];fleet=[];routing_rows=[];ops=[];reconcile=[];transitions=[]
        for i,t in enumerate(TIMESTAMPS):
            assert_slot(runtime.engine.timestamp,i)
            rows=runtime.run_slot();losses=update_after_slot(runtime)
            frame=pd.DataFrame(rows);recent=runtime.slot_audit[-142:]
            n=len(rows);accepted=sum(r['accepted'] for r in rows);assigned=sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in rows)
            revenue=sum(r['reward_contribution'] for r in rows);offers=sum(r['P_offer'] for r in rows if r['accepted'])
            replay_reward=sum(x[2] for x in list(runtime.learner.replay)[-142:])
            assert np.isclose(revenue,offers,rtol=1e-12,atol=1e-8) and np.isclose(revenue,replay_reward,rtol=1e-12,atol=1e-8)
            assert all(r['accepted']==(r['P_offer']<=r['P_max']) for r in rows)
            assert all(np.isfinite([r['P_offer'],r['P_max'],r['epsilon'],r['reward_contribution']]).all() for r in rows)
            assert len({r['request_id'] for r in runtime.audit})==len(runtime.audit)
            assert len(runtime.learner.replay)==142*(i+1)
            assert runtime.learner.training_steps==8*max(0,(i+1)-7)
            validate_fleet(runtime.engine.fleet.vehicles,range(142),5000)
            for state in runtime.states.values():validate_state(state)
            for net in (runtime.learner.online,runtime.learner.target):
                assert all(np.isfinite(w).all() for w in net.get_weights())
            assert all(np.isfinite(v.numpy()).all() for v in runtime.learner.online.optimizer.variables)
            assert sha(routing)==routing_hash
            op=runtime.engine.operational.state_for(runtime.engine.timestamp)
            assert np.isfinite(op[['mu','sigma','F_hat','H_hat']].to_numpy()).all()
            op.insert(0,'slot',str(t));ops.append(op)
            rec=dict(slot=str(t),requests=n,accepted=accepted,rejected=n-accepted,assignments=assigned,accepted_unmatched=accepted-assigned,accepted_revenue=revenue)
            slots.append(rec);reconcile.append(dict(slot=str(t),accepted_offers=offers,reward=revenue,replay_reward=replay_reward,passed=True))
            transitions.append(dict(slot=str(t),transitions=142,replay_size=len(runtime.learner.replay),terminal=i==15))
            learning.append(dict(slot=str(t),updates=len(losses),optimizer_updates=runtime.learner.training_steps,epsilon=runtime.learner.epsilon,mean_loss=float(np.mean(losses)) if losses else None))
            fleet.append(dict(slot=str(t),fleet_count=5000,valid=True,passenger_commitments=len(runtime.engine.passengers),movement_missions=len(runtime.engine.missions),charging_events=len(runtime.engine.charging_events)))
            routing_rows.append(dict(slot=str(t),frozen=True,checkpoint_sha256=routing_hash,probability_vectors=142,actions=9))
            cp=MODEL/('episode_001' if i==15 else f'slot_{i+1:03d}')
            save_v3_checkpoint(runtime,cp)
            status['latest_safe_checkpoint']=str(cp)
            atomic(OUT/'training_status.json',status)
            atomic(MODEL/'LATEST.json',dict(path=str(cp),slot=i+1))
            atomic(OUT/f'checkpoint_slot_{i+1:03d}.json',dict(path=str(cp),slot=i+1,schema='V3_FULL_RUNTIME_1'))
            for name,data in [('slot_metrics',slots),('learning_metrics',learning),('fleet_health',fleet),('routing_health',routing_rows),('reward_reconciliation',reconcile),('transition_metrics',transitions)]:pd.DataFrame(data).to_csv(OUT/(name+'.csv'),index=False)
            pd.concat(ops).to_csv(OUT/'operational_state_trace.csv',index=False)
            pd.DataFrame(runtime.slot_audit).groupby(['slot','action','factor'],as_index=False).agg(contexts=('destination_context','size'),requests=('generated','sum'),accepted=('accepted','sum'),revenue=('accepted_revenue','sum')).to_csv(OUT/'action_metrics.csv',index=False)
            if runtime.audit:
                pd.DataFrame(runtime.audit).groupby(['slot','sensitivity_condition','family'],as_index=False).agg(requests=('request_id','size'),accepted=('accepted','sum'),epsilon_mean=('epsilon','mean')).to_csv(OUT/'sensitivity_condition_metrics.csv',index=False)
            status.update(timestamp=str(runtime.engine.timestamp),slots_completed=i+1,requests=sum(x['requests'] for x in slots),accepted=sum(x['accepted'] for x in slots),rejected=sum(x['rejected'] for x in slots),assignments=sum(x['assignments'] for x in slots),accepted_unmatched=sum(x['accepted_unmatched'] for x in slots),accepted_revenue=sum(x['accepted_revenue'] for x in slots),replay_transitions=len(runtime.learner.replay),replay_size=len(runtime.learner.replay),optimizer_updates=runtime.learner.training_steps,epsilon=runtime.learner.epsilon,mean_recent_loss=learning[-1]['mean_loss'],latest_safe_checkpoint=str(cp))
            atomic(OUT/'training_status.json',status)
        restored=load_v3_checkpoint(cp)
        assert restored.slots==16 and restored.learner.training_steps==72 and len(restored.learner.replay)==2272
        assert all(np.array_equal(a,b) for a,b in zip(restored.learner.online.get_weights(),runtime.learner.online.get_weights()))
        atomic(OUT/'checkpoint_validation.json',dict(schema='V3_FULL_RUNTIME_1',path=str(cp),reload_passed=True))
        atomic(OUT/'date_access_audit.json',dict(training_slots=[str(t) for t in TIMESTAMPS],terminal_boundary='2026-03-01 08:00:00',March16='NOT_USED',March17_31='UNTOUCHED',supporting_artifacts='Frozen calibration, January request source and immutable causal forecasts; no protected-date evaluation'))
        gate={k:'PASS' for k in ['TECHNICAL_INVARIANTS','NUMERICAL_STABILITY','PASSENGER_ACCEPTANCE_INVARIANT','REWARD_RECONCILIATION','REPLAY_HEALTH','LEARNING_STARTED','CHECKPOINT_VALID','ROUTING_FROZEN','FLEET_INVARIANTS']}
        gate.update(MARCH17_31='UNTOUCHED',CONTINUE_TO_EPISODES_2_10='RECOMMENDED',EPISODE2='NOT_STARTED')
        atomic(OUT/'health_gate.json',gate);atomic(OUT/'verification.json',dict(completed=True,slots=16,health_gate=gate))
        (OUT/'README.md').write_text('# V3 fresh Episode 1\n\nCompleted 16 chronological March1 00:00–07:30 slots; 08:00 terminal boundary. Fresh 15D learner and approved full fleet. Eight updates per warm completed slot; exploration by optimizer-update count. Full checkpoint after each slot. See run_config.json, metrics and health_gate.json. Episode2 NOT_STARTED; continuation requires separate authorization. No March16 evaluation or March17–31 access.\n')
        status['status']='COMPLETED';atomic(OUT/'training_status.json',status)
    except BaseException as e:
        status.update(status='FAILED',failure=f'{type(e).__name__}: {e}')
        atomic(OUT/'training_status.json',status);traceback.print_exc();raise
    finally:lock.close()
def main():
    if '--lock-fd' in sys.argv:return run(int(sys.argv[sys.argv.index('--lock-fd')+1]))
    if sys.argv[1:]!=['--background']:raise ValueError('Explicit --background required')
    OUT.mkdir(parents=True,exist_ok=True);MODEL.mkdir(parents=True,exist_ok=True)
    lock=(MODEL/'writer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (OUT/'training_status.json').exists() or (MODEL/'LATEST.json').exists():raise ValueError('Fresh launch namespace already used')
    with (OUT/'episode_001.log').open('x') as log:
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--lock-fd',str(lock.fileno())],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(lock.fileno(),))
    lock.close();print(json.dumps(dict(pid=child.pid,status_file=str(OUT/'training_status.json'),log=str(OUT/'episode_001.log'))))
if __name__=='__main__':main()
