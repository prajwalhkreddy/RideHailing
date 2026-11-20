"""Approved development-only schedule; no training or protected evaluation."""
import hashlib
import pandas as pd
from src.simulation.multi_episode_od import isolated_evaluation
MILESTONES=(7,14,21,28,35)
WINDOWS=('2026-03-13T00:00:00-04:00','2026-03-14T08:00:00-04:00','2026-03-15T16:00:00-04:00')
def due(runtime):
    return runtime.slots==16 and (getattr(runtime,'episode_offset',0)//16+1) in MILESTONES

def evaluate_due(runtime,factory):
    """Call only at approved completed milestones, never from the two-episode pilot."""
    if not due(runtime):return []
    reports=[]
    for start in WINDOWS:
        with isolated_evaluation(runtime,pd.Timestamp(start),factory,seed=42) as (evaluation,step):
            revenue=0.;supported=0.
            for _ in range(16):
                step();revenue+=evaluation.system_revenue;supported+=evaluation.environment_reward
            ids=[str(x['source_trip_id']) for x in evaluation.audit]
            reports.append(dict(start=start,requests=len(ids),population_sha256=hashlib.sha256('\n'.join(ids).encode()).hexdigest(),revenue=revenue,supported_reward=supported,accepted=sum(x['accepted'] for x in evaluation.audit),assigned=sum(x['dispatch_outcome']=='ACCEPTED_AND_ASSIGNED' for x in evaluation.audit),pricing_updates=0,routing_updates=0,seed=42))
    return reports
