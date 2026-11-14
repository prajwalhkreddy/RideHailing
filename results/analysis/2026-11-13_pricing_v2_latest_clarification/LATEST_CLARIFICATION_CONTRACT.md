# Latest academic clarification — authoritative V2 design reconciliation

Primary authority: `notebooks/plan/Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx`, read in full from OOXML. References below are document section numbers, not guessed pages. The document is a meeting explanation with illustrative suggestions; the underlying transcript was not independently reverified. User explicitly designates this clarification primary where it resolves ambiguity. No V2 implementation or training performed.

## Explicitly clarified by meeting

Sections1–3: `P_offer=alpha*P_base`; `P_max_c=P_base+(P_base/e_c)*((L-L_base)/L_base)`; accept iff `P_offer<=P_max_c`, subject to final sign/zero rules. P_max is a passenger ceiling, not the offer. **No alpha×P_ref or alpha×P_max.** No max(P_platform_min,P_max) guarantee is supplied; V1's threshold floor must not silently transfer. Actual trip distance enters the stated ceiling; no L_effective floor is newly authorized.

Sections2/9: alpha_min=P_NYC_min/P_base, alpha_max=P_NYC_max/P_base. Values, discrete count and spacing await freeze; illustrative seven factors are not final.

Section3: proactive destination-based factors selected before a30-minute slot, retained for arrivals in that slot. No request-level DQN decisions. Passenger e, distance, ceiling and threshold are **not direct DQN features**. Their effects enter acceptance/rejection and reward. This supersedes the preceding contract-resolution recommendation to add passenger-specific information for a request-level decision. Absence of those features is intentional under the clarified system-level decision, not itself a V2 defect.

Section4 table explicitly says accepts + ride allotted/dispatched → revenue; rejects + no allotment → zero, without rejection penalty. Its equations shorthand accepted request reward as P_offer; a binary allotment indicator is also mentioned. Allocation-gated revenue is the strongest literal reading. Existing accepted-unmatched reward0 is compatible, but the document never explicitly names accepted-unmatched: confirm this boundary in reward aggregation, do not treat acceptance as assignment. Rejected outcomes must not disappear merely because their contribution is0.

Section4.1 explicitly leaves request-to-slot aggregation unspecified. `SLOT_REWARD_AGGREGATION=ACADEMIC_DECISION_REQUIRED`.

Sections5–6: fit distributions by weather×time group, including truncated normal/gamma/lognormal; no family approved. Historical initialization of drop-off probabilities followed by moving-average updates. The EWMA equation shown is **illustrative**, and neither lambda nor exact moving-average model is prescribed.

## Already numerically supported

Candidates P_base22.354198442390455 USD and L_base4.616983790655043 km retain their prior provenance; no final numerical confirmation is inferred (section10 expressly lists references as outstanding). Signed trip orientation e=r_L/r_P; individual Jan1–Mar15 source and1.5<=L<75 km scope per user. Safe population6,967,155;14 actual weather codes;422 observed code×half-hour-of-day groups before final validity/denominator treatment. No new fitted distributions here. Existing evidence on sign/near-zero sensitivity and tail fitting remains relevant to ceiling/acceptance, but inverse-price infinite-mean reasoning is **not an offered-fare divergence claim** now: offered prices depend on bounded alpha, not sampled1/e.

Grid geometry remains142 valid grids,16×16 raster, frozen routing169→64→32→9. Current13D sources include causal J_hat, lagged dispatch count, incoming passenger commitments,9local routing probabilities and destination ordinal popularity. Fleet objects provide supply data and popularity infrastructure provides lagged drop-off counts. Those are reusable inputs, not a complete proactive state.

## Numerical calibration still required

P/L confirmation; NYC bounds and alpha discretization; signed/zero/near-zero rules; grouped fitted sensitivities and their support; group minimum support/fallback; moving-average parameter/window. No pooled lognormal is approved by earlier AIC comparisons. No floor or price repair is inferred. See seven numerical-freeze groups in REMAINING_NUMERICAL_FREEZES.md.

## Architecture decision still required

**Destination structure:** section3 says factors for possible destination grids, while section7 applies a corresponding alpha for an origin-destination pair. Both are compatible with either global destination schedule alpha_d,t (142 entries) or origin-conditioned alpha_o,d,t (up to142×142 before admissibility). The source does not choose. Current state is origin/destination-specific and routing probabilities are9local actions, not142 destination probabilities. Do not equate an action factor count K with schedule dimension. A naive joint action space is K^142 (or larger); shared per-destination evaluation, multihead/factorized Q, or another design require explicit architecture approval, not automatic selection.

**State:** exact system/grid layout, supply eligibility definition, arrivals scope, mean-dispatch window, destination/drop-off probability meaning and optional weather/time remain open. **Current13D sufficient: NO**, because system concepts/layout are missing, not because passenger-specific inputs are forbidden.

**Transition:** coherent temporal skeleton is `(S_t,A_t,R_t,S_(t+1),done,operational_mask_(t+1))` at slot boundaries, where A_t is the published schedule. Possible R_t choices: total assigned revenue; mean per offered request (zero rejection/unmatched contribution); destination-attributed vector feeding a defined factorized loss. These differ in objective and credit assignment; none frozen. Freeze discount per slot, empty-slot reward/transition, terminal flush, full schedule versus subdecision replay, and accepted-unmatched semantics together. Do not reuse request gamma or8updates/slot as automatically approved V2 training settings.

**Drop-off:** decide global versus origin-conditional probability vector, completed drop-offs versus other event counts, lagged observation horizon, normalization, empty slots and reset/persistence. Existing six-slot SMA counts and quintile popularity are not a normalized probability vector. `DROP_OFF_UPDATE_RULE=NUMERICAL_FREEZE_REQUIRED`, with the model/scope needing architecture agreement first.

## Superseded V1 behaviour

Per-request selection; passenger-willingness preselection masks; minimum-platform-clamped acceptance; automatic seven-action finality; request-level replay and discount timing; direct Episode25 continuation. Earlier alpha×P_ref/R1/R2 offer investigations remain historical diagnostics only; do not reopen them as current offer options. Earlier passenger-information feature recommendation is superseded for the proactive design.

Episode25 exact continuation NO. Fresh V2 learner/replay required after architecture freeze; any transfer initialization needs separate approval. Old checkpoints/results remain unchanged.
