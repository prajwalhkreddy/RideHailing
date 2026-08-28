"""NB12 local supervised policy learning from corrected NB11 decisions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

from src.routing.baseline import ACTION_ORDER, GridRoutingFeatures, RoutingAction, RoutingState, valid_action_mask


# Each valid candidate has a separate validity field. Invalid candidate blocks
# are all zero. Within a valid block, missing numeric values become zero and a
# missing charging_available value becomes -1.
_CANDIDATE_FIELDS = (
    "valid", "grid_id", "predicted_demand", "supply_total", "supply_idle",
    "supply_busy", "supply_charging", "mean_fare", "std_fare", "ewma_fare",
    "ewma_std_fare", "mean_wait", "std_wait", "ewma_wait", "ewma_std_wait",
    "charging_available", "charging_wait",
)
STATE_FEATURE_ORDER = (
    "vehicle.current_grid",
    "vehicle.energy_level",
) + tuple(f"{action.value}.{field}" for action in ACTION_ORDER for field in _CANDIDATE_FIELDS)
STATE_DIMENSION = len(STATE_FEATURE_ORDER)
POLICY_ARCHITECTURE_VERSION = "routing-policy-87-64-32-5-v1"


@dataclass(frozen=True)
class RoutingLearningParameters:
    """Provisional engineering settings for local supervised policy learning."""

    hidden_units: tuple[int, int] = (64, 32)
    learning_rate: float = 0.001
    local_observation_capacity: int = 1000
    batch_size: int = 32
    local_epochs: int = 1

    def validate(self) -> None:
        if len(self.hidden_units) != 2 or any(not isinstance(unit, int) or unit <= 0 for unit in self.hidden_units):
            raise ValueError("routing_learning.hidden_units must contain two positive integers.")
        if not isinstance(self.learning_rate, (int, float)) or not np.isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("routing_learning.learning_rate must be positive and finite.")
        if any(not isinstance(value, int) or value <= 0 for value in (self.local_observation_capacity, self.batch_size, self.local_epochs)):
            raise ValueError("routing_learning capacity, batch_size, and local_epochs must be positive integers.")
        if self.batch_size > self.local_observation_capacity:
            raise ValueError("routing_learning.batch_size cannot exceed local_observation_capacity.")


def routing_learning_parameters_from_config(config: Mapping[str, Any]) -> RoutingLearningParameters:
    """Read corrected NB12 settings from the unified project configuration."""
    values = config.get("routing_learning")
    if not isinstance(values, Mapping):
        raise ValueError("routing_learning configuration is required for NB12.")
    parameters = RoutingLearningParameters(
        hidden_units=tuple(values["hidden_units"]),
        learning_rate=float(values["learning_rate"]),
        local_observation_capacity=int(values["local_observation_capacity"]),
        batch_size=int(values["batch_size"]),
        local_epochs=int(values["local_epochs"]),
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
    """Encode NB11 state deterministically in ``STATE_FEATURE_ORDER``."""
    values = [_finite_number(state.current_grid), _finite_number(state.energy_level)]
    for action in ACTION_ORDER:
        values.extend(_candidate_vector(state.action_features.get(action)))
    encoded = np.asarray(values, dtype=np.float32)
    if encoded.shape != (STATE_DIMENSION,) or not np.isfinite(encoded).all():
        raise ValueError("Routing state does not satisfy the fixed NB12 input contract.")
    return encoded


def action_mask_array(state: RoutingState) -> np.ndarray:
    """Return a separate boolean mask in fixed action order."""
    mask = valid_action_mask(state)
    return np.asarray([mask[action] for action in ACTION_ORDER], dtype=bool)


def _validate_mask(mask: np.ndarray) -> np.ndarray:
    result = np.asarray(mask, dtype=bool)
    if result.shape != (len(ACTION_ORDER),) or not result.any():
        raise ValueError("Action mask must contain five entries and at least one valid action.")
    return result


def masked_softmax(logits: np.ndarray, action_mask: np.ndarray) -> np.ndarray:
    """Numerically stable softmax over valid actions only."""
    values = np.asarray(logits, dtype=np.float64)
    mask = _validate_mask(action_mask)
    if values.shape != (len(ACTION_ORDER),) or not np.isfinite(values).all():
        raise ValueError("Policy logits must be a finite five-element vector.")
    shifted = values[mask] - np.max(values[mask])
    valid_exp = np.exp(shifted)
    probabilities = np.zeros(len(ACTION_ORDER), dtype=np.float32)
    probabilities[mask] = (valid_exp / valid_exp.sum()).astype(np.float32)
    return probabilities


def build_routing_policy_model(parameters: RoutingLearningParameters, *, seed: int | None = None) -> Model:
    """Build the common 87 -> 64 -> 32 -> 5-logit policy architecture."""
    parameters.validate()
    if seed is not None:
        tf.keras.utils.set_random_seed(seed)
    inputs = Input(shape=(STATE_DIMENSION,), dtype="float32", name="routing_state")
    hidden = Dense(parameters.hidden_units[0], activation="relu", name="dense_64")(inputs)
    hidden = Dense(parameters.hidden_units[1], activation="relu", name="dense_32")(hidden)
    outputs = Dense(len(ACTION_ORDER), activation="linear", name="action_logits")(hidden)
    return Model(inputs=inputs, outputs=outputs, name="LocalRoutingPolicyNetwork")


@dataclass(frozen=True)
class LocalPolicyObservation:
    """One local supervised example produced by an actual NB11 decision."""

    state: np.ndarray
    chosen_action_index: int
    action_mask: np.ndarray
    utility_vector: np.ndarray | None = None
    slot_id: int | None = None


class LocalObservationBuffer:
    """Bounded vehicle-local training examples; never exported."""

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("Observation capacity must be positive.")
        self._items: deque[LocalPolicyObservation] = deque(maxlen=capacity)

    def __len__(self) -> int:
        return len(self._items)

    def add(self, observation: LocalPolicyObservation) -> None:
        _validate_observation(observation)
        self._items.append(observation)

    def latest(self, size: int) -> list[LocalPolicyObservation]:
        if size <= 0 or not self._items:
            raise ValueError("Observation batch size must be positive and available.")
        return list(self._items)[-min(size, len(self._items)):]


def _validate_observation(observation: LocalPolicyObservation) -> None:
    if observation.state.shape != (STATE_DIMENSION,) or not np.isfinite(observation.state).all():
        raise ValueError("Observation state violates the fixed 87-feature contract.")
    mask = _validate_mask(observation.action_mask)
    if not 0 <= observation.chosen_action_index < len(ACTION_ORDER) or not mask[observation.chosen_action_index]:
        raise ValueError("Chosen action must be valid under the observation mask.")
    if observation.utility_vector is not None:
        utility = np.asarray(observation.utility_vector)
        if utility.shape != (len(ACTION_ORDER),):
            raise ValueError("Optional audit utility vector must have five entries.")


class LocalRoutingLearner:
    """One supervised policy learner per vehicle; observations remain local."""

    def __init__(self, vehicle_id: int, parameters: RoutingLearningParameters, *, seed: int) -> None:
        parameters.validate()
        self.vehicle_id = int(vehicle_id)
        self.parameters = parameters
        self.policy_model = build_routing_policy_model(parameters, seed=seed)
        self.optimizer = Adam(learning_rate=parameters.learning_rate)
        self.observations = LocalObservationBuffer(parameters.local_observation_capacity)
        self.gradient_updates = 0
        self.local_sample_count = 0
        self._trained_slots: set[int] = set()

    def policy_logits(self, state: RoutingState | np.ndarray) -> np.ndarray:
        vector = encode_routing_state(state) if isinstance(state, RoutingState) else np.asarray(state, dtype=np.float32)
        if vector.shape != (STATE_DIMENSION,) or not np.isfinite(vector).all():
            raise ValueError("Policy input violates the fixed NB12 state-vector contract.")
        return self.policy_model(vector[None, :], training=False).numpy()[0].astype(np.float32, copy=False)

    def policy_probabilities(self, state: RoutingState | np.ndarray, action_mask: np.ndarray | None = None) -> np.ndarray:
        if action_mask is None:
            if not isinstance(state, RoutingState):
                raise ValueError("An explicit action mask is required with an encoded state.")
            action_mask = action_mask_array(state)
        return masked_softmax(self.policy_logits(state), action_mask)

    def record_observation(
        self,
        state: RoutingState,
        chosen_action: RoutingAction,
        *,
        action_mask: np.ndarray | None = None,
        utility_vector: np.ndarray | None = None,
        slot_id: int | None = None,
    ) -> None:
        """Record NB11's chosen action as the supervised class label."""
        mask = action_mask_array(state) if action_mask is None else _validate_mask(action_mask)
        observation = LocalPolicyObservation(
            state=encode_routing_state(state).copy(),
            chosen_action_index=ACTION_ORDER.index(chosen_action),
            action_mask=mask.copy(),
            utility_vector=None if utility_vector is None else np.asarray(utility_vector, dtype=np.float32).copy(),
            slot_id=slot_id,
        )
        self.observations.add(observation)

    def _batch_loss(self, states: tf.Tensor, actions: tf.Tensor, masks: tf.Tensor, *, training: bool) -> tf.Tensor:
        logits = self.policy_model(states, training=training)
        masked_logits = tf.where(masks, logits, tf.constant(-1e9, dtype=logits.dtype))
        return tf.reduce_mean(tf.keras.losses.sparse_categorical_crossentropy(actions, masked_logits, from_logits=True))

    def train_for_slot(self, slot_index: int) -> float | None:
        """Train at most once at the end of a 30-minute main slot."""
        if slot_index in self._trained_slots:
            raise ValueError("NB12 training may run at most once per main slot.")
        self._trained_slots.add(slot_index)
        if not self.observations:
            return None
        batch = self.observations.latest(self.parameters.batch_size)
        states = tf.convert_to_tensor(np.stack([item.state for item in batch]), dtype=tf.float32)
        actions = tf.convert_to_tensor([item.chosen_action_index for item in batch], dtype=tf.int32)
        masks = tf.convert_to_tensor(np.stack([item.action_mask for item in batch]), dtype=tf.bool)
        loss: tf.Tensor | None = None
        for _ in range(self.parameters.local_epochs):
            with tf.GradientTape() as tape:
                loss = self._batch_loss(states, actions, masks, training=True)
            gradients = tape.gradient(loss, self.policy_model.trainable_variables)
            self.optimizer.apply_gradients(zip(gradients, self.policy_model.trainable_variables))
            self.gradient_updates += 1
        self.local_sample_count += len(batch)
        return float(loss.numpy()) if loss is not None else None

    def reset_from_global_weights(self, weights: Sequence[np.ndarray]) -> None:
        """Initialize a local round from externally supplied common weights."""
        self.policy_model.set_weights([np.asarray(weight).copy() for weight in weights])

    def export_local_update(self) -> dict[str, Any]:
        """Export compatible policy weights/metadata, never local observations."""
        return {
            "vehicle_id": self.vehicle_id,
            "weights": [weight.copy() for weight in self.policy_model.get_weights()],
            "sample_count": self.local_sample_count,
            "state_dimension": STATE_DIMENSION,
            "action_order": [action.value for action in ACTION_ORDER],
            "architecture_version": POLICY_ARCHITECTURE_VERSION,
        }
