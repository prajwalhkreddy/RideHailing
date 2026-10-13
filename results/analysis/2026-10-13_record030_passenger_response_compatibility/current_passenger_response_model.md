# Current passenger-response model: semantic audit

## Evidence and scope

Read-only inspection of `src/pricing/customer.py`, `src/pricing/customer_sensitivity.py`, `src/simulation/pricing_dispatch.py`, `src/simulation/production.py`, relevant `config/config.yaml` settings and equation tests. Record-029 definitions below use the frozen specification supplied for this audit. No simulation, fitting, adapter or production change was performed. The audit distinguishes implemented equations from an independently validated behavioural interpretation.

## Two alternative response branches

### Eq. (31): no sampled sensitivity parameter

In `customer.py:customer_acceptance_probability`, let alpha be the selected pricing arm, S supply and D potential demand:

p_accept = 1 / [1 + exp(0.67 alpha S/D − 1.67)].

`draw_customer_acceptance` accepts if U < p_accept, U drawn from the explicit NumPy RNG. S is finite and nonnegative; D finite and strictly positive. The implementation evaluates the logistic stably and bounds probability to [0,1]. Alpha must be one of 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15. Fare = request base fare × alpha. For positive S/D, increasing alpha lowers acceptance; for S=0 the probability is constant in alpha. There is **no epsilon** in Eq. (31), and no maximum-price threshold in this branch. The coefficients 0.67 and 1.67 are fixed, not sampled customer sensitivities.

`config/config.yaml` defaults to this eq31 branch. This does not mean the production runner uses it: `production.py:run_slot` explicitly selects historical_sensitivity.

### Historical sensitivity branch

For WeatherCode and half-hour Period (0–47), `HistoricalCustomerSensitivityModel` resolves P_base, D_base, epsilon_mean and epsilon_std_population. With mu=epsilon_mean and sigma=epsilon_std_population:

E ~ Normal(mu, sigma²) conditioned on E>0.

These fields are passed as the **underlying Normal location and scale**, not the resulting truncated distribution's moments. mu and sigma must be finite and nonnegative. If sigma=0, E=mu with mu>0. Otherwise SciPy truncnorm uses a=−mu/sigma, b=+infinity and the supplied RNG. A numerical guard replaces a nonpositive returned draw by the smallest representable positive float. There is no finite upper bound or Record-029 support restriction. Group-specific numerical parameters are loaded from artifacts, not universal constants; this audit does not recompute them.

Production loads `data/processed/customer_price_sensitivity_2026_01.parquet` and `customer_price_sensitivity_fallback_2026_01.parquet`. Lookup is exact weather/period, then period, weather, global under production's hierarchical mode. It uses a separately spawned customer RNG. These are not the Record-029 empirical row artifact or its shared T1–T4 groups.

With r=(L−D_base)/D_base:

P_dispatch = P_base × alpha
P_max = P_base × (1 + r/E)
accepted = (P_dispatch <= P_max).

Equality accepts. Sampling makes acceptance stochastic across customers, but the comparison is deterministic given the draw. Historical acceptance does not use the Eq. (31) probability or its uniform draw. `pricing_dispatch.py` implements these branches separately. Acceptance is not completion: dispatch may still leave an accepted request unserved.

## Limit and monotonicity behaviour

E must be strictly positive; zero/negative inputs raise an error. Limits below are mathematical limits, not successful evaluations at zero.

- L>D_base: as E→0+, P_max→+infinity; increasing E reduces P_max toward P_base and cannot increase acceptance at a fixed offer.
- L<D_base: as E→0+, P_max→−infinity; increasing E raises P_max toward P_base and cannot decrease acceptance at a fixed offer.
- L=D_base: P_max=P_base for every allowed E; acceptance is alpha<=1.
- Decreasing E reverses these directions. Increasing E is therefore not uniformly equivalent to increasing price aversion.

The derivative is dP_max/dE=−P_base*r/E². A negative finite P_max is allowed by the implementation and rejects a positive offered fare; no floor is applied. Extremely small positive E can cause nonfinite arithmetic, which is rejected. E→infinity approaches P_base, but threshold equality at the limit need not describe acceptance for finite E.

## Units and code-implied interpretation

Prices are in USD; L and D_base must share distance units (runtime request field is trip_distance_miles). E, alpha and r are dimensionless. The code treats E as a positive inverse coefficient on relative distance in a maximum-price rule. If that rule is rearranged at equality with nonzero deviations, E=r/[(P_max−P_base)/P_base]. This is a code-implied algebraic ratio, not proof of the artifact's statistical provenance or identified willingness-to-pay. Equal units alone do not establish compatibility.

## Record-029 definition and algebra

P_base=21.34586956773507 USD; tau_P=±1 USD; L_base=3.01799878914405 miles.

r_P=(P−P_base)/P_base; r_L=(L−L_base)/L_base; e=r_P/r_L.

Record-029 e is signed empirical descriptive passenger price-distance sensitivity. The frozen simulation support is [−12.890744316473482,15.442447741158892]. Uniform row resampling with replacement preserves duplicates within T1 00–03, T2 04–05, T3 06–15, T4 16–23, shared Clear/Rain. It is not Gaussian or established causal willingness-to-pay elasticity. The frozen distance-resolution denominator rule and no-L_min decision remain unchanged.

For defined historical e, algebra gives r_P=e*r_L and P=P_base*(1+e*r_L). For the original paired observation and matching references this reconstructs historical fare. For a newly sampled e and a chosen distance it is an algebraically implied synthetic fare; independent resampling need not preserve the historical joint dependence of distance and sensitivity. It can yield negative fares for some pairs. It is **not** mathematically a maximum willingness-to-pay. Using it as an acceptance threshold requires an additional behavioural assumption, domain treatment and validation; none is supplied here.

As e→0 at fixed finite r_L, implied P→P_base: there is no singularity from e in this rearrangement. This differs from the runtime divisor. Record-029's historical numerical instability concerns r_L near zero, not e near zero.

## Reciprocal and substitution

The formulas align algebraically only under E=1/e, with nonzero e, matching references and interpreting the same price in both equations. This reciprocal is negative for negative e, undefined at zero and unbounded near zero. Its distribution is not the runtime positive truncated Normal. It also does not establish that historical fare is a behavioural threshold. Direct E=e substitution is therefore invalid as a semantics-preserving replacement; accidental agreement for special values does not make the parameters equivalent.

Classification: **DIFFERENT_PARAMETERS** under the present definitions and roles. A possible algebraic reciprocal is not a justified behavioural transformation.

## Existing test evidence (read, not executed)

`tests/test_pricing.py:test_eq31_exact_monotonic_bounded_and_zero_demand_guard` explicitly checks the logistic equation and factor monotonicity. `tests/test_customer_sensitivity.py:test_dispatch_and_maximum_price_formulas_and_validation` checks P_max=25 for (P_base,D_base,L,E)=(20,4,6,2) and P_max=15 for (20,4,2,2), and the opposing monotonicities above/below D_base. Its equality-acceptance test checks offered<=maximum. `tests/test_pricing_dispatch.py` checks historical rejection, equality acceptance and distinct seeded sampling. These encode the current model, not Record-029 compatibility.

## Terminology

Runtime uses epsilon_customer, epsilon_mean and sensitivity; Record-029 uses epsilon for a different ratio. The maximum_price docstring's “signed relative-distance formula” concerns r's sign, not a signed E (which is rejected). Recommend documentation names `epsilon_price_distance` for Record-029 and `acceptance_inverse_distance_coefficient` for current E; `acceptance_price_sensitivity` is an alternative only with a clear definition and monotonicity caveat. Do not rename code in this audit.
