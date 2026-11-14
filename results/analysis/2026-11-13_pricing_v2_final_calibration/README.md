# Passenger Pricing V2 — final bounded calibration

**Analysis complete; V2 is not frozen or implemented.** All numerical observations are Jan1–Mar15 only. No production imports, model loads, dispatch simulation, training, physical-field changes or protected March17–31 access. Current hybrid generator retained by the provisional decision.

## Scope, provenance and methods

Reused prior verified `pricing_recalibration_decision_analysis/intermediate/fare_array_range.npy`, `distance_array_range.npy` and the two matching new-e arrays. These derive from the Jan1–Mar15 restricted cache; no full-period Parquet was opened. Filter: **1.5<=distance_km<75**, giving **6,967,155 trips**. TLC fare_amount in USD; source miles already converted by1.609344 in prior artifacts. P_base remains the expressly supplied **22.354198442390455**, even though its original [1,75) population differs from the new filter. It was not recomputed. No old VALID/T0/absolute-epsilon rule applied.

The active pricing/request/dispatch symbols were re-read and six source fingerprints match the preceding audit, before and after calculation. Paths/hashes below. Units and physical distance remain unchanged. All arrays were read with memory mapping; analysis intermediates exist only in process memory. Exactly six requested deliverables are produced.

For each reference, compute signed e=r_L/r_P. Exact zero price denominator is undefined; zero numerator with nonzero denominator is0. Candidate fare-gap thresholds flag **abs(P−P_base)<t**, then scenario fits/statistics retain >=t; these are diagnostic exclusions only, not source deletion. t=0 is the unfiltered comparator. Quantiles use NumPy linear interpolation; SD ddof0. Negative rates use the scenario's finite retained denominator. Exponential is the **only fitted family requested**; loc=0, scale=mean(positive e), rate=1/scale, full-population MLE (no fit subsample). Empirical CDF is an in-sample comparator, not a fitted winner. KS is descriptive; no IID/estimated-parameter p-value claimed. AIC/BIC only meaningful on the same target, not across different retained populations.

## Reference and denominator findings

| L_base | N | mean | SD | median | negative_N | negative_pct | zero_N | undefined_N |
|---|---|---|---|---|---|---|---|---|
| 4.500000 | 6967155.000000 | 1.451388 | 30.825790 | 1.038759 | 1023368.000000 | 14.688463 | 0.000000 | 0.000000 |
| 4.616984 | 6967155.000000 | 1.439360 | 29.909855 | 1.058745 | 991502.000000 | 14.231089 | 0.000000 | 0.000000 |

Provisional preference: **4.616983790655043 km**, because it represents the interpolated mean-fare curve crossing rather than an arbitrary bin lower edge. This is an interpretive recommendation, not a uniquely identified physical meter threshold and not selection by minimum SD. Both formulas are continuous in distance at their respective L_base for fixed e>0, but have a derivative kink; neither has superior mathematical continuity. Both produce a flat P_base below L_base, with the same short-trip pricing bias. The smoothness CSV rows evaluate e=0/0.1/1/2/10 at L_base±0.01 and exactly L_base. The special e=0 branch is not continuous as e approaches0 from above for long trips.

| L_base | threshold_USD | flagged_N | flagged_pct | mean | SD | median | P95 | P99 | max_abs | negative_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| 4.500000 | 0.000000 | 0.000000 | 0.000000 | 1.451388 | 30.825790 | 1.038759 | 5.784581 | 23.694626 | 17161.442304 | 14.688463 |
| 4.500000 | 0.010000 | 821.000000 | 0.011784 | 1.447890 | 15.448474 | 1.038759 | 5.782204 | 23.542209 | 6245.365443 | 14.684510 |
| 4.500000 | 0.050000 | 4189.000000 | 0.060125 | 1.458415 | 10.559040 | 1.038759 | 5.766081 | 22.962197 | 3584.952288 | 14.667155 |
| 4.500000 | 0.100000 | 9806.000000 | 0.140746 | 1.440864 | 9.344993 | 1.038759 | 5.735380 | 22.241228 | 2292.183484 | 14.644199 |
| 4.500000 | 0.250000 | 113212.000000 | 1.624939 | 1.282457 | 4.619529 | 1.034893 | 5.167809 | 12.780501 | 1098.776230 | 14.352921 |
| 4.500000 | 0.500000 | 206403.000000 | 2.962515 | 1.377716 | 3.480044 | 1.038759 | 4.987986 | 11.274981 | 548.275096 | 13.691983 |
| 4.616984 | 0.000000 | 0.000000 | 0.000000 | 1.439360 | 29.909855 | 1.058745 | 5.572599 | 22.860417 | 16628.981005 | 14.231089 |
| 4.616984 | 0.010000 | 821.000000 | 0.011784 | 1.433840 | 14.925137 | 1.058745 | 5.564387 | 22.666524 | 6063.715555 | 14.226966 |
| 4.616984 | 0.050000 | 4189.000000 | 0.060125 | 1.443481 | 10.149128 | 1.058745 | 5.553538 | 22.150070 | 3483.667249 | 14.209462 |
| 4.616984 | 0.100000 | 9806.000000 | 0.140746 | 1.426335 | 8.968640 | 1.058745 | 5.522269 | 21.275397 | 2230.220045 | 14.186481 |
| 4.616984 | 0.250000 | 113212.000000 | 1.624939 | 1.286107 | 4.429415 | 1.055828 | 4.979554 | 12.406590 | 1069.142214 | 13.870279 |
| 4.616984 | 0.500000 | 206403.000000 | 2.962515 | 1.366253 | 3.342463 | 1.058745 | 4.797601 | 10.831989 | 533.492211 | 13.229815 |

**No smallest defensible final threshold is established.** $0.01 flags821 rows (0.011784%) and halves SD, but extreme magnitude remains above6,000. At$0.10 only0.140746% is flagged, yet maxima exceed2,200. $0.25/$0.50 materially change tails and affect1.624939%/2.962515% of observations; stability does not plateau. The median is comparatively stable, which is not enough to declare a cutoff correct. Keep all five candidates pending an explicit resolution/admissibility decision. $0.10 is used below only as a labelled interior comparison, never as a recommendation.

N>=100 is applied to diagnostic support only:120 of147 half-km bins supported;27 bins contain1,665 trips (0.023898%). All those trips remain in the calibration population. This respects the distinction between sparse-bin mean evidence and individual passenger inclusion.

Negative e arises entirely from opposite-signed deviations, not numerical sign errors. At interpolated L_base,991,502 (14.231089%) are negative before fare-gap exclusions; even$0.50 retains a substantial13.229815% negative share. Most negatives therefore cannot be explained by the narrow denominator boundary. The CSV separates distance, price/distance signs, magnitude/frequency and gap medians. These are interpretable fare-distance heterogeneity, not automatically invalid or validated causal behavioural sensitivities. No abs transform applied.

## Positive distribution and generated-price implications

| L_base | threshold_USD | N | scale | KS | relative_error_median_pct | relative_error_P99_pct |
|---|---|---|---|---|---|---|
| 4.500000 | 0.000000 | 5943787 | 2.821176 | 0.186447 | 67.307709 | -52.971755 |
| 4.500000 | 0.010000 | 5943362 | 2.692154 | 0.171946 | 59.656211 | -55.122502 |
| 4.500000 | 0.050000 | 5941697 | 2.599518 | 0.161036 | 54.162485 | -55.725943 |
| 4.500000 | 0.100000 | 5938501 | 2.535605 | 0.153407 | 50.441418 | -54.995490 |
| 4.500000 | 0.250000 | 5870202 | 2.078675 | 0.136915 | 23.960617 | -31.330272 |
| 4.500000 | 0.500000 | 5835071 | 1.988208 | 0.146407 | 19.229428 | -24.053233 |
| 4.616984 | 0.000000 | 5975653 | 2.746274 | 0.178273 | 60.699347 | -51.998948 |
| 4.616984 | 0.010000 | 5975236 | 2.619000 | 0.163280 | 53.251821 | -53.880241 |
| 4.616984 | 0.050000 | 5973566 | 2.527947 | 0.152032 | 47.923829 | -54.160427 |
| 4.616984 | 0.100000 | 5970346 | 2.465841 | 0.144245 | 44.377575 | -53.294127 |
| 4.616984 | 0.250000 | 5903282 | 2.038292 | 0.149710 | 20.282392 | -29.970871 |
| 4.616984 | 0.500000 | 5866317 | 1.946258 | 0.160142 | 15.372795 | -22.274065 |

**DISTRIBUTION_FAMILY_STABILITY=WEAK** as evidence for a recommended family. There is only one permitted fitted family, so robust preference over other families cannot be established. Exponential consistently overestimates the median by15–67% and underestimates P99 by22–56%. Neither reference nor threshold yields a justified final exponential sampler. No additional families were fitted. All fitted parameters and median/P90/P95/P99 reproduction are persisted; loc0 and rate1/scale are explicit. Final distribution parameters: unresolved.

A structural problem is independent of fit scores: with untruncated exponential e, E[1/e] diverges. Therefore for any L>L_base the proposed **unclipped reference fare has infinite theoretical mean**. This is not fixed by removing historical near-P_base observations: exponential fitting still assigns support down to0. No new epsilon floor or truncation is invented. A fitted-support decision is necessary before freeze.

## P_ref validation and offline offers

For e>0 and L>L_base, P_ref=P_base+(P_base/e)r_L is the algebraic inverse of e=r_L/r_P. For paired historical e it reconstructs the original fare to floating precision; this is an identity, **not predictive validation**. The effective-distance floor changes this identity below L_base. Invalid/undefined e has no generated reference; exact e=0 has the expressly proposed base-price branch.

Independent sensitivity diagnostics use deterministic product quadrature:256 equally weighted quantile-midpoint nodes of each empirical distance band crossed with256 fitted exponential quantile nodes. There is no simulated request/dispatch, no DQN action selection, no RNG, and no fitted-parameter subsampling. This isolates independent sensitivity assignment; it is not the forecast-origin-weighted runtime request law. CSV N=65,536 in those rows denotes quadrature nodes, not real trips; observed_N records actual support. Quantiles/coverage/clipping are bounded approximations. Quadrature mean/SD/max are **finite-node diagnostics, not theoretical moments or hard bounds**. A512×512 check at the interior$0.10 scenario changes medians by at most$0.0213 and P95 by$3.44 (long-tail band); extreme moments are not convergence-certified. No final choice depends on them.

At interpolated L_base and diagnostic$0.10 gap:

| distance_lower | distance_upper | median | P05 | P95 | median_bias | observed_coverage_generated_P05_P95_pct |
|---|---|---|---|---|---|---|
| 1.500000 | 3.000000 | 22.354198 | 22.354198 | 22.354198 | 10.954198 | 0.000000 |
| 3.000000 | 5.000000 | 22.354198 | 22.354198 | 23.071702 | 5.354198 | 2.038218 |
| 5.000000 | 10.000000 | 28.149921 | 23.129732 | 111.650915 | 2.749921 | 65.430952 |
| 10.000000 | 20.000000 | 48.398092 | 27.836653 | 383.477629 | 9.698092 | 93.069763 |
| 20.000000 | 40.000000 | 86.099436 | 36.546767 | 892.768911 | 16.099436 | 98.069506 |
| 40.000000 | 60.000000 | 137.768728 | 48.716110 | 1587.639154 | 38.868728 | 94.991430 |
| 60.000000 | 75.000000 | 196.433732 | 62.407759 | 2381.655697 | 7.233732 | 83.748754 |

The1.5–3 km reference is exactly$22.3542 versus observed median$11.40; thus its degenerate P5–P95 interval covers0% of observed fares. Long-band reference intervals are excessively broad. Coverage means observed fares inside generated P5–P95; the reciprocal generated-inside-observed interval metric is also supplied. High long-band coverage alone is not calibration success.

For representative negative e, the same algebra is evaluated **only as a counterfactual continuation**, not an allowed runtime branch. Negative generated price rate is0% in the paired data: long-distance negative e reconstructs positive observed fares below P_base; short-distance floor returns P_base. However61.878816%/58.334628% of negative cases at L_base4.5/interpolated respectively yield a below-base long-trip reference. That violates the proposed base-fare interpretation and reverses the positive-sensitivity direction. With independent negative draws, nonpositive fares are mathematically possible. Clipping can conceal rather than resolve this semantic problem. “Implausible” is operationalized here as below-base long-trip fare, not a source-invalid label. **NEGATIVE_E_RUNTIME_POLICY=ACADEMIC_DECISION_REQUIRED**.

## Fare bounds and seven-action coverage

Empirical bounds use the complete approved distance population, before diagnostic denominator scenarios. Candidate clipping fractions below are on actual fares, not generated prices:

| q_lower | lower | upper | pct_low | pct_high |
|---|---|---|---|---|
| 0.005000 | 6.600000 | 94.700000 | 0.499731 | 0.491851 |
| 0.010000 | 7.200000 | 81.460000 | 0.542747 | 0.999963 |
| 0.025000 | 7.900000 | 70.000000 | 1.549556 | 1.690647 |
| 0.050000 | 8.600000 | 64.300000 | 3.546139 | 4.998066 |

No bound is frozen. Recommend **[6.60,94.70] (P0.5–P99.5) only as the least restrictive review comparator**, not a recommended runtime cap: overall quantiles disproportionately cap long trips. All four pairs are reported by distance/scenario/action. Raw extrema are never bounds.

Offers are alpha×P_ref with all seven requested factors, before clipping. ACTION_OFFER rows give distributions; ACTION_ENVELOPE coverage is the fraction of observed fares between the P5 of the0.85 offer and P95 of the1.15 offer, not an acceptance rate or coverage of seven fixed prices. At the illustrative interpolated/$0.10 scenario, envelope coverage ranges6.31% (1.5–3 km) to98.83% (20–40 km). Short-trip minimum offer≈$19.0011 remains well above observed median$11.40.

With the widest [6.60,94.70] pair, any action collapse is0%,0.079%,6.911%,25.024%,50.006%,71.379%,84.863% across ascending bands; all seven collapse to one for74.158% of60–75 km quadrature cases. These are model-conditional approximations, not actual selected-action frequencies. Per-arm low/high fractions and mean remaining distinct actions are provided. Bound selection cannot cure poor reference generation.

## Contract recommendations and unresolved decisions

Recommend **Contract B, operational-only feasibility mask followed by explicit passenger response**, if the requested Accept/Reject sequence must allow rejection. The unchanged13D state is insufficient for passenger-specific threshold conditioning; it might learn contextual average outcomes, but must not be represented as fully observed. No features or response equation are invented. Contract A remains coherent only if rejection is explicitly structurally redundant.

Seven academic decisions remain: (1) final L_base; (2) denominator resolution/admissibility; (3) negative-e runtime/sign policy; (4) fitted family and support/parameters, including inverse-tail risk; (5) fare bounds; (6) full reference/action/zero branch precedence and semantics; (7) response/state/reward/replay contract. The provisional action values, orientation, fixed P and hybrid generator are honoured, not reopened. See draft contract and response comparison.

## Deliverables and validation

- `V2_FINAL_CALIBRATION_RESULTS.csv`: typed union table; record_type selects population, positive/negative accounting, denominator scenarios, bin support, fare bounds, smoothness, paired reconstruction, independent reference, offers, clipping/collapse and quadrature convergence. Blank fields are not applicable. Currency USD; distance km; percentages0–100. q_lower is a fraction.
- `final_distribution_fit_comparison.csv`:12 exponential fits plus12 empirical comparators; only positive finite retained e fitted. Original sign/zero omission counts retained.
- `negative_e_diagnostics.csv`: grouped negative statistics and six deterministic representative examples/reference; example rows have record_type NEGATIVE_EXAMPLE, grouped rows have empty record_type. N is observed frequency, not quadrature mass.
- `V2_DRAFT_METHOD_CONTRACT.md` and `response_contract_comparison.md`: provisional scope and unresolved choices.

Checks passed: six source hashes match audit and are unchanged; N=6,967,155;12 scenarios and24 fit/comparator rows; formula matches completed e arrays at1e-13; exponential MLE scales equal full positive means; all negative band counts reconcile; no undefined values silently generated; paired inverse identity verified in persisted diagnostics; exact six-file scope. These are focused numerical/document checks, not simulator integration tests. No historical or V1 data changed. No production implementation or training.

Source hashes:
- `src/pricing/passenger_sensitive_v1.py`: `8874b1234f49496721582e43b997532f29bc48768a032be0d971875ce7a65b28`
- `src/simulation/passenger_sensitive_v1.py`: `77e81abaee4c3e4906d778e0858c0cf3ba2b6c811a25f34dc0a0ea7625b2fb30`
- `src/simulation/final_production.py`: `b2cd5371a632e745e1e65dcf9018fa3992942ff2e493caf3ec68b1d422fbaa78`
- `src/dispatch/generation.py`: `ae070a0a2e36341f169e12af98421b0916d9d58bd52ef65b5e61c2a46e3c4abf`
- `src/dispatch/dispatch.py`: `34178812543967eee87b96fa64f637e3d77292c9ad7c2c496b8cd9bcfe70cd62`
- `src/pricing/dqn_contract.py`: `ef9e65e6029ee62504532db9c44fbcb84f5c8f9836056ba0706be01bbcb279ee`
