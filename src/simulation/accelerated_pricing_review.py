"""Isolated review diagnostic. Does not alter or resume authoritative training."""
import json,os,signal,hashlib,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from src.simulation import multiepisode_pricing as base
from src.rl.pricing_dqn import PricingDQN,PricingAction
OUT=base.ROOT/'results/analysis/2026-11-01_accelerated_pricing_review'
MODEL=base.ROOT/'models/pricing_dqn/accelerated_review_phase_seed42'
UPDATES=128

def fingerprint(d):
    h=hashlib.sha256()
    for v in d.online.weights+d.target.weights+list(d.online.optimizer.variables):h.update(v.numpy().tobytes())
    h.update(pickle.dumps((list(d.replay.items),d.replay.rng.bit_generator.state,d.rng.bit_generator.state,d.training_steps)))
    return h.hexdigest()

def update_slot(d,timestamp):
    t=pd.Timestamp(timestamp)
    if not pd.Timestamp('2026-03-01')<=t<pd.Timestamp('2026-03-16'):raise ValueError('Training date blocked')
    if len(d.replay)<1000:return []
    return [d.train_step() for _ in range(UPDATES)]

def checked_slot(x,terminal,development=False):
    t=pd.Timestamp(x.timestamp)
    if development:
        if not pd.Timestamp('2026-03-16')<=t<pd.Timestamp('2026-03-16 02:00'):raise ValueError('Development boundary')
    elif not pd.Timestamp('2026-03-01')<=t<pd.Timestamp('2026-03-16'):raise ValueError('Protected date')
    requests=x.requests_for_slot()
    r=x.run_slot(requests=requests,terminal=terminal,train_dqn=False,explore_pricing=not development)
    violations=sum(1 for z in requests if z.assigned_vehicle_id is not None and z.offered_fare<float(x.profiles.loc[z.assigned_vehicle_id,'price_preference']))
    if violations:raise ValueError('Driver-price assignment violation')
    if r['federated_updates'] or r['fleet_size']!=5000 or len({v.vehicle_id for v in x.fleet.vehicles})!=5000:raise ValueError('Fleet/routing invariant')
    if not all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in x.fleet.vehicles):raise ValueError('Energy invariant')
    before=x.dqn.training_steps
    updates=[] if development else update_slot(x.dqn,t)
    expected=0 if development or len(x.dqn.replay)<1000 else UPDATES
    if x.dqn.training_steps-before!=expected:raise ValueError('Update cadence')
    r.update(optimizer_updates=len(updates),epsilon=x.dqn.epsilon,mean_loss=float(np.mean([z['loss'] for z in updates])) if updates else None,driver_price_assignment_violations=violations)
    return r

def metrics(x,episode):
    r=base.summarize(x,episode)
    # Current pricing states give the same fixed-fixture Q probe across evaluations.
    probe=getattr(x,'review_q_probe',None)
    if probe is None:
        rows=list(x.dqn.replay.items)[-512:]
        probe=np.stack([z[0] for z in rows]) if rows else None
    if probe is not None:q=x.dqn.online(probe,training=False).numpy()
    else:q=np.zeros((1,7))
    if not np.isfinite(q).all():raise ValueError('Nonfinite Q')
    r.update(q_min=float(q.min()),q_max=float(q.max()),mean_abs_Q=float(np.abs(q).mean()),mean_Q_spread=float(np.ptp(q,axis=1).mean()),slots_completed=x.slot_index,requests=sum(z['requests'] for z in x.reports),accepted=sum(z['accepted'] for z in x.reports),rejected=sum(z['rejected'] for z in x.reports),unmatched=sum(z['unmatched'] for z in x.reports),replay_insertions=sum(z['transitions'] for z in x.reports),fleet_count=len(x.fleet.vehicles),charging_events=len(x.charging_events),driver_price_assignment_violations=sum(z['driver_price_assignment_violations'] for z in x.reports),reserve_assignment_rejections=x.reserve_assignment_rejections,reserve_rejected_requests=len(x.reserve_rejected_request_ids),reserve_reposition_rejections=base.reserve_reposition_count(x.routing))
    return r

def evaluate(d,episode,stop,fixed=False):
    before=fingerprint(d)
    x=base.ProductionExperiment(start='2026-03-16',seed=424242,routing_checkpoint=base.ROUTING,frozen_routing=True);x.dqn=d
    x.review_q_probe=np.stack([x.current_states.build(g,g,x.timestamp) for g in range(142)])
    original=d.select_action
    if fixed:d.select_action=lambda state,explore=False:PricingAction(3,1.,d.epsilon,False)
    try:
        for j in range(4):
            checked_slot(x,j==3,True)
            if stop:return None
        result=metrics(x,episode)
    finally:
        if fixed:d.select_action=original
        if fingerprint(d)!=before:raise ValueError('Development mutated learner/replay')
    return result

def persist_rows(path,rows):
    tmp=path.with_suffix('.tmp');pd.DataFrame(rows).to_csv(tmp,index=False);tmp.replace(path)

def run(resume=False):
    lock=base.lock_writer(MODEL) # No PID/status writes before lock acquisition.
    stop=[];old={s:signal.signal(s,lambda signum,frame:stop.append(signum)) for s in (signal.SIGINT,signal.SIGTERM)}
    cp=None;x=None;episode=1
    try:
        OUT.mkdir(parents=True,exist_ok=True)
        protocol=json.loads((OUT/'review_protocol.json').read_text())
        starts=json.loads((base.OUT/'episode_protocol.json').read_text())['starts'][:25]
        if starts!=protocol['starts'] or protocol['updates_per_slot']!=128:raise ValueError('Review protocol mismatch')
        for spec in starts:base.guard(spec['start'])
        if base.sha(base.ROUTING)!=base.DIGEST:raise ValueError('Routing hash mismatch')
        cursor=MODEL/'cursor.json';rows=[];d=PricingDQN();start=0
        if resume:
            c=json.loads(cursor.read_text());start=c['index'];rows=c['rows'];d=PricingDQN.load(c['learner_checkpoint'])
        else:
            if cursor.exists() or list(MODEL.glob('episode_*')):raise ValueError('Explicit resume required')
            if len(d.replay) or d.training_steps or d.epsilon!=1 or base.weights_hash(d.online)!=base.weights_hash(d.target):raise ValueError('Fresh learner failure')
            d.save(MODEL/'initial_learner')
            base.atomic_json(cursor,dict(index=0,rows=[],learner_checkpoint=str(MODEL/'initial_learner')))
        base.atomic_json(MODEL/'process.json',dict(pid=os.getpid(),namespace=str(MODEL),resume=resume,review_phase=True))
        def status(name):
            base.atomic_json(OUT/'status.json',dict(status=name,pid=os.getpid(),episode=episode,slots_completed=0 if x is None else x.slot_index,replay_size=len(d.replay),optimizer_updates=d.training_steps,epsilon=d.epsilon,routing_sha256=base.DIGEST,namespace=str(MODEL),checkpoint=cp,review_phase=True,updates_per_slot=128,resume=resume,protected_dates_blocked=True))
            print(name,episode,0 if x is None else x.slot_index,flush=True)
        for i in range(start,25):
            episode=i+1;x=base.reset(starts[i],d);ns=MODEL/f'episode_{episode:04d}'
            if (ns/'CURRENT.json').exists():
                if not resume:raise ValueError('Partial review requires resume')
                x=base.restore_episode(x,ns);d=x.dqn
            status('EPISODE_INITIALIZED')
            if not (OUT/'development_0000.json').exists():
                result=evaluate(d,0,stop)
                if result is None:
                    cp=base.checkpoint(x,ns,base.RID);status('STOPPED_SAFE');return
                base.atomic_json(OUT/'development_0000.json',result)
            while x.slot_index<16:
                before=d.training_steps;checked_slot(x,x.slot_index==15)
                if before<50000<=d.training_steps:
                    base.atomic_json(OUT/'epsilon_floor.json',dict(episode=episode,slot=x.slot_index,optimizer_update=50000,epsilon=d.config.epsilon_end))
                if x.slot_index%8==0 or stop:
                    if base.sha(base.ROUTING)!=base.DIGEST:raise ValueError('Routing changed')
                    cp=base.checkpoint(x,ns,base.RID);status('CHECKPOINTED')
                if stop:status('STOPPED_SAFE');return
            record=metrics(x,episode);record['source_start']=starts[i]['start'];rows=[r for r in rows if r['episode']!=episode]+[record]
            cp=base.checkpoint(x,ns,base.RID)
            persist_rows(OUT/'episode_metrics.csv',rows)
            persist_rows(OUT/'action_evolution.csv',[dict(episode=r['episode'],epsilon=r['epsilon'],**{f'action_{j}':n for j,n in enumerate(r['action_counts'])}) for r in rows])
            persist_rows(OUT/'q_diagnostics.csv',[{k:r[k] for k in ['episode','mean_abs_Q','mean_Q_spread','q_min','q_max','mean_loss']} for r in rows])
            if episode%5==0:
                result=evaluate(d,episode,stop)
                if result is None:status('STOPPED_SAFE');return
                base.atomic_json(OUT/f'development_{episode:04d}.json',result)
                dev=[json.loads((OUT/f'development_{j:04d}.json').read_text()) for j in range(0,episode+1,5)]
                persist_rows(OUT/'development_metrics.csv',dev)
            if episode==25:
                fixed=evaluate(d,25,stop,True)
                if fixed is None:status('STOPPED_SAFE');return
                comparison=dict(fixed_factor_1=fixed,review_greedy=dev[-1])
                legacy=base.ROOT/'models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42'
                if (legacy/'CURRENT.json').exists():
                    pointer=json.loads((legacy/'CURRENT.json').read_text());path=legacy/pointer['directory']
                    meta=json.loads((path/'manifest.json').read_text())
                    if base.sha(path/'manifest.json')!=pointer['manifest_sha256']:raise ValueError('Legacy comparator integrity')
                    for name,h in meta['files'].items():
                        if base.sha(path/name)!=h:raise ValueError('Legacy payload integrity')
                    old_d=PricingDQN.load(path/'dqn');comparison['legacy']=evaluate(old_d,25,stop)
                    if comparison['legacy'] is None:status('STOPPED_SAFE');return
                else:comparison['legacy']='Unavailable at known provenance namespace; not required'
                base.atomic_json(OUT/'comparison_summary.json',comparison)
                # No invented significance/stability cutoff. Numerical mechanics pass;
                # descriptive curves require a later evidence review for YES vs INCONCLUSIVE.
                base.atomic_json(OUT/'learning_signal_assessment.json',dict(REVIEW_DQN_LEARNING_SIGNAL='INCONCLUSIVE',numerical_mechanics='PASS',structural_invariants='PASS',reason='Descriptive action/Q/development trajectories require the separate review evaluation; no undocumented convergence threshold is imposed.',final_convergence=False,development_revenue_change=dev[-1]['revenue']-dev[0]['revenue'],last_development_revenue_change=dev[-1]['revenue']-dev[-2]['revenue']))
            base.atomic_json(cursor,dict(index=i+1,rows=rows,learner_checkpoint=str(Path(cp)/'dqn')))
        if base.sha(base.ROUTING)!=base.DIGEST:raise ValueError('Routing changed')
        status('COMPLETE')
        with (OUT/'README.md').open('a') as f:f.write('\nBackground run completed 25 episodes. See learning_signal_assessment.json; this is not final convergence evidence.\n')
    except Exception as exc:
        base.atomic_json(OUT/'failure.json',dict(error=repr(exc),pid=os.getpid()))
        base.atomic_json(OUT/'learning_signal_assessment.json',dict(REVIEW_DQN_LEARNING_SIGNAL='NO',reason=repr(exc)))
        base.atomic_json(OUT/'status.json',dict(status='FAILED',pid=os.getpid(),episode=episode,review_phase=True,error=repr(exc)))
        raise
    finally:
        for s,h in old.items():signal.signal(s,h)
        lock.close()
