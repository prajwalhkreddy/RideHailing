# Narrow Routing-Effectiveness Diagnosis

**ROUTING_PROBABILITIES_INFORMATIVE = NO** (final FedAvg). **CENTRAL_PROBABILITIES_INFORMATIVE = INCONCLUSIVE**. Final FedAvg remains structurally complete; **pricing training remains blocked**. Recommended next category: **FEDAVG_PROTOCOL_CORRECTION**, for separately authorized design/review only. **ROUTING_STATE_CONTRACT_REVIEW_REQUIRED = YES**.

## Scope and reproducibility

Only the complete final behavioral March 1–15 dataset, its validated arrays, saved central/global/client checkpoints, existing training results, and directly relevant routing state/label/training code were inspected. No training, local update reproduction, simulator execution, methodology correction, model activation, or March 17–31 access occurred. Train 2,656,632 / validation 646,657; chronology unchanged. Model weights were read only. Small grid/type/slot metadata were read once from720 partitions; 169D arrays were reused. Diagnostic predictions and hashes are cached here for resumption. `diagnose.py` contains the analytical computation; `contract_review.py` documents source inspection. No neural models were fitted; conditional priors use train-only frequency counts.

## Central probability adequacy

| Model | CE | Multiclass Brier | Top-label ECE |
|---|---:|---:|---:|
| Central | 0.269109640 | 0.093789887 | 0.027600503 |
| Masked train-label prior | 0.293259219 | 0.095934945 | 0.006220436 |
| Final FedAvg | .441746289 | .178063054 | See previous probability report |

Central beats the prior on both aggregate losses: the public state contains useful held-out predictive signal under centralized learning (also binary AUROC.847967). This is not a full adequacy pass: paired144-slot mean CE/Brier differences are−.025521/−.002360 with SE.009562/.001278. CE clears the existing descriptive ±1.96SE check; Brier does not. The same previous gate therefore returns **INCONCLUSIVE**. Slot independence is assumed for this descriptive check; serial dependence is not corrected. ECE uses the same10 confidence bins, and is worse for central than prior despite improved CE/Brier. Meanprobability vectors and complete calibration bins are in central_probability_adequacy.json.

## Masks and class imbalance

All observations have 4–9valid actions; no STAY-only or STAY-plus-one-move rows. There are 30mask patterns in both periods. Masking changes prior CE from.297645 to.293259, and Brier from.096064 to.095935: its strength is primarily the dominant label, not forced-STAY masks. Full1–9cardinality counts/percentages, actionvalidity rates, STAY share and all threeCEs bycardinality for BOTH periods are in mask_diagnostics.json. Training-period model losses are in-sample descriptions only.

OverallSTAY95.218614%; validationSTAY95.057813%. The action CSV contains all 9 train/validation counts/shares and mean probability assigned to each trueclass.

| model | non_STAY_accuracy | non_STAY_CE | binary_AUROC | binary_Brier | binary_accuracy |
| --- | --- | --- | --- | --- | --- |
| central | 0.021652742576426045 | 4.426852586603108 | 0.8479666079673146 | 0.046147596761587334 | 0.9439733892929327 |
| fedavg | 0.0028473982289808817 | 5.9489048487426714 | 0.5538231130295515 | 0.09122538476165178 | 0.887043672302318 |
| prior | 0.0 | 5.085822607808585 | 0.5692725383451407 | 0.04688074021336289 | 0.9505781271988086 |

Non-STAY accuracy remains very low even centrally. Binary metrics distinguish MOVE probability1−p(STAY), threshold.5 for binaryaccuracy, and AUROC ranking from the original9-class top-1 decision. No threshold is applied to the model or dataset.

## Client heterogeneity and temporal shift

TrainclientSTAY share min/P10/median/mean/P90/max:52.6946/88.4327/95.8942/94.6391/99.3056/100%. Median non-STAY23, median supportedactions8, medianentropy.238664nats. JS divergence toglobaltrain prior median.005730, P90.014324, max.133373nats.55clients have noMOVE;841(16.82%) have>99%STAY;2981(59.62%) have>95%STAY;842(16.84%) have≤5MOVE;2183(43.66%) have≤20MOVE. Fullcount/actiondistributions are in client_distribution.csv; all requested summaryquantiles are in client_heterogeneity.json.

All5000clients appear in both periods. TemporalJS median.011969/P90.027185/max.266671nats. This is distribution shift evidence, not causal inference. ClientJS is dominated by a sharedSTAYmajority and should not be interpreted as measuring featureheterogeneity fully.

## Saved update directions and optimization consistency

100clients were deterministically stratified by counttertile, high/lowSTAY and high/lowJS. Saved round1 localweights were compared with the seed 42 common initialization reconstructed without optimization. Median pair cosine.630624; negativepairfraction0%; meanupdate alignmentmedian.812814; normofmean/meannorm.780425 (weighted.779755). Updates partially average out but do not show strong opposing/cancelling directions in this sample/round. Count–norm correlation.673305; STAY share–alignment correlation−.039328. Sampling cannot establish behavior for all clients/all rounds.

No accidental central/FedAvg contract mismatch found: same X/M/Y, no extra normalization, same 169→64→32→9,seed 42,maskedcrossentropy,Adam.001,batch32,float32. Central has83,020continuousAdamsteps in one chronological epoch. Eachlocalclient has5–18steps/round (median18), freshAdam/reset moments, and common globalweights; clientfinalweights are sampleweighted. Withinclient ordering is chronological, no shuffle; smallpositiveclients retain finalpartialbatch; zeros excluded. These are intentional protocol differences. Fresh local optimizers/weight averaging need not reproduce central optimization, even when directions broadly align. No ablation was performed.

## Global round progression

| round | CE | Brier | accuracy | L2_initial | L2_previous |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.7076931962022995 | 0.2231129724816587 | 0.8870003726859834 | 0.2621608300668355 | 0.2621608300668355 |
| 2 | 0.6309926720745447 | 0.2215035205092954 | 0.8870050119305907 | 0.3068880283040724 | 0.1143074482303222 |
| 3 | 0.5533118732530524 | 0.2106552207868911 | 0.8870297545684961 | 0.3745952175168283 | 0.0960331038180208 |
| 4 | 0.4970384972179136 | 0.1988495222366915 | 0.8871070753119505 | 0.4412066459250757 | 0.0913273316822513 |
| 5 | 0.4417462887343048 | 0.178063054036549 | 0.8871070753119505 | 0.5097557002587108 | 0.0856291961680844 |

CE andBrier monotonically improve; accuracy is almost flat (~88.7%). Drift frominitial grows while consecutiveparametersteps shrink. This supports incomplete/protocol-dependent learning rather than divergence; no additionalrounds are recommended or executed here.

## State–label information and ambiguity

The169features contain local9×(mu,sigma,F_hat) and all142H_hat values. P_min,W_max,batteryenergy,chargingbranch and private feasibility are absent. H_i_max is also absent but fixed10 externally in thisbaseline. Position is implicit candidate-relative context, not explicitGridID; global station topology/reachability is external. Topologicalactionmask is separately supplied, not an energy feasibility mask. REPOSITION usesU1(P_min,mu,sigma)+U2(F_hat,W_max)−movementcost afterenergy/reservechecks. Charging usesU3(H_i_max,H_hat)−pathcost overreachable stations, selecting shortestpath nextaction. Ties use score/action/stationID. CompleteA/B/C/D classification with source locations is in routing_state_label_information_map.csv. Public masked states cannot deterministically identify these private/simulator-dependent decisions.

Exactfloat32 state+mask repeats:56,275groups /3,291,587observations;40.7570%groups have conflictinglabels (45.5420%representedobservations), weightedconditionalentropy.081250nats. All exactrepeated groups span multipleclients. Separately REPOSITION54,422groups /3,273,002observations;33.4938%groupsconflict; conditionalentropy.071294. Charging3,775groups /10,044observations;0%conflict. Rounded4decimalstate+mask:43.4481%allgroups and35.8158%REPOSITIONgroupsconflict; charging0%. Absolute1e−4in nativefeatureunits is diagnostic, far below typical fare magnitudes; no equivalence or measurementprecision claim.64-bithashing has negligible nonzero collisionrisk. Percentages are over repeated groups, not alltrips; state hash evidence does not by itself attribute every conflict to a particular hidden variable.

## Decision-type mixture

| type | N | STAY_share | central_CE | fedavg_CE | prior_CE |
| --- | --- | --- | --- | --- | --- |
| REPOSITION | 641955 | 0.9565826265080886 | 0.2496925285243964 | 0.4071680627182479 | 0.2630842569586824 |
| EV_CHARGING_NEXT_HOP | 4702 | 0.13079540621012334 | 2.92009047060116 | 5.162644860009872 | 4.412988662860605 |

Charging is.7271% ofvalidation but contributes8.50%ofFedAvg CE. It is disproportionately difficult; howeverREPOSITION alone remains worse thanprior, so removingcharging would not resolve inadequacy and was not attempted. Fulltypeaction/maskdistributions are saved.

## Train-only conditional prior probes

| prior | CE | Brier | zero_true_probability_N |
| --- | --- | --- | --- |
| global | 0.2932592191357729 | 0.09593494534270659 | 0 |
| grid | Infinity | 0.08645549506455852 | 161 |
| half_hour | 0.29590254704347113 | 0.09636485398796191 | 0 |
| grid_x_6hour | Infinity | 0.08454794020342113 | 1258 |

Coarse time bins are00–05,06–11,12–17,18–23. Frequencies use train labels only; missingcontexts fall back toglobaltrain prior. Zero remainingmaskmass also falls back. Unobserved targetactions in observedcontexts are not silently smoothed: theirCE is genuinely infinite. Grid×6hour achieves bestBrier.084548 but has1,258zero-probability held-out targets; gridprior has161. It is not a usable CE winner. Globalprior is strongest finiteCEconditional probe; half-hourprior does not improve it. These probes indicate spatialassociation while demonstrating sparseconditional-support risk; none replaces the policy.

## Root cause and next action

- **CLASS_IMBALANCE: HIGH** — STAY95.218614% overall; central MOVE accuracy2.1653%, FedAvg0.2847%;59.62% clients >95%STAY.
- **MASK_DOMINANCE: LOW** — No observations have only 1 or 2 actions; all have 4–9; masking lowers prior CE only0.297645 to0.293259.
- **CLIENT_NON_IID: MODERATE** — Client train JS median0.005730/P90 .014324/max .133373 nats;STAY52.69–100%;temporal JS median.011969. Strong majority shared, minority exposure heterogeneous.
- **FEDAVG_OPTIMIZATION_DRIFT: HIGH** — Protocol-dependent optimization gap: centralCE.269110 versusFedAvg.441746;Brier.093790 versus.178063. RoundBrier improves.223113 to.178063. Sampled round1 paircosmedian.630624, zero negativepairs, cancellationratio.780425; destructive gradient conflict NOT demonstrated. Local5–18 fresh-Adamsteps thenweight averaging differs fromcentral83020continuoussteps. No controlled ablation identifies a single causal mechanism.
- **PUBLIC_STATE_LABEL_NONIDENTIFIABILITY: HIGH** — P_min,W_max,energy,branch absent. Exact repeatedREPOSITION groups33.4938% conflict, covering39.4620% repeated observations; conditionalentropy.071294 nats. Hidden inputs prevent deterministic label reconstruction but do not imply no useful probabilistic signal.
- **DECISION_TYPE_MIXTURE: MODERATE** — Validationcharging4702/646657=.7271%;FedAvg CE5.162645 vsREPOSITION.407168. Charging contributes8.50% ofFedAvg CE, but REPOSITION alone also underperformsprior.263084.
- **IMPLEMENTATION_MISMATCH: NO** — Same cachedfeatures/masks/labels, deterministicseed 42 architecture, compiledloss,Adam.001,batch32,float32. Fresh localoptimizer andweight averaging intentional, not accidental discrepancy.

Primary explanation for the central–FedAvg gap is federated optimization/protocol interacting with heterogeneous minority exposure. Destructive update conflict is not established. Independently, hidden label inputs produce substantial exact state ambiguity and warrant contract review, but cannot alone explain why central performs better with identical inputs. The centralcombinedgate isINCONCLUSIVE, so no claim is made that a protocol correction alone will pass adequacy.

**Exactly one recommended next category: FEDAVG_PROTOCOL_CORRECTION.** This is authorization for no change: a next task must decide the correction. No optimizer, rate, epochs, rounds, weighting, loss, state, head or calibration change was made. Pricing remains blocked. March 17–31 untouched.

## Validation and files

All requestedJSON/CSV artifacts are present; diagnostic probability arrays and hash/metadata caches preserve completedwork. Analyticalchecks verifyN/splits,finite normalizedmaskedprobabilities, peraction/type/count conservation, savedCE agreement, correct train prior,100unique savedclients,5rounds, and gapinterpretations. Evidence is descriptive; severitylabels are reasoned assessments, not formally estimated causal effects. See diagnostic_validation.json for checks.

**ROUTING_EFFECTIVENESS_DIAGNOSIS_COMPLETE**
