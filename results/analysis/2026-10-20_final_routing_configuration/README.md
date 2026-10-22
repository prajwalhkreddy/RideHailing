> Superseded configuration status: the subsequent explicit baseline decisions freeze all seven numerical values. See ../2026-10-20_final_routing_policy/README.md. The historical discussion below records the earlier unresolved stage. routing_configuration.json contains the current frozen values.

# Final routing configuration and structural migration

The final project architecture is **169 → 64 → 32 → 9**. No routing training, production FedAvg, simulator episode, CNN work or pricing-DQN work was performed. **ROUTING_TRAINING_READY = NO** pending the seven numerical decisions below.

## Frozen state and output

`src/routing/final_state.py` defines the exact feature order. Indices 0–26 contain μ, σ, F̂ for each of STAY/N/NE/E/SE/S/SW/W/NW, in that order. Indices 27–168 contain Ĥ for Grid_ID 0 through 141. Units are USD, USD, successful dispatches/minute and minutes respectively. No normalization is introduced. Invalid candidate triples are deterministic zeros with a separate action mask; they are not observations or estimates for a fabricated grid. All 142 global charging-wait estimates are retained.

`RoutingState.from_producer` uses the canonical published operational state at the requested decision timestamp. `encode_routing_state` rejects legacy states and checks shape, finite/nonnegative values and masked placeholders. No fare_count or raw-wait substitute enters the state. `policy_state_spec.json` describes every index.

`src/routing/learning.py` builds the final model with unchanged 64/32 hidden layers and nine linear logits. `masked_softmax` masks before normalization. Invalid probabilities are zero; valid probabilities sum to one. `src/routing/federated.py` inherits the new dimension/version and requires identical final parameter shapes.

## Narrow source resolution and project decisions

Final targeted rereading of `notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx` confirms:

- XML paragraphs 154–155: F̂ and Ĥ equations, AUTHORITATIVE_SOURCE_FOUND; no numerical δ/κ values.
- Paragraph 156: α/β/δ/κ/ζ names, but no exact μ/σ formula or final coefficient values.
- Paragraph 171: safe handling of near-zero σ, AUTHORITATIVE_SOURCE_FOUND as a qualitative requirement; numerical floor NOT_FOUND.
- Paragraphs 159–161 and 174–175: utility/objective equations, but no final reposition-cost coefficient.
- Paragraph 188: nine candidate triples plus Ĥ for all grids.

The bounded source findings from the preceding interface task remain applicable; no further broad search was performed. `parameter_source_matrix.csv` separates source evidence, provisional values, project values and unresolved items. AUTHORITATIVE_SOURCE_FOUND applies to the equations/qualitative requirements above, not to numerical values which were not found.

As explicitly authorized in this task, the following are now **PROJECT_IMPLEMENTATION_DECISION**, not manuscript-exact claims:

μ(t) = α × mean(previous completed slot's successful-assignment fares) + (1−α) × μ(t−1).

σ(t) = β × population SD of that same population + (1−β) × σ(t−1).

Only ASSIGNED dispatches enter either recurrence. Empty price slots carry μ/σ. This σ recurrence smooths within-slot SD; it is not a pooled running-variance equation. F̂ uses successful dispatch count/30 minutes, not fare_count as a state substitute. Ĥ uses the previous completed slot's observation. No future/same-slot outcomes enter decisions.

Charging aggregation is frozen as the mean elapsed queue wait across all queued EVs at co-located stations, weighted by queue count. An observed station grid with no queued EVs reports zero; missing/nonstation observations carry prior Ĥ. This is a queue snapshot, not completed-wait duration. Station count/capacity/power remain unchanged.

## Configuration, safeguards and cost

The single canonical specification is this folder's `routing_configuration.json`, referenced by `config/config.yaml: final_routing`. Every field records value, status and rationale. `src/routing/configuration.py` reads it and exposes `configured_interfaces` to construct the producer and utility interface. Missing required values block startup; `LocalRoutingLearner.train_for_slot` also checks this contract before any training.

α and β have provisional legacy values 0.3, but their **final values remain null**. δ and κ remain null. ζ is unused by the frozen recurrences and classified NOT_REQUIRED_FOR_CURRENT_MODULE; no ζ value or dispatch interpretation is invented.

Numerical safeguards are explicit project configuration decisions:

- σ floor: **0.000001 USD**, far below cent-scale fare resolution.
- Ĥ floor: **0.000001 minutes** (60 microseconds), far below operational time resolution.

These are numerical regularizers, not empirical estimates or author values. Utilities use max(denominator, floor), preserving monotonic behavior with saturation within the floor region. Estimated σ/Ĥ are not changed. Both safeguards are required, validated positive/finite, and stored in configuration rather than hidden constants.

C_rep = explicit normalized utility-cost/km × graph distance in metres / 1000. The coefficient is **unresolved**, not invented. STAY costs zero, cardinal distance is 3 km, diagonal distance is 3√2 km; charging destinations use full shortest-path distance. No separate energy monetary cost is added; existing energy consumption constrains feasible paths.

## Initialization

`historical_priors` wires `data/processed/spatial_3km_jan_mar_2026/fare_bootstrap_legacy_cutoff.parquet` explicitly and verifies its saved fingerprint. It provides finite μ/σ priors for all 142 grids: 136 grid-specific and 6 global fallbacks. The verified source construction uses fares before 2026-01-25 18:30. The first decision must be **strictly later**; early-January starts fail closed and require a separate pre-start prior decision. No validation/test outcomes are fitted.

F̂₀ and Ĥ₀ remain explicit unresolved nonnegative finite values. Production factory construction is blocked until supplied. Fixture priors do not become defaults.

## Legacy and tests

155-input artifacts are **KEEP_PROVENANCE / SUPERSEDED_FOR_FINAL_169_INPUT_POLICY**. `src/routing/legacy_learning155.py` preserves the former implementation under an explicitly legacy path. Saved artifacts are untouched. `load_final_policy` rejects old input/output shapes; no reshaping or partial weight reuse occurs. Legacy learning tests are explicitly pointed at that provenance module rather than pretending they validate the new state.

Focused fixtures cover exact 169-feature order, 27/142 partition, boundaries, masks, nine outputs, checkpoint save/load, old-checkpoint rejection, historical-prior cutoff, configuration rejection, utilities/navigation and operational timing. Plain FedAvg is exercised with constant-weight tiny networks and unequal sample counts, a zero-sample participant and aggregated-weight loading. No gradient updates or training rounds are run.

## Exact remaining decisions

For starts after the historical-prior cutoff, freeze:

1. Final α.
2. Final β.
3. δ.
4. κ.
5. F̂₀.
6. Ĥ₀.
7. Normalized reposition-cost coefficient.

For earlier starts, additionally provide leakage-free μ₀/σ₀ priors. After these choices, the next task is train/validate the final nine-action routing policy and plain FedAvg. The architecture, price-recurrence forms, safeguards and charging aggregation no longer need a decision. Pricing DQN remains outside scope.

Validation result: **34 tests passed, 0 failed** using `python -B -m unittest tests.test_final_routing_configuration tests.test_operational_routing tests.test_operational_grid_state tests.test_config tests.test_routing_federated -q`. No training tests from the explicit legacy module were run.
