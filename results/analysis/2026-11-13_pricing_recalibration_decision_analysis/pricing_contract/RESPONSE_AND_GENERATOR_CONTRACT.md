# Response, observability and generator implications

## Mask information

For ascending candidate prices c_j=a_jP_base, m_j=1[c_j<=P_accept]. The mask is a feasible prefix of length K. For0<K<7 it reveals c_(K-1)<=P_accept<c_K; K=7 reveals P_accept>=c_6. Current minimum protection ensures K>=1. This is passenger-specific interval information used by exploration, greedy selection and Bellman maximization, although raw Q(s,a) does not receive epsilon, distance or the threshold as features. Equal13D states can have different feasible actions.

If the mask disappears, neither epsilon nor request distance/threshold is present in the unchanged 13D state. Context may predict an aggregate acceptance distribution but cannot distinguish individual passengers with identical state and different independent epsilon draws. Classification: **POST_ACTION_RESPONSE_WITH_UNCHANGED_13D_STATE=UNOBSERVABLE_WITH_RESPECT_TO_PASSENGER_THRESHOLD**. This does not claim the entire simulator is unobservable. No features are added.

## Explicit rejection decisions required

- Define accepted/rejected outcome and whether clipped offer or proposed action is evaluated.
- Define reward for rejection separately from accepted-unmatched; no penalty/value is selected here.
- A selected rejected action requires an explicit transition policy; current no-action skip must not silently be reused.
- Specify dispatch bypass and ensure no vehicle/commitment/energy change for rejected requests.
- Link to the next chronological actionable/selected request under the chosen semantics; settle terminal handling.
- Define attempted/accepted/assigned counters. Existing mu/sigma/F_hat use successful assignments; document whether that remains unchanged. Rejected offers must not accidentally enter successful-fare statistics.
- Specify replay fields for selected action, realized/clipped offer, outcome, reward, next state/mask and semantic version. If masks cease to represent passenger feasibility, define target maximization accordingly.

## Hybrid generator

Current origin counts come from forecasts; intact January rows preserve OD, distance, duration and fare jointly. Sensitivity is independently resampled. Array a pools Jan 1–Mar 15 distances conditional on1<=km<75. These distributions need not match: origin weighting, period and truncation differ.

Saved March 16 four-slot request export is a development illustration only, not an expected-generator distribution or selection dataset. No new requests, checkpoint load or simulation occur. `generator_comparison.json` and `generator_distance_comparison.csv` quantify this finite fixture against array a. Distances are already empirical, so a separate independent marginal draw is not automatically necessary. Whether to force array-a probabilities as the runtime target is **ACADEMIC_DECISION_REQUIRED**. Preserve the baseline and physical joint fields until that choice is explicit.
