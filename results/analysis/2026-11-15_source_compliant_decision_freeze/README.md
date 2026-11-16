# Source-compliant decision freeze

## Frozen scope

PRICING_DECISION_UNIT = DESTINATION_GRID_PER_30_MINUTE_SLOT. Produce142 factors before each30-minute slot, one per valid destination, shared across all request origins. This freezes the user-authorized decision unit, not a network architecture. Request origin does not select a different factor for the same destination. Global system information about origins is not forbidden; its aggregation into destination state remains unresolved.

Freeze offer=alpha*P_base and raw P_max=P_base+(P_base/epsilon)*((L-L_base)/L_base). After the offer, sample/use conditional epsilon and accept iff offer<=P_max. No floor protection or passenger-specific action masking. Rejection has0reward and no dispatch. Successful assignment earns offered revenue. Accepted-unmatched reward needs explicit project agreement; historical0 is evidence, not automatic approval.

The current simulator can look up destination IDs and maintain slot boundaries, but the active run_slot selects request-specific actions after sampling. It has no active precomputed142-factor schedule and explicit supply/dropoff state representation. These are exact implementation gaps, not a reason to change the frozen unit. Directional routing probabilities are origin-based; choose a causal system representation or approved aggregation, rather than silently treating them as destination arrival probabilities. Destination popularity is ordinal and distinct from normalized dropoff probabilities.

## Remaining design gates

Fare bounds: persisted cleaned Jan1–Mar15 robust quantile pairs provide candidates, not validated tariffs. Raw0.01 and2084.1USD extrema are not adopted. No arbitrary quantile is selected. Counts outside empirical bounds are recovered from persisted percentages; observations are not removed. P_base22.354198442390455USD and L_base4.616983790655043km remain existing references.

Action range is source-specified through validated bounds; number/spacing is not. Seven, nine and eleven evenly spaced options have project provenance in V2_SLOT_DQN_DESIGN.md. Concrete conditional factors are provided for each candidate bound pair; none selected using development performance.

Whole-slot gross assigned revenue has the strongest objective provenance: existing ledger totals plus the earlier proactive design proposal. That does not approve additive value decomposition or independent destination credit assignment. The older OD transition path selected at first arrival and cannot be relabelled proactive. Freeze state/action representation, unmatched reward, discount, terminal/truncation and zero-request handling before implementing replay. No new reward normalization is selected.

## Weather and fitting

The weather table preserves all scenario N/mean/SD and separates sparse support from dense pooling due to unstable clustering. T1K2 passes saved project criteria; T2–4 pooling is not justified merely by failure to find stable clusters. Existing time boundaries are project-defined, not source-specified. Combined support statistics remain available in the referenced current support inventory. Runtime minimum5000 also makes T1 group2(N1669) fall back despite statistical grouping support.

No final group set is frozen for the new architecture. Accordingly no candidate fit is run under invented group, truncation or selection rules. The21 existing overlapping support/fallback candidates are inventoried with REFIT_REQUIRED; no fitted parameters or winning family is fabricated. Existing global empirical/Gamma/Weibull/Lognormal/Exponential comparisons can be reused, but do not supply exact conditional comparisons including truncated normal. Once grouping/fallback and fit protocol are approved, compare support compatibility, parametric likelihood/AIC/BIC where valid, held-out CDF/KS, central quantiles and tails. Empirical resampling remains a justified candidate, not an automatic winner. Do not compare discrete empirical likelihood directly with continuous density likelihood.

## Authority and preservation

Available source documents are the same-title unsuffixed DOCX files. Requested(1).docx copies are not present; identity to external numbered copies remains unverified. Exact hashes are recorded. Paragraph-indexed source requirements and static code trace are in the preceding source-compliance audit/readiness packages. The pricing source fixes feature categories and causal sequence but leaves dimensions, aggregation, numeric bounds and family selection unresolved.

Existing Episode1–25 remains HISTORICAL_REQUEST_LEVEL_MASKED_V2, preserved unchanged. No production or historical artifact is edited. No simulation, training, fitting or March17–31 access occurs. Focused implementation tests remain mandatory after eventual changes. This package is a partial freeze, not readiness approval.

## Artifact guide

pricing_unit_state_contract.csv maps each feature to current code, dimensions, timing and scope. fare_bounds_decision.csv and action_discretization_decision.csv provide unselected empirical options. acceptance_reward_contract.csv lists outcomes and later code changes. slot_aggregation_decision.csv and discount_terminal_decision.csv isolate RL choices. weather_grouping_decision.csv preserves scenario evidence. conditional_distribution_selection.csv records unavailable fit results explicitly. source_compliant_freeze_register.csv is the authoritative partial register; required_review_results.csv defines the requested post-implementation results. verification.json records checks and gates.
