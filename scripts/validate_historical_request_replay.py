"""Bounded separation, persistence and historical-count validation; no training."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    output=args.output.resolve();output.relative_to(ROOT/'results_v2/simulation')
    if output.exists():p.error('Choose a new output directory')
    from src.simulation.historical_request_replay import SOURCE,read_slot,replay_requests
    from src.pricing.od_contract import pairs_from_support,od_states
    from src.simulation.v3_checkpoint import digest
    from tests.test_od_pricing import runtime
    config=json.loads((ROOT/'config/historical_request_replay_validation.json').read_text())
    support_path=ROOT/'results_v2/pricing_dqn/2026-11-17_feasible_od_validation/od_feasibility.json'
    support=json.loads(support_path.read_text());pairs=pairs_from_support(support)
    t=time.perf_counter();frame=read_slot(config['observed_slot']);read_seconds=time.perf_counter()-t
    t=time.perf_counter();requests,counts=replay_requests(frame,config['observed_slot'],pairs);conversion_seconds=time.perf_counter()-t
    r=runtime();t=time.perf_counter();states=od_states(r.engine,pairs);state_seconds=time.perf_counter()-t
    t=time.perf_counter();actions=r.learner.select_actions(list(states.values()));inference_seconds=time.perf_counter()-t
    performance=dict(contexts=len(states),cartesian_contexts=142*142,read_seconds=read_seconds,
        request_conversion_seconds=conversion_seconds,state_construction_seconds=state_seconds,
        batched_inference_seconds=inference_seconds,inference_batches=(len(states)+1023)//1024,
        state_array_bytes=sum(s.nbytes for s in states.values()),selected_frame_bytes=int(frame.memory_usage(deep=True).sum()),
        replay_transitions_per_slot=len(states),replay_transitions_per_16_slots=len(states)*16,
        replay_capacity=100000,training_updates=0,
        scope='One observed slot read/conversion; full-support state/inference only; small synthetic fleet; no full-slot simulation')
    focused=unittest.defaultTestLoader.loadTestsFromNames(['tests.test_historical_request_replay','tests.test_od_pricing'])
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(focused)
    modules=['tests.test_dispatch_reward','tests.test_slot_pricing_v3','tests.test_operational_grid_state',
        'tests.test_driver_price_gate','tests.test_v3_episode1_protocol','tests.test_v3_stage2_protocol',
        'tests.test_routing_privacy','tests.test_routing_federated','tests.test_metric_grid']
    reglog=io.StringIO();reg=unittest.TextTestRunner(stream=reglog,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromNames(modules))
    def status(x):return dict(tests=x.testsRun,failures=len(x.failures),errors=len(x.errors),passed=x.wasSuccessful())
    paths=['src/simulation/historical_request_replay.py','src/simulation/od_pricing_runtime.py',
        'src/simulation/od_pricing_checkpoint.py','src/rl/od_pricing_dqn.py','src/pricing/od_contract.py',
        'src/simulation/final_production.py','src/dispatch/generation.py','src/pricing/dqn_contract.py',
        'tests/test_historical_request_replay.py','scripts/validate_historical_request_replay.py',
        'config/historical_request_replay_validation.json','config/final_temporal_protocol.json',
        'notebooks/plan/masterdocument/MASTER DOCUMENT1.docx']
    report=dict(configuration=config,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        git_dirty_state=subprocess.check_output(['git','status','--porcelain'],text=True),python=sys.version,
        command=sys.argv,source_hashes={path:digest(ROOT/path) for path in paths},
        historical_source=dict(path=str(SOURCE),sha256=digest(SOURCE),filter_start=config['observed_slot'],
            filter_end_exclusive='2026-03-12 00:30:00',fingerprint_note='Whole-file integrity fingerprint; only selected slot rows inspected'),
        od_support_sha256=support['support_sha256'],count_reconciliation=counts,
        performance=performance,focused=status(result),regression=status(reg),
        training_performed=False,protected_period_used_for_evaluation=False)
    output.mkdir(parents=True)
    (output/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'focused_tests.txt').write_text(log.getvalue());(output/'regression_tests.txt').write_text(reglog.getvalue())
    print(json.dumps(dict(focused=report['focused'],regression=report['regression'],counts=counts,performance=performance)))
    return 0 if result.wasSuccessful() and reg.wasSuccessful() else 1

if __name__=='__main__':raise SystemExit(main())
