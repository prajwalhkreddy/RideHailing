# Valid unseen OD reference-price acceptance

## Contract and scope

`VALID_UNSEEN_OD_REFERENCE_PRICE_V1` is an explicit, opt-in **provisional project research policy**, not a master-specified or optimized policy. Geographically valid requests absent from January support retain their original identities and receive factor **1.0 × common P_base**, followed by the existing passenger inequality and dispatch mechanics. Invalid IDs remain hard failures. Without this option, unseen OD requests still reject.

January support remains 9,572 OD pairs with its original fingerprint. Fallback requests do not create supported states, learned actions or replay transitions. Successful fallback assignments affect physical fleet/operational state normally and contribute separately to system revenue. Supported DQN reward excludes them. Rejected and accepted-unmatched requests contribute zero revenue.

Historical V3's action vocabulary does not contain exactly 1.0. A separate reference-request validator validates the approved fallback price and acceptance equation, then invokes unchanged base geometry/lifecycle validation. The V3 validator and action set are unchanged.

## Primary real-data execution

March12 00:00–02:00 America/New_York, corresponding to 04:00–06:00 UTC: four elapsed 30-minute slots and 120-second mini-slots; configured 5,000-vehicle fleet; seed42; actual historical requests and weighted binned sensitivity. No optimizer or routing updates.

- Source observations: **4,215**; eligible: **4,137**; existing-rule ineligible: **78**.
- Supported requests: **4,135**; fallback: **2**; invalid eligible geographic IDs: **0**.
- Accepted: **1,200**; rejected: **2,937**; assigned: **1,000**; accepted-unmatched: **200**.
- Supported reward: **$22,209.8666666667**.
- Fallback revenue: **$44.70839688478091**.
- Total system revenue: **$22,254.5750635514**; reconciliation passes floating-point tolerance.

Both fallback requests, (32,70) and (89,122), were accepted and successfully assigned at **$22.354198442390455** each. Their sampled epsilon, raw acceptance ceiling, timestamps and source IDs are in `fallback_request_outcomes.csv`. No support expansion or request removal occurred.

The primary four-slot execution took **166.797 seconds**, excluding initialization and repeat/resume. Runtime enforces valid fleet accounting, UTC event progression and passenger commitment/arrival agreement; explicit assertions check finite nonnegative energy, finite pricing states and exact acceptance inequality. Forecast-volume independence, pre-realization action ordering, DST charging/repositioning and invalid-input behavior are also covered by bounded tests. This ordinary-day interval alone is not a DST experiment or an exhaustive charging stress test.

## Forecast and frozen-component provenance

`JANUARY_HISTORICAL_AVERAGE_DEMAND_V1` uses each grid's January arithmetic mean for the local half-hour. All 31×48×142 January demand records reconcile. Predictions remain nonnegative fractional counts and do not derive from realized March12 requests. Popularity likewise uses January totals. The baseline has its own protocol identity, source/artifact hashes, cutoff and availability metadata; its predictions are checked against the saved January mean artifact. It is **not a trained CNN**, and does not establish final CNN compliance. Weather metadata retains the explicit 120-minute assumed availability protocol; oracle identities, changed artifacts and future availability are rejected.

Frozen routing uses `global_after_slot_528.keras`, whose training progress records source slot527 at March11 23:30 and availability at slot528/March12 00:00. It remains fixed throughout this check; this is not online federated learning. The later final-March12 snapshot was not used.

**Research limitation:** the required frozen weighted calibration uses Jan1–Mar15, and passenger weather retains the existing retrospective grouping semantics. Therefore this is not a fully prospective March12 model evaluation. No protected March17–31 data were loaded. Forecast and request event ordering pass their checks; global absence of calibration look-ahead is not claimed. Weather publication/vintage availability remains assumed rather than verified.

## Regression and resume evidence

The two failed regression readers were stale test doubles. They now accept `utc_mode=False` and explicitly reject/assert against unexpected UTC use in legacy fixtures; no assertions were removed.

`fallback_tests_fixed.txt`: **16 passed** (fallback, replay and UTC/DST).
`fallback_additional_tests.txt`: **12 passed** (baseline guard, fallback and historical OD), including two repeated fallback tests. Earlier failed test and interrupted initial execution logs remain as development evidence.

Schema5 records the fallback policy explicitly and requires a matching loader request. January support identity remains unchanged. Source fingerprints reject incompatible implementations. Fallback reconciliation is checked separately from supported replay reward.

**Repeat/resume passed.** All four fresh-repeat slot hashes match the primary execution; resuming from the slot-two checkpoint matches uninterrupted slots three and four. Comparison covers request/action/acceptance/assignment audit, supported replay, fallback revenue, fleet, passenger commitments, missions, operational state, pricing states, and learner/sensitivity RNG state. The temporary 146,156,797-byte checkpoint was removed; only concise checkpoint metadata remains. No new trained model is retained. See `fallback_validation.json`.

## Files and next task

`fallback_contract.json`, `fallback_run_config.json`, `fallback_slot_metrics.csv`, `fallback_request_outcomes.csv`, `fallback_checkpoint_metadata.json`, `january_historical_average.csv`, and test/log files supplement the preserved original preflight evidence. `scripts/validate_od_fallback_acceptance.py` reproduces this bounded check. No historical results or models are overwritten; the resume checkpoint is temporary.

Next single task: define a prospective calibration/information cutoff contract for a later chronological acceptance interval before any training promotion. This check does not authorize model training or resolve weather-vintage assumptions.
