# Request-Level Action/Replaying Contract — Current Resolution

**APPROVED AND IMPLEMENTED.** The former OD/slot granularity incompatibility below was real under the legacy contract and is now resolved by explicit authorization of request-level actions/replay, unchanged13D state, next-actionable masks, time-aware discount and slot-controlled updates. See request_level_architecture.md for code and validation evidence. No further architectural approval is pending.

The separate support-provenance question was explicitly resolved by authorizing Jan1–Mar15-only support recalculation. Only selection of the positive epsilon floor remains unresolved; all allowed candidates are evaluated and no floor is silently frozen.

## Historical preflight evidence — superseded status flags

# Action-Granularity Reconciliation

Status: **PASSENGER_MASK_ACTION_GRANULARITY_COMPATIBLE = NO**.

This preflight was completed before any implementation change. No model was loaded, resumed or initialized, and no calibration data was opened.

## Current execution flow

| Question | Verified current behavior | Evidence |
|---|---|---|
| Decision unit | One observed origin/destination pair per 30-minute slot, shared by multiple passenger requests | `src/simulation/final_production.py:230–233`; frozen `pricing_training_contract.json` transition field |
| Action timing | On the first encountered request for an OD, create `states[key]` and `selected[key]`; reuse `selected[key]` thereafter | `run_slot`, key `(r.origin_grid,r.destination_grid)` and `if key not in selected` |
| Passenger epsilon timing | Sampled separately for each request after the shared action has already been selected | `src/pricing/empirical_sensitivity.py:78–85`, `evaluate_resolved` |
| Passenger P_c timing | Calculated from the sampled epsilon inside that same response evaluation, after action selection | `maximum_price` call in `evaluate_resolved` |
| Selection API | `select_action(state, explore=True)` samples among all seven actions or uses unmasked argmax; no passenger mask argument | `src/rl/pricing_dqn.py:100–107` |
| Reward aggregation | Successful fares accumulated into `od_rewards[key]` | `src/simulation/final_production.py:250` |
| Replay unit | One transition per selected OD/slot, with its action and total successful fare; next state is the next slot's same OD | `src/simulation/final_production.py:261–262` |
| No-action representation | Replay requires an integer action 0..6; no absent-action event | `src/rl/pricing_dqn.py:42–54` |
| Bellman target | Replay stores state/action/reward/next-state/done, not passenger feasibility or next-state mask | `src/rl/pricing_dqn.py:51–59,109–114` |

## Why this is incompatible

Passengers sharing an OD/slot can have different sampled epsilon and trip-distance values, and therefore different P_c and feasible sets. Moving the first passenger's epsilon draw before the shared action would constrain only that first passenger, not later passengers. Reselecting for later passengers changes the decision unit; silently rejecting a later passenger or replacing the already selected action does not implement the requested per-passenger feasible-action policy. An intersection across future passengers would introduce a different group policy and potentially future information; it is not authorized.

The required V1 action mask must precede a passenger-specific action decision. That is incompatible with retaining the current shared OD/slot action and aggregated transition contract unchanged. This is an architectural incompatibility, not a floating-point or data defect.

## Replay consequence

**NO_ACTION_REPLAY_SEMANTICS_BLOCKER = YES** under the current contract. A no-offer request cannot be inserted as a normal replay transition without inventing an action. The current infrastructure does not define request-level no-action accounting, its effect on OD reward/transition boundaries, or bootstrap handling when no feasible next action exists. Merely passing `None` to `store` fails action validation. No eighth action, substitute 0.85 action, or synthetic transition is authorized.

## Minimal architectural decision required — not implemented

Approve a request-level decision contract: sample one positive epsilon and compute P_c before selecting a masked action for that request. Define the relationship to the existing 13D OD state, request/slot clock, reward attribution, terminal transitions and next-state feasibility/Bellman target. No-offer events need explicit counters and zero reward contribution without a fabricated action; decide how those events advance the environment relative to replayed actionable decisions.

This may retain the seven outputs and existing network topology, but changes the MDP decision/replay semantics and potentially the mask context carried by replay. It cannot be presented as a mask-only patch. No particular state augmentation, transition skipping rule or hierarchy redesign is selected here.

The requested stop conditions 1 and 2 therefore apply. Stage A implementation and Stage B calibration/validation stop here. Existing source code and frozen artifacts remain unchanged.
