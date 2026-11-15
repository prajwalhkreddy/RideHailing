# V2 runtime sensitivity integration and validation

## Current V2 preflight reconciliation — 14 November 2026

V2 TRAINING STATUS: **V2_TRAINING_BLOCKED_FULL_DAY_FIXTURE_AND_EXECUTION_HARNESS_NOT_PREPARED**; **TRAINING_NOT_YET_STARTED**. Historical test-contract conflicts are resolved with test/fixture-only changes. Focused57, exact broader123 and expanded applicable239 tests pass with zero failures/errors/skips. No production behavior or any of the six recorded V2 hashes changed. Contract/support/source hashes and48 March16 snapshots pass recheck. Unrestricted historical discovery is not certified safe and was not run.

Remaining blocker: no frozen full-day V2 request/epsilon/fleet fixture, reproducible full-day baselines or automated fresh25-episode harness/effective run config yet exists. Prepare and validate those prerequisites next; no training or baseline recomputation was authorized in this reconciliation task. V1 remains historical; V2 runtime remains INTEGRATED_VALIDATED_NOT_TRAINED. March17–31 remains untouched. See [reconciliation report](../../training/pricing_v2_staged_training_001/README.md).


**INTEGRATED_VALIDATED_NOT_TRAINED — READY_FOR_V2_TRAINING**, meaning technically ready for a separately authorized fresh run. No training is launched. Default configuration remains validation-only; the V2 provider rejects training unless explicitly authorized and the matching validated runtime-status artifact exists.

## Contract and provenance

The immutable reviewed sensitivity contract and every declared source hash were checked before implementation; the canonical population SHA256 matched. The reviewed contract remains REVIEWED_NOT_INTEGRATED as historical evidence; the new runtime_status.json records integration without overwriting it. All5,779,213 candidate epsilon values are loaded from the persisted canonical Parquet, with status, finite/nonnegative, denominator and Jan1–Mar15 date assertions. Actual zero count=0. An unexpected future zero fails closed with ZERO_EPSILON_RUNTIME_CONTRACT_CONFLICT because the existing threshold divides by epsilon; no epsilon floor is invented.

P_base=22.354198442390455 USD; L_base=4.616983790655043 km; r_P=(P-P_base)/P_base; r_L=(L-L_base)/L_base; epsilon=r_L/r_P. Runtime P_raw=P_base+(P_base/epsilon)*r_L is the algebraic inverse. Request distance arrives in km; sensitivity is dimensionless; resulting threshold and offers are USD. The existing effective-threshold rule max(0.85*P_base,P_raw) and seven factors0.85,0.90,0.95,1,1.05,1.10,1.15 remain the pricing formulation for this requested integration. The maximum offer is1.15*P_base. Historical reference/architecture debates are not silently generalized beyond this explicit task.

The historical5% denominator rule is enforced in pool eligibility, not reapplied as a price constraint to new requests. No abs conversion, epsilon clipping, parametric generation, upper-tail restriction or mean replacement occurs. The raw preference can be negative or large for small positive epsilon; the approved effective floor is applied to the **threshold**, not to epsilon or candidate prices. All fixture thresholds are finite. This does not prove independent sampling is a real-world willingness-to-pay model.

## Architecture and compatibility

- src/pricing/passenger_sensitive_v1.py is unchanged: existing positive provider/floor semantics and reference constants remain intact.
- src/pricing/passenger_sensitive_v2.py adds the validated empirical provider, contract-specific pricing adapter, version resolver and sampler continuation state.
- The existing PassengerSensitiveExperiment selects pricing through explicit passenger_sensitivity_version. Omission resolves to v1; a V2 provider without explicit v2 selection is rejected. config/passenger_sensitivity_v2_validation.json explicitly selects v2 and pins the reviewed contract hash.
- The request loop draws once, computes one threshold/mask, and reuses epsilon across all seven offers. Dispatch selection, fleet movement, charging, routing and reward equations are reused unchanged. RequestState adds V2 reference fields and a V2 validation branch. Existing v1-prefixed audit slots are reused as storage for epsilon/raw/effective thresholds; customer_model explicitly distinguishes v2, and a zero minimum metadata value means **no added epsilon floor**.
- DQN architecture, action indices, loss and update cadence are unchanged. Checkpoint serialization adds a distinct V2 schema only when a V2 provider is attached. It saves methodology version, reviewed-contract hash, support hash and sampler RNG state. V1 loader calls/default schema remain V1. Loading V2 requires an explicit validated provider; V1 checkpoints cannot load as V2, including zero-update checkpoints. Existing model/checkpoint/replay artifacts are untouched.

The provider uses the caller-owned NumPy Generator and integer row-index sampling with replacement, retaining duplicate frequencies. The projected epsilon array is loaded once per provider and reused across episodes; no raw taxi population is loaded per request or episode for sensitivity sampling. Existing request generation still uses its unchanged January empirical trip source. No duplicate large sensitivity file was created; the exact 46.2MB value array resides in memory and the existing ignored canonical Parquet remains the persistence source. Startup hash validation is intentionally not bypassed.

Checkpoint testing covers sampler/DQN continuation state, not a new mid-slot fleet-restoration facility. Any complete simulator continuation retains the existing environment-state requirements. Old Episode25 was neither loaded nor resumed; its optional out-of-distribution evaluation was skipped.

## Runtime distribution reproduction

One million draws with seed42, all exact members of the canonical support, all nonnegative. Mean1.806478 versus1.807321 (-0.0466%); median1.153928 versus1.154356 (-0.0371%); population SD1.975167 versus1.990089 (-0.7498%). P95 error-0.1073%; P99 error+0.1367%; CDF distance0.000576833. Full P05/P25/P75 results are in runtime_distribution_reproduction.csv. SD is more tail-sensitive than the median; exact equality is not demanded. A predeclared loose CDF sanity bound0.003 was passed. No repeated seed search was used to improve this check.

## Request fixture and controlled comparison

Development clock: March16,2026,00:00–00:30. Fixture: first64 chronological requests generated by the existing January empirical/CNN request pipeline for that slot. This is intentionally bounded and not a full-demand performance experiment. Static rows preserve ID, timestamp, OD, distance, sampled epsilon, raw/effective thresholds, mask and feasible count. One-draw-per-request is verified by independently replaying the sampler sequence; the simulator audit matches the static sequence exactly for each baseline.

The V1-versus-V2 sensitivity comparison holds **V2 references, actions, distances and threshold formula fixed**, substituting only the V1 versus V2 empirical epsilon source. It is not reported as a replay of historical V1 performance. On64 requests, forced fraction changes from73.4375% to64.0625%, choice fraction26.5625% to35.9375%, no-feasible fraction remains0%, and12.5% of masks change. Feasibility by factor and threshold moments are in the comparison CSV. A small fixture does not establish V2 superiority. V2 raw-threshold mean is negative because one very small sampled positive epsilon produces a large negative raw value; the effective floor keeps offered actions valid, without modifying the sample.

## Baselines and smoke execution

Each policy starts a fresh seed42,5,000-driver fleet and the same64 requests/epsilon sequence; one terminal30-minute slot per policy, exploration off and optimizer disabled. Neutral chooses1.00 when feasible, otherwise the nearest feasible configured factor. These policies exercise actual matching and movement; assignments/revenue are not estimated from masks.

| Policy | Requests | Assigned | Unmatched | Revenue USD | Feasibility violations |
|---|---:|---:|---:|---:|---:|
| Highest feasible |64|64|0|1330.074807|0|
| Lowest feasible |64|64|0|1216.068395|0|
| Neutral |64|64|0|1279.777861|0|

Fleet conservation passes at5,000. Assignment/request accounting and assignment-time revenue reconcile. Each run produces64 terminal-linked replay transitions in fresh in-memory replay and0 optimizer updates; pending transition is closed.57 trips complete within the slot; remaining assignments legitimately continue beyond the terminal horizon. No repeated assignment was observed. The nine routing-action counts are saved per policy, operational updates finish, and built-in finite/fleet validations pass.

Charging decisions/events are0 in this bounded fixture. Timed progression and fleet checks execute, but active queue/charging transitions are **not exercised**; this is a coverage limitation, not evidence of a stress test. The first implementation smoke attempt stopped at a legacy-only customer-model validator; the narrow V2 request validation branch resolved that integration boundary. No dispatch algorithm was changed.

## Tests and files

57 focused tests pass: V2 contract/source hashes and population, exact support membership, deterministic/different seeds, replacement, no floor, RNG continuation, V1 default compatibility, V2 selection, inverse formula/units, zero rejection, feasible masks, protected dates, checkpoint version separation and continuation, plus existing V1 and passenger-trip tests. Static/smoke checks additionally cover one draw per request, exact action reuse, reconciliation and fleet consistency. Test checkpoints live only in temporary directories. Existing V1 unit tests exercise tiny synthetic optimizer updates; the development smoke runs perform zero optimizer updates and no training experiment is launched.

runtime_contract_verification.json and runtime_status.json record the new status, code hashes, source hash, config and results. The requested distribution, request-level, sensitivity-comparison and baseline CSVs, smoke_test_summary.json, test_results.txt and verification.json are included. validate_runtime.py reproduces the bounded validation; it does not start training. No registry or historical V1 outputs changed. March17–31 was not accessed. Demand/routing models were not retrained.

## Final answers

The reviewed sampling contract is integrated exactly and reproducibly. Canonical distribution reproduction passes; no observed zero-epsilon conflict exists; units are consistent; thresholds/masks are finite and valid. V1 defaults and tests remain unchanged in behavior. The measured feasibility difference is diagnostic only. All three bounded baselines and smoke accounting checks pass, subject to the stated zero-event charging coverage. The runtime is ready for a separately authorized fresh V2 training run, **not** for resuming V1 Episode25 or claiming trained V2 performance. Training remains disabled in this task's config.

## Fresh training launch gate — 14 November 2026

The subsequent authorized fresh run is blocked before launch by broader test-contract conflicts:57 focused tests pass;111 related tests report2 failures and7 errors. Runtime source hashes match. No V2 training checkpoint or full-day benchmark exists. See [launch-gate report](../../training/pricing_v2_staged_training_001/README.md) for exact evidence and reconciliation required. The earlier smoke verdict does not override this gate. March17–31 remains untouched.
