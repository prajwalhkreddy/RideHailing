# Bounded prospective online-routing experiment — 17 November 2026

**Status: BLOCKED in the first slot; 0 of 4 slots completed.** The mandated safety stop was observed. Control, repeat and checkpoint/resume runs were not launched. No local gradients, federation updates or pricing optimizer updates occurred.

## Configuration and preflight

March 12, 2026, 00:00–02:00 America/New_York (04:00–06:00 UTC), four 30-minute elapsed slots, 120-second mini-slots, 5,000 vehicles: 500 EVs and 4,500 non-EVs. Seed 42 and the existing fresh 169→64→32→9 routing initialization were verified. Local Adam uses learning rate 0.001, batch capacity 32, one epoch and persistent moments; local memory capacity is 1,000. Existing local training selects the latest available minibatch. Equal participating-client FedAvg is explicitly NONPRIVATE.

The existing information manifest passed: January OD support, January–February weighted sensitivity, January historical-average forecast and January driver/prior provenance. Historical learned routing weights were not loaded. Initial global weights SHA-256: `90e6782df84c2e4c61b4597c64d22ed24325ddb14d39be5532bec04b232b11e0`. Updates were enabled only for routing; pricing retained its existing seeded epsilon-greedy configuration with zero optimizer updates. No new hyperparameters were selected.

Forecast weather remains assumption-based 120-minute persistence. Realized passenger weather is retrospective environmental conditioning, not a verified operational availability claim. Inherited architectural/hyperparameter choices retain the documented March-development exposure; this is not independent model-selection validation. March17–31 was not accessed.

## Runtime blocker

`src/simulation/final_production.py:206`, `ProductionExperiment.advance_until`, raised:

```
ValueError: Post-movement station reachability violated.
```

The post-arrival guard compares every non-charging arrival's battery energy with the charging-station reserve, without checking `is_ev`. Explicit non-EVs intentionally have zero battery energy, and dispatch/energy consumption already bypass their battery requirements. A new isolated arrival regression confirms that a non-EV with zero energy arriving where the reserve is 1 kWh is incorrectly rejected. An EV with insufficient reserve is correctly rejected.

The original traceback did not preserve the failing vehicle identity/type. Thus the exact real-run vehicle cannot be independently attributed from saved evidence; the missing non-EV exemption is directly demonstrated at the same failing guard. No real-data rerun was performed to obtain additional diagnostics. Production behavior and safety guards were not changed.

## Results and validation

| Item | Result |
|---|---|
| Preflight / initialized composition | Passed; 500 EV + 4,500 non-EV |
| Completed slots | 0 / 4 |
| Genuine local optimizer updates | 0; failure preceded slot-end learning |
| Federation rounds / committed replay transitions | 0 / 0 |
| Pricing optimizer updates | 0 |
| Control / deterministic repeat / resume | Not run following safety stop |
| Completed-slot request, reward, movement and charging metrics | Unavailable; not reported as zero |
| Bounded existing regressions | 40 passed in 56.245 seconds |
| New arrival regressions | 1 passed; 1 error reproducing the defect |
| New runtime checkpoint | None |

No claim of routing learning, probability improvement, revenue improvement or real-data deterministic equivalence is supported by this attempt. First-slot wall time and peak memory were not persisted before the exception; no performance bottleneck conclusion is drawn.

The new regression remains failing rather than weakening the expected non-EV behavior. Earlier fixture setup errors are retained in `arrival_fixture_setup_superseded.txt`; `arrival_regression.txt` is authoritative. Existing focused tests cover provenance, cutoff rejection, checkpoint/mixed-fleet fixtures, station reachability, UTC runtime, OD fallback and historical replay. Their synthetic parameter-update fixtures do not substitute for genuine real-data learning.

## Evidence

- `configuration.json`: exact configuration, Git identity/status, inherited routing and information manifests, script fingerprint and initial-state hashes.
- `preflight.json`: initialization and composition checks.
- `primary_run.log`, `primary_blocker.json`: original first-slot failure.
- `tests.txt`, `arrival_regression.txt`: bounded tests and isolated reproduction.
- `validation.json`: machine-readable blocked status, source fingerprints and preservation check.
- Runner: `scripts/validate_online_routing_experiment.py`; diagnostics wrap the existing local optimizer without replacing gradients or changing aggregation.
- Regression: `tests/test_online_routing_arrival_integration.py`.

No production modules, historical results or model checkpoints were edited. The existing preservation manifest confirms unchanged size/mtime for 2,279 historical paths. No extended training was started.

## Next single task

Correct the mixed-fleet post-arrival reserve applicability, retaining the EV station-reachability rejection and historical all-EV semantics. Validate the two arrival regressions, then retry this same four-slot learning/control protocol with an honestly refreshed source fingerprint if production code changes. Do not relax provenance checks or reuse this incomplete attempt as a successful experiment.
