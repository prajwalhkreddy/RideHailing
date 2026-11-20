# Prospective March12 engineering acceptance with non-learned routing

## Routing contract

`NONLEARNED_PRIVATE_UTILITY_ROUTING_V1` is an opt-in research baseline. Physical routing still uses `OperationalRouting.decide`, including existing private fare/wait preferences, persisted charging-wait preference, utility safeguards, normalized repositioning cost, energy feasibility and station reachability. No routing weights, federated updates or differential privacy are used.

For the OD state, each currently idle, unqueued driver contributes a one-hot vector for its deterministic utility-maximizing next-hop action. Per-grid arithmetic frequencies form a normalized nine-action probability vector; this is an empirical fleet response, not learned probability estimation. Grids without eligible idle drivers explicitly use STAY with probability one. Invalid masked actions are rejected. Probability evaluation copies the routing interface to avoid changing live rejection counters. Physical dispatch, charging admission and movement remain unchanged.

## Information boundaries

Sensitivity reuses the separately frozen January–February calibration (5,457,435 observations), including rebuilt conditional support/fallbacks. January-only OD support, historical-average demand and destination popularity are retained. Driver-profile and fare-prior inputs use January1–January25 18:30 exclusive; source counts and mean reconcile to persisted metadata. Latest eligible timestamps are measured from bounded historical source reads. The January lower boundary excludes four pre-January rows in the cleaned source.

`information_contract.json` binds active artifacts and hashes. Non-learned routing explicitly has zero fitted observations; no fictional training dates or adjusted model metadata are used. The inherited learned routing checkpoint and its CNN-selection lineage are not loaded. Existing broad checkpoint provenance may fingerprint historical files as preservation dependencies; fingerprints do not make their values active forecast/routing inputs.

January average demand is labeled a baseline, not CNN output. Forecast metadata retains issuance/target/channel/grid validation and the assumed 120-minute weather delay. March12 pickups enter at scheduled events. Realized passenger-weather context remains retrospective environmental conditioning, not verified decision-time weather availability. Grouping, reference and action choices remain development-tuned design assumptions; this is not independently selected out-of-sample methodology.

## Acceptance scope

March12 00:00–02:00 America/New_York (04:00–06:00 UTC), four slots, 5,000 vehicles, seed42, untrained epsilon-greedy OD pricing, master EWMA/Bellman contracts, historical request replay and explicit valid-unseen-OD reference-price fallback. No optimizer updates or model training are authorized. Four-slot repeat and two-slot checkpoint continuation test deterministic equivalence. Prior acceptance and blocked-preflight evidence remain intact.

Results are recorded in `validation.json`, `slot_metrics.csv`, `request_reconciliation.csv`, `request_outcomes.csv` and focused test logs. Integration outcomes must not be interpreted as policy effectiveness.

## Completed validation

**PASS:** four primary slots, four deterministic repeat slots and two checkpoint-continuation slots. Forty-eight focused tests passed. No optimizer updates or training occurred. Fleet conservation and finite nonnegative energy passed throughout; normalized masked utility probabilities and UTC clock invariants were enforced. There were no charging events in this window; charging/energy reserve safety is supported by regression tests, not demonstrated charging activity.

Of 4,215 source rows, 4,137 were eligible (78 invalid-trip rows excluded by unchanged eligibility). There were 4,135 supported requests and two explicit fallback requests; 1,192 accepted, 2,945 rejected, 996 assigned and 196 accepted-unmatched. Supported reward was $21,889.80; fallback reward $44.7083968848; total successful-dispatch reward $21,934.5083968848. In `slot_metrics.csv`, `requests` denotes fallback requests and `total_requests` denotes all eligible requests.

Compared with prior engineering acceptance, acceptance decreased by eight, assignments by four and revenue by $320.0666666666. Calibration and routing-response representation both changed; this is neither a causal attribution nor a policy-performance result.

Repeat/resume fingerprints compare request/OD/fallback audits, fleet, passenger commitments, missions, operational state, sampler/learner RNG, replay and OD states. Temporary checkpoints were removed automatically after validation; historical checkpoints remain untouched. Checkpoint artifact hashes and the information contract reject incompatible inputs.

The first setup assertion exposed four pre-January rows in the raw cleaned source; the corrected bounded provenance query uses both endpoints and reconciles the persisted 2,898,376 fare observations. `blocker.json` is retained as superseded setup evidence, not current status. `validation.json` is authoritative for completion.

Remaining limitations: assumed weather availability, development-tuned design choices, retrospective realized weather context, untrained pricing and a non-learned routing baseline. No federated or private-learning claim is made. The next architectural milestone is a cutoff-valid learned-routing integration with explicitly causal forecast lineage; any regeneration or training requires a separate task.
