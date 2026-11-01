# Read-only pricing-DQN stability diagnosis

**PRICING_DQN_STABILITY = UNRESOLVED_RISK**  
**FINAL_PRICING_RUN_RECOMMENDATION = DO_NOT_RESUME_YET**

No concrete Bellman/terminal/replay implementation defect was found. This is not evidence of stable values: terminal predictions are grossly miscalibrated. No simulator, optimizer or training was run; models were loaded with compile=False and used only for inference. Checkpoint payload hashes matched before and after analysis. Existing experiment artifacts and code were not changed. March17–31 untouched; the authoritative500×16×8 run remains preserved.

## Contract and temporal semantics

The implemented standard-DQN target is y=r+0.99(1−done)max Q_target(s′). The online selected action receives delta1 Huber gradients; target inference is outside the gradient tape. Adam is followed by tau0.005 soft target update every step. No discrepancy with the frozen formula was found.

One transition is an observed OD context within a30-minute slot. Reward is the unnormalized USD sum of fares of successfully assigned requests for that OD in that slot—not total slot revenue or one passenger fare. The next state is built for the **same OD** after simulator evolution to the next slot. Other OD rows in replay are not trajectory successors. Shared fleet dynamics affect that state; a matching OD need not have an observed request/transition in the following slot. The13D representation lacks explicit remaining episode time and OD identity. Therefore exact finite-horizon Markov sufficiency and next-state training coverage cannot be assumed.

All observed OD contexts in slot16 are terminal; the current-state placeholder is masked. Terminal rows survive FIFO replay eviction normally. The full replay has5,684 terminal rows; episode25 terminal count is recorded in transition_semantics.json. Counts for all25 episodes cannot be recovered independently from the permitted episode25 replay, which lacks episode/slot/OD identifiers. **Code-implied cross-episode bootstrap count:0. Independently measured exhaustive count: unavailable**, not an invented zero. Minimum/maximum remaining reward horizon is1/16 slots (0/15 bootstrap edges);8.5 is only a uniform-slot reference, not a measured horizon.

## Reward and Q scale

100,000 saved rewards: mean26.390, P9587.987, maximum970.009USD. Complete quantiles and zero/positive shares are in reward_statistics.json. Positive rewards proxy assigned contexts; replay has no assignment-count field.

The16-slot discounted factor is14.8542. Constant empirical-mean and P95 reward scenarios yield392.00 and1,306.97USD. Repeating the largest observed reward yields14,408.73USD, an empirical reference—not a universal bound. The mean-reward infinite-horizon reference2,638.99 is not the implemented episode horizon.

Saved reporting probes show mean|Q| / maximum / loss:

|Episode|Mean absolute Q|Maximum Q|Mean loss|
|---|---:|---:|---:|
|1|261.97|591.05|20.08|
|10|2,415.10|6,879.50|259.83|
|20|5,279.11|19,156.78|435.99|
|25|10,454.33|37,174.42|778.97|

Those training Q probes use the latest512 replay states, whose composition changes. A separate seed42 sample of4,096 final replay rows has all-action Q median1,821.13, mean6,733.45 and maximum42,473.68. These different probes are not contradictory.

Multistep realized returns cannot be reconstructed from unlabeled FIFO rows. However all5,684 terminal observations have exact realized return G=r: mean predicted chosen-action Q7,475.14 versus mean G24.68; MAE and mean signed Q−G both7,450.46; correlation0.292; median Q/G among positive returns101.74. This is direct overprediction evidence, independent of any assumed reward bound.

## Targets, residuals and reuse

Online/target mean absolute Q6,733.45/6,812.06; mean absolute gap96.02, maximum1,171.78. They track closely relatively, but can share inflation. Masked bootstrap contributes95.46% on average to |r|+|bootstrap|. The fixed sample has mean absolute TD error886.73 and Huber loss886.23, versus the episode-average778.97. Sampled terminal residuals average approximately−6,829; nonterminal residuals average+147.41. Growing loss reflects large target/residual scale and especially terminal overprediction, not simply larger fares.

Standard max-target minus the diagnostic Double-DQN selector averages89.70 and peaks1,049.15 before discount/masking. Relative disagreement is LOW, but this is **not** a measurement of true max-operator bias. No Double-DQN training or change is proposed.

51,072 updates×64=3,268,608 sampled examples;32.686 per final capacity or18.426 per177,396 total inserted transitions. This latter ratio is a global exposure average, not equal reuse for every transition; FIFO/growth and sample-index history prevent exact individual reuse reconstruction. The same400 slots at final cadence would yield3,192 updates,16× fewer. Acceleration plausibly magnifies bootstrapped approximation error/replay overfitting, but no matched8-update control establishes causation or guarantees safety of the final cadence.

## Development oscillation and decision

Adjacent checkpoint action-distribution total variation is0.782,0.934,0.959,0.925,0.959. Dominant action indices change5→6→3→2→6→0. Oscillation is descriptively **HIGH**, despite improved final revenue. Exact revenue/assignment changes are in development_policy_stability.json. This is not convergence or a significance test.

Replay shape, range, finiteness, terminal placeholders, hash integrity and RNG metadata pass. No implementation bug is proven; state/horizon aliasing, unsupported next-state contexts and severe terminal overprediction remain unresolved. Do not resume final training yet. A separate methodology/diagnostic decision is needed; no clipping, normalization, gamma, optimizer, architecture or algorithm change is selected here.

## Evidence

The twelve JSON files in this folder contain the Bellman contract, transition limits, rewards, horizon/Q comparisons, online/target comparisons, bootstrap and TD diagnostics, replay checks, exposure, policy changes and verdict. Sample seed42 and size4,096 are fixed. All terminal rows were used for the one-step return check. The source is the completed review episode25 checkpoint and existing CSV/JSON artifacts only.
