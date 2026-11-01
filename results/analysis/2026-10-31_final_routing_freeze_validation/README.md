# Final Temporal Routing Freeze Validation

**FINAL_ROUTING_MODEL_FROZEN = YES**  
**ROUTING_READY_FOR_PRICING = YES**  
**Improvement: MODEST / UNCERTAIN BUT POSITIVE.**

Methodology-faithful temporal federated routing provides a modest held-out probabilistic improvement over the empirical prior while retaining weak rare-action classification performance. Readiness authorizes no pricing training in this task. The next category is **FINAL_PRICING_DQN_TRAINING_PROTOCOL_FREEZE**, not executed.

## Frozen checkpoint and reproducibility

Checkpoint: `models/routing_policy/mar01_mar12_2026_temporal_fedavg_169x64x32x9_seed42/final_march12.keras`.  
SHA256: `db2d4170477addbbbf8654421b8eaf231b3359f68159ae860c4edbac1d2e8b2a`.

Two independently loaded copies produced bit-identical logits and masked probabilities over all 646,657 March 13–15 observations. Identical probability arrays yield identical repeated metrics; the previously recorded final metrics were also reproduced within 1e−12. Inference uses deterministic Dense/ReLU operations with training=False, no stochastic layer or RNG-dependent sampling. The checkpoint hash remained unchanged. No optimizer or training API was invoked.

Input 169 and output 9 shapes pass. Every true label is mask-valid; probabilities are finite, sum to one, and are exactly zero for invalid actions. Invalid-action predictions: 0. The existing temporal chronology and checkpoint evidence establish 576 March 1–12 training slots and next-slot updates; only the frozen March 13–15 validation slice was evaluated. March 16+ was not used for training; March 17–31 remained untouched.

## Aggregate probability quality

CE **0.291657966**, Brier **0.093053954**, ECE **0.015838035**. Empirical-prior CE/Brier:0.293259219/0.095934945. Observation-weighted differences(model−prior): **-0.001601253 / -0.002880991**.

Central CE remains better(0.269109640); temporal Brier is slightly better than central(0.093789887). Temporal losses substantially improve over old offline FedAvg(CE0.441746289/Brier0.178063054). The empirical prior remains a strong baseline. No claim of high routing accuracy or causal superiority is made.

## Paired slot-level uncertainty

Slot means weight each of144 half-hour slots equally. They differ from the observation-weighted aggregate because slot counts vary.

| Metric | Mean difference | Median | SD | SE | Fraction model wins | Moving-block95% interval |
|---|---:|---:|---:|---:|---:|---|
| CE | -0.002366828 | -0.014815502 | 0.085663133 | 0.007138594 | 0.777778 | [-0.019174270, 0.022761744] |
| Brier | -0.002924012 | -0.002432819 | 0.003709191 | 0.000309099 | 0.750000 | [-0.004221724, -0.001877550] |

Bootstrap:2,000 replicates, seed42, noncircular overlapping blocks of8slots(4hours). Each replicate samples18blocks from137 possible starts and averages144 sampled slot differences. Percentile intervals use2.5%/97.5% quantiles. SE is descriptive independent-slot SE; the block interval, rather than an independent-slot t-test alone, addresses short-range dependence. Three validation days limit broader temporal generalization. CE uncertainty includes zero; Brier interval is negative. The requested freeze rule does not require both intervals to exclude zero. No model selection or recalibration used these results.

## Daily stability

| date | N | model_CE | prior_CE | model_Brier | prior_Brier | model_ECE | prior_ECE | model_wins_both |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-13 | 219650 | 0.3396348732982635 | 0.3113784017169543 | 0.0987598339457288 | 0.0995851910508144 | 0.0142187232516168 | 0.007619218873279 | False |
| 2026-03-14 | 209982 | 0.2825687227217193 | 0.295055876155295 | 0.0937521947818162 | 0.0992424431700721 | 0.019167290685668 | 0.0080102379275688 | True |
| 2026-03-15 | 217025 | 0.2518950342500023 | 0.2731825271038424 | 0.0866034778498913 | 0.089040387210824 | 0.0172918685460844 | 0.0030730165327055 | True |

Temporal wins both losses on **2/3 days**:March 14 andMarch 15. March 13 has worse CE but better Brier. These mixed daily results qualify the overall improvement.

## Nine-action vector and true-action probability

| action | mean | SD | P05 | median | P95 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.9599890706787404 | 0.0645739544161145 | 0.8562476981292797 | 0.9796205779549924 | 0.9999360803930112 |
| 1 | 0.003504179725161 | 0.0065814691054089 | 0.0 | 0.0014972507770848 | 0.0140190776585826 |
| 2 | 0.0010269251991276 | 0.0051916564116204 | 0.0 | 0.0001137990909082 | 0.0019251738422007 |
| 3 | 0.0092201129407962 | 0.0123484220094032 | 0.0 | 0.0042787768231289 | 0.0280778280179718 |
| 4 | 0.0008219474950535 | 0.0016420849260973 | 0.0 | 0.0003786097992151 | 0.0023813264150123 |
| 5 | 0.0077541425756702 | 0.0294237662697081 | 1.100090075766604e-05 | 0.0014202275089135 | 0.0305187095354405 |
| 6 | 0.003477160385441 | 0.0105349768525781 | 0.0 | 0.0010217290844604 | 0.0136268432409635 |
| 7 | 0.0135182413821794 | 0.0279238385183054 | 0.0 | 0.0083862847766546 | 0.0369620881468111 |
| 8 | 0.0006882196178304 | 0.003109269304023 | 0.0 | 0.0002018166977365 | 0.001464242153646 |

Prediction entropy in nats: mean0.187676; P05/median/P95:0.000750/0.128085/0.592128. **ROUTING_VECTOR_NONDEGENERATE = YES**. The vector is strongly STAY-dominant but not constant: STAY probability SD.064574 and movement-action SDs reach.029424. The descriptive >.01 SD check is recorded with the full distribution, not used for model tuning or calibration. Mask structure is unchanged; variation need not imply strong rare-action skill.

| group | N | mean | median | P10 | P90 |
| --- | --- | --- | --- | --- | --- |
| ALL | 646657 | 0.9175204561885336 | 0.9794458800527164 | 0.8796622193238046 | 0.9998673005487504 |
| STAY | 614698 | 0.9635038733710024 | 0.9813763177511816 | 0.9180283509574692 | 0.999876574593584 |
| NON_STAY | 31959 | 0.0330774330892678 | 0.0058966937983347 | 0.0003833793351953 | 0.0899006709403517 |
| 1 | 3223 | 0.0059843282720555 | 0.0047802507794745 | 0.0007040728443952 | 0.0127933666152089 |
| 2 | 3682 | 0.0009977614307646 | 0.0004974186465229 | 0.0003282043870667 | 0.001046539119666 |
| 3 | 2610 | 0.0360393674899236 | 0.0206539414831969 | 0.0066197630040871 | 0.0849045814328974 |
| 4 | 1419 | 0.0021398349983934 | 0.0011489017644584 | 0.0001951297607104 | 0.0031792174502882 |
| 5 | 9329 | 0.0423003556073689 | 0.0083305459195534 | 0.0032232623335495 | 0.1229781149388157 |
| 6 | 3380 | 0.031225387455564 | 0.0180758621915882 | 0.00202800602253 | 0.0846826848395848 |
| 7 | 4388 | 0.0974176358580773 | 0.0356341546119372 | 0.0077500806813115 | 0.3072972169677186 |
| 8 | 3928 | 0.0024009287865035 | 0.0003833793351953 | 0.0003566949401967 | 0.0043964929649892 |

## Non-STAY qualification

| Model | Non-STAY CE | Non-STAY Brier |
|---|---:|---:|
| Temporal | 5.140560449 | 1.756599254 |
| Prior | 5.085822608 | 1.898173237 |
| Central | 4.426852587 | 1.600075736 |

**NON_STAY_PROBABILITY_SIGNAL = INCONCLUSIVE**: temporal improves non-STAY Brier but worsens CE versus prior; central is better on both. Non-STAY top-1 accuracy is 0.6195%. Aggregate gains therefore do not establish reliable rare-movement classification. This mixed subgroup result is retained as a limitation, not hidden by STAY accuracy. It does not demonstrate an invalid or constant probability vector; under the explicit aggregate/nondegeneracy freeze gate, it does not independently prohibit use as an input to a separately validated pricing model.

## Frozen method and decision boundary

- Public state:169D_PUBLIC_GRID_STATISTICS; private driver variables:LOCAL_ONLY.
- Learning:TEMPORAL_FEDAVG; latest 32 local observations from persistent buffers.
- Optimizer:PERSISTENT_ADAM; only CURRENT_SLOT_CONTRIBUTORS_ONLY participate.
- Aggregation:EQUAL_ELIGIBLE_CLIENT_WEIGHTING; each slot's aggregate is available next slot.

The method is recorded in routing_freeze_contract.json. No state, architecture, label, local/private boundary, training or calibration change occurred. The freeze passes because reproducibility and structural checks pass, aggregate CE/Brier improve, invalid actions are absent, and the vector is nondegenerate. CE uncertainty and mixed non-STAY performance remain thesis limitations. No additional routing rounds will be run merely to pursue significance.

Root README changes are confined to Current Resume Point, Routing Model Status and Open Methodology Decisions. Existing historical reports remain unchanged; runtime checkpoint activation was not modified. Routing-learning protocol is no longer an open methodological choice. Next action is the pricing-training protocol freeze—not pricing execution.

## Files and checks

Required checkpoint, contract, paired-slot, bootstrap, daily, vector, true-action, non-STAY and readiness artifacts are saved in this folder. vector_quality.json contains entropy and nondegeneracy detail. All144 slots and three days reconcile to646,657 observations; per-action and true-action summaries preserve that population. No model update, simulator generation, privacy implementation or March 17–31 access occurred.

**FINAL_ROUTING_FREEZE_VALIDATION_COMPLETE**
