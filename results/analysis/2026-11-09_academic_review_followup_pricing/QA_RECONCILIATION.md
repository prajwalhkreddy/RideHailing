# Academic Review Follow-up — Forensic QA

Overall: **numerical PASS; academically presentable WITH QUALIFICATIONS**. Existing analysis/evidence files remain unchanged. Only this report and its JSON are created.

## 1. Source population — PASS

N=8,692,819; cached timestamps 2026-01-01 00:00:00 through 2026-03-15 23:59:56. Source data/processed/price_distance_sensitivity_record029/authoritative_epsilon_jan_mar_2026.parquet, predicate pickup_timestamp >= Jan1 and < Mar16. TLC fare_amount renamed fare (USD); trip_distance in miles ×1.609344 gives km. Existing contract: finite positive fare, valid timestamps, 0<distance<=100 miles. Same cleaned population as previous factor study. Provenance: Record-029 README, cleaning_summary.json, analyze.py and restricted cache.

## 2. Minimum recorded fare — PASS_WITH_QUALIFICATION

Exact $0.01: 283; <=$0.50:310; <=$1:345; <=$2:1,012; <=$3:20,963; <=$5:110,999. Positive values comply with existing cleaning, but compliance does not establish operational legitimacy. Adjustment, anomaly or legitimate-fare explanations cannot be distinguished without component/source evidence. RAW_MINIMUM_OPERATIONALLY_REPRESENTATIVE=NO: 283 sparse records spanning varied distances do not establish a representative floor.

## 3. Flat-fare conclusion — PASS_WITH_QUALIFICATION

Exact-minimum band fare==0.01: distance P90/P95/P99=18.095463936/21.8468448/28.63022976 km. Fare-P5 band fare<=5.8, N=450,709: 1.17482112/1.31966208/15.11174016 km. NOT_SUPPORTED means this treatment provides no stable cutoff (B), not proof that no NYC flat-fare mechanism exists. Existing summary explicitly states this limitation.

## 4. Distribution sanity — PASS

Fare min/max/median=0.01/2555.20/15.60 USD; distance=0.01609344/160.82174592/3.02556672 km. Bounded examples below comply with finite positive fare and <=100-mile cleaning. They are retained, not certified error-free.

## 5. Action coverage — PASS

Inclusive observed_fare/21.34586956773507 in [0.85,1.15]: below 4,981,183 (57.30227444054685%); inside 1,250,025 (14.379972710808772%); above 2,461,611 (28.31775284864438%). Counts sum 8,692,819; percentages sum 100% within floating-point precision. Denominator includes unresolved epsilon rows, not only supported rows; not March16.

## 6. Distance coverage — PASS_WITH_QUALIFICATION

Inside-range percentages: 0–5 km 12.121778%; 5–10 36.892720%; 10–15 3.129452%; 15–20 0.200125%; 20–30 0.124831%; 30+ 0.527341%. WEAK is supported as broad fare-level representation, not a proof that the action set cannot serve a deliberately narrow adjustment experiment.

## 7. Counterfactual reconciliation — PASS

All seven factors have denominator 2,838; long table has 19,866 unique request/action pairs. Exact counts/rates below reconcile to original masks; no dispatch simulation.

## 8. Minimum-action acceptance — PASS

P_accept_c=max(0.85*P_base,P_raw_c) implies 0.85*P_base<=P_accept_c. Runtime feasible_mask uses exact candidate-price <= threshold, without tolerance. ACTION_085_ACCEPTANCE_100_PERCENT=STRUCTURAL_BY_CONSTRUCTION; not independent empirical evidence of universal acceptance.

## 9. Acceptance discontinuity — PASS_WITH_QUALIFICATION

At 0.90 the 1,559 rejected requests comprise 551 RAW_NONPOSITIVE +960 RAW_POSITIVE_BELOW_PLATFORM_MIN +48 RAW_WITHIN_PLATFORM_RANGE. The first 1,511 are protected to the minimum; another 48 have thresholds below the next arm. The remaining 238 within-range and 1,041 above-max requests accept. This motivates reviewing mask-versus-outcome semantics but does not identify the preferable design.

## 10. Sensitivity reconciliation — PASS

Signed VALID finite nonzero N=8,685,488; negative=11.734355052934276%; supported N=8,598,805; bounds [0.017809913104763053,27.324599740032788]. analyze.py applies dates then VALID/finite/nonzero, abs, positive quantiles/support. No historical signed-support filtering precedes abs. Persisted prior reconciliation matches.

## 11. T0 interpretation — PASS

YES denotes numerical reproduction only. Summary section 6 explicitly disclaims independently established causal/behavioural validity and does not claim optimality.

## 12. P_base — PASS_WITH_QUALIFICATION

Frozen 21.34586956773507 USD is full cleaned Jan–Mar mean fare. Restricted mean=21.352107453289896, median=15.60, P25/P75=10/26.66. Within ±0.25 km of L_base: mean fare22.4277488275, median20.50. MODERATE is defensible as qualitative global-reference support, not validated universal conditional pricing.

## 13. L_base — PASS_WITH_QUALIFICATION

Frozen4.856998243316242 km comes from3.01799878914405 miles, mean distance within ±$1 of historical P_base (479,000 trips). Restricted overall mean5.5486679697, median3.02556672, P25/P75=1.73809152/6.1155072 km. MODERATE is a provenance/context assessment, not behavioural validation. L_base==L_flat remains NOT_ESTABLISHED.

## 14. Extreme-value influence — PASS_WITH_QUALIFICATION

EXTREME_VALUE_SENSITIVITY=MODERATE overall, stronger for SD and observed-minimum interpretation. Above-P99 fares contribute27.595970% of squared deviations; distances25.785991%. Single-largest removal would shift means only from21.35210745 to21.35181597 USD and5.54866797 to5.54865011 km. No removal performed. Means exceed medians; quantiles expose skew. Extreme magnitudes do not change binary coverage membership once outside bounds; deleting records would change denominator and is not proposed. Sparse low-fare records undermine raw-minimum interpretation. These bounded verification reductions were needed because this influence was not quantified in saved outputs.

## 15. Cross-artifact/chart consistency — PASS_WITH_QUALIFICATION

Headline numbers in README, summary, master_results and supporting CSVs agree. Three master_results unit cells (signed_negative_pct, absolute_negative_pct,T0_negative_pct) say dimensionless instead of percent; numerical values are correct. Left unchanged under read-only scope; this QA supplies the explicit correction. Action-price chart has a full-range panel and labelled display zoom; CHART_INDEX.md records it, but analyze.py still describes the original single-panel generation. Chart numerical source is unchanged; exact presentation reproduction requires documenting the later layout step. No large plot regeneration done.

## 16. Claim audit — PASS

Targeted searches found causal/optimality/minimum-fare claims expressed as limitations, questions or negations. No unsupported positive assertion identified. Corrections to existing documents=0; unsupported claims corrected=0. Unit annotation and plot-provenance qualifications recorded here only.

## 17. Methodology preservation — PASS

NO_METHODOLOGY_CHANGE_YET=YES. Follow-up scripts only analyze historical/persisted development inputs and write their namespace plus the authorized canonical link. No model imports, checkpoint loads/writes, training or runtime change. Reference equations/support/actions/state/reward/gamma/mask remain as canonical specification.

## 18. Protected temporal scope — PASS_WITH_QUALIFICATION

PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED=YES for evaluation and analytical row selection. Cache contains Jan1–Mar15 only; development export March16 only. However source filename is full-Jan–Mar, and Parquet predicates can decode mixed-date row groups before filtering. A strict claim of zero file/byte access involving March17–31 is NOT ESTABLISHED by the saved evidence. No protected-date rows are used in analyses. This QA reads the restricted cache, metadata and saved outputs only; it does not reopen protected records.

## Exact acceptance reconciliation

| Factor | Accepted | Rejected | Acceptance % |
| --- | --- | --- | --- |
| 0.85 | 2838 | 0 | 100.0 |
| 0.9 | 1279 | 1559 | 45.06694855532064 |
| 0.95 | 1220 | 1618 | 42.98801973220578 |
| 1.0 | 1149 | 1689 | 40.48625792811839 |
| 1.05 | 1103 | 1735 | 38.86539816772375 |
| 1.1 | 1071 | 1767 | 37.73784355179704 |
| 1.15 | 1041 | 1797 | 36.680761099365746 |

## Bounded retained extreme examples

| Selection | Source row | Timestamp | Fare USD | Distance miles |
| --- | --- | --- | --- | --- |
| fare | 2070496 | 2026-01-25 00:43:10 | 2555.2 | 48.65 |
| fare | 5427931 | 2026-02-22 19:31:11 | 2084.1 | 41.62 |
| fare | 3570050 | 2026-02-01 03:47:35 | 1284.7 | 17.67 |
| trip_distance | 986907 | 2026-01-13 10:00:11 | 601.5 | 99.93 |
| trip_distance | 6224416 | 2026-02-09 08:20:12 | 297.42 | 99.58 |
| trip_distance | 3230525 | 2026-01-23 21:00:47 | 283.64 | 99.5 |

## Final classifications

```text
FOLLOWUP_ANALYSIS_NUMERICALLY_RECONCILED = YES
FOLLOWUP_ANALYSIS_ACADEMICALLY_PRESENTABLE = WITH_QUALIFICATIONS
FARE_MINIMUM_INTERPRETATION = RECORDED_MINIMUM_NOT_REPRESENTATIVE_OPERATIONAL_FLOOR
FLAT_FARE_EVIDENCE = NO_STABLE_CUTOFF_ESTABLISHED_NOT_PROOF_OF_ABSENCE
ACTION_RANGE_COVERAGE_RESULT = RECONCILED_WEAK_BROAD_FARE_COVERAGE
ACTION_085_ACCEPTANCE_INTERPRETATION = STRUCTURAL_BY_CONSTRUCTION
T0_NUMERICAL_CONSISTENCY = YES_NOT_OPTIMALITY_PROOF
NEW_METHODOLOGY_DECISION_REQUIRED_NOW = NO
NO_METHODOLOGY_CHANGE_YET = YES
PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES
PROTECTED_PERIOD_BYTE_LEVEL_NONACCESS = NOT_ESTABLISHED
EXTREME_VALUE_SENSITIVITY = MODERATE
```

The percentage-unit annotation and exact chart-layout reproducibility should be resolved in the final presentation preparation. Neither affects numerical reconciliation. Reference MODERATE classifications are qualitative, not statistical validation gates.
