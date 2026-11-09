# Passenger-Sensitive Pricing V1

## 1. Objective

Implement the approved request-level architecture and bounded calibration/validation. **Implementation complete; long training blocked pending an explicit epsilon_min decision.** No old checkpoint resumed.

## 2. Frozen Methodology

Global references; positive behavioural epsilon; unchanged13D state; seven actions; one-sided P_c; no contextual bases, d_min, passenger lower-bound function, post-selection clipping or new upper cap. See METHODOLOGY.md and pricing_v1_spec.json.

## 3. Global References

P_base_USD=21.34586956773507; L_base_km=4.856998243316242. L_gg_prime is actual passenger OD distance in km, not grid steps/travel time. Raw historical reference provenance is retained; no source data overwritten.

## 4. Request-Level Pricing Architecture

Individual chronological requests receive separate actions after epsilon/P_c. State contexts may be cached per OD/slot; actions are never shared. The old OD/slot boundary remains only in the legacy path. See request_level_architecture.md.

## 5. 13D State Contract

J_hat, J_disp_prev, incoming commitments, nine routing probabilities and destination popularity retain their exact existing13D producer. No epsilon, P_c or passenger identifier is appended.

## 6. Positive Epsilon

PositiveEpsilonProvider resamples eligible positive empirical rows with replacement using caller RNG, preserving frequencies; explicit epsilon floor and provenance required. No runtime abs() or Normal sampling. TLC completed trips do not identify passenger acceptance elasticity. This is a positive behavioural calibration parameter.

## 7. Calibration Data Status

No real response-labelled source found in the targeted artifacts. Simulator outcomes are not real response labels. Status CALIBRATION_ASSUMPTION. Existing Record-029 signed evidence is preserved. The approved positive-first correction uses Jan1–Mar15 VALID, then abs(), excludes nonfinite/zero, then inclusive positive P0.5–P99.5. Its exact bounds/population are in restricted_calibration_support.json. Prior provisional signed-first figures are superseded and archived under superseded_signed_first_calibration/. Historical Record-029 support remains unchanged.

## 8. Epsilon Distribution

| statistic | value |
| --- | --- |
| N | 8598805 |
| min_positive | 0.0178099131 |
| P0.1 | 0.0202321443 |
| P0.5 | 0.0319527661 |
| P1 | 0.0488715607 |
| P2.5 | 0.0984775652 |
| P5 | 0.172570874 |
| P10 | 0.283807131 |
| P25 | 0.477959412 |
| median | 0.820122877 |
| P75 | 0.9915507 |
| P90 | 1.583622 |
| P95 | 2.81856345 |
| P99 | 9.81764749 |
| max | 27.3245997 |
| exact_zero_count | 0 |
| nonfinite_count | 7331 |
| nonfinite_valid_count | 0 |
| excluded_unsupported_count | 86683 |
| excluded_invalid_status_count | 7331 |

V1 positive calibration support [0.017809913104763053, 27.324599740032788] after absolute-value transformation and nonfinite/zero exclusion. Nonfinite count7,331 belongs to invalid denominator-status rows; valid nonfinite count0. No protected rows enter quantiles.

## 9. Epsilon-Min Calibration

| candidate | epsilon_min | fraction_floored | Pc_min | Pc_max | negative_Pc_count | nonpositive_Pc_count | nonfinite_Pc_count | no_feasible_action_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NO_FLOOR | 0 | 0 | -1158.97871 | 33208.0614 | 1229215 | 1229215 | 0 | 61.7462892 |
| P0.5 | 0.0319527661 | 0.0049876698 | -644.485093 | 20802.4524 | 1229210 | 1229210 | 0 | 61.7462892 |
| P1 | 0.0488715607 | 0.00997801439 | -413.981767 | 13608.2628 | 1229193 | 1229193 | 0 | 61.7462194 |
| P2.5 | 0.0984775652 | 0.0250001018 | -194.694616 | 6764.13886 | 1227705 | 1227705 | 0 | 61.7461845 |
| P5 | 0.172570874 | 0.0500000872 | -101.937628 | 3889.61314 | 1214908 | 1214908 | 0 | 61.7457658 |

**RESEARCH_DECISION_REQUIRED.** NO_FLOOR is already finite; all four floors remain empirical candidates. They reduce extreme magnitude without an approved quantitative plausibility boundary to distinguish them. None is frozen or optimized for acceptance/revenue. Full epsilon/P_c quantiles and arm summaries remain in CSV.

## 10. Passenger Maximum Price

P_c=P_base+(P_base/epsilon_c)*((L_gg_prime-L_base)/L_base). Below/equal/above L_base implies below/equal/above P_base for positive epsilon. Negative P_c remains unaltered and generally leads to no feasible action. Finite positive epsilon and finite output enforced.

## 11. Seven Experimental Actions

Exactly [0.85,0.90,0.95,1.00,1.05,1.10,1.15]. Experimental platform bounds, not empirical NYC fare extrema. Exact candidate prices: 18.1439891325748095, 19.2112826109615630, 20.2785760893483165, 21.3458695677350700, 22.4131630461218235, 23.4804565245085770, 24.5477500028953305 USD.

## 12. Feasibility Mask

Boolean mask candidate_price<=P_c, including equality. Uniform exploration only among feasible actions; greedy argmax and target max only among feasible actions. No select-then-repair or clipping.

## 13. Empty-Mask / No-Offer Rule

NO_FEASIBLE_PRICING_ACTION: no action, offered price, acceptance test, dispatch, reward entry or replay transition. Simulator/operational time and request count still advance. No-offer is distinct from passenger rejection. All generated offers must satisfy P_offer<=P_c.

## 14. Request-Level Replay

Actionable requests only, with next_action_mask and delta_t_minutes. Pending transition finalized by next actionable request, skipping no-offer requests across slots. At terminal the final pending action becomes done=True. No synthetic eighth action. V1 checkpoint schema preserves these fields and rejects legacy checkpoint metadata.

## 15. Time-Aware Discounting

gamma_eff=0.99**(delta_t_minutes/30), from actual simulated request timestamps; identical timestamps give1. Nonterminal next mask must contain an action; terminal target is reward, no bootstrap. Terminal elapsed time is measured to episode end but ignored by target.

## 16. Slot-Controlled Optimizer Cadence

Exactly8 updates per completed warm slot (finalized replay>=1000), otherwise0. Batch64, capacity100000, Adam0.001, Huber, tau0.005, update-count exploration schedule unchanged. The fixture is cold and runs0 updates; focused tests perform8 updates with1000 transitions and8 again with2000, proving cadence is not proportional to request count. Do not use the old multiepisode slot wrapper on V1.

## 17. Driver/Dispatch Separation

Existing driver P_offer>=price_preference and FCFS/EV checks remain downstream. RequestState adds only V1/no-offer audit validation. Assigned reward=offered fare; accepted-unmatched=0; no-offer has no entry. Fixture all123 offers were assigned; unmatched mechanics are tested through zero-reward replay, not claimed as empirically observed in this capped fixture.

## 18. Four Diagnostic Groups

| group | N | epsilon_mean | epsilon_median | distance_km_mean | Pc_median | negative_Pc_percentage | no_feasible_action_percentage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 4377965 | 0.720239287 | 0.810519607 | 1.9293397 | 3.46916812 | 28.0772003 | 99.313905 |
| G2 | 1522356 | 2.22378738 | 1.27086325 | 3.29708144 | 16.3763021 | 0 | 63.1596683 |
| G3 | 2146815 | 0.432149743 | 0.419890835 | 14.2357631 | 107.975204 | 0 | 0 |
| G4 | 551669 | 3.5388213 | 1.98993934 | 6.71894718 | 23.2756672 | 0 | 0 |

All five candidates × four groups are in epsilon_four_group_diagnostics.csv. Epsilon=1 belongs to G2/G4; L=L_base belongs to G3/G4. G1: distance<L_base and epsilon<1; G2: distance<L_base and epsilon>=1; G3: distance>=L_base and epsilon<1; G4: distance>=L_base and epsilon>=1. These historical paired diagnostics are not acceptance-label evidence.

## 19. Request-Level Validation

**Historical mechanics fixture: superseded signed-first calibration, not corrected-population evidence.** Two capped March12 slots,400 actual generated requests, fresh seed42 network, P0.5 floor=0.017658441740057023 **diagnostic only**. 123 offers/accepted/assigned,277 no-offers,0 offered rejections,0 accepted-unmatched,123 replay transitions,0 optimizer updates. Assigned fare reward=$2572.177282912075; replay rewards reconcile. Fleet5000 conserved, unchanged weights.

| timestamp | slot_request_count | slot_actionable_request_count | slot_no_offer_count | slot_transitions_added | slot_optimizer_updates |
| --- | --- | --- | --- | --- | --- |
| 2026-03-12 15:30:00 | 200 | 54 | 146 | 53 | 0 |
| 2026-03-12 16:00:00 | 200 | 69 | 131 | 70 | 0 |

First slot retains one pending transition; terminal second slot closes it and its own final transition. Full request/mask/state and transition/timing tables are persisted. This capped fixture is mechanical validation, not a pricing-policy performance comparison.

## 20. Focused Tests

**48 tests passed,0 failed.** Commands in focused_tests.log: new V1 unit/saved-integration tests plus directly relevant standalone DQN and request-context regressions. Tests cover equation, floors, seeds, global references, masks, empty outcomes, next-actionable/time linking, masked/terminal targets, reward accounting, warmup/cadence, persistence, old-schema rejection, protected dates and no-offer request validation. No full repository suite.

## 21. Fresh DQN Namespace

Fresh seed42 online/target networks, Adam state, empty replay, training_steps0 and exploration1.0 are saved in models/pricing_dqn/passenger_sensitive_v1_seed42/. No historical weights loaded. The persisted checkpoint predates bounded fixture mutations and remains fresh. training_gate.json disallows long training until a floor is frozen. Readiness here means initialization ready, not training authorization.

## 22. Protected Evaluation Boundary

Calibration query explicitly filters >=2026-01-01 and <2026-03-16 before quantiles/support. Fixture March12 only. Runtime guard prohibits March17–31; March16 can only be development validation. No protected hierarchical/calibration/selection data accessed. Historical artifacts untouched.

## 23. Implementation Status

- `PRICING_V1_SPEC_FROZEN = YES`
- `REQUEST_LEVEL_ACTION_SELECTION_IMPLEMENTED = YES`
- `STATE_13D_UNCHANGED = YES`
- `POSITIVE_EPSILON_PROVIDER_IMPLEMENTED = YES`
- `EPSILON_RESPONSE_LABELS_AVAILABLE = NO`
- `EPSILON_CALIBRATION_PROXY_USED = YES`
- `EPSILON_MIN_FROZEN = NO`
- `PASSENGER_PC_IMPLEMENTED = YES`
- `FEASIBILITY_MASK_IMPLEMENTED = YES`
- `MASKED_EXPLORATION_IMPLEMENTED = YES`
- `MASKED_BELLMAN_TARGET_IMPLEMENTED = YES`
- `EMPTY_MASK_NO_OFFER_IMPLEMENTED = YES`
- `NO_OFFER_REPLAY_TRANSITION = NO`
- `REQUEST_LEVEL_REPLAY_IMPLEMENTED = YES`
- `NEXT_ACTIONABLE_REQUEST_SEMANTICS_VERIFIED = YES`
- `TIME_AWARE_DISCOUNT_IMPLEMENTED = YES`
- `SLOT_BASED_8_UPDATE_CADENCE_PRESERVED = YES`
- `POST_SELECTION_CLIPPING = NO`
- `D_MIN_ACTIVE = NO`
- `OLD_EP25_CHECKPOINT_RESUMED = NO`
- `FRESH_DQN_NAMESPACE_READY = YES`
- `LONG_DQN_TRAINING_STARTED = NO`
- `ROOT_README_UPDATED = YES`
- `CURRENT_STATE_README_UPDATED = YES`
- `ACADEMIC_REVIEW_README_UPDATED = YES`
- `DOCUMENTATION_CONSISTENCY_VERIFIED = YES`
- `PROTECTED_FINAL_HIERARCHICAL_EVALUATION_UNTOUCHED = YES`

## 24. Remaining Research Decisions

Only epsilon_min remains a research decision for training readiness. Allowed floors are fully compared, none uniquely justified by the specified finite/stability conditions. No new architectural approval is needed. After explicit floor selection, freeze provider provenance/config before any separately authorized long training.

## 25. Artifact Index

Positive-first correction validation passed: independent restricted-source quantiles, inclusive membership/source order, paired distances, all candidate floors, P_c calculations, feasible-arm counts and four-group totals. Record-029 file sizes/mtimes and small-artifact hashes are unchanged. See `positive_first_calibration_validation.json`. No simulation or training rerun.

All required JSON/MD/CSV artifacts are present, plus restricted_calibration_support.json, epsilon_min_decision.json, fixture_validation.json, slot_validation.csv, focused_tests.log and cached positive_epsilon_calibration.npy/calibration_distance_km.npy for reuse. Scripts calibrate_positive_epsilon.py and validate_request_fixture.py refuse redundant completed work. Source modules and tests are linked in request_level_architecture.md. Earlier preflight_integrity.json is historical; calibration_support_blocker.json records its explicit resolution.
