# Passenger Pricing V2 — contract-resolution analysis

**Analysis completed; no V2 method or sampler frozen, implemented or trained.** The two original structural concerns are confirmed. P_norm is a normalization reference, not an evidenced operating floor; lognormal improves inverse-moment safety but does not resolve empirical tail mismatch or reference-price calibration. Neither R1 nor R2 is ready across the full range. R3 remains unspecified.

## Scope and provenance

Fixed for this analysis: e=r_L/r_P; P_norm22.354198442390455 USD; L_base4.616983790655043 km; Jan1–Mar15 paired trips with1.5<=L<75 km, N6,967,155; seven alpha factors0.85/0.90/0.95/1/1.05/1.10/1.15. Hybrid forecast/intact-trip generator retained. No physical distance changes, no protected rows, no raw preparation, no model loading or simulation. Read-only memory maps from completed decision-analysis intermediates were reused; no old absolute epsilon, T0 or historical VALID filter.

The PDF pp7–9 was re-read. Its fitted-family request is completed here; its flat-fare prose is distinguished from the normalization references as expressly instructed. It provides no empirical-curve sensitivity-adjustment formula for R3. Existing code was not reopened broadly; six directly relevant source hashes still match the context audit.

## Fit method and interpretation

All six still-open fare-gap scenarios are retained:0 (baseline),0.01,0.05,0.10,0.25,0.50 USD. Flag abs(P−P_norm)<t; fit conditional positive finite e among retained rows. Negative observations are not transformed or declared invalid; their runtime policy remains unresolved. Full positive sample masses are fitted through exact duplicate-value weights, not a random subset. Positive families have location0; normal is unrestricted baseline only. Gamma/Weibull shape roots solve full weighted likelihood equations. Quantiles use linear interpolation. No parameter sweep or data-driven denominator selection.

Thirty fits plus six empirical CDF comparators are saved. Each fit includes parameters, full weighted log likelihood, AIC/BIC, exact weighted KS, numerical CDF/QQ pairs fromP0.1 throughP99.9, median/P90/P95/P99 reproduction, five small-e probabilities, analytical inverse mean and inverse quantiles. AIC/BIC compare families only within identical scenario; KS is descriptive, not an unadjusted significance test. Empirical KS0 is in-sample identity, not validation. No charts requested or created.

**Lognormal ranks first by AIC in all six scenarios**, but is not approved for freeze:

| threshold_USD | parameters | KS | median_error_pct | P99_error_pct | inverse_mean_analytic | empirical_inverse_mean |
|---|---|---|---|---|---|---|
| 0 | {"shape": 0.9637247638314539, "loc": 0, "scale": 1.3984301420890135} | 0.0969342 | 18.0553 | -50.0458 | 1.13773 | 1.7298 |
| 0.01 | {"shape": 0.9620347297757698, "loc": 0, "scale": 1.3977642210768366} | 0.0967069 | 17.9991 | -49.8925 | 1.13642 | 1.72992 |
| 0.05 | {"shape": 0.9583509140086045, "loc": 0, "scale": 1.3958094082569008} | 0.09631 | 17.8341 | -48.9149 | 1.13399 | 1.7304 |
| 0.1 | {"shape": 0.9538192710174224, "loc": 0, "scale": 1.3928317985742418} | 0.0959277 | 17.6543 | -47.3107 | 1.1315 | 1.7313 |
| 0.25 | {"shape": 0.8979203506710228, "loc": 0, "scale": 1.346540622619858} | 0.0932883 | 14.6383 | -18.8716 | 1.11137 | 1.74936 |
| 0.5 | {"shape": 0.8815865687892596, "loc": 0, "scale": 1.3293945275182804} | 0.0932785 | 13.6924 | -10.369 | 1.10946 | 1.75876 |

At no fare-gap exclusion, lognormal has sigma_log0.9637247638314539, exp(mu_log)=1.3984301420890135, location0. It overpredicts median by18.06%, underpredicts P99 by50.05%, and has KS0.09693. At$0.50, errors are still+13.69%/−10.37%, KS0.09328. Best of tested models is not synonymous with empirically adequate.

## Inverse-moment safety and lower tails

For scale theta/shape k: exponential E[1/e] diverges; gamma is finite iff k>1, equal1/((k−1)theta); Weibull is finite iff k>1, equalGamma(1−1/k)/scale. Lognormal with log-mean mu and log-SD sigma has E[1/e]=exp(−mu+sigma²/2), finite for these parameters. Unrestricted normal's density at zero is positive, so its reciprocal expectation is not a valid finite expectation (principal-value cancellation is not safety); it also generates nonpositive e.

| threshold_USD | family | parameters | INVERSE_MOMENT_SAFE | inverse_mean_analytic |
|---|---|---|---|---|
| 0 | exponential | {"loc": 0, "scale": 2.746274121694012} | NO | inf |
| 0 | gamma | {"shape": 0.869922554377812, "loc": 0, "scale": 3.1569179438716914} | NO | inf |
| 0 | lognormal | {"shape": 0.9637247638314539, "loc": 0, "scale": 1.3984301420890135} | YES | 1.13773 |
| 0 | weibull | {"shape": 0.8190331079967583, "loc": 0, "scale": 2.274146005667813} | NO | inf |
| 0.01 | exponential | {"loc": 0, "scale": 2.6189995111851894} | NO | inf |
| 0.01 | gamma | {"shape": 0.9275712050835909, "loc": 0, "scale": 2.8235023864816613} | NO | inf |
| 0.01 | lognormal | {"shape": 0.9620347297757698, "loc": 0, "scale": 1.3977642210768366} | YES | 1.13642 |
| 0.01 | weibull | {"shape": 0.8449762748639603, "loc": 0, "scale": 2.2772830669133204} | NO | inf |
| 0.05 | exponential | {"loc": 0, "scale": 2.527946700326875} | NO | inf |
| 0.05 | gamma | {"shape": 0.9747900634561731, "loc": 0, "scale": 2.593324239851089} | NO | inf |
| 0.05 | lognormal | {"shape": 0.9583509140086045, "loc": 0, "scale": 1.3958094082569008} | YES | 1.13399 |
| 0.05 | weibull | {"shape": 0.8680784956451916, "loc": 0, "scale": 2.2697457884773424} | NO | inf |
| 0.1 | exponential | {"loc": 0, "scale": 2.4658413302170756} | NO | inf |
| 0.1 | gamma | {"shape": 1.0094325720951294, "loc": 0, "scale": 2.4427994483069777} | YES | 43.3992 |
| 0.1 | lognormal | {"shape": 0.9538192710174224, "loc": 0, "scale": 1.3928317985742418} | YES | 1.1315 |
| 0.1 | weibull | {"shape": 0.884911353261541, "loc": 0, "scale": 2.2570430831710495} | NO | inf |
| 0.25 | exponential | {"loc": 0, "scale": 2.0382922060035127} | NO | inf |
| 0.25 | gamma | {"shape": 1.348394420058191, "loc": 0, "scale": 1.511643904545043} | YES | 1.8988 |
| 0.25 | lognormal | {"shape": 0.8979203506710228, "loc": 0, "scale": 1.346540622619858} | YES | 1.11137 |
| 0.25 | weibull | {"shape": 1.0494151860150978, "loc": 0, "scale": 2.0876932036988936} | YES | 9.91723 |
| 0.5 | exponential | {"loc": 0, "scale": 1.9462579727138043} | NO | inf |
| 0.5 | gamma | {"shape": 1.4559026446665202, "loc": 0, "scale": 1.3368050259704019} | YES | 1.64082 |
| 0.5 | lognormal | {"shape": 0.8815865687892596, "loc": 0, "scale": 1.3293945275182804} | YES | 1.10946 |
| 0.5 | weibull | {"shape": 1.1062368778225227, "loc": 0, "scale": 2.035948304720211} | YES | 4.87395 |

Gamma only becomes safe at$0.10, where its inverse mean is43.40; Weibull only at$0.25. Thus safety can be highly sensitive to denominator-driven fit shape. Lognormal is consistently finite, but suppresses observed small-e mass. With no gap exclusion, empirical Pr(e<0.01)=0.000825851 versus fitted0.000000147601; Pr(e<0.10)=0.0117539 versus0.0030980. Observed inverse mean1.729800 versus fitted1.137727; inverse P99≈11.6394 versus6.73023. Finite moments alone do not validate the price tail.

DISTRIBUTION_DECISION classification fields assess **freeze readiness**, not formal hypothesis rejection: EMPIRICALLY_ACCEPTABLE=NO_FOR_FREEZE for tested parametric candidates; INVERSE_MOMENT_SAFE is analytic YES/NO; TAIL_BEHAVIOUR_ACCEPTABLE=NO_FOR_FREEZE (normal NO). Each has a reason. No candidate is demonstrated defensible on all three axes. Distribution remains academic; lognormal is the leading comparative candidate, not a frozen sampler.

The empirical finite-sample inverse mean uses all actual positive observations. `finite_grid_inverse_mean` is a separate100,000 midpoint-quantile deterministic estimate of the fitted reciprocal; its finite value must not be mistaken for a finite expectation when the analytic mean diverges. Normal inverse quantiles/mean are left undefined for positive-pricing purposes rather than silently conditioning it. All fitted lower-tail probabilities mean0<e<t; normal nonpositive mass is reported separately.

**PRICE_DENOMINATOR_FILTER_DOES_NOT_SOLVE_SAMPLED_SMALL_E_TAIL.** Removing P≈P_norm targets large |e|. Small e instead occurs near L_base relative to price deviation; fitting adds its own tail. Observed Pr(e<0.01) stays≈0.000826–0.000841, and empirical inverse mean rises1.7298→1.7588 across thresholds. No gap threshold selected to improve fit.

## Reconstruction versus independently sampled fares

All6,967,155 finite nonzero signed e values reconstruct observed fares using actual distance: maximum absolute error1.1368683772161603e−13 USD; mean≈4.8578e−16; zero errors above1e−9. No exact-zero e or undefined e in this population. This is algebraic identity, not out-of-sample accuracy. It does not apply to e0 division or the R1 floored distance below L_base.

Independent e destroys the observed joint relation between fare and distance. R1/R2 then define synthetic conditional fares; matching the marginal e distribution does not establish a realistic fare conditional on distance.

Offline integration uses256 empirical distance midpoint-quantile nodes crossed with256 fitted-e nodes per band/scenario/family. No request generation, RNG, dispatch or acceptance simulation. These are bounded quadrature diagnostics, not millions of independent predicted trips. All positive families are evaluated for reference failures; offers are evaluated for inverse-safe scenarios only, as **conditional diagnostics, not approved viable contracts**. Normal is not used to silently generate invalid positive-sensitivity fares. Negative-reference rates integrate the exact conditional CDF over distance nodes: for R2 below L_base, Pr(P_ref<0)=F_e((L_base−L)/L_base). R1 rates0. The512-node check for lognormal baseline/$0.50 is saved; coverage/quantiles remain approximations.

## Short- and long-distance evidence

Baseline lognormal, no fare-gap exclusion (both contracts/scenarios fully in CSV):

| contract | distance_lower | distance_upper | median_reference | median_observed | median_bias | negative_reference_pct | IQR_intersection_union | observed_coverage_reference_P05_P95_pct |
|---|---|---|---|---|---|---|---|---|
| R1 | 1.5 | 2 | 22.3542 | 10 | 12.3542 | 0 | 0 | 0 |
| R2 | 1.5 | 2 | 12.4533 | 10 | 2.45332 | 19.9419 | 0.253204 | 95.4385 |
| R1 | 2 | 3 | 22.3542 | 12.75 | 9.6042 | 0 | 0 | 0 |
| R2 | 2 | 3 | 14.9835 | 12.75 | 2.23352 | 12.6979 | 0.471805 | 91.3863 |
| R1 | 3 | 4 | 22.3542 | 15.6 | 6.7542 | 0 | 0 | 0 |
| R2 | 3 | 4 | 18.4521 | 15.6 | 2.85206 | 3.97746 | 0.697697 | 82.9466 |
| R1 | 4 | 4.61698 | 22.3542 | 18.4 | 3.9542 | 0 | 0 | 0 |
| R2 | 4 | 4.61698 | 21.3623 | 18.4 | 2.96228 | 0.211215 | 0.278709 | 49.656 |
| R1 | 4.61698 | 6 | 24.0977 | 21.2 | 2.89774 | 0 | 0.367739 | 34.8313 |
| R2 | 4.61698 | 6 | 24.0977 | 21.2 | 2.89774 | 0 | 0.367739 | 34.8313 |
| R1 | 5 | 10 | 29.0682 | 25.4 | 3.66822 | 0 | 0.338251 | 63.8932 |
| R2 | 5 | 10 | 29.0682 | 25.4 | 3.66822 | 0 | 0.338251 | 63.8932 |
| R1 | 10 | 20 | 53.8031 | 38.7 | 15.1031 | 0 | 0.130672 | 91.7909 |
| R2 | 10 | 20 | 53.8031 | 38.7 | 15.1031 | 0 | 0.130672 | 91.7909 |
| R1 | 20 | 40 | 99.8798 | 70 | 29.8798 | 0 | 0.0667495 | 97.7847 |
| R2 | 20 | 40 | 99.8798 | 70 | 29.8798 | 0 | 0.0667495 | 97.7847 |
| R1 | 40 | 60 | 163.171 | 98.9 | 64.2707 | 0 | 0.118358 | 94.6391 |
| R2 | 40 | 60 | 163.171 | 98.9 | 64.2707 | 0 | 0.118358 | 94.6391 |
| R1 | 60 | 75 | 234.942 | 189.2 | 45.7419 | 0 | 0.290098 | 83.001 |
| R2 | 60 | 75 | 234.942 | 189.2 | 45.7419 | 0 | 0.290098 | 83.001 |

R1 short-trip floor overprices1.5–2/2–3/3–4/4–L_base median fares by$12.35/$9.60/$6.75/$3.95. P_norm equals operational floor: **NOT_SUPPORTED**. L_base equals taxi-meter threshold: **UNRESOLVED**; interpolation identifies a normalization-curve crossing, not a tariff distance. P_FLOOR=UNRESOLVED.

R2 reduces those median biases to$2.45/$2.23/$2.85/$2.96, but generates negative fares for19.94%/12.70%/3.98%/0.21% respectively. Its higher interval coverage partly includes negative/overwide intervals; it is not validation. R1/R2 coincide for L>=L_base and show long-band median excesses≈$3.67/$15.10/$29.88/$64.27/$45.74. Neither has demonstrated full-range suitability. R3_FORMULA=UNSPECIFIED; no adjustment equation invented. No best viable P_ref is established.

IQR overlap is intersection/union length (also USD intersection), not probability; observed coverage is fraction of actual fares within generatedP5–P95. Reciprocal generated-inside-observed coverage is separate. Short/long reporting bands overlap intentionally and must not be summed.

## Actions and fare limits

All seven alpha factors multiply P_ref. For finite positive reference, distinct factors give distinct prices and span30% of reference; for negative R2 reference all offers remain negative and factor ordering reverses. Numerically distinct actions do not imply empirically useful action choices. Per-alpha un-clipped distributions and empirical fare coverage, plus envelope coverage and within-request span, are saved for inverse-safe candidate scenarios. Envelope coverage is observed fares within P5 of0.85×reference and P95 of1.15×reference, not an acceptance rate. Seven-action semantic viability **UNRESOLVED**, conditional on a valid P_ref.

Previous empirical intervals [6.60,94.70], [7.20,81.46], [7.90,70], [8.60,64.30] remain diagnostic CSV rows only. No clipping applied in this task. Bounds are not ready until reference semantics are resolved. Using them to eliminate R2 negative prices or R1 structural bias would be using clipping to repair a broken model, not simply enforce support; reject that justification. No operational floor has been established.

## Files, checks and boundaries

Only this README, DISTRIBUTION_DECISION.csv, REFERENCE_FARE_COMPARISON.csv and V2_CONTRACT_RESOLUTION.md created. Distribution CSV contains JSON parameter/CDF/QQ/lower-tail mappings within cells (compact diagnostics, not passenger arrays). Reference CSV uses record_type=RECONSTRUCTION/REFERENCE/ACTION/ACTION_ENVELOPE/QUADRATURE_CHECK/PREVIOUS_BOUND_DIAGNOSTIC; empty fields not applicable. Probability fields0–1, percentages0–100, fares USD, distance km. Inf indicates proven divergence; blank analytical normal inverse means undefined.

Focused checks passed: N/date-restricted provenance; unchanged source fingerprints;30 fits+6 comparators; lognormal six within-scenario AIC wins; gamma/Weibull shape safety conditions verified from parameters; lognormal analytic inverse formula checked; signed reconstruction tolerance; R1/R2 equality above reference; four-file scope. No simulator tests or training. No March17–31 analytical rows accessed. Existing V1/historical/previous analysis artifacts unchanged.

Quadrature check maximum median difference $0.026347; maximum P95 difference $0.490244.

Source hashes (match previous audit):
- `src/pricing/passenger_sensitive_v1.py`: `8874b1234f49496721582e43b997532f29bc48768a032be0d971875ce7a65b28`
- `src/simulation/passenger_sensitive_v1.py`: `77e81abaee4c3e4906d778e0858c0cf3ba2b6c811a25f34dc0a0ea7625b2fb30`
- `src/simulation/final_production.py`: `b2cd5371a632e745e1e65dcf9018fa3992942ff2e493caf3ec68b1d422fbaa78`
- `src/dispatch/generation.py`: `ae070a0a2e36341f169e12af98421b0916d9d58bd52ef65b5e61c2a46e3c4abf`
- `src/dispatch/dispatch.py`: `34178812543967eee87b96fa64f637e3d77292c9ad7c2c496b8cd9bcfe70cd62`
- `src/pricing/dqn_contract.py`: `ef9e65e6029ee62504532db9c44fbcb84f5c8f9836056ba0706be01bbcb279ee`
