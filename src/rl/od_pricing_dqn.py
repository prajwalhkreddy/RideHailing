"""Shared 13D OD learner; unchanged optimizer, targets and exploration schedule."""
from dataclasses import asdict
from collections import deque
from pathlib import Path
import json
import numpy as np
import tensorflow as tf
from src.rl.slot_pricing_v3 import SlotDQN
from src.rl.pricing_dqn import DQNConfig, action_index, bellman_targets, soft_update
from src.pricing.slot_v3 import load_contract, sha, CONTRACT
from src.pricing.od_contract import VERSION, validate_state
from src.pricing.dispatch_reward import REWARD_VERSION
from src.pricing.dqn_contract import grid, timestamp


class ODPricingDQN(SlotDQN):
    # Inherit the tested Bellman/Huber/soft-target update without a shape change.
    def __init__(self, seed=42, *, master_math=False, config=None, utc_mode=False, exploration_contract="HISTORICAL_LINEAR_V1"):
        if exploration_contract not in {"HISTORICAL_LINEAR_V1", "MASTER_UPDATE_STAIRCASE_V1"}: raise ValueError("Unknown exploration contract")
        self.exploration_contract=exploration_contract
        self.utc_mode=bool(utc_mode)
        self.master_math = bool(master_math)
        self.loss_contract = "MASTER_HALF_SQUARED_BELLMAN_V1" if master_math else "HISTORICAL_OD_HUBER_V1"
        self.contract = load_contract(); self.contract_hash = sha(CONTRACT)
        self.config = config or DQNConfig(seed=seed); self.rng = np.random.default_rng(seed)
        self.replay = deque(maxlen=self.config.replay_capacity); self.identities = deque(maxlen=self.config.replay_capacity)
        self.training_steps = 0; self.decisions = 0
        tf.keras.utils.set_random_seed(seed)
        def build():
            return tf.keras.Sequential([tf.keras.Input((13,)), tf.keras.layers.Dense(64, activation='relu'), tf.keras.layers.Dense(64, activation='relu'), tf.keras.layers.Dense(7)])
        self.online = build(); self.target = build(); self.target.set_weights(self.online.get_weights())
        self.online.compile(optimizer=tf.keras.optimizers.Adam(self.config.learning_rate), loss="mse" if self.master_math else tf.keras.losses.Huber())
        self.online.optimizer.build(self.online.trainable_variables)

    def train_step(self):
        if not self.master_math:
            return super().train_step()
        c = self.config
        if len(self.replay) < c.minimum_replay_size:
            return None
        ix = self.rng.choice(len(self.replay), c.batch_size, replace=False)
        states, actions, rewards, following, dones = zip(*(self.replay[i] for i in ix))
        y = bellman_targets(rewards, np.asarray(dones, bool), self.target(np.stack(following), training=False).numpy(), c.gamma)
        with tf.GradientTape() as tape:
            q = tf.gather(self.online(np.stack(states), training=True), actions, axis=1, batch_dims=1)
            loss = .5 * tf.reduce_mean(tf.square(tf.stop_gradient(y)-q))
        grads = tape.gradient(loss, self.online.trainable_variables)
        if not np.isfinite(float(loss)) or any(g is None or not np.isfinite(g.numpy()).all() for g in grads):
            raise ValueError('Nonfinite Bellman update')
        self.online.optimizer.apply_gradients(zip(grads, self.online.trainable_variables))
        soft_update(self.online, self.target, c.soft_target_tau)
        self.training_steps += 1
        return float(loss)

    @property
    def epsilon(self):
        c = self.config
        if self.exploration_contract == "MASTER_UPDATE_STAIRCASE_V1":
            return max(.1, 1.-.005*(self.training_steps//10))
        return max(c.epsilon_end, c.epsilon_start-(c.epsilon_start-c.epsilon_end)*self.training_steps/c.epsilon_decay_steps)

    def select_action(self, state, explore=True):
        q = self.online(validate_state(state)[None], training=False).numpy()[0]
        if not np.isfinite(q).all(): raise ValueError('Invalid OD Q values')
        action = int(self.rng.integers(7)) if explore and self.rng.random() < self.epsilon else int(q.argmax())
        self.decisions += 1
        return action

    def select_actions(self, states, explore=True):
        """Batched inference; RNG consumption retains sorted per-context order."""
        values=np.stack([validate_state(s) for s in states])
        q=np.concatenate([self.online(values[i:i+1024],training=False).numpy() for i in range(0,len(values),1024)])
        if not np.isfinite(q).all(): raise ValueError('Invalid OD Q values')
        actions=[]
        for row in q:
            actions.append(int(self.rng.integers(7)) if explore and self.rng.random()<self.epsilon else int(row.argmax()))
        self.decisions+=len(actions)
        return actions

    def store(self, s, a, r, n, done, *, identity):
        s = validate_state(s); n = validate_state(n); a = action_index(a)
        slot, origin, destination = identity
        from src.simulation.utc_od_state import instant
        identity = (str(instant(slot, True) if self.utc_mode else timestamp(slot, True)), grid(origin), grid(destination))
        if not isinstance(done, (bool, np.bool_)) or not np.isfinite(r) or r < 0:
            raise ValueError('Invalid OD transition')
        self.replay.append((s.copy(), a, float(r), n.copy(), bool(done)))
        self.identities.append(identity)

    def save(self, path):
        p = Path(path); p.mkdir(parents=True, exist_ok=False)
        self.online.save(p/'online.keras'); self.target.save(p/'target.keras')
        rows = list(self.replay)
        np.savez_compressed(p/'replay.npz', s=np.array([r[0] for r in rows]).reshape(-1,13), a=np.array([r[1] for r in rows]), r=np.array([r[2] for r in rows]), n=np.array([r[3] for r in rows]).reshape(-1,13), d=np.array([r[4] for r in rows],bool))
        (p/'checkpoint.json').write_text(json.dumps(dict(exploration_contract=self.exploration_contract, utc_mode=self.utc_mode, loss_contract=self.loss_contract, config=asdict(self.config), version=VERSION, reward_contract=REWARD_VERSION, contract_hash=self.contract_hash, seed=self.config.seed, training_steps=self.training_steps, decisions=self.decisions, rng=self.rng.bit_generator.state, identities=list(self.identities))))

    @classmethod
    def load(cls, path, *, master_math=False, utc_mode=False, exploration_contract="HISTORICAL_LINEAR_V1"):
        p = Path(path); m = json.loads((p/'checkpoint.json').read_text())
        if m.get('exploration_contract','HISTORICAL_LINEAR_V1') != exploration_contract: raise ValueError('Incompatible exploration checkpoint')
        if m.get('utc_mode') != utc_mode or m.get('loss_contract') != ('MASTER_HALF_SQUARED_BELLMAN_V1' if master_math else 'HISTORICAL_OD_HUBER_V1') or m.get('version') != VERSION or m.get('reward_contract') != REWARD_VERSION or m.get('contract_hash') != sha(CONTRACT):
            raise ValueError('Incompatible OD learner checkpoint')
        obj = cls(m['seed'], master_math=master_math, config=DQNConfig(**m['config']),utc_mode=utc_mode,exploration_contract=exploration_contract); obj.online = tf.keras.models.load_model(p/'online.keras'); obj.target = tf.keras.models.load_model(p/'target.keras', compile=False)
        for net in (obj.online, obj.target):
            if net.input_shape != (None,13) or net.output_shape != (None,7) or [l.units for l in net.layers] != [64,64,7] or any(not np.isfinite(w).all() for w in net.get_weights()): raise ValueError('Invalid OD network')
        with np.load(p/'replay.npz', allow_pickle=False) as z:
            if len({len(z[k]) for k in ('s','a','r','n','d')} | {len(m['identities'])}) != 1 or len(z['s']) > 100000: raise ValueError('Invalid OD replay')
            for row, identity in zip(zip(z['s'],z['a'],z['r'],z['n'],z['d']), m['identities']): obj.store(*row, identity=identity)
        obj.training_steps = m['training_steps']; obj.decisions = m['decisions']; obj.rng.bit_generator.state = m['rng']
        if int(obj.online.optimizer.iterations) != obj.training_steps or any(not np.isfinite(v.numpy()).all() for v in obj.online.optimizer.variables): raise ValueError('Invalid OD optimizer')
        return obj
