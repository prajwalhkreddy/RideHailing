# Historical and Runtime Reference Reconciliation

| concept | historical_Record029 | runtime | same_or_different | why | methodological_impact |
| --- | --- | --- | --- | --- | --- |
| P_base | One global 21.34586956773507 USD | Resolved contextual mean fare; selected slot 20.321533859249936 USD | DIFFERENT | Exact WeatherCode × half-hour context, then period/weather/global fallback | A historical global base must not replace the runtime base |
| L_base_km | Price-conditioned global 4.856998243316242 km (479,000 reference trips) | Resolved contextual mean trip distance; selected slot 5.289170703620971 km | DIFFERENT | Runtime reference is the context mean, not the historical ±$1 subset | Reference-distance changes alter P_max even though unit conversion does not |
| epsilon definition | Signed relative_price_deviation / relative_distance_deviation | Positive abs(relative_distance_deviation / relative_price_deviation) | DIFFERENT | Reciprocal orientation plus absolute value and different reference population | Historical signed epsilon cannot be inserted directly into runtime P_max |
| epsilon sampling | Historical empirical distribution; archived support decisions | Uniform empirical row resampling with replacement within resolved pool | DIFFERENT | Duplicate-value frequencies preserved; caller-owned NumPy RNG | No Gaussian approximation, artificial floor or historical support substitution |
| P_max equation | Rearranging historical signed definition gives P_base*(1+epsilon_historical*r_distance) | P_base*(1+r_distance/epsilon_runtime), exactly the roadmap equation | DIFFERENT_EPSILON_CONVENTION | Historical epsilon and runtime epsilon have different definitions | FORMULA_ALGEBRA_EQUIVALENT refers to runtime versus roadmap, not interchangeable historical epsilon |
| Units | TLC miles in source; all reported distances converted to km | Trip and contextual reference both miles internally; km reporting | UNIT_INVARIANT | Same conversion in numerator/reference cancels | No numerical unit correction or retraining indicated |
| Denominator treatment | Strict distance gap <0.00804672 km unresolved; rows retained | Runtime positive empirical epsilon, no positive-epsilon floor or clipping | DIFFERENT | Historical resolution rule does not redefine current behavioural sampler | No silent transfer of historical filtering/support into runtime |

`FORMULA_ALGEBRA_EQUIVALENT = YES`: the active runtime equation is algebraically identical to the supplied roadmap equation **using its runtime positive distance/price sensitivity definition**. This does not assert identity with the historical price/distance definition.

`REFERENCE_CONVENTION_IDENTICAL = NO`. `HISTORICAL_EPSILON_DIRECT_SUBSTITUTION_VALID = NO`.

Let r_distance=(L-L_base)/L_base. Runtime uses P_max=P_base+r_distance*P_base/epsilon_runtime. Historical signed epsilon_historical=r_price/r_distance would instead imply P=P_base*(1+epsilon_historical*r_distance). Even the reciprocal relation requires identical references and a sign convention; those conditions do not hold between these artifacts. The difference is documented existing methodology, not a newly introduced change.

Runtime references resolve exact WeatherCode × Period, then same Period, then WeatherCode, then global. Every fallback pool has its own reference means and associated empirical values. Epsilon is sampled with replacement, retaining duplicate frequencies. The current runtime source has 2,812,236 valid pre-cutoff January observations and 243 exact contexts. No Record-029 bounded support is substituted.

The historical source threshold is expressed as an absolute distance gap (half the recorded distance resolution), not a dimensionless relative-deviation cutoff. Its raw provenance is 0.005 source miles, equivalent to 0.00804672 km. Earlier frozen-reference JSON contains historical unresolved notes; the later authoritative-epsilon methodology supplies this resolution rule. Neither file overrides the active passenger acceptance contract.

Sources: `data/processed/price_distance_sensitivity_record029/frozen_reference_values.json`, `authoritative_epsilon_methodology.json` in the same directory; `src/pricing/empirical_sensitivity.py`; `src/pricing/customer_sensitivity.py`; `src/pricing/dqn_contract.py`; `src/simulation/final_production.py`; and the consolidated roadmap indexed in `source_index.csv`.
