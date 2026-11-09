# Request-Level Bellman Return Scale Diagnostic

**CURRENT_BELLMAN_FORMULATION=METHODOLOGY_REVIEW_REQUIRED; STAGE1_REVIEW=REVIEW_REQUIRED.** This is a saved-artifact diagnostic, not a runtime or methodology change. No Stage2 launch. Technical Stage1 PASS is preserved; it does not establish scientific appropriateness of the value objective.

## Sources and scope

Stage1 completion marker, run_config, episode/slot summaries, saved512-point MC probe, and the exact Stage1 checkpoint replay referenced by the completion marker. All37,111 transitions remain in replay (capacity100,000); no trajectory truncation or development contamination. Only replay arrays are decoded; model files are hashed, never loaded. Directly relevant source verifies MC recurrence, next-actionable linking, terminal flushing and13D fields. Checkpoint files have identical before/after SHA256 hashes.

Request timestamps were not stored explicitly in replay. They are reconstructed as episode_end minus the cumulative remaining delta_t, using the saved terminal transition's time to episode end. Every slot's reconstructed count matches saved slot_summary counts exactly. Quantiles include the terminal transition's elapsed time; its gamma is unused for bootstrap. N nonterminal=37,110. No raw-data join or simulation rerun.

## Request density

{
  "requests_per_episode": 37111,
  "slot_count": 16,
  "requests_per_slot_min": 1549,
  "requests_per_slot_mean": 2319.4375,
  "requests_per_slot_median": 2381.5,
  "requests_per_slot_max": 2690,
  "actionable_equals_requests_every_slot": true,
  "unique_request_timestamps": 20735,
  "requests_in_shared_timestamp_groups": 26844,
  "extra_requests_beyond_first_at_timestamp": 16376,
  "mean_requests_per_unique_timestamp": 1.7897757414998794,
  "median_requests_per_unique_timestamp": 2.0
}

## Delta-t and gamma

| quantile | delta_t_minutes | gamma_eff |
| --- | --- | --- |
| min | 0 | 0.99994975 |
| P1 | 0 | 0.999977666 |
| P5 | 0 | 0.999988833 |
| P25 | 0 | 0.999994416 |
| median | 0.0166666667 | 0.999994416 |
| P75 | 0.0166666667 | 1 |
| P95 | 0.0333333333 | 1 |
| P99 | 0.0666666667 | 1 |
| max | 0.15 | 1 |

| condition | N | percentage |
| --- | --- | --- |
| delta_t_exactly_zero | 16376 | 44.1270782 |
| delta_t_lt_1_second | 16376 | 44.1270782 |
| delta_t_lt_10_seconds | 37111 | 100 |
| delta_t_lt_1_minute | 37111 | 100 |
| delta_t_ge_30_minutes | 0 | 0 |
| gamma_exactly_1 | 16376 | 44.1270782 |
| gamma_ge_0.9999 | 37111 | 100 |
| gamma_ge_0.999 | 37111 | 100 |


Same-time consecutive requests have gamma=1; subsecond/second gaps have gamma extremely close to1. Across an entire8-hour interval, discount is still0.99**16≈0.85146. Thousands of rewards are consequently summed with little elapsed-time attenuation. This is correct for the implemented continuous-time-discounted total-revenue objective; large scale alone is not evidence of error.

## Independent MC verification

| position_zero_based | timestamp | immediate_reward | future_requests_excluding_current | remaining_simulated_minutes | MC_return | direct_sum | absolute_difference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2026-03-02 07:00:00 | 18.1439891 | 37110 | 480 | 590407.348 | 590407.348 | 2.91503966e-07 |
| 9277 | 2026-03-02 09:11:10 | 22.413163 | 27833 | 348.833333 | 477539.204 | 477539.204 | 1.86264515e-07 |
| 18555 | 2026-03-02 10:59:49 | 18.1439891 | 18555 | 240.183333 | 322877.322 | 322877.322 | 4.18513082e-08 |
| 27833 | 2026-03-02 13:06:44 | 0 | 9277 | 113.266667 | 161941.451 | 161941.451 | 1.37661118e-08 |
| 37109 | 2026-03-02 14:59:58 | 18.1439891 | 1 | 0.0333333333 | 37.3552717 | 37.3552717 | 0 |
| 37110 | 2026-03-02 14:59:58 | 19.2112826 | 0 | 0.0333333333 | 19.2112826 | 19.2112826 | 0 |


The independent forward cumulative-product dot sum agrees with the reverse recurrence within2.92e-07 USD. The saved512-point probe matches recomputation with maximum difference0. No MC implementation error found. Saved MC summary statistics describe512 evenly spaced samples; this report's main MC statistics use all37,111 transitions, explaining small summary differences.

## Return by episode position

| episode_position | N | mean_immediate_reward | mean_MC_return | median_MC_return | P95_MC_return |
| --- | --- | --- | --- | --- | --- |
| 0–25% | 9278 | 14.7311348 | 536190.187 | 538136.389 | 583356.212 |
| 25–50% | 9278 | 18.2484408 | 402760.507 | 404317.411 | 470617.003 |
| 50–75% | 9278 | 18.4619455 | 242513.75 | 242762.338 | 314810.774 |
| 75–100% | 9277 | 17.7965464 | 80551.0001 | 79829.3574 | 153968.112 |


Correlation with remaining requests=0.998324296; remaining simulated minutes=0.998273817. These strong associations establish descriptive horizon dominance within this one realized trajectory; they are not a causal decomposition proving price/action has no effect. Pricing changes immediate fare and may alter assignment and subsequent fleet availability. Realized MC returns reflect the behavior policy and stochastic trajectory, not an unbiased independent estimate of optimal Q for each state/action.

## Immediate versus common future-value scale

Mean/median immediate reward=17.309503736/18.143989133 USD. Each adjacent arm changes offered fare by0.05×P_base=1.067293478387 USD (conditional on assignment, not a guaranteed revenue difference). Mean/median/SD full-chain MC=315510.192210916/322877.321850489/176195.107872545 USD. Median MC/median immediate=17795.277515; median MC/adjacent fare step=302519.717762. Most magnitude comes from future request revenue, not the current fare.

## State and terminal semantics

Active fields: J_hat,J_disp_previous,I_incoming,p_STAY,p_N,p_NE,p_E,p_SE,p_S,p_SW,p_W,p_NW,destination_popularity. Absolute simulation time:NO; episode progress:NO; remaining duration:NO; request index:NO; time-to-terminal:NO. Context can indirectly correlate with time but does not explicitly identify remaining horizon.

The saved protocol chooses a randomized start within March1–15 and executes exactly16 slots. run_staged.py sets terminal at j==15; the linker flushes the last real action and the target omits bootstrap. No modeled absorbing terminal event is required. Thus **EPISODE_BOUNDARY_SEMANTICS=ARTIFICIAL_TRAINING_SEGMENTATION**, not an intrinsic end to ride-hailing demand. This conclusion follows from the active schedule/terminal code, not inference from the duration alone.

## Identical-state horizon evidence

Unique13D vectors=2,424; repeated exact-state groups=1,407. Maximum within-identical-state time separation=29.983333 minutes. Same-state-and-action maximum separation=29.966667 minutes. The bounded strongest same-state/action pairs below show different realized remaining returns despite the same represented action/context:

| group_N | first_position | last_position | action | time_gap_minutes | first_MC | last_MC | MC_difference | first_reward | last_reward |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 313 | 20534 | 22871 | 0 | 29.9666667 | 288561.636 | 248529.864 | 40031.7717 | 18.1439891 | 18.1439891 |
| 440 | 18567 | 20527 | 0 | 29.9666667 | 322671.947 | 288693.415 | 33978.5324 | 18.1439891 | 18.1439891 |
| 203 | 29575 | 31992 | 0 | 29.9666667 | 131235.54 | 88766.8478 | 42468.6924 | 18.1439891 | 18.1439891 |
| 454 | 10905 | 13494 | 0 | 29.9666667 | 452671.054 | 411735.837 | 40935.2167 | 18.1439891 | 18.1439891 |
| 562 | 34422 | 37107 | 0 | 29.95 | 46087.1114 | 73.6430414 | 46013.4684 | 18.1439891 | 18.1439891 |
| 513 | 29574 | 31990 | 0 | 29.95 | 131253.684 | 88802.64 | 42451.0442 | 18.1439891 | 18.1439891 |
| 291 | 1549 | 3472 | 0 | 29.95 | 570871.237 | 550901.607 | 19969.6304 | 18.1439891 | 18.1439891 |
| 416 | 8365 | 10901 | 0 | 29.95 | 491106.227 | 452739.641 | 38366.5854 | 0 | 18.1439891 |
| 178 | 5806 | 8360 | 0 | 29.95 | 523891.503 | 491157.161 | 32734.342 | 18.1439891 | 0 |
| 258 | 5805 | 8359 | 0 | 29.95 | 523909.647 | 491175.305 | 32734.342 | 18.1439891 | 18.1439891 |


**HORIZON_ALIASING_RISK=HIGH.** Differences in realized MC alone cannot prove different conditional expectations; however, explicit artificial terminal dependence is absent from the state, while exact-state/action pairs and near-unit horizon correlations corroborate the concern. These are risk evidence, not proof that simply adding a field is the solution. No state change proposed or implemented.

## Offline objective illustrations only

| alternative | N | mean | median | SD | min | max | definition |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_current_request_chain | 37111 | 315510.192 | 322877.322 | 176195.108 | 19.2112826 | 590408.983 | Full request-event assigned-revenue chain, elapsed-time discount |
| B_immediate_request_reward | 37111 | 17.3095037 | 18.1439891 | 5.92968259 | 0 | 24.54775 | Contextual immediate assigned revenue; no future term |
| C_slot_aggregated_total_revenue | 16 | 343361.862 | 347167.424 | 175109.273 | 46340.8155 | 593368.783 | 16 slot-total rewards,0.99 per slot; represents total-revenue objective, not one request reward per slot |
| C_illustrative_next_slot_mean_chain | 37111 | 141.016433 | 146.089512 | 74.3864784 | 0 | 263.880117 | Illustration only: current request reward plus0.99 times future slot-mean-reward chain. Requires a new reward/value definition; not implied by merely changing next-state linkage |
| D_slot_normalized_request_chain | 37111 | 132.362134 | 139.823823 | 74.7906879 | 0.00714174075 | 254.434089 | Divide each request reward by all actionable requests in its slot, preserve current gamma chain; changes objective to slot-average revenue intensity |


A is the actual objective. B removes future revenue and therefore changes the control problem. Merely pointing to the next slot does not specify its reward or which passenger/state represents that slot. C includes both a slot-total illustration (which still has large cumulative-revenue scale) and an explicitly different slot-mean illustration, rather than silently equating them. D changes the objective by dividing rewards by request intensity; full slot counts also require end-of-slot knowledge. None was implemented or selected. Smaller numbers do not by themselves make an objective scientifically better.

## Decision

CURRENT_Q_OBJECTIVE: Expected total elapsed-time-discounted future successfully assigned gross fares over the global chronological actionable-request chain, ending at the artificial8-hour episode boundary.

MC arithmetic and saved chronology reconcile; no implementation error identified in the audited return computation. Total discounted assigned revenue can be a legitimate platform objective. The unresolved scientific issue is whether an artificial terminal global request chain, with no horizon in13D context, is the intended value representation. Common future revenue dominates the action-price increment and presents a difficult learning signal. The large returns alone are not grounds to call Q inflated; Stage1 Q is far below MC and has only128 updates.

**METHODOLOGY_REVIEW_REQUIRED**, not a claim of inherent invalidity of cumulative revenue. **STAGE1_REVIEW=REVIEW_REQUIRED**; do not launch Stage2 from this diagnostic. No recommendation among alternatives is frozen. Code, gamma, reward, state, replay, checkpoints and prior artifacts remain unchanged. Only this diagnostic package and the staged README link are written. March17–31 untouched.
