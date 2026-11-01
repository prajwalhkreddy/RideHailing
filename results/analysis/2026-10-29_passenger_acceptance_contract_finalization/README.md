# Passenger Acceptance Contract Finalization

**PASSENGER_ACCEPTANCE_CONTRACT_READY = YES**

## Frozen project contract

`Delta_D=(D-D_base)/D_base`; `Delta_P=(P-P_base)/P_base`; `epsilon=abs(Delta_D/Delta_P)`.

`P_dispatch=factor*P_base`; `P_max=P_base*(1+Delta_D/epsilon)`; passenger accepts iff `P_dispatch<=P_max`. Delta_D remains signed. A negative Delta_D can lower P_max below P_base, including negative P_max; no clamp is introduced. Equality accepts. The unchanged driver gate independently requires `P_dispatch>=driver.price_preference`, including equality.

PASSENGER_ELASTICITY_CONTRACT=FROZEN; PASSENGER_RUNTIME_SAMPLER=EMPIRICAL_BOOTSTRAP; PASSENGER_ACCEPTANCE_CONTRACT=FROZEN; DRIVER_PRICE_ELIGIBILITY=FROZEN. These are explicit project decisions, not claims of newly sourced paper equations.

## Historical population and support

The same **2,812,236 source-valid January1–January25 18:30 exclusive rows** established by the support analysis are used. This is the active runtime prior, not the superseded full-quarter Record-029 population. Finite positive fare and distance in(0,100]miles and existing weather/half-hour context validity remain unchanged. No raw preparation was rerun.

The new persisted historical artifact is `data/processed/passenger_empirical_absolute_epsilon_2026_01.parquet`, with a JSON fingerprint/contract beside it. It retains the source-valid fare/distance pairs, context references and exact epsilon observations. The old historical artifacts remain unchanged. Exact-context bases are reused from the validated artifact and checked against source means. Every exact runtime pool matches persisted epsilon values bitwise.

There are243 exact observed contexts. Each context excludes exact Delta_P0, then nonfinite epsilon, then nonpositive epsilon, with disjoint counts. This actual population has **zero such exclusions**, including the broader fallback pools. No old0.01mile distance-deviation filter, artificial epsilon floor, tail clipping or cap is applied. Exact-context support is **[4.0782867887295956e-06, 468668.1627126722]**; all positive near-zero observations and duplicate frequencies remain intact.

## Implementation and fallback

`src/pricing/empirical_sensitivity.py` implements the empirical sampler. `src/pricing/dqn_contract.py::behavioural_model` loads the fingerprint-checked new artifact for final production. Legacy Normal code is retained only for historical compatibility; it is not used by the final factory. The existing maximum_price and acceptance algebra are reused without changes.

The existing hierarchy remains exact WeatherCode×Period → Period → WeatherCode → global. A context without valid epsilon is skipped. Broader pools recompute their own P_base/D_base from the corresponding broader source population, preserving the existing fallback reference semantics; they do not mix incompatible exact-context ratios with a different fallback base. `empirical_sampler_validation.json` reports support and exclusions for each level.

Each request selects one uniformly random row index with replacement from its resolved pool using the caller's persistent NumPy Generator. No Normal draw, folding, interpolation or smoothing occurs. Context selection and fallback consume no RNG. Repeated rows retain repeated probability mass. The generator is not reset each slot; pickle checkpoint round-trip tests preserve subsequent draws. Nonfinite P_max fails closed with requested context, fallback level, bases, distance and epsilon in the error.

Requested context, resolved context and fallback level are recorded in the March16 request diagnostics. Final runtime's existing response fallback-level field remains supported.

## Focused tests and distribution fidelity

**30 tests passed,0failed before the simulator run**: frozen formula/sign, undefined/nonpositive exclusions, retained near-zero values, exact pool membership, replacement, seed reproducibility, correct context/fallback including empty exact pools, P_max signed-distance cases/equality/finiteness, driver price gate, unmatched separation, and checkpoint/RNG continuation. No broad suites or training ran.

One million diagnostic draws used the runtime sampler, with context counts allocated according to historical row-count weights and seed42. All draws belong to their resolved pools; no synthetic below-support tail exists.

| metric | historical | sampled |
| --- | --- | --- |
| mean | 3.9673995685142094 | 3.641255704609152 |
| median | 1.3155416793316084 | 1.3146019160638571 |
| SD_population | 307.7879831635643 | 87.62754957380835 |
| P0.1 | 0.008090362306854898 | 0.008013199806792637 |
| P0.5 | 0.040509460818666805 | 0.040752297621593304 |
| P1 | 0.08160350490003833 | 0.08234388475132827 |
| P5 | 0.40277148273406294 | 0.403123371670423 |
| P25 | 1.1255217273175695 | 1.1250715277343026 |
| P75 | 1.8163098327985603 | 1.8162347748912586 |
| P95 | 5.469235407566955 | 5.441518840442382 |
| P99 | 26.237185214589516 | 25.993126173190618 |

Quantiles and median are close, but sampled SD87.62755 differs materially from historical307.78798. The largest historical value468668.16 was not drawn (sample maximum41906.48). This is a finite-bootstrap tail realization, not clipping or synthetic support. The mean difference is -0.326144; the historical IID-reference standard error at one million draws is 0.307788. Sampling preserves empirical probabilities; it does not force exact sample moments. Fidelity passes support and implementation checks, not a claim that the sampled SD equals historical SD.

## Single March16 combined development validation

Exactly one seed42 development run covered00:00–02:00, four half-hour slots. Request signatures match the existing2,838-request fixture. It uses existing greedy pricing from the prior pricing checkpoint and the frozen routing checkpoint as provenance—not newly validated learned policies. No optimizer/replay insertion or federated updates were permitted. Model/optimizer variables and replay size remained unchanged after every slot.

| metric | value |
| --- | --- |
| requests | 2838 |
| accepted | 1197 |
| rejected | 1641 |
| assigned | 1197 |
| unmatched | 0 |
| price_ineligible_candidate_count | 53706 |
| requests_with_any_price_ineligible_candidate | 1143 |
| accepted_requests_unmatched_due_to_no_price_eligible_driver | 0 |
| revenue | 22135.616538986756 |
| fleet_count | 5000 |
| charging_decisions | 0 |
| charging_events | 0 |
| movement_checks | 2945 |

Identities pass: generated=accepted+passenger-rejected and accepted=assigned+unmatched. Reward equals summed assigned fares. All assigned fares satisfy the driver gate; counterfactual violations are zero. Candidate-level price failures are not passenger rejections and can occur even when another eligible driver is assigned. All5000 vehicles are conserved; energies remain finite/nonnegative. Movement checks verify any grid change follows an already busy vehicle's destination at a completed travel time. Existing passenger arrival/charging checks remain active. No teleportation was detected.

All sampled epsilon values belong to their resolved empirical pools; all P_max values are finite. The new P_max mean/sampleSD/median is **21.465555/119.033635/16.014187**, compared with old25.617178/167.774111/19.770191. Changed SD is descriptive, not a pass/fail criterion. New extrema and requested percentiles are in march16_pmax_distribution.json.

Seven-factor comparisons reuse exactly these new passenger realizations without further RNG:

| factor | accepted | rejected | acceptance_percentage |
| --- | --- | --- | --- |
| 0.85 | 1256 | 1582 | 44.25651867512333 |
| 0.9 | 1148 | 1690 | 40.45102184637068 |
| 0.95 | 1062 | 1776 | 37.420718816067655 |
| 1.0 | 953 | 1885 | 33.5799859055673 |
| 1.05 | 879 | 1959 | 30.972515856236782 |
| 1.1 | 834 | 2004 | 29.38689217758985 |
| 1.15 | 801 | 2037 | 28.224101479915433 |

This is not an optimal-pricing claim or evidence of DQN convergence. New policies changed fleet availability and therefore greedy state-dependent decisions, so aggregate differences are not an isolated causal estimate of the sampler alone.

## Artifacts and next step

Required JSON/CSV reports are provided alongside `march16_request_diagnostics.parquet`, the guarded one-run validation script and historical-population preparation script. The new historical population and metadata are under data/processed. The root README current resume section links here.

Existing routing experiences, central/FedAvg checkpoints and pricing checkpoints remain **PRE_CORRECTION_PROVENANCE**. March1–15 regeneration **NOT YET RUN**. No training, DQN methodology change, driver-gate change, privacy work or March17–31 access occurred. The next separately authorized task may create a new clean routing-experience dataset under both corrected upstream contracts without overwriting provenance. It was not launched here.
