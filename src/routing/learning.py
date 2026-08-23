"""NB12 local-only DQN-style routing learning.

The module deliberately owns no simulator state and emits no raw experience.
It turns the frozen NB11 routing state into a fixed, masked vector, learns per
vehicle from completed next-slot dispatch outcomes, and exports weights only.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

from src.routing.baseline import ACTION_ORDER, GridRoutingFeatures, RoutingAction, RoutingState, select_action as select_nb11_action, valid_action_mask


# ``valid`` is separate from numeric context so a zero-valued, valid grid is
# distinguishable from a padded/masked neighbour.  ``None`` charging capacity
# is encoded as -1; all other absent candidate blocks are zeros.
_CANDIDATE_FIELDS = (
    "valid",
    "grid_id",
    "predicted_demand",
    "supply_total",
    "supply_idle",
    "supply_busy",
    "supply_charging",
    "mean_fare",
    "std_fare",
    "ewma_fare",
    "ewma_std_fare",
    "mean_wait",
    "std_wait",
    "ewma_wait",
    "ewma_std_wait",
    "charging_available",
    "charging_wait",
)
STATE_FEATURE_ORDER = (
    "vehicle.current_grid",
    "vehicle.energy_level",
) + tuple(f"{action.value}.{field}" for action in ACTION_ORDER for field in _CANDIDATE_FIELDS)
STATE_DIMENSION = len(STATE_FEATURE_ORDER)


@dataclass(frozen=True)
class RoutingLearningParameters:
    """Approved provisional NB12 local-learning hyperparameters."""

    hidden_units: tuple[int, int] = (64, 32)
    learning_rate: float = 0.001
    gamma: float = 0.95
    replay_capacity: int = 1000
    batch_size: int = 32
    epsilon_start: float = 0.10
    epsilon_min: float = 0.01
    epsilon_decay: float = 0.995
    target_update_interval_slots: int = 5

    def validate(self) -> None:
        if len(self.hidden_units) != 2 or any(not isinstance(unit, int) or unit <= 0 for unit in self.hidden_units):
            raise ValueError("routing_learning.hidden_units must contain two positive integers.")
        if self.learning_rate <= 0 or not 0 <= self.gamma <= 1:
            raise ValueError("routing_learning learning_rate/gamma are invalid.")
        if self.replay_capacity <= 0 or self.batch_size <= 0 or self.batch_size > self.replay_capacity:
            raise ValueError("routing_learning replay_capacity and batch_size are invalid.")
        if not 0 <= self.epsilon_min <= self.epsilon_start <= 1 or not 0 < self.epsilon_decay <= 1:
            raise ValueError("routing_learning epsilon settings are invalid.")
        if self.target_update_interval_slots <= 0:
            raise ValueError("routing_learning.target_update_interval_slots must be positive.")


def routing_learning_parameters_from_config(config: Mapping[str, Any]) -> RoutingLearningParameters:
    """Read validated NB12 parameters from the unified project configuration."""
    values = config.get("routing_learning")
    if not isinstance(values, Mapping):
        raise ValueError("routing_learning configuration is required for NB12.")
    parameters = RoutingLearningParameters(
        hidden_units=tuple(values["hidden_units"]),
        learning_rate=float(values["learning_rate"]),
        gamma=float(values["gamma"]),
        replay_capacity=int(values["replay_capacity"]),
        batch_size=int(values["batch_size"]),
        epsilon_start=float(values["epsilon_start"]),
        epsilon_min=float(values["epsilon_min"]),
        epsilon_decay=float(values["epsilon_decay"]),
        target_update_interval_slots=int(values["target_update_interval_slots"]),
    )
    parameters.validate()
    return parameters


def _finite_number(value: float | int | None, *, missing: float = 0.0) -> float:
    if value is None:
        return missing
    result = float(value)
    if not np.isfinite(result):
        raise ValueError("Routing state features must be finite or None.")
    return result


def _candidate_vector(features: GridRoutingFeatures | None) -> list[float]:
    if features is None:
        return [0.0] * len(_CANDIDATE_FIELDS)
    charging_available = -1.0 if features.charging_available is None else float(features.charging_available)
    return [
        1.0,
        _finite_number(features.grid_id),
        _finite_number(features.predicted_demand),
        _finite_number(features.supply_total),
        _finite_number(features.supply_idle),
        _finite_number(features.supply_busy),
        _finite_number(features.supply_charging),
        _finite_number(features.mean_fare),
        _finite_number(features.std_fare),
        _finite_number(features.ewma_fare),
        _finite_number(features.ewma_std_fare),
        _finite_number(features.mean_wait),
        _finite_number(features.std_wait),
        _finite_number(features.ewma_wait),
        _finite_number(features.ewma_std_wait),
        charging_available,
        _finite_number(features.charging_wait),
    ]


def encode_routing_state(state: RoutingState) -> np.ndarray:
    """Encode NB11 state in ``STATE_FEATURE_ORDER`` as a finite float32 vector."""
    values = [_finite_number(state.current_grid), _finite_number(state.energy_level)]
    for action in ACTION_ORDER:
        values.extend(_candidate_vector(state.action_features.get(action)))
    encoded = np.asarray(values, dtype=np.float32)
    if encoded.shape != (STATE_DIMENSION,) or not np.isfinite(encoded).all():
        raise ValueError("Routing state does not satisfy the fixed NB12 input contract.")
    return encoded


def action_mask_array(state: RoutingState) -> np.ndarray:
    """Return the frozen NB11 action mask in ``ACTION_ORDER`` order."""
    return np.asarray([valid_action_mask(state)[action] for action in ACTION_ORDER], dtype=bool)


def build_routing_q_model(parameters: RoutingLearningParameters, *, seed: int | None = None) -> Model:
    """Build the shared 87 -> 64 -> 32 -> 5 linear-Q architecture."""
    parameters.validate()
    if seed is not None:
        tf.keras.utils.set_random_seed(seed)
    inputs = Input(shape=(STATE_DIMENSION,), dtype="float32", name="routing_state")
    hidden = Dense(parameters.hidden_units[0], activation="relu", name="dense_64")(inputs)
    hidden = Dense(parameters.hidden_units[1], activation="relu", name="dense_32")(hidden)
    outputs = Dense(len(ACTION_ORDER), activation="linear", name="q_values")(hidden)
    model = Model(inputs=inputs, outputs=outputs, name="LocalRoutingQNetwork")
    model.compile(optimizer=Adam(learning_rate=parameters.learning_rate), loss="mse")
    return model


@dataclass(frozen=True)
class LocalRoutingExperience:
    """A completed local outcome; dispatch is observed in the next main slot."""

    state: np.ndarray
    action_index: int
    reward: float
    next_state: np.ndarray
    next_action_mask: np.ndarray
    terminal: bool = False


class LocalReplayBuffer:
    """Bounded, vehicle-local raw experience storage (never exported)."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("Replay capacity must be positive.")
        self._items: deque[LocalRoutingExperience] = deque(maxlen=capacity)

    def __len__(self) -> int:
        return len(self._items)

    def add(self, experience: LocalRoutingExperience) -> None:
        _validate_experience(experience)
        self._items.append(experience)

    def sample(self, size: int, rng: np.random.Generator) -> list[LocalRoutingExperience]:
        if size <= 0 or size > len(self._items):
            raise ValueError("Replay sample size must be available and positive.")
        indices = rng.choice(len(self._items), size=size, replace=False)
        items = tuple(self._items)
        return [items[int(index)] for index in indices]


def _validate_experience(experience: LocalRoutingExperience) -> None:
    if experience.state.shape != (STATE_DIMENSION,) or experience.next_state.shape != (STATE_DIMENSION,):
        raise ValueError("Replay states must satisfy the fixed NB12 vector dimension.")
    if experience.next_action_mask.shape != (len(ACTION_ORDER),):
        raise ValueError("Replay next_action_mask has the wrong action dimension.")
    if not 0 <= experience.action_index < len(ACTION_ORDER):
        raise ValueError("Replay action index is invalid.")
    if experience.reward not in (0.0, 1.0) or not np.isfinite(experience.state).all() or not np.isfinite(experience.next_state).all():
        raise ValueError("Replay experience must contain finite states and binary reward.")


class LocalRoutingLearner:
    """One DQN-style learner per participating vehicle; no shared mutable state."""

    def __init__(self, vehicle_id: int, parameters: RoutingLearningParameters, *, seed: int) -> None:
        parameters.validate()
        self.vehicle_id = int(vehicle_id)
        self.parameters = parameters
        self.rng = np.random.default_rng(seed)
        self.online_model = build_routing_q_model(parameters, seed=seed)
        self.target_model = build_routing_q_model(parameters, seed=seed + 1)
        self.target_model.set_weights(self.online_model.get_weights())
        self.replay = LocalReplayBuffer(parameters.replay_capacity)
        self.epsilon = parameters.epsilon_start
        self.gradient_updates = 0
        self.local_sample_count = 0
        self._trained_slots: set[int] = set()

    def q_values(self, state: RoutingState | np.ndarray) -> np.ndarray:
        vector = encode_routing_state(state) if isinstance(state, RoutingState) else np.asarray(state, dtype=np.float32)
        if vector.shape != (STATE_DIMENSION,) or not np.isfinite(vector).all():
            raise ValueError("Q-value input violates the NB12 state-vector contract.")
        return self.online_model(vector[None, :], training=False).numpy()[0].astype(np.float32, copy=False)

    def choose_action(self, state: RoutingState, *, training: bool) -> RoutingAction:
        """Choose only valid actions; exploitation keeps NB11's deterministic ties."""
        mask = action_mask_array(state)
        if not mask.any():
            raise ValueError("Routing state has no valid action.")
        if training and self.rng.random() < self.epsilon:
            return ACTION_ORDER[int(self.rng.choice(np.flatnonzero(mask)))]
        q_values = self.q_values(state)
        return select_nb11_action(state, {action: float(q_values[index]) for index, action in enumerate(ACTION_ORDER)})

    def record_completed_outcome(
        self,
        state: RoutingState,
        action: RoutingAction,
        dispatch_received_next_slot: bool | None,
        next_state: RoutingState,
        *,
        terminal: bool = False,
    ) -> bool:
        """Record one outcome only after the next-slot dispatch result is known.

        ``None`` means the outcome is not completed yet and intentionally
        creates no fabricated reward or replay record.
        """
        if dispatch_received_next_slot is None:
            return False
        mask = action_mask_array(state)
        action_index = ACTION_ORDER.index(action)
        if not mask[action_index]:
            raise ValueError("A masked action cannot be recorded as an experience.")
        experience = LocalRoutingExperience(
            state=encode_routing_state(state).copy(),
            action_index=action_index,
            reward=1.0 if dispatch_received_next_slot else 0.0,
            next_state=encode_routing_state(next_state).copy(),
            next_action_mask=action_mask_array(next_state).copy(),
            terminal=bool(terminal),
        )
        self.replay.add(experience)
        return True

    def train_for_slot(self, slot_index: int) -> float | None:
        """Perform at most one local minibatch update for a completed main slot."""
        if slot_index in self._trained_slots:
            raise ValueError("NB12 training may run at most once per main slot.")
        self._trained_slots.add(slot_index)
        if len(self.replay) < self.parameters.batch_size:
            return None
        batch = self.replay.sample(self.parameters.batch_size, self.rng)
        states = np.stack([item.state for item in batch]).astype(np.float32, copy=False)
        next_states = np.stack([item.next_state for item in batch]).astype(np.float32, copy=False)
        targets = self.online_model(states, training=False).numpy()
        target_next_q = self.target_model(next_states, training=False).numpy()
        for index, item in enumerate(batch):
            bootstrap = 0.0
            if not item.terminal and item.next_action_mask.any():
                bootstrap = float(np.max(target_next_q[index, item.next_action_mask]))
            targets[index, item.action_index] = item.reward + self.parameters.gamma * bootstrap
        loss = self.online_model.train_on_batch(states, targets)
        self.gradient_updates += 1
        self.local_sample_count += len(batch)
        self.epsilon = max(self.parameters.epsilon_min, self.epsilon * self.parameters.epsilon_decay)
        if slot_index > 0 and slot_index % self.parameters.target_update_interval_slots == 0:
            self.target_model.set_weights(self.online_model.get_weights())
        return float(loss)

    def reset_from_global_weights(self, weights: Sequence[np.ndarray]) -> None:
        """Initialize a local round from common global weights; replay remains local."""
        copied = [np.asarray(weight).copy() for weight in weights]
        self.online_model.set_weights(copied)
        self.target_model.set_weights(copied)

    def export_local_update(self) -> dict[str, Any]:
        """Return federation-ready weights and sample count, never raw replay data."""
        return {
            "vehicle_id": self.vehicle_id,
            "weights": [weight.copy() for weight in self.online_model.get_weights()],
            "sample_count": self.local_sample_count,
            "state_dimension": STATE_DIMENSION,
            "action_order": [action.value for action in ACTION_ORDER],
        }
