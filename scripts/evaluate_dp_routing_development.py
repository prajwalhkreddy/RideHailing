"""Four fixed March16 development slots per routing model; no learner mutation."""
from pathlib import Path
import json,hashlib,pickle,argparse
import numpy as np
import pandas as pd
from scripts.train_dp_temporal_routing import R,OUT,BASE,BASE_HASH,save
from src.simulation.final_production import ProductionExperiment
from src.simulation.pricing_safety_monitor import learner_fingerprint
from src.rl.pricing_dqn import PricingDQN

PRICING=R/'models/pricing_dqn/final_nonprivate_multiepisode_seed42/episode_0025/checkpoint_0016_fb2fce6a/dqn'

def prohibited(*args,**kwargs):raise ValueError('Development attempted learner/replay mutation')

def main():
    models=[('NON_PRIVATE',BASE)]+[(f'DP_EPS{e}',R/f'models/routing_policy/dp_temporal_fedavg_eps{e}_seed42/final_march12.keras') for e in [8,4,2]]
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=['NON_PRIVATE','DP_EPS8','DP_EPS4','DP_EPS2']);args=parser.parse_args()
    if args.model:models=[m for m in models if m[0]==args.model]
    if not all(p.is_file() for _,p in models):raise FileNotFoundError('All frozen routing models required before comparison')
    saved_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in PRICING.iterdir() if p.is_file()}
    rows=[];initial=None
    for name,path in models:
        result=OUT/f'development_{name}.json'
        if result.exists():
            data=json.loads(result.read_text());rows.append(data['metrics'])
            if initial is None:initial=data['initial_fleet_hash']
            elif initial!=data['initial_fleet_hash']:raise ValueError('Initial fleet mismatch')
            continue
        learner=PricingDQN.load(PRICING);before=learner_fingerprint(learner)
        learner.store=prohibited;learner.train_step=prohibited
        x=ProductionExperiment(start='2026-03-16',seed=424242,routing_checkpoint=path,frozen_routing=True);x.dqn=learner
        fleet_hash=hashlib.sha256(pickle.dumps(x.fleet)).hexdigest()
        if initial is None:initial=fleet_hash
        elif initial!=fleet_hash:raise ValueError('Initial fleet mismatch')
        violations=0
        for slot in range(4):
            if x.timestamp != pd.Timestamp('2026-03-16')+pd.Timedelta(minutes=30*slot):raise ValueError('Protected date guard')
            requests=x.requests_for_slot()
            row=x.run_slot(requests=requests,terminal=slot==3,train_dqn=False,explore_pricing=False)
            v=sum(1 for q in requests if q.assigned_vehicle_id is not None and q.offered_fare<float(x.profiles.loc[q.assigned_vehicle_id,'price_preference']))
            violations+=v
            assert v==0 and row['transitions']==0 and row['federated_updates']==0 and row['fleet_size']==5000
            assert len({v.vehicle_id for v in x.fleet.vehicles})==5000
            assert all(np.isfinite(v.energy_level) and v.energy_level>=0 for v in x.fleet.vehicles)
            assert row['accepted']+row['rejected']==row['requests'] and row['assigned']+row['unmatched']==row['accepted']
            assert np.isclose(sum(q.offered_fare for q in requests if q.assigned_vehicle_id is not None),row['reward'],rtol=1e-12)
            print(name,'completed slot',slot+1,flush=True)
        assert learner_fingerprint(learner)==before
        counts=lambda key:sum(int(r[key]) for r in x.reports)
        row=dict(model=name,requests=counts('requests'),accepted=counts('accepted'),rejected=counts('rejected'),successful_assignments=counts('assigned'),accepted_unmatched=counts('unmatched'),assignment_rate=counts('assigned')/counts('requests'),revenue=sum(r['reward'] for r in x.reports),pricing_action_counts=json.dumps(np.sum([r['pricing_action_counts'] for r in x.reports],axis=0).tolist()),routing_action_counts=json.dumps(np.sum([r['routing_actions'] for r in x.reports],axis=0).tolist()),driver_price_violations=violations,operational_invariant_failures=0,replay_insertions=0,optimizer_updates=0,learner_unchanged=True,slots=4)
        rows.append(row)
        save(result,dict(metrics=row,initial_fleet_hash=fleet_hash,pricing_checkpoint=str(PRICING.relative_to(R)),pricing_sha256=saved_hashes,routing_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fixture='March16 00:00–02:00, seed424242, greedy',classification='PRELIMINARY_END_TO_END_PRIVACY_UTILITY',pricing_converged=False))
        pd.DataFrame([json.loads(p.read_text())['metrics'] for p in sorted(OUT.glob('development_*.json'))]).to_csv(OUT/'preliminary_end_to_end_comparison.csv',index=False)
    assert {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in PRICING.iterdir() if p.is_file()}==saved_hashes
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==BASE_HASH
    pd.DataFrame([json.loads(p.read_text())['metrics'] for p in sorted(OUT.glob('development_*.json'))]).to_csv(OUT/'preliminary_end_to_end_comparison.csv',index=False)

if __name__=='__main__':main()
