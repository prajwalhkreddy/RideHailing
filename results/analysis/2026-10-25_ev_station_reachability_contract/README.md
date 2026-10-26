# Final EV post-movement station-reachability contract

**EV_STATION_REACHABILITY_CONTRACT_READY = YES**

## Frozen project constraint

`EV_POST_MOVEMENT_STATION_REACHABILITY` is a **PROJECT_PHYSICAL_FEASIBILITY_CONSTRAINT**, not manuscript-derived. For every proposed non-charging movement:

`E_after = E_current - E_movement >= min_station_route_energy(destination)`.

All values are kWh. Reserve uses the existing shortest paths and0.15 kWh/km. Exact equality passes, with no added margin; reserve is zero at a valid station. This requires reachability of **at least one** station, not every station. It is distinct from the unchanged15-kWh charging trigger (75-kWh battery ×20% SOC).

Passenger FCFS eligibility now rejects a vehicle whose projected dropoff energy is below reserve, then considers remaining eligible vehicles in the existing order. Acceptance is untouched. The callback is explicitly wired into the final production FCFS path; the legacy optional contention path is not silently reinterpreted. Voluntary reposition candidates failing reserve are excluded before the unchanged U1+U2−C_rep argmax, including STAY's actual zero energy. Canonical nine-action topology/state masks remain unchanged; the physical filter selects only reserve-feasible labels under those masks. Rejection counts describe candidate exclusions, not a redefinition of passenger acceptance.

An arrival assertion checks reserve after completed passenger/reposition travel. Charging keeps energy<=E_min triggering, unchanged U3=1−exp(−H_i_max/H_hat), H_i_max10 minutes, existing route-energy filtering and timed multihop navigation. No station, capacity, consumption coefficient, utility or emergency recovery mechanism changed. Impossible constructed states still fail closed.

## Vehicle299 regression

Documented residual1.7248694329320955 kWh at grid104 is below station reserve3.1819805153394634 kWh. The passenger eligibility test therefore rejects this proposal. The historic trip's exact original consumption was not persisted; the regression uses a synthetic decomposition yielding that observed residual, not fabricated historical pre-trip values. The preserved slot680 checkpoint was never repaired or resumed. A focused checkpoint test explicitly rejects it because it lacks the new contract marker.

## Validation

**28 focused tests passed;0 failed**, covering ample/equal/insufficient passenger reserve, safe/unsafe reposition candidates, zero station reserve, diagonal/multihop energy, charging equality, U3, no teleportation, nonnegative energy, impossible states and legacy-checkpoint rejection.

A clean seed42 March1 fixture completed **2 slots**, ending01:00, with **9,077 experiences**,5,000 unique vehicles, finite169D states,9D masks and mask-valid labels. Duplicate IDs0; stranded events0; negative energies0. Reserve-rejected vehicle/request candidate pairs **0**; unique requests encountering such rejection **0**; reposition candidates excluded **0**. Zero exclusions in this short, initially well-charged fixture are reported honestly; unit fixtures test the binding constraint. No pricing/routing training or federated updates occurred.

Fixture data: `data/processed/routing_experiences_reachability_short_validation/`; summaries/checkpoint manifest: `short_validation/`. These are isolated validation outputs and must not be copied into final training data.

## Superseded generation and clean namespace

The original680 slots/3,077,890 experiences remain **SUPERSEDED_PRE_REACHABILITY_RESERVE_GENERATION / PROVENANCE_ONLY / DO_NOT_USE_FOR_FINAL_ROUTING_TRAINING**. Checkpoint SHA256 remains `f57b74fabd43bc2bcaf16e06ce6dd213bc7be491a1fd7d0895ef3eb8b5bf41f2`; no old partition was written. Classification metadata is added beside the old data and in its manifest. The new rule can change earlier assignments and routing, so equivalence cannot be assumed.

Future final data/checkpoint: `data/processed/routing_experiences_mar01_mar15_2026_reachability/`. Future report: `results/analysis/2026-10-25_routing_generation_reachability/`. Final namespace is prepared without a checkpoint or experience partitions; **the720-slot generation has not launched**. The launcher defaults to this new namespace; clean starts at March1 00:00 and ends after March15 23:30. It retains factor1.00, real simulator request flow,5,000 profiles, all other frozen interfaces and eight-slot/day-boundary/safe-stop checkpointing. A marker blocks old-checkpoint mixing.

## Next task — commands, not executed

From the configured project root/environment, first clean unattended launch:

```sh
python -B scripts/generate_simulator_routing_experiences.py --checkpoint-every-slots 8 --stop-after-slot 720 --background --log results/analysis/2026-10-25_ev_station_reachability_contract/clean_generation.log
```

Later resume uses the same command with `--resume`; never point at the old slot680 checkpoint. Safe SIGTERM and log/PID behavior remain as documented in the execution optimization report. No final routing training has occurred. The downstream trainer's existing old input paths must be explicitly migrated and checked in the later training task; do not invoke it on provenance data.

Evidence: `reachability_contract.json`, `vehicle_299_regression.json`, `reachability_tests.json`, `clean_generation_config.json`, `focused_tests.log` and `short_validation/`.
