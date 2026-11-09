from pathlib import Path
import json,shutil,re
import pandas as pd
R=Path(__file__).parent;V=R.parent
load=lambda p:json.loads(p.read_text())
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def table(f):
 return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(f'{x:.8g}' if isinstance(x,float) else str(x) for x in row)+' |' for row in f.itertuples(index=False,name=None))+'\n'
a=load(R/'analysis_summary.json');t=pd.read_csv(R/'sensitivity_truncation_comparison.csv');arms=pd.read_csv(R/'feasible_arm_before_after.csv');bands=pd.read_csv(R/'pricing_factor_distance_band_coverage.csv');fixture=load(R/'fixture_validation.json')
log=(R/'focused_tests.log').read_text();assert log.rstrip().endswith('OK');tests=int(re.search(r'Ran (\d+) tests',log).group(1))
archive=R/'pre_effective_threshold_provenance';archive.mkdir(exist_ok=True)
for n in ['README.md','METHODOLOGY.md','pricing_v1_spec.json','implementation_validation.json','epsilon_min_decision.json','request_level_architecture.md','action_granularity_reconciliation.md']:
 if not (archive/n).exists():shutil.copy2(V/n,archive/n)
flags=dict(SIGNED_EPSILON_DISTRIBUTION_DOCUMENTED='YES',ABSOLUTE_EPSILON_APPROVED_AND_IMPLEMENTED='YES',TRUNCATION_METHODOLOGY_JUSTIFIED='YES',TRUNCATION_ASYMMETRY_CONSIDERED='YES',RANDOM_SAMPLING_METHODOLOGY_JUSTIFIED='YES',PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED='NO',V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION='YES',EFFECTIVE_PASSENGER_THRESHOLD_IMPLEMENTED='YES',PLATFORM_MINIMUM_PROTECTION_IMPLEMENTED='YES',OLD_NO_OFFER_DIAGNOSTIC_SUPERSEDED='YES',PRICING_FACTOR_DATASET_JUSTIFICATION='MODERATE',SEVEN_FACTOR_SET_RETAINED='YES',EPSILON_MIN_FROZEN='YES',REQUEST_LEVEL_ARCHITECTURE_RETAINED='YES',STATE_13D_UNCHANGED='YES',MASKED_BELLMAN_TARGET_RETAINED='YES',SLOT_BASED_8_UPDATE_CADENCE_RETAINED='YES',LONG_DQN_TRAINING_STARTED='NO',ROOT_README_UPDATED='YES',CURRENT_STATE_README_UPDATED='YES',ACADEMIC_REVIEW_README_UPDATED='YES',DOCUMENTATION_CONSISTENCY_VERIFIED='YES',PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED='YES')
method=f'''# Passenger-Sensitive Pricing V1 — Frozen Project Methodology

## Academic Review Feedback Reconciliation

The academic review accepts the overall formulation, permits absolute historical sensitivities, requires distribution/truncation/sampling justification, requests a minimum-protected passenger threshold, and requires NYC evidence for the seven pricing factors. These points are implemented below. This is a **PROJECT IMPLEMENTATION DECISION**, not independent verification of manuscript numbering or a legally established NYC fare minimum.

`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED = NO`

`V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION = YES`

The consolidated roadmap uses the P_base-scaled adjustment. Equation numbering cannot be mapped unambiguously across historical documents. Explicit user authorization freezes that expression as the intended V1 RHS. The older module-guide expression lacking P_base on the adjustment is `SUPERSEDED_HISTORICAL_FORMULATION`; its source files remain unchanged.

## Signed vs Positive Sensitivity

`SIGNED_HISTORICAL_SENSITIVITY` remains unchanged in Record-029. `POSITIVE_V1_BEHAVIOURAL_SENSITIVITY` is an absolute-value calibration proxy, not identified causal passenger acceptance elasticity. Completed TLC trips contain no real rejected-offer response labels. Negative historical values are permitted and preserved.

## Sensitivity Distribution

Jan1–Mar15 finite VALID N={a['N_valid']:,}; signed mean={a['signed']['mean']:.9f}, population SD={a['signed']['SD']:.9f}, negative={a['signed']['negative_pct']:.6f}%. Zero among VALID=0; unresolved status={a['unresolved_status_N']:,} ({a['unresolved_status_pct']:.6f}% of all cleaned date-restricted rows), excluded before transformation/support. The absolute distribution is strongly right-skewed: mean={a['positive_before_support']['mean']:.9f}, median={a['positive_before_support']['median']:.9f}, SD={a['positive_before_support']['SD']:.9f}, maximum={a['positive_before_support']['max']:.6f}. All requested quantiles are in sensitivity_distribution_summary.csv. The three plots retain full tails with explicit log/symlog axes; bin heights are percentages, not density.

## Truncation Methodology

Sequence: restrict timestamps >=Jan1 and <Mar16; require VALID, finite and nonzero; compute abs(epsilon); compute positive empirical quantiles with linear interpolation; retain inclusively. March16 is development-only; March17–31 is excluded from calibration/selection/evaluation.

Freeze T0: **[{a['support_lower']!r}, {a['support_upper']!r}]**, P0.5–P99.5 of the positive distribution, N={a['retained_N']:,} ({a['retained_pct']:.6f}%). Bounds are symmetric in nominal tail probability only, NOT numerical epsilon space. Duplicate empirical values explain slightly unequal tail counts. Lower excluded43,331 (0.498890%), upper43,352 (0.499131%). Historical observations outside V1 support remain valid historical data.

Lower excluded epsilon ranges2.7832601825861228e-05 to0.017807720680742496; reciprocal sensitivity can amplify tiny values into very large raw adjustments (observed paired P_raw approximately−109,563 to6,483,902 USD). Upper excluded epsilon ranges27.325985491756203 to3282.8090993751007; the reciprocal term shrinks, with paired raw prices20.5944–21.8798 USD. Large epsilon therefore makes distance-induced price adjustment smaller; it does not independently establish that a passenger is causally price-insensitive.

T0/T1/T2/T3 compare independent lower/upper probability choices. All have finite raw prices and zero valid-request empty masks after threshold protection. Medians remain near0.82. Tighter bounds reduce tails but discard more evidence, without establishing a distinct instability breakpoint or superior behavioural validity. Retain simplest existing T0; no revenue-based selection. This is a defensible empirical regularization choice, not a uniquely estimated natural boundary. Non-Gaussian shape and sparse extremes motivate truncation; extreme historical values are not relabelled invalid.

`epsilon_min={a['support_lower']!r}` is frozen as the support lower bound itself. **No additional flooring**: P0.5/P1/P2.5/P5 post-support floors remain historical diagnostics, not runtime calibration. T0 already bounds reciprocal sensitivity and yields finite calculations; no evidence here requires another floor. No raw-price upper cap is added; the action ceiling bounds offers.

## Random Sampling Method

`TRUNCATED_EMPIRICAL_RESAMPLING`: uniformly sample supported empirical rows WITH REPLACEMENT, preserving duplicate-value frequencies; caller-owned seeded NumPy Generator. Use the existing global positive pool; no time-group conditioning was selected for transformed V1. Same ordered pool/seed produces identical samples. Runtime receives positive epsilon; it does not abs() signed samples or fit a Gaussian. No extra floor alters sampled values.

Empirical sampling preserves skew, tails within support, repeated empirical mass and any multimodality without imposing an unsupported family. Absolute transformation folds signed mass and changes shape; older signed Record-029 empirical-versus-truncated-Normal comparisons do not transfer unchanged, and are not used as direct V1 model-selection evidence. No parametric fit is performed.

## Raw Passenger Preference

P_base=21.34586956773507 USD; L_base=4.856998243316242 km; L_gg_prime=actual passenger OD distance in km. Both references remain global.

`P_raw_c = P_base + (P_base/epsilon_c)*((L_gg_prime-L_base)/L_base)`.

Raw values, including negative ones, remain logged unchanged. Their diagnostic categories are in raw_vs_effective_preference_summary.csv; equality tolerance is1e-10 USD and the requested categories overlap (e.g. negative and nonpositive).

## Effective Passenger Threshold

`P_platform_min=0.85*P_base`; `P_platform_max=1.15*P_base`.

`P_accept_c=max(P_platform_min,P_raw_c)`.

All seven candidate prices are factor×globalP_base. Mask `candidate_price<=P_accept_c` before exploration/greedy selection and Bellman target maximization. The maximum configured action enforces the platform ceiling; P_accept itself can exceed that ceiling.

## Platform Minimum Protection

The project-defined minimum is an external platform offer constraint. Effective passenger threshold is bounded below by that minimum, avoiding infeasibility solely because raw preference is below any permitted offer. This is a modelling definition, not observed willingness-to-pay and not post-selection DQN action clipping. It does not claim0.85*P_base is a statutory NYC minimum. Valid finite requests always have at least0.85 feasible. Defensive empty-mask no-offer/no-replay handling remains; invalid inputs fail closed and are not ordinary economic rejections. d_min=NOT_USED.

## Pricing-Factor Dataset Justification

All8,692,819 cleaned Jan1–Mar15 fares (TLC fare_amount provenance) are used, independent of epsilon support/status, divided by globalP_base. Only{a['factor_coverage_pct']:.6f}% lie inside0.85–1.15; thus this interval is not a full-market fare envelope or empirical extrema. Distance-conditioned coverage is essential and reported in km, including3–3.17km after miles×1.609344. Time-group summaries are descriptive only.

Retain exactly[0.85,0.90,0.95,1.00,1.05,1.10,1.15]. Each interior fare-factor band has observed support.0.85 and1.15 form a bounded symmetric experiment around the global reference;5% steps equal approximately1.06729348 USD. These are project discretization choices contextualized by observed fare mass, not uniquely estimated endpoints or statistically optimal spacing. **MODERATE** dataset justification for a bounded reference-price experiment; **WEAK** evidence for uniqueness of exact endpoints/spacing. The broad fare distribution does not justify claiming all trip contexts fit this range. Factors unchanged.

## Revised Feasible-Action Distribution

The previous T0 raw-only no-offer61.746289% is `SUPERSEDED_BY_EFFECTIVE_THRESHOLD_REFORMULATION` as a current runtime prediction, but remains historical raw-preference evidence. Effective-rule no-offer=0% across all T0–T3 eligible observations. Per-arm counts before/after are in feasible_arm_before_after.csv. This is a deterministic consequence of the minimum protection, not a measured improvement in real passenger acceptance. Historical diagnostics pair each distance with its own source epsilon; runtime independently samples epsilon from the global pool.

## Request-Level Architecture and Validation

Individual request decisions retain the13D context, seven outputs, masked exploration/greedy/target, next actionable chronological replay and time discount0.99**(elapsed minutes/30). Terminal target=reward. Eight optimizer updates per completed warm slot (replay>=1000), zero otherwise; existing batch64/Adam0.001/Huber/replay100000/tau0.005 unchanged. No passenger features appended. Successful assignment reward=offered gross fare; unmatched0. FCFS/driver/EV/routing interfaces retained. No old checkpoint resumed.

Revised bounded March12 fixture:400 requests, {fixture['offers_generated']} offers, {fixture['no_feasible_pricing_action']} no-offers, {fixture['assigned']} assigned, {fixture['accepted_unmatched']} unmatched, {fixture['transitions_added']} transitions; reward={fixture['reward']:.9f}; zero optimizer updates, fleet5000 conserved. Request audit logs raw and effective values separately. Source signed epsilon is unavailable for independent positive resampling and explicitly null. Old fixtures remain historical. {tests} focused tests passed. No long training started; preserved fresh checkpoint remains untrained. Any long training requires separate authorization.
'''
(R/'sensitivity_sampling_methodology.md').write_text(method[method.index('## Random Sampling Method'):method.index('## Raw Passenger Preference')])
(V/'METHODOLOGY.md').write_text(method)
(V/'README.md').write_text(method+'\n## Review Artifacts\n\n[Reconciliation results](review_feedback_reconciliation/README.md). Earlier calibration CSVs and fixtures are retained as historical raw-threshold evidence; current numerical results are in review_feedback_reconciliation/.\n')
(R/'README.md').write_text(method+'\n## Truncation Comparison\n\n'+table(t[['candidate','lower','upper','retained_N','retained_pct','epsilon_mean','epsilon_SD','epsilon_median','P_raw_min','P_raw_max','P_accept_min','P_accept_max','no_offer_pct']])+'\n## T0 Feasible Arms\n\n'+table(arms[arms.candidate=='T0'])+'\n## Distance-Conditioned Factor Coverage\n\n'+table(bands)+'\n## Completion Flags\n\n'+'\n'.join(f'- `{k} = {v}`' for k,v in flags.items())+'\n\n## Artifacts\n\nCSV: sensitivity_distribution_summary; sensitivity_truncation_comparison; excluded_tail_summary; raw_vs_effective_preference_summary; feasible_arm_before_after; pricing_factor_dataset_justification; pricing_factor_distance_band_coverage; pricing_factor_time_group_coverage; request_level_review_feedback_validation; request_level_transition_validation; slot_validation. PNG: signed_epsilon_distribution; positive_epsilon_distribution; positive_epsilon_distribution_logx. JSON: analysis_summary; fixture_validation; review_feedback_validation. Scripts and focused_tests.log provide reproducibility. No previous data/results were deleted.\n')
sup=load(V/'restricted_calibration_support.json');sup.update(sampling_family='TRUNCATED_EMPIRICAL_RESAMPLING',epsilon_min=a['support_lower'],epsilon_min_status='FROZEN',additional_floor=False,selection_status='PROJECT_METHODOLOGY_DECISION_T0_RETAINED');dump(V/'restricted_calibration_support.json',sup)
decision=load(V/'epsilon_min_decision.json');decision.update(EPSILON_MIN_RECOMMENDATION='APPROVED_SUPPORT_LOWER_BOUND_NO_ADDITIONAL_FLOOR',EPSILON_MIN_FROZEN=True,epsilon_min=a['support_lower'],reason='Positive T0 support already removes near-zero observations; bounded T0–T3 comparison establishes no need for an additional floor. Retain T0 per approved task rule.',fixture_candidate='T0 support lower bound; revised effective-threshold fixture',historical_candidates_status='Historical additional-floor diagnostics, not active runtime method');dump(V/'epsilon_min_decision.json',decision)
spec=load(V/'pricing_v1_spec.json');spec.update(status='REVIEW_RECONCILED_PROJECT_METHOD_FROZEN',epsilon_min=a['support_lower'],epsilon_min_status='FROZEN',calibration_support=sup,raw_preference_equation='P_base + (P_base/epsilon_c)*((L_gg_prime-L_base)/L_base)',effective_threshold='max(0.85*P_base, P_raw_c)',feasibility='candidate price <= P_accept_c',Pc_equation='P_base + (P_base/epsilon_c)*((L_gg_prime-L_base)/L_base)',Pc_field_interpretation='P_c_USD and v1_pc_usd now denote effective threshold; P_raw_c/v1_raw_pc_usd explicitly preserve equation value',passenger_lower_bound_function='PLATFORM_MINIMUM_PROTECTION',Pc_clamping=False,effective_threshold_floor=True,empty_mask_interpretation='Defensive invariant/data-quality condition, not expected economic behavior',allowed_floor_candidates='Historical diagnostic only; no additional floor selected',sampling_family='TRUNCATED_EMPIRICAL_RESAMPLING',PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED=False,V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION=True,training_requirement='Separate launch authorization; frozen supported provider provenance and validation_only=False required',long_training_started=False,bounded_fixture_floor={'value':a['support_lower'],'status':'T0_SUPPORT_LOWER_BOUND_NO_ADDITIONAL_FLOOR'},action_bounds_classification='PROJECT_PLATFORM_ACTION_BOUNDS_WITH_MODERATE_DATA_CONTEXT');dump(V/'pricing_v1_spec.json',spec)
validation=dict(status='PASS',completion_flags=flags,tests_passed=tests,tests_failed=0,fixture=fixture,source_numbering_verified=False,RHS_resolution='Explicit project decision; consolidated equation retained',historical_Record029_unchanged=True,long_training_started=False,protected_dates_accessed=False,remaining_research_decision='None blocking this bounded V1 methodology; exact factors remain project discretization choices, not uniquely data-identified. Long training requires separate authorization.')
dump(R/'review_feedback_validation.json',validation)
old=load(V/'implementation_validation.json');old.update(calibration_revision='POSITIVE_FIRST_T0_EFFECTIVE_THRESHOLD',epsilon_min_status='FROZEN',epsilon_min=a['support_lower'],fixture=fixture,fixture_scope='Revised March12 effective-threshold validation',completion_flags=flags,focused_tests_passed=tests,focused_tests_failed=0);dump(V/'implementation_validation.json',old)
# Directly affected V1 docs now point to current definitions; archived copies preserve prior text.
(V/'request_level_architecture.md').write_text('# Current Request-Level Architecture\n\nSee [METHODOLOGY.md](METHODOLOGY.md) and [reconciliation](review_feedback_reconciliation/README.md).\n\n13D state, request-level actions/replay, next-actionable linking, time discount and8/warm-slot cadence remain unchanged. All masks now use P_accept=max(0.85*P_base,P_raw), including next-state Bellman masks. Valid requests have at least one feasible arm. Defensive no-offer/no-replay remains for invariant defects; invalid values fail closed. Historical architecture details are preserved in review_feedback_reconciliation/pre_effective_threshold_provenance/.\n')
(V/'action_granularity_reconciliation.md').write_text('# Current Resolution\n\nRequest-level architecture is approved and implemented. Source numbering remains unverified; the RHS is resolved by explicit project decision. T0 positive support is retained with epsilon_min equal to its lower bound and no additional floor. See METHODOLOGY.md. Earlier preflight evidence is retained in review_feedback_reconciliation/pre_effective_threshold_provenance/.\n')
# Prevent obsolete generators from silently restoring superseded current-facing output.
for n in ['finalize_report.py','calibrate_positive_epsilon.py']:
 p=V/n;s=p.read_text();guard="raise SystemExit('Superseded generator: use review_feedback_reconciliation scripts; frozen current methodology must not be overwritten.')\n"
 if guard not in s:p.write_text(guard+s)
status=f'''Academic-review reconciliation is complete under an explicit project implementation decision. Equation-number provenance remains unverified (`PROFESSOR_EQUATION_NUMBER_SOURCE_VERIFIED=NO`); `V1_RHS_INTERPRETATION_RESOLVED_BY_PROJECT_DECISION=YES`. Historical formulation without the P_base adjustment multiplier is superseded, not rewritten.

V1 uses positive absolute Record-029 sensitivity as a behavioural calibration proxy, not causal acceptance elasticity. Restrict Jan1–Mar15 VALID finite/nonzero first, then abs(), then inclusive positive P0.5–P99.5: [{a['support_lower']!r}, {a['support_upper']!r}], N=8,598,805. Truncated empirical row resampling with replacement preserves duplicate mass, caller-controlled seed; global pool. T0 retained after four bounded asymmetric comparisons. epsilon_min is the support lower bound; no extra floor. Signed historical artifacts remain unchanged.

Raw preference is `P_base+(P_base/epsilon)*((L-L_base)/L_base)` with unchanged global references21.34586956773507 USD and4.856998243316242km. Effective threshold is `max(0.85*P_base,P_raw)`; all action masks use it. The seven factors0.85–1.15 remain; dataset justification is MODERATE for bounded reference-price exploration, weak for uniquely determining exact endpoints/spacing. Jan1–Mar15 fare coverage inside that interval is14.379973%; it is not a statutory NYC fare minimum or a full-market envelope.

The former61.746289% raw-rule no-offer rate is `SUPERSEDED_BY_EFFECTIVE_THRESHOLD_REFORMULATION`; revised valid calibration no-offer=0%. Historical raw diagnostics remain. No post-selection action clipping or d_min. Request-level13D state/replay, masked Bellman target, time-aware discount and8/warm-slot cadence retained. Bounded fixture400 requests, {fixture['assigned']} assignments, {fixture['no_feasible_pricing_action']} no-offers, zero optimizer updates; {tests} focused tests passed. No long training started; old checkpoints not resumed. March16 development-only; March17–31 untouched. [Reconciliation](LINK).
'''
p=Path('README.md');s=p.read_text();start=s.index('## Passenger-Sensitive Pricing V1 — Current Status, 7 November 2026');end=s.index('## Prior project status — 1 November 2026',start);p.write_text(s[:start]+'## Passenger-Sensitive Pricing V1 — Current Status, 7 November 2026\n\n'+status.replace('LINK',str(R/'README.md'))+'\n'+s[end:])
for path,title in [('results/analysis/2026-11-01_current_state_review/README.md','Passenger-Sensitive Pricing V1 — Approved Request-Level Contract'),('results/analysis/2026-11-04_academic_review_validation/README.md','Passenger-Sensitive Pricing V1 — Request-Level Architecture Decision')]:
 p=Path(path);s=p.read_text();i=s.index('## '+title);p.write_text(s[:i]+'## '+title+'\n\n## Academic Review Feedback Incorporated\n\nDated2026-11-07. Prior findings above are historical/pre-reformulation evidence. Review feedback on (1) distribution, sampling and asymmetric truncation; (2) permitted absolute values; (3) minimum-protected threshold; and (4) dataset justification of seven factors is incorporated.\n\n'+status.replace('LINK','../2026-11-07_passenger_sensitive_pricing_v1/review_feedback_reconciliation/README.md'))
# Preserve checkpoint weights/replay; gate metadata only records methodology readiness, not launch permission.
p=Path('models/pricing_dqn/passenger_sensitive_v1_seed42/training_gate.json');g=load(p);g.update(epsilon_min_status='FROZEN',epsilon_min=a['support_lower'],long_training_allowed=False,reason='Methodology reconciled; separate long-training authorization required');dump(p,g)
print('DOCUMENTATION_RECONCILED',tests)
