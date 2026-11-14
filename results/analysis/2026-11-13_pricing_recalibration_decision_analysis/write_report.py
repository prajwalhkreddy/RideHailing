from pathlib import Path
import sys,json,csv,collections,re,hashlib
import numpy as np,pandas as pd
R=Path(__file__).parent;sys.path.insert(0,str(R));from analyze import save,js,checkpoint,P,OLD

def table(df,cols=None):
 if cols is not None:df=df[cols]
 def fmt(v):
  if isinstance(v,(float,np.floating)):return '' if np.isnan(v) else f'{v:,.6f}'
  return str(v).replace('|','/').replace('\n',' ')
 return '| '+' | '.join(df.columns)+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'

def main():
 assert (R/'intermediate/fits_complete.json').exists()
 cand=json.loads((R/'reference_values/candidates.json').read_text());L=cand['L_candidates'];lc=L['C_PRICE_NEAR_PM1']
 stats=pd.read_csv(R/'epsilon_population/population_statistics.csv');masses=pd.read_csv(R/'epsilon_population/distance_probability_mass.csv');cuts=pd.read_csv(R/'distance_cutoffs/filter_scenarios.csv');fixed=pd.read_csv(R/'distance_cutoffs/fixed_reference_comparison.csv');fare=pd.read_csv(R/'fare_bounds/trip_fare_quantiles.csv');clips=pd.read_csv(R/'fare_bounds/quantile_clipping_effects.csv');fits=pd.read_csv(R/'distribution_fits/best_within_scenario.csv');precision=pd.read_csv(R/'reference_values/epsilon_precision_effects.csv');bands=pd.read_csv(R/'zero_denominator/price_gap_bands.csv');gen=json.loads((R/'decision_support/generator_comparison.json').read_text());prob=pd.read_csv(R/'decision_support/generator_distance_comparison.csv');rep=pd.read_csv(R/'array_a/array_distance_representation_comparison.csv')
 # Near-denominator diagnostics for bin populations, complementing full safe-trip counts.
 nb=[]
 for (c,r),g in rep.groupby(['candidate','representation']):
  for pop,w in [('BIN_UNWEIGHTED',np.ones(len(g))),('BIN_COUNT_WEIGHTED',g.N.to_numpy())]:
   for gap in [0,.01,.05,.1,.25,.5,1]:
    mk=abs(g.P-P)<=gap;nb.append(dict(candidate=c,representation=r,population=pop,fare_gap_le=gap,relative_gap_le=gap/P,N_units=int(mk.sum()),mass=float(w[mk].sum()),percentage=100*w[mk].sum()/w.sum()))
 save('zero_denominator/bin_price_gap_bands.csv',nb)
 refs=[dict(candidate='A_LOWER_EDGE',L_base_km=4.5,definition='Nearest mean-price bin lower edge',data_basis='Existing 148-bin array',price_at_reference=21.983204441915087,distance_interpretation='Lower edge of [4.5,5.0), not mean physical distance',zero_implication='One lower-edge bin e=0; weighted mass310535; no exact trip zero observed',advantages='Reproduces document example',limitations='Reference price differs from P_base; changing distance representation removes the zero'),dict(candidate='B_INTERPOLATED',L_base_km=L['B_INTERPOLATED'],definition='Linear interpolation of mean fare against lower-edge labels',data_basis='4.5 and5.0 bins',price_at_reference=P,distance_interpretation='Interpolation coordinate, not measured meter threshold',zero_implication='No observed bin/trip exact zero; inserting interpolated(P_base,L_base) yields0/0',advantages='Mean-price curve crossing by construction',limitations='Depends on bin coordinate and local linearity; no observed trip implied'),dict(candidate='C_PRICE_NEAR_PM1',L_base_km=lc,definition='Mean physical distance for abs(fare-P_candidate)<=1 in array range',data_basis='346880 permitted trip observations; diagnostic ±1USD window',price_at_reference=22.483206469961945,distance_interpretation='Actual conditional mean distance',zero_implication='No exact zero observed; sign pattern differs',advantages='Uses individual physical distances',limitations='Window not newly approved; does not make mean fare exactlyP_base; not a meter floor'),dict(candidate='D_TAXI_METER',L_base_km=np.nan,definition='Distinct taxi-meter threshold',data_basis='Not established by supplied empirical evidence',price_at_reference=np.nan,distance_interpretation='NOT_ESTABLISHED',zero_implication='No numeric scenario invented',advantages='Concept distinguished from reference distance',limitations='Requires academic/source evidence')]
 # Exact values from saved source, not hand-rounded narrative.
 a=pd.read_csv(R/'array_a/array_a_verified.csv');refs[0]['price_at_reference']=float(a.loc[a.lower_distance_km.eq(4.5),'mean_fare'].iloc[0]);near=pd.read_csv(R/'reference_values/price_conditioned_candidates.csv');refs[2]['price_at_reference']=float(near.query("scope=='ARRAY_RANGE' and half_window_USD==1").mean_fare.iloc[0]);save('reference_values/L_base_evidence.csv',refs)
 ops=[('Observed distance','PDF pp6,9: sample bin with p_i=N_i/sum N, then continuous distance within bin','PARTIALLY_SPECIFIED','Within-bin law and conditional OD/duration relationship unspecified'),('Effective distance','PDF p8: L_effective=max(L_observed,L_base)','FORMULA_EXPLICIT','Physical observed distance must remain unchanged'),('Base price','PDF p2: sum N_i P_i / sum N_i; candidate22.35419844≈22.3542','FORMULA_EXPLICIT','Final calibration filters and precision still need selection'),('Sensitivity calculation','PDF p3: e=((L-L_base)/(P-P_base))*(P_base/L_base)','FORMULA_EXPLICIT','Population, sign/zero support and denominator treatment unresolved'),('Sensitivity sampling','PDF pp6–7: independent common fitted population','PARTIALLY_SPECIFIED','No fitted family/parameters or mixture/zero specification'),('Zero sensitivity','PDF p6: if e=0 then P=P_base','FORMULA_EXPLICIT','Piecewise modelling branch, not definition of0/0'),('Short-distance fare','PDF p8: if L<=L_base then P=P_base','FORMULA_EXPLICIT','Interaction with action factor/clipping requires decision'),('Long-distance reference fare / P_max','PDF pp7,9: compute from approved pricing formulation','UNSPECIFIED','Complete equation and relation to factor-derived fare missing'),('Action factor','PDF p7: P_action=P_base*alpha; seven factors illustrative','FORMULA_EXPLICIT','Final factors and relation to distance-dependent reference remain open'),('Generated price','PDF p9: compute reference fare and apply pricing action','PARTIALLY_SPECIFIED','No equation combines long-distance fare, sensitivity,P_max and aP_base'),('NYC clipping','PDF p7: P_final=min(P_NYC_upper,max(P_NYC_lower,P_generated))','FORMULA_EXPLICIT','Exact bounds unresolved'),('Passenger response','PDF p9: clip then evaluate approved utility/response model','PARTIALLY_SPECIFIED','No complete response equation or explicit resolution of current preselection mask')]
 save('pricing_contract/source_document_contract.csv',[dict(operation=o,literal_source_expression=t,status=s,unresolved=u) for o,t,s,u in ops])
 (R/'pricing_contract/RESPONSE_AND_GENERATOR_CONTRACT.md').write_text('''# Response, observability and generator implications

## Mask information

For ascending candidate prices c_j=a_jP_base, m_j=1[c_j<=P_accept]. The mask is a feasible prefix of length K. For0<K<7 it reveals c_(K-1)<=P_accept<c_K; K=7 reveals P_accept>=c_6. Current minimum protection ensures K>=1. This is passenger-specific interval information used by exploration, greedy selection and Bellman maximization, although raw Q(s,a) does not receive epsilon, distance or the threshold as features. Equal13D states can have different feasible actions.

If the mask disappears, neither epsilon nor request distance/threshold is present in the unchanged13D state. Context may predict an aggregate acceptance distribution but cannot distinguish individual passengers with identical state and different independent epsilon draws. Classification: **POST_ACTION_RESPONSE_WITH_UNCHANGED_13D_STATE=UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. This does not claim the entire simulator is unobservable. No features are added.

## Explicit rejection decisions required

- Define accepted/rejected outcome and whether clipped offer or proposed action is evaluated.
- Define reward for rejection separately from accepted-unmatched; no penalty/value is selected here.
- A selected rejected action requires an explicit transition policy; current no-action skip must not silently be reused.
- Specify dispatch bypass and ensure no vehicle/commitment/energy change for rejected requests.
- Link to the next chronological actionable/selected request under the chosen semantics; settle terminal handling.
- Define attempted/accepted/assigned counters. Existing mu/sigma/F_hat use successful assignments; document whether that remains unchanged. Rejected offers must not accidentally enter successful-fare statistics.
- Specify replay fields for selected action, realized/clipped offer, outcome, reward, next state/mask and semantic version. If masks cease to represent passenger feasibility, define target maximization accordingly.

## Hybrid generator

Current origin counts come from forecasts; intact January rows preserve OD, distance, duration and fare jointly. Sensitivity is independently resampled. Array a pools Jan1–Mar15 distances conditional on1<=km<75. These distributions need not match: origin weighting, period and truncation differ.

Saved March16 four-slot request export is a development illustration only, not an expected-generator distribution or selection dataset. No new requests, checkpoint load or simulation occur. `generator_comparison.json` and `generator_distance_comparison.csv` quantify this finite fixture against array a. Distances are already empirical, so a separate independent marginal draw is not automatically necessary. Whether to force array-a probabilities as the runtime target is **ACADEMIC_DECISION_REQUIRED**. Preserve the baseline and physical joint fields until that choice is explicit.
''')
 # All required decisions, with status distinguishing evidence from approval.
 dec=[]
 def add(name,options,evidence,tradeoff,interpretation,status):
  dec.append(dict(decision=name,options=options,numerical_evidence=evidence,tradeoff=tradeoff,architecture_consequence='Version calibration and downstream price/response dependencies; no current change',training_consequence='No training authorized; changed contract cannot exactly resume old replay',recommended_evidence_based_interpretation=interpretation,academic_approval_required='YES',readiness=status))
 E='EVIDENCE_READY_FOR_FREEZE';A='ACADEMIC_INTERPRETATION_REQUIRED';M='MORE_ANALYSIS_REQUIRED';B='BLOCKED_BY_MISSING_FORMULA'
 add('EPSILON_ORIENTATION','relative distance/price versus historical reciprocal','Max reciprocal-product error2.220446049250313e-16 at identical references','Formula direction differs from old proxy','PDF direction is explicit; freeze as replacement only after dependent zero/population semantics are agreed',E)
 add('EPSILON_POPULATION','unweighted bins / count-weighted bins / individual trips','At4.5 lower edge:mean2.313937 vs1.628232 vs1.427109(array trips)','Equal bins strongly overweight rare long distances; weighted bins lose within-bin spread','Count weighting represents passenger frequency better than equal bins if passengers are the sampling unit; not a final selection',A)
 add('EPSILON_SIGN','signed / explicitly transformed / mixture','Matched trip population has1044072negative values; bin signs vary with representation','Positive-only families cannot model signed population unchanged','Do not silently abs the newly oriented ratio; choose behavioural interpretation',A)
 add('EPSILON_ZERO_RULE','piecewise price=P_base; explicit0/0 and price-denominator convention','No exact price-zero denominator; one lower-edge zero bin with310535weighted mass','Zero is representation dependent; near-zero price gaps still produce huge tails','Keep zero-price modelling branch distinct from undefined-ratio convention',A)
 add('EPSILON_DISTRIBUTION','empirical / normal / gamma / lognormal / Weibull / exponential with support definition','Positive component:Weibull best unweighted;lognormal weighted/trip at reference4.5; fit mismatch remains','Conditional fits exclude sign/zero mass and cannot silently replace whole distribution','No universal family dominates; repeat assessment after population/sign freeze with appropriate validation',M)
 add('LOWER_DISTANCE_CUTOFF','1 /1.5 /2km','Retained7946921/6967155/5974083','Higher lower limit removes large demand mass and changes reference-price alignment','Treat cutoff as substantive population choice, not outlier housekeeping',A)
 add('UPPER_DISTANCE_CUTOFF','75km versus existing<=100miles sensitivity only','Only1459safe records at>=75km; added to range1+','Small trip mass but tail statistics/reference shifts possible','75km has clear mass accounting; do not infer that all longer trips are invalid',E)
 add('MIN_BIN_COUNT','50 /100','Individual exclusion247/1665trips','Stability of tail-bin means versus retained shape','Numerical consequences available; threshold is not self-validating',A)
 add('SPARSE_BIN_SEMANTICS','individual bins / contiguous prefix','50:142bins vs134;100:121 vs120','Holes versus shorter contiguous range','Specify semantics explicitly; neither follows automatically from minimum count',A)
 add('P_BASE_PRECISION','exact22.354198442390455 / rounded22.3542','Price difference1.557609545e-6USD; max full-trip e difference5.728764','Tiny price rounding can affect extreme ratios','Preserving exact arithmetic is better for reproducibility; display rounding can be separate, pending approval',E)
 add('L_BASE','4.5edge /4.616983790655043interpolation /5.300620449409596conditional / separately evidencedmeterthreshold','Changing representation creates a negative bin where lower-edge reference giveszero','Reference distance is not meter base distance; ±1window is diagnostic','Do not equate L_base and L_flat; select definition based on modelling purpose',A)
 add('NYC_LOWER_BOUND','empirical lower quantiles plus source/tariff validation','Allsafe P0.1=3;P0.5/P1=4.4;P2.5=5.1;P5=5.8','Recorded fare quantiles are not legal or universal willingness-to-pay floors','Quantiles are diagnostics; obtain fare-component/source justification before naming NYC limit',M)
 add('NYC_UPPER_BOUND','empirical upper quantiles plus source validation','Allsafe P95=58.19;P99=78.6;P99.9=135.3','Trip fare limits differ from bin-mean maxima','Do not use rawmax2555.2 or binmean207.09 automatically',M)
 add('PRICE_GENERATION_FORMULA','explicit long-distance reference/e/P_max/action composition','PDF supplies separate floor,action andclip operations; combination equation absent','Different compositions imply different offers and response','Obtain complete piecewise equation; do not infer it from components',B)
 add('ACTION_FACTORS','seven examples / alternative approvedfactorvalues','Old range18.143989–24.547750;new19.001069–25.707328','Global interval cannot represent broad fare-distance curve','Evaluate after complete price-generation rule; not finalized',A)
 add('ACTION_COUNT','7 or another approvedcount','All135global bound/base combinations retain7distinctprices','No current clipping-collapse evidence, but distance-dependent offers unspecified','Do not infer a new count from incomplete pricing equation',A)
 add('ACCEPTANCE_SEQUENCE','preselectionmask / postactionresponse','Mask encodes threshold interval absent from13Dstate','Removing mask removes individual threshold information','Current unchangedstate is unobservable with respect to passenger threshold; agree response contract',A)
 add('REJECTION_REWARD','explicit approved reward andtransition semantics','Current selected feasibleoffers accepted; unmatchedreward0; rejection branch absent','Penalty/objective and temporal linkage change learning target','No reward value selected; do not silently reuse no-action or unmatched handling',A)
 add('REQUEST_GENERATOR','keep hybrid / explicitly targeted jointarray sampling','Development conditionalTV=.131465,KS=.120322;327/2838below1km','Forecast origin weighting versus aggregate marginal; preservephysicalcoupling','Keep baseline pending decision; independent distance/OD sampling unjustified',A)
 save('decision_support/ACADEMIC_DECISION_TABLE.csv',dec);counts=collections.Counter(d['readiness'] for d in dec)
 primary=stats[(stats.candidate=='A_LOWER_EDGE')&stats.representation.isin(['LOWER_EDGE','ACTUAL_TRIP'])]
 fitprimary=fits[(fits.L_base_candidate=='A_LOWER_EDGE')&fits.distance_representation.isin(['LOWER_EDGE','ACTUAL_TRIP'])]
 repstats=stats[stats.population.eq('BIN_UNWEIGHTED')]
 cuttable=cuts[cuts.L_definition.eq('FIXED_4P5')]
 preci=precision[precision.candidate.eq('A_LOWER_EDGE')]
 conditional_mass=prob.loc[prob.lower_km.lt(5),'development_N'].sum()/gen['in_array_range_N']*100
 summary=f'''# Academic recalibration decision summary

## 1. Why recalibration is needed

The supplied *Passenger Price Sensitivity and NYC Fare Calibration* document asks for a population-based sensitivity model, empirical distance demand, a base-fare mechanism and supported NYC fare bounds. These changes go beyond replacing a numerical constant. The current V1 uses a different historical ratio orientation, a positive absolute-value pool, a platform-protected acceptance threshold and seven pre-masked offers. The new document supplies several mathematical components but does not fully connect long-distance reference fare, sensitivity, maximum price and selected offer.

This analysis supplies evidence for academic decisions. It does not freeze V2, modify V1, load a learner, train, or alter simulation. All recalibration observations come from the already restricted Jan1–Mar15 cache. March16 appears only as a labelled saved request-stream illustration. No March17–31 analytical rows or full-period trip files were opened. Historical reference values and documents are reused as provenance, not recalculated from protected periods.

Two comparison scopes are reported. ARRAY_RANGE contains7,946,921 observations with1<=distance_km<75, enabling a like-for-like comparison with148 bin proxies. ALL_SAFE retains all8,692,819 cleaned Jan1–Mar15 trips and exposes effects hidden by the array range. Neither scope inherits historical Record029 VALID status or T0 bounds. Original physical fields remain unchanged.

## 2. Formula orientation

For this analysis only, r_P=(P-P_base)/P_base, r_L=(L-L_base)/L_base, and new e=r_L/r_P. The historical ratio is r_P/r_L. On the same observation with the same references and both deviations finite/nonzero, their product equals1. The maximum numerical error across the tested reference scenarios is2.220446049250313e-16, with zero mismatches above1e-12. This validates algebra, not a behavioural interpretation.

The current historical references differ from the new candidates, so taking a reciprocal of the old supported pool is not equivalent to recomputing new e. Absolute values would also discard sign. No absolute transformation is applied here. The saved historical epsilon is included only for source comparison in bounded extreme examples; a separately named same-reference reciprocal prevents confusing these quantities.

The new denominator is price, not distance. Historical exclusion of distances near L_base therefore cannot be inherited. New validity requires finite paired inputs and a nonzero price deviation. Exact-zero denominators are recorded separately rather than replaced by arbitrary constants. Near-zero denominators remain in all descriptive statistics and fits.

## 3. Array-a provenance

The existing half-kilometre fare CSV matches its checksum in the completed context audit. Its148 lower-edge labels run1.0–74.5; the represented interval is[1,75), not148 exact trip distances. Counts sum7,946,921 and weighted fare sum177,647,049.04USD. P_base_candidate is exactly22.354198442390455USD in the persisted calculation;22.3542 is the rounded document value. Raw preparation and fare aggregation were not rerun.

Actual within-bin mean distance was calculated from the permitted cache while checking count alignment. This is the only new bin-distance aggregation. Lower edge, midpoint and observed mean are distinct representations. The lower edge reproduces the document example; neither it nor the midpoint is automatically a true passenger distance. Bin mean fare is a conditional average, not a statutory tariff or individual price.

The price-near reference candidate uses the explicitly diagnostic ±1USD window around the new price, restricted to the array range:346,880 observations give L_base={lc:.15f}km and mean fare≈22.483206USD. Windows±0.25/0.50/1/2 and the full safe population are separately reported. The ±1 choice borrows a historical diagnostic width; it is not a newly approved V2 definition. Full-safe ±1 mean distance is≈5.207588km. No taxi-meter threshold is established.

## 4. Population weighting comparison

At P_base={P} and L_base4.5, the primary results are:

{table(primary,['population','scope','finite_mass','mean','population_SD','median','negative_mass','zero_mass','undefined_mass'])}

Unweighted bins allocate one vote to every distance interval, regardless of passenger volume. Count weighting instead assigns the bin proxy to its observed number of trips, but still suppresses within-bin variation. Trip-level ratios restore that variation and price-denominator instability. The ratio evaluated at mean fare/distance is not the mean of individual ratios.

{table(masses)}

Thus1–5km receives5.405405% of equal-bin probability but66.517322% of count-weighted probability. Conversely60–75km receives20.270270% versus0.025242%. These are radically different implied populations. If the modelling unit is passengers, frequency weighting has a clearer population interpretation than equal bins, but it does not establish that a bin-average ratio is a valid individual sensitivity. That remains an academic choice.

Statistics use population SD. Epsilon quantiles use the left inverse empirical CDF consistently with weights; fare quantiles use linear interpolation. For bin weighting, Kish effective N describes the concentration of148 bin weights; it is not evidence of millions of independent epsilon measurements. Trip counts and distinct support points are separately retained in fit tables.

## 5. Zero and extreme handling

At the exact candidate price, no observed trip has r_P=0. There are consequently no observed nonzero/0 or0/0 cases in the evaluated trip populations. At L_base4.5 the lower-edge bin at4.5 has e=0, representing310,535 weighted observations; no actual physical trip equals that exact kilometre reference. This zero is a representation effect. Using a midpoint or observed mean instead creates a negative value in that bin. An interpolated synthetic point(P_base,L_base) would be0/0 and requires a convention; none was inserted into the sample.

For ALL_SAFE observations, price gaps within$0.01/$0.05/$0.10/$0.25/$0.50/$1 contain858/4,457/10,414/116,921/212,606/353,811 rows. These cumulative counts overlap and must not be added. Relative bounds equal each dollar tolerance divided by22.354198442390455. The smallest price gap is approximately$0.00419844239. Resolution evidence, not arbitrary epsilon thresholds, motivates these diagnostics; no rows were excluded by them.

The matched trip-level distribution ranges approximately−15,450.17 to17,161.44. A saved example at fare22.36USD and distance24.542496km has e17,161.442304 because r_P≈0.00025953. Such cases can be numerically extreme while satisfying existing source cleaning. They are not declared invalid. The bounded example file preserves source-row IDs, timestamps, both deviations and historical values. It does not establish complete raw-record integrity or causal sensitivity.

The rule “if e=0, price=P_base” is a piecewise simulation convention. It cannot define0/0 or justify a near-zero exclusion. New denominator treatment, signs and any zero mass must be agreed before a final sampler is built.

## 6. Distribution fits

All fits use the full observation masses through exact weighted sufficient statistics or numerical likelihood solutions; no large-population random subsample was fitted. Positive families use fixed location0. Normal is the unrestricted baseline. Fits are made separately for each L_base and distance representation; historical T0 support is never used.

There are two explicitly different fit targets. SIGNED_COMPLETE retains all finite values. POSITIVE_COMPONENT_DIAGNOSTIC conditions on e>0, reports the excluded negative/zero mass, and does not claim to model the full population. No absolute transformation, shift or silent deletion is used. Gamma/lognormal/Weibull fitting is not attempted on incompatible negative support; zero-boundary cases require a separate modelling decision. Exponential can evaluate zero with finite density, but does not supply a structural point mass.

{table(fitprimary,['population','sign_treatment','family','KS','AIC'])}

For the4.5-km lower-edge case, the lowest positive-component AIC is Weibull for equally weighted bins and lognormal for count-weighted bins and trip-level observations. These are within-scenario comparisons, not a universal family recommendation. The full signed trip population leaves normal as the only compatible tested parametric baseline, with a large KS discrepancy around0.40. That is not evidence that normal is a good model; it is a limitation of the candidate support set. Empirical resampling reproduces the in-sample distribution exactly, so its zero in-sample KS is tautological and not an out-of-sample success.

AIC/BIC and likelihoods must only be compared for the same population/component. Frequency-weighted bin scores are descriptive pseudo-likelihood scores; repeated bin proxies do not create independent observations. Effective-N versions are supplied to expose this limitation. KS statistics measure fitted-CDF discrepancy. No unadjusted p-value is reported: parameters were estimated from these data, bins are not IID random samples, and trips may be dependent. No formal goodness-of-fit rejection or acceptance is claimed without an appropriate resampling/held-out procedure.

Histogram, CDF and Q–Q panels are saved for the reference scenarios. P1–P99 plotting windows are labelled display restrictions; full tails remain in likelihoods and statistics. Every representation has numerical Q–Q diagnostics. No single family clearly dominates across unresolved populations, representations and support conventions.

## 7. Distance and bin-count cutoffs

{table(cuttable,['scenario','retained_trips','bins_retained','largest_usable_endpoint_km','P_base','mean','population_SD'])}

Lower bounds1/1.5/2km retain7,946,921/6,967,155/5,974,083 trips, respectively. The existing allowed100-mile range is used solely as a sensitivity reference, not a proposed100-km rule. Adding distances>=75km brings only1,459 safe records; their small mass does not imply they are invalid. A final half-kilometre label can end at161km, while the actual physical cap remains160.9344km and observed maximum160.82174592km.

Individual50-count filtering removes6bins/247trips; contiguous filtering stops before68km and removes14bins/683trips. Individual100-count filtering removes27bins/1,665trips; contiguous filtering stops before61km and removes28bins/1,775trips. The61.5 bin has110 trips, so dropping sparse bins cannot be equated with a single upper cutoff.

The table above recomputes P_base within each scenario, showing the combined population/reference effect. Small price changes can move the denominator close to a common fare. To isolate filtering, a second table keeps exactP_base and L_base4.5 fixed: SDs change much less (about29.25–32.39 across most filters). For example, contiguous50 filtering has SD599.16 with its recomputed price but29.28 with fixed references. This is not evidence that the cutoff itself creates anomalous trips or that minimum-SD reference selection is justified.

## 8. Reference-value comparison

{table(repstats,['candidate','representation','mean','population_SD','negative_units','zero_units'])}

The4.5 candidate is the nearest lower-edge bin, with observed mean fare≈21.983204USD, not exactlyP_base. The4.616983790655043 candidate interpolates that curve toP_base. It does not identify a taxi-meter base distance. The5.300620449409596 candidate is a conditional physical-distance mean, subject to a diagnostic price-window choice. Midpoint and actual-mean representations alter signs as well as dispersion, so lower-edge epsilon moments are not representation invariant.

{table(preci,['comparison','mean_abs_e_difference','max_abs_e_difference','median_abs_e_difference','sign_changes'])}

Rounded22.3542 differs from exactP_base by only≈1.56e-6USD, yet the largest full-safe e difference is≈5.73 because of small denominators; median differences are tiny. Using historical21.34586956773507 changes the denominator more substantially and flips154,011 signs at fixedL_base. Exact arithmetic with separately rounded display values is a reproducible interpretation, not a newly frozen decision.

## 9. Fare-bound candidates

{table(fare.head(2))}

{table(clips[clips.scenario.eq('ALL_SAFE')],['q_lower','q_upper','lower','upper','pct_clipped_low','pct_clipped_high','pct_unaffected'])}

These bounds are empirical diagnostics on recorded TLC fare_amount. Ties make actual excluded percentages differ from nominal quantile tails. The$0.01 minimum,$7.52 illustrative value,$207 bin-mean scale and$2,555.20 maximum are not automatically operational fare limits. Trip-level quantiles and bin-mean ranges are separate artifacts, with all candidate distance/count filters evaluated.

Clipping the seven example global offers under all135 combinations of candidate empirical bounds and old/exact/rounded base price leaves7 distinct offers: zero collapsed action pairs. This finding concerns these global arithmetic candidates only. It says nothing about collapse under the missing distance-dependent price equation. Such clipping cannot be simulated or validated by inventing that equation.

## 10. Pricing-contract gap

The PDF explicitly states e=r_L/r_P; L_effective=max(L_observed,L_base); a base-price branch for short trips; e=0 implies priceP_base; P_action=P_base×alpha; and NYC lower/upper clipping. It does not fully specify how a long-distance fare and epsilon-derived preference combine with P_max and P_action. Source operations and page references are classified in `pricing_contract/source_document_contract.csv`.

**PRICE_GENERATION_FORMULA_READY_FOR_IMPLEMENTATION=NO.** The missing composition is material: multiplying a distance-dependent reference differs from multiplying globalP_base, and clipping may change both effective actions and response. No equation is supplied by this analysis. The current seven factors remain examples for comparison, not final V2 actions. Old global offers span$18.143989–$24.547750; the new exact price gives$19.001069–$25.707328. Distance-band coverage tables quantify the limited envelope without asserting a replacement.

## 11. Acceptance and state implication

For ordered prices c_j=a_jP_base, the current mask m_j=1[c_j<=P_accept] reveals a threshold interval through the number of feasible arms. The Q-network does not directly observe epsilon or distance, but the policy and Bellman maximization use this passenger-specific mask. A minimum-protected threshold guarantees at least the lowest arm is feasible.

Removing the mask while retaining the13D state leaves two passengers with identical public context but different independent sensitivities indistinguishable to the pricing policy. Classification: **UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. Aggregate contextual prediction may still be possible; individual threshold observability is not. This does not authorize state expansion.

A post-action rejection design needs explicit outcome, reward, dispatch-bypass, chronological replay and next-request semantics. Existing zero reward for accepted-unmatched is not an approved rejection penalty. Rejected offers must not silently enter successful-dispatch fare statistics or commitments. No reward value or new replay schema is chosen here.

## 12. Request-generator implication

The baseline already preserves empirical distance by resampling intact January trips conditional on forecast-driven origin counts. Independent draws from the pooled array marginal could break OD-distance-duration consistency and change energy, routing and fleet dynamics. It is therefore not an automatic requirement.

The saved March16 illustration contains2,838 requests;2,511 lie in[1,75),327 are below1km and none are>=75km. Conditional on the common range, half-kilometre total variation is{gen['conditional_halfkm_total_variation']:.6f}, binned KS is{gen['conditional_KS_binned']:.6f}, and Jensen–Shannon distance is{gen['conditional_JS_distance']:.6f}. Its1–5km share is{conditional_mass:.6f}%, versus66.517322% in array a. Thus this fixture is not an exact match, although both are empirically grounded. A short nighttime development fixture cannot certify the full generator distribution or select a new calibration rule.

**ARRAY_A_DISTANCE_PROBABILITIES_NEEDED_FOR_RUNTIME=ACADEMIC_DECISION_REQUIRED.** The smallest defensible baseline is to preserve existing joint observations until the target marginal and coupling requirements are agreed. No generator, physical distance, duration, demand forecast or geometry is changed.

## 13. Decision table

{table(pd.DataFrame(dec),['decision','readiness','academic_approval_required'])}

Readiness counts: {dict(counts)}. “Evidence ready” does not mean approved. “More analysis” identifies remaining validation/source needs after defining the target. One missing-formula decision blocks implementation directly; academic interpretation gates remain equally binding. The full CSV records options, numerical evidence, tradeoffs, architecture/training consequences and non-final interpretations for every decision.

## 14. Exact questions requiring academic freeze

1. Confirm the new distance/price ratio as the replacement analytical orientation; how should negative values be interpreted?
2. Is the passenger population represented by equally weighted bins, count-weighted bin proxies, or individual trips?
3. Is bin distance a lower edge, centre or observed mean when constructing epsilon?
4. What conventions govern exact/near-zero price denominators and0/0, and is a structural zero mass retained?
5. Which sign/support population should be used for distribution fitting, and what validation is required before selecting a family?
6. Which lower and upper physical ranges apply, and are they calibration-only or runtime filters?
7. Does a minimum count remove individual bins or define a contiguous range, and is the threshold50 or100?
8. Is exactP_base retained with rounded presentation, and which L_base definition is intended?
9. Is taxi-meter L_flat distinct from referenceL_base, and what evidence defines it?
10. What fare-component and empirical evidence justify NYC lower and upper limits?
11. What is the complete piecewise reference-fare/P_max/action/generation equation, including zero and short-distance cases?
12. Which factors/count and post-clipping action identities follow from that equation?
13. Does passenger response remain a preselection constraint or become an explicit post-action event, and what information must the policy observe?
14. If rejection occurs, what reward, replay, dispatch and operational-statistics treatment applies?
15. Should the existing joint request generator remain, or must it target a new distance marginal while preserving physical consistency?

No answer is silently selected. Any V2 implementation, checkpoint initialization or training requires a subsequent explicit decision and authorization. Historical Record029, current V1, replay, CNN, routing and protected evaluation remain unchanged.
'''
 # Make prose readable without changing artifact paths, identifiers or numbers.
 summary=re.sub(r'(?<=[a-zA-Z])(?=\d)', ' ',summary)
 # The regex above would alter identifier-like labels only in prose; restore mathematical identifiers.
 summary=summary.replace('P _','P_').replace('P 1','P1').replace('P 0','P0').replace('P 5','P5').replace('P 9','P9').replace('V 1','V1').replace('V 2','V2').replace('Record 029','Record029').replace('T 0','T0').replace('Jan 1','Jan1').replace('Mar 15','Mar15')
 (R/'decision_support/ACADEMIC_RECALIBRATION_DECISION_SUMMARY.md').write_text(summary)
 js('decision_support/decision_counts.json',dict(counts))
 readme=f'''# Passenger sensitivity / NYC fare recalibration — decision analysis

**Analysis only. No methodology frozen; no implementation or training.**

Read the [academic decision summary](decision_support/ACADEMIC_RECALIBRATION_DECISION_SUMMARY.md) and [decision table](decision_support/ACADEMIC_DECISION_TABLE.csv). The summary separates numerical evidence from required academic choices.

## Scope and definitions

- Source: existing Jan1–Mar15 cache only,8,692,819 cleaned rows. March16 saved request CSV used only for generator illustration; no protected rows or full-period trip Parquet opened.
- Matched array range:[1,75)km,148bins,7,946,921rows. A second ALL_SAFE scope retains the full restricted cache.
- Analytical new e=((L-L_base)/L_base)/((P-P_base)/P_base). No historical VALID filter, absolute transform, T0 truncation or arbitrary denominator threshold is used.
- P_base={P}; rounded candidate22.3542; historical21.34586956773507 evaluated separately.
- L candidates:4.5,4.616983790655043,{lc:.15f}km. The last is an explicitly diagnostic ±1USD conditional mean. Alternative windows/full-safe means are reported; none selected. Taxi-meter threshold not established.
- Epsilon quantiles:inverse empirical CDF, including weighted cases; SD:population. Fare quantiles:linear interpolation. Undefined ratios are counted separately.
- Distribution rows identify full signed versus strictly-positive conditional diagnostics. Positive components do not replace full populations. No final family selected.

## Headlines

At4.5km/lower-edge representation, equal-bin mean/SD=2.313937/0.407451; count-weighted=1.628232/0.579044; matched trip-level=1.427109/29.316258. Full-safe trip-level has8,692,819defined observations,1,105,611negative,zero exact zeros andzero undefined values. Near-price denominators still generate large tails.

The contract remains incomplete: **PRICE_GENERATION_FORMULA_READY_FOR_IMPLEMENTATION=NO**. Post-action response with unchanged13D state is **UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. Generator target probabilities remain an academic choice. Readiness counts:{dict(counts)}.

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

The saved March16 request fixture is insufficient to certify the full hybrid generator. No synthetic replacement, request replay, policy evaluation, checkpoint load or training was performed. No existing README, historical results, source code or methodology was edited.
'''
 (R/'README.md').write_text(readme)
 checkpoint('REPORTS_WRITTEN',decision_counts=dict(counts),summary_words=len(summary.split()))
 print('summary_words',len(summary.split()))
if __name__=='__main__':main()
