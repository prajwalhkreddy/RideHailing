"""Conservative Gaussian RDP accounting for fixed-public-participation clients.

Replace-one-driver adjacency: sensitivity of the equal-client mean is 2C/n.
No sampling amplification. Diagnostics and trusted resume state are NOT DP releases.
Reference: https://arxiv.org/abs/1702.07476
"""
import numpy as np

ORDERS = np.r_[np.arange(1.01, 2, .01), np.arange(2, 64, .1), np.arange(64, 513)]


def account(noise_multiplier, rounds, delta=1e-5, orders=ORDERS):
    if not np.isfinite(noise_multiplier) or noise_multiplier <= 0:
        raise ValueError('Positive finite noise multiplier required')
    if rounds < 0 or int(rounds) != rounds or not 0 < delta < 1:
        raise ValueError('Invalid accounting parameters')
    orders = np.asarray(orders, dtype=float)
    if not np.isfinite(orders).all() or (orders <= 1).any():
        raise ValueError('RDP orders must exceed one')
    per = orders / (2 * noise_multiplier ** 2)
    total = rounds * per
    eps = total + np.log(1 / delta) / (orders - 1)
    j = int(np.argmin(eps))
    return dict(epsilon=float(eps[j]) if rounds else 0., delta=delta,
                optimal_order=float(orders[j]), rounds=int(rounds),
                orders=orders.tolist(), per_round_RDP=per.tolist(),
                cumulative_RDP=total.tolist())


def solve_multiplier(target, rounds=576, delta=1e-5):
    if not np.isfinite(target) or target <= 0:
        raise ValueError('Positive target required')
    lo, hi = 1e-6, 1.
    while account(hi, rounds, delta)['epsilon'] > target:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if account(mid, rounds, delta)['epsilon'] > target:
            lo = mid
        else:
            hi = mid
    return hi


def clip_updates(updates, bound=1.):
    a = np.asarray(updates, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all() or not np.isfinite(bound) or bound <= 0:
        raise ValueError('Invalid client updates or clipping bound')
    norms = np.linalg.norm(a, axis=1)
    scale = np.minimum(1., bound / np.maximum(norms, np.finfo(float).tiny))
    return a * scale[:, None], norms


def noisy_mean(clipped_sum, participants, noise_multiplier, rng, bound=1.):
    if participants <= 0 or noise_multiplier <= 0:
        raise ValueError('Invalid aggregation parameters')
    sensitivity = 2 * bound / participants
    return clipped_sum / participants + rng.normal(
        0., noise_multiplier * sensitivity, size=clipped_sum.shape)
