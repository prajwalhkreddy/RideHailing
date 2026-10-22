# Short pricing-DQN / simulator integration

**DQN_SIMULATOR_INTEGRATION_READY = YES for this bounded interface fixture.** This is not pricing-policy training or evidence of economic performance. The greedy checkpoint produces no accepted requests in this controlled fixture; the separate forced-action path verifies successful assignment and downstream transitions.

## Scope and real interfaces

Two independent deterministic runs cover **2026-03-16 00:00–02:00**, four half-hour slots each, with the terminal next-state snapshot at 02:00. Each run uses three vehicles, origins 0/1/2, cyclic destinations 0→1→2→0, and 36 controlled requests. The canonical operational state still covers all 142 grids, as its interface requires. Seed is 42. There is no full-day run.

`src/simulation/pricing_dqn_fixture.py` connects:

- Saved epoch-200 forecasts and regenerated destination popularity at exact timestamps.
- Verified pre-start μ/σ priors and the frozen operational-state producer.
- The saved 169-input routing checkpoint, masked nine-action probabilities and real 13D pricing-state builder.
- The saved standalone DQN checkpoint and `select_action(..., explore=False)` for greedy decisions.
- Existing weather/half-hour P_base/D_base resolution and positive behavioural-E sampler.
- Real `RequestState`, `dispatch_requests`, same-grid/neighbor eligibility, FCFS lowest-ID matching, configured EV energy consumption, and `Fleet.advance_mini_slot`.
- Assignment-time dispatch ledger, passenger commitment adapter, next-state builder and actual DQN replay buffer.

The fixture uses the configured `legacy_fcfs_lowest_id` path; it does not replace matching with a stub or silently enable contention. The existing request validator calls the behavioural calibration branch `historical_sensitivity`; that internal compatibility name denotes the selected positive-E threshold model here, not Record-029. No Eq31 branch is used.

## Controlled requests and initialization

Requests are synthetic integration inputs, **not sampled historical trips**. Each origin submits three requests at mini-slot zero: two with distance D_base and one with distance 0.5×D_base, all with 40-minute trip duration. Positive E is drawn from the unchanged verified calibration. Request IDs/source IDs and pickup/drop-off fields are fixture-local values required by the existing request validator; they are not historical TLC record identifiers.

P_base/D_base and weather are real existing artifact lookups. The assigned request's fare, distance conversion to kilometres, timing and acceptance audit are passed intact through the real interfaces. These controlled OD/time/distance combinations are for branch coverage, not geographic travel calibration.

All three vehicles start idle at 60 kWh. The preceding simulation slot is explicitly recorded as completed with no simulated dispatches; initial I is an explicit empty passenger-commitment set. Neither is a guessed missing historical value. The main fixture begins after historical-prior availability. No unavailable forecast/popularity/base input is fabricated.

## Actions, acceptance and reward

Primary path: checkpoint greedy evaluation, exploration disabled without altering the stored epsilon schedule or checkpoint. All 12 OD decisions chose **action 5, factor 1.10**. All 36 requests were rejected; reward is zero.

Forced-action path: **action 3, factor 1.00**. Requests at D_base have P_disp=P_max and are accepted; shorter-distance requests have a lower threshold and are rejected. Outcomes:

| Mode | Accepted | Assigned | Accepted unmatched | Rejected | Revenue USD |
|---|---:|---:|---:|---:|---:|
| Greedy | 0 | 0 | 0 | 36 | 0 |
| Forced 1.00 | 24 | 6 | 18 | 12 | 128.03439281400887 |

Below/equal/above-threshold behavior is also covered by the direct acceptance tests. Accepted requests alone are sent to dispatch. Matching can leave them UNSERVED; rejected requests never receive a vehicle. No vehicle is assigned twice while busy.

The ledger reward is independently reconciled against assigned request fares after every slot. Each OD replay transition receives only revenue attributable to the requests priced by its action. These contributions sum to the slot reward; the whole-slot reward is not duplicated across OD transitions. No charging/reposition costs or utility scores enter it. Monetary values retain the precision of mean-fare lookup values; displayed revenue is not rounded in artifacts.

## State timing, arrivals and fleet consistency

Each current state is constructed before any current-slot pricing/dispatch outcome. Routing probabilities are obtained from the published operational state, marked **PROVISIONAL_ROUTING_BASELINE**. Saved forecast availability follows the previously frozen contract; this fixture does not establish live forecast-weather provisioning.

After 15 real two-minute fleet advances, the slot ledger and operational estimates publish state for the next boundary. J_disp counts are checked against actual assignment records by origin. F_hat is never substituted. Incoming supply uses only still-active passenger commitments assigned before that boundary, with drop-offs in `(t,t+30min]`. Forty-minute trips cross a boundary, producing six nonzero incoming-count contributions in the forced path. Commitments are checked against actual BUSY vehicle destinations and remaining travel times. Arrivals at minute 40 and 100 become IDLE at their proper destinations.

Every mini-slot checks vehicle IDs/state validity and conservation: **3 vehicles remain 3**. No reposition or charging arrivals enter I. No vehicle/travel update is bypassed.

Each run stores **12 fresh replay transitions**, including three terminal OD transitions from its final slot. Across both runs: 24 transitions and 48 current/next vectors. Existing synthetic replay from the loaded checkpoint is replaced only in memory by an isolated empty integration buffer; saved files are untouched. Terminal Bellman tests return reward despite arbitrarily high next-Q values. Optimizer updates are skipped: replay remains below the unchanged 1,000-row production warmup.

## Outputs and validation

- `integration_trace.csv`: 24 OD decisions, fares, counts, states and replay progression.
- `state_vectors.csv`: 48 explicit current/next vectors, keyed by state ID.
- `acceptance_dispatch_trace.csv`: 72 requests, E/threshold/acceptance/assignment/reward.
- `reward_reconciliation.csv`: all eight slot reward reconciliations.
- `fleet_conservation.json`: 120 mini-slot conservation checks.
- `state_validation.json`: integration assertions and checkpoint protection.
- `integration_config.json`: exact window, modes, request generation and saved checkpoint fingerprints.

`run_fixture.py` executes these interfaces and refuses to overwrite completed results implicitly. Missing forecasts, routing, popularity, dispatch history, explicit incoming commitments, invalid probabilities/grids/actions/timestamps and missing/nonfinite base fares fail closed. The pricing-state constructor now explicitly rejects absent required source objects.

DQN and routing checkpoint hashes were unchanged. No CNN/grid/passenger-analysis/LinUCB/privacy/attack code or training was changed. The current routing model remains structurally valid, an integration baseline and **not the final experimental policy**. No DQN or routing optimizer update occurred in the integration runs.

Next step, not executed: the first short non-private hierarchical DQN episode in the real 142-grid environment. This fixture's success proves the tested integration path, not the completeness of every full-environment path or experimental policy quality.

Focused validation: **29 tests passed, 0 failed** with `python -B -m unittest tests.test_pricing_dqn_simulator_integration tests.test_pricing_dqn_contract tests.test_standalone_pricing_dqn -q`. The standalone unit tests exercise tiny optimizer checks independently; the two simulator-integration runs execute zero optimizer updates.
