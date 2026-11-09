from pathlib import Path
import json, pandas as pd, numpy as np, hashlib
R=Path(__file__).parent;V=R.parent/'2026-11-07_passenger_sensitive_pricing_v1';j=json.loads((R/'analysis_results.json').read_text());fs=j['fare'];ds=j['distance'];sg,ab,po=j['sensitivity'];cl={'EMPIRICAL_FLAT_FARE_REGION':'NOT_SUPPORTED','SIGNED_EPSILON_ANALYSIS_COMPLETE':'YES','CURRENT_T0_SUPPORT_CONSISTENT_WITH_NEW_ANALYSIS':'YES','COUNTERFACTUAL_ACCEPTANCE_ANALYSIS_COMPLETE':'YES','FIXED_GLOBAL_ACTION_SPACE_EMPIRICAL_COVERAGE':'WEAK','P_BASE_EMPIRICAL_SUPPORT':'MODERATE','L_BASE_EMPIRICAL_SUPPORT':'MODERATE','L_BASE_EQUALS_L_FLAT':'NOT_ESTABLISHED','METHODOLOGY_CHANGE_RECOMMENDED_BEFORE_REVIEW':'NO','PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED':'YES'}
def md(rows,cols):
 out=['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']
 for r in rows:
  def fmt(x):return f'{x:,.6f}' if isinstance(x,float) and np.isfinite(x) else str(x)
  out.append('| '+' | '.join(fmt(r.get(c,'')) for c in cols)+' |')
 return '\n'.join(out)
questions=[('A','Does the fare data support an empirical minimum-fare region?','The observed minimum is sparse and spread across distances; no stable region is established.'),('B','Should an empirical minimum replace the project platform minimum or remain separate?','The observed $0.01 minimum and the $18.143989 platform floor have different meanings; no substitution is justified automatically.'),('C','Should an L_flat mechanism be introduced?','Low-fare distance percentiles vary strongly with band definition; no cutoff has been identified.'),('D','Is absolute positive epsilon magnitude acceptable after signed-distribution review?','Negative historical values exist and transformation changes interpretation; positive proxy acceptability requires review.'),('E','Is T0 empirical resampling still defensible?','Its numerical construction reproduces exactly, but completed-trip proxies do not identify response probabilities.'),('F','Does the seven-arm global set adequately cover observed fare-distance levels?','Only 14.379973% overall coverage; materially different conditional coverage.'),('G','Should actions become distance-relative?','This is a possible modelling decision, not an implemented recommendation or validated alternative.'),('H','Should acceptance remain a pre-selection mask or become an outcome after selection?','Zero observed rejection is structural; the offline seven-action curve is not observed demand.'),('I','Should training continue before these questions are resolved?','Further training remains paused; this report supplies evidence, not authorization.')]
synthesis=[('positive epsilon magnitude','11.734355% signed negatives; abs construction preserved','Numerically yes; behavioural meaning unresolved','Transformation is a proxy, not a causal elasticity','YES'),('T0 truncation','8,598,805 supported; exact bounds reproduced','YES','No alternative support adopted','YES: scientific suitability'),('empirical resampling','Supported empirical skew/tails preserved; no distribution fitted','YES','No response-data validation claimed','YES'),('P_accept lower protection','Minimum arm accepts every request; pre-mask higher offers may fail','YES','Zero selected-offer rejection is structural','YES'),('global P_base','Restricted mean 21.352107 versus frozen 21.345870; distance medians differ','Numerically compatible as global reference','Not a universal conditional fare level','YES'),('global L_base','Price-conditioned reference; no flat-region equivalence','Provenance consistent','Do not equate reference with L_flat','YES'),('seven action factors','14.379973% full fare coverage; weak long-distance coverage','Narrow range, not broad empirical coverage','Review whether relative global adjustments suffice','YES'),('hard pre-selection mask','Observed acceptance 100%; offline highest factor 36.680761%','YES','Mask and demand-curve evidence must be separated','YES'),('gamma=.99/request','No new discount evidence in this analysis','UNCHANGED','No gamma recommendation from this task','NO new decision from this evidence')]
pd.DataFrame(synthesis,columns=['current_V1_decision','new_empirical_evidence','consistent','potential_implication','academic_decision_required']).to_csv(R/'academic_review_summary/current_v1_vs_new_evidence.csv',index=False)
report=f'''# Academic Review Follow-up: Passenger-Sensitive Pricing V1

## 1. Objective

This report supplies the additional descriptive evidence requested after review of Passenger-Sensitive Pricing V1. It examines observed fare–distance structure, the signed historical sensitivity distribution and its positive transformation, acceptable-price behaviour under the unchanged formula, counterfactual passenger acceptance, and empirical coverage of the existing action prices. It does not train or evaluate a new policy. Neither action redesign nor a different acceptance mechanism is implemented. Existing Episode25 performance remains a separate result, not a result of this analysis.

The distinction between measured data, deterministic formula illustrations, and simulator-derived development observations is central. Fare and distance summaries are descriptive properties of recorded completed trips. Historical epsilon is a derived variable under Record-029, not a measured individual willingness to pay. Same-distance price examples are controlled formula evaluations using empirical quantiles. Counterfactual acceptance applies the existing deterministic rule to saved development requests; it is not an estimate of real passenger response to interventions.

## 2. Data and protected split

The calibration population contains **{fs['N']:,} cleaned Jan1–Mar15 trips**. The Parquet read used the predicate `2026-01-01 <= pickup_timestamp < 2026-03-16`; no full-period DataFrame was loaded. The selected fields come from the authoritative Record-029 table, which retains the cleaned source rows including rows with unresolved epsilon. Fare-distance analyses retain all these rows; signed sensitivity additionally requires VALID, finite, nonzero epsilon. The source price is **TLC fare_amount**, in USD, not an assumed all-in passenger payment. Source trip_distance is miles and is multiplied by exactly 1.609344 before all km bins and plots.

March16 contributes only the saved Episode25 00:00–02:00 export, containing 2,838 requests. No simulator replay or checkpoint loading was necessary for this task. March17–31 was excluded from all analysis selections. Frozen P_base and L_base retain their previously approved full-cleaned-Jan–Mar provenance; this is an existing reference exception, not a new recalibration with protected dates. The restricted population is used to compare those references, not replace them.

The source filenames, date predicate and numerical checkpoints are recorded in `analysis_results.json`, `progress.json`, and `validation.json`. A restricted analysis cache makes the calculations resumable. Population counts reconcile with the previous V1 factor and sensitivity studies. Meeting example values were not treated as empirical measurements.

## 3. NYC fare-distance findings

Recorded fare ranges from **${fs['min']:.2f} to ${fs['max']:,.2f}**, with median **${fs['median']:.2f}**, mean **${fs['mean']:.6f}**, and population SD **${fs['population_SD']:.6f}**. Distance ranges from **{ds['min']:.8f} to {ds['max']:.8f} km**, with median **{ds['median']:.8f} km**, mean **{ds['mean']:.6f} km**, and population SD **{ds['population_SD']:.6f} km**. Full quantiles are in `fare_distance/population_statistics.csv`; no trimming was applied to these statistics.

The 0.5-km and 1-km tables preserve observed counts and fare quantiles in each populated bin. Intervals are lower-inclusive and upper-exclusive. Sparse long-distance bins remain visible; their quantiles should not be read as stable conditional fare estimates. The first 0–0.5-km bin has a median fare of $8.20, compared with $6.50 in 0.5–1 km and $7.90 in 1–1.5 km. Thus even the short-distance medians are not a single simple monotonic tariff description. No causal regression or tariff reconstruction is fitted.

The broad conditional medians increase substantially across the distance bands used for action review:

{md(j['coverage_by_distance'],['lower_km','upper_km','N','median_fare','P5_fare','P95_fare'])}

Fare per kilometre is reported as a descriptive ratio for positive distances. Very short distances can make that ratio large; it is not identified as a per-kilometre tariff. The cleaned population deliberately retains short trips and unusual positive fares under its existing rule. This report does not declare them invalid or introduce new exclusions.

## 4. Minimum-fare / L_flat evidence

**EMPIRICAL_FLAT_FARE_REGION = NOT_SUPPORTED** by these observations. The observed minimum, $0.01, appears in 283 trips, with median distance 7.58001024 km and maximum 40.3945344 km. It therefore does not identify a short-distance flat-price regime. Widening the fare band to $0.51 or $1.01 still selects very sparse, broadly distributed distances. This is a statement about the evidence, not a claim that no tariff or minimum-charge rule can exist elsewhere.

The requested candidate distance percentiles are shown below. They are descriptive quantiles of low-fare-like records, **not proposed cutoffs**:

{md(j['minimum_fare'],['candidate','fare_upper','N','distance_median','L_flat_P90','L_flat_P95','L_flat_P99','distance_max'])}

The P5-fare band has P90/P95 distances around 1.17/1.32 km, but its P99 is approximately 15.11 km. The exact-minimum band's P95 is approximately 21.85 km. These changes show strong sensitivity to the definition of a low fare. A maximum observation would be particularly unsuitable as an automatic L_flat. The P1/P5 fare bands also contain more than nominal 1%/5% shares because inclusive boundaries include ties.

The retained source has fare_amount, not an itemized fare-component breakdown. Consequently this analysis cannot attribute unusual low fares to surcharges, negotiated fares, adjustments, recording errors, or specific payment components. Repeated fare levels and ties are visible, but rounding alone does not demonstrate a flat-distance mechanism. No statutory NYC minimum is asserted. **L_base == L_flat remains NOT_ESTABLISHED**; no d_min or L_flat is implemented.

## 5. Signed epsilon distribution

The VALID finite nonzero signed population is **{sg['N']:,}**. Mean is **{sg['mean']:.6f}**, population SD **{sg['population_SD']:.6f}**, median **{sg['median']:.6f}**, and negative share **{sg['negative_pct']:.6f}%**. The signed distribution is therefore not equivalent to a positive response parameter before transformation. Negative values are retained in the descriptive evidence and are not labelled erroneous.

The statistics file reports population and sample SD, sign counts, quantiles and counts with absolute epsilon below 0.001, 0.005 and 0.01. The analysis population excludes exact zero by the specified rule; reported zero counts describe that selected population. Full-support histograms use 0.05 and 0.10 bin widths and symlog count axes. A separate P1–P99 central view explicitly excludes tails only from that display; it does not alter any calculated population. The ECDF is displayed at 2,001 quantile positions and is not a fitted distribution.

{md(j['shapes'],['distribution','skewness','excess_kurtosis','P95_minus_median_over_median_minus_P5','P99_over_P50'])}

Extreme moment values show why a mean and SD alone are insufficient. They do not prove that extreme records are invalid or that a specific parametric family should be adopted. The bounded example table contains actual source rows for the 20 largest positive, 20 most negative and 20 smallest absolute nonzero epsilon observations. Fare, distance and persisted relative deviations are included to expose the ratio structure. A source row can appear in more than one selection if definitions overlap; the selections are diagnostic sets, not population counts.

## 6. Current V1 epsilon support

The absolute distribution before support has mean **{ab['mean']:.6f}**, population SD **{ab['population_SD']:.6f}**, and median **{ab['median']:.6f}**. V1 first takes absolute values within the restricted VALID population, then applies inclusive positive P0.5–P99.5 bounds **[0.017809913104763053, 27.324599740032788]**. These bounds reproduce the saved V1 support exactly within the documented numerical check.

The supported population contains **{po['N']:,}** observations, mean **{po['mean']:.6f}**, population SD **{po['population_SD']:.6f}**, and median **{po['median']:.6f}**. It remains right-skewed and heavy-tailed descriptively. **CURRENT_T0_SUPPORT_CONSISTENT_WITH_NEW_ANALYSIS = YES** means the construction and population reconcile; it does not independently establish causal or behavioural validity. The active sampling method remains TRUNCATED_EMPIRICAL_RESAMPLING, with replacement and duplicate frequencies preserved. No extra epsilon floor or fitted family is adopted.

Central interval coverage is explicitly measured in `central_interval_analysis.csv`. Mean ± SD bands are empirical intervals, not Gaussian probability assertions. For signed epsilon, literal membership in the positive T0 bounds is reported separately from membership by absolute magnitude. This avoids conflating positive support with a symmetric signed interval. T0 is symmetric in nominal tail probability, not in numerical distance from zero. Inclusive ties explain why the retained share is not exactly 99%.

## 7. Passenger acceptable-price behaviour

The unchanged expression is `P_raw_c = P_base + (P_base/epsilon_c)*((L-L_base)/L_base)`, followed by `P_accept_c = max(0.85*P_base, P_raw_c)`. P_raw_c, P_accept_c and P_offer are distinct quantities. The first is a raw formula output, the second is an effective acceptance threshold, and the third is an offered action price. An effective threshold can exceed the platform's largest selectable fare without changing the action set.

The distance/epsilon table uses distance P10/P25/P50/P75/P90 and interpretable 2, 5, 10 and 20 km values within observed support. Epsilon values are quantiles of the supported empirical positive population. These are formula illustrations, not invented observed passenger records. At a fixed distance below L_base, decreasing positive epsilon makes the negative adjustment larger in magnitude. Above L_base, it enlarges the positive adjustment. At L_base, the raw expression equals P_base regardless of epsilon. This follows directly from the displayed equation and explains the crossing in the curves.

The raw-preference table uses each supported historical trip's own epsilon and distance, matching the earlier calibration diagnostic. It is not independent runtime resampling. Mutually exclusive categories and the separate protection count are:

{md(j['raw_categories'],['category','N','percentage'])}

The protection-applied row overlaps the first two categories and must not be added to their total. Applying a platform minimum does not erase negative raw outputs from the evidence. It also guarantees feasibility of the minimum arm for valid inputs, which must be considered when interpreting the absence of observed rejection.

## 8. Counterfactual acceptance curves

Every saved March16 request is paired with all seven current factors, yielding **19,866 request-action rows**. Only the offered price and the existing deterministic acceptance comparison are evaluated. No dispatch, vehicle response, policy retraining, or stochastic demand simulation occurs. For each request the same sampled epsilon and effective threshold from the authoritative export are retained.

{md(j['counterfactual'],['factor','offer_price','accepted_N','rejected_N','acceptance_pct'])}

The minimum factor accepts every request by construction. At 0.90, 1,279 requests accept and 1,559 reject; those 1,559 correspond to the forced requests whose only feasible factor is 0.85. The 1.15 factor accepts 1,041 requests. These results reconcile with the saved feasible masks. Higher prices cannot increase acceptance under the frozen threshold comparison, so the monotone curve is partly a logical consequence of the model.

This curve is a **model counterfactual acceptance curve**, not a causal demand estimate. Runtime selected offers had zero rejection because infeasible arms were masked before selection. The current analysis exposes what that mask removes. Separate tables stratify by distance, epsilon magnitude and raw-preference category; absent groups are not fabricated. No claim about counterfactual assignments or revenue is made, because changing offers could change driver matching and future fleet state.

## 9. Existing DQN action-space coverage

The seven global offers range from approximately $18.14 to $24.55. Exactly **1,250,025 / 8,692,819 = 14.379972710808772%** of historical fares lie within the inclusive 0.85–1.15 factor range. The result matches the previous factor study. Below-range fares account for 57.302274%; above-range fares account for 28.317753%. The denominator is the full cleaned restricted fare population, not only the positive-supported epsilon population and not March16 requests.

{md(j['coverage_by_distance'],['lower_km','upper_km','N','median_historical_factor','below_pct','inside_pct','above_pct'])}

**FIXED_GLOBAL_ACTION_SPACE_EMPIRICAL_COVERAGE = WEAK** is a descriptive judgement about representing the broad observed fare-distance population, not a new statistical gate or a replacement of the earlier MODERATE justification for a bounded experiment. Coverage is highest in 5–10 km at approximately 36.89%, falls to 3.13% in 10–15 km and below 1% in each longer band. One global price interval therefore does not adequately represent the full range of recorded fare levels across materially different distances.

That does not prove a different action space would improve the simulator or the real system. Recorded fares include heterogeneous trip conditions and are not direct policy-action labels. Whether the intended model needs broad fare-level representation or only adjustments around a global reference is an academic design question. No endpoints, spacing, state features or masks are changed here.

## 10. P_base / L_base review

P_base remains **21.34586956773507 USD**, originally the global mean of the full cleaned Jan–Mar fare population. The restricted mean is **21.352107453289896 USD**; their difference is approximately $0.00624, computed as restricted mean minus frozen reference. The restricted median is $15.60, with P25/P75 $10.00/$26.66. The mean alignment supports its provenance as a global reference, not its suitability as a conditional fare for all distances.

Around L_base, diagnostic windows of ±0.25, ±0.50 and ±1.00 km produce the following observed fare summaries; these windows do not redefine the reference:

{md(j['reference_near'],['window_halfwidth_km','N','mean_fare','median_fare','P25_fare','P75_fare'])}

L_base remains **4.856998243316242 km**, converted from the frozen price-conditioned mean of 3.01799878914405 source miles. Its historical construction uses fares within ±$1 of P_base; it is not the overall mean distance. The restricted overall mean/median distances are 5.548668/3.025567 km, with P25/P75 1.738092/6.115507 km. These contextual comparisons do not demonstrate that L_base is a minimum-fare threshold.

**P_BASE_EMPIRICAL_SUPPORT = MODERATE** and **L_BASE_EMPIRICAL_SUPPORT = MODERATE** are qualitative review classifications. Both have documented empirical construction; neither is validated as a universal behavioural or tariff parameter. No equivalence between L_base and L_flat is established. The existing constants remain unchanged while their modelling interpretation is reviewed.

## 11. What remains valid from V1

The numerical positive-support construction, existing reference values, and saved development mask counts reconcile. The accepted/unmatched distinction remains essential: this analysis does not reinterpret the 52 unmatched requests as passenger rejection. Current empirical sampling continues to preserve the supported distribution without introducing a Gaussian assumption. No new evidence here concerns Bellman discounting, reward definition or state dimensionality; those remain unchanged.

{md(pd.read_csv(R/'academic_review_summary/current_v1_vs_new_evidence.csv').to_dict('records'),['current_V1_decision','new_empirical_evidence','consistent','potential_implication','academic_decision_required'])}

Numerical consistency is narrower than scientific validation. The follow-up does not prove passenger willingness-to-pay identification, DQN superiority, convergence, a natural fare floor, or protected-period generalization. The new evidence strengthens the need to distinguish global-reference arithmetic from observed fare heterogeneity and masked feasibility from empirical demand response.

## 12. What needs academic decision

'''
for label,q,e in questions:report+=f'**{label}. {q}** {e}\n\n'
report+='''## 13. Recommended decision sequence

First agree on what the passenger-preference equation is intended to represent and how completed-trip sensitivity proxies should be interpreted. Second decide whether observed low-fare evidence supports any additional fare/distance mechanism; the current evidence does not supply a defensible automatic L_flat. Third clarify whether the action space should represent broad distance-conditioned fare levels or a deliberately narrow global adjustment experiment. Fourth decide whether acceptance remains a feasibility constraint or becomes a modelled outcome after an action. These are methodology decisions, not implementation fixes inferred from the current tables.

Only after those decisions should implementation changes, if any, be specified and tested, followed by an explicit decision on further DQN training. Any new acceptance model would require its own data justification and validation. The existing gamma, reward, 13D state and checkpoints remain untouched. This sequence proposes a review order, not a preferred replacement method, distribution family or approved training run.

**NO_METHODOLOGY_CHANGE_YET. FURTHER_TRAINING_REMAINS_PAUSED.**
'''
(R/'academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md').write_text(report)
charttext='# Chart Index\n\nCharts retain full statistical populations unless the limitation explicitly identifies a display-only window.\n\n| File | Question | Population | Main takeaway | Limitations |\n| --- | --- | --- | --- | --- |\n'
for r in j['charts']:charttext+='| ['+Path(r['file']).name+'](../'+r['file']+') | '+' | '.join(r[k] for k in ['question','population','main_takeaway','limitations'])+' |\n'
(R/'academic_review_summary/CHART_INDEX.md').write_text(charttext)
master=pd.read_csv(R/'academic_review_summary/master_results.csv');extra=[]
for key,value in cl.items():extra.append(dict(analysis_section='classification',metric=key,value=value,unit='category',population='See evidence-specific population',source_file='academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md',interpretation_status='QUALITATIVE_REVIEW_JUDGEMENT'))
for r in j['minimum_fare']:
 for k in ['N','L_flat_P90','L_flat_P95','L_flat_P99']:extra.append(dict(analysis_section='minimum_fare',metric=r['candidate']+'_'+k,value=r[k],unit='count' if k=='N' else 'km',population='Jan1–Mar15 low-fare band',source_file='fare_distance/minimum_fare_distance_analysis.csv',interpretation_status='DESCRIPTIVE_NOT_ADOPTED'))
pd.concat([master,pd.DataFrame(extra)],ignore_index=True).to_csv(R/'academic_review_summary/master_results.csv',index=False)
readme='''# Academic Review Follow-up — Passenger-Sensitive Pricing V1

**Analysis only. NO_METHODOLOGY_CHANGE_YET. FURTHER_TRAINING_REMAINS_PAUSED.**

Read the [academic review report](academic_review_summary/ACADEMIC_REVIEW_FOLLOWUP.md), then the [chart index](academic_review_summary/CHART_INDEX.md) and [master numerical summary](academic_review_summary/master_results.csv).

## Scope and findings

- Cleaned Jan1–Mar15 fare-distance N=8,692,819; TLC fare_amount in USD; source miles converted to km before all analysis.
- VALID finite nonzero signed epsilon N=8,685,488; frozen supported positive N=8,598,805; support exactly reconciled.
- No minimum-fare flat-distance region established: $0.01 observations cover widely varying distances. Quantile candidates are descriptive, not L_flat selections.
- Existing action range covers 14.379972710808772% of observed fares; weak coverage of broad fare-distance levels, distinct from earlier moderate bounded-experiment justification.
- March16 counterfactuals use the existing 2,838-row export only, producing 19,866 request/action rows. These are threshold-rule outcomes, not observed causal demand or dispatch simulations.

## Artifacts and conventions

`fare_distance/`: full descriptive statistics, populated 0.5/1-km bins, distance bands, minimum-fare bands and charts.

`sensitivity_distribution/`: signed, absolute and T0 statistics; sign/near-zero/range counts, intervals, shape metrics, bounded actual extremes and charts.

`acceptable_price/`: empirical-quantile formula illustrations, same-distance examples and paired historical raw-preference categories. Illustration rows are not actual passengers.

`counterfactual_acceptance/`: saved March16 requests crossed with seven offers; global and grouped acceptance curves. No simulation.

`action_space_validation/`: historical factors, inclusive-range coverage and distance-conditioned coverage with figures.

`reference_value_review/`: frozen-versus-restricted comparisons and descriptive windows around L_base; no reference change.

`academic_review_summary/`: full review narrative, current-decision/evidence matrix, chart index and headline metrics.

Bins are lower-inclusive/upper-exclusive; observed groups only. Quantile windows/support are inclusive, using linear interpolation. SD uses ddof=0 except explicitly labelled sample SD. Shape moments use bias=True empirical moment estimates. Full-range histograms retain tails; the signed central figure alone displays P1–P99. Raw protection counts overlap category rows and must not be summed with them. Low-fare bands overlap each other. No fare components beyond fare_amount are available to explain unusual records.

The authoritative Parquet is read with a Jan1–Mar15 predicate, as in existing V1 calibration, and the selected rows are checkpointed in `jan01_mar15_analysis_cache.parquet`. Protected-date rows are not selected into the analysis. `progress.json` records completed work; `analysis_results.json` preserves numerical summaries. No checkpoint/model is opened, no source evidence is written, and no production module is imported.

## Review classifications

'''+ '\n'.join('`'+k+' = '+z+'`  ' for k,z in cl.items())+'\n\nThese qualitative classifications are not new automatic methodology gates. Support consistency means numerical reconciliation, not behavioural validation. Reference support reflects provenance and descriptive alignment, not universal tariff validity.\n\n## Validation\n\nSee [validation.json](validation.json) for population, support, coverage, mask and subgroup reconciliation checks. No training, methodology change or March17–31 evaluation occurred.\n'
(R/'README.md').write_text(readme)
(R/'classifications.json').write_text(json.dumps(cl,indent=2)+'\n')
print('report_words',len(report.split()),'charts',len(j['charts']))
