# Final Non-Private Pricing-DQN Training Protocol

**FINAL_PRICING_DQN_PROTOCOL_FROZEN = YES**. **Full training has NOT been launched.** Next action: **LAUNCH_FINAL_NONPRIVATE_PRICING_DQN**, requiring a separate launch task.

## Evidence and project decisions

The final module-wise document, M14/M16/M17 (PDF pp15,20–21), supports OD pricing decisions, successfully assigned fare reward, replay minibatches and continued learning across episodes. The corrected implementation document describes repeated simulation episodes with 30-minute slots. The inspected source does not select 8 versus 12 hours; the latest user-provided meeting guidance and explicit fallback authorize **8 hours / 16 slots**, classified **PROJECT TRAINING PROTOCOL**. The **500-episode** budget is an initial evaluation checkpoint, not guaranteed convergence. **Eight optimizer updates per completed slot** is a **PROJECT TRAINING SCHEDULE**, not a literature constant.

## Frozen model and reward

Standard DQN: 13→64 ReLU→64 ReLU→7 Q-values; Adam 0.001, Huber, gamma 0.99, batch 64, replay capacity 100,000, warmup 1,000, target tau 0.005, seed 42. Actions:[.85,.90,.95,1.,1.05,1.10,1.15]. State:[J_hat,J_disp_previous,I,9routing probabilities,destination popularity]; no passenger epsilon or private driver input is added.

One transition is one observed origin/destination pair within a 30-minute slot. Its action is reused for the OD in that slot. Reward is the sum of successfully assigned dispatch fares at assignment time. Rejected and accepted-unmatched requests contribute zero. No repositioning,charging,utility or rejection cost is subtracted. Existing reward reconciliation remains active. Slot 16 is terminal, with an ignored current-state copy as next state; this avoids reading a March16next state at the latest training window boundary.

## Episode sequence and reset

`episode_protocol.json` persists all 500 starts and environment seeds. A seed 42 uniform integer draw over 0..704 selects a contiguous 16-slot window within March1–15, with replacement. This keeps every source period eligible without crossing into March16. Environmentseeds derive from 500 SeedSequence42 children, so repeated windows have distinct reproducible simulator streams. No March17–31data is accessed.

Each episode starts a **reproducible cold environment** at its historical timestamp; it is not a reconstruction of the exact historical fleet. The existing configured fleet initializer sets positions, initial status and EV energy with the episodeenvironment seed. Charging queues/occupancy/jobs reset. Historical pretraining fare priors and frozen F_hat0/H_hat0 initialize a fresh operational EWMA; forecast/weather are from the selected window. Passenger/request/charging RNG reset deterministically. Passengercommitments,missions,dispatchledger,J_disp_previous andrequest counter reset. Frozen routing is inference-only. The reset contract is documented explicitly rather than silently carrying fleet/charging state across unrelated windows.

Pricing online weights,target weights,Adam state,replay,replay RNG,action RNG,optimizer counter and epsilon persist. Fresh environment constructors are attached to that persistent learner. Replay uses existingFIFO replacement at100,000; it is never cleared between training episodes.

## Optimizer and exploration schedule

All slot transitions enter replay first. Below 1,000 transitions:zero updates. Otherwise:8 independent minibatches of 64, each with one Adam update, counter increment and tau=.005 target soft update. No per-request updates. Onlineparameters alone receive gradients; target values are computed outside the gradient tape.

Epsilon=1−.95×min(update_count/50,000,1), reaching 0.05 at 50,000 updates and remaining there. Training is epsilon-greedy; development is greedy with no replay insertion or optimizer update. Initial target copies online exactly.

500-episodes×16 slots=8,000 slots and 64,000 maximum optimizer opportunities. The first planned-window attempt crossed warmup in slot 2 (497 then 1,005 cumulative transitions); the completed alternate fixture had2 warmup slots. Projected updates for the planned sequence are **63,992**, assuming the remaining completed slots remain warm. This is an update-count projection, not a wall-clock estimate. Fully warm episodes produce 128 updates.

## Checkpoint and development protocol

Every 8 slots, the existing atomic payload checkpoint saves online/target,Adam,replay/counters/RNG and simulator/fleet/charging/operational state. New start-aware restore removes the old March1-single-pass assumption. Explicitresume handles mid-episode checkpoints and preserves the learner across episode boundaries. A cursor commits after episode/development reporting; coarse checkpoints and history remain available. Oldpricing checkpoints are never loaded.

Every 25 episodes, save training summaries and rolling 25 revenue/assignments, acceptance/fulfillment,actioncounts,mean/medianabsoluteQ,Qspread,epsilon,replay,updates andloss. Q diagnostics use the latest 512 replay states and must be interpreted with their changing state composition.

A fixed **March16 00:00–02:00,4-slot,seed 424242** development fixture is greedy, without replay insertion, optimizer steps or epsilon changes. It is a diagnostic comparator, not a repeated hyperparameter search. The fixture was defined here but not additionally executed, preserving the two-attempt validation limit.

At episode 500, assess training stability, fixed development performance,Q/action stability and numerical health. Numericalfailure meansNO; documented agreement of stable indicators supportsYES; changing or insufficient evidence meansINCONCLUSIVE and a separate continuation recommendation. No invented strict revenue threshold and no automatic extension. The runner conservatively records REVIEW_REQUIRED/INCONCLUSIVE pending that evidence review. Episode500 is the primary candidate; March17–31 never selects a model.

## Upstream immutability

Routing:`models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras`. SHA256:`db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a`. Verified before/after the fixtures; no routing learning/FedAvg. Passenger epsilon remains abs(Delta_D/Delta_P), sampled empirically with replacement; P_max=P_base×(1+Delta_D/epsilon); accept when P_dispatch≤P_max. Drivereligibility retains P_dispatch≥P_min. No upstream formula or model changed.

## Bounded fixture results

One 16-slot real simulator episode completed after an earlier attempt stopped after 8 slots at checkpoint-directory creation. The directory bug was fixed and a focused regression added; the failed attempt remains preserved. No third simulator episode was run. The completed episode ran in `models/pricing_dqn/final_multiepisode_protocol_fixture_seed42/`, separate from the reserved final namespace.

| Episode | Replay before/after | Transitions | Optimizer updates | Charging events |
|---|---|---:|---:|---:|
| 2 | 0/6073 | 6073 | 112 | 58 |

Mean transitions/slot:379.562500. Final epsilon:0.997872000. Reproducible reset signatures and passenger RNG, persistent replay,16-slot terminal boundaries,8-updatecadence, mid-episode reload, reward accounting,fleet/energy andimmutable routing checks passed. Zero charging events, if present, would not establish new chargingevent coverage. **14 focused tests passed**, covering model/actions,state/replay validation,Bellman/terminaltargets,Huber/finiteupdates,targettau,epsilon,replayFIFO,exactDQNoptimizerresume,windowbounds andno March16 training.

The only existing simulator interface edit adds opt-in greedy pricing selection; its default behavior remains unchanged. The new wrapper owns the eight-update schedule, leaving the old single-pass runner intact. Implementation:`src/simulation/multiepisode_pricing.py`; entrypoint:`scripts/run_multiepisode_pricing.py`.

## Reserved launch and provenance

Reserved:`models/pricing_dqn/final_nonprivate_multiepisode_seed42/`. It contains no trained final model. Future authorized command: `PYTHONPATH=. python -B scripts/run_multiepisode_pricing.py --launch`; add `--resume` only after a committed/partial run. The final_launch_config.json records this configuration. No full training process was started.

Previous720-slot pricing output remains **COMPLETED_PRICING_TRAINING_RUN / TRAINING_SCHEDULE_MISMATCH / PRE_CORRECTION_PROVENANCE / NOT_FINAL_NONPRIVATE_BASELINE**. Its718 updates and epsilon≈.986 do not constitute the intended schedule. It was not resumed or overwritten.

All required contract JSON files, exactepisode sequence, fixture CSV records and this README are in this folder. March17–31 untouched. Next action remains launch only, not executed.

**FINAL_PRICING_DQN_PROTOCOL_FREEZE_COMPLETE**
