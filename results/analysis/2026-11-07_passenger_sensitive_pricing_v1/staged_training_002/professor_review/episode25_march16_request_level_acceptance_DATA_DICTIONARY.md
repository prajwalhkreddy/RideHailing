# Episode25 March16 request-level acceptance data dictionary

Source: deterministic read-only replay of the authoritative Episode25 checkpoint, March16 00:00–02:00, seed424242 and greedy policy. Only IDs/actions/counts were originally persisted, so complete records required replay. All persisted request actions and order match exactly; aggregate revenue/outcomes reconcile. No training or learner replay writes.

P_raw_c is the raw equation output; P_accept_c=max(platform minimum,P_raw_c); P_offer is the selected fare. Passenger acceptance does not imply driver matching. All 52 unmatched requests are passenger-accepted.

Runtime formula: P_raw_c=P_base+(P_base/epsilon_c)*((L_gg_prime_km-L_base_km)/L_base_km). Exact runtime comparisons are used for feasibility/boundaries, without an invented tolerance.

`transition_created` refers to learner replay writes (false); `transition_audited` refers to the in-memory next-request linker used for evaluation (true). Request sequence is an export ordinal, not an invented source identifier. Raw Q values are unmasked; feasibility columns must be read alongside them. Blank optional assignment identifiers mean no assignment.

| Column | Meaning / formula | Units | Source | Provenance |
| --- | --- | --- | --- | --- |
| request_sequence | 1-based export order of actual chronological requests; not a source ID | none | enumeration of request_audit order | DETERMINISTIC_DERIVATION |
| request_id | Runtime request identifier | identifier | replayed request_audit.Request_ID | DETERMINISTIC_REPLAY |
| request_timestamp | Runtime decision timestamp | local datetime | replayed request_audit.timestamp | DETERMINISTIC_REPLAY |
| slot_index | One-based main slot | index | replayed request_audit.slot | DETERMINISTIC_REPLAY |
| origin_grid_id | Request origin grid | identifier | replayed request_audit.Origin_Grid_ID | DETERMINISTIC_REPLAY |
| destination_grid_id | Request destination grid | identifier | replayed request_audit.Destination_Grid_ID | DETERMINISTIC_REPLAY |
| L_gg_prime_km | Actual request OD distance | km | replayed request_audit.L_gg_km | DETERMINISTIC_REPLAY |
| epsilon_c | Sampled positive passenger sensitivity magnitude | dimensionless | replayed request_audit.epsilon_c | DETERMINISTIC_REPLAY |
| P_base | Frozen global price reference | USD | replayed request_audit.P_base_USD | DETERMINISTIC_REPLAY |
| L_base_km | Frozen global distance reference | km | replayed request_audit.L_base_km | DETERMINISTIC_REPLAY |
| P_raw_c | Raw equation output, before platform minimum protection | USD | replayed request_audit.P_raw_c | DETERMINISTIC_REPLAY |
| P_platform_min | 0.85 * P_base | USD | replayed request_audit.P_platform_min | DETERMINISTIC_REPLAY |
| P_platform_max | 1.15 * P_base | USD | replayed request_audit.P_platform_max | DETERMINISTIC_REPLAY |
| P_accept_c | max(P_platform_min, P_raw_c) | USD | replayed request_audit.P_accept_c | DETERMINISTIC_REPLAY |
| selected_action_index | Zero-based chosen action | index | replayed request_audit.selected_action_index | DETERMINISTIC_REPLAY |
| selected_price_factor | Chosen pricing multiplier | dimensionless | replayed request_audit.selected_factor | DETERMINISTIC_REPLAY |
| P_offer | selected_price_factor * P_base | USD | replayed request_audit.P_offer_USD | DETERMINISTIC_REPLAY |
| feasible_action_count | Number of feasible factors | count | replayed request_audit.feasible_action_count | DETERMINISTIC_REPLAY |
| assigned | Successful dispatch assignment | boolean | replayed request_audit.assignment_status | DETERMINISTIC_REPLAY |
| reward | P_offer if assigned, otherwise zero | USD | replayed request_audit.reward | DETERMINISTIC_REPLAY |
| slot_start | Start from actual slot index | datetime | fixture start + (slot_index-1)*30 minutes | DETERMINISTIC_DERIVATION |
| slot_end | Exclusive slot end | datetime | slot_start + 30 minutes | DETERMINISTIC_DERIVATION |
| epsilon_support_lower | Inclusive frozen positive-support lower bound | dimensionless | restricted_calibration_support.json | DETERMINISTIC_DERIVATION |
| epsilon_support_upper | Inclusive frozen positive-support upper bound | dimensionless | restricted_calibration_support.json | DETERMINISTIC_DERIVATION |
| epsilon_sampling_method | Empirical row resampling with replacement | category | restricted_calibration_support.json | DETERMINISTIC_DERIVATION |
| feasible_0_85 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_085 | DETERMINISTIC_REPLAY |
| feasible_0_90 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_090 | DETERMINISTIC_REPLAY |
| feasible_0_95 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_095 | DETERMINISTIC_REPLAY |
| feasible_1_00 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_100 | DETERMINISTIC_REPLAY |
| feasible_1_05 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_105 | DETERMINISTIC_REPLAY |
| feasible_1_10 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_110 | DETERMINISTIC_REPLAY |
| feasible_1_15 | Candidate fare <= P_accept_c | boolean | replayed request_audit.mask_115 | DETERMINISTIC_REPLAY |
| forced_request | Exactly one feasible action | boolean | feasible_action_count == 1 | DETERMINISTIC_DERIVATION |
| choice_request | At least two feasible actions | boolean | feasible_action_count >= 2 | DETERMINISTIC_DERIVATION |
| highest_feasible_factor | Largest feasible multiplier | none | maximum action with true mask | DETERMINISTIC_DERIVATION |
| lowest_feasible_factor | Smallest feasible multiplier | none | minimum action with true mask | DETERMINISTIC_DERIVATION |
| greedy_selected | Greedy selection; exploration disabled | boolean | replay explore_pricing=False | DETERMINISTIC_DERIVATION |
| offer_generated | An offer was generated | boolean | P_offer_USD not null | DETERMINISTIC_DERIVATION |
| passenger_feasible | Offer meets passenger effective threshold | boolean | P_offer <= P_accept_c, exact runtime comparison | DETERMINISTIC_DERIVATION |
| passenger_accepted | Runtime passenger acceptance, distinct from matching | boolean | request_audit.passenger_status | DETERMINISTIC_DERIVATION |
| passenger_rejected | Offered but not accepted | boolean | offer_generated AND NOT passenger_accepted | DETERMINISTIC_DERIVATION |
| passenger_rejection_reason | No passenger rejections in this fixture | none | all passenger_status == ACCEPTED verified | DETERMINISTIC_DERIVATION |
| no_feasible_action | Empty feasible mask | boolean | feasible_action_count == 0 | DETERMINISTIC_DERIVATION |
| accepted_unmatched | Passenger accepted but dispatch did not assign | boolean | passenger_accepted AND NOT assigned | DETERMINISTIC_DERIVATION |
| no_price_eligible_driver | Runtime no-price-eligible-driver outcome | boolean | request_audit.pricing_outcome; not passenger rejection | DETERMINISTIC_DERIVATION |
| other_unmatched | Other accepted-unmatched outcome | boolean | accepted_unmatched AND NOT no_price_eligible_driver | DETERMINISTIC_DERIVATION |
| unmatched_reason | Dispatch outcome reason | none | runtime pricing_outcome | DETERMINISTIC_DERIVATION |
| assigned_vehicle_id | assigned vehicle id | identifier | RequestState.assigned_vehicle_id | DETERMINISTIC_REPLAY |
| driver_origin_grid_before_assignment | driver origin grid before assignment | identifier | RequestState.driver_origin_grid_before_assignment | DETERMINISTIC_REPLAY |
| source_trip_id | source trip id | identifier | RequestState.source_trip_id | DETERMINISTIC_REPLAY |
| selected_driver_price_eligible | Runtime assigned dispatch satisfied driver price eligibility; null without assignment | boolean | request_audit.driver_price_eligible for assigned requests | DETERMINISTIC_DERIVATION |
| transition_created | No learner replay transition written during read-only development | boolean | EvaluationView.store is a no-op | DETERMINISTIC_DERIVATION |
| transition_audited | Request transition tracked in ephemeral linker audit, not learner replay | boolean | request_audit.transition_created | DETERMINISTIC_DERIVATION |
| state_J_hat | Exact DQN input component 0 | model-state units | request_audit.state_13d[0] | DETERMINISTIC_REPLAY |
| state_J_disp_prev | Exact DQN input component 1 | model-state units | request_audit.state_13d[1] | DETERMINISTIC_REPLAY |
| state_I | Exact DQN input component 2 | model-state units | request_audit.state_13d[2] | DETERMINISTIC_REPLAY |
| state_prob_STAY | Exact DQN input component 3 | model-state units | request_audit.state_13d[3] | DETERMINISTIC_REPLAY |
| state_prob_N | Exact DQN input component 4 | model-state units | request_audit.state_13d[4] | DETERMINISTIC_REPLAY |
| state_prob_NE | Exact DQN input component 5 | model-state units | request_audit.state_13d[5] | DETERMINISTIC_REPLAY |
| state_prob_E | Exact DQN input component 6 | model-state units | request_audit.state_13d[6] | DETERMINISTIC_REPLAY |
| state_prob_SE | Exact DQN input component 7 | model-state units | request_audit.state_13d[7] | DETERMINISTIC_REPLAY |
| state_prob_S | Exact DQN input component 8 | model-state units | request_audit.state_13d[8] | DETERMINISTIC_REPLAY |
| state_prob_SW | Exact DQN input component 9 | model-state units | request_audit.state_13d[9] | DETERMINISTIC_REPLAY |
| state_prob_W | Exact DQN input component 10 | model-state units | request_audit.state_13d[10] | DETERMINISTIC_REPLAY |
| state_prob_NW | Exact DQN input component 11 | model-state units | request_audit.state_13d[11] | DETERMINISTIC_REPLAY |
| state_destination_popularity | Exact DQN input component 12 | model-state units | request_audit.state_13d[12] | DETERMINISTIC_REPLAY |
| Q_0_85 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[0] | DETERMINISTIC_REPLAY |
| Q_0_90 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[1] | DETERMINISTIC_REPLAY |
| Q_0_95 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[2] | DETERMINISTIC_REPLAY |
| Q_1_00 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[3] | DETERMINISTIC_REPLAY |
| Q_1_05 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[4] | DETERMINISTIC_REPLAY |
| Q_1_10 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[5] | DETERMINISTIC_REPLAY |
| Q_1_15 | Raw unmasked online-network Q for this action | discounted USD | online(state, training=False)[6] | DETERMINISTIC_REPLAY |
| selected_Q | Raw Q of chosen feasible action | discounted USD | Q[selected_action_index] | DETERMINISTIC_DERIVATION |
| request_outcome | Mutually exclusive final passenger/dispatch outcome | none | verified runtime assignment/pricing_outcome | DETERMINISTIC_DERIVATION |
| passenger_acceptance_margin_usd | Effective threshold minus offer | USD | P_accept_c - P_offer | DETERMINISTIC_DERIVATION |
| passenger_acceptance_margin_pct_of_P_base | Margin as percent of base | percent | 100 * margin / P_base | DETERMINISTIC_DERIVATION |
| at_acceptance_boundary | Exact equality; runtime has no feasibility tolerance | boolean | P_offer == P_accept_c | DETERMINISTIC_DERIVATION |
| raw_preference_category | Exclusive raw-preference category; ordered tests <=0, <minimum, <=maximum, otherwise above | none | P_raw_c and platform boundaries | DETERMINISTIC_DERIVATION |

## Unavailable requested fields

- **origin_zone_id / destination_zone_id**: Runtime request record exposes grid IDs, not distinct zone identifiers.
- **empirical epsilon source-row/index**: Provider returns sampled value, not sampled index.
- **assigned_driver_id**: Runtime exposes assigned_vehicle_id; no independent driver identity is inferred.
- **price_eligible_driver_count**: Legacy dispatch does not persist an exhaustive price-eligible count.
- **driver_price_preference**: Not stored in request audit; omitted rather than assuming vehicle ID is a profile key.
- **vehicle_destination_grid**: Not separately captured at assignment; request destination retained.
