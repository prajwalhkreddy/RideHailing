# Frozen FedAvg Protocol Correction Experiment

**FEDAVG_PROTOCOL_RECOVERS_SIGNAL = NO**  
**FEDAVG_PROTOCOL_CORRECTION_SUCCESS = NO**  
**ROUTING_READY_FOR_PRICING = NO**  
**ROUTING_STATE_CONTRACT_REVIEW_REQUIRED = YES**

## Scope and frozen contracts

The complete final behavioral dataset and its existing memory-mapped arrays were reused: 2,656,632 March 1–12 training observations and 646,657 March 13–15 validation observations. No raw processing, experience generation, CNN/passenger/pricing inspection, privacy, or March 17–31 access occurred. State169, architecture169→64→32→9, masks, labels, masked cross-entropy, float32 training, batch32, learning rate.001, seed42, and full-client sample weighting are unchanged. There was no state addition, class balancing, oversampling, loss change or broad search. Production configuration and selected runtime checkpoint were not changed.

## Prescribed variants and initialization

A reused the saved5-round full-epoch fresh-Adam control. Its saved checkpoints and localupdates were read for additional per-round probability/drift metrics; no control training was repeated. B runs exactly one fresh-Adam minibatch/client/round; C caps fresh-Adam work at5batches; D uses momentum-zero SGD with the same5-batch cap. All have5 rounds and5,000 active clients.

No initialcheckpoint was persisted for the originalcontrol. One seed42 initialization was reconstructed with the exact existing builder, saved as initial.keras in the newmodeldirectory, and used bit-identically for B/C/D. The initialization hash in protocol_variants.json hashes raw tensorbytes in fixedweightorder. A's documentedbuilder/seed matches, but no separately saved historicalinitial artifact exists for independent comparison.

For eachclient, a seed42/client RNG selects five distinct rowoffsets withoutreplacement. Roundr rotates the client's chronological sequence at offsetr; B takes up to32rows, C/D up to160, in batches32with finalpartialbatch. C/D receive identicalselectedrows; B receives their firstbatch. No withinroundduplicates; the circularboundary wrap is explicit. Batches are selected using training rows only. A retains its originalfullchronologicalepochs, so the shortwork variants also differ in which rows are exposed and order at the wrap; this experiment does not isolate drift from reducedoptimization budget perfectly.

Adam moments reset perclient; SGD momentum0. Aggregation weights are FULLclienttrainingcounts, not selectedminibatchcounts. Streaming float64weight sums followed byfloat32casting match the existing sampleweightedaggregator; focusedtests verify equivalence, including zero-clientexclusion. Newround checkpoints and partialsums every250clients permit resumption without storing5,000 client tensors for diagnostics.

## Held-out results

| variant | CE | Brier | ECE | accuracy | non_STAY_accuracy | non_STAY_CE |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0.4417462887343011 | 0.1780630540365483 | 0.0760058220585791 | 0.8871070753119505 | 0.0028473982289808 | 5.948904848742675 |
| B | 1.1424247418307152 | 0.3232424479397756 | 0.0662550813365385 | 0.8067599979587323 | 0.0630495322131481 | 5.465899004267919 |
| C | 0.7042631313893845 | 0.2262945871357646 | 0.1069521934933137 | 0.8870081047603289 | 0.0030664288619794 | 6.965363602784611 |
| D | 0.7318948106611958 | 0.2334074292665943 | 0.1171027733515453 | 0.8869787228778162 | 0.005976407271817 | 6.924378153095095 |

Central CE/Brier/ECE:0.269109640/0.093789887/0.027600503. Masked train-label prior CE/Brier:0.293259219/0.095934945. Central's previouscombined uncertainty gate wasINCONCLUSIVE despite lower aggregateCE/Brier; that qualification remains unchanged.

Best overall variant/round byCE thenBrier: **A/5**, CE0.441746289, Brier0.178063054, ECE0.076005822, accuracy88.710708%. Best corrected variant/round: **C/5**, CE0.704263131, Brier0.226294587. Ifcontrol wins, it is explicitly the comparisonwinner, not a successful correction. All20roundmetrics include true/predicted9-classcounts, STAYshare, non-STAYaccuracy/CE, invalidviolations and parameterdistance frominitial. No trainingloss or accuracy was used for selection.

## Local work and update magnitudes

| variant | round | clients | total_weight | mean | P10 | median | P90 | total_optimizer_steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 5 | 5000 | 2656632 | 16.884 | 14.0 | 18.0 | 18.0 | 84420 |
| B | 5 | 5000 | 2656632 | 1.0 | 1.0 | 1.0 | 1.0 | 5000 |
| C | 5 | 5000 | 2656632 | 5.0 | 5.0 | 5.0 | 5.0 | 25000 |
| D | 5 | 5000 | 2656632 | 5.0 | 5.0 | 5.0 | 5.0 | 25000 |

| variant | round | mean_local_update_L2 | global_update_L2 | weighted_mean_client_global_cosine |
| --- | --- | --- | --- | --- |
| A | 5 | 0.2465133358438455 | 0.0856291961680844 | 0.3440895898642968 |
| B | 5 | 0.0376681395861321 | 0.0212058317282023 | 0.5736613050581199 |
| C | 5 | 0.1162398040105682 | 0.0370948843416809 | 0.3286725928135721 |
| D | 5 | 0.0280978337406353 | 0.0108912888438591 | 0.2531283737606897 |

Meanlocalnorm is the unweighted mean of eachclient's parameter update norm. Globalnorm is the norm of the aggregated change from the previousglobalmodel. Weightedcosine uses fullsamples: sum(weight×unitlocaldelta) dot unitglobaldelta; it is accumulated without retainingclienttensors. Zero-normlocalupdates contribute0 by convention. These are parameter-space diagnostics, not proofs of causal optimizationdrift. Per-round statistics are in local_step_diagnostics.csv and update_diagnostics.csv.

## Adequacy and interpretation

Corrected variant-rounds beating the prior on bothCE andBrier without invalidpredictions: **0**. The explicitstop rule takes precedence: if none passes, recovery=NO, state contract review=YES, and no additional experiment. Passingbothprior losses would close most of the control-to-centralgap; probability_comparison.csv reports exact gapclosures rather than selecting for lowSD or top1accuracy. Selection across these prescribedrounds is validation selection, not independent test performance.

The experiment tests specified localwork/optimizer protocols, not every possiblecause. Reducedwork changes totaloptimization as well as drift. Failure of these variants does not prove allFedAvgprotocols incapable or establish that hidden state alone caused thegap. No additionalrates,epochs,rounds,FedProx,losses orarchitecture were attempted.

## State limitation and next action

**PUBLIC_STATE_LABEL_NONIDENTIFIABILITY = HIGH** remains: driverpreferences, battery/energy, chargingbranch and feasibility/reachability information are absent from169D;33.49%of repeatedexactREPOSITION state groups had conflictinglabels. No state change was made.

**Next category: ROUTING_STATE_CONTRACT_CORRECTION.** Not executed. Pricing remainsblocked even if a correctionpasses, pending separately authorized frozen routing verification. No productioncheckpoint activation took place; old models/results preserved.

## Artifacts and validation

Required protocol_variants.json, round_metrics.csv, probability_comparison.csv, local_step_diagnostics.csv, update_diagnostics.csv, protocol_selection.json and next_action.json are saved here. Newmodels: `models/routing_policy/mar01_mar12_2026_final_behavioral_fedavg_protocols_seed42/`. Each B/C/Dround has a checkpoint; all reloadlogits were verifiedexactly. Per-roundJSON files preserve incrementalresults. Entrypoint:`scripts/experiment_fedavg_protocols.py`; focusedtests:`tests/test_fedavg_protocol_experiment.py`.

Four focusedtests passed. All20variant-round reports present;15newrounds trained,5controlrounds reused; zero invalidactionpredictions; fullsampleweights andcountreconciliation passed; oldselectedcheckpoint SHA256 unchanged. See focused_validation.json. No pricing training; March 17–31 untouched.

**FEDAVG_PROTOCOL_CORRECTION_COMPLETE**
