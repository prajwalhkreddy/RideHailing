# Bellman discount correction

**ACTIVE correction; old time-aware result is historical**

Purpose: preserve the specific evidence for this folder. Complete methodology, chronology and authoritative results: [canonical V1 README](../README.md).

- Old time-aware gamma accumulated almost undiscounted request rewards; horizon aliasing risk HIGH.
- Request-step gamma0.99 is frozen, including same-timestamp transitions.
- Offline return/horizon evidence is distinct from subsequent fresh training.
- 37 focused tests passed at this correction stage.

## Artifact files

- [discount_methodology_decision.json](discount_methodology_decision.json)
- [bellman_discount_comparison.csv](bellman_discount_comparison.csv)
- [effective_horizon.json](effective_horizon.json)
- [request_step_return_quartiles.csv](request_step_return_quartiles.csv)
