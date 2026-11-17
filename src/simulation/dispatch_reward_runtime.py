"""Opt-in reward-only adaptation; explicitly NOT a master-aligned OD policy."""
import math
from src.pricing.dispatch_reward import REWARD_VERSION, reconcile_dispatch_rewards
from src.rl.dispatch_reward_dqn import DispatchRewardDQN
from src.simulation.slot_pricing_v3 import SlotPricingV3


class DispatchRewardRuntime(SlotPricingV3):
    """Reuse the historical slot once; commit only assignment rewards to replay."""
    reward_version = REWARD_VERSION

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Wrap the initialized learner without another RNG/model initialization.
        wrapper = object.__new__(DispatchRewardDQN)
        wrapper.core = self.learner
        wrapper.pending = None
        self.learner = wrapper

    def run_slot(self, requests=None, *, policy=None, weather_code=None):
        if self.learner.pending is not None:
            raise ValueError('Previous slot incomplete; runtime cannot continue')
        start = len(self.slot_audit)
        self.learner.pending = []
        try:
            rows = super().run_slot(requests, policy=policy, weather_code=weather_code)
            slots = self.slot_audit[start:]
            contexts = [row['destination_context'] for row in slots]
            if len(set(contexts)) != len(contexts) or len(slots) != len(self.learner.pending):
                raise ValueError('Slot/replay context mismatch')
            contributions, totals = reconcile_dispatch_rewards(rows, contexts)
            for slot in slots:
                if not math.isclose(totals[slot['destination_context']], slot['assignment_revenue'], rel_tol=1e-12, abs_tol=1e-9):
                    raise ValueError('Assignment reward reconciliation failed')
            for row, reward in zip(rows, contributions):
                row['reward_contribution'] = reward
                row['reward_contract'] = REWARD_VERSION
            for slot, transition in zip(slots, self.learner.pending):
                state, action, next_state, done = transition
                reward = totals[slot['destination_context']]
                self.learner.core.store(state, action, reward, next_state, done)
                slot['learning_reward'] = reward
                slot['reward_contract'] = REWARD_VERSION
            self.learner.pending = None
            # Reject the historical full-runtime checkpoint API before any writes.
            self.checkpoint_phase = 'DISPATCH_REWARD_POST_SLOT_COMMIT'
            return rows
        except Exception:
            self.checkpoint_phase = 'DISPATCH_REWARD_FAILED'
            raise
