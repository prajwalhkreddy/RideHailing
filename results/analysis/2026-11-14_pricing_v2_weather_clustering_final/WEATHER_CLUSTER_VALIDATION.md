# Weather-clustering rollback and representation gate

## Result: stopped before numerical clustering

The latest user decision supersedes the recent semantic weather freeze. **SEMANTIC_WEATHER_FREEZE=SUPERSEDED_BY_CLUSTERING_DECISION**. The historical semantic memberships {1,2,3,5}/{7,8,9,17}/{12,13,14,15,16,21} and their fits are preserved as provenance, not constraints or approved V2 groups.

WEATHER_CLUSTERING_REQUIRED=YES. MAX_ALLOWED_CLUSTER_SD=1.0 (inclusive). MAX_CLUSTER_SD=1.0. Exactly-three is no longer required. FINAL_WEATHER_CLUSTER_COUNT=UNRESOLVED; WEATHER_TAXONOMY_FROZEN=NO. WEATHER_GROUPS_DEFINED_BY_ELASTICITY_CLUSTERING=NOT_YET_ESTABLISHED: the intended method is authorized, but no successful final grouping exists. Do not set that success flag YES prematurely.

**The user's section 6 requires stopping if historical representations conflict. They do conflict.** No clustering population was chosen, no raw scenario statistics recalculated, no K search run, no minimum K inferred, and no final assignment manufactured. This is not a claim that no valid K mathematically exists; feasibility is unassessed until the SD population is specified.

## Methodology authority

Read `notebooks/plan/Price_Elasticity_Weather_Scenario_Analysis_Explained.docx`. It requires scenario counts, mean/SD, explicit similarity, and correctly pooled combined variance. Clear/cloudy/rainy are illustrative; no algorithm, unique representation, trimming/support restriction or SD<=1 rule is specified there. SD<=1 is the **current user decision**, not a retroactively attributed professor threshold.

## Historical implementation audit

| Source | Clustering representation/population | Algorithm and scope | Transform / seed / K | Acceptance rule |
|---|---|---|---|---|
| `data/processed/elasticity_v2/final_elasticity_methodology.json`, mapping `weather_code_class_mapping_final.csv` | 24 hourly 1%-per-tail trimmed signed mean features for each raw weather code; missing features same-hour pooled trimmed mean. Final class/hour SD separately used ALL untrimmed actual trips. | K-means Lloyd, weather-only membership from hourly curves | No scaling; Euclidean K-means objective; seed42, n_init50; fixed K3; 5% trim sensitivity. No winsorization recorded. | No SD<=1 acceptance condition recorded. |
| `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/reproduce_analysis.py::stats,scenarios,cluster` | Mean and population SD of unrestricted VALID individual signed observations; supported subset originally secondary | Average-linkage agglomerative Euclidean clustering; weather K2–8 and weather×six-hour K2–12 | No scaling; deterministic sorted scenarios/canonical labels; no stochastic seed required; no trimming | Every pooled cluster SD<4 and minimum cluster N>=1000, then silhouette preference. Not SD<=1. |
| Same folder `update_supported_analysis.py` | VALID individual signed observations restricted to prior inclusive P0.5–P99.5 support; now the primary decision population | Reuses the above `cluster` function through AST extraction; weather and weather×six-hour analysis | Unscaled mean/SD, not StandardScaler; deterministic; no per-tail trim; historical support restriction | SD<4 on supported observations; not SD<=1. |
| `results/analysis/2026-11-13_pricing_v2_weather_time_resolution/WEATHER_TIME_FREEZE_RECOMMENDATION.md` | Current candidate NEW-e unrestricted signed per-weather mean/SD; median/IQR and 1%-trimmed robustness alternatives | Standardized average-linkage agglomerative, weather only | StandardScaler by explicit then-current task; fixed K3; deterministic | No pooled SD<=1 acceptance. These were competing diagnostics, not a resolution of the current population gate. |

The October-2 record explicitly documents 225 observed hourly cells and 111 clustering-only imputed features. Its final SD and its clustering feature representation are different quantities. Applying SD<=1 to the 24 hourly means instead of actual-trip e would silently change the population under test. The archived generating-results paths in its JSON are historical references; the frozen metadata and actual saved mapping establish the method, not a newly executed generator.

October-2 epsilon was **r_L/r_P**, same orientation as V2 but different references, dates and feature processing. October-17 Record-029 analysis used **r_P/r_L** on its historical population/support. The current task requires r_L/r_P and prohibits old support reuse. Thus chronology alone does not establish a compatible single representation. Neither historical algorithm is selected or executed here. In particular, the October-17 code actually uses **unscaled**, not standardized, features; earlier descriptions suggesting otherwise do not override the executable source.

The relevant historical alternative categories are D (hourly means based on trimmed individual e), A (raw valid signed individuals) and E (support-restricted valid signed individuals). Positive-only is not established as the historical weather-clustering population. Positive-only distribution fitting must not silently become the clustering population.

## Exact unresolved decision

Specify the observation unit and population on which the new pooled SD<=1 applies: current valid signed individual e; an explicitly authorized trimmed/support-defined population; or a defined hourly/time aggregate population. If an aggregate representation is selected, explicitly resolve its weighting and distinction from trip-level combined SD. The two choices—feature representation and acceptance-test population—must not be conflated. Do not choose a population merely because it can satisfy the threshold.

No new support bound, positivity filter, trimming rule, algorithm or K has been invented. The prior forced-K3 result is not reused. Once population/representation is resolved, evaluate K from the smallest sensible value and require every code to be covered once with every cluster passing **inclusive** SD<=1. Use pooled variance sum[n_i*(SD_i²+(mu_i−mu_pool)²)]/sum[n_i], not mean(member SD). Sample SD is a separate reporting quantity, not a silent replacement for the population-SD gate.

## Preserved V2 contract

Planned equation remains e=((L−L_base)/L_base)/((P−P_base)/P_base), with candidate P_base=22.354198442390455 USD and L_base=4.616983790655043 km, Jan1–Mar15 and 1.5<=L<75 km. No calculation under this contract was performed in this stopped task. Negative retained diagnostically; zero numerator/nonzero denominator gives zero; denominator zero undefined; near-zero flagged without unauthorized filtering. Existing reference-approval issue remains unchanged.

TIME_TAXONOMY=T1_T4 retained: [00,04),[04,06),[06,16),[16,24). No 48-bin reopening. Threshold 5000 positive and hierarchy weather-cluster×time → weather-cluster-only → time-only → global remain. Exact scenario count, direct-fit count and fallback counts are **NOT_EVALUATED**, not zero: they depend on final K and membership. Previous semantic 12-scenario counts/routes are provenance only, not valid new-cluster counts.

GROUPED_DISTRIBUTION_REFIT_REQUIRED=YES. Semantic-group fits are SUPERSEDED_BY_CLUSTERING_DECISION for current grouping purposes, but preserved byte-for-byte. No new fitting was performed.

## Rare-code limitation

Existing safe-period diagnostic evidence in `2026-11-13_pricing_v2_weather_time_resolution/WEATHER_CLUSTER_COMPARISON.csv` records code17 N=596 across one pickup date (510 positives). This is historical diagnostic evidence, not a newly selected clustering population. Its reliability and pooled-SD implication must be assessed under the resolved population; it is not established as the cause of failure or assigned semantically. No new rare-code standalone cluster is approved.

## Deliverables and empty-table semantics

The three requested CSVs contain headers only because the hard population gate stopped their computation. They are intentionally empty, not zero-result datasets or a valid mapping. No all-14 assignment exists. RAW_WEATHER_CLUSTER_INPUTS.csv must not be read as evidence of zero calibration observations; WEATHER_CLUSTER_CANDIDATES.csv does not mean all K failed; FINAL_WEATHER_CLUSTER_MAPPING.csv does not supply runtime assignments.

All older numeric/semantic/forced-K3 reports and the previous final-approval package remain unchanged as requested. This report and the targeted final-freeze registry supersede only their weather-membership, weather-scenario-count/fallback-specific and semantic-fit conclusions. Their time and unrelated proposal approvals remain as recorded. Older statements that semantic grouping is frozen are now historical, not current authority.

## Validation and boundaries

Only this five-file package and the three authorized final-freeze registry files were written. Direct comparison preserves unrelated registry rows exactly. Targeted hashes verify old mapping, semantic calibration, forced-K3 reports and previous final-approval files unchanged. No production edits, data preparation, trip-level reads, protected March17–31 analytical rows, model loading, training, simulation, checkpoint or replay changes.

Completion status: semantic rollback complete; population/representation audit complete; numerical clustering **BLOCKED_BY_HISTORICAL_REPRESENTATION_CONFLICT**. WEATHER_CLUSTER_STABILITY=NOT_ASSESSED. No scientific success verdict is implied by completing the report.
