# Request-Level Pricing Architecture

**IMPLEMENTED.** The explicit user decision resolves the original action-granularity blocker. V1 is a separate opt-in execution path; historical OD/slot source and checkpoints remain for provenance.

| Component | V1 implementation |
|---|---|
| Decision unit | One individual passenger request, after distance/epsilon/P_c are available |
| Context | Same13D state, cached per OD/slot using existing state producer; no epsilon or P_c appended |
| Mask | Seven Boolean candidate-price<=P_c entries; applied in exploration, greedy selection and target max |
| Empty mask | No action/offer/acceptance test/dispatch/replay; separate no-offer count |
| Replay | state, action, reward, next_state, done, next_action_mask, delta_t_minutes |
| Linking | One pending actionable request; finalized only upon next chronological actionable request, including across slots |
| Skipped no-offer requests | Simulator clock and operational/request counters still advance; pending actionable transition retained |
| Time source | Actual simulator clock from slot start + empirical within-slot offset seconds, with existing mini-slot offset fallback |
| Discount | 0.99**(elapsed minutes/30); equal event timestamps give1, never synthetic minimum spacing |
| Terminal | Flush last actionable request at episode end, done=True and target=reward; stored elapsed time to episode boundary is ignored by bootstrap |
| Nonterminal target | Target-network maximum over next request mask only; all-false next mask raises |
| Reward | Actual successfully assigned offered fare; accepted-unmatched zero; no entry for no offer |
| Update trigger | Slot completion only; eight updates when finalized replay has>=1000 transitions, zero otherwise |
| Cross-slot accounting | A prior-slot pending transition is counted when finalized in the next slot; not fabricated early using future data |
| Episode reset | New V1 environment/linker/provider episode RNG, same learner for subsequent training episodes after terminal flush; learner/replay/optimizer schedule persist |
| Persistence | Separate V1 checkpoint schema stores masks and elapsed times; rejects legacy checkpoint metadata before loading models |

Implementation files: `src/pricing/passenger_sensitive_v1.py`, `src/rl/passenger_sensitive_dqn.py`, `src/simulation/passenger_sensitive_v1.py`. `src/dispatch/request.py` adds explicit V1 audit validation; FCFS selection and driver gate are unchanged. The V1 experiment inherits existing fleet/movement/charging/operational methods. CNN/routing/driver/EV/DP models and methodology are unchanged. This changes the pricing decision/replay boundary, not those components.

The old `multiepisode_pricing.slot` wrapper must not be used for V1, because V1 owns its eight-update slot trigger. Training requires an explicitly frozen floor/provenance and validation_only=False; diagnostic fixtures use train_dqn=False. No long-training launcher or old checkpoint resume is invoked.

## Bounded evidence

Historical fixture using superseded signed-first calibration; not current-population validation. Two capped March12 slots (first200 generated chronological requests each), fresh seed42 learner, real FCFS/EV interfaces, diagnostic P0.5 floor only. 400 requests,123 offers/assignments,277 no-offers,123 finalized replay transitions, zero rejected offers, zero optimizer updates. The first slot finalizes53 transitions and retains one pending; the terminal second slot finalizes70 including that prior request. Synthetic focused tests independently verify warmup and eight actual optimizer updates per completed warm slot, masked bootstrap, no-action skips and equal timestamps. The fresh persisted checkpoint remains untrained and empty-replay.
