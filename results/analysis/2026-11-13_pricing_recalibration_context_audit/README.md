# Pricing recalibration — read-only context audit

13 November 2026. **Implementation authorized: NO. Training authorized: NO.** Only the five audit files in this folder are written. No existing code, methodology, results, checkpoint or README is changed. No simulator is instantiated. No March17–31 analytical rows are read; this audit uses saved aggregate tables and the bounded Jan1–Mar15 extreme examples/March16 development export only.

Authority: `notebooks/plan/Passenger Price Sensitivity and NYC Fare Calibration.pdf`, nine pages. Page references below refer to this supplied document, not independently verified meeting recordings. Text and all 148 printed table rows were extracted with pypdf. PDF rendering utilities were unavailable; this is a content/numerical audit, not a visual-layout certification.

## Executive findings

- The current implementation is the frozen V1 request-level masked DQN, not the earlier behavioural-E or time-group runtime described in historical root-README sections.
- Current Record029 epsilon is relative **price / distance** deviation. PDF p3 defines relative **distance / price** deviation. At identical references these are reciprocals when both are defined and nonzero. V1 samples the absolute historical ratio; it does not calculate the new ratio.
- The new reference values also differ. Therefore simply reciprocating the existing positive sampling pool is not a valid recalibration.
- Array a **is reproducible** from existing safe-period artifacts. No raw-data preparation, guessed filter, or protected-period read is needed.
- Final epsilon weighting/population, reference and fare-generation decisions remain open. New distribution fits and action-coverage analysis cannot silently inherit current V1 support or semantics.
- Pricing is coupled to dispatch and routing through price eligibility, successful assignments and operational price statistics. Episode25 is historical evidence, not an exact-resume checkpoint for a changed environment.

## 1. Exact formula and reference audit

Current persisted Record029 formula (`authoritative_epsilon_methodology.json`):

```text
relative_price_deviation = (fare-P_base)/P_base
relative_distance_deviation = (trip_distance-L_base)/L_base
epsilon = relative_price_deviation / relative_distance_deviation
```

P_base=21.34586956773507 USD; L_base=3.01799878914405 source miles =4.856998243316242 km. P_base is the frozen complete cleaned Jan–Mar mean. L_base is the mean of479,000 trips within ±$1 of that price, not an overall distance mean or taxi-meter threshold. Historical reference reuse is an explicit exception; new calibration need not read that full-period population.

PDF p3:

```text
e_i = ((L_i-L_base)/(P_i-P_base))*(P_base/L_base)
    = r_L/r_P
historical epsilon = r_P/r_L
new e * historical epsilon = 1  [same references; r_P != 0 and r_L != 0]
```

V1 `epsilon_c=abs(historical epsilon)` after date/VALID/finite/nonzero filtering and positive truncation. Its reciprocal is `abs(new e)` only under the SAME references and untruncated corresponding observations; sign information is lost. The new 22.3542/4.5 references break a direct old-pool reciprocal equivalence.

Current runtime `maximum_price` uses `P_base+(P_base/epsilon_c)*r_L`. Algebraically solving **new** e=r_L/r_P for price yields that inverse-e expression for nonzero e. Solving the historical ratio for price instead yields `P_base+P_base*epsilon*r_L`. Thus the currently approved behavioural proxy is not an algebraic reconstruction of historical fare; it is a project modelling choice. No code is corrected in this audit.

**RECIPROCAL_ORIENTATION_CONFLICT=YES.** Source direction is explicit; sign/zero/denominator/population/reference choices for migration still require a coherent freeze.

## 2. Array-a provenance and reproducibility

Existing source: `results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_by_distance_0p5km.csv`.
Generator: the same package's `analyze.py::binfare`; `floor(distance_km/0.5)`, arithmetic mean of TLC `fare_amount` renamed `fare`. Source miles are multiplied by1.609344 **before** binning. Underlying historical source is `authoritative_epsilon_jan_mar_2026.parquet`; saved analysis/cache restricts Jan1 <= pickup < Mar16. Fare analysis includes unresolved-epsilon rows. Cleaning: finite positive fare, valid timestamps and0<source distance<=100 miles. No epsilon-support filter selects the fare table.

Selecting existing rows with lower edge1.0 through74.5 gives **[1,75) km**, 148 left-closed/right-open bins, not148 exact distance observations. The PDF's L label is the **lower edge**, while P is the within-bin mean. This representational choice must be kept explicit when calculating e or interpreting L_base as a meter distance.

| Verification | Result |
| --- | --- |
| Saved/PDF bins compared | 148/148 |
| Count mismatches | 0 |
| Total trips | 7,946,921 |
| Weighted sum of fares |177,647,049.04 USD |
| Weighted mean fare |22.354198442390455 USD |
| Maximum printed-vs-saved mean-fare difference |0.0000005 USD (six-decimal printing) |
| Nearest bin lower edge |4.5 km |
| Interpolated lower-edge reference |4.616983790655043 km |
| e mean using PDF rounded P_base 22.3542 |2.313937751408604 |
| e population/sample SD |0.40745062211203814 /0.40883415961494074 |

Using the unrounded weighted P_base instead gives mean2.3139374877441035 and population SD0.40745053855931057. The last displayed digit differs because the PDF explicitly substitutes22.3542. This is rounding sensitivity, not failed reproduction. Exact calibration precision must be frozen. PDF counts/fare precision are reproduced; its printed e values differ by at most about3e-6 when compared with full-precision P_base arithmetic.

**ARRAY_A_REPRODUCIBLE=YES.** Its actual temporal provenance is Jan1–Mar15, not full Jan–Mar. The PDF calls it NYC empirical data without a precise date filter; this audit supplies the recoverable source period.

## 3. Population and zero semantics

| Population option | Implied sampling unit | Consequence |
| --- | --- | --- |
|148 unweighted e values |One equally weighted bin |Sparse long-distance bins have same mass as nearly-million-trip bins; reported mean≈2.313938. |
|148 e values weighted by N_i |Trip-frequency-weighted bin proxy |Preserves bin frequency but assigns a mean-fare-derived proxy to every trip in its bin; diagnostic weighted mean≈1.628232. Not equivalent to raw-trip ratios. |
|Raw trip-level e |Individual paired fare/distance |Preserves within-bin variation; may have negative/undefined/extreme ratios; ratio of means differs from mean of ratios. |

**EPSILON_POPULATION_DEFINITION=ACADEMIC_DECISION_REQUIRED.** PDF pp6–7 says sample independently from a common fitted population, not deterministic lookup by each passenger's distance bin; this does not resolve the weighting population used to fit it.

At L=L_base and P!=P_base the new e is0. If both equal their bases the ratio is0/0, not mathematically0; an explicit convention is required. `if e=0 then price=P_base` is a separate piecewise simulation rule, not a division limit. Current provider and `maximum_price` reject epsilon<=0. Historical Record029 flags abs(L-L_base)<0.005 mile unresolved (9,017 historical rows); it addresses the OLD distance denominator, not the NEW price denominator. V1 then excludes zero before absolute quantiles. Reusing that VALID flag would pre-exclude near-base-distance cases that the new method may wish to retain. Zero mass, price-denominator resolution, negative values and positive-family treatment must be specified rather than inherited.

## 4. Extremes, fitting and cutoff evidence

60 unique saved safe-period extreme examples reproduce historical epsilon from paired fare/distance with max absolute difference2.2737367544323206e-13. Example source row2924115: fare 92.30, distance 3.03miles, epsilon 835.906737; row6678981: fare 121.72,3.03miles,epsilon 1182.502151. At 3.03miles relative-distance deviation is0.0039765459479701995. Small distance denominators plus large price deviations explain these values; the saved examples do not establish a unit error or require a pairing error. Negative signs follow opposite-signed relative deviations. This is not a complete raw duplicate/misalignment audit or proof every source observation is valid.

For a bounded follow-up use source_row_index, timestamps, fare, distance and both deviations in the existing restricted cache/extreme CSV. Historical near-zero/variance tables in the Record029 report explain the resolution effect, but must not be confused with new e's price denominator. Do not reopen full-period raw rows without a safe temporal selection.

Current sampling is `TRUNCATED_EMPIRICAL_RESAMPLING`: global Jan1–Mar15 VALID finite nonzero -> abs -> inclusive P0.5–P99.5 [0.017809913104763053,27.324599740032788], N=8,598,805; replacement preserves duplicates. No extra floor. `sample()` uses max(raw,epsilon_min), an identity for approved support. No Gaussian or fitted-family draw is active.

Existing historical `final_distribution_fit_comparison.csv` compares signed supported T1–T4 truncated normals with empirical quantiles and KS; V1 T0–T3 tables compare empirical truncation only. Neither fits exponential/gamma/lognormal/Weibull/normal to the new population. **DISTRIBUTION_FITTING=ANALYSIS_REQUIRED**; define weighting, zeros, signs and support before likelihood/AIC/BIC or KS interpretation. Estimated-parameter/weighted KS needs appropriate calibration; naive independent-trip significance for duplicated bin proxies is not justified.

Existing bin-table cutoff accounting (NOT applied):

| Candidate range km |Historical Jan1–Mar15 retained N |Excluded below lower bound |Excluded >=75 |
| --- | ---: | ---: | ---: |
|[1,75) |7,946,921 |744,439 |1,459 |
|[1.5,75) |6,967,155 |1,724,205 |1,459 |
|[2,75) |5,974,083 |2,717,277 |1,459 |

In the saved 2,838-request March16 development fixture the respective retained counts are2,511/2,276/1,997;327/562/841 are below the lower bound;none >=75. These are observed fixture effects, not all training requests or new selection criteria. No new stream generated. The runtime January sampler permits nonnegative fare/distance, positive duration, finite fields; it does NOT impose Record029's100-mile cap or1-km floor. Full March training-request impacts require existing persisted per-request logs or a separately authorized accounting pass, not extrapolation from this fixture.

Among array bins, N<50 removes6 bins/247 trips; N<100 removes27 bins/1,665 trips. N<50 edges:68,70.5,71.5,72,74,74.5. The100 threshold would remove61.0 but keep61.5 (N110). A contiguous cutoff is therefore different from dropping individual bins. PDF does not choose semantics or exact endpoint inclusivity.

## 5. Pricing, response and compatibility gates

- No taxi-meter fare floor currently exists. `P_accept=max(.85P_base,P_raw)` is a threshold protection, not `if L<=L_base then fare=P_base`.
- No empirical NYC post-generation clipping exists. The seven offers bound **offers**, not raw/effective preferences; exact NYC bounds remain unresolved (PDF pp7,9). Do not substitute raw $0.01, illustrative $7.52 or highest-bin mean$207.09.
- New PDF gives a workflow but not the complete P_max/reference-fare-to-action equation. `P_action=P_base*alpha` alone does not explain long-distance reference pricing. **PRICE_GENERATION_FORMULA_READY_FOR_IMPLEMENTATION=NO.**
- Seven factors are illustrative in the new PDF; **ACTION_SPACE_FINALIZED=NO** for recalibration (still frozen for historical V1).
- Existing preselection masking differs from select/clip/respond prose. **PASSENGER_RESPONSE_SEQUENCE=ACADEMIC_DECISION_REQUIRED.** Do not infer that the approved utility model or preselection mask is abolished without an explicit response contract.
- Assigned reward is offer; accepted-unmatched0. A selected-and-rejected request is not an implemented branch. Rejection reward/penalty and replay/next-state handling need a decision; do not invent a penalty or silently skip a real selected action.
- **EP25_CHECKPOINT_COMPATIBLE=NO for exact continuation under proposed changed semantics; CONDITIONAL only as an explicitly approved transfer initialization.** Even if13×7 shapes load, replay rewards/masks/states reflect the old environment and cannot be relabelled to reproduce counterfactual future fleet paths. Preserve all historical files; any new method needs a versioned learner/replay policy after approval. Same-method resumption remains a separate authorized task.

## 6. Audit scope and impact inventory

See [CURRENT_ARCHITECTURE.md](CURRENT_ARCHITECTURE.md) for symbols, data flow and reference/action assumptions; [CHANGE_IMPACT_MATRIX.csv](CHANGE_IMPACT_MATRIX.csv) for directive-level classification; [IMPLEMENTATION_PRECONDITIONS.md](IMPLEMENTATION_PRECONDITIONS.md) and [ANALYSIS_NEXT_STEPS.md](ANALYSIS_NEXT_STEPS.md) for ordered gates.

- ACADEMIC_DECISION_REQUIRED: **10**
- ANALYSIS_REQUIRED: **4**
- ARCHITECTURE_CONFLICT: **1**
- BLOCKER: **2**
- IMPLEMENTATION_READY_AFTER_FREEZE: **4**
- NO_CHANGE: **5**

Counts are matrix-row classifications, not independent defects. Two BLOCKER rows are formula/population migration safety and incomplete price generation; open academic choices must also be resolved. No implementation, fitting, simulation, training, checkpoint load or protected-row read performed. Existing saved aggregation checks and read-only source inspection are the validation in this task; no test suite was run.

## Evidence fingerprints

SHA256 of the targeted authority/code/metadata inputs at report creation (verified unchanged after writing):

- `README.md`: `ae2eaf11fc9d50f92abe3767c4e99fe58a968acb4b323a714960dbb67f7646dd`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/README.md`: `3e839d95c9333be6df481156ff3c4d4cbd3bd9f65d815413a534e8da24a13c56`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/METHODOLOGY.md`: `ccc905bf47b4e28e0fca9e59f4736c7159fea353675656908cb6b112bf4256b8`
- `results/analysis/2026-11-09_academic_review_followup_pricing/final_academic_review/FINAL_ACADEMIC_REVIEW.md`: `0f33820f1063d82a736f98a74b246488c3424e67e4c0e731e7c89e0cf8bf8040`
- `results/analysis/2026-11-09_academic_review_followup_pricing/QA_RECONCILIATION.md`: `8461052f5389dc3f5113e391fa582804a5334c7ad08809f5cb413925d5197420`
- `notebooks/plan/Passenger Price Sensitivity and NYC Fare Calibration.pdf`: `6bff09ca3e92acfead77117723b793cc594861d5b08274b15533d4e5aa2f7540`
- `src/pricing/passenger_sensitive_v1.py`: `8874b1234f49496721582e43b997532f29bc48768a032be0d971875ce7a65b28`
- `src/simulation/passenger_sensitive_v1.py`: `77e81abaee4c3e4906d778e0858c0cf3ba2b6c811a25f34dc0a0ea7625b2fb30`
- `src/simulation/final_production.py`: `b2cd5371a632e745e1e65dcf9018fa3992942ff2e493caf3ec68b1d422fbaa78`
- `src/dispatch/generation.py`: `ae070a0a2e36341f169e12af98421b0916d9d58bd52ef65b5e61c2a46e3c4abf`
- `src/dispatch/dispatch.py`: `34178812543967eee87b96fa64f637e3d77292c9ad7c2c496b8cd9bcfe70cd62`
- `src/pricing/dqn_contract.py`: `ef9e65e6029ee62504532db9c44fbcb84f5c8f9836056ba0706be01bbcb279ee`
- `src/rl/passenger_sensitive_dqn.py`: `45aa0d662db00b60513b5598afb3fb00648866b1da5cd7e1cac889d05cf18f1c`
- `src/rl/pricing_dqn.py`: `37ad0f29996e02ff6110514fe70657f8c08fea3ea503fb3ea1bf4dc3dbbc402d`
- `src/routing/configuration.py`: `8607bdfdce35ae5799bc726211338ab3f11c93ff9be784282aa86034032669c1`
- `src/routing/operational_interface.py`: `800b2826cf4b5e38ddca98106c9cd14050bf142589abf387671379a983be6e81`
- `src/routing/final_state.py`: `5db2dbd8528cbdfadf87d697484f0fb9911e8d4ad81b5cf38ec58aad605749b4`
- `src/simulation/operational_state.py`: `38d803b200a07d78022abc720c9fe955abaeb7b1f53a20c371bb2f038c905e39`
- `src/simulation/temporal_protocol.py`: `146386da67be82b9699d4b928a044c7bab096ac1ec26212d69b5f3250ed059e1`
- `config/final_temporal_protocol.json`: `0ac51d6ce0a07d020aafa4dc94d8c3c5bd2f9eccebdddb55a5b4081391cb6fac`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/run_staged.py`: `16f3034a2956a82cde2250e3d2d49ada70c9a407021005356a4badf0122aa2dd`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/restricted_calibration_support.json`: `e3ea9eeca5981aaae0516b91ced3ca5e2fa5e140e6f84134a20561b67ec3b1b8`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/pricing_v1_spec.json`: `a1f5ba36f388475cd0911d23b148f2b6ca1f11a26cd1e6a68daf93105b7b6ff3`
- `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/analyze_review.py`: `222c746a918174e034db6415d1a53eb68397e513fecb92c06238889995ea0902`
- `results/analysis/2026-11-09_academic_review_followup_pricing/analyze.py`: `425de78db212408ebe9fcd21cbff321c983df6c5b22626322aeebd8e89cef051`
- `results/analysis/2026-11-09_academic_review_followup_pricing/fare_distance/fare_by_distance_0p5km.csv`: `cb00116863f8cd0691bed8ec35a2c8c48a6fd466e5efa51b03811e3e56dd6811`
- `results/analysis/2026-11-09_academic_review_followup_pricing/sensitivity_distribution/epsilon_extreme_examples.csv`: `ab0517469446076a80d1e01c7c432198db16e377b0fa8323780c19aba8102c78`
- `data/processed/price_distance_sensitivity_record029/authoritative_epsilon_methodology.json`: `0d83b9a63f4a9b7ee75bb95133db183f9deb34fd9ee73addb15de08dfa55ddd7`
- `data/processed/price_distance_sensitivity_record029/cleaning_summary.json`: `1a8d0e64ed88b86df986f70f3194df1cc248e1563963719080273ce469f35f8a`
