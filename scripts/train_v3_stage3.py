"""Full-state V3 Episodes 11–25 only. Detached launch uses inherited exclusive writer lock."""
from pathlib import Path
import os,sys,json,subprocess,fcntl,traceback,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'results/analysis/2026-11-15_source_aligned_slot_pricing_v3/training/stage_ep11_ep25'
MODEL=ROOT/'models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep11_ep25'
REPORT=OUT.parents[1]
def atomic(path,value):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
RESUME=ROOT/'models/pricing_dqn/source_aligned_slot_pricing_v3/stage_ep02_ep10/episode_010'
def initial():
    return dict(status='STARTING',pid=os.getpid(),stage='ep11_ep25',episode=11,timestamp='2026-03-04 08:00:00',slot=0,stage_slots_completed=0,stage_target_slots=240,requests=0,accepted=0,rejected=0,assignments=0,accepted_unmatched=0,accepted_revenue=0.,replay_transitions=0,replay_size=22720,optimizer_updates=1224,epsilon=1-.95*1224/50000,mean_recent_loss=None,latest_safe_checkpoint=str(RESUME),latest_completed_episode=10,resume_checkpoint=str(RESUME),failure=None,episode26='NOT_STARTED',started_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def run(fd,resumed_runtime=None):
    # Preserve inherited lock until process exit.
    lock=os.fdopen(fd,'a');status=initial();atomic(OUT/'training_status.json',status)
    try:
        import numpy as np,pandas as pd
        from src.pricing.slot_v3 import load_contract,sha,validate_state
        from src.simulation.slot_pricing_v3 import SlotPricingV3
        from src.simulation.v3_stage2_checkpoint import load_v3_checkpoint as load_episode10
        from src.simulation.v3_stage3_checkpoint import save_v3_checkpoint,load_v3_checkpoint
        from src.simulation.v3_stage3_protocol import timestamps,begin_episode,update_after_slot
        from src.fleet.fleet import validate_fleet
        protocol=load_contract()['training_protocol'];atomic(OUT/'run_config.json',dict(inherited=protocol,stage3=json.loads((OUT/'stage3_protocol.json').read_text())))
        routing=ROOT/protocol['routing_checkpoint'];routing_hash=sha(routing)
        runtime=resumed_runtime if resumed_runtime is not None else load_episode10(RESUME)
        assert runtime.episode==10 and runtime.slots==16 and runtime.learner.training_steps==1224
        assert len(runtime.learner.replay)==22720 and runtime.learner.epsilon==1-.95*1224/50000
        assert str(runtime.engine.timestamp)=='2026-03-04 08:00:00'
        status['status']='RUNNING';atomic(OUT/'training_status.json',status)
        slots=[];learning=[];fleet=[];routing_rows=[];ops=[];reconcile=[];transitions=[]
        for episode in range(11,26):
            begin_episode(runtime,episode)
            status.update(episode=episode,slot=0,timestamp=str(runtime.engine.timestamp))
            atomic(OUT/'training_status.json',status)
            for i,t in enumerate(timestamps(episode)):
                assert runtime.engine.timestamp==t
                rows=runtime.run_slot();losses=update_after_slot(runtime)
                frame=pd.DataFrame(rows);recent=runtime.slot_audit[-142:]
                n=len(rows);accepted=sum(r['accepted'] for r in rows);assigned=sum(r['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for r in rows)
                revenue=sum(r['reward_contribution'] for r in rows);offers=sum(r['P_offer'] for r in rows if r['accepted'])
                replay_reward=sum(x[2] for x in list(runtime.learner.replay)[-142:])
                assert np.isclose(revenue,offers,rtol=1e-12,atol=1e-8) and np.isclose(revenue,replay_reward,rtol=1e-12,atol=1e-8)
                assert all(r['accepted']==(r['P_offer']<=r['P_max']) for r in rows)
                assert all(np.isfinite([r['P_offer'],r['P_max'],r['epsilon'],r['reward_contribution']]).all() for r in rows)
                assert len({r['request_id'] for r in runtime.audit})==len(runtime.audit)
                assert len(runtime.learner.replay)==142*((episode-1)*16+i+1)
                assert runtime.learner.training_steps==1224+8*((episode-11)*16+i+1)
                validate_fleet(runtime.engine.fleet.vehicles,range(142),5000)
                for state in runtime.states.values():validate_state(state)
                for net in (runtime.learner.online,runtime.learner.target):
                    assert all(np.isfinite(w).all() for w in net.get_weights())
                assert all(np.isfinite(v.numpy()).all() for v in runtime.learner.online.optimizer.variables)
                assert sha(routing)==routing_hash
                op=runtime.engine.operational.state_for(runtime.engine.timestamp)
                assert np.isfinite(op[['mu','sigma','F_hat','H_hat']].to_numpy()).all()
                op.insert(0,'slot',str(t));ops.append(op)
                rec=dict(episode=episode,slot=str(t),requests=n,accepted=accepted,rejected=n-accepted,assignments=assigned,accepted_unmatched=accepted-assigned,accepted_revenue=revenue)
                slots.append(rec);reconcile.append(dict(slot=str(t),accepted_offers=offers,reward=revenue,replay_reward=replay_reward,passed=True))
                transitions.append(dict(slot=str(t),transitions=142,replay_size=len(runtime.learner.replay),terminal=i==15))
                learning.append(dict(slot=str(t),updates=len(losses),optimizer_updates=runtime.learner.training_steps,epsilon=runtime.learner.epsilon,mean_loss=float(np.mean(losses)) if losses else None))
                fleet.append(dict(slot=str(t),fleet_count=5000,valid=True,passenger_commitments=len(runtime.engine.passengers),movement_missions=len(runtime.engine.missions),charging_events=len(runtime.engine.charging_events)))
                routing_rows.append(dict(slot=str(t),frozen=True,checkpoint_sha256=routing_hash,probability_vectors=142,actions=9))
                cp=MODEL/(f'episode_{episode:03d}' if i==15 else f'episode_{episode:03d}_slot_{i+1:03d}')
                save_v3_checkpoint(runtime,cp)
                status['latest_safe_checkpoint']=str(cp)
                atomic(OUT/'training_status.json',status)
                atomic(MODEL/'LATEST.json',dict(path=str(cp),slot=i+1))
                atomic(OUT/f'checkpoint_episode_{episode:03d}_slot_{i+1:03d}.json',dict(path=str(cp),slot=i+1,schema='V3_FULL_RUNTIME_1'))
                for name,data in [('slot_metrics',slots),('learning_metrics',learning),('fleet_health',fleet),('routing_health',routing_rows),('reward_reconciliation',reconcile),('transition_metrics',transitions)]:pd.DataFrame(data).to_csv(OUT/(name+'.csv'),index=False)
                pd.concat(ops).to_csv(OUT/'operational_state_trace.csv',index=False)
                pd.DataFrame([x for x in runtime.slot_audit if x['slot']>='2026-03-04 08:00:00']).groupby(['slot','action','factor'],as_index=False).agg(contexts=('destination_context','size'),requests=('generated','sum'),accepted=('accepted','sum'),revenue=('accepted_revenue','sum')).to_csv(OUT/'action_metrics.csv',index=False)
                if runtime.audit:
                    pd.DataFrame([x for x in runtime.audit if x['slot']>='2026-03-04 08:00:00']).groupby(['slot','sensitivity_condition','family'],as_index=False).agg(requests=('request_id','size'),accepted=('accepted','sum'),epsilon_mean=('epsilon','mean')).to_csv(OUT/'sensitivity_condition_metrics.csv',index=False)
                status.update(timestamp=str(runtime.engine.timestamp),episode=episode,slot=i+1,stage_slots_completed=(episode-11)*16+i+1,requests=sum(x['requests'] for x in slots),accepted=sum(x['accepted'] for x in slots),rejected=sum(x['rejected'] for x in slots),assignments=sum(x['assignments'] for x in slots),accepted_unmatched=sum(x['accepted_unmatched'] for x in slots),accepted_revenue=sum(x['accepted_revenue'] for x in slots),replay_transitions=len(runtime.learner.replay)-22720,replay_size=len(runtime.learner.replay),optimizer_updates=runtime.learner.training_steps,epsilon=runtime.learner.epsilon,mean_recent_loss=learning[-1]['mean_loss'],latest_safe_checkpoint=str(cp))
                atomic(OUT/'training_status.json',status)
            restored=load_v3_checkpoint(cp)
            assert restored.episode==episode and restored.slots==16
            assert restored.learner.training_steps==runtime.learner.training_steps
            assert all(np.array_equal(a,b) for a,b in zip(restored.learner.online.get_weights(),runtime.learner.online.get_weights()))
            # Loading restores saved RNG states; no draws/updates occurred since save.
            del restored
            status['latest_completed_episode']=episode
            atomic(OUT/f'episode_{episode:03d}_health.json',dict(status='PASS',episode=episode,slots=16,checkpoint=str(cp),checkpoint_reload=True,metrics=[x for x in slots if x['episode']==episode]))
            atomic(OUT/'training_status.json',status)
        restored=load_v3_checkpoint(cp)
        assert restored.slots==16 and restored.learner.training_steps==3144 and len(restored.learner.replay)==56800
        assert all(np.array_equal(a,b) for a,b in zip(restored.learner.online.get_weights(),runtime.learner.online.get_weights()))
        atomic(OUT/'checkpoint_validation.json',dict(schema='V3_FULL_RUNTIME_1',path=str(cp),reload_passed=True))
        atomic(OUT/'date_access_audit.json',dict(training_slots=[str(t) for e in range(11,26) for t in timestamps(e)],terminal_boundary='2026-03-09 08:00:00',March16='NOT_USED',March17_31='UNTOUCHED',supporting_artifacts='Frozen calibration, January request source and immutable causal forecasts; no protected-date evaluation'))
        gate={k:'PASS' for k in ['TECHNICAL_INVARIANTS','NUMERICAL_STABILITY','PASSENGER_ACCEPTANCE_INVARIANT','REWARD_RECONCILIATION','REPLAY_HEALTH','LEARNING_STARTED','CHECKPOINT_VALID','ROUTING_FROZEN','FLEET_INVARIANTS']}
        gate.update(MARCH17_31='UNTOUCHED',EPISODE26='NOT_STARTED',episodes_completed=15,slots_completed=240,**{k:status[k] for k in ['requests','accepted','rejected','assignments','accepted_unmatched','accepted_revenue','replay_size','optimizer_updates','epsilon','mean_recent_loss']})
        atomic(OUT/'health_gate.json',gate);atomic(OUT/'verification.json',dict(completed=True,slots=240,health_gate=gate))
        pd.DataFrame([x for x in runtime.slot_audit if x['slot']>='2026-03-04 08:00:00']).groupby(['action','factor'],as_index=False).agg(action_frequency=('destination_context','size'),requests=('generated','sum'),accepted=('accepted','sum'),accepted_revenue=('accepted_revenue','sum')).to_csv(OUT/'action_summary.csv',index=False)
        (OUT/'README.md').write_text('# V3 Stage 3 completed\n\nEpisodes11–25, March4 08:00 to March9 07:30; 08:00 terminal boundary. Full-state continuation from Episode10; no environment or learner resets. Eight updates per warm slot. See stage3_protocol.json, metrics, per-episode health and health_gate.json. Episode26 NOT_STARTED. March16 and March17–31 not used.\n')
        status['status']='COMPLETED';atomic(OUT/'training_status.json',status)
    except BaseException as e:
        status.update(status='FAILED',failure=f'{type(e).__name__}: {e}')
        atomic(OUT/'training_status.json',status);traceback.print_exc();raise
    finally:lock.close()
if __name__=='__main__':raise SystemExit('Launch only through handoff_v3_ep25.py; Episode10 gate required')
