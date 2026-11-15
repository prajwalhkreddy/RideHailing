"""Opt-in, hash-verified V2 empirical sensitivity. No fitted approximation."""
from pathlib import Path
import copy
import hashlib
import json
import numpy as np
import pandas as pd
from src.pricing.passenger_sensitive_v1 import ACTIONS, EpsilonDraw

DEFAULT_CONTRACT = 'results/analysis/2026-11-14_pricing_v2_sensitivity_distribution_selection/pricing_v2_sensitivity_contract.json'

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

class V2EmpiricalSensitivityProvider:
    version = 'v2'

    def __init__(self, *, rng, root=None, contract_path=DEFAULT_CONTRACT, expected_contract_sha256=None, training_authorized=False):
        if not isinstance(rng, np.random.Generator):
            raise ValueError('Caller-owned Generator required.')
        self.root = Path(root or Path(__file__).resolve().parents[2])
        self.training_authorized = bool(training_authorized)
        self.contract_path = self.root / contract_path
        self.contract_hash = sha256(self.contract_path)
        if expected_contract_sha256 is not None and self.contract_hash != expected_contract_sha256:
            raise ValueError("V2 contract hash mismatch.")
        c = json.loads(self.contract_path.read_text())
        if (c['sampling_candidate_status'] != 'REVIEWED_NOT_INTEGRATED'
            or c['sampling_candidate'] != 'EMPIRICAL_RESAMPLING'
            or c['denominator_relative_threshold'] != .05
            or c['epsilon_formula'] != 'r_L/r_P; r_P=(P-P_base)/P_base; r_L=(L-L_base)/L_base'
            or c['distance_unit'] != 'km'
            or c['calibration_period'] != {'start_inclusive':'2026-01-01','end_exclusive':'2026-03-16'}):
            raise ValueError('Unsupported V2 contract.')
        for path, expected in c['source_hashes'].items():
            if sha256(self.root / path) != expected:
                raise ValueError('V2 source hash mismatch: '+path)
        reference = json.loads((self.root / c['reference_source']).read_text())
        if (c['P_base'] != reference['P_base'] or c['L_base'] != reference['L_base']
            or c['effective_current_USD_threshold'] != .05*c['P_base']):
            raise ValueError('Frozen V2 reference mismatch.')
        population = self.root / c['population_path']
        if sha256(population) != c['population_sha256']:
            raise ValueError('V2 population hash mismatch.')
        # Column projection, loaded once per provider, never per episode/request.
        f = pd.read_parquet(population, columns=['epsilon','is_runtime_candidate','epsilon_status','pickup_timestamp','r_P'])
        if not (f.pickup_timestamp.ge('2026-01-01') & f.pickup_timestamp.lt('2026-03-16')).all():
            raise ValueError('Calibration date boundary violation.')
        expected = f.epsilon_status.isin(['POSITIVE_VALID','NONNEGATIVE_VALID'])
        if not np.array_equal(expected, f.is_runtime_candidate):
            raise ValueError('Candidate status mismatch.')
        a = f.loc[expected, 'epsilon'].to_numpy(dtype=np.float64, copy=True)
        if (len(a) != 5779213 or not np.isfinite(a).all() or (a < 0).any()
            or (abs(f.loc[expected, 'r_P']) < .05).any()):
            raise ValueError('Invalid V2 support.')
        if (a == 0).any():
            raise ValueError('ZERO_EPSILON_RUNTIME_CONTRACT_CONFLICT: inverse-epsilon threshold.')
        a.setflags(write=False)
        self.values, self.rng, self.contract = a, rng, c
        self.support_hash = c['population_sha256']
        self.pricing = V2PriceContract(c)

    def sample(self):
        value = float(self.values[self.rng.integers(len(self.values))])
        return EpsilonDraw(value, value, 0.) # zero metadata means no added floor

    def sample_many(self, n):
        return self.values[self.rng.integers(len(self.values), size=n)]

    def state_dict(self):
        return dict(passenger_sensitivity_version='v2', contract_sha256=self.contract_hash,
                    empirical_support_sha256=self.support_hash,
                    rng_state=copy.deepcopy(self.rng.bit_generator.state))

    def load_state_dict(self, state):
        if (state.get('passenger_sensitivity_version') != 'v2'
            or state.get('contract_sha256') != self.contract_hash
            or state.get('empirical_support_sha256') != self.support_hash):
            raise ValueError('Incompatible sensitivity continuation; V1 cannot resume as V2.')
        self.rng.bit_generator.state = copy.deepcopy(state['rng_state'])

    def require_training_ready(self):
        if not self.training_authorized:
            raise ValueError('V2 validation config cannot train; explicit fresh-training authorization required.')
        path=self.root/'results/analysis/2026-11-14_pricing_v2_runtime_integration_validation/runtime_status.json'
        status=json.loads(path.read_text())
        if (status.get('status')!='INTEGRATED_VALIDATED_NOT_TRAINED'
            or status.get('contract_sha256')!=self.contract_hash
            or status.get('empirical_support_sha256')!=self.support_hash):
            raise ValueError('Validated V2 runtime status required before training.')

class V2PriceContract:
    """Existing inverse-epsilon threshold with V2 reference values and units."""
    def __init__(self, c):
        self.P_BASE_USD = float(c['P_base'])
        self.L_BASE_KM = float(c['L_base'])
        self.CANDIDATE_PRICES = np.asarray(ACTIONS)*self.P_BASE_USD
        self.P_PLATFORM_MIN = float(self.CANDIDATE_PRICES[0])
        self.P_PLATFORM_MAX = float(self.CANDIDATE_PRICES[-1])
    def maximum_price(self, distance_km, epsilon):
        if not np.isfinite([distance_km,epsilon]).all() or distance_km < 0 or epsilon <= 0:
            raise ValueError('Finite km and positive epsilon required; no epsilon fallback.')
        value = self.P_BASE_USD+(self.P_BASE_USD/epsilon)*((distance_km-self.L_BASE_KM)/self.L_BASE_KM)
        if not np.isfinite(value):raise ValueError('Nonfinite threshold.')
        return float(value)
    def effective_threshold(self, raw):
        if not np.isfinite(raw):raise ValueError('Nonfinite preference.')
        return max(self.P_PLATFORM_MIN,float(raw))
    def feasible_mask(self, threshold):
        if not np.isfinite(threshold):raise ValueError('Nonfinite threshold.')
        return self.CANDIDATE_PRICES <= threshold

def resolve_pricing(version, provider):
    from src.pricing import passenger_sensitive_v1 as v1
    if version == 'WEATHER_TIME_CONDITIONED_V2':
        from src.pricing.passenger_sensitive_v2_conditioned import ConditionedV2SensitivityProvider
        if type(provider) is ConditionedV2SensitivityProvider:return provider.pricing
        raise ValueError('Explicit conditional provider required.')
    if version == 'v1' and getattr(provider,'version','v1') == 'v1':return v1
    if version == 'v2' and type(provider) is V2EmpiricalSensitivityProvider:return provider.pricing
    raise ValueError('Explicit compatible passenger_sensitivity_version/provider required.')
