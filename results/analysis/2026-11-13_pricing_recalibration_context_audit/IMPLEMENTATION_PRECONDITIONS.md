# Implementation preconditions

This is a decision checklist, not implementation authorization. Existing V1 remains unchanged and paused.

## Established evidence

- [x] Supplied nine-page PDF read; exact formula extracted.
- [x] Array a recovered from the existing 148-bin Jan1–Mar15 aggregate, without guessed filters or protected rows.
- [x] Current signed ratio and V1 positive support construction traced.
- [x] Reciprocal conflict proven at identical nonzero references. Changed references prevent simply inverting the old sampling pool.
- [x] Hybrid request source, acceptance mask, driver eligibility, replay and downstream feedback traced.
- [x] Calibration, training, development and protected boundaries documented.

## Required academic/methodology agreements before coding

1. Freeze the new epsilon orientation explicitly for the replacement. Decide whether negative values are retained, transformed or modelled separately. The PDF direction is clear; historical VALID statuses and support do not automatically transfer.
2. Select the epsilon population: 148 equally weighted bin proxies, count-weighted proxies, or paired trip-level values. Specify representative distance (lower edge versus centre/mean), weighting and sample-size interpretation.
3. Freeze treatment of exact/near-zero price denominators, measurement resolution, the 0/0 case, exact e=0 and any probability mass at zero. The new zero-price branch must avoid division by zero.
4. Preserve Jan1–Mar15 calibration and exclude development-driven selection. Full Jan–Mar wording must not authorize protected rows. Array a already uses the permitted period.
5. Finalize the lower cutoff (1/1.5/2 km), upper bound and endpoint inclusivity. Specify whether cutoffs apply only to calibration or also to runtime demand.
6. Specify minimum bin count (50/100) and whether to remove sparse bins individually or select a contiguous upper cutoff. If runtime sampling changes, specify within-bin sampling and joint OD/duration constraints.
7. Freeze P_base precision after population selection; choose the final L_base definition. Candidates are the 4.5-km lower edge, 4.616983790655043-km interpolation or a separately justified meter threshold. Reference L_base and taxi-meter L_flat are not automatically interchangeable.
8. Validate and select the sensitivity family/support/truncation, or explicitly retain empirical sampling. Settle zeros, negative values and goodness-of-fit methods. New e cannot inherit old T0 quantiles.
9. Freeze empirical NYC lower and upper fare bounds using defined fare components and source validity. $0.01, $7.52 and $207 are not approved bounds.
10. Specify the complete reference-fare/P_max/generation equation, distance and epsilon inputs, piecewise floor, zero rule and clipping order. Resolve how a long-distance reference translates into a×P_base.
11. Finalize factors, action count and semantics. Decide action identity/replay handling if clipping makes different actions yield the same fare.
12. Resolve preselection masking versus postselection acceptance/rejection and the complete passenger-response function. Assess information lost when removing the mask from the current 13D context; do not automatically add state features.
13. If rejection is possible, decide its reward/penalty and chronological transition handling. Do not silently treat the existing unmatched-zero reward as an approved rejection reward.
14. Decide whether distance/spatial sampling replaces the forecast-driven intact-trip generator. Preserve actual physical distance and duration for EV/routing; fare calculations need a separate effective-distance field.
15. Agree on a versioned model/replay initialization and validation plan. Episode25 cannot be an exact continuation after environment changes. Transfer initialization requires separate approval.

## Implementation work after those decisions

- Create separate calibration, specification and sampling artifacts; preserve Record029 and V1 history.
- Implement only approved formula, zero, floor, clipping, response, action and replay changes. Update every active seven-arm assumption consistently if needed.
- Keep observed OD/distance fields unchanged. Test fare-distance isolation, boundary cases and unit consistency.
- Test masking or explicit rejection, rewards, next-request replay, checkpoint semantic compatibility and date guards.
- Validate eligibility, dispatch ledger, operational updates, fleet conservation, charging and routing-input shifts in a separately authorized bounded integration run.
- Reassess frozen routing before any retraining decision. Reference changes alone do not imply CNN/grid regeneration.
- Train only after separate authorization. March17–31 remains held out.

**EP25_REPLAY_COMPATIBLE_WITH_NEW_METHOD=NO.** Changed rewards, masks and states cannot reconstruct counterfactual fleet history through scalar correction. Historical replay remains preserved.
