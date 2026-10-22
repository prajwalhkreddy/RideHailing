# Current status: bounded generation resumed through March 1 03:00

The passenger-arrival precision blocker is resolved. Six of 720 slots are committed, with 27,009 experiences. The original first slot is unchanged. Generation is paused at the requested 03:00 boundary; no routing training or FedAvg has run. Resume from the latest checkpoint, not from the beginning. See [boundary correction and validation](../2026-10-21_passenger_arrival_boundary_fix/README.md).

The original blocked-attempt report below is retained as historical evidence; its counts and checkpoint time describe that earlier attempt only.

---

# Simulator-derived routing generation: blocked

**SIMULATOR_ROUTING_POLICY_READY = NO**

Generation was stopped at a genuine existing runner invariant failure, as required by the task. The committed dataset contains only the first half-hour of the requested March 1–15 period. It is not a completed final training dataset.

## Exact blocker

During the second slot (March 1 00:30–01:00), the runner raised:

`ValueError: Unprocessed passenger arrival.`

Location: `src/simulation/final_production.py`, `ProductionExperiment._state_sources`, when checking passenger commitments while publishing the 01:00 next pricing state. The frozen passenger-arrival/timing logic was not modified or bypassed. Diagnosing or repairing that invariant is a separate prerequisite before resumption.

## Valid completed work

- Committed slots: **1 / 720**, March 1 00:00–00:30.
- Committed real requests: **3,494**; successful assignments: **494**.
- Experiences: **4,570**, all REPOSITION; EV_CHARGING_NEXT_HOP: **0**.
- Active driver participants: **4,570**; zero-experience drivers: **430**. Each active driver has one committed experience (minimum/median/mean/maximum all 1).
- Labels 0..8: **[3505, 74, 113, 289, 114, 296, 15, 148, 16]**.
- Partial train/validation counts: **4,570 / 0**. Planned chronological split remains March 1–12 / March 13–15.
- No routing training or FedAvg rounds ran. No new routing checkpoint exists. Effectiveness/collapse is not assessable; the old provisional checkpoint remains unchanged and is not superseded.

The second attempted slot is uncommitted and contributes no saved experiences or metrics. Request/assignment totals above refer only to the committed slot, not the incomplete attempt.

## Resume checkpoint and collection contract

Large data: `data/processed/routing_experiences_mar01_mar15_2026/slot_0000.parquet`.

Resume state: `data/processed/routing_experiences_mar01_mar15_2026/generation_checkpoint.pkl`, at **March 1 00:30**. It preserves fleet, charging infrastructure, operational state, prior dispatch history, active passenger commitments, charging missions, identifiers and RNG states. Do not discard the completed slot or restart March 1 unnecessarily. Load only this locally generated trusted checkpoint.

The opt-in routing-data-generation mode uses action 3 / factor 1.00, the real request generator, existing behavioural-E acceptance and FCFS matching. No pricing replay insertion or optimizer updates occur. The existing provisional routing model is frozen. Collection records per-driver actual utility labels and charging continuation next hops, with finite 169D states and separate nine-action masks. Cached published state/encoding results are reused only within the identical causal timestamp. No equations or operational coefficients were changed.

The collection-only terminal path avoids consuming March-16 forecast inputs after the last March-15 slot. Experience timestamps identify the causal source slot; `event_offset_minutes` records within-slot timing, including end-boundary decisions. This is collection infrastructure, not a change to the frozen temporal protocol.

## Validation and prepared training

Committed Parquet checks passed: exact 169D states, nine-element masks, finite values, valid integer labels under masks, unique experience IDs and March-1-only timestamps. Full-run validation failed at the passenger-arrival invariant above. No broad suite or training job ran.

The prepared trainer preserves one driver per client and the existing fixed configuration: five plain sample-weighted FedAvg rounds, Adam 0.001, batch 32, one local epoch, seed42, masked cross-entropy, no class rebalancing or early stopping. It refuses to train until all 720 slots are committed. Zero-sample exclusion and chronological March13–15 evaluation are explicit. No metric in the report represents a trained model; empty history/confusion files and NOT_RUN metadata intentionally indicate that stage was not reached.

The remaining prerequisite is resolution of the runner's passenger-arrival invariant. No CNN, acceptance model, pricing architecture, H_i_max, frozen coefficients, grid geometry, March16 integration artifact or final-evaluation data was changed.
