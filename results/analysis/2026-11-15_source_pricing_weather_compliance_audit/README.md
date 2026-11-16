# Source pricing and weather compliance audit

## Authority and scope

Only the two specified document titles define requirements here. Their available repository copies have no `(1)` suffix. Exact filenames, SHA256 and paragraph citations are in verification.json and every requirements row. Identity to an externally numbered copy is not independently verified. Findings are conditional on these available copies being the intended source versions. Later project decisions are implementation evidence, not amendments to these requirements.

No production, tests, training configuration, checkpoints, prior results or READMEs were changed. Only this audit directory is created. No training, model execution, test suite, clustering or simulation ran. Only a saved March16 request table was read for numerical checking; no March17–31 observations were accessed.

## Conclusions

**WEATHER_COMPLIANCE=PARTIAL. PRICING_COMPLIANCE=NOT_COMPLIANT.** There are5 independent blocking mismatch rows and4 major mismatch rows. These are specification-compliance findings, not an assessment of whether another design is useful.

Weather scenario statistics, defined mean/SD similarity, T1 grouping, combined-observation SD and explicit fallback reporting are substantially aligned. The documents neither mandate global K3 nor prescribe an algorithm, K, ddof, support cutoff or exact time partition. T2–T4 pooling of supported weather cells after failed clustering stability is not itself similarity evidence, and requires reconciliation with the stated combination basis. Raw-observation combination to compute pooled SD is explicitly allowed; it is not automatically prohibited joint model training.

Pricing does not implement the described proactive experiment. The active V2 runner is the V1-named subclass with a V2 provider, not its overridden legacy parent run_slot. Request-level passenger conditioning/masking, a modified ceiling and request replay cannot be presented as the requested source design.

## Blocking mismatches

- **P03 — Acceptance inequality against stated raw ceiling**: Effective ceiling max(0.85 P_base,P_raw), rather than document P_raw. Evidence: `src/pricing/passenger_sensitive_v2.py:119-124; src/simulation/passenger_sensitive_v1.py:63,75-76`. Required action: Use stated ceiling or obtain an explicit source amendment; do not present floor-adjusted acceptance as this document.
- **P04 — Alpha bounds from validated NYC fare limits**: Imports fixed seven factors0.85–1.15; platform limits computed FROM those factors × P_base, not validated NYC limits / P_base. Evidence: `src/pricing/passenger_sensitive_v2.py:7,107-111; src/pricing/passenger_sensitive_v1.py:8-11`. Required action: Validate/freeze NYC bounds, derive alpha limits, then specify action discretization.
- **P05 — Proactive destination pricing before slot/arrival**: run_slot selects action inside each arrived-request loop after advance_until. State cached by OD; actions not cached before slot. Evidence: `src/simulation/passenger_sensitive_v1.py:50-64`. Required action: Produce destination-based factors before slot; apply them to later requests.
- **P06 — Passenger details excluded from direct action selection; offer before response**: 13D tensor excludes epsilon/distance, but action mask uses both before selection; passenger details directly constrain available DQN actions. Evidence: `src/simulation/passenger_sensitive_v1.py:59-76; src/rl/passenger_sensitive_dqn.py:63-71`. Required action: Separate proactive price decision from request-specific acceptance; avoid pre-offer passenger feasibility masks.
- **P09 — Slot-level aggregated reward/transition**: ActionableRequestLinker stores one transition per request to next actionable request. Slot ledger sums revenue for reporting; complete_slot optimizer cadence is not slot replay aggregation. Evidence: `src/rl/passenger_sensitive_dqn.py:127-146; src/simulation/passenger_sensitive_v1.py:92-110`. Required action: Define and implement slot/destination reward aggregation and next-state semantics.

## Major gaps

- **W10**: No qualifying stable cut: full T-pooled runtime fallback, including well-supported weather cells. Failure to find a stable partition is not evidence that all cells are similar. Separate diagnostic grouping from fallback; establish source-compatible grounds for combining supported scenarios.
- **P07**: Accepted-unmatched yields zero; actual passenger rejection branch absent. customer_accepted=True, rejected count hardcoded0. No-action requests skipped by linker, and are not rejections. Observe passenger rejection after offer and include its zero contribution in slot transition.
- **P10**: 13D=[forecast, previous dispatch, incoming commitments, nine routing probabilities, ordinal destination popularity]; no direct available-supply count or separate drop-off-probability vector. Reconcile missing supply/drop-off features; define exact structure before implementation.
- **P12**: Weather/time supports are sampled empirically; candidate distribution comparison was pooled, not separately fitted/validated per sufficiently supported group. Fit/compare and document defensible distribution for each supported group; do not transfer pooled superiority without group evidence.

## Exact active path and consequences

The conditioned harness imports `PassengerSensitiveExperiment`. Its override advances to a request arrival, caches the13D system-derived state by OD, samples epsilon from actual weather/time, computes raw and floored ceilings, builds the passenger mask, selects a DQN action, and sets customer_accepted=True. Epsilon/distance are not tensor features, but they directly affect action availability. State caching is not proactive action selection.

The selected offer cannot be rejected by the modeled passenger: feasibility is enforced first. Driver-price failure and accepted-unmatched outcomes are distinct and do produce zero reward. These do not substitute for observed passenger rejections. Empty-mask no-offer requests are skipped by the linker, but the floor guarantees at least the minimum arm for finite valid thresholds.

In the unchanged Highest Feasible March16 export, 42,125/73,754 (57.115546%) offers exceed the source raw ceiling but are accepted by the floored rule. This is a direct classification comparison of stored values, not an alternative-policy simulation. It does not estimate revenue or fleet outcomes after correction.

The slot ledger reconciles successful dispatch fares. Eight optimizer updates at slot completion and a slot revenue total do not change the unit of stored experience: each transition still connects actionable requests. Source requires slot aggregation but does not specify sum versus mean, destination indexing, normalization or exact transition construction. Those choices remain decisions, not inferred requirements.

The13D tensor contains forecast demand, previous dispatch, incoming commitments, nine routing probabilities and ordinal destination popularity. Available supply and a separate drop-off probability vector are absent. Their indirect influence through routing does not equal explicit source-described features. Weather/time as tensor features is optional.

## Distribution fitting: avoid an unsupported binary judgment

The source allows other data-supported distributions and does not select a parametric family. Empirical resampling is therefore not intrinsically forbidden. The verified gap is that comparative family/tail fitting was pooled, while weather/time supports are subsequently chosen empirically without per-supported-group comparison. Truncated normal is a mentioned candidate, not a mandated winner. The exact sparse fallback and sample-size thresholds are source-unspecified; dense T2–T4 pooling is a separate justification issue.

## Results that remain valid and reusable

Scenario counts/means/SDs, T1 grouping diagnostics, combined support statistics, support lookup metadata, raw P_max/offer arithmetic, existing reference provenance, and fixed-fixture integrity remain valid evidence for what was implemented. Historical/current V2 rewards, assignments, action frequencies and Q results remain valid under that different formulation; no deletion or numerical revision is warranted by this audit. Their existence or passing tests does not establish source compliance.

## What must change before source-compliant review

1. Confirm the exact source versions if the numbered copies differ. Freeze validated NYC fare bounds and derive the action range, rather than reverse-defining bounds from factors.
2. Restore proactive destination factors before slot arrivals; separate request acceptance from DQN action selection and reconcile the raw ceiling.
3. Preserve rejection as observed zero reward; define the unspecified slot/destination aggregation and replay contract explicitly.
4. Reconcile supply/drop-off state features, including the suggested historical/moving-average drop-off update.
5. Justify weather combinations/pooling and compare candidate fits/tails within supported weather/time groups; define sparse fallback transparently.
6. Only after separately authorized implementation and validation, regenerate acceptance/rejection, dispatch, slot-reward and policy comparisons under the corrected source contract. Do not relabel current V2 experiments as those results.

## Required results and figures

Numerical/content readiness: **18/34 required result rows**. Readiness is at the field/metric-definition level: an aligned arithmetic or dispatch-count definition does not make the entire experiment source-compatible. The matrix marks experiment-level reward/revenue/acceptance results as different-formulation evidence. Suggested and source-silent items are excluded from the denominator.

**No particular figure types are explicitly mandated by either inspected document. SOURCE_REQUIRED_VISUALS_READY=0/0, not proof that the review is complete.** The weather document suggests a scenario results table. It requires reporting individual/combined statistics and accepted/excluded groups; the pricing document requires fit comparison and evaluation of revenue/acceptance/dispatch. Histograms, CDFs, dendrograms, loss curves and Q scatterplots are optional renderings, not literal source requirements. The earlier63-figure package is not used as authority.

After changes, show scenario weather/time/count/mean/SD/group/combination results; validated references and fare-derived alpha bounds; per-group fit/tail comparisons and selected sampling/fallback; proactive state/action and slot transition definitions; offers/raw ceilings, rejection-zero outcomes, dispatch and revenue metrics. Exact graph styles and aggregation choices remain unspecified.

## Files

- [Weather requirements](source_requirements_weather.csv)
- [Pricing requirements](source_requirements_pricing.csv)
- [Implementation gaps](implementation_gap_matrix.csv)
- [Weather compliance](current_weather_compliance.csv)
- [Pricing compliance](current_pricing_compliance.csv)
- [Results readiness](review_result_gap_matrix.csv)
- [Source-required versus supporting visuals](source_required_visuals.csv)
- [Read-only verification and evidence hashes](verification.json)

Counts are independent audit rows: the integrated-flow summary P15 does not add another blocking count. P07 records the absent rejection outcome; its pre-action selection cause is already counted in P06. No tests were changed or run.
