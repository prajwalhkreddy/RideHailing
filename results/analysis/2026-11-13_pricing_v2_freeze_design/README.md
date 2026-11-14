# Pricing V2 final pre-implementation freeze package

Primary proposals: [V2_NUMERICAL_FREEZE.md](V2_NUMERICAL_FREEZE.md) and [V2_SLOT_DQN_DESIGN.md](V2_SLOT_DQN_DESIGN.md); statuses in[V2_FREEZE_STATUS.csv](V2_FREEZE_STATUS.csv). Highest authority remains `notebooks/plan/Professor_Meeting_Clarifications_DQN_Dynamic_Pricing_Explanation.docx`. Earlier alpha×P_ref work is not the V2 offer contract.

This package closes bounded comparisons and supplies one minimal architecture proposal, **not an assertion all methods are resolved**. No implementation/training/checkpoint change. OldV1/results untouched. No March17–31 analytical rows accessed. Only four new requested files.

## Recommendations and evidence limits

- Retain document P_base22.354198442390455 and interpolatedL_base4.616983790655043 as candidates; explicitly confirm the reference-population distinction:documentP comes from[1,75), while new[1.5,75) mean is24.20370974379068.
- Recommend empirical simulation bounds[6.60,94.70], conditionalalpha endpoints0.2952465514256313–4.236340669698073; not statutory prices. Recommend11equal factors under transparent proposed$5quantization-error ceiling; not professor-selected.
- Preserve14raw weather categories, propose48half-hour clock groups.422observed groups,6,967,155trips.354groups with>=500positive fitted ×3families=1062attempts. Lognormal wins all converged comparisons but tails mismatch;354positive-truncated-normal attempts boundary-limited, not finalized fits. No runtime family freeze.
- Propose minimum5000positive observations andfallbackA(weather/time→weather→time→global).187directgroups cover92.856754% ofsource trip mass. Pooling coverage is not validation of fallback distribution fit.
- Recommendlambda0.30 for global drop-off EWMA by safe-period heldoutCE;lambda0.50winsBrier narrowly but has larger update variability.
- Propose142destination schedule via shared additive/factorizedQ approximation; systemstate2146, Qoutput[B,142,11]. Passenger-specific fields remain excluded.
- Assignedfare total reward; accepted-unmatched0 recommendation pending confirmation. Explicit slotgamma0.99candidate, not inherited request semantics. Fresh learner/replay required.

## Status counts

- ACADEMIC_CONFIRMATION_REQUIRED: 9
- ENGINEERING_CHOICE_READY: 5
- READY_TO_FREEZE: 1
- MORE_EVIDENCE_REQUIRED: 1

Ready/engineering-ready are evidence-backed proposals, not automatic academic approval.16items preserved. Remaining difficulties are explicit:reference population, pricing bounds, family/tail/support validation, factorization/state scope and objective/horizon approval.

## Methods and validation

Reused safe Jan1–Mar15 cache, existing weather filtered beforeMar16, existing verified fare/distance/e intermediates, and existing spatial dropoff_count filtered beforeMar16. No raw preparation or protected-row extraction. Group fitting uses conditional positive newe withno additional denominator cutoff; negative/zero/invalid/support counts documented. Temporary computational scripts/results stayed in system temporary directory; all review evidence consolidated into four outputs. No extra results tree created.

Fitting: weighted full-observation MLE using unique-value counts, loc0positivegamma/lognormal; truncatednormal bounds(0,infinity) optimized from3starts. Boundary parameters labelled invalidforfreeze. AIC/BIC/KS/quantiles retained pergroup. No naiveKSsignificance claim, no heldout distribution-fit success claim. Drop-off model selection uses Jan1–7historical initialization, warmJan8–Feb28, forwardMar1–15validation; observe/update after prediction. Not a final protected test.

Checks: support422groups sums6,967,155;positive total5,975,653;1062fitattempts/354groups; candidategrids strictly increasing andbound endpoints;0duplicateactions; dropout probability normalization and pre-update scoring; forecast metrics719nonempty slots; codehashes unchanged versus audit; required four-file scope. No simulator tests because no implementation.

- `src/pricing/passenger_sensitive_v1.py` unchanged SHA256 `8874b1234f49496721582e43b997532f29bc48768a032be0d971875ce7a65b28`
- `src/simulation/passenger_sensitive_v1.py` unchanged SHA256 `77e81abaee4c3e4906d778e0858c0cf3ba2b6c811a25f34dc0a0ea7625b2fb30`
- `src/pricing/dqn_contract.py` unchanged SHA256 `ef9e65e6029ee62504532db9c44fbcb84f5c8f9836056ba0706be01bbcb279ee`
- `src/dispatch/generation.py` unchanged SHA256 `ae070a0a2e36341f169e12af98421b0916d9d58bd52ef65b5e61c2a46e3c4abf`
- `src/dispatch/dispatch.py` unchanged SHA256 `34178812543967eee87b96fa64f637e3d77292c9ad7c2c496b8cd9bcfe70cd62`
- `src/simulation/operational_state.py` unchanged SHA256 `38d803b200a07d78022abc720c9fe955abaeb7b1f53a20c371bb2f038c905e39`
