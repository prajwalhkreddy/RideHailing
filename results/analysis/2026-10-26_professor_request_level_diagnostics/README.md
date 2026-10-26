# Professor request-level March 16 diagnostic

**ACTIVE_IMPLEMENTATION_DIAGNOSTIC**  
**NOT_SOURCE_VALIDATED_ACCEPTANCE_ANALYSIS**

The passenger acceptance source equation remains unresolved. This report describes the current implementation; it does not validate its equation against professor or paper authority.

## Fixture and scope

Exactly one four-slot simulation covered March 16, 2026, 00:00–02:00. It reproduced the existing greedy development fixture in `../2026-10-26_pricing_training_adequacy/march16_greedy_diagnostic.json`: seed 42, fresh fleet/operational state, identical request signatures in all four slots, and unchanged loaded model parameters. Pricing used greedy inference from `models/pricing_dqn/mar01_mar15_2026_nonprivate_seed42/checkpoint_0720_a79095b4/dqn`; routing used the frozen `models/routing_policy/mar01_mar12_2026_reachability_169x64x32x9_seed42/fedavg_round_5.keras`. This is not a new training run or a replay of the earlier random-pricing smoke test.

No acceptance, dispatch, routing, or pricing implementation was changed. No March 1–15 regeneration or March 17–31 evaluation was performed. Diagnostic instrumentation is contained in `diagnose.py`; its completed-output guard prevents accidental repetition.

## Current acceptance and sampling

The existing sampler draws positive E from the existing Normal parent distribution conditioned on E > 0, using the current weather/half-hour lookup and fallback rules. Its convention remains source-unvalidated.

For each request, the unchanged implementation uses:

```
P_disp = pricing_factor * P_base
P_max = P_base + P_base * ((trip_distance - L_base) / L_base) / E
accepted = (P_disp <= P_max)
```

Prices are USD; distance and L_base are miles. The Parquet preserves all inputs, outputs, actual arrival timestamp, slot timestamp, weather code, half-hour index, and sensitivity lookup level. Independently recomputing P_max and comparing every decision found **zero inconsistencies**.

## Passenger outcomes

| Measure | Result |
|---|---:|
| Generated | 2,838 |
| Accepted | 1,801 |
| Rejected | 1,037 |
| Acceptance | 63.460183% |
| Assigned | 1,801 |
| Accepted but unmatched | 0 |
| Assigned fare total, USD | 33,721.10975948257 |

| Pricing factor | Generated | Accepted | Rejected |
|---|---:|---:|---:|
| 0.85 | 581 | 372 | 209 |
| 0.90 | 2,257 | 1,429 | 828 |
| 0.95 | 0 | 0 | 0 |
| 1.00 | 0 | 0 | 0 |
| 1.05 | 0 | 0 | 0 |
| 1.10 | 0 | 0 | 0 |
| 1.15 | 0 | 0 | 0 |

Unobserved factors have undefined acceptance percentages, represented by blank CSV cells. These request counts are not counts of distinct OD-slot pricing decisions.

| Population | Mean E | Median E | Mean P_disp | Mean P_max |
|---|---:|---:|---:|---:|
| Accepted | 7.141297 | 6.383421 | 18.723548 | 39.224353 |
| Rejected | 3.057696 | 2.602911 | 18.526423 | 1.985043 |

Weather/half-hour and fixed distance-bucket breakdowns are in the corresponding CSVs. Distance buckets are 0–1, >1–3, >3–5, >5–10, and >10 miles.

## Dispatch and driver minimum-price counterfactual

All 1,801 assignments had a driver minimum price available from the persisted profile's `price_preference` field. **884 satisfy** and **917 violate** `P_disp >= P_i_min`: **50.916158%** violate. Equality passes. The column `current_code_price_gate_pass` is a counterfactual comparison, not evidence that dispatch enforced the gate.

The current dispatch does not enforce that hard price rule. These counts describe actual selected assignments only. They do not estimate replacement assignments, acceptance, or revenue under a corrected dispatch policy; that would require a different simulation.

`idle_candidate_count` records IDLE vehicles in the origin and directly neighboring grids at actual arrival, before acceptance/dispatch. It is not a count after energy/reserve eligibility checks. There were no accepted-unmatched requests: zero-idle, idle-existed/other feasibility, and unresolved unmatched categories all contain zero observations. No causal unmatched examples are invented.

## Focused validation and review files

Assertions passed for exactly 2,838 unique request IDs; generated = accepted + rejected; accepted = assigned + unmatched; independently recomputed acceptance decisions; all request timestamps within the four-slot window; and exact saved fixture signatures. Accepted/assigned counts and revenue match the existing fixture within floating-point tolerance.

Online/target pricing weights, optimizer variables, routing weights, replay size, and DQN/replay RNG states were unchanged after every slot. Optimizer steps remained **718 → 718**. Replay insertion and training calls were guarded against execution. Snapshot access was restricted to March 16; no March 17–31 evaluation occurred. No broad test suite was run.

- `request_level_diagnostics.parquet`: one row for each request, including all acceptance inputs and dispatch/gate outcomes.
- `acceptance_summary.json`: counts, accepted/rejected moments, formula and unchanged-model checks.
- `acceptance_by_pricing_factor.csv`: all seven factors; no fabricated observations.
- `acceptance_by_weather.csv`: actual weather-code × half-hour breakdown.
- `acceptance_by_distance.csv`: fixed distance buckets.
- `dispatch_summary.json`: assignment identities, unmatched breakdown and idle-candidate definition.
- `driver_price_gate_counterfactual.json`: available-profile coverage, passing/violating counts and example IDs.
- `representative_requests.csv`: five accepted-assigned, five rejected, and five gate-violating examples; zero unmatched examples because none exist. Categories can overlap.
- `diagnose.py`: local instrumentation used for this single execution; production code is untouched.

**PROFESSOR_REQUEST_LEVEL_DIAGNOSTIC_COMPLETE**
