# Implementation migration plan

No implementation or training is authorized by this readiness package.

1. Freeze validated fare bounds / alpha range.
2. Freeze action discretization.
3. Freeze proactive state/action unit and causal feature scopes.
4. Freeze reward/transition aggregation, unmatched reward and temporal semantics.
5. Fit/select conditional sensitivity distributions after grouping/fallback agreement.
6. Implement post-offer raw-ceiling acceptance/rejection.
7. Implement slot replay and operational-only masks.
8. Run focused unit and integration tests.
9. Only with separate authorization, fresh training.

Phases1–5 require recorded methodology decisions and subsequent fitting authorization. Phases6–8 implement the frozen contracts in a separate version. Test pre-arrival action timing, causal snapshots, zero-reward rejection without dispatch, unmatched treatment, no passenger pre-mask/bootstrapping mask, slot sums/replay, no duplicate assignment, fleet/charging conservation, conditional support and protected dates. Phase9 needs passed gates and explicit launch authorization. Do not warm-start from historical request replay or present its Episode25 results as evidence for the new formulation. Preserve all old checkpoints, fixtures, baselines, audits and V1 artifacts.
