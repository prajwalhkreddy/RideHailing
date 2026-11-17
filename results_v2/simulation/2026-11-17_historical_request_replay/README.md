# Historical request replay validation

Demand: `HISTORICAL_REQUEST_REPLAY_V1`; pricing: `FEASIBLE_OD_PRICING_V1`;
reward: `SUCCESSFUL_DISPATCH_REWARD_V1`. No model training performed.

## Results

For March12 2026, 00:00–00:30, the existing source contains **1,746** pickups.
Existing empirical-generator trip eligibility excludes **29** invalid trip rows;
**1,717** eligible pickups produce exactly **1,717** replay requests. There are
no unsupported OD pairs in this selected slot. This is count/conversion validation,
not a claim that all March slots were simulated or contain no unsupported pairs.

**16 focused tests and 76 bounded regression tests passed**, with zero failures
or errors. Tests cover independent forecast/count variation, exact trip alignment,
source ordering, no pre-decision request loading, reward reconciliation, unsupported
OD rejection, protected-date rejection before I/O, batch RNG order, historical
compatibility and deterministic full-runtime resume. Full runtime fixtures use
small constructed populations; the observed slot is not fully simulated.

## Bounded performance

| Measurement | Result |
|---|---:|
| Historical slot read | 0.206 s |
| Conversion of eligible observations | 0.029 s |
| Construction of 9,572 OD states | 0.538 s |
| Batched inference, 10 batches | 0.198 s |
| State-array payload | 497,744 bytes |
| Selected source-frame payload | 97,908 bytes |
| Replay transitions per slot | 9,572 |
| Transitions across 16 slots | 153,152 |
| Retained replay capacity | 100,000 |

Single bounded measurements use a small fixture fleet. They are not full-production
latency or process-memory estimates. No optimizer training occurred.

## Evidence and limitations

`final_validation/validation.json` contains configuration, source fingerprints, exact temporal
filter, support hash, Git commit/dirty state, timing, counts and test summaries.
`final_validation/focused_tests.txt` and `final_validation/regression_tests.txt` contain final execution results. The earlier root-level reports are retained as preceding validation evidence.
`preservation.json` verifies historical snapshot preservation.
The whole-source fingerprint is an integrity check; only the selected slot's
observations were inspected for this source-count diagnostic.

See `src/simulation/README.md` for the protocol, source-identifier encoding,
checkpoint contract, historical alternative and reproduction command.
TLC pickups proxy request arrivals. Unsupported ODs remain a fail-closed research
decision. The unchanged January mask justifies proactive zero-demand experiences;
causal pruning, stricter significance, pricing bounds, CNN information availability,
sensitivity estimation and other master gaps remain separate work.

Recommended next task: a bounded eligible-demand/OD-coverage audit over permitted
training dates, with an explicit decision for unsupported historical OD pairs,
before authorizing larger historical-replay execution. No protected evaluation,
model retraining or long simulation is included here.
