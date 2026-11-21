# Two-episode passenger acceptance data dictionary

One row per eligible request in the March 1, 2026 training run `2026-11-20_multi_episode_orchestration`. Episodes cover 00:00–08:00 and 08:00–16:00 America/New_York (05:00–21:00 UTC). All 68,845 rows were recovered directly from checkpoint audit ledgers; no simulation, RNG replay or model inference was performed.

Source checkpoints: `milestone_episode01_slot16/runtime.json` and `latest_episode02_slot16/runtime.json` under `models/pricing_dqn/2026-11-20_multi_episode_orchestration_seed42/`. Runtime-file hashes match their immutable manifests. Exact binary floating-point audit values are decoded from hexadecimal and exported as round-trippable decimal representations. Source hashes are in [validation](../passenger_evidence_validation.json).

`NA` denotes unavailable/not applicable. An accepted request has no passenger rejection reason. Accepted-but-unmatched means no successful assignment, not passenger rejection. Request arrival is the recorded pickup-time proxy, not the time a real passenger first requested a vehicle. The actual acceptance distance is recorded `L`, sourced from TLC miles × 1.609344 by historical replay; no OD-matrix distance was substituted. The miles column is algebraically reconstructed, not reread from source data.

| Column | Unit / meaning | Provenance |
|---|---|---|
| `experiment_id` | Authoritative run directory name | DERIVED / EXACT RECONSTRUCTION |
| `episode_id` | Checkpoint role (1 milestone, 2 latest) | DERIVED / EXACT RECONSTRUCTION |
| `slot_start_utc` | Recorded slot parsed to UTC | DERIVED / EXACT RECONSTRUCTION |
| `slot_start_ny` | Recorded slot converted to America/New_York | DERIVED / EXACT RECONSTRUCTION |
| `slot_index` | One-based dense chronological rank within episode | DERIVED / EXACT RECONSTRUCTION |
| `request_id` | request_id; globally unique source identity | RECORDED |
| `request_arrival_utc` | Recorded source_pickup parsed to UTC | DERIVED / EXACT RECONSTRUCTION |
| `origin_grid` | origin_grid; zero-based grid ID | RECORDED |
| `destination_grid` | destination_grid; zero-based grid ID | RECORDED |
| `trip_distance_km` | L; actual acceptance distance in km | RECORDED |
| `weather_code` | weather_code; unchanged project code | RECORDED |
| `time_group` | T_group; T1–T4 | RECORDED |
| `sensitivity_group` | sensitivity_condition; selected empirical pool | RECORDED |
| `sampled_elasticity` | epsilon; positive dimensionless recorded draw | RECORDED |
| `p_base_usd` | P_base; USD | RECORDED |
| `l_base_km` | L_base; km | RECORDED |
| `selected_pricing_factor` | factor; dimensionless | RECORDED |
| `offered_price_usd` | P_offer; USD | RECORDED |
| `maximum_acceptable_price_usd` | P_max; raw ceiling USD, no minimum clamp | RECORDED |
| `accepted` | accepted; boolean | RECORDED |
| `fallback_od` | is_fallback; boolean | RECORDED |
| `successful_dispatch_reward_usd` | reward_contribution; USD at assignment, zero otherwise | RECORDED |
| `rejected` | Boolean complement of accepted | DERIVED / EXACT RECONSTRUCTION |
| `assigned` | dispatch_outcome equals ACCEPTED_AND_ASSIGNED | DERIVED / EXACT RECONSTRUCTION |
| `accepted_unmatched` | accepted AND NOT assigned | DERIVED / EXACT RECONSTRUCTION |
| `rejection_reason` | Recorded comparison reason standardized; NA for accepted | DERIVED / EXACT RECONSTRUCTION |
| `source_trip_distance_km` | Same recorded TLC-derived L as acceptance distance | DERIVED / EXACT RECONSTRUCTION |
| `source_trip_distance_miles_reconstructed` | L / 1.609344; reconstructed miles | DERIVED / EXACT RECONSTRUCTION |
| `dispatch_outcome` | dispatch_outcome; recorded status | RECORDED |
| `source_trip_id` | source_trip_id; source identity | RECORDED |
| `value_provenance` | Static provenance description | DERIVED / EXACT RECONSTRUCTION |

## Formula and reconciliation

`P_max = P_base + (P_base / epsilon) * ((L - L_base) / L_base)`. References are 22.354198442390455 USD and 4.616983790655043 km. Acceptance is `P_offer <= P_max`; successful dispatch reward equals the offer only for assigned requests. All 68,845 formula comparisons had maximum absolute difference zero before CSV serialization. Each of 32 ordered request-ID lists matches the saved SHA256 order hash.

Seven supported-OD factors correspond to uniformly spaced fares 6.60–94.70 USD. Factor 1.0 is the separate valid-unseen-OD fallback, not an eighth DQN action. Empirical draws use January–February request-count-weighted conditioning; weather/time labels are recorded, not newly assigned.

## Slot summary and analyses

The slot summary joins recorded metrics to demand reconciliation by episode and slot. Rejected and unmatched counts are derived by subtraction. `acceptance_rate` divides by eligible requests; `dispatch_success_rate` divides assigned by accepted. Pricing optimizer updates are the number of saved losses in that slot, not the cumulative update counter. Exploration is the pre-slot epsilon. Means are computed from the complete passenger ledger, including fallback requests. All fields are available.

Distance bins are left-closed [0,2), [2,5), [5,10), [10,20), [20,infinity) km. Fare bands are reporting-only [0,10), [10,25), [25,50), [50,75), [75,100), [100,infinity) USD. Elasticity bands are reporting-only [0,1.5), [1.5,2), [2,2.5), [2.5,3), [3,infinity). These do not alter sampling support. Empty strata are omitted; every table reconciles to 68,845. Rejection-margin distributions include all requests: positive means rejected, zero/negative means accepted.

The analysis is descriptive training evidence. Pricing actions are shared within OD-slot contexts, not randomized independent passenger treatments. Assignment also depends on availability and private driver constraints. A lower fare or higher acceptance rate does not imply higher revenue or causal policy superiority.

The distribution-statistics CSV uses the sample standard deviation (`std`, divisor N−1); means and quantiles include every eligible request. Negative raw ceilings are retained as recorded and are not clipped.
