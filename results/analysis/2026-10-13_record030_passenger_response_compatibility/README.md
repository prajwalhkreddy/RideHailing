# Record-030 passenger-response compatibility audit

**Finding: DIFFERENT_PARAMETERS.** Eq. (31) has no sampled epsilon. The production historical branch instead samples a positive truncated-Normal divisor in a maximum-price threshold. Record-029 is a signed empirical price-deviation/distance-deviation ratio. Neither direct substitution nor an unapproved reciprocal preserves the current model.

## Recommended conceptual course

**Option A is recommended now:** retain the existing acceptance model as an explicitly separate model and keep Record-029 descriptive until a behavioural link is agreed. This preserves implementation, not proof of the existing model's empirical validity. The Record-030 empirical-sensitivity pricing experiment remains blocked. If that experiment remains the objective, Option B needs explicit methodology/professor agreement before an adapter is written.

| Option | Advantages | Required assumptions | Implementation impact | Risk |
|---|---|---|---|---|
| A: Keep acceptance; Record-029 descriptive | Preserves baseline and avoids conflating quantities | Existing acceptance assumptions remain explicit and independently contestable | None; separate reporting terminology | Cannot test pricing outcomes driven by Record-029 epsilon; baseline may be misspecified |
| B: Define a new behavioural link | Could support the intended experiment | Explicit approved map from descriptive e to response, treatment of signs/domains, behavioural validation | New response adapter and tests after approval | Historical fare is not reservation price; possible negative thresholds and loss of joint dependence |
| C: Calibrate/validate a separate response model | Separates descriptive evidence from behaviour | Justified identification/calibration targets; acceptance or behavioural evidence, not fare-distance ratios alone | Separate calibration/validation workflow after agreement | Nonidentification, confounding and falsely treating descriptive fit as behavioural validation |

No option was implemented. Taking absolute values, discarding negative values, reciprocating samples or replacing the empirical family would not be a neutral integration step.

## Files for review

- [Current model and algebra](current_passenger_response_model.md): exact branches, sampling, units, limits, source/test evidence and historical rearrangement.
- [Parameter comparison](passenger_response_parameter_comparison.csv): required semantic dimensions.

The frozen historical rearrangement implies a fare, not a maximum willingness-to-pay. An acceptance threshold requires an additional behavioural assumption. Recommend distinct names: epsilon_price_distance versus acceptance_inverse_distance_coefficient (or explicitly defined acceptance_price_sensitivity). No production renaming was performed.

## Audit boundaries

Only directly relevant acceptance, pricing dispatch, runner, configuration and equation tests were inspected. No simulation or test scenario was run. Only these three audit files were created; production code and Record-029 artifacts were not modified. The Eq. (31) label refers to the equation implemented in the repository, not an independent literature verification.

NOT_DIRECTLY_COMPATIBLE
