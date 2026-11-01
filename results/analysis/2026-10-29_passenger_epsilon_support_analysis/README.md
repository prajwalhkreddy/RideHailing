# Passenger Epsilon Support Analysis

## Frozen core contract

**PASSENGER_ELASTICITY_CORE_CONTRACT_FROZEN = YES**. The explicit project decision of 29 October 2026 resolves the following:

```
Delta_D = (D - D_base) / D_base
Delta_P = (P - P_base) / P_base
epsilon = abs(Delta_D / Delta_P)
P_max = P_base * (1 + Delta_D / epsilon)
P_dispatch = pricing_factor * P_base
accept iff P_dispatch <= P_max
```

Epsilon is nonnegative; sign is not retained. The P_base multiplier and inverse-epsilon P_max expression are frozen. No orientation/sign/multiplication question is reopened. This is an explicit project contract, not a claim of newly identified paper validation. Runtime acceptance and historical artifacts remain unchanged in this analysis; the currently calibrated epsilon moments are not aligned with the resolved formula.

## Population and references

The final runtime's `behavioural_model` loads the existing January historical prior and hierarchical fallback artifacts, not the Record-029 full-quarter population. Its source-valid calibration population is **2,812,236 rows**, January1 inclusive through January25 18:30 exclusive, across **243 WeatherCode × Period contexts** (Period0–47). This is the existing runtime prior's intended historical population, not a newly selected Jan–Mar population. No March17–31 rows were accessed.

Processed `cleaned_trips.parquet` and the existing January demand weather/time lookup were read with date filters. Finite positive fare, finite distance in (0,100] miles and valid context restrictions were preserved. Persisted context P_base and D_base were reused and independently verified against all source-valid group means. No new global or fare-conditioned reference was constructed.

The old calibration retained2,807,460 rows after excluding4,776 rows within0.01mile of D_base. That was a denominator-resolution restriction for the **old price-over-distance formula**. For this diagnostic the complete source-valid population is reported before that formula-specific restriction, with its affected count separately disclosed. No production cleaning rule was changed; whether to preserve this restriction under the new formula remains an explicit decision. A distance band is not a universal epsilon floor.

## Zero semantics

Old preprocessing excludes abs(D−D_base)<0.01mile using floating-point comparison tolerance. It does not explicitly exclude Delta_P=0: a retained such row would yield old epsilon0. Near-zero old epsilon is retained; there is no clipping. Reconstructing the old observations reproduces persisted group means and counts and finds **zero old epsilon0 rows**.

Under the newly frozen formula, exact Delta_P0 is undefined at calibration; exact Delta_D0 with nonzero Delta_P produces epsilon0, which is undefined for runtime P_max. Both counts are **zero** here. Undefined values are separately counted, never clipped. All2,812,236 new epsilon values are finite and positive. Runtime rejects an explicitly supplied zero epsilon; its sampler produces strictly positive values.

## Empirical distribution

| Statistic | Absolute epsilon |
|---|---:|
| min_positive | 4.0782867887296e-06 |
| P0.01 | 0.000753708665758232 |
| P0.05 | 0.00395301501758253 |
| P0.1 | 0.0080903623068549 |
| P0.5 | 0.0405094608186668 |
| P1 | 0.0816035049000383 |
| P2.5 | 0.204928353197624 |
| P5 | 0.402771482734063 |
| P10 | 0.76305372657768 |
| P25 | 1.12552172731757 |
| median | 1.31554167933161 |
| mean | 3.96739956851421 |
| P75 | 1.81630983279856 |
| P90 | 3.06400368171028 |
| P95 | 5.46923540756695 |
| P99 | 26.2371852145895 |
| P99.5 | 51.6900248550857 |
| P99.9 | 271.746423703785 |
| max | 468668.162712672 |

Percentile labels are percentages: P0.01 means the0.01st percentile (quantile0.0001), not P1. Linear empirical quantiles are used. Nested counts for0<epsilon below0.001/0.005/0.01/0.025/0.05/0.10 are respectively **377 / 1,773 / 3,498 / 8,722 / 17,331 / 34,391**. Exact epsilon0 count is0.

`epsilon_by_context.csv` contains all243 observed contexts, source/defined N, zero counts, minimum positive, P0.5/P1/P5, median, mean and population SD (ddof=0). No missing contexts are fabricated. Fallback groups are not additional disjoint observations in this table.

## Current sampler diagnosis

Parent Normal parameters are the persisted **old-formula** epsilon_mean and epsilon_std_population, resolved from exact weather/half-hour, then same Period, then same WeatherCode, then global. Generic default is error on missing context; final runtime explicitly selects hierarchical fallback. Exact parent ranges and global parent parameters are recorded in sampling_support_assessment.json.

`sample_positive_truncated_normal` uses SciPy truncnorm on (0,infinity) with standardized lower bound−mu/sigma. For sigma0 it returns positive mu, otherwise rejects an invalid zero-variance group. A numerical nonpositive sampled result is replaced by nextafter(0,1); this is not an empirical lower bound and does not prevent extreme amplification. The mathematical support includes arbitrarily small positive values. Parent mu/sigma are not the output truncated-distribution moments.

The caller supplies a persistent NumPy Generator; final runtime seeds it using default_rng(seed), with42 the baseline. SciPy receives that generator through random_state. No RNG was invoked here.

**Current sampler aligned with the frozen historical definition: NO.** Its parent moments were computed from the reversed ratio. The active P_max algebra already matches the newly frozen expression, but its E distribution does not. No runtime correction was made.

## Near-zero P_max sensitivity

`pmax_near_zero_sensitivity.csv` evaluates all nine requested epsilon values at empirical Delta_D P10/median/P90: −0.7979095182 / −0.4397970740 / +1.4474977815. At epsilon0.001 the corresponding P_max/P_base ratios are approximately **−796.9095 / −438.7971 / 1448.4978**; at epsilon1 they are0.2020905 /0.5602029 /2.4474978.

As epsilon approaches zero from above, positive Delta_D gives positive divergence and negative Delta_D gives negative divergence. Delta_D0 gives ratio1 for every strictly positive epsilon; at epsilon0 the formula remains undefined. No negative P_max clipping is introduced. These analytical ratios require no saved requests, simulation or new acceptance draws.

## Data-derived support options

| Candidate | Historical observations affected | Maximum inverse-epsilon amplification |
|---|---:|---:|
| Strict epsilon>0 only | 0 | Unbounded continuous support |
| Observed positive minimum4.078286788729596e-6 | 0 | 245201.000274 |
| Empirical P0.5=0.040509460818666805 | 14062 (0.500029%) | 24.685591 |
| Empirical P1=0.08160350490003833 | 28122 (0.999987%) | 12.254376 |
| Old abs(D−D_base)>=0.01mile | 4776 (0.169829%) | No uniform epsilon bound implied |

Affected fractions use defined historical epsilon N; undefined denominator count is separately0. Inclusive percentile bounds exclude only values strictly below them. Strict-positive continuous support is unbounded in amplification even though this finite empirical sample has a positive minimum. The sample minimum is not a guaranteed population bound. All are candidates only; no floor or percentile is selected.

## Sampling-family evidence and remaining decision

Positive-truncated Normal conditions on positive draws; folded Normal abs(Normal(mu,sigma)) maps both tails onto the positive axis. Their densities and moments differ. Taking an absolute Normal draw enforces nonnegativity but does not reproduce a historical ratio distribution.

Empirical/bootstrap sampling from the newly computed absolute epsilon values most faithfully preserves the observed distribution and duplicate frequencies, conditional on an explicitly approved support/zero policy. This is a fidelity assessment, not implementation or approval to replace the family.

The identified `Final_Next_Implementation_Process.docx`, XML paragraphs56–57, prescribes an ordinary Normal without mandatory truncation and allows bounds as a later modelling choice; paragraph96 repeats Normal sampling. It does not uniquely resolve the positive-support issue after the new nonnegative contract. Folded or empirical sampling would require a new explicit family decision. No document establishes P0.5 or P1 as a required floor.

**EPSILON_SUPPORT_DECISION_REQUIRED = YES**: freeze the sampling family and handling/support of zero and small positive epsilon; explicitly decide the fate of the old distance-resolution restriction. No arbitrary epsilon floor, empirical tail clipping, distribution fit or runtime change is authorized by this report.

## Validation and status

Source-valid N, old retained N, old group epsilon means and all context reference means reproduced existing artifacts. New epsilon is finite/nonnegative;243 context totals reconcile. Source/runtime hashes are recorded and unchanged. Only analytical calculations and documentation were performed: zero simulator runs, zero training/regeneration, zero runtime RNG draws, no March17–31 access.

The hard driver minimum-price gate remains implemented, including equality. Downstream artifacts remain pre-correction provenance until the calibration/sampling contract is implemented and jointly validated. Core mathematics is resolved; runtime sampling support remains the next decision.

## Files

- epsilon_distribution.json: full-population statistics, quantiles, zero counts and old eligibility comparison.
- epsilon_by_context.csv: all observed weather/half-hour summaries.
- near_zero_support.csv: candidate bounds, affected fractions and amplification.
- pmax_near_zero_sensitivity.csv: analytical ratios, not simulated outcomes.
- sampling_support_assessment.json: frozen core contract, current sampler, evidence, unresolved support and validation hashes.

**PASSENGER_EPSILON_SUPPORT_ANALYSIS_COMPLETE**
