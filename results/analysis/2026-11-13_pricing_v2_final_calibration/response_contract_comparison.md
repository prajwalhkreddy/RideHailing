# Passenger response alternatives — no implementation

| Aspect | Contract A: passenger mask | Contract B: operational mask, response afterward |
|---|---|---|
| Before decision | Current13D public context plus action mask derived from passenger threshold; policy/target use mask | Current13D public context, hard operational/pricing mask and proposed distance/sensitivity-dependent candidate offers; passenger threshold not in mask |
| Hidden from unchanged network | Raw distance, independently assigned e, threshold and offer vector; mask supplies threshold interval | Raw/effective distance, e, P_ref, actual seven dollar offers and passenger acceptance threshold/response parameters; none directly in13D |
| Selection/response | Selected feasible offer deterministically accepted; rejection redundant if mask uses same threshold | Passenger can reject a hard-feasible offer; response model must be specified independently of operational feasibility |
| Reward | Current gross successfully assigned fare and accepted-unmatched zero could be proposed, not automatically V2-approved | Rejection reward undefined; do not inherit accepted-unmatched zero without approval |
| Replay | Current masked next-request semantics require versioned validation for changed action meanings | Store rejection outcome; define next chronological state, time advancement, terminal/discount and bootstrap mask; no silent skipping |
| Dispatch | Accepted request enters driver/energy/price eligibility | Rejected request bypasses dispatch; accepted request may still be unmatched |
| Operational feedback | Successful assignments affect fares, dispatch counts, commitments | Rejections must not fabricate assignments/commitments; decide response/demand counters and updates explicitly |

Current13D = J_hat, previous successful dispatch count, incoming commitments, nine routing probabilities, destination popularity. Passenger e/distance are available to the surrounding simulator for reference generation, but not thereby visible to the network. A fixed seven-index network does not automatically observe changing dollar offers. Contract B is not fully passenger-observable with unchanged13D. A contextual-average partially observed model is possible only if explicitly accepted; no features are added here.

For state → feasible actions → mask → select → Accept/Reject → reward to include meaningful rejection, **feasible must mean hard operational/pricing feasibility, not passenger willingness**. Recommend B subject to approved state/response/reward/replay design. A is a valid alternative only when acceptance is intentionally structural. P_ref is not automatically an approved acceptance threshold, and no threshold or response function is invented. Driver eligibility is separate from passenger response in both contracts.

No simulation, network changes or training. Fresh versioned learner/replay would be required for approved changed semantics; old Episode25 is untouched.
