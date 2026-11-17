"""Explicitly opt-in empirical bin sampling; provisional, not final calibration."""
import hashlib
import json
from pathlib import Path
import numpy as np
from src.pricing.slot_v3 import FittedSensitivity

VERSION = 'PROVISIONAL_BINNED_EMPIRICAL_SENSITIVITY_V1'

class BinnedSensitivity(FittedSensitivity):
    VERSION = VERSION
    FAMILY = "EMPIRICAL_BIN_RESAMPLE"
    def __init__(self, path, seed=42):
        super().__init__(seed)
        self.calibration_path = str(Path(path).resolve())
        raw = Path(path).read_bytes()
        self.calibration_hash = hashlib.sha256(raw).hexdigest()
        self.calibration = json.loads(raw)
        c = self.calibration
        if c.get('version') != self.VERSION or c.get('status') != 'PROVISIONAL_OPT_IN':
            raise ValueError('Unsupported sensitivity contract')
        if c.get('P_base') != self.contract['P_base'] or c.get('L_base') != self.contract['L_base']:
            raise ValueError('Common reference mismatch')
        if c.get('grouping') != self.grouping or c.get('historical_support_counts') != {k:int(v) for k,v in self.counts.items()}:
            raise ValueError('Historical grouping/fallback mismatch')
        if set(c['conditions']) != set(self.contract['conditions']):
            raise ValueError('Missing conditional empirical pool')
        for pool in c['conditions'].values():
            a = np.asarray(pool['values'], float)
            if a.ndim != 1 or not len(a) or not np.isfinite(a).all() or (a <= 0).any():
                raise ValueError('Positive finite empirical support required')
            if pool['lower'] != float(a.min()) or pool['upper'] != float(a.max()):
                raise ValueError('Empirical support bounds mismatch')

    def draw(self, code, t):
        sid, level, T = self.select(code, t)
        pool = self.calibration['conditions'][sid]
        epsilon = self.sample_pool(pool)
        if not np.isfinite(epsilon) or not 0 < pool['lower'] <= epsilon <= pool['upper']:
            raise ValueError('Invalid empirical draw')
        result = dict(sensitivity_condition=sid, fallback_level=level, T_group=T,
                      family=self.FAMILY, epsilon=epsilon,
                      sensitivity_version=self.VERSION, sensitivity_hash=self.calibration_hash)
        self.audit.append(dict(timestamp=str(t), weather_code=int(code), **result))
        return result

    def sample_pool(self, pool):
        return float(self.rng.choice(pool["values"]))

    def snapshot(self):
        return dict(binned_sampler_version=self.VERSION, path=self.calibration_path,
                    sha256=self.calibration_hash, rng=self.rng.bit_generator.state, audit=self.audit)

    @classmethod
    def restore(cls, snapshot):
        if snapshot.get('binned_sampler_version') != cls.VERSION:
            raise ValueError('Sensitivity version mismatch')
        obj = cls(snapshot['path'])
        if obj.calibration_hash != snapshot['sha256']:
            raise ValueError('Changed sensitivity calibration')
        obj.rng.bit_generator.state = snapshot['rng']
        obj.audit = snapshot['audit']
        return obj
