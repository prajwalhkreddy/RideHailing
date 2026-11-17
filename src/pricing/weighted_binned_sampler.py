"""Request-count weighted empirical bin mode; historical modes remain explicit."""
import json
from pathlib import Path
import numpy as np
from src.pricing.binned_sampler import BinnedSensitivity

VERSION = 'REQUEST_COUNT_WEIGHTED_BINNED_SENSITIVITY_V1'

class WeightedBinnedSensitivity(BinnedSensitivity):
    VERSION = VERSION
    FAMILY = 'REQUEST_COUNT_WEIGHTED_EMPIRICAL_BIN_RESAMPLE'

    def __init__(self, path, seed=42):
        super().__init__(path, seed)
        c = self.calibration
        if c.get('weighting') != 'HISTORICAL_REQUEST_COUNT' or c.get('calibration_period') != '2026-01-01 <= pickup_timestamp < 2026-03-16':
            raise ValueError('Weighted population contract mismatch')
        for pool in c['conditions'].values():
            n = np.asarray(pool['request_counts'],float)
            w = np.asarray(pool['probabilities'],float)
            if n.shape != np.asarray(pool['values']).shape or w.shape != n.shape:
                raise ValueError('Weighted bin shape mismatch')
            if not np.isfinite(n).all() or (n < 0).any() or (n != np.floor(n)).any() or n.sum() <= 0:
                raise ValueError('Invalid historical bin counts')
            if not np.isfinite(w).all() or (w < 0).any() or not np.allclose(w,n/n.sum(),rtol=0,atol=1e-15) or not np.isclose(w.sum(),1,rtol=0,atol=1e-14):
                raise ValueError('Invalid normalized bin probabilities')
            if int(n.sum()) != pool['represented_requests'] or pool['excluded_bin_requests'] < 0 or pool['represented_requests'] + pool['excluded_bin_requests'] != pool['source_requests']:
                raise ValueError('Request population does not reconcile')
        if c['conditions']['GLOBAL']['source_requests'] != c.get('source_N'):
            raise ValueError('Global population mismatch')

    def sample_pool(self, pool):
        return float(self.rng.choice(pool['values'], p=pool['probabilities']))


def load_sensitivity(path, seed=42):
    version=json.loads(Path(path).read_text()).get('version')
    classes={BinnedSensitivity.VERSION:BinnedSensitivity,VERSION:WeightedBinnedSensitivity}
    if version not in classes:raise ValueError('Unknown sensitivity version')
    return classes[version](path,seed)


def restore_sensitivity(snapshot):
    provider=load_sensitivity(snapshot['path'])
    if provider.VERSION != snapshot.get('binned_sampler_version'):
        raise ValueError('Mixed sensitivity snapshot version')
    return type(provider).restore(snapshot)
