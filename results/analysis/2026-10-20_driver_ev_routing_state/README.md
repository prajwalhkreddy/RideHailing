# Driver, EV and nine-action routing interface

**Interface implementation validated; production training is NOT ready.** Operational parameters and the policy input dimension require decisions. This focused change adds `src/routing/operational_interface.py` and focused tests; it does not activate the legacy simulator, change passenger acceptance, retrain models, or change station infrastructure.

## Authoritative source resolution

The current roadmap is `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx`. Stable zero-based XML paragraph locations are recorded instead of unstable rendered page numbers:

- Paragraphs 154–155: F̂ and Ĥ recurrences — FOUND_AUTHORITATIVE; δ/κ values — NOT_FOUND.
- Paragraph 156: α/β/δ/κ/ζ names, with a direction to use manuscript price equations; exact μ/σ recurrences and numerical values are not supplied.
- Paragraphs 159–161: U1, U2 and repositioning objective — FOUND_AUTHORITATIVE.
- Paragraphs 174–175: U3 and charging-destination objective — FOUND_AUTHORITATIVE.
- Paragraph 188: candidate μ/σ/F̂ plus Ĥ over all grids — FOUND_AUTHORITATIVE.

The narrow supporting search covered the charging implementation guide, supervisor implementation documents, the final module input/output PDF (especially pages 3/11), and targeted terms in the joint pricing/dispatch/repositioning paper. It did not establish the missing final parameter values, initialization, safeguard, or queue aggregation. This is a scoped negative finding, not a claim about every possible external manuscript.

`unresolved_configuration.json` classifies each requested item. Existing μ/σ EWMAs, provisional α=β=0.3, fare priors and queue aggregation are FOUND_IMPLEMENTATION_ONLY, not manuscript decisions. Required production choices remain PROJECT_CONFIG_DECISION_REQUIRED. ζ is not applied; its relation remains unresolved.

## Utilities and cost

- U1 = 1−Φ((P_min−μ)/σ), implemented with stable complementary error function. Price quantities are USD. A mandatory positive configured floor safeguards σ; no default is invented.
- U2 = 1−exp(−F̂×W_max), with successful dispatches/minute and minutes. Inputs must be finite/nonnegative. Floating-point saturation is represented by the largest float below 1 to preserve the open upper bound.
- U3 = 1−exp(−H_max/Ĥ), both waits in minutes. A separate positive floor is mandatory; missing safeguard fails closed.
- C_rep uses actual metric distance. STAY is zero, cardinal is 3 km and diagonal is 3√2 km. No established distance-cost coefficient was found in the inspected baseline: it used an equal average of legacy price, wait and charging utilities instead. The new interface requires an explicit normalized utility-cost/km coefficient. Its economic definition/value needs agreement; the 0.01 fixture value is not a production coefficient. Existing battery-degradation coefficients remain untouched.

Repositioning maximizes U1+U2−C_rep over valid, energy-feasible actions only. Exact ties choose the lowest canonical action index. All inputs are read through the operational producer's `state_for(timestamp)`, so the requested boundary must match its published state; producer completed-slot timing guards remain in force.

## EV navigation

Energy ≤ configured minimum selects charging; energy > minimum selects ordinary repositioning. This matches the existing implementation in `src/charging/energy.py` (its old docstring says “strictly below,” but its expression uses ≤). Battery calibration is not changed.

All 15 existing station IDs and their saved grid mapping are retained. Charging destinations maximize U3 minus full graph-path cost among reachable, energy-feasible stations. Dijkstra uses the saved true-3-km adjacency and actual cardinal/diagonal distances. Ties choose the lowest next-action index then station ID. Co-located stations therefore have deterministic identity selection without changing capacity or queues.

The final station grid is distinct from the next grid. `start_next_hop` marks travel BUSY, deducts next-edge energy and sets distance-dependent travel duration; current location remains unchanged until fleet arrival. It never teleports to the final station. At-station STAY does not bypass existing charger admission/queues. No reachable destination raises an explicit error rather than a teleport fallback. Station occupancy is not an exclusion: waiting is represented by Ĥ and existing queues.

Actions: 0 STAY, 1 N, 2 NE, 3 E, 4 SE, 5 S, 6 SW, 7 W, 8 NW. Local labels come from the actual decision's next hop and are checked against that origin's action mask. Legacy five-action labels are not converted or imported.

## Policy state: discovered structural conflict

The existing `src/routing/learning.py` network really is **155→64→32→9**, with 2 vehicle fields plus 9×17 legacy candidate features. Those features include raw/legacy fare and wait summaries and are not the roadmap operational state.

The explicit roadmap state is **9×3 + 142 = 169** features:

- Indices 0–26: action-order candidate triples μ [USD], σ [USD], F̂ [dispatches/minute].
- Indices 27–168: Ĥ [minutes], Grid_ID 0 through 141.

No normalization is introduced. Invalid candidate triples are zero placeholders paired with a separate nine-action mask, not imputed observations. Every index, association and unit is listed in `policy_state_spec.json`. All four estimates come from the operational state, never fare_count/raw wait substitutes.

The faithful encoder is implemented. Asking it for 155 features raises **STATE_DIMENSION_DECISION_REQUIRED**. No 14 values are silently discarded, no padding rule is invented, and the existing network/hidden layers/checkpoints are preserved. Consequently the new state is not connected to the old training path. Approval is required either to use 169 inputs or to define an authoritative 155-feature reduction. This is additional to the already-known parameter blockers.

## Output and FedAvg

Existing nine-logit output and `masked_softmax` are reused: masking precedes normalization, invalid probabilities are zero and valid probabilities sum to one. The tiny fixture confirms identical 155-input/9-output shapes, 1:3 sample weighting yielding 2.5 from weights 1 and 3, exclusion of a zero-sample client, and successful loading/inference of aggregated weights. This proves structural compatibility of the existing network, not compatibility with the unapproved 169-feature state. No FedAvg redesign or production training occurred.

## Validation and next dependency

Focused tests cover exact utility values/monotonicity, safeguards, unit contracts, distance cost, masks/ties, threshold equality, energy feasibility, multi-hop selection, timed movement, feature ordering, state timing, input incompatibility, output masking, and sample-weighted FedAvg. `hand_calculated_utility_fixtures.csv` contains explicit numerical examples. Test-only floors are 0.01 USD and 0.01 minutes; cost is 0.01 utility units/km.

The next task is to freeze the remaining operational equations/parameters/priors, charging-wait aggregation, safeguards, cost definition, and **155-versus-169 state specification**. Only then adapt the agreed input contract and train/validate the nine-action policy and plain FedAvg. Pricing DQN is not the next task. Production routing training ready: **NO**.

Validation command: `python -B -m unittest tests.test_operational_routing tests.test_operational_grid_state tests.test_config -q`. Result: **22 passed, 0 failed**. Only quick fixtures were executed.
