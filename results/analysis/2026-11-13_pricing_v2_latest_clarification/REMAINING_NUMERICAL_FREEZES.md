# Minimum remaining freezes before coding

Counts use grouped decisions, not individual scalar parameters: **7 numerical/calibration freezes and4 architecture decisions**. These include dependencies; no claim that only numbers remain. The latest document explicitly leaves aggregation/state choices open.

## Seven numerical/calibration groups

1. **N1 References:** confirm candidate P_base22.354198442390455 USD and L_base4.616983790655043 km; units/version/population. NUMERICAL_FREEZE_REQUIRED.
2. **N2 NYC bounds:** empirical P_NYC_min/max using existing evidence; no new quantile selection. NUMERICAL_FREEZE_REQUIRED. Previous [6.60,94.70]/[7.20,81.46]/[7.90,70]/[8.60,64.30] are diagnostics, not approved caps.
3. **N3 Alpha grid:** afterN1/N2, freeze number K, spacing/endpoints and hard-bound numerical tolerances. alpha limits are ratios, historical seven not final. Depends onA2.
4. **N4 Sensitivity validity:** sign/negative runtime treatment, zero-e ceiling convention, near-zero price-denominator rule and fitted support/truncation. Zero denominator undefined; zero numerator/nonzero denominator zero. No automatic abs/oldT0. Candidate positive models alone do not settle negative population handling.
5. **N5 Weather/time calibration:** actual category/slot definitions and per-group fitted family/parameters/support/fit validation. Compare at least truncated normal, gamma, lognormal afterN4; no global-family default. Codes×48half-hour-of-day bins are available, not frozen. Other historical time groups do not transfer automatically.
6. **N6 Sparse groups:** minimum effective support, repeated-day support, missing/unseen weather/time fallback/pooling hierarchy. No threshold selected; no silent global fallback.
7. **N7 Drop-off numerics:** window length or lambda, initialization period and normalization tolerances afterA4. DROP_OFF_UPDATE_RULE=NUMERICAL_FREEZE_REQUIRED. Existing6-slot SMA is reusable evidence, not newly approved probability update.

## Four architecture decisions

A1. Exact proactive system/grid state and source scopes: supply eligibility; arrivals; mean dispatch; routing/drop-off representation; weather/time optional. No passenger inputs.
A2. Destination-action representation: destination-only versus origin-conditioned schedule; network factorization, action attribution and joint/factorized replay shape. No output dimension assumed.
A3. Slot objective and transition: reward aggregation, accepted-unmatched0 confirmation, destination credit assignment, empty slots, next-slot/terminal and discount semantics. Rejected contribution0 is already resolved; do not reopen a rejection penalty.
A4. Drop-off probability model/event meaning: global/conditional, observed completed events and causal updates, SMA/EWMA or another meeting-compatible moving average, carry-forward/normalization on zero-observation slots. Lambda alone cannot resolve these choices.

Ready semantics do not authorize coding. ResolveA1–A4 andN1–N7 before implementing the final learner; later bounded integration and training require separate authorization. No P_ref offer contract question remains.
