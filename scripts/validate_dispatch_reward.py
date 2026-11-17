"""Run bounded reward tests and publish a provenance-bearing validation record."""
import argparse
import hashlib
import io
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to(ROOT / 'results_v2' / 'pricing_dqn')
    if output.exists():
        parser.error('Use a new run directory; existing evidence is never overwritten')
    config = json.loads((ROOT / 'config/dispatch_reward_validation.json').read_text())
    from src.pricing.dispatch_reward import REWARD_VERSION
    if config['methodology_version'] != REWARD_VERSION:
        raise ValueError('Configuration/reward contract mismatch')
    paths = ['config/dispatch_reward_validation.json', 'src/pricing/dispatch_reward.py',
             'src/rl/dispatch_reward_dqn.py', 'src/simulation/dispatch_reward_runtime.py',
             'src/simulation/slot_pricing_v3.py', 'src/rl/slot_pricing_v3.py',
             'tests/test_dispatch_reward.py', 'scripts/validate_dispatch_reward.py',
             'notebooks/plan/masterdocument/MASTER DOCUMENT1.docx',
             config['historical_configuration_reference'], config['routing_model_reference']]
    hashes = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    provenance = dict(run_id=output.name, git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),
        started_at=datetime.now(timezone.utc).isoformat(), methodology_version=REWARD_VERSION,
        configuration=config, source_sha256=hashes, python=sys.version,
        command=sys.argv, metric_definitions={'reward':'Sum offered fare for ACCEPTED_AND_ASSIGNED only',
            'accepted_revenue':'Descriptive sum of accepted fares; not learning reward',
            'learning_reward':'Successful-assignment fare sum stored per destination-context transition'},
        full_master_compliance=False, datasets='Existing frozen runtime dependencies; four constructed requests, no raw regeneration')
    log = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_dispatch_reward')
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    provenance['validation'] = dict(status='PASS' if result.wasSuccessful() else 'FAIL',
        tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped))
    output.mkdir(parents=True)
    (output/'validation.json').write_text(json.dumps(provenance,indent=2)+'\n')
    (output/'test_results.txt').write_text(log.getvalue())
    print(json.dumps(provenance['validation']))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
