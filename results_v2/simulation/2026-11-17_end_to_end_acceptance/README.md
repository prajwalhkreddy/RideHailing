## Current result — explicit fallback acceptance completed

The original preflight stop below is preserved as historical evidence. The approved
versioned fallback now accounts for both previously unsupported requests without
expanding January support. Four real-data slots, deterministic repeat and resume
passed; no training occurred. See [fallback acceptance report](FALLBACK_ACCEPTANCE.md)
for results and the explicit retrospective calibration/forecast limitations.

# Real-data OD acceptance preflight — 17 November 2026

**BLOCKED_AT_OD_SUPPORT_PREFLIGHT. End-to-end acceptance has not passed.**

The selected development interval is March 12, 2026, 00:00–02:00 America/New_York (04:00–06:00 UTC), four consecutive 30-minute elapsed slots. The January-only feasibility artifact validates its internal support hash and contains 9,572 OD pairs.

## Request reconciliation

| Quantity | Requests |
|---|---:|
| Source observations | 4,215 |
| Eligible under existing replay rules | 4,137 |
| Ineligible under existing replay rules | 78 |
| Eligible and January-supported | 4,135 |
| Eligible but January-unseen | 2 |
| Eligible invalid geographic IDs | 0 |

Both unsupported requests occur in the 00:30 local slot: OD (32,70) at 00:31:08 and OD (89,122) at 00:35:30, one request each. Their grid IDs satisfy the current 0–141 geographic contract. `unsupported_requests.csv` preserves their source identifiers. `slot_request_reconciliation.csv` reconciles all four slots. Eligibility is the existing finite/nonnegative fare and distance, finite positive duration rule; no new cleaning or dropping policy was applied.

The actual UTC replay validator rejects the complete affected slot with `UNSUPPORTED_HISTORICAL_OD: 2 pairs; first=[(32, 70), (89, 122)]; research decision required`. Source-row conservation, geographic-ID validity, source-identity uniqueness and January support integrity assertions pass.

## Explicit stop and remaining decision

The requested unsupported-OD stop rule applies. No alternate interval was searched, no January support was expanded and no eligible request was silently excluded. An explicit methodology decision for geographically valid requests absent from January support is required before this interval can be replayed.

Simulation slots completed: **0**; simulation requests processed: **0**; optimizer updates: **0**. Pricing/acceptance/reward totals, fleet/charging/arrival invariants, runtime performance, deterministic repeat and checkpoint/resume are **not evaluated**, rather than zero-valued outcomes. Forecast construction and the remaining integrated preflight checks were not continued after this gate. No compatible forecast or full runtime readiness is claimed.

## Evidence and preservation

`validation.json` records selected-row content hash, source size/mtime, source metadata and calibration-contract hashes, January support hash, Git revision and pre-existing dirty state, intended seed 42 and UTC interval. Its selected-row digest is not a full multi-month dataset hash. `tests.txt` records bounded existing replay regressions; these do not substitute for real-data acceptance. Prior UTC boundary/resume evidence remains in `../2026-11-17_utc_od_runtime/` and was not rerun as a real-data acceptance claim.

Only the selected development interval was loaded. March17–31 records were not loaded or evaluated. No training, historical artifact changes, model changes or production-code edits were performed. Next task: resolve and document unsupported-OD behavior, then retry this same bounded interval under the approved contract.

## Bounded regression result

Seven existing replay tests ran in 4.402 seconds: **5 passed, 2 errored**. `test_forecast_volume_independence_and_no_lookahead` and `test_historical_replay_resume` use mock readers that reject the `utc_mode` keyword now passed by the runtime. These failures are recorded, not suppressed or treated as a passed suite. No code or test changes were made after the explicit OD stop gate. Before acceptance can pass, these mock/interface incompatibilities also require reconciliation. The actual selected-data support rejection and count assertions passed independently.
