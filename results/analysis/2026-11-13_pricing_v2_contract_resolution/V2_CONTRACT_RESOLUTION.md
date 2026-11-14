# V2 contract-resolution decision record

Analysis only. No production change, sampler implementation, model load or training. Provisional references are retained for this comparison, not promoted to an operational tariff.

## READY TO FREEZE

- For this analysis, orientation e=r_L/r_P and individual paired Jan1–Mar15 population;1.5<=L<75 km. P_norm=22.354198442390455 USD, provisional reference distance4.616983790655043 km. N>=100 remains a bin diagnostic criterion, not passenger exclusion. Physical OD/distance/duration stay intact.
- Distinguish normalization P_norm from operational P_floor. Do not set P_floor=P_norm. Distinguish reference L_base from taxi-meter flat-fare distance.
- Retain current hybrid generator: CNN forecast → origin counts → intact empirical trip sampling → independent sensitivity assignment → pricing. No Array-a independent distance draw.
- Seven provisional factors remain0.85/0.90/0.95/1/1.05/1.10/1.15 multiplying a subsequently approved P_ref. Existing V1 action semantics are not overwritten.
- Zero numerator/nonzero denominator gives e0; zero denominator undefined. No silent reference fare for undefined values. Signed negatives retained for diagnostics; no automatic abs.
- Contract B sequence: state → operationally feasible actions → mask → select → passenger response → reward. Feasible means valid action index, finite generated fare, and approved hard fare/operational constraints once frozen. **Passenger acceptance threshold must not be used in the preselection mask when rejection is intended.** These are coherent contract definitions, not approval of an unspecified response model.

## REQUIRES ACADEMIC DECISION

Six grouped decisions remain:
1. **Sensitivity admissibility/sign policy:** price-denominator resolution and negative/zero runtime treatment. Price-gap exclusions do not solve the independently sampled small-e tail.
2. **Fitted sensitivity law/support:** lognormal has best AIC across all scenarios and finite inverse moments, but material lower-tail and quantile mismatch. No family recommended for freeze. Approve tail fidelity/validation requirements without selecting a cutoff to optimize likelihood.
3. **Reference-price architecture:** R1 floor empirically unsupported as normalization-price floor; R2 improves medians but permits negative prices; R3 adjustment unspecified. Specify complete distance/sensitivity/reference equation, independent pairing assumptions, zero branch and alpha precedence. No viable full-range contract established.
4. **Operational floor and bounds:** establish P_floor from appropriate evidence, separately from P_norm; select empirical bounds only after reference model. Existing quantiles are diagnostics, not statutory fare claims.
5. **Passenger response and observable information:** specify response function and minimally sufficient information classes. Exact features/dimensions remain unselected.
6. **Rejection learning semantics:** reward for rejected offer and whether rejection creates replay transition require explicit freeze; choose no penalty here. Rejection bypasses dispatch and causes no assignment-related fleet movement or passenger commitments. Exogenous vehicle/charging time evolution may still continue; “fleet unchanged” means no rejection-induced assignment, not freezing the world. Operational successful-fare statistics are not updated for rejected offers unless explicitly specified otherwise. Next state remains the next chronological actionable request; define rejection recording, reward attribution, timing/discount and bootstrap mask consistently.

### Passenger-information classes, redundancy and limits

| Class | What it enables | Redundancy / what remains missing |
|---|---|---|
| Sensitivity e | Passenger-specific heterogeneity if response uses e | Alone lacks distance/reference/actual dollar offers; together with actual distance and fixed formula determines P_ref |
| Actual distance / relative distance | Position relative to reference and physical trip context | Alone cannot determine reference or willingness without e; physical distance not replaced by fare-effective distance |
| P_ref / candidate dollar offers | Lets action index condition on its actual price scale | Given fixed alphas, one P_ref determines all seven offers; redundant with e+distance under fixed formula, but not necessarily sufficient for response |
| Acceptance threshold normalized to P_ref (if threshold response approved) | Direct comparison alpha against passenger tolerance | Sufficient for deterministic threshold acceptability given fixed actions; not sufficient for revenue scale unless P_ref also known; threshold may summarize e/distance for response but no such formula yet approved |
| Response parameters or sufficient response statistic | Conditions stochastic utility/acceptance if chosen | Required instead of assuming an unapproved deterministic threshold; equivalence to e/threshold depends on final response law |
| Combined reference scale + response-relevant statistic | Candidate minimal information classes for price/revenue and passenger response | Potentially compresses e/distance; do not select exact features or claim whole-simulator Markov sufficiency from these alone |

Current13D contains demand, prior dispatch, incoming commitments, routing probabilities and destination popularity—not e, distance, P_ref, dollar-offer vector or threshold. **UNCHANGED_13D_SUFFICIENT=NO** for passenger-specific price conditioning under Contract B. Contextual-average policies remain possible but are partially observed. Mask information must not covertly reintroduce deterministic passenger acceptance.

## REJECTED BY EMPIRICAL EVIDENCE

- P_NORM_EQUALS_OPERATIONAL_FLOOR=NOT_SUPPORTED: R1 short-band median overpricing$3.95–$12.35.
- R1 as currently calibrated full-range empirical reference: not supported; positive long-distance bias remains even with lognormal.
- R2 as ready unbounded positive fare mechanism: not supported; baseline lognormal yields≈19.94% negative references at1.5–2 km and material long-distance bias.
- Exponential as unbounded inverse-price sensitivity law: divergent E[1/e]. Gamma/Weibull safety is shape-conditional; normal baseline has invalid nonpositive support and undefined reciprocal expectation.
- Lowest AIC or finite inverse moment alone as freeze justification. Lognormal is comparative leader, not validated final family.
- Clipping as a repair for structurally miscalibrated reference prices. No clipping performed.

## STILL UNSPECIFIED IN SOURCE

- R3_FORMULA=UNSPECIFIED: the source does not define an empirical distance-fare baseline plus sensitivity adjustment. No equation supplied here.
- P_FLOOR=UNRESOLVED; L_BASE_EQUALS_TAXI_METER_THRESHOLD=UNRESOLVED. No legal minimum inferred from historical fare_amount quantiles.
- Complete passenger response function, sufficient observable context and rejection reward/replay decisions.
- Approved final fitted family/support/parameters and final fare limits.

The given R1/R2 expressions are evaluated, not silently replaced. Signed paired inverse reconstruction passes to≈1.14e−13 USD, but independent sensitivity assignment is a different synthetic joint model. Its empirical adequacy must precede pricing training. Any changed V2 semantics require separately authorized fresh learner/replay; Episode25 untouched.

Implementation performed NO. Training performed NO. Protected analytical rows accessed NO.
