# V2 draft method contract — NOT FROZEN

## Provisionally supplied contract
- Calibration: individual paired Jan1–Mar15 observations,1.5<=L<75 km, N6,967,155; no old VALID/T0/abs filter. Physical distance unchanged.
- e=((L−L_base)/L_base)/((P−P_base)/P_base). Negative retained diagnostically; no automatic abs.
- Exact nonzero price denominator and zero numerator gives e0. Zero price denominator undefined/invalid, including0/0. Nonfinite inputs undefined. No silent fare for undefined e.
- P_base=22.354198442390455 USD, expressly fixed despite narrower range; display22.3542.
- N>=100 only supports half-km diagnostic bins;27 unsupported bins/1,665 trips retained in trip population.
- REQUEST_GENERATOR_V2_BASELINE=CURRENT_HYBRID: frozen CNN next30-minute forecast → request counts → intact empirical trip sampling preserving OD/distance/duration → independent calibrated sensitivity → pricing. No independent Array-a runtime distance draw. Calibration range does not silently filter runtime demand; behavior outside range needs subsequent validation.
- Actions remain [.85,.90,.95,1,1.05,1.10,1.15], with proposed offer alpha×P_ref, not alpha×global P_base.

## Recommendations pending academic freeze
- L_base: prefer4.616983790655043 km as interpolated curve reference over lower-edge4.5, not because it minimizes SD; neither is a uniquely validated meter distance. Both compared.
- Denominator threshold: **UNRESOLVED; no smallest stability cutoff supported**. Scenarios retain abs(fare−P_base)>=0/.01/.05/.10/.25/.50 USD; source rows unchanged. $0.10 is an interior diagnostic, not selected.
- Fitted distribution: **UNRESOLVED; exponential not justified**. Only requested exponential fitted, positive conditional MLE loc0/scale=mean. Scale ranges1.946258–2.821176; all12 exact parameter sets in CSV. DISTRIBUTION_FAMILY_STABILITY=WEAK. Empirical CDF is comparator only, not a substituted runtime sampler. Exponential near-zero support causes infinite mean unbounded inverse-e price; no floor/truncation chosen.
- NEGATIVE_E_RUNTIME_POLICY=ACADEMIC_DECISION_REQUIRED. Negative observations are not source-invalid. Diagnostic continuation can yield below-base long-trip prices and cannot establish a runtime rule.
- Bounds: [6.60,94.70], [7.20,81.46], [7.90,70], [8.60,64.30] corresponding P0.5–P99.5/P1–P99/P2.5–P97.5/P5–P95. Widest pair is a review comparator only; no bound frozen or statutory claim.

## Proposed reference equation
L_effective=max(L_observed,L_base).
For finite e>0: P_ref=P_base+(P_base/e)*((L_effective−L_base)/L_base).
For e=0: P_ref=P_base.
Undefined/nonfinite e: no silently generated price.
Negative e: no approved runtime branch; diagnostic continuation only.
P_offer=alpha×P_ref, followed by proposed empirical lower/upper clipping once bounds are approved.

Above L_base the positive formula algebraically inverts new e. Below L_base it deliberately imposes a flat reference, producing short-trip bias against observed fares. At e0 the reference branch equals P_base; whether the final offered price should still vary by alpha or be forced to P_base is a **branch-precedence question**, not silently resolved by this analysis. No historical P_raw/P_accept expression is substituted as a new response rule.

## Response, state and remaining approvals
Recommend operational-only mask then passenger response (B) to permit meaningful rejection; unchanged13D is not sufficient for individual passenger observability. Alternatively A uses passenger feasibility and makes rejection redundant. Approve response equation, required context, rejection reward, dispatch bypass, operational counters, chronological next-state/replay/discount semantics before implementation. No added features or rejection penalty here.

Seven remaining academic decisions: final L_base; price-denominator resolution; negative runtime/sign treatment; fitted family/support/parameters; fare limits; final reference/action/zero precedence; response/state/reward/replay architecture. Evidence does not authorize freeze just because analysis finished.

Implementation performed NO. Training performed NO. March17–31 analytical rows accessed NO. CNN/routing/grid/V1/checkpoints unchanged. No new sampler implemented.
