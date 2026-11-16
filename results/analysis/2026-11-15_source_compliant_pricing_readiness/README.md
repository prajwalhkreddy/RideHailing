# Source-compliant pricing readiness

Status: NOT_READY. This package records evidence and unresolved choices; it freezes no new numeric or architectural contract.

## Historical formulation

Existing weather-conditioned Episode1–25 is classified here as **HISTORICAL_REQUEST_LEVEL_MASKED_V2**. Its checkpoints, fixture, baselines and reports remain untouched and valid for that formulation. No source-compliant results are inferred from it.

## Source authority

Requested (1).docx names absent in notebooks/plan; same-title unsuffixed documents inspected. Byte identity to any external (1) copies is unverified. Findings apply to these exact hashed documents.
Exact source hashes and paragraph-indexed requirements are reused from ../2026-11-15_source_pricing_weather_compliance_audit/. Weather paragraphs17–27 require separate scenarios, similarity and pooled statistics. Pricing paragraphs15–27 require fare-derived bounds and proactive destination factors;51–62 distinguish response/reward and require aggregation;64–101 require conditional distribution comparison.

## Acceptance impact — saved development draws only

N=73,754 March16 requests. Raw P_max below0: {'N': 6112, 'percentage': 8.287008162269165}; positive but below P_base: {'N': 45812, 'percentage': 62.11459717439054}; exactly0: {'N': 0, 'percentage': 0.0}. Historical offers above raw ceiling: {'N': 42125, 'percentage': 57.11554627545624}.

|Offer definition|USD|Raw ceiling below offer N|Percent|
|---|---:|---:|---:|
|historical action (0.85)|19.00106868|42125|57.115546|
|historical action (0.9)|20.1187786|46035|62.416954|
|historical action (0.95)|21.23648852|49449|67.045855|
|historical action (1)|22.35419844|51924|70.401605|
|historical action (1.05)|23.47190836|53834|72.991295|
|historical action (1.1)|24.58961829|55310|74.992543|
|historical action (1.15)|25.70732821|56507|76.615506|
|observed extrema (unvalidated) min (0.000447343)|0.01|6116|8.292432|
|observed extrema (unvalidated) max (93.2308)|2084.1|73712|99.943054|
|empirical P0.1–P99.9 min (0.134203)|3|8234|11.164140|
|empirical P0.1–P99.9 max (6.1465)|137.4|72092|97.746563|
|empirical P0.5–P99.5 min (0.295247)|6.6|12495|16.941454|
|empirical P0.5–P99.5 max (4.23634)|94.7|70694|95.851072|
|empirical P1–P99 min (0.322087)|7.2|13410|18.182065|
|empirical P1–P99 max (3.64406)|81.46|69940|94.828755|
|empirical P2.5–P97.5 min (0.353401)|7.9|14599|19.794181|
|empirical P2.5–P97.5 max (3.1314)|70|69009|93.566451|
|empirical P5–P95 min (0.384715)|8.6|15906|21.566288|
|empirical P5–P95 max (2.87642)|64.3|68409|92.752935|

These are conditional response inequalities using saved draws, not counterfactual dispatch/revenue forecasts. Raw ceilings below the minimum arm mean no acceptable arm in that candidate set; source-compliant proactive pricing still makes an offer and records rejection, rather than skipping the request by passenger masking. For any positive minimum fare, negative/zero ceilings reject all offers. The historical seven-arm minimum rejects 57.11554627545624% of these draws. Fleet feedback prevents projecting alternative realized revenue from this table.

## Fare bounds and actions

Fare is TLC fare_amount, USD, Jan1–Mar15. The current distance-filtered fare population is6,967,155 at1.5<=km<75 (not the positive-epsilon sampler population). Observed extrema are $0.01–$2084.1; their validity is not established. Existing quantile-pair candidates are empirical, not tariff limits or adopted filters. P_base=22.354198442390455 originates from the earlier1<=km<75 reference construction; it is not recomputed here. No validated NYC fare-limit pair was established by the inspected evidence.

ACTION_DISCRETIZATION_NOT_SPECIFIED_BY_SOURCE. Seven evenly spaced factors .85–1.15 are an existing project choice, not a source requirement. Source-specified endpoints depend on approved fare limits; neither the old endpoints nor an arbitrary new spacing is frozen.

## Proactive state and aggregation

The earlier V2_SLOT_DQN_DESIGN.md proposes142 destination decisions shared across origins, system features and additive joint value decomposition. It explicitly leaves approval outstanding. Origin-conditioned20164 OD decisions are an alternative, not source-mandated. Current13D uses origin quantities plus destination popularity, missing explicit supply/dropoff probabilities. Neither13D nor proposed2146/2288 dimensions are frozen by this audit. Routing directions are not destination probabilities; popularity is not a normalized dropoff vector.

SLOT_AGGREGATION_DECISION_REQUIRED. Earlier final_production.run_slot sums assigned fares per observed OD and creates next-boundary OD transitions, but selects actions on first arrival. Current V2 stores request transitions. Earlier whole-slot/additive proposal supplies provenance for a slot-total candidate, not approval. Mean-per-request revenue has no demonstrated provenance in these inspected contracts and is not promoted as a candidate. Accepted-but-unmatched reward remains NOT_SPECIFIED_BY_SOURCE; historical0 is a project choice.

## Weather and conditional distributions

Behavioural similarity grouping: YES. T-pooled fallback as sparse pooling: PARTIAL; T2–4 instability does not establish sparsity or similarity of dense scenarios. Time groups are project-defined. Separate and combined N/mean/SD are available. T1 mapping and cleaned observations are reusable. T1 group2 has1669 observations, below current runtime5000 minimum, so runtime fallback differs from clustering membership. T2–4 pools contain108740,2544533,2693253 observations respectively; grouping instability alone cannot justify calling them sparse.

All21 current overlapping supports are inventoried in conditional_fit_requirements.csv; these are candidates, not21 newly approved final groups. No complete exact conditional comparison including truncated normal exists. Global empirical/Gamma/Weibull/Lognormal/Exponential evidence is reusable but incomplete for required families and conditional selection. Empirical resampling is not inherently prohibited: it must be justified against groupwise alternatives. Reuse existing CDF/KS, Wasserstein, quantile/tail metrics and parametric AIC/BIC; do not compare discrete empirical likelihood directly with continuous densities. Decide truncation bounds, validation split, support and fallback before fitting. No fitting was run.

## Files and validation

The CSVs separate fare evidence/candidates, state and timing, response/outcomes, aggregation, weather fits, decision register and source-required review results. implementation_migration_plan.md gives the nine ordered phases. verification.json contains exact acceptance-impact counts, source/evidence hashes and read-only checks. No production, test, training, old report or protected-date data was changed/accessed. Required review numerical content is distinguished from optional figure choices by the inherited result inventory.
