"""Frozen 169-feature operational-state encoding; no legacy substitutions."""
from dataclasses import dataclass
import numpy as np
from src.routing.baseline import ACTION_ORDER

STATE_FEATURE_ORDER = tuple(f'{a}.{f}' for a in ('STAY','N','NE','E','SE','S','SW','W','NW') for f in ('mu','sigma','F_hat')) + tuple(f'H_hat.Grid_ID_{g}' for g in range(142))

@dataclass(frozen=True)
class RoutingState:
    values: np.ndarray
    mask: np.ndarray

    @classmethod
    def from_producer(cls, routing, producer, timestamp, grid):
        values, mask = routing.encode(producer,timestamp,grid,expected_dimension=169)
        return cls(values,mask)


def encode_routing_state(state):
    if not isinstance(state,RoutingState):
        raise ValueError('Legacy routing state is incompatible: require final operational 169-feature state.')
    values=np.asarray(state.values,dtype=np.float32)
    mask=action_mask_array(state)
    if values.shape!=(169,) or not np.isfinite(values).all():
        raise ValueError('Expected finite 169-feature state.')
    if (values<0).any():raise ValueError('Operational estimates must be nonnegative.')
    if np.any(values[:27].reshape(9,3)[~mask]!=0):
        raise ValueError('Masked positions must be zero placeholders.')
    return values.copy()


def action_mask_array(state):
    if not isinstance(state,RoutingState):raise ValueError('Final operational RoutingState required.')
    mask=np.asarray(state.mask,dtype=bool)
    if mask.shape!=(9,) or not mask[0]:raise ValueError('Nine-action mask with valid STAY required.')
    return mask.copy()
