# V2 implementation plan — conditional, no code executed

## 1. Freeze and version contracts

Approve the seven numerical and four architecture groups. Create separate V2 method/state/action/sampler/reward schemas with hashes; preserve V1 and Episode25. No exact continuation. P_offer=alphaP_base, ceiling and acceptance as section1 of latest source. No passenger-dependent preselection mask. Price bounds constrain available factors/operational validity; do not invent acceptance clamping.

## 2. Calibrate grouped sensitivities (future authorized work)

Use Jan1–Mar15 individual observations,1.5<=km<75, approved e orientation/references and validity. Count negative/zero/undefined/flagged/positive separately pergroup. Existing hourly WeatherCode joins permit48half-hour-of-day bins; confirm grouping and chronology rather than adopting illustrative morning/evening names. Fit truncated normal/gamma/lognormal plus justified candidates on the approved support. Validate tails and induced acceptance, not just AIC. No calibration onMarch16 development orMarch17–31 protected rows. Historical Record029 untouched.

Expected parameter artifact schema (specification only): schema_version, method_hash, P_base_USD, L_base_km, orientation, date_start/end_exclusive, weather_code/taxonomy_version, time_group_id/definition, timezone_semantics, N_total/valid/negative/zero/flagged, independent_dates, family, parameters with names/units, support_lower/upper and inclusivity, truncation normalization, denominator/sign rules, fit metrics/validation_period, inverse-tail diagnostics, fallback_group_id/reason, approval_status, random_seed_contract, source_fingerprints. Include a complete supported/unseen-group lookup contract. Refuse unresolved or unapproved parameters. No current artifact created.

## 3. Assemble state before slot

Reuse artifact_snapshots causal CNN forecasts, DispatchLedger previous completed outcomes, passenger_commitment/incoming and current routing probabilities. Add system supply from Fleet.vehicles at boundary; do not use static initialization as live supply. Distinguish idle count from driver/energy-eligible supply. Decide inclusion of passenger versus reposition/charging arrivals. Reuse timestamp/snapshot checks; retain available_at/observed_through<=slot_start. Mean dispatch is not automatically raw J_disp_previous or operational F_hat (rate per minute).

Build explicit normalized drop-off probability history from approved historical initialization plus completed simulated observations. Reuse aggregate_dropoffs/trailing_dropoff_average as counting/lagging infrastructure only. Destination popularity remains separate ordinal context. Existing historical popularity is loaded from saved parquet, not dynamically updated by simulated drop-offs; a new online probability producer is needed. Never use same-slot future outcomes as input.

## 4. Select and publish destination schedule

At slot start compute A_t once, before generating/handling individual passenger decisions; freeze schedule until next boundary. Decision count and output dimensions depend onA2. Factors must cover approved reachable/allowed destination keys, with fail-closed behavior for missing keys. No new independent distance/OD sampling. Reuse CNN-driven counts and EmpiricalODDistribution.sample_trip preserving OD/distance/duration. Apply stored destination (or origin-destination, if approved) alpha to each arriving request. Assign sensitivity from approved weather/time group; weather availability must be causal for runtime and group fallback explicit.

## 5. Passenger and downstream lifecycle

Compute offer alphaP_base, sample/assign e, calculate ceiling under approved sign/zero rule, compare offer<=ceiling. Log offer, group/family, e, ceiling and acceptance for audit, not as DQN state. Rejected: zero reward contribution, bypass dispatch, no assignment/commitment or successful-fare update; fleet/world time still advances normally. Accepted: preserve find_eligible_vehicle energy/reserve/driver price tests and FCFS matching; assignment creates commitments and physical movement. Accepted-unmatched remains distinct; existing0 revenue is proposed pending explicit allotment interpretation confirmation.

## 6. Accumulate and learn at slot boundary

Available ledger/request fields: requestID, origin/destination, offered fare, customer_accepted, status, assigned vehicle, timestamp. Aggregate offered/accepted/rejected/assigned/accepted-unmatched counts and gross assigned revenue; group by destination orOD as approved. DispatchLedger already totals assigned gross revenue byslot and dispatch counts byorigin. V1 currently sets all offered accepted; new rejection flags require logging, not reuse of that assumption. Arrival/completion is distinct from assignment-time revenue.

At end of slot, reconcile revenue=sum successful assigned offers; process movement/charging/operational updates; form next causal system state; write approved slot transition including schedule, aggregate reward, full outcome counters and next operational mask. Do not retain ActionableRequestLinker or silently create per-passenger DQN transitions under the same schedule. Rejection observations affect counters and aggregate reward even when0. Destination-factorized learning is a design choice, not automatically additive joint Q. No optimizer settings or update cadence inherited without temporal review.

## 7. Preserve routing and validate bounded shifts later

Physical Fleet.advance_time, passenger duration/distance/energy, timed charging and routing mission interfaces stay intact. OperationalGridState.complete_slot updates mu/sigma from assigned fares, F_hat from assignments and H_hat from charging waits. New prices/rejections therefore alter169D routing inputs, probabilities, utility decisions and future supply despite frozen routing weights. No automatic retraining.

After separate implementation authorization, test: schedule chosen before slot and immutable; no passenger-state leakage; offer/ceiling/acceptance exact boundaries; rejection dispatch bypass and0 contribution; accepted-unmatched distinction; slot reward reconciliation; replay temporal/terminal/empty-slot behavior; normalized causal drop-off vector; supply/arrivals; no duplicate assignment; fleet/energy/charging invariants; source-date guards and sampler fallback. Then a separately authorized bounded development run with fixed seeds can compare demand/assignment/revenue, routing input mu/sigma/F_hat/H_hat ranges, routing probability validity, reachable actions, fleet conservation and charging against saved baseline. UseMarch16 only as development if authorized; never openMarch17–31 now. Do not conclude model compatibility from shape alone.

No production changes, fits, simulations, checkpoint loading or training in this reconciliation.
