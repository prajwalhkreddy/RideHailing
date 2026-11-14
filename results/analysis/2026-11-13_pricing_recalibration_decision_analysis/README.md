# Passenger sensitivity / NYC fare recalibration — decision analysis

**Analysis only. No methodology frozen; no implementation or training.**

Read the [academic decision summary](decision_support/ACADEMIC_RECALIBRATION_DECISION_SUMMARY.md) and [decision table](decision_support/ACADEMIC_DECISION_TABLE.csv). The summary separates numerical evidence from required academic choices.

## Scope and definitions

- Source: existing Jan 1–Mar 15 cache only,8,692,819 cleaned rows. March 16 saved request CSV used only for generator illustration; no protected rows or full-period trip Parquet opened.
- Matched array range:[1,75)km,148 bins,7,946,921 rows. A second ALL_SAFE scope retains the full restricted cache.
- Analytical new e=((L-L_base)/L_base)/((P-P_base)/P_base). No historical VALID filter, absolute transform, T0 truncation or arbitrary denominator threshold is used.
- P_base=22.354198442390455; rounded candidate22.3542; historical21.34586956773507 evaluated separately.
- L candidates:4.5,4.616983790655043,5.300620449409596 km. The last is an explicitly diagnostic ±1 USD conditional mean. Alternative windows/full-safe means are reported; none selected. Taxi-meter threshold not established.
- Epsilon quantiles:inverse empirical CDF, including weighted cases; SD:population. Fare quantiles:linear interpolation. Undefined ratios are counted separately.
- Distribution rows identify full signed versus strictly-positive conditional diagnostics. Positive components do not replace full populations. No final family selected.

## Headlines

At 4.5 km/lower-edge representation, equal-bin mean/SD=2.313937/0.407451; count-weighted=1.628232/0.579044; matched trip-level=1.427109/29.316258. Full-safe trip-level has8,692,819defined observations,1,105,611 negative,zero exact zeros andzero undefined values. Near-price denominators still generate large tails.

The contract remains incomplete: **PRICE_GENERATION_FORMULA_READY_FOR_IMPLEMENTATION=NO**. Post-action response with unchanged 13D state is **UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. Generator target probabilities remain an academic choice. Readiness counts:{'EVIDENCE_READY_FOR_FREEZE': 3, 'ACADEMIC_INTERPRETATION_REQUIRED': 12, 'MORE_ANALYSIS_REQUIRED': 3, 'BLOCKED_BY_MISSING_FORMULA': 1}.

## Artifact index

| Directory/file | Contents |
| --- | --- |
|array_a/array_a_verified.csv |Saved fare/counts plus actual physical mean distances |
|array_a/array_distance_representation_comparison.csv |9reference/representation arrays, with deviations andnew e |
|epsilon_population/population_statistics.csv |All populations, scopes, signs, weighted moments/quantiles |
|epsilon_population/distance_probability_mass.csv |Equal-bin versus passenger-frequency mass |
|epsilon_population/reciprocal_validation.csv |Same-reference reciprocal checks |
|zero_denominator/ |Cumulative dollar-gap bands, zero cases, bounded source examples and observed precision |
|distance_cutoffs/ |Recomputed-reference and fixed-reference filter comparisons |
|distribution_fits/distribution_fit_comparison.csv |Likelihood,AIC/BIC,KS,parameters andsupport compatibility for each declared scenario |
|distribution_fits/best_within_scenario.csv |Descriptive within-scenario AIC ordering, not a final model |
|distribution_fits/qq_diagnostics.csv |Numerical Q–Q data for all scenarios |
|distribution_fits/*.png |Reference-case histogram/CDF/Q–Q overlays; labelled central display windows |
|fare_bounds/ |Trip quantiles and actual clipping percentages for all candidate filters |
|reference_values/ |P/L candidate definitions, windows and precision consequences |
|pricing_contract/ |Literal PDF operations, candidate offers/coverage, clipping collapse andresponse semantics |
|decision_support/ |Academic table/summary plus saved-generator comparison |
|intermediate/ |Resumable numerical arrays and completion markers; not runtime artifacts |
|input_fingerprints.json; validation.json |Evidence integrity and focused numerical checks |

## Reproduction and checkpoints

Run only in this analysis namespace using the existing project Python environment: `analyze.py`, then `supplement.py`, then `fit_distributions.py`, then `write_report.py`, then `validate.py`. These scripts do not import simulator/model code. Each expensive phase and fit scenario is persisted. Full trip e arrays and duplicate-compressed values are analysis intermediates. Source checksum mismatch stops reuse; outputs are not production inputs. `progress.json` records current completion.

## Interpretation limits

Normal is only a baseline for signed trip values; tested positive families cannot fit negative values unchanged. Conditional-family rankings cannot select a full-population sampler. Weighted-bin likelihoods are descriptive frequency-weighted scores, not independent-trip evidence; effective-N columns expose this. KS is descriptive with no naive p-values. Empirical in-sample KS=0 is not validation. Central plot windows do not trim fit/statistic inputs.

Reference recomputation can dominate cutoff effects by moving P_base near discrete fares; consult the fixed-reference table before attributing SD changes to exclusions. No quantile bound is a verified NYC tariff. All seven candidate global offers remain distinct under tested clipping bounds; the missing long-distance formula could change this.

The saved March 16 request fixture is insufficient to certify the full hybrid generator. No synthetic replacement, request replay, policy evaluation, checkpoint load or training was performed. No existing README, historical results, source code or methodology was edited.
