"""Reward-versioned learner envelope around unchanged historical DQN mechanics."""
import json
from pathlib import Path
from src.pricing.dispatch_reward import REWARD_VERSION
from src.rl.slot_pricing_v3 import SlotDQN


class DispatchRewardDQN:
    """Delegate optimization; never accept historical replay as corrected replay."""
    def __init__(self, seed=42):
        self.core = SlotDQN(seed)
        self.pending = None

    def __getattr__(self, name):
        return getattr(self.core, name)

    def store(self, state, action, reward, next_state, done):
        if self.pending is None:
            raise ValueError('Reward commit requires a completed dispatch slot')
        self.pending.append((state, action, next_state, done))

    def save(self, path):
        if self.pending is not None:
            raise ValueError('Cannot checkpoint an uncommitted slot')
        path = Path(path)
        path.mkdir(parents=True, exist_ok=False)
        self.core.save(path / 'learner')
        (path / 'checkpoint.json').write_text(json.dumps({
            'version': REWARD_VERSION, 'reward_contract': REWARD_VERSION,
            'scope': 'LEARNER_ONLY_NOT_FULL_RUNTIME',
            'state_contract': 'HISTORICAL_15D_DESTINATION_ONLY',
        }, indent=2) + '\n')

    @classmethod
    def load(cls, path):
        path = Path(path)
        metadata = json.loads((path / 'checkpoint.json').read_text())
        if metadata.get('version') != REWARD_VERSION or metadata.get('reward_contract') != REWARD_VERSION:
            raise ValueError('Incompatible reward checkpoint contract')
        if metadata.get('scope') != 'LEARNER_ONLY_NOT_FULL_RUNTIME' or metadata.get('state_contract') != 'HISTORICAL_15D_DESTINATION_ONLY':
            raise ValueError('Incompatible checkpoint scope/state')
        obj = object.__new__(cls)
        obj.core = SlotDQN.load(path / 'learner')
        obj.pending = None
        return obj
