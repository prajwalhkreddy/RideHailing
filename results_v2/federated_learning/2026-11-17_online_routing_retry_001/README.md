# Mixed-fleet arrival correction and online-routing retry 001

**Outcome: arrival correction validated; four-slot learned run and checkpoint/resume passed; independent repeat blocked by global RNG fingerprint mismatch.** The control was not launched after the correctness stop. This is a bounded development integration experiment, not final model training or publication evaluation.

## Correction and provenance

`ProductionExperiment.advance_until` previously required charging-station battery reserve for every arrival, including explicit non-EVs. `research_mixed.configure` establishes `vehicle.is_ev`; non-EVs retain zero energy and already bypass battery constraints in dispatch, energy consumption and utility routing. Movement preserves the same vehicle identity. The arrival check now uses that same `getattr(vehicle, 'is_ev', True)` contract: explicit non-EVs skip the battery reserve; absent identity preserves historical all-EV semantics. Location/status and travel timing checks remain active. EV thresholds, charging-mission handling and station-reserve calculations are unchanged.

Arrival errors include ID, EV type, current grid, original destination, energy, applicable reserve, UTC event time and reason. No private preferences are included. Run logs use restricted file permissions. The original failed experiment did not capture its vehicle identity; this retry does not assert that the original vehicle was a non-EV.

The original failed directory and historical initialization evidence remain unchanged. `routing_initialization.json` and `information_contract.json` here carry the corrected source hash and explicit new activation provenance; they do not relabel historical trained weights. The runner was reused with output/provenance overrides. The provenance tests now target this current source manifest, retaining their incompatibility checks.

## Frozen experiment

March12 2026 00:00–02:00 New York / 04:00–06:00 UTC; four elapsed 30-minute slots; 120-second mini-slots; 5,000 vehicles, exactly 500 EVs and 4,500 non-EVs; seed42. January OD support and January–February weighted sensitivity are unchanged. Forecasts use the existing cutoff-valid January historical-average baseline and assumption-based 120-minute weather persistence. Realized request weather retains its previously documented research availability limitation.

Fresh 169→64→32→9 routing, Adam0.001, minibatch capacity32, one local epoch, bounded memory1000 and persistent local optimizers are unchanged. Each current-slot participant trains on its available latest minibatch; memories include only already realized experiment experiences. FedAvg uses equal participating-client weights and is NONPRIVATE. The initial weight hash is unchanged from the approved fresh contract. Pricing remains seeded epsilon-greedy with no optimizer updates. No CNN training or March17–31 access occurred.

## Primary learned run

| Slot | Requests | Participants/updates | Sample presentations | Mean local CE | Global update L2 | Mean absolute probability change |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 1717 | 4788 | 4788 | 10.425753 | 0.018974 | 0.009015 |
| 2 | 1153 | 4824 | 9519 | 9.353158 | 0.019686 | 0.012538 |
| 3 | 729 | 4855 | 14284 | 8.313862 | 0.020756 | 0.015569 |
| 4 | 538 | 4875 | 19079 | 7.058232 | 0.021148 | 0.020759 |

All four rounds made genuine gradient updates: **19,342 optimizer steps**, **47,670 sample presentations**, and four nonzero global parameter changes. Finite gradients, losses and weights were checked; global weights were independently checked against the equal-client average. Masked routing probabilities were finite, normalized and zero on invalid actions. Global availability advanced at slot boundaries. Within-run probability changes also include changing operational states and must not be interpreted as a controlled learning effect.

Request accounting: 4,215 source rows = 78 excluded by unchanged validity rules + **4,137 eligible requests**; 4,135 supported and 2 fallback. There were **1,192 accepted**, **2,945 rejected**, **996 assigned**, and **196 accepted-unmatched**. Successful-dispatch reward reconciled to **$21,934.508396884783**, including fallback revenue. Replay contains **38,288** transitions; pricing optimizer updates are zero.

Fleet size/composition, finite bounded EV energy, zero non-EV energy, non-EV exclusion from charging, normal arrival checks, UTC processing and checkpoint boundary checks passed. **Charging events: 0**; real charging activity is not claimed. Existing focused charging tests retain safety coverage.

## Determinism and stop

The saved slot2 checkpoint restored exactly. Resumed slots3 and4 matched the uninterrupted run exactly across runtime, routing/global/local state, optimizer state, private memory, fleet/charging and captured RNG fingerprints.

The independent fresh repeat completed slot1 computation but failed the strict comparison:

```
Determinism mismatch at slot 1: ['global_rng']
```

All other compared fingerprints matched: runtime, hierarchy, local parameters/optimizers, charging, pricing weights and pricing optimizer. The mismatch is not evidence of differing dispatch outcomes, but it fails the explicitly required RNG-state equivalence. No component of the global RNG bundle was guessed or silently ignored. The experiment stopped; remaining repeat slots and the no-update control were not executed. Therefore full repeatability and a control comparison remain unvalidated.

## Tests and performance

The prepatch isolated non-EV failure was reproduced. After correction, **46 focused tests passed in 55.084 seconds**, including non-EV zero-energy arrival, no reserve lookup for non-EVs, EV insufficient/sufficient reserve, UTC arrival, diagnostic content, absent-identity historical behavior, charging/station safety, provenance, checkpoint, replay and OD fallback.

Primary slot execution totaled **579.49 seconds** (279.63,104.79,99.10,95.97). The maximum recorded primary process RSS was **3,506,487,296 bytes** on macOS. These slot times exclude startup, checkpoint serialization and diagnostic hashing. Local optimizer-call time totaled about312.44 seconds; initial local-model construction adds overhead. No client subsampling or fleet reduction was used. Resume also incurs per-driver model/optimizer reconstruction. No separate performance tuning was attempted.

## Evidence and preservation

- `configuration.json`, `preflight.json`, `correction.json`: Git/configuration provenance, cutoff checks and source fingerprints.
- `primary_slot_metrics.csv`, `primary_metrics.json`, `primary_request_reconciliation.csv`, `primary_probabilities.npz`: aggregate primary evidence.
- `primary_checks.json`, `resume_checks.json`, corresponding completion files: exact equivalence evidence.
- `slot2_checkpoint/`: private runtime checkpoint, not a platform-facing report; retains local state for reproducibility.
- `repeat_blocker.json`, restricted `repeat_run.log`: new stopping condition.
- `tests.txt`, `validation.json`, `preservation.json`: tests, machine-readable outcome and unchanged 2,279 historical paths under the existing size/mtime manifest.

Historical results, checkpoints and the original failed-run evidence remain untouched. No default experiment activation or extended training was introduced.

## Next single task

Diagnose the fresh-run global RNG fingerprint mismatch and establish deterministic initialization/capture semantics without weakening the equivalence check. Then complete the outstanding independent repeat and matched control under the same frozen protocol. No performance or final-learning claim is justified yet.
