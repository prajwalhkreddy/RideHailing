# Driver Minimum-Price Eligibility Fix

**DRIVER_PRICE_ELIGIBILITY_FIX_READY = YES**

## Implementation

`src/dispatch/dispatch.py::find_eligible_vehicle` now applies `request.offered_fare >= driver_minimum_prices[vehicle.vehicle_id]` before candidate selection. Equality is eligible. `src/simulation/final_production.py::run_slot` always supplies the validated persisted profile `price_preference` series. There is no runtime minimum-price fallback. Missing keys and non-finite/negative minima fail closed. Generic legacy callers without a mapping retain compatibility; the final production path explicitly supplies it.

Existing availability, local/direct-neighbor search, energy and station-reserve checks retain their order. The additional price test follows those feasibility checks and precedes selection. Same-grid priority and lowest-ID ordering within each pool are unchanged. A failed candidate remains idle, consumes no trip energy and cannot create a passenger commitment. Routing U1 is unchanged and does not substitute for the gate.

## Outcomes and counters

Passenger acceptance is unchanged. An accepted request without any eligible driver retains the existing immediate UNSERVED/accepted-unmatched behavior; no waiting queue or deadline redesign is introduced. Generated = accepted + passenger-rejected and accepted = assigned + unmatched remain the existing production identities.

Future slot reports include:

- `price_ineligible_candidate_count`: evaluated local candidates that pass prior availability/energy/reserve checks but fail price.
- `requests_with_any_price_ineligible_candidate`: distinct accepted requests with such an event, including requests subsequently assigned to another driver.
- `accepted_requests_unmatched_due_to_no_price_eligible_driver`: unmatched requests with at least one otherwise feasible candidate blocked solely by price and no selected driver.

These are DRIVER_PRICE_INELIGIBLE observer events, not passenger rejections. Candidate counts cover the existing evaluated search pools; neighbors are not searched when a same-grid eligible driver exists. No per-request console logging or reporting-system redesign was added. Counters appear in existing slot reports; final long-run persistence remains a later task.

## Focused validation

**20 tests passed, zero failed**: 12 new gate tests and 8 existing dispatch tests. Coverage includes above/equal/below price, FCFS fallback, all candidates failing, unchanged passenger acceptance, unmatched accounting, no blocked-driver energy/trip mutation, fleet conservation, station feasibility and equality, neighbor fallback, invalid/missing minima, and production-call wiring. Production wiring is checked structurally; no full runner episode was launched.

Five representative saved March16 violations were checked using their exact offered fares, driver minima and grids in small isolated fleets. Each original driver is now blocked; a later driver with minimum equal to fare is selected when present. Trip duration/distance are synthetic fixture values, so these are targeted regression cases, not predictions of corrected full-fixture outcomes. The previous 917/1801 violations remain historical evidence and were not recomputed.

## Unresolved contract and downstream status

Passenger elasticity orientation, sign/absolute treatment, sampling support and P_max remain **SOURCE_CONTRACT_UNRESOLVED** and unchanged. Existing routing experiences, central/FedAvg models and pricing checkpoints are retained as pre-correction provenance.

Wait for passenger-contract resolution. Then implement its correction if needed, validate passenger and driver behavior together, add final diagnostic persistence, regenerate March1–15 routing experiences once and retrain downstream models. None of those actions occurred here. No March17–31 data was accessed; no privacy or DQN protocol changes were made.

## Files

- `driver_price_gate_validation.json`: completion checks and counter definitions.
- `focused_test_results.json`: focused command and result.
- `downstream_regeneration_status.json`: unchanged-artifact status and prerequisites.
- Implementation: `src/dispatch/dispatch.py`, `src/simulation/final_production.py`.
- Tests: `tests/test_driver_price_gate.py`.
