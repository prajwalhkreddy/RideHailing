# Hierarchical routing-to-pricing coupling validation

Status: **bounded inference coupling verified**. No production source, methodology, historical results, or checkpoints were modified. No training or full simulation was initiated. This validates an interface, not policy effectiveness or full master compliance.

## Architecture established by the master

`notebooks/plan/masterdocument/MASTER DOCUMENT1.docx` §5.1 defines the OD pricing state as forecast origin demand, estimated prior dispatches, incoming vehicles, origin mean routing response, and destination popularity. §5.3 specifies epsilon-greedy pricing. §7.2 equation (11) assigns physical repositioning to the driver's private utility maximization; §7.3 retains EV charging decisions. §8 equations (19)–(21) train local classifiers on private decisions, average client parameters, and supply global routing probabilities for the next slot. The global classifier estimates responses; it need not replace private utility decisions. This implementation is NONPRIVATE, with no differential-privacy claim.

## Boundary trace

1. `final_production.py:route_idle` calls `research_mixed.decision`, records the chosen masked action and 169D public routing state in driver-local memory, and executes the private decision. Preferences are not uploaded through the federation interface.
2. `online_provenance.py` checks experience time/slot eligibility. `research_hierarchy.py:finish_slot` resets participating local model weights from the current global weights, retains local Adam state, and calls `learning.py:train_for_slot`.
3. Local masked cross-entropy updates upload parameters. The equal-client contract sets each positive participant's aggregation weight to one before `federated.py:aggregate_policy_updates`. Global version advances on an actual update; availability is the completed slot boundary.
4. `od_pricing_runtime.py` chooses current-slot prices before routing/federation. At close it records private actions, completes operational statistics, advances the UTC timestamp, and calls `finish_slot`. Only then are next states constructed.
5. `utc_od_inputs.py:state_sources` constructs origin-indexed routing vectors/masks. `research_feedback.probabilities` calls the current global model for a learned hierarchy, not utility frequencies. Invalid actions are masked and probabilities normalized.
6. `UTCStateBuilder` validates snapshot target/availability, then `od_contract.od_states` sets the final dispatch feature to previous completed EWMA dispatch/minute × 30 minutes. The resulting next state is stored in replay and becomes the subsequent decision state.
7. `ODPricingDQN.select_actions` batches those exact 13D states into the 13→64→64→7 network. No projection or replacement of its nine routing dimensions occurs.

The four completed real-data rounds remain prior evidence; the fourth boundary's feedback was constructed but no fifth slot was executed. No claim is made about a fifth-slot action.

## State and controlled inference evidence

`state_and_q_evidence.csv` contains two verified January-feasible pairs, **(0,0)** and **(1,0)**, using saved learned/control routing probabilities after the first real-data slot. Forecast, EWMA and popularity values are deliberately small synthetic fixture values, not claimed real observations. The feature order is:

`[forecast(origin), EWMA_dispatch_rate(origin)*30, incoming(origin), p_STAY, p_N, p_NE, p_E, p_SE, p_S, p_SW, p_W, p_NW, popularity(destination)]`.

Non-routing features are identical between arms. A fresh actual configured seed-42 DQN, with no weight edits or optimizer calls, produces maximum absolute Q differences **0.00015030056238174438** and **0.0013502240180969238**. This establishes numerical dependence; a different greedy action is neither required nor asserted. The CSV supplies every feature and every Q output.

The live `state_sources`/feedback branch is separately tested with controlled input vectors and recorded probabilities. A utility replacement raises immediately in that test. Snapshot timing rejects both stale and future targets. Invalid probability values are rejected. Existing provenance fixtures check masks, equal-client aggregation, next-boundary availability, global versions, checkpoint identity and deterministic restoration.

## Why physical actions and revenue matched

The earlier real-data run recorded 19,342 genuine local updates and four federation rounds. Its learned/control mean absolute probability differences grew from 0.00787809 to 0.04871474. Independent repeat and checkpoint continuation were exact. Private actions and realized outcomes matched.

This is expected for this bounded configuration: private utility, rather than the response estimator, chooses driver movements. Pricing optimizer updates were zero; the implemented exploration schedule depends on optimizer steps, so epsilon remained 1.0. Identical random streams therefore selected identical exploratory prices despite different Q inputs. Identical prices and physical states explain equal assignment/revenue outcomes. This is not evidence that routing feedback is disconnected, nor proof that trained pricing will improve performance.

## Tests, preservation and limitations

**15 tests passed in 16.346 seconds**: five new coupling tests, four online provenance tests, six arrival integration tests. Command: `python -B -m unittest tests.test_hierarchical_coupling tests.test_online_routing_provenance tests.test_online_routing_arrival_integration -q`.

The existing federation fixtures use explicitly synthetic parameter payloads to test aggregation and resume; they perform no gradient training and are separate from the unchanged-weight inference test. The existing small empty-request runtime fixture checks checkpoint/next-state integration, not a full real-data simulation. Real gradient evidence is reused from the preserved prior experiment. Logs, source hashes and evidence provenance are recorded locally.

No coupling defect was identified within this scope. The hierarchy is structurally ready for a separately authorized, frozen, bounded joint-learning protocol. Full learned-pricing efficacy, privacy, independent model-selection provenance and existing weather-availability assumptions remain outside this validation. Recommended next task: freeze the bounded joint routing/pricing experiment protocol, including exploration/optimizer cadence and matched controls, before running training.
