# Final Behavioral Routing Training and Probability Adequacy

**FINAL_BEHAVIORAL_ROUTING_MODEL_READY = YES**  
**ROUTING_READY_FOR_PRICING = NO**  
**ROUTING_PROBABILITIES_INFORMATIVE = NO**  
**ROUTING_EFFECTIVENESS_CONCERN = YES**

Structural completion and predictive adequacy are separate. Models are preserved regardless of whether pricing readiness passes. No pricing training is authorized by this report.

## Complete authoritative dataset

Only `data/processed/routing_experiences_mar01_mar15_2026_final_behavioral/` was used. All720slots, March1 00:00–March15 23:30, contain **3,303,289** experiences. Completion boundary March16 00:00 is a checkpoint timestamp, not a training experience. Source partitions were streamed once into validated memory-mapped arrays; all partition hashes and the checkpoint hash were checked and recorded.

Every state is169D and finite; every mask is9D; labels are integers0–8 and mask-valid. IDs are contiguous and unique; driver IDs are0–4999; current grids0–141. Invalid-action placeholder triples are zero. The checkpoint has720reports, correct experience count,5000unique valid fleet members, finite/nonnegative energy, no pricing replay/optimization or federated updates during generation. Upstream behavioral fingerprints match generation evidence. Requests1,705,916 and assignments262,478 reconcile. No legacy155D or5-action schema entered training.

## Action and decision-type distribution

| action | name | total | percentage | train | validation |
| --- | --- | --- | --- | --- | --- |
| 0 | STAY | 3145346 | 95.21861393296196 | 2530648 | 614698 |
| 1 | N | 25165 | 0.7618164804835423 | 21942 | 3223 |
| 2 | NE | 10298 | 0.3117498953315922 | 6616 | 3682 |
| 3 | E | 21359 | 0.6465979815874421 | 18749 | 2610 |
| 4 | SE | 8725 | 0.2641306891404294 | 7306 | 1419 |
| 5 | S | 35762 | 1.0826179604630417 | 26433 | 9329 |
| 6 | SW | 16404 | 0.4965959684423615 | 13024 | 3380 |
| 7 | W | 25213 | 0.7632695776845441 | 20825 | 4388 |
| 8 | NW | 15017 | 0.4546075139050806 | 11089 | 3928 |

Majority is STAY, **95.218614%** overall. Zero-support actions: []. Positive support below1%: [1, 2, 3, 4, 6, 7, 8]; this descriptive threshold matches the existing material-support reporting convention and does not alter training. No balancing, smoothing, weighting by inverse class frequency or loss search was performed.

Decision types: REPOSITION **3,284,260** from 5000 unique participants; EV_CHARGING_NEXT_HOP **19,029** from 2779 participants. Previous provenance counts: {'REPOSITION': 3234802, 'EV_CHARGING_NEXT_HOP': 23038}; different upstream contracts and populations prevent a direct causal comparison.

All5000profiles contributed; zero-experience participants0. Experience-count min/P10/median/mean/P90/max: 180 / 521.0 / 703.0 / 660.6578 / 720.0 / 720.

## Frozen chronology and configuration

TRAIN:576slots, March1–12, **2,656,632** experiences. VALIDATION:144slots, March13–15, **646,657** experiences. No random split and no March16+ training/evaluation rows. The action table shows both split distributions.

One existing configuration:169→64→32→9 logits, mask invalid actions, Adam0.001, batch32, seed42, central1epoch; plain FedAvg5rounds,1local epoch per round, fresh local Adam per client, chronological examples, sample-weighted aggregation. The exact RoutingLearningParameters values were asserted before optimization. No architecture/learning-rate/loss search or balancing occurred. Initializations and central/local methods reuse the existing tested trainer. Progress checkpoints and completed-client updates prevent unnecessary repeated optimization after interruption.

## Central model

Accuracy **95.07760683%**, CE **0.269109640**. Training-side majority action0 achieves **95.05781272%** on validation. No validation labels selected that baseline action.

True action counts: [614698, 3223, 3682, 2610, 1419, 9329, 3380, 4388, 3928]. Predicted counts: [644787, 0, 8, 0, 0, 0, 1451, 411, 0]. Valid-action prediction rate1.0; invalid violations0. STAY true/predicted shares: 95.057813%/99.710820%. Largest predicted class share99.710820%. Meaningfully supported (>=1%) actions never predicted: [5].

Catastrophic collapse under the existing rule (prediction>90% while corresponding true share<90%): **False**. This rule does not erase overconcentration or missed-supported-action concerns. Overall concern:True.

## Plain FedAvg

| round | active_participants | training_examples | training_loss | accuracy | cross_entropy |
| --- | --- | --- | --- | --- | --- |
| 1 | 5000 | 2656632 | 1.143297269286122 | 0.8870003726859834 | 0.7076931962022994 |
| 2 | 5000 | 2656632 | 0.4133761694902415 | 0.8870050119305907 | 0.6309926720745452 |
| 3 | 5000 | 2656632 | 0.3658042904381002 | 0.8870297545684961 | 0.5533118732530525 |
| 4 | 5000 | 2656632 | 0.3365534869880791 | 0.8871070753119505 | 0.4970384972179136 |
| 5 | 5000 | 2656632 | 0.3170261274137159 | 0.8871070753119505 | 0.4417462887343008 |

All5000clients active each round, with exactly2,656,632 training examples represented. Aggregation weights are sample_count/total_count and all resulting tensors were independently checked against the weighted sum. Zero-sample clients are excluded by the tested mechanism; observed excluded count:0. No DP, secure aggregation or robust aggregation was used. Every round checkpoint reload reproduced logits exactly on a held-out slice.

Final accuracy **88.71070753%**, CE **0.441746289**. True counts:[614698, 3223, 3682, 2610, 1419, 9329, 3380, 4388, 3928]; predicted counts:[605411, 0, 0, 0, 0, 0, 0, 41246, 0]. STAY true/predicted:95.057813%/93.621657%; largest predicted share:93.621657%. Meaningfully supported actions never predicted:[5]; all zero-prediction actions:[1, 2, 3, 4, 5, 6, 8]. Invalid-action violations:0; catastrophic-collapse rule:False.

## Probability adequacy gate

| Method | Cross-entropy | Multiclass Brier |
|---|---:|---:|
| Final FedAvg | 0.441746289 | 0.178063054 |
| Masked training-label empirical prior | 0.293259219 | 0.095934945 |

Brier is mean sum over all9squared class-probability errors, not divided by9. Prior frequencies use March1–12 labels only; invalid actions are zeroed and remaining probability renormalized per validation mask. All training classes have support; no prior smoothing or probability clipping was used. Both methods use identical March13–15 targets/masks.

Mean final predicted vector:[0.9198438756403997, 0.005243376494152067, 0.0021306645371063724, 0.003765781249169107, 0.0038527816961941293, 0.008489343136391679, 0.0030124703760842355, 0.053168986576403024, 0.000492720294103519]. True validation distribution:[0.9505781271988086, 0.004984095123071427, 0.005693899547982934, 0.00403614280832033, 0.002194362699236226, 0.014426504313724277, 0.005226882257518282, 0.006785668445559238, 0.0060743176057786435]. Ten-bin top-label calibration and ECE are stored for both methods; FedAvg ECE:0.076005822; prior ECE:0.006220436. Calibration is descriptive, not a fitted recalibration step.

**ROUTING_PROBABILITIES_INFORMATIVE = NO**. The gate compares both held-out CE and Brier and uses a descriptive paired144-slot loss-difference standard-error check for numerical/uncertainty separation. That check assumes independent slots; it is not a claim of fully dependence-adjusted statistical significance. Structural correctness or top-1 accuracy alone cannot establish useful pricing inputs.

Previous provenance FedAvg accuracy85.3673%, CE0.538560, Brier0.245881; prior CE0.352059, Brier0.117621. The new dataset differs after both upstream corrections. Improved absolute scores, if present, do not alone demonstrate improved model effectiveness; the new same-dataset baseline is decisive.

## Behavioral and supply diagnostics

| metric | value |
| --- | --- |
| requests | 1705916.0 |
| accepted | 421985.0 |
| rejected | 1283931.0 |
| assignments | 262478.0 |
| accepted_unmatched | 159507.0 |
| price_ineligible_candidate_count | 210821707.0 |
| requests_with_any_price_ineligible_candidate | 408424.0 |
| accepted_requests_unmatched_due_to_no_price_eligible_driver | 158456.0 |
| driver_price_assignment_violations | 0.0 |
| P_max_above_2base | 148234.0 |
| P_max_above_5base | 27277.0 |
| epsilon_min | 1.1166503391926148e-05 |
| P_max_min | -1503930.2016186535 |
| P_max_max | 4111297.755527564 |

Reserve exclusions: 118 candidate evaluations across 12 requests; reposition exclusions 0. Exact grid-slot idle supply is available for 102,240 rows. Imbalance=requests−idle_at_slot_start; this is a boundary snapshot, not dynamic neighbor availability or proof of actual supply-caused rejection.

Largest deficits:

| timestamp | grid | requests | idle_at_slot_start | assignments | accepted_unserved | demand_minus_slot_start_idle |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-03-01 00:30:00 | 46 | 1306 | 1 | 61 | 78 | 1305 |
| 2026-03-01 00:00:00 | 46 | 1268 | 40 | 95 | 20 | 1228 |
| 2026-03-01 01:00:00 | 46 | 1206 | 1 | 77 | 88 | 1205 |
| 2026-03-01 01:30:00 | 46 | 1122 | 13 | 61 | 75 | 1109 |
| 2026-03-01 02:00:00 | 46 | 1046 | 14 | 59 | 72 | 1032 |
| 2026-03-08 00:30:00 | 46 | 1306 | 336 | 32 | 105 | 970 |
| 2026-03-04 18:00:00 | 36 | 1410 | 448 | 77 | 219 | 962 |
| 2026-03-05 21:30:00 | 36 | 1454 | 500 | 58 | 181 | 954 |
| 2026-03-07 00:30:00 | 46 | 1302 | 354 | 109 | 137 | 948 |
| 2026-03-07 00:00:00 | 46 | 1292 | 351 | 126 | 106 | 941 |

Largest excess supply:

| timestamp | grid | requests | idle_at_slot_start | assignments | accepted_unserved | demand_minus_slot_start_idle |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-03-13 05:00:00 | 31 | 0 | 2130 | 0 | 0 | -2130 |
| 2026-03-13 05:30:00 | 31 | 2 | 2132 | 2 | 0 | -2130 |
| 2026-03-13 04:30:00 | 31 | 1 | 2124 | 1 | 0 | -2123 |
| 2026-03-13 06:00:00 | 31 | 0 | 2122 | 0 | 0 | -2122 |
| 2026-03-13 04:00:00 | 31 | 1 | 2121 | 1 | 0 | -2120 |
| 2026-03-13 06:30:00 | 31 | 0 | 2118 | 0 | 0 | -2118 |
| 2026-03-13 03:30:00 | 31 | 2 | 2119 | 2 | 0 | -2117 |
| 2026-03-13 03:00:00 | 31 | 2 | 2110 | 2 | 0 | -2108 |
| 2026-03-13 07:00:00 | 31 | 0 | 2108 | 0 | 0 | -2108 |
| 2026-03-13 02:00:00 | 31 | 1 | 2105 | 1 | 0 | -2104 |

These summaries reuse existing saved diagnostics; no simulator rerun occurred.

## Selection, validation and next step

Selected structural checkpoint: `models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42/fedavg_round_5.keras`. The fifth global FedAvg checkpoint is selected because the architecture requires the federated policy, not because validation selected a best round or because central accuracy wins. Runtime checkpoint activation is not changed in this task.

Focused tests cover full dataset/cache and chronological boundaries,169D/9D valid masks, trained-model shape and save/reload, sample-weighted aggregation and zero-client exclusion, correct train-only prior, final-round selection and absence of March16+ leakage. Exact test results are saved in focused_test_results.json.

**ROUTING_READY_FOR_PRICING = NO**. If NO, the next task is a narrow routing-effectiveness diagnosis; if YES, separately define/freeze the final multi-episode DQN protocol. Neither task nor any pricing training was executed here. March17–31 remained untouched. Existing provenance datasets/checkpoints were preserved.

## Files

Requested dataset/action/participant/split/configuration JSON and CSV files, central history/validation/confusion matrix, all-round FedAvg metrics/final validation/confusion matrix, probability adequacy and selection are in this folder. Models and resumable training caches are isolated under `models/routing_policy/mar01_mar12_2026_final_behavioral_169x64x32x9_seed42`. Reproduction entrypoint: `scripts/train_final_behavioral_routing.py`; analytical gate: `scripts/summarize_behavioral_routing.py`. Existing baseline trainer and old outputs are unchanged.

**FINAL_BEHAVIORAL_ROUTING_TRAINING_COMPLETE**
