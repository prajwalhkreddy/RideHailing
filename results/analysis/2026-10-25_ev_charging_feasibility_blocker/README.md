# EV charging-feasibility blocker — methodology decision required

**EV_CHARGING_FEASIBILITY_BLOCKER_RESOLVED = NO**  
**PROJECT_CONFIG_DECISION_REQUIRED = YES**

## Preserved checkpoint and reproduction

The unchanged atomic checkpoint is March15 04:00, **680/720 slots**, **3,077,890 experiences**,5,000 vehicles. SHA256 `f57b74fabd43bc2bcaf16e06ce6dd213bc7be491a1fd7d0895ef3eb8b5bf41f2` matches the supplied reference before and after diagnosis. No committed partition0..679 was modified or scanned. No new partition/checkpoint was written. Existing uncommitted files were not promoted.

An in-memory restore reproduced the exact exception during the first resumed slot, at **March15 04:30**, in `ProductionExperiment.route_idle` → `OperationalRouting.decide` (operational_interface.py). Vehicle/driver **299** is IDLE at **grid104**, energy **1.7248694329320955 kWh**. Battery capacity75 kWh; active E_min is **15 kWh** (20% SOC), and energy is strictly below it. The separate energy configuration reference minimum7.5 kWh is not the active trigger. H_i_max remains10 minutes.

## Cause and immediately preceding transition

Primary classification **E: a passenger assignment was permitted despite leaving insufficient energy to reach charging afterward**. At the checkpoint this vehicle was already BUSY at grid74, committed to grid104, with energy already deducted. Assignment: **03:55:05**; scheduled/observed completion: **04:26:17** (31.2 minutes). It then waited idle until04:30 without a further energy-consuming action. The bad reachability state therefore predates this checkpoint, rather than being caused by the arrival fix.

The exact prior passenger distance, consumption and pre-assignment energy are not recoverable from this checkpoint: the commitment contains timestamps/destination, while the ledger retains aggregate counts/revenue only. Those fields are explicitly null in `offending_ev_trace.json`. Under the executed dispatch eligibility rule, pre-assignment energy exceeded15 kWh, implying consumption greater than13.275130567067905 kWh; this is a bound, not an observed exact trip consumption. No earlier committed period was regenerated to invent missing provenance.

## Station feasibility

All **15 station identities** were considered. None is reachable with current energy. Nearest: station **0**, grid **37**, route `104>89>74>62>48>37`, distance **21213.203435596424 m**, required energy **3.181980515339 kWh**, residual **-1.457111082407 kWh**. `station_feasibility.csv` records every candidate, path, distance, energy, residual and rejection reason. Conversion is metres/1000 ×0.15 kWh/km. The topology supplies routes; available energy is insufficient. No reachable candidate was incorrectly filtered in this reproduction.

## Existing contract versus missing decision

- Passenger assignment (`find_eligible_vehicle`) requires IDLE, energy above the charging trigger and enough energy for the passenger trip. Deduction rejects negative-energy trips. It does not reserve energy to reach a station after dropoff.
- Reposition selection checks the selected edge's energy, not residual charging reachability.
- Charging selection checks total shortest-path energy; continuation checks each actual timed hop. It refuses impossible travel and does not teleport.

The inspected active paths and directly affected tests contain no already-frozen post-movement charging-reserve invariant to repair. Adding one changes admissible assignments/routing decisions. Therefore **no production code or frozen values were changed**.

The project must decide a station-reachability/reserve criterion for passenger assignments and discretionary repositioning (including any margin and interaction with the charging trigger), plus the recovery policy for already-stranded committed states. For example, a prospective post-trip energy requirement based on station-route energy would alter dispatch eligibility and needs explicit approval; it is not adopted here. Because vehicle299 is already stranded in slot680's saved state, a prospective guard alone cannot make this exact checkpoint feasible. Any earlier regeneration or recovery mechanism also requires explicit authorization; neither was performed.

## Validation and outcome

Exact fail-closed failure reproduced; all candidate energy conversions and checkpoint hash verified. Preserved fleet count is5,000; no teleportation or negative-energy workaround occurred. No new experiences were persisted, so no duplicates were introduced. No correction/bounded-success resume or regression suite was run after the methodology-stop gate. Generation remains at680 slots with40 remaining. No model training or further generation was launched.

Evidence: `failure_diagnosis.json`, `offending_ev_trace.json`, `station_feasibility.csv`, `energy_invariant_validation.json`, `resume_validation.json`.
