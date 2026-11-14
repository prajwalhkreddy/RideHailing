# Weather/time freeze recommendation

## Decision

**A final stable three-weather taxonomy is not established.** Exactly-three clustering was completed, but the full mean/SD partition changes substantially under both robust feature choices. The requirement to recommend a final mapping only when stable is not met. Do not disguise this as a resolved freeze by choosing a historical semantic map or selecting the highest silhouette across different feature spaces.

Recommended next-step design: retain **T1–T4** as the parsimonious time candidate, and carry the prespecified mean/SD three-cluster result as a **primary validation candidate only**. This is one conditional 12-scenario design, not approval to implement or to freeze weather. Final weather selection requires a methodology decision about tail-sensitive versus robust scenario similarity and rare-event reliability. No extra tuning, regrouping, or historical-map restoration was performed.

`THREE_CLUSTER_STABILITY = WEAK`

`T1_T4_SUPPORTED_UNDER_NEW_E = YES` **descriptively as an operational candidate**, not proof of optimal boundaries or independently replicated populations.

`FINAL_WEATHER_MAPPING_APPROVED = NO`

`WEATHER_TIME_TAXONOMY_FREEZE_READY = NO`

`GROUPED_DISTRIBUTION_REFIT_REQUIRED = YES`

`P_BASE_POPULATION_ALIGNMENT = PROFESSOR_CONFIRMATION_REQUIRED`

## Exact three-cluster candidates

| feature variant | WEATHER_GROUP_1 | WEATHER_GROUP_2 | WEATHER_GROUP_3 |
|---|---|---|---|
| Primary signed mean + SD | 1,2,3,5,7,8,9,12,15,16,17,21 | 13 | 14 |
| Robust median + IQR | 1,2,3,5,7,8,9,12,13,14,15,21 | 16 | 17 |
| 1%-per-tail trimmed mean + SD | 1,2,3,5,7,8,9,12,13,14,15,21 | 16 | 17 |

Use neutral identifiers because the broad groups mix physical weather categories. Primary aliases: mixed weather / Heavy Sleet / Light Snowfall. Robust aliases: mixed weather / Heavy Snowfall / Rain Shower. Aliases do not replace persisted code descriptions. FINAL_WEATHER_MAPPING.csv exposes all three assignments and explicitly marks the primary candidate **NOT_FROZEN**; its filename does not imply approval.

Robust variants agree exactly (ARI=1). Each differs from the primary on codes 13,14,16,17: aligned agreement 10/14=71.428571%, ARI=−0.158182. A shared large cluster makes raw agreement look better than partition stability. These are materially different partitions, not label permutations. Descriptive silhouettes are 0.465867, 0.500107, 0.681182; they describe different feature geometries and do not authorize selecting the last model.

## Reliability and historical comparisons

Primary singletons 13 and 14 have SD 53.372977 and 77.582343 but medians 0.985897 and 1.009273, close to the mixed cluster median 1.058745. Their isolation disappears with central/trimmed features, consistent with strong tail influence. This is not a formal tail-causality decomposition. Code 13 has 18,501 trips across four dates; 14 has 62,047 across twelve. Robust singleton 16 has 12,829 trips across four dates; 17 only 596 across **one** date and 510 positive e. Trip count is not a substitute for independent weather-event replication. Code 21 also has only one date. No claim of statistically significant or population-generalizable cluster differences is made; no independent-day bootstrap or equivalence test was run. Consequently significance of the partition changes is **not established**, while operational assignment differences are directly observed.

Compare after maximum-agreement label alignment (Hungarian assignment, code-unweighted); exact match/moved code lists are in the comparison CSV. Equal-optimum alignments can make particular match identities nonunique; ARI and maximum percentage remain label-invariant.

- Historical A (superseded numeric classes): primary agreement **50.000000%**, ARI **−0.167201**. One optimal alignment matches 1,2,3,9,12,17,21; moves 5,7,8,13,14,15,16.
- Historical B (unselected semantic manual groups): primary agreement **35.714286%**, ARI **−0.058788**. One optimal alignment matches 1,2,3,5,13; moves 7,8,9,12,14,15,16,17,21.

Historical A source: `data/processed/elasticity_v2/weather_code_class_mapping_final.csv`, provenance `final_elasticity_methodology.json` alongside it; it used r_L/r_P with different references/population and trimmed hourly features. Historical B: `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/manual_3bucket_reference_check_supported.csv`; old Record-029 r_P/r_L supported population. Differences cannot be attributed exclusively to epsilon orientation because population, reference and feature construction also changed. Neither historical mapping was adopted. Agreement is not a hypothesis test.

## Method and population

Authority: `notebooks/plan/Price_Elasticity_Weather_Scenario_Analysis_Explained.docx` and `notebooks/plan/Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx`. Both require scenario-first analysis and weather/time-conditioned distributions; neither freezes specific semantic groups or mandates 48 sensitivity distributions.

Existing safe input: `results/analysis/2026-11-09_academic_review_followup_pricing/jan01_mar15_analysis_cache.parquet`, selecting pickup_timestamp, fare and trip_distance. Timestamp bounds were asserted January 1 inclusive to March 16 exclusive. TLC miles were multiplied by 1.609344 before retaining **1.5 ≤ L < 75 km**. Weather joined many-to-one by pickup hour against `data/processed/weather/nyc_weather_processed_2026_01.parquet`, `_02.parquet`, `_03.parquet`; read filters required January 1 ≤ Datetime < March 16. No missing weather, no row multiplication. March 16 and March 17–31 were not calibration inputs.

P_base=22.354198442390455 USD; L_base=4.616983790655043 km. Compute r_P=(fare−P_base)/P_base, r_L=(L−L_base)/L_base and **e=r_L/r_P**. Exact-zero r_P yields undefined; nonfinite e is excluded from valid summary calculations only. No sign restriction, tail clipping or denominator cutoff is used for primary clustering. Positive counts are for future positive-distribution support assessment, not a change to signed descriptive statistics. The diagnostic near-zero flag is |r_P|<0.001, without exclusion.

N=6,967,155; valid e=6,967,155; positive=5,975,653; negative=991,502; zero=0; undefined=0. Fourteen raw codes retained. All reported SDs use ddof=0; empirical quantiles use NumPy linear interpolation.

Use **average-linkage agglomerative clustering, Euclidean distance, exactly K=3**, reusing the compatible approach in `results/analysis/2026-10-17_passenger_sensitivity_weather_scenarios/reproduce_analysis.py::cluster`. Do not execute that legacy script: it reads the wrong historical population. The legacy code uses unscaled features; **this task explicitly requires StandardScaler**, which is applied separately to each current feature pair across the 14 equally weighted scenarios (population scale). N is not a feature. Codes are sorted ascending and cluster IDs ordered by smallest member code. Seed 42 is fixed for reproducibility; the agglomerative algorithm itself has no stochastic initialization. No predictive/RL training or model loading occurred.

Variants: A=full signed mean/SD; B=median/IQR; C=mean/SD after removing floor(0.01*N) observations from each signed tail **within each raw weather scenario**, only for the clustering robustness diagnostic. This mirrors the historical 1%-per-tail trimming concept, not its old hourly features or assignments. Trimming never changes the primary population or final support counts. No algorithm or hyperparameter search was conducted. Standardization constants and silhouettes are recorded in WEATHER_CLUSTER_COMPARISON.csv.

Combined group SD was independently checked against sqrt(sum[n_i*(SD_i²+(mean_i−pooled_mean)²)]/sum[n_i]); it was never obtained by averaging SDs. Grouped medians/quantiles are calculated directly for descriptive reporting, not joint distribution training.

## Historical time contract and current evidence

Source: `data/processed/price_distance_sensitivity_record029/final_passenger_sensitivity_methodology.json`, status RECORD029_FINAL_SENSITIVITY_MODEL_READY. The decision authority is an explicit project methodology decision, not independently verified supervisor approval. Definitions:

- T1: [00:00,04:00), eight half-hour simulator slots.
- T2: [04:00,06:00), four slots.
- T3: [06:00,16:00), twenty slots.
- T4: [16:00,24:00), sixteen slots.

These were derived for old signed r_P/r_L supported Clear/Rain elasticity through exhaustive contiguous hourly partitions K=1..4 minimizing trip-weighted squared deviations of hourly medians. Four groups were frozen as a parsimonious project choice, not proven globally optimal. The separate 00–05/06–11/12–17/18–23 six-hour scheme was presentation-only. All T1–T4 boundaries align with 30-minute simulator slots; a distribution can serve several pricing slots without changing pricing cadence.

Current all-weather signed NEW-e statistics:

| time | total_N | mean | SD | median | IQR | positive_N | negative_N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 568009 | 1.184428 | 39.718462 | 0.945358 | 2.154444 | 450723 | 117286 |
| 2 | 138181 | 1.274906 | 52.426031 | 1.061394 | 2.721739 | 112315 | 25866 |
| 3 | 3014550 | 1.533648 | 26.867029 | 1.116165 | 1.498901 | 2628561 | 385989 |
| 4 | 3246415 | 1.403409 | 29.267690 | 1.033659 | 1.484232 | 2784054 | 462361 |

T1/T2 have greater dispersion than T3/T4; T2/T3 SD ratio is 1.951315. All four have differing central/spread summaries, though T3/T4 are closest in standardized mean/SD distance (1.015362), and T2/T4 median difference is only 0.027735. Thus retaining these boundaries has continuity and descriptive support; it does not prove four separate fitted families necessary or causal time effects. Weather composition can confound pooled time differences. Pairwise distances are descriptive standardized Euclidean comparisons, not p-values.

## Twelve versus 144 scenarios

Conditional on the PRIMARY mapping; all positive support counts use untrimmed e>0:

| metric | 3 × T1–T4 | 3 × 48 half-hours |
|---|---:|---:|
| possible groups | 12 | 144 |
| observed groups | 10 | 88 |
| absent groups | 2 | 56 |
| valid positive e total | 5,975,653 | 5,975,653 |
| observed groups ≥5,000 positives | 8 | 50 |
| minimum observed positive N | 450 | 86 |
| all-trip mass covered directly | 99.941698% | 99.031829% |
| positive-trip mass covered directly | 99.945696% | 99.057375% |
| observed groups requiring fallback | 2 | 38 |
| observed trip mass requiring fallback | 4,062 (0.058302%) | 67,454 (0.968171%) |
| observed positive mass requiring fallback | 3,245 | 56,328 |

For the robust alternative, 12 possible gives 9 observed/5 direct/99.933373% all-trip direct coverage; 144 possible gives 80 observed/48 direct/99.807310% coverage. The robust code17 group is never eligible for weather-only fitting (510 positives). These alternative counts are reported to avoid making the support recommendation depend on silently selecting the primary partition.

Half-hours are viable for the large mixed-weather group, but fragment rare events. Their separate fit estimates would have lower effective support; sampling instability was **not estimated by bootstrap**. They preserve real subperiod detail: half-hour median ranges within T1, T2, T3, T4 are respectively 0.909516–0.983342, 0.928594–1.405296, 0.988768–1.176970, 0.973707–1.145611. Weighted RMS half-hour median deviations from the pooled T median are 0.022814, 0.180001, 0.052081, 0.052151. T2 loses the most central variation when pooled. Half-hour SD variation can also reflect tail noise, not stable behavioral structure. No out-of-sample distribution-fit benefit has been demonstrated to justify 144 scenarios. Prefer T1–T4 for the next conditional analysis rather than 48 just to match simulator cadence.

## Support and fallback

Keep the proposed minimum **5,000 valid positive e**; no threshold changed. It is workable as a pooling gate but does not by itself validate fitted tails or independence. In the primary 12-group design, observed fallback counts are weather×time=8, weather-only=2, time-only=0, global=0. The **two absent combinations** would also use weather-only if encountered (full theoretical grid: 8 direct, 4 weather-only). These are fallback policies, not fabricated observations. Primary 144: observed levels 50/38/0/0; 56 absent groups would use weather-only.

Robust 12: observed levels 5/3/1/0; three absent groups would use time-only. Robust 144: observed levels 48/30/2/0; absent levels 0/18/46/0. Counts and positive mass for every variant are machine-readable in TIME_GROUP_COMPARISON.csv. Hierarchy is weather×time → weather-only → time-only → global. No positive pool is claimed fitted merely because N passes.

## Distribution next step and unresolved reference

`GROUPED_DISTRIBUTION_REFIT_REQUIRED = YES`. Existing raw-code×half-hour fits do not represent these merged weather/T groups; parameters cannot be averaged. Their software infrastructure can be reused, not their fitted parameters or family selections. After weather and P_base decisions, fit truncated normal, gamma and lognormal separately on approved positive populations, compare goodness of fit and tails, and verify any numerical convergence boundaries. No new family sweep was performed here: support counts establish practicality, not adequacy of any distribution family.

Carry forward P_base_[1,75)=22.354198442390455 and P_base_[1.5,75)=24.20370974379068 USD unchanged. P_BASE_POPULATION_ALIGNMENT=PROFESSOR_CONFIRMATION_REQUIRED. All current new-e results are conditional on the former as instructed. A changed reference would require recomputation before final taxonomy validation.

## Validation and limits

Asserted safe timestamp bounds, unique hourly weather join, N=6,967,155, all 14 codes mapped once per variant, exactly three labels per fit, finite features and label alignment. Each time design reconciles population and positive counts. Combined population means/SDs agree with within/between pooled formulas. No production code or configuration was changed; no implementation, predictive training, simulation, model loading or protected analytical rows. Only the five requested deliverables were written in this package; historical reports remain untouched.

The title/file names record the requested resolution task. They do not assert that a stable weather freeze has been achieved. The remaining weather decision is an evidence limitation, not an equation-number or document-availability blocker.
