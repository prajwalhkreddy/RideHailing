# Minimal proactive slot-DQN proposal — no implementation

## Immutable academic semantics

Before each30-minute slot choose destination pricing factors. P_offer=alphaP_base. Passenger ceiling=P_base+(P_base/e)*((L−L_base)/L_base), subject to approved sign/zero rules. Accepted iff offer<=ceiling. No passenger-specific e/distance/ceiling in state or preselection mask; operational validity only. Rejection0 and bypassdispatch. Hybrid forecast counts + intact empirical OD/distance/duration generator retained; no independent Array-a draw. Historical V1 unchanged.

## Destination representation and Q architecture

Recommend one alpha per destination grid for entire slot:142-entry schedule, shared across request origins. This is the simplest reading of destination-based wording; origin-conditioned factors would create up to20,164decisions and are not uniquely prescribed. Origin-specific offers remain an academic alternative, not silently implemented.

Propose a shared destination-conditioned Q function q_theta(S,d,k), evaluated for all142destinations before requests. ForK11, outputs[B,142,11], selectedindices[B,142], actualalpha[B,142]. Output counts forK7/9/11 are994/1278/1562; do not construct K^142joint outputs. Shared parameters avoid142separate learners. A single dense1562head or shared destination evaluation are representational alternatives; shared evaluation is proposed for consistent destination treatment.

Because destinations compete for shared vehicles, independent pricing is **not scientifically equivalent to an unconstrained joint optimizer**. Explicit proposed approximation: additive value decomposition Q_total(S,A)=sum_d q_theta(S,d,a_d). This permits argmax perhead for an operationally separable mask and one joint slot loss against total slot reward; no separate global-reward label copied into142independent request transitions. Coupling/nonseparable hardconstraints would invalidate this simple argmax and require further design. Approve factorization as an approximation, not a professor-prescribed algorithm. No hidden network layers are frozen in this task.

## V2_STATE_SPEC_PROPOSAL

System grid matrix[B,142,15] in fixed Grid_ID order:

|Field|Pergrid width|Existing source / proposed definition|
|---|---:|---|
|Predicted next-slot demand|1|artifact_snapshots CNN prediction; causal availability before boundary|
|Available vehicle supply|1|Fleet.vehicles IDLE count at grid, exclude charging-required as proposed; no passenger-specific eligibility query|
|Passenger vehicles arriving|1|incoming known passenger commitments in next30min; scope explicitly excludes unverified reposition/charging arrival estimates|
|Mean successful dispatch history|1|OperationalGridState F_hat×30, smoothed expected half-hour count; source is rate/minute; proposed interpretation of mean JVT1, not raw lag count|
|Routing probabilities|9|_state_sources masked directional distribution perorigin; not a142destination transition vector|
|Drop-off probability|1|Proposed normalized global EWMA component forgrid; new producer using existing counts|
|Destination popularity|1|Existing ordinal encoding0/.25/.5/.75/1, separate from normalized probability|

Total2130grid entries. Append14-weather-code onehot and2cyclic time-of-day sin/cos: **2146 system-state dimensions**. Weather/time are recommended because response distribution changes by them; without them identical operational states can conceal predictable response regimes. These are pre-slot system context, not individual passenger details. Use causally available weather at boundary; no future same-slot observation leakage. Unseen weather requires explicit fallback/encoding contract; do not assume all codes forever present. Exact supply/arrivals/F_hat scope needs approval.

For a straightforward shared evaluator, concatenate flattened system2146 plus142destination identity onehot: input[B,142,2288] after broadcast; shared function outputs[B,142,K]. Destination ID is query metadata, not extra passenger state. Fixed grid ordering supplies spatial identity; a learned embedding is not required for this proposal. Operationalmask[B,142,K] contains only validfactor/index/hard-bound rules. All passenger thresholds absent. Feature scaling must be fitted on safe training data and versioned; dimensions do not authorize arbitrary scale defaults.

## Slot reward and transition

Proposed (S_t,A_t,R_t,S_next,done,operationalmask_next), with one transition per completed slot and no request-level linker. R_t=sum assigned gross offers (or fixed positive scale thereof, if approved). Retain audit counters per destination andwhole slot: offered,accepted,rejected,assigned,accepted-unmatched,revenue. Empty request slot still produces0reward transition as world evolves, if approved. Rejected requests contribute0 but are not removed from counters. No assignment-related fleet change for rejection; existing vehicles and charging continue with time.

Proposed Bellman target R_t+gamma_slot*(1−done)*sum_d max_valid_k q_target(S_next,d,k), subject to approved additive approximation. No actual optimization here. Terminal at true end of defined episode: no bootstrap, flush completed outcomes, preserve event-order semantics. Artificial truncation versus true terminal must be distinguished and frozen; do not silently zero continuation at an arbitrary observation boundary. Gamma0.99per30minutes is a proposed horizon decision, not the old request-step parameter. Replay hashes include state/action/reward/group-sampler/reference/time contracts.

## Causal sequence and routing compatibility

1. At slotstart advance previously scheduled physical events to boundary; snapshots contain only information available byboundary.
2. Build state with CNN forecast, live supply, known arrivals, completed-history estimates, routing probabilities, lagged drop-off vector and popularity; choose entire factor schedule once.
3. Generate/handle intact requests, apply saved destinationfactor, assign group sensitivity and ceiling, accept/reject; accepted proceeds to existing driver price/energy/FCFS eligibility.
4. Record successful assignment fare/commitments; vehicle movement and timed charging proceed chronologically during slot. Log actual completed drop-offs separately from future commitments.
5. At completion reconcile ledger/outcomes and assignment-time revenue; finalize physical events, update operational mu/sigma/F_hat/H_hat using approved completed observations.
6. Update drop-off vector with completed-slot proportions only; empty-slot carry-forward. Preserve historical popularity semantics separately unless explicitly versioned.
7. Update routing operational state/probabilities and routing missions in the approved existing boundary order, then construct next pricing snapshot; do not recompute S_t using those later outcomes.

Fleet/EV/grid/CNN interfaces stay; new prices/rejections shift assigned fares/supply and hence routing inputs. Later authorized bounded integration must test conservation, no duplicate assignment, causal state, probabilities, charging, reward and slot replay, and inspect routing distribution shift. No automatic routing retraining. No simulation now.

Episode25 exact continuation NO; old replay NO. Fresh V2 learner/replay required. Preserve V1 as evidence. Academic approval still needed for factorization, exact state scopes, aggregate reward, references/bounds, sign/support and gamma. No production code implemented.
