# Passenger-arrival boundary correction

**PASSENGER_ARRIVAL_BLOCKER_RESOLVED = YES**

## Root cause and correction

The original 01:00 invariant failure was a floating-countdown/absolute-timestamp precision mismatch (category D). Vehicles 918 and 4561 were scheduled to arrive exactly at March 1 01:00, but retained positive countdowns of approximately 9.65e-11 and 2.29e-12 seconds when the clock reached that boundary. Their destinations were 85 and 27. Arrival details are retained in `arrival_failure_diagnosis.json`.

`ProductionExperiment.advance_until` in `src/simulation/final_production.py` now derives passenger countdowns from unchanged absolute commitment timestamps and selects passenger completions using the next clock timestamp. Completion still uses the existing fleet arrival transition and commitment removal. A coincident float-timed movement exposed the same precision issue at 02:12 for vehicles 553 and 524; its focused regression and evidence are retained. No scheduled arrival timestamp or trip duration was changed.

The 30-minute main slots, 2-minute mini-slots, J_disp, utilities, labels, pricing and operational recurrences are unchanged. Arrivals <=t complete before state publication; only arrivals >t remain pending. I(g,t) still counts already-committed arrivals in (t,t+30 minutes]. Invariants remain fail-closed, including destination mismatch and due-event checks.

## Boundary validation

`boundary_fixture.csv` records A at t−1 second and B exactly at t completed at their destinations, with commitments cleared and no incoming contribution. C at t+2 minutes and D at t+30 minutes remain pending and contribute to incoming supply. A repeated advance does not complete arrivals twice. A one-nanosecond-before-boundary check ensures future arrivals are not advanced early. The affected real vehicles were verified IDLE at the correct destinations at 01:00, with zero idle wait and cleared commitments before routing.

## Bounded checkpoint continuation

The original valid 00:30 checkpoint was reused and preserved as `generation_checkpoint_before_boundary_fix.pkl` beside the active checkpoint. The original slot_0000 Parquet is byte-for-byte unchanged. Five additional slots completed through **March 1 03:00**, including four consecutive slots after the original failing 01:00 boundary. The intermediate correction committed through 02:00 before the coincident-event regression was diagnosed; continuation reused that valid checkpoint without repeating committed slots.

**22,439 new experiences** were appended, producing **27,009** across six slots. IDs are contiguous and unique; no overlap with the original 4,570 records exists. Every saved state is finite and 169D; every mask is length 9 and every label 0..8 is allowed by its mask. Fleet conservation is 5,000 unique vehicles. Published operational mu, sigma, F_hat and H_hat are finite, with no due passenger commitments remaining. Existing assignment/fleet invariants remained active.

Generation stopped at the explicit requested boundary. No full 720-slot generation, routing training, FedAvg or pricing optimizer updates ran. The optional `stop_after_slot` collector limit and CLI argument enforce bounded validation; the default full target remains 720.

## Focused tests and evidence

`python -B -m unittest tests.test_passenger_arrival_boundary`: **9 passed, 0 failed**. Tests cover before/on/after-boundary arrivals, inclusive incoming horizon, coincident float events, commitment clearing, fail-closed checks, fleet conservation, repeated boundaries, checkpoint restoration and append-once integrity.

- `arrival_failure_diagnosis.json`: original arrivals and diagnosed mechanism.
- `precision_followup_diagnosis.json`: coincident-event reproduction.
- `boundary_fixture.csv`: four temporal boundary cases.
- `resume_boundary_observations.json`: observed publication boundaries and affected vehicles.
- `resume_validation.json`: bounded continuation and integration results.
- `checkpoint_integrity.json`: checkpoint/slot hashes and experience counts.

The next authorized task may resume from the latest **03:00 checkpoint**, not March 1 00:00. Full collection and any subsequent training remain outside this task.
