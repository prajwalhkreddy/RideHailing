# Feasible OD pricing

`FEASIBLE_OD_PRICING_V1` is an opt-in master §5.1/§5.4 correction. Instantiate
`src.simulation.od_pricing_runtime.ODPricingRuntime` with the existing production
engine arguments. A shared 13→64→64→7 learner independently selects one action
for each historical supported `(origin, destination)` at the slot boundary,
before current requests are inspected. This does not establish full master compliance.

## State contract

| Positions | Feature | Units and timing |
|---|---|---|
| 0 | CNN demand at origin | Requests in current 30-minute slot; existing forecast snapshot availability checks |
| 1 | Origin successful-dispatch EWMA | Dispatches per slot: existing operational `F_hat` in dispatches/minute × 30; includes only completed preceding slots |
| 2 | Incoming vehicles at origin | Count of known passenger commitments dropping off during `(t,t+30min]`; committed before t |
| 3–11 | Origin routing response | Nine masked probabilities, STAY/N/NE/E/SE/S/SW/W/NW; existing global routing-policy snapshot |
| 12 | Destination popularity | Existing ordinal encoding 0/.25/.5/.75/1, available at decision time |

No destination feature substitutes for an origin feature. The existing routing
producer supplies the grid policy response; private vehicle utilities are not
added to the pricing state. Primary and target networks both take 13 features.
The shared existing learner update retains Adam, Huber loss, gamma, target
update, replay capacity and exploration schedule. Historical 15D weights are
incompatible; this task performs no training.

## Feasibility and price actions

`od_contract.load_support()` reads only January 2026 pickup rows from the existing
spatial trip artifact. It reuses the empirical generator's finite duration,
distance and fare eligibility checks. Positive observed OD count defines the mask;
it is not a fitted significance threshold. Support is sorted and hashed. The
January evidence contains 3,699,644 rows, 3,616,239 generator-eligible rows and
9,572 pairs, rather than the Cartesian 20,164 possibilities. No protected
March evaluation observations define support. An OD absent from the mask fails
closed; no new pair is inferred from current requests. Explicit `od_support`
injection supports bounded fixtures and must pass the same metadata checks.
A stricter meaningful-support threshold requires a research decision.

The existing seven provisional V3 price actions and common P_base are retained.
Final master alignment of empirical bounds and action spacing remains unresolved.
Each matching request receives its OD's previously selected action.

## Reward and replay

`SUCCESSFUL_DISPATCH_REWARD_V1` remains authoritative. A successful assignment
contributes its offered fare once; rejected and accepted-unmatched requests
contribute zero. `environment_reward` is the latest slot's sum of OD rewards.
Audits separately retain descriptive accepted revenue and assignment revenue.
Replay tensors carry a parallel bounded identity deque `(slot, origin, destination)`;
FIFO eviction is synchronized. Next states retain the same OD identity.
The inherited Bellman update consumes those successful-assignment rewards.

## Full runtime persistence

Use `save_od_checkpoint(runtime, new_path)` and `load_od_checkpoint(path)` from
`src.simulation.od_pricing_checkpoint`. Saves are allowed only after a fully
committed slot. The atomic `FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_2` envelope preserves learner
and target weights, Adam state, replay/identities, RNGs, fleet, passenger commitments,
charging, operational statistics, environment clock, pricing configuration,
OD support and reward version. Immutable sources/artifacts are hashed. Missing,
corrupt, changed or incompatible historical checkpoint contracts are rejected.
The existing explicit value codec and checkpoint infrastructure are reused.
No historical checkpoint is migrated or overwritten. Failed slots cannot resume
through continued execution; restore a valid committed snapshot.

## Validation and remaining boundaries

Run from repository root in the established TensorFlow environment:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B scripts/validate_od_pricing.py --output results_v2/pricing_dqn/a_new_od_validation_run
```

The command executes small constructed fixtures, not a training run. Identical
offers preserve request outcomes, sensitivity RNG, fleet, commitments, charging and
operational behavior. Two-slot uninterrupted/resumed execution is compared exactly,
including weights, replay and a nonzero synthetic optimizer-state sentinel.

Historical V3 source remains unchanged. The new narrow slot adapter calls the same
production request, dispatch, movement, routing and charging components. Broader
master gaps remain: realized-demand generation, sensitivity/weather estimation,
CNN information availability, EWMA deviation, loss choice and hierarchy/privacy
integration. This correction does not resolve those questions or authorize training.

## Primary realized-demand protocol

The OD runtime now uses `HISTORICAL_REQUEST_REPLAY_V1` by default. Forecast
features remain separate from observed pickup counts. Earlier OD checkpoint
schemas are incompatible with the new demand contract. See
[simulation protocol](../simulation/README.md) for chronology, eligibility,
ordering, unsupported-OD behavior and bounded reproduction. Historical V3 keeps
its forecast-driven alternative unchanged.

## Provisional binned sensitivity

`ODPricingRuntime(sensitivity_contract=path, ...)` explicitly selects the versioned
positive empirical bin sampler; omission keeps historical V3. Common references
remain provisional. Continuous temperature/wind conditioning is an open decision,
not implemented by inventing bins. See [calibration evidence](../../results_v2/passenger_sensitivity/2026-11-17_binned_estimator_review/README.md).
OD schema `FEASIBLE_OD_HISTORICAL_REPLAY_RUNTIME_3` binds sampler version, calibration
hash and RNG; incompatible historical schemas cannot be mixed. No training authorized.

## Request-count-weighted calibration

The approved weighted mode is selected by passing the new versioned contract to
`sensitivity_contract`. It samples bins in proportion to historical request counts
within the selected pool; request distance is not a sampler input. Uniform and
historical V3 remain explicit compatible modes. Checkpoints reject version/hash
mixing. See [contract and limitations](../../results_v2/passenger_sensitivity/2026-11-17_request_weighted_calibration/README.md).
