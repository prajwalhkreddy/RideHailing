# Passenger-Sensitive Pricing V1 — Meeting Summary

For complete methodology, chronology, authoritative numerical results and artifact provenance, see [README.md](README.md).

## Objective and method

Test request-level pricing with positive passenger sensitivity magnitude sampled from the frozen empirical support, scaled raw preference, platform-min protected acceptance, seven masked actions and request-step Bellman discount. The unchanged 13D state receives passenger information through masks only.

## Key results

Training through Episode25 is technically valid and numerically stable, with a learning signal. Policy stability and convergence are not established. The value function remains under-calibrated. March16 is development-only; protected evaluation remains untouched.

## Action dominance

Highest-feasible outperformed Episode25 on the fixed development fixture. This supports HIGH action-dominance risk, not universal dominance. DQN incremental dynamic value is unresolved.

## Questions for academic review

1. Is positive absolute sensitivity with empirical truncation/resampling acceptable?
2. Is the selected positive P0.5–P99.5 support methodology acceptable?
3. Is P_accept_c = max(platform minimum, P_raw_c) acceptable?
4. Is the 0.85–1.15 factor set sufficiently justified?
5. Is gamma = 0.99 per request the appropriate Bellman interpretation?
6. Given high action-dominance pressure, should training continue, reward/environment be reconsidered, or highest-feasible become a formal benchmark?
7. What evidence is required before claiming DQN adds dynamic value?

Further training: **AWAITING_ACADEMIC_REVIEW**.
