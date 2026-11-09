# Current-State Hierarchical RL Implementation Review

## Passenger-Sensitive Pricing V1 — Current Authoritative State

The implemented and validated V1 methodology is frozen. The authoritative fresh sequence is **staged_training_002**, completed through Episode25, with technical invariants PASS. Numerical stability and a learning signal are observed; policy stability is **NO**, convergence **NO**, action-dominance risk **HIGH**, and DQN incremental dynamic value **UNRESOLVED**. Further training is **AWAITING_ACADEMIC_REVIEW**, not authorized. No Episode100 run is approved. A possible continuation with the highest-feasible baseline as a permanent comparator is **PROPOSED_NOT_AUTHORIZED**. March17–31 remains untouched.

`PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

| Academic-review feedback | Resolution in V1 |
| --- | --- |
| Overall formulation/document acceptable | Consolidated framework retained, with explicit project implementation decisions. |
| Section V must explain sensitivity distribution, random sampling and truncation; truncation need not be symmetric | Signed, absolute and supported distributions documented; T0–T3 comparison includes asymmetric probability cuts; empirical row resampling specified. |
| Negative sensitivity may occur; absolute values acceptable | Historical signed observations preserved; V1 uses positive sensitivity magnitude after date/VALID filtering. |
| Effective preference should use max(NYC minimum price, passenger-preference expression) | Project operationalizes platform minimum as 0.85×P_base and P_accept_c=max(platform minimum,P_raw_c); this is not a verified statutory NYC minimum. |
| Pricing factors need dataset justification | Coverage and distance-conditioned evidence reported; MODERATE justification for a bounded experiment, not unique optimal endpoints. |

`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED = NO`  
`V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION = YES`

The available consolidated formulation contains the P_base-scaled adjustment. The review accepted the overall document, but equation numbering cannot be mapped unambiguously across historical documents. An explicit project decision resolves the intended expression; it does not verify the equation number.

Calibration is restricted to **Jan1–Mar15**, using VALID finite nonzero historical observations. First compute `epsilon_proxy_raw = abs(epsilon_Record029)`, then calculate inclusive empirical P0.5–P99.5 on that positive distribution. **V1_POSITIVE_EPSILON_CALIBRATION_SUPPORT = [0.017809913104763053, 27.324599740032788]**. Retained N=**8,598,805**, **99.001979%**. `RECORD029_HISTORICAL_SUPPORT` is a separate, signed historical support and is unchanged.

Underlying signed N=8,685,488; mean 0.640621, population SD 7.106335; negative share 11.734355%. Absolute proxy before truncation: mean 1.414638, population SD 6.993510, median 0.820126. Supported positive population: mean 1.095299, population SD 1.817300, median 0.820123. These are calibration proxies derived from completed trips, not empirically identified causal willingness-to-pay elasticities.

```text
P_base = 21.34586956773507 USD
L_base = 4.856998243316242 km
L_gg_prime = actual passenger OD distance in km
P_raw_c = P_base + (P_base / epsilon_c) * ((L_gg_prime - L_base) / L_base)
P_platform_min = 0.85 * P_base
P_platform_max = 1.15 * P_base
P_accept_c = max(P_platform_min, P_raw_c)
P_offer = a * P_base
feasible action: P_offer <= P_accept_c
```

P_raw_c is raw passenger preference; P_accept_c is the effective passenger acceptance threshold. Historical Pc/Pmax names are aliases only in their dated source context, not competing active formulas. The upper offer bound is enforced by the largest configured action, 1.15; P_raw_c/P_accept_c are not upper-clipped. The expression lacking the P_base adjustment multiplier is **SUPERSEDED_HISTORICAL_FORMULATION**.

The former condition `P_offer <= P_raw_c` produced **61.746289%** no-feasible/no-offer outcomes: **SUPERSEDED_RAW_THRESHOLD_DIAGNOSTIC**. Under `P_offer <= max(0.85*P_base,P_raw_c)`, valid-request no-feasible rate is **0%**, by construction because the minimum arm remains feasible. This is not evidence of improved real-world demand. No post-selection clipping is performed. `d_min = NOT_USED`; no deterministic minimum-distance fare rule is active.

Actions remain **[0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]**. Dataset justification is **MODERATE**. Coverage of observed fare/P_base in 0.85–1.15 is **14.379973%**, measured on all 8,692,819 cleaned **Jan1–Mar15** fares in the saved factor study—not March16 development requests and not only supported epsilon rows. This period distinction avoids mislabelling “development-fare coverage.” Distance-band evidence uses km after converting historical miles. Exact endpoints and 5% spacing are project design choices; neither empirical optimization nor a full-market fare envelope is claimed.

One decision and one replay transition per **individual actionable passenger request**. The network remains **13→64→64→7**. State indices are 0 J_hat; 1 J_disp_prev; 2 incoming commitments I; 3–11 routing probabilities STAY,N,NE,E,SE,S,SW,W,NW; 12 destination popularity. Passenger sensitivity, distance, P_raw_c and P_accept_c affect the **action mask only**, not appended state features. No explicit time-to-terminal field is added.

Masks apply before exploration, greedy selection and Bellman target maximization. There is no synthetic eighth action or post-selection clipping. An empty mask remains a defensive invariant/data-quality path, not normal valid-input behavior.

The next state is the next chronological actionable request, not the next 30-minute slot. Intervening non-actionable cases are not fake DQN actions. A no-action request creates no transition. Assigned reward is successful assignment-time gross **P_offer**; accepted but unmatched reward is **0**. Terminal target is reward only; nonterminal target is `r + 0.99 * max_masked_Q_target(next_state)`.

Gamma is **0.99 PER ACTIONABLE REQUEST TRANSITION**, including same-timestamp requests. Elapsed time may be retained as diagnostic metadata but has no target/replay-weight effect. `GAMMA_VALUE_CHANGED = NO`; `GAMMA_APPLICATION_SEMANTICS_CHANGED = YES`. Adam learning rate 0.001, Huber loss, batch64, replay100000, warmup1000, tau0.005 and seed42 remain frozen. Exactly eight updates occur per completed warm 30-minute slot. Exploration decays from1.0 to0.05 over50,000 optimizer updates, not requests. Training is March1–15; March16 is fixed greedy development only; March17–31 is protected.

The superseded rule `gamma_eff = 0.99^(delta_t_minutes/30)` was mathematically consistent with elapsed-time-discounted total revenue, but inappropriate for the intended request-step representation. In the saved 37,111-request episode, median gap=1 second; 44.127% of discounts equal1 and 100% are ≥0.9999. Old full-trajectory mean/median returns were **$315,510.19/$322,877.32**, with remaining-request/time correlations **0.998324/0.998274**. The 13D state omitted time-to-terminal and the eight-hour boundary was artificial: **HORIZON_ALIASING_RISK=HIGH**.

Applying the unchanged gamma value once per request gave offline mean/median **$1,725.83/$1,799.28**, with correlations **−0.478167/−0.466432**. Weight falls below50%/10%/5%/1% after **69/230/299/459 requests**. The 1% horizon corresponds to approximately **5.94 minutes** at observed average intensity; terminal exposure is **1.23683%**. Assessment **SUPPORTED**. Remaining correlation and artificial-terminal effects are reduced, not eliminated. The limited residual truncation exposure justified retaining 13D and existing terminal semantics in this correction. This is a change in gamma application, not gamma-value tuning or proof of full Markov sufficiency.

### Staged training results

| episode | requests | assignments | assignment_rate | revenue | forced_rate | choice_rate | replay_size | optimizer_updates | exploration_epsilon |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 37111 | 33528 | 0.903452 | 642375.127717 | 0.658403 | 0.341597 | 37111 | 128 | 0.997568 |
| 10 | 39488 | 31657 | 0.801687 | 606587.710093 | 0.677320 | 0.322680 | 100000 | 1280 | 0.975680 |
| 25 | 51654 | 22536 | 0.436288 | 435187.848519 | 0.713536 | 0.286464 | 100000 | 3200 | 0.939200 |

| episode | mean_abs_Q | max_abs_Q | mean_abs_TD | mean_loss | MC_return_mean | MC_return_median | Q_MC_MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4.127954 | 39.370998 | 20.916428 | 24.332136 | 1723.784417 | 1797.625861 | 1725.698279 |
| 10 | 55.037945 | 130.933395 | 11.201169 | 8.368096 | 1528.837823 | 1561.104082 | 1479.369087 |
| 25 | 138.293045 | 196.008087 | 12.567836 | 13.262941 | 838.012691 | 841.808621 | 722.323343 |

### Fixed March16 results

| episode | requests_seen | assignments | assignment_rate | revenue | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2838 | 2767 | 0.974982 | 54330.574517 | 19.616313 | 0.450669 | 0.549331 | 3.107260 | 33.486538 |
| 10 | 2838 | 2792 | 0.983791 | 56855.790887 | 20.328218 | 0.450669 | 0.549331 | 58.999302 | 104.065437 |
| 25 | 2838 | 2786 | 0.981677 | 56419.267854 | 20.220285 | 0.450669 | 0.549331 | 147.337677 | 199.559387 |

The fixed March16 fixture has2,838 requests, environment/sensitivity seed424242, 00:00–02:00, greedy actions and unchanged learner fingerprints. Episode10→25 revenue fell **$56,855.79→$56,419.27** (approximately−0.77%); assignments2792→2786 and assignment rate decreased approximately0.21 percentage points. Episode25 is not an improvement over Episode10. Training episodes have different source dates/conditions: their assignment rates are not a controlled comparison.

No development replay writes, optimizer/target mutation, epsilon decay or training-RNG mutation occurred. This is a reused development fixture, not final held-out evaluation. March17–31 remains untouched.

Stage-summary Q columns are **bounded replay-probe statistics**; episode-summary/live-status Q columns can be trajectory probes and differ legitimately (for example Episode10 55.037945 versus54.595501). Use stage_summary.csv for the tables here. MC calibration uses512 deterministic trajectory positions with full realized returns; it is not the mean across every request. Thus fresh Episode1 MC1723.784417/1797.625861 differs from the old-trajectory offline correction1725.825875/1799.281877 without contradiction.

Q magnitude rose and Episode1→10 TD/loss declined. By Episode25, Q is closer in scale but remains below realized returns: training mean selected Q116.199814 versus MC838.012691; development mean/median selected Q147.064789/153.370972 versus MC1916.483886/1991.282060, correlation0.002390. This indicates incomplete value calibration, not divergence. Episode10→25 TD rose11.201169→12.567836 and loss8.368096→13.262941. The current review describes **Q_SCALE_TREND=APPROACHING_RETURN_SCALE** and **LEARNING_SIGNAL=YES** across the staged sequence, without claiming monotonic improvement or calibrated Q.

### Action dominance and baseline comparison

All1,279 choice requests and23,179 feasible-arm pairs were checked at DQN pre-dispatch fleet snapshots; the four sequential policies each used the same2,838-request March16 fixture. Greedy selected highest feasible in12.35%, one below in78.58%, and at least two below in9.07%. Passenger acceptance is preserved for feasible arms; driver eligibility weakly expands with price; immediate reward strictly rises conditional on the same successful assignment.

All feasible arms select the same assigned driver in45.97% of choice requests; assignment or driver changes occur in53.87%. **Long-term strict dominance is not established**, even for the same driver: fares update operational price estimates feeding routing, while changed assignments alter vehicle trajectories and future supply. The frozen-fleet counterfactual is distinct from a sequential policy run. Highest-feasible earned **$1,597.74 more** and made **8 more assignments** than Episode25 DQN (about+2.8% revenue). All baselines had zero feasibility violations and conserved the fleet. This supports **HIGH** dominance risk, not universal dominance or proof that DQN can never add value.

| policy | assignments | revenue | mean_offered_fare | mean_assigned_fare | driver_unmatched | passenger_feasibility_violations |
| --- | --- | --- | --- | --- | --- | --- |
| DQN | 2786 | 56419.267854 | 20.220285 | 20.250993 | 52 | 0 |
| HIGHEST_FEASIBLE | 2794 | 58017.006192 | 20.724974 | 20.764855 | 44 | 0 |
| LOWEST_FEASIBLE | 2688 | 48771.042788 | 18.143989 | 18.143989 | 150 | 0 |
| NEUTRAL_1_OR_LOWER | 2747 | 53672.054441 | 19.515901 | 19.538425 | 91 | 0 |

### Review interpretation and unresolved question

**Interpretation/provenance distinction:** these are the current review classifications explicitly requested for this consolidation, not a new numerical analysis. The earlier automated `episode25_review.json` recorded Q_SCALE_TREND, LEARNING_SIGNAL and POLICY_STABLE as UNCLEAR. Those provisional classifications are **SUPERSEDED** by this current review interpretation; the JSON remains unchanged. “POLICY_STABLE=NO” means stability has not been demonstrated by the observed fixed-fixture policy/results, not a significance-tested claim. Exact Episode10→25 request-level action-change percentages were not recoverable because Episode10 did not persist those actions. No missing evidence is invented.

1. Is positive absolute sensitivity with empirical truncation/resampling an acceptable behavioural proxy, given the absence of observed rejected-offer response labels?
2. Is `max(platform minimum, P_raw_c)` an acceptable effective passenger acceptance threshold, including its guaranteed minimum feasible arm?
3. Is the fixed0.85–1.15 factor set acceptable with moderate dataset justification and limited fare coverage?
4. Is gamma0.99 per request the preferred interpretation after moving the decision boundary to individual requests, given its request-intensity-dependent elapsed horizon?
5. With highest-feasible outperforming Episode25 DQN on March16, should longer training proceed first, should reward/environment structure be reconsidered, or should highest-feasible become a formal benchmark?
6. What evidence—across controlled fixtures, uncertainty and operational tradeoffs—should be required before claiming nontrivial DQN dynamic value?

These are questions for academic review, not decisions or authorization for another run.

[V1 hub](../2026-11-07_passenger_sensitive_pricing_v1/README.md) · [Methodology](../2026-11-07_passenger_sensitive_pricing_v1/METHODOLOGY.md) · [Academic review summary](../2026-11-07_passenger_sensitive_pricing_v1/ACADEMIC_REVIEW_SUMMARY.md) · [Feedback reconciliation](../2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/README.md) · [Bellman correction](../2026-11-07_passenger_sensitive_pricing_v1/bellman_discount_correction/README.md) · [Authoritative staged training](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/README.md) · [Action dominance](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/action_dominance_diagnostic/README.md)

<details>
<summary>Historical review record — superseded pricing results and provisional decisions</summary>

The following dated content is preserved verbatim as provenance. Statements that V1 was blocked, uncalibrated, untrained, detached/running, time-aware, or awaiting earlier decisions are SUPERSEDED by the current section. Historical pre-reformulation Episode25 is not corrected V1 Episode25. Other subsystem results are not re-audited here.


## 1. Review Scope

**PRICING_REVIEW_CUTOFF = EPISODE_25**. Reporting/consolidation only, from saved artifacts. No training, simulation, checkpoint mutation or protected-data access occurred. The run is intentionally paused for review; saved status confirms STOPPED_SAFE. Later partial episode26 remains untouched and excluded from every aggregate below. Pricing findings are **PRELIMINARY / INTERIM — NOT FINAL CONVERGENCE**.

The supplied task's framework is followed: A CNN, B passenger sensitivity/P_max, C driver acceptance/repositioning, D pricing DQN, E federated learning, F conditional model-only routing privacy implemented; secure aggregation pending. A separately identified meeting-discussion file was not supplied in this request or located by the narrow filename check; exact document alignment is **NOT AVAILABLE FROM CURRENT SAVED ARTIFACTS**. No additional roadmap requirements are inferred.

## 2. Architecture Implemented

True3km demand aggregation → CNN demand forecast → public13D pricing state → seven-factor DQN → empirical passenger P_max gate → independent driver price/availability/energy eligibility → FCFS assignment → timed fleet/charging movement → causal operational statistics → U1/U2/U3 movement decisions. Frozen public169D temporal-FedAvg routing probabilities feed pricing; they are not a replacement for utility-selected movements. Conditional central driver-level DP routing variants are now evaluated; the appended privacy comparison defines their release boundary.

## 3. Changes Made Since Earlier Implementation

Verified corrections include true3km metre-based cells,142 valid grids and16×16 raster; chronological Jan–Mar CNN with TRAIN-only fitting; empirical rather than synthetic Normal passenger sampling; exact inclusive passenger and driver price gates; separate rejection reasons; causal operational μ/σ/F_hat/H_hat; EV post-movement station reachability and timed/no-teleportation navigation; public169→64→32→9 routing; temporal federated updates;13→64→64→7 pricing with seven factors; standard replay/Adam/Huber/soft-target semantics; deterministic resume; fixed March16 development; protected hierarchical final evaluation. These are verified implementation/project decisions, not blanket claims of external approval.

U1=1−Φ((P_min−μ)/σ), U2=1−exp(−F_hat W_max), U3=1−exp(−H_max/H_hat); configured denominator safeguards apply. Repositioning maximizes U1+U2−cost; charging navigation maximizes U3−path cost. Current saved α/β/δ/κ are0.3 and normalized-distance cost coefficient0.25. H_max baseline10minutes is project calibration, with future5/10/20 sensitivity planned, not executed.

## 4. CNN Demand Prediction Results

| model | MAE | RMSE | R2 |
|---|---|---|---|
| CNN | 6.072322141353772 | 20.48501848867863 | 0.9511007257716422 |
| HistoricalAverage | 3.3145281355210443 | 16.271804138733728 | 0.969146736451782 |
| Seasonal | 28.088483443646933 | 92.15524822560909 | 0.0103768654763042 |
| CNN_continued | 5.242741437019256 | 18.29280020640285 | 0.9610066924742178 |


**CNN_VALID_BUT_HISTORICAL_BASELINE_SUPERIOR**. Selected continuation is epoch200, not a convergence guarantee. Historical-average baseline is better on MAE/RMSE/R². Previously saved prediction-total/observed-total ratios are0.937148 for continued CNN and0.946775 for historical baseline; these are aggregate level ratios, not MAPE. Relative error/MAPE for this final comparison: **NOT AVAILABLE FROM CURRENT SAVED ARTIFACTS**.

These are already published original CNN aggregate test metrics, whose original split included dates later reserved for hierarchical evaluation. This task reads only saved aggregate reports, not protected observations or predictions. Do not reinterpret them as a new untouched hierarchical test result. Retrospective observed weather also limits live forecasting claims.

## 5. Passenger Sensitivity and Acceptance

Current runtime convention: ΔD=(D−D_base)/D_base; ΔP=(P−P_base)/P_base; epsilon=abs(ΔD/ΔP). Empirical sampling selects historical rows with replacement and preserves duplicate frequencies. P_dispatch=factor×P_base; **P_max=P_base(1+ΔD/epsilon)**; passenger accepts iff **P_dispatch≤P_max**. Signed ΔD may produce negative P_max; no clamp. Driver independently requires **P_dispatch≥P_min**, equality eligible.

The final runtime prior has2,812,236 valid January observations before January25 18:30,243 exact contexts, with exact→period→weather→global fallback. Undefined exact-zero ΔP, nonfinite and nonpositive epsilon are excluded by contract; the saved population has zero such exclusions. Positive near-zero epsilon is retained with no artificial floor, clipping or Normal sampler. Exact-context support is[4.0782867887295956e−06,468668.1627126722]. This differs from superseded signed offline sensitivity descriptions.

Seven-factor acceptance on the saved2,838-request contract fixture, holding passenger realizations fixed:

| factor | accepted | rejected | acceptance_percentage |
|---|---|---|---|
| 0.85 | 1256 | 1582 | 44.25651867512333 |
| 0.9 | 1148 | 1690 | 40.45102184637068 |
| 0.95 | 1062 | 1776 | 37.420718816067655 |
| 1.0 | 953 | 1885 | 33.5799859055673 |
| 1.05 | 879 | 1959 | 30.972515856236782 |
| 1.1 | 834 | 2004 | 29.38689217758985 |
| 1.15 | 801 | 2037 | 28.224101479915433 |


P_max mean21.465555, median16.014187, sample SD119.033635; min-4556.420594, max1434.830916. These are model-derived thresholds, not causal willingness-to-pay estimates or optimal-price evidence.

## 6. Passenger / Driver / Supply Outcome Separation

Across completed training episodes1–25, saved slot reports give:

|Outcome|Count|
|---|---:|
|Generated requests|1118214|
|Passenger rejected price|814420|
|Passenger accepted|303794|
|Accepted, no price-eligible driver under saved search semantics|56496|
|Accepted, unmatched for another recorded operational reason|47|
|Successfully assigned|247251|

Generated=accepted+rejected; accepted=assigned+unmatched hold for all400 saved slots. Candidate driver-price rejections total29520112; they are not unique requests or passenger rejections. The saved count of requests experiencing any blocked candidate is296897, including requests later assigned elsewhere.

For exact episode10/25 development **accepted/rejected/unmatched raw counts: NOT PERSISTED IN MONITORING ARTIFACT**. The separate development summaries persist acceptance and fulfillment rates but not those raw counts. No accepted=assigned inference is used. The earlier contract-validation fixture explicitly had1,197 accepted/assigned and zero unmatched; it is a different evaluation and cannot fill the missing current counts.

## 7. Federated Routing and Repositioning

**FINAL_ROUTING_MODEL_FROZEN=YES; ROUTING_READY_FOR_PRICING=YES; MODEST / UNCERTAIN BUT POSITIVE.** Temporal routing CE0.291657966/Brier0.093053954 versus empirical-prior0.293259219/0.095934945: changes−0.001601253/−0.002880991. ECE0.015838035. CE block interval includes zero; Brier interval is negative. Non-STAY top1 accuracy0.6195%; subgroup probability signal remains inconclusive. Invalid predictions:0. These current freeze results supersede earlier readiness-NO reports.

Temporal FedAvg uses persistent local Adam, latest32 observations, current-slot contributors and equal eligible-client aggregation; slot aggregation becomes available next slot. Frozen inference hash: `db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a`.

Frozen validation mean action probabilities (not physical movement frequencies):

| action | mean |
|---|---|
| 0 | 0.9599890706787404 |
| 1 | 0.003504179725161 |
| 2 | 0.0010269251991276 |
| 3 | 0.0092201129407962 |
| 4 | 0.0008219474950535 |
| 5 | 0.0077541425756702 |
| 6 | 0.003477160385441 |
| 7 | 0.0135182413821794 |
| 8 | 0.0006882196178304 |


## 8. Pricing DQN — Current 25-Episode Result

Authoritative protocol remains500episodes×16slots with8 optimizer steps per warm slot; replay100,000, warmup1,000, batch64, Adam0.001, gamma0.99, Huber, tau0.005; epsilon1→0.05 over50,000 updates. Review cutoff has400 simulated training slots and3,192 updates; no final policy selected. Seven factors are0.85–1.15 in0.05 increments. Reward is gross successfully assigned fare per observed OD/slot, not requested or accepted fare. Signed/absolute sensitivity is not a pricing state feature.

## 9. Eight Core Review Metrics

### 9.1 Total Revenue

Training episodes1–25 total **4791417.80**; individual episode revenue range **12544.84–356489.38**. Different source windows/environment trajectories make this unsuitable as a like-for-like policy improvement estimate. Fixed March16 development revenue: **23981.01→20595.95**, change **-3385.05 (-14.1156%)**. The fixed fixture is the comparable development evaluation.

### 9.2 Passenger Acceptance Rate

Training accepted/requested=27.1678%. Saved fixed-development acceptance rates are **44.8203%→31.2544%**. Raw development counts remain unavailable as noted above. Acceptance is distinct from assignment success.

### 9.3 Successful Assignment Rate

Fixed requests2,838; assignments1,272→887. Assignment/request rates **44.8203%→31.2544%**, change **-13.5659 percentage points**. Development summaries separately persist fulfillment_rate1.0 at both checkpoints; this is reported as saved, not recalculated from invented accepted counts. Training assignments/accepted=81.3877% uses explicit saved counts.

### 9.4 Pricing Factor Distribution

| factor | episode10_count | episode10_pct | episode25_count | episode25_pct |
|---|---|---|---|---|
| 0.85 | 904 | 78.40416305290546 | 0 | 0.0 |
| 0.9 | 0 | 0.0 | 183 | 15.871639202081527 |
| 0.95 | 0 | 0.0 | 0 | 0.0 |
| 1.0 | 5 | 0.4336513443191674 | 0 | 0.0 |
| 1.05 | 0 | 0.0 | 22 | 1.9080659150043364 |
| 1.1 | 146 | 12.662619254119688 | 0 | 0.0 |
| 1.15 | 98 | 8.49956634865568 | 948 | 82.22029488291413 |


Counts are OD pricing decisions, not requests; each evaluation has1,153 contexts. Dominant factor changes **0.85→1.15**. This large shift does not establish either factor as optimal or demonstrate convergence.

### 9.5 Dispatch Vehicle Utilization

Fleet5,000. Unique assigned vehicles, percent dispatched, assignments/active vehicle, per-vehicle median/P10/P90 and idle/non-dispatched count: **INSUFFICIENT SAVED DETAIL FOR CURRENT 25-EPISODE RUN**. Saved slot summaries and current fleet snapshots do not establish a complete historical assignment-to-vehicle table. Do not equate5,000 conserved vehicles with5,000 dispatched vehicles. The best directly verified operational artifact is the separate final passenger/driver contract fixture, which establishes conservation and movement checks, not these utilization statistics.

### 9.6 Repositioning Behavior

Current authoritative pricing run,400 slots, aggregated saved navigation action counts:

| action | count | percentage |
|---|---|---|
| STAY | 1563013 | 88.87931676654844 |
| N | 30592 | 1.739586336468251 |
| NE | 19542 | 1.111238107585727 |
| E | 34449 | 1.958911143599463 |
| SE | 16309 | 0.9273964945561161 |
| S | 37227 | 2.116879594263323 |
| SW | 17369 | 0.9876724332543491 |
| W | 24992 | 1.4211474150436232 |
| NW | 15086 | 0.8578517086807018 |


Charging decisions are separately recorded: **1481**; saved charging-event records total **2730** (event records, not necessarily unique sessions). Directional counts combine ordinary navigation and charging next hops. A direction-by-charging split is **NOT AVAILABLE FROM CURRENT SAVED ARTIFACTS**; do not label this table ordinary repositioning only. This is current pricing-run behavior, distinct from routing-training labels and frozen validation probabilities above.

### 9.7 Training Stability and Routing Action Distribution

| metric | episode10 | episode25 |
|---|---|---|
| mean_abs_Q | 141.6536407470703 | 328.287353515625 |
| median_abs_Q | 99.5578842163086 | 255.68789672851562 |
| q_max | 586.09765625 | 1122.203857421875 |
| mean_Q_spread | 12.686588287353516 | 16.038427352905273 |
| mean_loss | 29.07678496837616 | 41.90878874063492 |
| terminal_mean_reward | 26.500238348368427 | 26.030598385893935 |
| terminal_selected_Q_mean | 147.0145263671875 | 338.09869384765625 |
| terminal_absolute_TD_error | 122.38717965261547 | 312.07167619518503 |
| bootstrap_fraction | 0.806625485420227 | 0.8936363458633423 |
| replay_size | 67413.0 | 100000.0 |
| optimizer_updates | 1272.0 | 3192.0 |
| epsilon | 0.975832 | 0.939352 |

Routing-model readiness and weak rare-action classification are separate from pricing-DQN stability. Routing mean probabilities are reported in section7; current navigation counts in9.6. Invalid model actions are zero in frozen validation, not a newly reconstructed full-run action audit.

### 9.8 Operational State Validity

| check | status | evidence_scope |
|---|---|---|
| fleet count invariant | PASS | All400 saved slot reports:5000 |
| valid grid IDs | NOT AVAILABLE | Contract fixture validated; no independent full25-run audit persisted |
| valid state dimensionality | PASS | Final protocol13D pricing/169D routing and checkpoint/resume validation |
| finite states | PASS | Saved stability/cadence replay checks; checkpoint-scoped, not exhaustive all25 trajectories |
| finite rewards | PASS | Saved replay checks and finite aggregate slot rewards |
| valid actions | PASS | Saved replay checks and seven-action monitoring counts |
| no driver-price assignment violation | NOT AVAILABLE | Separate final-contract fixture reports0; no per-assignment full25 audit saved |
| no invalid routing action | PASS | Frozen routing validation:0 invalid predictions; scope is routing validation |
| energy nonnegative / finite | NOT AVAILABLE | Separate contract fixture PASS; exhaustive25-run persisted audit unavailable |
| reachability contract | PASS | Frozen interface and separate validated fixture; not a new full-run verification |
| replay integrity | PASS | Saved authoritative checkpoint analysis PASS |
| checkpoint/resume integrity | PASS | Saved monitored_resume_validation.json and tests |
| routing hash unchanged | PASS | Monitoring/resume evidence identifies frozen hash |
| March17–31 protected | PASS | No protected data accessed for this consolidation; saved execution boundaries retained |
| accepted/unmatched accounting | PASS | All400 saved slot identities reconcile |
| reserve rejection accounting | PASS | Saved completed-episode reserve counters aggregated |
| charging-state validity | NOT AVAILABLE | Events/decisions saved; full25 charging-state audit not independently persisted |

PASS is limited to the stated evidence scope. NOT AVAILABLE indicates a reporting gap, not a demonstrated failure.

## 10. Training Stability

DQN mechanics validated; learning behavior observed; saved numerical values finite; no proven structural Bellman/replay bug. **Policy has NOT demonstrated convergence.** Terminal Q calibration worsens from episode10 to25; bootstrap dominance rises; fixed development revenue/assignments deteriorate; greedy action distribution changes substantially. Training was intentionally paused for current-state review. No optimal factor or final performance claim is justified.

Diagnostic investigations: the separate **ACCELERATED_REVIEW_PHASE_DIAGNOSTIC** used128 updates/slot and showed severe inflation/oscillation. Earlier cadence attribution favored monitored8-update continuation based on episode5 evidence, but does not establish episode25 or future convergence. The authoritative8-update monitoring table is the headline, not accelerated results.

## 11. Operational State Validity

Operational μ/σ use prior completed successful dispatch fares; F_hat tracks dispatch rate; H_hat tracks charging queue observations. Empty observations use frozen carry/decay rules. Saved all-slot accounting and fleet counts reconcile; reserve counters across completed episodes are 1 assignment candidate rejections and 0 reposition rejections. Zero counts do not prove every possible edge case. Contract fixtures validate price equality, finite energy, reachability, timed charging and no teleportation; exhaustive current-run audit gaps remain explicit.

## 12. What Is Complete

Spatial/data contract; CNN bounded implementation/evaluation; empirical passenger acceptance and independent driver gate; operational/EV interfaces; temporal routing freeze; pricing-DQN mechanics and exact resume; preliminary25-episode authoritative review; saved stability and cadence diagnostics. These completion statements do not imply final pricing convergence.

## 13. What Is Pending

**Reporting gaps:** named meeting-document alignment; raw development accepted/rejected/unmatched counts; current-run vehicle utilization; charging-specific directional split; exhaustive per-assignment/per-movement operational audit. Reporting gaps are not automatically implementation defects.

**Model-development gaps:** pricing stability/convergence and decision on25→50/100/500 continuation; full non-private baseline; secure aggregation and privacy hardening; later robustness/attacks; final baselines/ablations; multiple seeds/confidence intervals; protected final evaluation. Conditional driver-level routing DP, update clipping, Gaussian aggregation noise, conservative RDP accounting and before/after routing comparison are complete. Secure aggregation, production-grade privacy hardening and release accounting for raw diagnostics remain pending; see the appended comparison.

## 14. What Can Be Presented Now

Corrected CNN comparison, passenger epsilon/P_max and seven-factor acceptance curve, rejection separation, driver/EV architecture, final temporal FedAvg results, preliminary authoritative pricing through episode25, fixed revenue/assignment/action changes, stability diagnostics and scoped operational invariants. All pricing results are **PRELIMINARY / INTERIM**, **NOT FINAL CONVERGENCE**.

## 15. Limitations / Items Not Yet Claimed

No final pricing convergence; no optimal pricing factor; no protected hierarchical test result; no DP result; no robustness result; no multi-seed statistical conclusion; no new March17–31 result. Existing CNN aggregate evaluation is historical and is not a new protected hierarchical evaluation. Source-report historical statuses can be superseded; the temporal freeze governs current routing readiness.

## 16. Next Recommended Work

Current-state academic review and an explicit decision on further authoritative pricing training; conditional routing-DP results are available for review. Review calibration, bootstrap and fixed-development changes together. Resolve reporting gaps separately; do not silently alter methodology or restart/resume training from this report. Later continuation and protected evaluation require separate authorization.

## 17. Authoritative Artifact Index

See `source_index.csv` for section, artifact, status and scope notes, including each completed episode checkpoint used for aggregation. `core_results.csv` covers exactly eight metrics; seven have quantitative evidence, while dispatch utilization remains explicitly unavailable. `pricing_review.csv` preserves episode10/25 values. `operational_validity.csv` records scoped PASS/NOT AVAILABLE findings. All input artifacts remain unchanged except the requested append-only run README and root current-status update.

## 18. Current Status

CURRENT_STATE_REVIEW_READY = YES  
PRICING_REVIEW_CUTOFF = EPISODE_25  
PRICING_POLICY_CONVERGED = NO  
FINAL_ROUTING_MODEL_FROZEN = YES  
PASSENGER_ACCEPTANCE_CONTRACT_READY = YES  
PRIVACY_IMPLEMENTED = YES (conditional model-only routing mechanism; raw diagnostics excluded)  
PROTECTED_FINAL_EVALUATION_UNTOUCHED = YES

## Differential Privacy — temporal routing comparison

Conditional central driver-level DP is implemented at the trusted aggregation boundary: replacement adjacency with fixed public participation, C=1, no subsampling amplification, 576-round Gaussian RDP accounting. Individual epsilon targets8/4/2 at delta1e-5 are achieved; three-model joint release has epsilon9.533672. Raw research diagnostics are not DP-protected releases.

| model | epsilon | CE | Brier | accuracy | non_STAY_CE |
| --- | --- | --- | --- | --- | --- |
| NON_PRIVATE | not applicable | 0.291658 | 0.093054 | 0.949363 | 5.140560 |
| DP_EPS8 | 8.000000 | 0.830102 | 0.184402 | 0.900448 | 10.395219 |
| DP_EPS4 | 4.000000 | 2.042319 | 0.248193 | 0.875446 | 29.416439 |
| DP_EPS2 | 2.000000 | 19.522398 | 0.550814 | 0.723496 | 211.529834 |

The bounded same-episode25-checkpoint development comparison is complete; it remains preliminary because pricing is not converged. Secure aggregation, pricing convergence and robustness/attack evaluation remain pending. Protected final evaluation is untouched. See [privacy comparison](../2026-11-01_differential_privacy_comparison/README.md) for exact budgets, limitations, clipping and service metrics.


## Academic Review Validation — 2026-11-04

The consolidated roadmap is now available. [The validation package](../2026-11-04_academic_review_validation/README.md) adds verified evidence without rewriting the historical review above. Episode25 slot9 (March12 15:30–16:00) was reconstructed once from the saved slot8 simulator/learner/RNG checkpoint, with no optimizer update or persisted learner change. All comparable original slot metrics match: 2,996 requests,719 accepted,2,277 rejected,572 assignments and147 accepted-unmatched due to the driver price gate. Independent acceptance mismatches:0. Runtime P_max below/equal/above contextual base:2,365/0/631.

All10,620,409 cleaned historical Jan–Mar trips were descriptively binned **after km conversion**. Fares are not constant below3km; the3–3.17km bin has247,751 trips, median$14.20 and mean$16.266758. No universal fare-floor rule is inferred. Driver preferences explicitly require offered fare≥persisted minimum;2,065 of5,000 profiles fall below0.85×the selected runtime context base. That factor is not an implemented preference floor.

Saved final CNN predictions give MAE5.242741437, MSE334.626539391, RMSE18.292800206, R²0.961006692, NRMSE100.745164% and aggregate-volume error6.285204% over109,056 grid-slot observations. The historical section's narrower availability statement is superseded for these newly calculated metrics; no MAPE is claimed. Historical descriptive analysis and already-defined CNN evaluation were explicitly permitted. March17–31 hierarchical training/evaluation, policy selection and service/revenue evaluation remain untouched.

Authoritative pricing remains25complete episodes/3,192updates: early trend only, not convergence. Mean/median offered price per historical episode remains NOT PERSISTED. Existing DP diagnostics are unchanged; the exact referenced-paper LOW/HIGH regimes and alpha values remain unidentified. Historical signed global-reference epsilon and current positive contextual epsilon are distinct conventions, not a miles/km bug. No methodology, frozen model, driver profile or production source changed.


## Passenger-Sensitive Pricing V1 — Current Status, 2026-11-07

Historical metrics above are preserved and describe the earlier implementation.

Passenger-Sensitive Pricing V1 is the active **implementation specification**, but implementation is **BLOCKED** at its mandatory action-granularity preflight. Existing runtime has not been converted. Global P_base_USD=21.34586956773507; global L_base_km=4.856998243316242; L_gg_prime=actual passenger OD distance in km. Positive behavioural epsilon requires a calibrated epsilon_min; no calibration has run. TLC completed trips do not identify passenger acceptance elasticity. Planned proxy, if real response labels are absent: abs(Record-029 epsilon), Jan1–Mar15 only; historical signed evidence remains unchanged.

Required V1 equation: `P_c = P_base + (P_base/epsilon_c)*((L_gg_prime-L_base)/L_base)`. Seven experimental factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15] are not empirical NYC fare extrema. Mask candidate fare<=P_c **before** selection, equality feasible; empty mask means **no offer**, not passenger rejection. No passenger lower-bound f(), contextual bases, post-selection clipping or d_min rule is authorized.

Current implementation chooses one action per OD/slot **before** each passenger's epsilon/P_c exists, then stores one aggregated OD transition requiring an action. Passenger-specific masking and no-action handling therefore require an explicit decision/replay-contract change. No code/provider/mask or fresh learner was implemented; tests and calibration did not proceed. Old episode25 is **PRE_REFORMULATION_PRICING_PROVENANCE**. Its checkpoints remain unchanged and were not loaded. A fresh DQN is required after the gates; long training has not started. March17–31 remains untouched by calibration, training, selection or hierarchical evaluation.

[Version-1 specification and blocker](../2026-11-07_passenger_sensitive_pricing_v1/README.md).


## Passenger-Sensitive Pricing V1 — Approved Request-Level Contract

## Academic Review Feedback Incorporated

Dated2026-11-07. Prior findings above are historical/pre-reformulation evidence. Review feedback on (1) distribution, sampling and asymmetric truncation; (2) permitted absolute values; (3) minimum-protected threshold; and (4) dataset justification of seven factors is incorporated.

Academic-review reconciliation is complete under an explicit project implementation decision. Equation-number provenance remains unverified (`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED=NO`); `V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION=YES`. Historical formulation without the P_base adjustment multiplier is superseded, not rewritten.

V1 uses positive absolute Record-029 sensitivity as a behavioural calibration proxy, not causal acceptance elasticity. Restrict Jan1–Mar15 VALID finite/nonzero first, then abs(), then inclusive positive P0.5–P99.5: [0.017809913104763053, 27.324599740032788], N=8,598,805. Truncated empirical row resampling with replacement preserves duplicate mass, caller-controlled seed; global pool. T0 retained after four bounded asymmetric comparisons. epsilon_min is the support lower bound; no extra floor. Signed historical artifacts remain unchanged.

Raw preference is `P_base+(P_base/epsilon)*((L-L_base)/L_base)` with unchanged global references21.34586956773507 USD and4.856998243316242km. Effective threshold is `max(0.85*P_base,P_raw)`; all action masks use it. The seven factors0.85–1.15 remain; dataset justification is MODERATE for bounded reference-price exploration, weak for uniquely determining exact endpoints/spacing. Jan1–Mar15 fare coverage inside that interval is14.379973%; it is not a statutory NYC fare minimum or a full-market envelope.

The former61.746289% raw-rule no-offer rate is `SUPERSEDED_BY_EFFECTIVE_THRESHOLD_REFORMULATION`; revised valid calibration no-offer=0%. Historical raw diagnostics remain. No post-selection action clipping or d_min. Request-level13D state/replay, masked Bellman target, gamma=0.99 per request transition and8/warm-slot cadence retained. Bounded fixture400 requests, 390 assignments, 0 no-offers, zero optimizer updates; 57 focused tests passed. At reconciliation completion no training had started; the subsequently authorized staged run is tracked below; old checkpoints not resumed. March16 development-only; March17–31 untouched. [Reconciliation](../2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/README.md).

<!-- V1_STAGED_001_STATUS -->
## Passenger-Sensitive Pricing V1 Detached Stage1

Historical staged_training_001 execution decision (superseded time-aware discount): three separate detached stages. Stage1 initializes fresh and stops after Episode1 plus fixed March16 development evaluation. The prior attached partial attempt is preserved and not resumed. Each subsequent stage requires a later saved-artifact review. No automatic chaining, no Codex polling. Convergence=NO; March17–31 untouched. Current metrics are in the status file; see [staged report](../2026-11-07_passenger_sensitive_pricing_v1/staged_training_001/README.md).


## Active V1 request-step discount correction

**ACTIVE: gamma=0.99 per actionable request transition**, including same-timestamp requests. Terminal target is reward only; elapsed time remains diagnostic metadata. Gamma value unchanged; application semantics changed. Next state remains the next chronological actionable request; all masks, 13D state, rewards, cadence (8/warm slot), and other frozen parameters remain unchanged.

The old 0.99^(delta_t_minutes/30) rule is SUPERSEDED: near-unity discounts accumulated episode revenue and high horizon aliasing. `staged_training_001 = SUPERSEDED_TIME_AWARE_DISCOUNT_DIAGNOSTIC`; its artifacts/checkpoint remain unchanged. Offline comparison supports the correction: mean/median MC 1725.825875/1799.281877 versus 315510.192211/322877.321850; horizon correlation is materially reduced, not eliminated. Residual terminal exposure is 1.236830%.

Fresh staged_training_002 Episode1 only is authorized after focused tests; no old checkpoint resume, no automatic Stage2. March1–15 training, March16 fixed development, March17–31 protected. Execution status is recorded in `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/staged_training_002/training_status.json`; methodology evidence is in `results/analysis/2026-11-07_passenger_sensitive_pricing_v1/bellman_discount_correction/README.md`.

## Corrected V1 Episode25 completed review

| episode | revenue | assignments | assignment_rate | mean_offer | choice_request_rate | forced_request_rate | mean_abs_Q | max_abs_Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 54330.57451727768 | 2767 | 0.974982381959126 | 19.61631258848888 | 0.4506694855532064 | 0.5493305144467935 | 3.10725998878479 | 33.48653793334961 |
| 10 | 56855.79088714074 | 2792 | 0.9837914023960536 | 20.32821764648258 | 0.4506694855532064 | 0.5493305144467935 | 58.99930191040039 | 104.06543731689452 |
| 25 | 56419.26785448056 | 2786 | 0.981677237491191 | 20.220284866955804 | 0.4506694855532064 | 0.5493305144467935 | 147.33767700195312 | 199.55938720703125 |

```json
{
  "Q_SCALE_TREND": "UNCLEAR",
  "NUMERICALLY_STABLE": "YES",
  "POLICY_STABLE": "UNCLEAR",
  "LEARNING_SIGNAL": "UNCLEAR",
  "CONVERGED": "NO",
  "optimizer_updates": 3200,
  "exploration_epsilon": 0.9392,
  "protected_period_untouched": true,
  "policy_movement_available": false,
  "review_basis": "Descriptive Episode10\u219225 changes in Q/MC relative gap, MAE, TD and loss jointly; no convergence or causal performance claim.",
  "later_training_authorized": false
}
```

Full choice/all-action and feasible-count distributions are in development_ep01_ep10_ep25_comparison.csv, ep25_development_action_by_feasible_count.csv and ep25_development_choice_policy.csv under the staged_training_002 report. MC calibration is retained per episode, including 15, 20, 25 and Episode25 development. No equality of Q and MC is required. Exact Episode10→25 per-request policy movement is unavailable because Episode10 did not retain those request records; aggregate policy movement is descriptive only. No Episodes26+ launched; March17–31 untouched.

</details>
