# Passenger Pricing V2 frozen methodology — controlled draft

Status: **PARTIALLY_FROZEN — NOT AN IMPLEMENTABLE FINAL SPECIFICATION**. Authoritative for the explicitly frozen components below. Every unresolved runtime/configuration value is `PENDING_APPROVAL`; candidate values are evidence only and appear in the approval sheet. No production or training authorization.

## Frozen contract inventory (18 items)

| ID | Contract | Frozen specification |
|---|---|---|
| F01 | Semantic weather membership | NON_PRECIPITATION={1,2,3,5}; RAIN={7,8,9,17}; SNOW_FROZEN={12,13,14,15,16,21} |
| F02 | Time taxonomy | T1=[00,04); T2=[04,06); T3=[06,16); T4=[16,24) |
| F03 | Scenario structure | Exactly 12 weather×time scenarios; simulator slots remain 30 minutes |
| F04 | Support gate | 5000 valid positive observations |
| F05 | Fallback hierarchy | weather×time → weather-only → time-only → global; no synthetic balancing |
| F06 | Current sparse-scenario routes | RAIN_T2→RAIN_ALL; SNOW_FROZEN_T2→SNOW_FROZEN_ALL; recalibration may require recounts |
| F07 | Proactive timing | Generate destination pricing schedule before requests arrive each slot |
| F08 | Offer formula | P_offer=alpha*P_base; not alpha*P_ref or alpha*P_max |
| F09 | Passenger ceiling and acceptance expression | P_max=P_base+(P_base/e)*((L-L_base)/L_base); accept iff offer<=ceiling, subject to unresolved runtime admissibility |
| F10 | Response ordering | Response after offer; no passenger-willingness preselection mask |
| F11 | Rejected outcome | No dispatch; zero reward contribution; no rejection penalty |
| F12 | Assigned outcome | Successfully dispatched request contributes P_offer |
| F13 | Request generator | CURRENT_HYBRID: CNN next-slot counts → intact empirical OD/distance/duration → sensitivity → precomputed destination factor |
| F14 | Epsilon orientation | Trip-level e=r_L/r_P; no automatic abs |
| F15 | Diagnostic sign and zero semantics | Negative retained; zero numerator/nonzero denominator gives zero; zero denominator undefined; near-zero flagged without silent exclusion |
| F16 | DQN information boundary | System information only; no passenger-specific epsilon/distance/ceiling inputs |
| F17 | Learning granularity | Slot-level state/schedule/outcome/next-state transition; no request-level replay |
| F18 | Fresh learner and preservation | Fresh V2 learner/replay; Episode25 and V1 replay not resumable; historical artifacts preserved |

Required flags:

- WEATHER_GROUPS_DEFINED_SEMANTICALLY=YES
- ELASTICITY_CLUSTERING_DETERMINES_WEATHER_GROUP=NO
- WEATHER_TAXONOMY_FROZEN=YES
- V2_TIME_TAXONOMY=T1_T4
- REQUEST_GENERATOR_V2=CURRENT_HYBRID
- FRESH_V2_LEARNER_REQUIRED=YES; FRESH_V2_REPLAY_REQUIRED=YES

## Calibration and sampling contract

Use individual paired trips from Jan1–Mar15, with 1.5≤distance<75 km for the current V2 calibration. Source miles are converted consistently to km. Do not use old r_P/r_L, abs transformation, or V1/T0 support. Diagnostic negative observations remain retained; zero numerator with nonzero denominator gives e=0, while zero denominator is undefined. Near-zero price denominator remains flagged; the existing diagnostic flag |r_P|<0.001 is not a runtime exclusion or floor.

All 12 scenario IDs are the Cartesian product of NON_PRECIPITATION/RAIN/SNOW_FROZEN and T1/T2/T3/T4. Existing candidate-reference evidence: 6,967,155 observations; 5,975,653 positive; 991,502 negative; zero=undefined=0. Ten direct pools pass 5,000 positives. RAIN_T2 has 3,702 positives and routes to RAIN_ALL; SNOW_FROZEN_T2 has 4,891 and routes to SNOW_FROZEN_ALL. Direct-fit eligibility covers 99.8492498% of trips. Counts/fits are conditional on the existing references; changing references can change support counts without changing the frozen threshold/hierarchy.

| Required value | Specification | Approval dependency |
|---|---|---|
| P_base value and reference population | PENDING_APPROVAL | Q1 |
| L_base value and construction | PENDING_APPROVAL | Q1 |
| Runtime admissible sign/support domain | PENDING_APPROVAL | Q2 |
| Runtime e=0/invalid/nonfinite handling | PENDING_APPROVAL | Q2 |
| Runtime near-zero/inverse sensitivity safeguards | PENDING_APPROVAL | Q2 |
| Per-scenario family and parameters | PENDING_APPROVAL | Q3, Q1/Q2 compatibility |
| Fallback-pool family and parameters | PENDING_APPROVAL | Q3 |
| Fitted support/tail adequacy | PENDING_APPROVAL | Q2/Q3 |

L_base is a sensitivity/reference distance, not a taxi-meter/flat-fare threshold. No such equivalence or tariff rule is created. No automatic abs, invalid-draw retry, clipping, positive floor, accepted-threshold clamp or historical empirical truncation is introduced.

The existing lognormal AIC lead is not approval: P99 underfit 38.56–58.86%; gamma inverse moments diverge; normal fits reach optimization bounds. No distribution is currently approved for any of the twelve runtime scenarios, including weather-only fallback.

## Proactive offer and response

Before every 30-minute slot generate a destination pricing schedule using system information available at the boundary. Hybrid requests preserve OD/distance/duration. Assign sensitivity, apply precomputed factor, compute `P_offer=alpha*P_base` and the frozen passenger ceiling expression, then accept iff offer≤ceiling subject to approved runtime admissibility. No alpha×P_ref, alpha×P_max, or willingness-preselection mask. Passenger distance/e/ceiling are not direct DQN state inputs. Rejection gives no dispatch and zero contribution; successful assignment contributes the offer.

| Required value | Specification |
|---|---|
| Empirical simulation price bounds | PENDING_APPROVAL (Q4) |
| Alpha endpoints | PENDING_APPROVAL; derived as approved bounds/P_base |
| Action count and factors | PENDING_APPROVAL (Q4; existing 11-point proposal ENGINEERING_READY) |
| Hard-bound numerical tolerance | PENDING_APPROVAL (Q4 implementation contract) |
| Destination sharing/query architecture | PENDING_APPROVAL (Q5) |

The proposed $6.60–$94.70 interval is empirical, not legal/statutory NYC pricing. Historical seven actions are superseded as the V2 proposal. No alternative action count is invented. Candidate alpha endpoints remain 0.2952465514–4.2363406697 under the existing P_base; recompute algebraically only after reference approval if it changes.

## Exact state and architecture

Current 13D V1 state: SUPERSEDED for V2. Final state dimension, scaling, sources and shared network layers: **PENDING_APPROVAL (Q5)**.

Existing proposal retained without redesign: 142×15 system entries: predicted demand(1), supply(1), known passenger arrivals(1), smoothed successful dispatch history(1), routing probabilities(9), drop-off probability(1), destination popularity(1). Exact IDLE/charging eligibility, next-slot arrivals and F_hat×30 interpretation require approval. Passenger features are excluded.

The old 2146 system width assumed 14 raw weather categories and is no longer valid for the semantic-category proposal. **Conditional arithmetic only**: retaining the existing cyclic time encoding (2) and replacing that one-hot with three semantic groups gives 2130+3+2=2135; adding the existing 142-destination query identity gives 2277. Final dimension remains PENDING_APPROVAL; this is not automatic adoption of optional weather/time state features. Four sensitivity time groups do not require a four-way DQN time encoding.

Proposed shared q_theta(S,d,k) yields [batch,142,11] under the proposed K. All 142 factors precede requests. No K^142 monolithic output; no 142 independent learners. Exact factorization and source scopes remain Q5/Q6 approvals.

## Objective, credit and transitions

Rejected contribution=0 and assigned contribution=P_offer are frozen. Accepted-unmatched contribution=PENDING_APPROVAL (Q6; proposed zero). Slot aggregation=PENDING_APPROVAL (Q6; existing sum of successfully assigned fares). Empty-slot transition/reward convention=PENDING_APPROVAL. Destination credit-assignment=PENDING_APPROVAL.

The existing mechanism is **one global slot reward in one additive joint-value loss**, Q_total(S,A)=sum_d q_theta(S,d,a_d). It is not 142 separately labelled transitions each receiving the global reward, and is not destination-specific revenue supervision. Per-destination counters are audits, not reward labels. Shared fleet coupling makes additive decomposition an approximation requiring approval. Do not silently substitute another mechanism.

Frozen learning unit: slot transition (S_t,A_t,R_t,S_next), where S_t precedes the slot, A_t is the entire schedule, and S_next reflects the completed slot. Reward aggregation, target details, operational next-mask and done/truncation treatment remain PENDING_APPROVAL. True terminal versus artificial truncation and episode boundary definitions must be explicit; no fabricated terminal convention.

Gamma=PENDING_APPROVAL (Q6). Existing candidate 0.99 **per 30 minutes** has approximately 34.48-hour discount half-life; it is not a request-step setting. No tuning or expanded hyperparameter choices are made.

## Drop-off producer

Historical initialization and moving-average update principle comes from professor clarification. Exact global/conditional vector scope, update equation, lambda, initialization window and normalization tolerance=PENDING_APPROVAL (Q7). Existing candidate is global completed-drop-off EWMA with lambda=0.30, completed-slot causal updates and empty-slot carry-forward. Lambda is READY_TO_FREEZE as evidence, not yet frozen by authority.

Safe-period validation used Jan1–7 initialization, warm-up to March, and chronological Mar1–15 evaluation. That evidence does not authorize using Jan1–7 outcomes to initialize a simulated Jan1 training state. A causally valid production initialization window must be specified rather than silently transferred from the validation design.

## Preservation and completion gate

CNN, routing, 142-grid environment, current hybrid generator and historical V1 artifacts remain unchanged. Episode25 cannot resume under new semantics; fresh learner and replay are required. No protected March17–31 analytical data is used. No checkpoints/replay touched.

Final specification readiness=NO. Implementation authorized=NO. Training authorized=NO. Resolve Q1–Q7 with subitems explicit, update affected reference-dependent evidence only if subsequently authorized, then finalize this document. Any later implementation/testing/training is a separate task; this draft launches none.

## Evidence and authority

Authority order: latest professor clarification → explicit user-approved decisions → calibration evidence → current architecture → historical V1 provenance. Current user instructions freeze semantic grouping, T1–T4, minimum support and fallback; earlier readiness labels do not override those approvals.

Sources (existing artifacts only):
- `notebooks/plan/Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx`: proactive timing, offer/ceiling expressions, system-only inputs, response/reward semantics, moving-average guidance; aggregation remains unspecified.
- `notebooks/plan/Price_Elasticity_Weather_Scenario_Analysis_Explained.docx`: scenario-first descriptive analysis and correct pooled variance. Explicit later semantic decision supersedes clustering for membership.
- `results/analysis/2026-11-13_pricing_v2_weather_time_final/`: verified mapping, all counts and 36 fit comparisons.
- `results/analysis/2026-11-13_pricing_v2_final_freeze_check/`: current reference evidence and outstanding proposals.
- `results/analysis/2026-11-13_pricing_v2_latest_clarification/REMAINING_NUMERICAL_FREEZES.md`: state/source, runtime validity, terminal and drop-off producer dependencies not resolved by scalar proposals.
- `results/analysis/2026-11-13_pricing_v2_freeze_design/V2_SLOT_DQN_DESIGN.md` and `V2_NUMERICAL_FREEZE.md`: existing factorized architecture and numerical recommendations; no redesign.
- `results/analysis/2026-11-13_pricing_recalibration_context_audit/README.md`: distance/reference distinctions and old-orientation provenance.

No numerical analysis, model loading, training, simulation or protected-period analytical access was performed for this package.
