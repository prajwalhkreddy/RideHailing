# Final pricing contracts and 13D state

**DQN_STATE_READY = YES for the contract and deterministic integration interface.** No Q-network, DQN training, routing training, CNN training or long simulation was implemented. The existing legacy LinUCB loop is not activated or rewritten by this task; its configuration remains separate. The final pricing contract is selected explicitly by `config/config.yaml: pricing_dqn_contract.passenger_acceptance_model = behavioural_E_threshold`.

## Passenger acceptance and verified source

The selected project baseline is the existing positive behavioural-E threshold model:

P_disp = factor × P_base;
P_max = P_base + ((distance − D_base)/D_base) × P_base/E;
accept iff P_disp ≤ P_max, including equality.

Prices are USD; distance and D_base are miles; E is dimensionless and strictly positive. E, P_base and D_base must be finite/positive; distance finite/nonnegative; nonfinite P_max fails. Negative P_max is not clipped: it rejects a nonnegative offer. No zero-distance-denominator problem is introduced by this formula because distance deviation is in the numerator.

`src/pricing/customer_sensitivity.py` samples Normal(mean, population SD) conditioned on E>0; positive zero-variance means are deterministic. Its numerical sampler guard preserves strict positivity. `behavioural_model` verifies saved artifact hashes and requires the January training cutoff before use. Sources:

- `data/processed/customer_price_sensitivity_2026_01.parquet` and matching metadata.
- `data/processed/customer_price_sensitivity_fallback_2026_01.parquet` and matching metadata.

**Important provenance:** these are a separate legacy January calibration whose metadata explicitly defines absolute price-distance ratios. Their existing parameters are used as behavioural simulation calibration by project decision, not as causal willingness-to-pay. No new transformation is performed, and the signed Record-029 dataset is never read, absolutized, inverted or substituted. Its analysis and artifacts remain unchanged. The legacy function/column names containing “epsilon” do not make that distribution Record-029.

Runtime P_base/D_base are internally consistent means of TLC fare_amount/trip_distance for resolved WeatherCode × half-hour Period. Lookup order is exact → period → weather → global. The training interval is January 1 ≤ pickup < January 25, 18:30. Runtime offered fare uses this resolved USD base, not the Record-029 global mean. Raw empirical request.base_fare still exists for the separate Eq31 branch; it is not silently substituted into the selected behavioural branch. Eq31/logistic code remains optional provenance, never mixed into the final contract.

## Reward and dispatch history

Current-slot pricing reward is gross successfully assigned dispatch revenue: sum of accepted ASSIGNED request fares. Passenger rejection, accepted-but-unmatched and failed assignment contribute zero. No reposition, charging or utility costs are deducted. Assignment-time recognizes the pricing outcome when a vehicle is successfully allocated; it is not accounting for realized completed-trip cash receipts or later cancellations.

`completed_request_outcomes` adapts RequestStatus.ASSIGNED with accepted=true and a vehicle ID. Mini-slot request_time is converted using the frozen two-minute mini-slot. `DispatchLedger.complete_slot` checks a unique half-hour, duplicate request IDs and event times before recording counts/revenue. For decision t, `previous(t)` requires exactly t−30min's completed ledger entry. Missing history fails; an explicitly completed zero-event slot legitimately yields zero. J_disp is a count per previous slot, **not F_hat's EWMA rate**.

The four-request fixture contributes $20+$0+$0+$30 = **$50**.

## Incoming passenger arrivals

I(g,t) counts active passenger trips committed strictly before decision t whose known completion lies in **(t,t+30min]** and whose destination is g. Arrivals exactly at t are no longer incoming; arrivals at the slot end are included. Future assignments, unknown destinations/durations and duplicate active vehicles are rejected. Reposition travel is excluded.

`passenger_commitment` adapts an accepted assigned passenger request with known positive duration. Caller supplies still-active passenger trips and their assignment-slot timestamps. This explicit commitment interface avoids `build_raw_pricing_supply`'s legacy generic BUSY classification, which cannot distinguish passenger travel from repositioning. No generic BUSY estimate is silently reused.

## State, sources and normalization

`src/pricing/dqn_contract.py: PricingStateBuilder.build(origin, destination, timestamp)` returns:

[J_hat, J_disp_previous, I_incoming, p_STAY, p_N, p_NE, p_E, p_SE, p_S, p_SW, p_W, p_NW, destination_popularity].

The count/rate meanings and all 13 indices are in `pricing_state_spec.json`. Output is finite float64. Integer grid IDs must be 0–141; timestamps are timezone-naive project-local half-hour boundaries. Required missing data are never filled silently.

- J_hat comes from the frozen epoch-200 DQN-ready artifact.
- J_disp is the previous completed slot ledger.
- I uses explicit known passenger commitments.
- p is the mean of available, already-masked nine-action policy probability vectors. Empty populations require an explicit caller policy; this interface fails rather than inventing a uniform distribution. Invalid probabilities are zero; valid ones sum to one.
- Destination popularity uses the regenerated `destination_popularity.parquet`: six previous-slot drop-off averages mapped through fixed global reference quintiles to 0/.25/.5/.75/1. It is an ordinal score, not a normalized destination probability. Thresholds are 0, 1/3, 11/6 and 6, fitted before January 25, 18:30. The adapter rejects earlier times and requires the exact destination/time row. No popularity refit occurs.

Snapshots record target timestamp, available_at and observed_through; future/misaligned inputs fail. The caller must truthfully supply availability and completed-slot boundaries: timestamps cannot independently prove source provenance. The saved forecast's target-slot availability follows the already-frozen CNN interface; live forecast-weather provisioning is not newly established by this task.

**Normalization is identity**, explicitly saved in the state specification: raw nonnegative count features, unchanged probabilities and unchanged bounded ordinal popularity. The old LinUCB scaler's log1p/P99 clipping was inspected but not reused: it describes different contexts and lacks a justified J_disp calibration. No train/validation/test fitting or clipping is introduced. Later Q-network numerical conditioning must respect this frozen contract or explicitly revise it.

## Actions and routing checkpoint status

Seven project experimental-design actions: **0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15**. P_disp=factor×resolved P_base. The illustrative 0.8–2.0 roadmap set is not used.

The saved 169→64→32→9 checkpoint is **STRUCTURALLY_VALID / INTEGRATION_BASELINE / NOT_FINAL_EXPERIMENTAL_POLICY**. Its synthetic validation accuracy 29.23% is below majority accuracy 33.63%. State predictions are labeled **PROVISIONAL_ROUTING_BASELINE**. It remains available for fixtures; final simulator-generated routing experiences require subsequent retraining/evaluation. Only its documentation was updated.

## Validation and hand fixtures

`state_fixture.csv` records exact hand inputs and shows that changing destination changes only the popularity component. `reward_fixture.csv` records the four assignment outcomes. Tests cover threshold equality and distance effects, invalid E, exact action set, fare units, reward, lag, arrival boundaries, future snapshots, missing states, invalid grid/time/probabilities, mean routing response and verified legacy source/forecast/popularity lookup.

A separate tiny integration loaded the existing routing checkpoint, built a real 169-feature operational state and boundary mask, and combined its nine probabilities with saved epoch-200 forecasts and popularity into a valid 13D vector. Explicit completed-empty history and zero passenger commitments were fixture inputs, not defaults. No training occurred.

The contracts are ready for the next integration stage. This does not certify a completed live simulator, causal passenger behavior, forecast-weather availability, or a final experimental routing model.

Validation result: **16 tests passed, 0 failed** (`tests.test_pricing_dqn_contract` and `tests.test_config`), plus the checkpoint-backed integration check passed.
