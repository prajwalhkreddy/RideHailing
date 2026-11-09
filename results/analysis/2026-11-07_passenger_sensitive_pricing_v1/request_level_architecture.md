# Current Request-Level Architecture

See [METHODOLOGY.md](METHODOLOGY.md) and [reconciliation](review_feedback_reconciliation/README.md).

13D state, request-level actions/replay, next-actionable linking, gamma=0.99 per actionable request transition and8/warm-slot cadence. Elapsed time is diagnostic only; the historical time-aware rule is superseded. All masks now use P_accept=max(0.85*P_base,P_raw), including next-state Bellman masks. Valid requests have at least one feasible arm. Defensive no-offer/no-replay remains for invariant defects; invalid values fail closed. Historical architecture details are preserved in review_feedback_reconciliation/pre_effective_threshold_provenance/.
