# Passenger acceptance source-contract resolution

**Classification E — SOURCE_EQUATION_NOT_AVAILABLE.** **PROFESSOR_CLARIFICATION_REQUIRED = YES.** This means the original equation defining the active willingness-to-pay contract has not been established; it does **not** mean the repository contains no equations. Explicit project notes were found and conflict internally. No runtime code, model, data or prior report was modified. No regeneration, training, tuning or March17–31 access occurred.

## Source evidence and the conflict

`notebooks/plan/supervisor/Final_Next_Implementation_Process.docx`, Stage B (paragraphs46–49), defines fractional price/distance deviations and **epsilon=DeltaP/DeltaD**. Stage E (paragraph64) then states **P_max=P_base+P_base*DeltaD/epsilon** as a rearrangement. These cannot both represent the same epsilon relationship. Stage D additionally describes an ordinary Normal without mandatory truncation, whereas runtime uses positive truncation. Paragraph numbers identify 1-based XML paragraphs, not rendered pages.

`notebooks/plan/Price_Distance_Sensitivity_Implementation_Guide.docx`, paragraph134, also defines fractional price divided by fractional distance. It is a project methodology note, not independent evidence for the maximum acceptable fare equation.

`notebooks/plan/ImplementationPlan/Complete_Hierarchical_RL_Implementation_Roadmap_CNN_Updated.docx`, paragraph529, attributes an inverse-epsilon threshold to the manuscript but omits the P_base multiplier. It also explicitly asks for convention/unit confirmation. No exact original manuscript equation is identified there.

Two relevant stored pricing papers do not settle this conflict:

- `notebooks/plan/papers/Joint_Optimization_of_Pricing_Dispatching_and_Repositioning_in_Ride-Hailing_With_Multiple_Models_Interplayed_Reinforcement_Learning.pdf`, PDF page9: `F(x_i,c_i)=f0+zeta*(1-c_i)`, f0=0.5. This models a conversion rate from a pricing factor, not a relative-distance threshold.
- `notebooks/plan/papers/MARL-Based_Pricing_Strategy_via_Mutual_Attention_for_MoD_Systems_with_Ridesharing_and_Repositioning.pdf`, PDF page7, Eq31: a logistic conversion probability using pricing factor and vehicle/order ratio. It does not define the active price–distance epsilon or P_max.

The earlier `notebooks/plan/supervisor/customer sensitivity.pdf`, pages1,7–8, leaves the customer-preference paper/equation pending. This is a bounded source finding, not a repository-wide assertion that no unexamined document could supply it.

## Verified active formulas

Calibration implementation: `src/pricing/historical_sensitivity.py`, lines217–219, also recorded in `data/processed/customer_price_sensitivity_2026_01_metadata.json`:

`E_i = abs( [(P_i-P_base)/P_base] / [(L_i-L_base)/L_base] )`.

Thus calibration uses **price over distance**, followed by an absolute value. Its magnitude statistics parameterize the separate positive-truncated behavioural Normal.

Runtime `src/pricing/customer_sensitivity.py`:

`P_disp = factor*P_base`

`P_max = P_base*[1 + ((L-L_base)/L_base)/E]`

`accept iff P_disp <= P_max`.

This runtime inverse-E rule corresponds to **distance over price**. P_base and fares are USD; L and L_base (D_base in code) are miles; E and pricing factor are dimensionless. Runtime references are weather/half-hour resolved means, not Record029 global references. The P_base multiplier is present and dimensionally appropriate; that does not establish the source orientation.

## Exact clarification required — no choice made

1. If `E = fractional_price_change / fractional_distance_change`, algebra gives `P_max=P_base*[1+E*(L-L_base)/L_base]`.
2. If `E = fractional_distance_change / fractional_price_change`, algebra gives `P_max=P_base*[1+((L-L_base)/L_base)/E]`.

Both are dimensionally consistent with the P_base multiplier. Units cannot select one. These rearrangements assume the stated signed relationship: absolute calibration and positive truncation add behavioural assumptions and need explicit agreement too. Obtain the original equation with variable definitions/citation, or explicit professor approval of a self-contained project acceptance contract. Do not select multiplication/division merely to match a current component. Finding conflicting equations in a summary does not justify classifying either implementation as source-aligned.

## Minimum upstream correction bundle

**DISPATCH_PRICE_GATE_IMPLEMENTATION_REQUIRED = YES.** Preserve the existing verified finding that final FCFS does not enforce `P_disp >= P_i_min`; routing U1 is not a substitute. Once acceptance is resolved, implement the agreed calibration/sampling/acceptance corrections and this hard-price gate together. Equality must remain eligible. Validate units and request/driver boundary cases before authorizing one clean regeneration. No implementation is performed here.

## Downstream dependency impact

If either acceptance or dispatch eligibility changes, the current March1–15 routing experiences, central routing model, FedAvg model, routing probability adequacy result, March1–15 pricing run and March16 adequacy comparison are non-final **for the corrected contract**. Exact paths and causal reasons are in `upstream_dependency_impact.json`. Retain all as provenance; prior measurements remain evidence about the prior configuration. Do not delete or overwrite them.

Existing routing adequacy remains **ROUTING_PROBABILITIES_INFORMATIVE = NO**: FedAvg CE/Brier0.538560/0.245881 versus training-prior0.352059/0.117621. Do not tune or replace routing before corrected upstream simulation data exist.

## Resume point

Acceptance source resolution remains pending; combine its eventual correction with the missing dispatch gate before regeneration/retraining. March17–31 remains protected. Only root README's current blocker/resume subsection is updated; historical sections remain unchanged.

The requested verdict labels completion of this source-resolution investigation, **not approval of an unresolved mathematical contract**:

**PASSENGER_ACCEPTANCE_SOURCE_CONTRACT_RESOLVED**
