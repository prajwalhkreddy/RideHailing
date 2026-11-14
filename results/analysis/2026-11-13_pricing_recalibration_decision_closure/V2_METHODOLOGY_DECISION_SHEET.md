# V2 Methodology Decision Sheet

**Academic approval draft — decision closure only; no implementation or training authorization.**
13 November 2026. Evidence: completed context audit and decision analysis, plus *Passenger Price Sensitivity and NYC Fare Calibration*, pp2–9. This compact six-section sheet targets approximately 4–6 printed pages; Markdown pagination depends on renderer. No new fits, simulation, raw preparation, learner loading or protected-row access.

## 1. Scope and closure of remaining analysis

The existing decision table, read directly, contained **19 decisions: 3 evidence-ready, 12 academic, 3 more-analysis, 1 missing-formula blocker**. The exact original categories are recorded in the accompanying README. Only EPSILON_DISTRIBUTION, NYC_LOWER_BOUND and NYC_UPPER_BOUND were eligible for further analysis. Their bounded closure is an interpretation of completed fits and quantile coverage, not a repeated calculation.

- **Distribution:** within-scenario AIC winners differ; support differs. Existing evidence answers the selection question: **NO single parametric family is justified now**. Population/sign approval is the next dependency, not another fit sweep.
- **Fare lower/upper bounds:** existing quantiles quantify coverage, but neither identify a unique policy interval nor establish legal tariff bounds. These become **academic interpretation decisions**, jointly conditional on population and fare definition. No external tariff claim is made and no source validation is claimed complete.

Result: **3 evidence-ready, 15 academic, 0 additional-analysis, 1 missing-formula blocker**. Evidence-ready means ready to submit for approval, not approved. CSV block flags refer to freezing the complete V2 contract; they do not imply all 19 items require simultaneous code changes.

## 2. Population, denominator and sampling evidence

Historical `epsilon_old=r_P/r_L`; new PDF `e_new=r_L/r_P`. At identical references and finite nonzero deviations, `e_new=1/epsilon_old`; verified product error is at most2.220446049250313e-16. Changed references require rebuilding calibration, not inverting the old supported pool. Orientation is **EVIDENCE_READY_FOR_FREEZE**.

At exact P_base22.354198442390455 USD and L_base4.5 km:

| Population | Mass | Mean | Population SD | Negative mass |
|---|---:|---:|---:|---:|
| Equal lower-edge bins, [1,75) km |148|2.313937|0.407451|0|
| Count-weighted lower-edge bin proxies |7,946,921|1.628232|0.579044|0|
| Paired trips, matched [1,75) km |7,946,921|1.427109|29.316258|1,044,072|
| Paired trips, all safe Jan1–Mar15 |8,692,819|1.414919|29.609236|1,105,611|

Equal bins represent a **distance-response curve**. Individual paired trips directly represent the **passenger observational population**, but not necessarily causal individual sensitivity. Count-weighted proxies preserve passenger frequency while suppressing within-bin fare/distance variation; they are not equivalent to trip ratios. Recommendation, pending approval: define passengers as the unit if that is the intended estimand, resolve admissibility/signs first, and use weighted bins only as an explicitly approved approximation. Do not select equal bins merely because their SD is small. For1–5 km equal-bin mass is5.405405% versus66.517322% weighted; for60–75 km it is20.270270% versus0.025242%.

Exact price-denominator zeros: **0**. Cumulative all-safe counts within $0.01/0.05/0.10/0.25/0.50/1 of P_base are **858/4,457/10,414/116,921/212,606/353,811**; these overlap. Minimum gap is$0.00419844239. Relative tolerances are dollar gaps divided by P_base. Matched trip e ranges about−15,450.17 to17,161.44; fare22.36 and distance24.542496 km gives17,161.442304. These are not automatically invalid observations. An **explicit admissibility/resolution policy is required before operational trip-level use**, including the option to retain sensitive observations with an approved interpretation; the evidence does not justify a particular exclusion threshold. Lower-edge4.5 creates one zero bin (310,535 weighted mass), whereas actual trip zeros are0. Zero e and undefined0/0 require separate treatment.

Completed positive-component fits at the4.5 reference favour Weibull for equal bins (KS0.120167), lognormal for weighted bins (KS0.385185), matched trips (0.109105), and all-safe trips (0.125208). Signed trip normal KS≈0.40 is poor descriptive agreement. No universal family dominates; AIC is comparable only within the same target, weighted proxies are not independent trips, and KS here is descriptive, not an unadjusted hypothesis test. Positive-component fits omit negative/zero mass.

Pending approval, prefer **empirical resampling from the finally selected admissible population** as the transparent baseline; it preserves observed frequencies but does not cure ratio instability or prove generalization. Alternatives are a positive parametric component with explicitly modelled sign/zero mass, or another approved treatment. The PDF requests a fitted population, so an empirical alternative must be approved rather than silently substituted.

## 3. Calibration range, references and fare limits

Lower1/1.5/2 km retains7,946,921/6,967,155/5,974,083 trips. An upper75 km excludes1,459 safe longer records. Minimum50: individual-bin removal247 trips versus contiguous removal683 (end68 km); minimum100:1,665 versus1,775 (end62 versus61 km). These are empirical population/noise choices, **not proven necessary invalid-record protections**. Nonfinite/malformed data and unit integrity remain separate validity issues. Specify [1,75) endpoint semantics and whether filters apply to calibration or demand. Recomputing reference price can dominate SD changes: contiguous50 gives SD599.16 with its own P versus29.28 at fixed references. Do not optimize reference choice by minimum SD.

Exact P_base **22.354198442390455**, display **22.3542**. Preserve exact arithmetic pending approval; rounded P changes extreme e by up to5.728764 despite a≈$1.56e-6 difference. If the population changes, the present weighted reference does not automatically carry over.

| L_base candidate (km) | Meaning |
|---|---|
|4.5|Lower edge of closest mean-fare bin (fare≈21.983204), not exact mean-price crossing|
|4.616983790655043|Interpolated distance-response curve crossing at P_base|
|5.300620449409596|Actual mean distance of346,880 array-range trips within diagnostic±$1 of new P_base|

No candidate is uniquely established; **L_BASE=ACADEMIC_INTERPRETATION_REQUIRED**. The conditional mean is not a taxi-meter threshold; reference distance and meter base distance must not be conflated.

Existing all-safe TLC fare_amount quantile intervals:

| Quantiles | Candidate USD interval | Unaffected observations % |
|---|---|---:|
|P0.1–P99.9|[3,135.30]|99.886573|
|P0.5–P99.5|[4.40,91.23]|99.002959|
|P1–P99|[4.40,78.60]|98.505606|
|P2.5–P97.5|[5.10,70]|97.256782|
|P5–P95|[5.80,58.19]|92.139500|

Ties explain non-nominal tail fractions. Array-range quantiles differ (e.g.P0.5–P99.5=[5.80,91.71]); the chosen population must be named. **$0.01, $7.52, $207 and $2555.20 are not approved bounds.** Quantiles of fare_amount are not total-fare or statutory tariff limits. Exact lower/upper remain academic decisions; no interval selected.

## 4. Source equations and hard implementation blocker

Only explicit PDF expressions are reproduced here, arranged in dependency order (page locations retained):

1. p3: `e_i=((L_i-L_base)/(P_i-P_base))*(P_base/L_base)`.
2. p8: `L_effective=max(L_observed,L_base)`; if `L<=L_base`, `P=P_base`.
3. p6: if `epsilon=0`, `P=P_base`.
4. p7: `P_action=P_base*alpha`; seven example factors0.85–1.15.
5. p7: `P_final=min(P_NYC_upper,max(P_NYC_lower,P_generated))`.
6. pp7/9: Pmax is described as calculated via the approved pricing formulation. **No complete Pmax/reference-price equation is stated.** No inversion of the e equation is supplied here as a generation rule.

```text
L_observed -> L_effective=max(L_observed,L_base)
           -> reference fare/Pmax: UNSPECIFIED_IN_SOURCE
           -> P_generated: UNSPECIFIED_IN_SOURCE
           -> relation to P_action=P_base*alpha: UNSPECIFIED_IN_SOURCE
           -> clipping: explicit min/max equation
           -> passenger response function: UNSPECIFIED_IN_SOURCE
```

The short-distance and zero branches are explicit separately, but their priority relative to actions and clipping is **UNSPECIFIED_IN_SOURCE**. This graph records gaps, not an invented order of composition. **PRICE_GENERATION_FORMULA_COMPLETE=NO**.

Minimum exact formula question: **What is the complete piecewise distance/sensitivity-to-reference/Pmax-to-generated-offer equation, and does alpha multiply global P_base, the distance/sensitivity-derived reference/Pmax, an increment over P_base, or another specified quantity? Please define zero/short-distance branch precedence and clipping order.** The listed alternatives are not exhaustive. Factors and count are not final; both must be frozen before a new network/action/replay contract. Existing135 global clipping comparisons produced no collapsed actions; that cannot validate missing distance-dependent composition.

Current response is mask → feasible selection → structurally true acceptance. PDF prose is generation/selection → clipping → passenger response. Without the mask, unchanged13D state is **UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**, not universally devoid of predictive context. Options: retain mask; post-action rejection with approved passenger-relevant state/context; or another specified response architecture. No features are added. Under post-action rejection, reward, replay transition, dispatch bypass, operational-statistic updates and next-state semantics are undefined. Accepted-unmatched reward0 is not automatically rejection reward.

PDF pp6/9 explicitly directs empirical bin-distance/spatial sampling, but does not explicitly resolve replacement of this implementation's forecast-driven intact-trip generator or preservation of its joint OD/distance/duration law. **Replacement requirement: UNCLEAR.** Recommend preserving the joint generator as the architecture baseline until that conflict is resolved, not claiming the current generator exactly implements the PDF workflow. The saved March16 illustration has conditional TV0.131465/KS0.120322 versus array bins and327/2,838 requests below1 km; it is not full-generator certification.

Episode25 exact continuation **NO**, replay compatibility **NO for changed V2 semantics**. Fresh learner/replay required; transfer initialization only under separate approval. Existing V1/checkpoint history remains unchanged. No training now.

## 5. Decision register

Each row below supplies the requested decision, current V1, source directive, numerical evidence, recommendation, approval and implementation consequence. Full machine-readable choices/statuses are in `V2_DECISION_STATUS.csv`.

**D01 — EPSILON_ORIENTATION** (EVIDENCE_READY_FOR_FREEZE)  
Current V1: Record029 r_P/r_L; V1 uses positive absolute proxy. Source: PDF p3 explicitly r_L/r_P. Evidence: Max reciprocal-product error2.220446049250313e-16 at identical references. Recommendation: PDF direction is explicit; freeze as replacement only after dependent zero/population semantics are agreed Implementation consequence: Rebuild calibration with approved references; no reciprocal reuse of old pool. **Academic approval required: YES.**

**D02 — EPSILON_POPULATION** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Restricted positive trip-level V1 pool. Source: PDF pp3/6 uses equal-bin example but calls it population. Evidence: At4.5 lower edge:mean2.313937 vs1.628232 vs1.427109(array trips). Recommendation: Individual paired trips are the passenger observational unit, conditional on approved denominator/sign treatment; count-weighted bins are a reduced proxy; equal bins describe a distance-response curve. Implementation consequence: Freeze observational unit and weights before sampler. **Academic approval required: YES.**

**D03 — EPSILON_SIGN** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Absolute-value positive proxy. Source: PDF p7 asks inspection of negative/zero observations. Evidence: Matched trip population has1044072negative values; bin signs vary with representation. Recommendation: Do not silently abs the newly oriented ratio; choose behavioural interpretation Implementation consequence: Implement only approved sign semantics. **Academic approval required: YES.**

**D04 — EPSILON_ZERO_RULE** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Positive support; old distance-resolution handling. Source: PDF p6 e=0 implies price=P_base; undefined ratios unresolved. Evidence: No exact price-zero denominator; one lower-edge zero bin with310535weighted mass. Recommendation: Keep zero-price modelling branch distinct from undefined-ratio convention Implementation consequence: Separate zero-price branch, undefined ratio and near-zero policy. **Academic approval required: YES.**

**D05 — EPSILON_DISTRIBUTION** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Truncated empirical resampling. Source: PDF pp6–7 requests fitted common distribution, family unresolved. Evidence: Positive component:Weibull best unweighted;lognormal weighted/trip at reference4.5; fit mismatch remains. Recommendation: Prefer empirical resampling of the finally approved population as a pending-approval baseline; no single parametric family justified now. Implementation consequence: Version sampler only after population/support approval. **Academic approval required: YES.**

**D06 — LOWER_DISTANCE_CUTOFF** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Existing cleaned trips; not a 1/1.5/2 km runtime rule. Source: PDF p8 discusses 1/1.5/2 km. Evidence: Retained7946921/6967155/5974083. Recommendation: Treat cutoff as substantive population choice, not outlier housekeeping Implementation consequence: Freeze scope before recalculating references. **Academic approval required: YES.**

**D07 — UPPER_DISTANCE_CUTOFF** (EVIDENCE_READY_FOR_FREEZE)  
Current V1: Existing cleaning <=100 miles. Source: PDF p8 approximately75 km. Evidence: Only1459safe records at>=75km; added to range1+. Recommendation: 75km has clear mass accounting; do not infer that all longer trips are invalid Implementation consequence: Specify endpoint inclusivity and calibration/runtime scope. **Academic approval required: YES.**

**D08 — MIN_BIN_COUNT** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: No new 50/100 V1 criterion. Source: PDF p8 discusses50/100. Evidence: Individual exclusion247/1665trips. Recommendation: Numerical consequences available; threshold is not self-validating Implementation consequence: Do not silently remove sparse bins. **Academic approval required: YES.**

**D09 — SPARSE_BIN_SEMANTICS** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Intact trip sampling. Source: PDF does not resolve holes versus contiguous cutoff. Evidence: 50:142bins vs134;100:121 vs120. Recommendation: Specify semantics explicitly; neither follows automatically from minimum count Implementation consequence: Persist explicit selection semantics. **Academic approval required: YES.**

**D10 — P_BASE_PRECISION** (EVIDENCE_READY_FOR_FREEZE)  
Current V1: 21.34586956773507 USD. Source: PDF p2 weighted array mean, displayed22.3542. Evidence: Price difference1.557609545e-6USD; max full-trip e difference5.728764. Recommendation: Preserving exact arithmetic is better for reproducibility; display rounding can be separate, pending approval Implementation consequence: Persist exact value; round display only; re-evaluate if population changes. **Academic approval required: YES.**

**D11 — L_BASE** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: 4.856998243316242 km (historical conditioned reference). Source: PDF pp2/9 reference alternatives unresolved. Evidence: Changing representation creates a negative bin where lower-edge reference giveszero. Recommendation: Do not equate L_base and L_flat; select definition based on modelling purpose Implementation consequence: Keep physical distance distinct from effective fare distance. **Academic approval required: YES.**

**D12 — NYC_LOWER_BOUND** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Platform minimum 0.85 P_base. Source: PDF p7 empirical lower bound unspecified. Evidence: Allsafe P0.1=3;P0.5/P1=4.4;P2.5=5.1;P5=5.8. Recommendation: Select a jointly approved empirical fare interval after population/fare-component agreement; none selected here. Implementation consequence: Implement clipping only after approval. **Academic approval required: YES.**

**D13 — NYC_UPPER_BOUND** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Platform maximum action 1.15 P_base. Source: PDF p7 empirical upper bound unspecified. Evidence: Allsafe P95=58.19;P99=78.6;P99.9=135.3. Recommendation: Select jointly with lower bound using persisted tail coverage; raw maximum and bin means are not approved bounds. Implementation consequence: Implement clipping only after approval. **Academic approval required: YES.**

**D14 — PRICE_GENERATION_FORMULA** (BLOCKED_BY_MISSING_FORMULA)  
Current V1: P_raw=P_base+(P_base/epsilon)*r_L; P_accept=max(0.85P_base,P_raw). Source: PDF pp7/9 separate action/clipping components; full Pmax missing. Evidence: PDF supplies separate floor,action andclip operations; combination equation absent. Recommendation: Obtain complete piecewise equation; do not infer it from components Implementation consequence: Hard implementation blocker; no inferred inverse equation. **Academic approval required: YES.**

**D15 — ACTION_FACTORS** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: 0.85,0.90,0.95,1,1.05,1.10,1.15. Source: PDF p7 factors explicitly illustrative. Evidence: Old range18.143989–24.547750;new19.001069–25.707328. Recommendation: Evaluate after complete price-generation rule; not finalized Implementation consequence: Define action meaning and values after formula. **Academic approval required: YES.**

**D16 — ACTION_COUNT** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Seven actions. Source: PDF does not finalize count. Evidence: All135global bound/base combinations retain7distinctprices. Recommendation: Do not infer a new count from incomplete pricing equation Implementation consequence: Freeze output width, action indices and replay contract before network. **Academic approval required: YES.**

**D17 — ACCEPTANCE_SEQUENCE** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Mask, select feasible offer, acceptance true. Source: PDF p9 generate/select, clip, then response. Evidence: Mask encodes threshold interval absent from13Dstate. Recommendation: Current unchangedstate is unobservable with respect to passenger threshold; agree response contract Implementation consequence: Mask/state/response contract must be agreed together. **Academic approval required: YES.**

**D18 — REJECTION_REWARD** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Assigned gross fare; accepted-unmatched zero; no selected rejection branch. Source: No explicit rejection reward or transitions. Evidence: Current selected feasibleoffers accepted; unmatchedreward0; rejection branch absent. Recommendation: No reward value selected; do not silently reuse no-action or unmatched handling Implementation consequence: Specify reward, replay, dispatch bypass, operational updates and next state. **Academic approval required: YES.**

**D19 — REQUEST_GENERATOR** (ACADEMIC_INTERPRETATION_REQUIRED)  
Current V1: Forecast counts and intact January trip sampling. Source: PDF pp6/9 empirical distance-bin draw then spatial assignment; no explicit legacy-generator migration contract. Evidence: Development conditionalTV=.131465,KS=.120322;327/2838below1km. Recommendation: Preserve the intact joint-trip generator as architecture baseline pending reconciliation with PDF pp6/9 bin-first workflow; replacement requirement UNCLEAR. Implementation consequence: Preserve OD/distance/duration/energy consistency; no generator replacement now. **Academic approval required: YES.**

## 6. Approval closure and minimum question set

### Can freeze from evidence
EPSILON_ORIENTATION; UPPER_DISTANCE_CUTOFF; P_BASE_PRECISION (all pending academic approval and stated scope).

### Requires academic interpretation
EPSILON_POPULATION; EPSILON_SIGN; EPSILON_ZERO_RULE; EPSILON_DISTRIBUTION; LOWER_DISTANCE_CUTOFF; MIN_BIN_COUNT; SPARSE_BIN_SEMANTICS; L_BASE; NYC_LOWER_BOUND; NYC_UPPER_BOUND; ACTION_FACTORS; ACTION_COUNT; ACCEPTANCE_SEQUENCE; REJECTION_REWARD; REQUEST_GENERATOR.

### Blocked by missing source formula
PRICE_GENERATION_FORMULA.

### Requires additional analysis
None at this pre-implementation decision stage. This does not waive later validation of an approved population, sampler or tariff claim.

### Eight logically grouped approval questions
1. **Population/support:** Are sensitivities individual-trip ratios or bin proxies; if proxies, what weights/representative distance? What signed/zero/undefined/near-zero price-denominator treatment is approved?
2. **Calibration references:** Confirm exact P precision and orientation; which physical range, sparse-bin rule, L_base definition and meter-reference relationship apply? Do filters affect calibration only or runtime demand?
3. **Sampling:** Approve empirical resampling of that population, a positive parametric component plus sign/zero model, or another explicit treatment; what subsequent validation is required?
4. **Fare bounds:** Which paired empirical quantiles/population/fare components define lower and upper limits, and are these modelling caps rather than statutory limits?
5. **Complete pricing/action formula:** Supply the complete piecewise equation requested in section4, explicitly how alpha interacts with distance/sensitivity-derived reference fare, branch/clipping priority, final factor values and action count.
6. **Response and learning:** Retain mask or adopt post-action response with what observable passenger context? If rejection is possible, specify reward, replay, dispatch bypass, operational updates and next-state semantics.
7. **Request generation:** Does bin-first prose require replacing the forecast-driven intact joint-trip generator, or may it remain while array probabilities are calibration diagnostics? If replacement, specify the joint physical consistency contract.
8. **Version transition:** Confirm fresh V2 learner/replay after semantic changes and whether any transfer initialization is separately permitted; approval here does not authorize training.

**Implementation authorized: NO. Training authorized: NO. Protected March17–31 analytical rows accessed: NO.**
