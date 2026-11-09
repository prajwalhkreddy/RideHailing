from pathlib import Path
import json,re
import pandas as pd,numpy as np
R=Path(__file__).parent
load=lambda n:json.loads((R/n).read_text())
def dump(n,v):(R/n).write_text(json.dumps(v,indent=2)+'\n')
def table(f):
 def fmt(v):return f'{v:.9g}' if isinstance(v,float) else str(v)
 return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(fmt(x) for x in row)+' |' for row in f.itertuples(index=False,name=None))+'\n'
sup=load('restricted_calibration_support.json');fixture=load('fixture_validation.json');decision=load('epsilon_min_decision.json')
distribution=pd.read_csv(R/'epsilon_positive_distribution.csv');comparison=pd.read_csv(R/'epsilon_floor_comparison.csv');groups=pd.read_csv(R/'epsilon_four_group_diagnostics.csv');slots=pd.read_csv(R/'slot_validation.csv')
log=(R/'focused_tests.log').read_text();assert log.rstrip().endswith('OK');tests=int(re.search(r'Ran (\d+) tests',log).group(1))
block=load('calibration_support_blocker.json');block.update(status='RESOLVED_BY_EXPLICIT_USER_AUTHORIZATION',decision_status='APPROVED_AND_EXECUTED',resolution='Recomputed identical inclusive P0.5–P99.5 rule from Jan1–Mar15 finite VALID signed epsilon only; historical support unchanged.');dump('calibration_support_blocker.json',block)
spec=load('pricing_v1_spec.json');spec.update(status='REQUEST_LEVEL_IMPLEMENTED_EPSILON_MIN_PENDING',implementation_started=True,implementation_complete=True,calibration_support=sup,epsilon_min=None,epsilon_min_status='RESEARCH_DECISION_REQUIRED',fresh_namespace_created=True,long_training_started=False,training_requirement='PositiveEpsilonProvider.require_training_ready rejects unresolved/unfrozen floor; V1 experiment additionally prevents training in validation mode.',bounded_fixture_floor={'candidate':'P0.5','value':fixture['epsilon_floor'],'status':'DIAGNOSTIC_ONLY_NOT_FROZEN'},production_interface='src.simulation.passenger_sensitive_v1.PassengerSensitiveExperiment',learner_interface='src.rl.passenger_sensitive_dqn.PassengerSensitiveDQN',legacy_entrypoint='Preserved for provenance, not the V1 execution path; do not invoke old multiepisode slot update wrapper on V1.');dump('pricing_v1_spec.json',spec)
architecture='''# Request-Level Pricing Architecture

**IMPLEMENTED.** The explicit user decision resolves the original action-granularity blocker. V1 is a separate opt-in execution path; historical OD/slot source and checkpoints remain for provenance.

| Component | V1 implementation |
|---|---|
| Decision unit | One individual passenger request, after distance/epsilon/P_c are available |
| Context | Same13D state, cached per OD/slot using existing state producer; no epsilon or P_c appended |
| Mask | Seven Boolean candidate-price<=P_c entries; applied in exploration, greedy selection and target max |
| Empty mask | No action/offer/acceptance test/dispatch/replay; separate no-offer count |
| Replay | state, action, reward, next_state, done, next_action_mask, delta_t_minutes |
| Linking | One pending actionable request; finalized only upon next chronological actionable request, including across slots |
| Skipped no-offer requests | Simulator clock and operational/request counters still advance; pending actionable transition retained |
| Time source | Actual simulator clock from slot start + empirical within-slot offset seconds, with existing mini-slot offset fallback |
| Discount | 0.99**(elapsed minutes/30); equal event timestamps give1, never synthetic minimum spacing |
| Terminal | Flush last actionable request at episode end, done=True and target=reward; stored elapsed time to episode boundary is ignored by bootstrap |
| Nonterminal target | Target-network maximum over next request mask only; all-false next mask raises |
| Reward | Actual successfully assigned offered fare; accepted-unmatched zero; no entry for no offer |
| Update trigger | Slot completion only; eight updates when finalized replay has>=1000 transitions, zero otherwise |
| Cross-slot accounting | A prior-slot pending transition is counted when finalized in the next slot; not fabricated early using future data |
| Episode reset | New V1 environment/linker/provider episode RNG, same learner for subsequent training episodes after terminal flush; learner/replay/optimizer schedule persist |
| Persistence | Separate V1 checkpoint schema stores masks and elapsed times; rejects legacy checkpoint metadata before loading models |

Implementation files: `src/pricing/passenger_sensitive_v1.py`, `src/rl/passenger_sensitive_dqn.py`, `src/simulation/passenger_sensitive_v1.py`. `src/dispatch/request.py` adds explicit V1 audit validation; FCFS selection and driver gate are unchanged. The V1 experiment inherits existing fleet/movement/charging/operational methods. CNN/routing/driver/EV/DP models and methodology are unchanged. This changes the pricing decision/replay boundary, not those components.

The old `multiepisode_pricing.slot` wrapper must not be used for V1, because V1 owns its eight-update slot trigger. Training requires an explicitly frozen floor/provenance and validation_only=False; diagnostic fixtures use train_dqn=False. No long-training launcher or old checkpoint resume is invoked.

## Bounded evidence

Two capped March12 slots (first200 generated chronological requests each), fresh seed42 learner, real FCFS/EV interfaces, diagnostic P0.5 floor only. 400 requests,123 offers/assignments,277 no-offers,123 finalized replay transitions, zero rejected offers, zero optimizer updates. The first slot finalizes53 transitions and retains one pending; the terminal second slot finalizes70 including that prior request. Synthetic focused tests independently verify warmup and eight actual optimizer updates per completed warm slot, masked bootstrap, no-action skips and equal timestamps. The fresh persisted checkpoint remains untrained and empty-replay.
'''
(R/'request_level_architecture.md').write_text(architecture)
p=R/'action_granularity_reconciliation.md';s=p.read_text();historical=s[s.index('# Action-Granularity Reconciliation'):];p.write_text('''# Request-Level Action/Replaying Contract — Current Resolution

**APPROVED AND IMPLEMENTED.** The former OD/slot granularity incompatibility below was real under the legacy contract and is now resolved by explicit authorization of request-level actions/replay, unchanged13D state, next-actionable masks, time-aware discount and slot-controlled updates. See request_level_architecture.md for code and validation evidence. No further architectural approval is pending.

The separate support-provenance question was explicitly resolved by authorizing Jan1–Mar15-only support recalculation. Only selection of the positive epsilon floor remains unresolved; all allowed candidates are evaluated and no floor is silently frozen.

## Historical preflight evidence — superseded status flags

'''+historical)
method='''# Passenger-Sensitive Pricing V1 Methodology

## Frozen construction

Global P_base_USD=21.34586956773507 and L_base_km=4.856998243316242 are the explicitly approved constants; source provenance for L_base is3.01799878914405 raw miles×1.609344. L_gg_prime is actual passenger OD trip distance in km. No contextual bases, d_min branch or passenger-specific lower-bound function.

P_c=P_base+(P_base/epsilon_c)*((L_gg_prime-L_base)/L_base). epsilon_c is finite, positive and>=configured epsilon_min>0. P_c is passenger maximum acceptable fare; it is not clipped or forced above zero/base/platform minimum. Epsilon is a positive behavioural calibration parameter, not conventional signed price elasticity. TLC completed trips do not identify passenger acceptance elasticity.

The seven platform factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15] are experimental bounds, not empirical NYC fare extrema. Candidate price=factor×global P_base. Mask price<=P_c before selection and target maximization, equality allowed. Empty mask gives no offer, no acceptance test, no dispatch, no action or replay entry; never passenger rejection. No post-selection clipping.

## Calibration source and authorization

No genuine response-labelled source was identified in targeted authoritative/review artifacts. Record-029 signed epsilon remains unchanged and serves only as a POSITIVE_BEHAVIOURAL_CALIBRATION_PROXY after taking absolute values. User explicitly authorized recomputing the existing signed P0.5–P99.5 support rule using finite VALID Jan1–Mar15 observations only. Historical full-Jan–Mar support is neither reused numerically nor overwritten. Existing global P/L references remain frozen by explicit instruction.

'''+f"Restricted signed support: [{sup['signed_support_lower']!r}, {sup['signed_support_upper']!r}], inclusive; then positive absolute values. Eligible N={sup['N_positive_supported']:,}. Proxy samples are empirical rows with replacement, preserving duplicates, caller-controlled RNG. A global eligible pool is used; no time-group model is selected or presumed valid for the transformed proxy. No new epsilon upper cap is applied beyond this explicitly authorized source-support filter.\n\n"+'''## Floor comparisons and remaining decision

Only NO_FLOOR diagnostic and positive P0.5/P1/P2.5/P5 were evaluated. Candidate diagnostics pair each historical distance with its own proxy epsilon; they are descriptive completed-trip calculations, not observed acceptance or independent runtime resampling. All P_c values are finite already under NO_FLOOR. Candidate floors shrink extreme magnitudes, but the supplied rules provide no distinct numerical/plausibility cutoff to justify one uniquely. **EPSILON_MIN_RECOMMENDATION=RESEARCH_DECISION_REQUIRED**. No choice based on reward, acceptance or assignments. Historical zeros/nonfinite/status exclusions are reported separately; nonfinite invalid-status counts overlap, not additive populations.

The two-slot mechanics fixture uses P0.5 **diagnostically only**, not as a recommendation or frozen setting. Long training fails closed unless provider provenance explicitly marks epsilon_min FROZEN and matches the configured value. Fresh model initialization is allowed without selecting a behavioural floor; it is not a training launch.

## Decision, replay and training boundaries

Individual request decisions preserve the13D contextual state and seven outputs. Next state is next actionable request, possibly across slots; no-offer events still advance time. gamma_eff=0.99**(delta_t_minutes/30), no artificial time spacing. Terminal target=reward. Target maxima respect next masks; empty nonterminal masks fail. Reward=assigned gross fare, accepted-unmatched zero. No artificial penalties.

Slot completion performs8 updates only with finalized replay>=1000; otherwise0. Request count never triggers optimization. Adam0.001/Huber/batch64/capacity100000/tau0.005 and exploration1→0.05 over50000 optimizer updates remain. A new environment/provider RNG is required between episodes while the same trained learner/replay/counters persist. See request_level_architecture.md.

March17–31 remains excluded from all new calibration/selection/training/evaluation. No old episode25 weights, replay, optimizer or counters were loaded. Old run status is PRE_REFORMULATION_PRICING_PROVENANCE. No long training occurred.
'''
(R/'METHODOLOGY.md').write_text(method)
flags=dict(PRICING_V1_SPEC_FROZEN='YES',REQUEST_LEVEL_ACTION_SELECTION_IMPLEMENTED='YES',STATE_13D_UNCHANGED='YES',POSITIVE_EPSILON_PROVIDER_IMPLEMENTED='YES',EPSILON_RESPONSE_LABELS_AVAILABLE='NO',EPSILON_CALIBRATION_PROXY_USED='YES',EPSILON_MIN_FROZEN='NO',PASSENGER_PC_IMPLEMENTED='YES',FEASIBILITY_MASK_IMPLEMENTED='YES',MASKED_EXPLORATION_IMPLEMENTED='YES',MASKED_BELLMAN_TARGET_IMPLEMENTED='YES',EMPTY_MASK_NO_OFFER_IMPLEMENTED='YES',NO_OFFER_REPLAY_TRANSITION='NO',REQUEST_LEVEL_REPLAY_IMPLEMENTED='YES',NEXT_ACTIONABLE_REQUEST_SEMANTICS_VERIFIED='YES',TIME_AWARE_DISCOUNT_IMPLEMENTED='YES',SLOT_BASED_8_UPDATE_CADENCE_PRESERVED='YES',POST_SELECTION_CLIPPING='NO',D_MIN_ACTIVE='NO',OLD_EP25_CHECKPOINT_RESUMED='NO',FRESH_DQN_NAMESPACE_READY='YES',LONG_DQN_TRAINING_STARTED='NO',ROOT_README_UPDATED='YES',CURRENT_STATE_README_UPDATED='YES',ACADEMIC_REVIEW_README_UPDATED='YES',DOCUMENTATION_CONSISTENCY_VERIFIED='YES',PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED='YES')
heads=['Objective','Frozen Methodology','Global References','Request-Level Pricing Architecture','13D State Contract','Positive Epsilon','Calibration Data Status','Epsilon Distribution','Epsilon-Min Calibration','Passenger Maximum Price','Seven Experimental Actions','Feasibility Mask','Empty-Mask / No-Offer Rule','Request-Level Replay','Time-Aware Discounting','Slot-Controlled Optimizer Cadence','Driver/Dispatch Separation','Four Diagnostic Groups','Request-Level Validation','Focused Tests','Fresh DQN Namespace','Protected Evaluation Boundary','Implementation Status','Remaining Research Decisions','Artifact Index']
texts=[
'Implement the approved request-level architecture and bounded calibration/validation. **Implementation complete; long training blocked pending an explicit epsilon_min decision.** No old checkpoint resumed.',
'Global references; positive behavioural epsilon; unchanged13D state; seven actions; one-sided P_c; no contextual bases, d_min, passenger lower-bound function, post-selection clipping or new upper cap. See METHODOLOGY.md and pricing_v1_spec.json.',
'P_base_USD=21.34586956773507; L_base_km=4.856998243316242. L_gg_prime is actual passenger OD distance in km, not grid steps/travel time. Raw historical reference provenance is retained; no source data overwritten.',
'Individual chronological requests receive separate actions after epsilon/P_c. State contexts may be cached per OD/slot; actions are never shared. The old OD/slot boundary remains only in the legacy path. See request_level_architecture.md.',
'J_hat, J_disp_prev, incoming commitments, nine routing probabilities and destination popularity retain their exact existing13D producer. No epsilon, P_c or passenger identifier is appended.',
'PositiveEpsilonProvider resamples eligible positive empirical rows with replacement using caller RNG, preserving frequencies; explicit epsilon floor and provenance required. No runtime abs() or Normal sampling. TLC completed trips do not identify passenger acceptance elasticity. This is a positive behavioural calibration parameter.',
'No real response-labelled source found in the targeted artifacts. Simulator outcomes are not real response labels. Status CALIBRATION_ASSUMPTION. Existing Record-029 signed evidence is preserved. The user authorized Jan1–Mar15-only support recalculation; its values and population are in restricted_calibration_support.json.',
 table(distribution.T.reset_index().rename(columns={'index':'statistic',0:'value'}))+f"\nRestricted signed support [{sup['signed_support_lower']!r}, {sup['signed_support_upper']!r}] before absolute-value transformation. Nonfinite count7,331 belongs to invalid denominator-status rows; valid nonfinite count0. No protected rows enter quantiles.",
 table(comparison[['candidate','epsilon_min','fraction_floored','Pc_min','Pc_max','negative_Pc_count','nonpositive_Pc_count','nonfinite_Pc_count','no_feasible_action_percentage']])+ '\n**RESEARCH_DECISION_REQUIRED.** NO_FLOOR is already finite; all four floors remain empirical candidates. They reduce extreme magnitude without an approved quantitative plausibility boundary to distinguish them. None is frozen or optimized for acceptance/revenue. Full epsilon/P_c quantiles and arm summaries remain in CSV.',
'P_c=P_base+(P_base/epsilon_c)*((L_gg_prime-L_base)/L_base). Below/equal/above L_base implies below/equal/above P_base for positive epsilon. Negative P_c remains unaltered and generally leads to no feasible action. Finite positive epsilon and finite output enforced.',
'Exactly [0.85,0.90,0.95,1.00,1.05,1.10,1.15]. Experimental platform bounds, not empirical NYC fare extrema. Exact candidate prices: '+', '.join(spec['candidate_prices_exact_USD'].values())+' USD.',
'Boolean mask candidate_price<=P_c, including equality. Uniform exploration only among feasible actions; greedy argmax and target max only among feasible actions. No select-then-repair or clipping.',
'NO_FEASIBLE_PRICING_ACTION: no action, offered price, acceptance test, dispatch, reward entry or replay transition. Simulator/operational time and request count still advance. No-offer is distinct from passenger rejection. All generated offers must satisfy P_offer<=P_c.',
'Actionable requests only, with next_action_mask and delta_t_minutes. Pending transition finalized by next actionable request, skipping no-offer requests across slots. At terminal the final pending action becomes done=True. No synthetic eighth action. V1 checkpoint schema preserves these fields and rejects legacy checkpoint metadata.',
'gamma_eff=0.99**(delta_t_minutes/30), from actual simulated request timestamps; identical timestamps give1. Nonterminal next mask must contain an action; terminal target is reward, no bootstrap. Terminal elapsed time is measured to episode end but ignored by target.',
'Exactly8 updates per completed warm slot (finalized replay>=1000), otherwise0. Batch64, capacity100000, Adam0.001, Huber, tau0.005, update-count exploration schedule unchanged. The fixture is cold and runs0 updates; focused tests perform8 updates with1000 transitions and8 again with2000, proving cadence is not proportional to request count. Do not use the old multiepisode slot wrapper on V1.',
'Existing driver P_offer>=price_preference and FCFS/EV checks remain downstream. RequestState adds only V1/no-offer audit validation. Assigned reward=offered fare; accepted-unmatched=0; no-offer has no entry. Fixture all123 offers were assigned; unmatched mechanics are tested through zero-reward replay, not claimed as empirically observed in this capped fixture.',
 table(groups[groups.candidate=='P0.5'][['group','N','epsilon_mean','epsilon_median','distance_km_mean','Pc_median','negative_Pc_percentage','no_feasible_action_percentage']])+ '\nAll five candidates × four groups are in epsilon_four_group_diagnostics.csv. Epsilon=1 belongs to G2/G4; L=L_base belongs to G3/G4. These historical paired diagnostics are not acceptance-label evidence.',
 f"Two capped March12 slots,400 actual generated requests, fresh seed42 network, P0.5 floor={fixture['epsilon_floor']!r} **diagnostic only**. 123 offers/accepted/assigned,277 no-offers,0 offered rejections,0 accepted-unmatched,123 replay transitions,0 optimizer updates. Assigned fare reward=${fixture['reward']:.12f}; replay rewards reconcile. Fleet5000 conserved, unchanged weights.\n\n"+table(slots[['timestamp','slot_request_count','slot_actionable_request_count','slot_no_offer_count','slot_transitions_added','slot_optimizer_updates']])+ '\nFirst slot retains one pending transition; terminal second slot closes it and its own final transition. Full request/mask/state and transition/timing tables are persisted. This capped fixture is mechanical validation, not a pricing-policy performance comparison.',
 f'**{tests} tests passed,0 failed.** Commands in focused_tests.log: new V1 unit/saved-integration tests plus directly relevant standalone DQN and request-context regressions. Tests cover equation, floors, seeds, global references, masks, empty outcomes, next-actionable/time linking, masked/terminal targets, reward accounting, warmup/cadence, persistence, old-schema rejection, protected dates and no-offer request validation. No full repository suite.',
'Fresh seed42 online/target networks, Adam state, empty replay, training_steps0 and exploration1.0 are saved in models/pricing_dqn/passenger_sensitive_v1_seed42/. No historical weights loaded. The persisted checkpoint predates bounded fixture mutations and remains fresh. training_gate.json disallows long training until a floor is frozen. Readiness here means initialization ready, not training authorization.',
'Calibration query explicitly filters >=2026-01-01 and <2026-03-16 before quantiles/support. Fixture March12 only. Runtime guard prohibits March17–31; March16 can only be development validation. No protected hierarchical/calibration/selection data accessed. Historical artifacts untouched.',
'\n'.join(f'- `{k} = {v}`' for k,v in flags.items()),
'Only epsilon_min remains a research decision for training readiness. Allowed floors are fully compared, none uniquely justified by the specified finite/stability conditions. No new architectural approval is needed. After explicit floor selection, freeze provider provenance/config before any separately authorized long training.',
'All required JSON/MD/CSV artifacts are present, plus restricted_calibration_support.json, epsilon_min_decision.json, fixture_validation.json, slot_validation.csv, focused_tests.log and cached positive_epsilon_calibration.npy/calibration_distance_km.npy for reuse. Scripts calibrate_positive_epsilon.py and validate_request_fixture.py refuse redundant completed work. Source modules and tests are linked in request_level_architecture.md. Earlier preflight_integrity.json is historical; calibration_support_blocker.json records its explicit resolution.'
]
(R/'README.md').write_text('# Passenger-Sensitive Pricing V1\n\n'+'\n\n'.join(f'## {i}. {h}\n\n{t}' for i,(h,t) in enumerate(zip(heads,texts),1))+'\n')
validation=dict(spec_frozen=True,request_level_action_selection=True,state_13d_unchanged=True,mask_selection_verified=True,masked_exploration_verified=True,masked_target_verified=True,empty_mask_no_offer=True,no_offer_no_transition=True,request_level_replay=True,next_actionable_semantics=True,time_aware_discount=True,slot_based_optimizer_updates=True,reward_semantics_verified=True,driver_dispatch_downstream=True,response_labels_available=False,epsilon_proxy_used=True,epsilon_min_status='RESEARCH_DECISION_REQUIRED',fresh_namespace_ready=True,old_checkpoint_not_loaded=True,long_training_started=False,protected_final_period_untouched=True,root_readme_updated=True,current_state_readme_updated=True,academic_review_readme_updated=True,affected_module_readmes_updated='NONE_REQUIRED_NO_EXISTING_READMES',documentation_consistency_verified=True,focused_tests_passed=tests,focused_tests_failed=0,fixture=fixture,completion_flags=flags)
dump('implementation_validation.json',validation)
status=f'''Passenger-Sensitive Pricing V1 is implemented in its separate opt-in request-level path. Individual passenger actions preserve the13D state; positive epsilon/P_c enter only the feasibility mask. Global P_base_USD=21.34586956773507 and L_base_km=4.856998243316242; L_gg_prime=actual OD distance in km. Seven experimental factors [0.85,0.90,0.95,1.00,1.05,1.10,1.15], no contextual bases, no d_min or passenger lower-bound function. Mask before selection/target maximization; empty mask means no offer, not rejection. No clipping.

Replay contains actionable requests only, linked to the next actionable chronological request with its mask. Discount is0.99**(delta_t_minutes/30); identical timestamps give1. Updates remain8 per completed warm slot,0 otherwise. Driver/dispatch/EV/routing/CNN/DP methodology is unchanged. Old shared OD/slot pricing is retired for V1; legacy execution/checkpoints remain historical.

The user authorized recomputing P0.5–P99.5 support using Jan1–Mar15 VALID rows only. Positive calibration proxy N=8,598,746; no real response labels identified. **EPSILON_MIN_RECOMMENDATION=RESEARCH_DECISION_REQUIRED**: all permitted floors are finite and no unique plausibility boundary is supplied. Long training fails closed until a floor is explicitly frozen. TLC completed trips do not identify acceptance elasticity.

Bounded March12 validation:400 requests,123 feasible accepted/assigned offers,277 no-offers,123 transitions,zero offered rejections and zero optimizer updates. **{tests} focused tests passed,0 failed.** Fresh seed42 initialization is saved; no long training started. Episode25 is PRE_REFORMULATION_PRICING_PROVENANCE and was not resumed. March17–31 remains untouched for calibration/selection/training/hierarchical evaluation. [V1 package](LINK).
'''
root=Path('README.md');s=root.read_text();a=s.index('## Passenger-Sensitive Pricing V1 — Current Status, 7 November 2026');b=s.index('## Prior project status — 1 November 2026',a);root.write_text(s[:a]+'## Passenger-Sensitive Pricing V1 — Current Status, 7 November 2026\n\n'+status.replace('LINK','results/analysis/2026-11-07_passenger_sensitive_pricing_v1/README.md')+'\n'+s[b:])
for path,title in [('results/analysis/2026-11-01_current_state_review/README.md','Passenger-Sensitive Pricing V1 — Approved Request-Level Contract'),('results/analysis/2026-11-04_academic_review_validation/README.md','Passenger-Sensitive Pricing V1 — Request-Level Architecture Decision')]:
 p=Path(path);s=p.read_text();heading='## '+title;a=s.index(heading);p.write_text(s[:a]+heading+'\n\nDated2026-11-07; this implemented status supersedes prior blockers. Historical episode25/request-level findings above remain prior-implementation evidence.\n\n'+status.replace('LINK','../2026-11-07_passenger_sensitive_pricing_v1/README.md'))
print('REPORT_FINALIZED',tests)
