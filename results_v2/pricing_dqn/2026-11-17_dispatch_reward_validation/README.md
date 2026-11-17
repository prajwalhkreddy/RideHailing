# Successful-dispatch reward validation — 17 November 2026

Status: PASS. Methodology: SUCCESSFUL_DISPATCH_REWARD_V1; reward-only destination-context baseline.

Focused tests: 12 passed, 0 failures/errors. Bounded historical regression: 64 passed, 0 failures/errors.
The broader historical 181-test suite was not rerun; these counts are separate.

The deterministic fixture runs one bounded slot in each mode with two vehicles and four requests:
assigned, accepted-unmatched and rejected outcomes are exercised. No optimizer updates occur.
Dispatch, acceptance, RNG state, fleet, ledger, operational state and next-state vectors agree.
Only assigned fares enter the corrected replay. Historical accepted-fare replay remains unchanged.

`validation.json` records exact input hashes, Git/dirty provenance, configuration, seed, references and metric definitions.
`test_results.txt` records the focused tests. `regression_results.txt` and `preservation_and_regression.json`
record the bounded regression and historical-file preservation checks.

Run instructions and checkpoint limitations: [output contract](../README.md).
Existing results/ and model checkpoints were not modified. Existing user changes were preserved.
Full master compliance and new full-runtime resume are not claimed. No training launch is part of this batch.

Next single task: version the feasible origin–destination state/action/replay identity contract and its tests,
while retaining this reward definition and the historical artifacts.
