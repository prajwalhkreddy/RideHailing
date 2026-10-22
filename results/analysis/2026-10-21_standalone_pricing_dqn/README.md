# Standalone pricing DQN

**STANDALONE_PRICING_DQN_READY = YES.** This is an independently tested implementation and synthetic fixture checkpoint, not a final experimental pricing model. No hierarchical simulator, CNN training, routing training, privacy or attack work was run.

## Frozen interface

`src/rl/pricing_dqn.py` accepts the existing 13D state in unchanged order:

0 J_hat; 1 previous-slot J_disp; 2 incoming I; 3–11 routing probabilities STAY/N/NE/E/SE/S/SW/W/NW; 12 destination popularity.

Inputs retain identity normalization: no clipping, scaling or fitting. Validation requires shape (13,), finite nonnegative values, nine nonnegative routing probabilities summing approximately to one, and popularity within [0,1]. Values must be representable by the float32 network. State copies prevent subsequent caller mutation of replay records. The upstream builder remains responsible for grid-specific routing masks, timestamps and causal provenance; a bare 13D vector cannot independently prove those properties.

The immutable action tuple maps indices 0–6 to **0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15**. `select_action` returns both index and factor, plus exploration diagnostics. Downstream offered fare remains factor × runtime P_base. The DQN accepts the frozen assignment-time slot reward without alteration. A test verifies successful fares $20+$25+$30 yield $75, excluding rejected and unmatched requests. It does not subtract driver or charging costs or change acceptance.

## Architecture and one configuration

Project implementation choice: **13 → 64 ReLU → 64 ReLU → 7 linear Q-values**. There is no Q-value softmax. Target weights initially exactly copy online weights.

- Gamma 0.99; Adam learning rate 0.001.
- Huber loss, delta 1; batch size 64.
- Replay capacity 100,000; minimum replay size 1,000.
- Epsilon 1.0 → 0.05 linearly over 50,000 completed optimizer updates; floor thereafter.
- Soft-target tau 0.005; seed 42.

All values are in `dqn_config.json`; no hyperparameter search occurred. Before replay warmup, `train_step()` returns None and does not advance the epsilon schedule. Multiple environment decisions without an optimizer update retain the same epsilon. `explore=False` selects greedy evaluation without changing the training schedule. Exploration is uniform over all seven valid pricing actions; greedy ties select the lowest index.

## Replay, target and training

`ReplayBuffer` stores copied (state, integer action_index, reward, next_state, boolean done) tuples. Capacity eviction is FIFO. Sampling uses its own seeded NumPy generator without replacement within a batch. Invalid dimensions, actions, booleans, nonfinite rewards/states and malformed probability slices fail closed. No pricing factor is substituted for an action index.

Standard DQN target:

- terminal: y = reward;
- otherwise: y = reward + gamma × max Q_target(next_state).

This is not Double DQN. Target predictions are evaluated outside the gradient tape. The selected online Q-value receives the Huber update; after Adam, each target weight becomes (1−tau)×old_target + tau×updated_online. Tests verify that exact relation and distinguish target-network next-Q values from online values. Diagnostics include loss, mean selected Q, mean target, epsilon and replay size.

`done` is supplied by the environment. No full-simulator episode horizon is chosen here. Terminal next states still satisfy the 13D contract even though they are not bootstrapped.

## Checkpoint and reproducibility

Fixture path: `models/pricing_dqn/standalone_13x64x64x7_fixture/`.

- `online.keras`: network plus Adam optimizer slots/iterations.
- `target.keras`: target network.
- `checkpoint.json`: config, schema/action mapping, training step/schedule position and independent action/replay RNG states.
- `replay.npz`: complete replay records in insertion order; no pickle.

Loading validates state/action dimensions, feature order, exact action mapping, architecture/activations, optimizer type, step consistency and replay records. Incompatible checkpoints fail explicitly. Save/load is for trusted local project checkpoints; cross-platform bitwise reproducibility is not claimed.

The deterministic run enabled TensorFlow deterministic operations. Tests and the saved fixture establish equal online/target/optimizer values after loading, equal next exploration action and exactly equal next sampled optimizer update in the current environment. Replay is persisted, so resume is replay-identical for this fixture.

## Synthetic fixture and validation

`run_fixture.py` creates seven explicit terminal examples with one valid hand-written state, actions 0–6 and synthetic rewards $1–$7. Repetition to 1,000 replay rows meets the unchanged production warmup setting; it does not imply 1,000 independent observations. It runs **100 updates**, without a simulator. Fixed seven-example Huber loss decreases from **3.50116517 to 0.15600096**. This verifies fitting mechanics only, not a pricing-performance claim.

The checkpoint is saved at update 100. One unsaved continuation on the original and restored agents proves exact resume. The script refuses implicit rerun when completed validation artifacts exist.

`bellman_fixture.csv` verifies reward 10, gamma .99 and max target next-Q 6: nonterminal target **15.94**, terminal target **10**. `synthetic_training_history.csv` records all 100 updates. `checkpoint_validation.json` records restoration results.

**23 focused tests passed, 0 failed**, plus the synthetic fitting/resume fixture passed. Command: `python -B -m unittest tests.test_standalone_pricing_dqn tests.test_pricing_dqn_contract -q`. Coverage includes shape/raw-Q output, initial target equality, exact factors, seeded exploration, greedy/tie behavior, epsilon endpoints/midpoint, replay validation/sampling/copying, Bellman targets, warmup, online updates, exact soft updates, checkpoint restoration/rejection and the $75 reward interface.

## Separation and next step

LinUCB code/results are unchanged. Callers explicitly choose the existing LinUCB class or `PricingDQN`; no default policy was replaced. The old LinUCB context is a different contract and must not be passed directly to this 13D module. No environment/policy-selection dispatcher is activated here.

Next: a short deterministic integration fixture linking J_hat + previous J_disp + incoming I + nine routing probabilities + popularity → state → DQN factor → runtime base fare → behavioural-E acceptance → assignment → reward → next state → replay. Validate that sequence before any short full hierarchical episode. This integration was not executed in this task.
